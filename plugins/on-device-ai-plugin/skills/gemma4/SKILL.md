---
name: gemma4
description: |
  Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스 스킬.
  Reference for the official usage of Google Gemma 4 multimodal models.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "gemma4", "gemma 4", "E2B", "E4B", "12B", "26B", "31B"
  - "Gemma 모델 로드/추론/파인튜닝", "Gemma load/inference/finetune"
  - "apply_chat_template", "멀티모달 입력 구성", "multimodal input"
  - "ASR", "전사", "transcribe", "오디오 입력", "이미지/비디오 입력"
  - "thinking mode", "function calling"
  - "vLLM 서빙", "llama.cpp 서빙", "MLX 서빙"

  관련 스킬 (Related skills):
  - `litert-lm`: Gemma 4를 온디바이스에서 실행할 때.
---

# Gemma 4 공식 사용법 레퍼런스

## 모델 관리 (~/.claude/repo)

모델이 필요한 작업(예: ASR, 추론, 파인튜닝 등)이 생기면
**반드시 먼저 사용자에게 확인**한다:

```
[모델 사용 흐름]
Step 1. 사용자에게 묻기:
  "로컬에 이미 Gemma 4 모델이 있으신가요? 있다면 경로를 알려주세요."

Step 2a. 사용자가 경로 제공 → 해당 경로 그대로 사용

Step 2b. 사용자가 없다고 하면 → ~/.claude/repo에 자동 다운로드 후 안내
```

### 모델 저장 경로

| 항목 | 값 |
|------|-----|
| HuggingFace | `google/gemma-4-E2B-it`, `google/gemma-4-E4B-it` 등 |
| 폴더 패턴 | `~/.claude/repo/gemma-4-<variant>` |

### 다운로드 방법

```bash
pip install huggingface_hub

# E2B-it (128K, 오디오/이미지/비디오 지원)
huggingface-cli download google/gemma-4-E2B-it \
  --local-dir ~/.claude/repo/gemma-4-E2B-it

# E4B-it
huggingface-cli download google/gemma-4-E4B-it \
  --local-dir ~/.claude/repo/gemma-4-E4B-it

# 12B-it (256K, 오디오/이미지/비디오 지원, Unified encoder-free)
huggingface-cli download google/gemma-4-12B-it \
  --local-dir ~/.claude/repo/gemma-4-12B-it
```

이미 `~/.claude/repo/gemma-4-<variant>`이 존재하면 재다운로드 없이 재사용한다.
다운로드 후 사용자에게 경로 안내.

---

공식 문서: https://huggingface.co/blog/gemma4
모델 카드: https://huggingface.co/google/gemma-4-E2B-it

## 모델 라인업

| 모델 | 유효 파라미터 | 임베딩 포함 | 컨텍스트 | 오디오 지원 |
|------|-------------|-----------|---------|-----------|
| Gemma 4 E2B | 2.3B | 5.1B | 128K | O |
| Gemma 4 E4B | 4.5B | 8B | 128K | O |
| Gemma 4 12B | 11.95B (Unified, encoder-free) | - | 256K | O |
| Gemma 4 26B A4B | 4B activated / 26B total (MoE) | - | 256K | X |
| Gemma 4 31B | 31B dense | - | 256K | X |

**모달리티 지원:**
- E2B, E4B, 12B: 텍스트 + 이미지 + 비디오 + 오디오
- 26B A4B, 31B: 텍스트 + 이미지 (오디오·비디오 없음)

## 핵심 패턴: apply_chat_template

**IMPORTANT**: Gemma 4 모델은 반드시 `processor.apply_chat_template()` 방식으로 입력을 구성해야 한다.
`processor(text=..., audio=...)` 직접 호출은 오디오 토큰, mm_token_type_ids 등이 올바르게 설정되지 않을 수 있다.

### 기본 구조

```python
from transformers import AutoModelForMultimodalLM, AutoProcessor

model = AutoModelForMultimodalLM.from_pretrained("google/gemma-4-E2B-it", device_map="auto")
processor = AutoProcessor.from_pretrained("google/gemma-4-E2B-it")

# messages 구성
messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "URL 또는 numpy_array", "sample_rate": 16000},
            {"type": "text", "text": "프롬프트 텍스트"},
        ],
    }
]

# 토크나이즈
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
).to(model.device)

# 생성 — 반드시 **inputs로 모든 텐서 전달
output = model.generate(**inputs, max_new_tokens=512, do_sample=False)

# 디코딩 — 프롬프트 제거 후
input_len = inputs["input_ids"].shape[-1]
response = processor.decode(output[0][input_len:], skip_special_tokens=True)
```

### apply_chat_template 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|-------|------|
| `tokenize` | - | True: 토큰화 수행 |
| `return_dict` | - | True: Dict 형식 반환 |
| `return_tensors` | - | "pt": PyTorch 텐서 |
| `add_generation_prompt` | False | True: 생성 프롬프트 추가 (추론 시 필수) |
| `enable_thinking` | False | True: Thinking 모드 활성화 |
| `load_audio_from_video` | False | True: 비디오에서 오디오도 로드 (E2B/E4B/12B만) |
| `tools` | None | Function Calling 도구 정의 리스트 |

