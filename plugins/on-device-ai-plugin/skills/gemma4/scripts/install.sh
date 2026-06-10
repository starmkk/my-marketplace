#!/usr/bin/env bash
# Gemma 4 개발 환경 안내
#
# Gemma 4 모델은 ~/.claude/repo/gemma-4-<variant>에서 관리됩니다.
# 모델이 없다면 Claude Code에게 "Gemma 4 모델 다운로드해줘"라고 요청하세요.

set -euo pipefail

echo ""
echo "================================================================="
echo "[gemma4] Gemma 4 환경 안내"
echo "================================================================="
echo ""
echo "Gemma 4 모델 위치 확인:"

if [ -d "$HOME/.claude/repo" ]; then
  GEMMA_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "gemma-4-*" -type d 2>/dev/null || true)
  if [ -n "$GEMMA_DIRS" ]; then
    echo ""
    echo "  발견된 Gemma 4 모델:"
    echo "$GEMMA_DIRS" | while read -r d; do
      echo "    $d"
    done
  else
    echo "  ~/.claude/repo에 Gemma 4 모델이 없습니다."
    echo "  Claude Code에게 'Gemma 4 모델 다운로드해줘'라고 요청하세요."
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'Gemma 4 모델 다운로드해줘'라고 요청하세요."
fi

echo ""
echo "다운로드 방법:"
echo "  pip install huggingface_hub"
echo "  huggingface-cli download google/gemma-4-E2B-it \\"
echo "    --local-dir ~/.claude/repo/gemma-4-E2B-it"
echo "================================================================="
