#!/usr/bin/env python3
"""PreToolUse(Bash) hook — `pkill -f`·`pgrep -f` 의 패턴이 자기 명령줄에 매칭되면 거부.

도구 셸은 명령 전체가 들어 있는 명령줄(`zsh -c "... eval '<명령>'"`)로 실행됨. `-f` 는 프로세스의
전체 명령줄을 정규식으로 검색하므로, 패턴이 명령 문자열에 매칭되면 자기 셸이 대상에 포함됨
- pkill: 자기 셸이 종료돼 뒤 명령이 실행되지 않음(exit 144)
- pgrep: 자기 셸 PID 를 잡아 항상 rc=0 거짓 양성이 됨(`while pgrep -f ...` 가 끝나지 않음)

- 판정: 각 후보 패턴에 `re.search(패턴, 명령 전체)` 를 수행해 자기 매칭을 직접 확인함.
  대괄호 유무가 아니라 매칭 여부가 기준이므로 `[r]un` 이어도 같은 명령에 `run` 평문이 남아 있으면
  거부하고, 정규식 오류(re.error)도 거부함
- 탐지: shell_parse.find_commands 로 basename 이 pkill·pgrep 인 명령을 위치와 무관하게 찾음
  (`sudo`·`xargs`·`$(...)`·`bash -c` 안쪽 포함). 다음 `; | & ( )` 전까지가 그 명령의 인자임
- 거부는 `permissionDecision: deny` 로만 표현함. allow 는 출력하지 않음
- 거부 사유: 매칭된 패턴의 분기(처음·`|`·`(` 뒤)마다 메타문자가 아닌 첫 글자를 `[c]` 로 감싼 대체 패턴을
  제시함(문자 클래스 안은 건드리지 않아 뜻이 같음). 바꾼 패턴도 자기 매칭하면 일반 안내로 대신함
- 입력 해석 실패·예외는 모두 통과(exit 0, 출력 없음) — hook 고장이 작업을 막지 않게 함
- 한계: 따옴표 없는 `echo pkill -f x` 처럼 인자 위치의 pkill 도 명령으로 보아 거부함(실사용 드묾).
  판정하지 못하는 경로 — `"$VAR"` 패턴, `-i`(대소문자 무시), 실제 argv 에 붙는 래퍼 접두
  (`zsh`·`snapshot`·`/dev/null`·`true` 등)에만 걸리는 짧은 패턴, `-x` 와 `-f` 를 함께 쓴 패턴은
  전체 일치(re.fullmatch)로만 봄
"""

from __future__ import annotations

import json
import re
import signal
import string
import sys

import shell_parse

_TARGETS = ("pkill", "pgrep")
_SIGNALS = frozenset(s.name.removeprefix("SIG") for s in signal.Signals)
# 값을 받는 짧은 옵션(procps-ng 3.3.16 `pkill --help` 기준). 대문자 -F 는 pidfile 이라 -f 와 구분함
_VALUE_SHORT = frozenset("gGPstuUFrd")
_VALUE_LONG = frozenset({
    "--signal", "--ns", "--nslist", "--pgroup", "--group", "--parent", "--session",
    "--terminal", "--euid", "--uid", "--pidfile", "--runstates", "--delimiter",
})
_HINT_CHARS = frozenset(string.ascii_letters + string.digits + "_-/")  # `[c]` 로 감쌀 리터럴 글자


def _is_signal(option: str) -> bool:
    """`-9`·`-STOP`·`-SIGTERM` 같은 시그널 옵션(`-P` 등 값 옵션과 구분하려고 먼저 거름)."""
    name = option[1:]
    return name.isdigit() or name.removeprefix("SIG") in _SIGNALS


def _parse_args(args: list[str]) -> tuple[bool, bool, list[str]]:
    """pkill·pgrep 인자에서 (-f 사용 여부, -x 사용 여부, 패턴 후보 목록) 을 뽑음."""
    full = False
    exact = False
    candidates: list[str] = []
    options_done = False
    i = 0
    while i < len(args):
        token = args[i]
        i += 1
        if options_done or not token.startswith("-") or token == "-":
            candidates.append(token)
        elif token == "--":
            options_done = True
        elif token.startswith("--"):
            name = token.split("=", 1)[0]
            full = full or name == "--full"
            exact = exact or name == "--exact"
            if name in _VALUE_LONG and "=" not in token:
                i += 1
        elif not _is_signal(token):
            for pos, char in enumerate(token[1:], start=1):
                if char in _VALUE_SHORT:
                    if pos == len(token) - 1:  # 값이 다음 토큰에 있음
                        i += 1
                    break
                full = full or char == "f"
                exact = exact or char == "x"
    return full, exact, candidates


