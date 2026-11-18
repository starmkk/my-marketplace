# 지표 카탈로그 — 정의·이유·주의

- 정본: `assets/catalog.json`. 이 문서의 **생성 표**(§9)는 `make_report.py catalog-md --write` 로만 갱신함(수기 수정 금지, 테스트가 동기 검사)
- 기본 임계 수치는 생성 표와 `init-thresholds` 출력에만 있음. 아래 설명 절에는 수치를 쓰지 않음
- 표기: core = 항상, purpose = 목적 태그, ext = 모델 유형 확장, optional = 필수 아님(있으면 판정)

---

## 1. NUM — 텐서 동등성("변환·이식이 수치를 보존했나")

- 대상: 인접 단계 쌍(S1-S2·S2-S3·S3-S4)의 출력·상태 텐서. S1 쪽은 **CPU fp32 골든**(또는 TF32 off CUDA 를 CPU 와 대조한 것)
- `NUM.max_abs`·`NUM.rel_l2`·`NUM.cos_min` 은 프로젝트가 float64 누산으로 계산해 텐서별(`tensor` 키)로 제공
- class(`fp`·`lowp`)에 따라 판정 지표가 달라짐 — fp 는 절대 오차(max_abs·rel_l2), lowp(int8 가중치·fp16 연산·활성 양자화)는 방향 유사도(cos·rel_l2)
  - 느슨한 lowp 임계를 fp 에 쓰면 결함 fp16 번들(Const 까지 half)도 통과함(SpeechLM `--fp16` rel_l2 2.4e-3)
- S3-S4 fp 의 rel_l2 는 기록만: ARM NEON exp 근사·Strassen 진입점 차로 비트 동일이 구조적으로 불가(SpeechLM state rel_l2 2.89e-3, SoundAI Δmargin 1.13e-3) → 판정은 DEC·ACC 가 맡음
- 비교기 안전장치(프로젝트 쪽 구현 요구): shape·프레임 수 불일치·원소 0 개·NaN/Inf = 실패, 짧은 쪽 절단 금지(Nemotron compare.py)

## 2. DEC — 판정 동등성("최종 출력이 같은가")

- `DEC.match_rate`: 최종 출력 바이트 동일 비율. 같은 libMNN 을 쓰는 S2-S3, 같은 단말의 S4-S5, 같은 단계 옛/새 빌드(regress)는 완전 일치가 기대값
  - S4-S5 가 완전 일치면 S4 의 정확도 근거를 S5 에 그대로 승계함(앱 경로에서 재채점 불필요)
- `DEC.flip`·`DEC.severe_flip`: 결정이 바뀐 건수와 그중 심각한 것. 일치율이 높아도 심각 flip 1 건이 더 중요할 수 있음(SpeechLM 없음↔위험)
  - 심각의 정의는 프로젝트가 결과 생성 전에 고정(분류 = 양성↔음성, 등급 = 2 단계 이상 도약 등)
- `DEC.margin_delta_max`(classifier): 확률 차 Δp 는 p≈0.5 에서 σ' 로 확대돼 잡음 바닥보다 작은 임계가 됨 → 결정 logit 차(margin)로 판정(SoundAI D18)
- `DEC.token_match_rate`(llm): 생성 토큰열 완전 일치. 분기는 동률 근처(tie margin)에서 생기므로 원인 분석은 root-cause.md §4

## 3. ACC — 태스크 정확도("쓸 만한가")

- `ACC.primary`: 모델별 주지표 값(서브셋별 + 전체). 정답 라벨이 없으면 S1 출력을 기준선으로 삼고 그 사실을 project 에 명시
- `ACC.degradation`: S1 대비 열화량(방향 반영, 양수 = 나빠짐). 서브셋별(`each`)과 전체(`overall`) 임계를 따로 동결
  - 평균 지표는 소수 입력의 대형 실패를 숨김 → 꼬리 지표가 필요하면 서브셋(파일·셋) 단위로 제공(Nemotron 파일별 사고 칸)
  - "S1 보다 좋아짐"을 개선 주장 근거로 쓰지 않음(하측 제한 없음, Nemotron tf ΔDER 음수)
