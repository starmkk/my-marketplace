---
name: owasp-masvs
description: |
  OWASP MASVS v2.1.0/MASWE v1.0.0/MASTG v2.0.0 모바일 앱 보안 국제표준 레퍼런스 스킬 — 국내 기준 공백 보완재.
  Reference for the OWASP Mobile Application Security ecosystem (MASVS/MASWE/MASTG), complementing Korean guidelines.

  사용자가 다음 표현을 쓸 때 반드시 이 스킬을 사용하라 (Trigger):
  - "MASVS", "MASTG", "MASWE", "모바일 앱 보안 국제표준"
  - "인증서 피닝", "WebView 보안", "탭재킹"
  - "Play Integrity", "App Attest", "앱 어테스테이션"
  WebView·딥링크·Keystore·생체인증 코드를 작성·수정할 때도 사용하라.

  경계: 국내 제도 판정=`mobile-app-verify`/`secure-coding-kr`, Java/Android 구현=`secure-coding-java`.
  주의: FV-5.1(변조 기능 금지)과 MASWE-0051(탐지 구현 의무)은 방향이 반대다 — 혼용 금지.
---

# OWASP MASVS 모바일 앱 보안 검증 레퍼런스 스킬

> 근거 문서: **OWASP MASVS v2.1.0**(2024-01-18, 8카테고리 24컨트롤) · **OWASP MASWE v1.0.0**(2026-08-17, 약점 78개) · **OWASP MASTG v2.0.0**(2026-06-30). 세 문서 모두 **CC BY-SA 4.0**. 조회일 **2026-09-17**.
> **인용 규약**: 세 문서는 웹 기반 living document 로 안정적 페이지 번호가 존재하지 않는다. 이 스킬은 기존 5종 스킬의 `(p.N)` 원문 페이지 병기 규약을 **대체하는 예외**로, 컨트롤 ID(`MASVS-STORAGE-1`)·약점 ID(`MASWE-0051`)·테스트 ID(`MASTG-TEST-02xx`)를 식별자로 쓰고 버전·조회일을 병기한다.

## 1. 개요

### 1.1 MAS 3문서 체계

| 문서 | 버전 | 역할 | 규모 |
|---|---|---|---|
| MASVS | v2.1.0 | **표준** — 무엇을 만족해야 하는가 (컨트롤) | 8카테고리 / 24컨트롤 |
| MASWE | v1.0.0 | **약점** — 컨트롤 위반이 구체적으로 무엇인가 | 78개 (MASWE-0001~0078) |
| MASTG | v2.0.0 | **시험 가이드** — 어떻게 점검·재현하는가 | TEST 292 · TECH 167 · TOOL 135 · DEMO 157 등 |

- MASVS 컨트롤은 v2 에서 추상 수준의 선언문 24개로 재편되었고, 점검 가능한 세부는 MASWE 가 담당한다.
- **이 스킬의 성격**: OWASP MAS 생태계 전체를 담은 레퍼런스가 아니라, **국내 기준(`mobile-app-verify` 등)의 공백을 메우는 보완재**다. 국내 기준이 이미 덮는 영역(SQL 삽입·암호화 저장 등)은 기존 스킬로 라우팅하고, 이 스킬은 국내 기준으로 지적할 수 없는 영역(§6)을 중심으로 다룬다.
- frontmatter 에 기존 5종과 달리 `관련 스킬:` 블록이 없는 것은 **의도된 예외**다 — frontmatter 예산(850자) 제약하에서 `경계:` 줄이 라우팅을 대신한다 (설계문서 쟁점 1 결정).

### 1.2 플러그인 안에서의 위치 — 상황별 라우팅

| 상황 | 이동할 스킬 |
|---|---|
| KISA 앱 검증 신청·제도 판정(부적합/보완요청) | 📕 `mobile-app-verify` |
| SW 보안약점 기준·진단절차·오탐/정탐 판정 | 📕 `secure-coding-kr` |
| Java/Android 취약→안전 코드 패턴 구현 | `secure-coding-java` |
| C/C++ (NDK 네이티브 모듈) 시큐어코딩 | `secure-coding-c` |
| 암호 알고리즘·키 길이·유효기간 선택 | `crypto-policy-kr` |
| 국내 기준 공백 영역의 국제 모범사례 점검 (§6) | **이 스킬** |
| 방향 반대 항목(루팅·탈옥)의 근거 문서 판별 | **이 스킬 §2** ↔ `mobile-app-verify` FV-5 |

### 1.3 v1 → v2 구조 변경

구버전 자료·보고서를 읽을 때 필요한 대응이다.

| 항목 | MASVS v1.5.0 (2023-01-31) | MASVS v2.1.0 (2024-01-18) |
|---|---|---|
| 구조 | V1~V8 그룹 | MASVS-XXXXX 8개 카테고리 |
| 요구사항 수 | 84개 | 24개 컨트롤로 추상화 |
| ID 접두사 | `MSTG-STORAGE-1` | `MASVS-STORAGE-1` |
| 레벨 | L1/L2/R 을 표준 본문에 내장 | 표준에서 제거 → MAS 프로파일로 이전 (§4) |
| V1 Architecture | 존재 | 삭제 — 프로세스 요구사항은 표준 범위 밖으로 정리 |
| 신설 | — | MASVS-PRIVACY 카테고리(컨트롤 4개) + CycloneDX 지원 |

- `MSTG-` 접두사 ID 를 만나면 **v1 기준 구버전 자료**다. v2 컨트롤로 번역하지 않고 그대로 인용하면 현행 표준과 어긋난다.

### 1.4 버전 고정 경고 ⚠️

이 스킬의 모든 수치·ID 는 **태그 고정판** 기준이다.

