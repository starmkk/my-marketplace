#!/bin/bash
# Install Qwen2.5-Omni dependencies
#
# 필수 환경변수:
#   QWEN25_OMNI_MODEL_PATH  Qwen2.5-Omni 로컬 모델 디렉토리 절대경로

set -e

# ===== QWEN25_OMNI_MODEL_PATH 검증 게이트 =====
_detect_rc() {
  local sh="${SHELL:-}"
  case "$sh" in
    *zsh)  echo "$HOME/.zshrc zsh" ;;
    *bash) echo "$HOME/.bashrc bash" ;;
    *fish) echo "$HOME/.config/fish/config.fish fish" ;;
    *)     echo "$HOME/.zshrc zsh" ;;
  esac
}

if [ -z "${QWEN25_OMNI_MODEL_PATH:-}" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  bar="======================================================================"
  echo "" >&2
  echo "$bar" >&2
  echo "[qwen25-omni] 환경변수가 올바르게 설정되지 않아 실행을 중단합니다." >&2
  echo "$bar" >&2
  echo "" >&2
  echo "[누락된 환경변수]" >&2
  echo "  - QWEN25_OMNI_MODEL_PATH  (필수)" >&2
  echo "      Qwen2.5-Omni 로컬 모델 디렉토리 절대경로" >&2
  echo "" >&2
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)" >&2
  echo "" >&2
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux QWEN25_OMNI_MODEL_PATH /absolute/path/to/Qwen2.5-Omni-7B" >&2
  else
    echo "  echo 'export QWEN25_OMNI_MODEL_PATH=/absolute/path/to/Qwen2.5-Omni-7B' >> $RC_FILE" >&2
    echo "  source $RC_FILE" >&2
  fi
  echo "" >&2
  echo "  모델 다운로드:" >&2
  echo "  huggingface-cli download Qwen/Qwen2.5-Omni-7B --local-dir /absolute/path/to/Qwen2.5-Omni-7B" >&2
  echo "" >&2
  echo "환경변수 설정 후 동일 명령을 다시 실행해 주세요." >&2
  echo "$bar" >&2
  echo "" >&2
  exit 2
fi

MODEL_PATH="${QWEN25_OMNI_MODEL_PATH/#\~/$HOME}"
if [ ! -d "$MODEL_PATH" ]; then
  echo "[qwen25-omni] QWEN25_OMNI_MODEL_PATH=$QWEN25_OMNI_MODEL_PATH — 디렉토리가 존재하지 않습니다." >&2
  exit 2
fi

echo "==================================="
echo "Qwen2.5-Omni Dependency Installation"
echo "==================================="
echo ""
echo "[INFO] 모델 경로: $MODEL_PATH"

echo ""
echo "Installing core dependencies..."
pip install transformers==4.52.3
pip install accelerate
pip install qwen-omni-utils[decord] -U
pip install soundfile

echo ""
echo "Core dependencies installed successfully!"

echo ""
read -p "Install FlashAttention-2? (recommended, y/n): " install_flash
if [ "$install_flash" = "y" ] || [ "$install_flash" = "Y" ]; then
    echo "Installing FlashAttention-2..."
    pip install -U flash-attn --no-build-isolation
    echo "FlashAttention-2 installed!"
fi

echo ""
read -p "Install vLLM dependencies? (optional, y/n): " install_vllm
if [ "$install_vllm" = "y" ] || [ "$install_vllm" = "Y" ]; then
    echo "Installing vLLM dependencies..."
    pip install setuptools_scm torchdiffeq resampy x_transformers
    echo "vLLM dependencies installed!"
fi

echo ""
read -p "Install quantization libraries? (optional, y/n): " install_quant
if [ "$install_quant" = "y" ] || [ "$install_quant" = "Y" ]; then
    echo "Installing GPTQ and AWQ..."
    pip install gptqmodel==2.0.0
    pip install autoawq==0.2.9
    echo "Quantization libraries installed!"
fi

echo ""
echo "==================================="
echo "Installation complete!"
echo "==================================="
