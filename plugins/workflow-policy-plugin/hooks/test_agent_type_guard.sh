#!/usr/bin/env bash
# agent_type_guard.py 시나리오 테스트 — subagent_type 누락·null·공백 거부, 명시 값 통과, 깨진 입력,
# name 안내(agent teams 켜짐에서만 additionalContext — G15~G20)
set -euo pipefail
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agent_type_guard.py"
export PYTHONDONTWRITEBYTECODE=1
unset CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS   # 사용자 환경 격리 — 케이스마다 TEAMS 로 지정
TEAMS=""
pass=0
fail=0
is_deny_json() {  # 출력(JSON 원문) → deny 응답 형식이면 0
  python3 -c '
import json, sys
out = json.loads(sys.argv[1])["hookSpecificOutput"]
ok = (out["hookEventName"] == "PreToolUse" and out["permissionDecision"] == "deny"
      and isinstance(out["permissionDecisionReason"], str)
      and out["permissionDecisionReason"].strip())
sys.exit(0 if ok else 1)' "$1" 2>/dev/null
}
# 출력 → 안내 전용 형식(키가 정확히 hookSpecificOutput{hookEventName, additionalContext})이면 0
is_context_json() {
  python3 -c '
import json, sys
data = json.loads(sys.argv[1])
out = data["hookSpecificOutput"]
ok = (set(data) == {"hookSpecificOutput"}
      and set(out) == {"hookEventName", "additionalContext"}
      and out["hookEventName"] == "PreToolUse"
      and isinstance(out["additionalContext"], str) and out["additionalContext"].strip())
sys.exit(0 if ok else 1)' "$1" 2>/dev/null
}
judge() {  # 설명 기대(deny|pass) rc 출력 → 집계
  local desc="$1" expect="$2" rc="$3" out="$4" ok=1
  # 통과는 출력이 전혀 없어야 함(allow 를 내면 Agent 권한 확인이 사라짐)
  if [[ "${rc}" -ne 0 ]]; then
    ok=0
  elif [[ "${expect}" == "deny" ]]; then
    is_deny_json "${out}" || ok=0
    # 거부 응답에 안내가 섞이지 않음(거부가 우선)
    [[ "${out}" != *additionalContext* ]] || ok=0
  elif [[ "${expect}" == "context" ]]; then
    # 허용·거부 결정 없이 안내만(permissionDecision 이 생기면 Agent 권한 확인이 사라짐)
    is_context_json "${out}" || ok=0
  elif [[ -n "${out}" ]]; then
    ok=0
  fi
  if [[ "${ok}" -eq 1 ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${desc}: expect=${expect} rc=${rc} out=${out}"
    fail=$((fail + 1))
  fi
}
check() {  # 설명 입력(JSON 원문) 기대(deny|pass|context) [PYTHONIOENCODING] — 팀 기능 값은 TEAMS
  local desc="$1" input="$2" expect="$3" enc="${4:-}" out rc=0
  out="$(printf '%s' "${input}" | CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="${TEAMS}" \
    PYTHONIOENCODING="${enc}" python3 "${HOOK}" 2>/dev/null)" || rc=$?
  judge "${desc}" "${expect}" "${rc}" "${out}"
}
agent() {  # tool_name tool_input(JSON 원문) → hook 입력
  printf '{"tool_name": "%s", "tool_input": %s}' "$1" "$2"
}
check "G1 subagent_type 누락" "$(agent Agent '{"prompt": "p"}')" deny
check "G2 빈 문자열" "$(agent Agent '{"prompt": "p", "subagent_type": ""}')" deny
check "G3 공백뿐" "$(agent Agent '{"prompt": "p", "subagent_type": "  "}')" deny
check "G10 null" "$(agent Agent '{"prompt": "p", "subagent_type": null}')" deny
check "G4 general-purpose 명시" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "general-purpose"}')" pass
check "G6 fork 명시" "$(agent Agent '{"prompt": "p", "subagent_type": "fork"}')" pass
check "G7 tool_name Task 누락" "$(agent Task '{"prompt": "p"}')" deny
check "G8 깨진 JSON" '{broken' pass
check "G9 tool_input 이 dict 아님" "$(agent Agent '"text"')" pass
# G11 은 목록 밖 추가 — R5 의 "문자열 아닌 값은 통과" 규칙을 고정함
check "G11 문자열 아닌 값" "$(agent Agent '{"prompt": "p", "subagent_type": 7}')" pass
# G12~G14 는 목록 밖 추가(검토 반영) — 출력 인코딩·stdin 없음·대상 밖 도구에서의 동작을 고정함
check "G12 ascii 출력 인코딩에서 누락" "$(agent Agent '{"prompt": "p"}')" deny ascii
check "G14 대상 밖 도구(TaskUpdate) 누락" "$(agent TaskUpdate '{"taskId": "1"}')" pass
g13_rc=0
g13_out="$(python3 "${HOOK}" 2>/dev/null <&-)" || g13_rc=$?
judge "G13 stdin 닫힘(sys.stdin None)" pass "${g13_rc}" "${g13_out}"
# G15~G20 — name 안내(사용자 결정 2026-11-19): 팀 기능 켜짐 + name 이 공백 아닌 문자열일 때만 안내
TEAMS=1
check "G15 name·타입 있음·팀 켜짐 → 안내" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" context
# G15 보강 — 안내에 그 이름의 종료 방법이 들어 있음(문구에서 이름을 빼는 돌연변이 방지)
g15_out="$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}' |
  CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 python3 "${HOOK}" 2>/dev/null)"
if python3 -c '
import json, sys
ctx = json.loads(sys.argv[1])["hookSpecificOutput"]["additionalContext"]
sys.exit(0 if "TaskStop({task_id: \"rev\"})" in ctx else 1)' "${g15_out}" 2>/dev/null; then
  pass=$((pass + 1))
else
  echo "FAIL G15 보강: 안내에 TaskStop({task_id: \"rev\"}) 없음: ${g15_out}"
  fail=$((fail + 1))
fi
check "G16 name 공백·팀 켜짐 → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "  "}')" pass
check "G17 name 있음·타입 누락 → 거부만" "$(agent Agent '{"prompt": "p", "name": "rev"}')" deny
check "G18 name 이 문자열 아님 → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": 7}')" pass
TEAMS=""
check "G19 팀 꺼짐(빈 값) → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" pass
TEAMS=0
check "G20 팀 값 0 → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" pass
# G21~G23 (추가) — 이유: CLI 의 켜짐 판정이 {1,true,yes,on}(반대 검토 — 바이너리) 이라 같은 집합으로 고정
TEAMS=" On "
check "G21 팀 값 ' On '(공백·대소문자) → 안내" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" context
TEAMS=false
check "G22 팀 값 false → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" pass
TEAMS=2
check "G23 팀 값 2(켜짐 집합 밖) → 출력 없음" \
  "$(agent Agent '{"prompt": "p", "subagent_type": "x", "name": "rev"}')" pass
TEAMS=""
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
