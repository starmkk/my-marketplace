---
name: openvoice-v2-kws
description: |
  OpenVoice V2 (MyShell.ai) + MeloTTS-Korean을 결합해 KWS 학습용 멀티화자 한국어 합성 데이터를
  생성하는 스킬. MeloTTS의 단일 화자 한계를 voice cloning(tone color conversion)으로 극복하고,
  AIHub 등 다화자 reference wav 풀에서 N가지 화자로 동일 키워드를 합성한다.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라:
  - "OpenVoice", "openvoice v2", "tone color cloning"
  - "voice cloning", "음성 복제", "화자 복제"
  - "multi-speaker 한국어 합성", "다화자 KWS 데이터"
  - "MeloTTS 화자 다양성 부족", "KWS 화자 풀"
  - "AIHub 화자로 키워드 합성", "reference wav로 합성"

  관련 스킬:
  - `melotts-kws`: 단일 화자 합성 + speed/pitch augmentation. 본 스킬과 상호 보완 관계.
---

# OpenVoice V2 + MeloTTS — 한국어 KWS 멀티화자 합성 스킬

## 1. 핵심 컨셉

이 스킬은 **두 단계 파이프라인**으로 동작한다:

```
[텍스트] ──MeloTTS-KR──▶ [base wav (단일 화자)]
                                │
[reference wav]──se_extractor─▶ [target speaker embedding]
                                │
                       OpenVoice ToneColorConverter
                                │
                                ▼
                       [target wav (target 화자 톤)]
```

- **MeloTTS-KR**: 한국어 발음/억양 담당 (안정적). 단일 화자.
- **OpenVoice V2**: tone color(목소리 색깔)만 target 화자로 변환.
- 결과: 발음은 안정적이고, 화자는 N명으로 다양화.

이는 OpenVoice 공식 `demo_part3.ipynb`의 패턴을 그대로 따른다.

## 2. 라이선스 (KT 사내 활용 OK 근거)
- OpenVoice V1, V2: **2024년 4월부터 MIT License** (이전엔 비상업).
- MeloTTS: **MIT License**.
- 두 모델 모두 상업/사내 활용 가능.

## 3. 언제 이 스킬을 쓰나

| 상황 | 어느 스킬을 쓸까 |
|---|---|
| 한 화자만 빠르게 합성, 화자 다양성 augmentation으로 충분 | `melotts-kws` |
| 진짜 multi-speaker 데이터가 필요 (KWS 일반화 성능 ↑) | **본 스킬** |
| reference wav를 5~10초씩 가지고 있음 (AIHub 등) | **본 스킬** |
| 빠른 PoC, GPU 없음 | `melotts-kws` (CPU 실시간) |
| 화자 N명 × 키워드 M개 = 대량 multi-speaker 합성 | **본 스킬** |

## 4. 환경 구축

### 소스 코드 관리 (~/.claude/repo)

OpenVoice 소스코드가 필요한 작업이 생기면 **반드시 먼저 사용자에게 확인**한다:

```
[소스 사용 흐름]
Step 1. 사용자에게 묻기:
  "로컬에 이미 OpenVoice 소스가 있으신가요? 있다면 경로를 알려주세요."

Step 2a. 사용자가 경로 제공 → 해당 경로 그대로 사용

Step 2b. 사용자가 없다고 하면 → ~/.claude/repo에 자동 다운로드 후 안내
```

| 항목 | 값 |
|------|-----|
| GitHub | https://github.com/myshell-ai/OpenVoice |
| 폴더 패턴 | `~/.claude/repo/OpenVoice@<version>` |
| 체크포인트 | `~/.claude/repo/OpenVoice@<version>/checkpoints_v2` |
| venv 위치 | `~/.claude/venvs/openvoice` |

처음 사용 시 환경 구축:
```bash
bash scripts/install.sh
```

`install.sh`가 수행하는 일:
1. venv 생성 (`~/Documents/work_2026/KWS/openvoice_env`)
2. OpenVoice GitHub 클론 + `pip install -e .`
3. MeloTTS 설치 (`pip install git+...`)
4. unidic 다운로드
5. checkpoints_v2 다운로드 (S3, ~200MB)
6. 한국어 base speaker embedding 위치 확인

⚠️ MeloTTS 환경과 별도로 두는 것을 권장. 의존성 충돌이 가끔 있음.

## 5. 워크플로우

### Step 1: 화자 풀 구성
AIHub 다화자 데이터셋이나 자체 녹음 데이터에서 화자별 reference wav를 모은다.

권장 구조:
```
~/datasets/kws_speaker_pool/
├── spk_001/  ref.wav  (5~15초, 깨끗한 한국어 발화)
├── spk_002/  ref.wav
├── ...
└── spk_050/  ref.wav
```

각 wav에서 speaker embedding을 한 번 추출해두면 합성 시 빠르다:
```bash
python scripts/prepare_speaker_pool.py \
  --pool_dir ~/datasets/kws_speaker_pool \
  --out_embeddings ./speaker_embeddings.pt
```

