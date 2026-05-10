---
name: mnn
description: |
  Alibaba MNN (Mobile Neural Network) 경량 딥러닝 프레임워크 개발 스킬.
  Development skill for MNN (Mobile Neural Network), Alibaba's lightweight deep learning framework.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "MNN", "Mobile Neural Network", "MNN-LLM"
  - "TensorFlow/Caffe/ONNX/PyTorch → MNN 변환", "model conversion to MNN"
  - "Android/iOS MNN 통합", "MNN deployment on mobile"
  - "FP16, Int8, Int4 양자화", "quantization for mobile inference"
  - "CPU/GPU/NPU 백엔드 설정", "backend configuration"
  - "MNN C++/Python API", "MNN inference and training"
  - "MNN 빌드/배포/런타임 트러블슈팅", "troubleshoot MNN build/runtime"

  관련 스킬 (Related skills):
  - `qwen25-omni`: Qwen2.5-Omni를 모바일/엣지에 MNN으로 배포할 때.
  - `litert`: 대안이 되는 온디바이스 추론 프레임워크.
---

# MNN Development Skill

## Overview

MNN is a highly efficient and lightweight deep learning framework for mobile and embedded devices. This skill provides comprehensive guidance for converting models, building MNN for different platforms, deploying LLMs, and optimizing models for production use.

## Quick Reference

