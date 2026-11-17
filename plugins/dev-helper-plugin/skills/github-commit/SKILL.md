---
name: github-commit
description: >
  현재 코드 변경사항을 검토하고 Conventional Commits + emoji 형식의 한국어 커밋 메시지로
  git에 커밋하는 스킬. 사용자가 "커밋해줘", "commit", "변경사항 저장", "git commit",
  "/github:commit", "커밋 메시지 작성" 등의 표현을 사용하거나 코드 변경 후 저장을 요청할 때
  반드시 이 스킬을 사용하라.
context: fork
agent: workflow-policy-plugin:wf-worker
model: sonnet
allowed-tools:
  - Bash
  - Read
---

# Git Commit Skill
## Git Settings

- **Main branch**: `main`
- **Use**: `gh` CLI

## Commit Message Rules

- **Commit format**: Conventional Commits + emoji, written in **Korean**
- **Commit types**:
  - `feat: ✨ 새로운 기능 추가`
  - `fix: 🐛 버그 수정`
  - `refactor: ♻️ 코드 리팩토링`
  - `docs: 📚 문서 업데이트`
  - `chore: 🔧 빌드/설정 변경`
  - `style: 🎨 코드 포맷팅`
  - `perf: 🚀 성능 개선`
  - `test: ✅ 테스트 추가/수정`

- **Tone**: imperative form — ("추가" not "추가됨", "추가되었습니다")
- **Scope**: split unrelated changes into separate commits
- **Co-author**: exclude Co-Author metadata from commit logs

## Steps

1. Identify all changes — run the collector **once** (replaces separate `git status`/`git diff` calls):
   `bash "${CLAUDE_PLUGIN_ROOT}/skills/github-commit/scripts/collect-changes.sh" [repo]`
   - 출력: identity · status · 수집 시점 staged 목록 · log · diff --stat · untracked(바이트) · secret scan · diff 본문(최대 20,000바이트, 비밀 패턴 마스킹)
   - secret scan 에 `SECRET` 행이 있으면 해당 파일을 Read 하지 말고 커밋 없이 위치만 보고(값은 옮기지 않음). 요청에 그 파일 허용이 명시된 경우만 진행
   - identity 가 `(미설정)` 이면 요청에 `-c user.name=… -c user.email=…` 지시가 있을 때만 그 플래그로 진행. git config 는 바꾸지 않음
   - diff 가 잘렸거나 신규 파일 내용이 필요할 때만 해당 파일을 Read
2. Write commit messages following the rules above and apply — 커밋 단위 명령을 `&&` 로 이어 Bash **1회**로 실행
   - 단위 명령: `git add -- <files> && git commit -F - -- <files> <<'MSG' … MSG` — 경로 한정으로 미리 stage 돼 있던 다른 파일을 섞지 않음
   - 마지막에 `git log --format='%h %s' -n <커밋 수>` 로 확인. hook 실패 시 뒤 단위는 실행되지 않으므로 실패 단위와 출력을 보고
   - `--no-verify`·push·히스토리 재작성(amend·rebase·reset)은 하지 않음 — 요청에 명시된 경우만 예외
3. Report a summary of all commits made — 커밋 해시·제목, 중단했다면 사유
