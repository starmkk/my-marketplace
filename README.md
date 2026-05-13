# vibe-coding-tools

개인 Claude Code 플러그인 마켓플레이스 — 개발 워크플로우 자동화 도구 모음

## 마켓플레이스 추가

```shell
/plugin marketplace add starmkk/my-marketplace
```

## 플러그인 설치

```shell
/plugin install dev-helper-plugin@vibe-coding-tools
```

---

## 플러그인 목록

### dev-helper-plugin

개발 워크플로우 자동화 스킬 2종을 제공합니다.

#### github-commit

현재 코드 변경사항을 검토하고 Conventional Commits + emoji 형식의 한국어 커밋 메시지로 git에 커밋합니다.

**트리거 표현:**
- "커밋해줘", "commit", "변경사항 저장", "git commit"

**사용:**
```shell
/dev-helper-plugin:github-commit
```

**커밋 형식:**
| 타입 | 이모지 | 설명 |
|------|--------|------|
| feat | ✨ | 새로운 기능 추가 |
| fix | 🐛 | 버그 수정 |
| refactor | ♻️ | 코드 리팩토링 |
| docs | 📚 | 문서 업데이트 |
| chore | 🔧 | 빌드/설정 변경 |
| style | 🎨 | 코드 포맷팅 |
| perf | 🚀 | 성능 개선 |
| test | ✅ | 테스트 추가/수정 |

---

#### save-docs

현재 세션 내용을 검토해 마크다운 문서로 정리하고 저장합니다. 개발 작업 세션과 질문·리뷰 세션을 구분해 단일 파일로 저장합니다.

**트리거 표현:**
- "문서 저장", "save docs", "세션 정리", "이 대화 저장", "기록해줘"

**사용:**
```shell
/dev-helper-plugin:save-docs
```

**저장 경로:**
- 기본값: `~/Documents/claude/docs/`
- 커스텀: 셸 프로파일에 `export CLAUDE_DOCS_DIR=/원하는/경로` 추가

**파일명 규칙:** `YYYYMMDD_<topic>.md`

---

### on-device-ai-plugin

온디바이스 AI 모델 개발을 위한 레퍼런스 스킬 7종을 제공합니다. 모델 사용법(Gemma 4, Qwen2.5-Omni)과 추론 프레임워크(LiteRT, LiteRT-LM, MNN), 호스팅 앱(AI Edge Gallery), 합성 데이터 검증(Gemma 4 ASR Round-Trip QA)을 한 묶음으로 다룹니다.

**설치:**
```shell
/plugin install on-device-ai-plugin@vibe-coding-tools
```

**스킬 한눈에 보기:**

| 스킬 | 카테고리 | 한 줄 설명 |
|---|---|---|
| `gemma4` | 모델 | Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스 |
| `qwen25-omni` | 모델 | Alibaba Cloud Qwen2.5-Omni 멀티모달 (텍스트/이미지/오디오/비디오 + 음성 합성) |
| `litert` | 추론 엔진 | Google LiteRT (구 TensorFlow Lite) 온디바이스 ML 추론 |
| `litert-lm` | 추론 엔진 | Google LiteRT-LM 온디바이스 LLM 추론 |
| `mnn` | 추론 엔진 | Alibaba MNN 모바일 경량 딥러닝 프레임워크 |
| `gallery` | 호스팅 앱 | Google AI Edge Gallery — 온디바이스 LLM Android/iOS 앱 |
| `gemma4-asr-qa` | 데이터 QA | Gemma 4 ASR로 합성 wav를 round-trip QA해 품질 필터링 |

---

#### gemma4

Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스. 모델 로드/추론/파인튜닝, `apply_chat_template` 입력 구성, 오디오 ASR·이미지·비디오 멀티모달 태스크 구현, Thinking 모드·Function Calling, vLLM/llama.cpp/MLX 서빙을 다룹니다.

**환경변수 (선택):**
- `GEMMA4_MODEL_PATH` — Gemma 4 모델 디렉토리 절대경로 (`gemma4-asr-qa`와 공유)

**트리거 표현:**
- "gemma4", "gemma 4", "E2B", "E4B", "26B", "31B"
- "apply_chat_template", "멀티모달", "ASR", "transcribe"
- "thinking mode", "function calling"
- "llama.cpp", "MLX", "온디바이스 추론"

**지원 모델:**

| 모델 | 유효 파라미터 | 컨텍스트 | 오디오 지원 |
|------|-------------|---------|-----------|
| Gemma 4 E2B | 2.3B (5.1B with embed) | 128K | O |
| Gemma 4 E4B | 4.5B (8B with embed) | 128K | O |
| Gemma 4 26B A4B | 4B activated / 26B total (MoE) | 256K | X |
| Gemma 4 31B | 31B dense | 256K | X |

---

#### qwen25-omni

Alibaba Cloud Qwen2.5-Omni 멀티모달 모델 개발 레퍼런스. 텍스트/이미지/오디오/비디오 입력 + 자연스러운 음성 합성 출력을 단일 end-to-end 모델로 처리합니다. Transformers/vLLM/MNN 백엔드, 양자화(GPTQ-Int4/AWQ/FP16), voice chatting, 모바일/엣지 배포를 다룹니다.

