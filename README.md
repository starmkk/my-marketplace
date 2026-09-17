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
| `code-quality-plugin` | 1.0.4 | 스킬 3종 + 에이전트 1종 + 훅 1종 | 6원칙 코드 리뷰 + C++/lint 컨벤션 + Serena 우선 검색 |
| `research-plugin` | 1.0.0 | 에이전트 3종 | 논문 문헌·특허 선행기술·레퍼런스 구현 조사 |
| `secure-coding-plugin` | 1.0.4 | 스킬 7종 + 에이전트 1종 | 한국 전자정부 SW 개발보안(시큐어코딩) 공식 가이드 레퍼런스 + OWASP MASVS·ASVS 국제표준 보완 |

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

## secure-coding-plugin

한국 전자정부 소프트웨어 개발보안(시큐어코딩) 공식 가이드 6종을 근거로 한 국내 기준 레퍼런스 스킬 5종에, OWASP 국제표준을 근거로 국내 기준의 공백을 보완하는 스킬 2종(모바일 — MASVS v2.1.0 / MASWE v1.0.0 / MASTG v2.0.0, 웹·API — ASVS 5.0.0)을 더한 스킬 7종과 시큐어코딩 리뷰 에이전트 1종을 제공합니다. 코드 진단/리뷰, 안전한 코드 작성, 검증 절차 대응에 사용합니다.

### 설치

```shell
/plugin install secure-coding-plugin@vibe-coding-tools
```

### 스킬 한눈에 보기

| 스킬 | 용도 | 근거 문서 |
|---|---|---|
| `secure-coding-kr` | 허브 — 보안약점 진단기준·진단절차, 오탐 판별 | 소프트웨어 보안약점 진단가이드(2021, 612p) |
| `secure-coding-java` | Java/Android 취약→안전 코드 패턴, 착시 조치 판별 | 시큐어코딩(Java) 교안 + Android-JAVA 시큐어 코딩 가이드(2판) |
| `secure-coding-c` | C/C++ 위험함수 매핑, 메모리·정수 안전성 | C 시큐어 코딩 가이드(3판, 222p) |
| `mobile-app-verify` | 전자정부 앱 소스코드 검증 절차·기준 | 모바일 전자정부서비스 앱 소스코드 검증 가이드라인(2021) |
| `crypto-policy-kr` | 암호 알고리즘·키 길이·유효기간 판정 | 암호 알고리즘 및 키 길이 이용 안내서(2018) |
| `owasp-masvs` | 국내 기준 공백 보완 — 모바일 앱 보안 국제표준 (제도 판정 근거 아님) | OWASP MASVS v2.1.0 / MASWE v1.0.0 / MASTG v2.0.0 |
| `owasp-asvs` | 국내 기준 공백 보완 — 웹·API 보안 검증 국제표준 (제도 판정 근거 아님) | OWASP ASVS 5.0.0 |

### 에이전트

| 에이전트 | 동작 모드 | 한 줄 설명 |
|---|---|---|
| `secure-coding-reviewer` | 진단 / 오탐 판정 / 조치 검토 | SW 보안약점 진단원 관점에서 코드를 진단하고 기준번호·CWE·원문 페이지를 병기해 보고서 기재 가능한 판정을 돌려줌 |

보안약점 진단, 정적분석 결과의 오탐/정탐 판정, 보완조치가 착시 조치(반려 대상)인지 확인이 필요할 때 호출합니다. 허브 `secure-coding-kr` 의 라우터 표에 따라 언어·맥락별 판정 기준 스킬을 로드해 쓰며, 코드를 대신 수정하지 않고 `SendMessage` 로 보고서 전문을 전달합니다. 오탐 판정이 판단 결정적 작업이므로 실행 모델은 `model: opus` 로 고정되어 있습니다(v1.0.2).

국내 기준번호·CWE 기재가 필요 없는 일반 보안 리뷰는 `/security-review`, 버그 탐지는 `/code-review`, 구조 품질 리뷰는 `code-quality-plugin` 의 `strategic-code-reviewer` 를 씁니다.

