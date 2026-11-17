#!/usr/bin/env bash
# collect-changes.sh
# github-commit 스킬 수집 단계 backbone.
# 커밋 판단에 필요한 저장소 상태를 Bash 호출 1회로 출력.
# 비밀 검사는 잘리기 전 전체 diff(추가 줄)와 untracked 파일 본문 전체에 먼저 수행하고,
# 검출되면 diff 본문을 출력하지 않음. 비밀 값 자체는 어떤 경로로도 출력하지 않고 위치만 보고.
# diff 표시 상한은 바이트 기준(로캘 무관).
#
# 사용:
#   $ bash collect-changes.sh              # 현재 저장소
#   $ bash collect-changes.sh /path/to/repo
#
# 종료 코드: 0 정상(비밀 검출 여부는 출력의 SECRET 행·secret_hits 로 판단) · 2 git 저장소 아님

set -euo pipefail

REPO="${1:-.}"
DIFF_LIMIT=20000   # diff 본문 표시 상한(바이트) — 검사 범위에는 적용하지 않음
SECRET_RE='sk-ant-[A-Za-z0-9_-]{10,}|gh[po]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}'
SECRET_RE+='|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[bp]-[0-9A-Za-z-]{10,}'
# 사용자 git 설정(diff.external·color.diff·textconv)이 unified diff 형식을 바꾸면 검사가 빠지므로 고정
DIFF_OPTS=(--no-ext-diff --no-color --no-textconv)

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: git 저장소 아님: $REPO" >&2
  exit 2
fi
cd "$(git -C "$REPO" rev-parse --show-toplevel)"

section() { printf '\n=== %s ===\n' "$1"; }
# untracked 파일 목록(NUL 구분), macOS AppleDouble(._*) 제외
untracked() {
  git ls-files --others --exclude-standard -z \
    | while IFS= read -r -d '' f; do [[ "${f##*/}" == ._* ]] || printf '%s\0' "$f"; done
}

section "repo"
pwd
section "identity"
printf 'user.name=%s\nuser.email=%s\n' \
  "$(git config user.name || echo '(미설정)')" "$(git config user.email || echo '(미설정)')"
section "status"
git -c color.status=false status --short -uall
section "staged (수집 시점에 이미 stage 된 파일)"
git diff --cached --name-only
section "log"
git log --oneline --no-color -5 2>/dev/null || echo "(커밋 없음)"
section "diff --stat (staged)"
git diff --cached --stat "${DIFF_OPTS[@]}"
section "diff --stat (unstaged)"
git diff --stat "${DIFF_OPTS[@]}"

section "untracked (바이트·경로)"
while IFS= read -r -d '' f; do
  printf '%s\t%s\n' "$({ wc -c < "$f"; } 2>/dev/null || echo '?')" "$f"
done < <(untracked)

# 검사를 diff 본문보다 먼저 수행 — 검출 시 본문을 출력하지 않아 값이 컨텍스트에 들어가지 않게 함
section "secret scan (전체 diff 추가 줄 + untracked 본문)"
hits=0
# grep -q 로 끝내면 pipefail 아래에서 앞단 SIGPIPE(141)가 검출 성공을 실패로 뒤집음 → 변수로 받아 판정
while IFS= read -r -d '' f; do
  added="$({ git diff --cached -U0 "${DIFF_OPTS[@]}" -- "$f"; git diff -U0 "${DIFF_OPTS[@]}" -- "$f"; } \
    | grep -E '^\+' | grep -v -E '^\+\+\+ ' || true)"
  [[ "$added" =~ $SECRET_RE ]] || continue
  printf 'SECRET %s (diff 추가 줄)\n' "$f"
  hits=$((hits + 1))
done < <({ git diff --cached --name-only -z; git diff --name-only -z; } | sort -zu)
while IFS= read -r -d '' f; do
  lines="$(grep -n -I -E "$SECRET_RE" -- "$f" 2>/dev/null | cut -d: -f1 | paste -sd, - || true)"
  [[ -n "$lines" ]] || continue
  printf 'SECRET %s:%s (untracked)\n' "$f" "$lines"
  hits=$((hits + 1))
done < <(untracked)
printf 'secret_hits=%d\n' "$hits"

section "diff 본문 (staged+unstaged, 최대 ${DIFF_LIMIT}바이트, 비밀 패턴 마스킹)"
if (( hits > 0 )); then
  echo "(비밀 검출 — diff 본문 생략)"
  exit 0
fi
# 검출 0 이어도 삭제 줄에 남은 비밀은 표시될 수 있어 표시용 본문은 항상 마스킹
masked() {
  { git diff --cached "${DIFF_OPTS[@]}"; git diff "${DIFF_OPTS[@]}"; } \
    | sed -E "s#${SECRET_RE}#[REDACTED]#g"
}
total="$(masked | wc -c)"
masked | head -c "$DIFF_LIMIT" || true   # head 가 일찍 닫아 생기는 SIGPIPE 는 정상
echo
if (( total > DIFF_LIMIT )); then
  printf '... (잘림: 전체 %d바이트 — 파일별 내용은 diff --stat 와 Read 로 확인)\n' "$total"
fi
