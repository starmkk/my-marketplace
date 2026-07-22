---
name: tensorflow
description: "TensorFlow v2.21.0-rc0 및 TFLite 핵심 API/기능 레퍼런스. TFLite C/C++/Python API를 사용할 때, 모델 로딩/추론/양자화를 구현할 때, Delegate(XNNPACK/GPU/CoreML/NNAPI) 설정할 때, SavedModel을 .tflite로 변환할 때, SignatureRunner/AsyncRunner를 사용할 때, 프로파일링/벤치마크할 때, LiteRT.main 또는 LiteRT-LM.main과 연동할 때 이 스킬을 반드시 참조하라. tensorflow, tflite, litert, delegate, quantization, interpreter, converter 키워드에 반응한다."
---

# TensorFlow / TFLite 핵심 API 레퍼런스

소스 경로: `third_party/tensorflow/` (v2.21.0-rc0, C++20, Bazel 7.7.0)

---

## 1. 모델 로딩

### C++ — FlatBufferModel

```cpp
#include "tensorflow/lite/core/model_builder.h"

// 파일에서 로딩 (mmap 지원)
auto model = tflite::FlatBufferModel::BuildFromFile("model.tflite");

// 버퍼에서 로딩
auto model = tflite::FlatBufferModel::BuildFromBuffer(buf, size);

// 검증 포함 로딩
auto model = tflite::FlatBufferModel::VerifyAndBuildFromFile("model.tflite", verifier);
```

모델 인스턴스는 Interpreter보다 오래 살아야 한다. .tflite 파일은 FlatBuffer 포맷.

### C API

```c
#include "tensorflow/lite/c/c_api.h"

TfLiteModel* model = TfLiteModelCreateFromFile("model.tflite");
// 또는 버퍼에서
TfLiteModel* model = TfLiteModelCreate(buffer, size);
TfLiteModelDelete(model);
```

### Python

```python
interpreter = tf.lite.Interpreter(model_path="model.tflite")
# 또는 버퍼에서
interpreter = tf.lite.Interpreter(model_content=model_bytes)
```

---

## 2. 추론 (Inference)

### C++ 워크플로우

```cpp
#include "tensorflow/lite/core/interpreter.h"
#include "tensorflow/lite/core/kernels/register.h"
#include "tensorflow/lite/interpreter_builder.h"

// 1. Op Resolver 선택
tflite::ops::builtin::BuiltinOpResolver resolver;           // 전체 연산자
// tflite::ops::builtin::BuiltinOpResolverWithXNNPACK resolver; // XNNPACK 기본 활성화
// tflite::ops::builtin::BuiltinOpResolverWithoutDefaultDelegates resolver; // delegate 없이

// 2. Interpreter 빌드
tflite::InterpreterBuilder builder(*model, resolver);
builder.SetNumThreads(4);  // delegate 적용 전에 설정
std::unique_ptr<tflite::Interpreter> interpreter;
builder(&interpreter);

// 3. 텐서 할당
interpreter->AllocateTensors();

// 4. 입력 설정
float* input = interpreter->typed_input_tensor<float>(0);
memcpy(input, data, sizeof(float) * input_size);

// 5. 추론 실행
interpreter->Invoke();

// 6. 출력 읽기
float* output = interpreter->typed_output_tensor<float>(0);
```

### C API 워크플로우

```c
TfLiteInterpreterOptions* opts = TfLiteInterpreterOptionsCreate();
TfLiteInterpreterOptionsSetNumThreads(opts, 4);
TfLiteInterpreterOptionsAddDelegate(opts, delegate);  // 선택

TfLiteInterpreter* interp = TfLiteInterpreterCreate(model, opts);
TfLiteInterpreterAllocateTensors(interp);

// 입력
TfLiteTensor* input = TfLiteInterpreterGetInputTensor(interp, 0);
TfLiteTensorCopyFromBuffer(input, data, data_size);

// 추론
TfLiteInterpreterInvoke(interp);

// 출력
const TfLiteTensor* output = TfLiteInterpreterGetOutputTensor(interp, 0);
TfLiteTensorCopyToBuffer(output, result, result_size);

// 정리
TfLiteInterpreterDelete(interp);
TfLiteInterpreterOptionsDelete(opts);
```

### Python 워크플로우