- MASWE 는 **v1.0.0 태그 기준 78개**(0001~0078)다. GitHub `main` 브랜치에는 **MASWE-0118 까지** 확장돼 있고 5번째 프로파일 **EUDIW**(EU Digital Identity Wallet)가 추가돼 있다 — main 브랜치 값을 이 스킬의 수치와 섞지 마라.
- 프로파일은 **v1.0.0 기준 4종**(L1·L2·R·P)만 다룬다 (§4).
- 상류 저장소가 갱신되면 이 수치는 낡는다. 인용 시 반드시 "v1.0.0 / 2026-09-17 조회" 를 병기하라.

## 2. `mobile-app-verify` 와의 경계 — 방향 반대 항목 경고 ⭐

**이 절이 이 스킬에서 가장 중요하다.** 국내 검증 가이드라인과 OWASP MAS 는 같은 단어를 쓰면서 점검 방향이 정반대인 항목을 가진다.

### 2.1 FV-5.1 ↔ MASWE-0051 — 같은 단어, 정반대 방향

| 구분 | 📕 `mobile-app-verify` FV-5.1 | 📋 이 스킬 MASWE-0051 |
|---|---|---|
| 점검 질문 | 앱이 루팅·탈옥을 **유발하는 기능을 갖고 있는가** | 앱이 루팅·탈옥 **탐지를 구현했는가** |
| 방향 | 플랫폼 보안모델 위배 **금지** (있으면 부적합) | 방어 기능 구현 **의무** (없으면 약점) |
| 소속 | 기능 보안취약점 FV-5 (제도 기준) | MASVS-RESILIENCE-1·RESILIENCE-4, MAS-R 프로파일 |
| 구속력 | 전자정부법 체계의 검증 기준 | 국제 모범사례 — **구속력 없음** |

### 2.2 오판 시나리오

- ❌ **시나리오 A (국내 기준 과잉 적용)**: 진단자가 "루팅 탐지가 구현되지 않았다"를 `mobile-app-verify` FV-5 위반으로 보고한다. → 오판이다. FV-5.1 은 변조를 *유발하는 기능의 부재*를 보는 항목이며, 원문은 루팅 탐지 API·구현 방법을 기재하지 않았다. 탐지 미구현은 국내 가이드라인을 근거로 지적할 수 없다.
- ❌ **시나리오 B (국제 기준 과잉 적용)**: 진단자가 MASWE-0051 을 근거로 "루팅 탐지 미구현 = 검증 부적합"이라고 보고한다. → 오판이다. MASWE 는 제도 판정 근거가 아니다. KISA 검증에서 부적합 사유가 되려면 원문 기준(FV-1~9, 소스코드 보안약점 26개)에 해당해야 한다.
- ❌ **시나리오 C (양방향 혼합)**: 하나의 보고서 항목 안에서 "FV-5(루팅·탈옥) 관련: 탐지 로직이 없으며 MASVS 위반"처럼 두 문서를 근거 구분 없이 병기한다. → 독자가 어느 쪽이 제도 판정인지 구분할 수 없어, 보완조치의 우선순위가 뒤집힌다.
- ✅ **올바른 서술**: "루팅 탐지 미구현 — 출처: OWASP MASWE-0051(v1.0.0, 2026-09-17 조회), MAS-R 프로파일 권고. **구속력 없음** — 국내 검증 기준(FV-5)은 별개 항목이며 이를 요구하지 않음."

### 2.3 역할 분담 규칙

- 📕 **국내 제도 판정**(KISA 앱 검증, 부적합/보완요청 판단) → `mobile-app-verify` 원문 기준. 진단가이드 기준·오탐 판정 → `secure-coding-kr`. 구현 코드 패턴 → `secure-coding-java`. 암호 알고리즘·키 길이 → `crypto-policy-kr`.
- 📋 **국제 모범사례 보강**(국내 기준이 침묵하는 영역의 현행 점검) → 이 스킬.
- **이 스킬은 제도 판정 근거가 아니다.** 이 스킬의 내용으로 지적할 때는 반드시 ① 출처를 OWASP MASVS/MASWE 로 밝히고 ② **"구속력 없음"** 을 병기하라. "미기재 ≠ 부적합" 원칙(`mobile-app-verify` §6 각주)이 양방향으로 적용된다.

### 2.4 참고 — 관리지침 별표1 항목 9

- `mobile-app-verify` 가 기록한 관리지침 별표1 대응 항목명은 **"9. 루팅 및 탈옥 기기에서의 정상 동작"** 이다 (원문 p.36 기재를 재인용).
- 이 항목명 역시 "탐지·차단 구현"이 아니라 변조 기기 환경에서의 동작을 보는 표현이어서, MAS-R 의 탐지 의무와 같은 방향이라고 단정할 수 없다. **항목의 정확한 취지는 관리지침 원문 확인이 필요**하다 — 항목명만으로 MASWE-0051 과 등치하지 마라.

## 3. 24개 컨트롤 총괄

### 3.1 카테고리 요약

소속 MASWE 수는 **약점 파일의 소속 카테고리 기준**이며 합계 78이다.

| 카테고리 | 컨트롤 수 | 소속 MASWE 수 |
|---|---|---|
| MASVS-STORAGE | 2 | 6 |
| MASVS-CRYPTO | 2 | 11 |
| MASVS-AUTH | 3 | 8 |
| MASVS-NETWORK | 2 | 3 |
| MASVS-PLATFORM | 3 | 12 |
| MASVS-CODE | 4 | 10 |
| MASVS-RESILIENCE | 4 | 15 |
| MASVS-PRIVACY | 4 | 13 |
| **합계** | **24** | **78** |

- 개별 MASWE 는 여러 컨트롤에 **다중 매핑**된다(예: MASWE-0001 은 STORAGE-1·STORAGE-2·CRYPTO-2 에 동시 매핑). 아래 3.2 의 "매핑 MASWE" 열은 다중 매핑을 포함하므로 컨트롤 단위로 합산하면 78을 넘는다 — 수치 인용 시 집계 기준을 명시하라.
- 컨트롤 원문 전문은 `references/masvs-24-controls.md`, 78개 약점 전수 색인은 `references/maswe-78.md` 참조.

