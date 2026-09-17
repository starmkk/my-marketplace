# C 시큐어 코딩 가이드(3판) — 원문 코드 패턴 모음

> 「(3판) C 시큐어 코딩 가이드」(행정안전부/KISA) 원문에 수록된 ❌ 안전하지 않은 / ✅ 안전한 코드 예제를
> **원문 그대로** 수록한다 (원문 코드 스타일·오탈자 보존, 오탈자는 `[원문 오탈자]` 표기).
> 원문 권고가 현행 기준과 다른 예제에는 `> ⚠️ 현행 권고:` 를 병기했다 — 상세는 SKILL.md 4·5장.
>
> **수록 범위 — 전수 수록 아님**: 58개 항목 중 **47개 항목**의 예제만 수록한다 (46개 절 — 「무부호→부호 / 부호→무부호 변환」 절이 2개 항목 통합).
> **미수록 11개 항목**: 3 크로스사이트 스크립트 / 8 보호 메커니즘 우회 입력값 변조 / 11 LDAP 처리 / 20 부적절한 인가 /
> 23 중요정보 평문 저장·전송 / 30 솔트 없이 일방향 해쉬 / 40 오류 메시지 통한 정보 노출 / 46 정수를 문자로 변환 /
> 52 남은 디버그 코드 / 53 시스템 데이터 정보노출 / 54 DNS lookup에 의존한 보안결정.
> 이 중 상당수는 **원문에 예제가 실재하나 이 파일에 옮겨지지 않은 것**이다 — "이 파일에 없음 = 원문에 예제 없음"으로 답하지 마라.
> 미수록 항목의 정의·규칙·페이지는 `weakness-58.md` 참조, 예제 원문 확인은 원문 해당 페이지를 직접 참조.
> 진단 보고서에 기재할 기준번호(1~49)·CWE는 이 파일에 없다 — `secure-coding-kr/references/weakness-49.md` 총괄표(정본) 참조.

---

## 제1절 입력데이터 검증 및 표현

### SQL 삽입 (CWE-89, p.3)

❌ 안전하지 않은 코드 — C:

```c
#include <stdlib.h>
#include <sql.h>
void Sql_process(SQLHSTMT sqlh)
{
  char *query = getenv("query_string");
  SQLExecDirect(sqlh, query, SQL_NTS);
}
```

`name' OR 'a'='a` 입력 시 WHERE 절이 항상 참.

❌ 안전하지 않은 코드 — C (사례 2):

```c
char * command = GetParameter(queryStr, "command");
if (strcmp(command, GET_USER_INFO_CMD) == EQUAL)
{
  const char * userId   = GetParameter(queryStr, USER_ID_PARAM);
  const char * password = GetParameter(queryStr, PASSWORD_PARAM);
  char query[MAX_QUERY_LENGTH];
  sprintf(query, "SELECT * FROM members WHERE username= '%s' AND password = '%s'",
          userId, password);
  SQLExecDirect(statmentHandle, query, SQL_NTS);
}
```

✅ 안전한 코드 — C (발췌: 길이 제한 + 정규식 필터링):

```c
const char * makeSecureString(const char *str, int maxLength)
{
  char * buffer      = (char *) malloc(maxLength + 1);
  char * originalStr = (char *) malloc(maxLength + 1);
  strncpy(originalStr, str, maxLength);
  originalStr[maxLength] = NULL;
  regmatch_t mt;
  const char * currentPos = originalStr;

  while (regexec(&unsecurePattern, currentPos, 1, &mt, REG_NOTBOL) == 0)
  {
    strncat(buffer, currentPos, mt.rm_so);
    currentPos += mt.rm_eo;
  }
  strcat(buffer, currentPos);
  free(originalStr);
  return buffer;
}
```

정규식 `"[^[:alnum:]]|select|delete|update|insert|create|alter|drop"` (REG_ICASE)로 필터링,
`MAX_USER_ID_LENGTH`/`MAX_PASSWORD_LENGTH` 로 길이 제한.

> ⚠️ 현행 권고: 필터링·문자열 조립보다 **파라미터라이즈드 쿼리**(ODBC `SQLPrepare`+`SQLBindParameter`)가 1순위다. 원문 안전 예제의 `buffer`는 초기화 없이 `strncat` 되는 결함도 있다.

### 자원 삽입 (CWE-99, p.8)

❌ / ✅ — 외부 입력 포트를 그대로 사용 vs 범위 검사:

```c
int main()
{
  char* rPort = getenv("rPort");
  struct sockaddr_in serv_addr;
  int sockfd = 0;
  int port = 0;
  ...
  if(strcmp(rPort,"") < 0)
  {
    printf("bad input");
  }
  port = atoi(rPort);
  if( port < 3000 || port > 3003)
    port = 3000;

  serv_addr.sin_port = htons(atoi(rPort));
  if (connect(sockfd, &serv_addr ,sizeof(serv_addr)) < 0) {
    exit(1);
  }
  return 0;
}
```

(✅ 원문 안전 예제 — 허용 범위 3000~3003 화이트리스트. 취약 버전은 `htons(atoi(rPort))` 를 검증 없이 사용.)