## 오디오 ASR (음성 인식)

### 단일 오디오 전사

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": "URL 또는 numpy_array", "sample_rate": 16000},
            {"type": "text", "text": "Transcribe the audio."},
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
).to(model.device)

output = model.generate(**inputs, max_new_tokens=1000, do_sample=False)
print(processor.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True))
```

### 공식 ASR 프롬프트 (상세 지시)

```python
# 공식 모델 카드 권장 프롬프트
ASR_PROMPT = (
    "Transcribe the following speech segment in its original language. "
    "Follow these specific instructions for formatting the answer:\n"
    "* Only output the transcription, with no newlines.\n"
    "* When transcribing numbers, write the digits, i.e. write 1.7 "
    "and not one point seven, and write 3 instead of three."
)
```

### 오디오 입력 방식

```python
# 방법 1: URL
{"type": "audio", "url": "https://example.com/audio.mp3"}

# 방법 2: 로컬 numpy array + sample_rate
import soundfile as sf
waveform, sr = sf.read("audio.flac", dtype="float32")
{"type": "audio", "audio": waveform, "sample_rate": sr}
```

**오디오 제한사항:**
- 최대 30초
- E2B, E4B, 12B 지원 (26B A4B, 31B 미지원)
- 음성만 학습됨 (음악/비음성 소리 미지원)

## 이미지 이해

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "https://example.com/image.png"},
            {"type": "text", "text": "What's in this image?"},
        ],
    }
]

inputs = processor.apply_chat_template(
    messages, tokenize=True, return_dict=True, return_tensors="pt",
    add_generation_prompt=True,
).to(model.device)

output = model.generate(**inputs, max_new_tokens=200)
```

### Object Detection (Bounding Box)

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "https://example.com/image.png"},
            {"type": "text", "text": "What's the bounding box for the 'view recipe' element?"},
        ],
    }
]
# 출력: [{"box_2d": [y1, x1, y2, x2], "label": "view recipe element"}]
```

## 비디오 이해

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "video", "url": "https://example.com/video.mp4"},
            {"type": "text", "text": "What is happening in the video?"},
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
    load_audio_from_video=True,   # E2B/E4B/12B: 비디오 오디오도 처리
).to(model.device)

output = model.generate(**inputs, max_new_tokens=200)
```

## Thinking 모드

내부 추론 과정을 활성화하여 복잡한 문제에 대해 더 정확한 답변을 생성한다.

```python
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
    enable_thinking=True,           # Thinking 모드 활성화
).to(model.device)

output = model.generate(**inputs, max_new_tokens=4000)
input_len = inputs["input_ids"].shape[-1]
generated_text = processor.decode(output[0][input_len:], skip_special_tokens=True)

# parse_response로 사고 과정과 최종 답변 분리
result = processor.parse_response(generated_text)
print(result["content"])          # 최종 답변
```

## Function Calling

```python
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Gets the current weather for a specific location.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"},
            },
            "required": ["city"],
        },
    },
}

messages = [
    {"role": "user", "content": [
        {"type": "text", "text": "What is the weather in Seoul?"},
    ]},
]

inputs = processor.apply_chat_template(
    messages,
    tools=[WEATHER_TOOL],           # 도구 정의 전달
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
    enable_thinking=True,
).to(model.device)

output = model.generate(**inputs, max_new_tokens=1000)
generated_text = processor.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
result = processor.parse_response(generated_text)
# 출력 예: call:get_weather{city:Seoul}
```

## 학습 (Fine-tuning)

### 학습용 데이터 구성 (apply_chat_template)

```python
# 전체 대화 (프롬프트 + 응답)
full_messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": waveform, "sample_rate": 16000},
            {"type": "text", "text": "Transcribe the audio."},
        ],
    },
    {
        "role": "assistant",
        "content": [{"type": "text", "text": target_text}],
    },
]
full_inputs = processor.apply_chat_template(
    full_messages, tokenize=True, return_dict=True, return_tensors="pt",
)

# 프롬프트만 (labels 마스킹용 길이 계산)
prompt_messages = [
    {
        "role": "user",
        "content": [
            {"type": "audio", "audio": waveform, "sample_rate": 16000},
            {"type": "text", "text": "Transcribe the audio."},
        ],
    },
]
prompt_inputs = processor.apply_chat_template(
    prompt_messages, tokenize=True, return_dict=True, return_tensors="pt",
    add_generation_prompt=True,
)
prompt_length = prompt_inputs["input_ids"].shape[1]

# labels: 프롬프트 부분은 -100
labels = full_inputs["input_ids"].clone()
labels[:, :prompt_length] = -100
```

### TRL Fine-tuning

```bash
pip install git+https://github.com/huggingface/trl.git

python examples/scripts/openenv/carla_vlm_gemma.py \
    --env-urls https://sergiopaniego-carla-env.hf.space \
    --model google/gemma-4-E2B-it
```

## 서빙 및 배포

### llama.cpp

```bash
brew install llama.cpp
llama-server -hf ggml-org/gemma-4-E2B-it-GGUF
```

