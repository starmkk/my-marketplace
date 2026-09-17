# ASVS 5.0.0 — 17챕터 색인 + 국내 공백 7챕터 요구사항 수록

> **출처**: OWASP Application Security Verification Standard (ASVS) —
> `https://github.com/OWASP/ASVS` 태그 `v5.0.0`
> (렌더: `https://owasp.org/www-project-application-security-verification-standard/`)
> **버전**: **ASVS 5.0.0** (릴리스 2025-05-30). 공식 한국어 PDF(103페이지) 존재
> **라이선스**: CC BY-SA 4.0 · **조회일**: 2026-09-17
>
> 이 파일은 **색인 + 공백 챕터 선별 수록**임 — 17챕터 전체는 챕터 수준 색인만 두고, 국내 기준이
> 덮지 못하는 공백 7개 챕터(요구사항 144개)만 요구사항 수준으로 수록함. **345개 전수 해설이
> 아님.** 요구사항 요지는 한국어 1줄 압축이며 원문 전재가 아님 — 원문은 위 저장소의
> `5.0/docs_en/..._5.0.0_en.flat.json` (태그 `v5.0.0`)을 볼 것.
>
> ⚠️ **버전 고정 주의**: 반드시 태그 `v5.0.0` 으로 조회할 것. `main` 브랜치는 다음 버전 작업이
> 진행 중이라 요구사항 수·내용이 이미 다를 수 있음. 이 파일의 수치는 전부 v5.0.0 태그 기준임.

---

## 17챕터 총괄 색인 (345개 요구사항)

**굵은 글씨 7개가 국내 공백 챕터**(★) — 국내 설계단계 SR 대응이 없는 챕터로, 아래에서
요구사항 수준으로 수록함. 나머지 10챕터는 국내 SR 대응표만 둠.

| 챕터 | 영문 제목 | 요구사항 | L1 | L2 | L3 | 섹션 |
|---|---|---|---|---|---|---|
| V1 | Encoding and Sanitization | 30 | 8 | 19 | 3 | 5 |
| V2 | Validation and Business Logic | 13 | 4 | 7 | 2 | 4 |
| **V3** ★ | **Web Frontend Security** | **31** | 8 | 11 | 12 | 7 |
| **V4** ★ | **API and Web Service** | **16** | 2 | 8 | 6 | 4 |
| V5 | File Handling | 13 | 4 | 5 | 4 | 4 |
| V6 | Authentication | 47 | 13 | 22 | 12 | 8 |
| V7 | Session Management | 19 | 6 | 12 | 1 | 6 |
| V8 | Authorization | 13 | 4 | 3 | 6 | 4 |
| **V9** ★ | **Self-contained Tokens** | **7** | 4 | 3 | 0 | 2 |
| **V10** ★ | **OAuth and OIDC** | **36** | 5 | 24 | 7 | 7 |
| V11 | Cryptography | 24 | 3 | 11 | 10 | 7 |
| V12 | Secure Communication | 12 | 3 | 6 | 3 | 3 |
| **V13** ★ | **Configuration** | **21** | 1 | 12 | 8 | 4 |
| V14 | Data Protection | 13 | 2 | 7 | 4 | 3 |
| **V15** ★ | **Secure Coding and Architecture** | **21** | 3 | 10 | 8 | 4 |
| V16 | Security Logging and Error Handling | 17 | 0 | 16 | 1 | 5 |
| **V17** ★ | **WebRTC** | **12** | 0 | 7 | 5 | 3 |
| **합계** | | **345** | **70** | **183** | **92** | **73** |

요구사항 ID 형식은 `V<챕터>.<섹션>.<순번>` (예 `V3.1.1`). 레벨(L1/L2/L3)은 요구사항당 1개임.

---

## 국내 대응 10챕터 — SR 대응표 (요구사항 전개 없음)

이 10개 챕터는 국내 설계단계 기준(SR1-1~SR4-1)이 이미 덮으므로 **대응표만** 둠. 개별 요구사항
진단은 국내 원문 기준(`secure-coding-kr` 스킬)을 정본으로 사용할 것.

