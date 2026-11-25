---
name: update-plugins
description: >
  vibe-coding-tools marketplace plugin 을 호스트에서 최신으로 갱신하고 voiceguard 컨테이너까지 즉시
  반영한 뒤 결과 표를 내는 스킬 — 호스트 갱신은 claude CLI, 컨테이너 반영은 claude-insights
  `run_reports.py --sync-env` 에 위임. "plugin 업데이트", "plugin 갱신", "모든 plugin 최신으로",
  "marketplace update", "plugin 설치·업데이트", "컨테이너에도 plugin 반영" 이 언급될 때 사용하라.
  일일 cron 의 env_sync 를 기다리지 않고 바로 반영할 때 쓴다. 원본 작업 사본의 미push 커밋 점검(확인 후
  gh push)과 컨테이너 project scope 갱신을 포함한다.
---

# update-plugins — marketplace plugin 갱신·컨테이너 반영

호스트를 먼저 올린다. `--sync-env` 는 호스트↔컨테이너 버전이 **다를 때만** 컨테이너를 갱신하므로,
호스트가 구버전이면 아무것도 하지 않는다. 컨테이너 갱신 로직(EXDEV 대체 포함)은 claude-insights
`scripts/reports/env_sync.py` 가 정본 — 이 스킬에 복제하지 않는다.

## 0. 준비

- claude CLI: `command -v claude || ls ~/.local/bin/claude` — 없으면 중단하고 보고
- claude-insights 저장소: `CLAUDE_INSIGHTS_DIR` → `~/work/claude/claude-insights` 중 먼저 있는 곳.
  없으면 1~3 단계(호스트)만 하고 컨테이너 반영은 "저장소 없음 — 미반영" 으로 보고
- 컨테이너(voiceguard) 안에서 실행 중이면 호스트 단계를 하지 않고 호스트에서 실행하라고 안내만 함
- 갱신 전 버전 기록: `claude plugin list` 에서 `@vibe-coding-tools` 항목의 이름·Version·Scope

## 1. 원본 미push 점검(호스트)

marketplace 갱신은 GitHub 에 올라간 커밋만 받는다 — 로컬 원본의 미push 커밋은 조용히 빠진다(2026-11-21
workflow-policy 1.0.9 누락 사례).

- 원본 작업 사본: `MARKETPLACE_SRC_DIR` → `~/work/research/my-marketplace` 중 먼저 있는 곳. 없으면 건너뜀
- 원격은 `~/.claude/plugins/known_marketplaces.json` 의 `vibe-coding-tools.source.repo` 로
  `https://github.com/<repo>.git` — 작업 사본의 `origin` 이 SSH 별칭이면 샌드박스에서 해석되지 않으므로 HTTPS 사용
- `git ls-remote <URL> refs/heads/main` 해시와 로컬 `HEAD` 비교
  - 같음 → 다음 단계
  - 원격 해시가 `HEAD` 의 조상(로컬이 앞섬) → `git log --oneline <원격>..HEAD` 를 보여 주고 push 여부 확인.
    승인 시 `gh auth status` 확인 뒤 `git push <URL> HEAD:main`(gh 자격증명), 이어서
    `git fetch <URL> main:refs/remotes/origin/main` 로 추적 ref 갱신
  - 미커밋 변경이 있거나 갈라짐(원격에만 있는 커밋) → push 하지 않고 보고(커밋은 github-commit, merge·rebase 는
    사용자 결정)
  - push 를 거절·보류하면 표 아래에 "미push 커밋 n개는 이번 갱신에서 제외" 로 표기

## 2. marketplace 갱신(호스트)

- `claude plugin marketplace update vibe-coding-tools`
- 출력에 `EXDEV` 가 있을 때만 `git -C ~/.claude/plugins/marketplaces/vibe-coding-tools pull --ff-only`
  로 대체. 그 밖의 실패·fast-forward 불가는 중단하고 원문 마지막 몇 줄을 보고(rebase·reset 금지)

