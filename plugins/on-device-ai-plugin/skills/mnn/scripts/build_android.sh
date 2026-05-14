#!/bin/bash

##
# MNN Android Build Script
#
# Automates building MNN for Android with common configurations
#
# 필수 환경변수:
#   MNN_SOURCE_PATH  MNN 소스코드 레포 로컬 클론 경로
#
# Usage:
#   ./build_android.sh [OPTIONS]
#
# Options:
#   --abi <abi>           Target ABI: arm64-v8a (default), armeabi-v7a, or both
#   --gpu                 Enable GPU support (OpenCL)
#   --vulkan              Enable Vulkan support
#   --llm                 Enable LLM support
#   --mini                Enable minimal build (smaller size)
#   --ndk <path>          Path to Android NDK
#   --output <path>       Output directory (default: ./build_android)
#
# Examples:
#   ./build_android.sh --abi arm64-v8a --gpu
#   ./build_android.sh --abi both --llm --gpu
##

set -e

# ===== MNN_SOURCE_PATH 검증 게이트 =====
_detect_rc() {
  local sh="${SHELL:-}"
  case "$sh" in
    *zsh)  echo "$HOME/.zshrc zsh" ;;
    *bash) echo "$HOME/.bashrc bash" ;;
    *fish) echo "$HOME/.config/fish/config.fish fish" ;;
    *)     echo "$HOME/.zshrc zsh" ;;
  esac
}

if [ -z "${MNN_SOURCE_PATH:-}" ]; then
  read -r RC_FILE SHELL_NAME < <(_detect_rc)
  bar="======================================================================"
  echo "" >&2
  echo "$bar" >&2
  echo "[mnn] 환경변수가 올바르게 설정되지 않아 실행을 중단합니다." >&2
  echo "$bar" >&2
  echo "" >&2
  echo "[누락된 환경변수]" >&2
  echo "  - MNN_SOURCE_PATH  (필수)" >&2
  echo "      MNN 소스코드 레포 로컬 클론 경로" >&2
  echo "" >&2
  echo "[설정 방법] (감지된 셸: $SHELL_NAME, 권장 rc 파일: $RC_FILE)" >&2
  echo "" >&2
  if [ "$SHELL_NAME" = "fish" ]; then
    echo "  set -Ux MNN_SOURCE_PATH /path/to/MNN" >&2
  else
    echo "  echo 'export MNN_SOURCE_PATH=/path/to/MNN' >> $RC_FILE" >&2
    echo "  source $RC_FILE" >&2
  fi
  echo "" >&2
  echo "  클론 방법: git clone https://github.com/alibaba/MNN" >&2
  echo "" >&2
  echo "환경변수 설정 후 동일 명령을 다시 실행해 주세요." >&2
  echo "$bar" >&2
  echo "" >&2
  exit 2
fi

MNN_SOURCE_PATH="${MNN_SOURCE_PATH/#\~/$HOME}"
if [ ! -d "$MNN_SOURCE_PATH" ]; then
  echo "[mnn] MNN_SOURCE_PATH=$MNN_SOURCE_PATH — 디렉토리가 존재하지 않습니다." >&2
  exit 2
fi

# Default values
ABI="arm64-v8a"
ENABLE_GPU=false
ENABLE_VULKAN=false
ENABLE_LLM=false
ENABLE_MINI=false
NDK_PATH="${ANDROID_NDK}"
OUTPUT_DIR="./build_android"
MNN_DIR="$MNN_SOURCE_PATH"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --abi)
            ABI="$2"
            shift 2
            ;;
        --gpu)
            ENABLE_GPU=true
            shift
            ;;
        --vulkan)
            ENABLE_VULKAN=true
            shift
            ;;
        --llm)
            ENABLE_LLM=true
            shift
            ;;
        --mini)
            ENABLE_MINI=true
            shift
            ;;
        --ndk)
            NDK_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help)
            head -n 20 "$0" | tail -n +2 | sed 's/^##//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate NDK path
if [ -z "$NDK_PATH" ]; then
    echo "Error: ANDROID_NDK not set"
    echo "Please set ANDROID_NDK environment variable or use --ndk option"
    exit 1
fi

