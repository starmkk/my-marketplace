# 측정 통제 — 신원·열·회차 분리·단위 규칙

- 목적: "같은 것을 같은 조건에서 같은 정의로 쟀는가"를 측정 전에 고정해 재측정을 막음
- 위반 시 처리: 그 회차(또는 그 지표)는 `invalid` — 값은 리포트에 남기되 판정 근거로 쓰지 않음

---

## 1. 측정 신원(`identity`) 필수 키

| 단계 | 필수 키(누적) | 이유 |
|---|---|---|
| 전 단계 | `git_sha`·`git_dirty`·`manifest_sha256`·`threads_effective`·`thresholds_sha256` | 입력 집합·코드 판본·실효 스레드가 다르면 비교 불성립, 동결 임계 판본 결속 |
| S1 | `torch_version`·`device_name`·`tf32`·`checkpoint_sha256`·`attn_impl` | TF32 기본 on·eager/sdpa 차가 골든을 바꿈 |
| S2 | `mnn_commit`·`bundle_files_sha256`·`converter_args` | raw `.mnn` sha 는 헤더 uuid 로 매번 달라 앵커 금지 → 번들 파일별 sha 맵 사용 |
| S3 | S2 + `binary_sha256`·`mnn_patches_sha256` | MNN 패치 유무·빌드 판본 |
| S4 | S3 + `device_model`·`soc`·`android`·`cpus_allowed` | 단말·코어 집합 |
| S5 | S4 + `apk_sha256`·`so_sha256`·`cpuset`·`proc_state`·`core_distribution` | 앱 프로세스 상태가 코어 집합을 바꿈(D6) |

- 회차 시작 시각 `started_at`(ISO 8601, 타임존 포함)은 run 최상위 키. 동결 시각(`frozen_at`) 이전 회차는 invalid
- `thresholds_sha256` 은 하네스가 측정 시점에 동결 파일 sha256 을 읽어 기록(측정 후 조립 금지). 불일치 = invalid
- `git_dirty = true` 회차는 invalid(측정 중 추적 파일 수정 금지). 측정용 빌드는 커밋 직후 clean 트리에서 만듦
- **요청값으로 실측 필드를 채우지 않음**: `threads_effective`·`effective` 는 엔진이 실제 적용한 값을 읽음
- 단말 push 바이너리는 host sha 와 단말 `sha256sum` 을 대조하고 그 값을 `binary_sha256` 에 기록
- 변환 인자는 기본값에 기대지 않고 명시(`--weightQuantAsymmetric=1`, `--useGeluApproximation 0` 등)
- 권장 키(선택 — 누락이어도 invalid 아님): `call_path`(S3~S5 호출 경로, 형식 `cli:<바이너리>` · `app:<클래스>→<so>`)·`manifest_name`(사람이 읽는 입력 집합 이름). 리포트 §1 보조 표에 표시하며 S3~S5 의 `call_path` 미기록은 `(미기록)`(필수 키 누락 `(누락)` 과 구분)

## 2. 단말 열 통제(S4·S5, 결정 D5)

- **회차 시작 조건**: 배터리 온도 ≤ 34.0 °C ∧ CPU 상한 클럭 복구(`scaling_max_freq == cpuinfo_max_freq`, 전 policy)
  - 온도는 HAL 실시간 값(`dumpsys thermalservice` 의 실시간 절, `Cached temperatures` 금지 — ZF G-OH 1 차 무효 원인)
  - 대기: 60 s 간격 폴링, 상한 600 s. 초과 = 그 회차 invalid(`thermal.wait_sec` 기록)
- **회차 중 감시**: 배터리 45 °C 초과 시 프로세스 SIGSTOP, 38 °C 이하 SIGCONT, 정지 상한 1800 s
  - 정지 구간에 걸친 timing 행은 `paused = true` → RTF·분위수 집계에서 제외, `thermal.pause_events` 기록
  - CPU 존 온도(65 °C 등)로 감시하면 재개 7~8 s 만에 재정지(실행 비율 약 5 %)해 무의미 — 배터리 센서 사용(SL)
- **기록**: `thermal.{start_battery_c, clock_restored, wait_sec, pause_events, source}`, 성능 회차의 cpufreq 분포(가능하면)
- **짧은 입력으로 장시간 성능을 외삽하지 않음**: 60 s smoke RTF 0.464 ↔ 30 분 0.82~0.84(NM F711N). 장시간 판단은 `ship` soak 회차로

## 3. A/B 비교 — 같은 세션 ABBA

- 회귀(`regress`: MNN 패치·C++ 수정 전후)·최적화(`optimize`: 구성 A vs B) 의 성능 판정은 **같은 세션 ABBA 3 쌍 이상**만 근거로 씀
  - 순서: A B B A A B … (AB·BA 둘 다 포함), 각 회차 시작 전 §2 시작 조건 충족
  - 허용폭은 측정 전에 thresholds.json 에 동결(기본 지연·RTF +5 %, CPU·메모리 +2 %)
  - 판정 = 쌍별 Δ% = (B − A) ÷ A × 100 의 중앙값
