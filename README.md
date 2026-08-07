# vibe-coding-tools

개인 Claude Code 플러그인 마켓플레이스 — AI 개발 워크플로우 자동화 도구 모음

## 마켓플레이스 추가

```shell
/plugin marketplace add starmkk/my-marketplace
```

## 플러그인 목록

| 플러그인 | 버전 | 구성 | 한 줄 설명 |
|---|---|---|---|
| `dev-helper-plugin` | 1.0.4 | 스킬 3종 | git 커밋 자동화 + PyTorch 프로젝트 하네스 + 세션 인계 문서 |
| `on-device-ai-plugin` | 1.1.8 | 스킬 7종 + 에이전트 1종 | 온디바이스 AI 모델 개발 레퍼런스 |
| `kws-speech-plugin` | 1.0.2 | 스킬 3종 | KWS 학습용 한국어 합성 데이터 파이프라인 |
| `code-quality-plugin` | 1.0.0 | 스킬 3종 + 에이전트 1종 + 훅 1종 | 6원칙 코드 리뷰 + C++/lint 컨벤션 + Serena 우선 검색 |
| `research-plugin` | 1.0.0 | 에이전트 3종 | 논문 문헌·특허 선행기술·레퍼런스 구현 조사 |

---

## dev-helper-plugin

개발 워크플로우 자동화 스킬 3종을 제공합니다.

### 설치

```shell
/plugin install dev-helper-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 한 줄 설명 |
|---|---|
| `github-commit` | Conventional Commits + emoji 형식의 한국어 커밋 자동화 |
| `pytorch-harness` | Config-Driven + Factory Pattern 기반 PyTorch 프로젝트 하네스 스캐폴딩 |
| `project-handoff` | 토픽별 자기완결 세션 인계(handoff) 문서 작성 — cross-repo / Claude Design 시안 변형 지원 |

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

### project-handoff

세션·마일스톤 작업을 다른 conversation / `/clear` 이후 / 다른 작업자에게 인계하기 위한 **토픽별 자기완결 handoff 문서**를 작성합니다. `docs/superpowers/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` 파일 1개가 산출물이며, next-turn Claude가 이 파일만 읽고 즉시 작업을 이어갈 수 있어야 함이 설계 기준입니다.

> 구 `resume-handoff` / `enhanced-handoff` 대체 — `RESUME.md` 단일 누적 방식(1164 라인/214KB로 비대화)은 폐기하고, 토픽별 파일이 SoT입니다. 오래된 handoff는 그 자리에 남아 timeline archive 역할을 합니다.

**3가지 변형 (발화·repo 상태로 self-detect):**

| 변형 | 트리거 | 추가 산출물 |
|---|---|---|
| 기본 (session) | "마일스톤 PASS", "진행상황 정리", "다음 세션 인계", "`/clear` 전에 정리" | — |
| cross-repo | "cross-repo", "sibling repo 인계", "여러 repo 걸친 변경", "includeBuild", "vendor 갱신" | multi-repo 스냅샷 표 |
| design-mockup | "시안 도착", "Claude Design", "`.tar.gz` mockup", "inventory 갱신" | `design-mockups/inventory.md` 1행 갱신 |

**표준 골격 (필수 섹션):**

| 섹션 | 핵심 |
|---|---|
| 헤더 | 작성일 / branch / "이 문서만 읽고 진입 가능" 선언 / 진입 순서 / SDD ledger cross-link |
| §1 현재 상태 스냅샷 | branch / HEAD / commit 범위 / 빌드 상태 / plan·spec·architect refs |
| §2 완료 작업 | 커밋·검증됨 — "건드리지 말 것" commit 표 + 근본원인 |
| §5 다음 작업 ★ | 우선순위 순, 각 항목의 왜 / 어디(파일:라인) / 주의 — next-turn의 진입점 |
| §6 빌드·실행 환경 | 매번 붙이는 env prefix + gradle/adb 명령 |
| §8 참조 인덱스 | spec / plan / architect-review / ledger 경로 |
| §9 재개 절차 | next-turn이 그대로 실행 가능한 번호 스텝 |

선택 섹션: §0 한 줄 요약, §3 핵심 설계 결정(동결), §4 핵심 파일 인덱스, §7 함정(신규 발견).

**포함 스크립트:**
```shell
# git 상태 캡처 → §1 스냅샷 표 markdown 출력 (인자로 sibling repo 추가 시 multi-repo 표)
bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/capture-repo-state.sh" \
    /path/to/sibling-repo-1 /path/to/sibling-repo-2

