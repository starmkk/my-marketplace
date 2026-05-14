---
name: gallery
description: |
  Google AI Edge Gallery — 온디바이스 LLM Android/iOS 앱 레퍼런스 스킬.
  Reference for Google AI Edge Gallery, an on-device LLM Android/iOS reference app.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "gallery", "ai edge gallery", "google ai edge"
  - "온디바이스 앱", "on-device app", "model download", "모델 다운로드"
  - "agent skills", "custom task", "CustomTask", "model_allowlist.json"
  - "llm chat ui", "LLM 채팅 UI", "Jetpack Compose"
  - Gallery 코드 읽기/수정, 모델 다운로드/관리 로직, Agent Skills 시스템 확장,
    CustomTask 추가, model_allowlist.json 수정, Compose UI 작업

  관련 스킬 (Related skills):
  - `litert`: Gallery 내부 ML 추론 백엔드(LiteRT).
  - `litert-lm`: Gallery가 LLM 실행에 사용하는 엔진.
---

# Google AI Edge Gallery 레퍼런스 스킬

## 환경변수

| 변수 | 필수 | 설명 |
|------|------|------|
| `GALLERY_SOURCE_PATH` | 선택 | Google AI Edge Gallery 레포 로컬 클론 경로 |

미설정 시에도 레퍼런스 스킬로 사용 가능하다. 로컬 클론이 있으면 설정해두면 경로 탐색 없이 소스를 직접 참조할 수 있다.

**설정 방법:**
```shell
# 클론
git clone https://github.com/google-ai-edge/gallery

# 등록 (zsh/bash)
echo 'export GALLERY_SOURCE_PATH=/path/to/gallery' >> ~/.zshrc
source ~/.zshrc

# 검증
bash scripts/install.sh
```

---

Gallery는 온디바이스에서 오픈소스 LLM을 실행하는 Android/iOS 앱이다. 모델 다운로드, 멀티턴 채팅, 멀티모달(이미지/오디오), Agent Skills, 벤치마크를 지원한다. LiteRT-LM을 추론 백엔드로 사용한다.

## 코드베이스 탐색 방법

이 스킬은 경로에 의존하지 않는다. Gallery 소스코드를 찾으려면:
1. 프로젝트의 CLAUDE.md나 설정 파일에서 Gallery 경로를 확인
2. `find` 또는 `glob`으로 `com/google/ai/edge/gallery/` 패턴 검색
3. 일반적 위치: `third_party/Gallery.main/`, `external/gallery/` 등

## 앱 아키텍처 (MVVM + Jetpack Compose)

```
MainActivity → GalleryApp → GalleryNavHost
                                ├── HomeScreen
                                ├── GlobalModelManager (모델 선택/다운로드)
                                ├── LlmChatScreen (AI 채팅)
                                ├── LlmAskImageScreen (이미지 질문)
                                ├── LlmAskAudioScreen (오디오 전사)
                                ├── AgentChatScreen (Agent + Skills)
                                ├── MobileActionsScreen (디바이스 제어)
                                ├── BenchmarkScreen (성능 테스트)
                                └── TinyGardenScreen (미니 게임)
```

### 핵심 패턴
- **MVVM**: ViewModel + StateFlow/LiveData
- **Hilt**: 의존성 주입
- **Jetpack Compose**: 선언적 UI
- **WorkManager**: 백그라운드 모델 다운로드
- **DataStore**: proto-serialized 영속 설정

### 디렉토리 구조
```
Gallery/
├── model_allowlist.json              # 모델 카탈로그 (JSON)
├── model_allowlists/                 # 태스크별 모델 설정
├── skills/                           # 스킬 정의
│   ├── built-in/                     # 내장 스킬 (8개)
│   └── featured/                     # 커뮤니티 스킬
├── Android/src/app/src/main/java/com/google/ai/edge/gallery/
│   ├── data/                         # 데이터 모델 + 리포지토리
│   │   ├── Model.kt                  # Model 클래스 (이름, URL, 크기, configs)
│   │   ├── Tasks.kt                  # Task 정의 (채팅, 이미지, 오디오 등)
│   │   ├── Config.kt                 # 설정 키 (TEMPERATURE, TOPK 등)
│   │   ├── DownloadRepository.kt     # 모델 다운로드 관리
│   │   ├── DataStoreRepository.kt    # 영속 설정 관리
│   │   └── ModelAllowlist.kt         # allowlist JSON 파싱
│   ├── runtime/
│   │   └── LlmModelHelper.kt        # LLM 추론 인터페이스
│   ├── customtasks/                  # 확장 태스크
│   │   ├── common/CustomTask.kt      # CustomTask 인터페이스
│   │   ├── LlmModelHelper.kt        # 추론 구현 (LiteRT-LM 사용)
│   │   ├── agentchat/               # Agent Skills (15 파일)
│   │   ├── mobileactions/           # 디바이스 제어 (FunctionGemma)
│   │   └── tinygarden/              # 미니 게임
│   ├── ui/
│   │   ├── llmchat/                 # 채팅 UI + ViewModel
│   │   ├── modelmanager/            # 모델 관리 UI + ViewModel
│   │   ├── benchmark/               # 벤치마크 UI
│   │   ├── common/chat/             # 공유 채팅 컴포넌트 (26 파일)
│   │   └── navigation/              # NavGraph
│   ├── worker/
│   │   └── DownloadWorker.kt        # 백그라운드 다운로드 Worker
│   ├── di/                          # Hilt 모듈
│   └── common/                      # 유틸리티
└── Android/src/app/build.gradle.kts  # Gradle 빌드 설정
```