**환경변수 (스크립트 실행 시 필수):**
- `QWEN25_OMNI_MODEL_PATH` — Qwen2.5-Omni 로컬 모델 디렉토리 절대경로

미설정 시 모든 스크립트가 친절한 안내 메시지와 함께 즉시 중단됩니다. 등록 방법:

```shell
echo 'export QWEN25_OMNI_MODEL_PATH=/absolute/path/to/Qwen2.5-Omni-7B' >> ~/.zshrc
source ~/.zshrc
```

**트리거 표현:**
- "Qwen2.5-Omni", "qwen omni"
- "voice chatting", "speech synthesis", "실시간 음성 응답"
- "GPTQ-Int4", "AWQ", "FP16 양자화"
- "Chelsie voice", "Ethan voice"
- "모바일/엣지 배포", "MNN deployment"

---

#### litert

Google LiteRT(구 TensorFlow Lite) 온디바이스 ML 추론 프레임워크 레퍼런스. `.tflite` 모델 로딩/컴파일/실행, `CompiledModel`/`Environment`/`TensorBuffer` API, GPU/NPU delegate, dispatch API, CMake/Bazel 빌드를 다룹니다.

**환경변수 (선택):**
- `LITERT_SOURCE_PATH` — LiteRT 소스코드 레포 로컬 클론 경로

**트리거 표현:**
- "litert", "tflite", "TensorFlow Lite"
- "on-device inference", "온디바이스 추론"
- "delegate", "dispatch", "accelerator", "XNNPACK"

---

#### litert-lm

Google LiteRT-LM 온디바이스 LLM 추론 프레임워크 레퍼런스. `.litertlm` 모델 로딩/실행, Engine/Conversation/Session API, Gemma·Qwen 등의 온디바이스 실행, function calling/tool use, 멀티모달(vision/audio) 추론을 다룹니다.

**환경변수 (선택):**
- `LITERT_LM_SOURCE_PATH` — LiteRT-LM 소스코드 레포 로컬 클론 경로

**트리거 표현:**
- "litert-lm", "litertlm"
- "on-device LLM", "Gemma inference", "Qwen on-device"
- "Engine API", "Conversation API", "Session API"
- "constrained decoding", "function calling"

---

#### mnn

Alibaba MNN(Mobile Neural Network) 경량 딥러닝 프레임워크 개발 레퍼런스. TensorFlow/Caffe/ONNX/PyTorch → MNN 변환, Android/iOS 통합, MNN-LLM 모바일 LLM 배포, FP16/Int8/Int4 양자화, CPU/GPU/NPU 백엔드 설정, MNN C++/Python API를 다룹니다.

**환경변수 (스크립트 실행 시 필수):**
- `MNN_SOURCE_PATH` — MNN 소스코드 레포 로컬 클론 경로

미설정 시 모든 스크립트가 친절한 안내 메시지와 함께 즉시 중단됩니다. 등록 방법:

```shell
echo 'export MNN_SOURCE_PATH=/path/to/MNN' >> ~/.zshrc
source ~/.zshrc
```

**트리거 표현:**
- "MNN", "Mobile Neural Network", "MNN-LLM"
- "model conversion to MNN", "TensorFlow/ONNX → MNN"
- "FP16/Int8/Int4 quantization", "양자화"
- "Android/iOS MNN 통합"

---

#### gallery

Google AI Edge Gallery — 온디바이스 LLM Android/iOS 레퍼런스 앱. 모델 다운로드/관리, LLM 채팅 UI, Agent Skills 시스템 확장, CustomTask 추가, `model_allowlist.json` 수정, Jetpack Compose UI 작업을 다룹니다. 추론 백엔드로 LiteRT-LM을 사용합니다.

**환경변수 (선택):**
- `GALLERY_SOURCE_PATH` — Google AI Edge Gallery 레포 로컬 클론 경로

**트리거 표현:**
- "gallery", "ai edge gallery", "google ai edge"
- "온디바이스 앱", "model download"
- "agent skills", "custom task", "model_allowlist.json"
- "llm chat ui", "Jetpack Compose"

---

#### gemma4-asr-qa

로컬 Gemma 4 E2B-it ASR로 MeloTTS/OpenVoice V2 합성 wav를 transcribe하고 원본 텍스트와 비교(round-trip QA)하여 품질이 떨어지는 데이터를 자동 필터링하는 스킬. CER/WER 임계값 기반 필터링과 wekws 호환 manifest 산출을 지원합니다.

**환경변수 (필수):**
- `GEMMA4_MODEL_PATH` — Gemma 4 E2B-it 모델 디렉토리 절대경로

미설정 시 모든 스크립트가 친절한 안내 메시지와 함께 즉시 중단됩니다. 등록 방법:

```shell
echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> ~/.zshrc
source ~/.zshrc
```

**트리거 표현:**
- "Gemma 4 ASR", "gemma asr", "gemma transcribe"
- "round-trip QA", "합성 품질 검증"
- "CER 계산", "WER 계산", "synthesis quality filtering"
- "합성 데이터 필터링"

---

## 업데이트

```shell
/plugin marketplace update vibe-coding-tools
```
