# port-metrics 리포트 — example-streaming-asr

## 0. 요약

- 종합 판정: **fail** (종료 코드 1)
- 태스크 지표: CER (%, lower)
- 범위: stages S1, S2, S3, S4, S5 / 목적 convert, regress, ship / 유형 streaming / 입력 audio
- 임계 동결: 2026-11-10T09:00:00+09:00
- 임계 파일: `-`
- thresholds sha256: `6b98e51d0a9c1b7a14d837ac5bcbbf564635d9c4d2f5e9b45216bb1b54b328c3`
- 유효성 한도: start_battery_max_c = 34, wait_max_sec = 600, sampler_min_n = 100, sampler_max_gap_ratio = 2
- 카탈로그 기본 규칙과 다른 규칙: 0 건

| 상태 | 건수 |
|---|---|
| pass | 74 |
| fail | 1 |
| invalid | 0 |
| not_established | 0 |
| record_only | 172 |

- fail 지표: `SPD.jitter`

## 1. 측정 신원

| 회차 | 단계 | 백엔드 | 종류 | pacing | 프로파일 | 실효(class) | 시작 | git_sha | 유효성 |
|---|---|---|---|---|---|---|---|---|---|
| s1_acc_cuda | S1 | cuda | accuracy | - | pt-fp32-t4 | fp32/fp32/none (fp) | 2026-11-11T10:00:00+09:00 | 9f3c2ab | ok |
| s1_golden_cpu | S1 | cpu | accuracy | - | pt-fp32-t4 | fp32/fp32/none (fp) | 2026-11-11T10:30:00+09:00 | 9f3c2ab | ok |
| s1_perf | S1 | cpu | perf | max | pt-fp32-t4 | fp32/fp32/none (fp) | 2026-11-11T11:00:00+09:00 | 9f3c2ab | ok |
| s2_acc | S2 | cpu | accuracy | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-11T13:00:00+09:00 | 9f3c2ab | ok |
| s2_perf | S2 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-11T13:30:00+09:00 | 9f3c2ab | ok |
| s3_acc | S3 | cpu | accuracy | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-11T14:00:00+09:00 | 9f3c2ab | ok |
| s3_perf | S3 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-11T14:30:00+09:00 | 9f3c2ab | ok |
| s3_sampler | S3 | cpu | sampler | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-11T15:00:00+09:00 | 9f3c2ab | ok |
| s4_acc | S4 | cpu | accuracy | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T09:00:00+09:00 | 9f3c2ab | ok |
| s4_acc_old | S4 | cpu | accuracy | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T09:30:00+09:00 | 41d7e05 | ok |
| s4_perf_a1 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T10:00:00+09:00 | 41d7e05 | ok |
| s4_perf_b1 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T10:20:00+09:00 | 9f3c2ab | ok |
| s4_perf_b2 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T10:40:00+09:00 | 9f3c2ab | ok |
| s4_perf_a2 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T11:00:00+09:00 | 41d7e05 | ok |
| s4_perf_a3 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T11:20:00+09:00 | 41d7e05 | ok |
| s4_perf_b3 | S4 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T11:40:00+09:00 | 9f3c2ab | ok |
| s4_rt | S4 | cpu | perf | realtime | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T13:00:00+09:00 | 9f3c2ab | ok |
| s4_sampler | S4 | cpu | sampler | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-12T14:00:00+09:00 | 9f3c2ab | ok |
| s5_acc | S5 | cpu | accuracy | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-13T09:00:00+09:00 | 9f3c2ab | ok |
| s5_perf | S5 | cpu | perf | max | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-13T10:00:00+09:00 | 9f3c2ab | ok |
| s5_rt | S5 | cpu | perf | realtime | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-13T11:00:00+09:00 | 9f3c2ab | ok |
| s5_sampler | S5 | cpu | sampler | - | fp16-high-normal-t4 | fp16/fp32/none (fp) | 2026-11-13T12:00:00+09:00 | 9f3c2ab | ok |

- 호출 경로 = `identity.call_path`(S3~S5) · 입력 집합 = `manifest_name` (`manifest_sha256` 앞 12자)

