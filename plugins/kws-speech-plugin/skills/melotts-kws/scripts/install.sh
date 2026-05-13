#!/usr/bin/env bash
# MeloTTS-KWS 환경 구축 스크립트
# 위치: ~/Documents/claude/skills/melotts-kws/scripts/install.sh
# 사용: bash scripts/install.sh

set -euo pipefail

# ===== 사용자 환경 설정 =====
SKILL_DIR="${MELOTTS_KWS_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_DIR="${MELO_ENV_DIR:-$HOME/Documents/work_2026/KWS/melotts_env}"
SRC_DIR="${MELO_SRC_DIR:-$HOME/Documents/work_2026/KWS/MeloTTS}"
PY_BIN="${PYTHON_BIN:-python3.10}"   # 3.9~3.11 권장. 3.12는 unidic 호환성 이슈 있음

echo "[INFO] venv 위치: $ENV_DIR"
echo "[INFO] MeloTTS 소스 위치: $SRC_DIR"
echo "[INFO] Python: $PY_BIN"

# ===== 1. Python venv 생성 =====
if [ ! -d "$ENV_DIR" ]; then
  echo "[STEP 1/5] venv 생성"
  "$PY_BIN" -m venv "$ENV_DIR"
else
  echo "[STEP 1/5] venv 이미 존재 — 재사용"
fi

# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# ===== 2. MeloTTS 클론 =====
if [ ! -d "$SRC_DIR" ]; then
  echo "[STEP 2/5] MeloTTS clone"
  mkdir -p "$(dirname "$SRC_DIR")"
  git clone https://github.com/myshell-ai/MeloTTS.git "$SRC_DIR"
else
  echo "[STEP 2/5] MeloTTS 이미 클론됨 — git pull"
  (cd "$SRC_DIR" && git pull --ff-only || true)
fi

# ===== 3. 의존성 설치 =====
echo "[STEP 3/5] MeloTTS 및 의존성 설치"
cd "$SRC_DIR"
# torch는 macOS에서 기본 wheel을 사용 (MPS 지원). Linux/CUDA는 별도 처리 필요.
pip install -e .

# 추가 의존성: 16k 리샘플링, augmentation, manifest 생성용
pip install soundfile librosa numpy scipy pyyaml tqdm

# ===== 4. unidic 다운로드 (일본어 모듈이지만 import 시 필요) =====
echo "[STEP 4/5] unidic 다운로드"
python -m unidic download || {
  echo "[WARN] unidic download 실패 — unidic-lite로 대체 시도"
  pip install unidic-lite
}

# ===== 5. 한국어 모델 사전 다운로드 (선택) =====
echo "[STEP 5/5] MeloTTS-Korean 모델 사전 다운로드"
python - <<'PY'
import os
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
from melo.api import TTS
print("Loading KR model (first run will download weights)...")
tts = TTS(language='KR', device='cpu')
print("[OK] KR model loaded. spk2id =", tts.hps.data.spk2id)
PY

echo ""
echo "================================================================="
echo "[DONE] 설치 완료."
echo ""
echo "사용하려면:"
echo "  source $ENV_DIR/bin/activate"
echo "  cd $SKILL_DIR"
echo "  python scripts/synthesize.py --text '오케이 케이티' --output /tmp/test.wav"
echo "================================================================="
