---
name: port-metrics
description: |
  원본 PyTorch 모델을 MNN 으로 포팅하는 5 단계(S1 PT CUDA → S2 pymnn → S3 C++ CLI → S4 단말 CLI →
  S5 단말 Java 앱, GPU 변형 포함)에서 측정할 공통 지표를 정의하고, 측정 전 임계 동결·필수 지표
  체크리스트·결과 JSON 검증·판정·표준 markdown 리포트 생성까지 하는 스킬. 프로젝트(모델)에 종속되지 않음.

  다음 상황에서 반드시 사용하라:
  - 새 모델의 PT → MNN 변환·포팅을 시작하거나 측정 계획을 세울 때 ("측정 지표", "성능 지표", "측정 계획")
  - PT 대비 MNN 동등성·정확도·속도·메모리를 측정·보고할 때 ("PT vs MNN", "parity", "RTF", "PSS", "리포트")
  - MNN 패치·C++ 수정 후 회귀를 확인할 때 ("패치 회귀", "ABBA", "성능 회귀")
  - 정밀도 프로파일(fp16·w8a·precision·memory)을 비교하거나 단말·앱 출하 게이트를 판정할 때
  - MNN 결과가 PT 와 안 맞아 원인을 찾을 때 ("불일치 원인", "어느 단계에서 틀어졌나")

  관련: `device-settings`(단말 설정 기록·복원), on-device-ai-plugin `mnn`(MNN API·변환·빌드)·
  `mnn-source-inspector` 에이전트(MNN 소스로 동작 확정)
---

# port-metrics — PT → MNN 포팅 공통 측정 지표

프로젝트마다 지표 정의가 달라 다시 측정하는 일을 막기 위해 **무엇을·어떤 정의로·어떤 조건에서** 잴지를
측정 전에 고정하고, 결과를 같은 형식의 리포트로 만듦. 근거는 Zipformer·SpeechLM·SoundAI(Granite)·Nemotron
4 사례의 재측정 원인과 VoiceGuard 2 모델 파이프라인 사례(references/case-evidence.md).

## 핵심 구조

- **단계**: S1 PT(CUDA, 정확도 기준 + CPU fp32 골든) → S2 pymnn → S3 C++ CLI → S4 단말 CLI → S5 단말 앱(출하 상태). GPU 는 `backend` 변형
- **비교(이중 기준)**: 정확도는 항상 S1 대비 누적 열화, 텐서·출력 동등성은 인접 단계끼리 — 어느 단계에서 틀어졌는지 바로 드러남
- **지표 = 코어 + 목적 + 유형**: 코어(항상) + `convert`·`regress`·`optimize`·`ship` + `streaming`·`llm`·`classifier`
- **정의 정본**: `assets/catalog.json`(45 지표). 시간·자원 지표는 생성기가 원자료 행에서 계산, 텐서·정확도는 프로젝트가 값 제공
- **판정 상태**: `pass`·`fail`·`invalid`(측정 무효)·`not_established`(판정 불성립)·`record_only`
- **예상 fail**: 구조적으로 fail 하는 회차 지표(SPD·RES·PWR·THM)를 **측정 전** 규칙에 `expected_fail`(사유)로 등록 — 원판정은 fail 그대로 싣고
  종합 판정·rc 에서만 pass 로 봄. 리포트 §0·체크리스트에 등록 규칙을 매번 표시

## 절차

```
S="${CLAUDE_PLUGIN_ROOT}/skills/port-metrics/scripts/make_report.py"
```

- **동결 파일 기본 위치 = `experiments/port-metrics/thresholds.json`**(프로젝트 루트에서 실행). 명령은 모두 이 위치를 기본으로 씀 —
  이 위치를 쓰면 프로젝트 CLAUDE.md 에 경로 포인터가 필요 없음. 다른 위치를 쓸 때만 프로젝트 CLAUDE.md 에 `--thresholds <경로>` 를 한 줄 적음
