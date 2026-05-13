# C++ 스트리밍 디코더 개발 가이드

## 목표 아키텍처

온디바이스(Android/ARM) 경량 C++ 스트리밍 KWS 디코더:
- ONNX Runtime C++ API 사용
- kaldi-native-fbank 또는 자체 구현 FBANK
- 최소 의존성, 헤더 전용 구성 가능

---

## 기존 runtime 분석

### `runtime/core/kws/keyword_spotting.h` 핵심 구조
```cpp
class KeywordSpotting {
public:
    KeywordSpotting(const std::string& onnx_path,
                    const std::string& cmvn_path,
                    float threshold = 0.7f,
                    int chunk_size = 16);

    // 스트리밍 처리 메인 함수
    bool AcceptWaveform(const float* data, int len);

    // 검출 결과 조회
    bool GetResult(int* keyword_idx, float* score);

    // 상태 초기화
    void Reset();

private:
    // ONNX Runtime
    Ort::Env env_;
    Ort::Session session_{nullptr};
    Ort::SessionOptions session_options_;

    // CMVN 파라미터
    std::vector<float> cmvn_mean_;
    std::vector<float> cmvn_istd_;

    // 오디오 버퍼
    std::vector<float> audio_buffer_;

    // ONNX 캐시 상태 (MDTC의 경우 convolution cache)
    std::vector<float> cache_;
    std::vector<int64_t> cache_shape_;

    // 후처리
    int smooth_window_;
    std::deque<std::vector<float>> score_history_;
    int cooldown_counter_;
    float threshold_;
};
```

---

## 경량 C++ 디코더 구현 템플릿

### 디렉토리 구조
```
kws_decoder/
├── CMakeLists.txt
├── include/
│   ├── kws_decoder.h         # 메인 헤더
│   ├── fbank_extractor.h     # FBANK 추출
│   └── cmvn_normalizer.h     # CMVN 정규화
├── src/
│   ├── kws_decoder.cc
│   ├── fbank_extractor.cc
│   └── cmvn_normalizer.cc
└── test/
    └── test_kws.cc
```

### kws_decoder.h
```cpp
#pragma once
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include <deque>

// 전방 선언 (ONNX Runtime 헤더 최소화)
namespace Ort { class Session; class Env; }

namespace kws {

struct DetectionResult {
    bool detected;
    int keyword_idx;
    float score;
    int64_t timestamp_ms;  // 검출 시각
};

class KwsDecoder {
public:
    struct Config {
        std::string onnx_model_path;
        std::string cmvn_path;       // cmvn 파라미터 파일
        int sample_rate = 16000;
        int num_mel_bins = 80;
        int chunk_frames = 16;       // 추론 단위 프레임 수
        float threshold = 0.7f;
        int smooth_window = 10;
        int cooldown_frames = 30;
        int num_threads = 1;
        bool use_nnapi = false;      // Android NNAPI
    };

    explicit KwsDecoder(const Config& config);
    ~KwsDecoder();

    // 오디오 청크 입력 (int16 PCM)
    DetectionResult ProcessChunk(const int16_t* samples, int num_samples);

    // float32 PCM 버전
    DetectionResult ProcessChunk(const float* samples, int num_samples);

    // 상태 초기화
    void Reset();

    // 현재 설정 조회
    const Config& GetConfig() const { return config_; }

private:
    void InitOnnxSession();
    void LoadCmvn(const std::string& cmvn_path);
    std::vector<float> ExtractFbank(const float* samples, int num_samples);
    void ApplyCmvn(std::vector<float>& feats);
    DetectionResult RunInference(const std::vector<float>& feats);
    float GetSmoothedScore(int kw_idx);

    Config config_;

    // ONNX Runtime (PImpl로 헤더 의존성 최소화)
    struct OnnxImpl;
    std::unique_ptr<OnnxImpl> onnx_;

    // CMVN
    std::vector<float> cmvn_mean_;
    std::vector<float> cmvn_istd_;

    // 캐시 상태 (모델 레이어별)
    std::vector<float> cache_data_;
    std::vector<int64_t> cache_shape_;

    // Smoothing
    std::deque<std::vector<float>> score_history_;

    // Cooldown
    int cooldown_counter_ = 0;

    // 타이밍
    int64_t processed_samples_ = 0;
};

}  // namespace kws
```