| 회차 | 호출 경로 | 입력 집합 |
|---|---|---|
| s1_acc_cuda | - | 88c7275ef3ef |
| s1_golden_cpu | - | 88c7275ef3ef |
| s1_perf | - | 88c7275ef3ef |
| s2_acc | - | 88c7275ef3ef |
| s2_perf | - | 88c7275ef3ef |
| s3_acc | (미기록) | 88c7275ef3ef |
| s3_perf | (미기록) | 88c7275ef3ef |
| s3_sampler | (미기록) | 88c7275ef3ef |
| s4_acc | (미기록) | 88c7275ef3ef |
| s4_acc_old | (미기록) | 88c7275ef3ef |
| s4_perf_a1 | (미기록) | 88c7275ef3ef |
| s4_perf_b1 | (미기록) | 88c7275ef3ef |
| s4_perf_b2 | (미기록) | 88c7275ef3ef |
| s4_perf_a2 | (미기록) | 88c7275ef3ef |
| s4_perf_a3 | (미기록) | 88c7275ef3ef |
| s4_perf_b3 | (미기록) | 88c7275ef3ef |
| s4_rt | (미기록) | 88c7275ef3ef |
| s4_sampler | (미기록) | 88c7275ef3ef |
| s5_acc | (미기록) | 88c7275ef3ef |
| s5_perf | (미기록) | 88c7275ef3ef |
| s5_rt | (미기록) | 88c7275ef3ef |
| s5_sampler | (미기록) | 88c7275ef3ef |

## 2. 단계 사슬 동등성

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `NUM.max_abs` | chain_s1_s2 | S1-S2 | encoder_out | 0.00032 | abs | pass |
| `NUM.max_abs` | chain_s1_s2 | S1-S2 | logits | 0.00051 | abs | pass |
| `NUM.rel_l2` | chain_s1_s2 | S1-S2 | encoder_out | 4e-05 | ratio | pass |
| `NUM.rel_l2` | chain_s1_s2 | S1-S2 | logits | 6.1e-05 | ratio | pass |
| `NUM.cos_min` | chain_s1_s2 | S1-S2 | encoder_out | 0.999999 | ratio | record_only |
| `NUM.cos_min` | chain_s1_s2 | S1-S2 | logits | 0.999998 | ratio | record_only |
| `DEC.match_rate` | chain_s1_s2 | S1-S2 | - | 0.995 | ratio | record_only |
| `DEC.flip` | chain_s1_s2 | S1-S2 | - | 2 | count | record_only |
| `NUM.max_abs` | chain_s2_s3 | S2-S3 | encoder_out | 0 | abs | pass |
| `NUM.max_abs` | chain_s2_s3 | S2-S3 | logits | 0 | abs | pass |
| `NUM.rel_l2` | chain_s2_s3 | S2-S3 | encoder_out | 0 | ratio | pass |
| `NUM.rel_l2` | chain_s2_s3 | S2-S3 | logits | 0 | ratio | pass |
| `NUM.cos_min` | chain_s2_s3 | S2-S3 | encoder_out | 1 | ratio | record_only |
| `NUM.cos_min` | chain_s2_s3 | S2-S3 | logits | 1 | ratio | record_only |
| `DEC.match_rate` | chain_s2_s3 | S2-S3 | - | 1 | ratio | pass |
| `NUM.max_abs` | chain_s3_s4 | S3-S4 | encoder_out | 0.00064 | abs | pass |
| `NUM.max_abs` | chain_s3_s4 | S3-S4 | logits | 0.0008 | abs | pass |
| `NUM.rel_l2` | chain_s3_s4 | S3-S4 | encoder_out | 0.0011 | ratio | record_only |
| `NUM.rel_l2` | chain_s3_s4 | S3-S4 | logits | 0.0029 | ratio | record_only |
| `NUM.cos_min` | chain_s3_s4 | S3-S4 | encoder_out | 0.99999 | ratio | record_only |
| `NUM.cos_min` | chain_s3_s4 | S3-S4 | logits | 0.99998 | ratio | record_only |
| `DEC.match_rate` | chain_s3_s4 | S3-S4 | - | 0.985 | ratio | record_only |
| `DEC.flip` | chain_s3_s4 | S3-S4 | - | 6 | count | record_only |
| `DEC.match_rate` | chain_s4_s5 | S4-S5 | - | 1 | ratio | pass |
| `DEC.match_rate` | base_s2 | base | - | 0.995 | ratio | record_only |
| `DEC.flip` | base_s2 | base | - | 2 | count | record_only |
| `DEC.severe_flip` | base_s2 | base | - | 0 | count | pass |
| `DEC.match_rate` | base_s3 | base | - | 0.995 | ratio | record_only |
| `DEC.flip` | base_s3 | base | - | 2 | count | record_only |
| `DEC.severe_flip` | base_s3 | base | - | 0 | count | pass |
| `DEC.match_rate` | base_s4 | base | - | 0.98 | ratio | record_only |
| `DEC.flip` | base_s4 | base | - | 8 | count | record_only |
| `DEC.severe_flip` | base_s4 | base | - | 0 | count | pass |
| `DEC.match_rate` | base_s5 | base | - | 0.98 | ratio | record_only |
| `DEC.flip` | base_s5 | base | - | 8 | count | record_only |
| `DEC.severe_flip` | base_s5 | base | - | 0 | count | pass |
| `DEC.match_rate` | regress_s4 | regress | - | 1 | ratio | pass |

