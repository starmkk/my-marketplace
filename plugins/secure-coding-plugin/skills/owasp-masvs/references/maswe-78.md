# MASWE v1.0.0 — 78개 약점 전체 색인

> **출처**: OWASP Mobile Application Security Weakness Enumeration (MASWE) —
> `https://github.com/OWASP/maswe` 태그 v1.0.0 (렌더: `https://mas.owasp.org/MASWE/`)
> **버전**: **MASWE v1.0.0** (published 2026-08-17) 기준. 부출처: MASVS v2.1.0 (컨트롤 ID)
> **라이선스**: CC BY-SA 4.0 · **조회일**: 2026-09-17
>
> **이 파일은 색인임** — 항목당 1줄이며 각 약점의 상세 해설(개요·영향·테스트)은
> `mas.owasp.org/MASWE/<카테고리>/<ID>/` 원문을 볼 것 (예: `/MASWE/MASVS-STORAGE/MASWE-0001/`).
> ⚠️ 단 `mas.owasp.org/MASWE/MASVS-STORAGE/` 형태의 **카테고리 목록 페이지는 404 로 존재하지
> 않음**(2026-09-17 실측) — 개별 항목 페이지만 존재함.
>
> ⚠️ **버전 고정 주의**: `main` 브랜치에는 MASWE 가 **0118 까지** 확장돼 있고 5번째 프로파일
> **EUDIW** 가 추가돼 있음. 이 표는 **v1.0.0 태그 기준 78개 / 프로파일 4종(L1·L2·R·P)** 이며
> main 브랜치 값을 섞지 말 것.

---

## 총괄표 (78개 전체)