### 설계 특징 — 원문 근거와 현행 모범사례의 분리 병기

이 플러그인은 **원문 근거와 현행 모범사례를 분리해 병기**합니다. 각 항목은 `❌ 취약 코드 → ✅ 권장(현행 모범사례) → 📋 원문 근거(페이지)` 3단 구조입니다.

- **✅ 현행 권고**가 주된 권고입니다. 원문이 낡은 경우(예: 2011년 가이드의 `java.util.Random` 권고) 현행 표준(`SecureRandom`)을 제시하고 출처(NIST/OWASP/CERT)를 명시합니다.
- **📋 원문 근거**는 제도 대응용입니다. 전자정부 앱 검증 등 형식 절차에서는 "어느 문서 몇 페이지가 근거인가"를 정확히 인용해야 하며, 반대로 원문에 없는 항목을 그 문서 근거로 지적하면 안 되기 때문입니다.

또한 각 스킬에는 **원문 범위 밖 항목을 명시하는 절**이 별도로 있어, 원문에 없는 내용을 원문 근거로 과잉 지적하는 일을 방지합니다.

**핵심 수치:**
- 분석·설계단계 보안설계 기준 **20개**, 구현단계 보안약점 **49개** (2021 개정판 — 2019년 이전 판의 47개와 구분)
- C 가이드 3판 보안약점 **58개**, 위험함수→대체함수 매핑 **40건**
- 모바일 앱 검증기준 **51개** (소스코드 보안약점 26 + 기능 보안취약점 FV-1~FV-9 세부 25)
- 암호 권고 기본선 **보안강도 112비트 이상**, 장기(2030년 이후) 사용 시 **128비트 / RSA 3072비트 이상**
- OWASP 국제표준 보완 — MASVS 컨트롤 **24개** / MASWE 약점 **78개** / MASTG-TEST **292개** (CC BY-SA 4.0, 2026-09-17 조회)
- OWASP ASVS 5.0.0 — **17챕터 345요구사항**(L1 70 · L2 183 · L3 92), 그중 국내 설계단계 기준 대응이 전무한 **공백 7챕터 144요구사항** (CC BY-SA 4.0, 2026-09-17 조회)

---

### secure-coding-kr

행정안전부·KISA 「소프트웨어 보안약점 진단가이드」(2021.11 개정판, 총 612페이지) 기반의 허브 스킬. 분석·설계단계 보안설계 기준 20개와 구현단계 보안약점 49개(2019년 이전 판의 47개와 구분)의 진단기준·진단절차를 다루고, 작업 성격에 따라 나머지 4개 스킬로 분기합니다.

**주요 내용:**
- 스킬 라우터 — 언어/작업별로 어떤 스킬로 갈 것인가
- 분석·설계단계 기준 20개 / 구현단계 보안약점 49개 대분류별 개관 (CWE 매핑, 페이지 근거)
- 진단 절차 (착수 → 진단 → 보고 → 종료 / 1차 → 제거 → 2차 → 종료)
- 진단 수행 방법과 오탐(False Positive) 판별
- 원문 편집 오류 주의 사항

**트리거 표현:**
- "보안약점", "보안약점 진단", "소프트웨어 개발보안"
- "시큐어코딩", "진단가이드", "SW 보안약점 진단원"
- "설계단계 보안설계 기준", "구현단계 보안약점", "CWE"

**references:** `design-phase-20.md` (설계 기준 20개 전수), `weakness-49.md` (구현 보안약점 49개 전수)

**관련 스킬:** `secure-coding-java`, `secure-coding-c`, `mobile-app-verify`, `crypto-policy-kr`

---

### secure-coding-java

Java/Android 시큐어코딩 및 SW 보안약점 진단원 관점의 취약→안전 코드 패턴 레퍼런스. 「SW 보안약점 진단원 관점의 시큐어코딩 · Java」 교안(2026, 주력 근거)과 행안부/KISA 「Android-JAVA 시큐어 코딩 가이드(2판)」(2011, 원전)를 발행 시점을 구분해 병기합니다.

