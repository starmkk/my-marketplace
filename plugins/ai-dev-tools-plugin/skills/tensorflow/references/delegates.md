# TFLite Delegate 상세 레퍼런스

## XNNPACK Delegate (CPU 최적화)

헤더: `tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h`

### Options 구조체

```c
typedef struct {
  int32_t num_threads;                          // -1: 기본, 0: 단일
  uint32_t runtime_flags;                       // XNN 런타임 플래그
  uint32_t flags;                               // 기능 플래그 (비트필드)
  struct TfLiteXNNPackDelegateWeightsCache* weights_cache;
  const char* weight_cache_file_path;           // 캐시 파일 경로
  int weight_cache_file_descriptor;
  void* weight_cache_provider;
} TfLiteXNNPackDelegateOptions;
```

### 플래그 전체 목록

| 플래그 | 설명 |
|-------|-----|
| `TFLITE_XNNPACK_DELEGATE_FLAG_QS8` | Signed INT8 양자화 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_QU8` | Unsigned INT8 양자화 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_FORCE_FP16` | FP32→FP16 자동 변환 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_DYNAMIC_FULLY_CONNECTED` | 동적 가중치 FC |
| `TFLITE_XNNPACK_DELEGATE_FLAG_VARIABLE_OPERATORS` | VAR_HANDLE/READ_VARIABLE/ASSIGN |
| `TFLITE_XNNPACK_DELEGATE_FLAG_TRANSIENT_INDIRECTION_BUFFER` | 메모리 절약 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_ENABLE_LATEST_OPERATORS` | 실험적 연산자 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_ENABLE_SUBGRAPH_RESHAPING` | 동적 텐서 지원 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_SLOW_CONSISTENT_ARITHMETIC` | 수치 일관성 |
| `TFLITE_XNNPACK_DELEGATE_FLAG_DISABLE_DYNAMICALLY_QUANTIZED_OPS` | 동적 양자화 비활성화 |

### Weight 캐시

```c
// 파일 기반 캐시
opts.weight_cache_file_path = "/path/to/cache";

// 인메모리 캐시
opts.weight_cache_file_path = TfLiteXNNPackDelegateInMemoryFilePath();  // ":memory"

// 수동 관리
struct TfLiteXNNPackDelegateWeightsCache* cache = TfLiteXNNPackDelegateWeightsCacheCreate();
opts.weights_cache = cache;
// ... delegate 사용 후 ...
TfLiteXNNPackDelegateWeightsCacheFinalizeSoft(cache);  // 추가 항목 허용
TfLiteXNNPackDelegateWeightsCacheFinalizeHard(cache);  // 더 이상 추가 불가
TfLiteXNNPackDelegateWeightsCacheDelete(cache);
```

### 인트로스펙션

```c
void* TfLiteXNNPackDelegateGetThreadPool(TfLiteDelegate*);  // pthreadpool_t 반환
const TfLiteXNNPackDelegateOptions* TfLiteXNNPackDelegateGetOptions(TfLiteDelegate*);
uint32_t TfLiteXNNPackDelegateGetFlags(TfLiteDelegate*);
```

---

## GPU Delegate

헤더: `tensorflow/lite/delegates/gpu/delegate.h`, `delegate_options.h`

### Options 구조체

```c
typedef struct {
  int32_t is_precision_loss_allowed;     // FP16 허용
  int32_t inference_preference;          // 추론 모드
  int32_t inference_priority1;           // 1차 우선순위
  int32_t inference_priority2;           // 2차
  int32_t inference_priority3;           // 3차
  int64_t experimental_flags;            // 실험적 기능
  int32_t max_delegated_partitions;      // 최대 파티션 (기본: 1)
  const char* serialization_dir;         // 커널 캐시 디렉토리
  const char* model_token;              // 모델 고유 식별자
} TfLiteGpuDelegateOptionsV2;
```

### 추론 모드

| 상수 | 설명 |
|-----|-----|
| `TFLITE_GPU_INFERENCE_PREFERENCE_FAST_SINGLE_ANSWER` | 단일 추론 최적화 (낮은 초기화 지연) |
| `TFLITE_GPU_INFERENCE_PREFERENCE_SUSTAINED_SPEED` | 반복 추론 최적화 |
| `TFLITE_GPU_INFERENCE_PREFERENCE_BALANCED` | 균형 |

### 우선순위

| 상수 | 설명 |
|-----|-----|
| `TFLITE_GPU_INFERENCE_PRIORITY_AUTO` | 자동 |
| `TFLITE_GPU_INFERENCE_PRIORITY_MAX_PRECISION` | FP32 정밀도 |
| `TFLITE_GPU_INFERENCE_PRIORITY_MIN_LATENCY` | 최소 지연 |
| `TFLITE_GPU_INFERENCE_PRIORITY_MIN_MEMORY_USAGE` | 최소 메모리 |

### 실험적 플래그