| 챕터 | 제목 | 요구사항 수 | 국내 SR 대응 | 비고 |
|---|---|---|---|---|
| V1 | Encoding and Sanitization | 30 | SR1-1~SR1-9 | ⚠️ 5.0.0 의 V1 은 4.0.3 V1 「Architecture」와 **전혀 다른 챕터** — 4.0.3 V1 은 삭제됐고 `V1` 기호만 재사용됨. 구버전 자료의 "V1" 인용과 혼용 금지 |
| V2 | Validation and Business Logic | 13 | SR1-1~SR1-9 | 입력검증·비즈니스 로직 검증 |
| V5 | File Handling | 13 | SR1-10 | 업로드·다운로드·저장 |
| V6 | Authentication | 47 | SR2-1, SR2-2, SR2-3 | ⚠️ **V6.2.5(L1, 비밀번호 조합 규칙 금지)가 국내 조합 강제 관행과 정면 충돌** — V6.2.10(정기 변경 강제 금지)도 충돌 소지. 제도 판정은 국내 기준을 따름 |
| V7 | Session Management | 19 | SR4-1 | 서버 세션 수명주기 |
| V8 | Authorization | 13 | SR2-4 | 접근통제·권한 검증 |
| V11 | Cryptography | 24 | SR2-5, SR2-6 | `crypto-policy-kr` 스킬 영역과 중첩 |
| V12 | Secure Communication | 12 | SR2-8 | TLS 등 전송 보호 |
| V14 | Data Protection | 13 | SR2-7 | 중요정보 보호 |
| V16 | Security Logging and Error Handling | 17 | SR3-1 | ⚠️ **비대칭** — SR3-1 은 **에러처리만** 대응하고 **보안 로깅은 국내 설계 기준에 대응 항목이 없음**. V16 은 L2 가 16개로 사실상 로깅 중심 챕터 |

---

## 공백 7개 챕터 — 요구사항 수준 수록 (144개)

국내 설계단계 20개(SR1-1~SR4-1)에 대응이 없는 챕터. 각 표의 요지는 식별·검색용 1줄 압축이며,
진단 인용 시에는 요구사항 ID·버전(5.0.0)·조회일과 "구속력 없음"을 병기할 것.

### V3 Web Frontend Security (31개 / L1 8 · L2 11 · L3 12)

섹션: 3.1 Documentation · 3.2 Unintended Content Interpretation · 3.3 Cookie Setup ·
3.4 Browser Security Mechanism Headers · 3.5 Browser Origin Separation ·
3.6 External Resource Integrity · 3.7 Other Browser Security Considerations

| ID | L | 요구사항 요지 |
|---|---|---|
| V3.1.1 | 3 | 브라우저가 지원해야 할 보안 기능(HTTPS·HSTS·CSP 등)과 미지원 시 동작(경고·차단)을 문서에 명시 |
| V3.2.1 | 1 | API·업로드 파일 등 직접 요청 시 잘못된 컨텍스트로 렌더링되지 않게 통제 — Sec-Fetch-* 검사, CSP sandbox, Content-Disposition attachment 등 |
| V3.2.2 | 1 | 텍스트로 표시할 콘텐츠는 createTextNode·textContent 등 안전한 렌더링 함수로 처리해 의도치 않은 HTML/JS 실행 방지 |
| V3.2.3 | 3 | 명시적 변수 선언·엄격한 타입 검사·document 전역 저장 회피·네임스페이스 격리로 DOM clobbering 방지 |
| V3.3.1 | 1 | 쿠키에 Secure 속성 설정, `__Host-` 접두사 미사용 시 `__Secure-` 접두사 사용 |
| V3.3.2 | 2 | 쿠키 목적에 맞는 SameSite 속성 설정으로 UI redress·CSRF 노출 제한 |
| V3.3.3 | 2 | 타 호스트 공유가 명시적 설계가 아닌 쿠키는 `__Host-` 접두사 사용 |
| V3.3.4 | 2 | 클라이언트 스크립트가 읽을 필요 없는 쿠키(세션 토큰 등)는 HttpOnly 설정, 해당 값은 Set-Cookie 로만 전달 |
| V3.3.5 | 3 | 쿠키 이름+값 합계 4096바이트 이하 — 초과 시 브라우저가 저장하지 않아 기능 상실 |
| V3.4.1 | 1 | 모든 응답에 HSTS(Strict-Transport-Security) 헤더 — max-age 1년 이상, L2 이상은 서브도메인 포함 |
| V3.4.2 | 1 | CORS Access-Control-Allow-Origin 은 고정값 또는 Origin 값을 신뢰 출처 allowlist 로 검증, `*` 사용 시 민감정보 미포함 |
| V3.4.3 | 2 | CSP 응답 헤더 필수 — 최소 object-src 'none'·base-uri 'none' + allowlist 또는 nonce/hash, L3 는 응답별 정책 |
| V3.4.4 | 2 | 모든 응답에 X-Content-Type-Options: nosniff — MIME 스니핑 금지, CORB 활성화 |
| V3.4.5 | 2 | Referrer-Policy 등으로 Referer 헤더를 통한 민감정보(경로·쿼리·내부 호스트명) 유출 방지 |
| V3.4.6 | 2 | 모든 응답에 CSP frame-ancestors 디렉티브로 임베딩 통제 — X-Frame-Options 는 구식이라 의존 금지 |
| V3.4.7 | 3 | CSP 헤더에 위반 보고(report) 위치 지정 |
| V3.4.8 | 3 | 문서 렌더링 응답에 Cross-Origin-Opener-Policy(same-origin 계열) — tabnabbing·frame counting 방지 |
| V3.5.1 | 1 | CORS preflight 에 의존하지 않으면 anti-forgery 토큰 또는 비-safelisted 헤더 요구로 CSRF 방어 |
| V3.5.2 | 1 | CORS preflight 에 의존하면 preflight 를 유발하지 않는 요청으로 민감 기능 호출이 불가함을 검증 |
| V3.5.3 | 1 | 민감 기능은 POST/PUT/PATCH/DELETE 사용(GET·HEAD·OPTIONS 등 safe 메서드 금지) 또는 Sec-Fetch-* 엄격 검증 |
| V3.5.4 | 2 | 별개 애플리케이션은 서로 다른 호스트명에 호스팅 — same-origin policy·쿠키 호스트 제한 활용 |
| V3.5.5 | 2 | postMessage 수신 시 origin 비신뢰 또는 문법 오류 메시지는 폐기 |
| V3.5.6 | 3 | JSONP 전면 비활성화 — XSSI(Cross-Site Script Inclusion) 방지 |
| V3.5.7 | 3 | 인가 필요 데이터를 스크립트 리소스 응답(JS 파일 등)에 포함 금지 — XSSI 방지 |
| V3.5.8 | 3 | 인증된 리소스는 의도된 경우만 로드·임베드 — Sec-Fetch-* 검증 또는 Cross-Origin-Resource-Policy |
| V3.6.1 | 3 | 외부(CDN) 호스팅 자산은 정적·버전 고정 + SRI(Subresource Integrity) 검증일 때만 — 불가하면 리소스별 문서화된 보안 결정 |
| V3.7.1 | 2 | 지원 종료·비보안 클라이언트 기술(Flash·ActiveX·Silverlight·애플릿 등) 미사용 |
| V3.7.2 | 2 | 통제 밖 호스트·도메인으로의 자동 리다이렉트는 allowlist 대상만 |
| V3.7.3 | 3 | 통제 밖 URL 리다이렉트 시 사용자 알림 + 취소 옵션 제공 |
| V3.7.4 | 3 | 최상위 도메인을 HSTS preload 공개 목록에 등재 — 헤더 의존을 넘어 브라우저에 내장 |
| V3.7.5 | 3 | 브라우저가 기대 보안 기능을 미지원하면 문서화된 대로 동작(경고·차단) |