### 3.2 컨트롤 × 매핑 MASWE 전체 표

한국어 요약은 원문 취지의 축약이다 (MASWE 번호는 `MASWE-` 접두사 생략 표기).

| ID | 한국어 요약 | 매핑 MASWE (다중 매핑 포함) |
|---|---|---|
| MASVS-STORAGE-1 | 민감 데이터를 안전하게 저장한다 | 0001·0002·0003·0004 |
| MASVS-STORAGE-2 | 민감 데이터의 유출을 방지한다 | 0001·0002·0005·0006·0018·0029·0030·0031·0032·0033·0034·0036·0037·0038·0040 |
| MASVS-CRYPTO-1 | 현행 강력한 암호를 업계 모범사례에 따라 사용한다 | 0007·0008·0009·0010·0011·0012·0047 |
| MASVS-CRYPTO-2 | 키 관리를 업계 모범사례에 따라 수행한다 | 0001·0003·0007·0009·0010·0013·0014·0015·0016·0017·0020·0022·0046 |
| MASVS-AUTH-1 | 안전한 인증·인가 프로토콜과 관련 모범사례를 따른다 | 0018·0019·0047 |
| MASVS-AUTH-2 | 로컬 인증을 플랫폼 모범사례에 따라 안전하게 수행한다 | 0016·0020·0021·0022 |
| MASVS-AUTH-3 | 민감한 작업을 추가 인증으로 보호한다 | 0016·0019·0023·0024·0025 |
| MASVS-NETWORK-1 | 모든 네트워크 트래픽을 현행 모범사례에 따라 보호한다 | 0026·0027·0047·0062 |
| MASVS-NETWORK-2 | 개발자 통제하의 모든 원격 엔드포인트에 아이덴티티 피닝을 수행한다 | 0028 |
| MASVS-PLATFORM-1 | IPC 메커니즘을 안전하게 사용한다 | 0018·0029·0030·0031·0032 |
| MASVS-PLATFORM-2 | WebView 를 안전하게 사용한다 | 0033·0034·0035·0063 |
| MASVS-PLATFORM-3 | 사용자 인터페이스를 안전하게 사용한다 | 0023·0036·0037·0038·0039·0040 |
| MASVS-CODE-1 | 최신 플랫폼 버전을 요구한다 | 0039·0041·0042 |
| MASVS-CODE-2 | 앱 업데이트를 강제하는 메커니즘을 갖춘다 | 0043 |
| MASVS-CODE-3 | 알려진 취약점이 없는 소프트웨어 컴포넌트만 사용한다 | 0044·0045·0046·0047·0048 |
| MASVS-CODE-4 | 신뢰할 수 없는 모든 입력을 검증·정화한다 | 0029·0034·0035·0045·0049·0050·0057 |
| MASVS-RESILIENCE-1 | 플랫폼의 무결성을 검증한다 | 0051·0052·0053·0054 |
| MASVS-RESILIENCE-2 | 안티탬퍼링 메커니즘을 구현한다 | 0055·0056·0057·0058 |
| MASVS-RESILIENCE-3 | 정적분석 방지 메커니즘을 구현한다 | 0059·0060·0061·0062 |
| MASVS-RESILIENCE-4 | 동적분석 방지 기법을 구현한다 | 0051·0053·0063·0064·0065 |
| MASVS-PRIVACY-1 | 민감 데이터·자원에 대한 접근을 최소화한다 | 0066·0073 |
| MASVS-PRIVACY-2 | 사용자 식별을 방지한다 | 0067·0068·0069·0070·0071 |
| MASVS-PRIVACY-3 | 데이터 수집·이용을 투명하게 공개한다 | 0072·0073·0074·0075 |
| MASVS-PRIVACY-4 | 사용자에게 자기 데이터에 대한 통제권을 제공한다 | 0076·0077·0078 |

### 3.3 카테고리별 국내 스킬 라우팅

카테고리마다 국내 기준과의 관계가 다르다 — 겹침 판단의 개요다 (전수 매핑은 `references/masvs-gap-vs-mobile-app-verify.md`).

| 카테고리 | 국내 기준과의 관계 | 우선 라우팅 |
|---|---|---|
| STORAGE | FV-4(중요정보 암호화 저장)와 겹침 큼 — 제도 판정은 국내 기준 | 📕 `mobile-app-verify` |
| CRYPTO | 보안기능 유형 약점·암호 정책과 겹침 큼. 국산 암호·키 길이는 국내 전용 영역 | 📕 `crypto-policy-kr` |
| AUTH | AUTH-1 은 FV-4.6 과 부분 겹침, **AUTH-2·AUTH-3 은 국내 공백** (§6.1) | 이 스킬 (공백부) |
| NETWORK | NETWORK-1 은 암호화 전송 요구와 겹침, **NETWORK-2(피닝)는 국내 공백** (§6.1) | 이 스킬 (공백부) |
| PLATFORM | PLATFORM-1 은 모바일 특화 약점 6개와 겹침 큼, **PLATFORM-2·3 은 국내 공백** (§6.1) | 혼합 |
| CODE | CODE-3·4 는 FV-6·FV-3·입력검증 약점과 겹침 큼, CODE-1·2 는 공백에 가까움 | 혼합 |
| RESILIENCE | RESILIENCE-2·3 은 FV-8·FV-9.2 와 겹침, RESILIENCE-1 은 **방향 반대**(§2), RESILIENCE-4 는 공백 | 혼합 — §2 필독 |
| PRIVACY | PRIVACY-1·4 는 FV-2.4·FV-4.5 와 부분 겹침, PRIVACY-2·3 은 재분류 여지 (§6.2) | 혼합 |

## 4. MAS 프로파일 선택 가이드