## 3. 태스크 정확도

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `ACC.primary` | s1_acc_cuda | S1 | - | 5 | % | record_only |
| `ACC.primary` | s1_acc_cuda | S1 | clean | 3 | % | record_only |
| `ACC.primary` | s1_acc_cuda | S1 | noisy | 7 | % | record_only |
| `ACC.primary` | s2_acc | S2 | - | 5.05 | % | record_only |
| `ACC.primary` | s2_acc | S2 | clean | 3.02 | % | record_only |
| `ACC.primary` | s2_acc | S2 | noisy | 7.08 | % | record_only |
| `ACC.primary` | s3_acc | S3 | - | 5.05 | % | record_only |
| `ACC.primary` | s3_acc | S3 | clean | 3.02 | % | record_only |
| `ACC.primary` | s3_acc | S3 | noisy | 7.08 | % | record_only |
| `ACC.primary` | s4_acc | S4 | - | 5.2 | % | record_only |
| `ACC.primary` | s4_acc | S4 | clean | 3.1 | % | record_only |
| `ACC.primary` | s4_acc | S4 | noisy | 7.3 | % | record_only |
| `ACC.primary` | s5_acc | S5 | - | 5.2 | % | record_only |
| `ACC.primary` | s5_acc | S5 | clean | 3.1 | % | record_only |
| `ACC.primary` | s5_acc | S5 | noisy | 7.3 | % | record_only |
| `ACC.degradation` | s2_acc | S2 | - | 0.05 | % | pass |
| `ACC.degradation` | s2_acc | S2 | clean | 0.02 | % | pass |
| `ACC.degradation` | s2_acc | S2 | noisy | 0.08 | % | pass |
| `ACC.degradation` | s3_acc | S3 | - | 0.05 | % | pass |
| `ACC.degradation` | s3_acc | S3 | clean | 0.02 | % | pass |
| `ACC.degradation` | s3_acc | S3 | noisy | 0.08 | % | pass |
| `ACC.degradation` | s4_acc | S4 | - | 0.2 | % | pass |
| `ACC.degradation` | s4_acc | S4 | clean | 0.1 | % | pass |
| `ACC.degradation` | s4_acc | S4 | noisy | 0.3 | % | pass |
| `ACC.degradation` | s5_acc | S5 | - | 0.2 | % | pass |
| `ACC.degradation` | s5_acc | S5 | clean | 0.1 | % | pass |
| `ACC.degradation` | s5_acc | S5 | noisy | 0.3 | % | pass |

