#!/usr/bin/env python3
"""PreToolUse(Bash) hook — 프로젝트에 .venv 가 있는데 시스템 python 으로 pytest 를 실행하면 거부.

전역 CLAUDE.md 의 "검증은 .venv/bin/python" 규칙(리포트 규칙 C3)을 실행 시점에 강제함.
시스템 python 이나 오염된 PYTHONPATH 는 오류 없이 다른 대상을 측정하므로 사후 검출로는 늦음.

- 대상: `python`·`python3`·`python3.X`(경로에 `venv` 없음) 의 `-m pytest` 와 `pytest` 단독 실행
- 판정 디렉터리: 명령 앞의 `cd <dir> &&` 가 있으면 그 경로, 없으면 hook 입력의 cwd. 그 디렉터리부터
  저장소 루트(.git)까지 `.venv/bin/python` 이 있으면 거부, 없으면(venv 없는 프로젝트) 통과
- 거부는 `permissionDecision: deny` 로만 표현함. allow 는 출력하지 않음
  (출력하면 모든 Bash 의 권한 확인이 사라짐)
- 입력 해석 실패·예외는 모두 통과(exit 0, 출력 없음) — hook 고장이 작업을 막지 않게 함
"""

from __future__ import annotations

import itertools
import json
import os
import re
import shlex
import sys
from pathlib import Path

_PYTHON = re.compile(r"^python(?:3(?:\.\d+)?)?$")
_SEPARATORS = re.compile(r"&&|\|\||;|\|")
_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


_WRAPPERS = {"env": 0, "time": 0, "exec": 0, "nohup": 0, "nice": 0, "stdbuf": 0, "timeout": 1}


def _unwrap(tokens: list[str]) -> list[str]:
    """`VAR=1`·env·time·nohup·nice·timeout <n> 같은 실행 래퍼를 벗겨 실제 명령부터 남김."""
    while tokens:
        if _ENV_ASSIGN.match(tokens[0]):
            tokens = tokens[1:]
            continue
        if tokens[0] not in _WRAPPERS:
            break
        positional = _WRAPPERS[tokens[0]]
        tokens = tokens[1:]
        while tokens and tokens[0].startswith("-") and tokens[0] != "-m":
            takes_value = tokens[0] in ("-u", "--unset", "-n", "-k", "-s", "--signal")
            tokens = tokens[2:] if takes_value else tokens[1:]
        tokens = tokens[positional:]
    return tokens


def _segments(command: str) -> list[list[str]]:
    parts: list[list[str]] = []
    for raw in _SEPARATORS.split(command):
        try:
            tokens = shlex.split(raw.strip().strip("()"))
        except ValueError:
            continue
        tokens = _unwrap(tokens)
        if len(tokens) >= 3 and tokens[0] in ("bash", "sh") and tokens[1] == "-c":
            parts.extend(_segments(tokens[2]))  # bash -c '<명령>' 안쪽도 판정
        elif tokens:
            parts.append(tokens)
    return parts


def _system_pytest(tokens: list[str]) -> bool:
    exe = tokens[0]
    if "venv" in exe:
        return False
    if os.path.basename(exe) == "pytest":
        return True
    return bool(_PYTHON.match(os.path.basename(exe))) and any(
        a == "-m" and b == "pytest" for a, b in itertools.pairwise(tokens))


def _venv_dir(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        if (directory / ".venv" / "bin" / "python").exists():
            return directory
        if (directory / ".git").exists():
            return None
    return None


def verdict(command: str, cwd: str) -> str | None:
    """거부 사유(거부 대상이 아니면 None)."""
    workdir = Path(cwd or ".")
    for tokens in _segments(command):
        if tokens[0] in ("source", ".") and len(tokens) > 1 and tokens[1].endswith("bin/activate"):
            return None  # venv 를 활성화한 뒤의 python·pytest 는 venv 것
        if tokens[0] == "cd" and len(tokens) > 1:
            target = Path(os.path.expanduser(tokens[1]))
            workdir = target if target.is_absolute() else workdir / target
            continue
        if _system_pytest(tokens):
            venv = _venv_dir(workdir.resolve())
            if venv is not None:
                return (f"이 프로젝트에는 {venv}/.venv 가 있어 시스템 python 으로 "
                        "pytest 를 실행하지 않는다. "
                        f"`{venv}/.venv/bin/python -m pytest ...` 로 다시 실행한다 "
                        "(시스템 python 은 오류 없이 다른 대상을 측정함).")
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") if isinstance(data, dict) else None
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str):
            return 0
        reason = verdict(command, str(data.get("cwd") or os.getcwd()))
    except Exception:
        return 0
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
