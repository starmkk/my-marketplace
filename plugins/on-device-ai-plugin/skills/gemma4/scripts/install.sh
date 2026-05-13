#!/usr/bin/env bash
# Gemma 4 모델 경로 환경변수 검증
#
# 선택 환경변수:
#   GEMMA4_MODEL_PATH  Gemma 4 모델 디렉토리 절대경로
#
# 미설정 시에는 레퍼런스 스킬로만 사용 가능합니다.
# gemma4-asr-qa 스킬의 GEMMA4_MODEL_PATH와 동일한 환경변수를 공유합니다.
#
# 모델 다운로드:
#   pip install huggingface_hub
#   huggingface-cli download google/gemma-4-E2B-it --local-dir /path/to/gemma-4-E2B-it

set -euo pipefail

_detect_rc() {
  local sh="${SHELL:-}"
  case "$sh" in
    *zsh)  echo "$HOME/.zshrc zsh" ;;
    *bash) echo "$HOME/.bashrc bash" ;;
    *fish) echo "$HOME/.config/fish/config.fish fish" ;;
    *)     echo "$HOME/.zshrc zsh" ;;
  esac
}

bar="======================================================================"

# GEMMA4_MODEL_PATH 검증
if [ -z "${GEMMA4_MODEL_PATH:-}" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "[gemma4] GEMMA4_MODEL_PATH 미설정 — 레퍼런스 스킬로만 사용합니다."
  echo ""
  echo "  로컬 모델 디렉토리가 있다면 아래 명령으로 등록하세요:"
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux GEMMA4_MODEL_PATH /absolute/path/to/gemma-4-E2B-it"
  else
    echo "  echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> $RC_FILE"
    echo "  source $RC_FILE"
  fi
  echo ""
  echo "  모델 다운로드 방법:"
  echo "  huggingface-cli download google/gemma-4-E2B-it --local-dir /absolute/path/to/gemma-4-E2B-it"
  echo ""
  exit 0
fi

# 경로 expansion 후 존재 검증
MODEL_PATH="${GEMMA4_MODEL_PATH/#\~/$HOME}"
if [ ! -d "$MODEL_PATH" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "$bar"
  echo "[gemma4] GEMMA4_MODEL_PATH 경로가 존재하지 않아 실행을 중단합니다."
  echo "$bar"
  echo ""
  echo "[오류]  GEMMA4_MODEL_PATH=$GEMMA4_MODEL_PATH"
  echo "        디렉토리가 존재하지 않습니다."
  echo ""
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)"
  echo ""
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux GEMMA4_MODEL_PATH /absolute/path/to/gemma-4-E2B-it"
  else
    echo "  echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> $RC_FILE"
    echo "  source $RC_FILE"
  fi
  echo ""
  echo "환경변수 수정 후 동일 명령을 다시 실행해 주세요."
  echo "$bar"
  echo ""
  exit 2
fi

echo ""
echo "================================================================="
echo "[OK] GEMMA4_MODEL_PATH=$MODEL_PATH"
echo ""
echo "모델 파일:"
ls -lh "$MODEL_PATH" | head -20 || true
echo "================================================================="
