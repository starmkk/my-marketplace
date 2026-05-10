---
name: gemma4-asr-qa
description: |
  로컬 Gemma 4 E2B-it ASR로 MeloTTS/OpenVoice V2 합성 wav를 transcribe하고 원본 텍스트와
  비교(round-trip QA)해 품질이 떨어지는 데이터를 자동 필터링하는 스킬.
  Round-trip QA skill that uses local Gemma 4 E2B-it ASR to transcribe synthesized wavs
  and filter out low-quality samples by comparing against the source text.

  사용자가 다음과 같은 표현을 쓸 때 반드시 이 스킬을 사용하라
  (Trigger when the user mentions any of):
  - "Gemma 4 ASR", "gemma asr", "gemma transcribe"
  - "round-trip QA", "round trip", "합성 품질 검증", "synthesis quality filtering"
  - "CER 계산", "WER 계산", "CER/WER threshold"
  - "합성 데이터 필터링", "잘못 합성된 wav 걸러내기"
  - "Gemma 4로 음성 인식", "한국어 ASR로 검증", "Korean ASR validation"

  관련 스킬 (Related skills):
  - `gemma4`: Gemma 4 모델 일반 사용법.
  - `melotts-kws`: 단일 화자 합성. 본 스킬이 산출물을 검증.
  - `openvoice-v2-kws`: 멀티 화자 합성. 본 스킬이 산출물을 검증.
---

# Gemma 4 E2B-it ASR Round-Trip QA 스킬

## 1. 스킬 목적

KyungGi님이 다운로드한 **Gemma 4 E2B-it** 모델은 TTS는 못 하지만 **ASR/음성이해**는 가능하다.
이 능력을 활용해 합성 데이터의 품질을 자동 검증한다:

```
[원본 텍스트 "오케이 케이티"]
        │
        ▼
   합성 (MeloTTS/OpenVoice)
        │
        ▼
   [합성 wav]
        │
        ▼  Gemma 4 ASR
        │
        ▼
[transcribe 결과 "오케이 케이티"]
        │
        ▼  원본과 비교 (CER/WER)
        │
        ▼
   [품질 점수] → 임계값 이하면 폐기
```

이를 **Round-trip QA** 또는 **Cycle Consistency Check**라고 한다.

## 2. 왜 이 스킬이 필요한가

합성 데이터에는 다음 실패 모드가 존재:

1. **MeloTTS의 발음 망가짐** — 한자/외래어/숫자 처리 실패
2. **OpenVoice tone color cloning이 발음을 흐릿하게** — 일부 화자 timbre가 발음 명료도 손상
3. **Augmentation으로 발음 매몰** — speed 0.85 + noise SNR 5dB가 합쳐지면 키워드가 거의 안 들림

이런 데이터로 KWS를 학습하면 **잘못된 텍스트와 wav 매칭이 학습되어 정확도가 떨어진다**.
사람이 일일이 듣고 검수할 수 없는 대량 데이터에서, ASR 기반 자동 필터는 거의 유일한 해결책.

## 3. 라이선스
- Gemma 4 모델: **Gemma Terms of Use** (Apache 2.0과 유사하지만 별도 약관). 상업 활용 가능, KT 사내 OK.
- 사용 전 https://ai.google.dev/gemma/terms 확인 권장.

## 4. 환경변수 (필수 사전 조건)

본 스킬은 **PC마다 다른 절대경로를 환경변수로만 받는다**. 하드코딩된 경로는 없다.

| 변수 | 필수 | 설명 |
|---|---|---|
| `GEMMA4_MODEL_PATH` | ✅ | Gemma 4 E2B-it 모델 디렉토리 절대경로 |
| `GEMMA4_VENV_DIR`   | ⬜ | venv 위치 (기본 `$HOME/.cache/gemma4-asr-qa/venv`) |
| `PYTHON_BIN`        | ⬜ | 사용할 python 실행파일 (기본 `python3`) |

### 4.1 Claude가 본 스킬을 호출할 때 반드시 가장 먼저 수행할 절차

