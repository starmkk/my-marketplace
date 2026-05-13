# Speaker Reference 디렉토리

화자별 reference wav를 다음 구조로 배치하세요:

```
speaker_refs/
├── spk_001/
│   └── ref.wav     (5~15초, 단일 화자, 깨끗한 한국어)
├── spk_002/
│   └── ref.wav
└── ...
```

각 폴더 안의 가장 큰 wav가 자동 선택됩니다.

## 권장 사양
- 길이: 5~15초
- 샘플레이트: 16kHz 이상
- 화자: 1명만 (다인 발화 X)
- SNR: > 25dB
- 포맷: wav, mp3, flac 모두 OK

## 추천 데이터 소스
1. AIHub 다화자 음성합성 데이터셋
2. Zeroth-Korean (오픈, Apache 2.0)
3. 자체 녹음 (5~10명도 충분)

자세한 구성 전략은 `references/speaker_pool_strategy.md` 참고.
