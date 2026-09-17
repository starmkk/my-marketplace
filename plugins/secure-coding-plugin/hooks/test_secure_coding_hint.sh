#!/usr/bin/env bash
# secure_coding_hint.py 동작 검증 — 탐지/오탐/병합/계약(항상 exit 0) 케이스.
# 선례 test_serena_first.sh 의 check() 방식을 따르되, 선례가 검증하지 않던
# 종료코드를 모든 케이스에서 단언한다 — "항상 exit 0"이 이 훅의 핵심 계약이다.
HOOK="$(cd "$(dirname "$0")" && pwd)/secure_coding_hint.py"
export PYTHONDONTWRITEBYTECODE=1   # 케이스 9 의 import 가 hooks/__pycache__ 를 만들지 않게
fail=0

# check <설명> <stdin JSON> <expect(yes|no)> : systemMessage 유무 + exit 0 단언
check() {
  local desc="$1" input="$2" expect="$3"
  local out rc has_msg="no"
  out=$(printf '%s' "$input" | python3 "$HOOK" 2>/dev/null)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL  $desc (exit=$rc — 훅은 모든 경로에서 exit 0 이어야 함)"
    fail=1
    return
  fi
  if echo "$out" | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("systemMessage") else 1)' 2>/dev/null; then
    has_msg="yes"
  fi
  if [ "$has_msg" = "$expect" ]; then
    echo "PASS  $desc"
  else
    echo "FAIL  $desc (expected warn=$expect, got warn=$has_msg)"
    fail=1
  fi
}

# count_in_msg <stdin JSON> <문자열> : systemMessage 안 등장 횟수 출력 (병합 검증용)
count_in_msg() {
  printf '%s' "$1" | python3 "$HOOK" 2>/dev/null \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("systemMessage","").count(sys.argv[1]))' "$2"
}

# ── 1. 정상 탐지 — 패턴별 1케이스 (Write 경로) ──────────────────────────────
check "WebView 탐지 (Write)"      '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/Web.java","content":"webView.addJavascriptInterface(bridge, \"app\");"}}' yes
check "생체인증 탐지"             '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/Auth.kt","content":"val prompt = BiometricPrompt(activity, executor, callback)"}}' yes
check "인증서 피닝·TLS 탐지"      '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/Net.kt","content":"val pinner = CertificatePinner.Builder().build()"}}' yes
check "JWT 탐지"                  '{"tool_name":"Write","tool_input":{"file_path":"/srv/src/main/java/Token.java","content":"import io.jsonwebtoken.Jwts;"}}' yes
check "OAuth·OIDC 탐지"           '{"tool_name":"Write","tool_input":{"file_path":"/web/src/auth/oauth.ts","content":"params.set(\"code_verifier\", verifier);"}}' yes
check "브라우저 보안 헤더 탐지"   '{"tool_name":"Write","tool_input":{"file_path":"/web/src/server.js","content":"res.setHeader(\"Content-Security-Policy\", csp);"}}' yes

# ── 2. Edit 경로 탐지 — 입력 필드가 다르다 (content vs new_string) ───────────
check "Edit new_string 탐지"      '{"tool_name":"Edit","tool_input":{"file_path":"/app/src/main/java/Tls.java","old_string":"// TODO","new_string":"TrustManager[] tm = buildTrustManagers();"}}' yes
check "Edit old_string 만은 무경고" '{"tool_name":"Edit","tool_input":{"file_path":"/app/src/main/java/Tls.java","old_string":"TrustManager[] tm;","new_string":"// removed"}}' no

# ── 3. ⭐ .md 안 탐지 문자열 → 무경고 — 이 저장소에서 매일 발생하는 시나리오 ──
check ".md 내 취약 예시 무경고"   '{"tool_name":"Write","tool_input":{"file_path":"/repo/plugins/secure-coding-plugin/skills/owasp-masvs/SKILL.md","content":"| addJavascriptInterface | MASWE-0034 |\nBiometricPrompt 도 다룬다"}}' no