- 기준 회차: S1 의 ACC.primary 회차 1 개(CUDA 정확도 회차). 골든 텐서 회차(CPU)와 둘 다 값을 내면 `acc_baseline` 으로 지정

## 4. SPD — 속도("제때 처리하나")

- `SPD.rtf_max`: 최대 속도 투입(pacing=max) 처리량. Σwall ÷ Σaudio — 파일별 비율의 평균이 아님
- `SPD.rtf_rt`: 실시간 투입(pacing=realtime). 1 근처가 정상이라 처리량 비교에 쓰지 않음
  - 같은 구성이 측정 방식에 따라 RTF 0.995~1.538 로 달랐음(Nemotron RTF 4 종) → 이름에 방식을 박음
- `SPD.units_per_sec`: 오디오가 아닌 입력(텍스트 등)의 처리량. 단위 정의(토큰·구간)는 project 에 명시
- `SPD.lat_*`: steady 행만의 nearest-rank 분위수. flush·warmup 이 섞이면 지터가 구조적으로 커짐(Zipformer KPI-4 3.94)
- `SPD.load_ms`: 엔진 생성 cold. 사용자 체감 대기 시간(SpeechLM 3.2 s ↔ 재생성 4.9~5.4 s)
- streaming 확장: `SPD.jitter`(p99 ÷ p50), `SPD.step_p95_over_hop`(처리 단위가 hop 안에 끝나는가), `SPD.tail_over_hop`(입력 종료 후 마지막 결과까지), `SPD.deadline_miss`
  - 실시간 가능 여부는 평균이 아니라 step 이 hop 안에 끝나는지로 결정됨(Nemotron R1)
- llm 확장: `SPD.prefill_ms_p50`·`SPD.ttft_ms_p50`·`SPD.decode_tok_s` — decode 속도는 prefill·샘플링을 뺀 구간으로만(SpeechLM decode_only_tok_s, predict 전체 기준과 혼용 금지)

## 5. RES — 자원("단말을 얼마나 쓰나")

- `RES.rss_peak_mib`: perf 회차 프로세스 수명 최대 RSS(VmHWM·ru_maxrss). 저메모리 단말 LMK 위험과 직결. S5 값에는 ART 가 포함됨
- `RES.bundle_mib`: 배포 번들 바이트. 다운로드·저장 공간
- sampler 회차 지표(`RES.cpu_*`·`RES.pss_*`): perf 회차와 분리해 nonce 로 결속
  - CPU % 는 thread 상한(4 스레드 ≈ 400 %)에 붙어 구성 비교가 안 됨 → 효율 비교는 `RES.cpu_s_per_unit`
  - PSS 는 단일 최댓값 대신 평균·p95 — 최댓값은 로드 순간 1 표본 포착 운에 좌우(SpeechLM)
- `RES.rss_after_release_mib`(optional): 기능을 껐다 켜는 앱에서 누적 위험(SpeechLM purge −162.4 MB)

## 6. THM·STB·PWR — 장시간·안정성

- `THM.start_battery_c`·`THM.pause_events`: 측정 조건 기록. 시작 조건 위반 회차는 invalid(measurement-control.md §2)
- `STB.soak_p99_ratio`·`THM.drift`(ship): 장시간 실행에서 지연 꼬리·중앙값이 얼마나 나빠지는가. 30 분 연속 기준(Zipformer KPI-7, Nemotron G5-thermal)
- `STB.deterministic`·`STB.reuse_identical`: 재실행·엔진 재사용 시 출력 동일 — 엔진 재사용 앱에서 상태 누수 검사
- `PWR.mah_per_unit`(optional): 4 사례 모두 미측정 공백. 측정 수단(current_now 적분·batterystats)과 충전 해제 조건을 함께 기록

## 7. CNV — 변환 검증(convert)

