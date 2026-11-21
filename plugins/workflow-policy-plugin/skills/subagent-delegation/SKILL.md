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
Each new agent loads CLAUDE.md, the skill list, and MCP tool schemas before doing anything.
Measured first-request size (median, 2026-11-10~17): Agent-tool `general-purpose` 46.6k (N=61) ·
`workflow-subagent` 48.3k · `Explore` 26.6k · `strategic-code-reviewer` 32.7k ·
`wf-worker` 16.5k · `wf-reader` 9.9k~13.3k · `web-fetch` 3.8k.
(Measured 2026-10-13: a 17-agent review workflow used ~6.8M cache-read tokens to produce
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
- **File ownership per stage**: each editing stage's prompt lists the files it owns. The stage runs
  `git diff` on them before editing; a change it did not make, or one outside its list, is reported
  rather than edited or reverted (2026-11-14~18: concurrent edits duplicated an item, rolled back)
- **Agent tool: always pass `subagent_type`** (an omitted one is denied by this plugin's
  `agent_type_guard.py` hook) and choose the cheapest type that can do the work
  - edit/execute → `workflow-policy-plugin:wf-worker`; read/review/verify/locate files or
    symbols → `workflow-policy-plugin:wf-reader` (`Explore` costs 2.0–2.7x as much); URL →
    `web-fetch`; a specialist agent where its rules are the point
  - `general-purpose` only when the task needs MCP, WebSearch, or Skill tools
  - Do not `fork` in a long session (it inherits the whole conversation). Continue an existing
    agent with `SendMessage` to the `agentId` from its spawn result for follow-up work in the
    same context
- **Agent lifecycle — omit `name` unless a live team is the point** (measured 2026-11-19 with
  agent teams on, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`)
  - Without `name`: the background agent ends after its report (`completed`), and `SendMessage`
    to its `agentId` resumes it with its context — this is how a reviewer is kept from design
    consult to diff review. Write the `agentId` into the step's notes file so it survives
    context compaction
  - With `name`: it becomes a teammate (with `teammateMode: "tmux"`, a separate process in a tmux
    pane) that idles after its report and never exits by itself — seen: 44 min idle at ~390 MB
    RSS, still listed as running after the milestone and the handoff; the team registries hold
    541 such named reviewers, critics and workers left since 07-30. `TaskStop` ends it, but the
    name is no longer reachable afterwards (no resume)
  - Reuse of a named one: an idle teammate makes no requests (39 min idle: 0) and continues with
    its context on `SendMessage(to: "<name>")`, so keep it while this session will reuse it.
    Stop it once it will not be reused here: save the result to a file, `TaskStop({task_id:
    "<name>"})` from the lead, then check `ListAgents`. In tmux mode a stopped teammate cannot be
    revived (the agent-teams docs say in-process mode restores it on the next message). Stop it
    before ending the session or `/clear` — a new session cannot address it. Keeping it alive
    saves no tokens: a reuse after a long idle re-reads its whole context (the docs give a 5-min
    default cache for in-process teammates), the same as resuming an unnamed subagent
  - Context: neither a teammate nor a subagent inherits the lead's conversation (measured: first
    request 12k–42k tokens vs ~600k for the lead; docs: "The lead's conversation history does not
    carry over"). They start from the agent definition, CLAUDE.md, git status and the spawn
    prompt, so the prompt carries the work basis and task-specific context. Only `fork` inherits
  - The `agent_type_guard.py` hook adds a model-only notice when a named Agent is spawned with
    agent teams on
- **Workflow stages: always pass `agentType`.** Omitted = `workflow-subagent`, which loads every tool
  definition plus the whole skill list (~48k tokens before the task; measured 2026-11-17: 468 agents,
  326M input-equivalent tokens in 30 days, ~80% fixed overhead — `claude-insights`
  `experiments/2026-11-17-workflow-tokens/report.md`). The Workflow API has no per-call tool limit,
  so a lean agent definition is the only lever
  - implement/fix stages → `workflow-policy-plugin:wf-worker` (Bash·Read·Edit·Write);
    review/investigate/verify stages → `workflow-policy-plugin:wf-reader` (Bash·Read); keep a
    specialist type (e.g. `code-quality-plugin:strategic-code-reviewer`) where its rules are the point
  - Write the plugin prefix. In a Workflow an unprefixed or unknown `agentType` fails with
    `agent type ... not found` (seen 2026-11-17; a process started before the plugin install also
    fails — restart it); in a skill's `agent:` frontmatter it silently falls back to the full
    toolset (seen with `mnn-source-inspector`)
  - A stage that needs a skill gets the SKILL.md path in its prompt and Reads it — giving the Skill
    tool brings the whole ~14k skill list. `schema` still works (the harness adds StructuredOutput)
- **Fewer, fuller requests** (cost grows with requests × context): 91% of workflow requests carried
  one tool call and 56% of Bash calls were single-file reads — issue independent reads in one message
  or one Bash that prints several files/ranges. Split work that would pass ~40 requests into stages
  with a short file hand-off (agents over 40 requests were 20% of agents and 46% of cost)
- **No command over 5 minutes inside an agent**: the prompt cache expires after 5 idle minutes and
  the next request rewrites the whole context (128 misses, 7.3% of workflow cost). Long builds/tests
  run from the main session in the background, or are split
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
    navigation or that skill. One that does need symbols calls `initial_instructions` once for its
    Serena session id, then `activate_project` with its worktree path and that id — Serena 2.1
    requires both `project` and `session`, and the id is not in the server instructions (Serena
    failures in voiceguard were all "No active project"). If that fails, it says so once and uses
    grep/Read
  - In a worktree session, temp scripts and outputs go under that worktree's `experiments/` — the
    original checkout's scratchpad path is outside the isolation boundary and is refused
- **Pass results through files, not prompts**: a stage writes `experiments/<date>-<topic>/`
  (`PLAN.md`, `report.md`); the next stage gets the path plus a few summary lines. In workflow
  scripts, interpolate a full prior result only in the final fix stage that must judge it
  - Name the exact output directory in the prompt. If the harness refuses a subagent's `.md` write
    (seen 2026-11-17), the subagent writes `.json`/`.txt` or returns the text, and the main session
    saves `report.md`
- **Short reports**: conclusion / verified / not verified / artifact paths; details in files (a
  detail file past 500 lines is split per Document Size). Use `schema` in workflows
- **Long runs**: for GPU sweeps or long device measurements, the agent prepares a small smoke run and
  the command; the main session launches the real run in the background. Agents never poll
  - Waiting (main session and agents): launch with `run_in_background` and wait for its completion
    notification — no `sleep N; …` chains or `until`/`pgrep` loops in Bash. A condition with no
    notification goes to `Monitor`. While waiting, report in one line what is running and its
    expected end time (seen 2026-11-20: 7 wait failures on aip1, `sleep 45` blocked on aip2, and a
    user asking at 17:30 what the session was waiting for)
- **The main session decides what is correct.** A subagent report is evidence; confirm its numbers
  and verdicts with a reproduction command or the original source (wrong comparison points have
  produced wrong conclusions before). Never assign judgment-critical work to a lower tier
- A project CLAUDE.md that restricts subagent usage further takes precedence
