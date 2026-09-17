# 「Android-JAVA 시큐어 코딩 가이드(2판)」 전 항목 레퍼런스 — 2011, 행안부/KISA

> 근거: 행정안전부 「소프트웨어 개발보안 가이드」 붙임3, 2011.09 (V1.1, 42페이지).
> **7개 유형(절) · 총 17개 보안약점 항목.** 모든 항목은 `가. 정의 → 나. 안전한 코딩기법 → 다. 예제(안전하지 않은/안전한 코드) → 라. 참고 문헌` 4단 구조.
>
> ⚠️ **시점 주의**: 2011년 문서다. ⚠️ 표기 항목은 원문 권고를 그대로 따르면 **현재 기준으로 취약하거나 부적절**하다 —
> 각 항목의 `📋/현행` 설명과 SKILL.md §6 「원문의 시대 지연 항목과 현행 대체 권고」를 반드시 병행 참조하라.

## 1. 17개 항목 전체 목록

| # | 유형 | 항목명 | CWE | 위험도 | 비고 |
|---|---|---|---|---|---|
| 1 | 입력 데이터 검증 및 표현 | 상대 디렉터리 경로 조작 | CWE-23 | 매우높음 | ⚠️ 조치 방식 구식 |
| 2 | 입력 데이터 검증 및 표현 | 절대 디렉터리 경로 조작 | CWE-36 | 매우높음 | ⚠️ 조치 방식 구식 |
| 3 | API 악용 | null 매개변수 미검사 | CWE-398 | 높음 | |
| 4 | API 악용 | equals()와 hashCode() 하나만 정의 | CWE-581 | 높음 | |
| 5 | 보안특성 | 기밀 정보의 단순한 텍스트 전송 | CWE-319 | 높음 | ⚠️ SSL 시대 API |
| 6 | 보안특성 | 취약한 암호화 알고리즘의 사용 | CWE-327 | 높음 | ⚠️ CBC 권고 |
| 7 | 보안특성 | 적절하지 않은 난수값의 사용 | CWE-330 | 높음 | ⚠️⚠️ **원문 권고 자체가 현재 취약** |
| 8 | 보안특성 | 전역적으로 접근가능한 파일 | **CWE 미부여** | 높음 | Android 특화 |
| 9 | 보안특성 | 외부에서 접근하여 활성화 가능한 컴포넌트 | **CWE 미부여** | 높음 | Android 특화 · 2판 개정 항목 |
| 10 | 보안특성 | 공유 아이디에 의한 접근제어 통과 | **CWE 미부여** | 높음 | Android 특화 |
| 11 | 시간 및 상태 | 경쟁 조건: 검사시점과 사용시점(TOCTOU) | CWE-367 | 높음 | |
| 12 | 시간 및 상태 | 제대로 제어되지 않은 재귀 | CWE-674 | 높음 | |
| 13 | 에러 처리 | 오류 메시지 통한 정보 노출 | CWE-209 | 높음 | |
| 14 | 에러 처리 | 오류 상황에 대한 처리 부재 | CWE-390 | 높음 | |
| 15 | 코드 품질 | 널포인터 역참조 | CWE-476 | 높음 | |
| 16 | 캡슐화 | 공용 메소드로부터 리턴된 private 배열-유형 필드 | CWE-495 | 높음 | |
| 17 | 캡슐화 | private 배열-유형 필드에 공용 데이터 할당 | CWE-496 | 높음 | |
| — | 캡슐화 | 시스템 데이터 정보 누출 | CWE-497 | 높음 | 위 표의 17번째 항목과 함께 캡슐화 3종 구성 |

> 정오: 원문 <표 1> 기준 캡슐화는 CWE-495 / CWE-496 / CWE-497 **3개 항목**이며, 위 표는 통번호 부여를 위해 마지막 행을 분리 표기했다(총 17개).
> **CWE 미부여 3개 항목(8·9·10)이 Android OS 플랫폼 고유의 취약점**으로, 일반 Java 가이드에는 없는 이 가이드만의 추가 항목이다.

절별 항목 수: 입력 데이터 검증 및 표현 2 / API 악용 2 / 보안특성 6 / 시간 및 상태 2 / 에러 처리 2 / 코드 품질 1 / 캡슐화 3.

