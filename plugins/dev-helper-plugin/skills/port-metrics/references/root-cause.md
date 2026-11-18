# 불일치 원인 추적 — MNN 결과가 PT 와 안 맞을 때

- 목적: 판정 fail 이 났을 때 임계를 완화하지 않고 원인을 단계·모듈·op 단위로 좁히는 공통 절차
- 원칙: **임계 완화 금지 → 원인 규명**. 원판정(fail)은 그대로 보존하고, 원인과 사용자 결정을 함께 기록함
- 근거: Zipformer P1(A9 참조 교체·A10 w8a 층 fp32 유지), SpeechLM audio-parity-review-report(교차 주입·α 스윕),
  SoundAI g6-delta layer-dump(op 단위 첫 이탈), Nemotron P1(전처리 버퍼 bf16)·FIN(제거법)

---

## 1. 단계 사슬로 좁히기(어느 단계에서 갈라졌나)

- 인접 단계 쌍(NUM·DEC)을 앞에서부터 보고 **처음 임계를 넘는 쌍**이 원인 단계임
  - S1 골든 → (ONNX/ORT) → S2 pymnn → S3 C++ → S4 단말 → S5 앱
  - 변환 경로에 ONNX 가 있으면 PT↔ORT 를 별도 쌍으로 둠(변환기 문제와 MNN 문제 분리, Zipformer G1)
- 참조를 중간 산출물 재계산으로 바꾸지 않음 — 오차가 사슬로 누적돼 원인이 가려짐(Zipformer C-F2 기각)
- pymnn 과 C++ 은 다른 빌드일 수 있음 → C++ 측 텐서 덤프(`Module_Forward_Separate` + dump_dir 등)로 pymnn 과 직접 비교(Zipformer P1 §5)

## 2. 기준점 자체를 먼저 의심

| 증상 | 확인 | 사례 |
|---|---|---|
| 변환 전(ORT) 부터 임계 초과 | 참조가 CUDA·TF32 인지. CPU fp32 참조와 ORT 차를 잼 | Zipformer: JIT-CUDA 참조 시 ORT max_abs 4.85e-3 ↔ JIT-CPU 2.9e-6 |
| PT 체크포인트 자체가 원본 카드와 다름 | 전처리 버퍼·상수가 bf16 반올림인지 비트 비교 | Nemotron: `.nemo` window·fb 버퍼 bf16 → fp32 교체 후 ΔDER 0.00 |
| 상수 하나가 미세하게 다름 | 그래프 상수 덤프(`load_as_dict`·JSON) vs PT buffer 실측 | SpeechLM: embed_scale 25.298(sqrt) ↔ PT 25.25(bf16 절단) |
| 구현 간 차가 이미 임계 수준 | eager↔sdpa·thread 1↔4·CPU↔GPU 잡음 바닥 | Nemotron: eager↔sdpa 2.93e-4 > 임계 1e-4 → not_established |

- TF32 는 PyTorch 기본 on(cudnn) — S1 기록에 `tf32` 키 필수

## 3. 변환 산출물 감사(실행 전에 번들을 의심)

- MNN 은 양자화 파라미터 파싱 실패·op 이름 불일치에도 rc 0 → **번들 바이트로 감사**(Zipformer `audit_quantization`, SoundAI Const DT_HALF 0 건)
- 점검 항목: 의도한 fp32 유지 op 수, half Const 수(`--fp16` 이 위치인코딩 등 Const 까지 half 로 만든 사례, SpeechLM rel_l2 2.4e-3), op 목록(GELU 근사 기본값, Nemotron `--useGeluApproximation 0`), 양자화 대칭 여부
- 변환기 결정성: 같은 입력 2 회 변환 JSON 덤프(uuid 제거) 동일 + 음성 대조군(1e-7 변경 → 다름)(Nemotron converter-equivalence)

## 4. 모듈·op 단위로 좁히기

| 방법 | 절차 | 쓰는 수치 | 사례 |
|---|---|---|---|
| op 덤프 첫 이탈 | 같은 입력으로 두 쪽 op 출력 저장(`Session_Debug` 콜백 등) → op 순서 동일 단언 → op 별 rel_l2·max_abs → 처음 벌어지는 op | op 별 rel_l2 | SoundAI: L0 attention Softmax(5.5e-7 → 4.9e-6) → ARM exp 근사 |
| 교차 주입 | 한 모듈 출력을 상대 쪽 값으로 바꿔 넣고 결과 일치 수 측정 | 결과 일치 수 | SpeechLM: PT audio_embed 주입 356/356 → 분기 100 % audio 몫 |
| α 스윕(허용치 곡선) | ref + α·(target − ref) 주입, α 별 결과 분기 수 | rel_l2 vs 분기 수 | SpeechLM: rel_l2 ≲ 1e-3 에서 분기 1, 3.5e-4 에서 0 → 허용치 근거 |
| PT fake-quant | PT 에 같은 양자화 규칙 적용 → MNN 과 비교 | rel_l2·flip | SpeechLM·SoundAI: MNN 오차 ≈ fake-quant 오차 → 런타임 결함 아님 |
| 층 감도 | 층군별 단독 양자화 rel_l2, 최악 청크 주원인 텐서 | 층별 rel_l2 | Zipformer: `encoder_embed.conv.0` → 6 층 fp32 유지 |
| 프로파일 2×2 귀속 | 서브모듈별 precision 을 교차(audio low × LLM high 등) | 불일치 trigger 공통 여부 | SpeechLM: 인코더 fp16 단독 불일치 0, 심각 flip 은 LLM fp16 |
| 제거법 | 같은 정밀도(fp32) 진단 행을 추가해 정밀도 요인 제거 | ΔDER 등 | Nemotron: fp32 hn ② +0.004 → 단말 fp16 연산이 원인 |
| tie margin | 분기 스텝 1·2 위 logit 차 | margin | SpeechLM: 0.00008~0.0072 → 동률 근처 불가피 분기 |

## 5. 상태 누적 vs 단발 오차

- 스트리밍·LLM 은 teacher-forced(상태 주입) 와 free-running 을 함께 봄 — tf 는 누적 오차를 숨김(Nemotron W8A8 tf −0.019 ↔ fr +0.245)
- 청크 진행에 따른 state rel_l2 추이(step 1 → 20 → 80, 압축 2 회 포함)로 발산 여부 확인(Nemotron G4-chain, SpeechLM 73 청크 추이)

## 6. 성능 불일치 추적

- 같은 단말에서 차이가 나면 먼저 **코어 배치**: 스레드별 `/proc/<pid>/task/<tid>/stat` processor 표본 + `Cpus_allowed_list`(Zipformer JNI +43.5 % = foreground cpuset 이 prime 코어 제외)
- 열·클럭: `scaling_cur_freq` 분포와 상한 유지 비율. 절대 지연 비교는 같은 열 상태 교대 측정(ABBA)만 근거로 씀(Nemotron latency-ab)
- 1 % 미만 차는 시간 지표로 분해 불가 → simpleperf 명령어 수로 경로 동등성 확인(Zipformer +0.0001 %)
- 소스 근거가 필요하면 on-device-ai-plugin `mnn-source-inspector` 에이전트로 MNN 소스 분기를 확정

## 7. 기록 형식

- 원인 추적 결과는 fail 판정 옆에 `원인 단계 / 원인 모듈·op / 근거 수치 / 사용자 결정(수용·패치·프로파일 제외)` 4 칸으로 남김
- MNN 을 패치했으면 패치 sha 를 `identity.mnn_patches_sha256` 에 반영하고 `regress` 목적으로 재측정(옛/새 바이트 동일 + ABBA)