- 다른 날·다른 세션의 단일 수치끼리 비교해 회귀를 판정하지 않음(ZF v4 회귀 1 차 FAIL 은 시작 온도 38.4 ↔ 34.3 °C 차)
- 1 % 미만 차를 시간으로 가르려 하지 않음 — simpleperf 명령어 수 등 결정적 지표로 경로 동등성 확인
- **A ↔ A 잡음 블록**: 같은 빌드를 a·b 양쪽에 놓은 블록을 같은 세션에 함께 재고 `noise_for` 로 대상 블록에 묶음 — 양방향 판정, 미통과면 대상 pass 는
  `not_established`(thresholds.md §7)
- **연속 세션**: 한 판정에 쓰는 ABBA 블록(대상 + 잡음)의 단말 회차는 같은 부팅(`boot_id` 동일)에서 블록 구간이 겹치지 않게 연속으로 재고, 블록 사이에
  블록 밖 단말 측정을 끼우지 않음. `boot_id`·종료 시각은 하네스가 원자료에 기록(생성기는 검사하지 않음 — 조립기 몫)
- **시작 온도 대역**: ABBA 는 상한뿐 아니라 하한도 고정(`validity.abba_start_battery_min_c`) — 블록 안 회차의 열 궤적을 맞춤
- 블록 안 모든 회차의 `threads_effective`·`manifest_sha256`·`pacing` 동일(생성기가 검사, 위반 = 블록 invalid)

## 4. 회차 분리 — perf 회차와 sampler 회차

| 회차 | 얻는 지표 | 금지 |
|---|---|---|
| `perf` | RTF·지연 분위수·처리량·peak RSS(프로세스 수명 VmHWM)·로드 시간 | 주기적 `adb shell` 샘플러 병행 |
| `sampler` | CPU %·CPU-s/작업량·RSS/PSS 평균·분위수·클럭 | 이 회차의 RTF·지연을 SoT 로 사용 |
| `accuracy` | 출력·정확도(ACC·DEC) | — |

- 샘플러(3 s 마다 adb 1 회, smaps_rollup 읽기)는 측정 대상 성능을 간섭함 → 분리(SL·GR)
- 같은 구성의 perf·sampler 회차는 같은 `nonce` 로 결속. nonce 짝이 없는 sampler 회차는 invalid
- smaps_rollup 은 상주 페이지 수에 비례해 비쌈(ZF: 표본당 9.7~22.4 ms) → PSS 표본 주기를 RSS 와 따로 길게(10 s 등)
- 샘플러 품질: 표본 ≥ 100, 최대 간격 ≤ 2 × 명목 주기, 위반 = 그 회차 sampler 지표 invalid

## 5. 단위·집계 규칙(생성기 고정)

| 항목 | 규칙 | 이유 |
|---|---|---|
| 메모리 | **MiB**(= 2^20 B). 원자료는 kB(`/proc` 값 그대로) 로 받고 ÷ 1024 | MB(10^6)·MiB 혼용 재측정(ZF PSS /1024 폐기, GR 정정) |
| 파일 크기 | bytes 원값 + MiB 표시 | 같은 이유 |
| 분위수 | **nearest-rank**, k = ceil(q·n), 보간 없음 | 실제 표본 값만 보고, 언어 간 동일 결과 |
| RTF | Σwall ÷ Σaudio(비율의 평균 아님), pacing 별로 이름 분리(`rtf_max`·`rtf_rt`) | RTF 4 종 혼동(NM) |
| 처리량(비오디오) | Σunits ÷ Σwall_sec, 단위 정의를 project 에 명시 | 텍스트 입력은 RTF 분모가 없음(GR) |
| CPU % | 1 코어 = 100 %, 스레드 그룹 합, Δticks ÷ CLK_TCK ÷ Δt | 코어당 % 는 온라인 코어 수(hotplug)에 좌우(GR F711N) |
| CPU 효율 | CPU-s ÷ 작업량(오디오 초·1k 토큰) | thread 상한(≈ 400 %)에 붙는 CPU % 는 구성 비교 불가(SL) |
| 지연 집계 대상 | `kind = steady` 만(warmup·flush 제외), flush 는 RTF 에만 포함 | flush chunk 가 지터를 3.94 로 오측(ZF) |
| 시계 | 단말 시간은 단말 `/proc/uptime`·monotonic, 호스트와 섞지 않음 | adb 지연·시계 차 |

## 6. 모집단 규칙

- 판정은 **전수 또는 사전에 고정한 표본 집합**으로만. smoke 는 실행 확인용(GR: smoke 최대치가 전수 꼬리의 1/70)
- 입력 manifest sha 가 비교 회차끼리 같아야 함. 누락·잘린 파일이 있으면 그 회차 invalid
- 고민감 구간(판정 경계 근처) 이 표본에 포함되는지 확인 — 분류 모델은 임계 근접 여유(`|p − thr|` 최소) 를 함께 기록

