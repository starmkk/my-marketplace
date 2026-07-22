#!/usr/bin/env bash
# capture-repo-state.sh
# project-handoff 스킬 §2 step 2 backbone.
# 현재 repo(+ 선택적 sibling repo)의 branch / HEAD / 직전 N commit chain 을
# handoff §1 스냅샷 표에 붙일 markdown 으로 출력.
#
# 사용:
#   $ bash capture-repo-state.sh                       # 현재 repo 단독
#   $ bash capture-repo-state.sh /path/to/SoundAI.Lite /path/to/SpeechLM.cpp.v3
#
# 단일 repo → "항목|값" 표. 2+ repo → "repo|branch|HEAD|커밋범위|상태" 표.

set -euo pipefail

N="${HANDOFF_COMMIT_CHAIN_N:-10}"   # commit chain 길이 (env override 가능)

repo_short_head() { git -C "$1" rev-parse --short HEAD 2>/dev/null || echo "?"; }
repo_branch()     { git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?"; }
repo_head_msg()   { git -C "$1" log -1 --pretty='%s' 2>/dev/null || echo "?"; }
repo_name()       { basename "$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1")"; }

# commit chain 을 "`h` (msg) ← `h` (msg) ← ..." 한 줄로
commit_chain_inline() {
  # shellcheck disable=SC2016  # 백틱·%h 는 markdown/git 포맷 리터럴 — 쉘 확장 의도 없음
  git -C "$1" log --oneline -"$N" --pretty='`%h` (%s)' 2>/dev/null | paste -sd '@' - \
    | sed 's/@/ ← /g'
}

if [[ "$#" -eq 0 ]]; then
  # 단일 repo — 현재 디렉터리
  R="."
  if ! git -C "$R" rev-parse --git-dir >/dev/null 2>&1; then
    echo "[FAIL] 현재 디렉터리가 git repo 가 아님" >&2; exit 1
  fi
  echo "## 1. 현재 상태 스냅샷"
  echo
  echo "| 항목 | 값 |"
  echo "|---|---|"
  echo "| branch | \`$(repo_branch "$R")\` |"
  echo "| HEAD | $(commit_chain_inline "$R") |"
  echo "| 빌드 | \`assembleDebug\` <GREEN/RED>. 단말 \`<모델>\` 연결. APK: \`<경로>\` |"
  echo "| 빌드 prefix(의무) | \`JAVA_HOME=... COPYFILE_DISABLE=1 ./gradlew ...\` |"
  echo "| ledger(SoT) | \`.superpowers/sdd/progress.md\` (\`<해당 절>\`) |"
  echo "| plan/spec | \`docs/superpowers/plans/<...>.md\` · \`docs/superpowers/specs/<...>.md\` |"
  echo "| architect | \`docs/superpowers/architect-reviews/<...>.md\` (\`<권장 요약>\`) |"
else
  # multi-repo — 현재 repo + 인자 repo들
  echo "## 1. 현재 상태 스냅샷 ($(($# + 1)) repo)"
  echo
  echo "| repo | branch | HEAD | 우리 커밋 범위 | 상태 |"
  echo "|---|---|---|---|---|"
  for R in "." "$@"; do
    if ! git -C "$R" rev-parse --git-dir >/dev/null 2>&1; then
      echo "| \`$R\` | ? | ? | (git repo 아님) | ⚠️ |"; continue
    fi
    # shellcheck disable=SC2016  # 백틱은 markdown 리터럴 — 확장 의도 없음
    printf '| **%s** | `%s` | `%s` (%s) | `<base>..%s` (<N> commits) | ✅ <상태> |\n' \
      "$(repo_name "$R")" "$(repo_branch "$R")" "$(repo_short_head "$R")" \
      "$(repo_head_msg "$R")" "$(repo_short_head "$R")"
  done
  echo
  echo "> ⚠️ sibling repo 는 무관 in-flight 변경 보유 가능 — 후속 작업 시 지정 파일만 명시 add."
  echo "> merge/PR 미실행 (git-policy §5.2 — 명시 요청 시만)."
fi
