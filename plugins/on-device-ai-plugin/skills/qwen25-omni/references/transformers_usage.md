# Transformers Usage Guide

## Installation

### Basic Setup

```bash
pip install transformers==4.52.3
pip install accelerate
pip install qwen-omni-utils[decord] -U
pip install soundfile  # For audio output
```

### Optional: FlashAttention-2 (Highly Recommended)

```bash
pip install -U flash-attn --no-build-isolation
```

Requirements:
- CUDA 11.8 or higher
- PyTorch 2.0 or higher
- Compatible GPU (Ampere, Ada, Hopper)

## Model Loading

### Standard Loading

```python
from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

# Load model
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype="auto",  # Uses bfloat16 on compatible hardware
    device_map="auto"     # Automatic device placement
)

# Load processor
processor = Qwen2_5OmniProcessor.from_pretrained("Qwen/Qwen2.5-Omni-7B")
```

### With FlashAttention-2

```python
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"
)
```

Benefits:
- 2x faster inference
- 50% memory reduction
- Better long-context handling

### Available Models

| Model | Parameters | Best For |
|-------|-----------|----------|
| Qwen/Qwen2.5-Omni-7B | 7B | Best quality |
| Qwen/Qwen2.5-Omni-3B | 3B | Faster, lower memory |
| Qwen/Qwen2.5-Omni-7B-GPTQ-Int4 | 7B (4-bit) | Memory constrained |
| Qwen/Qwen2.5-Omni-7B-AWQ | 7B (4-bit) | Memory constrained |

## Conversation Format

### Basic Text Conversation

```python
conversation = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "You are a helpful assistant."}
        ],
    },
    {
        "role": "user",
        "content": "Hello, who are you?"
    }
]
```

### With Audio Output

For audio generation, use this exact system prompt:

```python
conversation = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}
        ],
    },
    {
        "role": "user",
        "content": "Tell me about yourself"
    }
]
```

### Multi-turn Conversation

```python
conversation = [
    {"role": "system", "content": [{"type": "text", "text": "..."}]},
    {"role": "user", "content": "First question"},
    {"role": "assistant", "content": "First response"},
    {"role": "user", "content": "Follow-up question"},
]
```

## Multimodal Input Processing

### Image Input

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "/path/to/image.jpg"},
            {"type": "text", "text": "What's in this image?"},
        ],
    }
]
```

Supported formats: JPG, PNG, BMP, GIF, WebP
Supported sources: Local path, URL, base64

### Audio Input

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "/path/to/audio.wav"},
            {"type": "text", "text": "What's in this audio?"},
        ],
    }
]
```

Supported formats: WAV, MP3, FLAC, OGG
Supported sampling rates: 16kHz, 24kHz, 48kHz

### Video Input

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "/path/to/video.mp4"},
        ],
    }
]
```

Supported formats: MP4, AVI, MOV, MKV
Video will include audio by default if `use_audio_in_video=True`

## Inference

### Standard Inference

```python
from qwen_omni_utils import process_mm_info
import soundfile as sf

# Prepare conversation
USE_AUDIO_IN_VIDEO = True
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)

# Process inputs
inputs = processor(
    text=text, 
    audio=audios, 
    images=images, 
    videos=videos, 
    return_tensors="pt", 
    padding=True,
    use_audio_in_video=USE_AUDIO_IN_VIDEO
)
inputs = inputs.to(model.device).to(model.dtype)

# Generate
text_ids, audio = model.generate(**inputs, use_audio_in_video=USE_AUDIO_IN_VIDEO)

# Decode
text_output = processor.batch_decode(text_ids, skip_special_tokens=True)
print(text_output)

# Save audio
if audio is not None:
    sf.write("output.wav", audio.reshape(-1).detach().cpu().numpy(), samplerate=24000)
```

### Text-Only Inference

```python
# Faster, saves memory
text_ids = model.generate(**inputs, return_audio=False)
text_output = processor.batch_decode(text_ids, skip_special_tokens=True)
```

### Generation Parameters

```python
text_ids, audio = model.generate(
    **inputs,
    max_new_tokens=512,        # Maximum tokens to generate
    temperature=0.7,           # Sampling temperature (0.0-1.0)
    top_p=0.9,                 # Nucleus sampling
    do_sample=True,            # Enable sampling
    speaker="Chelsie",         # Voice type
    use_audio_in_video=True,   # Use audio from video
    return_audio=True          # Generate audio output
)
```

## Batch Processing

```python
conversations = [
    [{"role": "user", "content": [{"type": "image", "image": "img1.jpg"}]}],
    [{"role": "user", "content": [{"type": "audio", "audio": "audio1.wav"}]}],
    [{"role": "user", "content": "Text query"}],
]

text = processor.apply_chat_template(conversations, add_generation_prompt=True, tokenize=False)
audios, images, videos = process_mm_info(conversations)

inputs = processor(
    text=text,
    audio=audios,
    images=images,
    videos=videos,
    return_tensors="pt",
    padding=True
)
inputs = inputs.to(model.device)

# Batch inference (text-only for performance)
text_ids = model.generate(**inputs, return_audio=False)
results = processor.batch_decode(text_ids, skip_special_tokens=True)
```

## Memory Optimization

### Disable Audio Generation

```python
# Saves ~2GB GPU memory
model.disable_talker()

# Now only text output is available
text_ids = model.generate(**inputs, return_audio=False)
```

### Use Gradient Checkpointing (Training Only)

```python
model.gradient_checkpointing_enable()
```

### Reduce Precision

```python
# Use FP16 instead of BF16
model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-Omni-7B",
    torch_dtype=torch.float16,  # or torch.bfloat16
    device_map="auto"
)
```

## Performance Tips

1. **Always use FlashAttention-2** if possible - 2x speedup
2. **Use BF16 precision** on Ampere+ GPUs
3. **Enable compilation** with `torch.compile()` for PyTorch 2.0+
4. **Batch requests** when processing multiple inputs
5. **Use `return_audio=False`** when audio not needed
6. **Pre-process media files** to reduce runtime overhead
7. **Monitor GPU memory** with `nvidia-smi`

## Troubleshooting

### Import Error

```
ImportError: cannot import name 'Qwen2_5OmniForConditionalGeneration'
```

Solution: Ensure transformers==4.52.3 is installed

### Out of Memory

Solutions:
1. Use smaller model (3B instead of 7B)
2. Use quantized model (GPTQ-Int4 or AWQ)
3. Enable `model.disable_talker()`
4. Reduce video length
5. Use multi-GPU with `device_map="auto"`

### Slow Inference

Solutions:
1. Enable FlashAttention-2
2. Use BF16 precision
3. Reduce `max_new_tokens`
4. Use batch processing
5. Consider vLLM for production

### Audio Quality Issues

Solutions:
1. Ensure input audio is 24kHz
2. Use higher precision (BF16 vs quantized)
3. Check speaker parameter
4. Verify system prompt for audio generation