v2.0.0 부터 MASVS 는 검증 레벨을 표준 본문에 **포함하지 않는다**. 공식 문구: *"Starting on v2.0.0 the MASVS does not contain 'verification levels'. … reworked as 'MAS Testing Profiles' and moved over to the OWASP MASWE."* — 레벨은 MASWE 쪽의 **MAS 테스팅 프로파일**로 이전되었다. 즉 "MASVS L2 인증" 같은 표현은 v2 체계에서 부정확하며, "MAS-L2 프로파일 기준 점검"이 맞는 표현이다.

### 4.1 프로파일 4종 (v1.0.0 기준)

| 프로파일 | 공격자 모델 (📋 원문 취지) | 적용 MASWE 수 |
|---|---|---|
| MAS-L1 Essential Security | 기기에 설치된 **다른 앱**이 공격자 | 29 |
| MAS-L2 Advanced Security | **OS 를 신뢰할 수 없고** 공격자가 기기에 물리 접근 가능 | 50 |
| MAS-R Resilient Security | **기기 사용자 본인**이 공격자 (리버스 엔지니어·치터) | 15 |
| MAS-P Baseline Privacy | 공격자 중심이 아님 — 개인정보 보호·책임 있는 데이터 처리 | 13 |

⚠️ main 브랜치의 5번째 프로파일 MAS-EUDIW 는 v1.0.0 체계 밖이다 — 이 스킬 범위에서 제외 (§1.4).

### 4.2 어떤 앱에 어느 프로파일인가 (✅ 현행 권고 — 공격자 모델에서 도출)

- **모든 앱**: L1 이 기본선이다. L1 과 L2 는 상하위 관계가 아니라 공격자 모델이 다른 별도 프로파일이므로, 대상 위협에 따라 조합한다.
- **민감 데이터를 다루는 앱**(전자정부·금융·의료): L1 + L2. 기기 분실·도난, 신뢰할 수 없는 OS 시나리오가 위협 모델에 포함되기 때문이다.
- **사용자 본인의 조작이 위협인 앱**(금융 부정거래 방지, 게임 치팅 방지, DRM): 위 조합 + R. R 프로파일 15개는 전부 RESILIENCE 카테고리다. ✅ 기기·앱 어테스테이션(MASWE-0054·0056)의 현행 플랫폼 수단은 Google **Play Integrity** API 와 Apple **App Attest** 다.
- **개인정보를 처리하는 앱**: + P. 국내에서는 개인정보 보호법이 제도 기준이므로 P 는 참고용이다 (§6.2).
- 📕 국내 KISA 검증 신청 앱이라면 프로파일 선택과 무관하게 `mobile-app-verify` 의 51개 검증 항목이 우선 적용된다 — 프로파일은 그 위에 얹는 자율 점검 범위 설정 도구다.

### 4.3 프로파일별 MASWE 구성 (v1.0.0 실측)

폐지된 체크리스트를 대신해 프로파일로 점검 범위를 필터링할 때(§7 워크플로 ②단계)의 기준 데이터다.

**MAS-L1 (29개)** — 카테고리별 구성:

| 카테고리 | MASWE (접두사 생략) | 수 |
|---|---|---|
| STORAGE | 0002·0003·0004·0005·0006 | 5 |
| CRYPTO | 0007·0008·0009·0010·0011·0012·0013·0014 | 8 |
| AUTH | 0018·0019 | 2 |
| NETWORK | 0026·0027 | 2 |
| PLATFORM | 0029·0030·0031·0032·0033·0034·0035 | 7 |
| CODE | 0042·0044·0047·0048·0050 | 5 |

**MAS-L2 (50개)** — 위 L1 29개 전부 + L2 전용 21개:

| 카테고리 | L2 전용 MASWE | 수 |
|---|---|---|
| STORAGE | 0001 | 1 |
| CRYPTO | 0015·0016·0017 | 3 |
| AUTH | 0020·0021·0022·0023·0024·0025 | 6 |
| NETWORK | 0028 | 1 |
| PLATFORM | 0036·0037·0038·0039·0040 | 5 |
| CODE | 0041·0043·0045·0046·0049 | 5 |

**MAS-R (15개)**: MASWE-0051~0065 연번 전체 = RESILIENCE 카테고리 전체.
**MAS-P (13개)**: MASWE-0066~0078 연번 전체 = PRIVACY 카테고리 전체.

- v1.0.0 의 프로파일 구획은 깔끔하다 — R 과 P 는 카테고리와 1:1 로 일치하고, L1/L2 는 STORAGE~CODE 6개 카테고리를 나눠 가진다. L1 ⊂ L2 (v1.0.0 기준 L1 29개는 전부 L2 에도 속한다).

## 5. 추적 체인 — MASVS → MASWE → TEST → DEMO

### 5.1 렌더링 방향과 실제 저장 방향

렌더링된 웹 페이지에서는 다음 정방향 체인으로 보인다.

```
MASVS 컨트롤 ─→ MASWE 약점 ─→ MASTG-TEST 시험 ─→ MASTG-DEMO 재현 데모
(무엇을)        (무엇이 틀렸나)   (어떻게 점검하나)     (실제 재현 코드)
```

**그러나 소스 저장소의 실제 저장 방향은 역참조다** (v1.0.0/v2.0.0 실측):

| 연결 | 저장 위치와 방향 |
|---|---|
| MASWE → MASVS | MASWE 파일 frontmatter `mappings.masvs-v2:` 가 소속 컨트롤을 가리킴 (**정방향**) |
| TEST → MASWE | MASWE 파일에는 test 목록 필드가 **없다**. MASTG-TEST frontmatter 의 `weakness: MASWE-XXXX` 가 **역참조** |
| DEMO → TEST | MASTG-TEST 에도 demo 링크 필드가 **없다** (`tests-beta/` 200건 중 demo 필드 보유 0건). MASTG-DEMO frontmatter 의 `test: MASTG-TEST-XXXX` 가 **역참조** |