왜 국내에 없는가: 국내 기준은 XSS·CSRF 를 개별 약점으로 다루지만, CSP·HSTS·쿠키 접두사·
origin 분리 같은 **브라우저 보안 메커니즘의 체계적 요구**는 항목이 없음(진단가이드는 2021년 기준).

### V4 API and Web Service (16개 / L1 2 · L2 8 · L3 6)

섹션: 4.1 Generic Web Service Security · 4.2 HTTP Message Structure Validation ·
4.3 GraphQL · 4.4 WebSocket

| ID | L | 요구사항 요지 |
|---|---|---|
| V4.1.1 | 1 | 본문 있는 모든 응답에 실제 콘텐츠와 일치하는 Content-Type + 안전한 charset(UTF-8 등) 지정 |
| V4.1.2 | 2 | 사용자 대면 엔드포인트만 HTTP→HTTPS 자동 리다이렉트 — 그 외에는 투명 리다이렉트 금지(평문 전송 은폐 방지) |
| V4.1.3 | 2 | 중간 계층(LB·프록시·BFF)이 설정하는 헤더(X-Real-IP·X-Forwarded-* 등)를 최종 사용자가 덮어쓸 수 없게 |
| V4.1.4 | 3 | 명시적으로 지원하는 HTTP 메서드만 허용(preflight 의 OPTIONS 포함), 미사용 메서드 차단 |
| V4.1.5 | 3 | 고민감·다중 시스템 경유 요청·트랜잭션에는 전송 보호에 더해 메시지 단위 전자서명 |
| V4.2.1 | 2 | 모든 컴포넌트(LB·방화벽·앱서버)가 HTTP 버전에 맞는 메시지 경계 판정 — request smuggling 방지(HTTP/1.x 는 Transfer-Encoding 우선, H2/H3 는 Content-Length·DATA 프레임 일치 확인) |
| V4.2.2 | 3 | 생성하는 HTTP 메시지의 Content-Length 가 프로토콜 프레이밍상 길이와 충돌하지 않게 — request smuggling 방지 |
| V4.2.3 | 3 | HTTP/2·HTTP/3 에서 연결 특정 헤더(Transfer-Encoding 등) 송수신 금지 — response splitting·헤더 인젝션 방지 |
| V4.2.4 | 3 | H2/H3 요청 헤더에 CR·LF·CRLF 시퀀스 포함 시 거부 — 헤더 인젝션 방지 |
| V4.2.5 | 3 | 생성하는 URI·요청 헤더(Authorization·Cookie 등)가 수신측 허용 길이를 넘지 않게 검증·정제 — DoS 방지 |
| V4.3.1 | 2 | GraphQL 쿼리 allowlist·깊이 제한·수량 제한·비용 분석으로 고비용 중첩 쿼리 DoS 방지 |
| V4.3.2 | 2 | 운영 환경에서 GraphQL introspection 비활성화(외부 제공 목적 API 제외) |
| V4.4.1 | 1 | 모든 WebSocket 연결에 WSS(WebSocket over TLS) 사용 |
| V4.4.2 | 2 | WebSocket 초기 핸드셰이크에서 Origin 헤더를 허용 origin 목록과 대조 |
| V4.4.3 | 2 | 표준 세션 관리를 못 쓰면 세션 관리 보안 요구사항을 준수하는 전용 토큰 사용 |
| V4.4.4 | 2 | 전용 WebSocket 세션 토큰은 기존 인증된 HTTPS 세션을 통해 획득·검증 후 채널 전환 |

