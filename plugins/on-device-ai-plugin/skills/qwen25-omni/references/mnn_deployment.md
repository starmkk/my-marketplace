# MNN Mobile Deployment Guide

## Overview

MNN (Mobile Neural Network) is Alibaba's lightweight deep learning framework optimized for mobile and embedded devices. Qwen2.5-Omni models have been converted to MNN format for edge deployment.

## Pre-converted Models

Download from Hugging Face or ModelScope:

**Hugging Face:**
- 7B: https://huggingface.co/taobao-mnn/Qwen2.5-Omni-7B-MNN
- 3B: https://huggingface.co/taobao-mnn/Qwen2.5-Omni-3B-MNN

**ModelScope:**
- 7B: https://modelscope.cn/models/MNN/Qwen2.5-Omni-7B-MNN
- 3B: https://modelscope.cn/models/MNN/Qwen2.5-Omni-3B-MNN

## Build MNN from Source

```bash
# Clone MNN repository
git clone https://github.com/alibaba/MNN.git
cd MNN

# Create build directory
mkdir build && cd build

# Configure with LLM support
cmake .. \
  -DMNN_LOW_MEMORY=true \
  -DMNN_CPU_WEIGHT_DEQUANT_GEMM=true \
  -DMNN_BUILD_LLM=true \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=true

# Build
make -j
```

## Run Inference

```bash
# Basic inference
./llm_demo /path/to/Qwen2.5-Omni-3B-MNN/config.json prompt.txt
```

## Performance Benchmarks

### Snapdragon 8 Gen 1 (7B Model)

| Metric | Value |
|--------|-------|
| Memory Peak | 5.8 GB |
| Thinker Prefill | 25.58 tok/s |
| Thinker Decode | 8.35 tok/s |
| Talker Prefill | 17.21 tok/s |
| Talker Decode | 18.75 tok/s |
| Code2Wav | 20.83 tok/s |

### Snapdragon 8 Elite (7B Model)

| Metric | Value |
|--------|-------|
| Memory Peak | 5.8 GB |
| Thinker Prefill | 46.32 tok/s |
| Thinker Decode | 11.52 tok/s |
| Talker Prefill | 97.77 tok/s |
| Talker Decode | 38.65 tok/s |
| Code2Wav | 27.36 tok/s |

### Snapdragon 8 Gen 1 (3B Model)

| Metric | Value |
|--------|-------|
| Memory Peak | 3.6 GB |
| Thinker Prefill | 54.31 tok/s |
| Thinker Decode | 15.84 tok/s |
| Talker Prefill | 34.58 tok/s |
| Talker Decode | 51.90 tok/s |
| Code2Wav | 28.45 tok/s |

### Snapdragon 8 Elite (3B Model)

| Metric | Value |
|--------|-------|
| Memory Peak | 3.6 GB |
| Thinker Prefill | 55.16 tok/s |
| Thinker Decode | 23.31 tok/s |
| Talker Prefill | 217.82 tok/s |
| Talker Decode | 62.34 tok/s |
| Code2Wav | 27.36 tok/s |

## Android Integration

### Build for Android

```bash
cd MNN/project/android
mkdir build_64
../build_64.sh "-DMNN_OPENCL=ON -DMNN_ARM82=ON -DMNN_BUILD_LLM=ON"
```

### JNI Wrapper

```java
public class QwenOmniWrapper {
    static {
        System.loadLibrary("MNN");
        System.loadLibrary("MNN_Express");
    }
    
    public native long initModel(String modelPath);
    public native String generate(long handle, String input);
    public native void destroyModel(long handle);
}
```

## iOS Integration

### Build for iOS

```bash
cd MNN
sh package_scripts/ios/buildiOS.sh \
  "-DMNN_ARM82=ON -DMNN_BUILD_LLM=ON -DMNN_METAL=ON"
```

### Swift Wrapper

```swift
class QwenOmniModel {
    private var modelHandle: UnsafeMutableRawPointer?
    
    func load(path: String) {
        modelHandle = mnn_load_model(path)
    }
    
    func generate(input: String) -> String {
        return mnn_generate(modelHandle, input)
    }
}
```

## MNN Chat App

Pre-built Android app available:
https://github.com/alibaba/MNN/tree/master/apps/Android/MnnLlmChat

Features:
- Text-to-text chat
- Image-to-text understanding
- Audio-to-text transcription
- Text-to-image generation
- Qwen2.5-Omni 3B and 7B support

## Optimization Tips

1. **Use 3B model** for better mobile performance
2. **Enable GPU acceleration** with OpenCL (Android) or Metal (iOS)
3. **Use 4-bit quantization** for reduced memory
4. **Enable low memory mode** with MNN_LOW_MEMORY=true
5. **Profile on real devices** - emulators not representative

## Troubleshooting

### Build Fails

Solution: Ensure NDK and CMake are properly installed

### Out of Memory on Device

Solutions:
1. Use 3B model instead of 7B
2. Reduce max_new_tokens
3. Close background apps
4. Use GPU offloading

### Slow Inference

Solutions:
1. Enable GPU acceleration
2. Use ARM v8.2 optimizations
3. Reduce input size
4. Use quantized model

## Additional Resources

- MNN GitHub: https://github.com/alibaba/MNN
- MNN Documentation: https://mnn-docs.readthedocs.io
- MNN Chat App: https://github.com/alibaba/MNN/tree/master/apps/Android/MnnLlmChat
