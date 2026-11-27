#!/usr/bin/env python3
r"""PreToolUse(Bash) hook — 루트(`/`)나 네트워크 마운트의 상위 경로에서 시작하는 `find` 를 거부.

`find /` 는 /proc·/sys 와 모든 마운트를, `find ~`·`find /workspace` 는 그 아래 sshfs(호스트 `~/mnt/aip2`·
컨테이너 `/workspace/mnt/aip2`)를 순회해, 끊기거나 응답 없는 마운트에서 멈추거나 수 분 걸림
(2026-11-22·11-26 voiceguard 사례, 키 hook-block-root-find-scan)

- 탐지: shell_parse.find_commands 로 basename 이 find 인 명령을 위치와 무관하게 찾음(`sudo`·`timeout`·
  파이프 뒤·`$(...)`·`bash -c` 안쪽 포함). 다음 `; | & 개행` 전까지가 인자이고, 리디렉션(`2>/dev/null`)은
  빼며 괄호(`\(`·`\)`)는 인자로 남김
- 인자가 하나도 없는 find(`which find`·`man find`·`rg -n find` 의 인자 자리 단어 포함)는 판정하지 않음
- 시작 경로: 전역 옵션(`-H -L -P -D <값> -O<n>`) 뒤, 첫 식 토큰(`-…`·`(`·`)`·`!`·`,`) 앞까지. 없으면 `.`
  - `~`·`$VAR` 를 펼치고, glob 문자(`* ? [`)가 있으면 그 앞 디렉터리로 줄이며, 상대 경로는 hook 입력 cwd
    기준으로 정규화함(`//`·`/.` 은 `/`)
- 거부: 시작 경로가 `/` 이거나, /proc/self/mounts 의 FUSE·NFS·CIFS 마운트 지점의 엄격한 상위 경로임
  (로컬 FUSE 인 fuse.portal·gvfsd-fuse 도 포함 — 응답 없으면 같은 멈춤이 생김).
  마운트 지점 자체와 그 안쪽은 명시한 대상이라 통과함
- 예외: 같은 find 인자에 `-xdev`·`-mount` 가 있으면 통과(괄호 뒤에 있어도 인정). `-maxdepth` 는 예외가 아님
- 거부는 `permissionDecision: deny` 로만 표현함. allow 는 출력하지 않음
- 입력 해석 실패·예외는 모두 통과(exit 0, 출력 없음) — hook 고장이 작업을 막지 않게 함
- 한계: 같은 명령 안의 `cd / && find .` 처럼 명령 중간에 바뀐 cwd 는 보지 못함. `grep -r … /`·`rg … /`·
  `du /` 는 대상 밖임. 따옴표 없는 인자 위치의 find(`ls /usr/bin/find /`)도 명령으로 보아 거부함.
  `-exec … \;` 의 `;` 뒤에 둔 `-xdev` 는 보지 못함. 펼칠 수 없는 변수는 문자 그대로 경로로 봄.
  명령 치환 경로(`find "$(pwd)"`·`find $(pwd)`)는 판정하지 못해 통과하고, 인자 없는 맨 `find` 도 통과함.
  따옴표 안 `'~'` 도 펼쳐 거부함. glob 은 앞 디렉터리로 줄여 보수적으로 판정함(`~/w*` 도 `~` 로 봄).
  `-xdev` 여도 find 는 마운트 지점 자체를 stat 하므로 응답 없는 마운트에서는 멈출 수 있음 — 사유에 경로
  좁히기를 먼저 안내함
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Collection

import shell_parse

_MOUNTS_FILE = "/proc/self/mounts"
_NETWORK_FSTYPES = frozenset({"nfs", "nfs4", "cifs", "smb3"})
_OCTAL_ESCAPE = re.compile(r"\\([0-7]{3})")  # /proc/self/mounts 경로의 공백 등은 `\040` 로 기록됨
_COMMAND_END = frozenset(";|&\n")
_FLAG_GLOBALS = frozenset({"-H", "-L", "-P"})
_EXPRESSION_START = frozenset({"(", ")", "!", ","})
_NO_CROSS = frozenset({"-xdev", "-mount"})
_GLOB_CHARS = "*?["


def fuse_network_mounts(text: str) -> list[str]:
    """/proc/self/mounts 본문에서 FUSE·NFS·CIFS 마운트 지점 목록(8진 이스케이프는 풂, 깨진 줄은 무시)."""
    points: list[str] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        fstype = fields[2]
        if fstype == "fuse" or fstype.startswith("fuse.") or fstype in _NETWORK_FSTYPES:
            points.append(_OCTAL_ESCAPE.sub(lambda m: chr(int(m.group(1), 8)), fields[1]))
    return points


def _find_args(following: list[str]) -> list[str]:
    """find 뒤 토큰에서 그 명령의 인자 — 명령 끝 전까지, 리디렉션은 빼고 괄호는 남김."""
    args: list[str] = []
    skip_target = False
    for token in following:
        if skip_target:
            skip_target = False
            continue
        if not shell_parse.is_punct(token):
            args.append(token)
        elif token[0] in "<>":
            if args and args[-1].isdigit():
                args.pop()  # `2>/dev/null` 의 파일 디스크립터 번호
            skip_target = True
        elif any(c in _COMMAND_END for c in token):
            break
        else:
            args.append(token)  # `(`·`)` — 식의 일부
    return args


def _start_paths(args: list[str]) -> list[str]:
    """find 인자의 시작 경로(없으면 GNU find 기본값 `.`)."""
    index = 0
    while index < len(args):
        token = args[index]
        if token in _FLAG_GLOBALS or token.startswith("-O"):
            index += 1
        elif token == "-D":
            index += 2
        else:
            break
    paths: list[str] = []
    for token in args[index:]:
        if token.startswith("-") or token in _EXPRESSION_START:
            break
        paths.append(token)
    return paths or ["."]


def _resolve(path: str, cwd: str) -> str:
    """시작 경로를 절대 경로로 — `~`·`$VAR` 펼침, glob 은 앞 디렉터리로 줄임, `//`·`/.`·`..` 정규화."""
    expanded = os.path.expandvars(os.path.expanduser(path))
    glob_at = min((expanded.index(c) for c in _GLOB_CHARS if c in expanded), default=-1)
    if glob_at >= 0:
        prefix = expanded[:glob_at]
        expanded = prefix if prefix.endswith("/") else os.path.dirname(prefix)
    joined = os.path.join(cwd, expanded or ".")
    return "/" + os.path.normpath(joined).lstrip("/")


def _crossed_mount(resolved: str, mounts: Collection[str]) -> str | None:
    """`resolved` 아래에 있는 마운트 지점(엄격한 하위만, 없으면 None)."""
    prefix = resolved.rstrip("/") + "/"
    return next((m for m in mounts if m.startswith(prefix)), None)


def _reason(start: str, resolved: str, mount: str | None) -> str:
    scope = ("/proc·/sys 와 모든 마운트" if resolved == "/"
             else f"FUSE·네트워크 마운트 `{mount}`")
    return (f"`find {start}` 는 {scope}까지 순회해, 끊기거나 응답 없는 sshfs 에서 멈추거나 수 분 걸린다. "
            "찾는 대상이 있는 경로(예: `~/.claude/plugins`, 저장소 루트)로 시작 경로를 좁힌다. "
            "마운트를 건널 필요가 없는 넓은 탐색이면 시작 경로 바로 뒤에 `-xdev` 를 붙인다"
            f"(예: `find {start} -xdev -name …`). 응답 없는 마운트는 -xdev 로도 멈출 수 있어 경로 좁히기가 우선이다.")


def verdict(command: str, cwd: str, mounts: Collection[str]) -> str | None:
    """거부 사유(거부 대상이 아니면 None). `mounts` 는 FUSE·네트워크 마운트 지점 목록."""
    for _, following in shell_parse.find_commands(command, ("find",)):
        args = _find_args(following)
        if not args:
            continue  # `which find`·`man find` 처럼 인자 자리의 find 단어
        if any(token in _NO_CROSS for token in args):
            continue
        for start in _start_paths(args):
            resolved = _resolve(start, cwd)
            mount = None if resolved == "/" else _crossed_mount(resolved, mounts)
            if resolved == "/" or mount:
                return _reason(start, resolved, mount)
    return None


def _read_mounts() -> list[str]:
    try:
        with open(_MOUNTS_FILE, encoding="utf-8", errors="replace") as f:
            return fuse_network_mounts(f.read())
    except OSError:
        return []


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") if isinstance(data, dict) else None
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str):
            return 0
        cwd = data.get("cwd")
        if not isinstance(cwd, str) or not os.path.isabs(cwd):
            cwd = os.getcwd()
        reason = verdict(command, cwd, _read_mounts())
    except Exception:  # noqa: BLE001 — hook 고장이 작업을 막지 않게 모든 예외를 통과시킴(pkill_guard 와 같은 방침)
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