> **STEP 0 (환경변수 검증 게이트):**
> 어떤 워크플로우든 시작하기 전에 사용자 셸의 환경변수를 확인한다.
> ```bash
> echo "GEMMA4_MODEL_PATH=${GEMMA4_MODEL_PATH:-<unset>}"
> ```
> - 값이 비어 있거나(`<unset>`) 디렉토리가 없으면 **즉시 작업을 중단**하고
>   사용자에게 아래 4.2의 가이드를 그대로 출력한 뒤 사용자가 환경변수를
>   설정하고 알려줄 때까지 다음 단계로 넘어가지 말 것.
> - 사용자가 "설정했다"고 알리면, 위 echo 명령을 다시 실행해 값과 디렉토리
>   존재를 확인하고 그 결과를 사용자에게 다시 보여준 뒤 작업을 재개한다.
>
> Python/Bash 스크립트(`scripts/_env.py`, `scripts/install.sh`)에도 동일한
> 검증 게이트가 들어 있어 환경변수 미설정 상태에서 직접 실행해도 안전하게
> 안내 메시지와 함께 `exit 2`로 중단된다.

### 4.2 사용자에게 출력할 환경변수 설정 가이드

```text
[gemma4-asr-qa] 환경변수가 설정되지 않아 작업을 진행할 수 없습니다.

다음 명령으로 GEMMA4_MODEL_PATH를 셸 rc 파일에 추가해 주세요.

  # zsh 사용자 (macOS 기본)
  echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> ~/.zshrc
  source ~/.zshrc

  # bash 사용자
  echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> ~/.bashrc
  source ~/.bashrc

  # fish 사용자
  set -Ux GEMMA4_MODEL_PATH /absolute/path/to/gemma-4-E2B-it

설정이 끝나면 알려주세요. 환경변수를 확인한 뒤 작업을 이어서 진행합니다.
```

## 5. 환경 구축

```bash
# 0) 필수 환경변수 확인 (위 4.1 절차)
echo "GEMMA4_MODEL_PATH=$GEMMA4_MODEL_PATH"

# 1) 본 스킬이 설치된 디렉토리에서 install.sh 실행
bash scripts/install.sh
```

`install.sh`도 동일한 게이트를 가지므로 환경변수 미설정 시 자동 중단된다.

수행 단계:
1. venv 생성 (`$GEMMA4_VENV_DIR` 또는 기본 `~/.cache/gemma4-asr-qa/venv`)
2. transformers (latest) + torch + torchvision + librosa + accelerate 설치
3. jiwer 설치 (CER/WER 계산용)
4. 모델 가중치 위치 검증 (`$GEMMA4_MODEL_PATH`)
5. 모델 로드 테스트 + ASR 동작 확인

## 6. 워크플로우

### 6.1 단일 wav transcribe (테스트)
```bash
python scripts/transcribe.py \
  --audio /path/to/test.wav \
  --language Korean
```

출력: 전사된 텍스트만 stdout으로.

### 6.2 배치 transcribe (디렉토리 통째로)
```bash
python scripts/batch_transcribe.py \
  --in_dir ../openvoice-v2-kws/synth_multispk_aug \
  --out_csv ./asr_results.csv \
  --language Korean
```

CSV 형식: `wav_path, transcribed_text, processing_time_sec`

### 6.3 Round-trip QA (메인 시나리오)
```bash
python scripts/round_trip_qa.py \
  --source_manifest ../openvoice-v2-kws/synth_multispk/manifest.csv \
  --asr_results ./asr_results.csv \
  --out_report ./qa_report.csv \
  --cer_threshold 0.3 \
  --out_filtered_manifest ./filtered_manifest.csv
```

수행:
1. 원본 manifest의 (utt_id, text) 와 ASR 결과의 (wav, transcribed_text) 매칭
2. 한국어 CER/WER 계산
3. `qa_report.csv`: 모든 발화의 점수와 통과 여부
4. `filtered_manifest.csv`: CER < threshold인 발화만 (학습용)

### 6.4 E2E 한 번에 (편의 스크립트)
```bash
python scripts/filter_synth_dataset.py \
  --in_dir ../openvoice-v2-kws/synth_multispk_aug \
  --source_manifest ../openvoice-v2-kws/synth_multispk/manifest.csv \
  --out_filtered_manifest ./filtered_manifest.csv \
  --cer_threshold 0.3
```

