# wekws 데이터 manifest 포맷

wekws는 wenet 기반이며, 학습 데이터를 **JSON-Lines 포맷의 `.list` 파일**로 받는다
(또는 shards로 묶은 `.tar`. 본 스킬은 raw `.list`만 다룸).

## 파일 형식

각 줄에 한 개의 JSON 객체:
```jsonlines
{"key": "okk_0001__sp1.00_pt0_g0", "wav": "/abs/path/to.wav", "txt": "오케이 케이티", "label": 0}
{"key": "okk_0001__sp0.90_pt-2_g0", "wav": "/abs/path/to.wav", "txt": "오케이 케이티", "label": 0}
{"key": "neg_0001", "wav": "/abs/path/neg.wav", "txt": "안녕하세요", "label": -1}
```

## 필드 의미

| 필드 | 타입 | 설명 |
|---|---|---|
| `key` | str | 발화 고유 ID. 보통 파일 stem 사용. |
| `wav` | str | 절대 경로. wenet/wekws가 직접 읽음. 상대경로 X. |
| `txt` | str | transcript. KWS에선 키워드 자체. negative는 임의 텍스트. |
| `label` | int | 키워드 인덱스. negative는 `-1` (또는 모델 설정에 따라 `num_keywords`). |

## 라벨 규칙

- 키워드별로 0, 1, 2... 순서대로 정수 라벨 부여.
- "키워드가 아닌 발화"(negative)는 학습 시 사용하는 loss 종류에 따라:
  - **Max-pooling loss**: negative=`-1` 또는 `num_keywords`
  - **CTC loss**: 키워드 token sequence가 없는 transcript
  - **MMI loss**: anti-keyword set

본 스킬은 기본값 `-1`로 negative를 표기 (사용자 wekws 설정에 맞춰 조정 필요).

## 위치

본 스킬에서는 wekws 프로젝트 구조와 동일하게:
```
wekws_v2/examples/korean_kws/s0/
├── data/
│   ├── train.list           # 실데이터
│   ├── synth_train.list     # ← 본 스킬이 생성
│   ├── dev.list
│   └── test.list
└── ...
```

학습 시 두 파일을 합쳐서 사용:
```bash
cat data/train.list data/synth_train.list > data/train_mixed.list
```

또는 wekws의 `data_list_files` 옵션으로 여러 파일 동시 지정 (버전에 따라 상이).

## 검증

manifest 생성 후 다음을 확인:
```bash
# 라인 수
wc -l data/synth_train.list

# 라벨 분포
jq -r '.label' data/synth_train.list | sort | uniq -c

# 첫 줄 미리보기
head -1 data/synth_train.list | jq .

# 모든 wav 파일 존재 여부
jq -r '.wav' data/synth_train.list | xargs -I{} test -f {} && echo OK || echo MISSING
```

## 흔한 실수

1. **상대경로 사용** → 학습 디렉토리에서 못 찾음. 항상 `Path.resolve()`로 절대경로.
2. **한글 escape** — `ensure_ascii=False`로 저장해야 가독성/파싱 모두 OK.
3. **라벨 누락** — `keyword_map.json`에 없는 키워드는 negative(-1)로 떨어진다. 의도한 결과인지 확인.
4. **shards vs raw** — 데이터 양이 100만 건 넘어가면 raw `.list`는 I/O 병목. 그땐 wenet의 `make_shard_list.py`로 tar shards 생성 권장.