- 기존 동결 파일이 있으면 그것을 씀. `init-thresholds` 를 다시 실행하지 않음(기존 파일이 있으면 rc 2 로 거부됨)

1. **범위·임계 동결(측정 전)**
   ```bash
   python3 "$S" init-thresholds --stages S1,S2,S3,S4,S5 --purposes convert,ship \
       --model-types streaming --input-kind audio      # → experiments/port-metrics/thresholds.json
   ```
   - `limit: null` 을 제품 KPI·잡음 바닥으로 채우고 `reason` 기입, 기록만 할 항목은 `op: "record"`(규칙 삭제 금지)
   - `convert` 면 잡음 바닥(thread 1↔4·eager↔sdpa·CPU↔GPU)을 재서 S1-S2 NUM 규칙 `noise_floor` 기입
   - 기본 임계로 구조적으로 fail 하는 지표(예: 2 모델 파이프라인의 `SPD.jitter`)는 임계를 풀지 말고 규칙에 `expected_fail: "<구조 사유·선례>"` 등록 →
     references/thresholds.md §6. A ↔ B′ ABBA 블록이 있으면 a·b 쪽 fail 수 균형을 생성기가 대조(`regress` 는 대조 블록이 없으면 not_established)
   - 선택 한도: `validity.abba_start_battery_min_c`(ABBA 시작 온도 대역 하한)
   - 호환 변경: 1.0.25 부터 thresholds `validity` 의 모르는 키 = 형식 오류(rc 2)
   - `frozen_at` 기록 후 프로젝트 저장소에 커밋 → references/thresholds.md
   - 재동결(범위·임계 변경)은 사용자 승인 후 `--force` — 이전 판본은 `thresholds.json.<N>.bak`(번호 증가, 덮어쓰지 않음)과 git 이력에 남고, 이전 회차는 sha 불일치로 invalid 가 되므로 재측정
2. **체크리스트 확인**
   ```bash
   python3 "$S" checklist -o checklist.md            # --thresholds 생략 = 기본 위치
   ```
   - 단계별로 잴 지표·필요한 원자료 키·회차 종류(accuracy·perf·sampler)를 측정 전에 확인
3. **측정**: references/measurement-control.md 의 통제를 지킴
   - 회차마다 `identity`(단계별 필수 키 + `thresholds_sha256`)·`started_at`·실효 프로파일(`effective`) 기록
   - 단말: 회차 시작 배터리 ≤ 34 °C ∧ 상한 클럭 복구, 45 °C 정지 / 38 °C 재개, 정지 구간 행 `paused`
   - perf 회차와 sampler 회차 분리(nonce 결속), A/B 는 같은 세션 ABBA ≥ 3 쌍
   - 잡음 대조: A ↔ A 블록을 `noise_for: "<대상 블록>"` 으로 실으면 양방향(|중앙값| ≤ 허용폭) 판정 — 미통과면 대상 블록의 pass 는 `not_established`
   - 재측정으로 대체된 회차는 지우지 않고 `superseded_by`·`superseded_reason` 으로 남김(판정 제외, 리포트 §1 표시). 재측정 사유는 원자료에서 도출
4. **결과 JSON 조립**: 프로젝트 어댑터가 references/results-format.md 형식으로 `results.json` + `timing.jsonl`·`samples.jsonl` 작성
5. **리포트**
   ```bash
   python3 "$S" report results.json -o report.md                     # rc 0 = 전부 pass(예상 fail 포함)
   python3 "$S" report results.json --partial S1,S2 -o report.md     # 개발 중 부분
   ```
   - rc 0 = 판정 대상 ≥ 1 ∧ 모든 판정 항목이 pass 또는 사전 등록 예상 fail
   - rc 1 = 예상 밖 fail·invalid·not_established 존재(누락 지표 포함) 또는 판정 대상 0, rc 2 = 형식 오류, rc 3 = 예외