# self-review — 문서의 HEAD anchor 가 실제 git log 와 일치하는지 검증 (불일치 시 exit 1)
bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/verify-handoff-integrity.sh" \
    docs/superpowers/handoffs/2026-07-22-my-topic-handoff.md
```

**결합 스킬:** `dev-helper-plugin:github-commit` (작성 후 커밋 — 직접 `git commit` 금지), `superpowers:verification-before-completion` (커밋 직전 실측 검증), `superpowers:systematic-debugging` (§7 함정 행), `superpowers:writing-plans` (§5가 신규 마일스톤일 때)

**사용하지 말아야 할 때:** 단순 typo/1~2줄 패치, 작업 진행 중(TDD step 1~4), `RESUME.md` 복원 요청

---

## on-device-ai-plugin

온디바이스 AI 모델 개발을 위한 레퍼런스 스킬 7종과 에이전트 1종을 제공합니다. 모델 사용법(Gemma 4, Qwen 2.5/3.x)과 추론 프레임워크(LiteRT, LiteRT-LM, TensorFlow/TFLite, MNN), 호스팅 앱(AI Edge Gallery)을 한 묶음으로 다룹니다.

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
| `tensorflow` | 추론 엔진 | TensorFlow v2.21 / TFLite C/C++/Python API 및 Delegate 시스템 레퍼런스 |
| `mnn` | 추론 엔진 | Alibaba MNN 모바일 경량 딥러닝 프레임워크 |
| `gallery` | 호스팅 앱 | Google AI Edge Gallery — 온디바이스 LLM Android/iOS 앱 |

### 에이전트

| 에이전트 | 모델 | 한 줄 설명 |
|---|---|---|
| `mnn-source-inspector` | opus | MNN C++ 소스트리를 직접 탐색해 내부 아키텍처·API 규격·커널 선택 로직을 확정 |

`precision`/`memory`/`backend_type` 등 MNN 런타임 동작이나 llmexport 옵션의 의미가 불확실할 때, MNN 관련 오동작을 진단할 때 호출합니다. 추측 대신 소스로 확정하는 것이 목적입니다.

누적 조사 결과는 `~/.claude/agent-memory/mnn-source-inspector/` 에 사용자 전역으로 저장되며 MNN 을 쓰는 저장소들이 공유합니다.

---

### gemma4

Google Gemma 4 멀티모달 모델 공식 사용법 레퍼런스. 모델 로드/추론/파인튜닝, `apply_chat_template` 입력 구성, 오디오 ASR·이미지·비디오 멀티모달 태스크 구현, Thinking 모드·Function Calling, vLLM/llama.cpp/MLX 서빙을 다룹니다.

### 모델 관리 (~/.claude/repo)

모델이 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/gemma-4-<variant>`에 자동 다운로드합니다.

**모델 다운로드:**
```shell
huggingface-cli download google/gemma-4-E2B-it --local-dir ~/.claude/repo/gemma-4-E2B-it
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
| Gemma 4 12B | 11.95B (Unified, encoder-free) | 256K | O |
| Gemma 4 26B A4B | 4B activated / 26B total (MoE) | 256K | X |
| Gemma 4 31B | 31B dense | 256K | X |

**트리거 표현:**
- "gemma4", "gemma 4", "E2B", "E4B", "12B", "26B", "31B"
- "apply_chat_template", "멀티모달", "ASR", "transcribe"
- "thinking mode", "function calling"
- "llama.cpp", "MLX", "온디바이스 추론"

**관련 스킬:** `litert-lm` (온디바이스 실행)

---

### qwen

Alibaba Cloud Qwen 2.5/3.x 멀티모달 모델 개발 레퍼런스. 텍스트/이미지/오디오/비디오 입력 + 자연스러운 음성 합성 출력을 단일 end-to-end 모델로 처리합니다. Transformers/vLLM/MNN 백엔드, 양자화(GPTQ-Int4/AWQ/FP16), voice chatting, 모바일/엣지 배포를 다룹니다.

**지원 모델 라인업:**

| 계열 | 모델 | 구분 | 비고 |
|------|------|------|------|
| Qwen2.5-Omni | 3B / 7B | dense | 멀티모달 + 음성(Chelsie/Ethan) |
| Qwen3 (텍스트) | 0.6B~32B / 30B-A3B / 235B-A22B | dense + MoE | thinking·non-thinking 듀얼 모드, 2507 변형은 256K(최대 1M) |
| Qwen3-Omni | 30B-A3B (Instruct/Thinking/Captioner) | MoE | 멀티모달 + 음성, voice에 Aiden 추가, 텍스트 119/음성이해 19/음성생성 10개 언어 |

### 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/Qwen@<version>`에 자동 다운로드합니다.

