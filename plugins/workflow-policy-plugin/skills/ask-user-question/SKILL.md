---
name: ask-user-question
description: >
  AskUserQuestion 사용 규칙 상세 — 설명을 먼저 출력하고 같은 응답에서 호출하는 순서, 항목별로
  설명해야 할 네 가지(무엇을·왜 지금·선택지별 변화·추천과 이유), 한 번에 묶어 묻기(최대 4문항),
  묻지 말아야 할 것(관례적 기본값·코드로 확인 가능한 사실)을 다룬다.
  AskUserQuestion 을 호출하기 직전, 사용자에게 선택지·결정·승인을 물으려 할 때, 질문 설명문을
  작성할 때, "사용자에게 물어봐", "선택지", "결정 필요", "승인 요청" 이 언급될 때 사용하라.
  설명 출력 후 같은 응답에서 호출한다는 원칙은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
---

# 사용자에게 묻기 (AskUserQuestion) — 상세

- 전역 `~/.claude/CLAUDE.md` 의 해당 절 원문을 그대로 옮긴 상세판임. 전역 CLAUDE.md 에는
  매 턴 지켜야 할 핵심 규칙과 이 스킬로의 트리거만 남아 있음
- 전역 요약과 어긋나면 이 스킬이 기준임

## Asking the User (`AskUserQuestion`) (IMPORTANT)

Goal: remove the extra round-trip where the user has to ask what each question means.

- **Print the explanation first, then call `AskUserQuestion` in the same response** — never end the
  turn with the explanation alone
- **For each item, explain**: what is being decided (plain language, no assumed background) · why it
  must be decided now (what it blocks) · what each option changes (files, cost/time, reversibility) ·
  the recommendation and why
- **Ask once**: batch all items into one call (max 4 questions); number and title the explanations
  to match the questions
- Do not ask about conventional defaults or facts verifiable in the code — state the chosen value
  in the explanation and proceed
