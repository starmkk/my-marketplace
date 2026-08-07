#!/bin/bash
# serena_first.py 동작 검증 — 경고 대상/비대상 케이스
HOOK="$(cd "$(dirname "$0")" && pwd)/serena_first.py"
fail=0

check() {
  local desc="$1" input="$2" expect="$3"
  local out has_msg="no"
  out=$(echo "$input" | python3 "$HOOK" 2>/dev/null)
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

check "grep -r 경고"          '{"tool_name":"Bash","tool_input":{"command":"grep -r foo src/"}}'          yes
check "grep -R 경고"          '{"tool_name":"Bash","tool_input":{"command":"grep -R foo src/"}}'          yes
check "grep --include 경고"   '{"tool_name":"Bash","tool_input":{"command":"grep --include=*.py foo ."}}' yes
check "rg 경고"               '{"tool_name":"Bash","tool_input":{"command":"rg foo"}}'                    yes
check "단순 grep 무경고"      '{"tool_name":"Bash","tool_input":{"command":"cat a.txt | grep foo"}}'      no
check "ls 무경고"             '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'                    no
check "Bash 아닌 도구 무경고" '{"tool_name":"Read","tool_input":{"file_path":"/tmp/a"}}'                  no
check "빈 입력 무경고"        '{}'                                                                        no

exit $fail