왜 국내에 없는가: request smuggling·GraphQL introspection·WebSocket 핸드셰이크 등
**API·프로토콜 계층 요구**는 국내 설계·구현 기준 어디에도 대응 항목이 없음.

### V9 Self-contained Tokens (7개 / L1 4 · L2 3 · L3 0)

섹션: 9.1 Token source and integrity · 9.2 Token content

| ID | L | 요구사항 요지 |
|---|---|---|
| V9.1.1 | 1 | 자기수록형 토큰(JWT 등)은 내용 수용 전 전자서명·MAC 으로 변조 검증 |
| V9.1.2 | 1 | 토큰 생성·검증 알고리즘 allowlist — 'None' 금지, 대칭/비대칭 혼용 시 key confusion 방지 추가 통제 |
| V9.1.3 | 1 | 검증용 키 자료는 사전 구성된 신뢰 출처만 — JWT/JWS 의 'jku'·'x5u'·'jwk' 헤더는 신뢰 출처 allowlist 검증 |
| V9.2.1 | 1 | 유효기간이 있으면 검증 시각이 그 안일 때만 수용 — JWT 는 'nbf'·'exp' 클레임 검증 |
| V9.2.2 | 2 | 토큰 유형·용도 검증 — access token 만 인가 결정에, ID Token 만 사용자 인증 증명에 |
| V9.2.3 | 2 | 해당 서비스 대상(audience) 토큰만 수용 — JWT 'aud' 클레임을 서비스측 allowlist 로 검증 |
| V9.2.4 | 2 | 동일 개인키로 복수 audience 에 발급하는 발급자는 고유 audience 제한 클레임으로 타 대상 재사용 방지 |

왜 국내에 없는가: 국내 세션 관리 기준(SR4-1)은 서버측 세션을 전제함 — **JWT 등 자기수록형
토큰의 서명·알고리즘·클레임 검증** 요구는 국내 기준에 항목이 없음.

### V10 OAuth and OIDC (36개 / L1 5 · L2 24 · L3 7)

섹션: 10.1 Generic OAuth and OIDC Security · 10.2 OAuth Client · 10.3 OAuth Resource Server ·
10.4 OAuth Authorization Server · 10.5 OIDC Client · 10.6 OpenID Provider ·
10.7 Consent Management

