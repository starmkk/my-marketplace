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
4 사례의 재측정 원인(references/case-evidence.md).

## 핵심 구조

- **단계**: S1 PT(CUDA, 정확도 기준 + CPU fp32 골든) → S2 pymnn → S3 C++ CLI → S4 단말 CLI → S5 단말 앱(출하 상태). GPU 는 `backend` 변형
- **비교(이중 기준)**: 정확도는 항상 S1 대비 누적 열화, 텐서·출력 동등성은 인접 단계끼리 — 어느 단계에서 틀어졌는지 바로 드러남
- **지표 = 코어 + 목적 + 유형**: 코어(항상) + `convert`·`regress`·`optimize`·`ship` + `streaming`·`llm`·`classifier`
- **정의 정본**: `assets/catalog.json`(45 지표). 시간·자원 지표는 생성기가 원자료 행에서 계산, 텐서·정확도는 프로젝트가 값 제공
- **판정 상태**: `pass`·`fail`·`invalid`(측정 무효)·`not_established`(판정 불성립)·`record_only`

## 절차

```
S="${CLAUDE_PLUGIN_ROOT}/skills/port-metrics/scripts/make_report.py"
```

1. **범위·임계 동결(측정 전)**
   ```bash
   python3 "$S" init-thresholds --stages S1,S2,S3,S4,S5 --purposes convert,ship \
       --model-types streaming --input-kind audio -o thresholds.json
   ```
   - `limit: null` 을 제품 KPI·잡음 바닥으로 채우고 `reason` 기입, 기록만 할 항목은 `op: "record"`(규칙 삭제 금지)
   - `convert` 면 잡음 바닥(thread 1↔4·eager↔sdpa·CPU↔GPU)을 재서 S1-S2 NUM 규칙 `noise_floor` 기입
   - `frozen_at` 기록 후 프로젝트 저장소에 커밋 → references/thresholds.md
2. **체크리스트 확인**
   ```bash
   python3 "$S" checklist --thresholds thresholds.json -o checklist.md
   ```
   - 단계별로 잴 지표·필요한 원자료 키·회차 종류(accuracy·perf·sampler)를 측정 전에 확인
3. **측정**: references/measurement-control.md 의 통제를 지킴
   - 회차마다 `identity`(단계별 필수 키 + `thresholds_sha256`)·`started_at`·실효 프로파일(`effective`) 기록
   - 단말: 회차 시작 배터리 ≤ 34 °C ∧ 상한 클럭 복구, 45 °C 정지 / 38 °C 재개, 정지 구간 행 `paused`
   - perf 회차와 sampler 회차 분리(nonce 결속), A/B 는 같은 세션 ABBA ≥ 3 쌍
4. **결과 JSON 조립**: 프로젝트 어댑터가 references/results-format.md 형식으로 `results.json` + `timing.jsonl`·`samples.jsonl` 작성
5. **리포트**
   ```bash
   python3 "$S" report results.json --thresholds thresholds.json -o report.md   # rc 0 = 전부 pass
   python3 "$S" report results.json --thresholds thresholds.json --partial S1,S2 -o report.md  # 개발 중 부분
   ```
   - rc 1 = fail·invalid·not_established 존재(누락 지표 포함), rc 2 = 형식 오류
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

## 참조

| 문서 | 내용 |
|---|---|
| references/metric-catalog.md | 지표별 정의·이유·주의 + 생성 표(기본 임계) |
| references/stage-matrix.md | 단계·S1 두 산출물·비교 쌍·목적별 범위·회차 구성 예 |
| references/profiles.md | 프로파일 ID·실효 3 필드·x86/arm64 차이·precision 적용 증거 |
| references/measurement-control.md | 신원 필수 키·열 통제·ABBA·회차 분리·단위·분위수 |
| references/thresholds.md | 임계 결정 방법·잡음 바닥·동결 절차·상태 5 종 |
| references/root-cause.md | 불일치 원인 추적(단계 사슬·op 덤프·교차 주입·α 스윕·귀속) |
| references/results-format.md | results.json·thresholds.json·timing·samples 형식, 어댑터 체크 |
| references/case-evidence.md | 4 사례 대조와 근거 경로 |

## 리포트 구성

0 요약(상태 집계·fail 목록) / 1 측정 신원 / 2 단계 사슬 동등성 / 3 태스크 정확도 / 4 속도 / 5 자원 /
6 A/B / 7 측정 조건(열·cpuset) / 8 판정 상세 / 9 누락 지표

## 유지보수

- 지표 추가·기본값 변경은 `assets/catalog.json` 만 고치고 `python3 "$S" catalog-md --write` 로 생성 표 갱신
- 검증: `env -u PYTHONPATH python3 -m unittest discover -s scripts/tests -t scripts` (스킬 디렉터리에서)
