# 사례 근거 — 4 프로젝트군 측정 지표 대조

- 목적: port-metrics 지표·기본 임계·통제 규칙이 어느 사례에서 왔는지 추적 가능하게 함
- 조사일: 2026-11-18, 소스 위치 `/workspace/work/research2/`(호스트 aip1 기준)
- 약칭: ZF = Zipformer-ASR.main.v4(+ SoundAI.Lite zipformer 보고서), SL = SpeechLM.asset·SpeechLM.cpp.v4,
  GR = SoundAI.asset·SoundAI.cpp(→ Granite 로 이름 변경 예정), NM = Nemotron3.asset·Nemotron3.cpp
- 단말(S4·S5) 지표 1 차 대조: `Nemotron3.asset/docs/references/2026-11-18-device-metrics-speechlm-nemotron.md`

---

## 1. 사례 개요

| 항목 | ZF | SL | GR | NM |
|---|---|---|---|---|
| 기능 | 한국어 스트리밍 ASR | 통화 위험도 판정(audio encoder + Gemma LLM) | 피싱 텍스트 분류(ModernBERT) | 스트리밍 화자분리 |
| 입력 | audio | audio | text(RTF 없음) | audio |
| 주지표 | CER(5 셋, 12,099 발화) | risk·tone 일치율, 심각 flip(356 trigger) | 혼동행렬(59,382 통화) | DER(S-2 32 파일) |
| 측정 단계 | S1~S5 | S1~S4(S5 는 SoundAI.Lite) | S1~S4(S5 미측정) | S1~S4(S5 = F711N 앱 게이트) |
| GPU(MNN) | 없음 | 없음 | 없음(OpenCL OFF) | 없음 |
| 대표 단말 | S26·SM-S721N·S10 | S25 | S942N·S721N·F711N·G977N | S25·F711N |

## 2. 범주별 대조(지표 정의·임계)

| 범주 | ZF | SL | GR | NM | port-metrics 반영 |
|---|---|---|---|---|---|
| 텐서(S1-S2) | cos ≥ 0.9999, max_abs ≤ 1e-3, state rel_l2 ≤ 1e-4, w8a cos ≥ 0.99·rel_l2 ≤ 0.05 | G2a max_abs ≤ 1e-3, G2b w8 cos ≥ 0.99·rel_l2 ≤ 0.05 | logits ≤ 1e-4(ORT), Δp → Δmargin ≤ 2e-3 | G2a max_abs ≤ 1e-3·rel_l2 ≤ 1e-4, G2b cos ≥ 0.99·rel_l2 ≤ 0.05 | `NUM.*` fp/lowp 기본값 |
| 텐서(S2-S3) | C++ probe 덤프 ↔ pymnn | stage_parity feat 1e-3·state 1e-4 | Δp 2.98e-8 | G3-pre ≤ 1e-6, G3 ≤ 1e-4(FAIL 4/4 원판정 유지) | `NUM.*` S2-S3 1e-3/1e-4 |
| 텐서(S3-S4) | ISA 등급별 `.res` 일치 | host 임계 적용 → 초과는 보고만(state 2.89e-3) | Δmargin 1.13e-3(ARM exp 근사) | G4-stage max_abs ≤ 1e-3(7.5e-4) | fp: max_abs 판정·rel_l2 기록 |
| 출력 일치 | C++ = pymnn 12,099/12,099, JNI = CLI 100 % | records 바이트 50/50, 단말 identity 기록 | 바이트 동일 개수 | RTTM 바이트 동일, 앱 = CLI | `DEC.match_rate` S2-S3·S4-S5 = 1.0 |
| 정확도 | 셋별 +0.30 p·평균 +0.15 p | HOST_MEASURED risk ≥ 98·tone ≥ 99·flip ≤ 1 / strict 100·100·0 | 혼동행렬 불변(strict-release) | DER ≤ HF + 0.5 %p, ② ≤ 0.05 %p | `ACC.degradation` limit = 프로젝트 KPI |
| 속도 | proc_ms p99 ≤ 250·max ≤ 400, RTF ≤ 0.2(stream), 지터 ≤ 2.0 | RTF 중앙값, decode_only tok/s, prefill_sec | tok/s(Σtokens ÷ Σwall), 구간 p50/p99 | G5-rtf 중앙 < 1·p95 ≤ 576 ms, R1 tail·step·lag ≤ 1 hop | `SPD.*` 이름 고정, streaming·llm 확장 |
| 자원 | PSS 평균 ≤ 205 MB, CPU 평균 ≤ 60 %, 번들 ≤ 82 MB | RSS peak, PSS avg, CPU-s/audio-s | Peak RSS, Mean RSS(샤드 0), CPU % | G5-mem ru_maxrss ≤ 450 MB | `RES.*` MiB 고정, sampler 분리 |
| 열 | 냉각 ≤ 31 °C(HAL), 30 s 표본 | 배터리 45/38 °C 정지·재개 | 45/38 °C + 회차 간 180 s + ≤ 기준 + 0.5 °C | 냉각 게이트(배터리 ≤ 33·CPU ≤ 45·클럭 상한), drift ≤ 0.15 | 배터리 ≤ 34 °C + 클럭 복구(D5) |
| A/B | ABBA 3 쌍, 지연·RTF +5 %·CPU·PSS +2 % 사전 고정 | 회차 A/B nonce 결속 | SME2 ON/OFF ABBA ×2 + 냉각 | latency-ab 16 블록 t-CI | `AB.*` 쌍 Δ% 중앙값 |
| 판정 상태 | PASS/FAIL/REF(강등) | 정책별 차단/보고 | 승인 지점(AP) | pass/fail/invalid/not_established/record_only | 5 상태 채택 |

