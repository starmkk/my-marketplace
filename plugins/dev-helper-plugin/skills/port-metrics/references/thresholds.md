# 임계 — 결정 방법·잡음 바닥·동결·판정 상태

- 기본 수치: `metric-catalog.md` §9 생성 표와 `make_report.py init-thresholds` 출력(이 문서에는 수치를 다시 쓰지 않음)
- 원칙: **측정 전 동결 → 측정 → 판정**. 측정 후 완화 금지(강화만 허용, 강화도 새 동결 파일로 재측정), fail 원판정은 보존

---

## 1. 임계를 정하는 방법(우선순위 순)

| 방법 | 언제 | 절차 | 사례 |
|---|---|---|---|
| 기본값 | 대부분의 NUM·DEC·STB·streaming 지표 | 생성 표 값을 그대로 동결 | 4 사례 공통값(fp max_abs·rel_l2, lowp cos·rel_l2, ABBA 허용 %) |
| 잡음 바닥 × 배수 | 기본값이 잡음보다 작거나 모델 고유 지표 | §2 로 N-1 측정 → 배수(1.5~10)를 곱해 limit, `noise_floor` 기입 | SoundAI Δmargin 2e-3 = 단말 fp32 잡음 1.24e-3 × 약 1.6, Nemotron AOSC tau = 실측 × 10 |
| 음성 대조군 | 기본값이 결함을 통과시킬 위험 | 알려진 결함 변형(무패치 변환·창 함수 변경 등)이 **반드시 fail** 하는 값으로 | SpeechLM: 무패치 fp16(max_abs 0.027)이 fail 하도록 fp16 절대 임계, Nemotron mel: 결함 변이와 정상 최악 사이 |
| α 스윕(허용치 곡선) | 중간 텐서 오차가 최종 결과에 주는 영향을 모를 때 | ref + α·(target − ref) 주입, 결과 분기 0 이 되는 오차 수준 | SpeechLM: rel_l2 3.5e-4 에서 분기 0 |
| 제품 KPI | ACC.degradation·SPD.rtf_max(S4·S5) 등 `limit: null` 항목 | 요구사항에서 가져와 근거(`reason`)와 함께 기입 | Zipformer CER 셋별 +0.30 p·평균 +0.15 p, Nemotron DER +0.5 %p |

- 실측 drift 규모를 그대로 임계로 삼는 방식(SpeechLM HOST_MEASURED)은 **이미 측정한 값으로 임계를 맞추는 것**이라 사후 완화와 구분이 어려움 → 쓸 경우 별도 측정 집합으로 정하고 `reason` 에 명시

## 2. 잡음 바닥(N-1)

- 정의: 같은 단계에서 **결과가 같아야 할 두 구현 변형** 간 차이. 이보다 작은 임계는 판정 능력이 없음
- 측정 쌍(해당하는 것 모두)
  - thread 1 ↔ 4 (같은 바이너리·입력)
  - attention eager ↔ sdpa (PT)
  - CPU fp32 ↔ CUDA(TF32 off) fp32 (PT)
  - 같은 바이너리 반복 실행(결정성 확인 겸)
- 기록: thresholds `rules[]` 의 해당 규칙에 `noise_floor`(값)·`noise_source`(쌍 설명) 기입
- 판정 영향: `<=` 규칙에서 noise_floor > limit, `>=` 규칙에서 noise_floor < limit 이면 그 지표는 `not_established`(판정 불성립 — 통과도 실패도 아님)
- `convert` 목적이면 S1-S2 NUM 규칙에 noise_floor 가 없을 때 `not_established`(새 모델에서 기본값이 맞는지 확인을 강제)
- 사례: Nemotron G1-step 임계 1e-4 < eager↔sdpa 2.93e-4 → 원판정 FAIL 을 유지하되 기준점 재정의, SoundAI Δp 1e-4 < thread 4↔1 잡음 1.02e-4 → 지표 교체(Δmargin)

## 3. 동결 절차

