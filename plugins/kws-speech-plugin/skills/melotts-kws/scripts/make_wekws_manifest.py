#!/usr/bin/env python3
"""
augment된 wav 디렉토리 → wekws 호환 manifest (.list 파일).

wekws는 wenet 기반의 raw 데이터 포맷을 사용한다 (한 줄에 JSON 한 개):
    {"key": "utt_001", "wav": "/abs/path/to.wav", "txt": "오케이 케이티", "label": 0}

- key: utterance id (파일 stem 사용)
- wav: 절대 경로 (학습 시 wenet/wekws가 직접 읽음)
- txt: transcript (KWS에선 keyword 자체)
- label: 키워드 인덱스 (keyword_map.json에서 매핑). negative는 -1.

키워드 매핑 (`keyword_map.json`) 예:
    {
      "오케이 케이티": 0,
      "헤이 케이티": 1,
      "지니야": 2
    }

파일명에서 원본 키워드를 복원하기 위해, batch_synthesize.py가 만든 manifest CSV를
함께 받는 것이 가장 안전하다 (--source_manifest).

사용:
    python scripts/make_wekws_manifest.py \\
        --in_dir ./synth_aug \\
        --source_manifest ./synth_raw/manifest.csv \\
        --keyword_map examples/keyword_map.json \\
        --out ./data/synth_train.list
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _load_source_manifest(path: Path) -> dict[str, str]:
    """utt_id -> text 매핑."""
    out = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["utt_id"]] = row["text"]
    return out


def _utt_id_from_aug_filename(stem: str) -> str:
    """augment_audio.py가 만든 파일명: '{utt_id}__sp1.00_pt0_g0.wav' → utt_id 추출."""
    return stem.split("__", 1)[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in_dir", required=True, type=Path,
                   help="augment된 wav가 있는 디렉토리")
    p.add_argument("--source_manifest", type=Path, required=True,
                   help="batch_synthesize.py가 만든 utt_id↔text 매핑 CSV")
    p.add_argument("--keyword_map", type=Path, required=True,
                   help="keyword(text)→label_index 매핑 JSON")
    p.add_argument("--out", required=True, type=Path,
                   help="출력 manifest (.list, JSONLines)")
    p.add_argument("--default_label", type=int, default=-1,
                   help="keyword_map에 없는 텍스트의 라벨 (negative=-1)")
    args = p.parse_args()

    src = _load_source_manifest(args.source_manifest)
    kw_map = json.loads(args.keyword_map.read_text(encoding="utf-8"))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n_total, n_pos, n_neg, n_miss = 0, 0, 0, 0

    with args.out.open("w", encoding="utf-8") as f_out:
        for wav in sorted(args.in_dir.rglob("*.wav")):
            base_id = _utt_id_from_aug_filename(wav.stem)
            text = src.get(base_id)
            if text is None:
                n_miss += 1
                continue
            label = kw_map.get(text, args.default_label)
            if label == args.default_label:
                n_neg += 1
            else:
                n_pos += 1

            row = {
                "key": wav.stem,
                "wav": str(wav.resolve()),
                "txt": text,
                "label": int(label),
            }
            f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_total += 1

    print(f"[OK] {args.out}")
    print(f"     total={n_total} positive={n_pos} negative={n_neg} missing={n_miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
