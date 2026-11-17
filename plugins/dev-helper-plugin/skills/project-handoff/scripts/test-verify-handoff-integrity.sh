#!/usr/bin/env bash
# verify-handoff-integrity.sh 동작 검증 — 임시 git 저장소의 고정 문서로 종료 코드·출력을 단언.
# 핵심 계약
#   - HEAD anchor 는 '현재 상태 스냅샷' 절에서만 뽑음(§0 의 이전 해시에 속지 않음)
#   - handoff 커밋 뒤 실행(anchor = HEAD^, HEAD 가 handoff 변경)은 통과
#   - '참조 인덱스' 절의 경로는 repo 루트 기준으로 존재 확인(판정 못 하는 토큰은 건너뜀)
#   - 종료 코드: 0 = OK(WARN 허용) · 1 = FAIL
#
# 케이스 목록(고정)
#   T1  §0 에 이전 해시, §1 HEAD 행 정확 → 0
#   T2  §1 HEAD 행 해시 틀림 → 1
#   T3  다중 repo 표(HEAD 행 없음), 첫 행 해시 = HEAD → 0
#   T4  §1 절 없음 → WARN + 문서 첫 해시로 판정
#   T5  §8 에 없는 repo 상대 경로 → 1, 그 경로 출력
#   T6  §8 의 path:12·<자리표시>·URL·루트에 없는 첫 구성요소·{a,b}·공백·' §3' 접미 → 통과
#   T7  §10 절 없음 → 1
#   T8  파일명 날짜 ≠ 오늘 → WARN, 0
#   T9  handoff 커밋 뒤 실행(anchor = HEAD^, HEAD 가 handoff 변경) → 0
#   T10 anchor 뒤에 handoff 와 무관한 커밋 → 1
#   T11 해시 0개 + §10 없음 → 1(두 FAIL 모두 출력)
#   T12 하위 디렉터리에서 실행 → T5 와 같은 결과
#   T13 §8 마크다운 링크 대상 없음 → 1
#   T14 §8 절대 경로 없음 → 1
#   T15 §8 절 없음 → WARN, 0
#   T16 (추가) 없는 경로에 ' §3' 접미·http 부분 문자열 → 1
#       이유: T6 은 양성뿐이라 정규화 순서가 뒤바뀌거나 http 부분 문자열로 건너뛰어도 통과함
#   T17 handoff 가 repo 밖 + anchor = HEAD^ → 1
#   T18 다른 worktree 의 handoff 를 main 쪽 cwd 에서 검증(HEAD 는 무관 커밋) → 1
#   T19 §0 펜스 안 예시 §1(이전 해시) + 실제 §1 정확 → 0
#   T20 §10 heading 이 펜스 안에만 → 1
#   T21 §8 의 '…'·'...' 토큰, ':줄:열'·':L줄(-L줄)' 접미, 단말 경로 → 통과
#   T22 하위 디렉터리에서 인자 없이 실행 → 루트 docs/handoffs 최신 파일 선택
#   T23 §8 의 [x](../y.md) 링크 → 건너뜀
#   T24 '| **HEAD** |' 행(앞 행에 다른 해시) → 0
#   T25 (추가) cwd 와 다른 repo 의 handoff, anchor = cwd repo HEAD → 1
#   T26 (추가) cwd 와 다른 repo 의 handoff, anchor·§8 경로가 그 repo 기준 → 0
#       이유: HEAD 대조·§8 기준을 cwd 가 아니라 handoff 가 속한 repo 로 고정했는지 확인
#
# 사용: bash test-verify-handoff-integrity.sh   (모두 통과 시 exit 0)

set -uo pipefail
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1   # 사용자 전역 git 설정 격리

SCRIPT="$(cd "$(dirname "$0")" && pwd)/verify-handoff-integrity.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
TODAY="$(date +%Y-%m-%d)"
FENCE="$(printf '\140\140\140')"   # 펜스 코드 블록 표시(백틱 3개)
fail=0
out=""
rc=0

pass() { echo "PASS  $1"; }
flunk() { echo "FAIL  $1"; printf '%s\n' "$out" | sed 's/^/      | /'; fail=1; }

# 커밋 2개(c1·c2)와 src/a.txt·docs/spec.md 를 가진 저장소
new_repo() {
  local d="$WORK/$1"
  mkdir -p "$d/docs/handoffs" "$d/src"
  git -C "$d" init -q
  git -C "$d" config user.name tester
  git -C "$d" config user.email tester@example.com
  echo a > "$d/src/a.txt"
  echo spec > "$d/docs/spec.md"
  git -C "$d" add -A && git -C "$d" commit -q -m c1
  echo b >> "$d/src/a.txt"
  git -C "$d" commit -q -am c2
  echo "$d"
}
head_of() { git -C "$1" rev-parse --short "${2:-HEAD}"; }

