# 결과 형식 — results.json·thresholds.json·원자료 행

- 완전한 예: `assets/example/`(results.json·thresholds.json·timing·samples). 테스트 픽스처를 겸하므로 생성기와 항상 일치함
- 프로젝트 몫: 자기 하네스 산출물을 이 형식으로 바꾸는 어댑터(모델마다 다름). 생성기 몫: 검증·시간/자원 계산·판정·렌더
- JSON 에 NaN·Infinity 금지(파싱 단계에서 rc 2)

---

## 1. thresholds.json(측정 전 동결)

| 키 | 내용 |
|---|---|
| `schema` | `port-metrics-thresholds/1` |
| `frozen_at` | ISO 8601 datetime(타임존 포함). null 이면 전 판정 not_established |
| `scope` | `{stages[], purposes[], model_types[], input_kind: audio|other}` — 필수 지표 범위의 정본 |
| `validity` | `{start_battery_max_c, wait_max_sec, sampler_min_n, sampler_max_gap_ratio}` |
| `rules[]` | `{metric, when{pair?, class?, stage?, subset?}, op: <=|>=|==|record, limit, noise_floor?, noise_source?, reason?}` |
| `abba_limits_pct` | `{metric_id: 허용 열화 %}` |

- `when` 키: `pair`(`S1-S2`·`S2-S3`·`S3-S4`·`S4-S5`·`base`·`regress`), `class`(`fp`·`lowp`), `stage`(`S1`~`S5`), `subset`(`overall`·`each`·이름)
- 생성: `init-thresholds` (thresholds.md §3)

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

### 2.3 abba[]

```json
{"abba_id": "mnn-patch-0042", "metrics": ["SPD.rtf_max", "SPD.lat_p99", "RES.rss_peak_mib"],
 "pairs": [{"a": "old-1", "b": "new-1"}, {"a": "old-2", "b": "new-2"}, {"a": "old-3", "b": "new-3"}]}
```

- a = 기준(옛 빌드·구성 A), b = 대상. 순서(AB·BA)는 `started_at` 에서 도출 — 둘 다 있어야 유효, 쌍 ≥ 3
- metrics 는 catalog 에 `abba_limit_pct` 가 있는 지표만(없으면 rc 2)
- **perf 지표와 sampler 지표는 블록을 나눔**: `SPD.*`·`RES.rss_peak_mib` 는 perf 회차 쌍, `RES.cpu_s_per_unit`·`RES.pss_mean_mib` 는 sampler 회차 쌍으로 별도 abba 블록. 한 블록에 섞으면 한쪽 회차에 값이 없어 not_established
- 같은 회차를 한 블록에서 두 번 쓰거나 started_at 이 같아 순서를 못 정하면 그 블록 invalid

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