내부적으로 batch_transcribe → round_trip_qa 실행.

### 6.5 wekws manifest로 변환
필터링된 manifest를 `melotts-kws/scripts/make_wekws_manifest.py`에 다시 통과시키면 됨.

## 7. CER/WER 임계값 가이드

한국어 KWS 데이터 기준 권장 임계값:

| CER | 통과율 (대략) | 학습 데이터 품질 | 권장 사용처 |
|---|---|---|---|
| < 0.10 | 50~70% | 매우 깨끗 | 평가셋, 핵심 학습 데이터 |
| < 0.20 | 70~85% | 깨끗 | 일반 학습 데이터 |
| < 0.30 | 85~95% | 보통 | 대량 학습 데이터 (권장 기본값) |
| < 0.50 | 95~99% | 거친 | 사전학습 / curriculum learning 초기 |
| 모두 통과 | 100% | 미검증 | 권장 X |

권장 시작점: **CER < 0.30**.
실데이터로 학습/평가 후 KWS 정확도가 부족하면 0.20으로 더 엄격하게.

## 8. 성능 (참고)

Mac M-시리즈 또는 RTX 3090급 환경 기준 (1초 길이 wav 1개):

| 환경 | wav당 처리 시간 | 비고 |
|---|---|---|
| RTX 3090 (CUDA, fp16) | ~0.5초 | 가장 빠름 |
| M2 Pro (MPS, bf16) | ~3초 | Mac 권장 |
| M2 Pro (CPU, fp32) | ~10초 | 느리지만 안정적 |
| RTX 3090 + flash-attention | ~0.3초 | 최고 |

10,000개 wav 검증 시:
- GPU: 약 1.5시간
- Mac MPS: 약 8시간
- Mac CPU: 약 28시간

대용량은 GPU 권장. 또는 KWS 학습 직전에 한 번만 돌리면 됨.

## 9. 주의사항

### 9.1 Gemma 4 ASR도 완벽하지 않다
- KWS 키워드 자체는 짧고 단순해서 ASR이 잘 됨
- 하지만 일부 외래어/방언/특수 발음에서 약점 있음
- **첫 사용 시 반드시 50개 정도 샘플링해서 사람이 검수**할 것 (false positive/negative 비율 파악)

### 9.2 ASR이 틀린 경우의 처리
- 진짜 합성 품질이 나쁜 케이스
- ASR 자체가 약한 케이스 (외래어 등)
- 두 경우 구분이 안 되므로, 일관되게 ASR 신뢰

KWS 키워드를 정할 때 ASR이 잘 인식하는 단어로 정하는 것도 한 방법
(예: "오케이 빅스비"보다 "오케이 케이티"가 ASR이 더 정확).

### 9.3 메모리 사용량
- Gemma 4 E2B-it: bfloat16 기준 약 5GB VRAM
- batch_size=1 기준 (KWS wav는 짧아서 batching 효과 미미)
- 8GB 이상 GPU 권장

### 9.4 Thinking 모드 비활성화
ASR에는 thinking이 불필요. 본 스킬은 system prompt에 `<|think|>` 토큰을 넣지 않아 thinking 비활성화.

## 10. 참고 문서
- `references/gemma4_asr_usage.md` — Gemma 4 ASR API 상세
- `references/round_trip_qa_strategy.md` — Round-trip QA 이론과 변형
- `references/cer_wer_metrics.md` — 한국어 CER/WER 계산 주의사항

## 11. 스킬 체이닝 (전체 KWS 데이터 파이프라인)

```
melotts-kws / openvoice-v2-kws    ──합성──▶  synth_*.wav
                                                │
                                                ▼
                                  augment_audio.py (melotts-kws)
                                                │
                                                ▼
                                          synth_aug_*.wav
                                                │
                                                ▼
                              gemma4-asr-qa: filter_synth_dataset.py
                                                │
                                                ▼
                                       filtered_manifest.csv
                                                │
                                                ▼
                              make_wekws_manifest.py (melotts-kws)
                                                │
                                                ▼
                                  wekws 학습용 .list 파일
```

이 파이프라인 전체가 KyungGi님의 한국어 KWS 데이터 증강 시스템.