---

## 2. 항목별 상세

### 2.1 상대 디렉터리 경로 조작 (CWE-23) ⚠️

- **정의(원문)**: 외부의 입력을 통하여 "디렉터리 경로 문자열" 생성이 필요한 경우, 외부 입력에서 경로 조작에 사용될 수 있는 문자를 필터링하지 않으면, 예상 밖의 영역에 대한 경로 문자열이 가능해져 시스템 정보누출, 서비스 장애 등을 유발.
- **안전한 코딩기법(원문)**: 외부 입력이 직접 파일이름 생성에 사용될 수 없도록 한다. 불가피한 경우 `replaceAll()` 등으로 위험 문자열(`/`, `\` 등)을 제거하는 필터를 거친다.
- **코드 차이(원문)**: `new File("/usr/local/tmp/" + name)` 직접 결합 → `name.replaceAll("/","")`, `replaceAll("\\","")`, `.`·`&` 제거 + null/빈문자열 검사 + 기준 디렉터리 상수 분리 + 접미사(`-report`) 부여 후 사용.
- ⚠️ **현행**: 문자 제거(블랙리스트) 방식은 우회·정상 파일명 훼손 여지가 있다. 현행 표준은 `java.nio.file.Path` + `normalize()` + `startsWith(base)` 경계 검사 (Java 7+ 표준 API; 2026 교안 p.17 "정규화 후 기준 폴더 경계 확인"과 일치).
- **보고 표기**: 진단 보고서에는 2021 진단가이드 기준 3 「경로 조작 및 자원 삽입」(CWE-99, CWE-22)으로 기재하고, CWE-23/36은 2011 원문 참고 표기로만 병기한다 (2.2 절대 디렉터리 경로 조작 동일).
- 참고 문헌(원문): CWE-23 · OWASP Top 10 2010 A4 · SANS Top 25 2010 Rank 7 (CWE-22).

### 2.2 절대 디렉터리 경로 조작 (CWE-36) ⚠️

- **정의(원문)**: 외부 입력이 파일 시스템을 조작하는 경로를 직접 제어하면, 공격자가 치명적인 시스템 파일·일반 파일을 접근·변경·실행할 수 있다.
- **안전한 코딩기법(원문)**: `replaceAll` 로 위험 문자 제거 또는 **절대경로 문자열 포함여부 검사**.
- **코드 차이(원문)**: 외부저장소(`Environment.getExternalStorageDirectory()`)에서 읽은 `filename` 을 그대로 `new File("/usr/local/tmp/" + name)` → `if (name.indexOf("/") < 0)` 일 때만 파일 조작 수행(경로 구분자 포함 시 거부).
- Android 맥락: **외부저장소(SD카드)는 신뢰할 수 없는 입력원**이라는 관점이 이 예제의 핵심. 예외를 `Log.w("Error", "", e)` 로 logcat에 기록하는 형태도 등장.
- ⚠️ **현행**: 2.1과 동일 — `Path.normalize()+startsWith()` 로 대체.

### 2.3 null 매개변수 미검사 (CWE-398)

- **정의(원문)**: Java 표준에 따르면 `Object.equals()`, `Comparable.compareTo()`, `Comparator.compare()` 구현은 매개변수가 null인 경우 지정된 값을 반환해야 한다. 이 약속을 따르지 않으면 예기치 못한 동작이 발생.
- **안전한 코딩기법(원문)**: 위 세 메서드 구현에서 매개변수를 null과 비교해야 한다.
- **코드 차이(원문)**:

```java
// ❌ return (toString().equals(object.toString()));
// ✅
public boolean equals(Object object) {
    if(object != null)
       return (toString().equals(object.toString()));
    else return false ;
}
```

### 2.4 equals()와 hashCode() 하나만 정의 (CWE-581)

- **정의(원문)**: `a.equals(b) == true` 이면 `a.hashCode() == b.hashCode()` 이어야 한다. 한 클래스에서 equals()와 hashCode()는 둘 다 구현하거나 둘 다 구현하지 않아야 한다.
- **코드 차이(원문)**: equals()만 정의 → hashCode()를 함께 정의. 원문 예제는 `new HashCodeBuilder(17, 37).toHashCode()` (Apache Commons Lang) 사용.
- 현행 참고: `java.util.Objects.hash(...)` 등 표준 API로도 동일 계약 충족 가능 (Java 7+ 표준 API — 원문 미기재).

### 2.5 기밀 정보의 단순한 텍스트 전송 (CWE-319) ⚠️

- **정의(원문)**: 민감 데이터를 평문 형태로 통신 채널을 통해 보내면 스니핑될 수 있다.
- **안전한 코딩기법(원문)**: 민감 정보 전송 시 반드시 암호화 과정을 거친다. "최소한 128비트 길이의 키" 권고.
- **코드 차이(원문)**:

```java
// ❌ Socket socket = new Socket(hostname, port);          // 평문 소켓
// ✅ (2011 원문)
SocketFactory socketFactory = SSLSocketFactory.getDefault();
Socket socket = socketFactory.createSocket(hostname, port);
```

- ⚠️ **현행**: SSL 명칭 시대의 예시로, 프로토콜 버전·인증서/호스트네임 검증 언급이 없다. 현행은 최신 JSSE 기본 설정 + **TLS 1.2 이상**(TLS 1.0/1.1은 RFC 8996으로 폐기), 인증서·호스트네임 검증 유지. Android는 기본 평문 통신 차단(API 28+ cleartext 기본 금지) 및 Network Security Config 병용 (출처: Android developer docs).
- 참고 문헌(원문): CWE-319 · OWASP Top 10 2007 A9.

### 2.6 취약한 암호화 알고리즘의 사용 (CWE-327) ⚠️

- **정의(원문)**: 취약·위험한 암호화 알고리즘 사용 금지. **"RC2, RC4, RC5, RC6, MD4, MD5, SHA1, DES 알고리즘이 여기에 해당된다."**
- **안전한 코딩기법(원문)**: AES처럼 보다 강력한 알고리즘 사용.
- **코드 차이(원문)**:

```java
// ❌ Cipher c = Cipher.getInstance("DES");
// ✅ (2011 원문)
Cipher c = Cipher.getInstance("AES/CBC/PKCS5Padding");   // 최소 128비트 키
```

- ⚠️ **현행**: 금지 목록(RC계열·MD4/5·SHA1·DES)은 지금도 유효하나, **CBC+패딩 권고는 시대 지연** — 무결성 미보장(패딩 오라클 계열 위험). 현행은 `AES/GCM/NoPadding` + 호출마다 고유 IV (출처: NIST SP 800-38D). 국내 제도 대응(SEED/ARIA/LEA, 검증필 암호모듈)은 `crypto-policy-kr` 스킬 참조.
- 참고 문헌(원문): CWE-327 · OWASP Top 10 2010 A7 · SANS Top 25 2010 (CWE-327) · Bruce Schneier, "Applied Cryptography" (1996).

### 2.7 적절하지 않은 난수값의 사용 (CWE-330) ⚠️⚠️ — **원문 권고 자체가 현재 기준 취약**

- **정의(원문)**: 예측 가능한 난수 사용은 시스템에 취약점을 야기한다. 공격자는 다음 숫자를 예상하여 공격 가능.
- **안전한 코딩기법(원문)**: 난수발생기에서 seed를 사용하는 경우 예측하기 어려운 방법으로 변경하여 사용.
- **원문 코드 (2011년 권고 — 그대로 인용)**:

```java
// ❌ (원문의 '안전하지 않은 코드')
public double roledice() {
    return Math.random();   // 원문 사유: seed를 재설정할 수 없기 때문에 위험
}

// (원문의 '안전한 코드' — ⚠️ 현재 기준으로는 이것도 취약)
import java.util.Random;
import java.util.Date;
public int roledice() {
    Random r = new Random();
    r.setSeed(new Date().getTime());   // 시각 기반 seed
    return (r.nextInt()%6) + 1;
}
```

- ⚠️ **2011년 원문 권고. 현재는 `java.security.SecureRandom` 을 사용할 것.**
  - `java.util.Random` 은 선형합동 계열로 출력에서 내부 상태 복원이 가능하고, `new Date().getTime()` seed는 밀리초 단위 탐색으로 재현 가능 — **보안 목적으로는 현재 기준 취약**.
  - ✅ 현행: `SecureRandom` (가능하면 `SecureRandom.getInstanceStrong()`) — 토큰·키·세션ID 등 보안 목적 난수 전부. (출처: Java SE 표준 API; 2026 교안 p.35 "보안 목적은 SecureRandom"과 일치.)
- 참고 문헌(원문): CWE-330 · SANS Top 25 2009 (CWE-330) · Viega & McGraw, "Building Secure Software" (2002).

### 2.8 전역적으로 접근 가능한 파일 (CWE 미부여) — **Android 특화** ⚠️

- **정의(원문)**: 파일 생성 시 다른 응용프로그램이 접근할 수 있는 인자값(**MODE_WORLD_READABLE, MODE_WORLD_WRITABLE**)을 사용하면 보안성·무결성이 침해될 수 있다.
- **안전한 코딩기법(원문)**: 파일 접근권한은 최소한으로 유지.
- **코드 차이(원문)**:

```java
// ❌ FileOutputStream fOut = openFileOutput("test", MODE_WORLD_READABLE);
// ✅ FileOutputStream fOut = openFileOutput("test", MODE_PRIVATE);
```

- ⚠️ **현행**: 권고 방향(MODE_PRIVATE)은 지금도 유효. 다만 `MODE_WORLD_*` 는 API 17 deprecated, **API 24(Android 7.0)+에서 사용 시 SecurityException** — 신규 코드에서 등장하면 그 자체가 빌드/런타임 문제. 앱 간 공유가 필요하면 FileProvider 등 명시적 메커니즘 사용 (출처: Android developer docs `Context`; 원문 미기재 — 현행 권고).
- 참고 문헌(원문): developer.android.com · KISA 「안드로이드 기반 모바일 운영체제 보안기능 분석」.

### 2.9 외부에서 접근하여 활성화 가능한 컴포넌트 (CWE 미부여) — **Android 특화** · 2판 개정 항목 ⚠️

- **정의(원문, 2판 수정)**: manifest.xml에 `android:exported="true"` 로 설정된 컴포넌트는 외부에서 인텐트를 전달하여 활성화시킬 수 있다. 원래 의도하지 않았던 상황에서 수행이 시작되어 보안 침해 가능. 동일한 인텐트 필터를 사용하는 컴포넌트가 여러 개인 경우 **리졸버(resolver) 액티비티**가 동작하고, 라우팅되는 인텐트는 **System 레벨 사용자 권한으로 송신자의 ID가 바뀌어 전송**되므로 위험이 커진다.
- **안전한 코딩기법(원문)**: 컴포넌트에 대한 접근권한을 외부에 제공하지 않는다.
- **코드 차이(원문)**:

```xml
<!-- ❌ --> <service android:name=".syncadapter.SyncService" android:exported="true">
<!-- ✅ --> <service android:name=".syncadapter.SyncService" android:exported="false">
```

- 원문은 "속성을 제거하면 false가 된다"고 서술.
- ⚠️ **현행**: intent-filter가 있는 컴포넌트는 exported 기본값이 true로 동작해 왔고, **Android 12(API 31)+는 intent-filter 보유 컴포넌트에 `android:exported` 명시가 없으면 설치 자체가 거부**된다. "속성 제거 = false"라는 2011년 서술을 그대로 적용하지 말 것 (출처: Android 12 behavior changes, developer.android.com).

### 2.10 공유 아이디에 의한 접근제어 통과 (CWE 미부여) — **Android 특화**

- **정의(원문)**: `<manifest>` 태그에 `android:sharedUserId` 를 설정하면, 같은 아이디와 서명을 사용하는 다른 응용프로그램이 해당 프로그램의 정보에 접근할 수 있어 무결성·보안성이 침해될 수 있다.
- **안전한 코딩기법(원문)**: 공유 아이디 설정을 하지 않는다.
- **코드 차이(원문)**:

```xml
<!-- ❌ --> <manifest ... android:sharedUserId="android.uid.developer1">
<!-- ✅ --> <manifest ...>   <!-- android:sharedUserId 속성 삭제 -->
```

- 현행 참고: `sharedUserId` 는 API 29에서 deprecated — 원문 권고("설정하지 말라")와 현행 방향이 일치 (출처: Android developer docs `<manifest>`).

### 2.11 경쟁 조건: 검사시점과 사용시점 TOCTOU (CWE-367)

- **정의(원문)**: 자원 상태를 검사한 뒤 사용하는 시점 사이에 상태가 변할 수 있어 교착 상태·경쟁 조건·동기화 오류 발생.
- **안전한 코딩기법(원문)**: 공유자원(예: 파일)을 여러 스레드가 접근할 경우 **`synchronized` 동기화 구문으로 한 번에 하나의 스레드만 접근**하게 한다.
- **코드 차이(원문)**: Activity에서 `FileAccessThread`(존재 확인 후 읽기)와 `FileDeleteThread`(존재 확인 후 삭제)를 동시 start → 검사와 사용 사이에 파일이 삭제될 수 있음. 안전한 코드는 ① `Thread` 상속 → `Runnable` 구현 + 단일 인스턴스를 여러 Thread가 공유 ② `public synchronized void run()` ③ 검사·읽기·삭제를 하나의 동기화 블록 안에서 수행.
- 현행 참고: 파일 계열 TOCTOU는 원자적 파일 API(`Files.move` + `ATOMIC_MOVE`, `Files.createFile` 등) 활용도 병행 검토 (Java 7+ 표준 API — 원문 미기재).

### 2.12 제대로 제어되지 않은 재귀 (CWE-674)

- **정의(원문)**: 재귀 순환횟수를 제어하지 못하면 메모리·스택 자원 과다 사용. 귀납 조건(base case)이 없는 재귀는 무한 재귀에 빠진다.
- **안전한 코딩기법(원문)**: 모든 재귀 호출을 조건문/반복문 블럭 안에서만 수행.
- **코드 차이(원문)**:

```java
// ❌ return n * factorial(n - 1);            // 종료 조건 없음
// ✅ if (n == 1) { i = 1; } else { i = n * factorial(n - 1); }
```

### 2.13 오류 메시지 통한 정보 노출 (CWE-209)

- **정의(원문)**: 오류 메시지를 통해 환경·사용자·데이터 등 내부정보가 유출. 예외 이름이나 스택트레이스를 출력하면 내부구조 파악이 쉬워진다.
- **안전한 코딩기법(원문)**: 배포 SW에서 내부 구조·민감 정보를 오류 메시지로 출력하지 않는다.
- **코드 차이(원문)**: `catch (IOException e) { e.printStackTrace(); }` → `catch (IOException e) { System.out.println("예외발생"); }` (내부 정보 없는 고정 메시지).
- 2026 교안 대응: 7장 "사용자엔 일반 메시지, 로그엔 상세(전역 예외 처리)" — 원문의 "출력하지 말라"에 더해 **서버 로그에는 상세히 남긴다**는 축이 현행 실무에서 추가된다.

### 2.14 오류 상황에 대한 처리 부재 (CWE-390)

- **정의(원문)**: 오류를 포착했으나 아무 조치도 하지 않으면 그 상태로 계속 실행되어 의도하지 않은 결과 초래.
- **안전한 코딩기법(원문)**: 예외를 catch한 경우 적절한 처리를 한다.
- **코드 차이(원문)**: DB 연결 코드의 **빈 catch 블록** → catch에서 `conn.close()` 등 자원 정리 수행.
- 2026 교안 대응: 7장 실습 B "예외 삼킴" — 착시 조치 7번과 동일 계열.
- 참고 문헌(원문): CWE-390 · OWASP Top Ten 2004 A7.

### 2.15 널포인터 역참조 (CWE-476)

- **정의(원문)**: "그 객체가 NULL이 될 수 없다"는 가정 위반 시 발생. 공격자가 의도적으로 유발한 예외는 추후 공격 계획에 활용될 수 있다.
- **안전한 코딩기법(원문)**: 레퍼런스의 null 여부를 검사하여 안전한 경우에만 사용.
- **코드 차이(원문)**: `System.getProperty("cmd")` 결과를 즉시 `cmd.trim()` → `if (cmd != null)` 검사 후 사용, else 분기 처리.

### 2.16 공용 메소드로부터 리턴된 private 배열-유형 필드 (CWE-495)

- **정의(원문)**: private 배열을 public 메서드로 반환하면 배열 레퍼런스가 외부에 공개되어 외부에서 수정 가능.
- **안전한 코딩기법(원문)**: 반환하지 않거나, **배열의 복제본을 반환**.
- **코드 차이(원문)**: `return colors;` → 새 배열 할당 후 요소 복사하여 반환.

### 2.17 private 배열-유형 필드에 공용 데이터 할당 (CWE-496)

- **정의(원문)**: public 데이터/메서드 인자가 private 배열에 그대로 저장되면 사실상 public 필드가 된다.
- **안전한 코딩기법(원문)**: 외부 배열의 레퍼런스가 아닌 **값을 복사**하여 저장.
- **코드 차이(원문)**: `this.userRoles = userRoles;` → 새 배열 할당 후 요소별 복사.

### 2.18 시스템 데이터 정보 누출 (CWE-497)

- **정의(원문)**: 시스템 내부 데이터·디버깅 정보가 공개되면 공격의 빌미가 된다.
- **안전한 코딩기법(원문)**: **디버깅용 시스템 정보 출력 코드를 모두 삭제**.
- **코드 차이(원문)**: `System.err.printf(e.getMessage());` → `System.err.println("IOException Occured");` (상세 정보 미노출).

---

## 3. 이 가이드에 **없는** 항목 — 과잉 인용 금지

2011년 2판은 아래 항목을 **다루지 않는다.** 이 가이드를 출처로 지적하지 말 것:

| 항목 | 상태 |
|---|---|
| Intent 자체 취약점(암시적 Intent 노출, Intent Spoofing, PendingIntent) | 없음 — exported 항목에서 인텐트 라우팅 위험만 간접 언급 |
| 권한(permission) 선언·커스텀 퍼미션(`<uses-permission>`, `protectionLevel`) | 없음 |
| WebView 취약점(`addJavascriptInterface`, `setJavaScriptEnabled`, SSL 오류 무시 등) | 없음 |
| 로그(Log) 민감정보 출력 | 별도 항목 없음 — `Log.w(...)` 는 예제 부수 코드로만 등장 |
| 외부저장소 저장 정책 | 별도 항목 없음 — CWE-36 예제에서 입력원으로만 등장 |
| ContentProvider 권한, KeyStore, 루팅 탐지, 난독화 | 없음 |

> ESAPI는 제2장 약어표에만 등장하며, 본문 17개 항목의 안전한 코딩기법에는 사용되지 않는다.
> 현행 Android 진단에서 위 미기재 항목의 점검이 필요하면 SKILL.md §6.2 「원문 범위 밖 — 현행 Android 필수 점검」과 `mobile-app-verify` 스킬을 근거로 사용하라.

## 4. 시대 지연 항목 요약 (⚠️ 목록)

| 항목 | 원문(2011) 권고 | 현행 권고 | 출처 |
|---|---|---|---|
| 2.7 난수 | `java.util.Random` + `setSeed(new Date().getTime())` | `java.security.SecureRandom` (`getInstanceStrong()` 가능 시) | Java SE 표준 API / 2026 교안 p.35 |
| 2.1·2.2 경로 조작 | `replaceAll()` 위험 문자 제거 / `indexOf("/")` 검사 | `Path.normalize()` + `startsWith(base)` 경계 검사 | Java 7+ 표준 API / 2026 교안 p.17 |
| 2.5 평문 전송 | `SSLSocketFactory.getDefault()` | TLS 1.2+ / 인증서·호스트네임 검증 유지 / Android cleartext 금지 | RFC 8996 / Android developer docs |
| 2.6 암호 알고리즘 | `AES/CBC/PKCS5Padding` | `AES/GCM/NoPadding` + 고유 IV (국내 제도는 `crypto-policy-kr`) | NIST SP 800-38D |
| 2.8 파일 모드 | MODE_PRIVATE (방향 유효) | 동일 + `MODE_WORLD_*` 는 API 24+에서 SecurityException, 공유는 FileProvider | Android developer docs |
| 2.9 exported | "속성 제거 시 false" | Android 12+ intent-filter 보유 시 exported **명시 필수**, 기본값 서술 폐기 | Android 12 behavior changes |
