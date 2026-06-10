# Multimodal Inputs Guide

## Input Types

Qwen2.5-Omni supports four input modalities:
- **Text**: Questions, instructions, context
- **Images**: Photos, screenshots, diagrams
- **Audio**: Speech, music, sound effects
- **Video**: Video files with optional audio track

## Image Inputs

### Local File

```python
{"type": "image", "image": "/path/to/image.jpg"}
```

### URL

```python
{"type": "image", "image": "https://example.com/image.jpg"}
```

### Base64

```python
import base64

with open("image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

{"type": "image", "image": f"data:image/jpeg;base64,{image_b64}"}
```

### Supported Formats

- JPG/JPEG
- PNG
- BMP
- GIF
- WebP

### Multiple Images

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "image1.jpg"},
            {"type": "image", "image": "image2.jpg"},
            {"type": "text", "text": "Compare these images"},
        ],
    }
]
```

## Audio Inputs

### Local File

```python
{"type": "audio", "audio": "/path/to/audio.wav"}
```

### URL

```python
{"type": "audio", "audio": "https://example.com/audio.wav"}
```

### Supported Formats

- WAV (recommended)
- MP3
- FLAC
- OGG

### Sampling Rates

- 16 kHz
- 24 kHz (recommended)
- 48 kHz

### Audio Examples

**Speech Recognition:**
```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "speech.wav"},
            {"type": "text", "text": "Transcribe this audio"},
        ],
    }
]
```

**Audio Analysis:**
```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "music.mp3"},
            {"type": "text", "text": "Describe the music genre and mood"},
        ],
    }
]
```

## Video Inputs

### Local File

```python
{"type": "video", "video": "/path/to/video.mp4"}
```

### URL

```python
{"type": "video", "video": "https://example.com/video.mp4"}
```

### Supported Formats

- MP4 (recommended)
- AVI
- MOV
- MKV
- WebM

### With Audio Track

```python
# Process video with audio
USE_AUDIO_IN_VIDEO = True

conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "video.mp4"},
        ],
    }
]

audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)
inputs = processor(text=text, audio=audios, images=images, videos=videos,
                   return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
```

### Without Audio Track

```python
# Process only video frames
USE_AUDIO_IN_VIDEO = False

audios, images, videos = process_mm_info(conversation, use_audio_in_video=USE_AUDIO_IN_VIDEO)
inputs = processor(text=text, audio=audios, images=images, videos=videos,
                   return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
```

### Video Examples

**Video Summarization:**
```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "lecture.mp4"},
            {"type": "text", "text": "Summarize the key points"},
        ],
    }
]
```

**Screen Recording Analysis:**
```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "screen_recording.mp4"},
            {"type": "text", "text": "What application is being used?"},
        ],
    }
]
```

## Mixed Inputs

### Image + Audio

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "concert.jpg"},
            {"type": "audio", "audio": "music.wav"},
            {"type": "text", "text": "Is this the same concert?"},
        ],
    }
]
```

### Video + Image

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "gameplay.mp4"},
            {"type": "image", "image": "screenshot.png"},
            {"type": "text", "text": "Does this screenshot come from this video?"},
        ],
    }
]
```

### All Modalities

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Analyze these media files:"},
            {"type": "image", "image": "poster.jpg"},
            {"type": "audio", "audio": "soundtrack.mp3"},
            {"type": "video", "video": "trailer.mp4"},
        ],
    }
]
```

## Processing Pipeline

```python
from qwen_omni_utils import process_mm_info

# Step 1: Prepare conversation
conversation = [...]

# Step 2: Apply chat template
text = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
    tokenize=False
)

# Step 3: Process multimodal info
USE_AUDIO_IN_VIDEO = True
audios, images, videos = process_mm_info(
    conversation,
    use_audio_in_video=USE_AUDIO_IN_VIDEO
)

# Step 4: Create model inputs
inputs = processor(
    text=text,
    audio=audios,
    images=images,
    videos=videos,
    return_tensors="pt",
    padding=True,
    use_audio_in_video=USE_AUDIO_IN_VIDEO
)

# Step 5: Move to device
inputs = inputs.to(model.device).to(model.dtype)

# Step 6: Generate
text_ids, audio = model.generate(**inputs, use_audio_in_video=USE_AUDIO_IN_VIDEO)
```

## Best Practices

1. **Use consistent `use_audio_in_video`** across all steps
2. **Optimize media files** before processing:
   - Resize images to reasonable resolution (e.g., 1024x1024)
   - Resample audio to 24kHz
   - Compress videos to reduce file size
3. **Use local files** when possible (faster than URLs)
4. **Batch similar requests** for better GPU utilization
5. **Monitor memory usage** with longer videos
6. **Pre-validate file formats** to avoid runtime errors

## Limitations

- **Max video length**: ~60 seconds recommended for single GPU
- **Image resolution**: Higher resolution = more memory
- **Audio duration**: No hard limit but affects memory
- **Concurrent media**: Processing multiple videos increases memory

## Troubleshooting

### Video URL Not Loading

Check backend compatibility:
- torchvision >= 0.19.0: HTTP and HTTPS ✅
- torchvision < 0.19.0: No URLs ❌
- decord: HTTP only ✅

Solution:
```bash
pip install torchvision>=0.19.0
```

### Out of Memory with Video

Solutions:
1. Reduce video length (split into segments)
2. Lower video resolution
3. Set `use_audio_in_video=False`
4. Use smaller model (3B)
5. Use quantized model

### Audio Format Not Supported

Solution:
```bash
# Convert to WAV with ffmpeg
ffmpeg -i input.mp3 -ar 24000 output.wav
```

### Image Too Large

Solution:
```python
from PIL import Image

img = Image.open("large_image.jpg")
img = img.resize((1024, 1024), Image.LANCZOS)
img.save("resized_image.jpg")
```
