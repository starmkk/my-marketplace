#!/usr/bin/env bash
# LiteRT-LM 소스코드 경로 환경변수 검증
#
# 선택 환경변수:
#   LITERT_LM_SOURCE_PATH  LiteRT-LM 소스코드 레포 로컬 클론 경로
#
# 미설정 시에는 레퍼런스 스킬로만 사용 가능합니다.
# 레포를 클론했다면 아래와 같이 설정하세요:
#   git clone https://github.com/google-ai-edge/LiteRT-LM
#   export LITERT_LM_SOURCE_PATH=/path/to/LiteRT-LM

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

# LITERT_LM_SOURCE_PATH 검증
if [ -z "${LITERT_LM_SOURCE_PATH:-}" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "[litert-lm] LITERT_LM_SOURCE_PATH 미설정 — 레퍼런스 스킬로만 사용합니다."
  echo ""
  echo "  LiteRT-LM 레포를 클론했다면 아래 명령으로 등록하세요:"
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux LITERT_LM_SOURCE_PATH /path/to/LiteRT-LM"
  else
    echo "  echo 'export LITERT_LM_SOURCE_PATH=/path/to/LiteRT-LM' >> $RC_FILE"
    echo "  source $RC_FILE"
  fi
  echo ""
  echo "  클론 방법:"
  echo "  git clone https://github.com/google-ai-edge/LiteRT-LM"
  echo ""
  exit 0
fi

# 경로 expansion 후 존재 검증
LITERT_LM_PATH="${LITERT_LM_SOURCE_PATH/#\~/$HOME}"
if [ ! -d "$LITERT_LM_PATH" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "$bar"
  echo "[litert-lm] LITERT_LM_SOURCE_PATH 경로가 존재하지 않아 실행을 중단합니다."
  echo "$bar"
  echo ""
  echo "[오류]  LITERT_LM_SOURCE_PATH=$LITERT_LM_SOURCE_PATH"
  echo "        디렉토리가 존재하지 않습니다."
  echo ""
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)"
  echo ""
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux LITERT_LM_SOURCE_PATH /path/to/LiteRT-LM"
  else
    echo "  echo 'export LITERT_LM_SOURCE_PATH=/path/to/LiteRT-LM' >> $RC_FILE"
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
echo "[OK] LITERT_LM_SOURCE_PATH=$LITERT_LM_PATH"
echo ""
echo "주요 디렉토리:"
ls -1 "$LITERT_LM_PATH" 2>/dev/null | head -20 || true
echo "================================================================="
