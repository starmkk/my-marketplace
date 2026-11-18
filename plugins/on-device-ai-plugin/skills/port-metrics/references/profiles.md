# 정밀도 프로파일 — ID 규칙·실효 3 필드·플랫폼 차이

- 목적: "fp16 모델" 같은 단일 라벨이 실제 연산 경로를 숨겨 결론이 틀어지는 것을 막음
- 근거: SoundAI `experiments/2026-10-29-precision-memory-profiles/profile-spec.md` §2.4(3 필드 표기),
  SpeechLM.cpp.v4 `docs/design/2026-09-09-precision-dtype-spec-analysis.md`(x86 precision no-op),
  Nemotron3 `docs/references/2026-10-18-w8a8-precision-memory-options.md`(memory=low = W8A8)

---

## 1. 프로파일 ID

- 형식: `<weight>-<precision>-<memory>-t<threads>` (예 `fp16-high-normal-t4`, `w8a-low-normal-t4`)
- `weight` = 저장 형식: `fp32` · `fp16` · `bf16` · `w8a`(int8 비대칭 block) · `w8s`(int8 대칭) · `w4a` 등
  - 양자화 세부(block 크기·비대칭 여부·fp32 유지 op)는 `identity.converter_args` 에 원문 그대로 기록
  - MNNConvert `--weightQuantAsymmetric` 은 기본값에 기대지 말고 `=1`/`=0` 을 항상 명시(SpeechLM v3 배포본이 파싱 버그로 실제로는 대칭이었음)
- `precision` = MNN BackendConfig precision(`high`·`normal`·`low`) — **요청값**
- `memory` = MNN BackendConfig memory(`high`·`normal`·`low`) — **요청값**
- `t<threads>` = 요청 스레드 수. 실효 스레드는 `identity.threads_effective` 에 따로 기록

## 2. 실효 3 필드(`effective`) — 리포트의 정밀도 표기 기준

| 필드 | 의미 | 값 예 |
|---|---|---|
| `weight_storage` | 메모리에 상주하는 가중치 형식 | `fp32`·`fp16`·`int8` |
| `matmul_accum` | 행렬곱·누산이 실제로 도는 형식 | `fp32`·`fp16`·`int32+fp32` |
| `activation_quant` | 활성 동적 양자화 여부 | `none`·`int8` |

- **요청값이 아니라 실측 증거로 채움**: 엔진이 적용한 값(runtime_info·Arm82 사용 여부·로그)을 읽음. `getBnConfig` 같은 요청값 에코는 증거가 아님(Nemotron W8P)
- class 판정(생성기): `weight ∈ {fp32, fp16, bf16} ∧ accum = fp32 ∧ act = none` → `fp`, 그 외 → `lowp`. 두 회차를 비교할 때는 낮은 쪽을 따름

## 3. 사용자 측정 순서와 프로파일 대응

| 사용자 표기 | 프로파일 ID | arm64 실효(S4·S5) | x86 실효(S2·S3) |
|---|---|---|---|
| fp16 weight + fp32 연산 | `fp16-high-normal` | fp16 / fp32 / none | fp16 / fp32 / none |
| w8a weight + fp32 연산 | `w8a-high-normal` | int8 / fp32 / none | int8 / fp32 / none |
| w8a weight + fp16 연산 | `w8a-low-normal` | int8 / fp16 / none | int8 / **fp32** / none |
| w8a weight + int8 활성(W8A8) | `w8a-low-low` 또는 `w8a-high-low` | int8 / int32+fp16 / int8 | int8 / int32+fp32 / int8 |
| fp16 weight + fp16 연산 | `fp16-low-normal` | fp16 / fp16 / none | fp16 / **fp32** / none |

- memory=normal 은 int8 가중치를 로드 시 fp32 로 전개해 상주시키는 경로가 있음 → RSS 가 파일 크기만큼 줄지 않음(SoundAI H5: low 만 int8 상주). 메모리 비교는 RSS 실측으로만 함
- memory=low + int8 가중치 = 활성 동적 양자화(W8A8) — 정확도 경로가 완전히 다름. "메모리 옵션"으로 취급하지 않고 별도 프로파일로 다룸

## 4. 플랫폼 차이 — 호스트 결과로 단말 fp16 품질을 판단하지 않음

- **x86 에서 precision=low 는 no-op**: AVX2Backend 가 Precision_Low 를 하드코딩하고 Arm82 분기가 x86 에 컴파일되지 않음 → 호스트 low 출력 == high 출력(SpeechLM identity 50/50, SoundAI 1,524/1,524)
  - 이 일치는 "fp16 안전"의 근거가 아님. 단말에서만 fp16 연산이 실제로 돎(SpeechLM 단말 low: 불일치 6·심각 flip 2)
- arm64 fp16 연산 조건: `precision == low ∧ CPU fp16 산술 지원` → Arm82Backend
- ARM NEON 과 x86 AVX2 는 exp 근사(상대오차 5.6e-5 ↔ 1.4e-6)·Strassen 진입점·Softmax 분기가 달라 fp 프로파일도 비트 동일이 구조적으로 불가 → S3-S4 fp 의 rel_l2 는 기록만, 판정은 DEC·ACC 로
- SME2·i8mm·KleidiAI 빌드 옵션은 int8 GEMM 블록 합산 순서를 바꿔 출력을 바꿀 수 있음(Zipformer S26 5 셋 533 줄 상이) → 빌드 옵션은 `identity.converter_args`/빌드 스탬프에, 단말 cpu features 는 `identity` 에 기록하고 등급별로 별도 판정

## 5. precision 적용 증거(단말)

- 같은 libMNN·같은 번들에서 **precision 만 바꾼 두 회차의 출력이 달라야** "low 가 적용됐다"고 판정(SpeechLM differs-from 계약, Nemotron EV-fp16-high)
  - 같은 프로파일 두 회차 차 = 0(재현성) 과 high↔low 차 > tol(적용) 을 함께 확인
- 같은 번들을 공유하는 프로파일은 sha 가 같으므로 번들 sha 로는 구분 불가 → `profile`·`effective` 필드가 구분 키

## 6. thread 수

- thread 수는 MNN 작업 분할(Strassen 분할·Winograd unit)을 바꿔 비트 결과를 바꿀 수 있음(Zipformer THR, SoundAI t1↔t4 61,010/225,681 구간만 비트 동일)
  - 비교 회차끼리 `threads_effective` 가 같아야 동등성 비교가 성립함(다르면 그 쌍은 잡음 바닥 측정용)
- 실효 스레드는 `/proc/self/task` 수 또는 엔진 보고값으로 확인. 공유 스레드 풀 spin 대기가 CPU 를 먹는 경우가 있음(Zipformer decoder T=1 인데 4 스레드 spin)
