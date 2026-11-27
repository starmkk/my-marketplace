"""Bash hook 공용 셸 명령 위치 탐색 — 명령 문자열에서 지정한 이름의 명령과 그 뒤 토큰을 찾음.

- 토큰화: shlex(posix, punctuation_chars) — `; | & ( ) < >`·개행은 구분자 토큰이 됨. 따옴표 없는
  `\\(`·`\\)`·`\\;` 도 같은 구분자 토큰이 되므로, 인자가 어디서 끝나는지는 호출하는 guard 가 정함
- 탐색: basename 이 대상 이름인 토큰을 위치와 무관하게 찾음(`sudo`·`xargs`·`timeout`·파이프 뒤·
  따옴표 없는 `$(...)` 포함). 따옴표 안의 `$(...)`·백틱과 `bash -c '<명령>'` 안쪽은 재귀로 찾음
- 토큰화 실패(닫히지 않은 따옴표 등)는 그 문자열에서 찾은 명령이 없는 것으로 봄
"""

from __future__ import annotations

import os
import shlex
from collections.abc import Collection

PUNCT = "();<>|&\n"
_SHELLS = ("bash", "sh", "zsh")


def tokenize(command: str) -> list[str]:
    """명령 문자열을 셸 토큰으로 나눔(구분자는 별도 토큰). 닫히지 않은 따옴표는 ValueError."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=PUNCT)
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def is_punct(token: str) -> bool:
    """구분자 토큰(`;`·`|`·`&&`·`(`·`>` 등) 여부."""
    return all(c in PUNCT for c in token)


def _split_backticks(tokens: list[str]) -> list[str]:
    """따옴표 없는 백틱(공백 없는 토큰에 붙은 것)을 `;` 구분자로 펼침. 공백이 든 토큰은 그대로 둠."""
    expanded: list[str] = []
    for token in tokens:
        if "`" not in token or any(c.isspace() for c in token):
            expanded.append(token)
            continue
        for part_index, part in enumerate(token.split("`")):
            if part_index:
                expanded.append(";")
            if part:
                expanded.append(part)
    return expanded


def _substitution_body(token: str) -> str:
    """따옴표 안에 든 `$(...)`·백틱 명령 치환의 안쪽 문자열(없으면 빈 문자열)."""
    if "$(" in token:
        return token.split("$(", 1)[1]
    if "`" in token:
        return token.split("`", 1)[1].replace("`", " ")
    return ""


def _shell_c_body(following: list[str]) -> str:
    """`bash -c '<명령>'`·`bash -lc '<명령>'` 의 명령 문자열(없으면 빈 문자열)."""
    for offset, option in enumerate(following):
        if option.startswith("-") and not option.startswith("--") and "c" in option[1:]:
            return following[offset + 1] if offset + 1 < len(following) else ""
    return ""


def find_commands(command: str, names: Collection[str]) -> list[tuple[str, list[str]]]:
    """(명령 이름, 그 뒤 토큰 전체) 목록 — 뒤 토큰 중 어디까지가 인자인지는 호출 쪽이 정함."""
    try:
        tokens = _split_backticks(tokenize(command))
    except ValueError:
        return []
    found: list[tuple[str, list[str]]] = []
    for index, token in enumerate(tokens):
        name = os.path.basename(token)
        substitution = _substitution_body(token)
        if substitution:
            found.extend(find_commands(substitution, names))
            continue
        if name in _SHELLS:
            inner = _shell_c_body(tokens[index + 1:index + 5])
            if inner:
                found.extend(find_commands(inner, names))
            continue
        if name in names:
            found.append((name, tokens[index + 1:]))
    return found
