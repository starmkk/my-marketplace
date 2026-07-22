# cross-repo — 여러 repo 걸친 변경 인계 변형

본 문서는 project-handoff SKILL.md §1 의 **cross-repo 변형**이 위임하는 상세 절차다. 본 repo 와 sibling repo (예: SoundAI.Omni.TC ↔ SoundAI.Lite ↔ SpeechLM.cpp.v3 ↔ Zipformer-ASR.main) 사이 작업을 인계할 때, 양쪽 HEAD + commit chain + 후속 컨텍스트를 **하나의 handoff 파일**에 담는다.

기본 절차는 SKILL.md §2 (5 step) 와 동일하고, 아래 3 가지가 추가된다: (1) §1 스냅샷을 multi-repo 표로, (2) commit 요약을 repo별로, (3) 외부 의존·재현 절차를 명시.

**실사용 reference:** `docs/superpowers/handoffs/2026-07-02-live-speechlm-streaming-handoff.md` (3 repo) / `2026-05-30-soundai-lite-mnn-3.5.0-handoff.md` / `2026-05-30-libzipformer-kor-sharing-handoff.md` / `2026-06-25-mnn-3.6.0-upgrade-handoff.md`.

---

## §1. Trigger

- **sibling repo 와 작업 인계** — 두 repo 사이 의존 변경 (composite `includeBuild`, jniLibs vendor 갱신, 외부 모듈 추가)
- **cross-repo 변경 결선** — 한 작업이 두 repo 의 commit 을 모두 요구 (예: v3 네이티브 API 신설 → Lite JNI facade → Omni 앱 결선)
- **외부 repo 변경이 본 repo 에 영향** — 외부 repo 새 commit 이 본 repo build/회귀에 영향 (예: MNN 3.6.0 unification)

---

## §2. 양쪽 repo HEAD 캡처

`scripts/capture-repo-state.sh` 에 sibling repo 경로를 인자로 넘겨 한 번에 캡처:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/project-handoff/scripts/capture-repo-state.sh" \
  /path/to/SoundAI.Lite /path/to/SpeechLM.cpp.v3
```

출력을 handoff §1 의 multi-repo 표에 붙인다 (handoff-anatomy.md §1 multi-repo 형식):

```markdown
| repo | branch | HEAD | 우리 커밋 범위 | 상태 |
|---|---|---|---|---|
| **<source-repo>** | `<branch>` | `<hash>` | `<base>..<head>` (<N> commits) | ✅ <상태> |
| **<target-repo>** | `<branch>` | `<hash>` | `<base>..<head>` (<M> commits) | ✅ <상태> |
```

**commit chain (직전 ≥5) 양쪽 모두 적재** — next-turn 이 후속 commit 이 본 작업과 정합인지 검증 가능해야 한다.

⚠️ **무관 in-flight 변경 경고 필수** — sibling repo 가 무관한 dirty 변경을 다수 보유하는 경우가 흔하다. handoff §1 에 "우리 커밋은 지정 파일만 스테이징. 후속 작업 시 반드시 지정 파일만 명시 add" 를 명시.

---

## §3. repo별 commit 요약 (완료 작업 §2)

handoff 의 완료 작업 섹션을 repo별 소제목으로 분리, 각 repo commit 표:

```markdown
### <source-repo> (`<branch>`, `<base>..<head>`)
| commit | 내용 |
|---|---|
| `<hash>` | <핵심 변경> |

### <target-repo> (`<branch>`, `<base>..<head>`)
| commit | 내용 |
|---|---|
| `<hash>` | <핵심 변경> |
```

parity / 정합 증명이 있으면 (네이티브 ↔ 앱 결과 일치 등) 그 검증 상태를 명시.

---

## §4. 후속 작업자 인계 컨텍스트 (§6 빌드·실행에 통합)

다음 4 항을 handoff §6 에 명시:

1. **외부 의존** — source 가 target 의 어느 commit/모듈을 어떻게 쓰는가 (`includeBuild` / jniLibs vendor / 모델 자산 배치)
2. **환경변수** — CLAUDE.md §7 의 4 변수 + 프로젝트별 `<PROJECT>_BUILD_ROOT`
3. **빌드 명령** — 양쪽 repo 에서 검증된 명령 (native gtest 는 `cmake --build build --target <t> && ctest -R <t>` 등)
4. **검증 절차** — `connectedDebugAndroidTest --tests <FQCN>` 또는 `am instrument` 우회 + 단말 시각 확인

---

## §5. 잠재 위험 / OQ (§7 함정 또는 별도 절)

회귀 fingerprint 1 줄 + 영향 범위 + 해결 방향. 교차 repo 특유의 위험 (ABI mismatch, 모델 포맷, MNN release↔run SIGSEGV 등) 강조.

---

## §6. 재현 절차 (§9 재개 절차)

next-turn 이 그대로 재현 가능한 명령 셋 — env prefix + 단말 연결 + 빌드 + 회귀 + cold-load 측정 (CLAUDE.md §1.1 5번, base 대비 비교). handoff-anatomy.md §9 형식.

---

## §7. Commit

`dev-helper-plugin:github-commit` 위임. stage 대상: `docs/superpowers/handoffs/<YYYY-MM-DD>-<topic>-handoff.md` (신규). 메시지: `docs(handoff): 📤 <topic> cross-repo 인계 — <source> ↔ <target>`.

**주의** — handoff 파일은 본 repo 에만 commit. sibling repo 에는 각자의 코드 commit 만 (지정 파일 명시 add). handoff 문서를 sibling repo 에 중복 두지 않는다.
