#!/usr/bin/env bash
# OpenVoice V2 + MeloTTS 환경 구축
# 위치: ~/Documents/claude/skills/openvoice-v2-kws/scripts/install.sh

set -euo pipefail

# ===== 사용자 환경 설정 =====
SKILL_DIR="${OPENVOICE_V2_KWS_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
ENV_DIR="${OPENVOICE_ENV_DIR:-$HOME/Documents/work_2026/KWS/openvoice_env}"
SRC_DIR="${OPENVOICE_SRC_DIR:-$HOME/Documents/work_2026/KWS/OpenVoice}"
CKPT_DIR="${OPENVOICE_CKPT_DIR:-$SRC_DIR/checkpoints_v2}"
PY_BIN="${PYTHON_BIN:-python3.9}"   # OpenVoice 공식 권장 Python 3.9

echo "[INFO] venv 위치: $ENV_DIR"
echo "[INFO] OpenVoice 소스: $SRC_DIR"
echo "[INFO] 체크포인트: $CKPT_DIR"

# ===== 1. venv =====
if [ ! -d "$ENV_DIR" ]; then
  echo "[STEP 1/6] venv 생성"
  "$PY_BIN" -m venv "$ENV_DIR"
else
  echo "[STEP 1/6] venv 재사용"
fi
# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# ===== 2. OpenVoice clone =====
if [ ! -d "$SRC_DIR" ]; then
  echo "[STEP 2/6] OpenVoice clone"
  mkdir -p "$(dirname "$SRC_DIR")"
  git clone https://github.com/myshell-ai/OpenVoice.git "$SRC_DIR"
else
  echo "[STEP 2/6] OpenVoice 이미 존재 — git pull"
  (cd "$SRC_DIR" && git pull --ff-only || true)
fi

cd "$SRC_DIR"
pip install -e .

# ===== 3. MeloTTS (base TTS) =====
echo "[STEP 3/6] MeloTTS 설치 (base TTS)"
pip install git+https://github.com/myshell-ai/MeloTTS.git

# ===== 4. unidic =====
echo "[STEP 4/6] unidic 다운로드"
python -m unidic download || {
  echo "[WARN] unidic 다운로드 실패 — unidic-lite로 대체"
  pip install unidic-lite
}

# ===== 5. checkpoints_v2 다운로드 =====
echo "[STEP 5/6] OpenVoice V2 checkpoints 다운로드"
mkdir -p "$CKPT_DIR"
if [ ! -f "$CKPT_DIR/converter/checkpoint.pth" ]; then
  cd "$(dirname "$CKPT_DIR")"
  ZIP_PATH="checkpoints_v2_0417.zip"
  if [ ! -f "$ZIP_PATH" ]; then
    if command -v wget >/dev/null 2>&1; then
      wget -O "$ZIP_PATH" "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
    else
      curl -L -o "$ZIP_PATH" "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
    fi
  fi
  unzip -o "$ZIP_PATH" -d "$(dirname "$CKPT_DIR")"
  # 다운로드 zip은 checkpoints_v2/ 디렉토리를 만든다.
  echo "[STEP 5/6] 압축 해제 완료. 필요 시 zip 파일 수동 삭제: $ZIP_PATH"
else
  echo "[STEP 5/6] checkpoints_v2 이미 존재"
fi

# ===== 6. 추가 의존성 =====
echo "[STEP 6/6] 추가 의존성 설치"
pip install soundfile librosa numpy scipy pyyaml tqdm

# ===== 검증 =====
echo ""
echo "================================================================="
echo "[VERIFY] 한국어 base speaker embedding 확인"
KR_SE="$CKPT_DIR/base_speakers/ses/kr.pth"
if [ -f "$KR_SE" ]; then
  echo "[OK] $KR_SE 존재"
else
  echo "[WARN] $KR_SE 없음. checkpoint zip 구조가 변경됐을 수 있음."
  echo "       $(find "$CKPT_DIR" -name '*.pth' | head -10)"
fi

echo "[VERIFY] converter 체크포인트"
if [ -f "$CKPT_DIR/converter/checkpoint.pth" ]; then
  echo "[OK] converter/checkpoint.pth 존재"
else
  echo "[ERR] converter/checkpoint.pth 없음. install 재시도 필요."
  exit 1
fi

echo ""
echo "[DONE] OpenVoice V2 환경 구축 완료."
echo ""
echo "사용법:"
echo "  source $ENV_DIR/bin/activate"
echo "  export OPENVOICE_CKPT_DIR=$CKPT_DIR"
echo "  cd $SKILL_DIR"
echo "  python scripts/clone_synthesize.py \\"
echo "    --text '오케이 케이티' \\"
echo "    --reference /path/to/ref.wav \\"
echo "    --output /tmp/test.wav"
echo "================================================================="
