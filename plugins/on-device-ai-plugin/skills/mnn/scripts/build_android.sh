#!/usr/bin/env bash

##
# MNN Android Build Script
#
# Automates building MNN for Android with common configurations
#
# Usage:
#   ./build_android.sh [OPTIONS]
#
# Options:
#   --mnn-source <path>   MNN source directory (required)
#   --abi <abi>           Target ABI: arm64-v8a (default), armeabi-v7a, or both
#   --gpu                 Enable GPU support (OpenCL)
#   --vulkan              Enable Vulkan support
#   --llm                 Enable LLM support
#   --mini                Enable minimal build (smaller size)
#   --ndk <path>          Path to Android NDK
#   --output <path>       Output directory (default: ./build_android)
#
# Examples:
#   ./build_android.sh --mnn-source ~/.claude/repo/MNN@3.5.0 --abi arm64-v8a --gpu
#   ./build_android.sh --mnn-source ~/.claude/repo/MNN@3.5.0 --abi both --llm --gpu
##

set -e

# Default values
ABI="arm64-v8a"
ENABLE_GPU=false
ENABLE_VULKAN=false
ENABLE_LLM=false
ENABLE_MINI=false
NDK_PATH="${ANDROID_NDK:-}"
OUTPUT_DIR="./build_android"
MNN_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mnn-source)
            MNN_DIR="$2"
            shift 2
            ;;
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

# MNN_DIR 검증
if [ -z "$MNN_DIR" ]; then
    echo "Error: --mnn-source is required"
    echo "Usage: $0 --mnn-source /path/to/MNN [options]"
    echo "Example: $0 --mnn-source ~/.claude/repo/MNN@3.5.0 --abi arm64-v8a"
    exit 1
fi

MNN_DIR="${MNN_DIR/#\~/$HOME}"
if [ ! -d "$MNN_DIR" ]; then
    echo "Error: MNN source directory not found: $MNN_DIR"
    exit 1
fi

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
echo "MNN Source:  $MNN_DIR"
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
