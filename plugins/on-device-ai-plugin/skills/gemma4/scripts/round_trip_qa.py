#!/usr/bin/env python3
"""
Round-trip QA: ASR 결과와 원본 텍스트를 비교해 CER/WER 계산 및 필터링.

입력:
- source_manifest.csv: utt_id, wav, text [, ...]    (합성 시 만든 manifest)
- asr_results.csv:     wav_path, transcribed_text, ...  (batch_transcribe 결과)

출력:
- qa_report.csv:       모든 발화의 점수 (분석용)
- filtered_manifest.csv: CER < threshold 통과한 발화만 (학습용)

사용:
    python scripts/round_trip_qa.py \\
        --source_manifest ../openvoice-v2-kws/synth_multispk/manifest.csv \\
        --asr_results ./asr_results.csv \\
        --out_report ./qa_report.csv \\
        --out_filtered_manifest ./filtered_manifest.csv \\
        --cer_threshold 0.30
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

# 환경변수 게이트: _asr가 torch를 import하기 전에 검증.
from _env import ensure_gemma4_env

ensure_gemma4_env()

from _asr import normalize_korean  # noqa: E402

try:
    from jiwer import cer as jiwer_cer, wer as jiwer_wer
except ImportError:
    raise SystemExit("[ERR] jiwer 필요: pip install jiwer")


def _load_source_manifest(path: Path) -> dict[str, dict]:
    """wav 절대경로 → row dict."""
    by_wav = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            wav_abs = str(Path(row["wav"]).resolve())
            by_wav[wav_abs] = row
    return by_wav


def _load_asr_results(path: Path) -> dict[str, str]:
    """wav 절대경로 → transcribed_text."""
    by_wav = {}
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            wav_abs = str(Path(row["wav_path"]).resolve())
            by_wav[wav_abs] = row.get("transcribed_text", "")
    return by_wav


def _safe_metric(fn, ref: str, hyp: str) -> float:
    """jiwer는 빈 문자열에 대해 예외를 던질 수 있어 가드."""
    if not ref:
        return 1.0 if hyp else 0.0
    try:
        return float(fn(ref, hyp))
    except Exception:
        return 1.0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source_manifest", required=True, type=Path,
                   help="합성 시 만든 manifest (utt_id, wav, text, ...)")
    p.add_argument("--asr_results", required=True, type=Path,
                   help="batch_transcribe.py 출력 CSV")
    p.add_argument("--out_report", required=True, type=Path,
                   help="모든 발화의 QA 점수 CSV (분석용)")
    p.add_argument("--out_filtered_manifest", type=Path, default=None,
                   help="필터링 통과 발화만 담은 manifest CSV (학습용)")
    p.add_argument("--cer_threshold", type=float, default=0.30,
                   help="CER 임계값. 이 이하 통과. 기본 0.30")
    p.add_argument("--metric", default="cer", choices=["cer", "wer"],
                   help="필터링 기준 메트릭. 한국어는 cer 권장.")
    args = p.parse_args()

    src = _load_source_manifest(args.source_manifest)
    asr = _load_asr_results(args.asr_results)
    print(f"[qa] source manifest: {len(src)}개")
    print(f"[qa] asr results:     {len(asr)}개")

    # 매칭
    matched = [w for w in src if w in asr]
    print(f"[qa] 매칭: {len(matched)}/{len(src)}")
    if not matched:
        raise SystemExit("[ERR] source ↔ asr 매칭 0건. wav 경로 형식 확인 필요.")

    # 점수 계산
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    pass_count = 0

    for wav in matched:
        ref_raw = src[wav].get("text", "")
        hyp_raw = asr[wav]
        ref = normalize_korean(ref_raw)
        hyp = normalize_korean(hyp_raw)
        cer_v = _safe_metric(jiwer_cer, ref, hyp)
        wer_v = _safe_metric(jiwer_wer, ref, hyp)
        metric_v = cer_v if args.metric == "cer" else wer_v
        passed = metric_v <= args.cer_threshold
        if passed:
            pass_count += 1

        rows.append({
            **src[wav],
            "transcribed": hyp_raw,
            "cer": f"{cer_v:.4f}",
            "wer": f"{wer_v:.4f}",
            "passed": "1" if passed else "0",
        })

    # 보고서
    fieldnames = list(rows[0].keys())
    with args.out_report.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    pass_rate = pass_count / len(rows) * 100
    print(f"\n[REPORT] {args.out_report}")
    print(f"  total:        {len(rows)}")
    print(f"  passed:       {pass_count} ({pass_rate:.1f}%)")
    print(f"  threshold:    {args.metric} <= {args.cer_threshold}")
    avg_cer = sum(float(r["cer"]) for r in rows) / len(rows)
    avg_wer = sum(float(r["wer"]) for r in rows) / len(rows)
    print(f"  avg CER:      {avg_cer:.4f}")
    print(f"  avg WER:      {avg_wer:.4f}")

    # 필터된 manifest
    if args.out_filtered_manifest:
        passed_rows = [r for r in rows if r["passed"] == "1"]
        # 원본 manifest 컬럼만 유지 (transcribed/cer/wer/passed 제외)
        keep_cols = [c for c in fieldnames if c not in ("transcribed", "cer", "wer", "passed")]
        args.out_filtered_manifest.parent.mkdir(parents=True, exist_ok=True)
        with args.out_filtered_manifest.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keep_cols)
            w.writeheader()
            for r in passed_rows:
                w.writerow({c: r[c] for c in keep_cols})
        print(f"\n[FILTERED MANIFEST] {args.out_filtered_manifest}")
        print(f"  records: {len(passed_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
