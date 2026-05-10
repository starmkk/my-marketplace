# MNN-LLM Deployment Guide

## Overview

MNN-LLM is a large language model runtime solution for deploying LLMs locally on mobile devices, PCs, and IoT devices.

**Supported Models:**
- Qwen (Qwen2, Qwen2.5, Qwen-Omni)
- Llama (Llama 2, Llama 3, TinyLlama, MobileLLM)
- Baichuan
- Yi
- DeepSeek (including DeepSeek-R1)
- InternLM
- Phi
- Gemma
- ReaderLM
- Smolm

**Performance Highlights:**
- **CPU**: 8.6x faster prefill than llama.cpp, 2.3x faster decoding
- **GPU**: 25.3x faster prefill, 7.1x faster decoding than llama.cpp
- **Privacy**: Runs entirely on-device

## Quick Start

### 1. Build MNN with LLM Support

**For Android (ARM64):**

```bash
cd project/android
mkdir build_64
../build_64.sh "-DMNN_LOW_MEMORY=true \
  -DMNN_CPU_WEIGHT_DEQUANT_GEMM=true \
  -DMNN_BUILD_LLM=true \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=true \
  -DMNN_ARM82=true \
  -DMNN_OPENCL=true \
  -DMNN_USE_LOGCAT=true"
```

**For iOS:**

```bash
sh package_scripts/ios/buildiOS.sh "-DMNN_ARM82=ON \
  -DMNN_LOW_MEMORY=ON \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=ON \
  -DMNN_BUILD_LLM=ON \
  -DMNN_CPU_WEIGHT_DEQUANT_GEMM=ON"
```

**For PC (x86_64 with AVX512):**

```bash
mkdir build && cd build
cmake ../ -DMNN_LOW_MEMORY=true \
  -DMNN_CPU_WEIGHT_DEQUANT_GEMM=true \
  -DMNN_BUILD_LLM=true \
  -DMNN_SUPPORT_TRANSFORMER_FUSE=true \
  -DMNN_AVX512=true
make -j16
```

### 2. Model Conversion

MNN-LLM provides the `llmexport.py` tool to convert models.

**Install Dependencies:**

```bash
cd transformers/llm
pip install -r requirements.txt
```

**Convert Model to MNN:**

**Option 1: Direct Conversion to MNN**

```bash
# Export with 4-bit quantization
python llmexport.py \
  --path Qwen/Qwen2.5-7B \
  --export mnn \
  --quant_bit 4

# Export with 8-bit quantization
python llmexport.py \
  --path Qwen/Qwen2.5-7B \
  --export mnn \
  --quant_bit 8
```

**Option 2: Convert via ONNX (for custom bit depths)**

```bash
# Step 1: Export to ONNX
python llmexport.py \
  --path Qwen/Qwen2.5-7B \
  --export onnx

# Step 2: Convert ONNX to MNN with custom quantization
./MNNConvert \
  --modelFile ./transformers/llm/export/model/onnx/llm.onnx \
  --MNNModel llm.mnn \
  --keepInputFormat \
  --weightQuantBits=4 \
  --weightQuantBlock=64
```

**Quantization Options:**
- `weightQuantBits`: 2, 3, 4, 5, 6, 7, 8 (default: 4)
- `weightQuantBlock`: Block size for quantization (default: 64)
- HQQ quantization: Use `--hqq` flag for asymmetric quantization

### 3. Run LLM Inference

**C++ API:**

```cpp
#include <llm.hpp>

int main() {
    // Create LLM instance
    std::shared_ptr<Llm> llm(Llm::createLLM(config));
    
    // Load model
    llm->load("path/to/model.mnn");
    
    // Generate response
    std::string prompt = "Hello, how are you?";
    llm->response(prompt);
    
    // Stream response
    while (llm->is_running()) {
        std::string token = llm->fetch();
        std::cout << token << std::flush;
    }
    
    return 0;
}
```

**Python API:**

```python
import mnnllm

# Create LLM instance
llm = mnnllm.create('path/to/model.mnn')

# Generate response
response = llm.generate("Hello, how are you?")
print(response)

# Stream response
for token in llm.generate_stream("Tell me a story"):
    print(token, end='', flush=True)
```

## Configuration

### Model Config

Create a `config.json` file:

```json
{
  "model_type": "qwen2",
  "hidden_size": 4096,
  "num_hidden_layers": 32,
  "num_attention_heads": 32,
  "intermediate_size": 11008,
  "vocab_size": 151936,
  "max_position_embeddings": 32768,
  "rope_theta": 1000000
}
```

### LLM Config

```cpp
MNN::Transformer::LlmConfig config;

// Model paths
config.model_dir = "/path/to/model/directory";

// Prompt template
config.prompt_template = "<|im_start|>user\n%s<|im_end|>\n<|im_start|>assistant\n";

// Backend configuration
config.backend_type = MNN_FORWARD_CPU; // or MNN_FORWARD_OPENCL, MNN_FORWARD_VULKAN
config.numThread = 4;

// Memory configuration
config.memory = MNN::BackendConfig::Memory_Low;
config.precision = MNN::BackendConfig::Precision_Low; // FP16

// Generation parameters
config.max_new_tokens = 512;
config.temperature = 0.7;
config.top_k = 50;
config.top_p = 0.9;
```

