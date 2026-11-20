---
name: update-plugins
description: >
  vibe-coding-tools marketplace plugin 을 호스트에서 최신으로 갱신하고 voiceguard 컨테이너까지 즉시
  반영한 뒤 결과 표를 내는 스킬 — 호스트 갱신은 claude CLI, 컨테이너 반영은 claude-insights
  `run_reports.py --sync-env` 에 위임. "plugin 업데이트", "plugin 갱신", "모든 plugin 최신으로",
  "marketplace update", "plugin 설치·업데이트", "컨테이너에도 plugin 반영" 이 언급될 때 사용하라.
  일일 cron 의 env_sync 를 기다리지 않고 바로 반영할 때 쓴다.
---

# update-plugins — marketplace plugin 갱신·컨테이너 반영

호스트를 먼저 올린다. `--sync-env` 는 호스트↔컨테이너 버전이 **다를 때만** 컨테이너를 갱신하므로,
호스트가 구버전이면 아무것도 하지 않는다. 컨테이너 갱신 로직(EXDEV 대체 포함)은 claude-insights
`scripts/reports/env_sync.py` 가 정본 — 이 스킬에 복제하지 않는다.

## 0. 준비

- claude CLI: `command -v claude || ls ~/.local/bin/claude` — 없으면 중단하고 보고
- claude-insights 저장소: `CLAUDE_INSIGHTS_DIR` → `~/work/claude/claude-insights` 중 먼저 있는 곳.
  없으면 1~2 단계(호스트)만 하고 컨테이너 반영은 "저장소 없음 — 미반영" 으로 보고
- 컨테이너(voiceguard) 안에서 실행 중이면 호스트 단계를 하지 않고 호스트에서 실행하라고 안내만 함
- 갱신 전 버전 기록: `claude plugin list` 에서 `@vibe-coding-tools` 항목의 이름·Version·Scope

## 1. marketplace 갱신(호스트)

- `claude plugin marketplace update vibe-coding-tools`
- 출력에 `EXDEV` 가 있을 때만 `git -C ~/.claude/plugins/marketplaces/vibe-coding-tools pull --ff-only`
  로 대체. 그 밖의 실패·fast-forward 불가는 중단하고 원문 마지막 몇 줄을 보고(rebase·reset 금지)

## 2. plugin 갱신(호스트)

- 0 에서 기록한 user scope 항목마다 `claude plugin update <이름>@vibe-coding-tools`
- marketplace 에 있는데 설치되지 않은 plugin 은 설치하지 않고 표에 "미설치" 로만 표시(설치는 사용자 결정)
- project scope 설치분은 갱신하지 않고 표에 경로·버전만 표시 — 해당 프로젝트에서 갱신할지 사용자에게 알림

## 3. 컨테이너 반영

- 저장소에서 `.venv/bin/python scripts/run_reports.py --sync-env`
  - 출력의 `동기화 메모` 에 `EXDEV … git pull --ff-only 로 대체 갱신` 이 있으면 정상(대체 경로)
  - `갱신 실패`·`대체 실패` 줄이 있으면 실패로 보고
- 확인: `.venv/bin/python scripts/run_reports.py --sync-env --dry-run` 출력 중 **plugin 줄만** 판정
  - `plugin 버전 갱신: 없음` 과 `plugin 활성 집합 차이 …: 없음` 이면 일치
  - `CLAUDE.md 동기화` 등 다른 줄은 plugin 판정에 쓰지 않음(별도 항목으로만 표시)
  - 3 의 첫 실행 출력에 나오는 `<이름> (A ↔ B)` 는 **갱신 전** 차이 기록이다 — dry-run 결과로 판정

## 4. 보고

| plugin | 이전 | 이후(호스트) | 이후(컨테이너) | scope | 조치 |
|---|---|---|---|---|---|

- 조치: 갱신 · 변경 없음 · 미설치 · project scope(미갱신) · 실패(사유)
- 컨테이너 버전은 `docker exec voiceguard /root/.local/bin/claude plugin list` 로 확인한 값
- 끝에 한 줄: 현재 세션에는 `/reload-plugins` 후 적용됨(새 세션은 자동)

## 하지 않는 것

- plugin 활성화·비활성화 변경(활성 집합 차이는 보고만)
- marketplace clone 의 rebase·reset·force, git config 변경
- 컨테이너에 직접 `claude plugin update` 실행(`--sync-env` 가 담당)
