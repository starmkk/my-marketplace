#!/usr/bin/env bash
# serena_first.py 동작 검증 — 경고 대상/비대상 · 타입 가드 · 2채널 출력 · 계약 케이스.
# 훅 프로세스의 종료코드를 **모든 케이스에서** 단언한다 — "모든 경로에서 exit 0"이
# 이 훅의 핵심 계약이고, 이 단언이 없던 판본에서 타입 오류 입력 2종이 exit 1 로
# 죽고 있었다(실측).
#
# 이 파일은 훅 문구의 줄 수 상한·명령형 금지 규약의 **정본**이다 — 소스 주석은
# 숫자를 갖지 않고 이 파일을 가리킨다.
#
# ⚠️ 인용 규약 (두 헬퍼 공통, 예외 없음):
#    **호출부는 본문을 작은따옴표로 넘기고, 본문 안 파이썬 문자열은 큰따옴표만
#    쓴다.** 호출부를 큰따옴표로 넘기면 셸이 호출 시점에 `$`·백틱을 먼저
#    치환해 버리는데, 그 결과는 FAIL 이 아니라 **초록색 거짓 통과**다
#    (예: `assert "x" in "$UNDEF"` → `assert "x" in ""` 가 아니라 본문 자체가
#    뭉개져 단언이 사라진다). 규약이 헬퍼마다 갈리면 위 케이스를 복사해
#    새 케이스를 만들 때 조용히 어긋난다.
HOOK="$(cd "$(dirname "$0")" && pwd)/serena_first.py"
export PYTHONDONTWRITEBYTECODE=1   # pure_check 의 import 가 hooks/__pycache__ 를 만들지 않게
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
  if printf '%s' "$out" | python3 -c 'import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get("systemMessage") else 1)' 2>/dev/null; then
    has_msg="yes"
  fi
  if [ "$has_msg" = "$expect" ]; then
    echo "PASS  $desc"
  else
    echo "FAIL  $desc (expected warn=$expect, got warn=$has_msg)"
    fail=1
  fi
}

# json_check <설명> <stdin JSON> <python 단언 본문> : exit 0 단언 + 출력 JSON 을 d 로 받아 검사
#  본문의 assert 메시지는 삼키지 않는다 — 훅 자체의 stderr 만 위에서 막는다.
json_check() {
  local desc="$1" input="$2" body="$3"
  local out rc
  out=$(printf '%s' "$input" | python3 "$HOOK" 2>/dev/null)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "FAIL  $desc (exit=$rc — 훅은 모든 경로에서 exit 0 이어야 함)"
    fail=1
    return
  fi
  if printf '%s' "$out" | python3 -c "
import sys, json
d = json.load(sys.stdin)
$body
"; then
    echo "PASS  $desc"
  else
    echo "FAIL  $desc"
    fail=1
  fi
}

# pure_check <설명> <python 본문> : 상수를 직접 import 해 단언 (훅 실행 없음)
#  훅 디렉터리는 환경변수로 넘긴다 — 셸 치환으로 심으면 저장소 경로에
#  작은따옴표가 섞일 때 깨진다.
pure_check() {
  local desc="$1" body="$2"
  if HOOK_DIR="${HOOK%/*}" python3 -c "
import os, sys
sys.path.insert(0, os.environ['HOOK_DIR'])
from serena_first import USER_MESSAGE, MODEL_CONTEXT
$body
"; then
    echo "PASS  $desc"
  else
    echo "FAIL  $desc"
    fail=1
  fi
}

# ── 1. 탐지 대상 / 비대상 (기존 케이스 — 전부 유지) ─────────────────────────
check "grep -r 경고"          '{"tool_name":"Bash","tool_input":{"command":"grep -r foo src/"}}'          yes
check "grep -R 경고"          '{"tool_name":"Bash","tool_input":{"command":"grep -R foo src/"}}'          yes
check "grep --include 경고"   '{"tool_name":"Bash","tool_input":{"command":"grep --include=*.py foo ."}}' yes
check "rg 경고"               '{"tool_name":"Bash","tool_input":{"command":"rg foo"}}'                    yes
check "단순 grep 무경고"      '{"tool_name":"Bash","tool_input":{"command":"cat a.txt | grep foo"}}'      no
check "ls 무경고"             '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'                    no
check "Bash 아닌 도구 무경고" '{"tool_name":"Read","tool_input":{"file_path":"/tmp/a"}}'                  no
check "빈 입력 무경고"        '{}'                                                                        no

# ── 2. ⭐ 타입 오류 입력 → 무경고 + exit 0 ───────────────────────────────────
#  이 훅이 타입 가드 없이 `tool_input.get(...)` 를 바로 부르던 판본에서는 아래
#  처음 두 케이스가 AttributeError / TypeError 로 exit 1 을 냈다(실측).
#  가드 한 줄을 지워도 초록이면 안 되는 자리다.
check "tool_input 이 문자열"  '{"tool_name":"Bash","tool_input":"grep -r foo"}'             no
check "command 가 숫자"       '{"tool_name":"Bash","tool_input":{"command":123}}'           no
check "command 가 객체"       '{"tool_name":"Bash","tool_input":{"command":{"x":1}}}'       no
check "tool_input 누락"       '{"tool_name":"Bash"}'                                        no
check "command 누락"          '{"tool_name":"Bash","tool_input":{}}'                        no
check "tool_name 누락"        '{"tool_input":{"command":"grep -r foo"}}'                    no
check "최상위가 배열"         '[]'                                                          no
check "최상위가 문자열"       '"grep -r foo"'                                               no
check "JSON 파싱 실패"        'not-a-json'                                                  no