| ID | L | 요구사항 요지 |
|---|---|---|
| V10.1.1 | 2 | 토큰은 꼭 필요한 컴포넌트에만 전달 — 브라우저 앱의 backend-for-frontend 패턴이면 access/refresh token 은 백엔드만 접근 |
| V10.1.2 | 2 | 동일 user agent 세션·트랜잭션에서 시작된 흐름의 값(code·ID Token)만 수용 — PKCE 'code_verifier'·'state'·OIDC 'nonce' 는 추측 불가·트랜잭션 고유·클라이언트와 세션에 결속 |
| V10.2.1 | 2 | code flow 사용 시 PKCE 또는 'state' 파라미터 검증으로 토큰 요청을 유발하는 CSRF 방어 |
| V10.2.2 | 2 | 복수 인가 서버와 연동하는 클라이언트는 mix-up 공격 방어 — 'iss' 파라미터 반환 요구·검증 등 |
| V10.2.3 | 3 | 클라이언트는 필요한 scope(및 기타 인가 파라미터)만 요청 |
| V10.3.1 | 2 | 리소스 서버는 자기 대상(audience) access token 만 수용 — 'aud' 클레임 또는 token introspection |
| V10.3.2 | 2 | access token 의 위임 인가 클레임('sub'·'scope'·'authorization_details')을 인가 결정에 반영 |
| V10.3.3 | 2 | access token 에서 사용자 고유 식별이 필요하면 재할당 불가 클레임 조합(통상 'iss'+'sub') 사용 |
| V10.3.4 | 2 | 인증 강도·수단·최신성 요건이 있으면 'acr'·'amr'·'auth_time' 클레임 등으로 충족 여부 확인 |
| V10.3.5 | 3 | sender-constrained access token(OAuth 2 mTLS 또는 DPoP) 요구로 탈취 토큰 사용·재전송 방지 |
| V10.4.1 | 1 | redirect URI 는 클라이언트별 사전 등록 allowlist 와 **정확 문자열 비교**로 검증 |
| V10.4.2 | 1 | authorization code 는 1회용 — 재사용 시 토큰 요청 거부 + 그 code 로 발급된 토큰 전부 폐기 |
| V10.4.3 | 1 | authorization code 단명 — L1/L2 최대 10분, L3 최대 1분 |
| V10.4.4 | 1 | 클라이언트별 필요한 grant 만 허용 — 'token'(Implicit)·'password'(ROPC) grant 는 사용 금지 |
| V10.4.5 | 1 | public client 의 refresh token 재전송 방어 — DPoP·mTLS 결속 우선, L1/L2 는 rotation 허용(사용 후 무효화, 무효 토큰 재제시 시 해당 인가의 refresh token 전부 폐기) |
| V10.4.6 | 2 | code grant 에 PKCE 강제 — 유효한 'code_challenge' 요구, 'plain' 방식 거부, 토큰 요청 시 'code_verifier' 검증 |
| V10.4.7 | 2 | 미인증 동적 클라이언트 등록 지원 시 악성 클라이언트 위험 완화 — 등록 메타데이터 검증·사용자 동의·비신뢰 클라이언트 경고 |
| V10.4.8 | 2 | refresh token 에 절대 만료 설정 — sliding 만료를 쓰더라도 |
| V10.4.9 | 2 | 사용자가 인가 서버 UI 에서 refresh token·reference access token 을 폐기 가능 |
| V10.4.10 | 2 | confidential client 는 백채널 요청(토큰 요청·PAR·폐기 요청)에서 클라이언트 인증 수행 |
| V10.4.11 | 2 | 인가 서버 구성은 OAuth 클라이언트에 필요한 scope 만 부여 |
| V10.4.12 | 3 | 클라이언트별 필요한 'response_mode' 값만 허용 — 기대값 검증 또는 PAR·JAR 사용 |
| V10.4.13 | 3 | grant type 'code' 는 항상 pushed authorization request(PAR)와 함께 사용 |
| V10.4.14 | 3 | sender-constrained(Proof-of-Possession) access token 만 발급 — mTLS 인증서 결속 또는 DPoP 결속 |
| V10.4.15 | 3 | 서버측 클라이언트의 'authorization_details' 는 클라이언트 백엔드 발신·사용자 미변조 보장 — PAR 또는 JAR 요구 등 |
| V10.4.16 | 3 | confidential client + 공개키 기반·재전송 저항 강한 클라이언트 인증(mTLS 계열 또는 'private_key_jwt') 요구 |
| V10.5.1 | 2 | ID Token 재전송 방어 — ID Token 의 'nonce' 클레임과 인증 요청에 보낸 'nonce' 일치 확인 등 |
| V10.5.2 | 2 | 재할당 불가 클레임(통상 'sub')으로 사용자 고유 식별 |
| V10.5.3 | 2 | 인가 서버 메타데이터의 issuer URL 이 사전 구성 기대값과 정확히 일치하지 않으면 거부 — 인가 서버 사칭 방지 |
| V10.5.4 | 2 | ID Token 의 'aud' 클레임이 자신의 'client_id' 와 같은지 검증 |
| V10.5.5 | 2 | OIDC back-channel logout 시 logout token 검증 — 'logout+jwt' 타입·올바른 'event' 클레임·'nonce' 부재 확인(강제 로그아웃 DoS·cross-JWT confusion 방지) |
| V10.6.1 | 2 | OpenID Provider 는 response mode 로 'code'·'ciba'·'id_token'·'id_token code' 만 허용 — Implicit('token') 금지, 'code' 선호 |
| V10.6.2 | 2 | 강제 로그아웃 DoS 완화 — 최종 사용자 명시 확인 또는 'id_token_hint' 등 로그아웃 요청 파라미터 검증 |
| V10.7.1 | 2 | 인가 요청마다 사용자 동의 보장 — 클라이언트 신원이 불확실하면 항상 명시적 동의 프롬프트 |
| V10.7.2 | 2 | 동의 화면에 충분·명확한 정보 제시 — 요청 인가의 성격(scope·리소스 서버·RAR authorization details)·클라이언트 신원·인가 수명 |
| V10.7.3 | 2 | 사용자가 인가 서버를 통해 부여한 동의를 검토·수정·철회 가능 |

