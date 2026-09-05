# handoff-anatomy — 표준 골격 상세

본 문서는 project-handoff SKILL.md §3 이 위임하는 상세 골격이다. `docs/superpowers/handoffs/` 의 실사용 파일 5+ 종에서 추출한 공통 구조를 정의한다. 새 handoff 는 본 골격과 정합해야 한다.

**근거 파일 (읽어서 실제 톤·밀도 확인):**
- `2026-07-02-live-speechlm-streaming-handoff.md` — multi-repo(3 repo) 대형(182 라인). §1~§10 풀셋
- `2026-06-24-m-slm6-imported-realtime-remaining-handoff.md` — 단일 repo 중형(77 라인). §0~§6
- `2026-06-25-mnn-3.6.0-upgrade-handoff.md` — 인프라 업그레이드형. 현황→계획→선행확인→순서→요약표→결과

---

## 헤더 블록 (필수)

파일 최상단. next-turn 이 어디부터 읽을지 즉시 알게 한다.

```markdown
# <제목 — HANDOFF — <TOPIC> 또는 <TOPIC> — 핸드오프>

- 작성일: YYYY-MM-DD
- branch: `<branch>`
- 목적: <이 handoff 가 무엇을 인계하는가 1~2 줄. 완료 상태 + 다음 착수 대상>
- 다음 세션 진입: **§10 의 시작 프롬프트를 첫 입력으로 붙여넣기** → §5(다음 작업) → §6(빌드/실행) → §4(핵심 파일) 순서로 읽고 바로 착수
- SoT 보조: `.superpowers/sdd/progress.md` (SDD ledger, gitignored) + 본 문서 §8 참조 인덱스
```

**핵심:** "이 문서만 읽고 이어서 진행 가능하도록 작성" 을 명시 + 읽는 순서 지정. next-turn 이 헤매지 않게 하는 것이 handoff 의 전부다.

---

## §0. 한 줄 요약 (선택 — 중·대형 권장)

무엇이 done 이고 무엇이 남았는지 2~3 줄. 예:
```markdown
## 0. 한 줄 요약
Live Recording 중 Zipformer 자막 + SpeechLM 위험도 배너 = Plan A(네이티브 스트리밍+parity) + Plan B(앱 결선) **완료·커밋**. 남은 것은 **real-engine 다주기 소크(leak-0 확정)** = option 2.
```

---

## §1. 현재 상태 스냅샷 (필수)

`scripts/capture-repo-state.sh` 출력을 붙인다.

**단일 repo — 표 형식:**
```markdown
## 1. 현재 상태
| 항목 | 값 |
|---|---|
| branch | `feature/v2-tc` |
| HEAD | `<hash>` (`<msg>`) ← `<prev>` (`<msg>`) ← ... (직전 N commit chain) |
| 빌드 | `assembleDebug` GREEN. 단말 <모델> 연결. APK: `<경로>` |
| 빌드 prefix(의무) | `JAVA_HOME=... COPYFILE_DISABLE=1 ./gradlew ...` |
| ledger(SoT) | `.superpowers/sdd/progress.md` (<해당 절>) |
| plan/spec | `docs/superpowers/plans/<...>.md` · `docs/superpowers/specs/<...>.md` |
| architect | `docs/superpowers/architect-reviews/<...>.md` (권장 <요약>) |
```

**multi-repo — repo 행 표:**
```markdown
## 1. 현재 상태 스냅샷 (N repo)
| repo | branch | HEAD | 우리 커밋 범위 | 상태 |
|---|---|---|---|---|
| **<repo1>** | `<branch>` | `<hash>` | `<base>..<head>` (<N> commits) | ✅ <상태> |
| **<repo2>** | `<branch>` | `<hash>` | `<base>..<head>` (<M> commits) | ✅ <상태> |
```
+ merge/PR 미실행 명시 (git-policy §5.2 — 명시 요청 시만) + 무관 in-flight 변경 경고 (지정 파일만 add) + 단말/자산 배치 상태.

---

## §2. 완료 작업 (필수) — "건드리지 말 것"

이미 commit·검증된 것. next-turn 이 되돌리거나 재작업 안 하게. commit 표 + 근본원인.

```markdown
## 2. 완료 (커밋·단말 검증됨) — 건드리지 말 것
| Task | commit(s) | 핵심 |
|---|---|---|
| B0 | `<hash>` | <핵심 변경> |
| BUG1 FIX | `<hash>` | 근본원인: <...> → fix: <...>. 단말 검증됨 |
```

---

## §3. 핵심 설계 결정 (선택 — 대형) — "동결 — 재협의 금지"

next-turn 이 이미 결정된 것을 다시 협의하는 낭비 차단. `파일:라인` anchor 필수.

```markdown
## 4. 핵심 설계 결정 (동결 — 재협의 금지)
| # | 결정 | 근거/위치 |
|---|---|---|
| D1 | <결정 요지> | `<file>.kt:<line>` |
```

---