### 운영체제 명령어 삽입 (CWE-78, p.15)

❌ 안전하지 않은 코드 — C (catWrapper: `Story.txt; ls` 전달 시 `ls` 실행):

```c
  fgets(arg,80,stdin);
  commandLength = strlen(cat) + strlen(arg) + 1;
  command = (char *) malloc(commandLength);
  strncpy(command, cat, commandLength);
  strncat(command, argv[1], (commandLength - strlen(cat)) );
  system(command);
  return 0;
```

✅ 안전한 코드 — C:

```c
  fgets(arg,80,stdin);
  if (strpbrk(arg,";\"'."))
  {
    exit(1);
  }
  commandLength = strlen(cat) + strlen(arg) + 1;
```

> ⚠️ 현행 권고: 원문의 `strpbrk(";\"'.")` 블랙리스트는 `|`, `&`, 백틱, `$()`, 개행 등을 놓친다.
> `system()` 자체를 쓰지 말고 `fork()`+`execv(절대경로, 인자배열)` + 허용목록 검증 (CERT C ENV33-C, SKILL.md 4.5).

### LDAP 삽입 (CWE-90, p.19)

❌ 외부 입력 필터를 그대로 사용:

```c
int main()
{
  char* filter = getenv("filter_string");
  int rc;
  LDAP *ld = NULL;
  LDAPMessage* result;
  rc = ldap_search_ext_s(ld, FIND_DN, LDAP_SCOPE_BASE, filter, NULL, 0,
                         NULL, NULL, LDAP_NO_LIMIT, LDAP_NO_LIMIT, &result);
  return 0;
}
```

✅ 상수 필터 사용: `char* filter = "(manager=admin)";`

### 디렉터리 경로 조작 (CWE-23/36, p.21·25)

❌ 상대 경로 조작 (`reportName` 에 `../../../etc/passwd` 입력 가능):

```c
void f()
{
  char* rName = getenv("reportName");
  char buf[30];
  strncpy(buf, "/home/www/tmp/", 30);
  strncat(buf, rName, 30);
  unlink(buf);
}
```

✅ 고정 파일명 사용:

```c
void f()
{
  char buf[30];
  strncpy(buf, "/home/www/tmp/", 30);
  strncat(buf, "report", 30);
  unlink(buf);
}
```

❌ 절대 경로 조작 / ✅ 고정 경로:

```c
void absolute()
{
  /* 외부입력값으로 파일 경로가 설정되고 있다 */
  char* rName = getenv("reportName");
  unlink(rName);
}
```

```c
void absolute()
{
  /* 외부입력값으로 파일 경로를 설정하지 않아야한다 */
  unlink("/home/www/tmp/report");
}
```

> ⚠️ 현행 권고: 외부 입력 경로가 불가피하면 `realpath()` 정규화 후 허용 베이스 디렉터리 접두사 확인 + `..` 성분 거부 (SKILL.md 4.6). 참고로 원문 예제의 `strncat(buf, rName, 30)` 은 n 의미를 잘못 사용한 패턴이기도 하다(잔여 공간이 아닌 전체 크기 전달).

### 정수 오버플로우 (CWE-190, p.29)

❌ 안전하지 않은 코드:

```c
#include <stdlib.h>
void* intAlloc(int size, int reserve)
{
  void *rptr;
  size += reserve;
  rptr = malloc(size * sizeof(int));
  if (rptr == NULL)
    exit(1);
  return rptr;
}
```

✅ 원문 안전 코드:

```c
#include <stdlib.h>
void* intAlloc(int size, int reserve)
{
  void *rptr;
  unsigned s;
  size += reserve;
  s = size * sizeof(int);
  if (s < 0)
    return NULL;
  rptr = malloc(s);
  if (rptr == NULL)
    exit(1);
  return rptr;
}
```

> ⚠️ 현행 권고: 원문 안전 예제 자체에 결함 — `unsigned s` 에 대한 `if (s < 0)` 는 항상 거짓이고 `size += reserve` 의 signed overflow(UB)도 남는다. `__builtin_add_overflow`/`__builtin_mul_overflow`(GCC·Clang) 또는 C23 `ckd_add`/`ckd_mul` 사용 (CERT C INT30-C/INT32-C, SKILL.md 4.2).

✅ 원문 안전 코드 (사례 2 — 곱셈·덧셈 전 사전 검사, `filedIndex` 는 [원문 오탈자]):

```c
  if((dataIndex < 0) || (dataIndex > Integer.MAX_VALUE / DATA_SIZE))
  {
    // Error
    return;
  }
  if((fieldIndex < 0) || (filedIndex > (Integer.MAX_VALUE - (dataIndex * DATA_SIZE))))
  {
    // Error
    return;
  }
  int index = dataIndex * DATA_SIZE + fieldIndex;
```

> ⚠️ 현행 권고: `Integer.MAX_VALUE` 는 Java 표기가 C 예제에 섞인 것(원문 그대로). C에서는 `INT_MAX`(`<limits.h>`) — 그리고 이 수동 검사 전체를 체크드 연산으로 대체하는 편이 안전하다.

### 스택에 할당된 버퍼 오버플로우 (CWE-121, p.40)