왜 국내에 없는가: 국내 인증 기준(SR2-1~2-3)은 자체 인증 구현을 전제함 — **OAuth/OIDC 위임
인가 프로토콜의 역할별(클라이언트·리소스 서버·인가 서버) 요구**는 국내 기준에 항목이 없음.

### V13 Configuration (21개 / L1 1 · L2 12 · L3 8)

섹션: 13.1 Configuration Documentation · 13.2 Backend Communication Configuration ·
13.3 Secret Management · 13.4 Unintended Information Leakage

| ID | L | 요구사항 요지 |
|---|---|---|
| V13.1.1 | 2 | 애플리케이션의 모든 통신 요구 문서화 — 의존 외부 서비스와 사용자가 외부 연결 위치를 지정할 수 있는 경우 포함 |
| V13.1.2 | 3 | 서비스별 최대 동시 연결 수(커넥션 풀 한도)와 한도 도달 시 동작·복구 메커니즘 문서화 — DoS 예방 |
| V13.1.3 | 3 | 외부 시스템별 자원 관리 전략 문서화 — 해제 절차·타임아웃·재시도 한도/지연/백오프, 동기 HTTP 는 짧은 타임아웃 + 재시도 금지 또는 엄격 제한 |
| V13.1.4 | 3 | 보안에 중요한 시크릿 목록과 위협모델·업무 요구 기반 로테이션 일정 문서화 |
| V13.2.1 | 2 | 표준 세션을 못 쓰는 백엔드 컴포넌트 간 통신은 인증 — 개별 서비스 계정·단기 토큰·인증서 기반, 불변 자격증명(비밀번호·API 키·특권 공유 계정) 금지 |
| V13.2.2 | 2 | 백엔드 컴포넌트 간 통신(로컬·OS 서비스·API·미들웨어·데이터 계층 포함)은 최소 권한 계정으로 수행 |
| V13.2.3 | 2 | 서비스 인증에 자격증명을 써야 하면 기본 자격증명(root/root·admin/admin) 금지 |
| V13.2.4 | 2 | 통신 허용 외부 리소스·시스템을 allowlist 로 정의 — 앱 계층·웹서버·방화벽 또는 조합으로 구현 |
| V13.2.5 | 2 | 웹/앱 서버가 요청을 보내거나 데이터·파일을 로드할 대상 allowlist 구성 |
| V13.2.6 | 3 | 서비스별 문서화된 연결 구성(최대 병렬 연결·초과 시 동작·타임아웃·재시도 전략) 준수 |
| V13.3.1 | 2 | 시크릿 관리 솔루션(key vault)으로 백엔드 시크릿 생성·저장·접근통제·폐기 — 소스코드·빌드 산출물에 포함 금지, L3 는 HSM 등 하드웨어 기반 필수 |
| V13.3.2 | 2 | 시크릿 자산 접근에 최소 권한 원칙 적용 |
| V13.3.3 | 3 | 모든 암호 연산을 격리된 보안 모듈(vault·HSM)에서 수행 — 키 자료의 모듈 외부 노출 방지 |
| V13.3.4 | 3 | 시크릿의 만료·로테이션을 애플리케이션 문서 기준대로 구성 |
| V13.4.1 | 1 | 배포본에서 소스 관리 메타데이터(.git·.svn 폴더) 제거 또는 외부·앱 자체 접근 차단 |
| V13.4.2 | 2 | 운영 환경 전 컴포넌트에서 디버그 모드 비활성화 — 디버그 기능·정보 노출 방지 |
| V13.4.3 | 2 | 웹서버 디렉터리 리스팅 노출 금지(명시적 의도 제외) |
| V13.4.4 | 2 | 운영 환경에서 HTTP TRACE 메서드 미지원 — 정보 유출 방지 |
| V13.4.5 | 2 | 내부 API 문서·모니터링 엔드포인트 비노출(명시적 의도 제외) |
| V13.4.6 | 3 | 백엔드 컴포넌트의 상세 버전 정보 비노출 |
| V13.4.7 | 3 | 웹 계층은 지정된 확장자 파일만 서빙 — 의도치 않은 정보·구성·소스코드 유출 방지 |

