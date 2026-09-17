# MASVS v2.1.0 — 24개 컨트롤 색인

> **출처**: OWASP Mobile Application Security Verification Standard (MASVS) —
> `https://github.com/OWASP/masvs` (렌더: `https://mas.owasp.org/MASVS/`)
> **버전**: **MASVS v2.1.0** (2024-01-18) 기준. 부출처: MASWE v1.0.0 (소속 MASWE 매핑 산출),
> MASVS v1.5.0 (v1→v2 비교 절에서만 사용)
> **라이선스**: CC BY-SA 4.0 · **조회일**: 2026-09-17
>
> 이 파일은 **색인 수준** 요약임 — 컨트롤당 원문 1줄(표준 식별 목적) + 한국어 해설 2~4줄이며,
> `secure-coding-kr` 의 `weakness-49.md` 같은 항목당 전수 해설이 아님. 상세 해설은
> `mas.owasp.org` 원문을 볼 것.
>
> ⚠️ **버전 고정 주의**: MASWE `main` 브랜치에는 약점이 **MASWE-0118 까지** 확장돼 있고 5번째
> 프로파일 **EUDIW** 가 추가돼 있음. 이 파일의 "소속 MASWE 수"·프로파일 서술은 전부
> **MASWE v1.0.0 태그 기준 78개 / 프로파일 4종(L1·L2·R·P)** 임. main 브랜치 값을 섞지 말 것.

---

## 총괄표 (24개 컨트롤)

"소속 MASWE 수"는 MASWE v1.0.0 frontmatter `mappings.masvs-v2` 기준이며 **교차 카테고리 매핑을
포함**함(한 MASWE 가 여러 컨트롤에 매핑되므로 합계 118 매핑 ≠ 78개).

| 카테고리 | 컨트롤 ID | 원문(EN) | 한국어 요약 | 소속 MASWE 수 |
|---|---|---|---|---|
| STORAGE | MASVS-STORAGE-1 | The app securely stores sensitive data. | 민감데이터의 안전한 저장 | 4 |
| STORAGE | MASVS-STORAGE-2 | The app prevents leakage of sensitive data. | 민감데이터 유출 방지 | 15 |
| CRYPTO | MASVS-CRYPTO-1 | The app employs current strong cryptography and uses it according to industry best practices. | 현행 강력한 암호를 모범사례대로 사용 | 7 |
| CRYPTO | MASVS-CRYPTO-2 | The app performs key management according to industry best practices. | 암호키 관리를 모범사례대로 수행 | 13 |
| AUTH | MASVS-AUTH-1 | The app uses secure authentication and authorization protocols and follows the relevant best practices. | 안전한 인증·인가 프로토콜 사용 | 3 |
| AUTH | MASVS-AUTH-2 | The app performs local authentication securely according to the platform best practices. | 플랫폼 모범사례에 따른 로컬(생체) 인증 | 4 |
| AUTH | MASVS-AUTH-3 | The app secures sensitive operations with additional authentication. | 민감 작업에 추가 인증(step-up) 적용 | 5 |
| NETWORK | MASVS-NETWORK-1 | The app secures all network traffic according to the current best practices. | 모든 네트워크 트래픽 보호 | 4 |
| NETWORK | MASVS-NETWORK-2 | The app performs identity pinning for all remote endpoints under the developer's control. | 자체 통제 엔드포인트에 identity pinning 수행 | 1 |
| PLATFORM | MASVS-PLATFORM-1 | The app uses IPC mechanisms securely. | IPC 메커니즘의 안전한 사용 | 5 |
| PLATFORM | MASVS-PLATFORM-2 | The app uses WebViews securely. | WebView 의 안전한 사용 | 4 |
| PLATFORM | MASVS-PLATFORM-3 | The app uses the user interface securely. | UI 를 통한 노출의 안전한 통제 | 6 |
| CODE | MASVS-CODE-1 | The app requires an up-to-date platform version. | 최신 플랫폼 버전 요구 | 3 |
| CODE | MASVS-CODE-2 | The app has a mechanism for enforcing app updates. | 앱 업데이트 강제 메커니즘 보유 | 1 |
| CODE | MASVS-CODE-3 | The app only uses software components without known vulnerabilities. | 알려진 취약점 없는 컴포넌트만 사용 | 5 |
| CODE | MASVS-CODE-4 | The app validates and sanitizes all untrusted inputs. | 신뢰할 수 없는 입력의 검증·정제 | 7 |
| RESILIENCE | MASVS-RESILIENCE-1 | The app validates the integrity of the platform. | 플랫폼 무결성 검증(루팅·에뮬레이터 등) | 4 |
| RESILIENCE | MASVS-RESILIENCE-2 | The app implements anti-tampering mechanisms. | 앱 위변조 방지 | 4 |
| RESILIENCE | MASVS-RESILIENCE-3 | The app implements anti-static analysis mechanisms. | 정적 분석 방해(난독화 등) | 4 |
| RESILIENCE | MASVS-RESILIENCE-4 | The app implements anti-dynamic analysis techniques. | 동적 분석 방해(디버거·후킹 탐지 등) | 5 |
| PRIVACY | MASVS-PRIVACY-1 | The app minimizes access to sensitive data and resources. | 민감데이터·자원 접근 최소화 | 2 |
| PRIVACY | MASVS-PRIVACY-2 | The app prevents identification of the user. | 사용자 식별 방지 | 5 |
| PRIVACY | MASVS-PRIVACY-3 | The app is transparent about data collection and usage. | 데이터 수집·이용의 투명성 | 4 |
| PRIVACY | MASVS-PRIVACY-4 | The app offers user control over their data. | 사용자의 데이터 통제권 제공 | 3 |