# ── 3. ⭐ 2채널 동시 출력 — systemMessage(사용자) + additionalContext(모델) ──
#  두 채널은 수신자가 다르다. 하나만 내면 상대에게 닿지 않으므로 둘 다 단언한다.
HIT='{"tool_name":"Bash","tool_input":{"command":"grep -r foo src/"}}'
MISS='{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

json_check "두 채널 동시 출력" "$HIT" '
assert d.get("systemMessage"), "systemMessage 없음"
h = d.get("hookSpecificOutput") or {}
assert h.get("hookEventName") == "PreToolUse", h
ctx = h.get("additionalContext") or ""
assert ctx, "additionalContext 없음"
assert "find_referencing_symbols" in ctx, ctx
assert "ToolSearch" in ctx, ctx
'

json_check "비매칭은 두 채널 모두 없음" "$MISS" '
assert not d.get("systemMessage"), d
assert not d.get("hookSpecificOutput"), d
'

# ── 4. ⭐ permissionDecision 부재 — 권한 우회 사고를 기계로 막는다 ───────────
#  matcher 가 Bash 이므로 permissionDecision:"allow" 가 한 번 섞이면 세션의
#  **모든 Bash 호출에서 권한 프롬프트가 사라진다**. 에러가 아니라 "프롬프트가
#  안 뜬다"로만 나타나 사람 눈으로는 잡히지 않는다.
#  비매칭 경로까지 단언하는 이유: 나중에 "항상 hookSpecificOutput 을 내자"는
#  리팩터링이 들어와도 그 경로가 검사 밖에 남지 않게 하기 위해서다.
json_check "permissionDecision 부재 (매칭)" "$HIT" '
assert "permissionDecision" not in d, d
assert "permissionDecisionReason" not in d, d
h = d.get("hookSpecificOutput") or {}
assert "permissionDecision" not in h, h
assert "permissionDecisionReason" not in h, h
'

json_check "permissionDecision 부재 (비매칭)" "$MISS" '
assert "permissionDecision" not in d, d
h = d.get("hookSpecificOutput") or {}
assert "permissionDecision" not in h, h
'

# ── 5. 문구 규약 — 사실 서술 · 줄 수 상한 · 채널 분리 ────────────────────────
# 5-1. ⭐ 모델용 문구에 명령형이 없어야 한다 — 명령형은 프롬프트 인젝션 방어에
#      걸려 모델이 컨텍스트로 쓰지 않고 사용자에게 노출해 버린다.
#      블랙리스트는 스펙이 아니라 트립와이어다. 단어를 늘리는 대신 문구를
#      읽어서 사실 서술로 유지할 것.
pure_check "모델용 문구에 명령형 없음" '
for bad in ["할 것", "하라", "하십시오", "해야 한다", "하세요", "바랍니다"]:
    assert bad not in MODEL_CONTEXT, bad + " 발견: " + MODEL_CONTEXT
'

# 5-2. ⭐ 모델용 문구는 단정이 아니라 조건 서술이어야 한다 — 탐지는 정규식
#      휴리스틱이라 `mkdir rg tmp` 에도 발화하고, 규약의 출처는 사용자 전역
#      CLAUDE.md 이지 이 훅이 설치된 저장소가 아니다(마켓플레이스 배포).
#      거짓을 컨텍스트에 주입하면 훅이 트리거가 아니라 오염원이 된다.
pure_check "모델용 문구가 단정으로 흐르지 않음" '
first = MODEL_CONTEXT.splitlines()[0]
assert "이 저장소 규약" not in MODEL_CONTEXT, MODEL_CONTEXT
assert "사용자 CLAUDE.md" in first, first
assert "일치한다" in first, first
'

# 5-3. ⭐ 채널별 줄 수 상한 — 모델 5줄 / 사용자 3줄. 이 두 단언이 상한의 정본이다.
#      상한을 코드가 아니라 여기서 강제한다: 문자열이 고정이라 런타임 입력으로는
#      깨질 수 없고, 깨지는 유일한 경로가 파일 편집이기 때문이다.
pure_check "모델용 5줄 상한" '
n = len(MODEL_CONTEXT.splitlines())
assert n <= 5, str(n) + "줄: " + MODEL_CONTEXT
'

pure_check "사용자용 3줄 상한" '
n = len(USER_MESSAGE.splitlines())
assert n <= 3, str(n) + "줄: " + USER_MESSAGE
'

# 5-4. 빈 줄 금지 — 빈 줄을 상한에서 빼주기 시작하면 상한이 해석의 대상이 된다.
pure_check "두 문구에 빈 줄 없음" '
for label, text in [("USER_MESSAGE", USER_MESSAGE), ("MODEL_CONTEXT", MODEL_CONTEXT)]:
    for line in text.splitlines():
        assert line.strip(), label + " 에 빈 줄: " + text
'

# 5-5. ⭐ 두 채널의 내용이 달라야 한다 — 가장 그럴듯한 퇴행이 "두 채널에 같은
#      문자열을 넣어 해결"이고, 그러면 모델 채널에 사용자용 잡음이·사용자
#      화면에 ToolSearch 페이로드가 들어가 두 상한이 동시에 무의미해진다.
pure_check "두 채널 내용이 서로 다름" '
assert MODEL_CONTEXT != USER_MESSAGE
assert "ToolSearch" not in USER_MESSAGE, "도구 페이로드가 사용자 화면에 노출됨"
assert "ToolSearch" in MODEL_CONTEXT
'

# 5-6. 출력 문자열 상한 10,000자 (공식 문서) — 여유가 크지만 편집 사고 방지용
pure_check "채널별 10,000자 이내" '
assert len(USER_MESSAGE) <= 10000
assert len(MODEL_CONTEXT) <= 10000
'

exit $fail