- `CNV.audit_ok`: MNN 은 양자화 파라미터 파싱 실패·이름 불일치에도 rc 0 → 번들 바이트 감사가 유일한 실패 지점(Zipformer `audit_quantization`)
- `CNV.act_range_margin`(optional): fp16 연산(precision low) 계획 시 PT 활성 absmax 대비 fp16 최댓값 여유. 잔차 흐름이 65504 를 넘으면 fp16 붕괴(SpeechLM 층 15 102,973)
- 잡음 바닥은 지표가 아니라 thresholds 규칙의 `noise_floor` 로 기록(thresholds.md §2)

## 8. MQ — 측정 품질

- `MQ.excluded_rows`: 집계에서 빠진 행 수 — 제외가 많으면 대표성 의심
- `MQ.sampler_n`·`MQ.sampler_gap_ratio`: 샘플러 품질. 기준 미달이면 그 회차 sampler 지표 전체 invalid

## 9. 생성 표(catalog.json 렌더)

<!-- port-metrics:catalog-table:begin -->

### 지표 표(45 종)

| id | 이름 | 수준 | 범위 | 단계·문맥 | 입력 | 출처/회차 | 형, 단위 | 방향 | 판정 | ABBA % | ABBA 필수 목적 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `NUM.max_abs` | 텐서 최대 절대 오차 | core | pair | S1-S2 S2-S3 S3-S4 | audio·other | project/any | float, abs | lower | 판정 | - | - |
| `NUM.rel_l2` | 텐서 상대 L2 오차 | core | pair | S1-S2 S2-S3 S3-S4 | audio·other | project/any | float, ratio | lower | 판정 | - | - |
| `NUM.cos_min` | 텐서 코사인 유사도 최솟값 | core | pair | S1-S2 S2-S3 S3-S4 | audio·other | project/any | float, ratio | higher | 판정 | - | - |
| `DEC.match_rate` | 출력 완전 일치율 | core | pair | S1-S2 S2-S3 S3-S4 S4-S5 base regress | audio·other | project/any | float, ratio | higher | 판정 | - | - |
| `DEC.flip` | 판정 변경 건수 | core | pair | S1-S2 S3-S4 base | audio·other | project/any | int, count | lower | 기록 | - | - |
| `DEC.severe_flip` | 심각 판정 변경 건수 | core | pair | base | audio·other | project/any | int, count | lower | 판정 | - | - |
| `ACC.primary` | 태스크 주지표 | core | run | S1 S2 S3 S4 S5 | audio·other | project/any | float, task | none | 기록 | - | - |
| `ACC.degradation` | S1 대비 정확도 열화 | core | run | S2 S3 S4 S5 | audio·other | generator/any | float, task | lower | 판정 | - | - |
| `SPD.rtf_max` | 처리량 RTF(최대 속도 투입) | core | run | S1 S2 S3 S4 S5 | audio | generator/perf | float, x | lower | 판정 | 5 | regress·optimize |
| `SPD.rtf_rt` | 실시간 투입 RTF | purpose(ship) | run | S4 S5 | audio | generator/perf | float, x | lower | 기록 | - | - |
| `SPD.units_per_sec` | 처리량(단위/s) | core | run | S1 S2 S3 S4 S5 | other | generator/perf | float, units/s | higher | 기록 | 5 | regress·optimize |
| `SPD.lat_p50` | 단위 지연 p50 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | 5 | - |
| `SPD.lat_p95` | 단위 지연 p95 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | 5 | - |
| `SPD.lat_p99` | 단위 지연 p99 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | 5 | regress·optimize |
| `SPD.lat_max` | 단위 지연 최댓값 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | - | - |
| `SPD.load_ms` | 엔진 로드 시간 | core | run | S2 S3 S4 S5 | audio·other | project/perf | float, ms | lower | 기록 | - | - |
| `RES.rss_peak_mib` | 최대 상주 메모리 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | float, MiB | lower | 기록 | 2 | regress·optimize |
| `RES.bundle_mib` | 모델 번들 크기 | core | run | S2 | audio·other | generator/any | float, MiB | lower | 기록 | - | - |
| `MQ.excluded_rows` | 집계 제외 행 수 | core | run | S1 S2 S3 S4 S5 | audio·other | generator/perf | int, count | none | 기록 | - | - |
| `THM.start_battery_c` | 회차 시작 배터리 온도 | core | run | S4 S5 | audio·other | generator/perf | float, degC | none | 기록 | - | - |
| `THM.pause_events` | 열 정지 사건 수 | core | run | S4 S5 | audio·other | generator/perf | int, count | lower | 기록 | - | - |
| `CNV.audit_ok` | 변환 산출물 감사 | purpose(convert) | run | S2 | audio·other | project/any | bool, bool | none | 판정 | - | - |
| `CNV.act_range_margin` | fp16 활성 범위 여유 | optional(convert) | run | S1 | audio·other | project/any | float, x | higher | 판정 | - | - |
| `RES.cpu_s_per_unit` | 작업량당 CPU 시간 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, s/unit | lower | 기록 | 2 | optimize |
| `RES.cpu_pct_mean` | CPU 사용률 평균 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, % | lower | 기록 | - | - |
| `RES.cpu_pct_max` | CPU 사용률 최대 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, % | lower | 기록 | - | - |
| `RES.pss_mean_mib` | PSS 평균 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, MiB | lower | 기록 | 2 | optimize |
| `RES.pss_p95_mib` | PSS p95 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, MiB | lower | 기록 | - | - |
| `MQ.sampler_n` | 샘플 수 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | int, count | higher | 기록 | - | - |
| `MQ.sampler_gap_ratio` | 샘플 최대 간격 비 | purpose(optimize·ship) | run | S3 S4 S5 | audio·other | generator/sampler | float, ratio | lower | 기록 | - | - |
| `STB.soak_p99_ratio` | 장시간 지연 p99 비 | purpose(ship) | run | S4 S5 | audio·other | generator/perf | float, ratio | lower | 판정 | - | - |
| `THM.drift` | 지속 부하 열 드리프트 | purpose(ship) | run | S4 S5 | audio·other | generator/perf | float, ratio | lower | 판정 | - | - |
| `STB.deterministic` | 반복 실행 결정성 | purpose(ship) | run | S4 S5 | audio·other | project/any | bool, bool | none | 판정 | - | - |
| `STB.reuse_identical` | 엔진 재사용 동일성 | optional(ship) | run | S4 S5 | audio·other | project/any | bool, bool | none | 판정 | - | - |
| `RES.rss_after_release_mib` | 해제 후 잔류 메모리 | optional(ship) | run | S4 S5 | audio·other | project/any | float, MiB | lower | 기록 | - | - |
| `PWR.mah_per_unit` | 작업량당 배터리 소모 | optional(ship) | run | S4 S5 | audio·other | project/any | float, mAh/unit | lower | 기록 | - | - |
| `SPD.jitter` | 지연 지터 | ext(streaming) | run | S3 S4 S5 | audio·other | generator/perf | float, ratio | lower | 판정 | - | - |
| `SPD.step_p95_over_hop` | step p95 ÷ hop | ext(streaming) | run | S3 S4 S5 | audio·other | generator/perf | float, ratio | lower | 판정 | - | - |
| `SPD.tail_over_hop` | 종료 꼬리 지연 ÷ hop | ext(streaming) | run | S4 S5 | audio | generator/perf | float, ratio | lower | 판정 | - | - |
| `SPD.deadline_miss` | 마감 초과 건수 | ext(streaming) | run | S4 S5 | audio·other | generator/perf | int, count | lower | 판정 | - | - |
| `SPD.prefill_ms_p50` | prefill 시간 p50 | ext(llm) | run | S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | - | - |
| `SPD.ttft_ms_p50` | 첫 토큰 시간 p50 | ext(llm) | run | S2 S3 S4 S5 | audio·other | generator/perf | float, ms | lower | 기록 | - | - |
| `SPD.decode_tok_s` | decode 전용 토큰 속도 | ext(llm) | run | S2 S3 S4 S5 | audio·other | generator/perf | float, tok/s | higher | 기록 | 5 | - |
| `DEC.token_match_rate` | 토큰열 완전 일치율 | ext(llm) | pair | S1-S2 S2-S3 S3-S4 S4-S5 base | audio·other | project/any | float, ratio | higher | 기록 | - | - |
| `DEC.margin_delta_max` | 판정 마진 차 최댓값 | ext(classifier) | pair | S2-S3 S3-S4 base | audio·other | project/any | float, logit | lower | 판정 | - | - |

