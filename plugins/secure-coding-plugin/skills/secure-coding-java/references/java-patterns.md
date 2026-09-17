# Java 취약→안전 코드 패턴 전수 — 2026 교안 수록 스니펫

> 근거: 「SW 보안약점 진단원 관점의 시큐어코딩 · Java」 교안(2026.09, 47p).
> 교안은 취약 코드를 제시하고 진단 문제를 던지는 형식이므로, ❌ 블록은 **교안 원문 스니펫 그대로**다.
> ✅ 블록은 **현행 모범사례**(출처 병기), 📋 블록은 교안 원문(각 장 체크리스트 처방)과의 대응을 기록한다.
> 수록 스니펫: 실습 A/B/C 18개 + 종합 진단 3개 = **총 21개**.

---

## 제2장 — 입력값 검증과 인젝션

### [2-A] SQL 인젝션 — 문자열 결합 (p.8)

❌ 취약 (원문)

```java
public User findUser(String userId, String pw) {
  String sql = "SELECT * FROM members "
     + "WHERE user_id = '" + userId + "' "
     + "AND password = '" + pw + "'";   // 취약: 문자열 결합
  Statement stmt = conn.createStatement();
  ResultSet rs = stmt.executeQuery(sql);
  return rs.next() ? mapUser(rs) : null;
}
```

✅ 권장 (JDBC 표준 API)

```java
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM members WHERE user_id = ? AND password_hash = ?");
ps.setString(1, userId);
ps.setString(2, passwordHash);
ResultSet rs = ps.executeQuery();
```

📋 원문 근거: p.11 체크리스트 "SQL — 파라미터 바인딩". 진단 문제 원문: "신뢰 경계가 무너지는 라인은? / userId에 무엇을 넣으면 우회되나? / 인젝션 외 추가 지적 2가지는?" (비밀번호 평문 비교·평문 저장도 함께 지적 대상).

**진단 포인트**: `createStatement()` + `executeQuery(변수)`, SQL 문자열의 `+` 결합. 비밀번호가 SQL 조건에 평문으로 등장하는 것 자체도 4장 위반.

---

### [2-B] 착시 조치 — 블랙리스트 필터링 (p.9)

❌ 취약 (원문) — "위험 문자를 필터링했습니다"라는 회신

```java
private String sanitize(String in) {
  return in.replace("'", "")
     .replace(";", "")
     .replace("--", "")
     .replaceAll("(?i)SELECT|UNION", ""); // 취약: 블랙리스트
}
// pw 필드는 sanitize를 거치지 않음
```

✅ 권장: 필터링이 아니라 **구조 분리** — [2-A]의 PreparedStatement 바인딩. 블랙리스트 sanitize 함수는 제거한다.

📋 원문 근거: p.7 "블랙리스트는 하수 — 우회 가능 → 근본은 데이터·명령 분리". **반려 사유 2축**: ① 블랙리스트는 우회 가능(예: `SELESELECTCT` 재조합, 인코딩) ② **pw 필드 적용 누락** — 조치의 범위까지 검증해야 한다.

**진단 포인트**: `replace`/`replaceAll` 로 SQL 키워드·특수문자를 지우는 함수. 그 함수가 **모든 입력 경로에 적용됐는지**도 확인.

---

### [2-C1] 명령어 인젝션 — sh -c (p.10)

❌ 취약 (원문)

```java
String cmd = "/usr/bin/convert " + filename + " out.png";
Runtime.getRuntime().exec(new String[]{"sh","-c",cmd}); // 취약
```

✅ 권장 (Java 표준 API)

```java
Process p = new ProcessBuilder("/usr/bin/convert", filename, "out.png").start();
```

📋 원문 근거: p.11 "OS 명령 — 셸(sh -c) 미사용, ProcessBuilder로 인자 분리". **오탐 판별 훈련**: p.10 "셸 없이 exec면 통했을까?" — `exec(String[])` 인자 분리 + 셸 미경유라면 명령어 인젝션이 성립하지 않는다(과잉 지적 금지).

