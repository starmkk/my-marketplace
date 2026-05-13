---
name: wekws
description: >
  WeKws (wenet-e2e/wekws) Production First End-to-End Keyword Spotting Toolkit 레퍼런스 스킬.
  wekws 소스코드를 읽거나 수정할 때, 모델(MDTC/TCN/RNN) 구조를 분석할 때, 학습 파이프라인을
  이해하거나 수정할 때, PyTorch 모델을 ONNX로 변환할 때, C++ 스트리밍 디코더를 개발하거나
  분석할 때, 온디바이스(Android/ARM) 배포 작업을 할 때 반드시 이 스킬을 참조하라.
  wekws, keyword spotting, KWS, wake word, 웨이크워드, MDTC, streaming decoder,
  ONNX runtime, on-device inference, causal convolution 등의 키워드가 등장하면 즉시 트리거한다.
---

# WeKws Skill — Production First End-to-End Keyword Spotting

## 개요

WeKws는 IoT/온디바이스 환경을 위한 **소형(small-footprint) E2E 키워드 스포팅 툴킷**이다.
논문: ICASSP 2023 "WeKws: A Production First Small-Footprint End-to-End KWS Toolkit"

### 핵심 특징
- **Alignment-free**: 강제 정렬(force alignment) 없이 max-pooling loss 기반 E2E 학습
- **스트리밍**: causal convolution으로 프레임 단위 실시간 처리 지원
- **경량**: PyTorch만 의존, MDTC 백본으로 파라미터 최소화
- **다중 플랫폼**: TorchScript/ONNX 익스포트 → x86, Android, Raspberry Pi 배포

---

## 레포지토리 구조

```
wekws/
├── wekws/              # Python 학습 패키지
│   ├── model/          # 모델 정의 (MDTC, TCN, RNN 등)
│   ├── dataset/        # 데이터 로딩 및 전처리
│   ├── loss/           # Max-pooling loss 구현
│   └── utils/          # 평가, 특징 추출 유틸리티
├── runtime/            # C++ 추론 런타임
│   ├── core/
│   │   ├── kws/        # keyword_spotting.h/.cc (핵심 디코더)
│   │   ├── frontend/   # 오디오 특징 추출 (FBANK)
│   │   └── utils/      # 공통 유틸리티
│   ├── android/        # Android JNI 래퍼
│   └── server/         # x86 서버 데모
├── examples/           # 데이터셋별 학습 스크립트
│   ├── hi_xiaowen/s0/  # Mobvoi 데이터셋 예제
│   ├── hey_snips/s0/   # Hey Snips 예제
│   └── google_speech_command/s0/  # GSC 예제
└── tools/              # ONNX 변환, 평가 등 유틸리티
```

---

## 모델 아키텍처

```
입력 FBANK → CMVN → Linear(dim) → Backbone → Binary Classifier(s)
```

### 레이어 설명
| 레이어 | 역할 |
|--------|------|
| CMVN | 전역 cepstral mean/variance 정규화 |
| Linear | 입력 차원 → 모델 내부 차원 매핑 |
| Backbone | 시계열 특징 추출 (RNN / TCN / **MDTC**) |
| Binary Classifier | 키워드별 독립 sigmoid 출력 (posterior prob.) |

### 백본 비교
| 백본 | 특징 | 추천 |
|------|------|------|
| RNN (GRU/LSTM) | 가장 단순, 스트리밍 자연스러움 | 베이스라인 |
| TCN | Temporal Conv, 병렬 학습 가능 | 중간 |
| **MDTC** | Multi-scale Depthwise Temporal Conv, 최고 성능/크기 비율 | **권장** |

### MDTC 구조
- DTC(Depthwise Temporal Convolution) 블록 스택
- 다양한 dilation으로 멀티스케일 컨텍스트 학습
- Depthwise separable conv → 파라미터 대폭 감소
- **causal convolution** → 미래 프레임 참조 없이 스트리밍 가능

---

## 학습 파이프라인

### 데이터 준비
```bash
# examples/hey_snips/s0/run.sh 참조
stage 1: 데이터 다운로드 및 정리
stage 2: wav.scp, label 파일 생성
stage 3: CMVN 통계 계산 (compute_cmvn_stats.py)
```

### 주요 설정 파일 (conf/train.yaml)
```yaml
model: mdtc           # 백본 선택: rnn | tcn | mdtc
num_keywords: 1       # 키워드 수
input_dim: 80         # FBANK 차원
hidden_dim: 256       # 모델 내부 차원
# MDTC 전용
num_layers: 3
num_stack: 4
kernel_size: 11
causal: true          # 스트리밍을 위해 반드시 true
```

### 학습 실행
```bash
python wekws/bin/train.py \
  --config conf/train.yaml \
  --train_data data/train/data.list \
  --cv_data data/dev/data.list \
  --cmvn data/train/cmvn.pt \
  --model_dir exp/mdtc/
```

