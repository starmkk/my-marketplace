"""
qwen 환경변수 게이트 (레거시 호환).
QWEN25_OMNI_MODEL_PATH 요구사항이 제거되었습니다.
소스코드는 ~/.claude/repo/<RepoName>@<version>에서 관리됩니다.
"""

from __future__ import annotations


def ensure_qwen_env() -> dict[str, str]:
    """호환성 유지를 위해 남겨둔 함수. 빈 dict를 반환합니다."""
    return {}


# 이전 이름 호환성 유지
ensure_qwen25_omni_env = ensure_qwen_env
