# HANDOFF — <TOPIC>

- 작성일: YYYY-MM-DD
- branch: `<branch>`
- 목적: <이 handoff 가 인계하는 것 1~2 줄 — 완료 상태 + 다음 착수 대상>
- 다음 세션 진입: 본 문서 §5(다음 작업) → §6(빌드/실행) → §4(핵심 파일) 순서로 읽고 바로 착수
- SoT 보조: `.superpowers/sdd/progress.md` (SDD ledger, gitignored) + 본 문서 §8 참조 인덱스

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
| HEAD | `<hash>` (`<msg>`) ← `<prev>` (`<msg>`) ← ... (직전 N commit chain) |
| 빌드 | `assembleDebug` <GREEN/RED>. 단말 `<모델>` 연결. APK: `<경로>` |
| 빌드 prefix(의무) | `JAVA_HOME=... COPYFILE_DISABLE=1 ./gradlew ...` |
| ledger(SoT) | `.superpowers/sdd/progress.md` (`<해당 절>`) |
| plan/spec | `docs/superpowers/plans/<...>.md` · `docs/superpowers/specs/<...>.md` |
| architect | `docs/superpowers/architect-reviews/<...>.md` (`<권장 요약>`) |

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
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export COPYFILE_DISABLE=1
export PATH="$HOME/Library/Android/sdk/platform-tools:$PATH"
export JAVA_TOOL_OPTIONS="-Djavax.net.ssl.trustStore=$HOME/.gradle/kt-truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"
cd <repo>
```

- JVM 테스트: `./gradlew :app:testDebugUnitTest --tests "<pattern>"` <!-- pre-existing baseline 실패 있으면 명시 -->
- 단말 테스트: `./gradlew :app:assembleDebugAndroidTest` 후 `adb shell am instrument -w -e class <FQCN> ...` (connectedDebugAndroidTest flake 시 우회). appops `--uid` grant 필수
- AppleDouble: 빌드 실패 시 `find . -name "._*" -type f -delete`
- 커밋: `dev-helper-plugin:github-commit` 의무. 무관 dirty 는 지정 파일만 add

---

## 7. 함정 (신규 발견)   <!-- 선택 -->

| 증상 | 원인 | fix |
|---|---|---|
| `<logcat/빌드 fingerprint>` | `<root cause>` | `<fix>` |

---

## 8. 참조 인덱스

- 설계 spec: `docs/superpowers/specs/<...>.md`
- Plan: `docs/superpowers/plans/<...>.md`
- architect 협의: `docs/superpowers/architect-reviews/<...>.md`
- 메트릭: `docs/superpowers/specs/<...>-results.md`
- SDD ledger: `.superpowers/sdd/progress.md` (gitignored — repo-local)

---

## 9. 재개 절차 (다음 세션)

1. 본 문서 §1(상태) + §5(다음 작업) 읽기.
2. `.superpowers/sdd/progress.md` carry-forward 블록 확인.
3. `<primary>` 착수 = §5.1: `<file>` → `<변경>`. §6 env + 단말 자산/appops 확인.
4. Kotlin 변경 시 `kotlin-audio-architect` 협의 (CLAUDE.md §1.4 — 테스트-only 는 면제 가능).
5. 완료 시 `<results>.md` 메트릭 갱신 + 본 handoff §5 체크 + `dev-helper-plugin:github-commit`.
