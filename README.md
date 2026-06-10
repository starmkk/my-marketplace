# vibe-coding-tools

개인 Claude Code 플러그인 마켓플레이스 — AI 개발 워크플로우 자동화 도구 모음

## 마켓플레이스 추가

```shell
/plugin marketplace add starmkk/my-marketplace
```

## 플러그인 목록

| 플러그인 | 버전 | 스킬 수 | 한 줄 설명 |
|---|---|---|---|
| `dev-helper-plugin` | 1.0.1 | 2종 | git 커밋 자동화 + 세션 문서 저장 |
| `on-device-ai-plugin` | 1.1.3 | 6종 | 온디바이스 AI 모델 개발 레퍼런스 |
| `kws-speech-plugin` | 1.0.0 | 3종 | KWS 학습용 한국어 합성 데이터 파이프라인 |
| `ai-dev-tools-plugin` | 1.0.0 | 3종 | PyTorch/TensorFlow/LLM-Wiki AI 개발 도구 |

---

## dev-helper-plugin

개발 워크플로우 자동화 스킬 2종을 제공합니다.

### 설치

```shell
/plugin install dev-helper-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 한 줄 설명 |
|---|---|
| `github-commit` | Conventional Commits + emoji 형식의 한국어 커밋 자동화 |
| `save-docs` | 현재 세션을 마크다운 문서로 분류·저장 |

---

### github-commit

현재 코드 변경사항을 검토하고 Conventional Commits + emoji 형식의 한국어 커밋 메시지로 git에 커밋합니다.

**사용:**
```shell
/dev-helper-plugin:github-commit
```

**트리거 표현:**
- "커밋해줘", "commit", "변경사항 저장", "git commit"

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

### save-docs

현재 세션 내용을 검토해 마크다운 문서로 정리하고 저장합니다. 개발 작업 세션과 질문·리뷰 세션을 구분해 단일 파일로 저장합니다.

**사용:**
```shell
/dev-helper-plugin:save-docs
```

**트리거 표현:**
- "문서 저장", "save docs", "세션 정리", "이 대화 저장", "기록해줘"

**저장 경로:**
- 기본값: `~/Documents/claude/docs/`
- 커스텀: 셸 프로파일에 `export CLAUDE_DOCS_DIR=/원하는/경로` 추가

**파일명 규칙:** `YYYYMMDD_<topic>.md`

---

## on-device-ai-plugin

온디바이스 AI 모델 개발을 위한 레퍼런스 스킬 6종을 제공합니다. 모델 사용법(Gemma 4, Qwen 2.5/3.x)과 추론 프레임워크(LiteRT, LiteRT-LM, MNN), 호스팅 앱(AI Edge Gallery)을 한 묶음으로 다룹니다.

### 설치

```shell
/plugin install on-device-ai-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 카테고리 | 한 줄 설명 |
|---|---|---|
| `gemma4` | 모델 | Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스 |
| `qwen` | 모델 | Alibaba Qwen 2.5/3.x 멀티모달 (텍스트/이미지/오디오/비디오 + 음성 합성) |
| `litert` | 추론 엔진 | Google LiteRT (구 TensorFlow Lite) 온디바이스 ML 추론 |
| `litert-lm` | 추론 엔진 | Google LiteRT-LM 온디바이스 LLM 추론 |
| `mnn` | 추론 엔진 | Alibaba MNN 모바일 경량 딥러닝 프레임워크 |
| `gallery` | 호스팅 앱 | Google AI Edge Gallery — 온디바이스 LLM Android/iOS 앱 |

---

### gemma4

Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스. 모델 로드/추론/파인튜닝, `apply_chat_template` 입력 구성, 오디오 ASR·이미지·비디오 멀티모달 태스크 구현, Thinking 모드·Function Calling, vLLM/llama.cpp/MLX 서빙을 다룹니다.

**환경변수:**

| 변수 | 필수 | 설명 |
|------|------|------|
| `GEMMA4_MODEL_PATH` | 선택 | Gemma 4 모델 디렉토리 절대경로 |

미설정 시에도 레퍼런스 스킬로 사용 가능합니다.

**모델 다운로드:**
```shell
pip install huggingface_hub
huggingface-cli download google/gemma-4-E2B-it --local-dir /path/to/gemma-4-E2B-it
```