# ── 4. 테스트·샘플 경로 제외 ─────────────────────────────────────────────────
check "src/test/ 경로 무경고"     '{"tool_name":"Write","tool_input":{"file_path":"/app/src/test/java/WebTest.java","content":"webView.addJavascriptInterface(bridge, \"app\");"}}' no
check "_test. 파일 무경고"        '{"tool_name":"Write","tool_input":{"file_path":"/web/src/oauth_test.ts","content":"params.set(\"code_verifier\", v);"}}' no
check "androidTest/ 경로 무경고"  '{"tool_name":"Edit","tool_input":{"file_path":"/app/src/androidTest/java/A.kt","old_string":"x","new_string":"BiometricPrompt(a, e, c)"}}' no

# ── 5. 행 선두 주석 제외 ─────────────────────────────────────────────────────
check "// 주석행 무경고"          '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/W.java","content":"// addJavascriptInterface 는 위험하다\nint x = 1;"}}' no
check "* 블록주석행 무경고"       '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/W.java","content":" * setJavaScriptEnabled 주의\nint x = 1;"}}' no
check "주석+실코드 혼재는 경고"   '{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/W.java","content":"// 아래는 실코드\nweb.setJavaScriptEnabled(true);"}}' yes

# ── 6. 다중 패턴 동시 매칭 → 메시지 1개 병합 ─────────────────────────────────
MULTI='{"tool_name":"Write","tool_input":{"file_path":"/app/src/main/java/Multi.kt","content":"web.addJavascriptInterface(b, \"a\")\nval p = BiometricPrompt(a, e, c)"}}'
check "다중 매칭도 경고"          "$MULTI" yes
headers=$(count_in_msg "$MULTI" "시큐어코딩 점검 힌트")
entries=$(count_in_msg "$MULTI" "스킬 · ")
if [ "$headers" = "1" ] && [ "$entries" = "2" ]; then
  echo "PASS  다중 매칭 병합 (헤더 1개 · 엔트리 2개)"
else
  echo "FAIL  다중 매칭 병합 (expected 헤더 1·엔트리 2, got 헤더 $headers·엔트리 $entries)"
  fail=1
fi

# ── 7. 필드 누락 → 무경고 + exit 0 ──────────────────────────────────────────
check "tool_input 없음 무경고"    '{"tool_name":"Write"}' no
check "file_path 없음 무경고"     '{"tool_name":"Write","tool_input":{"content":"addJavascriptInterface"}}' no
check "content 없음 무경고"       '{"tool_name":"Write","tool_input":{"file_path":"/a/b/Main.java"}}' no
check "비대상 도구 무경고"        '{"tool_name":"Read","tool_input":{"file_path":"/a/Main.java"}}' no
check "빈 입력 무경고"            '{}' no

# ── 8. JSON 파싱 실패 → 무경고 + exit 0 ─────────────────────────────────────
check "JSON 파싱 실패 안전 종료"  'not-a-json' no

# ── 8-1. 타입 오류 입력 → 무경고 + exit 0 (가드 한 줄을 지워도 초록이면 안 된다) ──
check "tool_input 이 문자열"      '{"tool_name":"Write","tool_input":"addJavascriptInterface"}' no
check "file_path 가 숫자"         '{"tool_name":"Write","tool_input":{"file_path":123,"content":"addJavascriptInterface"}}' no
check "content 가 객체"           '{"tool_name":"Write","tool_input":{"file_path":"/a/B.java","content":{"x":1}}}' no
check "최상위가 배열"             '[]' no
check "file_path 가 빈 문자열"    '{"tool_name":"Write","tool_input":{"file_path":"","content":"addJavascriptInterface"}}' no

# ── 8-2. 화이트리스트 밖 확장자 → 무경고 ────────────────────────────────────
#  ⭐ .swift 케이스가 "iOS 는 제외 코드가 아니라 화이트리스트 미포함" 이라는
#     동결 결정을 테스트로 고정한다. iOS 를 지원하게 되면 이 케이스가 빨개진다.
check ".swift 무경고 (iOS 미포함)" '{"tool_name":"Write","tool_input":{"file_path":"/ios/Auth.swift","content":"let ctx = LAContext(); CertificatePinner()"}}' no
check ".py 무경고"                 '{"tool_name":"Write","tool_input":{"file_path":"/srv/app.py","content":"CSP = \"Content-Security-Policy\""}}' no

