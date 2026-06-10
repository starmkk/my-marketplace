---
name: litert
description: |
  Google LiteRT (구 TensorFlow Lite) 온디바이스 ML 추론 프레임워크 레퍼런스 스킬.
  Reference for Google LiteRT (formerly TensorFlow Lite), an on-device ML inference framework.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "litert", "tflite", "TensorFlow Lite"
  - "on-device inference", "온디바이스 추론"
  - "CompiledModel", "Environment", "TensorBuffer"
  - "delegate", "dispatch", "accelerator"
  - "GPU delegate", "NPU delegate", "XNNPACK"
  - "CMake/Bazel 빌드", ".tflite 모델 로딩/실행/컴파일"

  관련 스킬 (Related skills):
  - `litert-lm`: LiteRT 위에서 LLM 추론을 다룰 때.
  - `tensorflow`: SavedModel ↔ tflite 변환·양자화.
  - `mnn`: 대안이 되는 모바일 추론 프레임워크.
---

# LiteRT 레퍼런스 스킬

## 소스 코드 관리 (~/.claude/repo)

소스코드가 필요한 작업(예: LiteRT 헤더 탐색, 빌드, API 확인 등)이 생기면
**반드시 먼저 사용자에게 확인**한다:

```
[소스 사용 흐름]
Step 1. 사용자에게 묻기:
  "로컬에 이미 LiteRT 소스가 있으신가요? 있다면 경로를 알려주세요."

Step 2a. 사용자가 경로 제공 → 해당 경로 그대로 사용

Step 2b. 사용자가 없다고 하면 → ~/.claude/repo에 자동 다운로드 후 안내
```

### 참조 repo

| 항목 | 값 |
|------|-----|
| GitHub | https://github.com/google-ai-edge/LiteRT |
| 폴더 패턴 | `~/.claude/repo/LiteRT@<version>` |

### 다운로드 방법

```bash
# 최신 버전 tag 조회
LATEST=$(git ls-remote --tags --sort=-version:refname https://github.com/google-ai-edge/LiteRT \
  | grep -v '{}' | head -1 | awk '{print $2}' | sed 's|refs/tags/||')

# 최신 버전 clone (버전 미명시 시)
git clone --branch "$LATEST" --depth 1 \
  https://github.com/google-ai-edge/LiteRT \
  ~/.claude/repo/LiteRT@"$LATEST"

# 특정 버전 clone (예: v1.2.0)
git clone --branch v1.2.0 --depth 1 \
  https://github.com/google-ai-edge/LiteRT \
  ~/.claude/repo/LiteRT@v1.2.0
```

이미 `~/.claude/repo/LiteRT@<version>`이 존재하면 재다운로드 없이 재사용한다.
다운로드 후 사용자에게 경로 안내.

---

LiteRT(formerly TensorFlow Lite)는 Google의 고성능 온디바이스 ML 추론 런타임이다. 모바일, 임베디드, IoT 디바이스에서 저지연 ML 추론을 수행한다.

## 코드베이스 탐색 방법

이 스킬은 경로에 의존하지 않는다. LiteRT 소스코드를 찾으려면:
1. 프로젝트의 CLAUDE.md나 설정 파일에서 LiteRT 경로를 확인
2. `find` 또는 `glob`으로 `litert/cc/litert_compiled_model.h` 패턴 검색
3. 일반적 위치: `third_party/LiteRT.main/`, `external/litert/` 등

## 핵심 아키텍처

```
.tflite 파일 → Model IR (LiteRtModel) → CompiledModel → Runtime Execution
```

### 디렉토리 구조
```
litert/
├── c/               # ABI-stable C API (litert_common.h, litert_model.h, litert_compiled_model.h)
├── cc/              # Public C++ API (주 개발용)
│   ├── litert_compiled_model.h   # 메인 추론 API
│   ├── litert_environment.h      # 런타임 컨텍스트
│   ├── litert_model.h
│   ├── litert_tensor_buffer.h    # 버퍼 관리
│   └── options/                  # 백엔드별 옵션 (CPU, GPU, Qualcomm, MediaTek 등)
├── core/            # 내부 공유 코드 (model IR, serialization)
├── runtime/         # 실행 엔진 (compiled_model, accelerator, dispatch)
├── compiler/        # 컴파일러 플러그인 (MLIR 기반)
├── vendors/         # 하드웨어 벤더 구현 (google_tensor, qualcomm, mediatek, intel, samsung)
├── python/          # Python 바인딩
├── kotlin/          # Kotlin/Android 바인딩
├── js/              # JavaScript 바인딩
└── tools/           # 유틸리티
tflite/              # 레거시 TFLite (kernels, delegates, converter, schema)
```

