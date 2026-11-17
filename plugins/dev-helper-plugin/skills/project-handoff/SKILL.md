---
name: project-handoff
description: "세션·마일스톤 작업을 다른 conversation / `/clear` 이후 / 다른 작업자에게 인계할 때, 여러 repo 에 걸친 변경을 넘길 때, Claude Design 시안이 도착했을 때 — `docs/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` 토픽 handoff 파일을 작성한다. 사용자가 '핸드오프 / 진행상황 정리 / 다음 세션 인계 / `/clear` 전에 정리 / handoff 작성 / cross-repo 인계 / 시안 도착' 을 발화하거나, 마일스톤 PASS 직후 · 큰 결정 동결 직후에 사용. 'handoff 읽고 이어서 / 작업 재개' 로 handoff 를 읽고 시작할 때는 §8 재개 모드(동기화 점검)를 따른다. 구 resume-handoff / enhanced-handoff 를 대체 — RESUME.md 누적 방식은 폐기하고 토픽별 자기완결 handoff 파일이 SoT."
---

# project-handoff — 토픽별 세션 인계 문서 작성

## 0. 무엇을 만드는가 (그리고 RESUME.md 를 왜 안 쓰는가)

**단일 산출물:** `docs/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` — 자기완결 토픽 handoff 파일 1 개. next-turn Claude (다른 conversation / `/clear` 직후 / 다른 작업자) 가 **이 파일 하나만 읽고 즉시 이어서 작업**할 수 있어야 한다.

> **경로 규약:** 신규 handoff 는 항상 `docs/handoffs/` 에 쓴다. 구 경로 `docs/superpowers/handoffs/` 는 구 프로젝트용 **읽기 전용 fallback** (기존 handoff 조회·목록·검증 시에만 확인) 이며 절대 쓰지 않는다. 파일 이전(migration) 은 하지 않는다.

**RESUME.md 누적 방식 폐기 (구 resume-handoff / enhanced-handoff 대비 핵심 변경):**
- 구 스킬은 `docs/superpowers/RESUME.md` 단일 파일에 모든 마일스톤을 누적하고 sliding window 로 archive 분리했다.
- 실측 결과 RESUME.md 가 1164 라인 / 214KB 로 비대화 → next-turn read 비효율 + 갱신 부담 → 방식 폐기.
- **대체:** 작업 단위(토픽) 마다 `handoffs/` 에 자기완결 파일 1 개를 새로 쓴다. 오래된 handoff 는 그 자리에 그대로 남아 timeline archive 역할 (분리·이동 불필요).

**SoT 구성 (둘 다 next-turn 이 읽음):**
| SoT | 위치 | 성격 |
|---|---|---|
| 토픽 handoff 파일 | `docs/handoffs/<date>-<topic>-handoff.md` | git tracked, 공유 SoT, 본 스킬 산출물 |
| (있으면) 프로젝트 ledger | 프로젝트가 정한 경로 | 진행/커밋/carry-forward 상세 (있으면 handoff 헤더에 cross-link) |

**reference 실사용 파일** (골격의 근거 — 새 handoff 는 이들과 정합해야 함):
`docs/handoffs/2026-07-02-live-speechlm-streaming-handoff.md` (multi-repo·대형) / `2026-06-24-m-slm6-imported-realtime-remaining-handoff.md` (단일 repo·중형) / `2026-06-25-mnn-3.6.0-upgrade-handoff.md` (인프라 업그레이드형).

**언제 쓰나 (시점):** 마일스톤 경계(게이트 통과·커밋 직후)에 쓴다. handoff 작성의 요청당 비용 ≈ 호출 시점 문맥 크기이므로 (실측: 30일 중앙 536k vs 2026-11-17 표본 232k~256k) 문맥이 커질 때까지 미루지 않는다.

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

