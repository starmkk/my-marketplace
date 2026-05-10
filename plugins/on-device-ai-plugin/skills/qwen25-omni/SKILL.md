---
name: qwen25-omni
description: |
  Alibaba Cloud Qwen2.5-Omni 멀티모달 AI 모델 개발 스킬
  (텍스트/이미지/오디오/비디오 입력 + 자연스러운 음성 합성 출력).
  Qwen2.5-Omni multimodal AI development skill for Alibaba Cloud's end-to-end model
  (text/image/audio/video input with natural voice synthesis output).

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "Qwen2.5-Omni", "qwen omni", "qwen25-omni"
  - "Transformers/vLLM/MNN으로 Qwen 사용", "Qwen with Transformers/vLLM/MNN"
  - "텍스트/이미지/오디오/비디오 멀티모달 입력", "multimodal input"
  - "실시간 음성 응답", "voice chatting", "speech synthesis"
  - "GPTQ-Int4", "AWQ", "FP16 양자화", "quantization"
  - "Chelsie voice", "Ethan voice", "speaker setting"
  - "모바일/엣지 배포", "mobile/edge deployment with MNN"

  관련 스킬 (Related skills):
  - `mnn`: Qwen2.5-Omni 모바일 배포 백엔드.
  - `gemma4`: 다른 멀티모달 LLM 옵션.
---

# Qwen2.5-Omni Development Skill

## Overview

Qwen2.5-Omni is an end-to-end multimodal model by Qwen team at Alibaba Cloud, capable of understanding text, images, audio, and video while generating real-time text and natural speech responses. This skill provides comprehensive guidance for setup, deployment, and optimization across different platforms.

**Key Capabilities:**
- Multimodal perception: text, images, audio, video
- Real-time speech generation with natural voice
- Streaming responses for interactive applications
- Mobile/edge deployment with MNN
- High-performance inference with vLLM
- API integration with Alibaba Cloud

## Quick Reference

