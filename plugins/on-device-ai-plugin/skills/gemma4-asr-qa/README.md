# gemma4-asr-qa

로컬 Gemma 4 E2B-it 모델의 ASR 능력으로 합성 wav를 transcribe하고 원본 텍스트와
비교(round-trip QA)하여 합성 품질이 떨어지는 데이터를 자동 필터링하는 스킬.

## 디렉토리 구조

```
gemma4-asr-qa/
├── SKILL.md
├── README.md
├── scripts/
│   ├── install.sh                # transformers + librosa + jiwer 설치 (env-guarded)
│   ├── _env.py                   # 공통 환경변수 검증 게이트
│   ├── _asr.py                   # 공통 ASR 모듈 (싱글톤 캐시 + 한국어 정규화)
│   ├── transcribe.py             # 단일 wav transcribe (테스트용)
│   ├── batch_transcribe.py       # 디렉토리 → CSV (resume 지원)
│   ├── round_trip_qa.py          # ASR 결과 ↔ 원본 비교, CER/WER 계산, 필터
│   └── filter_synth_dataset.py   # E2E 편의 스크립트 (batch + qa)
├── references/
│   ├── gemma4_asr_usage.md       # API 가이드
│   ├── round_trip_qa_strategy.md # QA 이론과 응용 패턴
│   └── cer_wer_metrics.md        # 한국어 CER/WER 계산 주의사항
└── examples/
    └── qa_config.yaml            # 임계값 가이드 (참고용)
```

## 필수 환경변수

본 스킬은 PC마다 다른 절대경로를 **환경변수로만** 받는다. 하드코딩된 경로는 없다.

| 변수 | 필수 | 설명 |
|---|---|---|
| `GEMMA4_MODEL_PATH` | ✅ | Gemma 4 E2B-it 모델 디렉토리 절대경로 |
| `GEMMA4_VENV_DIR`   | ⬜ | venv 위치 (기본 `$HOME/.cache/gemma4-asr-qa/venv`) |
| `PYTHON_BIN`        | ⬜ | python 실행파일 (기본 `python3`) |

미설정 상태에서 어떤 스크립트든 실행하면 친절한 안내 메시지와 함께 즉시 중단된다.

### 환경변수 등록 방법

```bash
# zsh (macOS 기본)
echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> ~/.zshrc
source ~/.zshrc

# bash
echo 'export GEMMA4_MODEL_PATH=/absolute/path/to/gemma-4-E2B-it' >> ~/.bashrc
source ~/.bashrc

# fish
set -Ux GEMMA4_MODEL_PATH /absolute/path/to/gemma-4-E2B-it
```

## 빠른 시작

```bash
# 0. 환경변수 확인 (필수)
echo "GEMMA4_MODEL_PATH=$GEMMA4_MODEL_PATH"

# 1. 설치 (스킬 디렉토리로 이동 후)
bash scripts/install.sh

# 2. venv 활성화
source "${GEMMA4_VENV_DIR:-$HOME/.cache/gemma4-asr-qa/venv}/bin/activate"

# 3. 단일 wav 테스트
python scripts/transcribe.py --audio /path/to/test.wav

# 4. E2E 필터링 (가장 자주 쓸 명령)
#    <SYNTH_AUG_DIR>: 합성 + augmentation 결과 wav 디렉토리
#    <SYNTH_MANIFEST>: 합성 시 만든 manifest.csv
python scripts/filter_synth_dataset.py \
  --in_dir <SYNTH_AUG_DIR> \
  --source_manifest <SYNTH_MANIFEST> \
  --workdir ./qa_workdir \
  --cer_threshold 0.30

# 5. 필터된 manifest를 wekws .list로 변환 (melotts-kws 스킬의 도우미)
#    <MELOTTS_SKILL_DIR>: melotts-kws 스킬이 설치된 디렉토리
#    <KEYWORD_MAP>: 키워드→라벨 매핑 JSON
#    <OUT_LIST>: wekws에서 사용할 .list 출력 경로
python <MELOTTS_SKILL_DIR>/scripts/make_wekws_manifest.py \
  --in_dir <SYNTH_AUG_DIR> \
  --source_manifest ./qa_workdir/filtered_manifest.csv \
  --keyword_map <KEYWORD_MAP> \
  --out <OUT_LIST>
```

## 핵심 설계

1. **환경변수 단일 진입점** — `_env.ensure_gemma4_env()`가 모든 entrypoint와
   `install.sh`에서 가장 먼저 호출되어, 미설정 시 즉시 `exit 2`로 차단
2. **모델 싱글톤 캐시** — `_asr.py`에서 모델 1회 로드, batch 처리 시 재사용
3. **resume 지원** — `batch_transcribe.py`에 `--resume` 플래그. crash 시 이어쓰기
4. **한국어 정규화 내장** — `normalize_korean()`이 zero-width/구두점/공백 처리
5. **safe metric** — jiwer가 빈 문자열에 예외 던지는 것 가드
6. **manifest schema 보존** — `round_trip_qa.py`가 원본 manifest 컬럼을 그대로
   보존하여 후속 스크립트(make_wekws_manifest 등)에 그대로 통과시킬 수 있음

## 라이선스
- Gemma 4 모델: Gemma Terms of Use (상업 활용 가능)
- 이 스킬 코드: MIT
- 의존성: jiwer (Apache 2.0), transformers (Apache 2.0), librosa (ISC)

## 다음 단계 (후속 작업 후보)
- `--cross_check_with_whisper` 옵션 (이중 ASR 검증)
- 자모 단위 PER 계산 옵션
- speaker_id 별 CER 분포 자동 시각화
- KWS confidence 기반 self-cleaning 파이프라인
