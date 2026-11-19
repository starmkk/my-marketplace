#!/usr/bin/env python3
"""PreToolUse(Agent|Task) hook — `subagent_type` 없이 서브에이전트를 띄우면 거부, `name` 이면 수명 안내.

누락하면 general-purpose 로 떠서 모든 도구 정의·스킬 목록을 싣고 시작함(첫 요청 ~47k 토큰).
경량 에이전트(wf-worker·wf-reader, ~10k~17k)로 충분한 위임이 대부분이라 타입 명시를 강제함.

- 거부 대상: `tool_input.subagent_type` 이 없음·null·공백뿐인 문자열
- 통과: 그 밖의 값(비어 있지 않은 문자열, 문자열 아닌 값) — 어떤 타입인지는 판정하지 않음
- 거부는 `permissionDecision: deny` 로만 표현함. allow 는 출력하지 않음
  (출력하면 모든 Agent 호출의 권한 확인이 사라짐)
- 거부 대상이 아니고 agent teams 가 켜져 있으며(`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` = 1·true·yes·on)
  `name` 이 공백 아닌 문자열이면 `hookSpecificOutput.additionalContext`(모델 전용) 하나만 출력함 —
  permissionDecision·systemMessage 없음(권한 흐름 무변경). 이름 붙인 팀원은 보고 뒤에도 끝나지
  않고 대기하므로 띄우는 순간 수명·재사용 사실을 알림(2026-11-19 실측 — subagent-delegation
  "Agent lifecycle"). 팀 기능이 꺼진 곳에서는 사실이 아니므로 출력하지 않음
- `tool_name` 이 Agent·Task 가 아니면 통과(TaskUpdate 등 — matcher 가 넓게 걸려도 안전)
- 입력 해석 실패(깨진 JSON·stdin 없음·dict 아님)와 main 에 나열한 예외는 통과(exit 0, 출력 없음).
  나열 밖 예외도 exit 1 이라 차단하지 않음(PreToolUse 는 exit 2 만 차단) — fail-open
"""

from __future__ import annotations

import json
import os
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


def verdict(tool_input: dict[str, object]) -> str | None:
    """거부 사유(거부 대상이 아니면 None)."""
    agent_type = tool_input.get("subagent_type")
    if agent_type is None or (isinstance(agent_type, str) and not agent_type.strip()):
        return _REASON
    return None


def teams_enabled(value: str | None) -> bool:
    """`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 값이 켜짐인지 — CLI 와 같은 집합(1·true·yes·on).

    `--agent-teams` 플래그로만 켠 경우는 env 가 없어 안내가 빠진다(빠져도 해 없음).
    """
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def name_notice(tool_input: dict[str, object], teams_on: bool) -> str | None:
    """`name` 을 준 호출의 팀원 수명 안내(대상이 아니면 None). 모델용이라 사실 서술로 씀."""
    name = tool_input.get("name")
    if not teams_on or not isinstance(name, str) or not name.strip():
        return None
    return (
        f"name '{name}' 을 준 Agent 는 agent teams 팀원으로 뜬다. 팀원은 보고 뒤에도 끝나지 않고 "
        "대기한다(대기 중 요청·토큰 0, 프로세스·메모리 유지, ListAgents 에 실행 중으로 보임). "
        "대기 중에는 SendMessage(to: 이름)로 맥락을 유지한 채 다시 쓸 수 있고, teammateMode 가 "
        "tmux 이면 TaskStop 뒤 그 이름으로 재개되지 않는다. name 없이 띄운 에이전트는 보고 뒤 "
        "끝나고 SendMessage(to: 생성 결과의 agentId)로 전체 기록을 가진 채 재개된다. 이 세션에서 "
        f'더 쓰지 않을 팀원은 TaskStop({{task_id: "{name}"}}) 으로 끝낸다 '
        "(workflow-policy-plugin subagent-delegation 'Agent lifecycle')."
    )


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
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": reason,
                        }
                    }
                )
            )
            return 0
        teams_on = teams_enabled(os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"))
        notice = name_notice(tool_input, teams_on)
        if notice:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": notice,
                        }
                    }
                )
            )
    # fail-open: 깨진 JSON·인코딩(ValueError), stdin 없음(AttributeError), 예상 밖 구조
    # (TypeError·LookupError), 입출력·파이프(OSError), 깊은 중첩(RecursionError) 은 통과
    except (
        ValueError,
        TypeError,
        AttributeError,
        LookupError,
        OSError,
        RecursionError,
    ):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