```python
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()
output = interpreter.get_tensor(output_details[0]['index'])
```

---

## 3. SignatureRunner (Named I/O)

모델에 signature가 있으면 이름 기반으로 입출력 접근 가능.

### C++

```cpp
SignatureRunner* runner = interpreter->GetSignatureRunner("serving_default");
runner->AllocateTensors();

TfLiteTensor* input = runner->input_tensor("input_name");
// 데이터 설정...
runner->Invoke();
const TfLiteTensor* output = runner->output_tensor("output_name");
```

### C API

```c
TfLiteSignatureRunner* runner = TfLiteInterpreterGetSignatureRunner(interp, "serving_default");
TfLiteSignatureRunnerAllocateTensors(runner);
TfLiteTensor* input = TfLiteSignatureRunnerGetInputTensor(runner, "input_name");
TfLiteSignatureRunnerInvoke(runner);
const TfLiteTensor* output = TfLiteSignatureRunnerGetOutputTensor(runner, "output_name");
TfLiteSignatureRunnerDelete(runner);
```

### Python

```python
runner = interpreter.get_signature_runner("serving_default")
result = runner(input_name=input_data)  # dict 반환
```

---

## 4. 텐서 (Tensor)

### TfLiteTensor 구조체 (core/c/common.h)

| 필드 | 타입 | 설명 |
|-----|------|-----|
| `type` | `TfLiteType` | 데이터 타입 |
| `data` | `TfLitePtrUnion` | 데이터 포인터 |
| `dims` | `TfLiteIntArray*` | 차원 배열 |
| `bytes` | `size_t` | 총 바이트 크기 |
| `name` | `const char*` | 텐서 이름 |
| `quantization` | `TfLiteQuantization` | 양자화 파라미터 |
| `allocation_type` | enum | 메모리 할당 방식 |

### 데이터 타입 (TfLiteType)

| 상수 | 값 | 설명 |
|-----|---|-----|
| `kTfLiteFloat32` | 1 | 32비트 부동소수점 |
| `kTfLiteInt32` | 2 | 32비트 정수 |
| `kTfLiteUInt8` | 3 | 부호 없는 8비트 |
| `kTfLiteInt64` | 4 | 64비트 정수 |
| `kTfLiteString` | 5 | 문자열 |
| `kTfLiteBool` | 6 | 불리언 |
| `kTfLiteInt16` | 7 | 16비트 정수 |
| `kTfLiteInt8` | 9 | 부호 있는 8비트 (INT8 양자화) |
| `kTfLiteFloat16` | 10 | 반정밀도 부동소수점 |
| `kTfLiteBFloat16` | 19 | Brain Float 16 |
| `kTfLiteInt4` | 18 | 4비트 정수 |

### 메모리 할당 타입

| 타입 | 설명 |
|-----|-----|
| `kTfLiteMmapRo` | mmap 읽기전용 (가중치) |
| `kTfLiteArenaRw` | Arena 읽기/쓰기 |
| `kTfLiteArenaRwPersistent` | Arena 영구 보존 |
| `kTfLiteDynamic` | 동적 할당 |
| `kTfLiteCustom` | 사용자 정의 할당 |
| `kTfLiteNonCpu` | 비-CPU 메모리 (AHWB, GPU) |

---

## 5. Delegate 시스템

Delegate는 하드웨어 가속기에 연산을 위임하는 메커니즘. 우선순위: External > XNNPACK > GPU/Metal > NNAPI > Flex

### 5.1 XNNPACK (CPU 최적화, 기본 활성화)

```c
TfLiteXNNPackDelegateOptions opts = TfLiteXNNPackDelegateOptionsDefault();
opts.num_threads = 4;
opts.flags = TFLITE_XNNPACK_DELEGATE_FLAG_QS8 | TFLITE_XNNPACK_DELEGATE_FLAG_FORCE_FP16;
opts.weight_cache_file_path = "/path/to/cache";  // 반복 로딩 가속
TfLiteDelegate* delegate = TfLiteXNNPackDelegateCreate(&opts);
```

### 5.2 GPU Delegate (Metal/OpenCL/OpenGL)

```c
TfLiteGpuDelegateOptionsV2 opts = TfLiteGpuDelegateOptionsV2Default();
opts.is_precision_loss_allowed = 1;
opts.inference_preference = TFLITE_GPU_INFERENCE_PREFERENCE_SUSTAINED_SPEED;
TfLiteDelegate* delegate = TfLiteGpuDelegateV2Create(&opts);
```

