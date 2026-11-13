---
name: docs-policy
description: >
  문서 정책 상세 — docs/ 카테고리 하위폴더 저장 절차와 표준 카테고리, 메인(≤500줄)+상세 파일
  분할 규칙과 무손실 분할, 계획서는 계약만 기술하는 규칙과 계획서 파일 위치, 일일 dev-log 작성
  시점·기록 항목을 다룬다.
  docs/ 아래에 .md 를 만들거나 옮길 때, 스펙·설계·계획서를 작성하거나 500줄을 넘겨 분할할 때,
  PLAN.md·report.md 위치를 정할 때, dev-log 를 쓰거나 마일스톤을 기록할 때, "문서 저장",
  "문서 분할", "계획서", "dev-log", "개발 로그", "docs/README 인덱스" 가 언급될 때 사용하라.
  하위폴더 필수·500줄 상한·일일 dev-log 원칙은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
---

# 문서 저장 · 문서 크기 · 개발 로그 — 상세

- 전역 `~/.claude/CLAUDE.md` 의 해당 절 원문을 그대로 옮긴 상세판임. 전역 CLAUDE.md 에는
  매 턴 지켜야 할 핵심 규칙과 이 스킬로의 트리거만 남아 있음
- 전역 요약과 어긋나면 이 스킬이 기준임
- 본문의 "the documentation style above" 는 전역 CLAUDE.md §Language & Communication 의
  Documentation style 을 가리킴

## Documentation Storage Policy (`docs/`) (IMPORTANT)

- A `.md` under `docs/` always goes in a category subfolder — no loose top-level files
  (`docs/README.md` index is the only exception)
- **Procedure**: `ls docs/` → save into a matching subfolder; if none matches, create a new
  `kebab-case` (plural preferred) folder and add one line to the `docs/README.md` index
- **Standard categories**: `dev-logs/` (`dev-log-<YYYY-MM-DD>.md`) · `references/` (model/tech
  references, external specs) · `design/` (design & architecture decisions, experiment analysis)
- Convert relative dates to absolute (YYYY-MM-DD)
- **Experiment artifacts (raw data, json, html) go under `experiments/`, not `docs/`** — `docs/`
  holds only analysis and conclusions

## Document Size — Main + Linked Details (IMPORTANT)

Specs, designs, and plans (`.md`) keep a **main file ≤ 500 lines**; anything larger is split.

- **Main**: every heading and section number (`§x.y`) stays, each with a short contract summary
  (names, keys, commands, fixed values others depend on) + a link to its detail file
- **Details**: `<main-stem>/` subfolder next to the main file, one file per section group (not per
  subsection). The detail file is canonical; on conflict it wins. Edit details first, then update
  the main summary in the same change if a contract changed
- **Split losslessly**: move original text verbatim and verify by diff — never shorten by rewriting
- Reference by section number, not line number (line references break on split)
- **Plans describe contracts, not implementations**: owned files, signatures shared across
  modules, test case list (name + one-line assertion), gate commands + expected values, approval
  points. No function or test bodies — those are decided during TDD. Overrides any skill that
  requires complete code in plans. Converting an existing
  code-heavy plan is not a split: extract embedded decisions into contracts first, then drop the
  code (git keeps the original)
- **Plans are written directly** by the main session or a `fable` agent — no plan-writing skill.
  Multi-phase development: `<YYYY-MM-DD>-<topic>-plan.md` in the project's plan folder
  (`docs/dev-plans/<category>/`, else `docs/plans/`). Single task or measurement:
  `experiments/<YYYY-MM-DD>-<topic>/PLAN.md`, results in `report.md` of the same folder
- Exempt: dev-logs (one file per day) and handoffs (self-contained by design)

## Development Log (`docs/dev-logs/`) (IMPORTANT)

Every development task is recorded in `docs/dev-logs/dev-log-<YYYY-MM-DD>.md` — **one file per day,
appended as the work proceeds**, not written once at the end.

- **While developing**: append a section at each milestone (design frozen, module implemented,
  measurement finished, bug root-caused). The reasoning and wrong turns are the highest-value part
- **On completion**: what was implemented, verification result (lint / test / build, actual numbers),
  decisions and rejected alternatives with reasons, remaining items
- Record numbers with the **reproduction command**, mistakes with their **cause**. A disproved
  conclusion stays in place with a disproof note
- Use the documentation style above. Raw artifacts stay under `experiments/`; the dev-log links them
- Add one index line for a new dev-log to `docs/README.md`
