"""
gemma4-asr-qa 환경변수 검증 게이트.

본 모듈을 import한 entrypoint 스크립트는 main() 진입 직후
ensure_gemma4_env()를 호출해야 한다.
필수 환경변수가 누락되었거나 잘못된 경로를 가리키면 친절한 안내
메시지를 stderr로 출력한 뒤 sys.exit(2)로 즉시 중단된다.
"""

from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path
from typing import Iterable, NamedTuple


class EnvVarSpec(NamedTuple):
    name: str
    description: str
    must_exist: bool   # True면 디렉토리/파일 존재까지 검증
    is_dir: bool       # True면 디렉토리, False면 파일
    example: str       # 사용자에게 보여줄 export 예시 값


# ---------- 환경변수 정의 ----------

REQUIRED_VARS: tuple[EnvVarSpec, ...] = (
    EnvVarSpec(
        name="GEMMA4_MODEL_PATH",
        description="Gemma 4 E2B-it 모델 디렉토리 절대경로",
        must_exist=True,
        is_dir=True,
        example="/absolute/path/to/gemma-4-E2B-it",
    ),
)


# ---------- 검증 ----------

def _detect_login_rc() -> tuple[str, str]:
    """현재 SHELL 환경변수에서 rc 파일 경로 추정. (rc_path_display, shell_name)"""
    shell = os.environ.get("SHELL", "")
    home = str(Path.home())
    if shell.endswith("zsh"):
        return f"{home}/.zshrc", "zsh"
    if shell.endswith("bash"):
        return f"{home}/.bashrc", "bash"
    if shell.endswith("fish"):
        return f"{home}/.config/fish/config.fish", "fish"
    return f"{home}/.zshrc", "zsh"


def _format_export_lines(missing: Iterable[EnvVarSpec], shell_name: str) -> list[str]:
    lines: list[str] = []
    for spec in missing:
        val = shlex.quote(spec.example)
        if shell_name == "fish":
            lines.append(f"set -Ux {spec.name} {val}")
        else:
            lines.append(f"export {spec.name}={val}")
    return lines


def _print_setup_guide(missing: list[EnvVarSpec], invalid: list[tuple[EnvVarSpec, str, str]]) -> None:
    """누락/잘못된 환경변수에 대해 ~/.zshrc 추가 가이드 출력."""
    rc_path, shell_name = _detect_login_rc()
    bar = "=" * 70

    print("", file=sys.stderr)
    print(bar, file=sys.stderr)
    print("[gemma4-asr-qa] 환경변수가 올바르게 설정되지 않아 실행을 중단합니다.", file=sys.stderr)
    print(bar, file=sys.stderr)

    if missing:
        print("", file=sys.stderr)
        print("[누락된 환경변수]", file=sys.stderr)
        for spec in missing:
            req = "필수" if spec.must_exist else "선택"
            print(f"  - {spec.name}  ({req})", file=sys.stderr)
            print(f"      {spec.description}", file=sys.stderr)

    if invalid:
        print("", file=sys.stderr)
        print("[경로가 존재하지 않는 환경변수]", file=sys.stderr)
        for spec, value, reason in invalid:
            print(f"  - {spec.name}={value}", file=sys.stderr)
            print(f"      이유: {reason}", file=sys.stderr)

    print("", file=sys.stderr)
    print(f"[설정 방법] (감지된 셸: {shell_name}, 권장 rc 파일: {rc_path})", file=sys.stderr)
    print("", file=sys.stderr)

    targets = list(missing) + [spec for spec, _, _ in invalid]
    if not targets:
        targets = list(REQUIRED_VARS)

    for line in _format_export_lines(targets, shell_name):
        if shell_name == "fish":
            print(f"  {line}", file=sys.stderr)
        else:
            print(f"  echo '{line}' >> {rc_path}", file=sys.stderr)

    print("", file=sys.stderr)
    if shell_name == "fish":
        print("  # set -Ux는 즉시 영구 반영됩니다.", file=sys.stderr)
    else:
        print(f"  source {rc_path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("환경변수 설정 후 동일 명령을 다시 실행해 주세요.", file=sys.stderr)
    print(bar, file=sys.stderr)
    print("", file=sys.stderr)


def ensure_gemma4_env(extra: tuple[EnvVarSpec, ...] = ()) -> dict[str, str]:
    """
    필수 환경변수 검증 게이트.
    - 누락이거나 must_exist=True인데 경로가 없으면 안내 후 sys.exit(2).
    - 통과 시 변수명→값 dict 반환.
    """
    specs = REQUIRED_VARS + extra
    missing: list[EnvVarSpec] = []
    invalid: list[tuple[EnvVarSpec, str, str]] = []
    resolved: dict[str, str] = {}

    for spec in specs:
        raw = os.environ.get(spec.name, "").strip()
        if not raw:
            missing.append(spec)
            continue

        path = Path(os.path.expanduser(raw)).resolve()
        if spec.must_exist:
            if not path.exists():
                invalid.append((spec, raw, f"경로 없음: {path}"))
                continue
            if spec.is_dir and not path.is_dir():
                invalid.append((spec, raw, f"디렉토리가 아님: {path}"))
                continue
            if (not spec.is_dir) and not path.is_file():
                invalid.append((spec, raw, f"파일이 아님: {path}"))
                continue
        resolved[spec.name] = str(path)

    if missing or invalid:
        _print_setup_guide(missing, invalid)
        sys.exit(2)

    # 검증 통과한 값을 환경변수에 다시 반영(절대경로 정규화 결과)
    for k, v in resolved.items():
        os.environ[k] = v

    return resolved
