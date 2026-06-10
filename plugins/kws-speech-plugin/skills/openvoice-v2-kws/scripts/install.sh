#!/usr/bin/env bash
# OpenVoice V2 + MeloTTS 환경 구축
#
# OpenVoice 소스코드는 ~/.claude/repo/OpenVoice@<version>에서 관리됩니다.
# 소스가 없다면 Claude Code에게 "OpenVoice 소스 다운로드해줘"라고 요청하세요.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_DIR="$HOME/.claude/venvs/openvoice"

echo ""
echo "================================================================="
echo "[openvoice-v2-kws] OpenVoice 환경 안내"
echo "================================================================="
echo ""
echo "OpenVoice 소스 위치 확인:"

SRC_DIR=""
if [ -d "$HOME/.claude/repo" ]; then
  OV_DIRS=$(find "$HOME/.claude/repo" -maxdepth 1 -name "OpenVoice@*" -type d 2>/dev/null || true)
  if [ -n "$OV_DIRS" ]; then
    echo ""
    echo "  발견된 OpenVoice 소스:"
    echo "$OV_DIRS" | while read -r d; do
      echo "    $d"
    done
    SRC_DIR=$(echo "$OV_DIRS" | head -1)
  else
    echo "  ~/.claude/repo에 OpenVoice 소스가 없습니다."
    echo "  Claude Code에게 'OpenVoice 소스 다운로드해줘'라고 요청하세요."
    exit 0
  fi
else
  echo "  ~/.claude/repo 디렉토리가 없습니다."
  echo "  Claude Code에게 'OpenVoice 소스 다운로드해줘'라고 요청하세요."
  exit 0
fi

CKPT_DIR="$SRC_DIR/checkpoints_v2"

echo ""
echo "venv 위치: $ENV_DIR"
echo "소스: $SRC_DIR"
echo "체크포인트: $CKPT_DIR"
echo ""
echo "환경 구축을 시작합니다..."

# 1. venv
mkdir -p "$(dirname "$ENV_DIR")"
if [ ! -d "$ENV_DIR" ]; then
  echo "[STEP 1/6] venv 생성"
  python3 -m venv "$ENV_DIR"
else
  echo "[STEP 1/6] venv 재사용"
fi
# shellcheck disable=SC1091
source "$ENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# 2. OpenVoice 설치
echo "[STEP 2/6] OpenVoice 설치: $SRC_DIR"
cd "$SRC_DIR"
pip install -e .

# 3. MeloTTS (base TTS)
echo "[STEP 3/6] MeloTTS 설치 (base TTS)"
pip install git+https://github.com/myshell-ai/MeloTTS.git

# 4. unidic
echo "[STEP 4/6] unidic 다운로드"
python -m unidic download || {
  echo "[WARN] unidic 다운로드 실패 — unidic-lite로 대체"
  pip install unidic-lite
}

# 5. checkpoints_v2 다운로드
echo "[STEP 5/6] OpenVoice V2 checkpoints 다운로드"
mkdir -p "$CKPT_DIR"
if [ ! -f "$CKPT_DIR/converter/checkpoint.pth" ]; then
  cd "$SRC_DIR"
  ZIP_PATH="checkpoints_v2_0417.zip"
  if [ ! -f "$ZIP_PATH" ]; then
    if command -v wget >/dev/null 2>&1; then
      wget -O "$ZIP_PATH" "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
    else
      curl -L -o "$ZIP_PATH" "https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
    fi
  fi
  unzip -o "$ZIP_PATH" -d "$SRC_DIR"
  echo "[STEP 5/6] 압축 해제 완료. 필요 시 zip 수동 삭제: $SRC_DIR/$ZIP_PATH"
else
  echo "[STEP 5/6] checkpoints_v2 이미 존재"
fi

# 6. 추가 의존성
echo "[STEP 6/6] 추가 의존성 설치"
pip install soundfile librosa numpy scipy pyyaml tqdm

# 검증
echo ""
echo "================================================================="
echo "[VERIFY] 한국어 base speaker embedding 확인"
KR_SE="$CKPT_DIR/base_speakers/ses/kr.pth"
if [ -f "$KR_SE" ]; then
  echo "[OK] $KR_SE 존재"
else
  echo "[WARN] $KR_SE 없음. checkpoint zip 구조가 변경됐을 수 있음."
  find "$CKPT_DIR" -name '*.pth' | head -5 || true
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
echo "  cd $SKILL_DIR"
echo "  python scripts/clone_synthesize.py \\"
echo "    --text '오케이 케이티' \\"
echo "    --reference /path/to/ref.wav \\"
echo "    --output /tmp/test.wav"
echo "================================================================="