# 단일 repo §1 절 — s1_single <HEAD 셀 해시(빈 문자열이면 해시 없음)>
s1_single() {
  printf "## 1. 현재 상태 스냅샷\n\n| 항목 | 값 |\n|---|---|\n| branch | \`main\` |\n"
  if [[ -n "$1" ]]; then printf "| HEAD | \`%s\` (c2) |\n" "$1"; else printf '| HEAD | 미정 |\n'; fi
}
# 다중 repo §1 절 — s1_multi <첫 행 해시>
s1_multi() {
  printf '## 1. 현재 상태 스냅샷 (2 repo)\n\n| repo | branch | HEAD | 범위 | 상태 |\n'
  printf "|---|---|---|---|---|\n| **this** | \`main\` | \`%s\` (c2) | \`<base>..x\` | ok |\n" "$1"
  printf "| **sib** | \`main\` | \`1234567\` (x) | \`<base>..y\` | ok |\n"
}
# §8 절 — s8 <목록 줄...>
s8() {
  printf '## 8. 참조 인덱스\n\n'
  printf -- '- %s\n' "$@"
}

# write_doc <파일> <§0 본문> <§1 절(빈=생략)> <§8 절(빈=생략)> <§10 에 적을 HEAD(빈=§10 생략)>
write_doc() {
  local f="$1" s0="$2" s1="$3" s8="$4" h="$5" base
  base="$(basename "$1")"
  {
    printf '# HANDOFF — t\n\n## 0. 한 줄 요약\n\n%s\n\n' "$s0"
    if [[ -n "$s1" ]]; then printf '%s\n\n' "$s1"; fi
    printf '## 5. 다음 작업 ★\n\n- 없음\n\n'
    if [[ -n "$s8" ]]; then printf '%s\n\n' "$s8"; fi
    printf '## 9. 재개 절차 (다음 세션)\n\n1. 읽기\n\n'
    if [[ -n "$h" ]]; then
      printf '## 10. 다음 세션 시작 프롬프트 (그대로 복사해 첫 입력으로 사용)\n\n```text\n'
      printf -- '- docs/handoffs/%s\n  (§9 의 1번부터 시작)\n' "$base"
      printf '1. 실행 위치는 /repo (main, HEAD %s).\n```\n' "$h"
    fi
  } > "$f"
}

# run <실행 디렉터리> <handoff 경로> → out, rc
run() {
  out="$(cd "$1" && bash "$SCRIPT" "$2" 2>&1)"
  rc=$?
}

