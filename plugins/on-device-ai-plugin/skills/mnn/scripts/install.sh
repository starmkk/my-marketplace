#!/usr/bin/env bash
# MNN 개발 환경 안내
#
# MNN 소스코드는 ~/.claude/repo/MNN@<version>에서 관리됩니다.
# 소스가 없다면 Claude Code에게 "MNN 소스 다운로드해줘"라고 요청하세요.
#
# 사용 예:
#   python scripts/export_llm.py --model Qwen/Qwen2.5-7B \
#     --mnn-source ~/.claude/repo/MNN@3.5.0
#
#   ./scripts/build_android.sh --abi arm64-v8a \
#     --mnn-source ~/.claude/repo/MNN@3.5.0

set -euo pipefail

echo ""
echo "================================================================="
echo "[mnn] MNN 환경 안내"
echo "================================================================="
echo ""
echo "MNN 소스 위치 확인:"

if [ -d "$HOME/.claude/repo" ]; then
  MNN_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "MNN@*" -type d 2>/dev/null || true)
  if [ -n "$MNN_DIRS" ]; then
    echo ""
    echo "  발견된 MNN 소스:"
    echo "$MNN_DIRS" | while read -r d; do
      echo "    $d"
    done
    echo ""
    echo "  --mnn-source 인자 예시:"
    FIRST_DIR=$(echo "$MNN_DIRS" | head -1)
    echo "    --mnn-source $FIRST_DIR"
  else
    echo "  ~/.claude/repo에 MNN 소스가 없습니다."
    echo "  Claude Code에게 'MNN 소스 다운로드해줘'라고 요청하세요."
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'MNN 소스 다운로드해줘'라고 요청하세요."
fi

echo ""
echo "다음 스크립트를 사용할 수 있습니다:"
echo "  scripts/build_android.sh --mnn-source <path>  — Android용 MNN 빌드"
echo "  scripts/export_llm.py --mnn-source <path>     — LLM → MNN 포맷 변환"
echo "  scripts/convert_model.py --mnn-source <path>  — 일반 모델 → MNN 변환"
echo "================================================================="
