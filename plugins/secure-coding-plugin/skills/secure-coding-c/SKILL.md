---
name: secure-coding-c
description: |
  행정안전부/KISA 「C 시큐어 코딩 가이드(3판)」 58개 보안약점 기반 C/C++ 시큐어코딩 레퍼런스 스킬.
  Reference for C/C++ secure coding per the MOIS/KISA C Secure Coding Guide (3rd ed., 58 weaknesses).

  사용자가 다음 표현을 쓸 때 반드시 이 스킬을 사용하라 (Trigger):
  - "C 시큐어코딩", "C 보안약점", "위험 함수"
  - "버퍼 오버플로", "포맷 스트링", "정수 오버플로", "널 포인터 역참조"
  - "strcpy", "sprintf", "gets"
  - "TOCTOU", "경쟁 조건", "해제 후 사용", "심볼릭 링크 공격"
  - "명령어 삽입 C", "system() 안전하게", "chroot", "umask"
  - "FORTIFY_SOURCE", "ASan", "valgrind", "컴파일러 하드닝", "CERT C"
  일반 C/C++ 개발·메모리 디버깅에는 쓰지 마라 — 보안 진단·시큐어코딩 검토 맥락일 때만.

  경계: 키 길이=`crypto-policy-kr`, 기준·오탐=`secure-coding-kr`, 검증=`mobile-app-verify`.

  관련 스킬:
  - `secure-coding-kr`: 보안약점 기준·진단절차 허브.
  - `secure-coding-java`: Java/Android 시큐어코딩.
  - `crypto-policy-kr`: 암호 알고리즘·키 길이 권고.
---

# C 시큐어 코딩 (KISA 3판 + 현행 모범사례) 레퍼런스 스킬

> 근거 문서: 「(3판) C 시큐어 코딩 가이드」 행정안전부·한국인터넷진흥원(KISA), 본문 212페이지.
> 이 스킬의 모든 페이지 표기 `(p.N)`은 위 원문 본문 페이지 기준이다. **원문에 없는 내용은 "원문 미기재/원문 범위 밖"으로 명시한다.**

## 1. 개요

- 원문은 C 언어 보안약점 **58개**를 7개 유형으로 분류한다:
  입력데이터 검증 및 표현 19 / 보안기능 17 / 시간 및 상태 3 / 에러 처리 3 / 코드 오류 9 / 캡슐화 2 / API 오용 5.
- 각 항목은 `가. 정의 → 나. 안전한 코딩기법 → 다. 예제(안전하지 않은/안전한 코드) → 라. 참고문헌(CWE 등)` 4단 구성.
- 본 가이드의 58개 항목은 **「소프트웨어 보안약점 진단가이드(2021)」 구현단계 49개 기준과 별개의 C 특화 체계**다.
  전 언어 공통 진단기준은 `secure-coding-kr` 스킬을 참조하라.

**보고서 기재값의 정본(正本) 라우팅**: 진단 보고서에 기재할 **기준번호(1~49)·공식 보안약점명·CWE**는 허브 스킬 `secure-coding-kr`의 `references/weakness-49.md` 총괄표가 정본이며, 이 스킬의 58개 항목은 **C 가이드 3판 자체 체계**로서 구현·수정 패턴을 담당한다. 이 스킬의 CWE 표기(CWE-121/122/170 등)는 C 3판 체계이므로 **보고서 기재용이 아니다** — 두 체계는 번호·명칭·CWE가 모두 별개다. §4 각 절 머리의 기준표와 `references/weakness-58.md` 총괄표의 「2021 기준#」 열은 그 총괄표에서 옮겨 적은 것이다.

**이 스킬의 이중 구조 (중요)**: 원문(3판)은 발간 시점이 오래되어 일부 권고가 현행 기준에 미달한다
(`strcpy→strncpy` 권고, 3DES 허용 등). 따라서 이 스킬은 각 항목을 다음 3단으로 제공한다.

```
❌ 취약 코드              ← 원문 예제 그대로 (진단 대상 패턴)
✅ 권장 (현행 모범사례)    ← 지금 실제로 써야 할 코드. 이것이 주된 권고
📋 원문 근거 (p.N)        ← 가이드 원문의 권고 + 현행과 다르면 왜 다른지
```

**진단(코드 리뷰) 시 판정 규칙**: ❌ 패턴 발견 → 지적. 원문 권고(📋)만 따른 코드
(예: 널 종단 없는 `strncpy`) → "원문 기준 충족, 현행 기준 미흡"으로 구분 지적하고 ✅ 를 제시하라.

## 2. 위험 함수 → 안전한 대체 함수 매핑

> 원문에는 별도의 "위험 함수 목록 표"가 없다. 아래 표는 각 항목의 「나. 안전한 코딩기법」과 예제에
> 실제 기재된 내용을 취합한 것이며, **주의사항 열은 현행 기준의 함정 경고**(원문 미기재)다.

### 2.1 문자열 / 버퍼

