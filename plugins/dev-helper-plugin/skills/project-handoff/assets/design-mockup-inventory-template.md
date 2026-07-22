# Design Mockup Inventory — <PROJECT_NAME>

본 파일은 외부 Claude Design URL 에서 도착한 시안 번들의 단일 SoT 다. `project-handoff` 스킬 `references/design-mockup.md` §4 절차로 갱신.

---

## Inventory 표

| 버전 | 도착일 | 번들 경로 | 시안 line 범위 | 결선 마일스톤 | 결선 commit |
|---|---|---|---|---|---|
| v0.0.1 | YYYY-MM-DD | `docs/superpowers/design-mockups/v0.0.1/` | L1-L120 | M-UI1 | `<hash>` |
| v0.0.2 | YYYY-MM-DD | `docs/superpowers/design-mockups/v0.0.2/` | L121-L260 | M-UI2, M-UI3 | `<hash1>, <hash2>` |
| v0.0.<X> | YYYY-MM-DD | `docs/superpowers/design-mockups/v0.0.<X>/` | L<start>-L<end> | (대기) | (대기) |

---

## 운영 규칙

- **새 행 추가** — 시안 `.tar.gz` 도착 후 `project-handoff` SKILL.md §1 (design-mockup 변형) 진입 → `references/design-mockup.md §3` 절차로 압축 해제 + 본 표 1 행 추가
- **결선 commit 채움** — 결선 마일스톤이 후속 진행되어 본 시안 line range 가 본 repo build/UI 에 반영된 commit hash 를 적재. 별도 commit 가능 (메시지 `docs(handoff): 📥 design-mockups inventory — v0.0.<X> 결선 commit <hash> 적재`)
- **여러 마일스톤 분할 결선** — "결선 마일스톤" + "결선 commit" 셀 모두 쉼표 분리 (예: `M-UI2, M-UI3` / `<hash1>, <hash2>`)
- **시안 line 범위 형식** — 외부 Claude Design 응답에 명시된 절대 라인 번호 그대로. 한 시안이 여러 화면 cover 시 화면별 sub-range 쉼표 분리 (예: `L100-L150 (Library), L151-L200 (Player)`)

---

## Cross-link

- 시안 요청 protocol: `project-handoff/references/design-mockup.md §2`
- 외부 요청 프롬프트 템플릿: `project-handoff/assets/claude-design-request-template.md`
- 결선 마일스톤 site 안내: `app-android-pipeline` Phase 3 — Mockup Wiring