즉 실제 방향은 `MASWE ← MASTG-TEST ← MASTG-DEMO` 다. 웹사이트의 "이 약점에 연결된 Tests" 목록은 빌드 시점에 역참조를 수집해 동적 생성한 것이며 소스에 정적으로 존재하지 않는다.

### 5.2 실무 검색 레시피 (✅ 방법 예시)

저장소(태그 고정판)에서 특정 약점의 시험·데모를 찾을 때는 **역참조 방향으로 검색**한다.

```bash
# MASWE-0051 을 점검하는 시험 찾기 — MASWE 파일이 아니라 TEST 쪽을 검색
grep -rl "weakness: MASWE-0051" tests-beta/

# 특정 시험의 재현 데모 찾기 — TEST 파일이 아니라 DEMO 쪽 frontmatter 의 test: 값을 검색
grep -rl "MASTG-TEST-0234" . --include="*.md" | grep -i demo
```

- MASWE 파일 안에서 test 목록을 찾으려 하면 **아무것도 나오지 않는 것이 정상**이다 — 필드 자체가 없다.
- 검색 대상 저장소는 반드시 태그(`v1.0.0`/`v2.0.0`)로 체크아웃하라. main 은 §1.4 의 확장분이 섞인다.

### 5.3 MASTG v2.0.0 구성 개요 (실측 요약)

| 구성요소 | 총 파일 수 | 상태 분포 |
|---|---|---|
| MASTG-TEST | 292 (레거시 92 + 신규 200) | 현행 186 · placeholder 14 · deprecated 92 |
| MASTG-TECH | 167 | 현행 165 · deprecated 1 · placeholder 1 |
| MASTG-TOOL | 135 | 현행 129 · deprecated 6 |
| MASTG-DEMO | 157 | 현행 150 · placeholder 6 · draft 1 |
| MASTG-KNOW | 140 | 현행 132 · deprecated 2 · placeholder 6 |
| MASTG-BEST | 74 | 현행 66 · placeholder 8 |
| MASTG-APP | 29 | 현행 28 · deprecated 1 |

- 레거시 `tests/` 92건은 **전부 deprecated** 이며 `covered_by` 필드로 신규 TEST ID 를 지시한다 — 인용 전 deprecated 여부를 확인하라.
- ⚠️ 플랫폼 분포(android 161 · ios 129 · network 2)는 **deprecated 포함 292건 전체 기준**이다. 현행 186건만의 분포가 아니므로 분모를 섞지 마라.
- 상세는 `references/mastg-structure.md` 참조.

## 6. 국내 기준으로 지적할 수 없는 영역 — 확정 6 + 재분류 여지 2 ⭐

이 절이 이 스킬의 핵심 부가가치다. 용어에 주의하라 — 아래는 국내 기준이 "커버하지 못한" 결함 목록이 아니라, **「모바일 전자정부서비스 앱 소스코드 검증 가이드라인」을 근거로는 지적할 수 없는 영역**이다("미기재 ≠ 부적합"). 이 영역을 점검하려면 이 스킬(OWASP 근거·구속력 없음 병기)을 사용한다.

### 6.1 확정 6개 — 공백이 확인된 영역

| MASVS 컨트롤 | 영역 | 해당 MASWE | 공백 확인 근거 |
|---|---|---|---|
| MASVS-NETWORK-2 | 인증서 피닝 | 0028 | 📕 `mobile-app-verify` §6 표가 SSL Pinning 을 원문 미기재로 명시하며 *"현행 점검 권장(출처: OWASP MASVS — 구속력 없음)"* 으로 **이 문서를 직접 지목** |
| MASVS-PLATFORM-3 | 화면캡처·알림 노출·오버레이·접근성 유출 | 0036~0040 | §6 표에 "화면 캡처 방지/키보드 보안", "접근성 서비스 악용" 원문 미기재 명시 |
| MASVS-RESILIENCE-4 | 디버거·동적분석 도구 탐지 | 0063~0065 (+0051·0053 공유) | §6 표에 "디버깅 탐지", "에뮬레이터·후킹 탐지" 원문 미기재 명시 |
| MASVS-PLATFORM-2 | WebView 보안 전체 | 0033~0035 (+0063 공유) | 하이브리드 앱(앱+웹)이 검증 대상에 **명시 포함**(원문 p.11)되므로 적용 대상 밖이 아니라 실제 공백 |
| MASVS-AUTH-2 | 생체인증 우회 방지·키 무효화 | 0020~0022 (+0016 공유) | FV-4.2 는 바이오정보의 일방향 암호화 **저장**만 규정 — 인증 우회·폴백·재등록 시 키 무효화는 규정 없음 |
| MASVS-AUTH-3 | Step-up 인증·부인방지 | 0023~0025 (+0016·0019 공유) | 국내 51개 항목에 대응 항목 없음 |

각 영역의 요지와 점검 포인트 (✅ 표기 항목은 현행 플랫폼 관행 기준 권고이며, 구현 코드 상세는 `secure-coding-java` 로 라우팅):

**① MASVS-NETWORK-2 — 인증서 피닝 (MASWE-0028, L2)**
- 국내 원문은 TLS/E2E 암호화를 "권고" 수준으로만 기술한다. 인증서 유효성 검증 자체는 진단가이드 기준 28 소관 → `secure-coding-kr`.
- 📋 MASWE-0028 은 피닝의 단순 부재가 아니라 **불안전한 피닝**(백업 핀 없음·만료 무대응·핀 하드코딩 관리 부실)까지 다룬다.
- ✅ 점검: Android Network Security Config 의 `<pin-set>` 선언 여부·만료일, iOS `NSPinnedDomains`, 서드파티 피닝 라이브러리의 실패 처리(fail-open 여부).

