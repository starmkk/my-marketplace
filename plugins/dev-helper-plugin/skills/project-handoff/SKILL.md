---
name: project-handoff
description: "세션·마일스톤 작업을 다른 conversation / `/clear` 이후 / 다른 작업자에게 인계할 때, 여러 repo 에 걸친 변경을 넘길 때, Claude Design 시안이 도착했을 때 — `docs/superpowers/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` 토픽 handoff 파일을 작성한다. 사용자가 '핸드오프 / 진행상황 정리 / 다음 세션 인계 / `/clear` 전에 정리 / handoff 작성 / cross-repo 인계 / 시안 도착' 을 발화하거나, 마일스톤 PASS 직후 · 큰 결정 동결 직후에 사용. 구 resume-handoff / enhanced-handoff 를 대체 — RESUME.md 누적 방식은 폐기하고 토픽별 자기완결 handoff 파일이 SoT."
---

# project-handoff — 토픽별 세션 인계 문서 작성

## 0. 무엇을 만드는가 (그리고 RESUME.md 를 왜 안 쓰는가)

**단일 산출물:** `docs/superpowers/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` — 자기완결 토픽 handoff 파일 1 개. next-turn Claude (다른 conversation / `/clear` 직후 / 다른 작업자) 가 **이 파일 하나만 읽고 즉시 이어서 작업**할 수 있어야 한다.

**RESUME.md 누적 방식 폐기 (구 resume-handoff / enhanced-handoff 대비 핵심 변경):**
- 구 스킬은 `docs/superpowers/RESUME.md` 단일 파일에 모든 마일스톤을 누적하고 sliding window 로 archive 분리했다.
- 실측 결과 RESUME.md 가 1164 라인 / 214KB 로 비대화 → next-turn read 비효율 + 갱신 부담 → 방식 폐기.
- **대체:** 작업 단위(토픽) 마다 `handoffs/` 에 자기완결 파일 1 개를 새로 쓴다. 오래된 handoff 는 그 자리에 그대로 남아 timeline archive 역할 (분리·이동 불필요).

**SoT 구성 (둘 다 next-turn 이 읽음):**
| SoT | 위치 | 성격 |
|---|---|---|
| 토픽 handoff 파일 | `docs/superpowers/handoffs/<date>-<topic>-handoff.md` | git tracked, 공유 SoT, 본 스킬 산출물 |
| SDD ledger | `.superpowers/sdd/progress.md` | repo-local, gitignored, 진행/커밋/carry-forward 상세 (있으면 handoff 헤더에 cross-link) |

**reference 실사용 파일** (골격의 근거 — 새 handoff 는 이들과 정합해야 함):
`docs/superpowers/handoffs/2026-07-02-live-speechlm-streaming-handoff.md` (multi-repo·대형) / `2026-06-24-m-slm6-imported-realtime-remaining-handoff.md` (단일 repo·중형) / `2026-06-25-mnn-3.6.0-upgrade-handoff.md` (인프라 업그레이드형).

---

## 1. 어떤 변형인가 — self-detect

사용자 발화 + repo 상태로 다음 트리거 트리를 적용. 2+ 변형이 동시 신호면 사용자 confirm 후 모두 반영.

| 트리거 신호 | 변형 | 진입 reference |
|---|---|---|
| "마일스톤 PASS / 진행상황 정리 / 다음 세션 인계 / `/clear` 전에 정리" (단일 repo) | **기본 (session)** | 본 SKILL §2~§3 |
| "cross-repo / sibling repo 인계 / 여러 repo 걸친 변경 / includeBuild / vendor 갱신" | **cross-repo** | `references/cross-repo.md` |
| "시안 도착 / Claude Design / `.tar.gz` mockup / inventory 갱신" | **design-mockup** | `references/design-mockup.md` |

세 변형 모두 **최종 산출물은 handoffs/ 토픽 파일** (design-mockup 변형만 추가로 `design-mockups/inventory.md` 1 행 갱신). 변형은 §1 현재 상태 스냅샷의 형태(단일 repo 표 vs multi-repo 표)와 추가 섹션만 다르다.

