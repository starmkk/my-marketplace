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

# ── 9. 메시지 템플릿 "대응" 분기 — 현 테이블은 전부 미기재라 순수 함수로 검증 ──
if python3 -c "
import sys
sys.path.insert(0, '${HOOK%/*}')
from secure_coding_hint import build_message
msg = build_message([('X', 'secure-coding-java', 'ID-1', '대응')])
sys.exit(0 if ('국내 기준 대응 항목' in msg and '구속력 없음' not in msg) else 1)
" 2>/dev/null; then
  echo "PASS  템플릿 국내대응 분기"
else
  echo "FAIL  템플릿 국내대응 분기"
  fail=1
fi

exit $fail