if [ ! -d "$NDK_PATH" ]; then
    echo "Error: NDK path not found: $NDK_PATH"
    exit 1
fi

# Function to build for specific ABI
build_for_abi() {
    local TARGET_ABI=$1
    echo ""
    echo "========================================"
    echo "Building MNN for $TARGET_ABI"
    echo "========================================"
    echo ""
    
    # Determine build script
    if [ "$TARGET_ABI" = "arm64-v8a" ]; then
        BUILD_SCRIPT="build_64.sh"
        BUILD_DIR="${OUTPUT_DIR}/build_64"
    else
        BUILD_SCRIPT="build_32.sh"
        BUILD_DIR="${OUTPUT_DIR}/build_32"
    fi
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Prepare CMake flags
    CMAKE_FLAGS="-DMNN_BUILD_BENCHMARK=OFF"
    CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_BUILD_TEST=OFF"
    CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_USE_LOGCAT=ON"
    
    # Add common optimizations
    CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_ARM82=ON"
    CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_LOW_MEMORY=ON"
    
    # GPU support
    if [ "$ENABLE_GPU" = true ]; then
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_OPENCL=ON"
        echo "Enabling OpenCL GPU support"
    fi
    
    if [ "$ENABLE_VULKAN" = true ]; then
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_VULKAN=ON"
        echo "Enabling Vulkan support"
    fi
    
    # LLM support
    if [ "$ENABLE_LLM" = true ]; then
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_BUILD_LLM=ON"
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_SUPPORT_TRANSFORMER_FUSE=ON"
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_CPU_WEIGHT_DEQUANT_GEMM=ON"
        echo "Enabling LLM support"
    fi
    
    # Minimal build
    if [ "$ENABLE_MINI" = true ]; then
        CMAKE_FLAGS="$CMAKE_FLAGS -DMNN_BUILD_MINI=ON"
        echo "Enabling minimal build"
    fi
    
    # Run build script
    echo "CMake flags: $CMAKE_FLAGS"
    echo ""
    
    cd "$MNN_DIR/project/android"
    ./$BUILD_SCRIPT "$CMAKE_FLAGS"
    
    # Copy libraries
    echo ""
    echo "Copying libraries..."
    LIBS_DIR="${OUTPUT_DIR}/libs/${TARGET_ABI}"
    mkdir -p "$LIBS_DIR"
    
    if [ "$TARGET_ABI" = "arm64-v8a" ]; then
        SOURCE_DIR="${MNN_DIR}/project/android/build_64/libs/arm64-v8a"
    else
        SOURCE_DIR="${MNN_DIR}/project/android/build_32/libs/armeabi-v7a"
    fi
    
    cp -v "${SOURCE_DIR}"/*.so "$LIBS_DIR/" || true
    
    echo ""
    echo "Build complete for $TARGET_ABI"
    echo "Libraries: $LIBS_DIR"
    ls -lh "$LIBS_DIR"
}

# Main build process
echo "========================================"
echo "MNN Android Build Configuration"
echo "========================================"
echo "ABI:         $ABI"
echo "GPU:         $ENABLE_GPU"
echo "Vulkan:      $ENABLE_VULKAN"
echo "LLM:         $ENABLE_LLM"
echo "Minimal:     $ENABLE_MINI"
echo "NDK Path:    $NDK_PATH"
echo "Output Dir:  $OUTPUT_DIR"
echo "========================================"

# Build for specified ABI(s)
if [ "$ABI" = "both" ]; then
    build_for_abi "arm64-v8a"
    build_for_abi "armeabi-v7a"
elif [ "$ABI" = "arm64-v8a" ] || [ "$ABI" = "armeabi-v7a" ]; then
    build_for_abi "$ABI"
else
    echo "Error: Invalid ABI: $ABI"
    echo "Valid options: arm64-v8a, armeabi-v7a, both"
    exit 1
fi

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"
echo ""
echo "Libraries are available at:"
echo "  ${OUTPUT_DIR}/libs/"
echo ""
echo "To use in Android Studio:"
echo "  1. Copy ${OUTPUT_DIR}/libs/ to app/src/main/jniLibs/"
echo "  2. Add System.loadLibrary(\"MNN\") in your Java/Kotlin code"
echo "  3. Create JNI wrapper for native functions"
echo ""
