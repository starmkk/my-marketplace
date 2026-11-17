#!/usr/bin/env bash
# venv_guard.py 시나리오 테스트 — venv 있음·없음, cd 접두, env 접두, 비대상, 깨진 입력
set -uo pipefail
HOOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/venv_guard.py"
export PYTHONDONTWRITEBYTECODE=1
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
mkdir -p "${tmp}/withvenv/.venv/bin" "${tmp}/withvenv/.git" "${tmp}/withvenv/sub" \
  "${tmp}/novenv/.git"
touch "${tmp}/withvenv/.venv/bin/python"
pass=0
fail=0
check() {  # 설명 cwd 명령 기대(deny|pass)
  local desc="$1" cwd="$2" cmd="$3" expect="$4" input out rc got
  input="$(python3 -c 'import json,sys; print(json.dumps({"tool_name": "Bash", "cwd": sys.argv[1], "tool_input": {"command": sys.argv[2]}}))' "${cwd}" "${cmd}")"
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
check "venv 있음 + python3 -m pytest" "${tmp}/withvenv" "python3 -m pytest -q" deny
check "하위 디렉터리에서도 저장소 venv 적용" "${tmp}/withvenv/sub" "/usr/bin/python3 -m pytest" deny
check "pytest 단독" "${tmp}/withvenv" "pytest -q tests" deny
check "env 접두" "${tmp}/withvenv" "PYTHONPATH=scripts python3 -m pytest" deny
check "venv python 은 통과" "${tmp}/withvenv" ".venv/bin/python -m pytest -q" pass
check "env -u 후 venv python 통과" "${tmp}/withvenv" "env -u PYTHONPATH .venv/bin/python -m pytest" pass
check "venv 없는 프로젝트는 통과" "${tmp}/novenv" "python3 -m pytest" pass
check "cd 로 venv 프로젝트 진입" "${tmp}/novenv" "cd ${tmp}/withvenv && python3 -m pytest" deny
check "timeout 접두" "${tmp}/withvenv" "timeout 600 python3 -m pytest -q" deny
check "nice·nohup 접두" "${tmp}/withvenv" "nohup nice -n 5 pytest" deny
check "bash -c 안쪽" "${tmp}/withvenv" "bash -c 'python3 -m pytest -q'" deny
check "괄호 서브셸" "${tmp}/novenv" "(cd ${tmp}/withvenv && python3 -m pytest)" deny
check "activate 후 pytest 는 통과" "${tmp}/withvenv" "source .venv/bin/activate && pytest -q" pass
check "pytest 아닌 python" "${tmp}/withvenv" "python3 -c 'print(1)'" pass
check "비대상 명령" "${tmp}/withvenv" "ls -la" pass
out="$(printf '{broken' | python3 "${HOOK}")"; rc=$?
if [[ "${rc}" -eq 0 && -z "${out}" ]]; then pass=$((pass + 1)); else echo "FAIL 깨진 입력"; fail=$((fail + 1)); fi
echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
