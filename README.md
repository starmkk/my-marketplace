# vibe-coding-tools

개인 Claude Code 플러그인 마켓플레이스 — 개발 워크플로우 자동화 도구 모음

## 마켓플레이스 추가

```shell
/plugin marketplace add starmkk/my-marketplace
```

## 플러그인 설치

```shell
/plugin install dev-helper-plugin@vibe-coding-tools
```

---

## 플러그인 목록

### dev-helper-plugin

개발 워크플로우 자동화 스킬 2종을 제공합니다.

#### github-commit

현재 코드 변경사항을 검토하고 Conventional Commits + emoji 형식의 한국어 커밋 메시지로 git에 커밋합니다.

**트리거 표현:**
- "커밋해줘", "commit", "변경사항 저장", "git commit"

**사용:**
```shell
/dev-helper-plugin:github-commit
```

**커밋 형식:**
| 타입 | 이모지 | 설명 |
|------|--------|------|
| feat | ✨ | 새로운 기능 추가 |
| fix | 🐛 | 버그 수정 |
| refactor | ♻️ | 코드 리팩토링 |
| docs | 📚 | 문서 업데이트 |
| chore | 🔧 | 빌드/설정 변경 |
| style | 🎨 | 코드 포맷팅 |
| perf | 🚀 | 성능 개선 |
| test | ✅ | 테스트 추가/수정 |

---

#### save-docs

현재 세션 내용을 검토해 마크다운 문서로 정리하고 저장합니다. 개발 작업 세션과 질문·리뷰 세션을 구분해 단일 파일로 저장합니다.

**트리거 표현:**
- "문서 저장", "save docs", "세션 정리", "이 대화 저장", "기록해줘"

**사용:**
```shell
/dev-helper-plugin:save-docs
```

**저장 경로:**
- 기본값: `~/Documents/claude/docs/`
- 커스텀: 셸 프로파일에 `export CLAUDE_DOCS_DIR=/원하는/경로` 추가

**파일명 규칙:** `YYYYMMDD_<topic>.md`

---

## 업데이트

```shell
/plugin marketplace update vibe-coding-tools
```
