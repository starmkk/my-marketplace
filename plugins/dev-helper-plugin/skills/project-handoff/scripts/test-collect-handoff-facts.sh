#!/usr/bin/env bash
# collect-handoff-facts.sh 동작 검증 — 임시 git 저장소에서 시나리오별 출력·종료 코드를 단언.
# 핵심 계약
#   - 한 번 실행으로 오늘 날짜·파일명 접두, §1 스냅샷, 미커밋 변경, 최근 handoff 5개를 출력
#   - AppleDouble(._*) 은 미커밋 목록·handoff 목록에서 제외
#   - 어느 하위 디렉터리에서 실행해도 repo 루트 기준으로 같은 결과
#
# 케이스 목록(고정)
#   C1 깨끗한 repo → 날짜·HEAD·"미커밋 없음"
#   C2 수정·추적 안 함 파일(+ 추적 안 하는 ._x) → 목록, ._x 제외
#   C3 handoff 이름 역순 정렬·최대 5개·legacy 디렉터리 포함
#      (._* 단언 없음 — bash glob '*' 가 점 파일을 원래 제외해 단언이 공허함)
#   C4 git 저장소 아님 → exit 1
#   C5 sibling 인자 → 다중 repo 표
#   C6 하위 디렉터리에서 실행 → 루트에서와 같은 결과
#   C7 docs/handoffs 없음 → "없음" 출력, 0
#   C8 하위 디렉터리에서 상대 sibling 경로 → 다중 repo 표
#   C9 이름 중간에 ' ._' 가 든 일반 파일 → 미커밋 목록에 남음
#
# 사용: bash test-collect-handoff-facts.sh   (모두 통과 시 exit 0)

set -uo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1   # 사용자 전역 git 설정 격리

SCRIPT="$(cd "$(dirname "$0")" && pwd)/collect-handoff-facts.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
TODAY="$(date +%Y-%m-%d)"
fail=0
out=""
rc=0

pass() { echo "PASS  $1"; }
flunk() { echo "FAIL  $1"; printf '%s\n' "$out" | sed 's/^/      | /'; fail=1; }

new_repo() {
  local d="$WORK/$1"
  mkdir -p "$d/src"
  git -C "$d" init -q
  git -C "$d" config user.name tester
  git -C "$d" config user.email tester@example.com
  echo a > "$d/src/a.txt"
  git -C "$d" add -A && git -C "$d" commit -q -m "init $1"
  echo "$d"
}
# run <실행 디렉터리> [인자...] → out, rc
run() {
  local d="$1"; shift
  out="$(cd "$d" && bash "$SCRIPT" "$@" 2>&1)"
  rc=$?
}
# line_no <고정 문자열> → out 에서 처음 나온 줄 번호(없으면 0)
line_no() { printf '%s\n' "$out" | grep -nF -- "$1" | head -1 | cut -d: -f1 | grep . || echo 0; }

# C1
r="$(new_repo c1)"; h="$(git -C "$r" rev-parse --short HEAD)"
run "$r"
if [[ "$rc" -eq 0 && "$out" == *"$TODAY"* && "$out" == *"docs/handoffs/$TODAY-"* \
  && "$out" == *"\`$h\`"* && "$out" == *"미커밋 없음"* ]]; then pass "C1 깨끗한 repo"
else flunk "C1 깨끗한 repo"; fi

# C7 (C1 저장소 — docs/handoffs 없음)
if [[ "$rc" -eq 0 && "$out" == *"최근 handoff"*"없음"* ]]; then pass "C7 docs/handoffs 없음"
else flunk "C7 docs/handoffs 없음"; fi

# C2
r="$(new_repo c2)"
echo b >> "$r/src/a.txt"; echo n > "$r/new.txt"; echo x > "$r/._x"; echo y > "$r/src/._y"
run "$r"
if [[ "$rc" -eq 0 && "$out" == *" M src/a.txt"* && "$out" == *"?? new.txt"* \
  && "$out" != *"._x"* && "$out" != *"._y"* && "$out" != *"미커밋 없음"* ]]; then
  pass "C2 미커밋 목록·._* 제외"
else flunk "C2 미커밋 목록·._* 제외"; fi

# C3
r="$(new_repo c3)"
mkdir -p "$r/docs/handoffs" "$r/docs/superpowers/handoffs"
for n in 2026-01-01-a 2026-03-01-c 2026-04-01-d 2026-05-01-e 2026-06-01-f; do
  echo x > "$r/docs/handoffs/$n-handoff.md"
done
echo x > "$r/docs/superpowers/handoffs/2026-02-01-b-handoff.md"
run "$r"
n_f="$(line_no 'docs/handoffs/2026-06-01-f-handoff.md')"
n_c="$(line_no 'docs/handoffs/2026-03-01-c-handoff.md')"
n_b="$(line_no 'docs/superpowers/handoffs/2026-02-01-b-handoff.md')"
if [[ "$rc" -eq 0 && "$n_f" -gt 0 && "$n_f" -lt "$n_c" && "$n_c" -lt "$n_b" \
  && "$out" != *"2026-01-01-a-handoff.md"* ]]; then
  pass "C3 handoff 역순·5개·legacy 포함"
else flunk "C3 handoff 역순·5개·legacy 포함"; fi

# C6 (C3 저장소의 하위 디렉터리에서 — 루트 실행 결과와 같아야 함)
root_out="$out"
run "$r/src"
if [[ "$rc" -eq 0 && "$out" == "$root_out" ]]; then pass "C6 하위 디렉터리에서 실행"
else flunk "C6 하위 디렉터리에서 실행"; fi

# C4
mkdir -p "$WORK/plain"
run "$WORK/plain"
if [[ "$rc" -eq 1 ]]; then pass "C4 git 저장소 아님 exit 1"; else flunk "C4 git 저장소 아님 exit 1"; fi

# C5
r="$(new_repo c5)"; s="$(new_repo c5-sibling)"; sh="$(git -C "$s" rev-parse --short HEAD)"
run "$r" "$s"
if [[ "$rc" -eq 0 && "$out" == *"(2 repo)"* && "$out" == *"**c5-sibling**"* \
  && "$out" == *"\`$sh\`"* ]]; then pass "C5 sibling 인자 → 다중 repo 표"
else flunk "C5 sibling 인자 → 다중 repo 표"; fi

# C8 (C5 저장소의 src/ 에서 sibling 을 상대 경로로)
run "$r/src" "../../c5-sibling"
if [[ "$rc" -eq 0 && "$out" == *"(2 repo)"* && "$out" == *"**c5-sibling**"* \
  && "$out" == *"\`$sh\`"* ]]; then pass "C8 하위 디렉터리 + 상대 sibling 경로"
else flunk "C8 하위 디렉터리 + 상대 sibling 경로"; fi

# C9
r="$(new_repo c9)"
echo n > "$r/a ._b.txt"; echo n > "$r/src/c ._d.txt"; echo x > "$r/src/._y"
run "$r"
if [[ "$rc" -eq 0 && "$out" == *"a ._b.txt"* && "$out" == *"c ._d.txt"* \
  && "$out" != *"._y"* ]]; then
  pass "C9 이름 중간의 ' ._' 는 목록에 남음"
else flunk "C9 이름 중간의 ' ._' 는 목록에 남음"; fi

exit "$fail"