1. `make_report.py init-thresholds --stages ... --purposes ... --model-types ... --input-kind ...` → 기본 위치 `experiments/port-metrics/thresholds.json`(프로젝트 루트 기준, `-o <경로>` 로 바꾸면 프로젝트 CLAUDE.md 에 포인터 1 줄, `-o -` = stdout)
2. `limit: null` 항목을 KPI·잡음 바닥으로 채우고 `reason` 기입. 기록만 할 항목은 `op: "record"` 로 명시(규칙 삭제 금지 — 판정 지표에 규칙이 없으면 not_established)
3. §2 잡음 바닥을 측정해 `noise_floor`·`noise_source` 기입
4. `frozen_at` 에 현재 시각(ISO 8601, 타임존 포함) 기록 → 프로젝트 저장소에 커밋
5. `make_report.py checklist` 로 측정할 지표·원자료 키 목록 확인(`--thresholds` 생략 = 기본 위치)
6. 측정 하네스가 회차마다 `identity.thresholds_sha256 = sha256(동결 파일)` 과 `started_at` 을 기록

- 재동결: 동결 파일이 이미 있으면 `init-thresholds` 는 rc 2 로 거부함(새 세션이 실수로 다시 만들어 덮어쓰는 사고 방지). 범위·임계를 바꿔야 하면 사용자 승인 후 `--force` 로 다시 만들고 커밋 — 이전 판본은 `thresholds.json.<N>.bak`(번호 증가)·git 이력에 남고, 이전 회차는 sha 불일치로 invalid 이므로 재측정. 사용한 파일의 절대 경로는 stderr 와 리포트 §0 `임계 파일` 줄에 표시됨

- 겹치는 규칙(같은 지표에 when 이 겹침)은 형식 오류(rc 2) — 좁은 규칙을 추가해 특정 문맥만 완화하는 길을 막음
- 한계: 동결 파일과 frozen_at 을 고의로 다시 쓰는 변조는 막지 못함. 이 장치는 **실수와 순서 위반**(측정 후 동결·다른 판본 임계로 판정)을 잡는 것임 → 동결 파일은 측정 전에 커밋해 git 이력을 근거로 둠

## 4. 판정 상태

| 상태 | 의미 | 대표 원인 |
|---|---|---|
| `pass` | 동결 임계 충족 | — |
| `fail` | 동결 임계 위반 | 실측 결과 |
| `invalid` | 측정 자체가 무효(값은 남기되 근거로 안 씀) | 신원 키 누락·dirty·임계 sha 불일치·동결 전 측정·열 조건 위반·sampler 품질·nonce 짝·ABBA 구성, invalid 회차를 참조한 비교 |
| `not_established` | 판정 불성립(통과로 간주 금지) | 미동결·limit null·판정 지표 무규칙·잡음 바닥 > 임계·필수 지표 미측정·퇴화 입력(분모 0 등)·기준 서브셋 누락 |
| `record_only` | 기록만 | 판정 대상 아님·op record·카탈로그 범위 밖 문맥 |

- 집계 우선순위: invalid > not_established > fail > pass (record_only 제외)
- 종료 코드: 0 = 판정 대상 ≥ 1 ∧ 전부 pass 또는 사전 등록 예상 fail(§6) / 1 = 예상 밖 fail·invalid·not_established 또는 판정 대상 0 / 2 = 형식 오류 / 3 = 예외
- 예상 fail 은 상태가 아님 — 상태는 `fail` 그대로, 종합 판정(overall)·종료 코드에서만 pass 로 봄. 상태 집계 표는 원판정 건수

## 5. fail 이 났을 때

- 임계를 완화하지 않음. root-cause.md 절차로 원인 단계·모듈을 좁힘
- 결과 기록: fail 원판정 + 원인 + 사용자 결정(수용·MNN 패치·프로파일 제외·임계 재정의 후 **새 측정**) 을 리포트 옆 dev-log 에 남김
- 원판정을 "재설정 전 판정"으로 보존한 채 새 정책을 세운 사례: SpeechLM STRICT_100 → HOST_MEASURED, Zipformer 지표② → REF 강등(사용자 결정)

## 6. 예상 fail 사전 등록(`expected_fail`)

- 대상: 기본 임계를 유지하면 **구조적으로** fail 하는 회차 지표. 임계를 풀거나 `op: record` 로 바꾸는 대신 원판정(fail)을 싣고 rc 만 막지 않게 함
  - 예: 2 모델 파이프라인(ASR → 분류기)의 `SPD.jitter`·`SPD.tail_over_hop` — 분류 hop 이 섞여 단위 지연이 두 봉우리로 갈림