| ID | 제목(EN) | 카테고리 | MASVS 컨트롤 | 프로파일 |
|---|---|---|---|---|
| MASWE-0001 | Sensitive Data Stored Unencrypted in Private Storage | STORAGE | MASVS-STORAGE-1, MASVS-STORAGE-2, MASVS-CRYPTO-2 | L2 |
| MASWE-0002 | Sensitive Data Stored Unencrypted Outside of Private Storage | STORAGE | MASVS-STORAGE-1, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0003 | Cryptographic Keys Stored Outside of Platform Keystore | STORAGE | MASVS-STORAGE-1, MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0004 | Sensitive Data Hardcoded in the App Package | STORAGE | MASVS-STORAGE-1 | L1, L2 |
| MASWE-0005 | Insertion of Sensitive Data into Logs | STORAGE | MASVS-STORAGE-2 | L1, L2 |
| MASWE-0006 | Sensitive Data Not Excluded From Backup | STORAGE | MASVS-STORAGE-2 | L1, L2 |
| MASWE-0007 | Improper Encryption | CRYPTO | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0008 | Improper Hashing | CRYPTO | MASVS-CRYPTO-1 | L1, L2 |
| MASWE-0009 | Improper Use of Message Authentication Code (MAC) | CRYPTO | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0010 | Improper Generation of Cryptographic Signatures | CRYPTO | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0011 | Improper Verification of Cryptographic Signature | CRYPTO | MASVS-CRYPTO-1 | L1, L2 |
| MASWE-0012 | Improper Random Number Generation | CRYPTO | MASVS-CRYPTO-1 | L1, L2 |
| MASWE-0013 | Improper Cryptographic Key Generation | CRYPTO | MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0014 | Improper Cryptographic Key Derivation | CRYPTO | MASVS-CRYPTO-2 | L1, L2 |
| MASWE-0015 | Cryptographic Key Rotation Not Implemented | CRYPTO | MASVS-CRYPTO-2 | L2 |
| MASWE-0016 | Cryptographic Key Access Not Restricted | CRYPTO | MASVS-CRYPTO-2, MASVS-AUTH-2, MASVS-AUTH-3 | L2 |
| MASWE-0017 | Device Secure Lock Not Enforced | CRYPTO | MASVS-CRYPTO-2 | L2 |
| MASWE-0018 | Lack of Authentication or Authorization on App Components | AUTH | MASVS-AUTH-1, MASVS-PLATFORM-1, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0019 | Lack of Auto-fill Support for Credential Providers | AUTH | MASVS-AUTH-1, MASVS-AUTH-3 | L1, L2 |
| MASWE-0020 | Local Authentication Can Be Bypassed | AUTH | MASVS-AUTH-2, MASVS-CRYPTO-2 | L2 |
| MASWE-0021 | Fallback to Non-biometric Credentials Allowed for Sensitive Transactions | AUTH | MASVS-AUTH-2 | L2 |
| MASWE-0022 | Crypto Keys Not Invalidated on New Biometric Enrollment | AUTH | MASVS-AUTH-2, MASVS-CRYPTO-2 | L2 |
| MASWE-0023 | Step-Up Authentication Not Implemented for Sensitive Actions | AUTH | MASVS-AUTH-3, MASVS-PLATFORM-3 | L2 |
| MASWE-0024 | Sensitive Data Accessible After Session Termination | AUTH | MASVS-AUTH-3 | L2 |
| MASWE-0025 | Lack of Non-Repudiation for Critical Actions | AUTH | MASVS-AUTH-3 | L2 |
| MASWE-0026 | Network Traffic Not Encrypted | NETWORK | MASVS-NETWORK-1 | L1, L2 |
| MASWE-0027 | Insecure Certificate Validation | NETWORK | MASVS-NETWORK-1 | L1, L2 |
| MASWE-0028 | Insecure Identity Pinning | NETWORK | MASVS-NETWORK-2 | L2 |
| MASWE-0029 | Insecure Deep Links | PLATFORM | MASVS-PLATFORM-1, MASVS-STORAGE-2, MASVS-CODE-4 | L1, L2 |
| MASWE-0030 | Improper Use of the Clipboard | PLATFORM | MASVS-PLATFORM-1, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0031 | Allowing Untrusted App Extensions | PLATFORM | MASVS-PLATFORM-1, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0032 | Insecure Intents | PLATFORM | MASVS-PLATFORM-1, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0033 | Sensitive Native Functionality Exposed in WebViews | PLATFORM | MASVS-PLATFORM-2, MASVS-STORAGE-2 | L1, L2 |
| MASWE-0034 | WebViews Allow Access to Local Resources with Untrusted Content | PLATFORM | MASVS-PLATFORM-2, MASVS-STORAGE-2, MASVS-CODE-4 | L1, L2 |
| MASWE-0035 | WebViews Loading Untrusted Content | PLATFORM | MASVS-PLATFORM-2, MASVS-CODE-4 | L1, L2 |
| MASWE-0036 | Unnecessary Exposure of Sensitive Data via the User Interface | PLATFORM | MASVS-PLATFORM-3, MASVS-STORAGE-2 | L2 |
| MASWE-0037 | Unnecessary Exposure of Sensitive Data via Notifications | PLATFORM | MASVS-PLATFORM-3, MASVS-STORAGE-2 | L2 |
| MASWE-0038 | Insufficient Protection of Sensitive Data from Screenshots or Screen Recordings | PLATFORM | MASVS-PLATFORM-3, MASVS-STORAGE-2 | L2 |
| MASWE-0039 | App Vulnerable to Overlay Attacks | PLATFORM | MASVS-PLATFORM-3, MASVS-CODE-1 | L2 |
| MASWE-0040 | Sensitive Data Leaked via Accessibility Services | PLATFORM | MASVS-PLATFORM-3, MASVS-STORAGE-2 | L2 |
| MASWE-0041 | Running on a Recent Platform Version Not Ensured | CODE | MASVS-CODE-1 | L2 |
| MASWE-0042 | Latest Platform Version Not Targeted | CODE | MASVS-CODE-1 | L1, L2 |
| MASWE-0043 | Enforced Updating Not Implemented | CODE | MASVS-CODE-2 | L2 |
| MASWE-0044 | Dependencies with Known Vulnerabilities | CODE | MASVS-CODE-3 | L1, L2 |
| MASWE-0045 | Compiler-Provided Security Features Not Used | CODE | MASVS-CODE-3, MASVS-CODE-4 | L2 |
| MASWE-0046 | Use of Deprecated APIs or Functionality | CODE | MASVS-CODE-3, MASVS-CRYPTO-2 | L2 |
| MASWE-0047 | Using Non-Standard APIs for Security-Critical Functionality | CODE | MASVS-CODE-3, MASVS-AUTH-1, MASVS-CRYPTO-1, MASVS-NETWORK-1 | L1, L2 |
| MASWE-0048 | Malicious Code Included in the App | CODE | MASVS-CODE-3 | L1, L2 |
| MASWE-0049 | Unsafe Dynamic Code Loading | CODE | MASVS-CODE-4 | L2 |
| MASWE-0050 | Unsafe Handling of Untrusted Data | CODE | MASVS-CODE-4 | L1, L2 |
| MASWE-0051 | Root/Jailbreak Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-1, MASVS-RESILIENCE-4 | R |
| MASWE-0052 | App Virtualization Environment Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-1 | R |
| MASWE-0053 | Emulated or Virtual Device Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-1, MASVS-RESILIENCE-4 | R |
| MASWE-0054 | Device Attestation Not Implemented | RESILIENCE | MASVS-RESILIENCE-1 | R |
| MASWE-0055 | Malware Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-2 | R |
| MASWE-0056 | App Attestation Not Implemented | RESILIENCE | MASVS-RESILIENCE-2 | R |
| MASWE-0057 | App Resources Integrity Not Verified | RESILIENCE | MASVS-RESILIENCE-2, MASVS-CODE-4 | R |
| MASWE-0058 | Runtime Code Integrity Not Verified | RESILIENCE | MASVS-RESILIENCE-2 | R |
| MASWE-0059 | Code Obfuscation Not Implemented | RESILIENCE | MASVS-RESILIENCE-3 | R |
| MASWE-0060 | Resource Obfuscation Not Implemented | RESILIENCE | MASVS-RESILIENCE-3 | R |
| MASWE-0061 | Debug Artifacts Not Removed | RESILIENCE | MASVS-RESILIENCE-3 | R |
| MASWE-0062 | No Application-Level Payload Encryption | RESILIENCE | MASVS-RESILIENCE-3, MASVS-NETWORK-1 | R |
| MASWE-0063 | Debug Mechanisms Not Disabled | RESILIENCE | MASVS-RESILIENCE-4, MASVS-PLATFORM-2 | R |
| MASWE-0064 | Debugger Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-4 | R |
| MASWE-0065 | Dynamic Analysis Tools Detection Not Implemented | RESILIENCE | MASVS-RESILIENCE-4 | R |
| MASWE-0066 | Inadequate Permission Management | PRIVACY | MASVS-PRIVACY-1 | P |
| MASWE-0067 | Lack of Anonymization or Pseudonymisation Measures | PRIVACY | MASVS-PRIVACY-2 | P |
| MASWE-0068 | Incorrect Use of Identifiers for User Tracking | PRIVACY | MASVS-PRIVACY-2 | P |
| MASWE-0069 | Usage of Non-Privacy-Preserving Functionality | PRIVACY | MASVS-PRIVACY-2 | P |
| MASWE-0070 | Inadequate Awareness for Privacy Relevant Actions | PRIVACY | MASVS-PRIVACY-2 | P |
| MASWE-0071 | Inadequate Defaults for Privacy Relevant Actions | PRIVACY | MASVS-PRIVACY-2 | P |
| MASWE-0072 | Inadequate Privacy Policy | PRIVACY | MASVS-PRIVACY-3 | P |
| MASWE-0073 | Inadequate Data Collection Declarations | PRIVACY | MASVS-PRIVACY-3, MASVS-PRIVACY-1 | P |
| MASWE-0074 | Inadequate Tracking Domains Declarations | PRIVACY | MASVS-PRIVACY-3 | P |
| MASWE-0075 | Non-Reproducible Builds | PRIVACY | MASVS-PRIVACY-3 | P |
| MASWE-0076 | Lack of Proper Data Management Controls | PRIVACY | MASVS-PRIVACY-4 | P |
| MASWE-0077 | Inadequate Data Visibility Controls | PRIVACY | MASVS-PRIVACY-4 | P |
| MASWE-0078 | Inadequate or Ambiguous User Consent Mechanisms | PRIVACY | MASVS-PRIVACY-4 | P |

