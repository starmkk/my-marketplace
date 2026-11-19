#!/usr/bin/env bash
# verify-handoff-integrity.sh
# project-handoff 스킬 §2 step 4 self-review (handoff 커밋 직전 실행, 커밋 직후 재실행도 통과).
# 검사 5종 — 모두 실행한 뒤 끝에서 한 번만 종료 코드를 정함.
#   head   '현재 상태 스냅샷' 절의 HEAD anchor 가 git HEAD 와 일치하는가
#          (anchor = HEAD^ 이고 HEAD 가 이 handoff 를 포함한 커밋이면 '커밋 후 검증'으로 통과.
#           이때 기준 repo 는 handoff 파일이 있는 repo — 다른 파일 동반 허용)
#   prompt '다음 세션 시작 프롬프트' 절(heading·```text 블록·자기 파일명·HEAD) 이 있는가
#   refs   '참조 인덱스' 절의 경로(절대 경로 또는 repo 루트 기준 상대 경로)가 실제로 있는가
#   절 탐지는 펜스 코드 블록(```) 안의 줄을 heading 으로 보지 않음
#   date   파일명 앞 날짜가 오늘인가(다르면 WARN)
#   teammates 이 세션이 name 을 주고 띄운 팀원(agent teams) 중 살아 있는 프로세스가 있는가
#          (대기 = FAIL·TaskStop 안내, 작업 중일 수 있음·확인 불가 = WARN — check_teammates 주석)
#
# 사용:
#   $ bash verify-handoff-integrity.sh docs/handoffs/<YYYY-MM-DD>-<topic>-handoff.md
#   (인자 생략 시 repo 루트의 docs/handoffs/ 와 legacy docs/superpowers/handoffs/
#    (읽기 전용 fallback) 중 가장 최근 mtime 파일 자동 선택)
#
# 종료 코드: 0 = OK(WARN 허용) · 1 = FAIL

set -euo pipefail

HANDOFF="${1:-}"
HEX_RE="\`[0-9a-f]{7,40}\`"   # 백틱으로 감싼 커밋 해시

if [[ -z "$HANDOFF" ]]; then
  # 인자 생략 — cwd 의 repo 에서 최근 handoff 를 고른다(이때만 cwd 가 repo 여야 함)
  TOP=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [[ -z "$TOP" ]]; then
    echo "[FAIL] git repo 가 아님 — handoff 경로를 인자로 주거나 repo 안에서 실행" >&2; exit 1
  fi
  HANDOFF_DIR="$TOP/docs/handoffs"
  LEGACY_HANDOFF_DIR="$TOP/docs/superpowers/handoffs"  # 읽기 전용 fallback — 쓰기 금지
  # 가장 최근 handoff 자동 선택
  # (AppleDouble ._* 는 glob '*' 가 점 파일을 이미 제외 — 아래 이름 검사는 방어용)
  candidates=()
  for f in "$HANDOFF_DIR"/*-handoff.md "$LEGACY_HANDOFF_DIR"/*-handoff.md; do
    if [[ -f "$f" && "${f##*/}" != ._* ]]; then candidates+=("$f"); fi
  done
  if [[ "${#candidates[@]}" -gt 0 ]]; then
    # shellcheck disable=SC2012  # 파일명은 <YYYY-MM-DD>-<kebab-topic>-handoff.md 로 특수문자 없음.
    #   find -printf 는 GNU 전용이라 macOS(BSD find) 호환을 위해 ls -t 유지.
    HANDOFF=$(ls -t "${candidates[@]}" | head -1 || true)
  fi
  if [[ -z "$HANDOFF" ]]; then
    echo "[SKIP] docs/handoffs (및 legacy docs/superpowers/handoffs) 에 handoff 파일 없음"
    exit 0
  fi
  echo "[info] 인자 생략 → 최근 파일 검증: $HANDOFF"
fi

if [[ ! -f "$HANDOFF" ]]; then
  echo "[FAIL] handoff 파일 없음: $HANDOFF" >&2; exit 1
fi