**진단 포인트**: `Runtime.getRuntime().exec(` 인자에 `"sh"`, `"-c"`, `"cmd.exe"`, `"/c"`, 또는 문자열 결합.

---

### [2-C2] 반사형 XSS — 미인코딩 출력 (p.10)

❌ 취약 (원문)

```java
String q = request.getParameter("q");
out.println("<div>검색어: " + q + "</div>");
// 취약: 미인코딩
```

✅ 권장: 출력 위치(HTML body / attribute / JavaScript / URL)에 맞는 **문맥별 출력 인코딩** 적용 후 출력. (출처: OWASP XSS Prevention Cheat Sheet — 인코딩 라이브러리 선택은 프로젝트 표준을 따름)

📋 원문 근거: p.11 "XSS — 출력 위치에 맞는 인코딩 (입력 필터링 아님)". 교안은 ESAPI·OWASP Encoder 등 구체 라이브러리를 언급하지 않는다(원칙 수준만). p.10 "XSS는 왜 '남의 문제'가 되나?" — 피해자가 서버가 아니라 **다른 사용자**라는 점.

**진단 포인트**: `out.println(` / JSP 표현식 / 응답 작성부에 `getParameter` 값이 인코딩 없이 삽입.

---

## 제3장 — 파일 업로드와 경로 조작

### [3-A] 경로 조작 — 미검증 결합 (p.14)

❌ 취약 (원문)

```java
String basePath = "/app/data/files/";
File target = new File(basePath + filename); // 취약: 미검증 결합
resp.setHeader("Content-Disposition",
   "attachment; filename=" + filename);
fis.transferTo(resp.getOutputStream());
```

✅ 권장 (Java 7+ java.nio.file 표준 API)

```java
Path base = Paths.get("/app/data/files").toRealPath();
Path target = base.resolve(filename).normalize();
if (!target.startsWith(base)) {
  throw new SecurityException("경로 이탈 시도");
}
```

📋 원문 근거: p.17 "경로 조작 — 정규화 후 기준 폴더 경계 확인". `Path.normalize()+startsWith()` 구현 코드는 원문 미기재 — 처방을 표준 API로 옮긴 것. p.14 진단 문제의 "'확인 필요'한 점은?" — 단정 대신 추가 확인(filename의 출처·검증 존재 여부)을 구분하는 훈련. `Content-Disposition` 헤더에 미검증 filename이 들어가는 점(헤더 인젝션 여지)도 확인 대상.

**진단 포인트**: `new File(상수 + 변수)`, `../` 시퀀스 필터의 우회(인코딩·중첩) 가능성.

---

### [3-B] 착시 조치 — 확장자 블랙리스트 + 웹루트 저장 (p.15)

❌ 취약 (원문) — ".jsp/.php/.exe 차단 + 클라이언트 재검사" 회신

```java
List<String> DENY = List.of(".jsp",".php",".exe");
String lower = name.toLowerCase();
for (String bad : DENY)
  if (lower.endsWith(bad)) throw new Exception(); // 취약: 블랙리스트
File dest = new File("/app/webroot/upload/"+name); // 취약: 웹루트
file.transferTo(dest);
```

✅ 권장: ① 확장자 **화이트리스트**(허용 확장자만) ② 서버 측 시그니처(매직 바이트) 검증 ③ 서버에서 파일명 재생성(UUID) ④ **웹루트 밖** 실행 불가 저장소. 클라이언트 검사는 UX용일 뿐 보안 조치가 아니다.

📋 원문 근거: p.17 체크리스트 4행(종류/이름/위치 + 실행 차단). **반려 사유**: 블랙리스트 우회(`.jspx`, `.JSP`, 이중 확장자 등) + 저장 위치가 여전히 웹루트 + 클라이언트 재검사 무의미.