---

## 교차 검증 수치 (v1.0.0 frontmatter 전수 파싱, 전건 일치)

- **카테고리별**: STORAGE 6 · CRYPTO 11 · AUTH 8 · NETWORK 3 · PLATFORM 12 · CODE 10 ·
  RESILIENCE 15 · PRIVACY 13 = **78**
- **프로파일별**: L1 29 · L2 50 · R 15 · P 13 (한 항목이 L1·L2 에 중복 소속 가능)
- v1.0.0 frontmatter 에는 `status:` 필드가 **78개 전부에 없음** — 개별 draft/new 라벨 없이
  전부 정식 항목임

## 국내 기준(진단가이드 49개 / mobile-app-verify 51항목)에 대응이 없는 MASWE

다음 계열은 국내 코드 진단·검증 기준에 직접 대응 항목이 없음 (갭 상세·근거는
`masvs-gap-vs-mobile-app-verify.md` 참조):

- **NETWORK-2 계열**: MASWE-0028 (identity pinning)
- **AUTH-2 계열**: MASWE-0020~0022 (로컬/생체 인증 우회·폴백·키 무효화)
- **AUTH-3 계열**: MASWE-0023~0025 (step-up 인증·세션 종료 후 접근·부인방지)
- **PLATFORM-2 계열**: MASWE-0033~0035 (WebView 네이티브 노출·로컬 자원·비신뢰 콘텐츠)
- **PLATFORM-3 계열**: MASWE-0036~0040 (UI·알림·스크린샷·오버레이·접근성 노출)
- **RESILIENCE-4 계열**: MASWE-0063~0065 (디버그 메커니즘·디버거·동적 분석 도구 탐지)

## ⚠️ MASWE-0051 경고

**MASWE-0051(Root/Jailbreak Detection Not Implemented)은 `mobile-app-verify` 의 FV-5.1 과 점검
방향이 정반대임** — 두 기준을 같은 항목으로 등치해 판정하면 오판함. 반드시
`masvs-gap-vs-mobile-app-verify.md` 의 대조를 거쳐 적용할 것.

---

## 인용·전재 주의 (과잉 인용 금지)

- 이 파일은 CC BY-SA 4.0 원문의 **색인**임(제목·매핑·프로파일만 수록). 각 약점의 해설문을 이
  파일이나 산출물에 전재하지 말 것(ShareAlike 전염 방지) — 해설이 필요하면 원문 링크로 안내
- 산출물에 옮길 때는 출처 4요소(출처·버전·라이선스·조회일)를 함께 기재할 것
