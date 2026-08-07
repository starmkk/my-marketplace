#!/usr/bin/env python3
"""재귀 코드 검색(grep -r / rg) 감지 시 Serena 우선 사용을 경고하는 PreToolUse hook.

차단하지 않음. systemMessage 만 출력하고 항상 exit 0 함.
"""

import json
import re
import sys

# 재귀 grep(-r/-R/--recursive/--include) 또는 ripgrep 호출을 감지
PATTERN = re.compile(r"\b(grep\s+(-[a-zA-Z]*[rR]|--recursive|--include)|rg\s)")

MESSAGE = """🔍 **재귀 코드 검색 — serena 먼저 검토했는가?** (CLAUDE.md: *Code navigation → Serena first*)

로드 한 줄:
```
ToolSearch({query: "select:mcp__plugin_serena_serena__find_symbol,mcp__plugin_serena_serena__find_referencing_symbols,mcp__plugin_serena_serena__get_symbols_overview,mcp__plugin_serena_serena__search_for_pattern", max_results: 4})
```

- 정의 찾기 → `find_symbol` / **영향 범위·참조 추적 → `find_referencing_symbols`**(grep 대체 불가)
- 파일 구조 → `get_symbols_overview` / 심볼 아닌 텍스트 → `search_for_pattern`

**grep 이 정당한 경우**: serena 인덱스 밖(`scripts/vendor/`, 외부 저장소, site-packages) · 비코드 파일(로그·JSON·바이너리). 해당하면 **이유를 한 줄 밝히고** 진행."""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        sys.exit(0)

    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        print(json.dumps({}))
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if PATTERN.search(command):
        print(json.dumps({"systemMessage": MESSAGE}))
    else:
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