## §4. 핵심 파일 인덱스 (선택 — 파일 많을 때)

디렉터리별로 묶어 나열. 각 파일 한 줄 역할. ★ 로 안전/핵심 파일 강조.

---

## §5. 다음 작업 ★ (필수)

**handoff 의 심장.** next-turn 이 바로 이 섹션으로 착수한다. 우선순위 순. 각 항목:
- **왜** — 이 작업이 필요한 이유 / 미완결 지점
- **어디** — `파일:라인` + 무엇을 바꾸는가
- **주의** — 함정 / 전제조건 / fixture·권한

```markdown
## 5. 다음 작업 (option 2 — 잔여 defer 항목) ★
### 5.1 ★ real-engine 다주기 소크 (primary)
- **왜**: 현재 소크는 1-cycle만 → per-cycle native leak 을 one-time 로드와 구분 못 함.
- **어디**: `LiveSpeechLmRobustnessTest.kt` 의 `soak_realEngineSingleCycle` → 2-3 cycle 확장. cycle별 `Debug.getPss()` assert.
- **주의**: real engine 매 cycle 1.5GB 로드 → long-timeout. fixture: `/sdcard/speechlm_mnn/` + appops `--uid` grant.
```

---

## §6. 빌드·실행 환경 (필수) — "매번 prefix"

CLAUDE.md §7 정합. next-turn 이 그대로 복붙.

```markdown
## 6. 빌드 · 실행 환경 (매번 prefix)
​```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export COPYFILE_DISABLE=1
export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"
export JAVA_TOOL_OPTIONS="-Djavax.net.ssl.trustStore=$HOME/.gradle/kt-truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"
cd <repo>
​```
- JVM 테스트: `./gradlew :app:testDebugUnitTest --tests "..."` (+ pre-existing baseline 실패 있으면 명시)
- 단말 테스트: `assembleDebugAndroidTest` 후 `am instrument` (connectedDebugAndroidTest flake 시 우회). appops `--uid` grant 필수
- AppleDouble: 빌드 실패 시 `find . -name "._*" -type f -delete`
- 커밋: `dev-helper-plugin:github-commit` 의무. 무관 dirty 는 지정 파일만 add
```

---

## §7. 함정 (선택 — 신규 발견) — 증상 / 원인 / fix 표

systematic-debugging 으로 root cause 도달한 것만. 증상은 logcat/빌드 에러 fingerprint 로.

```markdown
## 7. 함정 (신규 발견)
| 증상 | 원인 | fix |
|---|---|---|
| `releaseEngine()` SIGSEGV | `executor==null` 로 종료 오추론 | `workerConfirmedTerminated` 플래그로만 판단 |
```

---

## §8. 참조 인덱스 (필수)

깊이 파고들 링크. 절대/repo-상대 경로.

```markdown
## 8. 참조 인덱스
- 설계 spec: `docs/superpowers/specs/<...>.md`
- Plan: `docs/superpowers/plans/<...>.md`
- architect 협의: `docs/superpowers/architect-reviews/<...>.md`
- 메트릭: `docs/superpowers/specs/<...>-results.md`
- SDD ledger: `.superpowers/sdd/progress.md` (gitignored — repo-local)
```

---

## §9. 재개 절차 (필수) — 다음 세션 번호 스텝

next-turn 이 순서대로 실행. 진입 site 는 §5 항목과 1:1.

```markdown
## 9. 재개 절차 (다음 세션)
1. 본 문서 §1(상태) + §5(다음 작업) 읽기.
2. `.superpowers/sdd/progress.md` carry-forward 블록 확인.
3. <primary 작업> 착수 = §5.1: <파일> → <변경>. §6 env + 단말 자산/appops 확인.
4. Kotlin 변경 시 `kotlin-audio-architect` 협의 (CLAUDE.md §1.4 — 테스트-only 는 면제 가능).
5. 완료 시 `<results>.md` 메트릭 갱신 + 본 handoff §5 체크 + `dev-helper-plugin:github-commit`.
```

---

## §10. 다음 세션 시작 프롬프트 (필수) — 복붙용 원문

§9 가 "사람이 읽는 절차" 라면 §10 은 **다음 사람이 assistant 에게 보내는 첫 입력 그 자체**다. handoff 를 읽으라는 지시, 어느 스텝부터 시작할지, 실행 위치, 계획 순서, 위임·리뷰·커밋 규칙, 동결 결정, 환경 확인 커맨드까지 한 블록에 넣어 next-turn 이 handoff 를 해석하다 지침을 빠뜨리는 일을 없앤다.