---

## 카테고리별 상세

각 절 제목의 "MASWE n"은 해당 카테고리를 **주 카테고리**로 하는 MASWE 개수(합계 78).
컨트롤별 "소속 MASWE"는 교차 카테고리 매핑 포함.

### MASVS-STORAGE (컨트롤 2 / MASWE 6)

- **STORAGE-1**: 민감데이터를 플랫폼 제공 안전 저장소(Keystore/Keychain 등)에 암호화해 저장하는지를
  다룸. 하드코딩된 비밀(0004)도 이 컨트롤 소속. 소속 MASWE: 0001, 0002, 0003, 0004
- **STORAGE-2**: 로그·백업·클립보드·스크린샷·알림 등 **비의도 경로를 통한 유출** 방지. 유출 경로가
  다른 카테고리(PLATFORM 등)에 있으면 교차 매핑됨. 소속 MASWE: 0001, 0002, 0005, 0006 +
  교차 매핑 11건(0018, 0029~0034, 0036~0038, 0040)
- 국내 대응: 진단가이드 '암호화되지 않은 중요정보'(CWE-312)·'하드코드된 중요정보'(CWE-259/321),
  mobile-app-verify 의 중요정보 저장 항목과 **부분 대응** — 백업·클립보드 등 유출 경로별 세분 기준은 국내에 없음

### MASVS-CRYPTO (컨트롤 2 / MASWE 11)

- **CRYPTO-1**: 검증된 강한 알고리즘·모드·파라미터의 올바른 사용(암호화·해시·MAC·서명·난수).
  소속 MASWE: 0007~0012, 0047
- **CRYPTO-2**: 키 생성·유도·저장·회전·접근통제 등 **키 수명주기 관리** 전반.
  소속 MASWE: 0001, 0003, 0007, 0009, 0010, 0013~0017, 0020, 0022, 0046
- 국내 대응: '취약한 암호화 알고리즘 사용'·'충분하지 않은 키 길이 사용'·'적절하지 않은 난수 값
  사용'·'솔트 없이 일방향 해쉬 함수 사용'·'부적절한 전자서명 확인' 및 `crypto-policy-kr` 스킬 영역과
  **대응 있음**. 단 키 회전(0015)·기기 잠금 강제(0017)는 국내 기준에 직접 대응 없음

### MASVS-AUTH (컨트롤 3 / MASWE 8)

- **AUTH-1**: 원격 서비스에 대한 인증·인가 프로토콜(모범사례 준수). 소속 MASWE: 0018, 0019, 0047
- **AUTH-2**: 생체인증 등 **로컬 인증**의 안전한 구현(우회 불가, 키와 결합). 소속 MASWE: 0016, 0020~0022
- **AUTH-3**: 민감 작업에 대한 **추가 인증**(step-up)·세션 종료 후 접근 차단·부인방지.
  소속 MASWE: 0016, 0019, 0023~0025