## 주요 API

### C++ API (권장)

```cpp
#include "litert/cc/litert_environment.h"
#include "litert/cc/litert_compiled_model.h"
#include "litert/cc/litert_tensor_buffer.h"

using namespace litert;

// 1. Environment 생성
auto env = Environment::Create(EnvironmentOptions()
    .SetDispatchLibraryDir("/path/to/dispatch")
    .SetCompilerPluginLibraryDir("/path/to/plugins"));

// 2. 컴파일 옵션 설정
auto options = Options::Create();
options->SetHardwareAccelerators(HwAccelerator::kGpu | HwAccelerator::kNpu);
options->AddCpuOptions(CpuOptions().SetNumThreads(4));
options->AddGpuOptions(GpuOptions().SetUseQuantizedGpuModel(true));

// 3. 모델 로드 + 컴파일
auto model = CompiledModel::Create(env, "model.tflite", options);

// 4. 버퍼 요구사항 확인 + 버퍼 생성
auto input_reqs = model->GetInputTensorBufferRequirements(0);
auto output_reqs = model->GetOutputTensorBufferRequirements(0);
auto input = TensorBuffer::Create(env, input_reqs.value());
auto output = TensorBuffer::Create(env, output_reqs.value());

// 5. 추론 실행 (비동기)
std::memcpy(input->GetData<float>(), data, size);
auto event = model->Run(input, output);
event->Wait();
auto* result = output->GetData<float>();
```

### C API (ABI-stable)

```c
LiteRtEnvironment env;
LiteRtCompiledModel model;
LiteRtCreateEnvironment(..., &env);
LiteRtCreateCompiledModel(env, litert_model, options, &model);
LiteRtCompiledModelRun(model, &input, &output, &event);
```

## 하드웨어 가속

| 플랫폼 | CPU | GPU | NPU |
|---------|-----|-----|-----|
| Android | XNNPACK | OpenCL, OpenGL | Qualcomm HTP, MediaTek APU, Google Tensor |
| iOS | XNNPACK | Metal | ANE (예정) |
| Linux | XNNPACK | WebGPU | - |
| macOS | XNNPACK | WebGPU, Metal | ANE (예정) |
| Windows | XNNPACK | WebGPU | Intel (예정) |

### Delegate vs Dispatch API
- **Delegate** (레거시): TFLite의 하드웨어 가속 메커니즘
- **Dispatch API** (신규): ABI-stable, 비동기 실행, 버퍼 핸드셰이킹, 하드웨어 버퍼 지원

## 빌드 시스템

### Bazel (주 빌드)
```bash
bazel build //litert/cc:litert_compiled_model
```

### CMake (크로스 플랫폼)
```bash
cmake --preset android-arm64
cmake --build cmake_build_android_arm64

# 주요 옵션
-DLITERT_ENABLE_GPU=ON
-DLITERT_ENABLE_NPU=ON
-DANDROID_NDK_HOME=<path>
```

## 벤더별 옵션

```cpp
// Qualcomm
options->AddQualcommOptions(QualcommOptions()
    .SetHtpPerformanceMode(kLiteRtHtpPerfTurbo));

// MediaTek
options->AddMediatekOptions(MediatekOptions()
    .SetPowerHint(kLiteRtMediatekPowerHintHigh));

// Google Tensor
options->AddGoogleTensorOptions(GoogleTensorOptions()
    .SetEnableEdgeTPU(true));
```

## 버퍼 타입

TensorBuffer는 다양한 메모리 타입을 추상화한다:
- CPU (standard malloc)
- GPU (OpenCL, Metal, WebGPU)
- Android Hardware Buffer (AHardwareBuffer)
- Ion, FastRPC (Qualcomm), DmaBuf (Linux)

## 상세 레퍼런스

아키텍처, 컴파일러 플러그인, 패턴 매칭, Dispatch API의 상세 내용은 `references/architecture.md`를 참조하라.