**② MASVS-PLATFORM-3 — UI 보안 (MASWE-0036~0040, L2)**
- 구성: UI 상 불필요 노출(0036) · 알림 민감정보(0037) · 화면캡처/녹화 미차단(0038) · 오버레이 공격/탭재킹(0039) · 접근성 서비스 유출(0040).
- ✅ 점검: 민감 화면의 `FLAG_SECURE`(Android)·화면전환 스냅숏 마스킹(iOS), 알림 본문의 민감정보 포함 여부, `filterTouchesWhenObscured` 등 오버레이 대응, 접근성 이벤트로 노출되는 필드.

**③ MASVS-RESILIENCE-4 — 동적분석 방지 (MASWE-0063~0065, R)**
- 구성: 디버그 메커니즘 미비활성화(0063) · 디버거 탐지 미구현(0064) · 동적분석 도구(Frida 류) 탐지 미구현(0065).
- R 프로파일 소속 — **자율 강화 항목이지 의무가 아니다.** 지적 시 "MAS-R 채택을 전제로 한 권고"임을 명시하라.
- ✅ 점검: release 빌드의 `android:debuggable` 값, 디버거 attach 탐지·대응 로직 유무, 알려진 계측 도구 흔적 탐지 여부.

**④ MASVS-PLATFORM-2 — WebView 보안 (MASWE-0033~0035, L1/L2)**
- 구성: 네이티브 기능 노출(0033, `addJavascriptInterface` 류) · 로컬 리소스 접근 허용(0034, file 접근 설정) · 신뢰할 수 없는 콘텐츠 로딩(0035).
- **하이브리드 전자정부 앱 점검에서 실질 효용이 가장 큰 영역**이다 — 국내 검증 대상에 하이브리드 앱이 포함되는데 원문에 WebView 항목이 없다.
- ✅ 점검: JavaScript 활성화 필요성, 브리지 인터페이스에 노출된 메서드 목록, `file://`·`content://` 접근 설정, 로딩 URL 의 출처 검증(허용 목록).

**⑤ MASVS-AUTH-2 — 로컬(생체) 인증 (MASWE-0020~0022, L2)**
- 구성: 로컬 인증 우회 가능(0020) · 민감 거래의 비생체 폴백 허용(0021) · 신규 생체 등록 시 키 미무효화(0022).
- 핵심 관점: 생체인증이 **이벤트 확인(불리언 결과)** 에 그치는지, **암호학적 결합**(인증 성공 시에만 키 사용 가능)인지.
- ✅ 점검: Android `BiometricPrompt` + `CryptoObject` 결합 여부, Keystore 키 생성 시 `setUserAuthenticationRequired(true)`·`setInvalidatedByBiometricEnrollment(true)` 상당 설정, iOS LAContext 단독 사용 여부.
- 📕 국내 기준으로는 FV-4.2(바이오정보 일방향 암호화 저장)와 FV-4.6(인증 방법 적절성)까지만 지적 가능하다.

**⑥ MASVS-AUTH-3 — 추가 인증 (MASWE-0023~0025, L2)**
- 구성: 민감 작업 전 Step-up 재인증 부재(0023) · 세션 종료 후 민감 데이터 접근 가능(0024) · 중요 행위의 부인방지 결여(0025).
- ✅ 점검: 송금·개인정보 변경 등 민감 트랜잭션 직전의 재인증 요구, 로그아웃/세션 만료 후 캐시·화면 스택의 민감 데이터 잔존, 중요 행위의 서명·감사 기록.

**확정 6개 영역 소속 MASWE 명세** (v1.0.0 원문 제목 + 한국어 요지):

| ID | 원문 제목 (EN) | 요지 | 프로파일 |
|---|---|---|---|
| MASWE-0028 | Insecure Identity Pinning | 아이덴티티 피닝 미적용·부실 적용 | L2 |
| MASWE-0033 | Sensitive Native Functionality Exposed in WebViews | WebView 에 민감 네이티브 기능 노출 | L1·L2 |
| MASWE-0034 | WebViews Allow Access to Local Resources with Untrusted Content | 신뢰 불가 콘텐츠에 로컬 리소스 접근 허용 | L1·L2 |
| MASWE-0035 | WebViews Loading Untrusted Content | WebView 의 신뢰 불가 콘텐츠 로딩 | L1·L2 |
| MASWE-0036 | Unnecessary Exposure of Sensitive Data via the User Interface | UI 를 통한 민감정보 불필요 노출 | L2 |
| MASWE-0037 | Unnecessary Exposure of Sensitive Data via Notifications | 알림을 통한 민감정보 노출 | L2 |
| MASWE-0038 | Insufficient Protection of Sensitive Data from Screenshots or Screen Recordings | 스크린샷·화면녹화로부터의 보호 미흡 | L2 |
| MASWE-0039 | App Vulnerable to Overlay Attacks | 오버레이 공격에 취약 | L2 |
| MASWE-0040 | Sensitive Data Leaked via Accessibility Services | 접근성 서비스를 통한 민감정보 유출 | L2 |
| MASWE-0020 | Local Authentication Can Be Bypassed | 로컬 인증 우회 가능 | L2 |
| MASWE-0021 | Fallback to Non-biometric Credentials Allowed for Sensitive Transactions | 민감 거래에서 비생체 폴백 허용 | L2 |
| MASWE-0022 | Crypto Keys Not Invalidated on New Biometric Enrollment | 신규 생체 등록 시 암호키 미무효화 | L2 |
| MASWE-0023 | Step-Up Authentication Not Implemented for Sensitive Actions | 민감 작업의 Step-up 인증 미구현 | L2 |
| MASWE-0024 | Sensitive Data Accessible After Session Termination | 세션 종료 후 민감 데이터 접근 가능 | L2 |
| MASWE-0025 | Lack of Non-Repudiation for Critical Actions | 중요 행위의 부인방지 결여 | L2 |
| MASWE-0063 | Debug Mechanisms Not Disabled | 디버그 메커니즘 미비활성화 | R |
| MASWE-0064 | Debugger Detection Not Implemented | 디버거 탐지 미구현 | R |
| MASWE-0065 | Dynamic Analysis Tools Detection Not Implemented | 동적분석 도구 탐지 미구현 | R |

