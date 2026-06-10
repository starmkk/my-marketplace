"""
Gemma 4 E2B-it ASR 공통 모듈 (싱글톤 캐시).

- 모델 로드는 비싸므로 한 번만.
- transcribe.py, batch_transcribe.py가 공유.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch


# ---------- 환경 ----------

def get_model_path() -> Path:
    """
    ~/.claude/repo/gemma-4-* 디렉토리를 검색해 모델 경로를 반환한다.
    사용자가 직접 경로를 지정한 경우 해당 경로를 우선 사용한다.
    """
    repo_base = Path.home() / ".claude" / "repo"
    if repo_base.exists():
        candidates = sorted(repo_base.glob("gemma-4-*"))
        if candidates:
            return candidates[0]
    raise RuntimeError(
        "Gemma 4 모델을 찾을 수 없습니다.\n"
        "Claude Code에게 'Gemma 4 모델 다운로드해줘'라고 요청하거나,\n"
        "모델 경로를 직접 이 함수에 전달하세요.\n"
        "기대 경로: ~/.claude/repo/gemma-4-<variant>"
    )


def select_dtype_and_device(prefer: str = "auto"):
    """디바이스와 dtype 자동 선택. (device_map, dtype)"""
    if prefer == "cpu":
        return "cpu", torch.float32
    if torch.cuda.is_available():
        return "auto", torch.bfloat16
    if torch.backends.mps.is_available():
        # MPS는 device_map='auto' 가 일부 케이스에서 깨지므로 'mps' 명시
        return "mps", torch.bfloat16
    return "cpu", torch.float32


# ---------- 모델 싱글톤 ----------

@dataclass
class ASRModel:
    processor: object
    model: object
    device: str | dict
    dtype: torch.dtype


_asr_cache: Optional[ASRModel] = None


def load_asr(prefer_device: str = "auto") -> ASRModel:
    """Gemma 4 ASR 모델 로드. 두 번째 호출부터 캐시 재사용."""
    global _asr_cache
    if _asr_cache is not None:
        return _asr_cache

    model_path = get_model_path()
    if not model_path.exists():
        # _env가 이미 검증했으므로 정상 흐름에선 도달하지 않는다.
        raise SystemExit(
            f"[ERR] Gemma 4 모델 경로 없음: {model_path}\n"
            "      GEMMA4_MODEL_PATH 환경변수를 다시 확인하세요."
        )

    device_map, dtype = select_dtype_and_device(prefer_device)

    # transformers 버전에 따라 클래스명이 다를 수 있어 fallback
    try:
        from transformers import AutoModelForMultimodalLM as _MMModel
    except ImportError:
        from transformers import AutoModelForImageTextToText as _MMModel  # type: ignore

    from transformers import AutoProcessor

    processor = AutoProcessor.from_pretrained(str(model_path))
    model = _MMModel.from_pretrained(
        str(model_path),
        dtype=dtype,
        device_map=device_map,
    )
    model.eval()

    print(f"[asr] loaded. device_map={device_map} dtype={dtype}")

    _asr_cache = ASRModel(
        processor=processor,
        model=model,
        device=device_map,
        dtype=dtype,
    )
    return _asr_cache


# ---------- ASR 호출 ----------

# 기본 ASR 프롬프트. 한국어 우선이지만 language 파라미터로 변경 가능.
DEFAULT_ASR_PROMPT = (
    "Transcribe the following speech segment in {language}. "
    "Output only the transcribed text, no other commentary."
)


def transcribe_audio(
    audio_path: Path | str,
    language: str = "Korean",
    asr: ASRModel | None = None,
    max_new_tokens: int = 128,
    custom_prompt: str | None = None,
) -> str:
    """
    한 wav 파일 → 텍스트.

    audio_path는 Gemma 4가 지원하는 포맷이면 됨 (wav, mp3, flac 등).
    모델은 내부적으로 16kHz로 리샘플링하므로 입력 SR은 자유.
    """
    if asr is None:
        asr = load_asr()

    prompt = (custom_prompt or DEFAULT_ASR_PROMPT).format(language=language)

    messages = [
        {
            "role": "user",
            "content": [
                # 공식 가이드: multimodal 입력은 텍스트보다 앞에 배치 권장
                {"type": "audio", "audio": str(audio_path)},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    # apply_chat_template으로 입력 변환
    inputs = asr.processor.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )

    # 디바이스 이동
    target_device = (
        asr.model.device if hasattr(asr.model, "device") else "cpu"
    )
    inputs = {
        k: (v.to(target_device, dtype=asr.dtype) if v.dtype.is_floating_point else v.to(target_device))
        if hasattr(v, "to") else v
        for k, v in inputs.items()
    }

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = asr.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # ASR은 deterministic
        )

    # 입력 부분 제외하고 생성된 토큰만 디코딩
    generated = outputs[0][input_len:]
    text = asr.processor.decode(generated, skip_special_tokens=True).strip()

    return text


# ---------- 텍스트 정규화 (CER/WER 계산용) ----------

import re

_ZW = re.compile(r"[\u200B-\u200F\uFEFF]")          # zero-width
_PUNCT = re.compile(r"[^\w\s가-힣]")                  # 영숫자/한글/공백 외 제거
_WS = re.compile(r"\s+")


def normalize_korean(text: str) -> str:
    """
    한국어 CER/WER 계산용 텍스트 정규화.
    - 소문자화
    - zero-width 제거
    - 구두점/특수문자 제거
    - 공백 압축
    """
    text = text.lower()
    text = _ZW.sub("", text)
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    return text