**Core Tasks:**
- **Model Conversion**: See [Model Conversion Workflow](#model-conversion-workflow)
- **Android Integration**: See `references/android_integration.md`
- **iOS Integration**: See `references/ios_integration.md`
- **LLM Deployment**: See `references/llm_deployment.md`
- **Optimization**: See `references/optimization.md`

**Architecture Details**: See `references/architecture.md`
**Operator Support**: See `references/operators.md`

## Model Conversion Workflow

### Step 1: Verify Model Compatibility

Check if your model's operators are supported:

**For ONNX models:**
```bash
# Export model operator info
python -c "import onnx; model = onnx.load('model.onnx'); print([node.op_type for node in model.graph.node])"
```

**For TensorFlow models:**
```bash
# Use TensorFlow's saved_model_cli
saved_model_cli show --dir model_dir --all
```

If unsupported operators are found, see `references/operators.md` for alternatives or custom operator implementation.

### Step 2: Convert Model to MNN

**Basic conversion:**

```bash
./MNNConvert \
  -f ONNX \                        # Framework: TF, CAFFE, ONNX, TORCHSCRIPT
  --modelFile model.onnx \         # Input model
  --MNNModel model.mnn \           # Output MNN model
  --bizCode MNN                    # Business identifier
```

**With graph optimizations:**

```bash
./MNNConvert \
  -f ONNX \
  --modelFile model.onnx \
  --MNNModel model.mnn \
  --bizCode MNN \
  --optimizeLevel 2                # 0=None, 1=Basic, 2=Full
```

**With quantization:**

```bash
# FP16 quantization (recommended for most models)
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_fp16.mnn \
  --fp16

# Int8 quantization with HQQ
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int8.mnn \
  --weightQuantBits 8 \
  --weightQuantBlock 64 \
  --hqq                            # Better accuracy
```

For detailed quantization options, see `references/optimization.md`.

### Step 3: Verify Conversion

Test the converted model:

```python
import MNN

# Load model
interpreter = MNN.Interpreter("model.mnn")
session = interpreter.createSession()

# Create dummy input
input_tensor = interpreter.getSessionInput(session)
input_tensor.copyFrom(your_test_data)

# Run inference
interpreter.runSession(session)

# Get output
output_tensor = interpreter.getSessionOutput(session)
print(output_tensor.getData())
```

## Platform Integration Workflows

### Android Integration

See `references/android_integration.md` for complete guide.

**Quick steps:**

1. **Build MNN for Android:**
```bash
cd project/android
mkdir build_64
../build_64.sh "-DMNN_OPENCL=ON -DMNN_ARM82=ON"
```

2. **Add to Android Studio project:**
   - Copy `libMNN.so` to `app/src/main/jniLibs/arm64-v8a/`
   - Create JNI wrapper in `cpp/native-lib.cpp`
   - Load library in Java: `System.loadLibrary("MNN")`

3. **Use in Java/Kotlin:**
```java
MNNWrapper wrapper = new MNNWrapper();
wrapper.loadModel(modelPath);
float[] output = wrapper.runInference(input);
```

### iOS Integration

See `references/ios_integration.md` for complete guide.

**Quick steps:**

1. **Build MNN for iOS:**
```bash
sh package_scripts/ios/buildiOS.sh "-DMNN_METAL=ON -DMNN_ARM82=ON"
```

2. **Add to Xcode project:**
   - Add `MNN.framework` to project
   - Link Metal.framework and Accelerate.framework
   - Create Objective-C++ wrapper

3. **Use in Swift/Objective-C:**
```swift
let inference = ModelInference()
inference.loadModel(path: modelPath)
let output = inference.runInference(input: input)
```

## LLM Deployment Workflow

See `references/llm_deployment.md` for comprehensive guide.

### Step 1: Build MNN with LLM Support

**For Android:**
```bash
cd project/android
mkdir build_64
../build_64.sh "-DMNN_LOW_MEMORY=true \
  -DMNN_BUILD_LLM=true \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=true \
  -DMNN_ARM82=true \
  -DMNN_OPENCL=true"
```

**For iOS:**
```bash
sh package_scripts/ios/buildiOS.sh "-DMNN_ARM82=ON \
  -DMNN_BUILD_LLM=ON \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=ON \
  -DMNN_METAL=ON"
```

### Step 2: Convert LLM Model

Install dependencies:
```bash
cd transformers/llm
pip install -r requirements.txt
```

Convert model:
```bash
# Direct conversion to MNN with 4-bit quantization
python llmexport.py \
  --path Qwen/Qwen2.5-7B \
  --export mnn \
  --quant_bit 4

# Or convert via ONNX for custom quantization
python llmexport.py --path Qwen/Qwen2.5-7B --export onnx
./MNNConvert --modelFile llm.onnx --MNNModel llm.mnn \
  --weightQuantBits 4 --weightQuantBlock 64
```

**Supported Models:**
- Qwen (Qwen2, Qwen2.5, Qwen-Omni)
- Llama (2, 3, TinyLlama)
- DeepSeek, Baichuan, Yi, Phi, Gemma

### Step 3: Run LLM Inference

**C++ API:**
```cpp
#include <llm.hpp>

std::shared_ptr<Llm> llm(Llm::createLLM(config));
llm->load("model.mnn");
llm->response("Hello, how are you?");

while (llm->is_running()) {
    std::cout << llm->fetch() << std::flush;
}
```

**Python API:**
```python
import mnnllm

llm = mnnllm.create('model.mnn')
for token in llm.generate_stream("Tell me a story"):
    print(token, end='', flush=True)
```

**Performance Notes:**
- CPU: 8.6x faster prefill vs llama.cpp
- GPU: 25.3x faster prefill vs llama.cpp
- Use 4-bit quantization for mobile (12.5% original size)
- Enable speculative decoding for 2-3x faster generation

## Model Optimization Workflow

See `references/optimization.md` for detailed guide.

### Optimization Strategy

**Level 1: Graph Optimization (Always do this)**
```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model.mnn \
  --optimizeLevel 2
```

**Level 2: FP16 Quantization (Recommended for most models)**
```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_fp16.mnn \
  --fp16
```
- Size: 50% reduction
- Speed: 2x faster on ARM v8.2+
- Accuracy: <1% loss

**Level 3: Int8 Quantization (For compute-intensive models)**
```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int8.mnn \
  --weightQuantBits 8 \
  --weightQuantBlock 64 \
  --hqq
```
- Size: 75% reduction
- Speed: 2.5x faster with ARM v8.2 sdot/VNNI
- Accuracy: <1% loss with HQQ

**Level 4: Int4 Quantization (For LLMs on mobile)**
```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int4.mnn \
  --weightQuantBits 4 \
  --weightQuantBlock 64
```
- Size: 87.5% reduction
- Speed: Best with weight dequantization
- Accuracy: 2-4% loss with HQQ

**Build with weight dequantization:**
```bash
cmake .. -DMNN_LOW_MEMORY=ON -DMNN_CPU_WEIGHT_DEQUANT_GEMM=ON
```

### Benchmark and Iterate

1. **Measure baseline (FP32)**
2. **Try FP16** - almost always worth it
3. **Try Int8 with HQQ** - if FP16 not enough
4. **Try Int4** - for LLMs only
5. **Use calibration** - if accuracy is critical

## Backend Configuration

### CPU Backend

```cpp
MNN::ScheduleConfig config;
config.type = MNN_FORWARD_CPU;
config.numThread = 4; // Adjust based on device cores

MNN::BackendConfig backendConfig;
backendConfig.precision = MNN::BackendConfig::Precision_Low; // FP16
backendConfig.memory = MNN::BackendConfig::Memory_Low;
config.backendConfig = &backendConfig;

session = interpreter->createSession(config);
```

**When to use:**
- Battery-critical applications
- Devices without GPU support
- When model is CPU-optimized

### GPU Backend (Mobile)

**Metal (iOS):**
```cpp
config.type = MNN_FORWARD_METAL;
config.numThread = 1;
backendConfig.precision = MNN::BackendConfig::Precision_Low; // FP16
backendConfig.power = MNN::BackendConfig::Power_High;
```

**OpenCL (Android):**
```cpp
config.type = MNN_FORWARD_OPENCL;
config.numThread = 1;
backendConfig.precision = MNN::BackendConfig::Precision_Low; // FP16
```

**Vulkan (Cross-platform):**
```cpp
config.type = MNN_FORWARD_VULKAN;
config.numThread = 1;
```

**When to use:**
- Compute-intensive models (CNNs, large models)
- When performance is critical
- Devices with good GPU support

### Fallback Strategy

```cpp
// Try GPU first, fallback to CPU
MNN::ScheduleConfig config;
config.type = MNN_FORWARD_OPENCL;
MNN::Session* session = interpreter->createSession(config);

if (!session) {
    config.type = MNN_FORWARD_CPU;
    config.numThread = 4;
    session = interpreter->createSession(config);
}
```

## Common Workflows

### Workflow 1: Deploy Vision Model on Android

1. Convert model to MNN with FP16
2. Build MNN with OpenCL support
3. Create JNI wrapper
4. Configure OpenCL backend with FP16
5. Test on real devices
6. Profile and optimize

### Workflow 2: Deploy LLM on iOS

1. Convert LLM with 4-bit quantization
2. Build MNN with LLM + Metal support
3. Create Objective-C++ wrapper
4. Configure Metal backend
5. Enable speculative decoding
6. Optimize memory usage

### Workflow 3: Optimize Model for Production

1. Start with FP32 baseline
2. Apply graph optimizations
3. Try FP16 quantization
4. Benchmark accuracy and speed
5. If needed, try Int8 with HQQ
6. Use calibration if critical
7. Deploy and monitor

## Troubleshooting

### Build Issues

**Problem: CMake can't find compiler**
```bash
# Set environment variables
export ANDROID_NDK=/path/to/ndk
export PATH=$ANDROID_NDK/toolchains/llvm/prebuilt/linux-x86_64/bin:$PATH
```

**Problem: Missing dependencies**
```bash
# Install required packages
apt-get install cmake build-essential
```

### Conversion Issues

**Problem: Unsupported operator**
- Check `references/operators.md` for supported ops
- Implement as custom operator
- Use alternative model architecture

**Problem: Model too large**
- Use Int8 or Int4 quantization
- Enable MNN_BUILD_MINI for smaller library
- Use block-wise quantization

### Runtime Issues

**Problem: Out of memory**
- Enable low memory mode
- Reduce batch size
- Use quantized model
- Reduce max_new_tokens (for LLMs)

**Problem: Slow inference**
- Enable GPU backend
- Use FP16 precision
- Enable ARM v8.2 optimizations
- Increase thread count (CPU)

**Problem: Poor accuracy**
- Try FP16 instead of Int8/Int4
- Use HQQ quantization
- Apply calibration
- Increase weightQuantBlock size

## Performance Tips

1. **Always enable ARM v8.2** on supported devices (`-DMNN_ARM82=ON`)
2. **Use GPU when available** - 3-5x faster for vision models
3. **Start with FP16** - best balance of size, speed, accuracy
4. **Profile on real devices** - emulators are not representative
5. **Use weight dequantization** for Int4/Int8 models
6. **Enable transformer fusion** for LLMs (`-DMNN_SUPPORT_TRANSFORMER_FUSE=ON`)
7. **Adjust thread count** based on device cores
8. **Use low memory mode** on resource-constrained devices

## Additional Resources

- **Architecture**: `references/architecture.md`
- **Android Integration**: `references/android_integration.md`
- **iOS Integration**: `references/ios_integration.md`
- **LLM Deployment**: `references/llm_deployment.md`
- **Optimization**: `references/optimization.md`
- **Operators**: `references/operators.md`
- **Official Docs**: https://mnn-docs.readthedocs.io
- **GitHub**: https://github.com/alibaba/MNN