def _self_matching(command: str) -> list[tuple[str, str, str]]:
    """(명령 이름, 자기 매칭 사유, 패턴) 목록 — 사유는 'match' 또는 'regex-error'."""
    found: list[tuple[str, str, str]] = []
    for name, following in shell_parse.find_commands(command, _TARGETS):
        args: list[str] = []
        for token in following:
            if shell_parse.is_punct(token):
                if token[0] in "<>" and args and args[-1].isdigit():
                    args.pop()  # `2>&1` 의 파일 디스크립터 번호는 패턴이 아님
                break
            args.append(token)
        full, exact, candidates = _parse_args(args)
        if not full:
            continue
        matcher = re.fullmatch if exact else re.search  # -x 는 명령줄 전체 일치라 자기 셸에 안 걸림
        for pattern in candidates:
            try:
                if matcher(pattern, command):
                    found.append((name, "match", pattern))
            except re.error:
                found.append((name, "regex-error", pattern))
    return found


def _class_end(pattern: str, start: int) -> int:
    """`start` 의 `[` 로 연 문자 클래스의 닫는 `]` 다음 위치(닫히지 않으면 패턴 끝).

    `[^` 뒤나 `[` 바로 뒤의 `]` 는 리터럴임(`[]|a]` 는 `]`·`|`·`a` 중 하나)
    """
    i = start + 1
    if pattern.startswith("^", i):
        i += 1
    if pattern.startswith("]", i):
        i += 1
    while i < len(pattern):
        if pattern[i] == "\\":
            i += 2
            continue
        if pattern[i] == "]":
            return i + 1
        i += 1
    return len(pattern)


def _branch_starts(pattern: str) -> list[int]:
    """분기가 시작하는 위치 — 패턴 처음과 문자 클래스 밖의 이스케이프 안 된 `|`·`(` 바로 뒤."""
    starts = [0]
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "\\":
            i += 2
            continue
        if char == "[":
            i = _class_end(pattern, i)
            continue
        if char in "|(":
            starts.append(i + 1)
        i += 1
    return starts


def _search(pattern: str, text: str) -> bool | None:
    """`re.search` 결과(정규식 오류면 None) — 힌트 계산 예외가 main 의 통과 경로로 새지 않게 함."""
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return None


def _bracketed_pattern(pattern: str) -> str | None:
    """분기마다 첫 리터럴 글자를 `[c]` 로 감싼 패턴(바꿀 분기가 없거나 여전히 자기 매칭이면 None).

    문자 클래스 밖의 리터럴 한 글자 `c` 와 `[c]` 는 같은 글자에 매칭되므로 뜻이 바뀌지 않음
    """
    chars = list(pattern)
    for start in _branch_starts(pattern):
        if start < len(pattern) and pattern[start] in _HINT_CHARS:
            chars[start] = f"[{pattern[start]}]"
    hint = "".join(chars)
    if hint == pattern or _search(hint, hint) is not False:
        return None
    return hint


def verdict(command: str) -> str | None:
    """거부 사유(거부 대상이 아니면 None)."""
    hits = _self_matching(command)
    if not hits:
        return None
    name, kind, pattern = hits[0]
    if kind == "regex-error":
        return (f"`{name} -f` 의 패턴을 정규식으로 해석할 수 없어 자기 매칭 여부를 확인하지 못한다. "
                "패턴을 단순화하거나 `[x]` 형식으로 바꾼다.")
    effect = ("자기 셸이 종료돼 뒤 명령이 실행되지 않는다(exit 144)" if name == "pkill"
              else "자기 셸 PID 를 잡아 항상 성공(rc=0)으로 끝나 조건 루프가 멈추지 않는다")
    head = f"`{name} -f` 의 패턴이 이 명령줄 자체에 매칭돼 {effect}. "
    split = "정지 뒤 재시작처럼 평문이 필요한 명령은 별도 Bash 호출로 나눈다."
    if _search(pattern, pattern) is False:
        return (head + f"패턴 `{pattern}` 자체는 자기 매칭하지 않지만 같은 Bash 호출의 다른 곳에 "
                "매칭되는 평문이 있다. " + split)
    hint = _bracketed_pattern(pattern)
    if hint is None:
        return (head + "패턴 각 분기에서 메타문자가 아닌 첫 글자를 대괄호로 감싸(예: `[w]orker.py`) "
                "평문이 같은 Bash 호출 어디에도 남지 않게 한다. " + split)
    reason = head + f"패턴을 `{hint}` 로 바꾼다(예: `{name} -f \"{hint}\"`)."
    # 셸 따옴표·이스케이프가 풀린 패턴은 명령 원문에 없어 바꿔 볼 수 없음 → 나머지 검증 생략
    if pattern in command and _search(hint, command.replace(pattern, hint, 1)) is not False:
        reason += " 바꾼 뒤에도 같은 Bash 호출의 다른 곳에 매칭되는 평문이 남는다. " + split
    return reason


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") if isinstance(data, dict) else None
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str):
            return 0
        reason = verdict(command)
    except Exception:  # noqa: BLE001 — hook 고장이 작업을 막지 않게 모든 예외를 통과시킴(2026-11-24 승인)
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