### CMakeLists.txt (온디바이스 빌드)
```cmake
cmake_minimum_required(VERSION 3.18)
project(kws_decoder CXX)

set(CMAKE_CXX_STANDARD 17)

# ONNX Runtime 경로 (Android NDK 빌드 시 ABI별 설정)
set(ORT_ROOT "${CMAKE_SOURCE_DIR}/third_party/onnxruntime")

find_library(ORT_LIB onnxruntime
    PATHS ${ORT_ROOT}/lib
    NO_DEFAULT_PATH
)

add_library(kws_decoder SHARED
    src/kws_decoder.cc
    src/fbank_extractor.cc
    src/cmvn_normalizer.cc
)

target_include_directories(kws_decoder PUBLIC
    include/
    ${ORT_ROOT}/include/
    third_party/kaldi-native-fbank/
)

target_link_libraries(kws_decoder
    ${ORT_LIB}
)

# Android 전용 설정
if(ANDROID)
    target_link_libraries(kws_decoder log)

    # NNAPI 지원
    if(ANDROID_PLATFORM_LEVEL GREATER_EQUAL 27)
        target_link_libraries(kws_decoder neuralnetworks)
        target_compile_definitions(kws_decoder PRIVATE ENABLE_NNAPI=1)
    endif()
endif()
```

---

## FBANK 추출 (C++ 경량 구현)

### 옵션 1: kaldi-native-fbank (권장)
```cpp
#include "kaldi-native-fbank/csrc/online-feature.h"

class FbankExtractor {
public:
    FbankExtractor(int sample_rate, int num_mel_bins) {
        knf::FbankOptions opts;
        opts.frame_opts.samp_freq = sample_rate;
        opts.frame_opts.frame_length_ms = 25.0f;
        opts.frame_opts.frame_shift_ms = 10.0f;
        opts.frame_opts.dither = 0.0f;
        opts.mel_opts.num_bins = num_mel_bins;
        fbank_ = std::make_unique<knf::OnlineFbank>(opts);
    }

    // 스트리밍 방식으로 샘플 추가
    void AcceptWaveform(float sample_rate, const float* data, int n) {
        fbank_->AcceptWaveform(sample_rate, data, n);
    }

    // 준비된 프레임 수
    int NumFramesReady() const {
        return fbank_->NumFramesReady();
    }

    // 프레임 추출
    std::vector<float> GetFrame(int frame_idx) {
        std::vector<float> frame(fbank_->Dim());
        fbank_->GetFrame(frame_idx, &frame);
        return frame;
    }

private:
    std::unique_ptr<knf::OnlineFbank> fbank_;
};
```

### 옵션 2: 자체 구현 (최소 의존성)
```cpp
// STFT + Mel filterbank 직접 구현
// kiss_fft 등 경량 FFT 라이브러리 사용 가능
// 참고: wekws/wekws/utils/fbank.py 를 C++로 포팅
```

---

## ONNX Runtime 세션 관리