## 핵심 컴포넌트

### 1. 모델 다운로드 & 관리

```kotlin
// DownloadRepository - WorkManager 기반
downloadRepository.downloadModel(model)     // 다운로드 시작
downloadRepository.cancelDownloadModel(model) // 취소

// 저장 경로: {externalFilesDir}/{normalizedName}/{version}/{downloadFileName}
// 기능: 이어받기, HuggingFace 토큰 인증, ZIP 자동 추출
```

### 2. LLM 추론

```kotlin
// LlmModelHelper 인터페이스
interface LlmModelHelper {
    fun initialize(model: Model, configs: Map<ConfigKey, Any>, onDone: () -> Unit)
    fun runInference(input: String, resultListener: ResultListener)
    fun stopResponse()
    fun resetConversation()
    fun cleanUp()
}

// ResultListener: (partialResult: String, done: Boolean, thinkingResult: String?) -> Unit
```

### 3. CustomTask 확장

```kotlin
// CustomTask 인터페이스 - 새 태스크를 추가하려면 이것을 구현
interface CustomTask {
    val task: Task
    fun initializeModelFn(model: Model, configs: Map<ConfigKey, Any>)
    fun cleanUpModelFn(model: Model)
    @Composable
    fun MainScreen(model: Model, navController: NavController)
}
```

### 4. Agent Skills 시스템

스킬은 LLM의 기능을 확장하는 모듈식 플러그인:

**스킬 타입:**
- **Text-Only**: Markdown으로 작성한 페르소나/시나리오 지시문
- **JavaScript**: 숨겨진 WebView에서 실행 (`window.ai_edge_gallery_get_result`)
  - API 호출, 이미지/웹뷰 반환 가능, Secret(API 키) 전달 지원
- **Native**: Android Intent (SMS, 이메일, 카메라, 알람 등)

**스킬 로딩:** 내장, URL, 로컬 파일, 커뮤니티 목록에서 로드 가능

### 5. 설정 (Config)

```kotlin
// 주요 ConfigKey
TEMPERATURE    // 0.0-2.0 (Slider)
TOPK           // 1-256 (Slider)
TOPP           // 0.0-1.0 (Slider)
MAX_TOKENS     // 출력 길이 제한
USE_GPU        // GPU 가속 (Switch)
ENABLE_THINKING // Gemma 4 thinking 모드 (Switch)
```

## 빌드 설정

```bash
# 요구사항
# Android SDK 35, Kotlin 2.2.0, AGP 8.8.2, JDK 11+

# HuggingFace OAuth 설정 필요 (ProjectConfig.kt)
# clientId, redirectUri 수정 후 빌드

cd Android/src
./gradlew assembleDebug
```

### 주요 의존성 (libs.versions.toml)
- LiteRT-LM: `0.10.0`
- Compose BOM: `2026.02.00`
- Hilt: `2.57.2`
- WorkManager: `2.10.0`
- CameraX: `1.4.2`
- Firebase: `33.16.0`
- Protobuf: `4.26.1`

## model_allowlist.json

모델 카탈로그 정의 파일. 각 모델의 이름, URL, 크기, 태스크 타입, 기본 설정, SoC별 변형을 정의한다.

```json
{
  "name": "Gemma 3n E2B",
  "url": "https://huggingface.co/...",
  "sizeInBytes": 1500000000,
  "configs": {
    "temperature": 1.0,
    "topK": 64,
    "topP": 0.95,
    "maxTokens": 4096,
    "accelerator": "gpu"
  },
  "taskTypes": ["llm_chat", "llm_ask_image"]
}
```

## 지원 태스크

| 태스크 ID | 설명 | 모달리티 |
|-----------|------|----------|
| `llm_chat` | 멀티턴 대화 | Text |
| `llm_prompt_lab` | 단일턴 + 파라미터 조정 | Text |
| `llm_ask_image` | 이미지 질문 | Text + Image |
| `llm_ask_audio` | 오디오 전사/번역 | Text + Audio |
| `llm_agent_chat` | Agent + Skills | Text + Tools |
| `llm_mobile_actions` | 디바이스 제어 | Text (FunctionGemma) |
| `llm_tiny_garden` | 미니 게임 | Text (FunctionGemma) |

## 상세 레퍼런스

DownloadWorker 상세, Agent 도구 구현, Intent 핸들링, Skill YAML 스키마 등은 `references/architecture.md`를 참조하라.