**환경 설치:**
```shell
bash skills/qwen/scripts/install.sh
```

**트리거 표현:**
- "Qwen2.5-Omni", "qwen omni", "Qwen 3", "Qwen 2.5", "Qwen3-Omni"
- "voice chatting", "speech synthesis", "실시간 음성 응답"
- "GPTQ-Int4", "AWQ", "FP16 양자화"
- "Chelsie voice", "Ethan voice", "Aiden voice"
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

### tensorflow

TensorFlow v2.21.0-rc0 및 TFLite 핵심 API 레퍼런스. TFLite C/C++/Python API, Delegate(XNNPACK/GPU/CoreML/NNAPI) 시스템, SavedModel → .tflite 변환, SignatureRunner/AsyncRunner, 프로파일링·벤치마크를 다룹니다.

**트리거 표현:**
- "tensorflow", "tflite", "TensorFlow Lite"
- "delegate", "XNNPACK", "CoreML", "NNAPI"
- "quantization", "interpreter", "converter"
- "SavedModel → .tflite 변환"

**관련 스킬:** `litert` (LiteRT/TFLite 온디바이스 추론)

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

### 소스 코드 관리 (~/.claude/repo)

MeloTTS 소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/MeloTTS@<version>`에 자동 다운로드합니다. venv는 `~/.claude/venvs/melotts`에 생성됩니다.

**환경 설치:**
```shell
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

### 소스 코드 관리 (~/.claude/repo)

OpenVoice 소스코드가 필요한 작업이 생기면 사용자에게 먼저 확인합니다. 없다면 `~/.claude/repo/OpenVoice@<version>`에 자동 다운로드합니다. 체크포인트는 `checkpoints_v2/`, venv는 `~/.claude/venvs/openvoice`에 생성됩니다.

**환경 설치:**
```shell
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

## 환경변수 전체 목록

각 스킬이 요구하는 환경변수를 한눈에 정리합니다.

> **참고:** 모든 소스코드와 모델은 환경변수 대신 `~/.claude/repo/` 방식으로 관리됩니다.
> Claude Code에게 소스나 모델이 필요하다고 하면 자동으로 다운로드해줍니다.
> 추가로 설정해야 할 환경변수는 없습니다.

| 경로 | 스킬 | 설명 |
|---|---|---|
| `~/.claude/repo/gemma-4-<variant>` | `gemma4` | Gemma 4 모델 (HuggingFace) |
| `~/.claude/repo/MeloTTS@<version>` | `melotts-kws` | MeloTTS 소스 |
| `~/.claude/repo/OpenVoice@<version>` | `openvoice-v2-kws` | OpenVoice V2 소스 + 체크포인트 |
| `~/.claude/repo/wekws@<version>` | `wekws` | wekws 소스 |
| `~/.claude/repo/MNN@<version>` | `mnn` | MNN 소스 |
| `~/.claude/repo/LiteRT@<version>` | `litert` | LiteRT 소스 |
| `~/.claude/repo/LiteRT-LM@<version>` | `litert-lm` | LiteRT-LM 소스 |
| `~/.claude/repo/gallery@<version>` | `gallery` | AI Edge Gallery 소스 |
| `~/.claude/venvs/melotts` | `melotts-kws` | MeloTTS Python venv |
| `~/.claude/venvs/openvoice` | `openvoice-v2-kws` | OpenVoice Python venv |

---

## code-quality-plugin

코드 구조 품질을 지키는 에이전트 1종·스킬 3종·훅 1종을 제공합니다. 작성 전 설계 협의와 작성 후 구조 리뷰를 한 묶음으로 다룹니다.

### 설치

```shell
/plugin install code-quality-plugin@vibe-coding-tools
```

### 구성 한눈에 보기

| 구성요소 | 종류 | 한 줄 설명 |
|---|---|---|
| `strategic-code-reviewer` | 에이전트 | DRY·KISS·SRP·YAGNI·SoC·Naming 6원칙으로 배치·분해·중복·복잡도·네이밍을 판단 |
| `strategic-code-reviewer` | 스킬 | 6원칙 판정 기준, 오탐 필터, 우선순위 등급, 보고 형식 |
| `cpp-convention` | 스킬 | C++17 동시성 패턴, NDK r25 전제, include 순서, `compile_commands.json` |
| `lint-test-policy` | 스킬 | 언어별 lint 도구, 테스트 케이스 요건, 세션 연속성 절차 |
| serena-first | 훅 | 재귀 `grep`/`rg` 실행 시 Serena 심볼 검색 우선 사용을 경고 (`PreToolUse`) |

### 사용 흐름

```
[새 함수·클래스·모듈을 만들려 함]
        │
        ▼
 strategic-code-reviewer (설계 협의 모드)
   ① 이미 있는가  ② 정말 필요한가(YAGNI)
   ③ 어디에 두는가(SoC)  ④ 어떻게 쪼개는가(SRP)
        │
        ▼
     [구현]  ←─ cpp-convention / lint-test-policy 참조
        │
        ▼
 strategic-code-reviewer (구현 리뷰 모드)
   6원칙 스캔 → 오탐 제거 → 우선순위 부여
        │
        ▼
   [lint · test 검증]
