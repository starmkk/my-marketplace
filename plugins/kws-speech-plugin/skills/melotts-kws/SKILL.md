---
name: melotts-kws
description: |
  MeloTTS(MyShell.ai)를 사용해 한국어 KWS 학습/평가용 합성 음성 데이터를 대량 생성하고,
  화자 다양성 한계를 극복하기 위한 표준 augmentation(speed/pitch/noise/RIR)과
  wekws 호환 manifest를 함께 만드는 스킬.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라:
  - "MeloTTS", "melo tts", "한국어 TTS", "TTS 합성"
  - "KWS 합성 데이터", "키워드 음성 생성", "wakeword 음성 합성"
  - "음성 합성으로 데이터 증강", "한국어 음원 생성"
  - "wekws 학습 데이터 만들기", "키워드 데이터셋 합성"
  - "Gemma TTS" (사용자가 잘못 알고 있을 때 — Gemma 4는 TTS 미지원, MeloTTS로 안내)
---

# MeloTTS-KWS: 한국어 KWS 합성 데이터 생성 스킬

## 1. 핵심 사실 (먼저 짚고 갈 것)

### 1.1 Gemma 4 E2B-it는 TTS가 아니다
사용자가 "Gemma TTS"를 언급하면 먼저 다음을 안내한다:

- Gemma 4 E2B-it는 **multimodal input 모델**이지만 **출력은 텍스트 전용**이다.
- 오디오 관련 기능은 ASR(음성 → 텍스트)과 음성 번역뿐이다.
- 따라서 TTS는 별도 모델이 필요하다 → 이 스킬에서는 **MeloTTS**를 사용한다.

이 사실을 무시하고 Gemma 4로 TTS 코드를 짜려 하지 말 것.

### 1.2 MeloTTS 한국어의 한계
- 한국어 모델 화자는 **단 1명** (`speaker_ids['KR']`).
- "다양한 화자"를 위해서는 **반드시 augmentation을 동반**해야 한다.
- 본 스킬은 그래서 단순 합성이 아니라 **합성 + augmentation 파이프라인**으로 구성된다.

## 2. 언제 이 스킬을 트리거하나

다음 의도가 보일 때 이 스킬의 워크플로우를 따른다:

| 의도 | 사용할 스크립트 |
|---|---|
| 한 문장만 빨리 합성해서 들어보기 | `scripts/synthesize.py` |
| 키워드 리스트 → wav 파일 대량 생성 | `scripts/batch_synthesize.py` |
| 합성된 wav에 화자 다양성 augmentation 적용 | `scripts/augment_audio.py` |
| wekws 학습용 manifest(`.list` 파일) 생성 | `scripts/make_wekws_manifest.py` |
| 처음 환경 구축 | `scripts/install.sh` |

## 3. 환경 구축 워크플로우

**환경변수 (필수):**
- `MELOTTS_KWS_DIR` — melotts-kws 스킬 디렉토리 절대경로

미설정 시 `cd` 명령이 실패합니다. 등록 방법:
```shell
echo 'export MELOTTS_KWS_DIR=/path/to/melotts-kws' >> ~/.zshrc
source ~/.zshrc
```

처음 사용 시:

```bash
cd "$MELOTTS_KWS_DIR"
bash scripts/install.sh
```

`install.sh`는 다음을 수행한다:
1. `~/Documents/work_2026/KWS/melotts_env` 에 Python venv 생성
2. MeloTTS GitHub 클론 후 `pip install -e .`
3. unidic 다운로드 (일본어 의존성이지만 기본 설치 필요)
4. macOS의 경우 MPS 가속 자동 활성화 확인
5. 한국어 모델 가중치 사전 다운로드 (huggingface-cli)

## 4. 단일 문장 합성 (테스트/데모용)

```bash
python scripts/synthesize.py \
  --text "오케이 케이티" \
  --output ./out/test.wav \
  --speed 1.0
```

기본 출력: 16kHz mono PCM WAV (KWS 표준).
MeloTTS 원본 출력은 22.05kHz/24kHz 등이므로 **자동으로 16kHz mono로 리샘플링**한다.

