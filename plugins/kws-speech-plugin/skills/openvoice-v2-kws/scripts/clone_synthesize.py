#!/usr/bin/env python3
"""
단일 문장 + 단일 reference 화자로 voice cloning 합성.

사용:
    python scripts/clone_synthesize.py \\
        --text "오케이 케이티" \\
        --reference /path/to/ref.wav \\
        --output ./out/cloned.wav \\
        --speed 1.2

또는 미리 추출된 embedding 사용:
    python scripts/clone_synthesize.py \\
        --text "오케이 케이티" \\
        --speaker_embeddings ./speaker_embeddings.pt \\
        --speaker_id spk_001 \\
        --output ./out/cloned.wav
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from _pipeline import load_pipeline, extract_target_se, synthesize_with_clone


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--output", required=True, type=Path)

    # 화자 지정: 두 가지 방법 중 하나
    p.add_argument("--reference", type=Path,
                   help="reference wav 경로 (즉석 embedding 추출)")
    p.add_argument("--speaker_embeddings", type=Path,
                   help="prepare_speaker_pool.py가 만든 .pt")
    p.add_argument("--speaker_id", type=str,
                   help="speaker_embeddings 내 특정 ID")

    p.add_argument("--speed", type=float, default=1.2)
    p.add_argument("--sample_rate", type=int, default=16000)
    p.add_argument("--device", default="auto")
    p.add_argument("--language", default="KR")
    args = p.parse_args()

    pipeline = load_pipeline(device=args.device, language=args.language)

    # target embedding 결정
    if args.reference:
        if not args.reference.exists():
            raise SystemExit(f"[ERR] reference wav 없음: {args.reference}")
        target_se = extract_target_se(args.reference, pipeline)
    elif args.speaker_embeddings and args.speaker_id:
        embeddings = torch.load(str(args.speaker_embeddings),
                                map_location=pipeline.device)
        if args.speaker_id not in embeddings:
            raise SystemExit(
                f"[ERR] '{args.speaker_id}' 없음. 사용 가능: {list(embeddings.keys())[:10]}..."
            )
        target_se = embeddings[args.speaker_id].to(pipeline.device)
    else:
        raise SystemExit(
            "[ERR] --reference 또는 (--speaker_embeddings + --speaker_id) 필요"
        )

    out = synthesize_with_clone(
        text=args.text,
        target_se=target_se,
        output=args.output,
        pipeline=pipeline,
        speed=args.speed,
        sample_rate=args.sample_rate,
    )
    print(f"[OK] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
