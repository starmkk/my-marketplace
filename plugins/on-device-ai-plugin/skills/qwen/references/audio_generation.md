# Audio Generation Guide

## Voice Types

Qwen2.5-Omni supports two voice types:

| Voice | Gender | Description |
|-------|--------|-------------|
| Chelsie | Female | Honeyed, velvety voice with gentle warmth and luminous clarity |
| Ethan | Male | Bright, upbeat voice with infectious energy and warm, approachable vibe |

## System Prompt for Audio Output

**Required system prompt for audio generation:**

```python
{
    "role": "system",
    "content": [
        {
            "type": "text",
            "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."
        }
    ]
}
```

Without this exact prompt, audio generation may not work properly.

## Basic Audio Generation

```python
import soundfile as sf

# Generate with default voice (Chelsie)
text_ids, audio = model.generate(**inputs)

# Save audio
sf.write("output.wav", audio.reshape(-1).detach().cpu().numpy(), samplerate=24000)
```

## Selecting Voice Type

```python
# Use Chelsie (female)
text_ids, audio = model.generate(**inputs, speaker="Chelsie")

# Use Ethan (male)
text_ids, audio = model.generate(**inputs, speaker="Ethan")
```

## Text-Only Mode

### Disable Audio Generation (Saves ~2GB Memory)

```python
# Permanently disable audio generation
model.disable_talker()

# Now can only generate text
text_ids = model.generate(**inputs, return_audio=False)
```

### Temporarily Skip Audio

```python
# Audio generation still available, just not returned
text_ids = model.generate(**inputs, return_audio=False)

# Later can still generate audio
text_ids, audio = model.generate(**other_inputs, return_audio=True)
```

## Audio Output Format

- **Sample Rate**: 24,000 Hz
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono
- **Format**: WAV (recommended)

## Streaming Audio

For real-time applications:

```python
# Generate with streaming
for i in range(num_chunks):
    text_ids, audio_chunk = model.generate(**chunk_inputs, speaker="Chelsie")
    # Process audio_chunk immediately
    play_audio(audio_chunk)
```

## Audio Quality Control

### High Quality (Default)

```python
text_ids, audio = model.generate(
    **inputs,
    temperature=0.7,  # Lower = more consistent
    do_sample=True,
    speaker="Chelsie"
)
```

### Consistent Output

```python
text_ids, audio = model.generate(
    **inputs,
    temperature=0.0,  # Deterministic
    do_sample=False,
    speaker="Chelsie"
)
```

## Multi-Turn Conversations with Audio

```python
import soundfile as sf

conversation = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}
        ],
    },
    {
        "role": "user",
        "content": "Tell me a story"
    }
]

# First turn
text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
inputs = processor(text=text, return_tensors="pt", padding=True)
inputs = inputs.to(model.device)

text_ids, audio = model.generate(**inputs, speaker="Chelsie")
response = processor.batch_decode(text_ids, skip_special_tokens=True)[0]

# Save audio
sf.write("turn1.wav", audio.reshape(-1).detach().cpu().numpy(), samplerate=24000)

# Add response to conversation
conversation.append({"role": "assistant", "content": response})

# Second turn
conversation.append({"role": "user", "content": "Continue the story"})
# ... repeat process
```

## Audio Post-Processing

### Adjust Volume

```python
import numpy as np

audio_np = audio.reshape(-1).detach().cpu().numpy()

# Normalize
audio_normalized = audio_np / np.max(np.abs(audio_np))

# Amplify
audio_loud = audio_normalized * 0.8  # 80% volume

sf.write("output.wav", audio_loud, samplerate=24000)
```

### Convert Format

```python
import subprocess

# WAV to MP3
subprocess.run([
    "ffmpeg", "-i", "output.wav",
    "-codec:a", "libmp3lame",
    "-qscale:a", "2",
    "output.mp3"
])
```

## Performance Considerations

### Memory Usage

- Audio generation adds ~2GB GPU memory
- Use `disable_talker()` if not needed
- Use `return_audio=False` for faster text generation

### Speed

- Audio generation adds ~1-2 seconds per response
- Streaming can reduce perceived latency
- Consider text-only for rapid interactions

## Troubleshooting

### No Audio Generated

Check:
1. System prompt includes audio generation instruction
2. `return_audio` is `True` (default)
3. Model not initialized with `disable_talker()`
4. Valid speaker parameter ("Chelsie" or "Ethan")

### Poor Audio Quality

Solutions:
1. Lower temperature (0.5-0.7)
2. Use BF16 instead of quantized model
3. Ensure sufficient GPU memory
4. Check input audio quality (if voice chat)

### Audio Cutoff

Solutions:
1. Increase `max_new_tokens`
2. Check GPU memory (may be swapping)
3. Reduce concurrent requests

### Wrong Voice

Solution:
```python
# Explicitly set speaker
text_ids, audio = model.generate(**inputs, speaker="Ethan")  # or "Chelsie"
```

## API Usage

When using Alibaba Cloud API:

```python
completion = client.chat.completions.create(
    model="qwen-omni-turbo",
    messages=messages,
    modalities=["text", "audio"],
    audio={
        "voice": "Chelsie",  # or "Ethan", "Cherry", "Serena"
        "format": "wav"
    },
    stream=True
)
```

Note: API supports additional voices not available in local deployment.
