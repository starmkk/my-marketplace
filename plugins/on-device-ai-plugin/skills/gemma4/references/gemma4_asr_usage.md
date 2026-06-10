# Gemma 4 E2B-it ASR API 가이드

출처:
- https://huggingface.co/google/gemma-4-E2B-it
- https://ai.google.dev/gemma/docs/capabilities/audio
- https://github.com/huggingface/huggingface-gemma-recipes

## 모델 능력 (공식 명시)
- **입력**: text + image + video + audio (E2B/E4B만 audio 지원)
- **출력**: 텍스트 전용 (TTS 불가)
- **오디오 능력**: ASR + speech-to-translated-text
- **Audio encoder**: conformer-based, 40ms frame duration
- **Edge 최적화**: Gemma 3N 대비 50% 작은 audio encoder

## 라이선스
- Gemma Terms of Use (https://ai.google.dev/gemma/terms)
- 상업 활용 허용. 단 Gemma 약관의 acceptable use policy 준수 필요.

## 표준 코드 패턴 (공식)

```python
import torch
from transformers import AutoProcessor, AutoModelForMultimodalLM
# 일부 transformers 버전은 AutoModelForImageTextToText로 명명
# from transformers import AutoModelForImageTextToText as AutoModelForMultimodalLM

MODEL_ID = "google/gemma-4-E2B-it"  # 또는 로컬 경로

processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(
    MODEL_ID,
    dtype="auto",       # bfloat16 자동 선택 (GPU/MPS)
    device_map="auto",
)

messages = [
    {
        "role": "user",
        "content": [
            # ⚠️ multimodal 입력은 텍스트보다 앞에 배치 권장
            {"type": "audio", "audio": "/path/to/audio.wav"},
            {"type": "text", "text": "Transcribe the following speech in Korean."},
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
).to(model.device)

input_len = inputs["input_ids"].shape[-1]

with torch.inference_mode():
    outputs = model.generate(**inputs, max_new_tokens=128, do_sample=False)

generated = outputs[0][input_len:]
text = processor.decode(generated, skip_special_tokens=True)
print(text)
```

## ASR 프롬프트 추천

### 단순 transcription
```
Transcribe the following speech segment in Korean.
Output only the transcribed text, no other commentary.
```

### Speech translation (보너스)
공식 가이드의 권장 형식:
```
Transcribe the following speech segment in Korean,
then translate it into English.
```

### 키워드 검증 (이 스킬의 용도)
```
Transcribe the following speech segment in Korean.
Output only the transcribed text, no other commentary.
```

→ thinking을 끄고 (system prompt에 `<|think|>` 미포함), do_sample=False로 결정론적 출력.

## Thinking 모드
- 모든 Gemma 4 모델은 thinking 모드 지원
- system prompt에 `<|think|>` 토큰을 넣으면 활성화
- ASR에는 thinking 불필요 → 사용하지 말 것
- **E2B/E4B variant는 thinking 비활성화 시 빈 thought block조차 생성하지 않음** (호환 OK)

## 의존성
```bash
pip install -U "transformers>=4.50" torch torchvision accelerate librosa soundfile
```

- transformers 최신 (Gemma 4 통합)
- torchvision: image 처리에 필요 (audio 단독이라도 의존성 체인에 포함)
- librosa: 모델 내부에서 audio 리샘플링/feature extract
- accelerate: device_map="auto" 지원

## 디바이스 가이드

| 환경 | dtype | device_map | 비고 |
|---|---|---|---|
| CUDA GPU (A100, RTX 30/40) | bfloat16 | "auto" | 가장 빠름. fp16도 OK |
| Mac M1/M2/M3 | bfloat16 | "mps" | "auto"가 깨질 수 있어 명시 |
| CPU only | float32 | "cpu" | 느리지만 안정적 |

## 메모리 사용량 (참고)
- E2B-it bfloat16: 약 5GB
- E2B-it int4 (GGUF): 약 2GB
- E4B-it bfloat16: 약 9GB

KWS QA용은 E2B-it면 충분.

## 알려진 이슈
1. **`AutoModelForMultimodalLM` 클래스명**: transformers 버전에 따라
   `AutoModelForImageTextToText`로도 import 가능. fallback 코드 권장.
2. **MPS에서 NaN/inf**: 일부 케이스에서 발생. 그때는 `device_map="cpu"` 폴백.
3. **첫 호출 지연**: 모델 로드 + 컴파일로 ~30초. 본 스킬은 싱글톤 캐시(`_asr.py`)로
   배치 처리 시 1회만 로드.
4. **Audio 전처리는 자동**: 16kHz가 아니어도 됨, 모델이 내부에서 리샘플링.
   하지만 입력이 16kHz면 약간 더 빠름.