# ── 9. 순수 함수 단언 — 셸을 거치지 않고 build_message 를 직접 검증 ──────────
# pure_check <설명> <python 본문> : 본문이 exit 0 이면 PASS
# ⚠️ 본문은 셸 큰따옴표 안에서 확장된다 — `$`·백틱·큰따옴표를 쓰지 말 것
#    (작은따옴표만 사용). 셸이 먼저 치환해 버리면 실패가 아니라 "거짓 통과"가 된다.
pure_check() {
  local desc="$1" body="$2"
  if python3 -c "
import sys
sys.path.insert(0, '${HOOK%/*}')
import re
from secure_coding_hint import build_message, PatternEntry, PATTERNS, MAX_ENTRIES
# E() 는 build_message 전용 합성 엔트리다 — build_message 가 pattern 필드를 읽지
# 않으므로 더미로 둔다. find_matches 를 여기서 테스트하게 되면 더미가 검증을
# 무의미하게 만드니 그때는 실제 정규식을 넘길 것.
# 키워드 인자로 넘기는 이유: 위치 인자면 필드 '순서'가 바뀔 때 조용히 어긋난
# 엔트리를 만든다 — M1 이 entry[2] 를 걷어낸 것과 같은 종류의 결합이다.
def E(name, skill, ids, domestic):
    return PatternEntry(name=name, pattern=re.compile('x'),
                        skill=skill, ids=ids, domestic=domestic)
def synth(n):
    return [E('N' + str(i), 'owasp-asvs', 'ID' + str(i), '미기재') for i in range(n)]
$body
"; then
    echo "PASS  $desc"
  else
    echo "FAIL  $desc"
    fail=1
  fi
}

# 9-1. "대응" 분기 — 현 테이블은 전부 미기재라 합성 입력으로만 검증 가능
pure_check "템플릿 국내대응 분기" "
msg = build_message([E('X', 'secure-coding-java', 'ID-1', '대응')])
assert '국내 기준 대응 항목' in msg, msg
assert '구속력 없음' not in msg, msg
"

# 9-2. ⭐ 동결 결정 '메시지에 스킬 절 번호 금지' 를 기계로 고정
pure_check "메시지에 절 번호(§) 없음" "
msg = build_message(list(PATTERNS))
assert '§' not in msg, msg
"

# 9-3. ⭐ 동결 결정 '5줄 이내' 를 기계로 고정 — 상한 초과 입력에서도 유지
#  입력을 실물 PATTERNS 가 아니라 합성으로 만드는 이유: 테이블은 '좁게 시작해
#  관찰 후 조정'하는 대상이라, 실물에 묶으면 패턴을 덜어냈다는 이유만으로 이
#  테스트가 빨개진다. 그때 고쳐지는 건 코드가 아니라 단언이고, 그 과정에서
#  5줄 상한이 함께 느슨해진다 — 동결을 고정하려던 목적이 뒤집히는 자리다.
pure_check "메시지 5줄 상한 (상한 초과)" "
msg = build_message(synth(MAX_ENTRIES + 1))
n = len(msg.splitlines())
assert n <= 5, str(n) + '줄: ' + msg
assert '외 1건 더 매칭됨' in msg, msg
"

pure_check "메시지 5줄 상한 (대량 매칭)" "
msg = build_message(synth(20))
n = len(msg.splitlines())
assert n <= 5, str(n) + '줄: ' + msg
assert '외 17건 더 매칭됨' in msg, msg
"

# 9-4. 정확히 상한일 때는 접기 문구가 붙지 않는다
#  기대값을 MAX_ENTRIES 로 계산하지 않고 5 로 고정한다 — 구현 상수에서 끌어오면
#  MAX_ENTRIES 가 4로 올라가 6줄이 돼도 이 단언 혼자서는 빨개지지 않는다.
pure_check "상한 이하는 접기 문구 없음" "
msg = build_message(synth(MAX_ENTRIES))
assert len(msg.splitlines()) <= 5, msg
assert '건 더 매칭됨' not in msg, msg
"

# 9-5. 매칭 0건이면 main() 이 막지만, 템플릿 자체도 줄 수를 넘기지 않는다
pure_check "0건 입력도 상한 이내" "
assert len(build_message([]).splitlines()) <= 5
"

exit $fail
