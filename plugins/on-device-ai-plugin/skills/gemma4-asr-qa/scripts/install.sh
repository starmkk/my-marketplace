#!/usr/bin/env bash
# Gemma 4 E2B-it ASR QA 환경 구축
#
# 필수 환경변수:
#   GEMMA4_MODEL_PATH  Gemma 4 E2B-it 모델 디렉토리 절대경로
#
# 선택 환경변수:
#   GEMMA4_VENV_DIR    venv 위치 (기본: $HOME/.cache/gemma4-asr-qa/venv)
#   PYTHON_BIN         사용할 python 실행파일 (기본: python3)

set -euo pipefail

# ===== 환경변수 검증 게이트 =====

# 현재 셸 추정
_detect_rc() {
  local sh="${SHELL:-}"
  case "$sh" in
    *zsh)  echo "$HOME/.zshrc zsh" ;;
    *bash) echo "$HOME/.bashrc bash" ;;
    *fish) echo "$HOME/.config/fish/config.fish fish" ;;
    *)     echo "$HOME/.zshrc zsh" ;;
  esac
}

_print_setup_guide() {
  local missing="$1"
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  local bar="======================================================================"

  {
    echo ""
    echo "$bar"
    echo "[gemma4-asr-qa] 환경변수가 올바르게 설정되지 않아 실행을 중단합니다."
    echo "$bar"
    echo ""
    echo "[누락/잘못된 환경변수]"
    echo "$missing"
    echo ""
    echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)"
    echo ""
    if [ "$SHELL_NAME" = "fish" ]; then
      echo "  set -Ux GEMMA4_MODEL_PATH /absolute/path/to/gemma-4-E2B-it"
      echo ""
      echo "  # set -Ux는 즉시 영구 반영됩니다."
    else
      echo "  echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> $RC_FILE"
      echo "  source $RC_FILE"
    fi
    echo ""
    echo "환경변수 설정 후 동일 명령을 다시 실행해 주세요."
    echo "$bar"
    echo ""
  } >&2
  exit 2
}

# 필수: GEMMA4_MODEL_PATH
if [ -z "${GEMMA4_MODEL_PATH:-}" ]; then
  _print_setup_guide "  - GEMMA4_MODEL_PATH (필수): Gemma 4 E2B-it 모델 디렉토리 절대경로 — 미설정"
fi

# 경로 expansion 후 존재 검증
MODEL_PATH="${GEMMA4_MODEL_PATH/#\~/$HOME}"
if [ ! -d "$MODEL_PATH" ]; then
  _print_setup_guide "  - GEMMA4_MODEL_PATH=$GEMMA4_MODEL_PATH — 디렉토리가 존재하지 않습니다."
fi

# 선택: GEMMA4_VENV_DIR (기본값은 일반 캐시 경로)
ENV_DIR="${GEMMA4_VENV_DIR:-$HOME/.cache/gemma4-asr-qa/venv}"
PY_BIN="${PYTHON_BIN:-python3}"

echo "[INFO] venv:        $ENV_DIR"
echo "[INFO] 모델 경로:   $MODEL_PATH"
echo "[INFO] python:      $PY_BIN"

# ===== 1. venv =====
if [ ! -d "$ENV_DIR" ]; then
  echo "[STEP 1/4] venv 생성"
  mkdir -p "$(dirname "$ENV_DIR")"
  "$PY_BIN" -m venv "$ENV_DIR"
else
  echo "[STEP 1/4] venv 재사용"
fi
# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# ===== 2. transformers + 의존성 =====
echo "[STEP 2/4] transformers + multimodal 의존성 설치"
# Gemma 4는 latest transformers 필요
pip install -U "transformers>=4.50" torch torchvision accelerate
pip install librosa soundfile numpy

# CER/WER 계산
pip install jiwer

# ===== 3. 모델 경로 검증 =====
echo "[STEP 3/4] 모델 경로 검증"
# 핵심 파일 확인
for f in config.json processor_config.json; do
  if [ ! -f "$MODEL_PATH/$f" ]; then
    echo "[WARN] $MODEL_PATH/$f 없음 (필수 파일일 수 있음)"
  fi
done
echo "[OK] 모델 디렉토리 발견."
ls -lh "$MODEL_PATH" | head -20

# ===== 4. 모델 로드 + ASR 동작 확인 =====
echo "[STEP 4/4] 모델 로드 테스트"
GEMMA4_MODEL_PATH="$MODEL_PATH" python - <<'PY'
import os
import sys
import torch

model_path = os.environ["GEMMA4_MODEL_PATH"]
print(f"[test] loading from {model_path}")

try:
    from transformers import AutoProcessor, AutoModelForMultimodalLM
except ImportError:
    print("[test] AutoModelForMultimodalLM 없음 — AutoModelForImageTextToText 시도")
    from transformers import AutoProcessor, AutoModelForImageTextToText as AutoModelForMultimodalLM

device_map = "auto"
dtype = torch.bfloat16 if torch.cuda.is_available() or torch.backends.mps.is_available() else torch.float32

print(f"[test] dtype={dtype} device_map={device_map}")

processor = AutoProcessor.from_pretrained(model_path)
model = AutoModelForMultimodalLM.from_pretrained(
    model_path,
    dtype=dtype,
    device_map=device_map,
)
print("[OK] 모델 로드 성공")
print(f"     model class: {type(model).__name__}")
print(f"     processor:   {type(processor).__name__}")
print(f"     dtype:       {model.dtype}")
PY

echo ""
echo "================================================================="
echo "[DONE] Gemma 4 ASR QA 환경 구축 완료."
echo ""
echo "사용법:"
echo "  source $ENV_DIR/bin/activate"
echo "  # GEMMA4_MODEL_PATH는 이미 환경변수로 설정되어 있어야 합니다."
echo "  python scripts/transcribe.py --audio /path/to/wav --language Korean"
echo "================================================================="