**환경 설치:**
```shell
bash skills/gemma4/scripts/install.sh
```

**지원 모델:**

| 모델 | 유효 파라미터 | 컨텍스트 | 오디오 지원 |
|------|-------------|---------|-----------|
| Gemma 4 E2B | 2.3B (5.1B with embed) | 128K | O |
| Gemma 4 E4B | 4.5B (8B with embed) | 128K | O |
| Gemma 4 26B A4B | 4B activated / 26B total (MoE) | 256K | X |
| Gemma 4 31B | 31B dense | 256K | X |

**트리거 표현:**
- "gemma4", "gemma 4", "E2B", "E4B", "26B", "31B"
- "apply_chat_template", "멀티모달", "ASR", "transcribe"
- "thinking mode", "function calling"
- "llama.cpp", "MLX", "온디바이스 추론"

**관련 스킬:** `litert-lm` (온디바이스 실행)

---

### qwen

Alibaba Cloud Qwen 2.5/3.x 멀티모달 모델 개발 레퍼런스. 텍스트/이미지/오디오/비디오 입력 + 자연스러운 음성 합성 출력을 단일 end-to-end 모델로 처리합니다. Transformers/vLLM/MNN 백엔드, 양자화(GPTQ-Int4/AWQ/FP16), voice chatting, 모바일/엣지 배포를 다룹니다.

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/Qwen@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/qwen/scripts/install.sh
```

**트리거 표현:**
- "Qwen2.5-Omni", "qwen omni", "Qwen 3", "Qwen 2.5"
- "voice chatting", "speech synthesis", "실시간 음성 응답"
- "GPTQ-Int4", "AWQ", "FP16 양자화"
- "Chelsie voice", "Ethan voice"
- "모바일/엣지 배포", "MNN deployment"

**관련 스킬:** `mnn` (모바일 배포 백엔드), `gemma4` (다른 멀티모달 LLM 옵션)

---

### litert

Google LiteRT(구 TensorFlow Lite) 온디바이스 ML 추론 프레임워크 레퍼런스. `.tflite` 모델 로딩/컴파일/실행, `CompiledModel`/`Environment`/`TensorBuffer` API, GPU/NPU delegate, dispatch API, CMake/Bazel 빌드를 다룹니다.

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/LiteRT@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/litert/scripts/install.sh
```

**트리거 표현:**
- "litert", "tflite", "TensorFlow Lite"
- "on-device inference", "온디바이스 추론"
- "delegate", "dispatch", "accelerator", "XNNPACK"
- "CompiledModel", "Environment", "TensorBuffer"

**관련 스킬:** `litert-lm` (LLM 추론), `tensorflow` (SavedModel ↔ tflite 변환), `mnn` (대안 모바일 추론 프레임워크)

---

### litert-lm

Google LiteRT-LM 온디바이스 LLM 추론 프레임워크 레퍼런스. `.litertlm` 모델 로딩/실행, Engine/Conversation/Session API, Gemma·Qwen 등의 온디바이스 실행, function calling/tool use, 멀티모달(vision/audio) 추론을 다룹니다.

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/LiteRT-LM@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/litert-lm/scripts/install.sh
```

**트리거 표현:**
- "litert-lm", "litertlm"
- "on-device LLM", "Gemma inference", "Qwen on-device"
- "Engine API", "Conversation API", "Session API"
- "constrained decoding", "function calling"
- ".litertlm 모델 로딩/실행"

**관련 스킬:** `litert` (하위 추론 엔진), `gemma4` (대표 실행 모델), `gallery` (Android/iOS 호스팅 앱)

---

### mnn

Alibaba MNN(Mobile Neural Network) 경량 딥러닝 프레임워크 개발 레퍼런스. TensorFlow/Caffe/ONNX/PyTorch → MNN 변환, Android/iOS 통합, MNN-LLM 모바일 LLM 배포, FP16/Int8/Int4 양자화, CPU/GPU/NPU 백엔드 설정, MNN C++/Python API를 다룹니다.

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/MNN@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/mnn/scripts/install.sh
```

