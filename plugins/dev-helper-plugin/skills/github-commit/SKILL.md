---
name: github-commit
description: >
  현재 코드 변경사항을 검토하고 Conventional Commits + emoji 형식의 한국어 커밋 메시지로
  git에 커밋하는 스킬. 사용자가 "커밋해줘", "commit", "변경사항 저장", "git commit",
  "/github:commit", "커밋 메시지 작성" 등의 표현을 사용하거나 코드 변경 후 저장을 요청할 때
  반드시 이 스킬을 사용하라.
context: fork
agent: general-purpose
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

1. Run `git status` and `git diff` to identify all changes
2. Write commit messages following the rules above and apply
3. Report a summary of all commits made
