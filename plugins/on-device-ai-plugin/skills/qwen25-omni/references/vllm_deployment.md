# vLLM Deployment Guide

## Installation

Install vLLM from Qwen2.5-Omni fork:

```bash
git clone -b qwen2_omni_public https://github.com/fyabc/vllm.git
cd vllm
git checkout de8f43fbe9428b14d31ac5ec45d065cd3e5c3ee0
pip install setuptools_scm torchdiffeq resampy x_transformers qwen-omni-utils accelerate
pip install -r requirements/cuda.txt
pip install --upgrade setuptools wheel
pip install .
pip install transformers==4.52.3
```

## Offline Inference

### Text-Only (Single GPU)

```bash
python end2end.py \
  --model Qwen/Qwen2.5-Omni-7B \
  --prompt audio-in-video-v2 \
  --enforce-eager \
  --thinker-only
```

### Text-Only (Multi-GPU)

```bash
python end2end.py \
  --model Qwen/Qwen2.5-Omni-7B \
  --prompt audio-in-video-v2 \
  --enforce-eager \
  --thinker-only \
  --thinker-devices [0,1,2,3] \
  --thinker-gpu-memory-utilization 0.9
```

### With Audio Output (Single GPU)

```bash
python end2end.py \
  --model Qwen/Qwen2.5-Omni-7B \
  --prompt audio-in-video-v2 \
  --enforce-eager \
  --do-wave \
  --voice-type Chelsie \
  --warmup-voice-type Chelsie \
  --output-dir output_wav
```

### With Audio Output (Multi-GPU)

```bash
python end2end.py \
  --model Qwen/Qwen2.5-Omni-7B \
  --prompt audio-in-video-v2 \
  --enforce-eager \
  --do-wave \
  --voice-type Chelsie \
  --warmup-voice-type Chelsie \
  --thinker-devices [0,1] \
  --talker-devices [2] \
  --code2wav-devices [3] \
  --thinker-gpu-memory-utilization 0.9 \
  --talker-gpu-memory-utilization 0.9 \
  --output-dir output_wav
```

## Online Serving

### Start Server (Text-Only)

```bash
# Single GPU
vllm serve Qwen/Qwen2.5-Omni-7B \
  --port 8000 \
  --host 127.0.0.1 \
  --dtype bfloat16

# Multi-GPU (4 GPUs)
vllm serve Qwen/Qwen2.5-Omni-7B \
  --port 8000 \
  --host 127.0.0.1 \
  --dtype bfloat16 \
  -tp 4
```

### Client Request

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
        {"type": "audio_url", "audio_url": {"url": "https://example.com/audio.wav"}},
        {"type": "text", "text": "What are these?"}
      ]}
    ]
  }'
```

## Performance Tuning

### GPU Memory Utilization

```bash
vllm serve Qwen/Qwen2.5-Omni-7B \
  --gpu-memory-utilization 0.9  # Use 90% of GPU memory
```

### Tensor Parallelism

```bash
# Split model across 4 GPUs
vllm serve Qwen/Qwen2.5-Omni-7B -tp 4
```

### Max Model Length

```bash
vllm serve Qwen/Qwen2.5-Omni-7B \
  --max-model-len 32768
```

## Benefits Over Transformers

- 2-3x faster inference
- Better GPU utilization
- Built-in API server
- Automatic batching
- Continuous batching
- PagedAttention for memory efficiency

## Limitations

- Currently supports thinker only (text output)
- Audio output requires custom implementation
- Requires installation from fork

## Troubleshooting

### Installation Fails

Solution: Ensure CUDA and PyTorch versions match

### Out of Memory

Solutions:
1. Reduce `--gpu-memory-utilization`
2. Reduce `--max-model-len`
3. Use more GPUs with `-tp`
4. Use quantized model

### Slow Inference

Solutions:
1. Increase `--gpu-memory-utilization`
2. Enable tensor parallelism
3. Use larger batch sizes
