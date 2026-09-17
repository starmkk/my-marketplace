#!/usr/bin/env python3
"""재귀 코드 검색(grep -r / rg) 감지 시 Serena 우선 사용을 안내하는 PreToolUse hook.

차단하지 않음 — 모든 경로에서 exit 0.

⚠️ `permissionDecision` 은 출력하지 않는다. 이 훅의 matcher 는 `Bash` 이므로
   `"allow"` 를 한 번 내보내면 **모든 Bash 호출의 권한 프롬프트가 사라진다**
   (공식 문서: `"allow"` skips the permission prompt). "차단하지 않음"은
   "권한 확인을 건너뛴다"는 뜻이 아니다. 이 고장은 에러를 내지 않고 "프롬프트가
   안 뜬다"로만 나타나 눈으로 잡히지 않으므로 테스트가 부재를 단언한다.
   같은 이유로 `permissionDecisionReason` 도 쓰지 않는다 — allow/ask 에서는
   "shown to the user but not Claude" 라 모델 채널이 되지 못한다.

출력 채널이 둘이며 **수신자가 다르다** (공식 훅 문서 확인, 2026-09-18):
  · `systemMessage`                        → 사용자 화면 전용
  · `hookSpecificOutput.additionalContext` → 모델 컨텍스트 전용(화면에 안 보임)
안내 본문(도구 선택·`ToolSearch` 로드 한 줄)의 수신자는 **모델**이므로 후자가
본채널이다. 이 훅의 원래 결함이 바로 이것이었다 — 모델을 향한 문구를
`systemMessage` 단일 채널로만 내보내 정작 도구를 고르는 모델에게는 닿지 않았다.
사용자는 훅이 돌았다는 사실과 예외 조건만 알면 되므로 전자는 3줄로 둔다.

모델용 문구는 **사실 서술**로 쓴다 — 명령형("~하라", "~할 것")은 프롬프트
인젝션 방어에 걸려 모델이 컨텍스트로 쓰지 않고 사용자에게 노출해 버린다
(공식 문서 명시). 테스트가 명령형 부재를 단언한다.

줄 수 상한은 코드가 아니라 **테스트가 강제**한다 — 값의 정본은
`test_serena_first.sh` 의 상한 단언 케이스이며 여기에 숫자를 적지 않는다.
두 문자열이 고정이라 런타임 입력으로는 상한이 깨질 수 없고, 깨지는 유일한
경로가 이 파일의 편집이기 때문이다. 자르기 로직을 넣으면 실행되지 않는
분기만 생긴다. 채널별로 상한이 다른 이유는 비용 함수가 다르기 때문이다 —
`systemMessage` 는 grep 을 칠 때마다 사용자 화면을 먹고,
`additionalContext` 는 모델 컨텍스트 토큰을 먹는다.
"""

# `str | None` 애노테이션은 3.10 미만에서 정의 시점에 TypeError 를 낸다.
# 훅이 import 단계에서 죽으면 "모든 경로 exit 0" 계약이 인터프리터 버전에
# 따라 깨지므로, 한 줄로 그 경로를 닫아 둔다.
from __future__ import annotations

import json
import re
import sys

# 재귀 grep(-r/-R/--recursive/--include) 또는 ripgrep 호출을 감지
RECURSIVE_SEARCH = re.compile(r"\b(grep\s+(-[a-zA-Z]*[rR]|--recursive|--include)|rg\s)")

# 사용자 화면용 — 빈 줄 없음. 줄 수 상한은 테스트의 "사용자용 N줄 상한"
# 케이스가 강제한다(숫자를 여기 적으면 테스트와 조용히 어긋난다).
# `ToolSearch` 로드 한 줄은 넣지 않는다: 사용자는 도구를 호출하는 주체가
# 아니므로 그 페이로드의 수신자가 아니고, grep 을 칠 때마다 화면을 먹는다.
# 대신 "모델에 전달했다"는 사실을 적어 훅 동작을 관찰할 수 있게 한다.
USER_MESSAGE = """🔍 **재귀 코드 검색 감지** — Serena 우선 규약 안내를 모델 컨텍스트에 전달함 (CLAUDE.md: *Code navigation → Serena first*)
- 영향 범위·참조 추적은 `find_referencing_symbols` 담당 — grep 으로 대체 불가
- serena 인덱스 밖(외부 저장소·site-packages)이나 비코드 파일(로그·JSON·바이너리)이면 grep 이 정당함"""

# 모델 컨텍스트용 — 빈 줄 없음, 사실 서술만(명령형 금지). 줄 수 상한은
# 테스트의 "모델용 N줄 상한" 케이스가 강제한다.
# 코드펜스를 쓰지 않는 이유: 펜스 3줄이 상한을 먹는데 이 문자열은 화면에
# 렌더되지 않으므로 펜스가 주는 이득이 없다.
# ⚠️ 1행이 단정으로 흐르지 않게 유지할 것. 탐지는 정규식 휴리스틱이라
#    `mkdir rg tmp` 같은 입력에도 발화하므로 "재귀 검색이다"는 참이 아닐 수
#    있고, 규약의 출처는 **사용자 전역 CLAUDE.md** 이지 이 훅이 설치된
#    저장소가 아니다 — 마켓플레이스로 임의 저장소에 깔리기 때문이다.
#    거짓을 모델 컨텍스트에 주입하면 이 훅은 트리거가 아니라 오염원이 된다.
MODEL_CONTEXT = """실행하려는 Bash 명령이 재귀 코드 검색 패턴(grep -r / rg)과 일치한다. 사용자 CLAUDE.md 규약은 심볼 단위 탐색에 Serena 를 먼저 쓰는 것으로 되어 있다.
로드 한 줄: `ToolSearch({query: "select:mcp__plugin_serena_serena__find_symbol,mcp__plugin_serena_serena__find_referencing_symbols,mcp__plugin_serena_serena__get_symbols_overview,mcp__plugin_serena_serena__search_for_pattern", max_results: 4})`
정의 찾기는 find_symbol, 영향 범위·참조 추적은 find_referencing_symbols 가 담당하며 후자는 grep 으로 대체되지 않는다.
파일 구조 파악은 get_symbols_overview, 심볼이 아닌 텍스트 검색은 search_for_pattern 이 담당한다.
serena 인덱스 밖(외부 저장소·site-packages)이거나 비코드 파일(로그·JSON·바이너리)인 경우는 grep 이 적절한 자리다."""


def command_of(data: object) -> str | None:
    """stdin JSON 에서 Bash 명령 문자열을 뽑음. 비대상·타입 불일치면 None.

    타입 가드를 이 한 곳에 모아 판정부를 단일 경로로 유지한다 — 가드가
    판정부에 흩어지면 "모든 경로 exit 0" 계약이 분기마다 재확인 대상이 된다.
    이 함수가 없던 판본은 `tool_input` 이 문자열이면 AttributeError,
    `command` 가 숫자면 TypeError 로 **exit 1** 을 냈다(실측).
    """
    if not isinstance(data, dict):
        return None
    if data.get("tool_name") != "Bash":
        return None
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    if not isinstance(command, str):
        return None
    return command


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        sys.exit(0)

    command = command_of(data)
    if command is None or not RECURSIVE_SEARCH.search(command):
        print(json.dumps({}))
        sys.exit(0)

    # 두 채널 동시 출력 · permissionDecision 미출력 — 근거는 위 docstring 참조.
    print(json.dumps({
        "systemMessage": USER_MESSAGE,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": MODEL_CONTEXT,
        },
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