**주요 내용:**
- 진단 관점의 핵심 원칙 (Source → 흐름 → Sink, 시프트 레프트)
- 주제별 취약→안전 코드 패턴 (SQL 인젝션, XSS, 경로 조작, 접근통제 등)
- 착시 조치(반려 대상) 패턴 판별 — 이 스킬의 핵심
- Android 특화 항목 (2011 가이드 원전)
- 원문의 시대 지연 항목과 현행 대체 권고, Java 진단 체크리스트

**트리거 표현:**
- "Java 시큐어코딩", "Java 보안약점"
- "SQL 인젝션", "PreparedStatement", "XSS"
- "하드코딩 비밀번호", "SecureRandom"
- "Android 시큐어코딩", "android:exported", "sharedUserId"

**references:** `java-patterns.md` (교안 코드 스니펫 전수), `android-java-2011.md` (2011 가이드 원전)

**관련 스킬:** `secure-coding-kr` (진단기준 허브), `secure-coding-c`, `mobile-app-verify`, `crypto-policy-kr`

---

### secure-coding-c

행정안전부/KISA 「C 시큐어 코딩 가이드(3판)」 보안약점 58개(7개 유형) 기반 C/C++ 시큐어코딩 레퍼런스. 위험 함수 → 안전한 대체 함수 매핑 40건과 메모리·정수 안전성을 다루며, 원문 권고가 현행 기준에 미달하는 경우(`strcpy→strncpy` 등)를 구분해 현행 권장을 제시합니다.

**주요 내용:**
- 위험 함수 → 안전한 대체 함수 매핑 (40건, 현행 기준 함정 경고 포함)
- 유형별 보안약점 58개 개관
- 핵심 항목 심층 (❌ 취약 / ✅ 현행 권장 / 📋 원문 근거 3단 구조)
- 원문 범위 밖 — 현행 필수 점검 (ASan, 컴파일러 하드닝 등)
- C 진단 체크리스트 (grep 패턴)

**트리거 표현:**
- "C 시큐어코딩", "C 보안약점 58개"
- "버퍼 오버플로", "strcpy", "gets", "위험 함수"
- "use after free", "double free", "정수 오버플로"
- "race condition", "TOCTOU", "CERT C"

**references:** `weakness-58.md` (보안약점 58개 전수), `c-code-patterns.md` (코드 패턴 전수)

**관련 스킬:** `secure-coding-kr` (진단기준 허브), `secure-coding-java`, `crypto-policy-kr`

---

### mobile-app-verify

행정안전부·KISA 「모바일 전자정부서비스 앱 소스코드 검증 가이드라인」(2021.10) 기반, 전자정부 앱을 KISA에 소스코드 검증 신청할 때의 검증 절차·검증기준 레퍼런스. 검증기준 51개(소스코드 보안약점 26 + 기능 보안취약점 FV-1~FV-9 세부 25)를 다룹니다.

**주요 내용:**
- 검증 절차 흐름 (제출물 준비·신청 → 소스코드 검증 → 보완조치 확인 → 배포)
- 검증기준 51개 한눈에 보기
- 모바일 특화 점검 포인트 (앱 위변조, 루팅/탈옥 탐지, 난독화 등)
- 점검 체크리스트, 주의사항 / 문서 미기재 항목

**트리거 표현:**
- "모바일 전자정부", "전자정부 앱", "앱 소스코드 검증"
- "기능 보안취약점", "FV-", "소스코드 보안약점 26개"
- "앱 위변조", "루팅 탐지", "난독화", "ProGuard"
- "KISA 앱 검증 신청", "보안명세서", "보완조치내역서"

**references:** `procedure.md` (검증 절차 상세), `verification-criteria.md` (검증기준 상세)

**관련 스킬:** `secure-coding-kr` (진단기준 허브), `secure-coding-java` (Java/Android 구현), `crypto-policy-kr` (중요정보 암호화 검증), `owasp-masvs` (국내 기준으로 지적할 수 없는 영역의 국제표준 보완 — 방향 반대 항목 주의)

---

### crypto-policy-kr

