#!/usr/bin/env python3
"""
KWS 화자 다양성 augmentation.

MeloTTS 한국어 모델은 단일 화자이므로 단순 합성만으로는 화자 다양성이 없다.
이 스크립트는 다음을 적용해 1개 wav를 N개 변형으로 확장한다:

  1. Speed perturbation (re-tempo): 발화 속도 변화 → 화자처럼 인식되는 효과
  2. Pitch shift: 피치 변경 → 남/녀, 어른/아이 흉내
  3. Volume gain: 녹음 환경 다양성
  4. (선택) Background noise mix: MUSAN 등의 잡음 혼합 (SNR 제어)
  5. (선택) Room Impulse Response (RIR) convolution: 방 잔향 시뮬레이션

설정은 YAML로 관리한다 (`examples/augment_config.yaml` 참고).

사용:
    python scripts/augment_audio.py \\
        --in_dir ./synth_raw \\
        --out_dir ./synth_aug \\
        --config examples/augment_config.yaml
"""

from __future__ import annotations

import argparse
import itertools
import random
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import soundfile as sf
import yaml

try:
    import librosa
except ImportError:
    librosa = None
from scipy.signal import fftconvolve


# ---------- Audio I/O ----------

def _load_wav(path: Path, target_sr: int) -> np.ndarray:
    audio, sr = sf.read(str(path), always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if sr != target_sr:
        if librosa is None:
            raise SystemExit("librosa 필요: pip install librosa")
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return audio


def _save_wav(path: Path, audio: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(str(path), (audio * 32767).astype(np.int16), sr, subtype="PCM_16")


# ---------- Augmentations ----------

def aug_speed(audio: np.ndarray, sr: int, factor: float) -> np.ndarray:
    """Re-tempo: 길이를 factor만큼 변경 (피치도 약간 따라감 — KWS에는 OK)."""
    if librosa is None:
        raise SystemExit("librosa 필요")
    return librosa.effects.time_stretch(audio, rate=factor)


def aug_pitch(audio: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    if librosa is None:
        raise SystemExit("librosa 필요")
    return librosa.effects.pitch_shift(audio, sr=sr, n_steps=semitones)


def aug_gain(audio: np.ndarray, db: float) -> np.ndarray:
    return audio * (10.0 ** (db / 20.0))


def aug_noise_mix(audio: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """clean + noise를 SNR(dB) 기준으로 mix."""
    # 길이 맞추기 (loop or crop)
    if len(noise) < len(audio):
        n_repeat = (len(audio) // len(noise)) + 1
        noise = np.tile(noise, n_repeat)
    noise = noise[: len(audio)]

    eps = 1e-10
    p_audio = np.mean(audio ** 2) + eps
    p_noise = np.mean(noise ** 2) + eps
    target_p_noise = p_audio / (10.0 ** (snr_db / 10.0))
    scale = np.sqrt(target_p_noise / p_noise)
    return audio + noise * scale


def aug_rir(audio: np.ndarray, rir: np.ndarray) -> np.ndarray:
    """RIR convolution. RIR은 보통 main peak로 정렬돼 있다고 가정."""
    if rir.ndim == 2:
        rir = rir.mean(axis=1)
    rir = rir / (np.max(np.abs(rir)) + 1e-10)
    out = fftconvolve(audio, rir, mode="full")[: len(audio)]
    # 클리핑 방지 정규화
    peak = np.max(np.abs(out)) + 1e-10
    if peak > 1.0:
        out = out / peak * 0.97
    return out.astype(np.float32)


# ---------- Pipeline ----------

def _gen_combos(cfg: dict) -> list[dict]:
    """speed × pitch × gain의 cartesian product (또는 random sampling)."""
    speeds = cfg.get("speed_factors", [1.0])
    pitches = cfg.get("pitch_semitones", [0])
    gains = cfg.get("gain_db", [0.0])

    combos = [
        {"speed": s, "pitch": p, "gain": g}
        for s, p, g in itertools.product(speeds, pitches, gains)
    ]

    random_n = cfg.get("random_n")
    if random_n and random_n < len(combos):
        rng = random.Random(cfg.get("seed", 42))
        combos = rng.sample(combos, random_n)
    return combos


def _load_aux_wavs(dir_path: str | None, sr: int) -> list[np.ndarray]:
    if not dir_path:
        return []
    p = Path(dir_path)
    if not p.exists():
        print(f"[warn] aux dir 없음: {p}")
        return []
    wavs = []
    for f in sorted(itertools.chain(p.rglob("*.wav"), p.rglob("*.WAV"))):
        try:
            wavs.append(_load_wav(f, sr))
        except Exception as e:
            print(f"[warn] {f}: {e}")
    print(f"[info] aux wavs from {p}: {len(wavs)}")
    return wavs


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in_dir", required=True, type=Path)
    p.add_argument("--out_dir", required=True, type=Path)
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--sample_rate", type=int, default=16000)
    args = p.parse_args()

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sr = args.sample_rate
    rng = random.Random(cfg.get("seed", 42))

    combos = _gen_combos(cfg)
    print(f"[aug] {len(combos)} 변형/파일")

    noises = _load_aux_wavs(cfg.get("noise_dir"), sr)
    rirs = _load_aux_wavs(cfg.get("rir_dir"), sr)
    snr_range = cfg.get("snr_db_range", [5, 20])
    noise_prob = float(cfg.get("noise_prob", 0.0))
    rir_prob = float(cfg.get("rir_prob", 0.0))

    in_files = sorted(args.in_dir.rglob("*.wav"))
    if not in_files:
        raise SystemExit(f"[ERR] {args.in_dir} 에 wav 없음")

    total = 0
    for src in in_files:
        try:
            audio = _load_wav(src, sr)
        except Exception as e:
            print(f"[skip] {src}: {e}")
            continue

        stem = src.stem
        for i, c in enumerate(combos):
            x = audio
            if c["speed"] != 1.0:
                x = aug_speed(x, sr, c["speed"])
            if c["pitch"] != 0:
                x = aug_pitch(x, sr, c["pitch"])
            if c["gain"] != 0.0:
                x = aug_gain(x, c["gain"])

            tags = [f"sp{c['speed']:.2f}", f"pt{int(c['pitch'])}", f"g{int(c['gain'])}"]

            if noises and rng.random() < noise_prob:
                noise = rng.choice(noises)
                snr = rng.uniform(snr_range[0], snr_range[1])
                x = aug_noise_mix(x, noise, snr)
                tags.append(f"snr{snr:.0f}")

            if rirs and rng.random() < rir_prob:
                rir = rng.choice(rirs)
                x = aug_rir(x, rir)
                tags.append("rir")

            out_path = args.out_dir / f"{stem}__{'_'.join(tags)}.wav"
            _save_wav(out_path, x, sr)
            total += 1

    print(f"[DONE] {total}개 파일 생성 → {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