### 6.2 재분류 여지 2개 — "타 문서 소관"일 가능성이 있는 영역

| MASVS 컨트롤 | 영역 | 해당 MASWE | 재분류 사유 |
|---|---|---|---|
| MASVS-PRIVACY-2 | 익명화·가명화, 추적 식별자 사용 | 0067~0071 | **개인정보 보호법 소관**일 수 있음 — `mobile-app-verify` §6 각주의 5분류상 "타 문서 소관" 가능성. 소스코드 검증 가이드라인의 공백이라 단정하지 않는다 |
| MASVS-PRIVACY-3 | 스토어 데이터 수집 라벨, 재현 가능 빌드 | 0072~0075 | 스토어 라벨(0073·0074)은 **배포 단계 사안**으로 소스코드 검증 범위 밖일 여지. 재현 가능 빌드(0075)는 공백으로 보이나 확정 근거 부족 |

**재분류 여지 2개 영역 소속 MASWE 명세** (전부 P 프로파일):

| ID | 원문 제목 (EN) | 요지 |
|---|---|---|
| MASWE-0067 | Lack of Anonymization or Pseudonymisation Measures | 익명화·가명화 조치 결여 |
| MASWE-0068 | Incorrect Use of Identifiers for User Tracking | 사용자 추적 식별자 오용 |
| MASWE-0069 | Usage of Non-Privacy-Preserving Functionality | 프라이버시 비보존 기능 사용 |
| MASWE-0070 | Inadequate Awareness for Privacy Relevant Actions | 프라이버시 관련 행위의 고지 미흡 |
| MASWE-0071 | Inadequate Defaults for Privacy Relevant Actions | 프라이버시 관련 기본값 부적절 |
| MASWE-0072 | Inadequate Privacy Policy | 개인정보처리방침 미흡 |
| MASWE-0073 | Inadequate Data Collection Declarations | 데이터 수집 선언(스토어 라벨) 미흡 |
| MASWE-0074 | Inadequate Tracking Domains Declarations | 추적 도메인 선언 미흡 |
| MASWE-0075 | Non-Reproducible Builds | 재현 불가능한 빌드 |

- 재분류 여지 2개를 지적할 때는 확정 6개보다 한 단계 더 조심하라 — "국내 가이드라인 미기재"까지만 말할 수 있고, 국내 제도 전체의 공백이라고 말할 수 없다(개인정보 보호법·스토어 정책이 별도로 규율할 수 있다).

### 6.3 지적 서술 템플릿

이 스킬을 근거로 발견사항을 기록할 때의 정형 문구다.

```
[권고] WebView 브리지에 불필요한 네이티브 메서드 노출
- 출처: OWASP MASWE-0033 (MASVS-PLATFORM-2), MASWE v1.0.0, 2026-09-17 조회
- 성격: 국제 모범사례 권고 — 구속력 없음. 국내 검증 가이드라인(2021.10)에는
  대응 항목이 없어 해당 문서를 근거로는 지적 불가(미기재 ≠ 부적합).
- 권고 조치: (구현 상세는 `secure-coding-java` 참조)
```

- 24개 컨트롤 전체와 `mobile-app-verify` 51항목의 대응·겹침·방향 반대 전수 매핑은 `references/masvs-gap-vs-mobile-app-verify.md` 참조.

## 7. MAS Checklist 폐지와 대체 워크플로

- OWASP 는 공식 MAS Checklist(엑셀)를 **2026-07-14 폐지**했다. 폐지 사유(공식): 정적 산출물 대신 **구조화 메타데이터**를 쓰고, AI assisted workflows 를 포함한 **커스텀 뷰를 각자 생성**하라는 것.
- ❌ 따라서 "MASVS 체크리스트 엑셀을 내려받아 점검하라"는 안내는 더 이상 유효하지 않다. 구버전 엑셀 파일이 사내에 남아 있어도 현행 점검 기준으로 쓰지 마라 — 폐지 시점 이후의 MASWE/MASTG 변경이 반영되지 않는다.

| 구분 | 폐지 전 (~2026-07-14) | 폐지 후 (현행) |
|---|---|---|
| 산출물 | OWASP 공식 엑셀 체크리스트 | 구조화 메타데이터(MASWE/MASTG frontmatter) 기반 **커스텀 뷰** |
| 갱신 주체 | OWASP 가 릴리스마다 배포 | 사용자가 태그 고정 데이터로 자체 생성·갱신 |
| 점검 범위 결정 | 엑셀 시트의 레벨 열 필터 | 프로파일(L1/L2/R/P) 기준 MASWE 필터링 (§4.3) |
| 이 스킬의 대응 | — | references 4종이 로컬 커스텀 뷰 역할 |

- 폐지 이후의 표준 워크플로는 다음과 같다.

```
① 프로파일 선택 (§4.2)        — 위협 모델에 따라 L1/L2/R/P 조합 결정
② MASWE 필터링 (§4.3)         — 선택한 프로파일 소속 약점 추출
                                (references/maswe-78.md 색인 활용)
③ MASTG-TEST 역참조 검색 (§5.2) — weakness: 필드로 해당 약점의 시험 절차 수집
④ 시험 수행·기록 (§6.3)        — 약점 ID·테스트 ID·버전·조회일을 보고서에 병기
```

- 이 스킬의 references 4종이 ①~③단계의 로컬 데이터 역할을 한다 — 즉 이 스킬 자체가 "커스텀 뷰" 방식의 구현이다.

## 8. 점검 체크리스트

국내 검증 대상 앱에 OWASP 관점 보강 점검을 수행할 때의 순서다.

