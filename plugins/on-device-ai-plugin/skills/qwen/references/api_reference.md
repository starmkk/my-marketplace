# API Reference Guide

## Alibaba Cloud API

Access Qwen2.5-Omni through Alibaba Cloud Model Studio API.

### Installation

```bash
pip install openai
```

### Basic Usage

```python
import base64
import numpy as np
import soundfile as sf
from openai import OpenAI

client = OpenAI(
    api_key="your_api_key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

messages = [
    {
        "role": "system",
        "content": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.",
    },
    {
        "role": "user",
        "content": [
            {"type": "video_url", "video_url": "https://example.com/video.mp4"},
        ],
    },
]

# Stream mode (required for Qwen-Omni)
completion = client.chat.completions.create(
    model="qwen-omni-turbo",
    messages=messages,
    modalities=["text", "audio"],
    audio={
        "voice": "Chelsie",  # Cherry, Ethan, Serena, Chelsie
        "format": "wav"
    },
    stream=True,
    stream_options={"include_usage": True}
)

# Process response
text = []
audio_string = ""
for chunk in completion:
    if chunk.choices:
        if hasattr(chunk.choices[0].delta, "audio"):
            try:
                audio_string += chunk.choices[0].delta.audio["data"]
            except Exception:
                text.append(chunk.choices[0].delta.audio["transcript"])
    else:
        print(chunk.usage)

print("".join(text))

# Save audio
wav_bytes = base64.b64decode(audio_string)
wav_array = np.frombuffer(wav_bytes, dtype=np.int16)
sf.write("output.wav", wav_array, samplerate=24000)
```

### Available Voices

| Voice | Gender | Description |
|-------|--------|-------------|
| Cherry | Female | Sweet, clear voice |
| Chelsie | Female | Warm, velvety voice |
| Serena | Female | Professional, calm voice |
| Ethan | Male | Upbeat, energetic voice |

### Input Types

**Text:**
```python
{"role": "user", "content": "Hello"}
```

**Image URL:**
```python
{"role": "user", "content": [
    {"type": "image_url", "image_url": "https://example.com/image.jpg"}
]}
```

**Audio URL:**
```python
{"role": "user", "content": [
    {"type": "audio_url", "audio_url": "https://example.com/audio.wav"}
]}
```

**Video URL:**
```python
{"role": "user", "content": [
    {"type": "video_url", "video_url": "https://example.com/video.mp4"}
]}
```

### Parameters

```python
completion = client.chat.completions.create(
    model="qwen-omni-turbo",
    messages=messages,
    modalities=["text", "audio"],  # Output modalities
    audio={
        "voice": "Chelsie",        # Voice type
        "format": "wav"            # Audio format
    },
    temperature=0.7,               # Sampling temperature
    top_p=0.9,                     # Nucleus sampling
    max_tokens=512,                # Max output tokens
    stream=True,                   # Streaming required
    stream_options={
        "include_usage": True      # Include token usage
    }
)
```

### Error Handling

```python
try:
    completion = client.chat.completions.create(...)
    for chunk in completion:
        # Process chunk
        pass
except Exception as e:
    print(f"API Error: {e}")
```

### Rate Limits

Check API documentation for current limits:
https://help.aliyun.com/zh/model-studio/user-guide/qwen-omni

### Pricing

Check current pricing:
https://help.aliyun.com/zh/model-studio/pricing

## Best Practices

1. **Use streaming** - Required for Qwen-Omni
2. **Handle errors gracefully** - Network issues, rate limits
3. **Optimize media files** - Smaller files = faster upload
4. **Cache responses** when appropriate
5. **Monitor usage** - Track token consumption
6. **Use appropriate voice** for context
7. **Implement retry logic** for transient failures

## Troubleshooting

### Connection Error

Solution: Check API key and base_url

### Rate Limit Exceeded

Solution: Implement exponential backoff

### Audio Not Received

Solution: Ensure `modalities=["text", "audio"]` is set

### Invalid Media URL

Solution: Ensure URL is publicly accessible
