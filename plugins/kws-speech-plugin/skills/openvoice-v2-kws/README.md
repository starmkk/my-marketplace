# openvoice-v2-kws

OpenVoice V2 + MeloTTS-Korean으로 한국어 KWS 학습용 멀티화자 합성 데이터를 만드는 스킬.
`melotts-kws`의 단일 화자 한계를 voice cloning으로 극복한다.

## 디렉토리 구조

```
openvoice-v2-kws/
├── SKILL.md
├── README.md
├── scripts/
│   ├── install.sh                       # OpenVoice + MeloTTS + ckpt 다운로드
│   ├── _pipeline.py                     # 공통 파이프라인 (싱글톤 캐시)
│   ├── prepare_speaker_pool.py          # 화자 풀 → speaker embedding 사전 추출
│   ├── clone_synthesize.py              # 단일 합성 (텍스트 + reference)
│   └── batch_multispk_synthesize.py     # 키워드 × 화자 풀 → 대량 합성
├── references/
│   ├── openvoice_v2.md                  # API 상세
│   ├── speaker_pool_strategy.md         # 화자 풀 구성
│   └── kws_multispeaker_aug.md          # 학습 베스트 프랙티스
└── examples/
    └── speaker_refs/                    # 화자 reference wav 예시 위치
```

## 빠른 시작

```bash
cd ~/Documents/claude/skills/openvoice-v2-kws

# 1. 설치 (OpenVoice + MeloTTS + 체크포인트 ~200MB 다운로드)
bash scripts/install.sh

# 2. venv 활성화
source ~/Documents/work_2026/KWS/openvoice_env/bin/activate
export OPENVOICE_CKPT_DIR=~/Documents/work_2026/KWS/OpenVoice/checkpoints_v2

# 3. 화자 풀 준비 (여러분의 reference wav를 spk_xxx/ 폴더에 배치)
ls ~/datasets/kws_speaker_pool
# spk_001  spk_002  spk_003  ...

# 4. 화자별 embedding 한 번 추출 (재사용 가능)
python scripts/prepare_speaker_pool.py \
  --pool_dir ~/datasets/kws_speaker_pool \
  --out_embeddings ./speaker_embeddings.pt

# 5. 단일 화자 테스트 합성
python scripts/clone_synthesize.py \
  --text "오케이 케이티" \
  --speaker_embeddings ./speaker_embeddings.pt \
  --speaker_id spk_001 \
  --output ./out/test.wav

# 6. 키워드 × 화자 풀 대량 합성
python scripts/batch_multispk_synthesize.py \
  --keywords ../melotts-kws/examples/keywords.txt \
  --speaker_embeddings ./speaker_embeddings.pt \
  --out_dir ./synth_multispk \
  --speakers_per_keyword 30 \
  --speed 1.2 \
  --manifest ./synth_multispk/manifest.csv

# 7. (권장) acoustic augmentation으로 도메인 갭 해소
python ../melotts-kws/scripts/augment_audio.py \
  --in_dir ./synth_multispk \
  --out_dir ./synth_multispk_aug \
  --config ../melotts-kws/examples/augment_config.yaml

# 8. wekws manifest 생성
python ../melotts-kws/scripts/make_wekws_manifest.py \
  --in_dir ./synth_multispk_aug \
  --source_manifest ./synth_multispk/manifest.csv \
  --keyword_map ../melotts-kws/examples/keyword_map.json \
  --out ./data/synth_multispk_train.list
```

## Claude Code에 등록

```bash
ln -s ~/Documents/claude/skills/openvoice-v2-kws ~/.claude/skills/openvoice-v2-kws
```

또는 wekws_v2 프로젝트 전용:
```bash
ln -s ~/Documents/claude/skills/openvoice-v2-kws \
      ~/Documents/work_2026/KWS/wekws_v2/.claude/skills/openvoice-v2-kws
```

## 핵심 설계 결정

1. **MeloTTS를 base TTS로 사용** — OpenVoice는 tone color converter 역할만. 발음/억양은 MeloTTS-KR이 담당.
2. **Speaker embedding 사전 추출** — 100명 풀이라면 한 번 추출 후 모든 합성에 재사용. 시간 절약.
3. **싱글톤 파이프라인** — `_pipeline.py`에서 모델을 한 번만 로드하여 batch 합성 시 모델 재로드 비용 제거.
4. **`melotts-kws` 스킬 재사용** — augmentation, manifest 생성은 그대로 가져다 씀. 코드 중복 X.

## 라이선스
- OpenVoice V2: MIT (2024년 4월부터)
- MeloTTS: MIT
- 둘 다 KT 사내/상업 활용 가능

## 다음 단계
- AIHub 데이터셋 어댑터 (`prepare_speaker_pool_aihub.py`)
- Gemma 4 ASR 기반 round-trip QA 자동 필터
- wekws 학습 스크립트 직접 통합
