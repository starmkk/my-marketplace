#!/usr/bin/env python3
"""
디렉토리 내 wav 파일들을 Gemma 4로 일괄 transcribe.

출력 CSV 컬럼: wav_path, transcribed_text, processing_time_sec, error

사용:
    python scripts/batch_transcribe.py \\
        --in_dir ../openvoice-v2-kws/synth_multispk_aug \\
        --out_csv ./asr_results.csv \\
        --language Korean
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# 환경변수 게이트: 무거운 의존성(torch 등) 로드보다 먼저 검증해야 한다.
from _env import ensure_gemma4_env

ensure_gemma4_env()

from _asr import load_asr, transcribe_audio  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in_dir", required=True, type=Path)
    p.add_argument("--out_csv", required=True, type=Path)
    p.add_argument("--language", default="Korean")
    p.add_argument("--device", default="auto",
                   choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--max_new_tokens", type=int, default=128)
    p.add_argument("--limit", type=int, default=0,
                   help="처음 N개만 처리 (디버그/속도 측정용). 0=무제한.")
    p.add_argument("--resume", action="store_true",
                   help="기존 out_csv가 있으면 이미 처리된 wav는 건너뜀")
    args = p.parse_args()

    wavs = sorted(args.in_dir.rglob("*.wav"))
    if not wavs:
        raise SystemExit(f"[ERR] {args.in_dir}에 wav 없음")
    if args.limit > 0:
        wavs = wavs[: args.limit]
    print(f"[batch] 총 {len(wavs)}개 wav")

    # resume 모드: 이미 처리된 파일 스킵
    done: set[str] = set()
    if args.resume and args.out_csv.exists():
        with args.out_csv.open("r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                done.add(row["wav_path"])
        print(f"[batch] resume — 기존 완료 {len(done)}개")

    asr = load_asr(prefer_device=args.device)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)

    # append vs new
    write_header = not (args.resume and args.out_csv.exists())
    mode = "a" if (args.resume and args.out_csv.exists()) else "w"

    fail = 0
    t_total_start = time.time()

    with args.out_csv.open(mode, encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["wav_path", "transcribed_text", "processing_time_sec", "error"])

        for i, wav in enumerate(wavs, 1):
            wav_abs = str(wav.resolve())
            if wav_abs in done:
                continue

            t0 = time.time()
            try:
                text = transcribe_audio(
                    audio_path=wav,
                    language=args.language,
                    asr=asr,
                    max_new_tokens=args.max_new_tokens,
                )
                err = ""
            except Exception as e:
                text = ""
                err = f"{type(e).__name__}: {e}"
                fail += 1

            dt = time.time() - t0
            w.writerow([wav_abs, text, f"{dt:.3f}", err])
            f.flush()  # crash 시 진행상황 보존

            if i % 10 == 0 or i == len(wavs):
                rate = i / (time.time() - t_total_start)
                print(f"[batch] {i}/{len(wavs)}  ({rate:.2f} wav/s)  last={text[:40]!r}")

    print(f"\n[DONE] success={len(wavs) - fail} fail={fail} → {args.out_csv}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
