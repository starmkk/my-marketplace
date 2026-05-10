# Supported Operators

## Overview

MNN supports a comprehensive set of operators from multiple frameworks, enabling conversion of most deep learning models.

## Framework Support

| Framework | Supported OPs | Status |
|-----------|---------------|--------|
| TensorFlow | 178 | Full Support |
| Caffe | 52 | Full Support |
| ONNX | 158 | Full Support |
| TorchScript | 163 | Full Support |

## Backend Support

| Backend | Total OPs | Status |
|---------|-----------|--------|
| CPU | 111+ | Optimized |
| ARM v8.2 | 6+ | FP16/INT8 Optimized |
| Metal | 55+ | iOS GPU Optimized |
| OpenCL | 43+ | Android GPU Optimized |
| Vulkan | 32+ | Cross-platform GPU |
| CUDA | 40+ | NVIDIA GPU |

## Common Operators

### Convolution Operations

**Supported:**
- Conv2D / Conv3D
- DepthwiseConv2D
- TransposeConv (Deconvolution)
- DilatedConv
- GroupConv

**Optimizations:**
- Winograd algorithm (3x3 to 7x7 kernels)
- Im2Col + GEMM
- Direct convolution for small kernels
- Strassen algorithm for large matrices

### Pooling Operations

**Supported:**
- MaxPool / MaxPool3D
- AvgPool / AvgPool3D
- GlobalMaxPool / GlobalAvgPool
- AdaptiveMaxPool / AdaptiveAvgPool

### Activation Functions

**Supported:**
- ReLU / ReLU6 / LeakyReLU / PReLU
- Sigmoid / Tanh
- Swish / HSwish
- Mish
- ELU / SELU / GELU
- Softmax / LogSoftmax

### Normalization

**Supported:**
- BatchNorm
- LayerNorm
- InstanceNorm
- GroupNorm
- LocalResponseNorm (LRN)

### Recurrent Operations

**Supported:**
- LSTM
- GRU
- RNN
- Bidirectional LSTM/GRU

### Attention Mechanisms

**Supported:**
- MultiheadAttention
- ScaledDotProductAttention
- Self-Attention
- Cross-Attention

**Optimizations for Transformers:**
- Fused attention kernels
- Flash Attention (on supported backends)
- KV cache optimization
- Rope embedding optimization

### Tensor Operations

**Element-wise:**
- Add, Sub, Mul, Div
- Pow, Sqrt, Square
- Exp, Log, Abs
- Min, Max, Clip

**Reduction:**
- Sum, Mean, Max, Min
- ArgMax, ArgMin
- ReduceL1, ReduceL2

**Tensor Manipulation:**
- Reshape, Flatten
- Transpose, Permute
- Concat, Split, Stack
- Slice, Gather, Scatter
- Expand, Tile, Repeat
- Squeeze, Unsqueeze

### Math Operations

**Supported:**
- MatMul / BatchMatMul
- Gemm
- Conv (as MatMul)
- Einsum (limited support)

### Data Type Operations

**Supported:**
- Cast
- Quantize / Dequantize
- Int8 / FP16 / BF16 conversions

### Control Flow

**Supported:**
- If
- While
- Loop
- Switch

## Operator Compatibility Matrix

### Vision Models

| Operator Category | ResNet | MobileNet | EfficientNet | YOLO | ViT |
|-------------------|--------|-----------|--------------|------|-----|
| Conv2D | ✓ | ✓ | ✓ | ✓ | ✓ |
| BatchNorm | ✓ | ✓ | ✓ | ✓ | ✓ |
| ReLU/Swish | ✓ | ✓ | ✓ | ✓ | ✓ |
| MaxPool | ✓ | ✓ | ✓ | ✓ | N/A |
| DepthwiseConv | N/A | ✓ | ✓ | N/A | N/A |
| Attention | N/A | N/A | N/A | N/A | ✓ |
| LayerNorm | N/A | N/A | N/A | N/A | ✓ |

### NLP Models

