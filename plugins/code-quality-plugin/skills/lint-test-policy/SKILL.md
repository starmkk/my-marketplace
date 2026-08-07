---
name: lint-test-policy
description: >
  lint·테스트 정책 상세 레퍼런스 — 언어별 lint 도구 목록(clang-tidy·ruff·mypy·ktlint·shellcheck),
  테스트 케이스 요건과 파일 명명 규칙, 세션 시작 시 테스트 파일 우선 확인 절차를 다룬다.
  lint 를 실행할 때, 테스트를 작성할 때, 새 세션에서 프로젝트 상태를 파악할 때,
  "lint", "린트", "테스트 작성", "검증", "커버리지" 가 언급될 때 사용하라.
  lint→test→verify 순서와 zero-warning 원칙은 전역 CLAUDE.md 에 있으며 이 스킬은 그 상세판이다.
---

# lint · 테스트 정책 — 상세

전역 `~/.claude/CLAUDE.md` 의 Testing & Quality 섹션이 순서(lint→test→verify)와 zero-warning
원칙을 정의함. 이 문서는 그 상세판임.

## 1. 언어별 lint 도구

| 언어 | 도구 |
| --- | --- |
| C / C++ | `clang-tidy`, `clang-format`, `cppcheck` |
| Python | `ruff`, `mypy` |
| Kotlin | `ktlint`, `detekt` |
| Shell / Bash | `shellcheck` |
| CMake | `cmake-lint` (best effort) |

### 실행 규칙

- 진입점만이 아니라 **수정한 모든 파일**에 lint 를 실행함
- lint 오류는 즉시 수정함. 사용자 승인 없이 억제(suppress)하거나 무시하지 않음
- 경고는 오류로 취급함 — zero warnings 를 통과 기준으로 함

### shell 스크립트 열거 방식

```bash
shellcheck -x $(find scripts -name '*.sh')
```

파일명을 하드코딩하지 않고 `find` 로 열거하는 이유: 하드코딩하면 신규 스크립트가 조용히 검증에서
누락됨(실제로 누락 사례 있음).

## 2. 테스트 케이스 요건

- 모든 신규 함수/클래스는 최소 1개 이상의 대응 테스트 케이스를 가짐
- 테스트는 **정상 흐름 · 경계 조건 · 오류 조건**을 모두 다룸
- 테스트 파일 명명
  - C/C++ → `<source-filename>_test.cc`
  - Python → `test_<module>.py`
- 테스트 케이스는 구현과 **함께 커밋**함
- 신규 순수 함수는 TDD(RED→GREEN)로 구현함

## 3. 세션 연속성 (IMPORTANT)

새 세션을 시작할 때 **기존 테스트 파일을 먼저 읽어** 다음을 파악함.

- 이미 구현·검증된 것이 무엇인가
- 무엇이 통과하고 무엇이 실패하는가
- 개발이 현재 어느 지점에 있는가

테스트 파일을 **프로젝트 상태의 진실 원천**으로 취급함. 새 작업이 기존 테스트를 깨뜨린다면
진행 전에 사용자에게 보고함.

## 4. 순수 함수 / I/O 분리

계산이 순수하면 테스트가 mock 없이 성립하며 그것이 곧 검증 가능성임. 파싱·검증 같은 계산 로직과
파일 입출력·네트워크를 같은 함수에 두지 않음.
