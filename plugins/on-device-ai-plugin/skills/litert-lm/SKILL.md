---
name: litert-lm
description: |
  Google LiteRT-LM 온디바이스 LLM 추론 프레임워크 레퍼런스 스킬.
  Reference for Google LiteRT-LM, an on-device LLM inference framework.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "litert-lm", "litertlm"
  - ".litertlm 모델 로딩/실행", "on-device LLM"
  - "Engine API", "Conversation API", "Session API"
  - "Gemma inference", "Qwen on-device"
  - "function calling", "tool use", "constrained decoding"
  - "멀티모달 추론", "vision/audio LLM"

  관련 스킬 (Related skills):
  - `litert`: 하위 추론 엔진(LiteRT).
  - `gemma4`: LiteRT-LM으로 실행할 대표 모델.
  - `gallery`: LiteRT-LM을 호스팅하는 Android/iOS 앱.
---

# LiteRT-LM 레퍼런스 스킬

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `LITERT_LM_SOURCE_PATH` | 선택 | LiteRT-LM 소스코드 레포 로컬 클론 경로 |

미설정 시에도 레퍼런스 스킬로 사용 가능하다. 로컬 클론이 있으면 설정해두면 소스 파일을 직접 참조할 수 있다.

**설정 방법:**
```shell
# 클론
git clone https://github.com/google-ai-edge/LiteRT-LM

# 등록 (zsh/bash)
echo 'export LITERT_LM_SOURCE_PATH=/path/to/LiteRT-LM' >> ~/.zshrc
source ~/.zshrc

# 검증
bash scripts/install.sh
```

---

LiteRT-LM은 Google의 온디바이스 LLM 추론 프레임워크다. Chrome, Chromebook Plus, Pixel Watch 등에서 GenAI 경험을 구동한다. Gemma, Qwen, Llama, Phi 등 다양한 LLM을 CPU/GPU/NPU에서 실행할 수 있다.

## 코드베이스 탐색 방법

이 스킬은 경로에 의존하지 않는다. LiteRT-LM 소스코드를 찾으려면:
1. 프로젝트의 CLAUDE.md나 설정 파일에서 LiteRT-LM 경로를 확인
2. `find` 또는 `glob`으로 `runtime/core/engine_impl.cc` 또는 `python/litert_lm/` 패턴 검색
3. 일반적 위치: `third_party/LiteRT-LM.main/`, `external/litert-lm/` 등

## 핵심 아키텍처

```
EngineSettings → Engine::Create() → Conversation::Create() → send_message() → Response
                  (Model + Tokenizer + Executor)
```

### 디렉토리 구조
```
LiteRT-LM/
├── c/                  # C API (engine.h - FFI/JNI용)
├── runtime/            # 핵심 C++ 런타임
│   ├── core/           # engine_impl, session_basic/advanced, tasks
│   ├── engine/         # Engine 인터페이스, settings
│   ├── executor/       # LLM/Vision/Audio executor
│   ├── conversation/   # 멀티턴 대화 관리
│   ├── components/     # tokenizer, prompt_template, lora, constrained_decoding
│   ├── proto/          # protobuf 정의 (engine, llm_model_type, sampler_params)
│   └── util/           # 유틸리티
├── python/             # Python API + CLI
│   ├── litert_lm/      # 핵심 라이브러리 (interfaces.py, tools.py)
│   └── litert_lm_cli/  # CLI 도구
├── kotlin/             # Kotlin/Android 바인딩
├── schema/             # .litertlm 파일 포맷 (FlatBuffers)
│   └── core/           # litertlm_header_schema.fbs, read/export
├── prebuilt/           # 플랫폼별 프리빌트 바이너리
├── CMakeLists.txt      # CMake 빌드
└── Cargo.toml          # Rust 의존성
```

## 주요 API

### Python API

