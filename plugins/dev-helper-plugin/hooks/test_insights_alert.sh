#!/usr/bin/env bash
# insights_alert.py 시나리오 테스트 — 알림 없음·활성·해소·깨진 파일
set -uo pipefail
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/insights_alert.py"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
mkdir -p "${tmp}/reports/state"
pass=0
fail=0
check() {  # 이름 기대(empty|contains:<문구>) alerts-json
  local name="$1" expect="$2" json="$3" out
  printf '%s' "${json}" > "${tmp}/reports/state/alerts.json"
  out="$(CLAUDE_INSIGHTS_DIR="${tmp}" HOME="${tmp}/nohome" python3 "${HOOK}")"
  local rc=$?
  if [[ "${rc}" -ne 0 ]]; then echo "FAIL ${name}: rc=${rc}"; fail=$((fail + 1)); return; fi
  if [[ "${expect}" == "empty" ]]; then
    if [[ -z "${out}" ]]; then pass=$((pass + 1)); else echo "FAIL ${name}: ${out}"; fail=$((fail + 1)); fi
  elif [[ "${out}" == *"${expect#contains:}"* && "${out}" == *systemMessage* ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${name}: ${out}"; fail=$((fail + 1))
  fi
}
check "알림 없음" empty '{}'
check "해소된 알림" empty '{"host|relogin": {"active": false, "resolved_at": "2026-11-17T06:00"}}'
check "재로그인 필요" "contains:재로그인 필요 — voiceguard" \
  '{"voiceguard|relogin": {"active": true, "since": "2026-11-17T06:20:00+09:00", "detail": "x"}}'
check "호스트 표기" "contains:호스트" '{"host|expiring": {"active": true, "since": "2026-11-17"}}'
check "환경 동기화" "contains:환경 동기화 확인 필요 — 호스트↔voiceguard" \
  '{"env|env_sync": {"active": true, "since": "2026-11-17"}}'
check "인증 확인 실패" "contains:인증 상태 확인 실패 — 호스트 (since 2026-11-27T18:52): 다음 정기 점검에서 자동 재확인" \
  '{"host|check_failed": {"active": true, "since": "2026-11-27T18:52:00+09:00", "detail": "x"}}'
check "깨진 파일" empty '{broken'
check "객체 아닌 JSON" empty '[]'
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
