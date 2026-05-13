#!/usr/bin/env python3
"""
화자 풀 디렉토리 → speaker embedding 사전 추출.

권장 입력 구조:
    pool_dir/
      spk_001/  ref.wav     (또는 다수 wav)
      spk_002/  ref.wav
      ...

출력: torch .pt 파일 — {speaker_id: tensor}

사용:
    python scripts/prepare_speaker_pool.py \\
        --pool_dir ~/datasets/kws_speaker_pool \\
        --out_embeddings ./speaker_embeddings.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

from _pipeline import load_pipeline, extract_target_se


def _find_ref_wav(spk_dir: Path) -> Path | None:
    """spk 폴더에서 reference wav 1개 선택. 가장 큰 wav를 사용."""
    cands = list(spk_dir.rglob("*.wav")) + list(spk_dir.rglob("*.WAV"))
    if not cands:
        return None
    cands.sort(key=lambda p: p.stat().st_size, reverse=True)
    return cands[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pool_dir", required=True, type=Path,
                   help="화자별 폴더가 있는 루트")
    p.add_argument("--out_embeddings", required=True, type=Path,
                   help="출력 .pt 파일 (dict 저장)")
    p.add_argument("--device", default="auto")
    p.add_argument("--vad", action="store_true", default=True,
                   help="VAD로 무음 제거")
    p.add_argument("--no_vad", action="store_false", dest="vad")
    args = p.parse_args()

    pipeline = load_pipeline(device=args.device)

    spk_dirs = sorted([d for d in args.pool_dir.iterdir() if d.is_dir()])
    if not spk_dirs:
        raise SystemExit(f"[ERR] {args.pool_dir} 안에 화자 폴더 없음")

    embeddings: dict[str, torch.Tensor] = {}
    fail = 0
    for spk_dir in spk_dirs:
        ref = _find_ref_wav(spk_dir)
        if ref is None:
            print(f"[skip] {spk_dir.name}: wav 없음", file=sys.stderr)
            fail += 1
            continue
        try:
            se = extract_target_se(ref, pipeline, vad=args.vad)
            # cpu로 옮겨서 저장 (GPU 텐서 직렬화 회피)
            embeddings[spk_dir.name] = se.detach().cpu()
            print(f"[OK]   {spk_dir.name}: {ref.name}")
        except Exception as e:
            print(f"[FAIL] {spk_dir.name} ({ref.name}): {e}", file=sys.stderr)
            fail += 1

    args.out_embeddings.parent.mkdir(parents=True, exist_ok=True)
    torch.save(embeddings, str(args.out_embeddings))
    print(f"\n[DONE] {len(embeddings)}/{len(spk_dirs)} 화자 임베딩 저장 → {args.out_embeddings}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
