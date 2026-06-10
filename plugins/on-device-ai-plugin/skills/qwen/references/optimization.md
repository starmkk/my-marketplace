# Optimization Guide

## Memory Optimization

### Level 1: FlashAttention-2

```bash
pip install -U flash-attn --no-build-isolation
```

```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"
)
```

**Benefits:**
- 2x faster inference
- 50% memory reduction
- Better long-context handling

### Level 2: Quantization

#### GPTQ-Int4

```bash
pip install gptqmodel==2.0.0 numpy==2.0.0
```

```python
from gptqmodel import GPTQModel

model = GPTQModel.from_quantized(
    "Qwen/Qwen2.5-Omni-7B-GPTQ-Int4",
    device="cuda:0",
    use_cuda_fp16=True
)
```

**Memory Savings:** 50%+
**Performance Impact:** <5%

#### AWQ

```bash
pip install autoawq==0.2.9
```

```python
from awq import AutoAWQForCausalLM

model = AutoAWQForCausalLM.from_quantized(
    "Qwen/Qwen2.5-Omni-7B-AWQ",
    fuse_layers=True,
    device_map="auto"
)
```

**Memory Savings:** 50%+
**Performance Impact:** <5%

### Level 3: Disable Audio Generation

```python
model.disable_talker()  # Saves ~2GB
```

### Level 4: Use Smaller Model

```python
# Use 3B instead of 7B
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-3B",
    torch_dtype="auto",
    device_map="auto"
)
```

**Memory Savings:** ~50%
**Performance Impact:** ~10-15%

## Speed Optimization

### Enable Compilation (PyTorch 2.0+)

```python
model = torch.compile(model, mode="reduce-overhead")
```

### Batch Processing

```python
# Process multiple inputs at once
inputs = processor(
    text=batch_texts,
    audio=batch_audios,
    images=batch_images,
    return_tensors="pt",
    padding=True
)
```

### Reduce Max Tokens

```python
text_ids = model.generate(
    **inputs,
    max_new_tokens=256  # Lower = faster
)
```

### Multi-GPU Deployment

```python
# Automatic distribution
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    device_map="auto",  # Distributes across GPUs
    torch_dtype="auto"
)
```

## Inference Optimization

### Use Text-Only When Possible

```python
text_ids = model.generate(**inputs, return_audio=False)
```

### Pre-process Media

```python
# Resize images
from PIL import Image
img = Image.open("large.jpg").resize((1024, 1024))

# Resample audio
import librosa
audio, sr = librosa.load("audio.mp3", sr=24000)

# Compress video
# ffmpeg -i input.mp4 -vcodec h264 -acodec aac output.mp4
```

### Cache Frequent Inputs

```python
# Cache processed inputs
input_cache = {}

def get_or_process(media_path):
    if media_path not in input_cache:
        # Process and cache
        input_cache[media_path] = process_media(media_path)
    return input_cache[media_path]
```

## Production Optimization

### Use vLLM

```bash
vllm serve Qwen/Qwen2.5-Omni-7B \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9
```

### Enable Continuous Batching

vLLM automatically enables continuous batching for better throughput.

### Monitor Performance

```python
import time
import torch

start = time.time()
with torch.cuda.amp.autocast():
    output = model.generate(**inputs)
end = time.time()

print(f"Inference time: {end-start:.2f}s")
print(f"GPU memory: {torch.cuda.max_memory_allocated()/1e9:.2f}GB")
```

## Benchmarking

```python
import torch.profiler

with torch.profiler.profile(
    activities=[
        torch.profiler.ProfilerActivity.CPU,
        torch.profiler.ProfilerActivity.CUDA,
    ],
    record_shapes=True,
) as prof:
    output = model.generate(**inputs)

print(prof.key_averages().table(sort_by="cuda_time_total"))
```

## Comparison Table

| Optimization | Memory Savings | Speed Improvement | Quality Impact |
|--------------|----------------|-------------------|----------------|
| FlashAttention-2 | 50% | 2x | None |
| GPTQ-Int4 | 50%+ | -10% | <5% |
| AWQ | 50%+ | -10% | <5% |
| Disable Talker | ~2GB | Slight | N/A (text only) |
| 3B Model | 50% | Same tok/s | ~10% |
| Multi-GPU | None | 2-4x | None |
| vLLM | Better util | 2-3x | None |

## Recommended Configurations

### Development (Single GPU, 24GB)

```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-3B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"
)
```

### Production (Multi-GPU, High Throughput)

```bash
vllm serve Qwen/Qwen2.5-Omni-7B \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --dtype bfloat16
```

### Edge/Mobile (Constrained Memory)

```bash
# Use MNN with 3B model
./llm_demo Qwen2.5-Omni-3B-MNN/config.json prompt.txt
```

### Low-End GPU (12GB VRAM)

```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B-GPTQ-Int4",
    device_map="auto"
)
model.disable_talker()  # Text-only
```
