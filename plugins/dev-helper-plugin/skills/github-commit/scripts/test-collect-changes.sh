#!/usr/bin/env bash
# collect-changes.sh 동작 검증 — 임시 git 저장소에서 시나리오별 출력·종료 코드를 단언.
# 핵심 계약
#   - 비밀 검사는 diff 표시 상한과 무관하게 전체 diff·untracked 본문에 적용
#   - 비밀 값은 어떤 경로(diff 본문·untracked·삭제 줄)로도 출력되지 않음
#   - 사용자 git 설정(color·external diff)과 무관하게 검사됨
#
# 케이스 목록(고정)
#    1. git 저장소가 아니면 exit 2
#    2. 변경 없는 저장소 → secret_hits=0, 주요 섹션 존재
#    3. untracked 파일 3번째 줄의 비밀 → "SECRET <파일>:3 (untracked)", 값 미노출
#    4. 상한(20,000바이트) 뒤 tracked diff 의 비밀 → 검출, 본문 생략, 값 미노출
#    5. 비밀이 담긴 줄을 삭제만 한 diff → 검출 안 함, 삭제 줄의 값도 마스킹
#    6. 수집 전에 stage 된 파일 → staged 섹션에 표시
#    7. 공백 포함 파일명 + 깨진 심볼릭 링크 + AppleDouble(._*) → 중단 없음, ._* 는 untracked 목록·검사 제외
#    8. 상한 안쪽 tracked diff 의 비밀 → 검출, "(비밀 검출 — diff 본문 생략)", 값 미노출
#    9. 패턴 6종 × (diff 경로·untracked 경로) 양성 검출, 같은 접두의 짧은 음성은 미검출
#   10. 저장소에 color.diff=always · diff.external 설정 → 여전히 검출
#   11. 비밀 없는 큰 diff(한글 포함) → 바이트 기준 잘림 표시
#
# 사용: bash test-collect-changes.sh   (모두 통과 시 exit 0)

set -uo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1   # 사용자 전역 git 설정 격리

SCRIPT="$(cd "$(dirname "$0")" && pwd)/collect-changes.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
fail=0

rep() { printf "%.0s$1" $(seq 1 "$2"); }
# 비밀 표본은 실행 중 조립 — 이 파일 자체는 비밀 패턴을 담지 않음
KEYWORD="PRIVATE"
FAKE="ghp_$(rep a 24)"
POSITIVE=("sk-ant-$(rep a 20)" "ghp_$(rep b 24)" "github_pat_$(rep C 22)"
  "AKIA$(rep D 16)" "-----BEGIN RSA ${KEYWORD} KEY-----" "xoxb-$(rep 1 12)")
NEGATIVE=("sk-ant-short" "ghp_short" "github_pat_x" "AKIA123" "-----BEGIN PUBLIC KEY-----" "xoxb-1")

pass() { echo "PASS  $1"; }
flunk() { echo "FAIL  $1"; fail=1; }

new_repo() {
  local d="$WORK/$1"
  mkdir -p "$d"
  git -C "$d" init -q
  git -C "$d" config user.name tester
  git -C "$d" config user.email tester@example.com
  echo "$d"
}
commit_all() { git -C "$1" add -A && git -C "$1" commit -q -m init; }

# 1
mkdir -p "$WORK/plain"
bash "$SCRIPT" "$WORK/plain" >/dev/null 2>&1
rc=$?
if [[ "$rc" -eq 2 ]]; then pass "1 비저장소 exit 2"; else flunk "1 비저장소 exit 2"; fi

# 2
r="$(new_repo clean)"; echo hello > "$r/a.txt"; commit_all "$r"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"secret_hits=0"* && "$out" == *"=== identity ==="* && "$out" == *"=== status ==="* ]]; then pass "2 변경 없음"; else flunk "2 변경 없음"; fi

# 3
r="$(new_repo untracked)"; echo base > "$r/a.txt"; commit_all "$r"
printf 'line1\nline2\ntoken=%s\n' "$FAKE" > "$r/new.txt"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"SECRET new.txt:3 (untracked)"* && "$out" != *"$FAKE"* ]]; then pass "3 untracked 비밀 위치·미노출"; else flunk "3 untracked 비밀 위치·미노출"; fi

# 4
r="$(new_repo bigdiff)"; echo base > "$r/big.txt"; commit_all "$r"
{ head -c 30000 /dev/zero | tr '\0' 'x' | fold -w 100; echo "key=$FAKE"; } >> "$r/big.txt"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"SECRET big.txt (diff 추가 줄)"* && "$out" == *"diff 본문 생략"* && "$out" != *"$FAKE"* ]]; then pass "4 상한 뒤 비밀 검출·본문 생략·미노출"; else flunk "4 상한 뒤 비밀 검출·본문 생략·미노출"; fi