### 5.3 CoreML (Apple ANE), 5.4 NNAPI (Android), 5.5 External, 5.6 Stable ABI

각 delegate의 상세 옵션, 플래그, 고급 기능은 `references/delegates.md` 참조.

---

## 6. 모델 변환 (Python)

### TFLiteConverter

```python
# Keras 모델에서 변환
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# SavedModel에서 변환
converter = tf.lite.TFLiteConverter.from_saved_model("./saved_model")

# ConcreteFunction에서 변환
converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete_func])
```

### 양자화 설정

```python
# 동적 범위 양자화 (가중치만, 가장 간단)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# 전체 정수 양자화 (가중치 + 활성화)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = lambda: (yield [sample] for sample in calibration_data)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

# FP16 양자화
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]

# Select TF Ops (호환성 우선)
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS,
    tf.lite.OpsSet.SELECT_TF_OPS  # 전체 TF 연산자 포함
]

tflite_model = converter.convert()
with open("model.tflite", "wb") as f:
    f.write(tflite_model)
```

### 양자화 모드 비교

| 모드 | 크기 감소 | 정확도 | 필요 데이터 | 속도 |
|-----|---------|-------|-----------|-----|
| 동적 범위 | ~4x | 약간 손실 | 불필요 | 빠름 |
| 전체 정수 (INT8) | ~4x | 약간 손실 | 대표 데이터셋 | 가장 빠름 |
| FP16 | ~2x | 거의 무손실 | 불필요 | 중간 |
| QAT | ~4x | 최소 손실 | 학습 필요 | 가장 빠름 |

양자화 수식: `real_value = scale * (quantized_value - zero_point)`

---

## 7. 프로파일링

### C++ Profiler API

```cpp
#include "tensorflow/lite/core/api/profiler.h"

// 이벤트 타입
Profiler::EventType::OPERATOR_INVOKE_EVENT       // 연산자 실행
Profiler::EventType::DELEGATE_OPERATOR_INVOKE_EVENT  // Delegate 연산자

// 매크로 사용
TFLITE_SCOPED_TAGGED_OPERATOR_PROFILE(profiler, "Conv2D", node_index);
```

### 메모리 사용량

```cpp
#include "tensorflow/lite/profiling/memory_info.h"

auto usage = MemoryUsage::GetMemoryUsage();
// usage.mem_footprint_kb         — RSS (KB)
// usage.total_allocated_bytes    — 총 힙 할당
// usage.in_use_allocated_bytes   — 사용 중 힙
```

### 벤치마크 도구

```bash
# 빌드 후 실행
benchmark_model --graph=model.tflite --num_threads=4 --warmup_runs=5 --num_runs=50
```

출력: 초기화 지연, 추론 시간 (min/max/mean/median), 메모리 사용량, 처리량(MB/s)

---

## 8. 비동기 추론 (Experimental)

```cpp
#include "tensorflow/lite/core/async/async_signature_runner.h"

auto* runner = interpreter->GetAsyncSignatureRunner("serving_default");
runner->PrepareBackends();

auto* task = runner->CreateTask();
// 버퍼 등록
runner->RegisterBuffer(kTfLiteIoTypeInput, &buffer, &attrs, &handle);
// 비동기 실행
runner->InvokeAsync(task);
// 대기
runner->Wait(task);
runner->Finish(task);
```

---

## 9. 멀티스레딩 & 취소

```cpp
// 스레드 수 설정 (InterpreterBuilder에서, delegate 적용 전)
builder.SetNumThreads(4);
// 또는 런타임에
interpreter->SetNumThreads(4);

// -1: 플랫폼 자동 감지, 0: 단일 스레드

// 추론 취소 (스레드 안전)
interpreter->Cancel();

// 콜백 기반 취소
interpreter->SetCancellationFunction(ctx, [](void* ctx) -> bool {
    return should_cancel;
});
```

---

## 10. 메모리 관리 (Arena)

TFLite는 Arena 기반 메모리 할당으로 텐서 메모리를 효율적으로 재사용.

