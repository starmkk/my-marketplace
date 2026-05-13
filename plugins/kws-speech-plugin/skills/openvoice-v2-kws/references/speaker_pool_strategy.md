# 화자 풀 구성 전략

KWS 학습 데이터의 multi-speaker 다양성은 결국 **reference wav 풀의 품질**로 결정된다.
이 문서는 KyungGi님 환경에서 활용 가능한 한국어 화자 데이터 소스와 구성 전략을 정리한다.

## 1. 추천 데이터 소스

### 1.1 AIHub 다화자 데이터셋 (1순위)
- **다화자 음성합성 데이터** (KAIST + ETRI 등 다수): 100명+ 화자, 발화 시간 시간~수십시간
- **자유발화 음성 (남녀/연령대별)**: 수백 명 화자, KWS의 자연스러운 발화 분포에 적합
- **상담 음성 데이터**: 다양한 화자 + 자연스러운 톤
- 가입/심사 후 무료 다운로드. KT 사내 활용 라이선스 별도 확인 필요.

### 1.2 Zeroth-Korean (오픈)
- ~50시간, 100명 내외 화자
- Apache 2.0. 즉시 사용 가능
- Hugging Face: `kresnik/zeroth_korean`

### 1.3 KsponSpeech
- AIHub. 1000+ 화자, 1000시간
- 대화체라 KWS reference로는 깔끔하지 않을 수 있음 (자르기/필터링 필요)

### 1.4 자체 녹음
- 사내/지인 5~10명 녹음만 해도 베이스라인은 가능
- 마이크/환경만 통일하면 깨끗한 reference 확보 가능

## 2. 화자별 reference 선별 기준

### 자동 필터 (스크립트로 거르기)
- 길이 5~15초
- SNR > 25dB (잡음/음악 없음)
- VAD 비율 > 70% (대부분 발화)
- 단일 화자 (speaker diarization으로 검증)

### 수동 점검 (샘플링 검수)
- 발음이 또렷한가
- 감정/속도가 극단적이지 않은가
- 마이크 음질이 균일한가

## 3. 화자 풀 크기 권장

| KWS 데이터 규모 | 화자 풀 크기 | 비고 |
|---|---|---|
| PoC | 5~10명 | 빠른 검증 |
| 베이스라인 | 30~50명 | 일반화 시작 |
| 정식 모델 | 100~200명 | 도메인 갭 최소화 |
| SOTA 시도 | 500명+ | diminishing returns |

연구(Synth4KWS, Google 2024)에 따르면 화자 수는 **약 100명 근처에서 saturates**한다.
무한정 늘리는 것보다 100명 다양화 + 환경 augmentation에 집중하는 게 효율적.

## 4. 화자별 폴더 구조 권장

본 스킬의 `prepare_speaker_pool.py`는 다음 구조를 가정:

```
~/datasets/kws_speaker_pool/
├── spk_001/  ref.wav      ← 가장 큰 wav 자동 선택
├── spk_002/
│   ├── ref_a.wav
│   └── ref_b.wav          ← 가장 큰 파일이 사용됨
├── spk_003/  ref.wav
└── ...
```

화자 ID는 폴더명 (예: `spk_001`, `f_001`, `m_022`)이 그대로 사용된다.

## 5. AIHub 데이터 → 풀 변환 워크플로우

대부분 AIHub 데이터는 화자별로 정리되어 있지 않으므로 한 번 전처리 필요:

```python
# 의사코드
for utterance in aihub_metadata:
    speaker = utterance["speaker_id"]
    src_wav = utterance["audio_path"]
    dst_dir = pool_root / speaker
    dst_dir.mkdir(exist_ok=True)
    # 가장 깨끗한 5~15초 짜리 1~3개만 복사
    if 5.0 <= utterance["duration"] <= 15.0 and utterance["snr"] > 25:
        copy(src_wav, dst_dir / utterance["filename"])
```

이 부분은 데이터셋마다 metadata 형식이 달라서 본 스킬에 일반 스크립트로 포함하지 않음.
필요 시 `prepare_speaker_pool_aihub.py` 같은 데이터셋별 어댑터를 추가로 작성하면 됨.

## 6. 화자 균형 (성별/연령) 점검

키워드 K개 × 화자 N명 합성 후, 학습 데이터의 성별/연령 분포를 확인:
- 남:여 = 1:1 권장
- 연령대 20~60대 골고루
- 한쪽으로 쏠리면 KWS 모델도 그쪽으로 편향됨 (예: 여성 인식률 만 떨어지는 케이스)

AIHub 데이터는 메타데이터에 성별/연령이 있으므로 풀 구성 시 균형 맞추기.

## 7. 사용 패턴

### 패턴 A: 풀 전체 사용 (작은 풀)
```bash
python scripts/batch_multispk_synthesize.py \
  --speakers_per_keyword 0      # 0 = 전체 사용
```

### 패턴 B: 키워드별 무작위 N명 샘플링 (큰 풀)
```bash
python scripts/batch_multispk_synthesize.py \
  --speakers_per_keyword 30     # 매 키워드마다 30명 무작위
```

큰 풀(100명+)에서 풀 전체를 모든 키워드에 쓰면 데이터가 너무 커진다.
키워드별 30명씩 샘플링해도 충분히 다양성 확보됨 (논문 근거: Synth4KWS).

## 8. 라이선스 주의

- AIHub 데이터: 가입 시 동의서 확인 필요. **합성 결과물의 외부 배포 제한** 있을 수 있음.
- 사내 학습용은 대부분 OK, 외부 공개 모델/데이터셋은 별도 검토.
- 자체 녹음: 화자별 동의서 받아두기 (개인정보보호법).
