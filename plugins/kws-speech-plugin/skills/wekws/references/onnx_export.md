# ONNX Export 상세 가이드

## export_onnx.py 내부 동작

wekws의 ONNX 변환은 PyTorch `torch.onnx.export()`를 사용하며,
스트리밍 추론을 위해 **캐시(cache) 입출력**을 포함한 동적 그래프를 익스포트한다.

### 변환 전 체크리스트
```python
# 모델이 causal=True로 학습되었는지 확인
grep "causal" conf/train.yaml
# → causal: true 이어야 스트리밍 가능

# 모델 파라미터 확인
python -c "
import torch
ckpt = torch.load('exp/avg.pt', map_location='cpu')
print(ckpt['configs'])
"
```

### 변환 명령 (전체 옵션)
```bash
python wekws/bin/export_onnx.py \
  --config exp/mdtc/train.yaml \
  --checkpoint exp/mdtc/avg.pt \
  --cmvn data/train/cmvn.pt \
  --onnx_model exp/mdtc/kws.onnx \
  --chunk_size 16 \       # 청크당 프레임 수
  --num_left_chunks 4 \   # 왼쪽 컨텍스트 청크 수 (MDTC)
  --output_size 256       # hidden dim
```

### Dynamic Axes 설정
```python
# export_onnx.py 내부 - 동적 배치/시간 축
dynamic_axes = {
    'feats':     {0: 'batch', 1: 'time'},
    'cache_in':  {1: 'batch'},
    'logits':    {0: 'batch', 1: 'time'},
    'cache_out': {1: 'batch'},
}
```

---

## ONNX 모델 검증

### 기본 검증
```python
import onnx
import onnxruntime as ort
import numpy as np

# 모델 로드 및 구조 확인
model = onnx.load("exp/kws.onnx")
onnx.checker.check_model(model)

# 입출력 노드 확인
sess = ort.InferenceSession("exp/kws.onnx")
print("Inputs:", [(i.name, i.shape) for i in sess.get_inputs()])
print("Outputs:", [(o.name, o.shape) for o in sess.get_outputs()])
```

### PyTorch vs ONNX 출력 비교
```python
import torch
import numpy as np
import onnxruntime as ort

# 더미 입력 (batch=1, time=16, feat=80)
feats = np.random.randn(1, 16, 80).astype(np.float32)
cache = np.zeros((num_layers, 1, hidden_dim), dtype=np.float32)

# ONNX 추론
sess = ort.InferenceSession("kws.onnx")
onnx_out = sess.run(None, {'feats': feats, 'cache_in': cache})

# 최대 절댓값 차이 확인 (< 1e-5 이면 OK)
print("Max diff:", np.max(np.abs(torch_out - onnx_out[0])))
```

---

## INT8 양자화

### ONNX Runtime 동적 양자화 (권장 - 간단)
```python
from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    model_input="exp/kws.onnx",
    model_output="exp/kws_int8.onnx",
    weight_type=QuantType.QInt8,
    optimize_model=True,
)
```

### 정적 양자화 (더 정확, 캘리브레이션 필요)
```python
from onnxruntime.quantization import quantize_static, CalibrationDataReader

class KwsCalibrationReader(CalibrationDataReader):
    def __init__(self, data_list, num_samples=100):
        self.data = self._load(data_list, num_samples)
        self.iter = iter(self.data)

    def get_next(self):
        return next(self.iter, None)

quantize_static(
    model_input="exp/kws.onnx",
    model_output="exp/kws_static_int8.onnx",
    calibration_data_reader=KwsCalibrationReader("data/train/data.list"),
)
```

### 양자화 후 성능 비교
```bash
# 크기 비교
ls -lh exp/kws*.onnx

# 속도 벤치마크 (onnxruntime_perf_test)
onnxruntime_perf_test -m exp/kws.onnx -e cpu -r 1000
onnxruntime_perf_test -m exp/kws_int8.onnx -e cpu -r 1000
```

---

## Android용 ONNX 모델 최적화

### ONNX → ORT 형식 변환 (Android 권장)
```bash
# onnxruntime mobile 패키지 필요
python -m onnxruntime.tools.convert_onnx_models_to_ort \
  --optimization_style Fixed \
  exp/kws.onnx

# 결과: exp/kws.ort (더 빠른 로딩, 작은 크기)
```

### NNAPI 가속 활성화 (Android)
```cpp
// C++ 코드에서 NNAPI provider 설정
Ort::SessionOptions session_options;
uint32_t nnapi_flags = NNAPI_FLAG_USE_FP16;
OrtSessionOptionsAppendExecutionProvider_Nnapi(
    session_options, nnapi_flags);
```