# 판정 기준 repo — 한 곳에서만 정한다(HEAD 대조·커밋 후 검증·§8 상대 경로가 같이 씀)
#   HANDOFF_TOP = handoff 가 속한 repo(밖이면 빈 값 → 커밋 후 검증 불가), HANDOFF_REL = 그 안 경로
#   TOP = HANDOFF_TOP, 없으면 cwd 의 repo
HANDOFF_ABS="$(cd "$(dirname "$HANDOFF")" && pwd -P)/$(basename "$HANDOFF")"
HANDOFF_TOP=$(git -C "$(dirname "$HANDOFF_ABS")" rev-parse --show-toplevel 2>/dev/null || true)
HANDOFF_REL=""
if [[ -n "$HANDOFF_TOP" && "$HANDOFF_ABS" == "$HANDOFF_TOP"/* ]]; then
  HANDOFF_REL="${HANDOFF_ABS#"$HANDOFF_TOP"/}"
  TOP="$HANDOFF_TOP"
else
  HANDOFF_TOP=""
  TOP=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [[ -z "$TOP" ]]; then
    echo "[FAIL] git repo 가 아님 — handoff 도 cwd 도 git repo 밖" >&2; exit 1
  fi
fi

status=0
ANCHOR=""   # check_head 가 채우고 check_prompt 가 참조
# 인자가 여럿이면 공백으로 이어 한 줄로 출력(긴 문구를 줄 나눠 넘겨도 잘리지 않게)
fail() { echo "[FAIL] $*" >&2; status=1; }
warn() { echo "[WARN] $*"; }

# section_body <heading 정규식> — 첫 매치 heading 다음 줄부터 다음 '## ' 전까지 출력
# (같은 제목이 다시 나와도 거기서 끝). 펜스 코드 블록(^```) 안의 줄은 heading 으로 보지 않음.
# 종료 코드: 0 = heading 있음 · 1 = 없음(heading 존재 검사도 이 함수로 함)
section_body() {
  awk -v re="$1" '
    /^```/ { fence = !fence; if (f) { print } next }
    !fence && f && /^## / { exit }
    !fence && !f && $0 ~ re { f = 1; next }
    f
    END { exit !f }
  ' "$HANDOFF"
}
first_hash() { grep -oE "$HEX_RE" | head -1 | tr -d "\`" || true; }

# head_committed_handoff — '커밋 후 검증': handoff 가 속한 repo(HANDOFF_TOP)에서 anchor = HEAD^
# 이고 HEAD 커밋의 변경 파일에 이 handoff 가 있으면 [OK] 출력 후 0, 아니면 1(판정 불가 포함).
# handoff 가 repo 밖이면 HEAD 가 그 파일을 바꿨을 수 없으므로 판정 불가
head_committed_handoff() {
  local head parent names
  if [[ -z "$HANDOFF_TOP" ]]; then
    echo "  [info] handoff 가 git repo 안에 없음 — '커밋 후 검증' 불가: $HANDOFF_ABS" >&2
    return 1
  fi
  head=$(git -C "$HANDOFF_TOP" rev-parse -q --verify HEAD 2>/dev/null || true)
  parent=$(git -C "$HANDOFF_TOP" rev-parse -q --verify 'HEAD^' 2>/dev/null || true)
  if [[ -z "$head" || -z "$parent" || "$parent" != "$ANCHOR"* ]]; then return 1; fi
  if ! names=$(git -C "$HANDOFF_TOP" -c core.quotePath=false \
    diff --name-only 'HEAD^' HEAD 2>/dev/null); then
    echo "  [info] git diff HEAD^ HEAD 실패 — '커밋 후 검증' 불가" >&2
    return 1
  fi
  if ! grep -qxF -- "$HANDOFF_REL" <<<"$names"; then return 1; fi
  echo "[OK](커밋 후 검증) HEAD anchor ($ANCHOR) = HEAD^," \
    "HEAD (${head:0:7}) 가 이 handoff 를 포함한 커밋"
}

# ── head: §1 스냅샷의 HEAD anchor ↔ git HEAD ──────────────────────────────────
check_head() {
  local re='^## [0-9]+\. 현재 상태 스냅샷' body real
  if body=$(section_body "$re"); then
    # '| HEAD |'·'| **HEAD** |' 행의 첫 해시 → 없으면 절의 첫 해시(다중 repo 표 첫 행 = 현재 repo)
    ANCHOR=$( (grep -E '^\| *\*{0,2}HEAD\*{0,2} *\|' <<<"$body" || true) | first_hash)
    if [[ -z "$ANCHOR" ]]; then ANCHOR=$(first_hash <<<"$body"); fi
  else
    warn "'현재 상태 스냅샷' 절 없음 — 문서 전체의 첫 해시를 HEAD anchor 로 판정"
    ANCHOR=$(first_hash < "$HANDOFF")
  fi
  if [[ -z "$ANCHOR" ]]; then
    fail "HEAD anchor 없음 — §1 '현재 상태 스냅샷' 표의 HEAD 셀에 \`<hash>\` 를 적을 것"
    return 0
  fi

  real=$(git -C "$TOP" rev-parse -q --verify HEAD 2>/dev/null || true)
  if [[ -z "$real" ]]; then
    fail "git HEAD 없음(커밋 0개 repo) — HEAD anchor ($ANCHOR) 를 대조할 수 없음"
    return 0
  fi
  if [[ "$real" == "$ANCHOR"* ]]; then
    echo "[OK] HEAD anchor ($ANCHOR) = git HEAD (${real:0:7})"
    return 0
  fi
  # handoff 커밋 직후 재실행: 문서의 anchor 는 커밋 직전 HEAD(= 지금의 HEAD^)
  if head_committed_handoff; then return 0; fi
  fail "HEAD anchor ($ANCHOR) ≠ git HEAD (${real:0:7})"
  {
    echo "  → §1 HEAD 셀은 handoff 커밋 직전 HEAD 여야 함(handoff 커밋 자체는 적지 않음)"
    echo "  → '커밋 후 검증' 통과 조건: anchor = HEAD^ 이고 HEAD 가 이 handoff 를 포함한 커밋"
    echo "  → handoff 와 무관한 커밋이 뒤에 생겼거나 해시가 틀림:"
    echo "     §1 HEAD·commit chain 과 §10 의 HEAD 를 \`${real:0:7}\` 기준으로 정정 후 재검증"
  } >&2
}

# ── prompt: §10 다음 세션 시작 프롬프트 ───────────────────────────────────────
check_prompt() {
  local re='^## [0-9]+\. 다음 세션 시작 프롬프트' prompt base
  if ! prompt=$(section_body "$re"); then
    fail "§10 '다음 세션 시작 프롬프트' heading 없음 — handoff-template.md §10 골격을 추가할 것"
    return 0
  fi
  if ! grep -q '^```text' <<<"$prompt"; then
    fail "§10 에 \`\`\`text 펜스 블록이 없음 — 복붙용 원문 블록 1개 필요"
  fi
  base=$(basename "$HANDOFF")
  if ! grep -qF "$base" <<<"$prompt"; then
    fail "§10 프롬프트에 자기 파일명($base)이 없음 — 'handoff 를 읽고' 지시에 경로 필요"
  fi
  if [[ -n "$ANCHOR" ]] && ! grep -qF "$ANCHOR" <<<"$prompt"; then
    warn "§10 프롬프트에 HEAD anchor($ANCHOR) 가 없음 — 실행 위치 줄에 'HEAD <hash>' 권장"
  fi
  if ! grep -qE '§9 ?의 [0-9]+ ?번' <<<"$prompt"; then
    warn "§10 프롬프트에 '§9 의 N번' 진입 스텝 지정이 없음"
  fi
}

# ── refs: §8 참조 인덱스의 경로 존재 ──────────────────────────────────────────
# 토큰 = 백틱 안 문자열 + 마크다운 링크 대상. 판정 순서
#   ① 끝의 ' §…'·'#…'·':<줄>(-<줄>)'·':<줄>:<열>'·':L<줄>(-L<줄>)' 제거
#   ② 공백·{·<·*·$·~ 가 있거나 '://'·'…'·'...' 를 포함하면 건너뜀(자리표시·glob·URL·생략 표기)
#      단말 경로(/sdcard/ /storage/ /data/local/ /data/data/ /system/ /vendor/)도 건너뜀
#   ③ 절대 경로, 또는 첫 구성요소가 repo 루트에 실제 있는 상대 경로만 존재 확인
#      (첫 구성요소가 '..' 이면 repo 루트 기준이 아니므로 건너뜀)
check_refs() {
  local re='^## [0-9]+\. 참조 인덱스' body tok first target missing=()
  local strip='s/ *§.*$//; s/#.*$//; s/:[0-9]+(-[0-9]+|:[0-9]+)?$//; s/:L[0-9]+(-L?[0-9]+)?$//'
  if ! body=$(section_body "$re"); then
    warn "'참조 인덱스' 절 없음 — 참조 경로 검사를 건너뜀"
    return 0
  fi
  while IFS= read -r tok; do
    tok=$(sed -E "$strip" <<<"$tok")
    if [[ -z "$tok" || "$tok" =~ [[:space:]{\<*$~] || "$tok" == *"://"* ]]; then continue; fi
    if [[ "$tok" == *"…"* || "$tok" == *"..."* ]]; then continue; fi
    case "$tok" in
      /sdcard/* | /storage/* | /data/local/* | /data/data/* | /system/* | /vendor/*) continue ;;
    esac
    if [[ "$tok" == /* ]]; then
      target="$tok"
    else
      tok="${tok#./}"
      first="${tok%%/*}"
      if [[ -z "$first" || "$first" == ".." || ! -e "$TOP/$first" ]]; then continue; fi
      target="$TOP/$tok"
    fi
    if [[ ! -e "$target" ]]; then missing+=("$tok"); fi
  done < <(
    { grep -oE "\`[^\`]+\`" <<<"$body" | tr -d "\`"
      grep -oE '\]\([^)]+\)' <<<"$body" | sed -E 's/^\]\(//; s/\)$//'
    } || true
  )
  if [[ "${#missing[@]}" -gt 0 ]]; then
    fail "§8 참조 인덱스의 경로 ${#missing[@]}개가 없음:"
    {
      printf '  - %s\n' "${missing[@]}"
      echo "  → 모듈·sibling repo 기준 경로라면 repo 루트 기준 전체 경로나 절대 경로로 적을 것"
      echo "  → 단말·원격 경로는 백틱 밖이나 §6 에 적을 것"
    } >&2
  else
    echo "[OK] §8 참조 경로 존재"
  fi
}

# ── date: 파일명 앞 날짜 ↔ 오늘 ───────────────────────────────────────────────
check_date() {
  local base today
  base=$(basename "$HANDOFF")
  today=$(date +%Y-%m-%d)
  if [[ ! "$base" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})- ]]; then
    warn "파일명에 YYYY-MM-DD 접두가 없음: $base"
  elif [[ "${BASH_REMATCH[1]}" != "$today" ]]; then
    warn "파일명 날짜(${BASH_REMATCH[1]}) ≠ 오늘($today) — 새로 쓴 handoff 라면 파일명 정정"
  fi
}

# ── teammates: 이 세션이 name 을 주고 띄운 팀원(agent teams)의 살아 있는 프로세스 ─────────
# name 을 준 Agent 는 팀원으로 떠서 보고 뒤에도 끝나지 않고 대기한다(isActive=false). 새 세션에서는
# 주소 불가이고 TaskStop 뒤에는 같은 이름으로 재개되지 않으므로 handoff 전에 리더가 종료한다.
#   등록부   ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/teams/session-<세션 ID 앞 8자>/config.json
#   살아 있음 tmux 팀원 = `ps -ww -eo pid=,args=` 의 한 줄에 '--agent-id <id>' 또는
#            '--agent-id=<id>' 토큰(정확 일치). 그 밖 backendType 은 프로세스로 확인 불가 → WARN
#   판정     isActive 가 false → FAIL, true·키 없음 → WARN(작업 중일 수 있음), 없으면 OK
#   재사용 예외 §1 의 '실행 중(이 세션 한정' 줄(펜스·HTML 주석 줄 제외)에 `이름`(백틱 포함 고정
#            문자열)이 있으면 대기 팀원도 WARN — handoff 뒤 같은 세션에서 계속 쓸 팀원만(사용자 결정
#            2026-11-19), 세션 종료·/clear 전 TaskStop
#   믿을 수 없음 등록부의 leadProcess.pid 가 ps 에 없으면(샌드박스 PID 격리 등) WARN 만 내고 끝냄
#   세션 ID 없음 → info 로 건너뜀, python3 없음·ps 실패·등록부 읽기 실패 → WARN(ListAgents 로 확인)
PY_TEAMMATES=""
read -r -d '' PY_TEAMMATES <<'PY' || true
import io, json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
pids, alive = set(), set()
for line in io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace"):
    args = line.split()
    if not args:
        continue
    pids.add(args[0])
    for i, a in enumerate(args):
        if a == "--agent-id" and i + 1 < len(args):
            alive.add(args[i + 1])
        elif a.startswith("--agent-id="):
            alive.add(a.split("=", 1)[1])
lead_pid = (cfg.get("leadProcess") or {}).get("pid")
if lead_pid is not None and str(lead_pid) not in pids:
    print("nolead\t" + str(lead_pid))
    sys.exit(0)
for m in cfg["members"]:
    if m.get("agentType") == "team-lead":
        continue
    name = m.get("name") or m.get("agentId")
    if m.get("backendType") != "tmux":
        print("unknown\t" + str(name) + "\t" + str(m.get("backendType")))
    elif m.get("agentId") in alive:
        print(("idle" if m.get("isActive") is False else "busy") + "\t" + str(name))
PY

check_teammates() {
  local sid="${CLAUDE_CODE_SESSION_ID:-}" cfg psout rows kind name extra found=0 kept
  if [[ -z "$sid" ]]; then
    echo "[info] CLAUDE_CODE_SESSION_ID 없음 — 팀원 검사 건너뜀"
    return 0
  fi
  cfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/teams/session-${sid:0:8}/config.json"
  if [[ ! -f "$cfg" ]]; then
    echo "[OK] 이 세션의 팀원 없음"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    warn "python3 없음 — 팀원 검사를 못 함. ListAgents 의 Teammates 행으로 직접 확인"
    return 0
  fi
  if ! psout=$(ps -ww -eo pid=,args= 2>/dev/null); then
    warn "ps 를 읽지 못함 — 팀원 검사를 못 함. ListAgents 의 Teammates 행으로 직접 확인"
    return 0
  fi
  if ! rows=$(python3 -c "$PY_TEAMMATES" "$cfg" <<<"$psout" 2>/dev/null); then
    warn "팀 등록부를 읽지 못함($cfg) — ListAgents 의 Teammates 행으로 직접 확인"
    return 0
  fi
  # §1 의 '실행 중(이 세션 한정' 줄들(펜스 안·HTML 주석 줄 제외) — 재사용 예정 팀원 판정용
  kept=$( { section_body '^## [0-9]+\. 현재 상태 스냅샷' || true; } \
    | awk '/^```/ { fence = !fence; next } !fence && !/<!--/' \
    | grep -F '실행 중(이 세션 한정' || true)
  while IFS=$'\t' read -r kind name extra; do
    case "$kind" in
      nolead)
        warn "ps 에 리더 프로세스(pid $name)가 보이지 않음(샌드박스 PID 격리 등) —" \
          "팀원 검사를 믿을 수 없음. ListAgents 의 Teammates 행으로 직접 확인"
        return 0
        ;;
      idle)
        found=1
        if grep -qF -- "\`$name\`" <<<"$kept"; then
          extra="§1 에 재사용 예정으로 기록된 대기 팀원 '$name' — handoff 뒤 이 세션에서 계속 쓸"
          extra+=" 때만 유효(새 세션에서는 주소 불가). 세션을 끝내거나 /clear 하기 전에"
          warn "$extra TaskStop({task_id: \"$name\"})"
          continue
        fi
        fail "대기 팀원 '$name' 이 살아 있음(name 을 주고 띄운 Agent — 보고 뒤에도 끝나지 않음)"
        {
          echo "  → 결과 원문을 파일로 보관했는지 확인한 뒤 리더(메인 세션)에서"
          echo "     TaskStop({task_id: \"$name\"}) 로 종료하고 ListAgents 의 Teammates 행이 사라졌는지 확인"
          echo "  → 새 세션에서는 주소 불가, 종료 뒤에는 같은 이름으로 재개 불가"
        } >&2
        ;;
      busy)
        found=1
        warn "작업 중일 수 있는 팀원 '$name' — 종료할지 사용자에게 묻고, 남기면 §1 에 '실행 중: <이름·목적·결과 경로>' 로 기록"
        ;;
      unknown)
        found=1
        warn "팀원 '$name'(backendType $extra) 은 프로세스로 확인할 수 없음 — ListAgents 로 확인"
        ;;
    esac
  done <<<"$rows"
  if [[ "$found" -eq 0 ]]; then
    echo "[OK] 이 세션의 살아 있는 팀원 없음"
  fi
}

check_head
check_prompt
check_refs
check_date
check_teammates

if [[ "$status" -eq 0 ]]; then
  echo "[PASS] $HANDOFF"
else
  echo "[FAIL] 위 항목 정정 후 재검증 — $HANDOFF" >&2
fi
exit "$status"