## 7. S5(앱) 측정 상태(결정 D6)

- 성능은 **출하 프로세스 상태 그대로**(앱이 실제로 도는 top-app·foreground) 측정
- `identity.cpuset`·`proc_state`·`core_distribution`(스레드별 실행 코어 분포) 필수 — 같은 단말에서도 상태에 따라 사용 가능 코어가 다름(F711N foreground = 0-6)
- S4 CLI ↔ S5 앱의 성능 차는 **JNI + 프로세스 상태 합산 효과**로만 기록. "JNI 오버헤드"로 해석하지 않음
- S5 의 RSS 에는 ART 런타임(약 96~100 MiB)이 포함됨 → S4 값과 직접 빼서 비교하지 않음
- 출력 동등성(S4-S5 `DEC.match_rate = 1.0`)은 같은 단말·입력·구성에서 판정 — 결과가 같으면 S4 정확도 근거를 S5 에 승계

## 8. 재측정 — 사유 도출과 대체 회차

- **재측정 사유는 원자료에서 도출**: 하네스가 신고한 사유를 믿지 않고, 조립기가 시작 기록(온도·클럭·대기)·열 정지 기록·종료 코드·표본 품질에서
  닫힌 사유 코드 목록(프로젝트가 측정 전에 정함)으로 기계적으로 도출함. 도출 코드가 없는 회차의 재측정 = 결과를 보고 고르는 것이므로 금지
- 재측정 횟수 상한·ID 규칙(예: 원 ID + `-re<n>`)·ABBA 는 쌍 단위 재측정(쌍의 한 회차가 무효면 쌍 전체를 같은 순서로 다시)을 측정 전에 고정
- **대체된 회차는 지우지 않고 results 에 남김**: `superseded_by` = 재측정 회차, `superseded_reason` = 도출한 사유. 생성기는 그 회차를 판정에서 빼고
  리포트 §1 에 표시함("invalid 회차도 리포트에 남김" 과 양립 — 형식은 results-format.md §2.1)
  - 문제없는(invalid 사유가 없는) 회차를 대체하면 리포트에 `신원·열 검사 통과 회차 대체(원자료 품질 미검사)` 가 찍힘 → 사유의 원자료 근거를 보고서에 따로 실음
  - 측정 대상 자체의 실패(종료 코드 ≠ 0·출력 누락)는 재측정 사유가 아님 — 그대로 실패로 보고
- 대체된 perf 와 nonce 로 묶인 sampler 는 invalid → 재측정 perf 와 같은 nonce 로 다시 잼

## 9. 실시간 투입 lag 의 기준 시각(streaming)

- 실시간(`pacing: realtime`) 회차의 마감·lag(`deadline_miss`·`SPD.tail_over_hop` 의 `wall_total_sec`)은 **오디오 위치 0 을 t0** 로 계산
  - k 번째 hop 의 투입 가능 시각 = t0 + k × hop 길이 → 첫 hop = t0 + hop 길이(그 hop 의 오디오가 다 들어온 시각)
  - **첫 hop 투입 시각을 t0 로 쓰면 모든 마감이 hop 길이만큼 늦춰져 완화됨** — 원자료에 t0 원천(오디오 위치 0 의 시계 값)을 따로 기록
- 조립기 확인: steady 행의 투입 시각(반환 시각 − `wall_ms`) ≥ t0 + 그 hop 끝까지의 누적 오디오 길이(허용 오차 1 ms). 어긋나면 t0 원천이 잘못된 것
- `deadline_miss` 는 어댑터가 원자료 시각으로 다시 계산한 값과 대조(하네스가 적은 값을 그대로 옮기지 않음)

## 10. 하네스의 측정 대상 종료 규칙

- **하네스는 측정 대상 프로세스에 종료 신호를 보내지 않음**: 시작한 회차는 끝까지 실행(열 정지 상한을 넘겨도 SIGCONT 뒤 완주). 하네스가 죽인 회차와
  측정 대상이 스스로 죽은 회차를 원자료로 구분할 수 없게 되기 때문
  - 시작 조건(온도·클럭)은 측정 대상을 띄우기 **전에** 판정 — 불충족이면 시작하지 않음(회차가 아님)
- **단말 측정 대상은 adb 세션과 분리 실행**(`nohup`·`setsid` 등): adb 연결이 끊겨도 측정 대상이 SIGHUP 으로 죽지 않게 하고, 하네스는 폴링으로 종료를 확인
- **종료 코드 회수**: 측정 대상의 종료 코드를 단말 파일로 남겨 회차마다 회수·기록. 회수하지 못한 회차는 "성공"이 아니라 사유 코드 대상(재측정) 또는 실패
- 회차 종료 시각·`boot_id`(시작·끝)를 기록 — 도중 재부팅을 재측정 사유로 가리지 않음