**Core Tasks:**
- **Transformers Setup**: See [Transformers Usage Workflow](#transformers-usage-workflow)
- **vLLM Deployment**: See `references/vllm_deployment.md`
- **MNN Mobile Deployment**: See `references/mnn_deployment.md`
- **Multimodal Input Processing**: See `references/multimodal_inputs.md`
- **Audio Generation**: See `references/audio_generation.md`

**Advanced Topics:**
- **API Integration**: See `references/api_reference.md`
- **Optimization Strategies**: See `references/optimization.md`

## Transformers Usage Workflow

### Step 1: Install Dependencies

**Basic installation:**
```bash
pip install transformers==4.52.3
pip install accelerate
pip install qwen-omni-utils[decord] -U
```

Or use the installation script:
```bash
bash scripts/install_dependencies.sh
```

**With FlashAttention-2 (recommended):**
```bash
pip install -U flash-attn --no-build-isolation
```

### Step 2: Load Model and Processor

**Standard loading:**
```python
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype="auto",
    device_map="auto"
)
processor = Qwen2_5OmniProcessor.from_pretrained("Qwen/Qwen2.5-Omni-7B")
```

**With FlashAttention-2 (2x faster):**
```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype="auto",
    device_map="auto",
    attn_implementation="flash_attention_2"
)
```

**Available models:**
- `Qwen/Qwen2.5-Omni-7B` - Full model
- `Qwen/Qwen2.5-Omni-3B` - Smaller, faster
- `Qwen/Qwen2.5-Omni-7B-GPTQ-Int4` - 4-bit quantized
- `Qwen/Qwen2.5-Omni-7B-AWQ` - AWQ quantized

### Step 3: Prepare Multimodal Input

**Video input with audio:**
```python
from qwen_omni_utils import process_mm_info

conversation = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}
        ],
    },
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "path/to/video.mp4"},
        ],
    },
]

USE_AUDIO_IN_VIDEO = True
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)
inputs = processor(text=text, audio=audios, images=images, videos=videos, 
                   return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
inputs = inputs.to(model.device).to(model.dtype)
```

For detailed multimodal input handling, see `references/multimodal_inputs.md`.

### Step 4: Generate Response

**With text and audio output:**
```python
import soundfile as sf

text_ids, audio = model.generate(**inputs, use_audio_in_video=USE_AUDIO_IN_VIDEO)
text = processor.batch_decode(text_ids, skip_special_tokens=True)
print(text)

# Save audio output
sf.write("output.wav", audio.reshape(-1).detach().cpu().numpy(), samplerate=24000)
```

**Text-only output (faster):**
```python
text_ids = model.generate(**inputs, return_audio=False)
text = processor.batch_decode(text_ids, skip_special_tokens=True)
```

**Change voice type:**
```python
# Available: "Chelsie" (female), "Ethan" (male)
text_ids, audio = model.generate(**inputs, speaker="Chelsie")
```

See `references/audio_generation.md` for complete audio guide.

## GPU Memory Requirements

| Model | Precision | 15s Video | 30s Video | 60s Video |
|-------|-----------|-----------|-----------|-----------|
| 3B | BF16 | 18.38 GB | 22.43 GB | 28.22 GB |
| 7B | BF16 | 31.11 GB | 41.85 GB | 60.19 GB |
| 7B | GPTQ-Int4 | 11.64 GB | 17.43 GB | 29.51 GB |
| 7B | AWQ | 11.77 GB | 17.84 GB | 30.31 GB |

Note: Actual usage is typically 1.2x higher.

## Common Workflows

### Workflow 1: Voice Chatting

1. Install dependencies with FlashAttention-2
2. Load model with audio generation
3. Set system prompt for voice output
4. Process audio/video input
5. Generate text and speech response
6. Handle multi-turn conversations

See `scripts/voice_chatting_demo.py`.

### Workflow 2: Video Analysis

1. Load model (text-only mode saves memory)
2. Prepare video input
3. Process video and audio
4. Generate analysis
5. Extract specific information

See `references/multimodal_inputs.md`.

### Workflow 3: MNN Mobile Deployment

1. Download MNN-converted model
2. Build MNN library
3. Integrate into app
4. Optimize with quantization
5. Profile performance

See `references/mnn_deployment.md`.

### Workflow 4: vLLM Serving

1. Install vLLM from fork
2. Configure multi-GPU
3. Deploy as API server
4. Implement streaming
5. Enable batching

See `references/vllm_deployment.md`.

## Performance Optimization

### Level 1: FlashAttention-2 (Always Use)

```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"
)
```

Benefits: 2x faster, 50% memory reduction

### Level 2: Quantization

**GPTQ-Int4:**
```bash
pip install gptqmodel==2.0.0
python scripts/low_vram_demo_gptq.py
```

**AWQ:**
```bash
pip install autoawq==0.2.9
python scripts/low_vram_demo_awq.py
```

See `references/optimization.md`.

### Level 3: Text-Only Mode

```python
model.disable_talker()  # Saves ~2GB
text_ids = model.generate(**inputs, return_audio=False)
```

## Batch Inference

```python
conversations = [
    [{"role": "user", "content": [{"type": "video", "video": "v1.mp4"}]}],
    [{"role": "user", "content": [{"type": "audio", "audio": "a1.wav"}]}],
    [{"role": "user", "content": "Who are you?"}],
]

text = processor.apply_chat_template(conversations, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversations, use_audio_in_video=True)
inputs = processor(text=text, audio=audios, images=images, videos=videos, 
                   return_tensors="pt", padding=True)
inputs = inputs.to(model.device)

text_ids = model.generate(**inputs, return_audio=False)
results = processor.batch_decode(text_ids, skip_special_tokens=True)
```

See `scripts/batch_inference.py`.

## Troubleshooting

### Installation Issues

**KeyError 'qwen2_5_omni'**
```bash
pip uninstall transformers
pip install transformers==4.52.3
```

**Cannot install decord**
```bash
pip install qwen-omni-utils -U  # Uses torchvision
```

**FlashAttention-2 fails**
```bash
nvcc --version  # Check CUDA 11.8+
pip install flash-attn==2.5.0 --no-build-isolation
```

### Runtime Issues

**Out of memory**
1. Use GPTQ-Int4/AWQ (50% savings)
2. Enable `model.disable_talker()` (~2GB)
3. Reduce video length
4. Use 3B model
5. Multi-GPU deployment

**Audio not working**
1. Check system prompt includes audio instruction
2. `use_audio_in_video` consistent across steps
3. `return_audio=True` (default)
4. Valid speaker ("Chelsie"/"Ethan")
5. Not using `disable_talker()`

**Slow inference**
1. Enable FlashAttention-2 (2x speedup)
2. Use BF16/FP16
3. Use batch processing
4. Consider vLLM

## Best Practices

1. **Always use FlashAttention-2** - 2x gain
2. **Profile memory** - Use `nvidia-smi`
3. **Start with 3B** - Faster iteration
4. **Use batching** - Better GPU use
5. **Enable streaming** - Better UX
6. **Test on target hardware** - Varies
7. **Use vLLM for production**
8. **Error handling** - Graceful degradation
9. **Cache preprocessing** - Avoid recompute

## Additional Resources

- **Transformers**: `references/transformers_usage.md`
- **vLLM**: `references/vllm_deployment.md`
- **MNN**: `references/mnn_deployment.md`
- **Multimodal**: `references/multimodal_inputs.md`
- **Audio**: `references/audio_generation.md`
- **API**: `references/api_reference.md`
- **Optimization**: `references/optimization.md`
- **GitHub**: https://github.com/QwenLM/Qwen2.5-Omni
- **Wiki**: https://deepwiki.com/QwenLM/Qwen2.5-Omni
- **Hugging Face**: https://huggingface.co/Qwen/Qwen2.5-Omni-7B
- **ModelScope**: https://modelscope.cn/models/Qwen/Qwen2.5-Omni-7B
- **Paper**: https://arxiv.org/abs/2503.20215
