# melotts-kws

MeloTTS로 한국어 KWS 학습/평가용 합성 데이터를 만드는 Claude Code 스킬.

## 디렉토리 구조

```
melotts-kws/
├── SKILL.md                  # Claude가 읽는 메인 스킬 문서
├── README.md                 # 이 파일
├── scripts/
│   ├── install.sh            # 환경 구축
│   ├── synthesize.py         # 단일 문장 합성
│   ├── batch_synthesize.py   # 키워드 리스트 → 대량 wav
│   ├── augment_audio.py      # speed/pitch/noise/RIR 증강
│   └── make_wekws_manifest.py# wekws .list 파일 생성
├── references/
│   ├── melotts_korean.md
│   ├── kws_augmentation.md
│   └── wekws_data_format.md
└── examples/
    ├── keywords.txt
    ├── keyword_map.json
    └── augment_config.yaml
```

## 빠른 시작 (5단계)

```bash
cd ~/Documents/claude/skills/melotts-kws

# 1. 설치
bash scripts/install.sh

# 2. venv 활성화
source ~/Documents/work_2026/KWS/melotts_env/bin/activate

# 3. 단일 문장 테스트
python scripts/synthesize.py \
  --text "오케이 케이티" \
  --output ./out/test.wav

# 4. 키워드 리스트 대량 합성
python scripts/batch_synthesize.py \
  --keywords examples/keywords.txt \
  --out_dir ./synth_raw \
  --manifest ./synth_raw/manifest.csv

# 5. 화자 다양성 증강
python scripts/augment_audio.py \
  --in_dir ./synth_raw \
  --out_dir ./synth_aug \
  --config examples/augment_config.yaml

# 6. wekws manifest 생성
python scripts/make_wekws_manifest.py \
  --in_dir ./synth_aug \
  --source_manifest ./synth_raw/manifest.csv \
  --keyword_map examples/keyword_map.json \
  --out ./data/synth_train.list
```

## Claude Code에 등록하는 법

이 폴더를 그대로 다음 중 한 곳으로 옮기거나 심볼릭 링크:

- **글로벌 스킬**: `~/.claude/skills/melotts-kws/`
- **프로젝트 전용**: `<project>/.claude/skills/melotts-kws/`

```bash
# 글로벌로 등록
ln -s ~/Documents/claude/skills/melotts-kws ~/.claude/skills/melotts-kws

# 또는 wekws_v2 프로젝트 전용
ln -s ~/Documents/claude/skills/melotts-kws \
      ~/Documents/work_2026/KWS/wekws_v2/.claude/skills/melotts-kws
```

## 핵심 주의사항

1. **Gemma 4 E2B-it는 TTS가 아니다.** ASR/번역만 가능. 본 스킬은 MeloTTS를 사용.
2. **MeloTTS 한국어는 단일 화자.** 화자 다양성은 augmentation으로 보완.
3. **합성-only 학습은 위험.** 실데이터와 1:1~3:1로 섞고, 평가는 반드시 실데이터로.
4. **MIT License.** KT 사내/상업 활용 가능.

## 다음 단계 아이디어

- [ ] OpenVoice (MyShell의 voice cloning 모델)을 추가해 진짜 multi-speaker 만들기
- [ ] Gemma 4 E2B-it ASR로 round-trip QA (합성 → ASR → 텍스트 일치 확인)
- [ ] wekws 학습 스크립트와 직접 연동 (`run_synth.sh`)
- [ ] tar shards로 변환 (대용량 학습용)