# 5
r="$(new_repo removal)"; printf 'keep\nkey=%s\n' "$FAKE" > "$r/old.txt"; commit_all "$r"
printf 'keep\n' > "$r/old.txt"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"secret_hits=0"* && "$out" == *"[REDACTED]"* && "$out" != *"$FAKE"* ]]; then pass "5 삭제 줄 미검출·마스킹"; else flunk "5 삭제 줄 미검출·마스킹"; fi

# 6
r="$(new_repo staged)"; echo base > "$r/a.txt"; commit_all "$r"
echo pre > "$r/pre.txt"; git -C "$r" add pre.txt
out="$(bash "$SCRIPT" "$r")"
staged_block="$(printf '%s\n' "$out" | sed -n '/^=== staged/,/^=== log/p')"
if [[ "$staged_block" == *"pre.txt"* ]]; then pass "6 미리 stage 된 파일 표시"; else flunk "6 미리 stage 된 파일 표시"; fi

# 7
r="$(new_repo oddnames)"; echo base > "$r/a.txt"; commit_all "$r"
echo x > "$r/with space.txt"; ln -s "$r/nowhere" "$r/broken-link"; printf 'token=%s\n' "$FAKE" > "$r/._meta"
out="$(bash "$SCRIPT" "$r")"
rc=$?
untracked_block="$(printf '%s\n' "$out" | sed -n '/^=== untracked/,/^=== secret/p')"
if [[ "$rc" -eq 0 && "$untracked_block" == *"with space.txt"* && "$untracked_block" == *"broken-link"* \
  && "$untracked_block" != *"._meta"* && "$out" == *"secret_hits=0"* ]]; then pass "7 공백 파일명·깨진 링크·._* 목록·검사 제외"; else flunk "7 공백 파일명·깨진 링크·._* 목록·검사 제외"; fi

# 8
r="$(new_repo tracked)"; echo base > "$r/c.txt"; commit_all "$r"
printf 'token=%s\n' "$FAKE" >> "$r/c.txt"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"SECRET c.txt (diff 추가 줄)"* && "$out" == *"(비밀 검출 — diff 본문 생략)"* && "$out" != *"$FAKE"* ]]; then pass "8 상한 안쪽 tracked 비밀 미노출"; else flunk "8 상한 안쪽 tracked 비밀 미노출"; fi

# 9
r="$(new_repo patterns)"; echo base > "$r/t.txt"; commit_all "$r"
for i in "${!POSITIVE[@]}"; do
  pos="${POSITIVE[$i]}"; neg="${NEGATIVE[$i]}"
  printf 'v=%s\n' "$pos" >> "$r/t.txt"
  out="$(bash "$SCRIPT" "$r")"; git -C "$r" checkout -q -- t.txt
  if [[ "$out" == *"secret_hits=1"* && "$out" != *"$pos"* ]]; then pass "9 패턴 ${i} diff 양성"; else flunk "9 패턴 ${i} diff 양성"; fi
  printf 'v=%s\n' "$pos" > "$r/u.txt"
  out="$(bash "$SCRIPT" "$r")"; rm -f "$r/u.txt"
  if [[ "$out" == *"secret_hits=1"* && "$out" != *"$pos"* ]]; then pass "9 패턴 ${i} untracked 양성"; else flunk "9 패턴 ${i} untracked 양성"; fi
  printf 'v=%s\n' "$neg" >> "$r/t.txt"; printf 'v=%s\n' "$neg" > "$r/u.txt"
  out="$(bash "$SCRIPT" "$r")"; git -C "$r" checkout -q -- t.txt; rm -f "$r/u.txt"
  if [[ "$out" == *"secret_hits=0"* ]]; then pass "9 패턴 ${i} 음성"; else flunk "9 패턴 ${i} 음성"; fi
done

# 10
r="$(new_repo gitconf)"; echo base > "$r/a.txt"; commit_all "$r"
git -C "$r" config color.diff always; git -C "$r" config diff.external /bin/true
printf 'token=%s\n' "$FAKE" >> "$r/a.txt"
out="$(bash "$SCRIPT" "$r")"
if [[ "$out" == *"SECRET a.txt (diff 추가 줄)"* ]]; then pass "10 color·external diff 설정에도 검출"; else flunk "10 color·external diff 설정에도 검출"; fi

# 11
r="$(new_repo bytes)"; echo base > "$r/k.txt"; commit_all "$r"
for _ in $(seq 1 1500); do echo "가나다라마바사아자차"; done >> "$r/k.txt"
out="$(LC_ALL=C bash "$SCRIPT" "$r")"
if [[ "$out" == *"secret_hits=0"* && "$out" == *"... (잘림: 전체"*"바이트"* ]]; then pass "11 바이트 기준 잘림 표시"; else flunk "11 바이트 기준 잘림 표시"; fi

exit "$fail"
