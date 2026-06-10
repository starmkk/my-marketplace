#!/usr/bin/env bash
# Google AI Edge Gallery 개발 환경 안내
#
# Gallery 소스코드는 ~/.claude/repo/gallery@<version>에서 관리됩니다.
# 소스가 없다면 Claude Code에게 "Gallery 소스 다운로드해줘"라고 요청하세요.

set -euo pipefail

echo ""
echo "================================================================="
echo "[gallery] Gallery 환경 안내"
echo "================================================================="
echo ""
echo "Gallery 소스 위치 확인:"

if [ -d "$HOME/.claude/repo" ]; then
  GALLERY_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "gallery@*" -type d 2>/dev/null || true)
  if [ -n "$GALLERY_DIRS" ]; then
    echo ""
    echo "  발견된 Gallery 소스:"
    echo "$GALLERY_DIRS" | while read -r d; do
      echo "    $d"
    done
  else
    echo "  ~/.claude/repo에 Gallery 소스가 없습니다."
    echo "  Claude Code에게 'Gallery 소스 다운로드해줘'라고 요청하세요."
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'Gallery 소스 다운로드해줘'라고 요청하세요."
fi

echo ""
echo "================================================================="
