# 국내 설계단계 20개(SR1-1~SR4-1) ↔ ASVS 5.0.0 대응표

> **출처**: OWASP Application Security Verification Standard (ASVS) —
> `https://github.com/OWASP/ASVS` (구조화 데이터: 태그 `v5.0.0` 의 flat.json)
> **버전**: **ASVS 5.0.0** (2025-05-30) 기준. 부출처: 행정안전부·KISA
> 「소프트웨어 보안약점 진단가이드」(2021.11) 분석·설계단계 보안설계 기준 20개
> (SR 코드·기준명은 `secure-coding-kr` §5 및 `references/design-phase-20.md` 기준).
> **라이선스**: CC BY-SA 4.0 · **조회일**: 2026-09-17
>
> 이 파일은 원문 전재가 아니라 **요약·매핑**이다. 대응은 **챕터(주제) 수준**이며 요구사항
> 단위 동치가 아니다 — 요구사항 수준 단정은 태그 `v5.0.0` 원문 대조 후에만 한다.
> 제도 판정 근거가 아니며, ASVS 측 지적은 항상 "구속력 없음"을 병기한다.
>
> ⚠️ **버전 고정**: main 브랜치는 v5.0.0 과 다를 수 있다 — 반드시 태그로 조회할 것.

## 1. 대응 강도 범례

- **직접**: ASVS 챕터의 주제가 해당 SR 기준의 취지를 정면으로 다룬다.
- **부분**: 챕터의 일부 측면만 대응하거나, SR 취지의 일부만 겹친다.
- **없음**: 대응 챕터 부재 (역방향 공백은 §3).

## 2. SR 번호별 대응표 (20행)

| SR | 기준명 | 대응 ASVS 챕터 | 강도 | 비고 |
|---|---|---|---|---|
| SR1-1 | DBMS 조회 및 결과 검증 | V1 Encoding and Sanitization | 직접 | 인젝션 방어(인코딩·새니타이즈) 주제 |
| SR1-2 | XML 조회 및 결과 검증 | V1 Encoding and Sanitization | 직접 | |
| SR1-3 | 디렉토리 서비스 조회 및 결과 검증 | V1 Encoding and Sanitization | 직접 | |
| SR1-4 | 시스템 자원 접근 및 명령어 수행 입력값 검증 | V1 Encoding and Sanitization | 직접 | |
| SR1-5 | 웹 서비스 요청 및 결과 검증 | V1 · V2 Validation and Business Logic | 부분 | 입력 검증 관점만 — 프로토콜 수준(GraphQL·WebSocket 등)은 V4 소관이나 V4 는 국내 대응 없음(§3) |
| SR1-6 | 웹 기반 중요 기능 수행 요청 유효성 검증 | V2 Validation and Business Logic | 직접 | 비즈니스 로직 검증 주제 |
| SR1-7 | HTTP 프로토콜 유효성 검증 | V1 · V2 | 부분 | HTTP 메시지 구조 검증 자체는 V4.2 소관이나 V4 는 국내 대응 없음(§3) |
| SR1-8 | 허용된 범위내 메모리 접근 | V1 · V2 | 부분 | 웹 표준인 ASVS 에서 메모리 안전은 주변적 — 챕터 수준 대응(수집 데이터 기준) |
| SR1-9 | 보안기능 입력값 검증 | V1 · V2 | 직접 | |
| SR1-10 | 업로드·다운로드 파일 검증 | V5 File Handling | 직접 | |
| SR2-1 | 인증 대상 및 방식 | V6 Authentication | 직접 | |
| SR2-2 | 인증 수행 제한 | V6 Authentication | 직접 | |
| SR2-3 | 비밀번호 관리 | V6 Authentication | 직접 | ⚠️ **V6.2.5(조합 규칙 금지)·V6.2.10(정기 변경 강제 금지)과 정면 충돌** — SKILL.md §7. 제도 판정은 국내 기준 |
| SR2-4 | 중요자원 접근통제 | V8 Authorization | 직접 | |
| SR2-5 | 암호키 관리 | V11 Cryptography | 직접 | 알고리즘·키 길이의 국내 권고 판정은 `crypto-policy-kr` |
| SR2-6 | 암호연산 | V11 Cryptography | 직접 | |
| SR2-7 | 중요정보 저장 | V14 Data Protection | 직접 | |
| SR2-8 | 중요정보 전송 | V12 Secure Communication | 직접 | |
| SR3-1 | 예외처리 | V16 Security Logging and Error Handling | **부분** | ⚠️ §4 비대칭 — 에러처리만 대응, 로깅은 국내에 없음 |
| SR4-1 | 세션통제 | V7 Session Management | 직접 | 쿠키 보안 속성·응답 헤더는 V3 소관이나 V3 는 국내 대응 없음(§3) |

