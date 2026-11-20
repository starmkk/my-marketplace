# 결과 형식 — results.json·thresholds.json·원자료 행

- 완전한 예: `assets/example/`(results.json·thresholds.json·timing·samples). 테스트 픽스처를 겸하므로 생성기와 항상 일치함
- 프로젝트 몫: 자기 하네스 산출물을 이 형식으로 바꾸는 어댑터(모델마다 다름). 생성기 몫: 검증·시간/자원 계산·판정·렌더
- JSON 에 NaN·Infinity 금지(파싱 단계에서 rc 2)

---

## 1. thresholds.json(측정 전 동결)

- 기본 위치: 프로젝트 루트의 `experiments/port-metrics/thresholds.json`(모든 명령의 기본값, 프로젝트 저장소에 커밋)

| 키 | 내용 |
|---|---|
| `schema` | `port-metrics-thresholds/1` |
| `frozen_at` | ISO 8601 datetime(타임존 포함). null 이면 전 판정 not_established |
| `scope` | `{stages[], purposes[], model_types[], input_kind: audio|other}` — 필수 지표 범위의 정본 |
| `validity` | `{start_battery_max_c, wait_max_sec, sampler_min_n, sampler_max_gap_ratio}` + 선택 `abba_start_battery_min_c`. 그 밖의 키는 rc 2 |
| `rules[]` | `{metric, when{pair?, class?, stage?, subset?}, op: <=|>=|==|record, limit, noise_floor?, noise_source?, reason?, expected_fail?}` |
| `abba_limits_pct` | `{metric_id: 허용 열화 %}` |

- `when` 키: `pair`(`S1-S2`·`S2-S3`·`S3-S4`·`S4-S5`·`base`·`regress`), `class`(`fp`·`lowp`), `stage`(`S1`~`S5`), `subset`(`overall`·`each`·이름)
- 생성: `init-thresholds` (thresholds.md §3)
- `rules[].expected_fail`(선택): 예상 fail 사전 등록 사유(비어 있지 않은 문자열). `when.stage` 가 있는 규칙 ∧ 회차(scope = run) 지표 ∧ 범주 SPD·RES·PWR·THM
  일 때만 허용, `op: record` 규칙에는 불가(위반 = rc 2). `init-thresholds` 는 넣지 않음 → thresholds.md §6
- `validity.abba_start_battery_min_c`(선택, 수, ≤ `start_battery_max_c`): ABBA 블록이 참조하는 회차의 `thermal.start_battery_c` 가 이 값 미만이면
  그 블록 invalid(시작 온도 대역을 [하한, 상한] 으로 고정). 키가 있는데 그 회차에 `thermal` 이 없어도 invalid. 키가 없으면 검사하지 않음

## 2. results.json

```json
{
  "schema": "port-metrics-results/1",
  "project": {"name": "...", "task_metric": {"id": "cer", "unit": "%", "direction": "lower"}},
  "runs": [ ... ],
  "pairs": [ ... ],
  "abba": [ ... ]
}
```

### 2.1 runs[]

| 키 | 조건 | 내용 |
|---|---|---|
| `run_id` | 필수 | 유일 |
| `stage` | 필수 | `S1`~`S5`, thresholds scope 안 |
| `backend` | 필수 | `cpu`·`cuda`·`opencl`·`vulkan` |
| `run_kind` | 필수 | `perf`·`sampler`·`accuracy` |
| `pacing` | perf 필수 | `max`·`realtime` |
| `profile` | 필수 | `<weight>-<precision>-<memory>-t<N>`(profiles.md) |
| `effective` | 필수 | `{weight_storage, matmul_accum, activation_quant}` 실측 실효값 |
| `started_at` | 필수 | ISO 8601 datetime, frozen_at 이후 |
| `identity` | 필수 | 단계별 필수 키(measurement-control.md §1) + `thresholds_sha256` |
| `thermal` | S4·S5 의 perf·sampler 필수 | `{start_battery_c, clock_restored, wait_sec, pause_events, source}` |
| `nonce` | perf·sampler 필수 | sampler 는 같은 nonce 의 perf 1 개와 1:1(stage·backend·profile·git_sha 동일) |
| `timing` | perf 필수(그 외 금지) | timing.jsonl 경로(results.json 기준 상대) |
| `samples` | sampler 필수(그 외 금지) | samples.jsonl 경로 |
| `meta` | 선택 | 아래 표 |
| `values` | 선택 | `[{metric, value, subset?}]` — catalog source=project 지표만 |
| `acc_baseline` | 선택 | S1 ACC 기준 회차 지정(후보 2 개 이상일 때) |
| `superseded_by` | 선택 | 이 회차를 대체한 재측정 회차의 run_id — 있으면 **대체된 회차**(판정 제외) |
| `superseded_reason` | `superseded_by` 와 함께 필수 | 대체 사유(비어 있지 않은 문자열 — 원자료에서 도출한 사유 코드 권장) |