KISA 「암호 알고리즘 및 키 길이 이용 안내서」(2018) 기반 암호 알고리즘·키 길이·유효기간 판정 레퍼런스. 기본선은 **보안강도 112비트 이상**, 2030년 이후까지 쓸 공개키 암호는 **128비트 강도 = RSA 3072비트 이상**을 권고합니다.

**주요 내용:**
- 보안강도별 권고 키 길이 종합표 / 권고 암호 알고리즘 (SEED, ARIA, LEA 등 국산 포함)
- SHA-1, HAS-160 용도별 사용 가능 여부 정밀 판정 (과잉 지적 방지)
- 암호키 유효기간 (NIST SP 800-57 기반)
- 선택 가이드(의사결정)와 코드 진단용 빠른 판정 체크리스트
- 현행 모범사례 — 안내서 범위 밖 보완 권고 (운영모드·IV·KDF·난수 생성 등)

**트리거 표현:**
- "암호 알고리즘", "키 길이", "보안강도"
- "SEED", "ARIA", "LEA", "KCDSA", "국산 암호"
- "RSA 키 길이", "SHA-1 사용 가능"
- "안전성 유지기간", "암호키 유효기간"

**references:** `algorithm-tables.md` (알고리즘·키 길이 표 전수)

**관련 스킬:** `secure-coding-kr` (진단기준 허브), `secure-coding-java` (Java 암호 API), `secure-coding-c` (C/C++ 암호 구현), `mobile-app-verify` (중요정보 암호화 검증)

---

### owasp-masvs

OWASP **MASVS v2.1.0**(8카테고리 24컨트롤) / **MASWE v1.0.0**(약점 78개) / **MASTG v2.0.0**(TEST 292) 기반 모바일 앱 보안 국제표준 레퍼런스(CC BY-SA 4.0, 2026-09-17 조회). OWASP MAS 생태계 전체를 담은 레퍼런스가 아니라 **국내 기준의 공백을 메우는 보완재**로, 「모바일 전자정부서비스 앱 소스코드 검증 가이드라인」을 근거로는 지적할 수 없는 영역 **확정 6건**(NETWORK-2 인증서 피닝 · PLATFORM-2 WebView · PLATFORM-3 화면캡처·알림·오버레이 · RESILIENCE-4 디버거/후킹 탐지 · AUTH-2 생체인증 · AUTH-3 Step-up 인증)과 **재분류 여지 2건**(PRIVACY-2·PRIVACY-3)을 중심으로 다룹니다. 기존 5종과 달리 **제도 판정 근거가 아니므로**, 이 스킬을 근거로 지적할 때는 출처를 OWASP MASVS/MASWE 로 밝히고 "구속력 없음"을 병기합니다.

> ⚠️ **방향 반대 경고**: `mobile-app-verify` 의 FV-5.1(루팅·탈옥을 유발하는 기능 금지)과 MASWE-0051(루팅·탈옥 탐지 구현 의무)은 같은 단어를 쓰면서 점검 방향이 정반대입니다 — 두 기준을 혼용하면 오판이 됩니다.

**주요 내용:**
- MASVS 8카테고리 24컨트롤 총괄과 MAS 프로파일(L1/L2/R/P) 선택 가이드
- `mobile-app-verify` 와의 경계 — 방향 반대 항목(FV-5.1 ↔ MASWE-0051) 오판 방지 규칙
- 국내 기준으로 지적할 수 없는 영역 확정 6건 + 재분류 여지 2건 (이 스킬의 핵심 부가가치)
- 추적 체인(MASVS → MASWE → MASTG-TEST → DEMO)과 소스 저장소 역참조 검색법
- MAS Checklist 폐지(2026-07) 이후의 대체 점검 워크플로

**트리거 표현:**
- "MASVS", "MASTG", "MASWE", "모바일 앱 보안 국제표준"
- "인증서 피닝", "WebView 보안", "탭재킹"
- "Play Integrity", "App Attest", "앱 어테스테이션"

**references:** `masvs-24-controls.md` (24컨트롤 전수 — ID·원문·연결 MASWE), `maswe-78.md` (MASWE-0001~0078 전수 색인), `mastg-structure.md` (MASTG 구성요소별 규모·상태 실측), `masvs-gap-vs-mobile-app-verify.md` (국내 51항목 ↔ 24컨트롤 전수 매핑)

