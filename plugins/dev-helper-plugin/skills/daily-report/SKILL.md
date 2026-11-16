---
name: daily-report
description: >
  claude-insights 가 생성한 Claude Code 작업 리포트 열람 — 매일 06:00 일일 리포트(어제 작업,
  실패·재시도, CLAUDE.md 규칙 준수, 사용량)와 매주 월요일 /insights 기반 주간 요약을 보여주고,
  리포트의 개선 제안을 사용자 확인 후 적용하도록 돕는다. "/daily-report", "일일 리포트",
  "어제 리포트", "주간 요약", "insights 요약", "리포트 제안 적용" 이 언급될 때 사용하라.
argument-hint: "[YYYY-MM-DD|어제|weekly]"
---

# daily-report

리포트 생성은 claude-insights 저장소의 호스트 cron 이 수행함. 이 스킬은 생성된 리포트를 **열람**하고
제안 적용을 보조만 함.

## 저장소 위치 탐색 (먼저 존재하는 경로 사용)

1. 환경변수 `CLAUDE_INSIGHTS_DIR`
2. `/workspace/work/claude/claude-insights` — nemotron 등 `/home/<user>` 를 `/workspace` 로 마운트한 컨테이너
3. `~/work/claude/claude-insights` — 호스트

모두 없으면 "이 머신에는 claude-insights 리포트가 없음 — 리포트는 생성 호스트와 메일로만 제공" 이라고
안내하고 종료함.

| 종류 | 저장소 상대 경로 |
|---|---|
| 일일 리포트 | `reports/daily/<YYYY-MM-DD>.md` |
| 일일 집계 원본 | `reports/data/<YYYY-MM-DD>.json` |
| 주간 요약 | `reports/weekly/<YYYY-Www>/summary.md` |
| 주간 /insights 원본 | `reports/weekly/<YYYY-Www>/insights.html` |
| 실행 로그 | `logs/daily-<날짜>.log`, `logs/weekly-<주차>.log` |

## 절차

1. 인자 해석
   - 없음 → 가장 최근 일일 리포트
   - 날짜(`2026-11-16`, `어제`, `그제`) → 해당 일일 리포트. 상대 날짜는 KST 기준 절대 날짜로 변환
   - `weekly`·`주간` → 가장 최근 주간 요약
2. 파일을 Read 로 읽어 섹션 1(요약)과 7(오늘 시도해볼 개선)을 먼저 보여주고, 나머지는 요청 시 보여줌
3. 파일이 없거나 제목에 `(실패)` 가 있으면 해당 로그의 마지막 20줄을 보여주고 재실행 명령을 안내함
   - 재실행은 **호스트**에서만: `<저장소>/scripts/run_daily_report.sh --date <날짜>`,
     `<저장소>/scripts/run_weekly_insights.sh --week <주차>`
   - 저장소 경로가 `/workspace` 로 시작하면 컨테이너 안이므로 명령을 안내만 하고 실행하지 않음
     (컨테이너에서 실행하면 그 세션 기록이 분석 대상에 섞임)
4. 사용자가 제안 적용을 요청하면
   - 대상 파일(CLAUDE.md, `~/.claude/skills/`, `settings.json` 등)을 먼저 읽고 변경 diff 를 제시
   - 사용자 확인 후에만 적용. settings.json 은 기존 hooks 항목을 보존하는 병합만 허용
   - 적용 후 어떤 제안을 반영했는지 한 줄로 보고(다음 주간 요약의 "지난주 제안 추적" 에 반영됨)

## 하지 않는 것

- 컨테이너 안에서 리포트 생성·재생성을 실행하지 않음
- 제안을 사용자 확인 없이 적용하지 않음
