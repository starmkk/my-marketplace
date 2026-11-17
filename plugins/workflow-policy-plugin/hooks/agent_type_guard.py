#!/usr/bin/env python3
"""PreToolUse(Agent|Task) hook — `subagent_type` 없이 서브에이전트를 띄우면 거부.

누락하면 general-purpose 로 떠서 모든 도구 정의·스킬 목록을 싣고 시작함(첫 요청 ~47k 토큰).
경량 에이전트(wf-worker·wf-reader, ~10k~17k)로 충분한 위임이 대부분이라 타입 명시를 강제함.

- 거부 대상: `tool_input.subagent_type` 이 없음·null·공백뿐인 문자열
- 통과: 그 밖의 값(비어 있지 않은 문자열, 문자열 아닌 값) — 어떤 타입인지는 판정하지 않음
- 거부는 `permissionDecision: deny` 로만 표현함. allow 는 출력하지 않음
  (출력하면 모든 Agent 호출의 권한 확인이 사라짐)
- `tool_name` 이 Agent·Task 가 아니면 통과(TaskUpdate 등 — matcher 가 넓게 걸려도 안전)
- 입력 해석 실패(깨진 JSON·stdin 없음·dict 아님)와 main 에 나열한 예외는 통과(exit 0, 출력 없음).
  나열 밖 예외도 exit 1 이라 차단하지 않음(PreToolUse 는 exit 2 만 차단) — fail-open
"""

from __future__ import annotations

import json
import sys

_TARGET_TOOLS = frozenset({"Agent", "Task"})
_REASON = (
    "subagent_type 을 명시해 다시 호출한다(누락 = general-purpose, 첫 요청 ~47k 토큰; "
    "wf-* 는 ~10k~17k). "
    "편집·실행 = `workflow-policy-plugin:wf-worker` / "
    "읽기·검토·검증·위치 찾기 = `workflow-policy-plugin:wf-reader` / "
    "URL = `web-fetch` / 규칙이 핵심인 작업 = 해당 전문 에이전트 / "
    "`general-purpose` 는 MCP·WebSearch·Skill 도구가 꼭 필요할 때만 명시 / "
    "대화 상속이 필요하면 `fork`."
)


def verdict(tool_input: dict) -> str | None:
    """거부 사유(거부 대상이 아니면 None)."""
    agent_type = tool_input.get("subagent_type")
    if agent_type is None or (isinstance(agent_type, str) and not agent_type.strip()):
        return _REASON
    return None


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict) or data.get("tool_name") not in _TARGET_TOOLS:
            return 0
        tool_input = data.get("tool_input")
        if not isinstance(tool_input, dict):
            return 0
        reason = verdict(tool_input)
        if reason:
            # ensure_ascii 기본값(True) — 출력 인코딩이 ascii 여도 깨지지 않게 함
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                     "permissionDecision": "deny",
                                                     "permissionDecisionReason": reason}}))
    # fail-open: 깨진 JSON·인코딩(ValueError), stdin 없음(AttributeError), 예상 밖 구조
    # (TypeError·LookupError), 입출력·파이프(OSError), 깊은 중첩(RecursionError) 은 통과
    except (ValueError, TypeError, AttributeError, LookupError, OSError, RecursionError):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