**진단 포인트**: `endsWith` 기반 거부 목록, 저장 경로의 `webroot`/`www` 문자열, `transferTo(` 대상 디렉터리.

---

### [3-C] 업로드 → 웹셸 — Content-Type 신뢰 (p.16)

❌ 취약 (원문)

```java
if (!file.getContentType().startsWith("image/"))
  throw new Exception();          // 취약: 헤더는 위조 가능
File dest = new File("/app/webroot/avatars/"+name);
file.transferTo(dest);            // 취약: 웹 실행 경로
return "/avatars/" + name;
```

✅ 권장: [3-B] ✅와 동일한 4겹 방어. Content-Type 헤더는 클라이언트가 임의 지정 가능하므로 판정 근거로 쓰지 않는다.

📋 원문 근거: p.13 "웹셸 = 실행되는 파일을 실행되는 위치에 올림 → 서버 장악". p.16 진단 문제 "Content-Type 검사로 충분한가? / 서버 장악까지 단계는?"

**진단 포인트**: `getContentType()` 이 유일한 검증이면 반려. 반환 URL이 업로드 파일을 웹 경로로 직접 노출하는지 확인.

---

## 제4장 — 계정 및 인증 관리

### [4-A] 하드코딩 자격증명 · 약한 해시 (p.20)

❌ 취약 (원문)

```java
private static final String ADMIN_PW = "P@ssw0rd2020"; // 취약
private static final String API_KEY  = "sk_live_9f83.."; // 취약
public boolean login(String id, String pw) {
  String stored = userDao.findPasswordHash(id); // MD5
  return md5(pw).equals(stored);   // 취약: 약한 해시·솔트 없음
}
```

✅ 권장: 자격증명은 소스·설정에서 분리(환경변수/비밀 관리 시스템). 비밀번호 검증은 **bcrypt / Argon2id / PBKDF2WithHmacSHA256** 등 솔트+스트레칭 내장 해시 라이브러리의 verify 함수 사용. (출처: OWASP Password Storage Cheat Sheet, NIST SP 800-63B)

📋 원문 근거: p.23 "느린 해시(bcrypt/Argon2)+사용자별 솔트 / 소스·설정에 비밀정보 부재(git 노출 확인)". p.19 "하드코딩 = 비밀번호 포스트잇 — .properties도 git 올라가면 마찬가지".

**진단 포인트**: `static final String` 비밀 리터럴, `md5(`/`"MD5"` 가 비밀번호 경로에 존재, `.properties`·git 이력 노출.

---

### [4-B] 착시 조치 — 이중 SHA-256 (p.21)

❌ 취약 (원문) — "SHA-256을 두 번 적용했습니다" 회신

```java
public String hashPassword(String pw) {
  return sha256(sha256(pw));   // 취약: 강화가 아니라 착시
}
```

✅ 권장: [4-A] ✅와 동일 — 느린 해시 + 사용자별 솔트. 빠른 해시는 몇 번을 겹쳐도 빠르다.

📋 원문 근거: p.21 "강화가 아니라 착시". **반려 사유**: 솔트 부재(레인보우 테이블·동일 비밀번호 식별 가능) + 스트레칭 부재(GPU 대량 대입에 무력).

**진단 포인트**: `sha256(sha256(`, 해시 함수 중첩 호출, 솔트 파라미터 부재.

---

### [4-C1] 세션 고정 (p.22)

❌ 취약 (원문)

```java
if (login(id, pw)) {
  HttpSession s = req.getSession(); // 취약: 기존 세션 재사용
  s.setAttribute("user", id);
}
```

✅ 권장 (Servlet 3.1+ 표준 API)

```java
if (login(id, pw)) {
  req.changeSessionId();               // 로그인 성공 시 세션 ID 재발급
  req.getSession().setAttribute("user", id);
}
// 또는: 기존 세션 invalidate() 후 getSession(true)로 신규 발급
```