1. **사실 수집 (Bash 1회) + 파일명 결정** — `bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/collect-handoff-facts.sh" [repo2 repo3 ...]` 실행 → 오늘 날짜·파일명 접두, §1 스냅샷 표(HEAD / branch / 직전 10 commit chain markdown — `capture-repo-state.sh` 위임), 미커밋 변경, 최근 handoff 5개를 한 번에 출력. multi-repo 는 인자로 sibling repo 경로 추가. `<topic>` 은 kebab-case ≤ 30 자 (예: `live-speechlm-streaming`, `mnn-3.6.0-upgrade`). 파일명: `docs/handoffs/<오늘 날짜 YYYY-MM-DD>-<topic>-handoff.md` — 날짜는 스크립트 출력값 (추정 금지).
   - **독립 사실 확인은 Bash 1회 또는 병렬 호출로 묶는다** — 순차 `grep`·`sed`·`cat`·`ls` 를 요청마다 하나씩 보내지 않는다 (근거: 30일 35회 handoff 작성의 요청 수 중앙 7, 10회 이상 12건이 9.2M IET — 초과 요청은 순차 grep·sed·cat·ls).
2. **표준 골격 채우기(§10 시작 프롬프트 포함)** — `${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/assets/handoff-template.md` 골격을 복사 후 placeholder 치환. 필수/선택 섹션 상세는 `references/handoff-anatomy.md` 위임. cross-repo / design-mockup 변형은 해당 reference 의 추가 절차 병행. **§1·§10 의 HEAD = 작성 기준 HEAD = handoff 커밋 직전 HEAD** (handoff 커밋 자체의 해시는 적지 않는다).
3. **실행 중 작업 정리** — 이 세션이 띄운 백그라운드 서브에이전트·워크플로·백그라운드 명령을 확인한다(`ListAgents`, 백그라운드 작업 목록). 남아 있으면 항목별로 종료할지 AskUserQuestion 1회로 묻고, 종료한 것은 종료하고 남기는 것은 handoff §1 에 `실행 중: <이름·목적·결과 경로>` 로 적는다. 다음 세션이 같은 빌드 디렉터리·단말을 쓰다 충돌하는 것을 막기 위함(관측: 새 세션 시작 뒤에도 이전 세션의 리뷰 에이전트 2개가 계속 실행)
4. **self-review (commit 전)** — `bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/verify-handoff-integrity.sh" <handoff 파일 경로>` 실행 → HEAD anchor(§1 스냅샷 ↔ `git HEAD`)·§10 시작 프롬프트·§8 참조 경로 존재·파일명 날짜를 검사. `[FAIL]` 이면 정정 후 재검증 (`[WARN]` 은 확인만).
5. **commit** — 전역 CLAUDE.md Git Commit Rules: `dev-helper-plugin:github-commit` 스킬 위임 (직접 `git commit` 금지). §5 참조. 커밋 직후 verify 를 다시 돌려도 통과한다 (anchor = `HEAD^` 이고 HEAD 가 이 handoff 를 포함한 커밋 → `[OK](커밋 후 검증)`). 그 뒤 handoff 와 무관한 커밋이 생기면 FAIL — §1·§10 HEAD 를 정정.

---

## 3. 표준 골격 (요약)

next-turn 이 이 순서로 읽는다. **필수** 섹션은 모든 handoff 에 존재, **선택** 은 분량·변형에 따라. 상세·예시는 `references/handoff-anatomy.md`.

| 순서 | 섹션 | 필수? | 핵심 |
|---|---|---|---|
| 헤더 | 제목 + 작성일 + branch + 목적 1 줄 + "이 문서만 읽고 진입 가능" 선언 + 진입 순서 안내 + (있으면) 프로젝트 ledger cross-link | **필수** | next-turn 이 어느 섹션부터 읽을지 명시 |
| §0 | 한 줄 요약 | 선택 | 중·대형 handoff 권장 |
| §1 | 현재 상태 스냅샷 (표: branch / HEAD / commit 범위 / 빌드 상태 / prefix / plan·spec refs). multi-repo 면 repo 행 표 | **필수** | collect-handoff-facts.sh 출력 |
| §2 | 완료 작업 (커밋·검증됨 — "건드리지 말 것") — commit 표 + 근본원인 | **필수** | 무엇이 이미 done 인지 |
| §3 | 핵심 설계 결정 (동결 — 재협의 금지) — D1/D2… 표 + 파일:라인 | 선택 | 대형 handoff. 재협의 낭비 차단 |
| §4 | 핵심 파일 인덱스 | 선택 | 파일 많을 때 |
| §5 | **다음 작업 ★** — 우선순위 순, 각 항목 왜 / 어디(파일:라인) / 주의 | **필수** | next-turn 의 진입점 |
| §6 | 빌드·실행 환경 (매번 prefix) — 프로젝트 빌드·실행 prefix + 빌드·테스트 명령 | **필수** | 프로젝트 CLAUDE.md 정합 |
| §7 | 함정 (신규 발견) — 증상 / 원인 / fix 표 | 선택 | systematic-debugging 결과만 |
| §8 | 참조 인덱스 — spec / plan / (있으면) 프로젝트 ledger 경로 (repo 루트 기준 또는 절대 경로) | **필수** | 깊이 파고들 링크 |
| §9 | 재개 절차 (다음 세션) — 번호 스텝 | **필수** | "3. option 2 착수 = §5.1…" 형태 |
| §10 | **다음 세션 시작 프롬프트** — 다음 사람이 assistant 의 **첫 입력으로 그대로 붙여넣는** 텍스트 블록 | **필수** | handoff 경로 + 진입 스텝 + 실행 위치/HEAD + 계획 순서 + 위임·리뷰·커밋 규칙 + 동결 결정 + 환경 확인 커맨드. 상세 `references/handoff-anatomy.md` §10 |