왜 국내에 없는가: 국내 기준은 코드 내 약점 중심임 — **배포 구성·백엔드 서비스 간 인증·
시크릿 관리 솔루션(vault/HSM) 수준의 운영 구성 요구**는 대응 항목이 없음.

### V15 Secure Coding and Architecture (21개 / L1 3 · L2 10 · L3 8)

섹션: 15.1 Documentation · 15.2 Security Architecture and Dependencies ·
15.3 Defensive Coding · 15.4 Safe Concurrency

| ID | L | 요구사항 요지 |
|---|---|---|
| V15.1.1 | 1 | 취약 서드파티 컴포넌트의 위험 기반 조치 기한과 라이브러리 일반 갱신 정책 문서화 |
| V15.1.2 | 2 | SBOM 등 서드파티 라이브러리 인벤토리 유지 — 사전 정의·신뢰·지속 관리되는 저장소 출처 확인 포함 |
| V15.1.3 | 2 | 시간·자원 소모 기능 식별과 가용성 방어 문서화 — 비동기 처리·큐·사용자/앱별 병렬 제한 등 |
| V15.1.4 | 3 | "위험 컴포넌트(risky components)"로 간주되는 서드파티 라이브러리를 문서에 명시 |
| V15.1.5 | 3 | "위험 기능(dangerous functionality)" 사용 부위를 문서에 명시 |
| V15.2.1 | 1 | 문서화된 갱신·조치 기한을 넘긴 컴포넌트 미포함 |
| V15.2.2 | 2 | 시간·자원 소모 기능의 가용성 상실 방어를 문서화된 보안 결정·전략대로 구현 |
| V15.2.3 | 2 | 운영 환경에 필요한 기능만 포함 — 테스트 코드·샘플·개발 기능 비노출 |
| V15.2.4 | 3 | 서드파티 컴포넌트와 전이 의존성 전부를 기대 저장소에서만 수급 — dependency confusion 공격 위험 제거 |
| V15.2.5 | 3 | 위험 기능·위험 컴포넌트 부위에 추가 보호 — 샌드박싱·캡슐화·컨테이너화·네트워크 격리로 침투 확산 지연 |
| V15.3.1 | 1 | 데이터 객체 전체가 아니라 필요한 필드 부분집합만 반환 — 비공개 필드 노출 방지 |
| V15.3.2 | 2 | 백엔드의 외부 URL 호출은 의도된 기능이 아니면 리다이렉트 미추적으로 구성 |
| V15.3.3 | 2 | mass assignment 방어 — 컨트롤러·액션별 허용 필드 제한, 의도 밖 필드 삽입·갱신 불가 |
| V15.3.4 | 2 | 프록시·미들웨어는 사용자 원 IP 를 조작 불가 신뢰 필드로 전달, 로깅·rate limiting 등에 그 값 사용(원 IP 자체의 한계도 감안) |
| V15.3.5 | 2 | 변수 타입 명시 보장 + 엄격한 동등·비교 연산 — type juggling/type confusion 방지 |
| V15.3.6 | 2 | prototype pollution 을 방지하는 JavaScript 작성 — object literal 대신 Set()·Map() 사용 등 |
| V15.3.7 | 2 | HTTP parameter pollution 방어 — 프레임워크가 파라미터 출처(쿼리·본문·쿠키·헤더)를 구분하지 않는 경우 특히 |
| V15.4.1 | 3 | 멀티스레드 공유 객체(캐시·파일·메모리 객체)는 thread-safe 타입·락·세마포어로 안전 접근 — 경쟁 조건·데이터 오염 방지 |
| V15.4.2 | 3 | 자원 상태 확인과 의존 동작을 단일 원자 연산으로 수행 — TOCTOU 경쟁 조건 방지 |
| V15.4.3 | 3 | 락의 일관된 사용으로 교착·무한 재시도 방지, 락 로직은 자원 관리 코드 내부에 한정 |
| V15.4.4 | 3 | 스레드 풀 등 공정한 자원 할당 정책으로 thread starvation 방지 |

왜 국내에 없는가: SBOM·dependency confusion·mass assignment·prototype pollution 등은
국내 기준에 대응 항목이 없음. 경쟁 조건·TOCTOU 는 구현단계 C 가이드와 일부 겹치나
**설계단계 SR 20개에는 대응이 없어** 공백 챕터로 분류함.

### V17 WebRTC (12개 / L1 0 · L2 7 · L3 5)

섹션: 17.1 TURN Server · 17.2 Media · 17.3 Signaling