## 3. plugin 갱신(호스트)

- 0 에서 기록한 user scope 항목마다 `claude plugin update <이름>@vibe-coding-tools` — **한 번에 하나씩
  순차 실행**. 병렬이면 `installed_plugins.json` 쓰기 경합으로 "updated" 출력에도 기록이 유실되고
  `--sync-env` 가 차이 없음으로 판정함(2026-11-25 dev-helper 1.0.29 실측). 끝나면 그 파일의 user 버전을 출력과 대조
- marketplace 에 있는데 설치되지 않은 plugin 은 설치하지 않고 표에 "미설치" 로만 표시(설치는 사용자 결정)
- 호스트 project scope 설치분은 갱신하지 않고 표에 경로·버전만 표시 — 해당 프로젝트에서 갱신할지 사용자에게 알림

## 4. 컨테이너 반영

- 저장소에서 `.venv/bin/python scripts/run_reports.py --sync-env`
  - 출력의 `동기화 메모` 에 `EXDEV … git pull --ff-only 로 대체 갱신` 이 있으면 정상(대체 경로)
  - `갱신 실패`·`대체 실패` 줄이 있으면 실패로 보고
- 확인: `.venv/bin/python scripts/run_reports.py --sync-env --dry-run` 출력 중 **plugin 줄만** 판정
  - `plugin 버전 갱신: 없음` 과 `plugin 활성 집합 차이 …: 없음` 이면 일치
  - `CLAUDE.md 동기화` 등 다른 줄은 plugin 판정에 쓰지 않음(별도 항목으로만 표시)
  - 4 의 첫 실행 출력에 나오는 `<이름> (A ↔ B)` 는 **갱신 전** 차이 기록이다 — dry-run 결과로 판정
- 컨테이너 project scope: `--sync-env` 는 user scope 만 맞춘다. `/workspace/.claude/settings.json` 의 project
  scope 설치분(2026-11-21 확인)은 직접 갱신
  - `docker exec -w /workspace voiceguard /root/.local/bin/claude plugin list` 에서
    `Scope: project` 항목이 같은 plugin 의 user 버전보다 낮으면 항목마다 순차로
    `docker exec -w /workspace voiceguard /root/.local/bin/claude plugin update <이름>@vibe-coding-tools --scope project`
  - 실패하면 원문 마지막 줄을 보고(EXDEV 대체는 하지 않음 — 2026-11-21 실측 성공)

## 5. 보고

| plugin | 이전 | 이후(호스트) | 이후(컨테이너) | scope | 조치 |
|---|---|---|---|---|---|

- 컨테이너 project scope 는 scope 열을 `project(/workspace)` 로 한 별도 행
- 조치: 갱신 · 변경 없음 · 미설치 · project scope(미갱신 — 호스트) · 실패(사유)
- 1 에서 push 했으면 push 범위(`<원격>..<HEAD>`)를, 제외했으면 미push 커밋 수를 표 아래 한 줄로
- 컨테이너 버전은 `docker exec -w /workspace voiceguard /root/.local/bin/claude plugin list` 로 확인한 값
- 끝에 한 줄: 실행 중인 claude(호스트·컨테이너)는 `/reload-plugins` 또는 재시작 후 적용됨 —
  `/clear` 는 같은 프로세스라 반영되지 않음(2026-11-22 voiceguard 세션이 1.0.26 설치 뒤 1.0.24 로드)

## 하지 않는 것

- plugin 활성화·비활성화 변경(활성 집합 차이는 보고만)
- marketplace clone 의 rebase·reset·force, git config 변경
- 사용자 확인 없는 push, force push, 원본 작업 사본의 merge·rebase
- 컨테이너 user scope 에 직접 `claude plugin update` 실행(`--sync-env` 가 담당) — project scope 만 4 에서 직접 갱신