## 3. 재측정·정의 변경의 반복 원인

| 원인 | ZF | SL | GR | NM |
|---|---|---|---|---|
| 같은 이름 다른 정의 | RTF 배치 ↔ stream(1.8~2.3 배), PSS /1024 ↔ 10^6 | tok/s 2 종(predict 전체 ↔ decode_only) | MB ↔ MiB 혼용 | RTF 4 종(0.995~1.538) |
| 기준점 오선택 | JIT-CUDA 참조 → JIT-CPU(A9) | embed_scale 25.25 bf16 | 원본 sdpa ↔ 골드 eager | `.nemo` 버퍼 bf16 |
| 임계 < 잡음 바닥 | batch-row 1e-5 < 타일링 3.2e-5 | STRICT_100 도달 불가 | Δp 1e-4 < thread 잡음 | G1-step 1e-4 < eager↔sdpa 2.9e-4 |
| 정의 범위 누락 | flush chunk 포함으로 지터 3.94 오측 | peak RSS 누적·워밍업 포함 | smoke 가 꼬리 1/70 | G5-rtf "또는" 원안 |
| 열·세션 교란 | 다른 세션 단일 수치 FAIL → ABBA | 시작 온도로 RTF ±15 % | 회차 순서 효과 +5~44 % | 클럭 1.69 ↔ 3.84 GHz |
| 프로세스·코어 | JNI +43.5 % = cpuset 차 | — | 코어 배치 미수집(한계) | foreground 0-6(prime 제외) |
| 샘플러 간섭 | smaps 비용 → PSS 10 s 분리 | 회차 분리 + nonce | 회차 분리 + nonce | — |
| 호스트 fp16 착시 | — | x86 low == high 50/50 | low ≡ high 1,524/1,524 | x86 precision=low = fp32 |

## 4. 근거 문서 위치(주요)

- ZF: `Zipformer-ASR.main.v4/docs/design/2026-10-15-kpi-targets.md`, `docs/plans/2026-10-15-p1-convert-plan.md`(§5.5 G1·G2·A8·A9),
  `docs/plans/2026-10-19-p4-perf-measure-plan.md`(KPI-1~9 정의), `docs/reports/2026-10-20-p4-improvement-report.md`,
  `docs/reports/2026-11-06-zipformer-asr-final-report.md`, `docs/design/2026-10-16-w8a-b64-embed-fp32-decision.md`,
  `SoundAI.Lite/docs/reports/2026-11-06-zipformer-jni-cpuset-core-placement.md`·`2026-11-06-zipformer-v4-regression.md`
- SL: `SpeechLM.asset/docs/design/2026-09-08-audio-parity-review-report.md`(α 스윕·교차 주입),
  `2026-09-07-plan-f-batch-eval-v3-50.md`(HOST_MEASURED), `SpeechLM.cpp.v4/CLAUDE.md`(성능 측정 방법·발열 정책),
  `docs/design/2026-09-10-m2-android-results.md`, `2026-09-12-fp16-low-strict-infeasibility.md`, `2026-09-10-arm-neon-vs-x86-avx2-fp-spec.md`
- GR: `SoundAI.asset/docs/design/2026-10-29-soundai-mnn-design.md`(D5·D18), `experiments/2026-10-29-precision-memory-profiles/profile-spec.md`·`smoke-report.md`,
  `experiments/2026-10-30-device-metrics-survey/proposal.md`, `docs/design/2026-11-02-final4-device-interim-report.md`,
  `SoundAI.cpp/experiments/2026-10-31-g6-delta/layer-dump/`(op 첫 이탈)