---

## ONNX 변환 (★ 핵심)

자세한 내용: `references/onnx_export.md` 참조

### 빠른 변환 흐름
```bash
# 1. 최적 체크포인트 평균화 (optional)
python tools/average_model.py --src_path exp/ --dst_path exp/avg.pt --num 5

# 2. ONNX 익스포트
python wekws/bin/export_onnx.py \
  --config exp/train.yaml \
  --checkpoint exp/avg.pt \
  --cmvn data/cmvn.pt \
  --onnx_model exp/kws.onnx

# 3. INT8 양자화 (온디바이스 권장)
python tools/quantize_onnx.py \
  --input exp/kws.onnx \
  --output exp/kws_int8.onnx
```

### ONNX 모델 I/O 형태
```
입력:  feats      [batch, time, feat_dim]   # FBANK 특징
       cache_in   [num_layers, batch, ...]   # 이전 상태 캐시
출력:  logits     [batch, time, num_kw]      # 키워드 posterior
       cache_out  [num_layers, batch, ...]   # 갱신된 캐시
```

---

## 스트리밍 추론 처리 (★★ 핵심)

자세한 내용: `references/streaming_inference.md` 참조

### 스트리밍 원리
1. 오디오를 **chunk** 단위(예: 160 샘플 = 10ms)로 분할
2. FBANK 특징 추출 (각 프레임: 25ms window, 10ms shift)
3. CMVN 정규화
4. ONNX 모델 추론 (캐시 상태 유지)
5. posterior probability → 임계값 비교 → 검출 판정

### 후처리 (Post-processing)
- **Smoothing Window**: 연속된 N개 프레임 평균으로 스파이크 제거
- **Threshold**: 일반적으로 0.5~0.8 (FA와 FRR 균형)
- **Cooldown**: 한 번 검출 후 일정 프레임 동안 재검출 억제

---

## C++ 스트리밍 디코더 개발 가이드

자세한 내용: `references/cpp_decoder.md` 참조

### 기존 runtime 구조 (ONNX Runtime 기반)
```
runtime/core/kws/
├── keyword_spotting.h    # 메인 KWS 클래스
├── keyword_spotting.cc   # 구현
└── CMakeLists.txt

의존성:
- onnxruntime (공식 C++ API)
- kaldi-native-fbank (FBANK 특징 추출)
```

### 온디바이스 경량 C++ 디코더 설계 원칙
```
[AudioBuffer] → [FbankExtractor] → [CmvnNormalizer] → [OnnxSession] → [PostProcessor]
```

핵심 클래스:
- `StreamingBuffer`: 오디오 링버퍼, chunk 관리
- `FbankExtractor`: kaldi-native-fbank 래퍼
- `KwsOnnxModel`: ONNX Runtime 세션 + 캐시 상태
- `DetectionResult`: 검출 결과 구조체

---

## Pretrained 모델 활용

### 공개 모델 목록
| 데이터셋 | 키워드 | 링크 |
|----------|--------|------|
| Mobvoi | Hi Xiaowen / Ni Hao Wenwen | GitHub Releases |
| Hey Snips | hey snips | GitHub Releases |
| Google Speech Commands | 35 words | GitHub Releases |

### 모델 다운로드 후 ONNX 변환 체크리스트
1. `conf/train.yaml` 설정 파일 확인 (모델 구조 파라미터)
2. `data/cmvn.pt` CMVN 파일 확인
3. `export_onnx.py` 실행 시 `--causal true` 옵션 확인
4. ONNX 모델 입출력 노드 이름 확인: `tools/check_onnx.py`

---

## 평가 지표

- **FRR** (False Rejection Rate): 키워드를 놓친 비율 ↓
- **FA/h** (False Alarms per Hour): 시간당 오검출 수 ↓
- 일반적 목표: FA/h ≤ 0.5 조건에서 FRR 최소화

---

## 참조 파일 안내

| 파일 | 내용 |
|------|------|
| `references/onnx_export.md` | ONNX 변환 상세, 양자화, 검증 방법 |
| `references/streaming_inference.md` | 스트리밍 추론 상세, 후처리 알고리즘 |
| `references/cpp_decoder.md` | C++ 디코더 설계, 코드 템플릿, Android 통합 |

---

## 빠른 참조: 자주 쓰는 스크립트

```bash
# 학습
python wekws/bin/train.py --config conf/train.yaml ...

# 평가
python wekws/bin/score.py --test_data data/test/data.list ...

# ONNX 변환
python wekws/bin/export_onnx.py ...

# 스트리밍 Python 테스트
python wekws/bin/stream_kws.py --onnx exp/kws.onnx --wav test.wav

# 실시간 마이크 테스트 (runtime)
./runtime/server/x86/build/kws_main --onnx exp/kws.onnx --threshold 0.7
```
