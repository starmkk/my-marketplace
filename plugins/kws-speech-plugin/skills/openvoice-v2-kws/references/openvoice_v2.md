# OpenVoice V2 API 가이드

출처:
- https://github.com/myshell-ai/OpenVoice
- https://huggingface.co/myshell-ai/OpenVoiceV2
- demo_part3.ipynb (공식 예제)

## 라이선스
**MIT License (2024년 4월부터)**. V1, V2 모두 상업 활용 가능.

## V2의 차별점 (V1 대비)
- Native multi-lingual 학습 (영/스/프/중/일/한)
- 더 공격적인 augmentation으로 robust
- Cross-lingual cloning 품질 향상

## 핵심 컴포넌트
| 컴포넌트 | 역할 |
|---|---|
| `ToneColorConverter` | base wav의 timbre를 target으로 변환 |
| `se_extractor.get_se()` | reference wav → speaker embedding |
| `MeloTTS` | base TTS (V2부터 권장 base speaker) |
| `base_speakers/ses/{lang}.pth` | 각 언어 base speaker의 source SE |

## 체크포인트 구조
설치 스크립트로 받는 `checkpoints_v2_0417.zip`을 풀면:
```
checkpoints_v2/
├── converter/
│   ├── checkpoint.pth        # ToneColorConverter 가중치
│   └── config.json
└── base_speakers/
    └── ses/
        ├── en-us.pth          # 영어 미국 base speaker SE
        ├── kr.pth             # 한국어 base speaker SE  ← 본 스킬에서 사용
        ├── jp.pth
        └── ...
```

## 표준 사용 패턴 (공식 demo_part3 기반)

```python
import torch
from openvoice.api import ToneColorConverter
from openvoice import se_extractor
from melo.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
ckpt_dir = "checkpoints_v2"

# 1) ToneColorConverter 로드
converter = ToneColorConverter(f"{ckpt_dir}/converter/config.json", device=device)
converter.load_ckpt(f"{ckpt_dir}/converter/checkpoint.pth")

# 2) source SE (base TTS speaker — 한국어)
src_se = torch.load(f"{ckpt_dir}/base_speakers/ses/kr.pth", map_location=device)

# 3) target SE (복제할 화자) — reference wav 한 번 인코딩
target_se, audio_name = se_extractor.get_se(
    "reference.wav", converter, vad=True
)

# 4) base TTS 생성 (MeloTTS-Korean)
tts = TTS(language="KR", device=device)
spk_id = tts.hps.data.spk2id["KR"]
tts.tts_to_file("오케이 케이티", spk_id, "tmp.wav", speed=1.2)

# 5) tone color conversion
converter.convert(
    audio_src_path="tmp.wav",
    src_se=src_se,
    tgt_se=target_se,
    output_path="cloned.wav",
    message="@MyShell"  # watermark
)
```

## Speaker embedding
- `se_extractor.get_se()`는 wav를 256차원 임베딩으로 인코딩 (`[1, 256, 1]` 형태).
- 한 번 추출하면 .pt로 저장하여 무한 재사용 가능. 이게 본 스킬의 효율성 핵심.
- VAD를 켜면 무음 구간 자동 제거 → 짧은 클립도 robust.

## Reference wav 권장 사양
| 항목 | 권장 | 비고 |
|---|---|---|
| 길이 | 5~15초 | 너무 길면 느려짐 |
| 화자 | 단일 | 여러 화자 섞이면 평균화됨 |
| 샘플레이트 | 16kHz 이상 | 자동 리샘플링되지만 손실 있음 |
| 잡음 | < -30dB SNR | 잡음 많으면 timbre가 잡음 톤으로 학습 |
| 포맷 | wav, mp3 모두 OK | 24-bit FLAC도 가능 |

## Watermark (`message` 인자)
공식 코드는 `message="@MyShell"`을 watermark로 박는다.
Tone color converter 출력에 imperceptible watermark가 인코딩되며, 추후 합성 음원의
출처 추적에 사용될 수 있다. 비활성화하려면 빈 문자열 `""`.
KWS 학습 데이터에는 무관하지만 알아둘 가치가 있음.

## Cross-lingual Voice Cloning
영어 reference로 한국어 합성, 또는 그 반대도 가능.
KWS에는 권장하지 않음 (발음 정확성 손실 위험). 같은 언어 reference 사용할 것.

## 알려진 이슈
1. **Mac MPS NaN** — 일부 케이스에서 NaN 발생. CPU로 폴백.
2. **체크포인트 다운로드 URL 변경** — `0417` 버전이 표준. 다른 버전이 나오면 환경변수로 지정.
3. **MeloTTS 의존성 충돌** — torch/transformers 버전 충돌 발생 가능. `OpenVoice` 환경과 별도 venv 권장.
4. **첫 호출 지연** — 모델 로드 ~10초. 본 스킬은 `_pipeline.py`에서 싱글톤 캐시로 한 번만 로드.

## 참고 논문
- Qin, Z. et al. "OpenVoice: Versatile Instant Voice Cloning." arXiv:2312.01479 (2023).
