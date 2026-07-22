# design-mockup — Claude Design 시안 결선 변형

본 문서는 project-handoff SKILL.md §1 의 **design-mockup 변형**이 위임하는 절차다. 메인 세션은 시안을 직접 작성하지 않고 (아래 정책), 외부 Claude Design URL 에 요청 → `.tar.gz` 번들 도착 → 본 repo 마일스톤 결선까지를 관리한다.

**정책 근거:** "시안 작성 위임 정책 — 메인 세션은 프롬프트만 안내, 직접 작성 금지" (프로젝트 memory `feedback_design_mockup_policy.md`).

이 변형의 산출물은 **2 개**: (1) `docs/superpowers/design-mockups/inventory.md` 1 행 (시안 SoT), (2) 결선 착수 시 SKILL.md §2 절차로 handoff 파일 (다음 세션이 어느 마일스톤에서 어느 시안 line 을 결선할지 인계).

---

## §1. Trigger

- **외부 Claude Design 시안 요청** — "시안 만들어줘 / Claude Design 에 던질 프롬프트"
- **시안 `.tar.gz` 도착** — 외부 Claude Design 번들 통합 요청
- **inventory 갱신** — "inventory 갱신 / 결선 commit 채워줘"

inventory SoT: `docs/superpowers/design-mockups/inventory.md`.

---

## §2. 외부 요청 protocol

`assets/claude-design-request-template.md` 본문의 placeholder 6 개 (`<DESIGN_SYSTEM_NAME>` / `<PROJECT_NAME>` / `<TARGET_SCREENS>` / `<EXISTING_VERSION>` / `<DELIVERABLE_FORMAT>` / `<PRIORITY_NOTES>`) 를 사용자 confirm 후 치환 → 사용자가 외부 URL 에 직접 paste. **메인 Claude 는 외부 URL 호출 안 함.**

**line range 강제** — 외부 응답에 시안 본문의 절대 라인 번호 (L\<start\>-L\<end\>) 가 반드시 명시돼야 한다. 후속 마일스톤이 시안 line 을 1:1 ref 로 추적해 결선하므로. 누락 시 재요청 권유.

---

## §3. 번들 도착 후 흡수

1. **압축 해제** — `docs/superpowers/design-mockups/v0.0.<X>/` 생성 후 unpack:
   ```bash
   mkdir -p docs/superpowers/design-mockups/v0.0.<X>
   tar -xzf <bundle>.tar.gz -C docs/superpowers/design-mockups/v0.0.<X>/
   ```
2. **inventory.md 1 행 추가** (§4)
3. **결선 마일스톤 site 안내** — 시안 line range 에 대응하는 후속 마일스톤 (M-UI<N>) 후보 1~3 개를 사용자에게 1 줄씩 제시. 사용자 confirm 후, 결선 착수 시 그 컨텍스트를 handoff §5 (다음 작업) 에 반영
4. **모듈 구조 변경 동반 시** — feature 모듈 추가 등 build 변경이 필요하면 `app-android-pipeline` 스킬 Phase 3 (Mockup Wiring) 로 위임. 아니면 본 변형에서 inventory 갱신만

---

## §4. inventory.md 갱신

`assets/design-mockup-inventory-template.md` 정합. 행 형식:

```
| 버전 | 도착일 | 번들 경로 | 시안 line 범위 | 결선 마일스톤 | 결선 commit |
|---|---|---|---|---|---|
| v0.0.<X> | YYYY-MM-DD | `docs/superpowers/design-mockups/v0.0.<X>/` | L<start>-L<end> | (대기) | (대기) |
```

- **시안 line 범위** — 외부 응답의 절대 라인 그대로. 여러 화면이면 화면별 sub-range 쉼표 분리 (`L100-L150 (Library), L151-L200 (Player)`)
- **결선 commit 초기값** — `(대기)`. §5 에서 채움
- inventory.md 미존재 repo 는 첫 도착 시 디렉터리 + 파일 신규 생성

---

## §5. 결선 commit 채움

후속 마일스톤이 시안 line range 를 본 repo build/UI 에 반영하면 그 commit hash 를 해당 행 "결선 commit" 셀에 적재. 여러 마일스톤 분할 결선이면 "결선 마일스톤" + "결선 commit" 셀 모두 쉼표 분리 (`M-UI2, M-UI3` / `<hash1>, <hash2>`).

---

## §6. Commit

`dev-helper-plugin:github-commit` 위임. stage 대상:
- 시안 도착: `docs/superpowers/design-mockups/v0.0.<X>/` (전체) + `inventory.md` (갱신) + (결선 착수 시) handoff 파일
- 결선 commit 채움: `inventory.md` 만

메시지:
- 도착: `docs(handoff): 📥 design-mockups v0.0.<X> 흡수 — <TARGET_SCREENS> + inventory 1 행`
- 결선: `docs(handoff): 📥 design-mockups inventory — v0.0.<X> 결선 commit <hash>`