| Operator Category | BERT | GPT | Llama | Qwen | T5 |
|-------------------|------|-----|-------|------|-----|
| Embedding | ✓ | ✓ | ✓ | ✓ | ✓ |
| LayerNorm | ✓ | ✓ | ✓ | ✓ | ✓ |
| Attention | ✓ | ✓ | ✓ | ✓ | ✓ |
| RoPE | N/A | ✓ | ✓ | ✓ | N/A |
| MLP/FFN | ✓ | ✓ | ✓ | ✓ | ✓ |
| SiLU/GELU | ✓ | ✓ | ✓ | ✓ | ✓ |

## Custom Operators

MNN allows adding custom operators for unsupported operations.

### Register Custom OP

**C++ Implementation:**

```cpp
#include <MNN/Interpreter.hpp>

class CustomOp : public MNN::Execution {
public:
    CustomOp(Backend *backend) : Execution(backend) {}
    
    virtual ErrorCode onResize(const std::vector<Tensor *> &inputs,
                              const std::vector<Tensor *> &outputs) override {
        // Setup computation
        return NO_ERROR;
    }
    
    virtual ErrorCode onExecute(const std::vector<Tensor *> &inputs,
                               const std::vector<Tensor *> &outputs) override {
        // Implement custom operation
        // Access input data: inputs[0]->host<float>()
        // Write output data: outputs[0]->host<float>()
        return NO_ERROR;
    }
};

// Register custom op
MNN::OpCreatorRegister<CustomOp> __custom_op_register(MNN::OpType_Custom);
```

## Operator Fusion

MNN automatically fuses compatible operators for better performance.

### Supported Fusions

**Conv-BN-ReLU:**
```
Conv2D + BatchNorm + ReLU -> Fused_Conv_BN_ReLU
```

**Conv-Add-ReLU:**
```
Conv2D + Add + ReLU -> Fused_Conv_Add_ReLU
```

**MatMul-Add:**
```
MatMul + Add -> Fused_MatMul_Add
```

**Attention Fusion:**
```
Q·K^T + Softmax + ·V -> Fused_Attention
```

## Precision Support

| Operator Type | FP32 | FP16 | BF16 | INT8 | INT4 |
|---------------|------|------|------|------|------|
| Conv2D | ✓ | ✓ | ✓ | ✓ | N/A |
| MatMul | ✓ | ✓ | ✓ | ✓ | ✓ |
| Attention | ✓ | ✓ | Limited | Limited | N/A |
| ReLU | ✓ | ✓ | ✓ | ✓ | N/A |
| BatchNorm | ✓ | ✓ | ✓ | Fused | N/A |

## Unsupported Operators

Some operations are not yet supported or have limited support:

**Limited Support:**
- Some ONNX-specific operators
- Certain TensorFlow control flow variants
- Complex dynamic shapes in some operations

**Workarounds:**
1. Replace unsupported ops with equivalent supported ops
2. Implement as custom operators
3. Use alternative model architectures

## Verification

Check if a model's operators are supported:

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model.mnn \
  --bizCode MNN \
  --testdir test_data       # Verify conversion with test data
```

## Performance Characteristics

### CPU Optimizations

**Highly Optimized (Assembly):**
- Conv2D (Winograd, Im2Col+GEMM)
- MatMul / Gemm
- BatchNorm (when fused)
- ReLU family

**Well Optimized:**
- Pooling operations
- Element-wise operations
- Normalization layers

**Standard Implementation:**
- Less common operators
- Dynamic operations

### GPU Optimizations

**Metal (iOS):**
- Conv2D, DepthwiseConv
- MatMul
- Element-wise operations
- Pooling

**OpenCL (Android):**
- Conv2D, DepthwiseConv
- MatMul
- Activation functions
- Normalization

**Vulkan (Cross-platform):**
- Core convolution operations
- MatMul
- Element-wise operations
- Limited compared to Metal/OpenCL

## Reference

For the most up-to-date list of supported operators, check:
- [MNN Schema](https://github.com/alibaba/MNN/blob/master/schema/default/MNN.fbs)
- [TensorFlow Converter](https://github.com/alibaba/MNN/tree/master/tools/converter/source/tensorflow)
- [ONNX Converter](https://github.com/alibaba/MNN/tree/master/tools/converter/source/onnx)
- [Caffe Converter](https://github.com/alibaba/MNN/tree/master/tools/converter/source/caffe)
