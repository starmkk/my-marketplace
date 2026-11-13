---
name: subagent-delegation
description: >
  서브에이전트 위임·토큰 비용 정책 상세 — 위임 여부 판단, 검증 묶음(bundle) 구성, 워크플로우
  규모(단계당 4–6개), 에이전트 타입 선택, 난이도별 모델 배정(haiku·sonnet·opus·fable)과 effort,
  프롬프트·턴 길이 제한, 파일 경유 결과 전달, 보고 길이, 장시간 실행 분담을 다룬다.
  Agent 도구로 서브에이전트를 띄우기 직전, Workflow 스크립트를 작성·실행할 때, 에이전트 프롬프트를
  쓸 때, 모델·effort 를 고를 때, 서브에이전트 보고를 검증할 때, "ultracode", "use AgentTool",
  "서브에이전트", "위임", "병렬로", "워크플로우", "토큰 비용" 이 언급될 때 사용하라.
  model 필수 전달·소규모 작업 위임 금지·메인 세션 판정 원칙은 전역 CLAUDE.md 에 있으며 이 스킬은
  그 상세판이다.
---

# 서브에이전트 위임 · 토큰 비용 — 상세

- 전역 `~/.claude/CLAUDE.md` 의 해당 절 원문을 그대로 옮긴 상세판임. 전역 CLAUDE.md 에는
  매 턴 지켜야 할 핵심 규칙과 이 스킬로의 트리거만 남아 있음
- 전역 요약과 어긋나면 이 스킬이 기준임

## Work Execution — Subagents & Token Cost (IMPORTANT)

Cost comes from **agent count × fixed context** and **long agent conversations**, not from output.
Each new agent loads CLAUDE.md, the skill list, and MCP tool schemas (~34k–50k tokens) before doing
anything. (Measured 2026-10-13: a 17-agent review workflow used ~6.8M cache-read tokens to produce
~6k output tokens and no files; one 34-turn reviewer used half of it. Details:
`Nemotron3.dir/docs/references/2026-10-13-agent-token-cost-measurement.md`)

- **Delegate only when the work outweighs the fixed cost.** Small tasks (checking a few source lines,
  editing 1–2 files, recomputing one number) are done in the main session or bundled into another
  agent's task. Run independent large tasks in parallel in a single message
- **`ultracode`, `use AgentTool`, or an explicit workflow request** lifts only the restriction on
  *whether* to delegate. Every sizing, bundling, model, and report rule below still applies
- **Bundle verification**: never one agent per finding. Group by perspective (e.g. numeric
  reproduction / contract & boundary conditions) or by task. Standard shape: implement 1 →
  adversarial verification 2 perspectives → fix 1
- **Workflow size**: 4–6 agents per phase. Before running more than 10 agents in total, consider
  bundling or direct handling first. Re-run an interrupted workflow with `resumeFromRunId`
- **Choose the cheapest agent type**: `Explore` for locating files/symbols; `general-purpose` only
  when editing or executing. Do not `fork` in a long session (it inherits the whole conversation).
  Continue an existing agent with `SendMessage` for follow-up work in the same context
- **Model by difficulty** (default profile; the `dev-helper-plugin:model-profile` skill, invoked only
  on user request, replaces this assignment for the session) —
  `haiku`: mechanical substitution, file listing, format conversion ·
  `sonnet`: porting, non-core implementation (glue/wiring, CLI I/O, build files, JNI/Java
  boilerplate), tests, peripheral scripts (build, data prep), doc drafts, source
  cross-checks, number recomputation · `opus`: root cause analysis, conflicting evidence,
  adversarial review · `fable`: plans and design decisions, **core-logic implementation** (a
  module's central algorithm/public API, with its TDD tests), and escalation when opus produced an
  unreliable or conflicting result or a wrong verdict is very costly
  - Work whose mistake would pass silently (e.g. archive export rules in a build file) is
    core-logic regardless of file type
  - Pass `model` on every Agent call and workflow stage (omitted = inherits the main session model)
  - Set `effort: "low"` for mechanical haiku/sonnet tasks; keep the default for judgment work
- **Keep agent prompts and turns short**
  - A prompt holds only what the agent acts on — task, input paths, done criterion; no session
    history or background
  - Subagents do only what their prompt says; a user message that surfaces mid-run is left to the
    main session
  - Never paste CLAUDE.md rules into prompts (auto-injected); name only the needed rule or skill
  - Give long-running investigators the exact files, line ranges, and questions to answer
    (e.g. "read only design §6.2 (lines 761-819) and `hf_runner.py:51-106`, answer Q1–Q3")
  - Reference large docs by section/line range, never whole
  - Subagents skip Serena `initial_instructions` and unlisted skills unless the task needs symbol
    navigation or that skill
- **Pass results through files, not prompts**: a stage writes `experiments/<date>-<topic>/`
  (`PLAN.md`, `report.md`); the next stage gets the path plus a few summary lines. In workflow
  scripts, interpolate a full prior result only in the final fix stage that must judge it
- **Short reports**: conclusion / verified / not verified / artifact paths, ≤ 30 lines; details in
  files. Use `schema` in workflows
- **Long runs**: for GPU sweeps or long device measurements, the agent prepares a small smoke run and
  the command; the main session launches the real run in the background. Agents never poll
- **The main session decides what is correct.** A subagent report is evidence; confirm its numbers
  and verdicts with a reproduction command or the original source (wrong comparison points have
  produced wrong conclusions before). Never assign judgment-critical work to a lower tier
- A project CLAUDE.md that restricts subagent usage further takes precedence