### 온디바이스 최적화 설정
```cpp
#include "onnxruntime_cxx_api.h"

void KwsDecoder::InitOnnxSession() {
    auto& env = GetOrtEnv();  // 프로세스당 하나
    Ort::SessionOptions opts;

    // 쓰레드 설정
    opts.SetIntraOpNumThreads(config_.num_threads);
    opts.SetInterOpNumThreads(1);

    // 그래프 최적화 (온디바이스에서는 ORT_ENABLE_BASIC 권장)
    opts.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

    // 메모리 최적화
    opts.EnableMemPattern();
    opts.EnableCpuMemArena();

#ifdef ENABLE_NNAPI
    // Android NNAPI 가속
    if (config_.use_nnapi) {
        uint32_t nnapi_flags = NNAPI_FLAG_USE_FP16 | NNAPI_FLAG_CPU_DISABLED;
        OrtSessionOptionsAppendExecutionProvider_Nnapi(opts, nnapi_flags);
    }
#endif

    session_ = Ort::Session(env, config_.onnx_model_path.c_str(), opts);

    // 캐시 입력 크기 파악
    auto cache_info = session_.GetInputTypeInfo(1);  // cache_in
    auto cache_shape = cache_info.GetTensorTypeAndShapeInfo().GetShape();
    // cache_shape: [num_layers, batch, hidden_dim]
    cache_shape_ = cache_shape;
    cache_data_.assign(cache_shape[0] * 1 * cache_shape[2], 0.0f);
}
```

### 스트리밍 추론 실행
```cpp
DetectionResult KwsDecoder::RunInference(const std::vector<float>& feats) {
    auto memory_info = Ort::MemoryInfo::CreateCpu(
        OrtArenaAllocator, OrtMemTypeDefault);

    // feats shape: [1, T, feat_dim]
    int T = feats.size() / config_.num_mel_bins;
    std::vector<int64_t> feats_shape = {1, T, config_.num_mel_bins};
    std::vector<int64_t> cache_shape = {
        cache_shape_[0], 1, cache_shape_[2]
    };

    std::vector<Ort::Value> inputs;
    inputs.push_back(Ort::Value::CreateTensor<float>(
        memory_info, const_cast<float*>(feats.data()),
        feats.size(), feats_shape.data(), feats_shape.size()));
    inputs.push_back(Ort::Value::CreateTensor<float>(
        memory_info, cache_data_.data(),
        cache_data_.size(), cache_shape.data(), cache_shape.size()));

    const char* input_names[] = {"feats", "cache_in"};
    const char* output_names[] = {"logits", "cache_out"};

    auto outputs = session_.Run(
        Ort::RunOptions{nullptr},
        input_names, inputs.data(), 2,
        output_names, 2);

    // 캐시 업데이트
    auto* cache_out = outputs[1].GetTensorMutableData<float>();
    std::copy(cache_out, cache_out + cache_data_.size(), cache_data_.begin());

    // logits: [1, T, num_keywords] → 마지막 프레임
    auto* logits = outputs[0].GetTensorData<float>();
    auto logits_shape = outputs[0].GetTensorTypeAndShapeInfo().GetShape();
    int num_kw = logits_shape[2];
    int last_frame_offset = (T - 1) * num_kw;

    // Smoothing 업데이트
    std::vector<float> frame_scores(logits + last_frame_offset,
                                     logits + last_frame_offset + num_kw);
    score_history_.push_back(frame_scores);
    if ((int)score_history_.size() > config_.smooth_window)
        score_history_.pop_front();

    // Cooldown 처리
    DetectionResult result{false, -1, 0.0f, processed_samples_ * 1000 / config_.sample_rate};
    if (cooldown_counter_ > 0) {
        cooldown_counter_--;
        return result;
    }

    // 임계값 판정
    for (int i = 0; i < num_kw; i++) {
        float avg = GetSmoothedScore(i);
        if (avg >= config_.threshold) {
            result.detected = true;
            result.keyword_idx = i;
            result.score = avg;
            cooldown_counter_ = config_.cooldown_frames;
            break;
        }
    }
    return result;
}
```

---

## Android JNI 통합