### 기본 규칙 표

| 지표 | 조건(when) | 규칙 |
|---|---|---|
| `NUM.max_abs` | pair=S1-S2, class=fp | <= 0.001 |
| `NUM.max_abs` | pair=S1-S2, class=lowp | record |
| `NUM.max_abs` | pair=S2-S3 | <= 0.001 |
| `NUM.max_abs` | pair=S3-S4, class=fp | <= 0.001 |
| `NUM.max_abs` | pair=S3-S4, class=lowp | record |
| `NUM.rel_l2` | pair=S1-S2, class=fp | <= 0.0001 |
| `NUM.rel_l2` | pair=S1-S2, class=lowp | <= 0.05 |
| `NUM.rel_l2` | pair=S2-S3 | <= 0.0001 |
| `NUM.rel_l2` | pair=S3-S4, class=fp | record |
| `NUM.rel_l2` | pair=S3-S4, class=lowp | <= 0.05 |
| `NUM.cos_min` | pair=S1-S2, class=fp | record |
| `NUM.cos_min` | pair=S1-S2, class=lowp | >= 0.99 |
| `NUM.cos_min` | pair=S2-S3 | record |
| `NUM.cos_min` | pair=S3-S4, class=fp | record |
| `NUM.cos_min` | pair=S3-S4, class=lowp | >= 0.99 |
| `DEC.match_rate` | pair=S1-S2 | record |
| `DEC.match_rate` | pair=S2-S3 | >= 1 |
| `DEC.match_rate` | pair=S3-S4 | record |
| `DEC.match_rate` | pair=S4-S5 | >= 1 |
| `DEC.match_rate` | pair=base | record |
| `DEC.match_rate` | pair=regress | >= 1 |
| `DEC.severe_flip` | pair=base | <= 0 |
| `ACC.degradation` | subset=overall | <= null(프로젝트 기입) |
| `ACC.degradation` | subset=each | <= null(프로젝트 기입) |
| `SPD.rtf_max` | stage=S1 | record |
| `SPD.rtf_max` | stage=S2 | record |
| `SPD.rtf_max` | stage=S3 | record |
| `SPD.rtf_max` | stage=S4 | <= null(프로젝트 기입) |
| `SPD.rtf_max` | stage=S5 | <= null(프로젝트 기입) |
| `CNV.audit_ok` | (전체) | == true |
| `CNV.act_range_margin` | (전체) | >= 4 |
| `STB.soak_p99_ratio` | (전체) | <= 1.2 |
| `THM.drift` | (전체) | <= 0.15 |
| `STB.deterministic` | (전체) | == true |
| `STB.reuse_identical` | (전체) | == true |
| `SPD.jitter` | stage=S3 | record |
| `SPD.jitter` | stage=S4 | <= 2 |
| `SPD.jitter` | stage=S5 | <= 2 |
| `SPD.step_p95_over_hop` | stage=S3 | record |
| `SPD.step_p95_over_hop` | stage=S4 | <= 1 |
| `SPD.step_p95_over_hop` | stage=S5 | <= 1 |
| `SPD.tail_over_hop` | (전체) | <= 1 |
| `SPD.deadline_miss` | (전체) | == 0 |
| `DEC.margin_delta_max` | pair=S2-S3 | <= null(프로젝트 기입) |
| `DEC.margin_delta_max` | pair=S3-S4 | <= null(프로젝트 기입) |
| `DEC.margin_delta_max` | pair=base | <= null(프로젝트 기입) |

- 규칙이 없는 판정 지표 값은 not_established, 기록 지표는 record_only

<!-- port-metrics:catalog-table:end -->