❌ 안전하지 않은 코드:

```c
void manipulate_string(char* string)
{
  char buf[24];
  strcpy(buf, string);
}
```

✅ 원문 안전 코드 (5행 괄호 위치는 원문 그대로 — [원문 오탈자]):

```c
void manipulate_string(char* string)
{
  char buf[24];
  /* 복사하려는 buf와 길이 비교를 한다. */
  if (strlen(string < sizeof(buf))
    strncpy(buf, string, sizeof(buf)-1);
  /* 문자열은 반드시 null로 종료되어야 함 */
  buf[sizeof(buf)-1] = '\0';
}
```

> ⚠️ 현행 권고: `strncpy` 는 널 종단 미보장 — 원문처럼 명시적 `buf[n-1]='\0'` 을 붙이면 원문 기준은 충족하나, `snprintf(buf, sizeof buf, "%s", string)` 또는 `strlcpy` 가 더 안전하고 간결하다 (CERT C STR32-C, SKILL.md 4.1).

❌ 사례 2 — 스택 배열 인덱스 무제한 증가 (`whle` 는 [원문 오탈자]):

```c
    int dataBuffer[MAX_DATA_BUFFER_LENGTH];
    int dataIndex = 0;
    const char * data = GetParameter(queryStr, DATA_PARAM);

    char * token = strtok(data, " ");
    whle(token != NULL)
    {
      dataBuffer[dataIndex] = atoi(token);
      token = strtok(NULL, " ");
      dataIndex++;
    }
```

✅ 사례 2 안전 코드 — 인덱스 상한 검사 추가:

```c
    char * token = strtok(data, " ");
    whle(token != NULL)
    {
      if(dataIndex >= MAX_DATA_BUFFER_LENGTH)
        break;
      dataBuffer[dataIndex] = atoi(token);
      token = strtok(NULL, " ");
      dataIndex++;
    }
```

### 힙에 할당된 버퍼 오버플로우 (CWE-122, p.44)

❌ / ✅:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define BUFSIZE 10
int main(char **argv)
{
  char *dest = NULL;
  dest = (char *)malloc(BUFSIZE);
  ……
  strcpy(dest, argv[1]);
  ……
  free(dest);
  return 0;
}
```

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define BUFSIZE 10
int main(int argc, char **argv)
{
  char *dest = NULL;
  dest = (char *)malloc(BUFSIZE);
  ……
  strlcpy(dest, argv[1], BUFSIZE);
  ……
  free(dest);
  return 0;
}
```

원문: "`strlcpy()` 함수는 문자 배열의 마지막 부분에 자동적으로 Null을 채워준다."

> ⚠️ 현행 권고: `strlcpy` 는 BSD/macOS 기본, glibc 2.38+ 제공(그 외 리눅스는 `-lbsd`). 이식성이 문제면 `snprintf(dest, BUFSIZE, "%s", argv[1])` (SKILL.md 2.1).

### 버퍼 시작 지점 이전에 쓰기 (CWE-124, p.57)

❌ / ✅:

```c
int main()
{
  int a[10];
  a[-1] = 0;
  return 0;
}
```

```c
int main()
{
  int a[10];
  a[0] = 0;
  return 0;
}
```

❌ 사례 2 — 인덱스 감소 루프:

```c
#include <stdio.h>
void inverseWordOrder(char * string)
{
  const int MAX_WORD_COUNT = 256;
  int wordIndex = MAX_WORD_COUNT - 1;
  char * words[MAX_WORD_COUNT];
  memset(words, NULL, MAX_WORD_COUNT * sizeof(int));
  char * token = strtok(string, " \t");
  while(token != NULL)
  {
    words[wordIndex] = token;
    token = strtok(NULL, " \t");
    wordIndex--;
  }
}
```

✅ 사례 2 안전 코드 (C++ vector 사용):

```cpp
#include <vector>
#include <stdio.h>
using namespace std;

void inverseWordOrder(char * string)
{
  const int MAX_WORD_COUNT = 256;
  vector<char *> words(MAX_WORD_COUNT, NULL);
  ...
}
```

> ⚠️ 현행 권고: `vector` 로 바꿔도 `operator[]` 는 경계 검사를 하지 않는다 — 인덱스 하한(`wordIndex >= 0`) 검사 또는 `at()` 사용이 본질적 수정이다. (또한 원문 ✅ 예제의 `using namespace std;` 는 본 프로젝트 컨벤션상 금지 패턴.)

### 범위 초과해서 읽기 (CWE-125, p.59)

❌ / ✅:

```c
int main()
{
  int a[3] = {1,2,3};
  int b = a[3];
  return 0;
}
```

```c
int main()
{
  int a[3] = {1,2,3};
  int b = a[2];
  return 0;
}
```

❌ 사례 2 — END_MARK 탐색 (배열에 END_MARK 가 없으면 out-of-bounds read):

```c
#include <stdio.h>
int readNextData(int * data_pool)
{
  static int curIdx = 0;
  int END_MARK = -1;
  // End mark 가 나올 때까지 인덱스를 증가시킨다
  if(data_pool[curIdx] != END_MARK)
  {
    curIdx++;
    return data_pool[curIdx];
  }
  return END_MARK;
}
```