**스크립트 사용 예시:**
```shell
# 모델 변환 (ONNX → MNN)
python skills/mnn/scripts/convert_model.py --input model.onnx --output model.mnn \
  --mnn-source ~/.claude/repo/MNN@3.5.0

# LLM 모델 MNN 변환 및 내보내기
python skills/mnn/scripts/export_llm.py --model Qwen/Qwen2.5-7B \
  --mnn-source ~/.claude/repo/MNN@3.5.0

# Android 빌드
bash skills/mnn/scripts/build_android.sh --abi arm64-v8a --gpu \
  --mnn-source ~/.claude/repo/MNN@3.5.0
```

**트리거 표현:**
- "MNN", "Mobile Neural Network", "MNN-LLM"
- "model conversion to MNN", "TensorFlow/ONNX → MNN"
- "FP16/Int8/Int4 quantization", "양자화"
- "Android/iOS MNN 통합"

**관련 스킬:** `qwen` (Qwen 모바일 배포), `litert` (대안 온디바이스 추론 프레임워크)

---

### gallery

Google AI Edge Gallery — 온디바이스 LLM Android/iOS 레퍼런스 앱. 모델 다운로드/관리, LLM 채팅 UI, Agent Skills 시스템 확장, CustomTask 추가, `model_allowlist.json` 수정, Jetpack Compose UI 작업을 다룹니다. 추론 백엔드로 LiteRT-LM을 사용합니다.

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/gallery@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/gallery/scripts/install.sh
```

**트리거 표현:**
- "gallery", "ai edge gallery", "google ai edge"
- "온디바이스 앱", "model download"
- "agent skills", "custom task", "model_allowlist.json"
- "llm chat ui", "Jetpack Compose"

**관련 스킬:** `litert` (ML 추론 백엔드), `litert-lm` (LLM 실행 엔진)

---

## kws-speech-plugin

KWS 학습용 한국어 합성 데이터 생성 파이프라인 스킬 3종을 제공합니다. MeloTTS 단화자 합성부터 OpenVoice V2 다화자 클로닝, wekws E2E KWS 학습까지 한 묶음으로 다룹니다.

### 설치

```shell
/plugin install kws-speech-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 카테고리 | 한 줄 설명 |
|---|---|---|
| `melotts-kws` | 합성 | MeloTTS 한국어 단화자 합성 + speed/pitch augmentation + wekws manifest 생성 |
| `openvoice-v2-kws` | 합성 | OpenVoice V2 tone color cloning으로 다화자 한국어 합성 |
| `wekws` | 학습/추론 | WeKws E2E KWS 모델 학습·ONNX 변환·C++ 스트리밍 디코더 레퍼런스 |

### 전체 파이프라인 흐름

```
[텍스트 키워드 목록]
        │
        ▼
 melotts-kws (단화자 합성 + augmentation)
        │
        ├──────────────────────────────────┐
        ▼                                  ▼
 openvoice-v2-kws (다화자 cloning)   gemma4 ASR QA (품질 검증)
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
               wekws (KWS 모델 학습)
```

---

### melotts-kws

MeloTTS(MyShell.ai) 한국어 단화자 TTS로 KWS 학습/평가용 합성 음성 데이터를 대량 생성하고, speed/pitch/noise/RIR augmentation과 wekws 호환 manifest를 함께 만드는 스킬.

**환경변수:**

| 변수 | 필수 | 설명 |
|------|------|------|
| `MELOTTS_KWS_DIR` | **필수** | melotts-kws 스킬 디렉토리 절대경로 |
| `MELO_ENV_DIR` | 선택 | MeloTTS venv 위치 (기본: `~/Documents/work_2026/KWS/melotts_env`) |
| `MELO_SRC_DIR` | 선택 | MeloTTS 소스 클론 위치 (기본: `~/Documents/work_2026/KWS/MeloTTS`) |
| `PYTHON_BIN` | 선택 | Python 실행 파일 (기본: `python3.10`) |

**환경 설치:**
```shell
export MELOTTS_KWS_DIR=/path/to/kws-speech-plugin/skills/melotts-kws
bash skills/melotts-kws/scripts/install.sh
```