**반드시 담을 8요소** (빠지면 next-turn 이 되묻는다 — 실측):
1. **handoff 자기 경로** + `§9 의 N번은 완료됨, N+1번부터` 진입 스텝
2. **실행 위치**(절대경로)·branch·HEAD hash, 워크트리/백그라운드 제약
3. **primary 계획서 경로**와 실행 스킬, Task 범위·순서, 계획서 내부 우선순위 규칙(말미 절 우선 등)
4. **위임 모델·리뷰·lint·테스트·커밋 스킬**의 Task 단위 절차 한 줄
5. **차단 게이트**(커맨드 → 기대값, skip 은 실패)
6. **기록 규칙**(dev-log 경로, 인덱스 갱신)
7. **동결 결정**(메모리 파일·handoff §3 참조 + 핵심 3~5개 한 줄씩) + "새 갈림길만 AskUserQuestion"
8. **금지·주의**(push 금지, add 제외 파일, 임시 디렉토리 고정) + **환경 확인 커맨드와 기대값**(예: `N passed`)

**형식 규칙**
- 제목은 `## 10. 다음 세션 시작 프롬프트 (그대로 복사해 첫 입력으로 사용)`, 본문은 ```` ```text ```` 펜스 블록 **1개**. 블록 앞에 blockquote 로 세션 형태 제약(대화형/워크트리) 1~2줄만.
- 블록 안 문장은 **명령형**("~해라", "~할 것"), 번호 목록. 설명·근거는 §3/§7 에 두고 여기서는 참조만.
- 경로·hash·커맨드는 §1/§6 과 **문자 그대로 동일**해야 한다(verify-handoff-integrity.sh 가 파일 경로·HEAD 존재를 검사). handoff 작성 후 커밋이 더 생기면 HEAD 를 함께 갱신.
- 길이 15~30줄. 넘치면 규칙을 CLAUDE.md/메모리로 옮기고 참조만 남긴다.

**실사용 예** (`docs/superpowers/handoffs/2026-09-05-v4-gemma-mnn-plan-d-complete-handoff.md` §10 축약):
```text
speechlm.v4_gemma_mnn 재개발을 이어서 진행한다. use AgentTool

먼저 handoff 를 읽고 그 순서대로 진행해라:
- docs/superpowers/handoffs/2026-09-05-v4-gemma-mnn-plan-d-complete-handoff.md
  (§9 의 1번 환경 확인 → 2번 갈림길 확정 → 3번 Plan E 착수)

작업 지침(~/.claude/CLAUDE.md 준수):
1. 실행 위치는 사용자 체크아웃 /MyCode/share/SpeechLM.asset/speechlm.v4_gemma_mnn (main, HEAD 01a9100). 워크트리 만들지 말 것.
2. Plan E 계획서 docs/superpowers/plans/2026-09-04-plan-e-bootstrap-convert-sh.md 를 superpowers:subagent-driven-development 로 E0 → E5 순서 실행(말미 "메인 세션 검수 보완" 우선).
   - 구현 sonnet, Task 마다 diff 를 strategic-code-reviewer(opus) 로 리뷰 → High 반영 → lint(ruff·mypy·shellcheck 무경고) → 테스트 → 커밋(dev-helper-plugin:github-commit 스킬, Co-Authored-By 없음, push 금지).
3. Plan E 완료 → Plan F(…plan-f-batch-eval-v3-50.md, 말미 "설계 검토 판정" 절 우선). 새 갈림길만 AskUserQuestion.
4. 중간 마일스톤마다 docs/dev-logs/dev-log-<오늘날짜>.md 에 append(실측 수치 + 재현 커맨드).
5. 확정된 결정(메모리 project-speechlm-v4-mnn-v2-rebuild.md, handoff §3)은 다시 묻지 말 것. 특히 D-D15(audio encoder 는 memory normal·fp32).
6. 모드만 바뀐 파일 3개와 .vscode/ 는 add 금지. slow e2e 는 --basetemp 고정 디렉토리 사용.
7. Plan F 완료 시점에 dev-helper-plugin:project-handoff 로 handoff 를 새로 작성.

시작 전 환경 확인: nvidia-smi, python3 -c "import torch;print(torch.cuda.is_available())",
cd speechlm.v4_gemma_mnn && PYTHONPATH=$PWD/scripts python3 -m pytest tests -p no:warnings -m "not slow and not gpu" -o addopts="" (361 passed 확인 후 착수).
```

**흔한 누락**: (a) 위임 모델·리뷰어 지정이 없어 next-turn 이 전부 직접 구현 (b) 동결 결정 참조가 없어 이미 확정된 사항을 사용자에게 재질문 (c) 환경 확인 기대값(`N passed`)이 없어 skip 을 통과로 오인 (d) HEAD 가 §1 과 달라 verify 실패.

---

## 밀도 가이드

- **길이**: 단일 repo 중형 70~120 라인, multi-repo 대형 150~250 라인. 넘치면 §3/§4 를 spec/plan 으로 위임하고 링크만.
- **표 위주** — 문장 단락 최소. commit 표 / 결정 표 / 함정 표.
- **언어**: 한국어 (글로벌 정책). 코드·경로·식별자는 원문.
- **`파일:라인` anchor** — §3/§5/§7 은 반드시 파일 경로 + 가능하면 라인. next-turn 이 grep 없이 직행.