✅ 사례 2: `int readNextData(int * data_pool, int size)` — 크기를 인자로 전달받아 범위 검사.

### 검사되지 않은 배열 인덱싱 (CWE-129, p.61)

❌ `sizes[num-1]` 에 무검증 인덱스:

```c
int getsizes(int sock, int count, int *sizes)
{
  char buf[BUFFER_SIZE];
  int ok;
  int num, size;

  while ((ok = gen_recv(sock, buf, sizeof(buf))) == 0)
  {
    if (hasDotInBuffer(buf))
      break;
    else if (sscanf(buf,"%d %d", &num, &size) == 2)
      sizes[num-1] = size;
  }
    ...
}
```

✅ 범위 검사 추가:

```c
int getsizes(int sock, unsigned int MAXCOUNT, int *sizes)
{
  char buf[BUFFER_SIZE];
  int ok;
  int num, size;

  while ((ok = gen_recv(sock, buf, sizeof(buf))) == 0)
  {
    if (hasDotInBuffer(buf)) break;
    // buf 로부터 num, size 값을 읽는다.
    if (sscanf(buf,"%d %d", &num, &size) == 2)
    {
      // num 값의 범위를 검사한다.
      if (num > 0 && num <= MAXCOUNT)
        sizes[num-1] = size;
      else { printf("..."); return(FAIL); }
    }
  }
  ...
}
```

### 널 종료 문제 (CWE-170, p.65)

❌ `read()` 결과에 `strcpy()`:

```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#define MAXLEN 1024
extern char *inputbuf;
extern int cfgfile;
void readstr()
{
  char buf[MAXLEN];
  read(cfgfile, inputbuf, MAXLEN);
  strcpy(buf, inputbuf);
}
```

✅ `strlcpy()` 사용:

```c
void readstr()
{
  char buf[MAXLEN];
  read(cfgfile, inputbuf, MAXLEN);
  strlcpy(buf, inputbuf, MAXLEN);
}
```

> ⚠️ 현행 권고: 근본 수정은 `read()` 의 **반환 바이트 수**를 받아 `inputbuf[n] = '\0'` 처리다 — `read` 는 널 종단을 절대 붙이지 않으며, MAXLEN 바이트를 다 채우면 `strlcpy` 도 원본에서 널을 찾지 못해 초과 읽기가 남는다.

❌ 사례 2 — `strncpy`/`strncat` 조합 (`GetLastNam` 은 [원문 오탈자]):

```c
  char * userId = GetRequestParameter(queryStr, ID_PARAM);
  const char * firstName = GetFirstName(userId);
  const char * lastName  = GetLastNam(userId);
  char fullName[MAX_NAME_LENGTH];
  strncpy(fullName, firstName, MAX_NAME_LENGTH);
  strncat(fullName," ", MAX_NAME_LENGTH - strlen(fullName));
  strncat(fullName, lastName, MAX_NAME_LENGTH - strlen(fullName));
```

두 이름의 합이 `MAX_NAME_LENGTH` 초과 시 널 종단 미보장.

> ⚠️ 현행 권고: `snprintf(fullName, sizeof fullName, "%s %s", firstName, lastName)` 한 줄로 대체 — 항상 널 종단, 반환값으로 절단 검출.

### 의도하지 않은 부호 확장 (CWE-194, p.69)

❌ / ✅:

```c
extern int info[256];
int signed_overflow(int id)
{
  short s;
  unsigned sz;
  /* int형 변수값을 short형 변수에 저장함으로써 오버플로우 발생 */
  s = id;
  if (s > 256) return 0;
  /* 위의 값을 unsigned형 변수에 저장함으로써 부호 확장 발생 */
  sz = s;
  return info[sz];
}
```

```c
extern int info[256];
int signed_overflow(int id)
{
  int s;
  unsigned sz;
  s = id;
  if (s > 256 || s < 0)
    return 0;
  sz = (unsigned) s;
  return info[sz];
}
```

> ⚠️ 현행 권고: 원문 ✅ 예제도 상한이 `> 256` 이라 `id == 256` 이 통과 — `info[256]` 은 out-of-bounds (유효 인덱스 0~255). `>= 256` 이어야 한다.

### 무부호→부호 / 부호→무부호 변환 (CWE-196 p.73 / CWE-195 p.169)

❌ `-1` 반환이 `unsigned` 로 해석:

```c
int chunkSz()
{
  if (!initialized) return -1;
  return chunkSize;
}
void* chunkCpy(void *dBuf, void *sBuf)
{
  unsigned size;
  size = chunkSz();
  return memcpy(dBuf, sBuf, size);
}
```

✅ signed 로 받고 음수 검사 후 캐스팅:

```c
void* chunkCpy(void *dBuf, void *sBuf)
{
  int size;
  size = chunkSz();
  if (size < 0) return NULL;
  return memcpy(dBuf, sBuf, (unsigned)size);
}
```

❌ CWE-195 (p.169) — `len()` 이 NULL 입력 시 `return -1;` 을 `unsigned int` 로 반환 → `0xffffffff`:

