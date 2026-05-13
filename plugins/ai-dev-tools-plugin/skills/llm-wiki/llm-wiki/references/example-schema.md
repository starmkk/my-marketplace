# Example CLAUDE.md Schemas

도메인별 CLAUDE.md 스키마 예시 모음. 실제 사용 시 복사해서 커스터마이즈하라.

---

## 예시 1: 논문 연구 위키 (Research Wiki)

```markdown
# Wiki Schema — AI/ML Research

## 목적
AI/ML 관련 논문, 기사, 강의 노트를 점진적으로 축적하는 개인 연구 위키.

## 디렉터리 구조
raw/papers/          # PDF 논문
raw/articles/        # 웹 기사 (마크다운 클립)
raw/notes/           # 개인 메모
wiki/sources/        # 논문/기사별 요약 페이지
wiki/models/         # 모델 엔티티 (GPT-4, Gemma 등)
wiki/concepts/       # 개념 (Attention, LoRA, MoE 등)
wiki/authors/        # 저자 페이지
wiki/overview.md     # 분야 전체 현황 요약
wiki/index.md
wiki/log.md

## Ingest 워크플로
1. 논문/기사 읽기
2. Abstract, 핵심 기여, 실험 결과, 한계점 파악
3. wiki/sources/[제목-연도].md 작성 (frontmatter: title, authors, year, venue, tags)
4. 관련 모델/개념/저자 페이지 갱신
5. 기존 논문과의 관계 명시 (cites, extends, contradicts)
6. overview.md에서 언급이 필요한지 확인
7. index.md, log.md 갱신

## 소스 페이지 포맷
---
title: "논문 제목"
authors: [저자1, 저자2]
year: 2024
venue: NeurIPS / arXiv
tags: [transformer, efficient-inference]
updated: 2026-04-18
---

## 핵심 기여
[1~3줄]

## 방법론
[핵심 아이디어 설명]

## 실험 결과
[주요 수치]

## 한계점
[저자가 인정한 것 + 내 관찰]

## 관련 작업
- extends: [[논문A]]
- contradicts: [[논문B]]
- used by: [[논문C]]

## Lint 체크
- 같은 개념에 대해 다른 논문이 상충되는 정의 사용하는지
- 오래된 SOTA 클레임 (이미 갱신됐을 수 있음)
- 저자 페이지에 최신 논문이 없는지
```

---

## 예시 2: 팀 프로젝트 위키 (Team Project Wiki)

```markdown
# Wiki Schema — SoundAI.Lite Project

## 목적
SoundAI.Lite Android 앱 개발 관련 의사결정, 기술 조사, 아키텍처를 축적하는 팀 위키.

## 디렉터리 구조
raw/meeting-notes/     # 회의록 (날짜별)
raw/research/          # 기술 조사 문서
raw/specs/             # 기능 명세
wiki/decisions/        # 주요 기술 결정 (ADR 형식)
wiki/components/       # 컴포넌트별 페이지 (MNN, Qwen, Diarization 등)
wiki/issues/           # 해결된 기술 이슈
wiki/glossary/         # 용어 정의
wiki/overview.md       # 프로젝트 현황 요약
wiki/index.md
wiki/log.md

## ADR (Architecture Decision Record) 포맷
wiki/decisions/ 하위 페이지:
---
title: "ADR-001: MNN inference framework 선택"
date: 2026-03-01
status: accepted  # proposed / accepted / deprecated / superseded
---
## 컨텍스트
## 결정
## 결과
## 대안 (고려했으나 기각된 것)

## Ingest 워크플로
1. 회의록/문서 읽기
2. 새로운 결정, 이슈 해결, 기술 변경 식별
3. 해당 decisions/, components/ 페이지 갱신
4. overview.md 프로젝트 현황 반영
5. index.md, log.md 갱신
```

---

## 예시 3: 독서 위키 (Book Reading Wiki)

```markdown
# Wiki Schema — Reading Wiki

## 목적
읽는 책마다 챕터별 메모를 축적하고 캐릭터, 테마, 아이디어를 연결하는 독서 동반 위키.

## 디렉터리 구조
raw/chapters/          # 챕터별 메모/하이라이트
wiki/books/            # 책 페이지 (메타데이터 + 전체 인상)
wiki/characters/       # 캐릭터/인물 페이지
wiki/themes/           # 반복되는 테마/아이디어
wiki/quotes/           # 인상적인 인용구 모음
wiki/connections/      # 책 간 연결고리
wiki/index.md
wiki/log.md

## Ingest 워크플로 (챕터 단위)
1. 챕터 메모 읽기
2. 등장/발전한 캐릭터 페이지 갱신
3. 새 테마 등장 시 wiki/themes/ 페이지 생성 또는 갱신
4. 인용구 추가
5. 다른 책과의 연결 확인
6. log.md에 `## [날짜] ingest | [책제목] Ch.N` 형식 추가
```

---

## index.md 템플릿

```markdown
# Wiki Index
*마지막 갱신: 2026-04-18 | 총 페이지: 42 | 소스: 18개*

## Sources (18)
| 페이지 | 요약 | 날짜 |
|--------|------|------|
| [[sources/paper-A-2024]] | Attention 효율화 방법 제안 | 2026-04-01 |

## Concepts (12)
| 페이지 | 요약 |
|--------|------|
| [[concepts/attention]] | Transformer 핵심 메커니즘 |

## Entities (8)
| 페이지 | 유형 | 요약 |
|--------|------|------|
| [[models/gemma4]] | 모델 | Google 멀티모달 모델 |
```

---

## log.md 템플릿

```markdown
# Wiki Log

## [2026-04-18] ingest | Gemma 4 Technical Report
- 요약: Google의 Gemma 4 멀티모달 아키텍처 및 성능 벤치마크
- 갱신된 페이지: models/gemma4.md (신규), concepts/moe.md (갱신), overview.md
- 발견한 모순: concepts/moe.md의 파라미터 수 수정 (이전: 추정치, 현재: 공식 수치)

## [2026-04-15] query | Gemma vs Qwen 비교
- 질문: 온디바이스 추론 성능 비교
- 생성된 페이지: comparisons/gemma-vs-qwen.md (신규 저장)

## [2026-04-10] lint
- 고아 페이지 2개 발견: concepts/rnn.md, concepts/lstm.md → overview.md에 링크 추가
- 오래된 SOTA 클레임: sources/paper-B-2023.md의 벤치마크 → ⚠️ 표시
```
