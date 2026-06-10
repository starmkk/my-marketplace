"""
mnn 환경변수 게이트 (레거시 호환).
MNN_SOURCE_PATH 요구사항이 제거되었습니다.
소스코드는 ~/.claude/repo/MNN@<version>에서 관리됩니다.
스크립트 사용 시 --mnn-source 인자로 MNN 소스 경로를 전달하세요.
"""

from __future__ import annotations


def ensure_mnn_env() -> dict[str, str]:
    """호환성 유지를 위해 남겨둔 함수. 빈 dict를 반환합니다."""
    return {}