- **대체된 회차**: 판정 항목을 만들지 않고(집계·rc 무영향) 원자료(timing·samples)도 읽지 않음. acc_baseline 후보·필수 지표 누락 검사·nonce 1:1 계산에서 빠짐.
  리포트 §1 유효성 칸에 `대체됨 → <run_id>(사유)`, 회차 문제(§7)는 그대로 표시. 문제없는 회차를 대체했으면 `신원·열 검사 통과 회차 대체(원자료 품질 미검사)` 표시
- 대체 형식 검사(위반 = rc 2): 미지 run·자기 참조·순환·stage 다름, 대체하는 회차의 `started_at` 이 더 늦어야 함, `run_kind`·`pacing`·`backend`·`profile`·
  `effective`·`identity.{git_sha, manifest_sha256, threads_effective}` 동일(같은 역할의 재측정), 대체된 회차를 `pairs[]`·`abba[]` 가 참조
- sampler 가 대체된 perf 와 nonce 로 묶여 있으면(재측정 perf 가 다른 nonce) 형식 오류가 아니라 그 sampler 지표 invalid(`perf 짝 <id> 는 대체됨`) —
  재측정 perf 와 같은 nonce 로 sampler 도 다시 잼

| meta 키 | 쓰는 지표 |
|---|---|
| `rss_peak_kb` | RES.rss_peak_mib(perf 회차 VmHWM·ru_maxrss, kB) |
| `bundle_bytes` | RES.bundle_mib(S2) |
| `hop_ms` | SPD.step_p95_over_hop·SPD.tail_over_hop |
| `window_sec` | STB.soak_p99_ratio·THM.drift(있으면 soak 회차로 계산) |
| `wall_total_sec`·`audio_total_sec` | SPD.tail_over_hop(realtime) |
| `clk_tck`·`sample_interval_sec`·`work_amount` | sampler 지표 |

### 2.2 pairs[]

```json
{"pair_id": "s2-s3-fp16", "kind": "chain", "ref": "<run_id>", "target": "<run_id>",
 "values": [{"metric": "NUM.max_abs", "tensor": "encoder_out", "value": 2.1e-5},
            {"metric": "DEC.match_rate", "value": 1.0}]}
```

- `kind`: `chain`(인접 단계만) · `base`(ref = S1) · `regress`(같은 단계 옛 → 새)
- class 는 두 회차 `effective` 에서 생성기가 판단(하나라도 lowp → lowp)
- 키 검사(위반 = 그 쌍 항목 invalid): 두 회차 `identity.manifest_sha256` 동일(모든 kind), `threads_effective` 동일(`regress` 와 S1 이 끼지 않은 `chain` —
  S1 은 PT 스레드라 의미가 달라 면제, `base` 면제)

### 2.3 abba[]

```json
{"abba_id": "mnn-patch-0042", "metrics": ["SPD.rtf_max", "SPD.lat_p99", "RES.rss_peak_mib"],
 "pairs": [{"a": "old-1", "b": "new-1"}, {"a": "old-2", "b": "new-2"}, {"a": "old-3", "b": "new-3"}]}
```

- a = 기준(옛 빌드·구성 A), b = 대상. 순서(AB·BA)는 `started_at` 에서 도출 — 둘 다 있어야 유효, 쌍 ≥ 3
- metrics 는 catalog 에 `abba_limit_pct` 가 있는 지표만(없으면 rc 2)
- **perf 지표와 sampler 지표는 블록을 나눔**: `SPD.*`·`RES.rss_peak_mib` 는 perf 회차 쌍, `RES.cpu_s_per_unit`·`RES.pss_mean_mib` 는 sampler 회차 쌍으로 별도 abba 블록. 한 블록에 섞으면 한쪽 회차에 값이 없어 not_established
- 같은 회차를 한 블록에서 두 번 쓰거나 started_at 이 같아 순서를 못 정하면 그 블록 invalid
- 블록 안 모든 회차의 `identity.threads_effective` 가 같아야 함(다르면 그 블록 invalid)
- `noise_for`(선택): 다른 블록의 abba_id — 이 블록이 그 블록(A ↔ B′)의 **A ↔ A 잡음 대조**임을 표시
  - 형식(위반 = rc 2): 미지 블록·자기 참조·잡음 블록을 다시 가리킴, 잡음 블록 `metrics` ⊄ 대상 블록 `metrics`
  - 구성(위반 = 잡음 블록 항목 invalid): 블록 안 모든 회차 `git_sha` 동일, a 쪽 `git_sha`·`profile` == 대상 a 쪽, `stage`·`run_kind`·`pacing`·
    `manifest_sha256`·`threads_effective` == 대상
  - 판정: 잡음 블록은 양방향(|쌍별 Δ% 중앙값| ≤ 같은 허용폭, 값은 부호 유지). 대상 블록 지표가 pass 인데 같은 지표의 잡음 블록 항목이 pass 가 아니면
    대상 항목 = `not_established`(허용폭은 넓히지 않음). 대상 fail·invalid 는 그대로

