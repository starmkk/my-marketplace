#!/usr/bin/env python3
"""
편의 스크립트: 합성 데이터셋 ↦ ASR ↦ Round-trip QA ↦ 필터링을 한 번에.

사용:
    python scripts/filter_synth_dataset.py \\
        --in_dir ../openvoice-v2-kws/synth_multispk_aug \\
        --source_manifest ../openvoice-v2-kws/synth_multispk/manifest.csv \\
        --workdir ./qa_workdir \\
        --cer_threshold 0.30
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# 환경변수 게이트: subprocess로 batch_transcribe.py를 spawn하기 전에 빠르게 실패시킨다.
from _env import ensure_gemma4_env

ensure_gemma4_env()


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        raise SystemExit(f"[ERR] 명령 실패 (rc={proc.returncode})")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in_dir", required=True, type=Path,
                   help="ASR 대상 wav 디렉토리 (보통 augmented 합성 결과)")
    p.add_argument("--source_manifest", required=True, type=Path,
                   help="합성 시 만든 manifest (utt_id, wav, text, ...)")
    p.add_argument("--workdir", required=True, type=Path,
                   help="중간 산출물(asr_results.csv, qa_report.csv)을 둘 디렉토리")
    p.add_argument("--cer_threshold", type=float, default=0.30)
    p.add_argument("--language", default="Korean")
    p.add_argument("--device", default="auto",
                   choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--limit", type=int, default=0,
                   help="처음 N개만 (디버그용)")
    p.add_argument("--resume", action="store_true",
                   help="batch_transcribe 단계에서 기존 결과 이어쓰기")
    args = p.parse_args()

    args.workdir.mkdir(parents=True, exist_ok=True)
    asr_csv = args.workdir / "asr_results.csv"
    report_csv = args.workdir / "qa_report.csv"
    filtered_csv = args.workdir / "filtered_manifest.csv"

    here = Path(__file__).resolve().parent
    py = sys.executable

    # Step 1: batch transcribe
    cmd1 = [
        py, str(here / "batch_transcribe.py"),
        "--in_dir", str(args.in_dir),
        "--out_csv", str(asr_csv),
        "--language", args.language,
        "--device", args.device,
    ]
    if args.limit > 0:
        cmd1 += ["--limit", str(args.limit)]
    if args.resume:
        cmd1 += ["--resume"]
    run(cmd1)

    # Step 2: round-trip QA
    cmd2 = [
        py, str(here / "round_trip_qa.py"),
        "--source_manifest", str(args.source_manifest),
        "--asr_results", str(asr_csv),
        "--out_report", str(report_csv),
        "--out_filtered_manifest", str(filtered_csv),
        "--cer_threshold", str(args.cer_threshold),
    ]
    run(cmd2)

    print("\n=================================================================")
    print("[ALL DONE]")
    print(f"  ASR 결과:   {asr_csv}")
    print(f"  QA 보고서:  {report_csv}")
    print(f"  필터 manifest: {filtered_csv}")
    print(f"\n다음 단계: melotts-kws/scripts/make_wekws_manifest.py로 wekws .list 생성")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