- NM: `Nemotron3.asset/docs/design/2026-10-13-p1-pt-baseline-results.md`, `2026-10-20-p4-a2-tolerance-freeze.md`(mel 층별 임계),
  `docs/references/2026-10-24-p4-terms-perf-rtf.md`(RTF 4 종), `docs/reports/2026-10-28-nemotron3-p4-final-report.md`,
  `experiments/20261013-converter-equivalence/`, `scripts/verify/gates.py`(상태 판정)

## 5. 공통 공백(어느 사례도 표준으로 측정하지 않음)

- 전력·배터리 소모 → `PWR.mah_per_unit`(선택)
- MNN GPU 백엔드(OpenCL·Vulkan) → backend 태그로 같은 지표 적용(정의만)
- LLM TTFT 별도 정의 → `SPD.ttft_ms_p50`
- 엔진 로드 시간(NM) → `SPD.load_ms` 코어

## 6. 5 번째 사례 — VoiceGuard 2 모델 파이프라인(1.0.25 반영)

- 조사일: 2026-11-21. 대상: SoundAI.Lite VoiceGuard(Zipformer ASR → Granite 분류기, 단말 S4·S5) 영어 지원(eng-perf)·한국어 대표 세트(kor-perf) 측정 계약
- 근거: `SoundAI.Lite-eng-perf/docs/dev-plans/feature/2026-11-20-voiceguard-eng-plan/m5-measurement.md` §9.11(한계)·§9.12(results 조립 계약, r7 — 합성 검증 6 회)
- 성격: 앞 4 사례는 "지표 정의" 의 근거, 이 사례는 **생성기가 판정하지 못해 프로젝트 조립기·판정 표로 메운 공백** 의 근거

| 공백(1.0.23) | 사례에서의 결과 | 1.0.25 반영 |
|---|---|---|
| 구조적 fail 지표가 있으면 rc 0 불가 | 2 모델이라 `SPD.jitter`·`SPD.tail_over_hop` 이 기본 임계로 fail → "rc 1 기대" 로 운영, 판정을 생성기 밖 닫힌 판정 표로 옮김 | 예상 fail 사전 등록(`expected_fail`) |
| 예상 fail 이 양쪽에 나면 대상 쪽 악화가 가려짐 | "B′ 우세 fail = b 쪽 fail 수 > a 쪽" 을 조립기 판정 표에 둠 | 예상 fail 균형 항목(`regress`) |
| results 의 모든 회차를 판정 | 대체된 회차를 results 에서 빼고 별도 제외 목록으로 보존("invalid 회차도 남김" 과 어긋남) | 대체 회차(`superseded_by`) |
| ABBA 가 한쪽(≤ 허용폭)만 봄 | A ↔ A 블록을 a·b 뒤집어 한 번 더 싣고 판정 표로 결합 | 잡음 블록(`noise_for`) 양방향 + 대상 결합 |
| 쌍·블록 키 미검사 | manifest·threads 동일, ABBA 시작 대역 [32.0, 33.0] °C 를 조립기 검사로 보완 | 쌍·블록 키 검사, `abba_start_battery_min_c` |

### 합성 검증(반박 검증) 6 회에서 반복된 지적 유형

- 실측 전에 합성 원자료로 조립기·생성기를 돌려 계약의 구멍을 찾는 검증을 6 회 반복 — 회차마다 High 지적이 나온 유형
  - **신고 의존**: 재측정·제외 사유, 실패 여부를 하네스 신고값으로 받음 → 원자료에서 도출하고 신고와 다르면 조립 실패(measurement-control.md §8)
  - **기준 시각**: 실시간 lag 의 t0 를 첫 hop 투입 시각으로 두면 마감이 hop 길이만큼 완화됨(§9)
  - **종료 원인 구분 불가**: 하네스가 측정 대상을 종료시키거나 adb 세션 종료로 함께 죽으면 측정 대상 실패와 구분되지 않음(§10)
  - **한쪽 판정**: A ↔ A 잡음이 음수면 한쪽 판정에서 pass — 양방향이 아니면 잡음 대조가 되지 않음
  - **결과를 본 뒤 선택**: 재측정할 회차·쌍·반복 번호를 측정 뒤에 고름 → 반복 번호·쌍 구성·재측정 조건을 사전 고정
  - **조용한 누락**: 한쪽 구성에만 판정 항목이 있거나 세션이 끊긴(재부팅) 블록이 그대로 pass → 항목 집합·`boot_id` 대조
- 생성기에 넣지 않은 것(프로젝트 조립기 몫): 사유 코드 목록, 번들·빌드 결속, `boot_id` 연속성, t0 원천 대조, 출력 완전성