OK_S8="$(s8 "코드: \`src/a.txt\`" "spec: \`docs/spec.md\`")"

# T1
r="$(new_repo t1)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "이전 커밋 \`$(head_of "$r" HEAD^)\` 에서 이어짐" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK]"* && "$out" != *"[WARN]"* ]]; then
  pass "T1 §0 이전 해시 무시·§1 HEAD 행 정합"
else flunk "T1 §0 이전 해시 무시·§1 HEAD 행 정합"; fi

# T2
r="$(new_repo t2)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single deadbee)" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"deadbee"* ]]; then pass "T2 §1 HEAD 행 해시 틀림"
else flunk "T2 §1 HEAD 행 해시 틀림"; fi

# T3
r="$(new_repo t3)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "이전 \`$(head_of "$r" HEAD^)\`" "$(s1_multi "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK]"* ]]; then pass "T3 다중 repo 표 첫 행"
else flunk "T3 다중 repo 표 첫 행"; fi

# T4
r="$(new_repo t4)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "현재 \`$h\`" "" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[WARN]"*"현재 상태 스냅샷"* && "$out" == *"[OK]"* ]]; then
  pass "T4 §1 절 없음 → WARN + 문서 첫 해시"
else flunk "T4 §1 절 없음 → WARN + 문서 첫 해시"; fi

# T5
r="$(new_repo t5)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" \
  "$(s8 "코드: \`src/a.txt\`" "없음: \`docs/missing.md\`")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"docs/missing.md"* ]]; then pass "T5 §8 없는 상대 경로"
else flunk "T5 §8 없는 상대 경로"; fi

# T12 (T5 문서를 하위 디렉터리에서)
run "$r/src" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"docs/missing.md"* ]]; then pass "T12 하위 디렉터리에서 실행"
else flunk "T12 하위 디렉터리에서 실행"; fi

# T6
r="$(new_repo t6)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$(s8 \
  "줄 번호: \`src/a.txt:12\` · \`src/a.txt:3-9\`" \
  "자리표시: \`<자리표시>\` · \`docs/<topic>.md\` · \`docs/*.md\`" \
  "변수·홈: \`docs/\$NAME.md\` · \`~/docs/x.md\` · \`docs/~x.md\`" \
  "URL: \`https://example.com/docs/x\` · [링크](https://example.com/docs/y)" \
  "루트에 없는 첫 구성요소: \`nope-root/x.md\` · \`main\`" \
  "중괄호: \`docs/{a,b}.md\`" \
  "공백: \`docs/no such file.md\`" \
  "접미: \`docs/spec.md §3\` · \`docs/spec.md#sec\` · [spec](docs/spec.md)")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" != *"[FAIL]"* ]]; then pass "T6 §8 판정 제외·접미 제거"
else flunk "T6 §8 판정 제외·접미 제거"; fi

# T7
r="$(new_repo t7)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" ""
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"다음 세션 시작 프롬프트"* ]]; then pass "T7 §10 절 없음"
else flunk "T7 §10 절 없음"; fi

# T8
r="$(new_repo t8)"; h="$(head_of "$r")"; f="$r/docs/handoffs/2000-01-01-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[WARN]"*"2000-01-01"* ]]; then pass "T8 파일명 날짜 ≠ 오늘"
else flunk "T8 파일명 날짜 ≠ 오늘"; fi

# T9
r="$(new_repo t9)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
git -C "$r" add docs/handoffs && git -C "$r" commit -q -m handoff
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK]"*"커밋 후 검증"* ]]; then pass "T9 handoff 커밋 뒤 실행"
else flunk "T9 handoff 커밋 뒤 실행"; fi

# T10 (handoff 는 추적 안 함 → anchor = HEAD^ 이지만 HEAD 는 handoff 를 바꾸지 않음)
r="$(new_repo t10)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
echo c >> "$r/src/a.txt"; git -C "$r" commit -q -am c3
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"$h"* ]]; then pass "T10 anchor 뒤 무관한 커밋"
else flunk "T10 anchor 뒤 무관한 커밋"; fi

# T11
r="$(new_repo t11)"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "")" "$OK_S8" ""
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"anchor"* && "$out" == *"다음 세션 시작 프롬프트"* ]]; then
  pass "T11 해시 0개 + §10 없음"
else flunk "T11 해시 0개 + §10 없음"; fi

# T13
r="$(new_repo t13)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$(s8 '계획: [plan](docs/nope-plan.md)')" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"docs/nope-plan.md"* ]]; then pass "T13 §8 링크 대상 없음"
else flunk "T13 §8 링크 대상 없음"; fi

# T14
r="$(new_repo t14)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" \
  "$(s8 "절대: \`$WORK/t14/src/a.txt\` · \`$WORK/none/x.md\`")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"$WORK/none/x.md"* && "$out" != *"t14/src/a.txt"* ]]; then
  pass "T14 §8 절대 경로 없음"
else flunk "T14 §8 절대 경로 없음"; fi

# T15
r="$(new_repo t15)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[WARN]"*"참조 인덱스"* ]]; then pass "T15 §8 절 없음 → WARN"
else flunk "T15 §8 절 없음 → WARN"; fi

# T16
r="$(new_repo t16)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" \
  "$(s8 "없음: \`docs/gone.md §3\` · \`docs/http-gone.md:12\`")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"docs/gone.md"* && "$out" == *"docs/http-gone.md"* ]]; then
  pass "T16 없는 경로 + 접미·http 부분 문자열"
else flunk "T16 없는 경로 + 접미·http 부분 문자열"; fi

# T17 (handoff 가 어느 repo 에도 없음 — HEAD 가 그 파일을 바꿨을 수 없음)
r="$(new_repo t17)"; h="$(head_of "$r" 'HEAD^')"; mkdir -p "$WORK/outside"
f="$WORK/outside/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"* && "$out" != *"[OK](커밋 후 검증)"* ]]; then
  pass "T17 repo 밖 handoff + anchor = HEAD^"
else flunk "T17 repo 밖 handoff + anchor = HEAD^"; fi

# T18 (worktree 의 추적 안 하는 handoff, anchor = HEAD^, HEAD 는 handoff 와 무관한 c2)
r="$(new_repo t18)"; h="$(head_of "$r" 'HEAD^')"; w="$WORK/t18-wt"
git -C "$r" worktree add -q "$w" -b wt
mkdir -p "$w/docs/handoffs"; f="$w/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"* && "$out" != *"[OK](커밋 후 검증)"* ]]; then
  pass "T18 다른 worktree 의 handoff + 무관 커밋"
else flunk "T18 다른 worktree 의 handoff + 무관 커밋"; fi

# T19
r="$(new_repo t19)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
s0="$(printf '예시\n\n%smarkdown\n%s\n%s' "$FENCE" "$(s1_single "$(head_of "$r" 'HEAD^')")" "$FENCE")"
write_doc "$f" "$s0" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK] HEAD anchor ($h)"* ]]; then pass "T19 펜스 안 예시 §1 무시"
else flunk "T19 펜스 안 예시 §1 무시"; fi

# T20 (§10 heading 은 §0 의 펜스 안에만, ```text 블록·자기 파일명은 §8 뒤에 따로 있음)
r="$(new_repo t20)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
s0="$(printf '예시\n\n%smarkdown\n## 10. 다음 세션 시작 프롬프트\n%s' "$FENCE" "$FENCE")"
s8x="$(printf '%s\n\n%stext\n- docs/handoffs/%s (§9 의 1번)\n%s' \
  "$OK_S8" "$FENCE" "$(basename "$f")" "$FENCE")"
