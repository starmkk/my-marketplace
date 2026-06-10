#!/usr/bin/env bash
# MeloTTS-KWS 환경 구축 스크립트
#
# MeloTTS 소스코드는 ~/.claude/repo/MeloTTS@<version>에서 관리됩니다.
# 소스가 없다면 Claude Code에게 "MeloTTS 소스 다운로드해줘"라고 요청하세요.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$HOME/.claude/venvs/melotts"

echo ""
echo "================================================================="
echo "[melotts-kws] MeloTTS 환경 안내"
echo "================================================================="
echo ""
echo "MeloTTS 소스 위치 확인:"

SRC_DIR=""
if [ -d "$HOME/.claude/repo" ]; then
  MELO_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "MeloTTS@*" -type d 2>/dev/null || true)
  if [ -n "$MELO_DIRS" ]; then
    echo ""
    echo "  발견된 MeloTTS 소스:"
    echo "$MELO_DIRS" | while read -r d; do
      echo "    $d"
    done
    SRC_DIR=$(echo "$MELO_DIRS" | head -1)
  else
    echo "  ~/.claude/repo에 MeloTTS 소스가 없습니다."
    echo "  Claude Code에게 'MeloTTS 소스 다운로드해줘'라고 요청하세요."
    exit 0
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'MeloTTS 소스 다운로드해줘'라고 요청하세요."
  exit 0
fi

echo ""
echo "venv 위치: $ENV_DIR"
echo "사용할 소스: $SRC_DIR"
echo ""
echo "환경 구축을 시작합니다..."

# 1. Python venv 생성
mkdir -p "$(dirname "$ENV_DIR")"
if [ ! -d "$ENV_DIR" ]; then
  echo "[STEP 1/4] venv 생성"
  python3 -m venv "$ENV_DIR"
else
  echo "[STEP 1/4] venv 재사용"
fi

# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# 2. MeloTTS 설치
echo "[STEP 2/4] MeloTTS 설치: $SRC_DIR"
cd "$SRC_DIR"
pip install -e .
pip install soundfile librosa numpy scipy pyyaml tqdm

# 3. unidic 다운로드
echo "[STEP 3/4] unidic 다운로드"
python -m unidic download || {
  echo "[WARN] unidic download 실패 — unidic-lite로 대체"
  pip install unidic-lite
}

# 4. 한국어 모델 사전 다운로드
echo "[STEP 4/4] MeloTTS-Korean 모델 사전 다운로드"
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
