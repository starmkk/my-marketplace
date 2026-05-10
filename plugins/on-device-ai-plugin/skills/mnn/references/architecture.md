# MNN Architecture

## Overview

MNN (Mobile Neural Network) consists of three main components:
1. **Converter** - Converts models from various frameworks to MNN format
2. **Interpreter** - Loads and parses MNN models
3. **Backend** - Executes operations on different hardware (CPU, GPU, NPU)

## Key Components

### 1. Model Converter (MNNConvert)

The converter transforms models from training frameworks to optimized MNN models.

**Supported Input Formats:**
- TensorFlow (178 OPs)
- Caffe (52 OPs)
- ONNX (158 OPs)
- TorchScript (163 OPs)

**Conversion Process:**
1. Parse source model format
2. Graph optimization (layer fusion, constant folding, etc.)
3. Generate MNN model with FlatBuffers schema
4. Optional quantization (FP16, Int8)

### 2. Interpreter

The interpreter manages the model lifecycle and execution.

**Core Responsibilities:**
- Model loading and parsing
- Memory management
- Session creation and configuration
- Scheduling computational graphs

**Key Features:**
- Pre-inference mechanism for runtime optimization
- Dynamic input support
- Multi-input/output handling
- Control flow support

### 3. Backend Abstraction

MNN uses a backend abstraction layer to support multiple hardware platforms.

**Supported Backends:**

**CPU:**
- ARM v7a, v8 with NEON
- ARM v8.2 with FP16, dot product instructions
- x86/x64 with SSE4.1, AVX2, AVX512
- VNNI support for Int8 acceleration

**GPU:**
- Metal (iOS) - Highly optimized, faster than CoreML
- OpenCL (Android/iOS) - Supports Adreno, Mali GPUs
- Vulkan (Cross-platform)
- CUDA (NVIDIA) - With TensorCore support

**NPU:**
- CoreML (iOS)
- HIAI (Huawei)
- NNAPI (Android)
- QNN (Qualcomm)

### 4. Optimization Techniques

**Pre-inference Mechanism:**
- Runtime optimization through online cost evaluation
- Optimal computation scheme selection
- Considers both algorithm implementation and backend characteristics

**Kernel Optimization:**
- Hand-written assembly for ARM/x86
- Winograd convolution (3x3 to 7x7)
- Im2Col + GEMM optimization
- Strassen algorithm for large matrices

**Memory Optimization:**
- Memory reuse and pooling
- Lazy memory allocation
- Low memory mode (`MNN_LOW_MEMORY`)

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         Training Framework              │
│  (TensorFlow/Caffe/ONNX/PyTorch)       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          MNNConvert Tool                │
│  - Parse model                          │
│  - Graph optimization                   │
│  - Quantization (optional)              │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          MNN Model (.mnn)               │
│  (FlatBuffers format)                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         MNN Interpreter                 │
│  - Load model                           │
│  - Create session                       │
│  - Schedule graph                       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       Backend Execution                 │
│  CPU / GPU / NPU                        │
│  - Execute operators                    │
│  - Memory management                    │
└─────────────────────────────────────────┘
```

## Performance Characteristics

**Size:**
- iOS: ~12MB static library (armv7+arm64)
- Android: ~800KB core so (armv7a)
- Can reduce by ~25% with `MNN_BUILD_MINI`

**Speed:**
- 2x faster on ARM v8.2 with FP16
- 2.5x faster with ARM v8.2 sdot/VNNI
- Outperforms TensorFlow Lite, CoreML, PyTorch Mobile

**Memory:**
- Efficient memory management
- Low memory mode available
- Weight dequantization for Int8 models