## Multimodal Support

### Vision-Language Models

**Supported Models:**
- Qwen-VL
- InternVL2.5
- DeepSeek-VL

**Example:**

```cpp
#include <llm.hpp>

// Create multimodal LLM
std::shared_ptr<Llm> llm(Llm::createLLM(config));
llm->load("qwen-vl.mnn");

// Load image
std::string image_path = "image.jpg";

// Generate response with image
std::string prompt = "<img>" + image_path + "</img>What's in this image?";
llm->response(prompt);
```

### Audio Models

**Supported Models:**
- Qwen2.5-Omni (multimodal: text + audio)
- Whisper (speech-to-text)

**Example:**

```cpp
// Audio-to-text with Qwen-Omni
std::string audio_path = "audio.wav";
std::string prompt = "<audio>" + audio_path + "</audio>Transcribe this audio.";
llm->response(prompt);
```

## Performance Optimization

### 1. Speculative Decoding

Enable speculative decoding with EAGLE-3 or lookahead algorithms:

```cpp
config.use_speculative_decoding = true;
config.draft_model_path = "draft_model.mnn";
```

**Performance Gain:** 2-3x faster decoding in typical scenarios

### 2. KV Cache Optimization

```cpp
config.kv_cache_method = MNN::Transformer::KVCacheMethod::PAGED;
config.max_cache_length = 4096;
```

### 3. Weight Dequantization

Enable weight dequantization for Int4/Int8 models:

```bash
# Build with weight dequantization
-DMNN_CPU_WEIGHT_DEQUANT_GEMM=true
```

### 4. Backend Selection

**CPU (Best for battery life):**
```cpp
config.backend_type = MNN_FORWARD_CPU;
config.numThread = 4; // Adjust based on device
```

**GPU (Best for performance):**
```cpp
config.backend_type = MNN_FORWARD_OPENCL; // or VULKAN, METAL
config.memory = MNN::BackendConfig::Memory_Low;
config.precision = MNN::BackendConfig::Precision_Low; // FP16
```

### 5. Memory Management

**Low Memory Mode:**
```cpp
config.memory = MNN::BackendConfig::Memory_Low;
```

**Lazy Loading:**
```cpp
config.use_mmap = true; // Use mmap for model loading
```

## Android Integration Example

```java
public class LLMWrapper {
    static {
        System.loadLibrary("MNN");
        System.loadLibrary("llm");
    }
    
    private long llmPtr;
    
    public void loadModel(String modelPath, String configPath) {
        llmPtr = nativeCreateLLM(modelPath, configPath);
    }
    
    public String generate(String prompt) {
        return nativeGenerate(llmPtr, prompt);
    }
    
    public void streamGenerate(String prompt, StreamCallback callback) {
        nativeStreamGenerate(llmPtr, prompt, callback);
    }
    
    private native long nativeCreateLLM(String modelPath, String configPath);
    private native String nativeGenerate(long llmPtr, String prompt);
    private native void nativeStreamGenerate(long llmPtr, String prompt, 
                                            StreamCallback callback);
    
    public interface StreamCallback {
        void onToken(String token);
        void onFinish();
    }
}
```

## Troubleshooting

### Common Issues

**1. Out of Memory**
- Reduce `max_new_tokens`
- Enable low memory mode
- Use 4-bit quantization instead of 8-bit
- Reduce `max_cache_length`

**2. Slow Generation**
- Enable GPU backend if available
- Use speculative decoding
- Enable ARM v8.2 optimizations
- Increase thread count on CPU

**3. Poor Quality Output**
- Use 8-bit quantization instead of 4-bit
- Adjust temperature, top_k, top_p parameters
- Use HQQ quantization for better accuracy

**4. Model Loading Fails**
- Verify model format is correct MNN format
- Check model and config paths
- Ensure sufficient storage space
- Verify model file is not corrupted

## Benchmark Results

**Android (Snapdragon 8 Gen 2):**

| Model | Backend | Prefill (tokens/s) | Decode (tokens/s) |
|-------|---------|-------------------|-------------------|
| Qwen2-7B | CPU | 45.2 | 8.3 |
| Qwen2-7B | OpenCL | 128.5 | 18.7 |
| Llama3-8B | CPU | 42.8 | 7.9 |
| Llama3-8B | OpenCL | 121.3 | 17.2 |

**iOS (A17 Pro):**

| Model | Backend | Prefill (tokens/s) | Decode (tokens/s) |
|-------|---------|-------------------|-------------------|
| Qwen2-7B | CPU | 52.3 | 9.8 |
| Qwen2-7B | Metal | 156.8 | 22.4 |
| Llama3-8B | CPU | 49.1 | 9.2 |
| Llama3-8B | Metal | 148.2 | 21.1 |

## Reference

- [MNN-LLM Paper](https://arxiv.org/abs/2410.00025)
- [MNN-LLM User Guide](https://mnn-docs.readthedocs.io/en/latest/transformers/llm.html)
- [MNN-LLM Android App](https://github.com/alibaba/MNN/tree/master/apps/Android/MnnLlmChat)
