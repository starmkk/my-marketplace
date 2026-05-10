# LiteRT-LM 상세 아키텍처 레퍼런스

## 목차
1. [Engine 생성 상세](#engine-creation)
2. [Conversation & Session](#conversation-session)
3. [Tokenizer](#tokenizer)
4. [Constrained Decoding](#constrained-decoding)
5. [Function Calling 상세](#function-calling)
6. [LoRA 지원](#lora)
7. [Speculative Decoding](#speculative-decoding)
8. [Proto 정의](#proto-definitions)
9. [.litertlm 파일 포맷](#file-format)
10. [주요 파일 경로 매핑](#file-paths)

---

## Engine Creation

### 내부 흐름

```
EngineSettings
  ├── model_path: 모델 파일 경로
  ├── backend: CPU(3) | GPU(4)
  ├── max_num_tokens: KV 캐시 크기
  ├── cache_dir: 컴파일 아티팩트 캐시
  ├── vision_backend: 비전 백엔드
  ├── audio_backend: 오디오 백엔드
  └── enable_speculative_decoding: 투기적 디코딩
       ↓
Engine::Create()  [engine_impl.cc]
  ├── .litertlm 파일 파싱 (섹션별 분리)
  ├── LiteRT Environment 생성 (dispatch lib 경로 포함)
  ├── Tokenizer 초기화 (HuggingFace or SentencePiece)
  ├── LLM Executor 생성 (prefill/decode 모델)
  ├── Vision Executor 생성 (선택)
  ├── Audio Executor 생성 (선택)
  └── Engine 인스턴스 반환
```

### Engine Settings 전체 옵션

```python
engine = litert_lm.Engine(
    model_path="model.litertlm",        # 필수
    backend=litert_lm.Backend.CPU,       # CPU=3, GPU=4
    max_num_tokens=4096,                 # KV 캐시 최대 토큰
    cache_dir="/tmp/litert-lm-cache",    # 컴파일 캐시
    vision_backend=litert_lm.Backend.CPU,# 비전 백엔드
    audio_backend=litert_lm.Backend.CPU, # 오디오 백엔드
    enable_speculative_decoding=None,    # 투기적 디코딩
    npu_dispatch_dir="/path/to/npu/",    # NPU 디스패치 라이브러리
)
```

---

## Conversation & Session

### Conversation

```python
conversation = engine.create_conversation(
    messages=[
        {"role": "system", "content": "시스템 프롬프트"},
        {"role": "user", "content": "이전 사용자 메시지"},
        {"role": "assistant", "content": "이전 어시스턴트 응답"},
    ],
    tools=[func1, func2],                # Function calling
    sampler_config={                      # 샘플링 설정
        "temperature": 0.7,
        "top_k": 40,
        "top_p": 0.95,
    },
    enable_constrained_decoding=False,    # 제약 디코딩
)
```

**내부 동작:**
1. Jinja2 템플릿으로 프롬프트 포맷팅
2. 모델별 데이터 프로세서 초기화 (Gemma4, Qwen 등)
3. KV 캐시 + 대화 상태 설정
4. 샘플러 파라미터 적용

### Session

```python
session_config = litert_lm.Session.Config(
    max_output_tokens=256,
    sampler_params=litert_lm.SamplerParams(
        type=litert_lm.SamplerType.TopP,
        top_p=0.95,
        temperature=0.7,
    )
)
```

### 추론 흐름 (session_basic.cc)

1. 입력 텍스트 토크나이즈
2. **Prefill**: 모든 입력 토큰 일괄 처리 → KV 캐시 채움
3. **Decode 루프**: 토큰 하나씩 생성
   - Logits 계산
   - Sampling (Top-K/Top-P/Temperature)
   - EOS 토큰 체크
   - 콜백으로 partial result 스트리밍
4. 디토크나이즈 → 텍스트 반환

---

## Tokenizer

### HuggingFace Tokenizer
- BPE(Byte-Pair Encoding) 기반
- JSON 설정 파일에서 로드
- Rust `tokenizers` 라이브러리 사용
- 구현: `runtime/components/huggingface_tokenizer.cc`

### SentencePiece Tokenizer
- 문자/서브워드 토크나이저
- `.spm` 모델 파일
- Gemma 모델에서 주로 사용

### 인터페이스
```cpp
class Tokenizer {
    virtual std::vector<int> Encode(absl::string_view text) = 0;
    virtual std::string Decode(absl::Span<const int> tokens) = 0;
    virtual int VocabSize() = 0;
};
```

---

## Constrained Decoding

구조화된 출력(JSON, 함수 호출 등)을 강제하는 디코딩 기법.

**방식:**
- FST (Finite State Transducer) 제약
- LLGuidance 통합 (복잡한 문법)
- 토큰 생성 시 유효한 토큰만 허용

**위치:** `runtime/components/constrained_decoding/`

**사용 예:**
```python
conversation = engine.create_conversation(
    tools=[...],
    enable_constrained_decoding=True,  # 함수 호출 스키마 강제
)
```

---

## Function Calling 상세

### Python API

```python
from litert_lm import Tool, ToolEventHandler

# 도구 정의 (함수 데코레이터 방식)
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

# 이벤트 핸들러 (도구 호출 승인/거부)
class MyHandler(ToolEventHandler):
    def on_tool_call(self, tool_name, args):
        print(f"Calling {tool_name} with {args}")
        return True  # 승인

    def on_tool_result(self, tool_name, result):
        print(f"Result: {result}")

# 대화에 도구 연결
conversation = engine.create_conversation(
    tools=[search_web],
    tool_event_handler=MyHandler(),
)
```

### 지원 모델별 출력 형식
- **Gemma 4**: JSON 기반 함수 호출
- **FunctionGemma**: Python 스타일 호출
- **Qwen 3/2.5**: XML 스타일 호출

### 내부 흐름
1. 도구 스키마를 시스템 프롬프트에 주입
2. 모델이 도구 호출 생성 (constrained decoding 활용)
3. ANTLR4 파서로 호출 구문 분석
4. 도구 실행 → 결과를 모델에 피드백
5. 최종 응답 생성

---

## LoRA 지원

Low-Rank Adaptation을 통한 모델 파인튜닝 적용.

```python
engine = litert_lm.Engine(
    model_path="base_model.litertlm",
    lora_path="adapter.bin",      # LoRA 어댑터 파일
    lora_rank=8,                  # LoRA 랭크
)
```

**구현:** `runtime/components/lora.*`

---

## Speculative Decoding

작은 모델로 후보 토큰을 먼저 생성하고, 큰 모델로 검증하여 생성 속도를 향상.

```python
engine = litert_lm.Engine(
    model_path="model.litertlm",
    enable_speculative_decoding=True,
)
```

---

## Proto Definitions

### engine.proto
- `EngineParams`: 엔진 설정 (모델 경로, 백엔드, 토큰 수)

### llm_model_type.proto
- `GenericModel`, `Gemma3N`, `Gemma3`, `Gemma4`, `FunctionGemma`, `Qwen3`, `Qwen2p5`

### sampler_params.proto
- `SamplerParams`: temperature, top_k, top_p, type (Greedy/TopK/TopP)

### llm_metadata.proto
- 모델 메타데이터 (레이어 수, 헤드 수, vocab 크기 등)

### token.proto
- 토큰 정의 (id, text, logprob)

**위치:** `runtime/proto/`

---

## .litertlm 파일 포맷

### 구조
```
[FlatBuffers Header] [Section 1] [Section 2] ... [Section N]
```

### 헤더 스키마 (litertlm_header_schema.fbs)
```flatbuffers
table LiteRtLmHeader {
  sections: [Section];
}

table Section {
  type: SectionType;
  offset: uint64;
  size: uint64;
}

enum SectionType : byte {
  TFLiteModel,
  SP_Tokenizer,
  HF_Tokenizer_Zlib,
  LlmMetadata,
  // ...
}
```

### 특징
- 16KB 블록 정렬 (효율적 메모리 매핑)
- 섹션별 독립 접근 가능
- Zlib 압축 지원 (토크나이저 등)

### 읽기/쓰기
```cpp
// 읽기
auto reader = LiteRtLmRead("model.litertlm");
auto tflite_model = reader->GetSection(SectionType::TFLiteModel);
auto tokenizer = reader->GetSection(SectionType::HF_Tokenizer_Zlib);

// 쓰기 (내보내기)
LiteRtLmExport exporter;
exporter.AddSection(SectionType::TFLiteModel, tflite_data);
exporter.AddSection(SectionType::HF_Tokenizer_Zlib, tokenizer_data);
exporter.Write("output.litertlm");
```

**참조:** `schema/core/`

---

## 주요 파일 경로 매핑

### 핵심 런타임
| 파일 | 설명 |
|------|------|
| `runtime/core/engine_impl.cc` | 엔진 초기화 |
| `runtime/core/session_basic.cc` | 기본 세션 (prefill/decode) |
| `runtime/core/session_advanced.cc` | 고급 기능 (LoRA 등) |
| `runtime/core/tasks.cc` | 비동기 태스크 |
| `runtime/engine/engine.h` | Engine 인터페이스 |
| `runtime/engine/engine_settings.cc` | 엔진 설정 |

### 컴포넌트
| 파일 | 설명 |
|------|------|
| `runtime/components/tokenizer.h` | 토크나이저 인터페이스 |
| `runtime/components/huggingface_tokenizer.cc` | HF 토크나이저 |
| `runtime/components/prompt_template.cc` | Jinja2 프롬프트 |
| `runtime/components/lora.*` | LoRA 어댑터 |
| `runtime/components/constrained_decoding/` | 제약 디코딩 |

### Executor
| 파일 | 설명 |
|------|------|
| `runtime/executor/llm_executor_settings.h` | LLM 실행기 설정 |
| `runtime/executor/llm_executor_base.h` | 실행기 인터페이스 |
| `runtime/executor/litert_compiled_model_executor.cc` | LiteRT 통합 |
| `runtime/executor/vision_executor.h` | 비전 처리 |
| `runtime/executor/audio_executor.h` | 오디오 처리 |

### 대화
| 파일 | 설명 |
|------|------|
| `runtime/conversation/conversation.h` | 대화 인터페이스 |
| `runtime/conversation/io_types.h` | I/O 타입 |
| `runtime/conversation/model_data_processor/` | 모델별 프로세서 |

### 바인딩
| 파일 | 설명 |
|------|------|
| `python/litert_lm/interfaces.py` | Python ABC |
| `python/litert_lm/litert_lm.cc` | C++ → Python 바인딩 |
| `python/litert_lm/tools.py` | Function calling API |
| `kotlin/.../Engine.kt` | Kotlin 엔진 |
| `c/engine.h` | C API (FFI/JNI) |

### 스키마
| 파일 | 설명 |
|------|------|
| `schema/core/litertlm_header_schema.fbs` | 파일 포맷 |
| `schema/core/litertlm_read.cc` | 파일 읽기 |
| `schema/core/litertlm_export.cc` | 파일 내보내기 |
