#!/usr/bin/env python3
"""
키워드 × 화자 풀 → 대량 multi-speaker 합성.

사용:
    python scripts/batch_multispk_synthesize.py \\
        --keywords ../melotts-kws/examples/keywords.txt \\
        --speaker_embeddings ./speaker_embeddings.pt \\
        --out_dir ./synth_multispk \\
        --speakers_per_keyword 20 \\
        --speed 1.2 \\
        --manifest ./synth_multispk/manifest.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
from pathlib import Path

import torch

from _pipeline import load_pipeline, synthesize_with_clone


def _slug(text: str) -> str:
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^\w\-가-힣]", "", s)
    return s[:40] or "utt"


def _load_keywords(path: Path) -> list[tuple[str, str]]:
    """(utt_id_base, text) — 화자 ID는 합성 시 추가됨."""
    items = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                base, text = line.split("\t", 1)
            else:
                base = f"{_slug(line)}_{i:04d}"
                text = line
            items.append((base.strip(), text.strip()))
    return items


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--keywords", required=True, type=Path)
    p.add_argument("--speaker_embeddings", required=True, type=Path)
    p.add_argument("--out_dir", required=True, type=Path)
    p.add_argument("--speakers_per_keyword", type=int, default=0,
                   help="키워드당 사용할 화자 수 (0=풀 전체 사용)")
    p.add_argument("--speed", type=float, default=1.2)
    p.add_argument("--sample_rate", type=int, default=16000)
    p.add_argument("--device", default="auto")
    p.add_argument("--language", default="KR")
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rng = random.Random(args.seed)

    pipeline = load_pipeline(device=args.device, language=args.language)
    embeddings = torch.load(str(args.speaker_embeddings),
                            map_location=pipeline.device)
    speaker_ids = sorted(embeddings.keys())
    print(f"[batch] 화자 풀 크기: {len(speaker_ids)}")

    items = _load_keywords(args.keywords)
    print(f"[batch] 키워드 수: {len(items)}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[str, str, str, str]] = []  # (utt_id, wav, text, speaker_id)
    fail = 0

    for base_id, text in items:
        # 화자 샘플링
        if args.speakers_per_keyword > 0 and args.speakers_per_keyword < len(speaker_ids):
            chosen = rng.sample(speaker_ids, args.speakers_per_keyword)
        else:
            chosen = speaker_ids

        for spk in chosen:
            utt_id = f"{base_id}__{spk}"
            wav_path = args.out_dir / f"{utt_id}.wav"
            try:
                target_se = embeddings[spk].to(pipeline.device)
                synthesize_with_clone(
                    text=text,
                    target_se=target_se,
                    output=wav_path,
                    pipeline=pipeline,
                    speed=args.speed,
                    sample_rate=args.sample_rate,
                )
                rows.append((utt_id, str(wav_path.resolve()), text, spk))
            except Exception as e:
                print(f"[FAIL] {utt_id}: {e}", file=sys.stderr)
                fail += 1

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        with args.manifest.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["utt_id", "wav", "text", "speaker_id"])
            w.writerows(rows)
        print(f"[OK] manifest: {args.manifest}")

    print(f"[DONE] success={len(rows)} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