## 5. KWS 대량 합성 워크플로우 (메인 시나리오)

### 5.1 입력 준비
키워드 텍스트 파일 (`examples/keywords.txt` 참고):
```
오케이 케이티
헤이 케이티
지니야
```

### 5.2 1차 합성
```bash
python scripts/batch_synthesize.py \
  --keywords examples/keywords.txt \
  --out_dir ./synth_raw \
  --sample_rate 16000
```

각 키워드당 1개의 baseline wav가 생성된다.

### 5.3 화자 다양성 augmentation
```bash
python scripts/augment_audio.py \
  --in_dir ./synth_raw \
  --out_dir ./synth_aug \
  --config examples/augment_config.yaml
```

기본 `augment_config.yaml`에 따라 1개 wav → N개 변형:
- Speed perturbation: `[0.85, 0.9, 1.0, 1.1, 1.2]` (×5)
- Pitch shift: `[-2, -1, 0, +1, +2]` semitone (×5)
- 조합: cartesian product (5×5=25) 또는 random sampling
- (선택) MUSAN 배경잡음 / RIR convolution

기본은 5×5=25 grid이며, `random_n: 10`으로 설정하면 25개 중 10개만 무작위 샘플링.

### 5.4 wekws manifest 생성
```bash
python scripts/make_wekws_manifest.py \
  --in_dir ./synth_aug \
  --keyword_map examples/keyword_map.json \
  --out ./data/synth_train.list
```

wekws가 요구하는 JSON-Lines 포맷 (`key`, `wav`, `txt`, `label`)으로 manifest 생성.

## 6. wekws 통합 시 권장 사용법

KyungGi님의 `wekws_v2/examples/korean_kws/s0` 워크플로우에서:

1. 기존 실데이터 `train.list` 옆에 합성 데이터 `synth_train.list`를 둔다.
2. **합성 데이터만으로 학습하지 말고**, 실데이터:합성데이터 = 1:1 ~ 1:3 비율로 섞어서 학습한다.
3. 합성 데이터는 cleantion이 너무 깨끗해서 도메인 갭이 발생하므로, **반드시 noise/RIR augmentation을 통과시킨 후** 사용한다.
4. wekws의 학습 시 augmentation(`spec_aug`, `noise_aug`)은 그대로 켜둔다 — 합성 데이터에도 추가로 적용된다.

## 7. 자주 하는 실수와 해결책

| 증상 | 원인 | 해결 |
|---|---|---|
| 합성 데이터로 학습한 모델이 실데이터에서 성능 폭락 | 도메인 갭 | augment_audio.py에서 noise/RIR 켜기, 실데이터와 1:1 이상 섞기 |
| MeloTTS 한국어 발음이 부자연스러움 | speed=1.0이 너무 느림 | speed=1.2~1.3 권장 (한국어 모델 특성) |
| MPS에서 죽음 (Mac M-series) | torch MPS 호환 이슈 | `device='cpu'` 강제 — CPU도 실시간 가능 |
| unidic 다운로드 실패 | 네트워크/SSL | `python -m unidic download` 수동 실행 또는 `unidic-lite`로 대체 |
| 외장 SSD 모델 경로 access denied | macOS Sandbox | 로컬 SSD로 가중치 복사 |

## 8. 라이선스
MeloTTS는 MIT 라이선스이므로 KT 사내/상업 용도 모두 사용 가능하다.
이 점은 사용자에게 명시적으로 안내해도 좋다.

## 9. 참고 문서
- `references/melotts_korean.md` — MeloTTS 한국어 API 상세
- `references/kws_augmentation.md` — KWS augmentation 이론과 권장 설정
- `references/wekws_data_format.md` — wekws manifest 포맷 명세

## 10. Gemma 4 E2B-it를 버리지 말 것
사용자가 다운로드한 `gemma-4-E2B-it`는 TTS는 못 하지만 **ASR/검증용**으로 매우 유용하다.
합성한 음성을 Gemma 4로 다시 transcribe해서 원본 텍스트와 일치하는지 검증하면 합성 품질을 자동 모니터링할 수 있다 (round-trip QA). 필요 시 별도 스킬로 확장 가능.