---

## 2. 작성 절차 (5 step)

1. **토픽·범위 확정 + 파일명 결정** — `<topic>` 은 kebab-case ≤ 30 자 (예: `live-speechlm-streaming`, `mnn-3.6.0-upgrade`). 파일명: `docs/superpowers/handoffs/<오늘 날짜 YYYY-MM-DD>-<topic>-handoff.md`. 날짜는 `date +%Y-%m-%d` 로 확정 (추정 금지).
2. **git 상태 캡처** — `bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/capture-repo-state.sh" [repo2 repo3 ...]` 실행 → §1 스냅샷 표에 붙일 HEAD / branch / 직전 10 commit chain markdown 출력. multi-repo 는 인자로 sibling repo 경로 추가.
3. **표준 골격 채우기** — `${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/assets/handoff-template.md` 골격을 복사 후 placeholder 치환. 필수/선택 섹션 상세는 `references/handoff-anatomy.md` 위임. cross-repo / design-mockup 변형은 해당 reference 의 추가 절차 병행.
4. **commit** — CLAUDE.md §5.1 정책: `dev-helper-plugin:github-commit` 스킬 위임 (직접 `git commit` 금지). §5 참조.
5. **self-review** — `bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/verify-handoff-integrity.sh" <handoff 파일 경로>` 실행 → 문서의 HEAD anchor 가 실제 `git log` 와 일치하는지 검증. 불일치 시 정정 후 재검증.

---

## 3. 표준 골격 (요약)

next-turn 이 이 순서로 읽는다. **필수** 섹션은 모든 handoff 에 존재, **선택** 은 분량·변형에 따라. 상세·예시는 `references/handoff-anatomy.md`.

| 순서 | 섹션 | 필수? | 핵심 |
|---|---|---|---|
| 헤더 | 제목 + 작성일 + branch + 목적 1 줄 + "이 문서만 읽고 진입 가능" 선언 + 진입 순서 안내 + SDD ledger cross-link | **필수** | next-turn 이 어느 섹션부터 읽을지 명시 |
| §0 | 한 줄 요약 | 선택 | 중·대형 handoff 권장 |
| §1 | 현재 상태 스냅샷 (표: branch / HEAD / commit 범위 / 빌드 상태 / prefix / plan·spec·architect refs). multi-repo 면 repo 행 표 | **필수** | capture-repo-state.sh 출력 |
| §2 | 완료 작업 (커밋·검증됨 — "건드리지 말 것") — commit 표 + 근본원인 | **필수** | 무엇이 이미 done 인지 |
| §3 | 핵심 설계 결정 (동결 — 재협의 금지) — D1/D2… 표 + 파일:라인 | 선택 | 대형 handoff. 재협의 낭비 차단 |
| §4 | 핵심 파일 인덱스 | 선택 | 파일 많을 때 |
| §5 | **다음 작업 ★** — 우선순위 순, 각 항목 왜 / 어디(파일:라인) / 주의 | **필수** | next-turn 의 진입점 |
| §6 | 빌드·실행 환경 (매번 prefix) — env 4 변수 + gradle/adb 명령 + appops | **필수** | CLAUDE.md §7 정합 |
| §7 | 함정 (신규 발견) — 증상 / 원인 / fix 표 | 선택 | systematic-debugging 결과만 |
| §8 | 참조 인덱스 — spec / plan / architect-review / ledger 경로 | **필수** | 깊이 파고들 링크 |
| §9 | 재개 절차 (다음 세션) — 번호 스텝 | **필수** | "3. option 2 착수 = §5.1…" 형태 |

**절 번호는 유동** — 위는 논리 순서. 실제 파일은 선택 섹션을 빼면 번호가 당겨진다 (reference 파일들도 §개수가 6~10 으로 제각각). 순서만 지키면 됨.

---

## 4. 결합 필수 plugin / 스킬