```

- 에이전트는 소스를 직접 수정하지 않습니다. 판단만 돌려주며 구현·수정은 메인 세션에서 합니다.
- 버그·보안 취약점 탐지는 이 플러그인의 목적이 아닙니다. `/code-review`·`/security-review` 를 씁니다.
- `cpp-convention`·`lint-test-policy` 는 전역 `~/.claude/CLAUDE.md` 의 상세판입니다. CLAUDE.md 에는 핵심 규약만 두고 상세는 이 스킬을 진실 원천으로 삼아 내용이 어긋나는 것을 막습니다.

### serena-first 훅

`grep -r` / `grep -R` / `grep --include` / `rg` 실행을 감지해 Serena 심볼 검색을 먼저 검토했는지 묻습니다. **차단하지 않고 경고만** 합니다 — 정의 찾기는 `find_symbol`, 참조 추적은 `find_referencing_symbols`(grep 으로 대체 불가), 파일 구조는 `get_symbols_overview` 가 정확합니다.

serena 인덱스 밖(외부 저장소, `site-packages`)이거나 비코드 파일(로그·JSON·바이너리)이면 grep 이 정당합니다. 해당하면 이유를 한 줄 밝히고 진행하면 됩니다.

---

## research-plugin

근거 확보가 목적인 조사 전문 에이전트 3종을 제공합니다. 세 에이전트 모두 **없는 근거를 만들어내지 않는 것**을 최우선 규율로 삼으며, 확인한 것과 미확인을 구분해 보고합니다.

### 설치

```shell
/plugin install research-plugin@vibe-coding-tools
```

### 에이전트 한눈에 보기

| 에이전트 | 대상 | 한 줄 설명 |
|---|---|---|
| `quantization-literature-surveyor` | 논문 | 양자화·모델 압축 문헌을 원문까지 열어 직접 인용문을 확보하고 `[인용확정]`/`[미검증]` 을 구분 표기 |
| `patent-prior-art-researcher` | 특허 | 특허 DB 를 검색해 문헌번호·출원인·청구범위를 확인하고 발명 후보별 저촉 위험을 판정 |
| `reference-impl-comparator` | 외부 구현 | llama.cpp·transformers·ggml 등 레퍼런스 소스를 읽어 우리 구현과 대조하고 이식 힌트를 추출 |

### 선택 기준

- 논문 근거가 필요하면 → `quantization-literature-surveyor`
- 직무발명 신고서·출원 준비라면 → `patent-prior-art-researcher`
- "llama.cpp 는 어떻게 하는지" 가 궁금하면 → `reference-impl-comparator`
- MNN **내부** 구조 조사는 이 플러그인이 아니라 `on-device-ai-plugin` 의 `mnn-source-inspector` 를 씁니다

세 에이전트 모두 보고 시 `SendMessage` 로 보고서 전문을 전달합니다. 백그라운드 실행 시 평문 출력은 호출자에게 전달되지 않기 때문입니다.

---

## 마켓플레이스 업데이트

```shell
/plugin marketplace update vibe-coding-tools
```