- 국내 대응: AUTH-1 은 '적절한 인증 없는 중요기능 허용'·'부적절한 인가'와 부분 대응.
  **AUTH-2(0020~0022)·AUTH-3(0023~0025) 계열은 국내 49개·51항목에 직접 대응 없음**
  (갭 상세는 `masvs-gap-vs-mobile-app-verify.md` 참조)

### MASVS-NETWORK (컨트롤 2 / MASWE 3)

- **NETWORK-1**: TLS 등 현행 모범사례에 따른 모든 트래픽 보호(평문 전송 금지, 인증서 검증).
  소속 MASWE: 0026, 0027, 0047, 0062
- **NETWORK-2**: 개발자가 통제하는 원격 엔드포인트에 대한 identity pinning. 소속 MASWE: 0028
- 국내 대응: NETWORK-1 은 '암호화되지 않은 중요정보'(CWE-319 전송 평문)·'부적절한 인증서 유효성
  검증'과 대응 있음. **NETWORK-2(피닝)는 국내 기준에 대응 없음**

### MASVS-PLATFORM (컨트롤 3 / MASWE 12)

- **PLATFORM-1**: 인텐트·딥링크·클립보드·앱 확장 등 **IPC** 의 안전한 사용. 소속 MASWE: 0018, 0029~0032
- **PLATFORM-2**: **WebView** 의 안전한 설정(네이티브 브리지 노출·로컬 자원 접근·비신뢰 콘텐츠 로딩).
  소속 MASWE: 0033~0035, 0063
- **PLATFORM-3**: **UI 를 통한 노출** 통제(화면·알림·스크린샷·오버레이·접근성 서비스).
  소속 MASWE: 0023, 0036~0040
- 국내 대응: PLATFORM-1 일부는 `secure-coding-java` 의 `android:exported` 등 구현 지침과 겹치나
  49개 기준에 직접 항목은 없음. **PLATFORM-2(0033~0035)·PLATFORM-3(0036~0040) 계열은 국내 기준에
  대응 없음**

### MASVS-CODE (컨트롤 4 / MASWE 10)

- **CODE-1**: 최신 플랫폼 버전에서 실행되도록 요구(minSdk/target 관리). 소속 MASWE: 0039, 0041, 0042
- **CODE-2**: 강제 업데이트 메커니즘 보유. 소속 MASWE: 0043
- **CODE-3**: 알려진 취약점 있는 의존성·비표준 API·악성 코드 배제. 소속 MASWE: 0044~0048
- **CODE-4**: 신뢰할 수 없는 입력의 검증·정제(동적 코드 로딩 포함). 소속 MASWE: 0029, 0034, 0035, 0045, 0049, 0050, 0057
- 국내 대응: CODE-4 는 진단가이드 제1절 '입력데이터 검증 및 표현'(17개 항목)과 취지가 대응하고,
  CODE-3 은 '취약한 API 사용'과 부분 대응. **CODE-1·CODE-2(플랫폼 버전·강제 업데이트)는 국내 기준에
  직접 대응 없음**

### MASVS-RESILIENCE (컨트롤 4 / MASWE 15)

- **RESILIENCE-1**: 플랫폼 무결성 검증 — 루팅/탈옥·가상화·에뮬레이터 탐지, 기기 증명.
  소속 MASWE: 0051~0054
- **RESILIENCE-2**: 앱 위변조 방지 — 앱 증명, 리소스·런타임 코드 무결성. 소속 MASWE: 0055~0058
- **RESILIENCE-3**: 정적 분석 방해 — 코드·리소스 난독화, 디버그 산출물 제거, 페이로드 암호화.
  소속 MASWE: 0059~0062
- **RESILIENCE-4**: 동적 분석 방해 — 디버그 메커니즘 비활성화, 디버거·동적 분석 도구 탐지.
  소속 MASWE: 0051, 0053, 0063~0065
- 국내 대응: mobile-app-verify 기능 보안취약점(앱 위변조 검증·루팅 탐지·난독화)과 **겹침이 가장 큰
  카테고리**. 0061(Debug Artifacts)은 진단가이드 '제거되지 않고 남은 디버그 코드'와 부분 대응.
  단 **MASWE-0051 은 FV-5.1 과 점검 방향이 정반대**(`maswe-78.md` 경고 참조)이고,
  **RESILIENCE-4 의 동적 분석 탐지 계열(0063~0065)은 국내 기준에 대응 없음**

