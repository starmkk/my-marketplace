# 스트리밍 추론 상세 가이드

## 스트리밍 처리 전체 흐름

```
마이크/파일 → [오디오 버퍼] → [FBANK 추출] → [CMVN 정규화]
    → [ONNX 추론 + 캐시] → [Posterior Smoothing] → [임계값 판정] → [검출 이벤트]
```

---

## 특징 추출 (FBANK)

### 파라미터 (wekws 기본값)
```yaml
sample_rate: 16000      # 샘플링 레이트
num_mel_bins: 80        # Mel 필터뱅크 수
frame_length: 25        # 프레임 길이 (ms) = 400 샘플
frame_shift: 10         # 프레임 이동 (ms) = 160 샘플
low_freq: 20            # 최저 주파수 (Hz)
high_freq: 8000         # 최고 주파수 (Hz)
dither: 0.0             # 디더링 (학습 시만)
```

### chunk 단위 처리
```
chunk_size = 10ms → 160 샘플 → 1 FBANK 프레임 생성
chunk_size = 160ms → 16 FBANK 프레임 → MDTC에 입력
```

### Python 스트리밍 FBANK 추출 예시
```python
import torchaudio
import torch

def compute_fbank_streaming(wav_chunk, sample_rate=16000):
    """청크 단위 FBANK 계산"""
    transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=sample_rate,
        n_mels=80,
        win_length=400,
        hop_length=160,
        f_min=20,
        f_max=8000,
    )
    feats = transform(wav_chunk)  # [1, 80, T]
    feats = feats.squeeze(0).T    # [T, 80]
    return feats
```

---

## CMVN 정규화

### cmvn.pt 파일 구조
```python
cmvn = torch.load('data/cmvn.pt')
# cmvn['mean']  : shape [feat_dim]  - 전역 평균
# cmvn['istd']  : shape [feat_dim]  - 전역 역표준편차
```

### 적용
```python
def apply_cmvn(feats, mean, istd):
    return (feats - mean) * istd
```

---

## ONNX 스트리밍 추론 상세

### 캐시 초기화 및 관리
```python
import numpy as np
import onnxruntime as ort

class WekwsStreamingDecoder:
    def __init__(self, onnx_path, cmvn_mean, cmvn_istd,
                 num_keywords=1, threshold=0.7):
        self.sess = ort.InferenceSession(
            onnx_path,
            providers=['CPUExecutionProvider']
        )
        self.mean = cmvn_mean
        self.istd = cmvn_istd
        self.threshold = threshold

        # 입출력 이름 확인
        self.input_names = [i.name for i in self.sess.get_inputs()]
        # 보통: ['feats', 'cache_in']

        # 캐시 크기는 모델에서 추출
        cache_shape = self.sess.get_inputs()[1].shape
        # cache_in shape: [num_layers, batch=1, hidden_dim] (MDTC의 경우)
        self.cache = np.zeros(
            [cache_shape[0], 1, cache_shape[2]], dtype=np.float32
        )

        # Smoothing을 위한 sliding window
        self.smooth_window = 10
        self.score_buffer = np.zeros((self.smooth_window, num_keywords))
        self.buffer_idx = 0

        # Cooldown (검출 후 억제)
        self.cooldown_frames = 50
        self.cooldown_counter = 0

    def process_chunk(self, feats_chunk):
        """
        feats_chunk: np.ndarray [T, feat_dim] - FBANK + CMVN 적용 후
        Returns: (detected: bool, keyword_idx: int, score: float)
        """
        # ONNX 추론
        inputs = {
            'feats': feats_chunk[np.newaxis],  # [1, T, feat_dim]
            'cache_in': self.cache,
        }
        outputs = self.sess.run(None, inputs)
        logits = outputs[0]      # [1, T, num_keywords]
        self.cache = outputs[1]  # 캐시 업데이트

        # 마지막 프레임의 posterior
        scores = logits[0, -1, :]  # [num_keywords]

        # Smoothing window 업데이트
        self.score_buffer[self.buffer_idx] = scores
        self.buffer_idx = (self.buffer_idx + 1) % self.smooth_window
        smoothed = self.score_buffer.mean(axis=0)

        # Cooldown 처리
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            return False, -1, 0.0

        # 임계값 판정
        max_idx = np.argmax(smoothed)
        max_score = smoothed[max_idx]
        if max_score >= self.threshold:
            self.cooldown_counter = self.cooldown_frames
            return True, max_idx, float(max_score)

        return False, -1, float(max_score)

    def reset(self):
        """상태 초기화 (새 발화 시작 시)"""
        self.cache = np.zeros_like(self.cache)
        self.score_buffer[:] = 0
        self.cooldown_counter = 0
```

---

## 후처리 알고리즘

### 1. Smoothing (평활화)
```python
# Exponential Moving Average (단순하고 메모리 효율적)
ema_score = alpha * new_score + (1 - alpha) * ema_score
# alpha = 0.3 ~ 0.5 권장

# Sliding Window Mean (더 안정적)
window = deque(maxlen=10)
window.append(new_score)
smoothed = np.mean(window)
```

### 2. 임계값 조정 가이드
| 시나리오 | FA/h 목표 | 권장 threshold |
|----------|-----------|----------------|
| 민감한 환경 (조용한 방) | ≤ 0.5 | 0.7 ~ 0.8 |
| 일반 환경 | ≤ 1.0 | 0.5 ~ 0.7 |
| 노이즈 많은 환경 | 유연 | 0.4 ~ 0.6 |

### 3. Cooldown (억제 구간)
```python
# 한 번 검출 후 N 프레임 동안 재검출 억제
# 이유: 단일 발화가 여러 번 검출되는 것 방지
COOLDOWN_FRAMES = 30  # 300ms (10ms 프레임 기준)
```

---

## 실시간 마이크 스트리밍 테스트 (Python)

```python
import pyaudio
import numpy as np
import torch

CHUNK = 160          # 10ms @ 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

decoder = WekwsStreamingDecoder(
    onnx_path="exp/kws.onnx",
    cmvn_mean=cmvn['mean'].numpy(),
    cmvn_istd=cmvn['istd'].numpy(),
    threshold=0.7,
)

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True, frames_per_buffer=CHUNK)

print("Listening... (Ctrl+C to stop)")
audio_buffer = np.array([], dtype=np.int16)

while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
    audio_buffer = np.append(audio_buffer, samples.astype(np.int16))

    # 160ms 분량 쌓이면 추론
    if len(audio_buffer) >= 2560:  # 160ms
        chunk = audio_buffer[:2560].astype(np.float32) / 32768.0
        audio_buffer = audio_buffer[160:]  # 10ms shift

        # FBANK 추출 + CMVN 적용 후 decoder.process_chunk() 호출
        detected, kw_idx, score = decoder.process_chunk(fbank_chunk)
        if detected:
            print(f"[DETECTED] keyword={kw_idx}, score={score:.3f}")
```

---

## 평가 스크립트

```bash
# 파일 기반 스트리밍 평가
python wekws/bin/stream_kws.py \
  --onnx exp/kws.onnx \
  --cmvn data/train/cmvn.pt \
  --test_data data/test/data.list \
  --threshold 0.7 \
  --chunk_size 16

# DET curve (임계값 vs FRR/FA 트레이드오프)
python tools/compute_det.py \
  --score_file exp/scores.txt \
  --output exp/det_curve.png
```