```c
unsigned int len(char *s)
{
  unsigned int l = 0;
  if (s == NULL)
  {
    return -1;
  }
  l = strnlen(s, BUFSIZE-1);
  return l;
}
```

### 프로세스 제어 (CWE-114, p.53)

❌ / ✅:

```c
  filename = getenv("SHAREDFILE");
  if ((handle = dlopen(filename, RTLD_LAZY)) != NULL)
  {
    exit(1);
  }
```

```c
  /* 절대경로 지정을 통해 해당 경로에서만 라이브러리를 찾음*/
  filename = "/usr/lib/hello.so";
  if ((handle = dlopen(filename, RTLD_LAZY)) != NULL);
  {
    ...
  }
```

(✅ 예제의 `if (...) ;` 세미콜론은 원문 그대로 — [원문 오탈자] 성격의 결함.)

### 시스템 설정의 외부 제어 (CWE-15, p.50)

```c
main(int argc, char *argv[])
{
  sethostid(atol(argv[1]));   /* ❌ */
}
```

```c
main(int argc, char *argv[])
{
  sethostid(0xC0A80101);      /* ✅ */
}
```

---

## 제2절 보안기능

### 중요한 자원에 대한 잘못된 권한허용 (CWE-732, p.82)

❌ / ✅:

```c
// 파일 권한 : rw-rw-rw-, 디렉터리 권한 : rwxrwxrwx
umask(0);
FILE *out = fopen("important_file", "w");
```

```c
umask(077); // 파일 권한 : rw-------, 디렉터리 권한 : rwx------
FILE *out = fopen("important_file", "w");
```

### 취약한 암호화 알고리즘 사용 (CWE-327, p.84~86)

❌ (원문 p.86 발췌 — 원문은 이 항목에서 AES-128-CBC 초기화 코드를 예시 문맥으로 수록):

```c
EVP_CIPHER_CTX ctx;
EVP_CIPHER_CTX_init(&ctx);
EVP_EncryptInit(&ctx, EVP_aes_128_cbc(), key, iv);
```

원문 권고: RC2/RC4/RC5/RC6/MD4/MD5/SHA1/DES 대신 **3-DES, AES, SEED** 사용. 검증필 암호모듈 사용.

> ⚠️ 현행 권고: **3DES는 현행 기술 기준 부적합** (NIST SP 800-131A Rev.2 — **2023년 말 이후** 암호화 용도 disallowed, Sweet32) — 단 제도(KISA 안내서 2018)에는 3DES 금지 목록이 없으므로 지적 근거는 NIST를 인용하라. **SHA-1은 용도별 판정** — 단순해시·전자서명만 제도상 부적합, 메시지인증(HMAC-SHA1)·키유도·난수생성은 허용(일괄 지적은 과잉, 신규 설계는 SHA-256 이상 권장). AES-GCM 또는 ARIA/SEED/LEA + AEAD 구성. CBC 단독 사용 시 패딩 오라클 위험 — `crypto-policy-kr` 스킬 2항 참조.

### 하드코드된 패스워드 (CWE-259, p.93)

❌:

```c
  /* 패스워드가 "asdf"로 하드코딩 되어있다.*/
  SQLConnect(hdbc, (SQLCHAR*) server, strlen(server), user, strlen(user), "asdf", 4);
```

### 충분하지 않은 키 길이 (CWE-310, p.96)

❌:

```c
  /* 키값이 512bit로 너무 짧다 */
  rsa = RSA_generate_key(512, 35, NULL, NULL);
```

> ⚠️ 현행 권고: RSA 2048비트 이상(장기 3072). `RSA_generate_key()` 는 OpenSSL 3.0 deprecated — `EVP_PKEY_Q_keygen(NULL, NULL, "RSA", 3072)` 등 EVP API. 공개지수 35 같은 비표준 값 대신 65537.

### 적절하지 않은 난수 (CWE-330, p.99)

❌ 상수 seed:

```c
  /* srand()에서 상수 형태의 seed를 사용하고 있다.*/
  srand( 100 );
  ...
  temp = rand()%101;
```

> ⚠️ 현행 권고: 원문 권고("랜덤 seed 변경")로는 불충분 — `rand()` 는 seed 와 무관하게 예측 가능하므로 보안 용도 금지 (CERT C MSC30-C). `getrandom(2)` / `/dev/urandom` / OpenSSL `RAND_bytes()` 사용 (SKILL.md 4.8).

### 패스워드 평문 저장 (CWE-256, p.102)

❌ (발췌):

```c
  fp = fopen("config", "r");
  fgets(user, sizeof(user), fp);
  fgets(passwd, sizeof(passwd), fp);
  fclose(fp);
  ...
  SQLConnect(hdbc, ..., /* 파일로부터 패스워드를 평문으로 읽어들이고 있다 */ (SQLCHAR*) passwd, ...);
```

### 하드코드된 암호화 키 (CWE-321, p.107)

❌:

```c
  cpasswd = crypt(passwd, salt);

  /* 암호화 키가 소스코드내에 상수로 하드코드 되어 있다 */
  if (strcmp(cpasswd, "68af404b513073582b6c63e6b") != 0)
  {
    printf("Incorrect password\n");
    return -1;
  }
```

