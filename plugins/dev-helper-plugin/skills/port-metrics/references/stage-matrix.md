# 단계 매트릭스 — 단계·비교 대상·산출물·필수 범위

- 정확한 필수 지표 목록은 `make_report.py checklist --thresholds thresholds.json` 이 동결 scope 로 출력함(이 문서는 구조 설명)
- 결정: D2 이중 기준 — ACC 는 S1 대비 누적 열화, NUM·DEC 는 인접 단계 사슬

---

## 1. 단계 정의

| 단계 | 환경 | 답하는 질문 | 대표 프로파일 |
|---|---|---|---|
| S1 | 호스트, Python, PT(CUDA) | 기준 정확도는? 골든 텐서는? | 원본 가중치(bf16·fp16 저장) + fp32 연산 |
| S2 | 호스트, Python pymnn, CPU | 변환이 수치를 보존했나 | `fp16-high-normal` |
| S3 | 호스트, C++ 디코더 + CLI, CPU | 디코더 이식이 결과를 보존했나 | `fp16-high-normal`, `w8a-high-normal` |
| S4 | 단말 CLI(Android), CPU | ARM 커널·저정밀 연산 영향과 단말 성능은 | `fp16-high-normal`, `w8a-high-normal`, `w8a-low-normal`, `w8a-low-low` … |
| S5 | 단말 앱(Java/JNI), CPU, 출하 프로세스 상태 | 앱 수용이 결과를 바꾸지 않았나, 출하 상태 성능은 | S4 와 같은 집합 |
| GPU 변형 | 어느 단계든 `backend` = `opencl`·`vulkan`·`cuda` | 같은 질문을 GPU 백엔드로 | 같은 지표를 backend 태그로 구분 |

- 프로파일 실효값은 profiles.md §3. 호스트(S2·S3)에서 `precision=low` 는 no-op 이라 fp16 연산 영향은 S4 에서 처음 드러남

## 2. S1 이 만드는 두 산출물

| 산출물 | 실행 | 쓰임 |
|---|---|---|
| 정확도 기준(`ACC.primary`) | CUDA, 원 구현 그대로 | 모든 단계 `ACC.degradation` 의 기준 |
| 골든 텐서 | **CPU fp32**(또는 TF32 off CUDA 를 CPU 와 대조해 동등 확인) | S1-S2 `NUM.*` 의 ref |

- 이유: CUDA·TF32 참조는 변환 전(ORT)부터 텐서 임계를 넘을 수 있음(Zipformer: JIT-CUDA 참조 ORT max_abs 4.85e-3 ↔ JIT-CPU 2.9e-6)
- 두 회차가 모두 ACC.primary 를 내면 `acc_baseline: true` 로 하나를 지정
- S1 기록: `tf32`·`attn_impl`·`checkpoint_sha256`(bf16 버퍼·상수가 원인인 사례 대비, root-cause.md §2)

## 3. 비교 쌍(pairs)

| kind | ref → target | 지표 | 기대 |
|---|---|---|---|
| chain S1-S2 | S1 골든 → S2 | NUM·DEC | fp: 절대 오차 작음 / lowp: cos·rel_l2 |
| chain S2-S3 | S2 → S3 | NUM·DEC | 같은 libMNN·가중치 → 출력 완전 일치 |
| chain S3-S4 | S3 → S4 | NUM·DEC | ISA 차 존재 — fp 는 max_abs 판정, rel_l2 기록 / lowp 는 cos·rel_l2 |
| chain S4-S5 | S4 → S5 | DEC | 같은 단말·입력·구성 → 출력 완전 일치(정확도 승계 근거) |
| base | S1 → 각 단계 | DEC.flip·severe_flip·margin | 심각 변경 0 |
| regress | 같은 단계 옛 → 새 빌드 | DEC.match_rate | 출력 완전 일치(의도한 수치 변경이면 fail 후 사용자 결정) |

- 쌍의 두 회차는 `manifest_sha256`·`threads_effective` 가 같아야 동등성 비교가 성립함(다르면 잡음 바닥 측정용으로만)
- 변환 경로에 ONNX 가 있으면 PT ↔ ORT 쌍을 S1 단계 안에서 별도로 측정해 변환기 문제를 분리(root-cause.md §1)

## 4. 목적 태그별 추가 범위

| 목적 | 언제 | 추가로 필수가 되는 것 |
|---|---|---|
| `convert` | 새 모델·변환 옵션 변경 | `CNV.audit_ok`, S1-S2 NUM 규칙의 `noise_floor` |
| `regress` | MNN 패치·C++ 수정 후 | regress 쌍 `DEC.match_rate`, 같은 세션 ABBA(RTF 또는 처리량·지연 p99·peak RSS) |
| `optimize` | 구성 A vs B(thread·프로파일·빌드 옵션) | sampler 회차(CPU-s/작업량·PSS), ABBA(위 + CPU-s·PSS) |
| `ship` | 출하 게이트 | sampler 회차, 실시간 투입 회차, soak 회차(`window_sec`, 창 ≥ 2), 결정성 |

- 사용자 흐름의 매 MNN 패치 확인 = `regress`(+ 변환을 다시 했으면 `convert`)
- 모델 유형 확장: `streaming`(jitter·step/hop·tail·deadline), `llm`(prefill·TTFT·decode tok/s·토큰 일치), `classifier`(margin)

## 5. 단계별 회차 구성 예(ship + streaming, 오디오 입력)

| 단계 | accuracy | perf(max) | perf(realtime) | perf(soak) | sampler |
|---|---|---|---|---|---|
| S1 | ○(CUDA) + 골든(CPU) | ○ | — | — | — |
| S2 | ○ | ○ | — | — | — |
| S3 | ○ | ○ | — | — | 선택 |
| S4 | ○ | ○ | ○ | ○ | ○ |
| S5 | ○ | ○ | ○ | ○ | ○ |

- perf 와 accuracy 는 같은 회차여도 됨(timing 행을 내면서 출력도 저장). sampler 회차는 반드시 따로
- 단말 회차는 매번 열 시작 조건(measurement-control.md §2)을 통과해야 유효

## 6. 단계 진행 중 부분 리포트

- 개발 중에는 `report --partial S1,S2` 로 필수 검사를 측정한 단계까지만 축소 가능 — 리포트 머리에 "부분 리포트"가 표시되며, 최종 판정에는 쓰지 않음
- scope 자체(동결 파일)는 바꾸지 않음. 단계를 빼고 싶으면 새 동결 파일을 만들고 처음부터 측정
