# Claude Design 시안 요청 프롬프트 (한국어 본문)

본 문서는 외부 Claude Design URL 에 던질 표준 프롬프트 템플릿이다. 메인 세션은 시안을 직접 작성하지 않고 (`feedback_design_mockup_policy.md` 정책), 본 템플릿의 placeholder 6 개를 사용자 confirm 후 채워 외부 URL 에 paste 한다.

---

## 사용 방법

1. 메인 Claude 가 사용자에게 6 placeholder 의 값을 1 회 question — 답이 모이면 다음 §본문 placeholder 치환
2. 치환된 본문을 사용자가 외부 Claude Design URL (https://claude.ai 의 별도 Design conversation) 에 paste
3. 외부 Claude Design 응답으로 `.tar.gz` 번들 + 변경 요약 markdown 도착
4. 도착 후 `project-handoff` 스킬 `references/design-mockup.md §3` 의 흡수 절차로 진행

---

## Placeholder (6 개, `<UPPER_SNAKE>` 형식)

| placeholder | 의미 | 예시 |
|---|---|---|
| `<DESIGN_SYSTEM_NAME>` | 시안 시스템 명 | `SoundAI Design v2` |
| `<PROJECT_NAME>` | 본 repo 명 | `SoundAI.Omni` |
| `<TARGET_SCREENS>` | 요청 대상 화면 목록 (쉼표 분리) | `Library, Player, Settings` |
| `<EXISTING_VERSION>` | 기존 시안 버전 (첫 요청이면 `(없음)`) | `v0.0.7` 또는 `(없음)` |
| `<DELIVERABLE_FORMAT>` | 산출물 형식 명세 | `.tar.gz + 시안 line range 표 + 변경 요약 markdown` |
| `<PRIORITY_NOTES>` | 우선순위 / 제약 메모 | `다크 모드 우선 / 한 손 조작 가능 / Compose 가능 영역만` |

---

## 본문 (외부 Claude Design URL 에 paste 할 프롬프트 본체)

```text
안녕하세요. <PROJECT_NAME> Android 프로젝트의 시안 작업을 요청합니다.

# 1. 시안 시스템 명
<DESIGN_SYSTEM_NAME>

# 2. 대상 화면
<TARGET_SCREENS>

# 3. 기존 시안 버전
<EXISTING_VERSION>

# 4. 산출물 형식 요구
<DELIVERABLE_FORMAT>

# 5. 우선순위 / 제약
<PRIORITY_NOTES>

---

# 응답 요구사항 (필수)

본 시안을 메인 세션이 본 repo 의 마일스톤에서 1:1 ref 추적해 결선해야 하므로, 다음 4 항을 반드시 충족해 응답해 주세요.

(1) **시안 line range (절대 라인) 명시 강제** — 각 화면별 시안 본문이 마크다운 또는 텍스트 산출물 안에서 어느 절대 라인 (L<start>-L<end>) 에 위치하는지 명시. 후속 마일스톤이 시안 line 을 단일 ref 로 추적해야 결선이 가능합니다. line range 누락 시 본 시안을 본 repo 마일스톤에 결선할 수 없습니다.

(2) **`.tar.gz` 번들 + 변경 요약 markdown 동봉** — 산출물 전체를 `.tar.gz` 1 개 번들로 압축. 번들 안에 `CHANGELOG.md` 또는 `summary.md` 1 개를 동봉해 본 버전의 핵심 변경 + 화면별 요약을 markdown 으로 정리.

(3) **시안 버전 (v0.0.X) 명시** — 본 응답의 시안 버전을 `v0.0.X` 형식으로 응답 첫 줄에 명시. 기존 시안 버전 (위 §3) 보다 큰 patch 번호 자동 할당. 첫 요청이면 `v0.0.1`.

(4) **기존 시안과의 diff 요약** — 기존 시안 (`<EXISTING_VERSION>`) 이 있으면 본 버전과의 diff (추가 화면 / 제거 화면 / 변경 화면) 를 표 형식으로 동봉. 첫 요청이면 본 항목 생략 가능.

---

# 응답 형식 예시

```
시안 버전: v0.0.X
도착일: YYYY-MM-DD

## 화면 1 — Library (L1-L80)
<본문>

## 화면 2 — Player (L81-L160)
<본문>

## CHANGELOG (v0.0.<prev> → v0.0.X)
| 화면 | 변경 | line range |
|---|---|---|
| Library | 추가 | L1-L80 |
| Player | 변경 | L81-L160 |
| Settings | 제거 | (이전 L161-L220 폐기) |
```

번들 path 가 메인 세션에 전달되면 본 repo 의 `docs/superpowers/design-mockups/v0.0.X/` 디렉터리로 압축 해제 + `docs/superpowers/design-mockups/inventory.md` 에 1 행 적재됩니다.

감사합니다.
```

---

## Cross-link

- 본 템플릿 사용 절차: `project-handoff/references/design-mockup.md §2`
- 흡수 절차: `project-handoff/references/design-mockup.md §3`
- inventory 행 형식: `project-handoff/assets/design-mockup-inventory-template.md`
- 시안 작성 위임 정책: 해당 프로젝트의 `~/.claude/projects/<project-slug>/memory/feedback_design_mockup_policy.md` (있으면 참조)

## 운영 메모

- placeholder 는 **strict `<UPPER_SNAKE>` 형식**. small case / backtick wrap / 다른 prefix 금지
- 본 템플릿은 generic — `app-android-pipeline` 스킬 (Phase 3 — Mockup Wiring) 도 동일 placeholder 6 개로 본 템플릿을 참조 (중복 작성 의도)
- 외부 Claude Design URL 호출은 사용자가 직접 수행. 메인 Claude 가 URL 자동 호출 안 함
