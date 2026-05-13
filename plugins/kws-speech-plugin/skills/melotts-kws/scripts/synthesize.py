#!/usr/bin/env python3
"""
MeloTTS 단일 문장 합성 (테스트/데모용).

사용 예:
    python scripts/synthesize.py --text "오케이 케이티" --output ./out/test.wav
    python scripts/synthesize.py --text "헤이 케이티" --output ./out/h.wav --speed 1.2 --sample_rate 16000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

try:
    import librosa
except ImportError:
    librosa = None


def _select_device(prefer: str = "auto") -> str:
    """Mac MPS, CUDA, CPU 중 사용 가능한 디바이스 자동 선택."""
    import torch
    if prefer != "auto":
        return prefer
    if torch.backends.mps.is_available():
        # MeloTTS의 일부 op이 MPS에서 깨지는 경우가 있어 기본은 cpu로.
        # GPU 가속이 꼭 필요하면 --device mps 명시.
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def synthesize(
    text: str,
    output: Path,
    speed: float = 1.0,
    sample_rate: int = 16000,
    device: str = "auto",
    speaker: str = "KR",
    language: str = "KR",
) -> Path:
    """한 문장을 합성하여 wav로 저장. 자동으로 16kHz mono로 리샘플링."""
    from melo.api import TTS

    dev = _select_device(device)
    print(f"[synth] device={dev} lang={language} speed={speed} sr={sample_rate}")

    tts = TTS(language=language, device=dev)
    spk2id = tts.hps.data.spk2id
    if speaker not in spk2id:
        raise SystemExit(
            f"[ERR] speaker '{speaker}' 없음. 사용 가능: {list(spk2id.keys())}"
        )
    spk_id = spk2id[speaker]

    output.parent.mkdir(parents=True, exist_ok=True)

    # MeloTTS는 내부적으로 자체 sample rate(보통 44.1kHz)로 wav를 저장한다.
    # 그래서 일단 임시 경로에 저장한 뒤 16kHz mono로 리샘플링한다.
    tmp_path = output.with_suffix(".raw.wav")
    tts.tts_to_file(text, spk_id, str(tmp_path), speed=speed)

    audio, sr_orig = sf.read(str(tmp_path), always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)  # to mono
    if sr_orig != sample_rate:
        if librosa is None:
            raise SystemExit("[ERR] librosa가 필요합니다 (pip install librosa).")
        audio = librosa.resample(audio.astype(np.float32),
                                 orig_sr=sr_orig, target_sr=sample_rate)
    # 16-bit PCM으로 저장 (KWS 표준)
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(output), (audio * 32767).astype(np.int16), sample_rate, subtype="PCM_16")
    tmp_path.unlink(missing_ok=True)

    print(f"[OK] {output}  ({len(audio)/sample_rate:.2f}s @ {sample_rate}Hz mono)")
    return output


def main() -> int:
    p = argparse.ArgumentParser(description="MeloTTS 단일 문장 합성")
    p.add_argument("--text", required=True, help="합성할 텍스트 (한국어)")
    p.add_argument("--output", required=True, type=Path, help="출력 WAV 경로")
    p.add_argument("--speed", type=float, default=1.0, help="발화 속도 (한국어는 1.2~1.3 권장)")
    p.add_argument("--sample_rate", type=int, default=16000, help="출력 샘플레이트 (KWS는 16000)")
    p.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    p.add_argument("--speaker", default="KR")
    p.add_argument("--language", default="KR")
    args = p.parse_args()

    synthesize(
        text=args.text,
        output=args.output,
        speed=args.speed,
        sample_rate=args.sample_rate,
        device=args.device,
        speaker=args.speaker,
        language=args.language,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
