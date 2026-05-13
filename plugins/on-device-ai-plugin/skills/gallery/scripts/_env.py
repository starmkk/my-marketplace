"""
gallery 환경변수 검증 게이트.

GALLERY_SOURCE_PATH가 설정되어 있으면 경로를 검증한다.
미설정 시에는 경고만 출력하고 계속 진행한다 (레퍼런스 전용 사용 가능).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


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


def ensure_gallery_env() -> dict[str, str]:
    """
    GALLERY_SOURCE_PATH 환경변수 검증.
    - 미설정 시: 안내 메시지 출력 후 빈 dict 반환 (레퍼런스 스킬로만 사용)
    - 설정됐지만 경로 없음: 안내 메시지 출력 후 sys.exit(2)
    - 통과 시: {"GALLERY_SOURCE_PATH": 절대경로} 반환
    """
    raw = os.environ.get("GALLERY_SOURCE_PATH", "").strip()
    rc_path, shell_name = _detect_login_rc()

    if not raw:
        print("", file=sys.stderr)
        print("[gallery] GALLERY_SOURCE_PATH 미설정 — 로컬 소스 없이 레퍼런스 스킬로 사용합니다.", file=sys.stderr)
        print("  로컬 클론이 있다면 아래 명령으로 등록하세요:", file=sys.stderr)
        if shell_name == "fish":
            print("  set -Ux GALLERY_SOURCE_PATH /path/to/google-ai-edge-gallery", file=sys.stderr)
        else:
            print(f"  echo 'export GALLERY_SOURCE_PATH=/path/to/google-ai-edge-gallery' >> {rc_path}", file=sys.stderr)
            print(f"  source {rc_path}", file=sys.stderr)
        print("", file=sys.stderr)
        return {}

    path = Path(os.path.expanduser(raw)).resolve()
    bar = "=" * 70

    if not path.exists() or not path.is_dir():
        reason = "경로 없음" if not path.exists() else "디렉토리가 아님"
        print("", file=sys.stderr)
        print(bar, file=sys.stderr)
        print("[gallery] GALLERY_SOURCE_PATH 경로 오류로 실행을 중단합니다.", file=sys.stderr)
        print(bar, file=sys.stderr)
        print("", file=sys.stderr)
        print(f"[오류]  GALLERY_SOURCE_PATH={raw}", file=sys.stderr)
        print(f"        {reason}: {path}", file=sys.stderr)
        print("", file=sys.stderr)
        print(f"[설정 방법] (감지된 셸: {shell_name}, 권장 rc 파일: {rc_path})", file=sys.stderr)
        print("", file=sys.stderr)
        if shell_name == "fish":
            print("  set -Ux GALLERY_SOURCE_PATH /path/to/google-ai-edge-gallery", file=sys.stderr)
        else:
            print(f"  echo 'export GALLERY_SOURCE_PATH=/path/to/google-ai-edge-gallery' >> {rc_path}", file=sys.stderr)
            print(f"  source {rc_path}", file=sys.stderr)
        print("", file=sys.stderr)
        print("환경변수 수정 후 동일 명령을 다시 실행해 주세요.", file=sys.stderr)
        print(bar, file=sys.stderr)
        print("", file=sys.stderr)
        sys.exit(2)

    resolved = str(path)
    os.environ["GALLERY_SOURCE_PATH"] = resolved
    return {"GALLERY_SOURCE_PATH": resolved}