| 위험 함수·패턴 | 문제 | 원문 제시 대체 (p.) | ⚠️ 주의사항 (현행) |
|---|---|---|---|
| `gets()` | 길이 무검사 입력 → 오버플로 | `fgets(buf, BUFSIZE, stdin)` (p.196) | `gets()`는 **C11에서 표준 제거**됨. `fgets`는 개행 문자를 버퍼에 남김 |
| `strcpy()` (스택) | 오버플로 | `strncpy(buf, s, sizeof(buf)-1)` + 널 종단 (p.40) | **`strncpy`는 널 종단 미보장** — src가 n 이상이면 종단 없음, src가 짧으면 나머지를 0으로 채워 성능 손실. ✅ `snprintf(dst, sizeof dst, "%s", src)` 권장 |
| `strcpy()` (힙) | 오버플로 | `strlcpy(dest, src, BUFSIZE)` (p.44) | `strlcpy`는 **BSD/macOS 기본, glibc는 2.38부터** 제공(구버전 리눅스는 `-lbsd` 필요). 절단 발생 여부를 반환값으로 검사할 것 |
| `strcat()` | 오버플로 | `strncat(dst, src, 남은크기)` (p.65 예제) | `strncat`의 n은 **"이어붙일 최대 문자 수"** 이지 dst 전체 크기가 아님 — `MAX - strlen(dst)` 계산 오류가 흔한 버그. ✅ `snprintf` 또는 `strlcat` 권장 |
| `sprintf()` | 길이 무제한 출력 | (원문은 SQL 삽입 예제 등에서 취약 사용만 등장) | ✅ `snprintf(dst, sizeof dst, ...)` — 반환값이 버퍼 크기 이상이면 절단 발생 |
| `read()`/`readlink()` 결과에 `strcpy`/`strcat`/`strlen` | 널 종단 미보장 | `strlcpy()`, `strlcat()` (p.65) | `read`/`readlink`는 널 종단을 **절대 붙이지 않음** — 읽은 바이트 수로 직접 `buf[n] = '\0'` 처리 후 사용 |
| `strncpy()` (크기가 src보다 작을 때) | 널 종단 미보장 | 복사 후 명시적 널 종단 또는 `strlcpy()` (p.65) | 이 함정 때문에 CERT C(STR32-C)는 strncpy 결과의 널 종단 확인을 요구 |
| `_mbscpy()`/`_mbscat()` 등 `_mbsXXX()` | 멀티바이트 오버플로 | `_mbscpy_s()`, `_mbscat_s()` (p.202~203) | `_s` 계열(Annex K)은 **사실상 MSVC 전용** — glibc 미구현으로 리눅스 이식성 없음. 크로스플랫폼은 `snprintf`/`strlcpy` 계열로 |
| `strtok()` 반환 포인터 `free()` | 지역 배열을 가리킴 — 해제 불가 | `free()` 금지 (p.181) | `strtok`은 정적 상태 보유 — 멀티스레드는 `strtok_r()` (POSIX) 사용 |

### 2.2 프로세스 / 시스템 호출

