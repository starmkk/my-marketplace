"""
gemma4 환경변수 게이트 (레거시 호환).
GEMMA4_MODEL_PATH 요구사항이 제거되었습니다.
모델은 ~/.claude/repo/gemma-4-<variant> 경로에서 관리됩니다.
"""

from __future__ import annotations


def ensure_gemma4_env() -> dict[str, str]:
    """호환성 유지를 위해 남겨둔 함수. 빈 dict를 반환합니다."""
    return {}
