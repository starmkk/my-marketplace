#!/usr/bin/env bash
# agent_type_guard.py 시나리오 테스트 — subagent_type 누락·null·공백 거부, 명시 값 통과, 깨진 입력
set -euo pipefail
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agent_type_guard.py"
export PYTHONDONTWRITEBYTECODE=1
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
judge() {  # 설명 기대(deny|pass) rc 출력 → 집계
  local desc="$1" expect="$2" rc="$3" out="$4" ok=1
  # 통과는 출력이 전혀 없어야 함(allow 를 내면 Agent 권한 확인이 사라짐)
  if [[ "${rc}" -ne 0 ]]; then
    ok=0
  elif [[ "${expect}" == "deny" ]]; then
    is_deny_json "${out}" || ok=0
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
check() {  # 설명 입력(JSON 원문) 기대(deny|pass) [PYTHONIOENCODING]
  local desc="$1" input="$2" expect="$3" enc="${4:-}" out rc=0
  out="$(printf '%s' "${input}" | PYTHONIOENCODING="${enc}" python3 "${HOOK}" 2>/dev/null)" ||
    rc=$?
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
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