**§9 와 §10 의 관계**: §9 는 사람이 읽고 따라가는 번호 스텝, §10 은 그 스텝을 **assistant 에게 그대로 명령하는 복붙용 원문**이다. 둘 다 있어야 한다 — §9 만 있으면 next-turn 이 handoff 를 스스로 해석하며 위임 모델·커밋 규칙·동결 결정을 빠뜨린다(실측: §10 없이 작성된 handoff 는 다음 세션이 지침 절반을 되물었다).

**절 번호는 유동** — 위는 논리 순서. 실제 파일은 선택 섹션을 빼면 번호가 당겨진다 (reference 파일들도 §개수가 6~10 으로 제각각). 순서만 지키면 됨.

---

## 4. 결합 필수 plugin / 스킬

본 스킬은 단독 사용 금지. 다음과 결합해야 각 섹션이 정합 상태로 채워진다.

| Plugin / Skill | 결합 시점 | 어떻게 |
|---|---|---|
| **`dev-helper-plugin:github-commit`** | handoff 작성 후 (§2 step 5) | `docs(handoff): 📋 <topic> 인계 — <1 줄>` 별도 commit. 직접 `git commit` 금지 (전역 CLAUDE.md Git Commit Rules) |
| **실측 검증 (CLAUDE.md Testing & QA)** | commit 직전 (§2 step 4) | §1 commit chain / 회귀 수치 / cold-load 가 실측과 정합한지 evidence 기반 검증. §1 HEAD = 작성 기준 HEAD = 커밋 직전 HEAD |
| **root cause 분석 (opus 위임 가능)** | §7 함정 행 추가 시 | root cause 까지 도달한 디버깅만 증상/원인/fix 로 압축 |
| **계획서 직접 작성 (메인 세션 또는 fable, CLAUDE.md Plans 규칙)** | §5 다음 작업이 신규 마일스톤일 때 | plan 을 전역 CLAUDE.md 계획서 위치(`docs/dev-plans/<category>/`, 없으면 `docs/plans/`)의 `<date>-<topic>-plan.md` 에 저장 → §8 인덱싱 |
| **TDD (CLAUDE.md Testing & QA)** | §2 완료 작업의 회귀 카운트 | 회귀 수치는 실측값 (손 카운트 stale 위험) |

---

## 5. 작성 후 검증 체크리스트

commit 직전 모두 확인. 하나라도 fail 이면 보류 → 정정 → 재검증. **(스크립트)** 표기 항목은 `verify-handoff-integrity.sh` 가 검사하므로 손으로 다시 확인하지 않는다.

