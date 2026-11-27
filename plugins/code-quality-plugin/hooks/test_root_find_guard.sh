#!/usr/bin/env bash
# root_find_guard.py 시나리오 테스트 — 루트·네트워크 마운트 상위 deny / 좁힌 경로·-xdev pass / 깨진 입력
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="${DIR}/root_find_guard.py"
export PYTHONDONTWRITEBYTECODE=1
pass=0
fail=0
judge() {  # 설명 기대 실제 출력 rc
  local desc="$1" expect="$2" got="$3" out="$4" rc="$5"
  if [[ "${rc}" -eq 0 && "${got}" == "${expect}" && "${out}" != *'"allow"'* ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${desc}: rc=${rc} got=${got} out=${out}"
    fail=$((fail + 1))
  fi
}
run_hook() {  # cwd 명령 — hook 입력 JSON 으로 감싸 실제 hook 실행(마운트 = 이 호스트의 /proc/self/mounts)
  local payload='import json, sys
print(json.dumps({"tool_name": "Bash", "cwd": sys.argv[1], "tool_input": {"command": sys.argv[2]}}))'
  python3 -c "${payload}" "$1" "$2" | python3 "${HOOK}"
}
check() {  # 설명 명령 기대(deny|pass) — 루트('/') 판정은 마운트 목록과 무관함
  local desc="$1" cmd="$2" expect="$3" out rc got="pass"
  out="$(run_hook /usr "${cmd}")"
  rc=$?
  [[ "${out}" == *'"deny"'* ]] && got="deny"
  judge "${desc}" "${expect}" "${got}" "${out}" "${rc}"
}
check_reason() {  # 설명 명령 거부-사유에-포함될-문자열
  local desc="$1" cmd="$2" want="$3" out reason
  local extract='import json, sys
print(json.load(sys.stdin)["hookSpecificOutput"]["permissionDecisionReason"])'
  out="$(run_hook /usr "${cmd}")"
  reason="$(printf '%s' "${out}" | python3 -c "${extract}" 2>/dev/null)"
  if [[ "${out}" == *'"deny"'* && "${reason}" == *"${want}"* ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${desc}: want=${want} out=${out}"
    fail=$((fail + 1))
  fi
}
# 가짜 마운트 /fake/home/mnt/aip2·HOME=/fake/home 으로 verdict 를 직접 호출(거부 사유 또는 pass 출력)
probe_mounts() {  # cwd 명령
  local probe='import sys
sys.path.insert(0, sys.argv[1])
import root_find_guard as g
print(g.verdict(sys.argv[3], sys.argv[2], ["/fake/home/mnt/aip2"]) or "pass")'
  HOME=/fake/home python3 -c "${probe}" "${DIR}" "$1" "$2"
}
check_mounts() {  # 설명 cwd 명령 기대(deny|pass)
  local desc="$1" cwd="$2" cmd="$3" expect="$4" out rc got="deny"
  out="$(probe_mounts "${cwd}" "${cmd}")"
  rc=$?
  [[ "${out}" == "pass" ]] && got="pass"
  judge "${desc}" "${expect}" "${got}" "${out}" "${rc}"
}
check_mounts_reason() {  # 설명 cwd 명령 거부-사유에-포함될-문자열
  local desc="$1" cwd="$2" cmd="$3" want="$4" out
  out="$(probe_mounts "${cwd}" "${cmd}")"
  if [[ "${out}" != "pass" && "${out}" == *"${want}"* ]]; then
    pass=$((pass + 1))
  else
    echo "FAIL ${desc}: want=${want} out=${out}"
    fail=$((fail + 1))
  fi
}
check_raw() {  # 설명 hook-입력-원문 — 해석할 수 없는 입력은 출력 없이 통과
  local desc="$1" input="$2" out rc got="pass"
  out="$(printf '%s' "${input}" | python3 "${HOOK}")"
  rc=$?
  [[ -n "${out}" ]] && got="output"
  judge "${desc}" pass "${got}" "${out}" "${rc}"
}

# --- deny: 시작 경로가 루트('/')
check "평문 find /" 'find / -name hooks.json' deny
check "11-26 사례(-path /proc -prune)" 'find / -path /proc -prune -o -name hooks.json -print' deny
check "sudo 접두" 'sudo find / -name x' deny
check "timeout 접두 + 리디렉션 + 파이프" 'timeout 60 find / -name x 2>/dev/null | head' deny
check "&& 뒤" 'cd ~ && find / -name x' deny
check "bash -c 안쪽" "bash -c 'find / -name x'" deny
check "따옴표 안의 \$(...)" "echo \"\$(find / -name x)\"" deny
check "전역 옵션 -L 뒤" 'find -L / -name x' deny
check "glob /*" 'find /* -name x' deny
check "이중 슬래시 //" 'find // -name x' deny
check "/. 표기" 'find /. -name x' deny
check "여러 시작 경로 중 하나가 /" 'find /usr / -name x' deny
check "괄호 식만 있고 -xdev 없음" 'find / \( -path /proc -prune \) -o -name x -print' deny
check "-maxdepth 는 예외 아님" 'find / -maxdepth 2 -name x' deny
check "리디렉션이 경로 앞에 있음" 'find 2>/dev/null / -name x' deny
check "리디렉션 뒤의 -xdev 도 인정" 'find / 2>/dev/null -xdev -name x' pass
# --- pass: 루트지만 -xdev·-mount, 또는 루트가 아님
check "-xdev" 'find / -xdev -name x' pass
check "-mount" 'find / -mount -name x' pass
check "괄호 뒤의 -xdev" 'find / \( -path /proc -prune \) -o -xdev -name x -print' pass
check "좁힌 절대 경로" 'find /usr/share -name x' pass
check "절대 경로 실행 파일도 탐지" '/usr/bin/find / -name x' deny
check "따옴표 안 문자열의 find /" 'echo "find / -name x"' pass
check "커밋 메시지 안의 find /" 'git commit -m "find / 차단"' pass
check "닫히지 않은 따옴표" 'find "/ -name x' pass
# --- 거부 사유
check_reason "사유에 -xdev 안내" 'find / -name x' '-xdev'
check_reason "사유에 /proc 언급" 'find / -name x' '/proc'
# --- 네트워크 마운트 상위(가짜 마운트 /fake/home/mnt/aip2, HOME=/fake/home)
check_mounts "~ 는 마운트 상위" /tmp 'find ~ -name x' deny
check_mounts "절대 경로 상위" /tmp 'find /fake -name x' deny
check_mounts "상대 경로 . (cwd 기준)" /fake/home 'find . -name x' deny
check_mounts "시작 경로 생략 = ." /fake/home/mnt 'find -name x' deny
check_mounts "../.. 상대 경로" /fake/home/work/a 'find ../.. -name x' deny
check_mounts "\$HOME 변수" /tmp "find \"\$HOME\" -name x" deny
check_mounts "glob 은 앞 디렉터리로" /tmp 'find /fake/home/m* -name x' deny
check_mounts "-maxdepth 는 예외 아님" /tmp 'find /fake/home -maxdepth 1 -name x' deny
check_mounts "마운트 밖 하위 경로" /tmp 'find ~/.claude/plugins -name x' pass
check_mounts "마운트 없는 cwd 의 ." /fake/home/work 'find . -name x' pass
check_mounts "마운트 지점 자체(명시 대상)" /tmp 'find /fake/home/mnt/aip2 -name x' pass
check_mounts "마운트 안쪽" /tmp 'find /fake/home/mnt/aip2/repo -name x' pass
check_mounts "마운트 상위 + -xdev" /tmp 'find ~ -xdev -name x' pass
check_mounts "인자 자리의 find 단어(which)" /fake/home 'which find' pass
check_mounts "인자 자리의 find 단어(man | head)" /fake/home 'man find | head' pass
check_mounts_reason "사유에 마운트 지점 언급" /tmp 'find ~ -name x' '/fake/home/mnt/aip2'
# --- /proc/self/mounts 해석(FUSE·NFS·CIFS 만, 8진 이스케이프 풂, 깨진 줄 무시)
parse_probe='import sys
sys.path.insert(0, sys.argv[1])
import root_find_guard as g
text = ("sysfs /sys sysfs rw 0 0\nproc /proc proc rw 0 0\n"
        "aip2:/home/u/work /home/u/mnt/aip2 fuse.sshfs rw 0 0\n"
        "srv:/x /mnt/my\\040nfs nfs4 rw 0 0\nfusectl /sys/fs/fuse/connections fusectl rw 0 0\n"
        "/dev/sda1 / ext4 rw 0 0\nbroken-line\n")
print(g.fuse_network_mounts(text))'
parsed="$(python3 -c "${parse_probe}" "${DIR}")"
judge "마운트 목록 해석" "['/home/u/mnt/aip2', '/mnt/my nfs']" "${parsed}" "${parsed}" 0
# --- 배포 형태: main() 이 마운트 파일을 읽고 입력 cwd 를 쓰는지(가짜 mounts 파일)
mounts_file="$(mktemp)"
trap 'rm -f "${mounts_file}"' EXIT
printf '%s\n' 'aip2:/home/u/work /fake/home/mnt/aip2 fuse.sshfs rw 0 0' '/dev/sda1 / ext4 rw 0 0' > "${mounts_file}"
check_main() {  # 설명 cwd 명령 기대(deny|pass)
  local desc="$1" cwd="$2" cmd="$3" expect="$4" out rc got="pass"
  local probe='import io, json, sys
sys.path.insert(0, sys.argv[1])
import root_find_guard as g
g._MOUNTS_FILE = sys.argv[2]
sys.stdin = io.StringIO(json.dumps({"tool_name": "Bash", "cwd": sys.argv[3], "tool_input": {"command": sys.argv[4]}}))
sys.exit(g.main())'
  out="$(HOME=/fake/home python3 -c "${probe}" "${DIR}" "${mounts_file}" "${cwd}" "${cmd}")"
  rc=$?
  [[ "${out}" == *'"deny"'* ]] && got="deny"
  judge "${desc}" "${expect}" "${got}" "${out}" "${rc}"
}
check_main "main: 마운트 상위 cwd 의 find ." /fake/home 'find . -name x' deny
check_main "main: 마운트 없는 cwd 의 find ." /fake/home/work 'find . -name x' pass
# --- 깨진 입력은 출력 없이 통과
check_raw "JSON 아님" 'not json'
check_raw "tool_input 없음" '{"tool_name": "Bash"}'
check_raw "command 가 문자열 아님" '{"tool_name": "Bash", "tool_input": {"command": 1}}'

echo "passed=${pass} failed=${fail}"
[[ "${fail}" -eq 0 ]]