## 3. 원자료 행

### 3.1 timing.jsonl(perf 회차, 처리 단위 1 행)

| 키 | 필수 | 의미 |
|---|---|---|
| `unit_id` | ○ | 처리 단위 id(파일·청크·구간·요청) |
| `wall_ms` | ○ | 그 단위 처리 시간(ms, ≥ 0) |
| `kind` | ○ | `steady`·`warmup`·`flush`·`aux` |
| `paused` | ○ | 열 정지 구간에 걸쳤는가 |
| `audio_sec` | 오디오 | 그 단위가 담은 오디오 길이 |
| `units` | 비오디오 | 처리량 단위 수(토큰·구간) |
| `t_start_sec` | soak | 회차 시작 기준 단위 시작 시각 |
| `deadline_miss` | streaming | 마감 초과 여부 |
| `prefill_ms`·`decode_ms`·`gen_tokens`·`ttft_ms` | llm | LLM 구간 시간·토큰 |

- 단위 선택: 파일 단위 행이면 RTF·지연 = 파일 기준, 청크 단위 행이면 청크 기준. 지연 분위수의 의미가 바뀌므로 project 문서에 단위를 명시
- warmup·paused 행은 전 집계 제외, flush·aux 행은 분위수만 제외(RTF·처리량엔 포함)

### 3.2 samples.jsonl(sampler 회차, 표본 1 행)

| 키 | 필수 | 의미 |
|---|---|---|
| `t_sec` | ○ | 단말 monotonic 기준 표본 시각 |
| `cpu_ticks` | ○ | 프로세스 누적 utime + stime(tick) |
| `rss_kb` | ○ | VmRSS(kB) |
| `paused` | ○ | 표본 시점 정지 여부 |
| `pss_kb` | 선택 | smaps_rollup Pss(kB) |
| `hwm_kb` | 선택 | VmHWM(kB) |

## 4. 어댑터 작성 체크

- [ ] 실효값(`effective`·`threads_effective`)을 요청값이 아니라 엔진 보고·로그에서 채웠나
- [ ] 메모리 원자료를 kB 그대로 넘겼나(MiB 변환은 생성기)
- [ ] 분위수·RTF 를 어댑터에서 미리 계산해 넣지 않았나(생성기 지표를 values 에 넣으면 rc 2)
- [ ] 열 정지 구간 행에 `paused = true` 를 표시했나
- [ ] 회차마다 `thresholds_sha256`·`started_at` 을 하네스가 측정 시점에 기록했나
- [ ] scope 밖(목적·유형이 동결 범위에 없는) 판정 지표를 values 에 넣지 않았나 — 규칙이 전개되지 않아 not_established(rc 1). 생성기가 자동 계산한 scope 밖 지표는 record_only 로만 표시됨
- [ ] 신원 키를 빈 문자열로 채우지 않았나(빈 값 = 누락 = invalid)
- [ ] 재측정으로 대체된 회차를 지우지 않고 `superseded_by`·`superseded_reason` 으로 남겼나(사유는 하네스 신고가 아니라 원자료에서 도출)
- [ ] 쌍(pairs) 두 회차와 ABBA 블록 회차의 `manifest_sha256`·`threads_effective` 가 같은가(다르면 invalid)
- [ ] A ↔ A 잡음 블록에 `noise_for` 를 달았나(없으면 한쪽 판정이라 음의 잡음이 pass 로 보임)
- [ ] `regress` 에 예상 fail 이 있으면 그 회차 stage·pacing 의 그 지표를 판정하는 A ↔ B′ ABBA 블록을 실었나(없으면 균형 항목 not_established)