**[사전 확인]**
- [ ] 이 점검이 📕 제도 검증(KISA 신청)인지 📋 자율 보강 점검인지 구분했는가 — 제도 검증이면 `mobile-app-verify` 를 먼저 적용
- [ ] 위협 모델에 따라 프로파일 조합(L1/L2/R/P)을 선택했는가 (§4.2)
- [ ] 인용할 저장소를 태그(v1.0.0/v2.0.0)로 고정했는가 — main 브랜치 혼입 금지 (§1.4)
- [ ] 보고서 서식에 "출처: OWASP MASVS/MASWE vX.Y.Z, 조회일, 구속력 없음" 병기 칸을 마련했는가 (§2.3, §6.3)

**[국내 기준으로 지적할 수 없는 영역 — §6.1 확정 6개]**
- [ ] NETWORK-2: 피닝 적용 여부·백업 핀·만료 대응·실패 처리 (MASWE-0028)
- [ ] PLATFORM-2: WebView 브리지 노출·file 접근 설정·로딩 콘텐츠 출처 검증 (MASWE-0033~0035)
- [ ] PLATFORM-3: 화면캡처 차단·알림 민감정보·오버레이 대응·접근성 유출 (MASWE-0036~0040)
- [ ] AUTH-2: 생체인증-키스토어 암호학적 결합·폴백 정책·재등록 시 키 무효화 (MASWE-0020~0022)
- [ ] AUTH-3: 민감 작업 재인증·세션 종료 후 데이터 잔존·부인방지 (MASWE-0023~0025)
- [ ] RESILIENCE-4: (R 채택 시) 디버거·동적분석 도구 탐지, 디버그 메커니즘 비활성화 (MASWE-0063~0065)

**[재분류 여지 영역 — §6.2]**
- [ ] PRIVACY-2·3 지적 시 "국내 가이드라인 미기재"까지만 서술했는가 — 개인정보 보호법 등 타 규율 존재 가능성 병기

**[방향 반대 오판 방지 — §2]**
- [ ] "루팅·탈옥" 관련 발견사항의 근거 문서를 명시했는가 — FV-5.1(변조 기능 금지)과 MASWE-0051(탐지 구현 의무)을 혼용하지 않았는가
- [ ] OWASP 근거 지적에 전부 "구속력 없음"을 병기했는가

**[결과 처리]**
- [ ] 국내 기준 해당 발견사항은 해당 스킬로 라우팅했는가 — 소스코드 보안약점 → `secure-coding-kr`/`secure-coding-java`, 암호 → `crypto-policy-kr`
- [ ] deprecated MASTG-TEST(레거시 92건)를 인용하지 않았는가 — `covered_by` 의 신규 TEST ID 로 대체 (§5.3)
- [ ] 모든 수치·ID 에 버전(v1.0.0/v2.0.0/v2.1.0)과 조회일(2026-09-17)을 병기했는가 (§1.4)

## 9. 원문 범위 밖 / 확인 필요

이 스킬이 다루지 않거나, 데이터 수집 범위의 한계로 단정할 수 없는 항목이다.

| 항목 | 상태 |
|---|---|
| MASWE 개별 항목의 본문 상세(공격 시나리오·완화책 서술) | **수집 범위 밖** — 이 스킬의 데이터는 v1.0.0 frontmatter(ID·제목·매핑·프로파일) 전수 파싱 기준. 본문 세부는 원문 페이지에서 확인하라 |
| MASTG-TEST 개별 시험 절차의 단계별 상세 | **수집 범위 밖** — 규모·상태 분포만 실측(`references/mastg-structure.md`). 절차는 원문 확인 필요 |
| 관리지침 별표1 "루팅 및 탈옥 기기에서의 정상 동작" 항목의 정확한 취지 | **확인 필요** — 항목명만 재인용 가능 (§2.4). 관리지침 원문 미확인 상태에서 MASWE-0051 과의 방향 관계를 단정하지 않는다 |
| 컨트롤별 정확한 다중 매핑 수치 | 다중 매핑 특성상 집계 기준에 따라 달라짐 (§3.1) — 컨트롤 단위 수치 인용 전 §3.2 표 또는 `references/masvs-24-controls.md` 기준 확인 |
| MAS-EUDIW 프로파일, MASWE-0079 이후 | **범위 밖** — main 브랜치 확장분 (§1.4). 혼입 금지 |
| MASWE ↔ 국내 소스코드 보안약점 26개의 항목 단위 정밀 대응 | **확인 필요** — `references/masvs-gap-vs-mobile-app-verify.md` 는 컨트롤 단위 매핑이며, 약점 단위 전수 대응은 작성하지 않았다 |
| §6 점검 포인트의 ✅ 항목(FLAG_SECURE, CryptoObject 등 플랫폼 API) | **현행 플랫폼 관행 기준 권고** — MASWE frontmatter 데이터에서 도출한 것이 아니므로, 세부 구현 판단 전 MASTG-TEST 원문과 `secure-coding-java` 를 확인하라 |
| `mas.owasp.org/MASWE/MASVS-STORAGE/` 형태의 카테고리 목록 URL | **존재하지 않음(404 실측)** — 개별 항목 URL(`/MASWE/MASVS-STORAGE/MASWE-0001/`)만 유효 |

## 10. 상세 레퍼런스

| 파일 | 내용 |
|---|---|
| `references/masvs-24-controls.md` | 24개 컨트롤 전체 — ID·원문·연결 MASWE 상세 |
| `references/maswe-78.md` | MASWE-0001~0078 전수 색인 — ID·이름·카테고리·프로파일 (항목당 1줄) |
| `references/masvs-gap-vs-mobile-app-verify.md` | `mobile-app-verify` 51항목 ↔ MASVS 24컨트롤 전수 매핑 — 겹침 등급·OWASP 에만 있는 MASWE·방향 반대 항목 |
| `references/mastg-structure.md` | MASTG v2.0.0 구성요소(TEST/TECH/TOOL/DEMO/KNOW/BEST/APP)별 규모·상태 분포 실측 |