**관련 스킬:** `mobile-app-verify` (국내 제도 판정 — 방향 반대 항목 주의), `secure-coding-kr` (진단기준 허브), `secure-coding-java` (Java/Android 구현), `crypto-policy-kr` (암호 알고리즘·키 길이), `owasp-asvs` (웹·API 국제표준 — 자매 스킬)

---

### owasp-asvs

OWASP **ASVS 5.0.0**(17챕터 345요구사항 — L1 70 · L2 183 · L3 92) 기반 웹·API 애플리케이션 보안 검증 국제표준 레퍼런스(릴리스 2025-05-30, 공식 한국어 PDF 103p, CC BY-SA 4.0, 2026-09-17 조회). ASVS 전체를 담은 레퍼런스가 아니라 **국내 기준의 공백을 메우는 보완재**로, 국내 설계단계 20개 기준에 대응 항목이 전무한 **공백 7개 챕터 144요구사항**(V3 웹 프런트엔드 31 · V4 API·웹서비스 16 · V9 Self-contained Tokens/JWT 7 · V10 OAuth·OIDC 36 · V13 Configuration 21 · V15 Secure Coding·Architecture 21 · V17 WebRTC 12)을 중심으로 다룹니다. `owasp-masvs` 와 같이 **제도 판정 근거가 아니므로**, 이 스킬을 근거로 지적할 때는 출처를 OWASP ASVS 5.0.0 요구사항 ID 로 밝히고 "구속력 없음"을 병기합니다.

> ⚠️ **정면 충돌 경고**: ASVS **V6.2.5**(L1)는 비밀번호의 문자 종류 **조합 규칙 자체를 금지**하지만, 국내 관행은 문자종류 조합을 강제합니다 — 두 문서가 서로 반대 방향을 요구하는 직접 충돌이므로, 제도 판정은 국내 기준을 따르고 V6.2.5 를 국내 기준 맥락의 조치 근거로 쓰면 안 됩니다.

**주요 내용:**
- 17챕터 345요구사항 총괄과 L1/L2/L3 레벨 재정의(위험 감소 + 구현 노력 기준 — 4.0.3 통념 금지)
- 4.0.3 → 5.0.0 마이그레이션 경고 — 286개 중 11개만 무변경 생존, 109개(38%) 제거, V1 Architecture 삭제와 기호 재사용 함정, L1 46%→20%
- 국내 설계단계 20개(SR1-1~SR4-1) ↔ ASVS 챕터 대응과 공백 7개 챕터 144요구사항 (이 스킬의 핵심 부가가치)
- 국내 기준과 정면 충돌하는 비밀번호 정책(V6.2.5 조합 규칙 금지 · V6.2.10 정기 변경 강제 금지) 판정 규칙
- 태그 `v5.0.0` 고정 조회(flat.json)와 지적 서술 템플릿·점검 체크리스트

**트리거 표현:**
- "ASVS", "JWT 검증", "OAuth", "OIDC"
- "CSP", "CORS", "SameSite", "SRI"
- "WebSocket 보안", "GraphQL 보안", "SBOM"

**references:** `asvs-17-chapters.md` (17챕터 색인 + 국내 공백 7개 챕터의 요구사항 수준 수록), `asvs-sr20-mapping.md` (국내 설계단계 20개 ↔ ASVS 챕터 대응표 — SR 번호별 20행 + 역방향 공백 요약)

**관련 스킬:** `owasp-masvs` (모바일 앱 국제표준 — 자매 스킬), `secure-coding-kr` (진단기준 허브 — 제도 판정), `secure-coding-java` (Java/JSP 구현), `crypto-policy-kr` (암호 알고리즘·키 길이)

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
| `~/.claude/agent-memory/mnn-source-inspector/` | `mnn-source-inspector` | MNN 조사 결과 누적 메모리 (사용자 전역, 저장소 간 공유) |

---


## 마켓플레이스 업데이트

```shell
/plugin marketplace update vibe-coding-tools
```