write_doc "$f" "$s0" "$(s1_single "$h")" "$s8x" ""
run "$r" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL]"*"다음 세션 시작 프롬프트"* ]]; then
  pass "T20 §10 이 펜스 안에만"
else flunk "T20 §10 이 펜스 안에만"; fi

# T21
r="$(new_repo t21)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$(s8 \
  "생략: \`docs/…/x.md\` · \`docs/.../y.md\`" \
  "줄·열: \`src/a.txt:12:5\` · \`src/a.txt:L3\` · \`src/a.txt:L3-L9\` · \`src/a.txt:L3-9\`" \
  "단말: \`/sdcard/Download/x.wav\` · \`/storage/emulated/0/x\` · \`/data/local/tmp/y\`" \
  "단말: \`/data/data/com.x/files\` · \`/system/lib64/z.so\` · \`/vendor/lib/w.so\`")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" != *"[FAIL]"* ]]; then pass "T21 §8 생략 표기·줄 접미·단말 경로"
else flunk "T21 §8 생략 표기·줄 접미·단말 경로"; fi

# T22 (옛 파일은 해시가 틀림 — 최신 파일을 골라야 통과)
r="$(new_repo t22)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-new-handoff.md"
write_doc "$r/docs/handoffs/$TODAY-old-handoff.md" "요약" "$(s1_single deadbee)" "$OK_S8" "$h"
touch -t 200001010000 "$r/docs/handoffs/$TODAY-old-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$OK_S8" "$h"
run "$r/src" ""
if [[ "$rc" -eq 0 && "$out" == *"최근 파일 검증"*"$TODAY-new-handoff.md"* && "$out" == *"[PASS]"* ]]; then
  pass "T22 하위 디렉터리·인자 없음 → 루트 최신 파일"
else flunk "T22 하위 디렉터리·인자 없음 → 루트 최신 파일"; fi

# T23
r="$(new_repo t23)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$h")" "$(s8 '상위: [x](../y.md)' "코드: \`src/a.txt\`")" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" != *"[FAIL]"* ]]; then pass "T23 §8 의 ../ 링크 건너뜀"
else flunk "T23 §8 의 ../ 링크 건너뜀"; fi

# T24
r="$(new_repo t24)"; h="$(head_of "$r")"; f="$r/docs/handoffs/$TODAY-t-handoff.md"
s1="$(printf "## 1. 현재 상태 스냅샷\n\n| 항목 | 값 |\n|---|---|\n| base | \`%s\` |\n" \
  "$(head_of "$r" 'HEAD^')"; printf "| **HEAD** | \`%s\` (c2) |\n" "$h")"
write_doc "$f" "요약" "$s1" "$OK_S8" "$h"
run "$r" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK] HEAD anchor ($h)"* ]]; then pass "T24 굵은 HEAD 행"
else flunk "T24 굵은 HEAD 행"; fi

# T25·T26 (cwd = repo a, handoff 는 repo b 안 — 판정 기준은 b)
a="$(new_repo t25a)"; b="$(new_repo t25b)"
echo only-b > "$b/src/b-only.txt"; git -C "$b" add -A && git -C "$b" commit -q -m c3
f="$b/docs/handoffs/$TODAY-t-handoff.md"
write_doc "$f" "요약" "$(s1_single "$(head_of "$a")")" "$OK_S8" "$(head_of "$a")"
run "$a" "$f"
if [[ "$rc" -eq 1 && "$out" == *"[FAIL] HEAD anchor"* ]]; then
  pass "T25 다른 repo handoff 에 cwd repo HEAD"
else flunk "T25 다른 repo handoff 에 cwd repo HEAD"; fi
write_doc "$f" "요약" "$(s1_single "$(head_of "$b")")" "$(s8 "b 전용: \`src/b-only.txt\`")" \
  "$(head_of "$b")"
run "$a" "$f"
if [[ "$rc" -eq 0 && "$out" == *"[OK] HEAD anchor ($(head_of "$b"))"* ]]; then
  pass "T26 다른 repo handoff 를 그 repo 기준으로 판정"
else flunk "T26 다른 repo handoff 를 그 repo 기준으로 판정"; fi

exit "$fail"