📋 원문 근거: p.23 "세션 — 로그인 후 재발급, 로그아웃 시 무효화". p.19 비유: "놀이공원 팔찌 / 세션 고정 = 로그인 후 팔찌 교체로 방어". `changeSessionId()` 메서드명은 원문 미기재 — Servlet 3.1 표준으로 구체화.

**진단 포인트**: 로그인 성공 분기에 세션 재발급 호출 부재, 로그아웃 처리에 `invalidate()` 부재.

---

### [4-C2] 계정 열거 (p.22)

❌ 취약 (원문)

```java
if (u == null) return error("존재하지 않는 아이디"); // 취약
if (!verify(pw)) return error("비밀번호 불일치");   // 취약
```

✅ 권장

```java
if (u == null || !verify(pw)) {
  return error("아이디 또는 비밀번호가 올바르지 않습니다"); // 단일 메시지
}
```

📋 원문 근거: p.23 "정보 노출 — 실패 응답이 사용자 존재 여부를 흘리지 않음".

**진단 포인트**: 실패 메시지가 2종류로 갈리는 분기. 응답 시간 차이도 부수 확인 대상.

---

## 제5장 — 접근통제 및 인가

### [5-A] IDOR — 소유권 미검증 (p.26)

❌ 취약 (원문)

```java
@GetMapping("/orders/{orderId}")
public OrderDto getOrder(@PathVariable Long orderId) {
  Order o = orderRepository.findById(orderId).orElseThrow();
  return toDto(o);   // 취약: 소유권(인가) 검사 없음
}
```

✅ 권장

```java
@GetMapping("/orders/{orderId}")
public OrderDto getOrder(@PathVariable Long orderId, Principal principal) {
  Order o = orderRepository.findByIdAndOwnerId(orderId, currentUserId(principal))
      .orElseThrow(NotFoundException::new);   // 소유권을 질의 조건에 포함
  return toDto(o);
}
```

📋 원문 근거: p.29 "수평(IDOR) — 자원 접근 시 소유권을 서버에서 검증". p.26 진단 문제 "인증됐는데 뭐가 문제? / A는 어떻게 B의 주문을? / 수평/수직?" — 인증 통과 ≠ 인가 통과.

**진단 포인트**: `findById(경로변수)` 직후 로그인 주체와의 대조 없이 반환.

---

### [5-B] 착시 조치 — UI 숨김 + JS 권한 체크 (p.27)

❌ 취약 (원문) — "관리자 메뉴 숨김 + 자바스크립트 권한 체크" 회신, 서버엔 검사 없음

```jsp
<c:if test="${user.role=='ADMIN'}">
  <a href="/admin/users">회원 관리</a>   <!-- 버튼만 숨김 -->
</c:if>
```

```java
@GetMapping("/admin/users")
public String adminUsers(Model m){        // 취약: 권한 검사 없음
  m.addAttribute("users", userService.findAll()); return "admin"; }
```

✅ 권장: 서버 측 엔드포인트에서 역할 검증(관리자 URL 전체에 서버 측 인가 필터/검사 적용). UI 숨김은 UX일 뿐 보안 통제가 아니다.

📋 원문 근거: p.25 "숨김 ≠ 통제 — UI 숨김·클라이언트 검증은 보안 아님 → 서버에서만". **반려 사유**: 일반 사용자가 `/admin/users` 를 직접 호출하면 그대로 통과. 특정 프레임워크 어노테이션은 원문 미기재.

**진단 포인트**: 권한 분기가 뷰(JSP/JS)에만 존재하고 컨트롤러/필터에 없음.

---

### [5-C] 수직 권한 상승 — Mass Assignment (p.28)

❌ 취약 (원문)

```java
public String updateUser(UserForm form, HttpSession s){
  User u = repo.findById(loginId).orElseThrow();
  u.setName(form.getName());
  u.setEmail(form.getEmail());
  u.setRole(form.getRole());   // 취약: 폼 값으로 역할 설정
  repo.save(u); }
```

