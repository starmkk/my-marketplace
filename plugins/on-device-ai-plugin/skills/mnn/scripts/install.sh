#!/usr/bin/env bash
# MNN 소스코드 경로 환경변수 검증
#
# 필수 환경변수:
#   MNN_SOURCE_PATH  MNN 소스코드 레포 로컬 클론 경로
#
# 미설정 시 실행이 즉시 중단됩니다.
# 클론 방법:
#   git clone https://github.com/alibaba/MNN
#   export MNN_SOURCE_PATH=/path/to/MNN

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

# MNN_SOURCE_PATH 검증
if [ -z "${MNN_SOURCE_PATH:-}" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "$bar"
  echo "[mnn] 환경변수가 올바르게 설정되지 않아 실행을 중단합니다."
  echo "$bar"
  echo ""
  echo "[누락된 환경변수]"
  echo "  - MNN_SOURCE_PATH  (필수)"
  echo "      MNN 소스코드 레포 로컬 클론 경로"
  echo ""
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)"
  echo ""
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux MNN_SOURCE_PATH /path/to/MNN"
  else
    echo "  echo 'export MNN_SOURCE_PATH=/path/to/MNN' >> $RC_FILE"
    echo "  source $RC_FILE"
  fi
  echo ""
  echo "  클론 방법: git clone https://github.com/alibaba/MNN"
  echo ""
  echo "환경변수 설정 후 동일 명령을 다시 실행해 주세요."
  echo "$bar"
  echo ""
  exit 2
fi

# 경로 expansion 후 존재 검증
MNN_PATH="${MNN_SOURCE_PATH/#\~/$HOME}"
if [ ! -d "$MNN_PATH" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  echo ""
  echo "$bar"
  echo "[mnn] MNN_SOURCE_PATH 경로가 존재하지 않아 실행을 중단합니다."
  echo "$bar"
  echo ""
  echo "[오류]  MNN_SOURCE_PATH=$MNN_SOURCE_PATH"
  echo "        디렉토리가 존재하지 않습니다."
  echo ""
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)"
  echo ""
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux MNN_SOURCE_PATH /path/to/MNN"
  else
    echo "  echo 'export MNN_SOURCE_PATH=/path/to/MNN' >> $RC_FILE"
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
echo "[OK] MNN_SOURCE_PATH=$MNN_PATH"
echo ""
echo "주요 디렉토리:"
ls -1 "$MNN_PATH" 2>/dev/null | head -20 || true
echo ""
echo "다음 스크립트를 사용할 수 있습니다:"
echo "  scripts/build_android.sh  — Android용 MNN 빌드"
echo "  scripts/export_llm.py     — LLM → MNN 포맷 변환"
echo "  scripts/convert_model.py  — 일반 모델 → MNN 변환"
echo "================================================================="