**스크립트 사용 예시:**
```shell
# 단일 문장 합성 (테스트/데모)
python skills/melotts-kws/scripts/synthesize.py \
    --text "오케이 케이티" --output ./out/test.wav

python skills/melotts-kws/scripts/synthesize.py \
    --text "헤이 케이티" --output ./out/h.wav --speed 1.2 --sample_rate 16000

# 키워드 리스트 대량 합성
python skills/melotts-kws/scripts/batch_synthesize.py \
    --keywords examples/keywords.txt \
    --out_dir ./synth_raw \
    --sample_rate 16000 \
    --speed 1.2

# speed/pitch/noise/RIR augmentation
python skills/melotts-kws/scripts/augment_audio.py \
    --in_dir ./synth_raw \
    --out_dir ./synth_aug \
    --config examples/augment_config.yaml

# wekws manifest 생성
python skills/melotts-kws/scripts/make_wekws_manifest.py \
    --in_dir ./synth_aug \
    --out_manifest ./train.list
```

**트리거 표현:**
- "MeloTTS", "melo tts", "한국어 TTS", "TTS 합성"
- "KWS 합성 데이터", "키워드 음성 생성", "wakeword 음성 합성"
- "wekws 학습 데이터 만들기", "키워드 데이터셋 합성"

**관련 스킬:** `openvoice-v2-kws` (다화자 확장), `wekws` (KWS 학습)

> **주의:** MeloTTS 한국어 모델은 단 1명의 화자(`speaker_ids['KR']`)만 지원합니다. 화자 다양성이 필요하면 `openvoice-v2-kws`를 함께 사용하세요.

---

### openvoice-v2-kws

OpenVoice V2(MyShell.ai) + MeloTTS-Korean을 결합해 AIHub 등 다화자 reference wav 풀에서 N가지 화자로 동일 키워드를 합성하는 스킬. MeloTTS 단화자 한계를 voice cloning으로 극복합니다.

**파이프라인 구조:**
```
[텍스트] ──MeloTTS-KR──▶ [base wav (단일 화자)]
                                │
[reference wav]──se_extractor─▶ [target speaker embedding]
                                │
                       OpenVoice ToneColorConverter
                                │
                                ▼
                        [cloned wav (다화자)]
```

**환경변수:**

| 변수 | 필수 | 설명 |
|------|------|------|
| `OPENVOICE_V2_KWS_DIR` | **필수** | openvoice-v2-kws 스킬 디렉토리 절대경로 |
| `OPENVOICE_ENV_DIR` | 선택 | OpenVoice venv 위치 (기본: `~/Documents/work_2026/KWS/openvoice_env`) |
| `OPENVOICE_SRC_DIR` | 선택 | OpenVoice 소스 클론 위치 (기본: `~/Documents/work_2026/KWS/OpenVoice`) |
| `OPENVOICE_CKPT_DIR` | 선택 | OpenVoice V2 체크포인트 위치 (기본: `$OPENVOICE_SRC_DIR/checkpoints_v2`) |
| `PYTHON_BIN` | 선택 | Python 실행 파일 (기본: `python3.9`) |

**환경 설치:**
```shell
export OPENVOICE_V2_KWS_DIR=/path/to/kws-speech-plugin/skills/openvoice-v2-kws
bash skills/openvoice-v2-kws/scripts/install.sh
```

**스크립트 사용 예시:**
```shell
# 단일 문장 + 단일 reference 화자로 voice cloning 합성
python skills/openvoice-v2-kws/scripts/clone_synthesize.py \
    --text "오케이 케이티" \
    --reference /path/to/ref.wav \
    --output ./out/cloned.wav \
    --speed 1.2

# 화자 풀 → speaker embedding 사전 추출
python skills/openvoice-v2-kws/scripts/prepare_speaker_pool.py \
    --pool_dir ~/datasets/kws_speaker_pool \
    --out_embeddings ./speaker_embeddings.pt

# 키워드 × 화자 풀 → 대량 multi-speaker 합성
python skills/openvoice-v2-kws/scripts/batch_multispk_synthesize.py \
    --keywords ../melotts-kws/examples/keywords.txt \
    --speaker_embeddings ./speaker_embeddings.pt \
    --out_dir ./synth_multispk \
    --speakers_per_keyword 20 \
    --speed 1.2 \
    --manifest ./synth_multispk/manifest.csv
```

**트리거 표현:**
- "OpenVoice", "openvoice v2", "tone color cloning"
- "voice cloning", "음성 복제", "화자 복제"
- "multi-speaker 한국어 합성", "다화자 KWS 데이터"

**관련 스킬:** `melotts-kws` (base wav 생성), `wekws` (KWS 학습)

---

### wekws