- 대응 챕터 배정은 수집 데이터(챕터 수준 대응표)에 근거한다. "직접/부분" 등급은 챕터 제목·주제와 SR 기준명의 대조에 따른 이 파일의 판정이며, 요구사항 단위 검증을 대신하지 않는다.

## 3. 역방향 요약 — 국내 SR 대응이 없는 ASVS 7개 챕터

ASVS 17챕터 중 아래 7개는 국내 설계단계 20개에 대응 항목이 **전무**하다 (합계 144개 요구사항 — 상세는 SKILL.md §6, 요구사항 수준은 `asvs-17-chapters.md`).

| 챕터 | 요구사항 | 영역 |
|---|---|---|
| V3 Web Frontend Security | 31 | CSP·CORS·쿠키 속성·SRI 등 브라우저 보안 메커니즘 |
| V4 API and Web Service | 16 | HTTP 메시지 구조·GraphQL·WebSocket |
| V9 Self-contained Tokens | 7 | JWT 류 토큰의 무결성·내용 검증 |
| V10 OAuth and OIDC | 36 | 위임 인가·연합 인증 (역할별 요구) |
| V13 Configuration | 21 | 백엔드 통신 구성·시크릿 관리·정보 누출 |
| V15 Secure Coding and Architecture | 21 | 아키텍처·의존성(공급망)·방어적 코딩·동시성 |
| V17 WebRTC | 12 | TURN·미디어·시그널링 |

## 4. SR3-1 ↔ V16 비대칭 주의 ⚠️

- V16 챕터명은 「Security Logging **and** Error Handling」— 두 주제의 결합 챕터다.
- 국내 SR3-1(예외처리)이 대응하는 것은 **에러처리 측면뿐**이다. 보안 로깅(이벤트 기록·경보) 요구는 국내 설계단계 20개에 대응 항목이 없다.
- 따라서 "SR3-1 준수 = V16 대응 완료"로 보고하면 로깅 측면이 통째로 누락된다. V16 은 L1 이 0개(L2 16·L3 1)라 L1 범위 점검에서도 빠진다는 점을 함께 유의하라.
- 같은 맥락: `secure-coding-kr` §10 의 Top 10:2025 A09(Security Logging and Alerting Failures)도 국내 49개 기준 대응 없음이다.

## 5. 원칙 재확인 — "미기재 ≠ 부적합"

- §2 의 "부분"·§3 의 "없음"은 국내 기준의 **결함 목록이 아니다**. 자매 파일 `masvs-gap-vs-mobile-app-verify.md` §6 의 원칙 그대로 — **미기재 ≠ 부적합**이며, 국내 문서의 침묵이 자동으로 현행 점검 대상·부적합 사유가 되는 것은 아니다.
- 공백 영역을 점검·지적할 때는 반드시 ① 출처를 ASVS 5.0.0 요구사항 ID 로 밝히고 ② **"구속력 없음"** 을 병기하며 ③ 제도 판정은 국내 기준(`secure-coding-kr`·`mobile-app-verify`)을 따른다.