| 플래그 | 설명 |
|-------|-----|
| `TFLITE_GPU_EXPERIMENTAL_FLAGS_ENABLE_QUANT` | 양자화 모델 지원 (기본 ON) |
| `TFLITE_GPU_EXPERIMENTAL_FLAGS_CL_ONLY` | OpenCL 강제 |
| `TFLITE_GPU_EXPERIMENTAL_FLAGS_GL_ONLY` | OpenGL 강제 |
| `TFLITE_GPU_EXPERIMENTAL_FLAGS_ENABLE_SERIALIZATION` | GPU 커널 캐시 활성화 |

### 비동기 (Android)

```c
TfLiteDelegate* TfLiteGpuDelegateV2CreateAsync(const TfLiteGpuDelegateOptionsV2*);
```

---

## CoreML Delegate (Apple)

헤더: `tensorflow/lite/delegates/coreml/coreml_delegate.h`

### Options 구조체

```c
typedef struct {
  TfLiteCoreMlDelegateEnabledDevices enabled_devices;
  int coreml_version;              // 2 또는 3
  int max_delegated_partitions;    // 0 = 전부
  int min_nodes_per_partition;     // 기본: 2
} TfLiteCoreMlDelegateOptions;
```

### 디바이스 모드

| 모드 | 설명 |
|-----|-----|
| `TfLiteCoreMlDelegateDevicesWithNeuralEngine` | ANE가 있을 때만 생성 |
| `TfLiteCoreMlDelegateAllDevices` | 항상 생성 |

CoreML v3는 더 많은 연산자를 지원하고 입력 랭크 제약이 완화됨.

---

## NNAPI Delegate (Android)

헤더: `tensorflow/lite/delegates/nnapi/nnapi_delegate.h`

### Options 상세

```cpp
struct Options {
  enum ExecutionPreference {
    kUndefined = -1,
    kLowPower = 0,           // 전력 최소화
    kFastSingleAnswer = 1,   // 단일 추론 지연 최소화
    kSustainedSpeed = 2      // 반복 추론 처리량 최적화
  };

  ExecutionPreference execution_preference;
  const char* accelerator_name;        // 특정 디바이스 지정 (nullptr = 자동)
  const char* cache_dir;               // 컴파일 캐시 디렉토리
  const char* model_token;             // 캐시 고유 키
  bool disallow_nnapi_cpu;             // CPU 폴백 금지 (기본: true)
  int max_number_delegated_partitions; // 최대 파티션 (기본: 3)
  bool allow_fp16;                     // FP32→FP16 변환 허용
  bool allow_dynamic_dimensions;       // 동적 텐서 지원
  bool use_burst_computation;          // Burst 모드 (반복 추론)
  uint32_t max_execution_cache_size;   // 실행 캐시 (기본: 4)

  // 타임아웃 (ns)
  uint64_t max_compilation_timeout_duration_ns;
  uint64_t max_execution_timeout_duration_ns;
  uint64_t max_execution_loop_timeout_duration_ns;
};
```

### 메모리 등록 (고급)

```cpp
TfLiteBufferHandle RegisterNnapiMemory(
    ANeuralNetworksMemory* memory,
    CopyToHostTensorFnPtr callback,
    void* callback_context);
```

### 인트로스펙션

```cpp
static const Options GetOptions(TfLiteDelegate*);
int GetNnApiErrno();  // 마지막 NNAPI 에러 코드
```

---

## External Delegate (커스텀 공유 라이브러리)

헤더: `tensorflow/lite/delegates/external/external_delegate.h`

```c
#define kExternalDelegateMaxOptions 256

typedef struct TfLiteExternalDelegateOptions {
  const char* lib_path;                              // .so/.dylib 경로
  int count;
  const char* keys[kExternalDelegateMaxOptions];
  const char* values[kExternalDelegateMaxOptions];
} TfLiteExternalDelegateOptions;
```

공유 라이브러리가 export해야 하는 함수:
- `tflite_plugin_create_delegate(keys, values, num, error_fn)` → `TfLiteDelegate*`
- `tflite_plugin_destroy_delegate(delegate)`

---

## Stable Delegate (안정 ABI)

헤더: `tensorflow/lite/core/acceleration/configuration/c/stable_delegate.h`

```c
#define TFL_STABLE_DELEGATE_ABI_VERSION "1.0.0"

typedef struct TfLiteStableDelegate {
  const char* delegate_abi_version;
  const char* delegate_name;       // "vendor_name" (snake_case)
  const char* delegate_version;    // semver 2
  const TfLiteOpaqueDelegatePlugin* delegate_plugin;
} TfLiteStableDelegate;

typedef struct TfLiteOpaqueDelegatePlugin {
  TfLiteOpaqueDelegateStruct* (*create)(const void* tflite_settings);
  void (*destroy)(TfLiteOpaqueDelegateStruct*);
  int (*get_delegate_errno)(TfLiteOpaqueDelegateStruct*);
} TfLiteOpaqueDelegatePlugin;
```

Opaque 타입만 사용 → C++ ABI 비의존 → 공유 라이브러리로 안전하게 배포 가능.
예제: `delegates/utils/experimental/sample_stable_delegate/`