- [ ] **파일명 날짜 (스크립트)** — `date +%Y-%m-%d` 실측값. 추정한 날짜 아님 (다르면 WARN)
- [ ] **실행 중 작업** — 백그라운드 에이전트·워크플로·명령을 종료했거나 §1 에 `실행 중` 으로 기록했는가
- [ ] **§1 HEAD (스크립트) / commit chain** — HEAD 는 커밋 직전 HEAD, chain 은 collect-handoff-facts.sh 출력 그대로
- [ ] **§1 회귀 / cold-load** — 실측값 (`<회귀 시험 명령>` / `<단말 시험 명령>` 결과. 예: Android 는 `./gradlew :app:testDebugUnitTest` / `am start -W`)
- [ ] **§8 참조 경로 (스크립트)** — 백틱·링크 경로가 실제로 있는가. repo 루트 기준 상대 경로 또는 절대 경로로 적는다 (모듈·sibling repo 기준 경로는 스크립트가 판정하지 못하거나 FAIL)
- [ ] **§9 재개 절차** — next-turn 이 그대로 실행 가능한 명령 (진입 site 가 §5 항목과 1:1)
- [ ] **§10 시작 프롬프트 (heading·경로·HEAD 존재는 스크립트)** — ```text 블록 1개. 자기 파일 경로·HEAD hash·`§9 의 N번부터` 진입 스텝·환경 확인 커맨드가 들어 있고, 사용자 규칙(실행 위치·워크트리 금지·위임 모델·리뷰·lint·커밋 스킬·push 금지·add 제외)을 빠짐없이 옮겼는가 (verify-handoff-integrity.sh 가 heading·경로·HEAD 존재를 검사)
- [ ] **§6 prefix** — 프로젝트 빌드·실행 prefix (프로젝트 CLAUDE.md) 포함
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

## 8. 재개 모드 — handoff 를 읽고 세션을 시작할 때

handoff 를 읽고 이어서 작업하라는 요청(예: "handoff 를 읽고 이어간다")이면 첫 작업 전에 아래를 Bash 1회로 확인하고 결과를 3줄 이내로 보고한다.

1. **동기화**: `git status -sb`(브랜치·ahead/behind) · `git log --oneline -1` 을 handoff §1 HEAD 와 비교 · `bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/verify-handoff-integrity.sh" <handoff 파일 경로>` (작성 때와 같은 규칙으로 판정) · 원격이 있으면 `git fetch -q` 후 behind 수
   - §1 HEAD = `HEAD^` 이고 HEAD 가 이 handoff 를 포함한 커밋이면 동기화 정상 (verify 의 `[OK](커밋 후 검증)`)
   - 재개 모드에서 verify 의 `[FAIL]`·정정 안내는 **보고 항목**이다 — 지난 handoff 를 고치지 않는다(HEAD 가 앞섬·사라진 scratchpad/`experiments/` 경로는 흔한 정상 상태)
   - HEAD 가 handoff 보다 뒤 → `git pull --ff-only` 가능 여부를 보고하고 사용자 확인 후 실행
   - HEAD 가 앞섬 → 그 사이 커밋 제목을 보여 주고 §5 다음 작업이 이미 끝났는지 대조
2. **이전 세션의 미커밋 변경**: `git status --porcelain` 이 비어 있지 않으면 파일 목록을 보여 주고, 체크포인트 커밋 후 시작할지 묻는다(새 작업과 섞지 않음)
3. **진입**: §10 시작 프롬프트의 규칙(실행 위치·위임 모델·리뷰·커밋)을 이번 세션 규칙으로 따르고 §9 의 지정 스텝부터 시작

### 체크포인트 커밋 규칙

- 게이트(lint·test·실측)를 통과한 마일스톤마다 그 단계에서 바꾼 파일만 `dev-helper-plugin:github-commit` 으로 커밋한 뒤 다음 단계로 넘어간다
- 세션을 끝내거나 handoff 를 쓰기 전에 미커밋 변경이 남지 않게 한다. 남겨야 하면 handoff §1 에 파일과 이유를 적는다
- 다른 세션이 같은 저장소를 쓰는 중이면(`git status` 에 내 작업이 아닌 변경) 그 파일은 스테이징하지 않는다

---

## 7. 본 스킬의 위치 (plugin) 와 진화

본 스킬은 `vibe-coding-tools` 마켓플레이스의 **`dev-helper-plugin`** 에 포함된다 (`plugins/dev-helper-plugin/skills/project-handoff/`). 프로젝트별 `.claude/skills-source/` symlink 방식은 폐기 — **글로벌 재사용** (모든 프로젝트에서 handoff 작성) 목적이므로 plugin 배포가 SoT.

- 호출: `/dev-helper-plugin:project-handoff` 또는 트리거 발화
- 스크립트·asset 경로는 `${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/...` 로 해석
- 갱신: `/plugin marketplace update vibe-coding-tools` → `/plugin update dev-helper-plugin`

진화 시 본 SKILL.md 또는 references 를 직접 수정 → `dev-helper-plugin:github-commit`.
