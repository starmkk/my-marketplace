# MeloTTS 한국어 사용 가이드

출처: https://github.com/myshell-ai/MeloTTS, https://huggingface.co/myshell-ai/MeloTTS-Korean

## 라이선스
- MIT License — 상업적 사용 가능 (KT 사내 활용 OK)
- 의존 모델: VITS / VITS2 / Bert-VITS2 기반

## 한국어 모델 핵심 사실
- 화자 ID: `'KR'` 단 1개. (영어는 `EN-Default/US/BR/INDIA/AU` 5개)
- 권장 발화 속도: 1.2~1.3 (기본 1.0은 한국어에 다소 느린 편)
- 출력 sample rate: 모델 내부 기본값 (보통 44.1kHz). KWS용으로는 16kHz 리샘플링 필수.
- CPU 실시간 추론 가능. macOS MPS는 일부 op 호환성 이슈가 있어 본 스킬은 기본 CPU.

## 최소 코드 (공식 예시)
```python
from melo.api import TTS

text = "안녕하세요! 오늘은 날씨가 정말 좋네요."
model = TTS(language='KR', device='cpu')
spk_ids = model.hps.data.spk2id      # {'KR': 0}
model.tts_to_file(text, spk_ids['KR'], 'kr.wav', speed=1.0)
```

## 발음/표기 주의사항
- 한자/영문 혼용 시 영어로 발음되는 경우가 있음. 가능하면 한글로 정규화.
- 숫자는 한글로 풀어쓰는 것이 안정적 ("123" → "백이십삼" 또는 "일이삼").
- 외래어는 한글 표기로 작성 권장 ("Wi-Fi" → "와이파이").

## CLI 사용
```bash
# 설치 후
melo "안녕하세요" out.wav --language KR --speed 1.2
# 또는 파일 입력
melo input.txt out.wav --language KR --file
```

## 모델 가중치 위치
첫 실행 시 Hugging Face Hub에서 자동 다운로드:
- `myshell-ai/MeloTTS-Korean` (config.json + checkpoint.pth)
- 캐시 경로: `~/.cache/huggingface/hub/`

오프라인 환경에서는 미리 받아두기:
```bash
huggingface-cli download myshell-ai/MeloTTS-Korean
```

## 알려진 이슈
1. **unidic 다운로드 실패** — `unidic-lite`로 대체 가능 (`pip install unidic-lite`).
2. **MPS에서 NaN 발생** — torch MPS의 일부 transformer op 이슈. CPU로 폴백.
3. **긴 문장 잘림** — 문장 단위로 분리 후 합성 → 후처리에서 concat 권장.
4. **첫 토큰 침묵** — 일부 케이스에서 앞부분 50ms 정도 무음. trimming(librosa.effects.trim) 권장.