| 위험 함수·패턴 | 문제 | 원문 제시 대체 (p.) | ⚠️ 주의사항 (현행) |
|---|---|---|---|
| `system(외부입력)` | OS 명령어 삽입 | 후보 명령어 리스트 선택 또는 `strpbrk(arg, ";\"'.")` 검사 (p.15) | 원문의 4문자 블랙리스트는 `|`, `` ` ``, `$()`, `&`, 개행 등을 놓침 — **불충분**. ✅ CERT C ENV33-C: `system()` 자체를 쓰지 말고 `fork()`+`execv(절대경로, 인자배열)` 사용 |
| `vfork()` | 부모 주소공간 공유 — 오작동 | `fork()` (p.197) | `vfork`는 POSIX.1-2008에서 obsolete. 성능이 필요하면 `posix_spawn()` |
| `getlogin()` (멀티스레드) | 반환값이 타 스레드에 의해 변경 | `getlogin_r(id, MAX)` (p.205) | 반환 버퍼 크기 여유 확보, 실패(비0) 검사 필수 |
| `chroot()` 단독 | 상대경로로 jail 탈출 | `chroot()` 직후 `chdir("/")` (p.198) | chroot 전에 열린 fd로도 탈출 가능 — root 권한 드롭(`setuid`)까지 병행. 격리는 컨테이너/네임스페이스가 더 견고 |
| `chroot()` 후 권한 미복귀 | 최소 권한 위배 | 직후 `seteuid()` 로 복귀 (p.128) | 권한 드롭 순서: `setgroups()` → `setgid()` → `setuid()` — 역순이면 실패 |
| `dlopen(getenv(...))` | 임의 라이브러리 적재 | 절대경로 상수 `dlopen("/usr/lib/hello.so", ...)` (p.53) | `LD_PRELOAD`/`LD_LIBRARY_PATH` 도 신뢰 불가 — setuid 프로그램은 특히 주의 |
| `sethostid(atol(argv[1]))` | 시스템 설정 외부 제어 | 상수 사용 (p.50) | — |
| `umask(0)` | 전체 rw 허용 파일 생성 | `umask(077)` (p.82) | `fopen` 대신 `open(path, O_CREAT|O_WRONLY, 0600)` 으로 권한을 명시하는 편이 확실 |
| `access()` + `fopen()` | TOCTOU 경쟁 조건 | 파일 핸들 사용, mutex (p.140, 149) | ✅ `open()` 후 `fstat()` — 파일명 재검사 금지 (CERT C FIO45-C). 심볼릭 링크는 `O_NOFOLLOW|O_EXCL` |
| `SO_REUSEADDR` + `INADDR_ANY` 동시 사용 | 동일 포트 다중 바인딩 | 동시에 사용하지 않는다 (p.138) | — |
| `getenv()` 반환값 무검사 | 널 포인터 역참조 | 사용 전 NULL 검사 (p.162) | `getenv` 반환 문자열은 이후 호출로 무효화될 수 있음 — 필요 시 복사 |

### 2.3 자원 할당 / 해제 쌍

| 할당 | 반드시 짝이 되는 해제 | 출처 (p.) | ⚠️ 주의사항 (현행) |
|---|---|---|---|
| `SQLAllocHandle(SQL_HANDLE_ENV/DBC, ...)` | `SQLFreeHandle(...)` (역순) | p.166 | 에러 경로 포함 **모든** 경로에서 해제 (`goto cleanup` 패턴) |
| `socket()` / `accept()` | `shutdown()` + `close()` | p.166 | `fork()` 실패(-1) 경로에서도 `close()` 누락 금지 |
| `pthread_create()` | `pthread_join()` 또는 `pthread_detach()` | p.182 | C++는 `std::jthread`(C++20)가 자동 join |
| `pthread_cleanup_push()` | `pthread_cleanup_pop()` (같은 스코프) | p.178 | 매크로 쌍 — 중괄호를 여닫는 구현이 흔해 스코프 불일치 시 컴파일 오류/UB |
| `malloc()` | `free()` — 이후 포인터 `NULL` 대입 | p.44, 185 | ✅ double-free/use-after-free 방지: `free(p); p = NULL;` + ASan/Valgrind 검증 (아래 4.3) |
| 지역 배열 (`char p[10]`) | **`free()` 금지** (자동 반환) | p.180 | `strtok()` 반환값도 동일하게 `free()` 금지 (p.181) |

### 2.4 암호 / 난수 (상세 키 길이는 `crypto-policy-kr` 스킬 연계)

| 위험한 것 | 원문 제시 대체 (p.) | ✅ 현행 권장 (원문과 다름 — 주의) |
|---|---|---|
| base64 등 단순 인코딩으로 패스워드 보호 | 검증된 암호 알고리즘 (p.84) | 인코딩 ≠ 암호화. 패스워드 저장은 Argon2id 등 KDF (`crypto-policy-kr` 참조) |
| RC2/RC4/RC5/RC6, MD4/MD5, SHA1, DES | **3-DES, AES, SEED** (p.84), AES/ARIA/SEED/3DES (p.107) | **3DES는 현행 기술 기준 부적합** — NIST SP 800-131A Rev.2에서 **2023년 말 이후** 암호화 용도 불허(disallowed). 제도(KISA 안내서 2018)에는 3DES 금지 목록이 없으므로 지적 근거는 NIST를 인용하라 (`crypto-policy-kr` 참조). ✅ **AES-GCM 또는 ARIA/SEED/LEA + AEAD 구성** |
| 해쉬 MD4/MD5/SHA1 | 사용 금지 (p.107) | MD4/MD5는 용도 불문 부적합. **SHA-1은 용도별로 판정을 구분**한다 — ① 제도 판정: 단순해시(비밀번호 저장 포함)·전자서명 ❌ 부적합 / 메시지인증(HMAC-SHA1)·키유도·난수생성 ✅ 제도상 허용 — 일괄 지적은 과잉 (근거: KISA 「암호 알고리즘 및 키 길이 이용 안내서」 2018, `crypto-policy-kr` 참조). ② 기술 권고: 신규 설계는 용도 불문 SHA-256 이상/SHA-3 상향 (출처: NIST SP 800-131A Rev.2). 패스워드는 단순 해시가 아닌 KDF |
| `RSA_generate_key(512, ...)` | RSA 2048비트 이상, 대칭 128비트 이상 (p.96, 107) | `RSA_generate_key()`는 OpenSSL 3.0에서 deprecated — `EVP_PKEY_Q_keygen(NULL, NULL, "RSA", 3072)` 등 EVP API 사용 |
| `RSA_public_encrypt(..., RSA_NO_PADDING)` | `RSA_PKCS1_OAEP_PADDING` (p.132) | OAEP는 현행도 유효 (RFC 8017). PKCS#1 v1.5 암호화 패딩도 금지 대상 |
| `crypt(text, "xp")` (하드코드 솔트) | 매번 새 난수 salt (p.134) | `crypt()` 자체가 DES 기반 레거시 — 패스워드 저장은 Argon2id/bcrypt/scrypt (`crypto-policy-kr` 3항) |
| 솔트 없는 일방향 해쉬 | 패스워드+솔트 해쉬 (p.114) | 솔트만으로는 부족 — 스트레칭(KDF) 필수 (`crypto-policy-kr` 3항) |
| `srand(100)` / `srand(time(NULL))` + `rand()` | 랜덤 seed 변경 (p.99) | **seed 교체로는 불충분 — `rand()`는 암호학적 용도 금지.** ✅ 아래 4.8 |

### 2.5 정수 / 타입 변환

| 위험 패턴 | 원문 제시 대체 (p.) | ⚠️ 주의사항 (현행) |
|---|---|---|
| `malloc(signed_int * sizeof(int))` | 할당량 파라미터 `unsigned` 전달 (p.29) | unsigned 전환만으론 wrap-around 미해결 — ✅ 체크드 연산 (4.2) |
| 곱셈/덧셈 전 범위 미검사 | `MAX_VALUE / 배수` 사전 검사 (p.31) | ✅ `__builtin_mul_overflow` / C23 `ckd_mul` 이 간결·무결 (4.2) |
| `int`→`short`→`unsigned` 암묵 변환 | 범위 검사 후 명시적 캐스팅 (p.69) | 원문 안전 예제도 상한 검사가 `> 256`(off-by-one, 유효 인덱스는 0~255) |
| 음수 반환 가능 함수를 `unsigned`로 수취 | `int`로 받고 `< 0` 검사 후 캐스팅 (p.73) | `-1` → `0xFFFFFFFF` — `memcpy` 크기 인자로 흘러가면 치명적 |
| `char bA = iB;` (int→char 절단) | 충분한 크기 타입 사용 (p.172) | `-Wconversion` 컴파일 경고 활성화로 기계 검출 |
| 배열 인덱스 루프 비교 `>` | `>=` 사용 (p.61) | 인덱스는 `0 <= idx && idx < size` 양쪽 검사 |

## 3. 유형별 보안약점 58개 개관

| 유형 | 개수 | 대표 항목 (본문 p.) |
|---|---|---|
| 1. 입력데이터 검증 및 표현 | 19 | SQL 삽입(3), OS 명령어 삽입(15), 경로 조작(21), 정수 오버플로우(29), 스택/힙 버퍼 오버플로우(40/44), 널 종료 문제(65) |
| 2. 보안기능 | 17 | 취약한 암호화 알고리즘(84), 하드코드된 패스워드(93), 부적절한 난수(99), 최소 권한 위배(128), RSA 패딩(132) |
| 3. 시간 및 상태 | 3 | TOCTOU 경쟁 조건(140), 제어되지 않은 재귀(147), 심볼릭명 매핑(149) |
| 4. 에러 처리 | 3 | 오류 메시지 정보 노출(152), 오류상황 대응 부재(156), 부적절한 예외처리(159) |
| 5. 코드 오류 | 9 | 널 포인터 역참조(162), 부적절한 자원 해제(165), 스택 변수 주소 리턴(175), 스택 주소 해제(180), 무한 자원 할당(185) |
| 6. 캡슐화 | 2 | 남은 디버그 코드(188), 시스템 데이터 정보노출(190) |
| 7. API 오용 | 5 | 위험한 함수 사용(196), chroot Jail(198), 문자열 관리 오용(202), getlogin()(205) |
| **합계** | **58** | 전체 목록·CWE 매핑: `references/weakness-58.md` |

## 4. 핵심 항목 심층 (❌ 취약 / ✅ 현행 권장 / 📋 원문 근거)

### 4.1 버퍼 오버플로 (CWE-121/122/124/125/129/170)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 16 | 메모리 버퍼 오버플로우 | CWE-119 |
| 49 | 취약한 API 사용 (`strcpy`·`gets` 등 금지 API 사용) | CWE-676, CWE-242 |

> **이중 해당 판정** (예: 무검증 `strcpy(buf, 외부입력)` — 기준 16·49 양쪽 정탐 가능): 주(主)/부(副) 선택 규칙은 허브 문서 미기재다. 외부 입력이 버퍼 한계를 실제로 넘을 수 있으면 **기준 16을 주로, 49를 부로 병기**하고, 한계 초과가 성립하지 않는 단순 금지 API 사용이면 **기준 49**로 보고하라 — 어느 쪽이든 양쪽 근거 병기를 권장한다.

❌ 취약 코드 (p.40, p.44):

```c
void manipulate_string(char* string)
{
  char buf[24];
  strcpy(buf, string);
}
```

✅ 권장 (현행 모범사례):

```c
void manipulate_string(const char* string) {
  char buf[24];
  // snprintf는 항상 널 종단을 보장하고, 반환값으로 절단을 검출할 수 있다
  int n = snprintf(buf, sizeof buf, "%s", string);
  if (n < 0 || (size_t)n >= sizeof buf) {
    // 절단 또는 인코딩 오류 — 정책에 따라 거부/로깅
    return;
  }
}
```

- 대안: `strlcpy(buf, string, sizeof buf)` (BSD/macOS 기본, glibc 2.38+, 그 외 리눅스 `-lbsd`) — 반환값 ≥ 크기이면 절단.
- `strncpy`를 불가피하게 쓰면 **반드시** `buf[sizeof(buf)-1] = '\0';` 를 병기하라 (CERT C STR32-C).
- 읽기 방향(CWE-125)·배열 인덱싱(CWE-129)은 사용 전 `0 <= idx && idx < size` 양쪽 검사. 루프 종료 비교는 `>=` (p.61).
- 검출 도구: `-fsanitize=address` (ASan) 는 스택/힙/전역 out-of-bounds를 런타임에 잡는다.

📋 원문 근거: 스택(p.40)은 `strcpy → strncpy + 명시적 널 종단`, 힙(p.44)·널 종료(p.65)는 `strlcpy/strlcat` 권고.
원문 방향 자체는 유효하나, `strncpy` 단독 사용은 널 종단 미보장·불필요한 0 채우기 함정이 있어 현행 1순위는 `snprintf`/`strlcpy`다.
(참고: 원문 p.40 안전 예제의 `if (strlen(string < sizeof(buf))`는 원문 괄호 오류 그대로다 — 인용 시 주의.)

### 4.2 정수 오버플로·부호 변환·형변환 (CWE-190/194/195/196/398)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 14 | 정수형 오버플로우 | CWE-190 |

(부호 확장·정수↔문자 등 타입 변환 오류 — C 3판 18·19·45·46번 — 는 해당 2021 기준 미대응 — 허브에서 확인 필요. 재량으로 기준 14를 인용하려면 C 3판 근거를 반드시 병기하라.)

❌ 취약 코드 (p.29):

```c
void* intAlloc(int size, int reserve)
{
  void *rptr;
  size += reserve;
  rptr = malloc(size * sizeof(int));
  ...
}
```

✅ 권장 (현행 모범사례):

```c
#include <stdint.h>
#include <stdlib.h>

void* intAlloc(size_t size, size_t reserve) {
  size_t total, bytes;
  // GCC/Clang 체크드 연산: 오버플로 시 참을 반환 (C23은 <stdckdint.h>의 ckd_add/ckd_mul)
  if (__builtin_add_overflow(size, reserve, &total) ||
      __builtin_mul_overflow(total, sizeof(int), &bytes)) {
    return NULL;
  }
  return malloc(bytes);
}
```

- GCC·Clang: `__builtin_add_overflow` / `__builtin_sub_overflow` / `__builtin_mul_overflow`.
- C23 표준: `<stdckdint.h>` 의 `ckd_add` / `ckd_sub` / `ckd_mul` (동일 의미론).
- 음수 반환 가능 함수(`-1` 에러 코드)는 `int` 로 받고 `< 0` 검사 후에만 `(size_t)` 캐스팅 (p.73 원문 방향 유효).
- 검출: `-fsanitize=undefined` (UBSan) 가 signed overflow를 런타임 검출, `-Wconversion` 이 암묵 절단을 컴파일 타임 경고.

📋 원문 근거: 원문(p.29)은 "할당량 파라미터를 unsigned로 전달"을 권고하고, 사례 2(p.31)는 `MAX_VALUE / DATA_SIZE` 수동 사전 검사를 제시한다.
그러나 **원문 안전 예제 자체에 결함이 있다**: `unsigned s; ... if (s < 0)` 는 항상 거짓이며, `size += reserve` 의 signed overflow(UB)도 남는다.
수동 검사보다 체크드 연산이 정확하고 누락이 없다 (출처: CERT C INT30-C/INT32-C, C23 표준).

### 4.3 메모리 해제 오류 — use-after-free / double-free / 누수 (CWE-404/730)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 40 | 부적절한 자원 해제 (누수·미반환) | CWE-404 |
| 41 | 해제된 자원 사용 (use-after-free·double-free) | CWE-416 |

(스택 주소 해제·매크로 오용 — C 3판 48·49번 — 은 해당 2021 기준 미대응 — 허브에서 확인 필요.)

❌ 취약 코드 (p.181, `strtok` 반환값 이중 해제):

```c
  pch = strtok (str," ,.-");
  free(pch);
  while (pch != NULL)
  {
    printf ("%s\n",pch);
    pch = strtok (NULL, " ,.-");
    free(pch);
  }
```

✅ 권장 (현행 모범사례):

```c
// 소유권 규칙: malloc한 코드가 free한다. 빌린 포인터(strtok 반환값 등)는 절대 free하지 않는다.
char *p = malloc(n);
if (p == NULL) {
  return -1;
}
/* ... 사용 ... */
free(p);
p = NULL;  // 재해제(double-free)·해제 후 사용(use-after-free)을 널 검사로 차단
```

- **소유권 1원칙**: 할당 지점과 해제 지점을 1:1로 문서화. 함수 경계를 넘는 포인터는 "소유 이전/대여"를 주석으로 명시.
- 에러 경로 포함 모든 경로에서 해제: C는 `goto cleanup` 단일 출구 패턴, C++은 RAII(`std::unique_ptr`, `std::vector`).
- **검출 도구를 CI에 상시 편성**: `-fsanitize=address` (use-after-free/double-free/leak), Valgrind memcheck, `-fsanitize=undefined`.
  (출처: CERT C MEM30-C/MEM31-C, Clang/GCC AddressSanitizer 문서)

📋 원문 근거: 자원 해제 쌍 강제(p.165), 스택 주소 `free()` 금지(p.180), `strtok` 반환값 `free()` 금지(p.181),
`pthread_join`/`detach`(p.182). 원문 방향은 유효하나 "free 후 NULL 대입"과 검출 도구(ASan/Valgrind)는 원문 미기재 — 현행 필수 보강.

### 4.4 널 포인터 역참조 (CWE-476)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 39 | Null Pointer 역참조 | CWE-476 |

❌ 취약 코드 (p.162):

```c
  char *p = NULL;
  char cgi_home[BUFSIZE];
  p = getenv("CGI_HOME");
  strncpy(cgi_home, p, BUFSIZE-1);
```

✅ 권장 (현행 모범사례):

```c
const char *p = getenv("CGI_HOME");
if (p == NULL) {
  fprintf(stderr, "CGI_HOME not set\n");
  return -1;
}
char cgi_home[BUFSIZE];
snprintf(cgi_home, sizeof cgi_home, "%s", p);
```

- NULL 반환 가능 함수 목록을 팀 차원에서 관리: `getenv`, `malloc`, `fopen`, `strchr`, `strstr`, `strtok`, `getpwnam` 등.
- 정적 검출: `clang-tidy` 의 `clang-analyzer-core.NullDereference`, GCC `-fanalyzer`.

📋 원문 근거 (p.162): "변경될 수 있는 모든 포인터는 사용하기 전에 점검" — 현행과 동일. (원문 예제의 `cig_home` 은 원문 오탈자.)

### 4.5 명령어/자원 삽입 — system(), exec* (CWE-78/99/114)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 5 | 운영체제 명령어 삽입 | CWE-78 |
| 3 | 경로 조작 및 자원 삽입 (포트 등 자원 식별자 삽입) | CWE-99, CWE-22 |

(프로세스 제어 — C 3판 13번, `dlopen(getenv(...))` 외부 경로 라이브러리 적재 — 는 해당 2021 기준 미대응 — 허브에서 확인 필요.)

❌ 취약 코드 (p.15, catWrapper):

```c
  fgets(arg,80,stdin);
  commandLength = strlen(cat) + strlen(arg) + 1;
  command = (char *) malloc(commandLength);
  strncpy(command, cat, commandLength);
  strncat(command, argv[1], (commandLength - strlen(cat)) );
  system(command);
```

✅ 권장 (현행 모범사례):

```c
// 1) 쉘을 아예 통과시키지 않는다: system() 대신 fork + execv(절대경로, 인자배열)
// 2) 입력은 허용목록(allowlist)으로 검증한다 — 금지문자 블랙리스트가 아니라
#include <unistd.h>
#include <sys/wait.h>

int run_cat(const char *filename) {
  // 허용목록 검증: 파일명은 영숫자, '.', '_', '-' 만
  for (const char *c = filename; *c; ++c) {
    if (!isalnum((unsigned char)*c) && *c != '.' && *c != '_' && *c != '-') {
      return -1;
    }
  }
  pid_t pid = fork();
  if (pid == 0) {
    char *const argv[] = {"/bin/cat", (char *)filename, NULL};
    execv("/bin/cat", argv);  // 인자가 개별 배열 원소로 전달 — 쉘 해석 없음
    _exit(127);
  }
  int status;
  return (pid > 0 && waitpid(pid, &status, 0) == pid) ? status : -1;
}
```

📋 원문 근거 (p.15): 후보 명령어 리스트 선택 또는 `strpbrk(arg, ";\"'.")` 위험문자 검사.
**원문의 4문자 블랙리스트는 불충분** — `|`, `&`, `` ` ``, `$()`, 개행, 리다이렉션을 걸러내지 못한다.
현행 권고는 `system()` 자체 금지 + `exec*` 직접 호출 (출처: CERT C ENV33-C "Do not call system()").
자원 삽입(p.8)의 포트 범위 화이트리스트, 프로세스 제어(p.53)의 `dlopen` 절대경로 상수는 원문 방향 그대로 유효.

### 4.6 경로 조작·심볼릭 링크·TOCTOU (CWE-22/23/36/367/386)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 3 | 경로 조작 및 자원 삽입 | CWE-99, CWE-22 |
| 34 | 경쟁조건: 검사 시점과 사용 시점(TOCTOU) | CWE-367 |

> 보고서에는 기준 3의 **CWE-22** 를 기재한다 — C 3판의 CWE-23(상대)/CWE-36(절대)은 참고 표기로만 병기. 심볼릭명 매핑(C 3판 39번, CWE-386)은 1:1 대응 기준이 없다 — 검사·사용 시간차 공격이 성립하면 기준 34로 보고하되 C 3판 근거를 병기하라.

❌ 취약 코드 (p.149, access→fopen 시간차):

```c
  if(!access(file,W_OK))
  {
    f = fopen(file,"w+");
    operate(f);
  }
```

✅ 권장 (현행 모범사례):

```c
#include <fcntl.h>
#include <sys/stat.h>

// 검사와 사용을 하나의 syscall로: 이름 재검사 대신 fd 기반으로 일관 처리
int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
if (fd < 0) {
  return -1;  // 이미 존재(O_EXCL) 또는 심볼릭 링크(O_NOFOLLOW) — 공격 시도로 간주 가능
}
struct stat st;
if (fstat(fd, &st) == 0 && S_ISREG(st.st_mode)) {
  /* fd로만 조작 — 이후 파일명 기반 검사·재열기 금지 */
}
```

- `O_EXCL`: 기존 파일(공격자가 만든 심링크 포함)이면 실패. `O_NOFOLLOW`: 최종 경로가 심링크면 실패.
- 디렉터리 기준 상대 조작은 `openat()`/`fstatat()` 로 레이스 창을 제거.
- 경로 문자열 검증: 외부 입력을 경로에 조합하지 말고(원문 p.21과 동일), 불가피하면 `realpath()` 정규화 후
  허용 베이스 디렉터리의 접두사인지 확인 + `..` 성분 거부.
- 스레드 간 공유 상태는 `pthread_mutex_lock/unlock` (원문 p.140과 동일).
  (출처: CERT C FIO45-C "Avoid TOCTOU race conditions while accessing files", POSIX open(2))

📋 원문 근거: "파일 이름으로 권한을 검사하고 열면 취약 — 파일 핸들 사용 권장, mutex 사용"(p.140),
"심볼릭 링크 바꿔치기를 염두에 둔 프로그래밍"(p.149), "경로 인수에 외부 입력 조합 금지"(p.21).
원문 방향은 정확하나 구체 API(`O_EXCL|O_NOFOLLOW`, `openat`)는 원문 미기재 — 현행 보강.

### 4.7 권한 / umask / chroot 프로세스 보안 (CWE-266/272/732/243)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 20 | 중요한 자원에 대한 잘못된 권한 설정 (`umask(0)`·과다 파일 권한) | CWE-732 |

(프로세스 권한 부여·최소 권한 위배·chroot jail — C 3판 32·33·56번 — 은 해당 2021 기준 미대응 — 허브에서 확인 필요.)

❌ 취약 코드 (p.128, `chroot` 후 권한 미복귀 — `AAP_HOME`/`APP_HOME` 불일치는 원문 오탈자):

```c
char *privilegeDown()
{
  FILE *fp;
  chroot(APP_HOME);
  chdir("/");
  fopen("important_file", "r");
  ...
}
```

✅ 권장 (현행 모범사례):

```c
// chroot jail 구성의 표준 순서: chroot → chdir("/") → 권한 완전 드롭
if (chroot("/var/ftproot") != 0) { return -1; }
if (chdir("/") != 0) { return -1; }              // 상대경로 탈출 차단 (원문 p.198과 동일)
if (setgroups(0, NULL) != 0) { return -1; }      // 보조 그룹 제거
if (setgid(unpriv_gid) != 0) { return -1; }      // 그룹 먼저
if (setuid(unpriv_uid) != 0) { return -1; }      // 마지막에 uid — 이후 재상승 불가 확인
if (setuid(0) == 0) { return -1; }               // 드롭 성공 검증 (성공하면 안 됨)
```

- 파일 생성 권한: `umask(077)` (p.82) 또는 `open(..., 0600)` 으로 명시.
- 상승 권한 구간은 최소화하고, `seteuid(0)` → 작업 → `seteuid(getuid())` 복귀(p.124/128)를 함수 단위로 캡슐화.
- 드롭 순서와 검증은 CERT C POS36-C(권한 포기 순서)·POS37-C(포기 성공 확인) 기준.
- 견고한 격리가 필요하면 chroot보다 컨테이너/마운트 네임스페이스·seccomp을 우선 검토 (chroot는 보안 경계로 설계된 기능이 아님 — Linux chroot(2) man page).

📋 원문 근거: `umask(077)`(p.82), 사용자 권한만으로 수행(p.124), 권한 상승 직후 복귀(p.128), `chroot` 직후 `chdir("/")`(p.198). 모두 유효 — 드롭 순서·성공 검증이 원문 미기재라 현행 보강.

### 4.8 암호·난수 (CWE-327/310/330/325/759)

이 절이 다루는 진단가이드 2021 기준 (정본: `secure-coding-kr/references/weakness-49.md` 총괄표):

| 기준# | 보안약점명 (진단가이드 2021) | CWE |
|---|---|---|
| 21 | 취약한 암호화 알고리즘 사용 | CWE-327 |
| 24 | 충분하지 않은 키 길이 사용 | CWE-326 |
| 25 | 적절하지 않은 난수 값 사용 | CWE-330 |
| 31 | 솔트 없이 일방향 해쉬 함수 사용 | CWE-759 |

(하드코드된 패스워드·암호화 키는 기준 23 「하드코드된 중요정보」(CWE-259, CWE-321). RSA 패딩 오류 — C 3판 34번 — 는 1:1 대응 기준이 없다 — 기준 21로 보고하되 C 3판 근거를 병기하라.)

❌ 취약 코드 (p.99, 상수 seed):

```c
  srand( 100 );
  temp = rand()%101;
```

✅ 권장 (현행 모범사례):

```c
// 암호학적 난수(키, IV, salt, 토큰, 세션 ID)는 반드시 OS CSPRNG
#include <sys/random.h>   // Linux getrandom(2) — glibc 2.25+

unsigned char key[32];
if (getrandom(key, sizeof key, 0) != (ssize_t)sizeof key) {
  return -1;  // 대안: /dev/urandom 읽기, OpenSSL RAND_bytes(key, sizeof key)
}
```

- 우선순위: `getrandom(2)` > `/dev/urandom` > OpenSSL `RAND_bytes()`. macOS/BSD는 `arc4random_buf()`.
- **C++ 주의**: `std::random_device` 는 표준상 결정적 PRNG로 구현되어도 적합 — 구버전 MinGW에서 실제로 매번 같은 수열을 반환한 사례가 있다. 암호 용도로는 OS CSPRNG를 직접 써라.
- 암호 알고리즘: 원문 p.84의 `DES/RC*/MD*/SHA1 → 3DES, AES, SEED` 권고 중 **3DES는 현행 기술 기준 부적합**
  (NIST SP 800-131A Rev.2에서 **2023년 말 이후** 암호화 용도 disallowed, Sweet32). 제도(KISA 안내서 2018)에는
  3DES 금지 목록이 없으므로 지적 근거는 NIST를 인용하라. SHA-1은 **용도별 판정**(§2.4) — 단순해시·전자서명만
  제도상 부적합이며, 메시지인증(HMAC-SHA1)·키유도·난수생성은 허용(신규 설계는 SHA-256 이상 권장).
  ✅ **AES-GCM 또는 ARIA/SEED/LEA + AEAD 구성**. 키 길이·국내 알고리즘 선택은 `crypto-policy-kr` 스킬로.
- RSA: OAEP 패딩(p.132 원문 유효, RFC 8017), 키 2048비트 이상(장기 사용 3072). `RSA_generate_key()` 는 OpenSSL 3.0 deprecated — EVP API 사용.
- 패스워드 저장: 솔트 해시(p.114)만으로는 부족 — **Argon2id 등 KDF 필수** (`crypto-policy-kr` 3항).
  (출처: NIST SP 800-90A(DRBG), NIST SP 800-131A Rev.2, OWASP Password Storage Cheat Sheet)

📋 원문 근거: "랜덤 seed를 변경하여 사용"(p.99) — **불충분**. `rand()` 는 seed와 무관하게 예측 가능한 선형 합동 계열이므로 보안 용도 자체가 금지다 (CERT C MSC30-C "Do not use the rand() function for generating pseudorandom numbers").

## 5. 원문 범위 밖 — 현행 필수 점검

아래 항목은 **본 3판 원문에 존재하지 않는다.** 원문 근거로 지적하지 말고, 각 항목의 출처를 인용하라.

### 5.1 포맷 스트링 (CWE-134) — 원문에 없지만 C 진단 필수

> 판독 결과: 3판 `<표 1>` 58개 목록과 목차 어디에도 포맷 스트링 항목이 없다. 그러나 현행 C 진단에서 필수 점검 항목이며,
> 진단가이드 2021에는 **기준 17 「포맷 스트링 삽입」(CWE-134)** 이 존재한다 — 보고서에는 기준 17로 기재하라 (정본: `secure-coding-kr/references/weakness-49.md`).

```c
// ❌ 외부 입력을 포맷 문자열 위치에 직접 전달 — %n으로 임의 메모리 쓰기까지 가능
printf(user_input);
syslog(LOG_INFO, user_input);

// ✅ 포맷 문자열은 항상 상수, 외부 입력은 인자로
printf("%s", user_input);
syslog(LOG_INFO, "%s", user_input);
```

- 컴파일 검출: GCC/Clang `-Wformat -Wformat=2 -Werror=format-security`.
- 출처: **CERT C FIO30-C** "Exclude user input from format strings", CWE-134.

### 5.2 컴파일러 하드닝 플래그

```bash
# 배포 빌드 권장 기본선 (GCC/Clang)
CFLAGS="-O2 -D_FORTIFY_SOURCE=2 -fstack-protector-strong -fPIE -Wall -Wextra -Wformat=2 -Wconversion"
LDFLAGS="-pie -Wl,-z,relro,-z,now"
```

| 플래그 | 효과 |
|---|---|
| `-D_FORTIFY_SOURCE=2` | `memcpy`/`sprintf` 등의 컴파일·런타임 경계 검사 (glibc 2.34+/Clang은 `=3` 가능, `-O1` 이상 필요) |
| `-fstack-protector-strong` | 스택 카나리 — 스택 오버플로 악용 완화 |
| `-fPIE` + `-pie` | 실행파일 ASLR 적용 |
| `-Wl,-z,relro,-z,now` | GOT 영역 읽기전용 고정 (Full RELRO) |
| `-Werror=format-security` | 비상수 포맷 문자열을 컴파일 오류로 |

출처: **OpenSSF Compiler Options Hardening Guide for C and C++**, GCC/Clang 공식 문서.

### 5.3 정적/동적 분석 도구

| 단계 | 도구 | 용도 |
|---|---|---|
| 정적 | `clang-tidy` (`clang-analyzer-*`, `bugprone-*`, `cert-*` 체크) | 널 역참조, UAF 후보, CERT C 규칙 위반 |
| 정적 | `cppcheck --enable=all` | 자원 누수, 경계 오류, 미정의 동작 |
| 동적 | `-fsanitize=address` (ASan) | 힙/스택 오버플로, use-after-free, double-free, leak |
| 동적 | `-fsanitize=undefined` (UBSan) | signed overflow, 잘못된 시프트, 널 역참조 |
| 동적 | Valgrind memcheck | 비계측 바이너리의 메모리 오류·누수 |

- 원칙: **CI에서 ASan+UBSan 테스트 실행을 상시화**하라. 원문 58개 중 메모리·정수 계열 대부분이 기계 검출 가능하다.
- 출처: Clang Sanitizers 공식 문서, Valgrind 매뉴얼.

## 6. C 진단 체크리스트 (grep 패턴)

발견 즉시 지적 대상이 아니라 **정밀 확인 진입점**이다. 매칭 라인을 열어 4장 기준으로 판정하라.

```bash
# [금지·고위험 함수] gets(C11 제거)/위험 문자열 함수
grep -rn --include='*.[ch]' --include='*.cc' --include='*.cpp' \
  -E '\b(gets|strcpy|strcat|sprintf|vsprintf|_mbscpy|_mbscat)\s*\(' src/

# [명령어 삽입] system/popen/exec에 변수 유입 여부 확인
grep -rn -E '\b(system|popen)\s*\(' src/

# [strncpy 널 종단] strncpy 사용처마다 이후의 명시적 널 종단 존재 확인
grep -rn -E '\bstrncpy\s*\(' src/

# [난수] 보안 문맥의 rand 계열
grep -rn -E '\b(srand|rand|random)\s*\(' src/

# [포맷 스트링] 비상수 첫 인자 (수동 확인 필요)
grep -rn -E '\b(printf|fprintf|syslog|snprintf)\s*\(\s*[a-z_][a-zA-Z0-9_]*\s*[,)]' src/

# [TOCTOU] access 후 open/fopen 패턴
grep -rn -E '\baccess\s*\(' src/

# [권한] umask(0), chroot 단독, seteuid(0) 복귀 누락
grep -rn -E '\b(umask\s*\(\s*0\s*\)|chroot\s*\(|set(e)?uid\s*\()' src/

# [취약 암호] 레거시 알고리즘 심볼 — 매칭 즉시 지적 금지, 용도 확인 필수:
#   SHA1_ 계열: 단순해시·전자서명 용도만 제도상 부적합 — HMAC-SHA1 등 메시지인증·키유도·난수생성은
#   제도상 허용이므로 일괄 지적은 과잉 (`crypto-policy-kr` 참조. 신규 설계는 SHA-256 이상: NIST SP 800-131A Rev.2)
#   3DES(EVP_des_ede3): NIST 기준 2023년 말 이후 불허 — 제도(안내서 2018)엔 금지 목록 없음, NIST를 근거로 인용
grep -rni -E '\b(DES_|EVP_(des|rc2|rc4|md4|md5)|MD5_|SHA1_|RC4|EVP_des_ede3)' src/

# [메모리] free 이후 동일 포인터 재사용 후보 (도구 병행 필수 — 5.3)
grep -rn -E '\bfree\s*\(' src/

# [스레드] pthread_create 대비 join/detach 개수 비교
grep -rn -E '\bpthread_(create|join|detach)\s*\(' src/ | sort | uniq -c

# [기타 원문 항목] vfork, getlogin(비_r), dlopen(getenv), SO_REUSEADDR
grep -rn -E '\b(vfork\s*\(|getlogin\s*\(\s*\)|dlopen\s*\(\s*getenv|SO_REUSEADDR)' src/
```

빌드 검증 (5.2·5.3 연계):

```bash
cc -O2 -Wall -Wextra -Wformat=2 -Werror=format-security -Wconversion -c src/*.c   # 경고 0 확인
cc -g -fsanitize=address,undefined src/*.c -o app_asan && ./run_tests.sh app_asan  # 런타임 검증
```

## 7. 상세 레퍼런스

| 자료 | 내용 | 성격 |
|---|---|---|
| `references/weakness-58.md` | 58개 보안약점 전체 목록 (유형/한글명/영문명/CWE/원문 p. + **「2021 기준#」 대응 열**) + 항목별 정의 요약·핵심 코딩 규칙 | **원문(3판) 요약** + 58↔49 대응 (정본은 허브 `weakness-49.md`) |
| `references/c-code-patterns.md` | 원문 수록 ❌/✅ C/C++ 코드 예제 모음 (항목명·페이지 병기). **58개 중 47개 항목 수록** — 미수록 11개는 파일 서두 목록 참조. 원문 권고가 현행과 다른 예제에는 `> ⚠️ 현행 권고` 병기 | **원문 예제 원문 그대로**(부분 수록) + 현행 보정 주석 |
| 본문 4장·5장 | 현행 모범사례 코드와 출처 (CERT C, NIST, OpenSSF, POSIX 등) | **원문 범위 밖 현행 권고** |

- 특정 항목의 원문 정의·페이지가 필요하면 `references/weakness-58.md` 를 읽고 답하라.
- 원문 예제 코드 전문이 필요하면 `references/c-code-patterns.md` 를 읽고 답하라 (**47/58 항목 수록** — 미수록 항목은 파일 서두 목록으로 먼저 확인).
- 암호 알고리즘·키 길이의 정밀 판정은 반드시 `crypto-policy-kr` 스킬을 함께 참조하라.

검색 목적별 라우팅 — **무엇을 찾을 때 어디로 가는가** (허탕 왕복 방지):

| 찾는 것 | 어디로 |
|---|---|
| 진단 보고서 기재값 — 기준번호(1~49)·공식 보안약점명·CWE | `secure-coding-kr/references/weakness-49.md` 「총괄표 (49개)」 — **§4 기준표와 weakness-58 「2021 기준#」 열의 정본. `c-code-patterns.md`에는 보고용 기준번호가 없다** |
| C 3판 58개 목록·정의·페이지 + 58↔49 대응 | `references/weakness-58.md` (CWE 표기는 C 3판 자체 체계 — 보고서 기재용 아님) |
| 원문 ❌/✅ 코드 예제 전문 | `references/c-code-patterns.md` (47/58 수록) |
| 암호 알고리즘·키 길이·SHA-1/3DES 용도별 판정 | `crypto-policy-kr` 스킬 |
