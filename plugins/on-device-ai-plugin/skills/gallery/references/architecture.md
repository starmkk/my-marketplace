# Google AI Edge Gallery 상세 아키텍처 레퍼런스

## 목차
1. [DownloadWorker 상세](#download-worker)
2. [LLM 추론 구현 상세](#llm-inference)
3. [Agent Skills 시스템](#agent-skills)
4. [CustomTask 프레임워크](#custom-task)
5. [Model Allowlist 스키마](#model-allowlist)
6. [Proto 정의](#proto-definitions)
7. [HuggingFace OAuth 설정](#huggingface-oauth)
8. [주요 파일 경로 매핑](#file-paths)

---

## DownloadWorker 상세

`DownloadWorker`는 `CoroutineWorker`를 상속하여 백그라운드 모델 다운로드를 처리한다.

### 핵심 기능
- **이어받기**: 부분 다운로드 파일 감지 → HTTP Range 요청으로 이어받기
- **Foreground Service**: 알림에 진행률/속도/ETA 표시
- **HuggingFace 토큰**: `Authorization: Bearer <token>` 헤더 추가
- **ZIP 추출**: 다운로드 완료 후 자동 압축 해제
- **멀티 파일**: `extraDataFiles`로 여러 파일 순차 다운로드

### 저장 경로
```
{context.getExternalFilesDir(null)}/
  {normalizedModelName}/
    {version}/
      {downloadFileName}
```

### 진행률 추적
```kotlin
// WorkManager Data로 진행률 전달
setProgress(workDataOf(
    "progress" to percentComplete,
    "downloadedBytes" to bytesRead,
    "totalBytes" to totalSize,
    "speed" to bytesPerSecond,
    "eta" to estimatedSecondsRemaining,
))
```

### 취소
```kotlin
downloadRepository.cancelDownloadModel(model)
// → WorkManager.cancelUniqueWork(model.name)
```

**파일:** `worker/DownloadWorker.kt` (~350 lines)

---

## LLM 추론 구현 상세

### LlmModelHelper 인터페이스

```kotlin
interface LlmModelHelper {
    fun initialize(
        model: Model,
        configs: Map<ConfigKey, Any>,
        onDone: () -> Unit
    )
    fun runInference(
        input: String,
        resultListener: ResultListener,    // 스트리밍 콜백
        cleanUpListener: CleanUpListener   // 완료 콜백
    )
    fun stopResponse()
    fun resetConversation()
    fun cleanUp()
}

typealias ResultListener = (
    partialResult: String,
    done: Boolean,
    partialThinkingResult: String?
) -> Unit
```

### 실제 구현 (customtasks/LlmModelHelper.kt)

LiteRT-LM (`com.google.ai.edge.litertlm`)을 백엔드로 사용:

```kotlin
// 초기화
val engine = LiteRtLmEngine(
    modelPath = model.getLocalFilePath(),
    backend = if (configs[USE_GPU] == true) Backend.GPU else Backend.CPU,
    maxNumTokens = configs[MAX_TOKENS] as Int,
)

// 추론
engine.createConversation(messages).use { conversation ->
    conversation.sendMessageAsync(input).collect { chunk ->
        resultListener(chunk.text, chunk.done, chunk.thinking)
    }
}
```

### 멀티모달 처리
- **이미지**: Bitmap → byte array → LiteRT-LM Contents에 포함
- **오디오**: AudioRecord → PCM → LiteRT-LM 오디오 인코더
- **Thinking**: Gemma 4의 `<|think|>` 토큰 파싱 → `partialThinkingResult`로 분리

---

## Agent Skills 시스템

### 스킬 구조

```
skill-name/
├── SKILL.md          # YAML frontmatter + Markdown 지시문
└── (선택) assets/     # 추가 리소스
```

### SKILL.md 포맷

```yaml
---
name: "My Skill"
description: "스킬 설명"
homepage: "https://example.com"
secrets:
  - name: "API_KEY"
    description: "API 키"
---

# 스킬 지시문 (Markdown)
당신은 ...의 역할을 합니다.
```

### 스킬 타입

#### Text-Only 스킬
시스템 프롬프트에 Markdown 지시문을 주입하여 LLM의 행동을 조정.

#### JavaScript 스킬
숨겨진 WebView에서 JavaScript 실행:
```javascript
// 결과 반환
window.ai_edge_gallery_get_result = function(userMessage) {
    // API 호출, 데이터 처리 등
    return {
        type: "text",  // 또는 "image", "webview"
        content: "결과 텍스트"
    };
};
```

#### Native 스킬
Android Intent를 통한 디바이스 기능:
```kotlin
// IntentHandler.kt
fun handleIntent(action: String, params: Map<String, String>) {
    when (action) {
        "send_email" -> sendEmail(params["to"], params["subject"], params["body"])
        "send_sms" -> sendSms(params["number"], params["message"])
        "take_photo" -> launchCamera()
        "set_alarm" -> setAlarm(params["time"])
    }
}
```

### 스킬 관리 (SkillManagerViewModel)
```kotlin
// 스킬 로드 소스
- 내장 (assets/skills/)
- URL에서 다운로드
- 로컬 파일에서 로드
- 커뮤니티 featured 목록

// CRUD
skillManager.addSkill(skill)
skillManager.removeSkill(skillId)
skillManager.updateSkill(skillId, updatedSkill)
```

### 내장 스킬 목록
| 스킬 | 타입 | 설명 |
|------|------|------|
| calculate-hash | JS | 해시 계산 |
| interactive-map | JS | 인터랙티브 지도 |
| kitchen-adventure | Text | 요리 어드벤처 |
| mood-tracker | JS | 감정 추적 |
| qr-code | JS | QR 코드 생성 |
| query-wikipedia | JS | 위키피디아 검색 |
| send-email | Native | 이메일 전송 |
| text-spinner | JS | 텍스트 변환 |

---

## CustomTask 프레임워크

새로운 태스크 유형을 추가하기 위한 확장 포인트.

### 인터페이스

```kotlin
interface CustomTask {
    // 태스크 정의 (ID, 이름, 아이콘, 설명)
    val task: Task

    // 모델 초기화
    fun initializeModelFn(
        model: Model,
        configs: Map<ConfigKey, Any>,
        onDone: () -> Unit
    )

    // 모델 정리
    fun cleanUpModelFn(model: Model)

    // UI (Jetpack Compose)
    @Composable
    fun MainScreen(
        model: Model,
        navController: NavController
    )
}
```

### Hilt 등록

```kotlin
// LlmChatTaskModule.kt
@Module
@InstallIn(SingletonComponent::class)
abstract class LlmChatTaskModule {
    @Binds
    @IntoMap
    @StringKey(BuiltInTaskId.LLM_CHAT)
    abstract fun bindLlmChatTask(task: LlmChatTask): CustomTask
}
```

### 기존 태스크 구현체
| 클래스 | 태스크 ID | 디렉토리 |
|--------|-----------|----------|
| LlmChatTask | `llm_chat` | `ui/llmchat/` |
| LlmAskImageTask | `llm_ask_image` | `ui/llmchat/` |
| LlmAskAudioTask | `llm_ask_audio` | `ui/llmchat/` |
| AgentChatTask | `llm_agent_chat` | `customtasks/agentchat/` |
| MobileActionsTask | `llm_mobile_actions` | `customtasks/mobileactions/` |
| TinyGardenTask | `llm_tiny_garden` | `customtasks/tinygarden/` |

---

## Model Allowlist 스키마

`model_allowlist.json` 전체 구조:

```json
[
  {
    "name": "Gemma 3n E2B IT (int4)",
    "displayName": "Gemma 3n E2B",
    "url": "https://huggingface.co/litert-community/...",
    "downloadFileName": "gemma-3n-e2b-it-int4.litertlm",
    "sizeInBytes": 1500000000,
    "version": "v1",
    "taskTypes": ["llm_chat", "llm_ask_image", "llm_ask_audio"],
    "configs": {
      "temperature": 1.0,
      "topK": 64,
      "topP": 0.95,
      "maxTokens": 4096,
      "accelerator": "gpu",
      "enableThinking": true
    },
    "minMemoryBytes": 3000000000,
    "requiresAuth": false,
    "socVariants": {
      "qualcomm": {
        "url": "https://...",
        "accelerator": "npu"
      }
    },
    "extraDataFiles": [
      {
        "url": "https://...",
        "fileName": "extra_weights.bin",
        "sizeInBytes": 500000000
      }
    ]
  }
]
```

### 필드 설명
| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | 고유 식별자 |
| `displayName` | string | UI 표시명 |
| `url` | string | 다운로드 URL |
| `downloadFileName` | string | 로컬 파일명 |
| `sizeInBytes` | long | 파일 크기 |
| `version` | string | 버전 |
| `taskTypes` | string[] | 지원 태스크 목록 |
| `configs` | object | 기본 설정 |
| `minMemoryBytes` | long | 최소 메모리 요구량 |
| `requiresAuth` | boolean | HF 인증 필요 여부 |
| `socVariants` | object | SoC별 변형 |
| `extraDataFiles` | array | 추가 데이터 파일 |

---

## Proto Definitions

### settings.proto
```protobuf
message Settings {
    ThemeSetting theme = 1;
    string hf_access_token = 2;
    repeated string text_input_history = 3;
    repeated ImportedModel imported_models = 4;
    Skills skills = 5;
    // ...
}

message ImportedModel {
    string file_name = 1;
    string file_uri = 2;
    LlmConfig config = 3;
}

message Skills {
    repeated Skill skills = 1;
}
```

### skill.proto
```protobuf
message Skill {
    string name = 1;
    string description = 2;
    string instructions = 3;
    string homepage = 4;
    repeated Secret secrets = 5;
}
```

### benchmark.proto
벤치마크 결과 저장 (latency, throughput, tokens/s).

---

## HuggingFace OAuth 설정

Gated 모델 다운로드를 위한 OAuth 설정:

### 1. HuggingFace에서 OAuth 앱 생성
- https://huggingface.co/settings/applications/new
- Redirect URI: `com.google.ai.edge.gallery:/oauth`

### 2. ProjectConfig.kt 수정
```kotlin
object ProjectConfig {
    const val clientId = "YOUR_CLIENT_ID"
    const val redirectUri = "com.google.ai.edge.gallery:/oauth"
    const val authEndpoint = "https://huggingface.co/oauth/authorize"
    const val tokenEndpoint = "https://huggingface.co/oauth/token"
}
```

### 3. build.gradle.kts 수정
```kotlin
defaultConfig {
    manifestPlaceholders["appAuthRedirectScheme"] = "com.google.ai.edge.gallery"
}
```

---

## 주요 파일 경로 매핑

### 엔트리 포인트
| 파일 | 설명 |
|------|------|
| `MainActivity.kt` | Activity 진입점 |
| `GalleryApp.kt` | Root Composable |

### 데이터 레이어
| 파일 | 설명 |
|------|------|
| `data/Model.kt` | Model 데이터 클래스 |
| `data/Tasks.kt` | Task 정의, BuiltInTaskId |
| `data/Config.kt` | ConfigKey 정의 |
| `data/DownloadRepository.kt` | 다운로드 관리 |
| `data/DataStoreRepository.kt` | 영속 설정 |
| `data/ModelAllowlist.kt` | allowlist 파싱 |

### 런타임
| 파일 | 설명 |
|------|------|
| `runtime/LlmModelHelper.kt` | 추론 인터페이스 |
| `customtasks/LlmModelHelper.kt` | 추론 구현 (LiteRT-LM) |

### UI
| 파일 | 설명 |
|------|------|
| `ui/llmchat/LlmChatScreen.kt` | 채팅 화면 |
| `ui/llmchat/LlmChatViewModel.kt` | 채팅 ViewModel |
| `ui/modelmanager/GlobalModelManager.kt` | 모델 관리 화면 |
| `ui/modelmanager/ModelManagerViewModel.kt` | 모델 관리 VM |
| `ui/benchmark/BenchmarkScreen.kt` | 벤치마크 화면 |
| `ui/common/chat/` | 공유 채팅 컴포넌트 (26 파일) |
| `ui/navigation/GalleryNavGraph.kt` | 네비게이션 |

### CustomTask
| 파일 | 설명 |
|------|------|
| `customtasks/common/CustomTask.kt` | CustomTask 인터페이스 |
| `customtasks/agentchat/AgentChatScreen.kt` | Agent 채팅 |
| `customtasks/agentchat/AgentTools.kt` | 도구 정의 |
| `customtasks/agentchat/SkillManagerViewModel.kt` | 스킬 관리 |
| `customtasks/agentchat/IntentHandler.kt` | Native Intent |
| `customtasks/mobileactions/MobileActionsScreen.kt` | 디바이스 제어 |
| `customtasks/mobileactions/MobileActionsViewModel.kt` | 디바이스 제어 VM |
| `customtasks/tinygarden/TinyGardenScreen.kt` | 미니 게임 |

### 백그라운드
| 파일 | 설명 |
|------|------|
| `worker/DownloadWorker.kt` | 다운로드 Worker |

### 빌드 & 설정
| 파일 | 설명 |
|------|------|
| `app/build.gradle.kts` | 앱 빌드 설정 |
| `gradle/libs.versions.toml` | 버전 카탈로그 |
| `common/ProjectConfig.kt` | HF OAuth 설정 |
| `AndroidManifest.xml` | 권한, 컴포넌트 선언 |

### 스킬 & 에셋
| 경로 | 설명 |
|------|------|
| `skills/README.md` | 스킬 프레임워크 문서 |
| `skills/built-in/` | 내장 스킬 (8개) |
| `skills/featured/` | 커뮤니티 스킬 |
| `assets/skills/` | APK 내장 스킬 에셋 |

### 프로토콜
| 파일 | 설명 |
|------|------|
| `proto/settings.proto` | 앱 설정 스키마 |
| `proto/skill.proto` | 스킬 스키마 |
| `proto/benchmark.proto` | 벤치마크 스키마 |

### 문서
| 파일 | 설명 |
|------|------|
| `README.md` | 프로젝트 개요 |
| `DEVELOPMENT.md` | 빌드 가이드 |
| `Function_Calling_Guide.md` | 함수 호출 가이드 |
| `model_allowlist.json` | 모델 카탈로그 |
