# LiteRT 상세 아키텍처 레퍼런스

## 목차
1. [Dispatch API](#dispatch-api)
2. [Compiler Plugin](#compiler-plugin)
3. [Pattern Matching](#pattern-matching)
4. [Environment Options 전체 목록](#environment-options)
5. [Compilation Options 전체 목록](#compilation-options)
6. [버퍼 타입 상세](#buffer-types)
7. [Accelerator Test Suite](#ats)
8. [주요 파일 경로 매핑](#file-paths)

---

## Dispatch API

TFLite Delegate를 대체하는 새로운 하드웨어 가속 인터페이스.

**장점:**
- ABI-stable (바이너리 호환)
- 버퍼 핸드셰이킹 (TensorBufferRequirements)
- 비동기 실행 (Event 기반)
- 하드웨어 네이티브 버퍼 지원

**핵심 함수:**
```c
LiteRtDispatchInitialize();                         // 초기화
LiteRtDispatchDeviceContextCreate();                // 디바이스 관리
LiteRtDispatchInvocationContextCreate();            // 실행 컨텍스트
LiteRtDispatchGetInputRequirements();               // 입력 버퍼 스펙
LiteRtDispatchGetOutputRequirements();              // 출력 버퍼 스펙
LiteRtDispatchInvoke();                             // 추론 실행
```

**참조 파일:** `litert/DISPATCH_API.md`, `litert/runtime/dispatch/`

---

## Compiler Plugin

커스텀 하드웨어 가속기를 위한 컴파일러 플러그인 인터페이스.

**플러그인 구현 필수 함수:**
```c
// 1. 플러그인 생성
LiteRtCreateCompilerPlugin();

// 2. 모델 파티셔닝 - 가속할 연산 선택
LiteRtCompilerPluginPartition(
    plugin, soc_model, subgraph, selected_ops);

// 3. 선택된 연산 컴파일 → 바이트코드 생성
LiteRtCompilerPluginCompile(
    plugin, soc_model, partitions, &result);
```

**컴파일 흐름:**
1. `.tflite` → LiteRtModel 로드
2. 플러그인이 가속 가능한 op 선택 (파티셔닝)
3. 선택된 op을 하드웨어별 바이트코드로 컴파일 (AOT/JIT)
4. 런타임에서 가속기로 실행

**참조 파일:** `litert/COMPILER_PLUGIN.md`, `litert/compiler/plugin/`

---

## Pattern Matching

모델 변환/최적화를 위한 그래프 패턴 매칭 시스템.

```cpp
// 연산 타입 매칭
m_OpCode<kLiteRtOpCodeTflAdd>()

// 텐서 형상 매칭
m_Shape({1, 224, 224, 3})

// 옵션 조건 매칭
m_Options<AddOptions>([](const AddOptions& o) {
    return o.fused_activation_function == kFusedActRelu;
})

// 교환 법칙 적용 이진 연산
m_CommutativeOp<kLiteRtOpCodeTflAdd>(m_Any(), m_Const())

// 단일 사용 텐서
m_HasOneUse()
```

**예시 - ReLU-fused Add 매칭:**
```cpp
if (Match(op, m_Op<kLiteRtOpCodeTflAdd>(
    m_Any(), m_Any(),
    m_Options<AddOptions>([](const AddOptions& o) {
      return o.fused_activation_function == kFusedActRelu;
    })))) {
    // 변환 수행
}
```

**참조 파일:** `litert/PATTERN_MATCHING.md`

---

## Environment Options

```cpp
EnvironmentOptions env_opts;

// 플러그인/디스패치 경로
env_opts.SetCompilerPluginLibraryDir("/path/to/plugins");
env_opts.SetDispatchLibraryDir("/path/to/dispatch");
env_opts.SetCompilerCacheDir("/path/to/cache");
env_opts.SetRuntimeLibraryDir("/path/to/runtime");

// OpenCL (Android/Linux GPU)
env_opts.SetOpenClDeviceId(0);
env_opts.SetOpenClPlatformId(0);

// Metal (macOS/iOS)
env_opts.SetMetalDevice(metal_device);
env_opts.SetMetalCommandQueue(metal_queue);

// WebGPU (Web/Desktop)
env_opts.SetWebGpuDevice(wgpu_device);
env_opts.SetWebGpuQueue(wgpu_queue);

// Vulkan (실험적)
env_opts.SetVulkanEnvironment(vulkan_env);
```

---

## Compilation Options

```cpp
Options opts;

// 하드웨어 선택
opts.SetHardwareAccelerators(
    HwAccelerator::kGpu | HwAccelerator::kNpu);

// CPU
opts.AddCpuOptions(CpuOptions()
    .SetNumThreads(8));

// GPU
opts.AddGpuOptions(GpuOptions()
    .SetUseQuantizedGpuModel(true)
    .SetEnableBufferInterop(true));

// Qualcomm Hexagon
opts.AddQualcommOptions(QualcommOptions()
    .SetHtpPerformanceMode(kLiteRtHtpPerfTurbo));

// MediaTek
opts.AddMediatekOptions(MediatekOptions()
    .SetPowerHint(kLiteRtMediatekPowerHintHigh));

// Google Tensor
opts.AddGoogleTensorOptions(GoogleTensorOptions()
    .SetEnableEdgeTPU(true));

// Intel OpenVINO
opts.AddIntelOpenVinoOptions(...);

// Samsung
opts.AddSamsungOptions(...);

// 커스텀 op 등록
opts.AddCustomOpKernel("my_op", 1, kernel_impl, kernel_data);

// 외부 텐서 바인딩
opts.BindExternalTensor("constant_0", external_buffer);
```

**옵션 헤더 위치:** `litert/cc/options/litert_*_options.h`

---

## Buffer Types

| 타입 | 플랫폼 | 용도 |
|------|--------|------|
| CPU (malloc) | 모든 플랫폼 | 기본 CPU 메모리 |
| OpenCL | Android, Linux | GPU 가속 |
| Metal | macOS, iOS | Apple GPU |
| WebGPU | Web, Desktop | 크로스 플랫폼 GPU |
| AHardwareBuffer | Android | 하드웨어 네이티브 버퍼 |
| Ion | Android | 레거시 메모리 할당 |
| FastRPC | Qualcomm | DSP 통신 |
| DmaBuf | Linux | DMA 버퍼 공유 |

**Zero-copy 패턴:**
```cpp
// GPU 버퍼 직접 접근 (복사 없음)
auto buffer = TensorBuffer::CreateFromGpuBuffer(env, gpu_handle, requirements);
// 또는 AHardwareBuffer 래핑
auto buffer = TensorBuffer::CreateFromAhwb(env, ahwb, requirements);
```

---

## ATS (Accelerator Test Suite)

하드웨어 가속기 검증을 위한 테스트 프레임워크.

**기능:**
- 사전 빌드된 테스트 모델
- CPU 대비 기능 검증
- 성능 프로파일링
- AOT 컴파일 테스트

**Bazel 매크로:**
```python
litert_define_ats(
    name = "my_accelerator_test",
    models = ["model1.tflite", "model2.tflite"],
    accelerator = "gpu",
)
```

**프로파일링:**
```cpp
model.StartProfilingCollection();
// ... 추론 실행 ...
auto metrics = model.StopProfilingCollection();
// 지연 시간, 전력, 메모리 등 하드웨어 메트릭
```

**참조:** `litert/ats/`, `litert/TESTING.md`

---

## 주요 파일 경로 매핑

### API 헤더
| 파일 | 설명 |
|------|------|
| `litert/cc/litert_compiled_model.h` | 메인 추론 API |
| `litert/cc/litert_environment.h` | 런타임 컨텍스트 |
| `litert/cc/litert_model.h` | 모델 로딩 |
| `litert/cc/litert_tensor_buffer.h` | 버퍼 관리 |
| `litert/cc/litert_options.h` | 컴파일 옵션 |
| `litert/c/litert_common.h` | C API 공통 타입 |

### 런타임
| 파일 | 설명 |
|------|------|
| `litert/runtime/compiled_model.h` | 내부 구현 |
| `litert/runtime/accelerator.h` | 가속기 인터페이스 |
| `litert/runtime/accelerators/` | CPU/GPU/NPU 레지스트리 |
| `litert/runtime/dispatch/` | Dispatch API 구현 |

### 모델
| 파일 | 설명 |
|------|------|
| `litert/core/model/model.h` | 코어 모델 구조체 |
| `litert/core/model/model_load.h` | 모델 로딩 |
| `litert/core/model/model_serialize.h` | 직렬화 |
| `tflite/schema/schema.fbs` | FlatBuffer 스키마 |

### 벤더
| 디렉토리 | 하드웨어 |
|-----------|----------|
| `litert/vendors/google_tensor/` | Google Tensor NPU |
| `litert/vendors/qualcomm/` | Qualcomm Hexagon |
| `litert/vendors/mediatek/` | MediaTek APU |
| `litert/vendors/intel_openvino/` | Intel OpenVINO |
| `litert/vendors/samsung/` | Samsung NPU |

### 빌드
| 파일 | 설명 |
|------|------|
| `CMakePresets.json` | CMake 프리셋 (default, android-arm64 등) |
| `g3doc/instructions/CMAKE_BUILD_INSTRUCTIONS.md` | 빌드 가이드 |