### 주석문 안의 패스워드 (CWE-615, p.111)

❌:

```c
/* default password is "abracadabra".   주석문안에 패스워드가 포함되어있다 */
int verifyAuth(char *ipasswd, char *orgpasswd)
{
  char* admin="admin";
  if (strncmp(ipasswd, orgpasswd, sizeof(ipasswd)) != 0)
  {
    printf("Authetication Fail!\n");
  }
  return admin;
}
```

(참고: 이 예제의 `sizeof(ipasswd)` 는 포인터 크기(4/8)만 비교하는 별도 결함, `Authetication` 은 [원문 오탈자].)

### 하드코드된 사용자 계정 (CWE-255, p.120)

❌:

```c
  SQLConnect(hdbc,
             (SQLCHAR*) server,
             (SQLSMALLINT) strlen(server),
             /*사용자 이름을 코드에 상수로 사용하는 경우*/
             "root",
             4,
             passwd,
             strlen(passwd));
```

### 잘못된 권한 부여 (CWE-266, p.124)

❌ (원문 예제 — `seteuid(0)` 상승 후 복귀 패턴 자체는 제시되어 있으나 상승 자체가 문제인 예):

```c
char *privilegeUp()
{
  FILE *fp;
  /* 사용자 UID 생성 */
  seteuid(0);
  fp = fopen("/etc/passwd", "r");
  fgets(buf, sizeof(buf), fp);
  /* 현재 프로세스의 유효 사용자 UID를 획득 */
  seteuid(getuid());
  fclose(fp);
  return buf;
}
```

### 최소 권한 적용 위배 (CWE-272, p.128)

❌ (`AAP_HOME` 정의 vs `APP_HOME` 사용 불일치는 [원문 오탈자]):

```c
#define AAP_HOME "/var/tmp"
char buf[100];
char *privilegeDown()
{
  FILE *fp;
  /* root 권한을 주고 작업이 끝나도 원래대로 복귀시키지 않았다 */
  chroot(APP_HOME);
  chdir("/");
  fopen("important_file", "r");
  fgets(buf, sizeof(buf), fp);
  fclose(fp);
  return buf;
}
```

원문: "`chroot()` 함수 사용 직후에 `seteuid()` 를 호출해서 원래 사용자 권한으로 복귀."

> ⚠️ 현행 권고: 권한 드롭은 `setgroups()` → `setgid()` → `setuid()` 순서 + 드롭 성공 검증 (CERT C POS36-C/POS37-C, SKILL.md 4.7).

### 부적절한 RSA 패딩 (CWE-325, p.132)

❌ / ✅:

```c
  /* RSA함수에서 NO_PADDING과 같이 적절하지 않은 파라미터를 사용하는 경우*/
  RSA_public_encrypt(size, text, out, rsa_p, RSA_NO_PADDING);
```

```c
  RSA_public_encrypt(size, text, out, rsa_p, RSA_PKCS1_OAEP_PADDING);
```

### 하드코드된 솔트 (CWE-326, p.134)

❌ / ✅:

```c
  /* salt값으로 상수를 사용하고 있다 */
  out = (char*) crypt(text, "xp");
```

```c
void hardSalt(const char *text, const char *os)
{
  char *out;
  out = (char *) crypt(text, os);
}
```

원문: salt 는 예측 어려운 난수로 매번 새로 생성.

> ⚠️ 현행 권고: `crypt()` 자체가 DES 기반 레거시 — 패스워드 저장은 Argon2id/bcrypt/scrypt 등 KDF (`crypto-policy-kr` 3항).

### 같은 포트번호로의 다중 연결 (CWE-605, p.138)

❌:

```c
  optval = 1;
  setsockopt(server_sockfd, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof optval);
  server_address.sin_family = AF_INET;
  server_address.sin_port = 21;
  server_address.sin_addr.s_addr = htonl(INADDR_ANY);
  /* 소켓 옵션 SO_REUSEADDR과 서버 주소값 INADDR_ANY을 동시에 사용 */
  bind(server_sockfd, (struct sockaddr *) &server_address, server_len);
```

---

## 제3절 시간 및 상태

### TOCTOU 경쟁 조건 (CWE-367, p.140)

✅ mutex 로 임계영역 보호:

```c
int handle_mutex(pthread_mutex_t *mutex)
{
  int result;
  // mutex 를 사용해 임계영역을 보호한다
  result = pthread_mutex_lock(mutex);
  if (0 != result)
    return result;
  /* 임계영역 처리 */
  return pthread_mutex_unlock(mutex);
}
```

### 제어되지 않은 재귀 (CWE-674, p.147)

❌ / ✅ / ✅ 사례 2:

```c
int fac(n)
{
  return n*fac(n-1);
}
```

```c
int fac(n)
{
  if (n <= 0) return 1;
  else return n*fac(n-1);
}
```

```c
int i=0;
int fac(n)
{
  if (n <= 0)
    return 1;
  else
  {
    if(i>10000) exit(1);
    else i+=1;
    return n*fac(n-1);
  }
}
```

### 심볼릭명 매핑 (CWE-386, p.149)

❌ `access()` 검사와 `fopen()` 사용 사이 심볼릭 링크 교체 가능:

