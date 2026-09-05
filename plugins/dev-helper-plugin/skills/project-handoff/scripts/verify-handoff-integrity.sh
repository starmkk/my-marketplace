#!/usr/bin/env bash
# verify-handoff-integrity.sh
# project-handoff 스킬 §2 step 5 self-review.
# handoff 파일의 §1 스냅샷 안 HEAD commit anchor 가 현재 git HEAD 와 일치하는지 검증.
# + §10 '다음 세션 시작 프롬프트' 절(heading·```text 블록·자기 파일명·HEAD) 존재 검증.
# 불일치 시 exit 1 + 정정 권유.
#
# 사용:
#   $ bash verify-handoff-integrity.sh docs/superpowers/handoffs/<YYYY-MM-DD>-<topic>-handoff.md
#   (인자 생략 시 handoffs/ 의 가장 최근 mtime 파일 자동 선택)

set -euo pipefail

HANDOFF="${1:-}"
HANDOFF_DIR="docs/superpowers/handoffs"

if [[ -z "$HANDOFF" ]]; then
  # 가장 최근 handoff 자동 선택 (archive 제외)
  # shellcheck disable=SC2012  # handoff 파일명은 <YYYY-MM-DD>-<kebab-topic>-handoff.md 로 특수문자 없음.
  #                              find -printf 는 GNU 전용이라 macOS(BSD find) 호환을 위해 ls -t 유지.
  HANDOFF=$(ls -t "$HANDOFF_DIR"/*-handoff.md 2>/dev/null | head -1 || true)
  if [[ -z "$HANDOFF" ]]; then
    echo "[SKIP] $HANDOFF_DIR 에 handoff 파일 없음 — 검증 대상 없음"; exit 0
  fi
  echo "[info] 인자 생략 → 최근 파일 검증: $HANDOFF"
fi

if [[ ! -f "$HANDOFF" ]]; then
  echo "[FAIL] handoff 파일 없음: $HANDOFF" >&2; exit 1
fi

# 문서 안 첫 번째 `<7~40 hex>` 패턴을 HEAD anchor 로 가정 (§1 표의 HEAD 셀 첫 hash)
# shellcheck disable=SC2016  # 백틱은 markdown 리터럴 — 확장 의도 없음
anchor=$(grep -oE '`[0-9a-f]{7,40}`' "$HANDOFF" | head -1 | tr -d '`' || true)
if [[ -z "$anchor" ]]; then
  echo "[SKIP] HEAD commit anchor 를 $HANDOFF 에서 못 찾음 (§1 표에 \`<hash>\` 있는지 확인)"; exit 0
fi

real=$(git rev-parse --short HEAD 2>/dev/null || true)
if [[ -z "$real" ]]; then
  echo "[FAIL] git repo 가 아님" >&2; exit 1
fi

# §10 다음 세션 시작 프롬프트 — heading + ```text 블록 + 자기 경로 + HEAD 검사 (skill §3 §10, 필수)
status=0
if ! grep -qE '^## [0-9]+\. 다음 세션 시작 프롬프트' "$HANDOFF"; then
  echo "[FAIL] §10 '다음 세션 시작 프롬프트' heading 없음 — assets/handoff-template.md §10 골격을 추가할 것" >&2
  status=1
else
  prompt=$(awk '/^## [0-9]+\. 다음 세션 시작 프롬프트/{f=1} f' "$HANDOFF")
  if ! grep -q '^```text' <<<"$prompt"; then
    echo "[FAIL] §10 에 \`\`\`text 펜스 블록이 없음 — 복붙용 원문 블록 1개 필요" >&2; status=1
  fi
  base=$(basename "$HANDOFF")
  if ! grep -qF "$base" <<<"$prompt"; then
    echo "[FAIL] §10 프롬프트가 자기 파일명($base)을 참조하지 않음 — 'handoff 를 읽고' 지시에 경로 필요" >&2; status=1
  fi
  if ! grep -qE "HEAD ${anchor}|${anchor}" <<<"$prompt"; then
    echo "[WARN] §10 프롬프트에 HEAD anchor($anchor) 가 없음 — 실행 위치 줄에 'HEAD <hash>' 권장"
  fi
  if ! grep -qE '§9 ?의 [0-9]+ ?번' <<<"$prompt"; then
    echo "[WARN] §10 프롬프트에 '§9 의 N번' 진입 스텝 지정이 없음"
  fi
fi

# anchor 가 real HEAD 의 prefix 인지 (또는 vice versa)
if [[ "$real" == "$anchor"* ]] || [[ "$anchor" == "$real"* ]]; then
  echo "[OK] HEAD anchor ($anchor) 정합 with git HEAD ($real) — $HANDOFF"
  exit $status
else
  echo "[FAIL] HEAD anchor ($anchor) ≠ git HEAD ($real)"
  echo "  → $HANDOFF 의 §1 'HEAD' 셀을 \`$real\` 로 정정 필요"
  echo "  (handoff 작성 후 추가 commit 이 생겼다면 §1 commit chain 도 갱신)"
  exit 1
fi
