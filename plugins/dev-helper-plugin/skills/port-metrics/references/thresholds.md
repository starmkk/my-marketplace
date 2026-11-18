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
- 종료 코드: 0 = 판정 대상 ≥ 1 ∧ 전부 pass / 1 = fail·invalid·not_established 또는 판정 대상 0 / 2 = 형식 오류 / 3 = 예외

## 5. fail 이 났을 때

- 임계를 완화하지 않음. root-cause.md 절차로 원인 단계·모듈을 좁힘
- 결과 기록: fail 원판정 + 원인 + 사용자 결정(수용·MNN 패치·프로파일 제외·임계 재정의 후 **새 측정**) 을 리포트 옆 dev-log 에 남김
- 원판정을 "재설정 전 판정"으로 보존한 채 새 정책을 세운 사례: SpeechLM STRICT_100 → HOST_MEASURED, Zipformer 지표② → REF 강등(사용자 결정)
