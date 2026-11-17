#!/usr/bin/env bash
# collect-handoff-facts.sh
# project-handoff 스킬 §2 step 1 backbone.
# handoff 작성에 필요한 사실을 Bash 호출 1회로 출력(순차 date·git·ls 호출을 대체).
#   - 오늘 날짜와 권장 파일명 접두 docs/handoffs/<date>-
#   - §1 스냅샷 표(capture-repo-state.sh 출력, 인자 그대로 위임)
#   - 미커밋 변경(git status --short, AppleDouble ._* 제외)
#   - 최근 handoff 5개(docs/handoffs/ + legacy docs/superpowers/handoffs/ 읽기 전용, 이름 역순)
#
# 사용:
#   $ bash collect-handoff-facts.sh                         # 현재 repo 단독
#   $ bash collect-handoff-facts.sh /path/to/sibling-a /path/to/sibling-b
#
# 종료 코드: 0 정상 · 1 git 저장소 아님

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RECENT_N=5

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[FAIL] 현재 디렉터리가 git repo 가 아님" >&2
  exit 1
fi

# sibling 인자는 호출 위치 기준 상대 경로일 수 있으므로 repo 루트로 옮기기 전에 절대 경로로 바꿈
siblings=()
for arg in "$@"; do
  if [[ -d "$arg" ]]; then siblings+=("$(cd "$arg" && pwd)"); else siblings+=("$arg"); fi
done
cd "$(git rev-parse --show-toplevel)"

section() { printf '\n=== %s ===\n' "$1"; }
today="$(date +%Y-%m-%d)"

section "날짜·파일명"
echo "오늘: $today"
echo "파일명 접두: docs/handoffs/$today-<topic>-handoff.md"

section "§1 스냅샷 (capture-repo-state.sh)"
bash "$SCRIPT_DIR/capture-repo-state.sh" ${siblings[@]+"${siblings[@]}"}

section "미커밋 변경 (git status --short)"
# 이름이 ._ 로 시작하는 파일(AppleDouble)은 pathspec 으로 제외
# (출력 행 정규식은 이름 중간에 ' ._' 가 든 일반 파일까지 지움)
changes="$(git -c core.quotePath=false status --short -- . ':(exclude,glob)**/._*')"
if [[ -n "$changes" ]]; then printf '%s\n' "$changes"; else echo "미커밋 없음"; fi

section "최근 handoff (이름 역순, 최대 $RECENT_N)"
recent="$(
  for f in docs/handoffs/*-handoff.md docs/superpowers/handoffs/*-handoff.md; do
    name="${f##*/}"
    # ._* 는 glob '*' 가 점 파일을 이미 제외 — 아래 이름 검사는 방어용
    if [[ ! -f "$f" || "$name" == ._* ]]; then continue; fi
    printf '%s\t%s\n' "$name" "$f"
  done | sort -r | awk -F '\t' -v n="$RECENT_N" 'NR <= n {print $2}'
)"
if [[ -n "$recent" ]]; then printf '%s\n' "$recent"; else echo "없음"; fi