✅ 권장: 수정 가능 필드(name, email)만 담은 DTO로 바인딩 범위를 제한하고, `role` 은 요청에서 절대 받지 않는다. 역할 변경은 별도의 관리자 전용 기능 + 서버 측 인가로만.

📋 원문 근거: p.29 "민감 필드 — role 등 권한 필드를 입력으로 받지 않음". p.28 진단 문제 "일반 사용자가 뭘 할 수 있나?" — 본문에 `role=ADMIN` 을 실어 보내면 수직 상승.

**진단 포인트**: 요청 폼/DTO에 `role`·`admin`·권한 관련 세터가 존재하고 저장 경로로 흐름.

---

## 제6장 — 암호화 및 민감정보 보호

### [6-A] 민감정보 저장 — MD5 주민번호 · 평문 전화번호 (p.32)

❌ 취약 (원문)

```java
String encSsn = md5(ssn);   // 취약: 주민번호를 MD5(일방향)로
member.setSsn(encSsn);
member.setPhone(phone);     // 취약: 전화번호 평문
memberDao.save(member);
```

✅ 권장: 주민번호는 **복호화가 필요한 데이터** → 해시가 아니라 양방향 암호화 — `AES/GCM/NoPadding` + 고유 IV, 키는 소스와 분리(KMS/키스토어). (출처: NIST SP 800-38D. 국내 제도·검증필 암호모듈은 `crypto-policy-kr` 스킬 참조.) 전화번호 등 개인정보도 정책에 따라 암호화 저장.

📋 원문 근거: p.31 "되돌릴 필요 없다=해시 / 되돌려야 한다=양방향 암호화", "고유식별정보(주민·여권·운전면허·외국인등록번호)는 무조건 암호화". p.35 "MD5·SHA-1·DES 금지". 문제 2가지: ① MD5는 깨진 해시 ② 애초에 해시를 쓰면 업무상 필요한 복원이 불가 — 대상 구분 오류.

**진단 포인트**: `md5(`/`sha*(` 가 고유식별정보에 적용, 개인정보 필드의 평문 `save`.

---

### [6-B] 착시 조치 — 자체 XOR 암호화 + Base64 (p.33)

❌ 취약 (원문) — "자체 암호화 함수를 만들어 적용했습니다" 회신

```java
private static final String KEY="mySecretKey123"; // 취약: 하드코딩 키
public String encrypt(String plain){
  StringBuilder sb=new StringBuilder();
  for (int i=0;i<plain.length();i++)
    sb.append((char)(plain.charAt(i)^KEY.charAt(i%KEY.length())));
  return Base64.getEncoder()          // 취약: 인코딩≠암호화
    .encodeToString(sb.toString().getBytes()); }
```

✅ 권장: 자작 암호 전면 폐기 → 검증된 표준 `AES/GCM/NoPadding` + 고유 IV + 키 분리. (출처: NIST SP 800-38D)

📋 원문 근거: p.31 "Base64는 암호화 아님 — 열쇠 없이 누구나 복원, 인코딩일 뿐". **반려 사유 3축**: ① XOR 자작 암호 ② 하드코딩 키 ③ Base64를 암호화로 오인.

**진단 포인트**: `encrypt`라는 이름의 자작 메서드, `^`(XOR) 루프, `Base64.getEncoder()` 가 "암호화" 경로의 마지막 단계.

---

### [6-C] 약한 난수 — 재설정 토큰에 Random (p.34)

❌ 취약 (원문)

```java
public String createResetToken(String userId){
  Random rnd = new Random();      // 취약: 예측 가능한 난수
  long token = rnd.nextLong();
  resetTokenDao.save(userId, token);
  return Long.toString(token); }
```

✅ 권장 (Java SE 표준 API)

