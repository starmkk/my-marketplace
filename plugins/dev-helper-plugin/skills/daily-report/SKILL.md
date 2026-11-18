---
name: daily-report
description: >
  claude-insights 가 Notion 「Claude Code 리포트」 DB 에 게시한 일일·주간·월간 리포트를 열람하고, 미검토 리포트의
  조치 항목을 AskUserQuestion 인터뷰로 결정(적용·보류·기각)해 적용·기록·검토 상태 갱신까지 하는 스킬.
  "/daily-report", "일일 리포트", "어제 리포트", "주간 리포트", "월간 리포트", "리포트 검토",
  "조치 항목", "리포트 제안 적용" 이 언급될 때 사용하라.
argument-hint: "[없음 | YYYY-MM-DD | 어제 | 시작~끝 | weekly | monthly] [--host all|aip1|aip2]"
---

# daily-report v2 — 리포트 검토 인터뷰

리포트 생성·게시는 claude-insights 저장소의 호스트 cron(`scripts/run_reports.py`)이 수행함. 이 스킬은
Notion 의 리포트를 읽고 조치 항목을 사용자와 결정함. 생성·재생성은 호스트에서만 함(컨테이너에서는 명령 안내만).

## 0. 준비

- 저장소: `CLAUDE_INSIGHTS_DIR` → `/workspace/work/claude/claude-insights`(컨테이너) →
  `~/work/claude/claude-insights`(호스트) 중 먼저 있는 곳. `config.env` 에서 `HOST_LABEL`·`NOTION_DATA_SOURCE_ID` 를 읽음
  - 저장소가 없으면 HOST_LABEL 은 `hostname` 소문자, 리포트 DB 는
    `collection://41be93ff-c5a8-818a-9215-000b32131bbe`
- Notion 도구는 한 번에 로드: `ToolSearch({query: "select:mcp__claude_ai_Notion__notion-query-data-sources,mcp__claude_ai_Notion__notion-fetch,mcp__claude_ai_Notion__notion-update-page", max_results: 3})`
  - DB 스키마는 아래 표가 정본 — 별도 fetch 하지 않음

| 속성 | 값 |
|---|---|
| `제목` | `2026/11/16일 일일리포트(aip2) - 검토필요` (끝 접미어 = 상태) |
| `유형` · `호스트` · `주차` | 일일·주간·월간 · aip1·aip2 · `2026/11/3주차(11월15일~11월21일)` |
| `기간` | date 범위 — SQL 열 `date:기간:start`·`date:기간:end` |
| `검토` | 검토필요(🔴) · 검토미정(🟡) · 진행중(🔵) · 검토완료(✅) — 생성실패 페이지는 제목 접미어 `생성실패`(⚠️) |
| `조치 항목` · `키` | 미결정 조치 수 · `<host>|<기간 키>` |
| `관련 이슈` | 이슈 DB relation — 진행중(🔵)은 연결된 이슈가 진행 중이라는 표시(notion-issue 스킬이 설정·해제) |

## 1. 인자 → 조회 범위

| 인자 | 범위 |
|---|---|
| 없음 | 이 호스트의 `검토` ≠ 검토완료, 최신 7건 — 검토필요 → 검토미정 → 진행중 순, 같은 상태는 최신순 |
| `2026-11-16` · `어제` · `그제` | 그 날짜 일일(상대 날짜는 KST 절대 날짜로) |
| `11/10~11/16` · `2026-11-10~2026-11-16` | 기간과 겹치는 미검토 리포트 전체(일일·주간·월간) |
| `weekly` · `monthly` | 최신 주간 · 월간 |
| `--host all|aip1|aip2` | 호스트 필터(기본 HOST_LABEL) |

조회는 `notion-query-data-sources` SQL 1회: `SELECT url, "제목", "키", "검토", "유형", "date:기간:start", "date:기간:end", "조치 항목", "관련 이슈" FROM "<DB>" WHERE "호스트" = ? AND ...` (값은 `params` 로 바인딩)

## 2. 조치 항목 수집

- 각 페이지를 `notion-fetch` 로 읽어(독립 호출은 한 메시지로 병렬) `## ` 요약 절 3줄과 조치 표를 모음
  - 표 열: `id · 항목 · 종류 · 대상 · 근거 · 방법 · 중요도 · 키 · 결정` — 결정 열이 빈 행만 대상
  - 제목이 `생성실패` 면 원인 줄과 호스트 재실행 명령만 보여 주고 인터뷰 대상에서 뺌
  - `검토` 가 진행중이면 목록에 "관련 이슈 진행중"(`관련 이슈` 링크)을 표시하고 조치 항목은 그대로 인터뷰함 —
    이슈와 조치 항목은 별개
  - 본문에 `조치 항목 판독 실패` 비고가 있거나 `조치 항목` 속성이 비어 있으면(null) **판독 실패** — "조치 없음"과
    다름. 인터뷰·`검토완료 처리` 대상에서 빼고, 호스트 재생성 명령(`scripts/run_reports.py --date <끝 날짜> --kind
    <종류>`)을 안내함. 상태는 바꾸지 않음