→ `speaker_embeddings.pt`에 `{speaker_id: tensor}` 딕셔너리 저장.

### Step 2: 단일 합성 테스트
```bash
python scripts/clone_synthesize.py \
  --text "오케이 케이티" \
  --reference ~/datasets/kws_speaker_pool/spk_001/ref.wav \
  --output ./out/test_spk001.wav \
  --speed 1.2
```

### Step 3: 키워드 × 화자 풀 대량 합성 (핵심)
```bash
python scripts/batch_multispk_synthesize.py \
  --keywords ../melotts-kws/examples/keywords.txt \
  --speaker_embeddings ./speaker_embeddings.pt \
  --out_dir ./synth_multispk \
  --speakers_per_keyword 20 \
  --speed 1.2 \
  --manifest ./synth_multispk/manifest.csv
```

설명:
- 키워드 K개 × 화자 N명 → K×N개 wav 생성
- `--speakers_per_keyword`로 키워드당 사용할 화자 수 제한 (전체 풀이 너무 크면)
- `--manifest`로 `(utt_id, wav, text, speaker_id)` CSV 생성

### Step 4: 추가 augmentation (선택)
multi-speaker 합성 결과에 다시 `melotts-kws/scripts/augment_audio.py`를 통과시키면
화자 다양성 + 환경 다양성을 모두 확보할 수 있다.

```bash
python ../melotts-kws/scripts/augment_audio.py \
  --in_dir ./synth_multispk \
  --out_dir ./synth_multispk_aug \
  --config ../melotts-kws/examples/augment_config.yaml
```

### Step 5: wekws manifest 생성
`melotts-kws`의 manifest 생성기를 그대로 재사용. 단, source_manifest 컬럼에 화자 정보가 추가됨.

```bash
python ../melotts-kws/scripts/make_wekws_manifest.py \
  --in_dir ./synth_multispk_aug \
  --source_manifest ./synth_multispk/manifest.csv \
  --keyword_map ../melotts-kws/examples/keyword_map.json \
  --out ./data/synth_multispk_train.list
```

## 6. 권장 데이터 규모

| 시나리오 | 화자 수 | 키워드당 변형 (augmentation 후) | 권장 키워드 |
|---|---|---|---|
| 빠른 PoC | 5~10명 | 약 50개 | 4~5개 |
| 정식 학습 (저자원) | 30~50명 | 약 750개 | 5~10개 |
| 정식 학습 (충분 자원) | 100명+ | 1,500개+ | 5~10개 |

키워드당 1500개 이상 만들면 과적합 위험. 화자 다양성이 중요하지 같은 화자 같은 키워드를 무한히 늘리는 건 효과 한계.

## 7. 주의사항

### 7.1 Reference wav 품질이 결과 품질을 좌우
- **권장**: 5~15초, 단일 화자, 배경잡음 < -30dB, 16kHz 이상.
- **금지**: 잡음 많은 클립, 여러 화자 혼재, 길이 < 3초.
- VAD(`vad=True`)로 무음 구간을 자동 제거하지만, 입력 자체가 깨끗할수록 좋다.

### 7.2 도메인 갭은 여전히 존재
화자 다양성이 늘어도 합성 데이터 특유의 깨끗함(노이즈/잔향 부재)은 남는다.
**반드시** noise/RIR augmentation을 통과시킬 것 (`melotts-kws/augment_audio.py`).

### 7.3 한국어 reference + 한국어 합성이 가장 안정적
OpenVoice V2는 cross-lingual cloning을 지원하지만, KWS는 발음 정확성이 중요하므로
한국어 발화 reference로만 풀을 구성할 것.

### 7.4 GPU 권장
- Mac CPU/MPS에서 동작은 하지만, 100명 × 10키워드 = 1000개 합성 시 수십 분~수 시간 소요.
- CUDA GPU에서는 분 단위.
- Speaker embedding은 한 번 추출 후 재사용하므로 합성 단계만 GPU 필요.

### 7.5 V2 체크포인트만 사용
V1과 V2의 checkpoint는 호환되지 않는다. 본 스킬은 V2 전용이며 `checkpoints_v2_0417.zip`을 받는다.

## 8. 참고 문서
- `references/openvoice_v2.md` — OpenVoice V2 API 상세, embedding 구조
- `references/speaker_pool_strategy.md` — KWS용 화자 풀 구성 가이드 (AIHub 데이터셋 활용 등)
- `references/kws_multispeaker_aug.md` — multi-speaker KWS 학습 베스트 프랙티스 (학계 근거 포함)

## 9. 학계 근거
multi-speaker TTS 합성이 KWS 성능을 크게 개선한다는 것은 검증된 사실:
- Synth4KWS (Google, 2024): 50k 실데이터 baseline에서 EER 30.1%, AUC 46.7% 개선
- Jia et al. 2020: confusion words 시나리오에서 multi-speaker TTS가 결정적
- LLM-Synth4KWS (2025): 화자 다양성 부족이 일반화 성능 한계의 주원인

따라서 이 스킬은 KWS 정확도 향상의 "증명된 레버"다.
