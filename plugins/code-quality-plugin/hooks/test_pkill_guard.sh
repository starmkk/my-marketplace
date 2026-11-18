#!/usr/bin/env bash
# pkill_guard.py 시나리오 테스트 — 자기 매칭 deny / 안전 형태 pass / 깨진 입력
set -uo pipefail
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/pkill_guard.py"
export PYTHONDONTWRITEBYTECODE=1
pass=0
fail=0
check() {  # 설명 명령 기대(deny|pass)
  local desc="$1" cmd="$2" expect="$3" input out rc got
  input="$(python3 -c 'import json,sys; print(json.dumps({"tool_name": "Bash", "cwd": "/", "tool_input": {"command": sys.argv[1]}}))' "${cmd}")"
  out="$(printf '%s' "${input}" | python3 "${HOOK}")"
  rc=$?
  got="pass"
  [[ "${out}" == *'"deny"'* ]] && got="deny"
  if [[ "${rc}" -eq 0 && "${got}" == "${expect}" && "${out}" != *'"allow"'* ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${desc}: rc=${rc} got=${got} out=${out}"
    fail=$((fail + 1))
  fi
}
# --- deny: 패턴이 명령 문자열 자체에 매칭됨
check "평문 패턴 + 뒤 명령 (exit 144 재현)" 'pkill -f "run_reports.py"; cat log' deny
check "pgrep -f 평문" 'pgrep -f "run_reports.py"' deny
check "대괄호가 있어도 평문이 같은 명령에 남음(재시작 관용구)" \
  'pkill -f "[r]un_reports.py"; nohup python run_reports.py &' deny
check "따옴표 안의 | (교대 패턴)" 'pkill -f "a.py|b.py"; cat log' deny
check "kill \$(pgrep -f ...)" "kill \$(pgrep -f \"worker.py\")" deny
check "xargs pkill -f" 'echo x | xargs pkill -f worker.py' deny
check "sudo 접두" 'sudo pkill -f worker.py; true' deny
check "결합 플래그 -af" 'pgrep -af worker.py' deny
check "--full" 'pkill --full worker.py' deny
check "패턴 뒤에 오는 -f (getopt 재배열)" 'pgrep -a worker.py -f' deny
check "시그널 옵션 + -f" 'pkill -9 -f worker.py; echo done' deny
check "bash -c 안쪽" "bash -c 'pkill -f worker.py; cat log'" deny
check "개행으로 이어진 다음 줄" $'pkill -f worker.py\nls' deny
check "while pgrep -f (거짓 양성 루프)" 'while pgrep -f worker.py; do :; done' deny
check "따옴표 안의 \$(pgrep -f ...)" "[ -n \"\$(pgrep -f worker.py)\" ] && echo up" deny
check "백틱 pgrep" "kill \`pgrep -f worker.py\`" deny
check "bash -lc 결합 플래그" "bash -lc 'pkill -f worker.py; cat log'" deny
check "-STOP 시그널 뒤 -f" 'pkill -STOP -f worker.py; true' deny
check "-SIGTERM 시그널 뒤 -f" 'pkill -SIGTERM -f worker.py; true' deny
check "정규식 오류 패턴" 'pkill -f "[unclosed"; true' deny
# --- pass
check "-x 는 전체 일치라 자기 셸에 걸리지 않음" 'pgrep -fx worker.py; echo ok' pass
check "대괄호 + 평문 없음" 'pkill -f "[w]orker.py"; cat log' pass
check "대괄호 + 리다이렉트 숫자 토큰" 'pkill -f "[w]orker.py" 2>&1; ls' pass
check "-f 없는 pkill (프로세스 이름만 매칭)" 'pkill worker; cat log' pass
check "-u 값은 패턴 후보가 아님" 'pkill -u root -f "[w]orker.py"; echo root' pass
check "-F pidfile (대문자 F)" 'pkill -F /tmp/w.pid; echo ok' pass
check "pkill 아닌 명령" 'ls -la; grep -f patterns.txt log' pass
check "따옴표 안의 pkill 문자열(단일 토큰)" 'echo "pkill -f worker"' pass
check "빈 명령" '' pass
out="$(printf '{broken' | python3 "${HOOK}")"; rc=$?
if [[ "${rc}" -eq 0 && -z "${out}" ]]; then pass=$((pass + 1)); else echo "FAIL 깨진 입력"; fail=$((fail + 1)); fi
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