- 등록: 동결 전 thresholds `rules[]` 의 해당 규칙에 `expected_fail: "<사유>"`(형식 = results-format.md §1)
- 등록 요건(사유에 적을 것 — 셋 다)
  - 구조 원인: 왜 이 구성에서 반드시 fail 하는지(모델 수·hop 구조 등), 측정 잡음·미해결 결함이 아님
  - 선례: 같은 구조의 앞선 측정에서 같은 지표가 같은 방향으로 fail 한 기록(문서·리포트 경로)
  - 양쪽 구성에 같게 나타남: 기준(A)·대상(B′) 어느 쪽에서도 fail 한다는 근거 — 한쪽에서만 fail 하면 구조가 아니라 회귀
- 허용 범위: `when.stage` 가 있는 규칙, 회차(scope = run) 지표, 범주 SPD·RES·PWR·THM. ACC·DEC·NUM·STB·CNV 와 pair·ABBA 지표는 목적의 핵심 판정이라
  등록 불가(rc 2). 넓은 규칙(`when: {}`)은 stage 별 규칙으로 나눠 필요한 stage 에만 등록
- 판정 영향
  - 그 규칙으로 판정된 항목이 fail 이면 "예상" 표지(§0 예상 fail 목록·§8 `fail(예상)`), pass 면 표지 없음. invalid·`not_established` 는 그대로 rc 1
  - rc 0 = 판정 대상 ≥ 1 ∧ 모든 판정 항목이 pass 또는 예상 fail. 예상 밖 fail 이 하나라도 있으면 rc 1
  - 등록 규칙은 리포트 §0(`지표 [when]: 사유 — 덮은 항목 k, fail j`)과 `checklist` 에 매번 표시 — 등록이 조용히 늘지 않게 함
- **균형**: 예상 fail 이 기준·대상 양쪽에 나면 대상 쪽이 더 자주 fail 해도 가려짐 → 잡음 블록이 아닌 ABBA 블록(A ↔ B′)이 있으면 목적과 무관하게 블록마다 (지표, 서브셋)별로
  a 쪽·b 쪽 회차의 그 규칙 항목 fail 수를 셈
  - b 쪽 fail 수 > a 쪽 = `fail`(예상 아님, rc 1), 그 밖 = `pass`. 값 = n_b − n_a, 사유에 분모 표기
  - 한쪽에만 규칙 항목이 있거나 어느 항목이든 invalid·`not_established` = `not_established`, 블록 구성 invalid = `invalid`
  - `regress` 목적: 예상 fail 항목의 (회차 stage·pacing, 지표, 서브셋)을 판정한 균형 항목이 없으면 `not_established`("균형 대조 블록 없음", 대상 `(블록 없음)`) — regress 에서는 예상 fail 만으로 rc 0 이 되지 않음
  - regress 에서 블록이 판정하지 않는 지표(sampler `RES.*`, 블록과 pacing 이 다른 회차의 지표 등)의 예상 fail 은 `not_established` — 그 지표를 재는 A ↔ B′ 블록을 따로 실어야 함
  - 균형 항목은 ABBA 필수 지표 누락 검사를 채우지 않음(블록 `metrics` 는 따로 실어야 함)
- **측정 후 추가 = 사후 완화**: `expected_fail` 은 동결 파일 바이트에 들어가므로 측정 뒤 넣으면 sha 가 달라져 전 회차 invalid. 넣으려면 사용자 승인 후 재동결 + 재측정

## 7. 잡음 블록·ABBA 시작 대역

- A ↔ B′ 블록의 pass 는 "열화 중앙값 ≤ 허용폭" 한쪽만 봄 → 같은 빌드끼리(A ↔ A) 재도 그만큼 흔들리는지 **잡음 블록**(`abba[].noise_for`)으로 대조
  - 잡음 블록은 양방향(|중앙값| ≤ 같은 허용폭) — 음의 잡음(−3 %)도 fail. 허용폭은 잡음 결과를 보고 넓히지 않음
  - 대상 pass ∧ 잡음 비 pass = 대상 `not_established`(비저하를 주장하지 않음). 잡음 블록에 없는 지표의 대상 pass 는 사유에 "잡음 대조 없음" 병기
  - 한계: 쌍별 Δ 중앙값의 부호 양쪽만 막고 쌍별 산포는 막지 못함 — 잡음 pass 는 "잡음 중앙값이 허용폭 안"까지만 뜻함
- 시작 온도 대역: 상한(`start_battery_max_c`)만 두면 차가운 시작(클럭 상한 구간이 긺)과 따뜻한 시작이 한 블록에 섞임 → `validity.abba_start_battery_min_c` 로
  ABBA 참조 회차의 하한을 동결(예: [32.0, 33.0] °C). 미만 = 그 블록 invalid
