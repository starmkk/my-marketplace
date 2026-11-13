---
name: code-authoring-review
description: >
  코드 작성 절차 상세 — 구현 전 strategic-code-reviewer 설계 협의와 구현 후 diff 리뷰의 대상·생략
  조건·SendMessage 연속 사용, 서브에이전트 구현분의 리뷰 주체, YAGNI 오적용 금지(산출물 검증 생략
  불가)와 리뷰 결과를 증거로 다루는 수용·기각 기준을 다룬다.
  새 함수·클래스·모듈·스크립트를 만들기 직전, 기존 함수의 시그니처·책임을 바꾸기 직전, 구현을
  끝내고 lint·test 를 돌리기 직전, 서브에이전트가 구현을 끝낸 직후, 리뷰 지적을 수용할지 판단할 때, 검증 단계를 "YAGNI" 로
  미루려 할 때, "설계 협의", "리뷰 반영", "High 지적", "반대 리뷰" 가 언급될 때 사용하라.
  구현 전후 리뷰어 협의 의무와 YAGNI 원칙 한 줄은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
  6원칙 판정 기준 자체는 code-quality-plugin:strategic-code-reviewer 스킬에 있다.
---

# 코드 작성 절차 · 리뷰어 협의 — 상세

- 전역 `~/.claude/CLAUDE.md` 의 해당 절 원문을 그대로 옮긴 상세판임. 전역 CLAUDE.md 에는
  매 턴 지켜야 할 핵심 규칙과 이 스킬로의 트리거만 남아 있음
- 전역 요약과 어긋나면 이 스킬이 기준임

## Code Authoring Procedure — strategic-code-reviewer Consultation (IMPORTANT)

- **Before implementing** a new function/class/module/script, a change to an existing function's
  signature or responsibility, or when unsure whether equivalent code exists → consult the
  `strategic-code-reviewer` agent on the design. Skippable: typo/comment/doc edits, one-line changes
  leaving logic intact, or an explicit user instruction to skip
- **After implementing** → review the diff **before** lint/test, continuing the same reviewer agent
  via `SendMessage` (not a new one). Apply **High** findings; report Medium/Low to the user
- Subagents cannot call the reviewer: for a subagent-implemented change the main session (or a
  workflow stage with `agentType: 'code-quality-plugin:strategic-code-reviewer'`) runs the review,
  and the implementer or fix stage applies the High findings
- The reviewer returns judgment only; it does not modify sources. Bug/security detection uses
  `/code-review` and `/security-review`, not this agent

### YAGNI Misapplication — Never Skip Verification of the Deliverable (IMPORTANT)

YAGNI covers features not yet needed, never checking that what was built is correct.
**Test**: if omitting it lets a wrong result pass silently, it is not YAGNI.

- Gate the shipped artifact in its final packaged form (`A → B → C`: C needs its own gate);
  stateful/iterative pipelines also need continuous accumulation tests
- Case: PyTorch→ONNX verified, ONNX→MNN deferred as "YAGNI" → MNN conversion faults went unseen
  (details: `strategic-code-reviewer` skill §4)

### Reviewer Findings Are Evidence, Not Verdicts

- For significant structural decisions, add a deliberately opposing review (e.g. `codex:rescue`) —
  skip it when the adversarial verification perspectives already cover the same question
- Never accept or dismiss a review wholesale: state which findings are accepted or rejected, each
  with its reason
- Same test as YAGNI Misapplication: accept findings about things that fail silently; defer those
  that merely become inconvenient later (e.g. pre-splitting unwritten code into many modules)
