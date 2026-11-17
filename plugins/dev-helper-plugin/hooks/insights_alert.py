#!/usr/bin/env python3
"""SessionStart hook — claude-insights 의 미해결 알림(alerts.json active)을 한 줄로 표시.

리포트 파이프라인은 Claude 로그인이 끊기면 메일(SMTP)로 알리지만, 메일을 놓친 경우를 위해
세션 시작 때 한 번 더 보여 준다. 저장소·알림이 없으면 출력하지 않는다. 모든 경로 exit 0.
출력은 `systemMessage`(사용자 화면 전용)만 쓴다 — 모델 컨텍스트를 쓰지 않는다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_CANDIDATES = ("/workspace/work/claude/claude-insights", "~/work/claude/claude-insights")
_KIND_TEXT = {"relogin": "재로그인 필요", "expiring": "로그인 만료 임박",
              "container_down": "컨테이너 중지", "lock_busy": "실행 중복",
              "run_failed": "생성 실패", "env_sync": "환경 동기화 확인 필요"}
_TARGET_TEXT = {"host": "호스트", "env": "호스트↔voiceguard", "report": "리포트 실행"}
_STEPS = {"relogin": "`claude auth login`(호스트) 또는 "
                     "`docker exec -it voiceguard /root/.local/bin/claude auth login`",
          "expiring": "만료 전에 재로그인",
          "container_down": "`docker start voiceguard`"}


def _repo() -> Path | None:
    env = os.environ.get("CLAUDE_INSIGHTS_DIR")
    for raw in ([env] if env else []) + list(_CANDIDATES):
        path = Path(raw).expanduser()
        if (path / "reports" / "state" / "alerts.json").is_file():
            return path
    return None


def main() -> int:
    try:
        repo = _repo()
        if repo is None:
            return 0
        alerts = json.loads((repo / "reports" / "state" / "alerts.json").read_text("utf-8"))
        active = [(key.partition("|")[0], key.partition("|")[2], value)
                  for key, value in alerts.items()
                  if isinstance(value, dict) and value.get("active")]
        if not active:
            return 0
        parts = []
        for target, kind, value in active:
            name = _TARGET_TEXT.get(target, target)
            step = _STEPS.get(kind, "")
            since = str(value.get("since", ""))[:16]
            parts.append(f"{_KIND_TEXT.get(kind, kind)} — {name} (since {since})"
                         + (f": {step}" if step else ""))
        print(json.dumps({"systemMessage": "⚠️ claude-insights 리포트: " + " · ".join(parts)},
                         ensure_ascii=False))
    except Exception:  # 훅 실패가 세션 시작을 방해하지 않게 함
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