### MASVS-PRIVACY (컨트롤 4 / MASWE 13)

- **PRIVACY-1**: 민감데이터·권한·자원 접근 최소화. 소속 MASWE: 0066, 0073
- **PRIVACY-2**: 사용자 식별 방지 — 익명화·가명화, 추적 식별자 오용 금지. 소속 MASWE: 0067~0071
- **PRIVACY-3**: 수집·이용의 투명성 — 개인정보처리방침, 스토어 수집 신고, 재현 가능 빌드.
  소속 MASWE: 0072~0075
- **PRIVACY-4**: 사용자의 데이터 통제권 — 데이터 관리·가시성·동의 메커니즘. 소속 MASWE: 0076~0078
- 국내 대응: **국내 코드 진단 기준(진단가이드 49개·mobile-app-verify 51항목)에는 대응 항목 없음** —
  MASVS v2 에서 신설된 카테고리로, 국내에서는 코드 진단이 아닌 별도 법령·지침 영역에서 다뤄짐

---

## v1 → v2 구조 변경

| | MASVS v1.5.0 (2023-01-31) | MASVS v2.1.0 (2024-01-18) |
|---|---|---|
| 구조 | V1~V8 그룹 | MASVS-XXXXX 8개 카테고리 |
| 요구사항 수 | 84개 | 24개 컨트롤로 추상화 |
| ID 접두사 | `MSTG-STORAGE-1` | `MASVS-STORAGE-1` |
| 레벨 | L1/L2/R 을 표준 본문에 내장 | 표준에서 제거 → MAS 프로파일로 이전 |
| V1 Architecture | 존재 | 삭제 (프로세스 요구사항은 범위 밖) |
| 신설 | — | MASVS-PRIVACY (컨트롤 4개) + CycloneDX 지원 |

⚠️ `MSTG-STORAGE-1` 같은 **`MSTG-` 접두사는 v1(84개 요구사항) 유물**임. 외부 자료·구형 체크리스트에서
이 접두사가 보이면 v1 기준이므로 v2 컨트롤·MASWE 매핑에 혼입하지 말 것.

## MAS 프로파일 (v2 에서 표준 본문 밖으로 이전)

| 프로파일 | 공격자 모델(원문 취지) | 적용 MASWE 수 (v1.0.0) |
|---|---|---|
| MAS-L1 Essential Security | 기기에 설치된 다른 앱이 공격자 | 29 |
| MAS-L2 Advanced Security | OS 를 신뢰할 수 없고 공격자가 기기에 물리 접근 가능 | 50 |
| MAS-R Resilient Security | 기기 사용자 본인이 공격자(리버스 엔지니어·치터) | 15 |
| MAS-P Baseline Privacy | 공격자 중심 아님 — 개인정보 보호·책임 있는 데이터 처리 | 13 |

MASVS 공식 문구: *"Starting on v2.0.0 the MASVS does not contain 'verification levels'. … have been
reworked as 'MAS Testing Profiles' and moved over to the OWASP MASWE."* — 즉 레벨 판정은 이제
MASVS 가 아니라 **MASWE 의 프로파일 필드**에서 이뤄짐. `main` 브랜치의 5번째 프로파일 EUDIW 는
v1.0.0 체계 밖이므로 이 파일 범위에서 제외함.

---

## 인용·전재 주의 (과잉 인용 금지)

- 이 파일은 CC BY-SA 4.0 원문의 **요약·매핑 색인**임. 컨트롤 원문 1줄 인용은 표준 식별 목적이며,
  그 이상의 해설문 전재는 하지 말 것(ShareAlike 전염 방지)
- 산출물(보고서·문서)에 내용을 옮길 때는 출처 4요소(출처·버전·라이선스·조회일)를 함께 기재할 것
- 국내 기준과의 대응 서술은 취지 수준의 참고 매핑이며, 공식 대응표가 아님 — 진단·검증 제출물에는
  국내 원문 기준(`secure-coding-kr`·`mobile-app-verify`)을 정본으로 사용할 것