### JNI 래퍼 (KwsJni.cc)
```cpp
#include <jni.h>
#include "kws_decoder.h"

extern "C" {

JNIEXPORT jlong JNICALL
Java_com_kt_kws_KwsDecoder_nativeCreate(
    JNIEnv* env, jclass, jstring onnx_path, jstring cmvn_path,
    jfloat threshold) {

    const char* onnx = env->GetStringUTFChars(onnx_path, nullptr);
    const char* cmvn = env->GetStringUTFChars(cmvn_path, nullptr);

    kws::KwsDecoder::Config config;
    config.onnx_model_path = onnx;
    config.cmvn_path = cmvn;
    config.threshold = threshold;
    config.use_nnapi = true;

    env->ReleaseStringUTFChars(onnx_path, onnx);
    env->ReleaseStringUTFChars(cmvn_path, cmvn);

    return reinterpret_cast<jlong>(new kws::KwsDecoder(config));
}

JNIEXPORT jfloatArray JNICALL
Java_com_kt_kws_KwsDecoder_nativeProcessChunk(
    JNIEnv* env, jclass, jlong handle,
    jshortArray samples, jint num_samples) {

    auto* decoder = reinterpret_cast<kws::KwsDecoder*>(handle);
    jshort* data = env->GetShortArrayElements(samples, nullptr);

    auto result = decoder->ProcessChunk(
        reinterpret_cast<const int16_t*>(data), num_samples);

    env->ReleaseShortArrayElements(samples, data, JNI_ABORT);

    // 결과 반환: [detected(0/1), keyword_idx, score, timestamp_ms]
    jfloatArray ret = env->NewFloatArray(4);
    jfloat buf[4] = {
        result.detected ? 1.0f : 0.0f,
        (float)result.keyword_idx,
        result.score,
        (float)result.timestamp_ms
    };
    env->SetFloatArrayRegion(ret, 0, 4, buf);
    return ret;
}

JNIEXPORT void JNICALL
Java_com_kt_kws_KwsDecoder_nativeReset(
    JNIEnv* env, jclass, jlong handle) {
    reinterpret_cast<kws::KwsDecoder*>(handle)->Reset();
}

JNIEXPORT void JNICALL
Java_com_kt_kws_KwsDecoder_nativeDestroy(
    JNIEnv* env, jclass, jlong handle) {
    delete reinterpret_cast<kws::KwsDecoder*>(handle);
}

}  // extern "C"
```

### Kotlin 래퍼
```kotlin
class KwsDecoder(onnxPath: String, cmvnPath: String, threshold: Float = 0.7f) {
    private val handle: Long

    init {
        handle = nativeCreate(onnxPath, cmvnPath, threshold)
    }

    fun processChunk(samples: ShortArray): DetectionResult {
        val raw = nativeProcessChunk(handle, samples, samples.size)
        return DetectionResult(
            detected = raw[0] > 0.5f,
            keywordIdx = raw[1].toInt(),
            score = raw[2],
            timestampMs = raw[3].toLong()
        )
    }

    fun reset() = nativeReset(handle)

    fun close() = nativeDestroy(handle)

    data class DetectionResult(
        val detected: Boolean,
        val keywordIdx: Int,
        val score: Float,
        val timestampMs: Long,
    )

    private external fun nativeCreate(onnxPath: String, cmvnPath: String, threshold: Float): Long
    private external fun nativeProcessChunk(handle: Long, samples: ShortArray, n: Int): FloatArray
    private external fun nativeReset(handle: Long)
    private external fun nativeDestroy(handle: Long)

    companion object {
        init { System.loadLibrary("kws_decoder") }
    }
}
```

---

## 성능 벤치마크 타깃 (ARM Cortex-A55 기준)

| 모델 | 파라미터 | Float32 RTF | INT8 RTF | 메모리 |
|------|----------|-------------|----------|--------|
| MDTC-small | ~100K | ~0.05 | ~0.02 | ~5MB |
| MDTC-base  | ~400K | ~0.15 | ~0.06 | ~15MB |

RTF < 0.1 이면 실시간 처리 가능 (여유 있음)

---

## 빌드 및 테스트

```bash
# Host 빌드 (개발/테스트)
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4

# Android 크로스 컴파일
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a \
  -DANDROID_PLATFORM=android-26 \
  -DCMAKE_BUILD_TYPE=Release

# 실행 테스트
./test/test_kws --model kws.onnx --cmvn cmvn.bin --wav test.wav
```