WeKws(wenet-e2e/wekws) Production First End-to-End KWS 툴킷 레퍼런스. MDTC/TCN/RNN 모델 학습, PyTorch → ONNX 변환, C++ 스트리밍 디코더 개발, Android/ARM 온디바이스 배포를 다룹니다.

**트리거 표현:**
- "wekws", "keyword spotting", "KWS", "wake word", "웨이크워드"
- "MDTC", "streaming decoder", "ONNX runtime"
- "on-device inference", "causal convolution"

**관련 스킬:** `melotts-kws` (학습 데이터 합성), `openvoice-v2-kws` (다화자 학습 데이터)

---

## ai-dev-tools-plugin

AI 개발을 위한 도구 레퍼런스 스킬 3종을 제공합니다. PyTorch 프로젝트 템플릿 생성기, TensorFlow/TFLite API 레퍼런스, LLM 기반 개인 지식베이스 패턴을 한 묶음으로 다룹니다.

### 설치

```shell
/plugin install ai-dev-tools-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 카테고리 | 한 줄 설명 |
|---|---|---|
| `pytorch-harness` | 템플릿 | Config-Driven + Factory Pattern 기반 PyTorch 프로젝트 하네스 스캐폴딩 |
| `tensorflow` | 레퍼런스 | TensorFlow v2.21 / TFLite C/C++/Python API 및 Delegate 시스템 레퍼런스 |
| `llm-wiki` | 지식 관리 | LLM이 마크다운 위키를 점진적으로 구축·유지하는 개인 지식베이스(PKB) 패턴 |

---

### pytorch-harness

새로운 PyTorch 프로젝트를 Config-Driven + Factory Pattern 기반의 5계층 하네스 구조로 스캐폴딩합니다. YAML 설정, Stage 테스트(stage1~4), 하드웨어별 프로파일링이 포함된 전체 프로젝트 템플릿을 생성합니다.

**생성 시 확인 항목:**
1. 프로젝트 이름 (예: `speech-recognition`)
2. 태스크 유형 (ASR, 이미지 분류, 객체 탐지, NLP, 멀티모달 등)
3. 베이스 모델 (예: `google/gemma-4-E2B-it`, `openai/whisper-large-v3`)
4. 데이터셋 (예: LibriSpeech, ImageNet, 커스텀)
5. 타깃 하드웨어 (Mac M4, RTX 3090, A100, 온디바이스 등)
6. 파인튜닝 방식 (LoRA, Full Fine-tuning, QLoRA)

**생성 구조 (5계층 하네스):**
```
<project>/
├── configs/           # YAML 하이퍼파라미터
├── src/
│   ├── models/        # 모델 팩토리
│   ├── data/          # 데이터로더 팩토리 + Preprocessor
│   ├── training/      # Trainer
│   ├── inference/     # Inferencer
│   └── evaluation/    # Evaluator
└── tests/             # stage1~4 단계별 테스트
```

**트리거 표현:**
- "pytorch 프로젝트 템플릿", "신규 프로젝트 생성", "하네스 프로젝트 만들어줘"
- "scaffold", "new project template"
- "Config-Driven", "Factory Pattern", "ExperimentConfig"

---

### tensorflow

TensorFlow v2.21.0-rc0 및 TFLite 핵심 API 레퍼런스. TFLite C/C++/Python API, Delegate(XNNPACK/GPU/CoreML/NNAPI) 시스템, SavedModel → .tflite 변환, SignatureRunner/AsyncRunner, 프로파일링·벤치마크를 다룹니다.

**트리거 표현:**
- "tensorflow", "tflite", "TensorFlow Lite"
- "delegate", "XNNPACK", "CoreML", "NNAPI"
- "quantization", "interpreter", "converter"
- "SavedModel → .tflite 변환"

**관련 스킬:** `litert` (LiteRT/TFLite 온디바이스 추론)

---

### llm-wiki

LLM이 마크다운 파일로 구성된 위키를 점진적으로 구축·유지하는 개인 지식베이스(PKB) 패턴. Andrej Karpathy의 LLM-Wiki 아이디어를 기반으로 Ingest / Query / Lint 세 가지 오퍼레이션을 구현합니다.

| 개념 | RAG 방식 | LLM-Wiki 방식 |
|------|----------|--------------|
| 지식 합성 | 질의할 때마다 재수행 | 소스 추가 시 한 번만 수행, 위키에 영구 저장 |
| 교차 참조 | 없음 | 위키 페이지 간 링크로 구성됨 |
| 모순 감지 | 없음 | ingestion 시 기존 위키와 비교해 플래그 |

**트리거 표현:**
- "llm wiki", "llm 위키", "개인 지식베이스", "PKB"
- "소스 문서를 위키에 추가", "ingest", "문서 처리"
- "Obsidian + LLM", "마크다운 위키 관리"

---

## 환경변수 전체 목록

각 스킬이 요구하는 환경변수를 한눈에 정리합니다.

> **참고:** `on-device-ai-plugin`의 추론 프레임워크/앱 소스(`mnn`, `litert`, `litert-lm`, `gallery`)는 환경변수 대신 `~/.claude/repo/<RepoName>@<version>` 방식으로 관리됩니다. Claude Code에게 "소스 다운로드해줘"라고 요청하면 자동으로 받아집니다.

| 변수명 | 필수 | 플러그인 / 스킬 | 설명 |
|---|---|---|---|
| `GEMMA4_MODEL_PATH` | 선택 | on-device-ai / `gemma4` | Gemma 4 모델 디렉토리 절대경로 |
| `MELOTTS_KWS_DIR` | ✅ | kws-speech / `melotts-kws` | melotts-kws 스킬 디렉토리 절대경로 |
| `OPENVOICE_V2_KWS_DIR` | ✅ | kws-speech / `openvoice-v2-kws` | openvoice-v2-kws 스킬 디렉토리 절대경로 |
| `MELO_ENV_DIR` | 선택 | kws-speech / `melotts-kws` | MeloTTS venv 위치 (기본: `~/Documents/work_2026/KWS/melotts_env`) |
| `MELO_SRC_DIR` | 선택 | kws-speech / `melotts-kws` | MeloTTS 소스 클론 위치 (기본: `~/Documents/work_2026/KWS/MeloTTS`) |
| `OPENVOICE_ENV_DIR` | 선택 | kws-speech / `openvoice-v2-kws` | OpenVoice venv 위치 (기본: `~/Documents/work_2026/KWS/openvoice_env`) |
| `OPENVOICE_SRC_DIR` | 선택 | kws-speech / `openvoice-v2-kws` | OpenVoice 소스 클론 위치 (기본: `~/Documents/work_2026/KWS/OpenVoice`) |
| `OPENVOICE_CKPT_DIR` | 선택 | kws-speech / `openvoice-v2-kws` | OpenVoice V2 체크포인트 위치 (기본: `$OPENVOICE_SRC_DIR/checkpoints_v2`) |
| `PYTHON_BIN` | 선택 | kws-speech / install.sh | Python 실행 파일 (melotts: `python3.10`, openvoice: `python3.9`) |
| `CLAUDE_DOCS_DIR` | 선택 | dev-helper / `save-docs` | 세션 문서 저장 경로 (기본: `~/Documents/claude/docs/`) |

### 전체 설정 예제

```shell
# ~/.zshrc 또는 ~/.bashrc에 추가 후 `source ~/.zshrc` 실행

# ── 필수 ──────────────────────────────────────────────────────────────────

# [kws-speech-plugin] melotts-kws
export MELOTTS_KWS_DIR=/path/to/kws-speech-plugin/skills/melotts-kws

# [kws-speech-plugin] openvoice-v2-kws
export OPENVOICE_V2_KWS_DIR=/path/to/kws-speech-plugin/skills/openvoice-v2-kws

# ── 선택 (기본값으로 충분하면 설정 불필요) ────────────────────────────────
# export GEMMA4_MODEL_PATH=/path/to/gemma-4-E2B-it
# export MELO_ENV_DIR=~/KWS/melotts_env
# export MELO_SRC_DIR=~/KWS/MeloTTS
# export OPENVOICE_ENV_DIR=~/KWS/openvoice_env
# export OPENVOICE_SRC_DIR=~/KWS/OpenVoice
# export OPENVOICE_CKPT_DIR=~/KWS/OpenVoice/checkpoints_v2
# export PYTHON_BIN=python3.10          # melotts-kws install.sh 전용
# export CLAUDE_DOCS_DIR=~/my-docs      # save-docs 문서 저장 경로
```

---

## 마켓플레이스 업데이트

```shell
/plugin marketplace update vibe-coding-tools
```