- `키` 가 같은 항목은 1문항으로 합치고 근거 날짜를 병기(예: "11/14·11/16 반복")
- `<저장소>/reports/decisions.jsonl` 과 `<저장소>/decisions.permanent.jsonl` 에서 이미 applied·rejected 인 키는
  "이미 결정됨" 으로 자동 표기하고 묻지 않음
- CLAUDE.md 에 절을 추가하는 조치는 묻지 않고 기각으로 처리(사용자 영구 결정) — 근거를 한 줄로 알림

## 3. 인터뷰 (workflow-policy-plugin:ask-user-question 규칙)

- 먼저 항목별 설명(무엇을 · 왜(근거 수치) · 선택지별 변화 · 추천)을 출력하고 같은 응답에서 AskUserQuestion 1회(최대 4문항)
- 4건 이하: 항목당 1문항, 선택지 `적용`·`보류`·`기각`(추천을 첫 번째에 `(Recommended)`)
- 5건 이상: severity 상위 3건은 개별 문항, 나머지는 4번째 multiSelect 문항(최대 4개, 선택=적용·미선택=보류).
  남은 항목은 수를 알리고 다음 호출에서 이어 질문
- 조치가 없는 리포트(`조치 항목` = 0 이고 표에 "조치 항목 없음.")만 요약 1줄씩 보여 주고 `검토완료 처리` multiSelect 에 넣음

## 4. 적용

- 파일 변경은 대상 파일을 먼저 읽고 diff 를 한 번에 모아 제시 → 1회 확인 후 적용
  - `settings.json` 은 기존 hooks·permissions 를 보존하는 병합만
  - 마켓플레이스 plugin 변경은 patch 버전만 올리고 커밋은 `dev-helper-plugin:github-commit`
- `investigate` 는 조사 결과를 보고하고 결정은 `적용`(조사 완료)으로 기록

## 5. 기록과 상태 갱신

1. 결정마다 `<저장소>/reports/decisions.jsonl` 에 한 줄 추가:
   `{"key", "decision": "applied|rejected|deferred", "at": "<ISO KST>", "report_key": "<키>", "note": "<한 줄>"}`
   - 컨테이너(root)에서 썼으면 `chown "$(stat -c %u:%g <저장소>)" <파일>` 로 호스트 사용자 소유 유지
2. 페이지마다 `notion-update-page`:
   - 조치 표의 결정 열을 `update_content` 로 채움(행 단위 짧은 고유 문구로 `old_str`; Notion 은 `~` 를 `\~` 로 저장)
   - `update_properties`: `검토` = 아래 **검토 상태 재계산** 결과 · `조치 항목` = 미결정(보류) 수 ·
     `제목` 접미어를 새 상태로 교체 · `icon` ✅/🟡/🔴
   - 현재 `검토` 가 진행중이면 `검토`·`제목`·`icon` 은 유지하고 `조치 항목` 만 갱신(해제는 notion-issue 가 함).
     단 조치 없음 리포트를 사용자가 `검토완료 처리` 로 고르면 진행중보다 우선해 검토완료(✅) — 명시 결정 보존
   - **검토 상태 재계산**(notion-issue 의 진행중 해제도 이 규칙을 씀): 조치 표에 결정 열이 빈 행이 있거나 판독
     실패 → 검토필요(🔴) · 빈 행 없이 `보류` 가 남음 → 검토미정(🟡) · 모두 적용·기각 → 검토완료(✅) · 조치 없음
     ("조치 항목 없음.") → 사용자가 `검토완료 처리` 로 고른 경우만 검토완료, 그 외 검토필요
3. 결과를 표로 보고: 리포트 · 결정(적용 n·보류 n·기각 n) · 새 상태 · 남은 항목

## 하지 않는 것

- 리포트 생성·재생성 실행(호스트 `scripts/run_reports.py --date <날짜> --kind <종류>` 안내만)
- 사용자 확인 없는 적용, CLAUDE.md 절 추가, 다른 호스트 리포트의 상태 변경(`--host` 로 명시한 경우 제외)
- 비밀값을 Notion·결정 기록에 옮기기
