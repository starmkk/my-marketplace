#!/usr/bin/env python3
"""
단일 wav를 Gemma 4로 transcribe.

사용:
    python scripts/transcribe.py --audio /path/to/wav.wav
    python scripts/transcribe.py --audio /path/to/wav.wav --language Korean
    python scripts/transcribe.py --audio /path/to/wav.wav --device cpu
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 환경변수 게이트: 무거운 의존성(torch 등) 로드보다 먼저 검증해야 한다.
from _env import ensure_gemma4_env

ensure_gemma4_env()

from _asr import load_asr, transcribe_audio  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--audio", required=True, type=Path)
    p.add_argument("--language", default="Korean",
                   help="ASR 언어 (Korean, English, ...). 기본 Korean.")
    p.add_argument("--device", default="auto",
                   choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--max_new_tokens", type=int, default=128,
                   help="생성 최대 토큰 수. KWS 키워드는 짧으니 기본 128로 충분.")
    p.add_argument("--quiet", action="store_true",
                   help="결과 텍스트만 출력 (다른 로그는 stderr로)")
    args = p.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"[ERR] 파일 없음: {args.audio}")

    asr = load_asr(prefer_device=args.device)
    text = transcribe_audio(
        audio_path=args.audio,
        language=args.language,
        asr=asr,
        max_new_tokens=args.max_new_tokens,
    )

    if args.quiet:
        print(text)
    else:
        print(f"[input]  {args.audio}")
        print(f"[output] {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