```c
  if(!access(file,W_OK))
  {
    f = fopen(file,"w+");
    operate(f);
  }
  else
  {
    fprintf(stderr,"Unable to open file %s.\n",file);
  }
```

> ⚠️ 현행 권고: `open(path, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600)` + fd 기반 `fstat` — 파일명 재검사 금지 (CERT C FIO45-C, SKILL.md 4.6).

---

## 제4절 에러 처리

### 오류상황 대응 부재 (CWE-390, p.156)

❌:

```c
        /* FLAW: check the return value, but do nothing if there is an error */
        if (fputs("string", stdout) == EOF)
        {
            /* do nothing */
        }
```

### 적절하지 않은 예외처리 (CWE-754, p.159)

❌ / ✅:

```c
char fromBuf[10], toBuf[10];
fgets(fromBuf, 10, stdin);
strcpy(toBuf, fromBuf);
```

```c
char fromBuf[10], toBuf[10];
char *retBuf = fgets(fromBuf, 10, stdin);
// 함수호출 이후 결과 값을 비교한다.
if ( retBuf != fromBuf )
{
    println("에러");
    return;
}
strcpy(toBuf, fromBuf);
```

(✅ 예제의 `println` 은 C 표준에 없는 함수 — 원문 그대로.)

---

## 제5절 코드 오류

### 널 포인터 역참조 (CWE-476, p.162)

❌ (`cig_home` 은 [원문 오탈자]):

```c
int main()
{
  char *p = NULL;
  char cgi_home[BUFSIZE];
  p = getenv("CGI_HOME");
  strncpy(cgi_home, p, BUFSIZE-1);
  cig_home[BUFSIZE-1] = '\0';
  return 0;
}
```

원문: `getenv()` 반환값이 NULL 인지 검사 후 사용.

### 부적절한 자원 해제 (CWE-404, p.165)

❌ / ✅ (소켓·SQL 핸들 해제 누락 → 쌍 맞춤):

```c
void sqlDB()
{
  SQLHANDLE env_hd, con_hd;
  SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env_hd);
  SQLAllocHandle(SQL_HANDLE_DBC, env_hd, &con_hd);
}
```

```c
void sqlDB()
{
  SQLHANDLE env_hd, con_hd;
  SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env_hd);
  SQLAllocHandle(SQL_HANDLE_DBC, env_hd, &con_hd);
  SQLFreeHandle(SQL_HANDLE_DBC, con_hd);
  SQLFreeHandle(SQL_HANDLE_ENV, env_hd);
}
```

✅ 사례 2 — `fork()` 실패 경로 포함 소켓 해제:

```c
    switch(fork())
    {
    case 0:
      listenSocket = -1;
      comminucation();
      break;
    case -1:  // error case
      break;
    default:
      connectionSocket = -1;
    }
  }

  // 사용이 끝난 socket 을 close 한다
  if(listenSocket != -1)
  {
    close(listenSocket);
  }
  if(connectionSocket != -1)
  {
    close(connectionSocket);
  }
```

(`comminucation` 은 [원문 오탈자].)

### 스택 변수 주소 리턴 (CWE-562, p.175)

❌ / ✅:

```c
char *rpl()
{
  char p[10];
  /* 로컬 버퍼의 주소를 반환함 */
  return p;
}
```

```c
char *rpl()
{
  char p[10];
  int size = 10;
  if( size < 20 )
  {
    /* 메모리를 할당하고, 그 주소를 리턴하도록 메모리 영역을 변경 */
    char *buf = (char *)malloc(size);
    if (!buf)
      exit(1);
    memcpy(buf,p,10);
  }
  return buf;
}
```

(✅ 예제의 `buf` 는 if 블록 내부 선언인데 밖에서 return — 원문 그대로의 스코프 결함. 실사용 시 함수 첫머리에 선언할 것.)

### 매크로의 잘못된 사용 (CWE-730, p.178)

❌ `pthread_cleanup_push` 만 있고 `pop` 없음:

```c
void helper()
{
  int a = 0;
  pthread_cleanup_push (routine, ((void*)&a));
}
```

### 스택 주소 해제 (CWE-730, p.180)

❌ / ✅ (원문의 `#include stdlib.h` 표기는 원문 그대로 — [원문 오탈자]):

```c
#include stdlib.h
int main()
{
  char p[10];
  /* 지역변수내에 배열에 대한 메모리 해제 */
  free(p);
  return 0;
}
```

```c
#include stdlib.h
int main()
{
  char p[10];
  return 0;
}
```

❌ / ✅ 사례 2 — `strtok()` 반환값 `free()`:

```c
int main ()
{
  char str[] ="- This, a sample string.";
  char * pch;
  printf ("Splitting string \"%s\" into tokens:\n",str);
  pch = strtok (str," ,.-");
  free(pch);
  while (pch != NULL)
  {
    printf ("%s\n",pch);
    pch = strtok (NULL, " ,.-");
    free(pch);
  }
  return 0;
}
```