6. **fail 이면 원인 추적**: 임계 완화 대신 references/root-cause.md — 첫 이탈 단계 → 모듈·op → 원인, 패치했으면 `regress` 로 재측정

## 금지 규칙(재측정을 만든 실제 원인)

1. 측정 후 임계 완화 금지(강화만, 그것도 새 동결 파일로 재측정). fail 원판정은 보존
2. 요청값으로 실측 필드를 채우지 않음 — `effective`·`threads_effective` 는 엔진이 적용한 값
3. PT-CUDA(TF32 기본 on)를 텐서 골든으로 쓰지 않음 — 골든은 CPU fp32
4. 호스트(x86) 결과로 단말 fp16 품질을 판단하지 않음 — x86 `precision=low` 는 no-op
5. RTF 를 방식 수식어 없이 쓰지 않음 — `rtf_max`(최대 속도 투입)·`rtf_rt`(실시간 투입), Σwall ÷ Σaudio
6. 다른 세션 단일 수치로 회귀를 판정하지 않음 — 같은 세션 ABBA, 허용폭 사전 동결
7. 샘플러 병행 회차의 RTF·지연을 SoT 로 쓰지 않음
8. MB(10^6)·MiB 혼용 금지 — 메모리는 MiB, 원자료는 kB
9. smoke 결과로 판정하지 않음 — 전수 또는 사전 고정 표본
10. S4↔S5 성능 차를 "JNI 오버헤드"로 해석하지 않음 — S5 는 출하 프로세스 상태라 코어 집합이 다름(JNI + 프로세스 상태 합산)
11. 예상 fail 사후 등록 금지 — `expected_fail` 은 동결 전에만 넣음. 측정 뒤 추가 = 사후 완화(동결 파일 sha 가 바뀌어 전 회차 invalid → 재동결·재측정).
    정확도·동등성(ACC·DEC·NUM·STB·CNV)과 pair·ABBA 지표는 예상 fail 로 덮지 못함(rc 2)

## 참조

| 문서 | 내용 |
|---|---|
| references/metric-catalog.md | 지표별 정의·이유·주의 + 생성 표(기본 임계) |
| references/stage-matrix.md | 단계·S1 두 산출물·비교 쌍·목적별 범위·회차 구성 예 |
| references/profiles.md | 프로파일 ID·실효 3 필드·x86/arm64 차이·precision 적용 증거 |
| references/measurement-control.md | 신원 필수 키·열 통제·ABBA(잡음 블록·연속 세션)·회차 분리·단위·분위수·재측정(대체 회차)·실시간 lag 기준 시각·하네스 종료 규칙 |
| references/thresholds.md | 임계 결정 방법·잡음 바닥·동결 절차·상태 5 종·예상 fail 등록 요건 |
| references/root-cause.md | 불일치 원인 추적(단계 사슬·op 덤프·교차 주입·α 스윕·귀속) |
| references/results-format.md | results.json·thresholds.json·timing·samples 형식, 어댑터 체크 |
| references/case-evidence.md | 4 사례 대조와 근거 경로, 5 번째 사례(2 모델 파이프라인 — 예상 fail·합성 검증) |

## 리포트 구성

0 요약(상태 집계·fail 목록 — 예상 fail 이 있으면 예상 밖 fail 과 나눠 표시·등록 규칙·대체 회차 수) / 1 측정 신원(호출 경로·입력 집합·대체 표시 포함) /
2 단계 사슬 동등성 / 3 태스크 정확도 / 4 속도 / 5 자원 / 6 A/B(잡음 블록·예상 fail 균형 포함) / 7 측정 조건(열·cpuset) / 8 판정 상세 / 9 누락 지표

## 유지보수

- 지표 추가·기본값 변경은 `assets/catalog.json` 만 고치고 `python3 "$S" catalog-md --write` 로 생성 표 갱신
- 검증: `env -u PYTHONPATH python3 -m unittest discover -s scripts/tests -t scripts` (스킬 디렉터리에서)