```python
import litert_lm

# Engine 생성
with litert_lm.Engine(
    model_path="model.litertlm",
    backend=litert_lm.Backend.CPU,  # CPU=3, GPU=4
    max_num_tokens=4096,
) as engine:
    # Conversation 생성
    with engine.create_conversation(
        messages=[{"role": "system", "content": "You are helpful."}],
        sampler_config={"temperature": 0.7, "top_k": 40, "top_p": 0.95},
    ) as conversation:
        # 동기 호출
        response = conversation.send_message("Hello")

        # 스트리밍 (비동기)
        for chunk in conversation.send_message_async("Hello"):
            print(chunk["content"][0]["text"], end="", flush=True)
```

### Function Calling (Tool Use)

```python
from litert_lm import Tool

def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Sunny in {location}"

with engine.create_conversation(
    messages=[...],
    tools=[get_weather],
) as conv:
    response = conv.send_message("What's the weather in Seoul?")
    # 모델이 get_weather("Seoul")을 호출 → 결과를 자동으로 피드백
```

### CLI

```bash
# HuggingFace에서 다운로드 + 실행
litert-lm run \
    --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm \
    gemma-4-E2B-it.litertlm \
    --prompt="Hello"

# 모델 목록
litert-lm list
```

### Kotlin/Android API

```kotlin
val engine = Engine(
    modelPath = "model.litertlm",
    backend = Backend.CPU,
    maxNumTokens = 4096
)
val conversation = engine.createConversation(messages = listOf(...))
val response = conversation.sendMessage("Hello")
```

## 모델 포맷 (.litertlm)

FlatBuffers 헤더 + 섹션 기반 바이너리 포맷:
- **Header**: FlatBuffers 스키마 (`litertlm_header_schema.fbs`)
- **Sections**: TFLite 모델, Tokenizer (SP/HF), LLM Metadata
- 16KB 블록 정렬로 효율적 메모리 매핑

## 지원 모델

| 모델 | 멀티모달 | Function Calling |
|------|----------|------------------|
| Gemma 4 | Vision + Audio | O |
| Gemma 3 | Vision | - |
| Gemma 3N | Vision + Audio | - |
| Qwen 3 / 2.5 | - | O |
| Llama | - | - |
| Phi-4 | - | - |
| FunctionGemma | - | O |

## 추론 파이프라인

1. **Prefill**: 입력 프롬프트 토큰 일괄 처리
2. **Decode**: 토큰 하나씩 생성 (sampling: Top-K, Top-P, Greedy, Temperature)
3. **KV Cache**: 어텐션 키-값 캐시 (configurable max tokens)

## 멀티모달 지원

```python
# Vision (이미지 입력)
conversation.send_message({
    "text": "Describe this image",
    "image": image_bytes  # 또는 파일 경로
})

# Audio (오디오 입력)
conversation.send_message({
    "text": "Transcribe this",
    "audio": audio_bytes
})
```

## 빌드 시스템

### CMake (주 빌드)
```bash
cmake -B cmake/build -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=20
cmake --build cmake/build -t litert_lm_main -j4
```

### 의존성
- C++20 (gcc/g++ 13+), CMake 3.25+, Python 3.12+
- Protobuf 3, FlatBuffers, Abseil, HuggingFace Tokenizers
- XNNPACK, SentencePiece, ANTLR4, llguidance

## 플랫폼 지원

| 플랫폼 | CPU | GPU | NPU |
|--------|-----|-----|-----|
| Android (ARM64, x86_64) | O | O | O |
| iOS (ARM64) | O | - | - |
| Linux (x86_64, ARM64) | O | O | - |
| macOS (ARM64) | O | - | - |
| Windows (x86_64) | O | - | - |

## LiteRT와의 관계

LiteRT-LM은 LiteRT 위에 구축되었다:
- 모델은 TFLite (.tflite) 포맷으로 컴파일
- LiteRT의 GPU/NPU delegate를 통한 하드웨어 가속
- `litert::Environment` C++ API를 내부적으로 사용

## 상세 레퍼런스

핵심 컴포넌트, Constrained Decoding, LoRA, Speculative Decoding 등의 상세 내용은 `references/architecture.md`를 참조하라.