```cpp
// InterpreterOptions로 대형 텐서 동적 할당 (1MB 이상)
options.OptimizeMemoryForLargeTensors(1 << 20);

// 비영구 메모리 해제/재할당
interpreter->ReleaseNonPersistentMemory();
// ... 다른 작업 ...
// AllocateTensors()로 재할당
```

Arena 정렬: 기본 64바이트. 텐서 간 메모리 공유로 피크 메모리 최소화.

---

## 11. 상태 코드 (TfLiteStatus)

| 코드 | 값 | 의미 |
|-----|---|-----|
| `kTfLiteOk` | 0 | 성공 |
| `kTfLiteError` | 1 | 일반 런타임 오류 |
| `kTfLiteDelegateError` | 2 | Delegate 오류 |
| `kTfLiteApplicationError` | 3 | Delegate 비호환 |
| `kTfLiteUnresolvedOps` | 7 | 미지원 연산자 |
| `kTfLiteCancelled` | 8 | 사용자 취소 |

---

## 12. 멀티플랫폼 지원

| 플랫폼 | API | 경로 |
|-------|-----|-----|
| C/C++ | Interpreter, FlatBufferModel | `lite/core/` |
| Python | tf.lite.Interpreter | `lite/python/` |
| Android (Java) | Java Interpreter + JNI | `lite/java/` |
| iOS (ObjC) | TFLInterpreter | `lite/objc/` |
| iOS (Swift) | TensorFlowLite module | `lite/swift/` |
| Embedded | TFLite Micro (순수 C) | `lite/micro/` |

---

## 13. 빌트인 연산자

373+ 빌트인 연산자 (`lite/kernels/`). 주요 카테고리:

- **활성화**: ReLU, Sigmoid, Tanh, Softmax, LogSoftmax
- **합성곱**: Conv2D, DepthwiseConv2D, TransposeConv
- **풀링**: MaxPool, AveragePool, L2Pool
- **행렬**: FullyConnected, BatchMatMul, Gather
- **정규화**: BatchNorm, LayerNorm, L2Normalize
- **형태 변환**: Reshape, Squeeze, ExpandDims, Transpose
- **양자화**: Quantize, Dequantize, FakeQuant
- **어텐션**: 내장 MultiHeadAttention (experimental)

Op Resolver를 통해 등록:
```cpp
// 전체 등록
tflite::ops::builtin::BuiltinOpResolver resolver;

// 커스텀 연산자 추가
resolver.AddCustom("MyCustomOp", &my_op_registration);
```

---

## 14. 핵심 헤더 경로 요약

| 기능 | 헤더 경로 |
|-----|---------|
| C API | `tensorflow/lite/c/c_api.h` |
| Opaque C API | `tensorflow/lite/core/c/c_api_opaque.h` |
| C++ Interpreter | `tensorflow/lite/core/interpreter.h` |
| 모델 빌더 | `tensorflow/lite/core/model_builder.h` |
| 공통 타입 | `tensorflow/lite/core/c/common.h` |
| Op Resolver | `tensorflow/lite/core/api/op_resolver.h` |
| 빌트인 등록 | `tensorflow/lite/core/kernels/register.h` |
| SignatureRunner | `tensorflow/lite/core/signature_runner.h` |
| XNNPACK | `tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h` |
| GPU | `tensorflow/lite/delegates/gpu/delegate.h` |
| CoreML | `tensorflow/lite/delegates/coreml/coreml_delegate.h` |
| NNAPI | `tensorflow/lite/delegates/nnapi/nnapi_delegate.h` |
| External | `tensorflow/lite/delegates/external/external_delegate.h` |
| Profiler | `tensorflow/lite/core/api/profiler.h` |
| Async | `tensorflow/lite/core/async/async_signature_runner.h` |

---

## 15. 빌드 (간략)

```bash
# CMake (macOS arm64)
cd third_party/tensorflow/ && bash run-build.sh
# 출력: ../tensorflow-build/libtensorflow-lite.a

# Bazel
bazel build //tensorflow/lite:framework
```

CMake 핵심 옵션: `-DTFLITE_ENABLE_XNNPACK=ON`, `-DCMAKE_OSX_ARCHITECTURES=arm64`, `-DCMAKE_CXX_STANDARD=20`

LiteRT.main/LiteRT-LM.main 호환: v2.21.0-rc0 기준. `TFLITE_ENABLE_INSTALL=OFF` 권장 (export set 충돌 방지).