본 스킬은 단독 사용 금지. 다음과 결합해야 각 섹션이 정합 상태로 채워진다.

| Plugin / Skill | 결합 시점 | 어떻게 |
|---|---|---|
| **`dev-helper-plugin:github-commit`** | handoff 작성 후 (§2 step 4) | `docs(handoff): 📋 <topic> 인계 — <1 줄>` 별도 commit. 직접 `git commit` 금지 (CLAUDE.md §5.1) |
| **`superpowers:verification-before-completion`** | commit 직전 (§2 step 5) | §1 commit chain / 회귀 수치 / cold-load 가 실측과 정합한지 evidence 기반 검증 |
| **`superpowers:systematic-debugging`** | §7 함정 행 추가 시 | root cause 까지 도달한 디버깅만 증상/원인/fix 로 압축 |
| **`kotlin-audio-architect`** | Kotlin 작업 handoff 의 §8 참조 채울 때 | 협의 결과 `docs/superpowers/architect-reviews/<id>.md` 를 §8 에 인덱싱 (CLAUDE.md §1.4) |
| **`superpowers:writing-plans`** | §5 다음 작업이 신규 마일스톤일 때 | plan 을 `docs/superpowers/plans/<date>-<topic>.md` 에 저장 → §8 인덱싱 |
| **`superpowers:test-driven-development`** | §2 완료 작업의 회귀 카운트 | 회귀 수치는 실측값 (손 카운트 stale 위험) |

---

## 5. 작성 후 검증 체크리스트

commit 직전 모두 확인. 하나라도 fail 이면 보류 → 정정 → 재검증.

- [ ] **파일명 날짜** — `date +%Y-%m-%d` 실측값. 추정한 날짜 아님
- [ ] **§1 HEAD / commit chain** — `git log --oneline -10` 과 정합 (verify-handoff-integrity.sh PASS)
- [ ] **§1 회귀 / cold-load** — 실측값 (`./gradlew :app:testDebugUnitTest` / `am start -W` 결과)
- [ ] **§8 참조 경로** — 모든 링크가 `ls <path>` 로 존재 확인 (spec / plan / architect-review / ledger)
- [ ] **§9 재개 절차** — next-turn 이 그대로 실행 가능한 명령 (진입 site 가 §5 항목과 1:1)
- [ ] **§6 prefix** — env 4 변수 (CLAUDE.md §7) 포함
- [ ] **자기완결성** — 이 파일만 읽고 진입 가능한가? RESUME.md 등 폐기된 외부 SoT 에 의존 안 함
- [ ] **AppleDouble** — 외장 볼륨이면 `find . -name "._*" -type f -delete`
- [ ] **`.gitignore` collateral** — 신규 경로 `git check-ignore -v <path>` 사전 확인

---

## 6. 사용하지 말아야 할 때

- **단순 typo / 1~2 줄 패치** — handoff 가치 없음. 직접 commit
- **작업 진행 중 (TDD step 1~4)** — Step 5 commit 후에만
- **RESUME.md 를 되살리려는 요청** — 폐기된 방식. 토픽 handoff 로 안내
- **사용자가 "handoff 는 건드리지 마" 발화** — 별도 작업 우선

---

## 7. 본 스킬의 위치 (plugin) 와 진화

본 스킬은 `vibe-coding-tools` 마켓플레이스의 **`dev-helper-plugin`** 에 포함된다 (`plugins/dev-helper-plugin/skills/project-handoff/`). 프로젝트별 `.claude/skills-source/` symlink 방식은 폐기 — **글로벌 재사용** (모든 프로젝트에서 handoff 작성) 목적이므로 plugin 배포가 SoT.

- 호출: `/dev-helper-plugin:project-handoff` 또는 트리거 발화
- 스크립트·asset 경로는 `${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/...` 로 해석
- 갱신: `/plugin marketplace update vibe-coding-tools` → `/plugin update dev-helper-plugin`

진화 시 `superpowers:writing-skills` 로 본 SKILL.md 또는 references 수정 → `dev-helper-plugin:github-commit`.
