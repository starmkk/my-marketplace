#!/usr/bin/env bash
# LiteRT-LM 개발 환경 안내
#
# LiteRT-LM 소스코드는 ~/.claude/repo/LiteRT-LM@<version>에서 관리됩니다.
# 소스가 없다면 Claude Code에게 "LiteRT-LM 소스 다운로드해줘"라고 요청하세요.

set -euo pipefail

echo ""
echo "================================================================="
echo "[litert-lm] LiteRT-LM 환경 안내"
echo "================================================================="
echo ""
echo "LiteRT-LM 소스 위치 확인:"

if [ -d "$HOME/.claude/repo" ]; then
  LITERT_LM_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "LiteRT-LM@*" -type d 2>/dev/null || true)
  if [ -n "$LITERT_LM_DIRS" ]; then
    echo ""
    echo "  발견된 LiteRT-LM 소스:"
    echo "$LITERT_LM_DIRS" | while read -r d; do
      echo "    $d"
    done
  else
    echo "  ~/.claude/repo에 LiteRT-LM 소스가 없습니다."
    echo "  Claude Code에게 'LiteRT-LM 소스 다운로드해줘'라고 요청하세요."
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'LiteRT-LM 소스 다운로드해줘'라고 요청하세요."
fi

echo ""
echo "================================================================="