```java
SecureRandom sr = SecureRandom.getInstanceStrong(); // 또는 new SecureRandom()
byte[] buf = new byte[32];
sr.nextBytes(buf);
String token = Base64.getUrlEncoder().withoutPadding().encodeToString(buf);
```

📋 원문 근거: p.31 "토큰·키·세션ID는 SecureRandom", p.35 "보안 목적은 SecureRandom". `java.util.Random` 은 내부 상태가 예측 가능 — 공격자가 토큰을 예측해 임의 계정의 비밀번호 재설정 링크를 탈취할 수 있다. (2011 가이드는 `Random`+시각 seed를 권고했으나 현재 기준 취약 — `android-java-2011.md` ⚠️ 참조.)

**진단 포인트**: `new Random(`, `Math.random()` 이 토큰/키/세션ID/OTP 생성 경로에 존재.

---

## 제7장 — 예외 처리 및 로그 보안

### [7-A] fail-open — 예외 시 통과 (p.38)

❌ 취약 (원문)

```java
public boolean hasPermission(String user, String orderId){
  try {
    return permissionService.check(user, orderId).isAllowed();
  } catch (Exception e) {
    System.out.println("오류: " + e);
    return true;    // 취약: 예외 시 통과 (fail-open)
  } }
```

✅ 권장

```java
  } catch (Exception e) {
    log.error("권한 확인 실패: user={}, orderId={}", user, orderId, e);
    return false;   // fail-closed: 확신이 없으면 거부
  }
```

📋 원문 근거: p.37 "확신이 없으면 막아라 — 보안은 fail-closed", "**정상 테스트로는 절대 안 걸린다**" — 권한 서비스가 죽는 순간 전원 통과가 되는 결함. p.41 "보안 검사 예외 시 fail-closed(거부)".

**진단 포인트**: 보안 검사 메서드의 `catch` 에서 `return true` / 통과 값 반환.

---

### [7-B] 착시 조치 — 예외 삼킴 (p.39)

❌ 취약 (원문) — "스택트레이스 노출을 막으려고 모든 예외를 감쌌습니다" 회신

```java
public Report generate(String userId){
  try {
    return build(load(userId));
  } catch (Exception e) {
    return null;    // 취약: 예외 삼킴 (기록 없음)
  } }
```

✅ 권장: 예외를 기록하고 전파(또는 도메인 예외로 변환) → 전역 예외 처리기에서 사용자에겐 일반 메시지, 로그엔 상세 기록.

📋 원문 근거: p.41 "예외를 기록·전파, 삼키지 않음 / 사용자엔 일반 메시지, 로그엔 상세(전역 예외 처리)". **반려 사유**: 노출은 막았으나 ① 장애 원인 추적 불가(기록 없음) ② 호출부에 null 전파로 2차 결함(NPE·오동작) — 조치가 새 결함을 만든 사례.

**진단 포인트**: `catch (Exception e) { return null; }`, 빈 catch 블록, 광역 `catch(Exception)` 로 전 예외 무음 처리.

---

### [7-C] 민감정보 로깅 · 로그 인젝션 (p.40)

❌ 취약 (원문)

```java
log.info("로그인: id="+id+", pw="+pw           // 취약: 비번 로깅
  +", token="+token+", 주민번호="+ssn);         // 취약: 민감정보

String userId = req.getParameter("userId");
log.info("조회 요청: " + userId);   // 취약: 로그 인젝션
```

✅ 권장: 비밀번호·토큰·주민번호는 로그에서 제외(필요 시 마스킹). 외부 입력은 개행 문자(`\r`, `\n`) 제거·인코딩 후 기록 — 위조 로그 라인 삽입(로그 인젝션) 차단. (원문 미기재 세부 — 현행 권고: OWASP Log Injection)

📋 원문 근거: p.37 "로그 3축 — 남길 것(사건)·뺄 것(민감정보)·누가 보나(알림)", p.41 "보안 사건 기록 / 민감정보 제외 / 이상 징후 알림".