| ID | L | 요구사항 요지 |
|---|---|---|
| V17.1.1 | 2 | TURN 서비스는 특수 목적 예약 IP(내부망·브로드캐스트·루프백)로의 접근 불허 — IPv4·IPv6 모두 |
| V17.1.2 | 3 | 정당 사용자의 대량 포트 개방 시도에도 TURN 서버가 자원 고갈되지 않게 |
| V17.2.1 | 2 | DTLS 인증서 키를 문서화된 암호키 관리 정책에 따라 관리·보호 |
| V17.2.2 | 2 | 미디어 서버는 승인된 DTLS cipher suite 와 DTLS-SRTP 키 수립용 보안 보호 프로파일 사용 |
| V17.2.3 | 2 | 미디어 서버에서 SRTP 인증 검사 — RTP injection 에 의한 DoS·오디오/비디오 삽입 방지 |
| V17.2.4 | 2 | 변조(malformed) SRTP 패킷을 만나도 수신 미디어 처리 지속 |
| V17.2.5 | 3 | 정당 사용자발 SRTP 패킷 플러드 중에도 수신 미디어 처리 지속 |
| V17.2.6 | 3 | DTLS "ClientHello" 경쟁 조건 취약점 비해당 확인 — 공개 취약 정보 대조 또는 직접 테스트 |
| V17.2.7 | 3 | 미디어 서버 연계 녹음·녹화 메커니즘도 SRTP 플러드 중 처리 지속 |
| V17.2.8 | 3 | DTLS 인증서를 SDP fingerprint 속성과 대조, 불일치 시 미디어 스트림 종료 — 스트림 진본성 보장 |
| V17.3.1 | 2 | 시그널링 서버는 플러드 공격 중에도 정상 시그널링 메시지 처리 지속 — 시그널링 수준 rate limiting |
| V17.3.2 | 2 | 변조 시그널링 메시지에 의한 DoS 방지 — 입력 검증·정수/버퍼 오버플로 안전 처리·견고한 오류 처리 |

왜 국내에 없는가: WebRTC(TURN·DTLS-SRTP·시그널링)는 5.0 신설 도메인 챕터로,
**국내 설계·구현 기준 어디에도 관련 항목이 전혀 없음**.

---

## 4.0.3 → 5.0.0 마이그레이션 요약

근거: `5.0/en/0x05-For-Users-Of-4.0.md` (태그 v5.0.0) 및 공식 매핑 YAML
(`5.0/mappings/mapping_v5.0.0_to_v4.0.3.yml`, `mapping_v4.0.3_to_v5.0.0.yml`).

| 변경 사실 | 내용 |
|---|---|
| 무변경 생존 | 4.0.3 의 286개 중 **11개만 무변경 생존** — 5.0 의 345 = 신규 189 + 수정 130 + 문구 정리 15 + 이동 11 |
| 제거 | **109개(38%)가 별도 요구사항으로 존속하지 않음** — 단순 삭제 50 + 중복 제거 28 + 타 항목 병합 31 |
| V1 챕터 삭제 | 4.0.3 V1 「Architecture」 챕터 삭제 — 일부는 범위 밖, 나머지는 타 챕터 재배치. 5.0 의 V1 은 별개 챕터(Encoding and Sanitization) |
| L1 비중 급감 | 46%(128/278) → 20%(70/345) |
| 레벨 기준 변경 | "블랙박스 검증 용이성" → **"위험 감소 효과 + 구현 노력"** 기준으로 재배정 |

⚠️ **분모 주의 (286 vs 278)**: 4.0.3 원문에는 286개 항목이 있으나 그중 8개는 4.0.3 자체에서
이미 `[DELETED, ...]` 로 표기된 자리표시(tombstone)임. 실질 활성 요구사항은 **278개**이고
5.0 매핑 문서는 278개만 대상으로 함 — "286개 중 11개 생존"과 "128/278"은 분모가 다르며,
둘 다 원문 표현이므로 인용 시 어느 분모인지 밝혀야 함.

---

## 인용·전재 주의 (과잉 인용 금지)

- 이 파일은 CC BY-SA 4.0 원문의 **한국어 요지 색인**임 — 요구사항 원문 전재를 하지 말 것
  (ShareAlike 전염 방지). 원문 확인은 저장소 flat.json(태그 v5.0.0)으로 할 것
- **이 파일은 제도 판정 근거가 아님** — ASVS 는 구속력 없는 국제 기술 권고이며, 진단·검증
  제출물의 정본은 국내 원문 기준(`secure-coding-kr`·`mobile-app-verify`)임
- ASVS 근거 지적 시에는 요구사항 ID·버전(ASVS 5.0.0)·조회일과 **"구속력 없음"** 을 병기하고,
  부적합 판정 근거로 사용하지 말 것
- 산출물에 내용을 옮길 때는 출처 4요소(출처·버전·라이선스·조회일)를 함께 기재할 것
