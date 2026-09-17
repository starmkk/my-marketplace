---
name: secure-coding-java
description: |
  Java/Android 시큐어코딩 및 SW 보안약점 진단원 관점의 취약→안전 코드 패턴 레퍼런스 스킬.
  Java/Android secure coding and weakness remediation reference (auditor's view).

  사용자가 다음 표현을 쓸 때 반드시 이 스킬을 사용하라 (Trigger):
  - "Java 시큐어코딩", "Java 보안약점", "Android 시큐어코딩"
  - "SQL 인젝션", "PreparedStatement", "XSS", "경로 조작", "OS 명령어 삽입"
  - "IDOR", "권한 상승", "fail-open"
  - "착시 조치", "조치 반려"
  - "하드코딩 비밀번호", "약한 해시", "SecureRandom"
  - "MODE_WORLD_READABLE", "android:exported", "sharedUserId"
  일반 Java/Android 개발·디버깅에는 쓰지 마라 — 보안 진단·시큐어코딩 검토 맥락일 때만.

  경계: 키 길이=`crypto-policy-kr`, 기준·오탐=`secure-coding-kr`, 검증 제출=`mobile-app-verify`.

  관련 스킬:
  - `secure-coding-kr`: 보안약점 기준·진단절차 허브.
  - `secure-coding-c`: C/C++ 시큐어코딩.
  - `mobile-app-verify`: 모바일 전자정부 앱 검증 절차.
  - `crypto-policy-kr`: 암호 알고리즘·키 길이 권고.
---

# Java 시큐어코딩 레퍼런스 스킬

## 1. 개요

이 스킬은 근거 문서 2종을 기반으로 한다. **두 문서의 발행 시점(vintage)이 15년 차이**나므로, 반드시 출처와 시점을 구분해서 인용해야 한다.

| 근거 문서 | 발행 | 성격 | 이 스킬에서의 역할 |
|---|---|---|---|
| 「SW 보안약점 진단원 관점의 시큐어코딩 · Java」 교안 (47p) | **2026.09** | 개발자 대상 강의 교안. 진단원 관점(취약점 찾기 + 조치 승인/반려 판정) | **주력 근거** — 최신 실무 기준 |
| 행안부/KISA 「Android-JAVA 시큐어 코딩 가이드(2판)」 (42p) | **2011.09** | SW 개발보안 가이드 붙임3. 7개 유형 17개 항목 | 원전(原典) — Android 특화 3종의 출처. **일부 권고는 구식** |

> 서술 원칙 (이 스킬 전체 공통):
> - **✅ 권장** 블록에는 **지금 써야 할 현행 모범사례**를 제시한다 (출처 병기).
> - **📋 원문 근거** 블록에는 원문(2011/2026)이 무엇을 제시했는지, 현행 권고와 다르면 왜 다른지를 기록한다.
> - 원문에 없는 항목을 원문에 있는 것처럼 쓰지 않는다. 원문 밖 내용은 "원문 미기재 — 현행 권고"로 표기한다.
> - **권위 수준 구분**: 📕 **제도 기준** = 적합/부적합 판정 근거(고시·진단가이드 2021 등 — 문서·페이지 인용 필수) / 📋 **원문 권고** = 그 문서가 제시한 방법(당시 기준 — 현행과 다를 수 있음) / ✅ **현행 권고** = NIST/OWASP/CERT 등(**구속력 없음** — 출처·기준시점 명시) / ❌ **취약 코드** = 진단 대상 패턴. 제도 판정 근거(📕)와 현행 권고(✅)가 어긋나는 지점에서는 **양쪽을 병기**하고 어느 맥락의 판단인지 밝힌다.

**보고서 기재값의 정본(正本) 라우팅**: 진단 보고서에 기재할 **기준번호(1~49)·공식 보안약점명·CWE**는 허브 스킬 `secure-coding-kr`의 `references/weakness-49.md` 총괄표가 정본이며, 이 스킬은 취약→안전 **구현·수정 패턴**을 담당한다 — §3 각 절 머리의 기준표는 그 총괄표에서 옮겨 적은 것이다.

## 2. 진단 관점의 핵심 원칙

2026 교안의 관통 메시지 (제1장 + 마무리 슬라이드 「진단원의 눈으로」):

- 취약점은 **설계·구현 단계에서 코드에 들어오고**, 결함은 늦게 찾을수록 수정 비용이 커진다 → 진단은 "앞당긴 검증"(시프트 레프트). 보안팀은 만드는 사람이 아니라 검증자다.
- 진단의 3단 시선: **입력(Source) → 흐름 → 합쳐지는 곳(Sink)**.
- **도구를 믿되 의존하지 마라** — 오탐·미탐을 가려내는 눈이 진단원의 전문성이다.
- **'고쳤다'는 말이 아니라 코드를 검증하라** — 조치의 방향과 강도까지. 진단의 절반은 조치 승인/반려 판정이다(§4 착시 조치 참조).
- **공격자의 상상력을 가져라** — 실패 흐름, 예외, 아무도 안 보는 로그는 "정상 테스트로는 절대 안 걸린다".
- 프레임워크 시대의 진단 대상은 **프레임워크가 기본 대응하는 영역의 바깥**이다.

## 3. 주제별 취약→안전 코드 패턴

각 절은 `❌ 취약 코드(원문) → ✅ 권장(현행 모범사례) → 📋 원문 근거 → 진단 포인트` 순으로 구성한다.
❌ 코드는 2026 교안 원문 스니펫 그대로다. 전체 스니펫 전수는 `references/java-patterns.md` 참조.

### 3.1 입력값 검증과 인젝션 (교안 2장)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 1 | SQL 삽입 | CWE-89 |
| 5 | 운영체제 명령어 삽입 | CWE-78 |
| 4 | 크로스사이트 스크립트 | CWE-79 |

"인터프리터가 있는 곳에 인젝션이 있다. DB는 SQL을, 셸은 명령어를, 브라우저는 HTML을 읽는다." — SQL·OS명령·XSS는 **데이터·명령 분리**라는 하나의 원리다.

❌ 취약 코드 (교안 p.8, p.10)

```java
String sql = "SELECT * FROM members "
   + "WHERE user_id = '" + userId + "' "
   + "AND password = '" + pw + "'";   // 취약: 문자열 결합
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(sql);
```

```java
// 명령어 인젝션
String cmd = "/usr/bin/convert " + filename + " out.png";
Runtime.getRuntime().exec(new String[]{"sh","-c",cmd}); // 취약

// XSS (반사형)
String q = request.getParameter("q");
out.println("<div>검색어: " + q + "</div>");   // 취약: 미인코딩
```

✅ 권장 (현행 모범사례)

```java
// SQL: 파라미터 바인딩 (JDBC 표준 API)
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM members WHERE user_id = ? AND password_hash = ?");
ps.setString(1, userId);
ps.setString(2, hash);
// 동적 ORDER BY 컬럼·정렬 방향은 바인딩 불가 → 허용 목록(화이트리스트)과 대조 후 결합

// OS 명령: 셸 미경유 + 인자 분리 (Java 표준 API)
new ProcessBuilder("/usr/bin/convert", filename, "out.png").start();

// XSS: 출력 위치(HTML body/attribute/JS/URL)에 맞는 문맥별 인코딩
// 출처: OWASP XSS Prevention Cheat Sheet — 입력 필터링이 아니라 출력 인코딩이 근본 대책
```

📋 원문 근거: 2026 교안 p.11 체크리스트 — "파라미터 바인딩 / 동적 컬럼·정렬은 화이트리스트", "셸(sh -c) 미사용, ProcessBuilder로 인자 분리", "출력 위치에 맞는 인코딩(입력 필터링 아님)". 교안은 ESAPI·OWASP Encoder 같은 구체적 라이브러리를 언급하지 않는다(원칙 수준). 문맥별 인코딩의 세부 규칙은 원문 미기재 — 현행 권고(OWASP)로 보강한 것이다.

**진단 포인트** (grep 대상):
- `Statement` + `createStatement()` + `executeQuery(` 에 문자열 `+` 결합 → SQLi
- `prepareStatement` 를 쓰더라도 SQL 문자열에 `+` 가 남아 있으면(특히 `ORDER BY`, 컬럼명, 테이블명) 여전히 취약 (§4 착시 8번)
- `Runtime.getRuntime().exec(` 에 `"sh"`, `"-c"` 또는 문자열 결합 → 명령어 인젝션. 단, `exec(String[])` 인자 분리 + 셸 미경유면 **오탐 가능성** — 교안 p.10 "셸 없이 exec면 통했을까?"
- `out.println(` / JSP 표현식에 `request.getParameter` 값이 인코딩 없이 출력 → XSS

### 3.2 파일 업로드와 경로 조작 (교안 3장)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 3 | 경로 조작 및 자원 삽입 | CWE-99, CWE-22 |
| 6 | 위험한 형식 파일 업로드 | CWE-434 |

"웹셸 = 실행되는 파일(.jsp)을 실행되는 위치(웹 루트)에 올리는 것. 종류·위치 둘 다 뚫려야 서버가 넘어간다." 업로드 방어는 **종류·이름·저장 위치·실행 차단**의 4겹이다.

❌ 취약 코드 (교안 p.14, p.16)

```java
String basePath = "/app/data/files/";
File target = new File(basePath + filename); // 취약: 미검증 결합
```

```java
if (!file.getContentType().startsWith("image/"))
  throw new Exception();          // 취약: 헤더는 위조 가능
File dest = new File("/app/webroot/avatars/"+name);
file.transferTo(dest);            // 취약: 웹 실행 경로
```

✅ 권장 (현행 모범사례)

```java
// 경로 조작: 정규화 후 기준 디렉터리 경계 검사 (Java 7+ java.nio.file 표준 API)
Path base = Paths.get("/app/data/files").toRealPath();
Path target = base.resolve(filename).normalize();
if (!target.startsWith(base)) {
  throw new SecurityException("경로 이탈 시도");
}
```

업로드 4겹 (교안 p.17 체크리스트와 동일 원리):
1. **종류**: 확장자 화이트리스트 + 서버 측 파일 시그니처(매직 바이트) 검증 — Content-Type 헤더 검사만으로는 무효
2. **이름**: 서버에서 파일명 재생성(UUID 등) — 사용자 입력 파일명을 경로에 쓰지 않음
3. **위치**: 웹 루트 밖, 실행 불가 저장소
4. **실행 차단**: 저장 디렉터리의 스크립트 실행 권한 제거

📋 원문 근거: 2026 교안 p.17 — "정규화 후 기준 폴더 경계 확인 / 확장자 화이트리스트 + 서버 측 시그니처 검증 / 서버에서 파일명 재생성 / 웹 루트 밖, 실행 불가 저장소". `Path.normalize()+startsWith()` 구현은 원문 미기재 — 현행 권고(Java 표준 API)로 옮긴 것. 2011 가이드(CWE-23/36)는 `replaceAll()`로 위험 문자를 제거하는 방식을 제시했으나, 블랙리스트 문자 제거는 우회 여지가 있어 현재는 정규화+경계검사가 표준이다(§6 참조).

> **CWE 표기 채택 규칙**: 진단 보고서에는 **2021 진단가이드(허브) 기준 3 「경로 조작 및 자원 삽입」(CWE-99, CWE-22)** 을 기재한다. 2011 원문의 CWE-23(상대 경로 조작)·CWE-36(절대 경로 조작)은 참고 표기로만 병기한다.

**진단 포인트**:
- `new File(` 에 사용자 입력이 `+` 결합 → 경로 조작. `../` 필터만 있으면 우회(인코딩, 중첩) 검토
- 확장자 검사가 `endsWith` **블랙리스트**(`.jsp`, `.php`…)면 반려 — 화이트리스트인지 확인
- `getContentType()` 검사만 있으면 반려 — 시그니처 검증 여부 확인
- 저장 경로에 `webroot`, `www`, 정적 서빙 디렉터리가 보이면 웹셸 성립 조건 확인

### 3.3 계정·인증 관리 (교안 4장)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 23 | 하드코드된 중요정보 | CWE-259, CWE-321 |
| 21 | 취약한 암호화 알고리즘 사용 (MD5 등 깨진 해시) | CWE-327 |
| 31 | 솔트 없이 일방향 해쉬 함수 사용 | CWE-759 |
| 15 | 보안기능 결정에 사용되는 부적절한 입력값 | CWE-807 |
| 33 | 반복된 인증시도 제한 기능 부재 | CWE-307 |
| 29 | 사용자 하드디스크에 저장되는 쿠키를 통한 정보 노출 | CWE-539 |

(세션 고정·계정 열거는 구현단계 49개 기준에 1:1 대응 항목이 없다 — 설계단계 기준 SR4-1 세션통제·SR2-1 인증 대상 및 방식 연관. 보고 항목명이 필요하면 허브 문서에서 확인 필요.)

인증(Authentication) = "너는 누구인가", 인가(Authorization) = "무엇을 할 수 있나" — 이 둘의 구분이 4·5장의 전제다.

❌ 취약 코드 (교안 p.20, p.22)

```java
private static final String ADMIN_PW = "P@ssw0rd2020"; // 취약: 하드코딩
private static final String API_KEY  = "sk_live_9f83.."; // 취약
public boolean login(String id, String pw) {
  String stored = userDao.findPasswordHash(id); // MD5
  return md5(pw).equals(stored);   // 취약: 약한 해시·솔트 없음
}
```

```java
// 세션 고정
if (login(id, pw)) {
  HttpSession s = req.getSession(); // 취약: 기존 세션 재사용
  s.setAttribute("user", id);
}
// 계정 열거
if (u == null) return error("존재하지 않는 아이디"); // 취약
if (!verify(pw)) return error("비밀번호 불일치");   // 취약
```

✅ 권장 (현행 모범사례)
- 비밀번호 저장: **bcrypt / Argon2id / PBKDF2WithHmacSHA256** 등 솔트+스트레칭이 내장된 느린 해시 (출처: OWASP Password Storage Cheat Sheet, NIST SP 800-63B). 단순 SHA-256(이중 적용 포함)은 무효.
- 자격증명·API 키: 소스와 저장소에서 분리(환경변수·비밀 관리 시스템). `.properties` 도 git에 올라가면 하드코딩과 동일.
- 세션: 로그인 성공 시 세션 ID 재발급 — `request.changeSessionId()` (Servlet 3.1+) 또는 기존 세션 `invalidate()` 후 신규 발급. 로그아웃 시 무효화.
- 실패 응답: 아이디 존재 여부가 구분되지 않는 **단일 메시지**("아이디 또는 비밀번호가 올바르지 않습니다").

📋 원문 근거: 2026 교안 p.23 — "느린 해시(bcrypt/Argon2)+사용자별 솔트 / 소스·설정에 비밀정보 부재(git 노출 확인) / 로그인 후 재발급, 로그아웃 시 무효화 / 실패 응답이 사용자 존재 여부를 흘리지 않음". `changeSessionId()` 메서드명은 원문 미기재 — 현행 권고(Servlet 3.1 표준)로 구체화한 것.

**진단 포인트**:
- `private static final String` 에 `PW`, `PASSWORD`, `KEY`, `SECRET`, `sk_live` 류 리터럴 → 하드코딩. git 이력 노출도 확인
- `md5(`, `MessageDigest.getInstance("MD5")`, `"SHA-1"` 이 비밀번호 경로에 있으면 반려
- 로그인 성공 분기에 세션 재발급 호출이 없으면 세션 고정
- 로그인 실패 메시지가 2종류로 갈리면 계정 열거

#### 3.3.1 쿠키·헤더·파라미터 값을 신원으로 신뢰 — 기준 15 「보안기능 결정에 사용되는 부적절한 입력값」 (CWE-807)

위의 세션 고정 진단은 **세션이 이미 존재한다는 전제**다. 세션 자체가 없고 클라이언트가 보낸 값을 그대로 신원·권한으로 믿는 코드는 세션 고정이 아니라 **기준 15(CWE-807)로 보고**한다 — 실체는 인증 우회이며, 세션 고정으로 축소 평가하면 안 된다.

❌ 취약 코드 (원문 미기재 — 실전 패턴)

```java
// 쿠키 문자열을 그대로 신원으로 사용 — Cookie: user=admin 한 줄로 사칭 가능
String user = getCookieValue(request, "user");
if ("admin".equals(user)) { showAdminPage(); }   // 취약: 서명·검증 없는 외부 입력으로 권한 판정
```

✅ 권장 (현행 모범사례)
- 인증 주체는 **서버 측 세션(`HttpSession`)에 저장** — 클라이언트가 보낸 쿠키·헤더·파라미터 값은 **식별자일 뿐 신원 증명이 아니다.** 쿠키에는 `SecureRandom` 기반 추측 불가 세션 ID만 담는다 (§3.5).
- 토큰을 클라이언트에 두어야 한다면 **서명 검증 필수** — JWT는 서명·만료(`exp`)·`alg` 검증(`alg=none` 거부) (출처: OWASP JSON Web Token Cheat Sheet, RFC 8725).

📋 원문 근거: `weakness-49.md` 15번 정의(p.297) — "개발자는 **쿠키**·환경변수·히든필드가 조작될 수 없다고 가정하지만 공격자는 변경할 수 있다. 충분한 암호화·무결성 체크 없이는 외부 입력값을 신뢰하지 말 것." 대응방안(p.297) — "상태정보·민감 데이터(특히 세션정보)는 서버에 저장, 보안확인 절차도 서버에서 실행." 진단방법(p.300~302) 취약 예 — "평문 인증정보를 쿠키에 저장."

**진단 포인트**:
- `getCookies()` / `getHeader(` / `getParameter(` 반환값이 권한 분기(`if (role.equals("admin"))` 등)에 **직접** 쓰이는지 grep → 쓰이면 기준 15 정탐
- 히든 필드·쿠키의 가격·등급·인증 플래그(`authenticated=true`)를 서버 검증 없이 사용 → 기준 15

#### 3.3.2 무차별 대입 방어 — 기준 33 「반복된 인증시도 제한 기능 부재」 (CWE-307)

❌ 취약: 로그인 실패 횟수를 세지 않음 — 시도 제한·잠금·지연이 전무하면 그 자체로 기준 33 정탐. `weakness-49.md` 33번 진단방법(p.404~405): "**인증 함수 호출 횟수 확인 + 호출 제한 코드 존재 여부** 확인. 없으면 취약."

✅ 권장 (현행 모범사례, 출처: OWASP Authentication Cheat Sheet)
- **계정 단위** 실패 횟수 제한 + 초과 시 점증 지연(백오프) 또는 계정 잠금·추가 인증(CAPTCHA·2FA)
- **IP 단위 rate limit 병행** — 계정 잠금만으로는 잠금 유발 DoS·패스워드 스프레이를 못 막는다
- **잠금 해제 절차**(시간 경과 자동 해제 또는 본인 확인 후 해제)를 함께 설계. 잠금 사실은 응답으로 흘리지 않음(위 "단일 메시지" 원칙과 동일)

📋 원문 근거: `weakness-49.md` 33번 대응방안(p.400) — "**인증시도 횟수 제한**. 실패 횟수 초과 시 **계정 잠금 또는 추가 인증** 요구." (2026 교안 미기재 — 진단가이드 2021 + 현행 권고로 보강.)

#### 3.3.3 쿠키 보안속성 — HttpOnly · Secure · SameSite

세션·인증 쿠키 발급 시 3속성을 함께 설정한다 (출처: OWASP Session Management Cheat Sheet — `weakness-49.md` 29번 「사용자 하드디스크에 저장되는 쿠키를 통한 정보 노출」(CWE-539)의 💡현행 권고와 동일. 영속 쿠키는 만료시간 최소화 + 권한 등급·세션ID 등 중요정보 포함 금지 — 29번 대응방안 p.382):

```java
Cookie session = new Cookie("SESSIONID", sid);  // sid는 SecureRandom 기반 (§3.5)
session.setHttpOnly(true);  // JS 접근 차단 — XSS 시 세션 탈취 방지 (Servlet 3.0+)
session.setSecure(true);    // HTTPS로만 전송 — weakness-49.md 22번 대응방안(p.337)에도 기재
session.setPath("/");
response.addCookie(session);
// SameSite는 Servlet 표준 Cookie API 미지원 — 헤더로 직접 설정
response.setHeader("Set-Cookie",
    "SESSIONID=" + sid + "; Path=/; HttpOnly; Secure; SameSite=Lax");
```

**진단 포인트**: `addCookie(` / `Set-Cookie` 발급 지점에 `HttpOnly`·`Secure`·`SameSite` 부재 → 지적. 세션 ID·권한 등급이 장기 만료의 영속 쿠키에 저장 → 기준 29 정탐.

### 3.4 접근통제·인가 (교안 5장 — OWASP 1위)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 19 | 부적절한 인가 (수평 IDOR·수직 권한 상승) | CWE-285 |
| 18 | 적절한 인증 없는 중요기능 허용 | CWE-306 |

수평(IDOR) = "같은 등급인데 남의 것", 수직(권한 상승) = "낮은 권한이 높은 기능으로". **숨김 ≠ 통제, 검증은 서버에서만.**

❌ 취약 코드 (교안 p.26, p.28)

```java
@GetMapping("/orders/{orderId}")
public OrderDto getOrder(@PathVariable Long orderId) {
  Order o = orderRepository.findById(orderId).orElseThrow();
  return toDto(o);   // 취약: 소유권(인가) 검사 없음
}
```

```java
u.setName(form.getName());
u.setEmail(form.getEmail());
u.setRole(form.getRole());   // 취약: 폼 값으로 역할 설정 (Mass Assignment)
repo.save(u);
```

✅ 권장 (현행 모범사례)
- **수평**: 자원 조회 시 로그인 주체와 자원 소유자를 서버에서 대조 — 예: `orderRepository.findByIdAndUserId(orderId, loginUserId)` 형태로 소유권을 질의 조건에 포함.
- **수직**: 기능(URL) 접근 시 역할을 서버에서 검증 — 모든 관리자 엔드포인트에 서버 측 인가 검사. UI 숨김·JS 검사는 보안 조치가 아니다.
- **민감 필드**: `role`, `admin` 등 권한 필드는 요청 본문에서 받지 않는다 — 수정 가능 필드만 담은 DTO로 바인딩 범위를 제한.

📋 원문 근거: 2026 교안 p.29 — "자원 접근 시 소유권을 서버에서 검증 / 기능 접근 시 역할을 서버에서 검증 / 모든 요청을 서버 측에서(클라이언트 검증 불신) / role 등 권한 필드를 입력으로 받지 않음". 특정 프레임워크 어노테이션(@PreAuthorize 등)은 원문 미기재.

**진단 포인트**:
- `findById(입력값)` 직후 소유권 비교 없이 반환 → IDOR
- 권한 검사가 JSP/JS(`<c:if test="${user.role=='ADMIN'}">`)에만 있고 컨트롤러에 없으면 반려 (§4 착시 5번)
- 요청 폼/DTO에 `role` 세터가 바인딩되면 수직 권한 상승

### 3.5 암호화·민감정보 보호 (교안 6장)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 21 | 취약한 암호화 알고리즘 사용 | CWE-327 |
| 22 | 암호화되지 않은 중요정보 | CWE-312, CWE-319 |
| 24 | 충분하지 않은 키 길이 사용 | CWE-326 |
| 25 | 적절하지 않은 난수 값 사용 | CWE-330 |
| 31 | 솔트 없이 일방향 해쉬 함수 사용 | CWE-759 |
| 23 | 하드코드된 중요정보 (하드코딩 암호화 키) | CWE-259, CWE-321 |

먼저 가른다: **되돌릴 필요 없다 = 해시 / 되돌려야 한다 = 양방향 암호화.** 고유식별정보(주민·여권·운전면허·외국인등록번호)는 무조건 암호화. **Base64는 암호화가 아니다.**

❌ 취약 코드 (교안 p.32, p.33, p.34)

```java
String encSsn = md5(ssn);   // 취약: 주민번호를 MD5(일방향)로 — 복원 불가 + 깨진 해시
member.setSsn(encSsn);
member.setPhone(phone);     // 취약: 전화번호 평문
```

```java
private static final String KEY="mySecretKey123"; // 취약: 하드코딩 키
// XOR 자작 암호 + Base64 → 취약: 인코딩≠암호화
```

```java
Random rnd = new Random();      // 취약: 예측 가능한 난수
long token = rnd.nextLong();    // 비밀번호 재설정 토큰
```

✅ 권장 (현행 모범사례)
- 양방향 암호화: `Cipher.getInstance("AES/GCM/NoPadding")` + 호출마다 고유 IV(96bit 권장) — 인증 암호화(AEAD) (출처: NIST SP 800-38D). ECB·모드 미지정(`"AES"`)은 금지. 국내 제도 대응(SEED/ARIA/LEA, 검증필 암호모듈)은 `crypto-policy-kr` 스킬 참조.
- 키 관리: 키를 소스에서 분리(KMS·키스토어·환경변수).
- 보안 난수: `java.security.SecureRandom` (가능하면 `SecureRandom.getInstanceStrong()`) — 토큰·키·세션ID 전부 (출처: Java SE 표준 API, 교안 2026 동일).
- 해시/양방향 구분: 비밀번호는 §3.3의 느린 해시, 복호화가 필요한 개인정보는 양방향 암호화.

📋 원문 근거: 2026 교안 p.35 — "검증된 표준(공공은 검증필 모듈), **MD5·SHA-1·DES 금지** / 키는 소스와 분리 / Base64를 암호화로 착각 금지 / 보안 목적은 SecureRandom". GCM 모드·IV 규칙은 원문 미기재 — 현행 권고(NIST)로 구체화. 2011 가이드는 `AES/CBC/PKCS5Padding`을 제시했으나 현재는 GCM이 우선이다(§6). 교안의 "SHA-1 금지"는 용도 무구분 서술 — 제도 판정의 용도별 구분은 아래 진단 포인트 참조.

**진단 포인트**:
- `"MD5"`, `"DES"`, `"RC4"` 리터럴 → 즉시 반려 대상
- `"SHA-1"` 리터럴 → **용도 확인 후 판정** (일괄 반려 금지). 📕 제도 판정: 단순해시(비밀번호 저장 포함)·전자서명 용도는 반려하되, **메시지인증(HMAC)·키유도·난수생성 용도는 KISA 안내서(2018)상 허용** — HMAC-SHA1을 "SHA-1 금지"로 일괄 지적하면 과잉 지적이다 (판정 근거: `crypto-policy-kr` 「사용 제한 알고리즘」 표). ✅ 현행 권고: 신규 설계는 SHA-256 이상 (출처: NIST SP 800-131A Rev.2, 2019)
- `new Random(`, `Math.random()` 이 토큰·키·세션ID 생성 경로에 있으면 반려
- `Base64` 가 "암호화"라는 이름의 메서드 안에 있으면 착시 조치 의심
- `Cipher.getInstance("AES")` 처럼 모드 미지정, 또는 `"/ECB/"` → 반려
- 자작 `encrypt()` 함수(XOR, 시프트 연산) → 반려

### 3.6 예외 처리·로그 보안 (교안 7장)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 36 | 오류 메시지 정보노출 | CWE-209 |
| 37 | 오류상황 대응 부재 | CWE-390 |
| 38 | 부적절한 예외 처리 | CWE-754 |

"공격자는 정상 경로가 아니라 예외를 파고든다." **확신이 없으면 막아라 — 보안은 fail-closed.** 이런 결함은 "정상 테스트로는 절대 안 걸린다."

❌ 취약 코드 (교안 p.38, p.39, p.40)

```java
try {
  return permissionService.check(user, orderId).isAllowed();
} catch (Exception e) {
  System.out.println("오류: " + e);
  return true;    // 취약: 예외 시 통과 (fail-open)
}
```

```java
} catch (Exception e) {
  return null;    // 취약: 예외 삼킴 (기록 없음)
}
```

```java
log.info("로그인: id="+id+", pw="+pw           // 취약: 비번 로깅
  +", token="+token+", 주민번호="+ssn);         // 취약: 민감정보
log.info("조회 요청: " + userId);   // 취약: 로그 인젝션
```

✅ 권장 (현행 모범사례)
- 보안 검사의 예외는 **거부(return false / throw)** 로 실패 — fail-closed.
- 예외는 삼키지 말고 **기록 후 전파** 또는 전역 예외 처리기로 위임 — 사용자에게는 일반 메시지, 로그에는 상세.
- 로그 3축: **남길 것**(인증 성공/실패, 권한 거부 등 보안 사건) / **뺄 것**(비밀번호·토큰·주민번호 등 민감정보) / **누가 보나**(이상 징후 알림).
- 로그 인젝션: 외부 입력은 개행(`\r`, `\n`) 제거·인코딩 후 기록 (원문 미기재 세부 — 현행 권고: OWASP Log Injection 항목).

📋 원문 근거: 2026 교안 p.41 — "사용자엔 일반 메시지, 로그엔 상세(전역 예외 처리) / 보안 검사 예외 시 fail-closed(거부) / 예외를 기록·전파, 삼키지 않음 / 보안 사건 기록·민감정보 제외·이상 징후 알림". 2011 가이드도 같은 계열을 CWE-209(오류 메시지 정보 노출)·CWE-390(오류 상황 처리 부재)·CWE-497(시스템 데이터 누출)로 다룬다.

**진단 포인트**:
- `catch` 블록에서 `return true` (보안 검사 경로) → fail-open, 최우선 반려
- `catch (Exception e) { }` 빈 블록, `return null` 만 → 예외 삼킴
- `e.printStackTrace()`, `resp.getWriter().write("오류:"+e)`, `e.getMessage()` 응답 출력 → 정보 노출
- `log.` 호출 인자에 `pw`, `password`, `token`, `ssn`, 주민번호 변수 → 민감정보 로깅

**에러처리 기준 36·37·38 판정 분기표** — 보고서에 어느 항목명을 쓸지 이 표로 결정한다 (근거: `weakness-49.md` p.419~432):

| 코드 상황 | 해당 기준 | CWE | 판정 근거 (원문 진단방법) |
|---|---|---|---|
| catch 블록이 비어 있음 (`catch (Exception ignore) {}`) | 37 오류상황 대응 부재 | CWE-390 | "예외 처리 루틴(제어문)이 **비어있는지** 확인. catch 하고도 **아무 조치를 하지 않는 경우**"(p.427~428) |
| `catch (Exception e)` 광역 포착, 함수 반환값 미검사 | 38 부적절한 예외 처리 | CWE-754 | "**광범위한 처리 대신 구체적인 예외 처리**"(p.429), "반환값 검사·구체적 예외처리 수행 여부 확인"(p.431~432) |
| 예외 메시지·스택트레이스를 사용자에게 출력 | 36 오류 메시지 정보노출 | CWE-209 | "**예외이름·스택 트레이스 출력**으로 내부구조 노출"(p.419). 민감정보 여부는 진단원이 직접 판단(p.421~424) |

중복 해당 시 판정 지침: `catch (Exception ignore) {}` 처럼 한 코드가 37(비어 있음)·38(광역 포착)에 동시에 걸릴 때의 주(主)/부(副) 선택 기준은 **허브 문서 미기재** — 진단 보고서에 양쪽 근거를 병기하고, 지배적 결함(아무 조치 없음 → 37 주, 예외 구체화 부재 → 38 부)을 명시할 것을 권장한다.

### 3.7 코딩 보안 모범 사례 (교안 8장)

이 절은 종합 원칙 절이라 특정 기준에 1:1 대응하지 않는다. 단 아래 종합 예제는 다음 기준으로 보고한다 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 1 | SQL 삽입 (ORDER BY 동적 컬럼 결합) | CWE-89 |

"취약점은 많아도 원칙은 몇 개" — 7대 원칙:

| 원칙 | 설명 (교안 p.43 원문) |
|---|---|
| 입력을 불신하라 | 허용된 것만 통과 (2·3·5강) |
| 데이터·명령 분리 | 바인딩·인자분리·출력인코딩 (2강) |
| 최소 권한 · 겹 방어 | 꼭 필요한 것만 / 여러 겹 (5·3강) |
| 안전한 실패 · 보호·감시 | fail-closed / 민감정보·로그 (4·6·7강) |

종합 진단 훈련의 핵심 (교안 p.46, 심화): **"PreparedStatement로 바인딩했으니 안전"이라는 판정은 `ORDER BY` 동적 컬럼에서 무너진다.** 도구·패턴 매칭이 아니라 Source→흐름→Sink를 봐야 한다.

```java
String sql = "SELECT ... FROM orders "
  + "WHERE user_id = ? "
  + "ORDER BY " + sortColumn + " " + dir;  // (a) 취약: 바인딩 대상 아님
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, userId);                       // (b) 이것만으로는 불충분
```

## 4. 착시 조치(반려 대상) 패턴 — 이 스킬의 핵심

2026 교안의 각 장 실습 B는 "개발팀이 조치했다고 회신했지만 실제로는 무효인 조치"를 판별하는 훈련이다. 진단원이 **반려**해야 할 8종 착시 패턴:

| # | 착시 패턴 (개발팀 회신) | 왜 무효한가 | 올바른 조치 |
|---|---|---|---|
| 1 | "위험 문자(따옴표·세미콜론·SELECT·UNION)를 필터링했다" (SQLi) | 블랙리스트는 우회 가능. 게다가 **pw 필드는 sanitize를 거치지 않음**(적용 누락) — 조치의 '범위'까지 검증해야 한다 | PreparedStatement 파라미터 바인딩. 동적 컬럼·정렬은 화이트리스트 |
| 2 | ".jsp/.php/.exe 확장자를 차단했다 + 클라이언트 재검사" | 확장자 블랙리스트는 우회 가능(대소문자·이중 확장자 등). **저장 위치가 여전히 웹루트**. 클라이언트 재검사는 무의미 | 확장자 화이트리스트 + 시그니처 검증 + 웹루트 밖 저장 + 파일명 재생성 |
| 3 | "Content-Type이 image면 허용한다" | **HTTP 헤더는 위조 가능** — 시그니처 검증이 아니다 | 서버 측 파일 시그니처(매직 바이트) 검증 + 저장 위치 분리 |
| 4 | "SHA-256을 두 번 적용했다" (비밀번호) | "강화가 아니라 착시" — 빠른 해시를 반복해도 빠르다. **솔트·느린 해시가 빠짐** | bcrypt / Argon2id / PBKDF2 + 사용자별 솔트 |
| 5 | "관리자 메뉴를 숨기고 JS로 권한 체크했다" | **UI 숨김·클라이언트 검증은 보안이 아님**. URL 직접 호출로 우회. 서버에 검사가 없음 | 서버 측 엔드포인트에서 역할 검증 |
| 6 | "자체 암호화 함수를 만들어 적용했다" | XOR 자작 암호 + **하드코딩 키** + **Base64를 암호화로 오인** — 삼중 결함 | 검증된 표준 알고리즘(AES/GCM) + 키 분리. 자작 암호 금지 |
| 7 | "스택트레이스 노출을 막으려 모든 예외를 감쌌다" | 노출은 막았으나 **예외 삼킴(기록 없음)** 이라는 새 결함 발생 — 조치가 다른 축을 부러뜨림 | 전역 예외 처리: 사용자엔 일반 메시지, 로그엔 상세 기록 |
| 8 | "PreparedStatement로 바인딩했으니 인젝션은 안전하다" | **ORDER BY 동적 컬럼은 바인딩 대상이 아님** → 여전히 인젝션. 도구 사용 ≠ 안전 | 동적 컬럼·정렬 방향은 화이트리스트 대조 후 결합 |

착시 판정의 공통 질문 3가지:
1. **방향이 맞는가** — 블랙리스트/클라이언트 검증/인코딩 착각처럼 접근 자체가 틀리지 않았나?
2. **강도가 충분한가** — 이중 해시처럼 겉만 강화한 것 아닌가?
3. **범위가 완전한가** — pw 필드 누락처럼 일부에만 적용된 것 아닌가? 조치가 새 결함(예외 삼킴)을 만들지 않았나?

반대로 **오탐 판별**도 훈련 대상이다: `Runtime.exec(String[])` 인자 분리 + 셸 미경유라면 명령어 인젝션이 성립하지 않는다(교안 p.10).

## 5. Android 특화 항목 (2011 가이드 원전)

2011 가이드에서 CWE 미부여 3개 항목이 **Android 플랫폼 고유** 보안약점이다(모두 제3절 보안특성). 원리는 지금도 유효하며, 현행 플랫폼에서는 API 변화가 있다.

### 5.1 전역적으로 접근 가능한 파일 (MODE_WORLD_READABLE/WRITABLE)

❌ 취약 (2011 원문)

```java
FileOutputStream fOut = openFileOutput("test", MODE_WORLD_READABLE);
```

✅ 권장

```java
FileOutputStream fOut = openFileOutput("test", MODE_PRIVATE);
```

📋 원문 근거: 2011 가이드 — "파일에 대한 접근권한은 최소한으로 유지되어야 한다", MODE_PRIVATE 권고. 현행 참고: `MODE_WORLD_READABLE/WRITABLE` 은 API 17에서 deprecated, **API 24(Android 7.0)부터 사용 시 SecurityException** (출처: Android developer docs `Context`). 앱 간 데이터 공유는 FileProvider 등 명시적 메커니즘을 사용 — 원문 미기재, 현행 권고.

### 5.2 외부에서 접근하여 활성화 가능한 컴포넌트 (android:exported)

❌ 취약 (2011 원문, AndroidManifest.xml)

```xml
<service android:name=".syncadapter.SyncService" android:exported="true">
    <intent-filter>
        <action android:name="android.content.SyncAdapter"/>
    </intent-filter>
</service>
```

✅ 권장

```xml
<service android:name=".syncadapter.SyncService" android:exported="false">
```

📋 원문 근거: 2011 가이드 — 외부에서 인텐트를 전달해 컴포넌트를 임의 활성화 가능. 동일 인텐트 필터가 여러 개면 리졸버 액티비티가 동작하고, 라우팅된 인텐트는 System 레벨 권한으로 송신자 ID가 바뀌어 전송되어 위험이 커진다. 원문은 "false 설정 또는 속성 제거(제거 시 false)"를 제시했으나, 현행 참고: **Android 12(API 31)부터 intent-filter가 있는 컴포넌트는 `android:exported` 를 명시하지 않으면 설치가 거부**되고, intent-filter가 있으면 기본값이 true로 동작해 왔으므로 "속성 제거 = false"라는 2011년 서술은 현재 그대로 적용하면 안 된다 (출처: Android 12 behavior changes, developer.android.com).

### 5.3 공유 아이디에 의한 접근제어 통과 (android:sharedUserId)

❌ 취약 (2011 원문)

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.android.apis"
    android:sharedUserId="android.uid.developer1">
```

✅ 권장: `android:sharedUserId` 속성을 선언하지 않는다.

📋 원문 근거: 2011 가이드 — 같은 sharedUserId + 같은 서명의 다른 앱이 이 앱의 모든 데이터에 접근 가능하므로 "설정하지 않는 것이 바람직". 현행 참고: `sharedUserId` 는 **API 29에서 deprecated** 되었으며 신규 사용이 금지 방향 (출처: Android developer docs `<manifest>`). 원문 권고와 현행 방향이 일치한다.

### 5.4 Android API가 개입하는 일반 항목 (2011 가이드)

- **절대 경로 조작(CWE-36)**: `Environment.getExternalStorageDirectory()` 로 읽은 외부저장소 파일을 입력원으로 신뢰 — 외부저장소는 신뢰 불가 입력원. 원문 조치는 경로 구분자 검사로 거부. 현행은 §3.2의 `Path.normalize()+startsWith()` 패턴 적용.
- **TOCTOU(CWE-367)**: Activity에서 파일 접근/삭제 스레드 동시 실행 — 검사·사용을 `synchronized` 블록 하나로 묶는다.
- **기밀 정보 평문 전송(CWE-319)**: 평문 `new Socket()` → 원문은 `SSLSocketFactory` 제시. 현행은 TLS 1.2+ (§6).

## 6. ⚠️ 원문의 시대 지연 항목과 현행 대체 권고

2011 가이드는 원전으로서의 가치가 있으나, 아래 항목은 **원문 권고를 그대로 따르면 현재 기준으로 취약**하다.

| 원문(2011) 권고 | 문제점 | 현행 권고 | 출처 |
|---|---|---|---|
| 난수: `Math.random()` 대신 `java.util.Random` + `r.setSeed(new Date().getTime())` | **현재 기준 취약.** Random은 예측 가능한 선형합동 계열이며, 시각 기반 seed는 탐색 가능 | `java.security.SecureRandom` (가능하면 `SecureRandom.getInstanceStrong()`) | 2026 교안 p.35 "보안 목적은 SecureRandom" / Java SE 표준 API |
| 경로 조작: `replaceAll()` 로 위험 문자(`/`, `\`, `.`, `&`) 제거 | 블랙리스트 문자 제거는 우회·부작용(정상 파일명 훼손) 여지 | `java.nio.file.Path` + `normalize()` + `startsWith(base)` 경계 검사 | Java 7+ 표준 API / 2026 교안 p.17 "정규화 후 기준 폴더 경계 확인" |
| 평문 소켓 → `SSLSocketFactory.getDefault()` | SSL이라는 명칭 시대의 API 사용례. 프로토콜 버전·인증서 검증에 대한 언급 없음 | 최신 JSSE 기본 설정 + **TLS 1.2 이상**, 인증서·호스트네임 검증 유지(비활성화 금지). Android는 Network Security Config 병용 | RFC 8996(TLS 1.0/1.1 폐기) / Android developer docs |
| 암호화: `Cipher.getInstance("AES/CBC/PKCS5Padding")` | CBC+패딩은 무결성 미보장(패딩 오라클 계열 위험). 당시로선 DES 대체 권고였음 | `AES/GCM/NoPadding` + 호출마다 고유 IV (AEAD). 국내 제도는 `crypto-policy-kr` 참조 | NIST SP 800-38D |
| 파일 모드: `MODE_PRIVATE` 권고 자체는 유효 | 취약 예시의 `MODE_WORLD_*` 는 이제 API에서 제거 수준(API 24+ SecurityException) | `MODE_PRIVATE` + 앱 간 공유는 FileProvider | Android developer docs |
| 비밀번호/해시: 2011 가이드는 MD5·SHA1을 "취약 알고리즘"으로만 금지(대체 저장 방식 미기재) | 단순 해시 대체만으로는 비밀번호 저장에 불충분 | bcrypt / Argon2id / PBKDF2 + 사용자별 솔트 | OWASP Password Storage Cheat Sheet, NIST SP 800-63B |

### 6.1 2011년 2판에 **없는** 항목 — 과잉 인용 금지

아래 항목은 2011 가이드에 **존재하지 않는다.** "2011 가이드에 따르면…" 식으로 인용하지 말 것:

- **Intent 자체 취약점** (암시적 Intent 노출, Intent Spoofing, PendingIntent) — exported 항목에서 Intent 라우팅 위험을 간접 언급할 뿐
- **권한(permission) 선언·커스텀 퍼미션** (`<uses-permission>`, `protectionLevel`)
- **WebView 취약점** (`addJavascriptInterface`, `setJavaScriptEnabled` 등)
- **로그(Log) 민감정보 출력** — `Log.w(...)` 는 예제 부수 코드로만 등장
- ContentProvider 권한, KeyStore, 루팅 탐지, 난독화

**미기재의 성격 구분** (미기재 ≠ 부적합): 위 부재를 "2011 가이드 위반"의 근거로도, 반대로 "점검 불요"의 근거로도 쓰지 말 것.
- **타 문서 소관**: 암시적 Intent·과도한 권한·루팅 탐지·난독화는 `mobile-app-verify`(2021)의 소스코드 보안약점(모바일 특화)·FV 기준이 담당. 로그 민감정보는 이 스킬 §3.6(2026 교안 근거)이 담당.
- **현행 점검 권장** (구속력 없음): WebView·PendingIntent·KeyStore·ContentProvider 권한은 §6.2의 현행 권고(출처: developer.android.com, OWASP MASVS)로 점검.
- 각 항목이 2011년 당시 `의도적 제외`였는지 `당시 미존재`(관행 미정착)였는지는 원문 미기재 — 확인되지 않는 항목은 **성격 불명**으로 남긴다.

### 6.2 원문 범위 밖 — 현행 Android 필수 점검 (원문 미기재, 현행 권고)

위 미기재 항목 중 현행 Android 진단에서 비중이 큰 것 (각 항목 출처: Android App Security Best Practices — developer.android.com, OWASP MASVS):

- **암시적 Intent로 민감정보 전송 금지** — 명시적 Intent 사용, 브로드캐스트에 권한 지정
- **WebView**: `addJavascriptInterface` 최소화(API 17+ `@JavascriptInterface` 필수), 불필요한 `setJavaScriptEnabled(true)` 지양, SSL 오류 무시(`onReceivedSslError`에서 `proceed()`) 금지
- **권한**: 최소 권한 선언, 커스텀 퍼미션에 `protectionLevel="signature"` 검토
- **logcat 민감정보 금지** — 릴리스 빌드에서 디버그 로그 제거
- 국내 공공 앱이라면 `mobile-app-verify` 스킬의 26개 소스코드 보안약점 + FV 기준을 함께 적용

## 7. Java 진단 체크리스트

**[인젝션 계열]**
- [ ] `Statement`/`executeQuery` 에 문자열 결합 없음 — 전부 PreparedStatement 바인딩
- [ ] PreparedStatement 라도 `ORDER BY`·컬럼명·테이블명 결합 없음 (있으면 화이트리스트 확인)
- [ ] `Runtime.exec` 에 `sh -c` 없음, ProcessBuilder 인자 분리 (인자 분리형이면 오탐 여부 판별)
- [ ] 출력 지점마다 문맥별 인코딩 (입력 필터링을 XSS 조치로 제출하면 반려)

**[파일 계열]**
- [ ] 사용자 입력이 경로에 결합되는 지점: 정규화(`normalize`) + 경계(`startsWith`) 검사 존재
- [ ] 업로드: 확장자 화이트리스트 / 시그니처 검증 / 파일명 재생성 / 웹루트 밖 저장 — 4겹 모두
- [ ] Content-Type 헤더 검사만 있으면 반려

**[인증·인가]**
- [ ] 소스·설정에 하드코딩 자격증명 없음 (git 이력 포함)
- [ ] 비밀번호는 느린 해시 + 솔트 (MD5/SHA-1/단순·이중 SHA-256이면 반려)
- [ ] 로그인 성공 시 세션 재발급, 로그아웃 시 무효화
- [ ] 실패 응답이 계정 존재 여부를 흘리지 않음
- [ ] 자원 접근마다 서버 측 소유권 검증 (IDOR), 기능 접근마다 서버 측 역할 검증
- [ ] `role` 등 권한 필드가 요청 바인딩에 포함되지 않음
- [ ] 클라이언트가 보낸 쿠키·헤더·파라미터 값이 신원·권한 판정에 직접 쓰이지 않음 (쓰이면 기준 15 / CWE-807 정탐)
- [ ] 로그인 실패 횟수 제한·계정 잠금 또는 지연·IP rate limit 존재 (없으면 기준 33 / CWE-307 정탐)
- [ ] 인증·세션 쿠키에 `HttpOnly`·`Secure`·`SameSite` 설정 (§3.3.3)

**[암호화·난수]**
- [ ] MD5·DES·RC4 미사용, 모드 미지정/`ECB` 미사용 — AES/GCM + 고유 IV
- [ ] SHA-1은 **용도 확인 후 판정** — 단순해시·전자서명이면 반려, 메시지인증(HMAC)·키유도·난수생성은 제도상 허용(`crypto-policy-kr` 참조). 신규 설계는 SHA-256 이상
- [ ] 자작 암호·Base64-as-암호화 없음, 키는 소스와 분리
- [ ] 보안 목적 난수는 전부 SecureRandom (`new Random`, `Math.random` 이면 반려)

**[예외·로그]**
- [ ] 보안 검사 catch 블록이 fail-closed (예외 시 `return true` 는 최우선 반려)
- [ ] 빈 catch / 예외 삼킴 없음 — 기록 후 전파 또는 전역 처리
- [ ] 스택트레이스·`e.getMessage()` 가 응답으로 나가지 않음
- [ ] 로그에 비밀번호·토큰·주민번호 없음, 외부 입력은 개행 제거 후 기록

**[Android 추가]**
- [ ] `MODE_WORLD_READABLE/WRITABLE` 없음 → `MODE_PRIVATE`
- [ ] 외부 노출이 불필요한 컴포넌트는 `android:exported="false"` (Android 12+ 명시 필수)
- [ ] `android:sharedUserId` 미사용
- [ ] 외부저장소 입력을 신뢰하지 않음, §6.2 현행 필수 점검 병행

**[조치 검증(승인/반려)]**
- [ ] 제출된 조치가 §4 착시 8종에 해당하지 않는지 — 방향·강도·범위 3축 확인

## 8. 상세 레퍼런스

| 파일 | 내용 |
|---|---|
| `references/java-patterns.md` | 2026 교안 수록 취약 코드 스니펫 전수(실습 A/B/C + 종합 3종)를 ❌/✅/📋 3단 구조로, 장 번호·페이지·진단 포인트 병기 |
| `references/android-java-2011.md` | 2011 Android-JAVA 가이드 2판 7개 유형 17개 항목 전체 표(CWE 병기, 미부여 3개 명시) + 항목별 정의/코딩기법/코드 차이, 시대 지연 항목 ⚠️ 표기 |

검색 목적별 라우팅 — **무엇을 찾을 때 어디로 가는가** (허탕 왕복 방지):

| 찾는 것 | 어디로 |
|---|---|
| 기준번호(1~49)·CWE·공식 보안약점명·원문 페이지 | `secure-coding-kr/references/weakness-49.md` 「총괄표 (49개)」 — **이 SKILL.md §3 기준표의 정본. `java-patterns.md`에는 CWE가 없다** |
| 취약→안전 Java 코드 스니펫 전문 (「제2장 — 입력값 검증과 인젝션」~「제8장 — 종합 진단 3종」) | `references/java-patterns.md` |
| Android 플랫폼 항목·2011 원문 (「1. 17개 항목 전체 목록」·「2. 항목별 상세」) | `references/android-java-2011.md` |
| 암호 알고리즘·키 길이 적합성 판정 | `crypto-policy-kr` 스킬 |
| 오탐 판별 근거 (항목별 원문 페이지) | `secure-coding-kr/SKILL.md` 「8. 오탐(False Positive) 판별」 표 |