## 4. 속도

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `SPD.rtf_max` | s1_perf | S1 | - | 0.140244 | x | record_only |
| `SPD.lat_p50` | s1_perf | S1 | - | 22 | ms | record_only |
| `SPD.lat_p95` | s1_perf | S1 | - | 24 | ms | record_only |
| `SPD.lat_p99` | s1_perf | S1 | - | 24 | ms | record_only |
| `SPD.lat_max` | s1_perf | S1 | - | 24 | ms | record_only |
| `SPD.jitter` | s1_perf | S1 | - | 1.09091 | ratio | record_only |
| `SPD.step_p95_over_hop` | s1_perf | S1 | - | 0.15 | ratio | record_only |
| `SPD.deadline_miss` | s1_perf | S1 | - | 0 | count | record_only |
| `SPD.rtf_max` | s2_perf | S2 | - | 0.20122 | x | record_only |
| `SPD.lat_p50` | s2_perf | S2 | - | 32 | ms | record_only |
| `SPD.lat_p95` | s2_perf | S2 | - | 34 | ms | record_only |
| `SPD.lat_p99` | s2_perf | S2 | - | 34 | ms | record_only |
| `SPD.lat_max` | s2_perf | S2 | - | 34 | ms | record_only |
| `SPD.jitter` | s2_perf | S2 | - | 1.0625 | ratio | record_only |
| `SPD.step_p95_over_hop` | s2_perf | S2 | - | 0.2125 | ratio | record_only |
| `SPD.deadline_miss` | s2_perf | S2 | - | 0 | count | record_only |
| `SPD.load_ms` | s2_perf | S2 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s3_perf | S3 | - | 0.20122 | x | record_only |
| `SPD.lat_p50` | s3_perf | S3 | - | 32 | ms | record_only |
| `SPD.lat_p95` | s3_perf | S3 | - | 34 | ms | record_only |
| `SPD.lat_p99` | s3_perf | S3 | - | 34 | ms | record_only |
| `SPD.lat_max` | s3_perf | S3 | - | 34 | ms | record_only |
| `SPD.jitter` | s3_perf | S3 | - | 1.0625 | ratio | record_only |
| `SPD.step_p95_over_hop` | s3_perf | S3 | - | 0.2125 | ratio | record_only |
| `SPD.deadline_miss` | s3_perf | S3 | - | 0 | count | record_only |
| `SPD.load_ms` | s3_perf | S3 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_a1 | S4 | - | 0.25 | x | pass |
| `SPD.lat_p50` | s4_perf_a1 | S4 | - | 40 | ms | record_only |
| `SPD.lat_p95` | s4_perf_a1 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p99` | s4_perf_a1 | S4 | - | 42 | ms | record_only |
| `SPD.lat_max` | s4_perf_a1 | S4 | - | 42 | ms | record_only |
| `SPD.jitter` | s4_perf_a1 | S4 | - | 1.05 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_a1 | S4 | - | 0.2625 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_a1 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_a1 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_b1 | S4 | - | 0.262195 | x | pass |
| `SPD.lat_p50` | s4_perf_b1 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p95` | s4_perf_b1 | S4 | - | 44 | ms | record_only |
| `SPD.lat_p99` | s4_perf_b1 | S4 | - | 44 | ms | record_only |
| `SPD.lat_max` | s4_perf_b1 | S4 | - | 44 | ms | record_only |
| `SPD.jitter` | s4_perf_b1 | S4 | - | 1.04762 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_b1 | S4 | - | 0.275 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_b1 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_b1 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_b2 | S4 | - | 0.262195 | x | pass |
| `SPD.lat_p50` | s4_perf_b2 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p95` | s4_perf_b2 | S4 | - | 44 | ms | record_only |
| `SPD.lat_p99` | s4_perf_b2 | S4 | - | 44 | ms | record_only |
| `SPD.lat_max` | s4_perf_b2 | S4 | - | 44 | ms | record_only |
| `SPD.jitter` | s4_perf_b2 | S4 | - | 1.04762 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_b2 | S4 | - | 0.275 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_b2 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_b2 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_a2 | S4 | - | 0.25 | x | pass |
| `SPD.lat_p50` | s4_perf_a2 | S4 | - | 40 | ms | record_only |
| `SPD.lat_p95` | s4_perf_a2 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p99` | s4_perf_a2 | S4 | - | 42 | ms | record_only |
| `SPD.lat_max` | s4_perf_a2 | S4 | - | 42 | ms | record_only |
| `SPD.jitter` | s4_perf_a2 | S4 | - | 1.05 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_a2 | S4 | - | 0.2625 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_a2 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_a2 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_a3 | S4 | - | 0.25 | x | pass |
| `SPD.lat_p50` | s4_perf_a3 | S4 | - | 40 | ms | record_only |
| `SPD.lat_p95` | s4_perf_a3 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p99` | s4_perf_a3 | S4 | - | 42 | ms | record_only |
| `SPD.lat_max` | s4_perf_a3 | S4 | - | 42 | ms | record_only |
| `SPD.jitter` | s4_perf_a3 | S4 | - | 1.05 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_a3 | S4 | - | 0.2625 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_a3 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_a3 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s4_perf_b3 | S4 | - | 0.262195 | x | pass |
| `SPD.lat_p50` | s4_perf_b3 | S4 | - | 42 | ms | record_only |
| `SPD.lat_p95` | s4_perf_b3 | S4 | - | 44 | ms | record_only |
| `SPD.lat_p99` | s4_perf_b3 | S4 | - | 44 | ms | record_only |
| `SPD.lat_max` | s4_perf_b3 | S4 | - | 44 | ms | record_only |
| `SPD.jitter` | s4_perf_b3 | S4 | - | 1.04762 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_perf_b3 | S4 | - | 0.275 | ratio | pass |
| `SPD.deadline_miss` | s4_perf_b3 | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_perf_b3 | S4 | - | 850 | ms | record_only |
| `SPD.rtf_rt` | s4_rt | S4 | - | 0.953125 | x | record_only |
| `SPD.lat_p50` | s4_rt | S4 | - | 152 | ms | record_only |
| `SPD.lat_p95` | s4_rt | S4 | - | 155 | ms | record_only |
| `SPD.lat_p99` | s4_rt | S4 | - | 155 | ms | record_only |
| `SPD.lat_max` | s4_rt | S4 | - | 155 | ms | record_only |
| `SPD.jitter` | s4_rt | S4 | - | 1.01974 | ratio | pass |
| `SPD.step_p95_over_hop` | s4_rt | S4 | - | 0.96875 | ratio | pass |
| `SPD.tail_over_hop` | s4_rt | S4 | - | 0.625 | ratio | pass |
| `SPD.deadline_miss` | s4_rt | S4 | - | 0 | count | pass |
| `SPD.load_ms` | s4_rt | S4 | - | 850 | ms | record_only |
| `SPD.rtf_max` | s5_perf | S5 | - | 0.315549 | x | pass |
| `SPD.lat_p50` | s5_perf | S5 | - | 42 | ms | record_only |
| `SPD.lat_p95` | s5_perf | S5 | - | 130 | ms | record_only |
| `SPD.lat_p99` | s5_perf | S5 | - | 130 | ms | record_only |
| `SPD.lat_max` | s5_perf | S5 | - | 130 | ms | record_only |
| `SPD.jitter` | s5_perf | S5 | - | 3.09524 | ratio | fail |
| `SPD.step_p95_over_hop` | s5_perf | S5 | - | 0.8125 | ratio | pass |
| `SPD.deadline_miss` | s5_perf | S5 | - | 0 | count | pass |
| `SPD.load_ms` | s5_perf | S5 | - | 850 | ms | record_only |
| `SPD.rtf_rt` | s5_rt | S5 | - | 0.953125 | x | record_only |
| `SPD.lat_p50` | s5_rt | S5 | - | 152 | ms | record_only |
| `SPD.lat_p95` | s5_rt | S5 | - | 155 | ms | record_only |
| `SPD.lat_p99` | s5_rt | S5 | - | 155 | ms | record_only |
| `SPD.lat_max` | s5_rt | S5 | - | 155 | ms | record_only |
| `SPD.jitter` | s5_rt | S5 | - | 1.01974 | ratio | pass |
| `SPD.step_p95_over_hop` | s5_rt | S5 | - | 0.96875 | ratio | pass |
| `SPD.tail_over_hop` | s5_rt | S5 | - | 0.625 | ratio | pass |
| `SPD.deadline_miss` | s5_rt | S5 | - | 0 | count | pass |
| `SPD.load_ms` | s5_rt | S5 | - | 850 | ms | record_only |

## 5. 자원

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `RES.rss_peak_mib` | s1_perf | S1 | - | 1500 | MiB | record_only |
| `RES.bundle_mib` | s2_acc | S2 | - | 120 | MiB | record_only |
| `RES.rss_peak_mib` | s2_perf | S2 | - | 256 | MiB | record_only |
| `RES.rss_peak_mib` | s3_perf | S3 | - | 252 | MiB | record_only |
| `RES.cpu_pct_mean` | s3_sampler | S3 | - | 250 | % | record_only |
| `RES.cpu_pct_max` | s3_sampler | S3 | - | 250 | % | record_only |
| `RES.cpu_s_per_unit` | s3_sampler | S3 | - | 2.5 | s/unit | record_only |
| `RES.pss_mean_mib` | s3_sampler | S3 | - | 146.924 | MiB | record_only |
| `RES.pss_p95_mib` | s3_sampler | S3 | - | 147.363 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_a1 | S4 | - | 200 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_b1 | S4 | - | 202 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_b2 | S4 | - | 202 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_a2 | S4 | - | 200 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_a3 | S4 | - | 200 | MiB | record_only |
| `RES.rss_peak_mib` | s4_perf_b3 | S4 | - | 202 | MiB | record_only |
| `RES.rss_peak_mib` | s4_rt | S4 | - | 202 | MiB | record_only |
| `RES.cpu_pct_mean` | s4_sampler | S4 | - | 250 | % | record_only |
| `RES.cpu_pct_max` | s4_sampler | S4 | - | 250 | % | record_only |
| `RES.cpu_s_per_unit` | s4_sampler | S4 | - | 2.5 | s/unit | record_only |
| `RES.pss_mean_mib` | s4_sampler | S4 | - | 146.924 | MiB | record_only |
| `RES.pss_p95_mib` | s4_sampler | S4 | - | 147.363 | MiB | record_only |
| `RES.rss_peak_mib` | s5_perf | S5 | - | 302 | MiB | record_only |
| `RES.rss_peak_mib` | s5_rt | S5 | - | 302 | MiB | record_only |
| `RES.cpu_pct_mean` | s5_sampler | S5 | - | 250 | % | record_only |
| `RES.cpu_pct_max` | s5_sampler | S5 | - | 250 | % | record_only |
| `RES.cpu_s_per_unit` | s5_sampler | S5 | - | 2.5 | s/unit | record_only |
| `RES.pss_mean_mib` | s5_sampler | S5 | - | 146.924 | MiB | record_only |
| `RES.pss_p95_mib` | s5_sampler | S5 | - | 147.363 | MiB | record_only |

## 6. A/B(같은 세션 ABBA)

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `SPD.rtf_max` | abba_s4_patch | S4 | - | 4.87805 | % | pass |
| `SPD.lat_p99` | abba_s4_patch | S4 | - | 4.7619 | % | pass |
| `RES.rss_peak_mib` | abba_s4_patch | S4 | - | 1 | % | pass |

## 7. 측정 조건

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 |
|---|---|---|---|---|---|---|
| `MQ.excluded_rows` | s1_perf | S1 | - | 3 | count | record_only |
| `CNV.audit_ok` | s2_acc | S2 | - | true | bool | pass |
| `MQ.excluded_rows` | s2_perf | S2 | - | 3 | count | record_only |
| `MQ.excluded_rows` | s3_perf | S3 | - | 3 | count | record_only |
| `MQ.sampler_n` | s3_sampler | S3 | - | 120 | count | record_only |
| `MQ.sampler_gap_ratio` | s3_sampler | S3 | - | 1 | ratio | record_only |
| `STB.deterministic` | s4_acc | S4 | - | true | bool | pass |
| `MQ.excluded_rows` | s4_perf_a1 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_a1 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_a1 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_perf_b1 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_b1 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_b1 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_perf_b2 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_b2 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_b2 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_perf_a2 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_a2 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_a2 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_perf_a3 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_a3 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_a3 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_perf_b3 | S4 | - | 3 | count | record_only |
| `THM.start_battery_c` | s4_perf_b3 | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_perf_b3 | S4 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s4_rt | S4 | - | 1 | count | record_only |
| `STB.soak_p99_ratio` | s4_rt | S4 | - | 1.00649 | ratio | pass |
| `THM.drift` | s4_rt | S4 | - | 0.00657895 | ratio | pass |
| `THM.start_battery_c` | s4_rt | S4 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s4_rt | S4 | - | 0 | count | record_only |
| `MQ.sampler_n` | s4_sampler | S4 | - | 120 | count | record_only |
| `MQ.sampler_gap_ratio` | s4_sampler | S4 | - | 1 | ratio | record_only |
| `STB.deterministic` | s5_acc | S5 | - | true | bool | pass |
| `MQ.excluded_rows` | s5_perf | S5 | - | 3 | count | record_only |
| `THM.start_battery_c` | s5_perf | S5 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s5_perf | S5 | - | 0 | count | record_only |
| `MQ.excluded_rows` | s5_rt | S5 | - | 1 | count | record_only |
| `STB.soak_p99_ratio` | s5_rt | S5 | - | 1.00649 | ratio | pass |
| `THM.drift` | s5_rt | S5 | - | 0.00657895 | ratio | pass |
| `THM.start_battery_c` | s5_rt | S5 | - | 33.2 | degC | record_only |
| `THM.pause_events` | s5_rt | S5 | - | 0 | count | record_only |
| `MQ.sampler_n` | s5_sampler | S5 | - | 120 | count | record_only |
| `MQ.sampler_gap_ratio` | s5_sampler | S5 | - | 1 | ratio | record_only |

- S4↔S5 성능 차 = JNI + 프로세스 상태 합산 효과(JNI 오버헤드로 해석하지 않음)

| 회차 | 단계 | cpus_allowed | cpuset | proc_state | core_distribution |
|---|---|---|---|---|---|
| s4_acc | S4 | 0-7 | - | - | - |
| s4_acc_old | S4 | 0-7 | - | - | - |
| s4_perf_a1 | S4 | 0-7 | - | - | - |
| s4_perf_b1 | S4 | 0-7 | - | - | - |
| s4_perf_b2 | S4 | 0-7 | - | - | - |
| s4_perf_a2 | S4 | 0-7 | - | - | - |
| s4_perf_a3 | S4 | 0-7 | - | - | - |
| s4_perf_b3 | S4 | 0-7 | - | - | - |
| s4_rt | S4 | 0-7 | - | - | - |
| s4_sampler | S4 | 0-7 | - | - | - |
| s5_acc | S5 | 0-7 | top-app | TOP | {"cpu4-6": 0.72, "cpu7": 0.28} |
| s5_perf | S5 | 0-7 | top-app | TOP | {"cpu4-6": 0.72, "cpu7": 0.28} |
| s5_rt | S5 | 0-7 | top-app | TOP | {"cpu4-6": 0.72, "cpu7": 0.28} |
| s5_sampler | S5 | 0-7 | top-app | TOP | {"cpu4-6": 0.72, "cpu7": 0.28} |

| 회차 | 시작 배터리 degC | 클럭 복구 | 대기 s | 정지 횟수 | 출처 |
|---|---|---|---|---|---|
| s4_perf_a1 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_perf_b1 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_perf_b2 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_perf_a2 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_perf_a3 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_perf_b3 | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_rt | 33.2 | true | 120 | 0 | thermalservice HAL |
| s4_sampler | 33.2 | true | 120 | 0 | thermalservice HAL |
| s5_perf | 33.2 | true | 120 | 0 | thermalservice HAL |
| s5_rt | 33.2 | true | 120 | 0 | thermalservice HAL |
| s5_sampler | 33.2 | true | 120 | 0 | thermalservice HAL |

## 8. 판정 상세

| 지표 | 대상 | 문맥 | 서브셋·텐서 | 값 | 단위 | 상태 | 근거 |
|---|---|---|---|---|---|---|---|
| `SPD.jitter` | s5_perf | S5 | - | 3.09524 | ratio | fail | <= 2 |
| `CNV.audit_ok` | s2_acc | S2 | - | true | bool | pass | == true |
| `STB.deterministic` | s4_acc | S4 | - | true | bool | pass | == true |
| `SPD.rtf_max` | s4_perf_a1 | S4 | - | 0.25 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_a1 | S4 | - | 1.05 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_a1 | S4 | - | 0.2625 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_a1 | S4 | - | 0 | count | pass | == 0 |
| `SPD.rtf_max` | s4_perf_b1 | S4 | - | 0.262195 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_b1 | S4 | - | 1.04762 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_b1 | S4 | - | 0.275 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_b1 | S4 | - | 0 | count | pass | == 0 |
| `SPD.rtf_max` | s4_perf_b2 | S4 | - | 0.262195 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_b2 | S4 | - | 1.04762 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_b2 | S4 | - | 0.275 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_b2 | S4 | - | 0 | count | pass | == 0 |
| `SPD.rtf_max` | s4_perf_a2 | S4 | - | 0.25 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_a2 | S4 | - | 1.05 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_a2 | S4 | - | 0.2625 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_a2 | S4 | - | 0 | count | pass | == 0 |
| `SPD.rtf_max` | s4_perf_a3 | S4 | - | 0.25 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_a3 | S4 | - | 1.05 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_a3 | S4 | - | 0.2625 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_a3 | S4 | - | 0 | count | pass | == 0 |
| `SPD.rtf_max` | s4_perf_b3 | S4 | - | 0.262195 | x | pass | <= 0.5 |
| `SPD.jitter` | s4_perf_b3 | S4 | - | 1.04762 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_perf_b3 | S4 | - | 0.275 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_perf_b3 | S4 | - | 0 | count | pass | == 0 |
| `SPD.jitter` | s4_rt | S4 | - | 1.01974 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s4_rt | S4 | - | 0.96875 | ratio | pass | <= 1 |
| `SPD.tail_over_hop` | s4_rt | S4 | - | 0.625 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s4_rt | S4 | - | 0 | count | pass | == 0 |
| `STB.soak_p99_ratio` | s4_rt | S4 | - | 1.00649 | ratio | pass | <= 1.2 |
| `THM.drift` | s4_rt | S4 | - | 0.00657895 | ratio | pass | <= 0.15 |
| `STB.deterministic` | s5_acc | S5 | - | true | bool | pass | == true |
| `SPD.rtf_max` | s5_perf | S5 | - | 0.315549 | x | pass | <= 0.5 |
| `SPD.step_p95_over_hop` | s5_perf | S5 | - | 0.8125 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s5_perf | S5 | - | 0 | count | pass | == 0 |
| `SPD.jitter` | s5_rt | S5 | - | 1.01974 | ratio | pass | <= 2 |
| `SPD.step_p95_over_hop` | s5_rt | S5 | - | 0.96875 | ratio | pass | <= 1 |
| `SPD.tail_over_hop` | s5_rt | S5 | - | 0.625 | ratio | pass | <= 1 |
| `SPD.deadline_miss` | s5_rt | S5 | - | 0 | count | pass | == 0 |
| `STB.soak_p99_ratio` | s5_rt | S5 | - | 1.00649 | ratio | pass | <= 1.2 |
| `THM.drift` | s5_rt | S5 | - | 0.00657895 | ratio | pass | <= 0.15 |
| `ACC.degradation` | s2_acc | S2 | - | 0.05 | % | pass | <= 0.3 |
| `ACC.degradation` | s2_acc | S2 | clean | 0.02 | % | pass | <= 0.5 |
| `ACC.degradation` | s2_acc | S2 | noisy | 0.08 | % | pass | <= 0.5 |
| `ACC.degradation` | s3_acc | S3 | - | 0.05 | % | pass | <= 0.3 |
| `ACC.degradation` | s3_acc | S3 | clean | 0.02 | % | pass | <= 0.5 |
| `ACC.degradation` | s3_acc | S3 | noisy | 0.08 | % | pass | <= 0.5 |
| `ACC.degradation` | s4_acc | S4 | - | 0.2 | % | pass | <= 0.3 |
| `ACC.degradation` | s4_acc | S4 | clean | 0.1 | % | pass | <= 0.5 |
| `ACC.degradation` | s4_acc | S4 | noisy | 0.3 | % | pass | <= 0.5 |
| `ACC.degradation` | s5_acc | S5 | - | 0.2 | % | pass | <= 0.3 |
| `ACC.degradation` | s5_acc | S5 | clean | 0.1 | % | pass | <= 0.5 |
| `ACC.degradation` | s5_acc | S5 | noisy | 0.3 | % | pass | <= 0.5 |
| `NUM.max_abs` | chain_s1_s2 | S1-S2 | encoder_out | 0.00032 | abs | pass | <= 0.001 |
| `NUM.max_abs` | chain_s1_s2 | S1-S2 | logits | 0.00051 | abs | pass | <= 0.001 |
| `NUM.rel_l2` | chain_s1_s2 | S1-S2 | encoder_out | 4e-05 | ratio | pass | <= 0.0001 |
| `NUM.rel_l2` | chain_s1_s2 | S1-S2 | logits | 6.1e-05 | ratio | pass | <= 0.0001 |
| `NUM.max_abs` | chain_s2_s3 | S2-S3 | encoder_out | 0 | abs | pass | <= 0.001 |
| `NUM.max_abs` | chain_s2_s3 | S2-S3 | logits | 0 | abs | pass | <= 0.001 |
| `NUM.rel_l2` | chain_s2_s3 | S2-S3 | encoder_out | 0 | ratio | pass | <= 0.0001 |
| `NUM.rel_l2` | chain_s2_s3 | S2-S3 | logits | 0 | ratio | pass | <= 0.0001 |
| `DEC.match_rate` | chain_s2_s3 | S2-S3 | - | 1 | ratio | pass | >= 1 |
| `NUM.max_abs` | chain_s3_s4 | S3-S4 | encoder_out | 0.00064 | abs | pass | <= 0.001 |
| `NUM.max_abs` | chain_s3_s4 | S3-S4 | logits | 0.0008 | abs | pass | <= 0.001 |
| `DEC.match_rate` | chain_s4_s5 | S4-S5 | - | 1 | ratio | pass | >= 1 |
| `DEC.severe_flip` | base_s2 | base | - | 0 | count | pass | <= 0 |
| `DEC.severe_flip` | base_s3 | base | - | 0 | count | pass | <= 0 |
| `DEC.severe_flip` | base_s4 | base | - | 0 | count | pass | <= 0 |
| `DEC.severe_flip` | base_s5 | base | - | 0 | count | pass | <= 0 |
| `DEC.match_rate` | regress_s4 | regress | - | 1 | ratio | pass | >= 1 |
| `SPD.rtf_max` | abba_s4_patch | S4 | - | 4.87805 | % | pass | 쌍별 열화 % 중앙값 <= 5 |
| `SPD.lat_p99` | abba_s4_patch | S4 | - | 4.7619 | % | pass | 쌍별 열화 % 중앙값 <= 5 |
| `RES.rss_peak_mib` | abba_s4_patch | S4 | - | 1 | % | pass | 쌍별 열화 % 중앙값 <= 2 |

## 9. 누락 지표

- 없음