**진단 포인트**: `log.` 인자에 `pw`/`password`/`token`/`ssn` 변수, 외부 입력의 무가공 로깅.

---

## 제8장 — 종합 진단 3종

### [8-1] 몸풀기 — 댓글 검색 (p.44)

❌ 취약 (원문)

```java
public List<Comment> search(String keyword){
  String sql = "SELECT * FROM comments "
    + "WHERE content LIKE '%"+keyword+"%'"; // 취약: SQLi
  Statement st = conn.createStatement();
  ResultSet rs = st.executeQuery(sql);
  return mapComments(rs); }
```

✅ 권장: `LIKE ?` 바인딩 — `ps.setString(1, "%" + keyword + "%")`. 검색 결과를 화면에 출력한다면 출력 인코딩(XSS)도 병행.

📋 원문 근거: 진단 문제 "보안약점을 모두 찾으면? / 가장 시급한 것은?" — 가장 시급한 것은 SQLi.

---

### [8-2] 본 진단 — 프로필 수정 (a)~(e) (p.45)

❌ 취약 (원문)

```java
private static final String DB_PW="admin1234";       // (a)
String sql="UPDATE users SET avatar='"+avatar         // (b)
  +"' WHERE id='"+userId+"'"; stmt.executeUpdate(sql);
File f=new File("/webroot/img/"+avatar); saveUpload(f); // (c)
log.info("수정: "+userId+" pw="+DB_PW);               // (d)
catch(Exception e){ resp.getWriter().write("오류:"+e); }// (e)
```

취약점–교시 매핑 (교안 구조상):

| 지점 | 취약점 | 교시 | ✅ 대응 |
|---|---|---|---|
| (a) | 하드코딩 자격증명 | 4강 | 비밀 분리 (환경변수/비밀 관리) |
| (b) | SQL 인젝션 | 2강 | PreparedStatement 바인딩 |
| (c) | 웹루트 업로드/경로 조작 | 3강 | 웹루트 밖 + 정규화·경계 검사 + 파일명 재생성 |
| (d) | 민감정보 로깅 | 7강 | 로그에서 비밀 제외 |
| (e) | 예외 정보 노출 | 7강 | 전역 예외 처리, 응답엔 일반 메시지 |

---

### [8-3] 심화 — PreparedStatement 착시 (p.46)

❌ 취약 (원문) — "PreparedStatement로 바인딩했으니 인젝션은 안전합니다" 회신

```java
String sql = "SELECT ... FROM orders "
  + "WHERE user_id = ? "
  + "ORDER BY " + sortColumn + " " + dir;  // (a) 취약
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, userId);                       // (b)
```

✅ 권장

```java
// 정렬 컬럼·방향은 바인딩 불가 → 허용 목록과 대조 후에만 결합
Set<String> ALLOWED_COLS = Set.of("created_at", "amount", "status");
Set<String> ALLOWED_DIR  = Set.of("ASC", "DESC");
if (!ALLOWED_COLS.contains(sortColumn) || !ALLOWED_DIR.contains(dir)) {
  throw new IllegalArgumentException("허용되지 않은 정렬 조건");
}
String sql = "SELECT ... FROM orders WHERE user_id = ? ORDER BY "
  + sortColumn + " " + dir;   // 화이트리스트 통과 값만 결합
```

📋 원문 근거: p.11 "동적 컬럼·정렬은 화이트리스트" — 교안 전체에서 **오탐/미탐 판별력**을 가장 직접적으로 묻는 지점. "PreparedStatement 사용 = 안전"이라는 도구 기반 판정이 ORDER BY 동적 컬럼에서 무너진다. 인젝션 외 문제: user_id 바인딩만으로 소유권 검증(5강)이 됐는지도 별도 확인.

**진단 포인트**: `prepareStatement` 호출부의 SQL 문자열에 남아 있는 `+` 결합 — 특히 `ORDER BY`, `LIMIT`, 컬럼·테이블명.
