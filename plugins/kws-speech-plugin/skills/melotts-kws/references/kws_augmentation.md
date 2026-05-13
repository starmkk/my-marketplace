# KWS 데이터 증강 전략

## 왜 증강이 필요한가?

KWS 모델은 작고(보통 100k~1M 파라미터) 깨끗한 데이터에 쉽게 과적합한다.
실배포 환경에는 다음 변동이 있다:
- 화자 (성별/연령/사투리/감정)
- 발화 속도/억양
- 거리/방향 (원거리 마이크)
- 배경잡음 (TV, 음악, 웅성거림)
- 방의 잔향 (거실, 차량 내부, 사무실)
- 마이크/코덱 (전화, 블루투스, 폰 마이크)

합성 데이터는 깨끗하기 때문에, **증강 없이 그대로 사용하면 도메인 갭이 크다**.

## 증강 카테고리와 우선순위

### Tier 1 (필수)
| 항목 | 효과 | 본 스킬 구현 |
|---|---|---|
| Speed perturbation (0.9~1.1) | 발화속도 다양성 → 화자 효과 | augment_audio.py |
| Pitch shift (±2 semitone) | 화자 다양성 흉내 | augment_audio.py |
| Volume gain (±3dB) | 마이크 거리/감도 시뮬레이션 | augment_audio.py |

이 세 가지는 부수 비용이 거의 없고 효과가 크다. **무조건 켜라.**

### Tier 2 (강력 권장)
| 항목 | 효과 | 비고 |
|---|---|---|
| 배경잡음 mix (MUSAN 등) | 환경 잡음 robust | SNR 5~20dB 랜덤 |
| RIR convolution | 잔향/거리 robust | RIRS_NOISES 코퍼스 |

도메인 갭의 90%는 이 두 가지에서 온다. KWS 학습 정확도가 나쁘면 가장 먼저 의심할 부분.

### Tier 3 (선택)
| 항목 | 효과 | 비고 |
|---|---|---|
| Codec simulation | 전화/블루투스 환경 | sox로 wav → g711 → wav |
| SpecAugment | feature-level masking | wekws 학습 단계에서 켜는 게 일반적 |
| Voice conversion (RVC, OpenVoice) | 진짜 화자 다양성 | 별도 모델 + GPU 필요 |

## Tier별 사용 시나리오

### 시나리오 A: 빠른 PoC
- Tier 1만 적용
- 1 wav → 약 15개 변형 (3 speed × 5 pitch × 1 gain, random_n=15)
- wekws 학습 시 자체 SpecAugment 활용

### 시나리오 B: 실배포 준비
- Tier 1 + Tier 2 모두 적용
- noise_prob=0.5, rir_prob=0.3 권장
- MUSAN: https://www.openslr.org/17/
- RIRS_NOISES: https://www.openslr.org/28/

### 시나리오 C: 실데이터가 거의 없을 때
- Tier 1 + Tier 2 + 합성:실 = 3:1 비율
- 단, **검증/테스트는 반드시 실데이터로**.
- 합성-only 평가는 실성능을 과대평가한다.

## 데이터 비율 권장

| 실데이터 양 | 합성:실 비율 | 비고 |
|---|---|---|
| 10시간 이상 | 1:1 | 합성은 보조 |
| 1~10시간 | 2:1 ~ 3:1 | 합성을 메인으로 |
| 1시간 미만 | 5:1 이상 | 그래도 실데이터 필수 |
| 0시간 (cold start) | 합성만 | 베이스라인용. 실배포는 X |

## 흔한 실패 패턴

1. **합성 데이터로만 학습한 후 실데이터로 평가하면 정확도 폭락.**
   → 도메인 갭 미해소. Tier 2 augmentation 추가.

2. **Augmentation이 너무 강해서 키워드 자체가 망가짐.**
   → SNR 하한을 5dB 이상으로 유지. RIR도 너무 긴 잔향(>1초) 피하기.

3. **모든 증강을 cartesian product로 만들어서 데이터 폭발.**
   → augment_config.yaml의 `random_n`으로 제한. 동일 키워드의 변형이 너무 많으면 오히려 과적합 유도.

4. **Negative 샘플 부재.**
   → KWS는 false-alarm rate가 핵심 KPI. 키워드와 다른 일반 발화도 합성/수집해서 포함시켜야 함.

## 참고 문헌
- Ko, T. et al. "Audio augmentation for speech recognition." Interspeech 2015.
- Ko, T. et al. "A study on data augmentation of reverberant speech for robust speech recognition." ICASSP 2017.
- wekws repo: https://github.com/wenet-e2e/wekws