### MLX (Apple Silicon)

```bash
pip install -U mlx-vlm

mlx_vlm.generate \
  --model google/gemma-4-E4B-it \
  --image image.png \
  --prompt "Describe this image"

# 양자화 모델 + KV 캐시 양자화
mlx_vlm.generate \
  --model "mlx-community/gemma-4-26b-a4b-it-4bit" \
  --prompt "Your prompt" \
  --kv-bits 3.5 --kv-quant-scheme turboquant
```

### mistral.rs (Rust)

```bash
mistralrs serve mistralrs-community/gemma-4-E4B-it-UQFF --from-uqff 8
mistralrs run -m google/gemma-4-E4B-it --isq 8 --audio audio.mp3 -i "Transcribe this."
```

### Pipeline (간편 사용)

```python
from transformers import pipeline

pipe = pipeline("any-to-any", model="google/gemma-4-E2B-it")

messages = [
    {"role": "user", "content": [
        {"type": "image", "image": "https://example.com/image.png"},
        {"type": "text", "text": "Describe this image."},
    ]},
]

output = pipe(messages, max_new_tokens=100, return_full_text=False)
print(output[0]["generated_text"])
```

## 아키텍처 핵심 특징

1. **Alternating Attention**: Local SWA(512/1024) + Global 교대 패턴
2. **Dual RoPE**: SWA 레이어는 표준 RoPE, Global 레이어는 비례 RoPE (장문맥)
3. **Per-Layer Embeddings (PLE)**: 각 디코더 레이어에 토큰별 잔여 신호 주입 → 파라미터 대비 성능 향상
4. **Shared KV Cache**: 마지막 N개 레이어가 이전 레이어의 K/V 재사용 → 메모리 절감
5. **비전 인코더**: 원본 종횡비 유지, 토큰 예산 선택 가능 (70~1120)
6. **오디오 인코더**: USM Conformer, ~25 tokens/sec

## 자주 하는 실수 (주의사항)

1. **`processor(text=..., audio=...)` 직접 호출 금지** → 반드시 `apply_chat_template` 사용
2. **`model.generate(input_ids=..., ...)` 선택적 전달 금지** → 반드시 `model.generate(**inputs, ...)` 사용
3. **오디오는 텍스트 앞에 배치** — messages content에서 audio가 text보다 먼저
4. **E2B/E4B/12B만 오디오 지원** — 26B A4B, 31B는 오디오 미지원
5. **오디오 최대 30초** — 초과 시 잘라야 함
6. **비디오 오디오 로드** — E2B/E4B/12B에서 비디오의 오디오도 처리하려면 `load_audio_from_video=True`

## 벤치마크 (참고)

| 벤치마크 | 31B | 26B A4B | E4B | E2B |
|---------|-----|---------|-----|-----|
| MMLU Pro | 85.2% | 82.6% | 69.4% | 60.0% |
| AIME 2026 | 89.2% | 88.3% | 42.5% | 37.5% |
| LiveCodeBench | 80.0% | 77.1% | 52.0% | 44.0% |
| MMMU Pro | 76.9% | 73.8% | 52.6% | 44.2% |

## ASR Round-Trip QA (합성 데이터 품질 검증)

Gemma 4 E2B-it의 ASR 기능을 활용해 TTS 합성 wav를 전사하고 원본 텍스트와
비교(CER/WER)하여 품질이 낮은 데이터를 자동 필터링한다.

### 모델 경로

`~/.claude/repo/gemma-4-<variant>` 경로 또는 사용자 제공 경로를 사용한다 (`scripts/_asr.py` 참고).

### 주요 스크립트 (scripts/)

| 스크립트 | 기능 |
|----------|------|
| `transcribe.py` | 단일 wav 전사 |
| `batch_transcribe.py` | 디렉토리 내 wav 배치 전사 → CSV |
| `round_trip_qa.py` | 원본 manifest와 ASR 결과 비교 → QA 리포트 |
| `filter_synth_dataset.py` | E2E — 배치 전사 + QA 필터링 |
| `_asr.py` | ASR 공통 유틸리티 |

### 빠른 시작

```bash
# 단일 wav 전사 테스트
python scripts/transcribe.py --audio /path/to/test.wav --language Korean

# E2E 필터링 (배치)
python scripts/filter_synth_dataset.py \
  --in_dir /path/to/synth_aug \
  --source_manifest /path/to/manifest.csv \
  --out_filtered_manifest ./filtered_manifest.csv \
  --cer_threshold 0.3
```

### CER 임계값 가이드

| CER | 권장 사용처 |
|-----|------------|
| < 0.10 | 평가셋, 핵심 학습 데이터 |
| < 0.20 | 일반 학습 데이터 |
| < 0.30 | 대량 학습 데이터 (권장 기본값) |
| < 0.50 | 사전학습 / curriculum learning 초기 |

### 참고 문서

- `references/gemma4_asr_usage.md` — ASR API 상세
- `references/round_trip_qa_strategy.md` — Round-trip QA 이론
- `references/cer_wer_metrics.md` — 한국어 CER/WER 계산 주의사항
- `examples/qa_config.yaml` — QA 설정 예시