```c
int main ()
{
  char str[] ="- This, a sample string.";
  char * pch;
  printf ("Splitting string \"%s\" into tokens:\n",str);
  pch = strtok (str," ,.-");
  while (pch != NULL)
  {
    printf ("%s\n",pch);
    pch = strtok (NULL, " ,.-");
  }
  return 0;
}
```

### 스레드 조기 종료 (CWE-730, p.182)

❌ 자식 스레드를 기다리지 않고 반환:

```c
int run_thread1(void)
{
  pthread_t th;
  int status, a = 1;
  if (pthread_create(&th, NULL, (void*(*)(void*))th_worker, (void *)&a) < 0)
  {
    perror("thread create error: ");
    exit(0);
  }
  printf("Return without waiting for child thread\n");
  return 0;
}
```

원문: `pthread_join()` 으로 대기하거나 `pthread_detach()` 로 분리.

### 무한 자원 할당 (CWE-770, p.185)

❌ / ✅:

```c
int processMessage(char **message)
{
  char *body;
  int length = getMessageLength(message[0]);
  if (length > 0)
  {
    body = &message[1][0];
    processMessageBody(body);
  }
  else {......}
}
```

```c
int processMessage(char **message)
{
  char *body;
  unsigned int length = getMessageLength(message[0]);
  // 자원 고갈을 방지위해 사용자의 자원을 제한한다.
  if (length > 0 && length < MAX_LENGTH)
  {
    body = &message[1][0];
    ...
  }
}
```

✅ 사례 2 — Thread Pool (`accpet` 은 [원문 오탈자]):

```c
  listenSocket = socket(AF_INET_SOCK_STREAM, 0);
  ...
  while(TRUE)
  {
    connectionSocket = accpet(listenSocket, (struct sockaddr *) &cli_addr, &clilen);
    // Thread pool 에서 thread 를 할당받는다.
    if(threadPool.alloc(communication, &connectionSocket) == TRUE)
    {
      connectionSocket = -1;
    }
    else
    {
      close(connectionSocket);
    }
  }
```

---

## 제7절 API 오용

### 위험하다고 알려진 함수 (CWE-242, p.196)

❌ / ✅:

```c
#define BUFSIZE 100
void requestString()
{
  char buf[BUFSIZE];
  gets(buf);
}
```

```c
#define BUFSIZE 100
void requestString()
{
  char buf[BUFSIZE];
  /* buf 할당된 메모리 이내에서만 문자들을 입력 받음*/
  fgets(buf, BUFSIZE, stdin);
}
```

> ⚠️ 현행 권고: `gets()` 는 C11에서 표준에서 **제거**되었다 — 발견 즉시 지적 대상.

❌ / ✅ 사례 2 — `vfork()` → `fork()`:

```c
pid_t pid = vfork();
if (pid == 0) /* child */
{
  if (execve(filename, NULL, NULL) == -1)
  {
      /* Handle error */
  }
  _exit(1); /* in case execve() fails */
}
```

```c
pid_t pid = fork();
if (pid == 0) /* child */
{
  if (execve(filename, NULL, NULL) == -1)
  {
      /* Handle error */
  }
  _exit(1); /* in case execve() fails */
}
```

### chroot Jail (CWE-243, p.198)

❌ `chdir("/")` 누락 — 클라이언트가 `../../etc/passwd` 접근 가능:

```c
void changeRoot(FILE *network)
{
  FILE *localfile;
  char filename[80], buf[80];
  int len;

  chroot("/var/ftproot");

  fgets(filename, sizeof(filename), network);
  localfile = fopen(filename, "r");
  while ((len = fread(buf, 1, sizeof(buf), localfile)) != EOF)
  {
    fwrite(buf, 1, sizeof(buf), network);
  }
  fclose(localfile);
}
```

### 문자열 관리 오용 (CWE-251, p.202)

❌ / ✅:

```c
#include <mbstring.h>
void changeString(char *str1, char *str2)
{
  _mbscpy(str1, str2);
}
```

```c
#include <mbstring.h>
void changeString(char *str1, char *str2, unsigned size)
{
  _mbscpy_s(str1, size, str2);
}
```

> ⚠️ 현행 권고: `_s` 계열(Annex K)은 사실상 MSVC 전용 — glibc 미구현. 크로스플랫폼 코드는 `snprintf`/`strlcpy` 계열 사용 (SKILL.md 2.1).

### getlogin() (CWE-558, p.205)

❌ / ✅:

```c
int loginproc()
{
  struct passwd *pwd = getpwnam(getlogin());
  if (isTrustedGroup(pwd->pw_gid))
    return 1;  // allow
  else
    return 0;  // deny
}
```

```c
#define MAX 100
int loginproc()
{
  char id[MAX];
  struct passwd *pwd;
  if (getlogin_r(id, MAX) != 0)
    return 0;
  pwd = getpwnam(id);
  if (isTrustedGroup(pwd->pw_gid))
    return 1;  // allow
  else
    return 0;  // deny
}
```

✅ 사례 2:

```c
void downloadVipAccountInfos()
{
 const int MAX_USER_ID_LENGTH = 32;
 char userId[MAX_USER_ID_LENGTH];
 if(getlogin_r(userId, MAX_USER_ID_LENGTH - 1) != 0)
 {
  // Error
  ...
 }
}
```
