# HANDOFF — <TOPIC>

- 작성일: YYYY-MM-DD
- branch: `<branch>`
- 목적: <이 handoff 가 인계하는 것 1~2 줄 — 완료 상태 + 다음 착수 대상>
- 다음 세션 진입: **§10 의 시작 프롬프트를 첫 입력으로 붙여넣기** → §5(다음 작업) → §6(빌드/실행) → §4(핵심 파일) 순서로 읽고 바로 착수
- SoT 보조: (있으면) 프로젝트 ledger `<경로>` + 본 문서 §8 참조 인덱스

> **이 문서만 읽고 이어서 진행 가능하도록 작성됨.** RESUME.md 등 외부 SoT 에 의존하지 않는다.

---

## 0. 한 줄 요약

<무엇이 done, 무엇이 남았는지 2~3 줄. 남은 것 = 다음 작업 primary.>

---

## 1. 현재 상태 스냅샷

<!-- 단일 repo: 아래 표. multi-repo: cross-repo.md §2 의 repo 행 표로 교체 -->

| 항목 | 값 |
|---|---|
| branch | `<branch>` |
| HEAD | `<hash>` (`<msg>`) ← `<prev>` (`<msg>`) ← ... (직전 N commit chain — handoff 커밋 직전 HEAD) |
| 빌드 | `<빌드 명령>` <GREEN/RED>. <단말·산출물 경로> |
| 빌드·실행 prefix(프로젝트 CLAUDE.md) | `<env·명령 prefix>` |
| plan/spec | `<경로>` |
| 실행 중 | 없음(대기 팀원은 handoff 전 `TaskStop`). 이 세션에서 계속 쓸 대기 팀원만 `` 실행 중(이 세션 한정 — 새 세션에서 주소 불가): `<이름>` — <목적·결과 경로> `` — 세션 종료·`/clear` 전 `TaskStop` |

---

## 2. 완료 작업 (커밋·검증됨) — 건드리지 말 것

| Task / 항목 | commit(s) | 핵심 |
|---|---|---|
| `<Task>` | `<hash>` | `<핵심 변경>` |
| `<BUG FIX>` | `<hash>` | 근본원인: `<...>` → fix: `<...>`. 단말 검증됨 |

---

## 3. 핵심 설계 결정 (동결 — 재협의 금지)   <!-- 선택: 대형 handoff -->

| # | 결정 | 근거/위치 |
|---|---|---|
| D1 | `<결정 요지>` | `<file>:<line>` |

---

## 4. 핵심 파일 인덱스   <!-- 선택: 파일 많을 때 -->

- `<dir>/`: `<file>` (`<역할>`), ★ `<safety-critical file>`

---

## 5. 다음 작업 ★

### 5.1 ★ `<primary 작업>` (primary)
- **왜**: `<필요 이유 / 미완결 지점>`
- **어디**: `<file>:<line>` → `<무엇을 바꾸는가>`
- **주의**: `<함정 / 전제조건 / fixture·권한>`

### 5.2 `<secondary 작업>`
- **왜** / **어디** / **주의**

---

## 6. 빌드 · 실행 환경 (매번 prefix)

```bash
<프로젝트 빌드·실행 prefix — 프로젝트 CLAUDE.md 의 env·경로 설정을 그대로>
cd <repo>
```

- 테스트: `<프로젝트 테스트 명령>` <!-- pre-existing baseline 실패 있으면 명시 -->
- 단말·실측: `<단말 테스트·측정 명령>` (`<전제: 권한·자산 배치>`)
- AppleDouble: 빌드 실패 시 `find . -name "._*" -type f -delete`
- 커밋: `dev-helper-plugin:github-commit` 의무. 무관 dirty 는 지정 파일만 add

---

## 7. 함정 (신규 발견)   <!-- 선택 -->

| 증상 | 원인 | fix |
|---|---|---|
| `<logcat/빌드 fingerprint>` | `<root cause>` | `<fix>` |

---

## 8. 참조 인덱스

- 설계 spec: `<spec 경로>`
- Plan: `docs/dev-plans/<category>/<date>-<topic>-plan.md` (없으면 docs/plans/ 아래)
- 메트릭: `<결과 문서 경로>`
- (있으면) 프로젝트 ledger: `<경로>`

<!-- 경로는 repo 루트 기준 상대 경로 또는 절대 경로 — verify-handoff-integrity.sh 가 존재를 검사 -->

---

## 9. 재개 절차 (다음 세션)

1. 본 문서 §1(상태) + §5(다음 작업) 읽기.
2. (있으면) 프로젝트 ledger 의 carry-forward 블록 확인.
3. `<primary>` 착수 = §5.1: `<file>` → `<변경>`. §6 prefix + 전제(단말·자산·권한) 확인.
4. 구현 전후 `code-quality-plugin:strategic-code-reviewer` 협의 (전역 CLAUDE.md Code Authoring Procedure — 면제 조건 동일).
5. 완료 시 `<results>.md` 메트릭 갱신 + 본 handoff §5 체크 + `dev-helper-plugin:github-commit`.

---

## 10. 다음 세션 시작 프롬프트 (그대로 복사해 첫 입력으로 사용)

> 대화형 세션으로 시작할 것. <워크트리/백그라운드 제약이 있으면 한 줄>. <컨테이너 재시작 시 복구 커맨드가 있으면 §6 참조 한 줄>.

```text
<프로젝트> <작업>을 이어서 진행한다. <위임 허용 키워드: use AgentTool>

먼저 handoff 를 읽고 그 순서대로 진행해라:
- docs/handoffs/<YYYY-MM-DD>-<topic>-handoff.md
  (§9 의 <N>번 <이미 끝난 스텝>은 완료됨. <N+1>번 <스텝> → <N+2>번 <primary 착수>부터 시작)

작업 지침(~/.claude/CLAUDE.md 준수):
1. 실행 위치는 <절대경로> (<branch>, HEAD <hash>). <워크트리 만들지 말 것 / 만들 것>.
2. <primary 계획서 경로>를 <실행 방식: 메인 세션 직접 실행 / Task 단위 서브에이전트 위임 등>로 <Task 범위> 순서 실행.
   - <계획서 우선순위 규칙: 말미 절이 본문보다 우선 등>
   - <동결 결정 목록·재협의 금지>
   - 구현 <모델>, Task 마다 diff 를 <리뷰어>로 리뷰 → High 반영 → lint(<도구> 무경고) → 테스트 → 커밋(<커밋 스킬>).
3. <차단 게이트: 커맨드 → 기대 결과, skip 은 실패>.
4. <중간 마일스톤 기록 규칙: dev-log 경로·인덱스>.
5. 확정된 사용자 결정(<메모리 파일>, handoff §3)은 다시 묻지 말 것: <핵심 결정 3~5개 한 줄씩>. 새 갈림길만 AskUserQuestion.
6. <secondary 계획 순서>.
7. <금지 사항: push 금지·add 제외 파일·임시 디렉토리 규칙>.
8. <완료 시점에 dev-helper-plugin:project-handoff 로 handoff 재작성>.

시작 전 환경 확인: <커맨드 1>, <커맨드 2>,
<빠른 회귀 커맨드> (<기대 결과: N passed> 확인 후 착수).
```

