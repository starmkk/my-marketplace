#!/usr/bin/env python3
"""
MeloTTS 키워드 리스트 → 대량 합성.

입력 파일 형식 (각 줄):
    텍스트
또는
    utt_id<TAB>텍스트

예:
    오케이 케이티
    okk_001	오케이 케이티

사용:
    python scripts/batch_synthesize.py \\
        --keywords examples/keywords.txt \\
        --out_dir ./synth_raw \\
        --sample_rate 16000 \\
        --speed 1.2
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from synthesize import synthesize  # 같은 폴더 내 모듈


def _slug(text: str) -> str:
    """파일명용 슬러그 (한글은 유지)."""
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^\w\-가-힣]", "", s)
    return s[:40] or "utt"


def _load_keywords(path: Path) -> list[tuple[str, str]]:
    """(utt_id, text) 리스트 반환. utt_id가 없으면 자동 생성."""
    items: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                utt_id, text = line.split("\t", 1)
            else:
                utt_id = f"{_slug(line)}_{i:04d}"
                text = line
            items.append((utt_id.strip(), text.strip()))
    return items


def main() -> int:
    p = argparse.ArgumentParser(description="MeloTTS 대량 합성")
    p.add_argument("--keywords", required=True, type=Path,
                   help="키워드 텍스트 파일 (한 줄당 하나, 또는 utt_id<TAB>text)")
    p.add_argument("--out_dir", required=True, type=Path,
                   help="출력 디렉토리 (wav 파일들이 여기로)")
    p.add_argument("--sample_rate", type=int, default=16000)
    p.add_argument("--speed", type=float, default=1.2,
                   help="한국어 모델은 1.2 권장")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--manifest", type=Path, default=None,
                   help="(선택) utt_id, wav_path, text 매핑 CSV 출력")
    args = p.parse_args()

    items = _load_keywords(args.keywords)
    if not items:
        raise SystemExit(f"[ERR] 비어있는 키워드 파일: {args.keywords}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[batch] {len(items)}개 발화 합성 시작 → {args.out_dir}")

    rows: list[tuple[str, str, str]] = []
    for utt_id, text in items:
        wav_path = args.out_dir / f"{utt_id}.wav"
        try:
            synthesize(
                text=text,
                output=wav_path,
                speed=args.speed,
                sample_rate=args.sample_rate,
                device=args.device,
            )
            rows.append((utt_id, str(wav_path.resolve()), text))
        except Exception as e:
            print(f"[FAIL] {utt_id} ({text!r}): {e}", file=sys.stderr)

    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        with args.manifest.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["utt_id", "wav", "text"])
            w.writerows(rows)
        print(f"[OK] manifest: {args.manifest}")

    print(f"[DONE] success={len(rows)}/{len(items)}")
    return 0 if len(rows) == len(items) else 1


if __name__ == "__main__":
    sys.exit(main())
