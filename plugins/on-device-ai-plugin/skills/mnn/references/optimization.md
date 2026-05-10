# Model Optimization and Quantization Guide

## Overview

MNN provides comprehensive optimization and quantization capabilities to reduce model size and improve inference speed while maintaining accuracy.

## Model Conversion and Optimization

### Basic Conversion

```bash
./MNNConvert \
  -f TF \                          # Framework: TF, CAFFE, ONNX, TORCHSCRIPT
  --modelFile model.pb \           # Input model file
  --MNNModel model.mnn \          # Output MNN model
  --bizCode YOUR_BIZ_CODE         # Business code for tracking
```

### Graph Optimization Options

**Enable All Optimizations:**

```bash
./MNNConvert \
  -f ONNX \
  --modelFile model.onnx \
  --MNNModel model.mnn \
  --bizCode MNN \
  --optimizeLevel 2               # 0: None, 1: Basic, 2: Full
```

**Optimization Techniques Applied:**
- Operator fusion (Conv + BN + ReLU)
- Constant folding
- Dead code elimination
- Memory optimization
- Layout optimization

### Keep Input Format

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model.mnn \
  --keepInputFormat                # Preserve original input format (NHWC/NCHW)
```

## Quantization

### Quantization Types

MNN supports two main quantization approaches:

1. **Post-Training Quantization (PTQ)** - No training data required
2. **Quantization-Aware Training (QAT)** - Requires retraining

### FP16 Quantization

Convert model weights to FP16 for ~50% size reduction:

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_fp16.mnn \
  --fp16                           # Enable FP16 quantization
```

**Characteristics:**
- Model size: ~50% reduction
- Accuracy loss: Minimal (<1%)
- Speed: 2x faster on ARM v8.2+ with FP16 support
- Recommended for: Most models

### Int8 Quantization

#### Symmetric Quantization

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int8.mnn \
  --weightQuantBits 8 \            # 8-bit quantization
  --weightQuantBlock 0             # 0 = per-channel, >0 = block-wise
```

#### Asymmetric Quantization (HQQ)

HQQ provides better accuracy for quantized models:

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int8_hqq.mnn \
  --weightQuantBits 8 \
  --hqq                            # Enable HQQ asymmetric quantization
```

**Characteristics:**
- Model size: ~75% reduction (vs FP32)
- Accuracy loss: 1-3% (symmetric), <1% (HQQ)
- Speed: 2.5x faster with ARM v8.2 sdot/VNNI
- Recommended for: Compute-intensive models

### Int4 Quantization

Ultra-low bit quantization for maximum compression:

```bash
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int4.mnn \
  --weightQuantBits 4 \
  --weightQuantBlock 64            # Block size for better accuracy
```

**Block-wise Quantization:**

```bash
# Smaller blocks = better accuracy, larger model
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int4_block32.mnn \
  --weightQuantBits 4 \
  --weightQuantBlock 32

# Larger blocks = more compression, lower accuracy
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_int4_block128.mnn \
  --weightQuantBits 4 \
  --weightQuantBlock 128
```

**Characteristics:**
- Model size: ~87.5% reduction (vs FP32)
- Accuracy loss: 3-7% (symmetric), 2-4% (HQQ)
- Speed: Best for LLMs with weight dequantization
- Recommended for: LLMs on mobile devices

### Mixed-Bit Quantization

Quantize different layers with different precisions:

```bash
# For LLM models - 2 to 8 bits supported
./MNNConvert \
  --modelFile model.onnx \
  --MNNModel model_mixed.mnn \
  --weightQuantBits 4 \
  --sensitiveLayerBits 6 \         # Use 6-bit for sensitive layers
  --sensitiveLayerFile layers.txt  # File listing sensitive layers
```

### Calibration-Based Quantization

For better Int8 quantization accuracy:

**Step 1: Generate Calibration Data**

```python
import numpy as np

# Create calibration dataset (100-1000 samples)
calibration_data = []
for i in range(100):
    # Load real data or synthetic data
    data = load_image(f"calibration_{i}.jpg")
    calibration_data.append(preprocess(data))

np.save("calibration.npy", np.array(calibration_data))
```

**Step 2: Run Calibration**

```bash
./quantized.out \
  model.mnn \                      # Original FP32 model
  model_int8_calib.mnn \          # Output quantized model
  calibration.npy \               # Calibration data
  imageInputConfig.json           # Input configuration
```

**imageInputConfig.json:**

```json
{
  "format": "RGB",
  "mean": [127.5, 127.5, 127.5],
  "normal": [0.00784314, 0.00784314, 0.00784314],
  "width": 224,
  "height": 224,
  "path": "input",
  "channel": 3
}
```

## Model Compression

### Weight Pruning

MNN supports sparse computation for pruned models:

```bash
./MNNConvert \
  --modelFile pruned_model.onnx \
  --MNNModel model.mnn \
  --sparse                         # Enable sparse optimization
```

### Knowledge Distillation

Use MNN training APIs to distill large models:

```python
import MNN.nn as nn
import MNN.expr as expr

# Teacher model (large)
teacher = nn.load_module("teacher.mnn")
teacher.train(False)

# Student model (small)
student = create_student_model()

# Distillation loss
def distillation_loss(student_logits, teacher_logits, labels, temperature=3.0):
    soft_targets = expr.softmax(teacher_logits / temperature)
    soft_probs = expr.softmax(student_logits / temperature)
    distill_loss = expr.nll_loss(expr.log(soft_probs), soft_targets)
    
    hard_loss = expr.cross_entropy(student_logits, labels)
    return 0.7 * distill_loss + 0.3 * hard_loss

# Training loop
for epoch in range(num_epochs):
    for batch in dataloader:
        student_out = student(batch["input"])
        teacher_out = teacher(batch["input"])
        
        loss = distillation_loss(student_out, teacher_out, batch["label"])
        loss.backward()
        optimizer.step()
```

## Build Optimizations

### Minimal Build

Reduce library size by ~25%:

```bash
cmake .. \
  -DMNN_BUILD_MINI=ON \            # Minimal build
  -DMNN_SUPPORT_BF16=OFF \         # Disable BF16
  -DMNN_BUILD_TRAIN=OFF            # Disable training
```

### Reduce Size Further

```bash
cmake .. \
  -DMNN_BUILD_MINI=ON \
  -DMNN_REDUCE_SIZE=ON \           # Aggressive size reduction
  -DMNN_SUPPORT_DEPRECATED_OP=OFF  # Remove deprecated ops
```

### Enable Specific Ops Only

```bash
cmake .. \
  -DMNN_BUILD_CONVERTER=OFF \
  -DMNN_BUILD_MINI=ON \
  -DMNN_OP_REGISTER_MACRO=ON       # Register only used ops
```

## Runtime Optimizations

### Low Memory Mode

```cpp
ScheduleConfig config;
BackendConfig backendConfig;
backendConfig.memory = BackendConfig::Memory_Low;  // Low memory mode
config.backendConfig = &backendConfig;

Session* session = interpreter->createSession(config);
```

### Precision Control

```cpp
BackendConfig backendConfig;

// FP16 precision (faster, less accurate)
backendConfig.precision = BackendConfig::Precision_Low;

// FP32 precision (slower, more accurate)
backendConfig.precision = BackendConfig::Precision_Normal;

// BF16 precision (on supported platforms)
backendConfig.precision = BackendConfig::Precision_High;
```

### Weight Dequantization

For Int4/Int8 models, enable runtime dequantization:

```bash
cmake .. \
  -DMNN_LOW_MEMORY=ON \
  -DMNN_CPU_WEIGHT_DEQUANT_GEMM=ON  # Enable weight dequantization
```

### Dynamic Quantization

Dynamically quantize activations at runtime:

```cpp
BackendConfig backendConfig;
backendConfig.precision = BackendConfig::Precision_Low;  // FP16
config.backendConfig = &backendConfig;

// Activations will be quantized to FP16 dynamically
```

## Optimization Workflow

### Recommended Pipeline

**1. Start with FP32 Model**
- Convert to MNN with graph optimizations
- Benchmark accuracy and speed

**2. Try FP16 Quantization**
- Minimal accuracy loss
- Significant speed improvement
- Good balance for most use cases

**3. Try Int8 with HQQ**
- Better compression
- Acceptable accuracy loss
- Good for mobile deployment

**4. Try Int4 (LLMs only)**
- Maximum compression
- Use block-wise quantization
- Enable weight dequantization

**5. Fine-tune if Needed**
- Adjust quantization parameters
- Use mixed-bit quantization
- Apply calibration

## Benchmarking

### Measure Model Size

```bash
ls -lh model.mnn
```

### Measure Inference Speed

```cpp
#include <chrono>

auto start = std::chrono::high_resolution_clock::now();
interpreter->runSession(session);
auto end = std::chrono::high_resolution_clock::now();

auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
std::cout << "Inference time: " << duration.count() << " ms" << std::endl;
```

### Measure Accuracy

```python
import numpy as np

def evaluate_accuracy(original_model, quantized_model, test_data):
    original_outputs = []
    quantized_outputs = []
    
    for input_data in test_data:
        orig_out = original_model.forward(input_data)
        quant_out = quantized_model.forward(input_data)
        
        original_outputs.append(orig_out)
        quantized_outputs.append(quant_out)
    
    # Calculate accuracy drop
    accuracy_drop = compute_accuracy_difference(original_outputs, quantized_outputs)
    
    # Calculate cosine similarity
    cosine_sim = compute_cosine_similarity(original_outputs, quantized_outputs)
    
    return {
        "accuracy_drop": accuracy_drop,
        "cosine_similarity": cosine_sim
    }
```

## Size vs Accuracy Trade-off

| Quantization | Model Size | Speed | Typical Accuracy Loss |
|--------------|------------|-------|----------------------|
| FP32 (baseline) | 100% | 1x | 0% |
| FP16 | 50% | 2x | <1% |
| Int8 (symmetric) | 25% | 2.5x | 1-3% |
| Int8 (HQQ) | 25% | 2.5x | <1% |
| Int4 (block-64) | 12.5% | 3x* | 2-4% |
| Int4 (block-128) | 12.5% | 3x* | 3-7% |

*With weight dequantization enabled

## Tips and Best Practices

1. **Always benchmark** accuracy and speed after quantization
2. **Use HQQ** for better Int8 accuracy
3. **Use block-wise quantization** (block size 32-128) for Int4
4. **Enable weight dequantization** for Int4/Int8 models
5. **Use FP16** as the default choice for most models
6. **Apply graph optimizations** before quantization
7. **Test on real devices** for accurate performance measurements
8. **Use calibration** for critical accuracy requirements
