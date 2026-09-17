# MASTG v2.0.0 — 구성요소·추적 체인 구조

> **출처**: OWASP Mobile Application Security Testing Guide (MASTG) —
> `https://github.com/OWASP/mastg` 태그 v2.0.0 (렌더: `https://mas.owasp.org/MASTG/`)
> **버전**: **MASTG v2.0.0** (published 2026-06-30) tarball 전수 카운트 기준.
> 부출처: MASWE v1.0.0 (추적 체인 연결 대상)
> **라이선스**: CC BY-SA 4.0 · **조회일**: 2026-09-17
>
> 이 파일은 **색인 수준** 구조 요약임 — MASTG 본문 해설이 아니라 구성요소 수·상태 분포·참조
> 방향만 다룸. 개별 테스트·기법의 내용은 `mas.owasp.org/MASTG/` 원문을 볼 것.
>
> ⚠️ **버전 고정 주의**: 아래 수치는 전부 **v2.0.0 태그 실측**임. MAS `main` 브랜치는 계속
> 확장 중(MASWE 0118 까지, 5번째 프로파일 EUDIW 등)이므로 main 기준 수치를 섞지 말 것.

---

## 구성요소 표 (v2.0.0 태그 실측)

| 구성요소 | 총 파일 수 | 상태 분포 |
|---|---|---|
| MASTG-TEST (`tests/` 레거시) | 92 | 전부 `deprecated` (v1 스타일, `covered_by` 로 신규 TEST-ID 지시) |
| MASTG-TEST (`tests-beta/` 신규) | 200 | 현행 186 (status 필드 없음) · `placeholder` 14 |
| **MASTG-TEST 합계** | **292** | 현행 186 · placeholder 14 · deprecated 92 |
| MASTG-TECH (기법) | 167 | 현행 165 · placeholder 1 · deprecated 1 |
| MASTG-TOOL (도구) | 135 | 현행 129 · deprecated 6 |
| MASTG-DEMO (실습 예제) | 157 | 현행 150 · placeholder 6 · draft 1 |
| MASTG-KNOW (배경 지식) | 140 | 현행 132 · placeholder 6 · deprecated 2 |
| MASTG-BEST (모범사례) | 74 | 현행 66 · placeholder 8 |
| MASTG-APP (실습 대상 앱) | 29 | 현행 28 · deprecated 1 |

## MASTG-TEST 플랫폼 분포

android **161** · ios **129** · network **2**

⚠️ **분모는 292건 전체(deprecated 92건 포함)임** — 현행 186건만의 분포가 아님. 디렉터리는
`android/`·`ios/` 둘뿐이고 `platform: network` 는 개별 frontmatter 에 2건만 존재함.

## 추적 체인의 실제 저장 방향 ⭐

렌더 페이지에서는 `MASVS → MASWE → TEST → DEMO` 로 보이지만, **소스의 저장 방향은 역참조**임:
`MASWE ← MASTG-TEST ← MASTG-DEMO`.

- MASWE frontmatter `mappings.masvs-v2: [...]` → 자신이 속한 MASVS 컨트롤을 가리킴 (정방향)
- MASWE 파일에는 test 목록 필드가 **없음** — MASTG-TEST frontmatter 의 `weakness: MASWE-XXXX` 가
  역참조함
- MASTG-TEST 에도 demo 링크 필드가 **없음**(`tests-beta/` 200건 중 `demo` 보유 0건) —
  MASTG-DEMO frontmatter 의 `test: MASTG-TEST-XXXX` 가 역참조함
- 사이트의 "이 MASWE 에 연결된 Tests" 목록은 빌드 시점에 역참조를 모아 **동적 생성**한 것이며
  소스에 정적으로 박혀 있지 않음 → 소스에서 추적하려면 TEST 의 `weakness:`, DEMO 의 `test:` 를
  **역방향으로 grep** 해야 함

## MASTG-BEST — 이 플러그인과 층위가 가장 가까운 구성요소

MASTG-BEST(74건)는 "무엇이 취약한가"(MASWE)나 "어떻게 점검하는가"(TEST)가 아니라 **"어떻게
구현해야 하는가"** 를 다루는 시큐어코딩 모범사례 모음임 — `secure-coding-plugin` 의 구현 지침
스킬(`secure-coding-java`/`-c`)과 층위가 가장 가까움. 국제 기준의 구현 권고가 필요할 때 우선 참조.

## MAS Checklist 폐지와 커스텀 뷰

OWASP 는 **MAS Checklist 를 2026-07-14 폐지**하고, 고정 체크리스트 대신 MASWE/MASTG 데이터에서
목적별 **커스텀 뷰를 생성해 쓰도록 권장**함. 이 스킬(`owasp-masvs`)의 색인·갭 대조 파일들이 바로
그 커스텀 뷰에 해당함 — 폐지된 Checklist 를 기준 문서로 인용하지 말 것.

## 사용법 — 상황별 라우팅

| 상황 | 참조할 구성요소 |
|---|---|
| 특정 MASWE 를 어떻게 점검하는지 | MASTG-TEST (`weakness:` 역참조로 검색, `tests-beta/` 우선) |
| 점검 절차의 실행 예제·샘플 코드 | MASTG-DEMO (`test:` 역참조로 검색) |
| Frida·apktool 등 도구 사용법 | MASTG-TOOL |
| 정적/동적 분석 기법 자체 | MASTG-TECH |
| 플랫폼 보안 메커니즘 배경 지식 | MASTG-KNOW |
| 시큐어코딩 구현 권고 | MASTG-BEST |
| 실습·검증용 대상 앱 | MASTG-APP |

레거시 `tests/`(92건, 전부 deprecated)는 `covered_by` 가 가리키는 신규 TEST-ID 로 갈아탈 것.

---

## 인용·전재 주의 (과잉 인용 금지)

- 이 파일은 CC BY-SA 4.0 원문의 구조 요약임 — MASTG 본문 해설·절차문을 전재하지 말 것
  (ShareAlike 전염 방지). 산출물에는 출처 4요소(출처·버전·라이선스·조회일)를 함께 기재할 것
