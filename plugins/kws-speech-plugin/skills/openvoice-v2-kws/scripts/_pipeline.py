"""
OpenVoice V2 + MeloTTS 공통 파이프라인 모듈.

clone_synthesize.py / batch_multispk_synthesize.py / prepare_speaker_pool.py 가 공유한다.
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

try:
    import librosa
except ImportError:
    librosa = None

import torch


# ---------- 환경 ----------

def get_ckpt_dir() -> Path:
    """~/.claude/repo/OpenVoice@*/checkpoints_v2 를 검색."""
    repo_base = Path.home() / ".claude" / "repo"
    if repo_base.exists():
        candidates = sorted(repo_base.glob("OpenVoice@*/checkpoints_v2"))
        if candidates:
            return candidates[-1]
    raise RuntimeError(
        "OpenVoice checkpoints를 찾을 수 없습니다.\n"
        "Claude Code에게 'OpenVoice 소스 다운로드해줘'라고 요청하세요.\n"
        "기대 경로: ~/.claude/repo/OpenVoice@<version>/checkpoints_v2"
    )


def select_device(prefer: str = "auto") -> str:
    if prefer != "auto":
        return prefer
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        # MPS는 OpenVoice 일부 op에서 NaN 발생 사례가 있어 기본은 cpu
        return "cpu"
    return "cpu"


# ---------- 모델 로드 (싱글톤 패턴) ----------

@dataclass
class Pipeline:
    """MeloTTS + OpenVoice V2 파이프라인 인스턴스."""
    melo_tts: object
    melo_spk_id: int
    converter: object
    src_se: torch.Tensor
    device: str
    ckpt_dir: Path


_pipeline_cache: Optional[Pipeline] = None


def load_pipeline(device: str = "auto", language: str = "KR") -> Pipeline:
    """모델을 로드하여 Pipeline 객체 반환. 두 번째 호출부터는 캐시 사용."""
    global _pipeline_cache
    if _pipeline_cache is not None:
        return _pipeline_cache

    dev = select_device(device)
    ckpt = get_ckpt_dir()

    # MeloTTS (base speaker)
    from melo.api import TTS
    melo_tts = TTS(language=language, device=dev)
    melo_spk_id = melo_tts.hps.data.spk2id[language]

    # OpenVoice V2 ToneColorConverter
    from openvoice.api import ToneColorConverter
    converter = ToneColorConverter(
        str(ckpt / "converter" / "config.json"),
        device=dev,
    )
    converter.load_ckpt(str(ckpt / "converter" / "checkpoint.pth"))

    # source speaker embedding (base TTS의 화자)
    # 한국어는 base_speakers/ses/kr.pth
    src_se_path = ckpt / "base_speakers" / "ses" / f"{language.lower()}.pth"
    if not src_se_path.exists():
        # 일부 zip 구조 변형 대응
        candidates = list((ckpt / "base_speakers").rglob(f"{language.lower()}*.pth"))
        if not candidates:
            raise FileNotFoundError(
                f"source SE 파일 없음: {src_se_path}\n"
                f"ckpt 디렉토리: {ckpt}"
            )
        src_se_path = candidates[0]
    src_se = torch.load(str(src_se_path), map_location=dev)

    _pipeline_cache = Pipeline(
        melo_tts=melo_tts,
        melo_spk_id=melo_spk_id,
        converter=converter,
        src_se=src_se,
        device=dev,
        ckpt_dir=ckpt,
    )
    print(f"[pipeline] loaded. device={dev} ckpt={ckpt}")
    return _pipeline_cache


# ---------- Speaker embedding ----------

def extract_target_se(reference_wav: Path, pipeline: Pipeline,
                      vad: bool = True) -> torch.Tensor:
    """reference wav → target speaker embedding (tone color)."""
    from openvoice import se_extractor
    target_se, _audio_name = se_extractor.get_se(
        str(reference_wav),
        pipeline.converter,
        vad=vad,
    )
    return target_se


# ---------- 합성 ----------

def synthesize_with_clone(
    text: str,
    target_se: torch.Tensor,
    output: Path,
    pipeline: Pipeline,
    speed: float = 1.2,
    sample_rate: int = 16000,
    message: str = "@MyShell",
) -> Path:
    """
    한 문장을 target speaker tone으로 합성하여 16kHz mono로 저장.

    내부:
      1) MeloTTS로 base wav 생성 (한국어 speaker)
      2) OpenVoice ToneColorConverter로 target tone 적용
      3) 16kHz mono로 리샘플링 및 PCM_16 저장
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir) / "base.wav"
        cloned_path = Path(tmpdir) / "cloned.wav"

        # 1) base TTS
        pipeline.melo_tts.tts_to_file(
            text, pipeline.melo_spk_id, str(base_path), speed=speed
        )

        # 2) tone color conversion
        pipeline.converter.convert(
            audio_src_path=str(base_path),
            src_se=pipeline.src_se,
            tgt_se=target_se,
            output_path=str(cloned_path),
            message=message,
        )

        # 3) 16kHz mono 리샘플링 + PCM_16 저장
        audio, sr = sf.read(str(cloned_path), always_2d=False)
        if audio.ndim == 2:
            audio = audio.mean(axis=1)
        audio = audio.astype(np.float32)
        if sr != sample_rate:
            if librosa is None:
                raise SystemExit("librosa 필요: pip install librosa")
            audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
        audio = np.clip(audio, -1.0, 1.0)
        sf.write(str(output), (audio * 32767).astype(np.int16),
                 sample_rate, subtype="PCM_16")

    return output
