#!/usr/bin/env python3
"""국내 기준 공백 영역 보안 API 감지 시 OWASP 스킬 점검을 권하는 PostToolUse hook.

차단하지 않음. 경고만 출력하고 모든 경로에서 exit 0 함.

출력 채널이 둘이며 **수신자가 다르다** (공식 훅 문서 확인, 2026-09-18):
  · `systemMessage`                        → 사용자 화면에만 표시
  · `hookSpecificOutput.additionalContext` → 모델 컨텍스트에만 주입
어느 한쪽만 내면 상대에게 닿지 않는다. 이 훅의 목적이 "모델이 스킬을 로드하게
하는 트리거"이므로 additionalContext 가 필수이고, 사람이 훅의 동작을 관찰할 수
있어야 하므로 systemMessage 도 함께 낸다.
역할 분담: 이 훅은 "지금 이 코드를 점검하라"는 트리거만 담당하고, 판정 내용은
`owasp-masvs`·`owasp-asvs` 스킬에 위임함. 주석·리터럴 완전 분리 같은 판정 수준
분석을 훅에 넣으면 역할 분담이 무너지므로 하지 않음.

커버리지 한계 (훅이 조용하다고 점검이 끝난 것이 아님):
① 정규식은 존재하는 문자열만 잡으므로 `FLAG_SECURE` 미설정처럼 **부재가
   취약점인 항목**은 구조적으로 탐지 불가.
② `Bash` 명령이나 외부 프로세스가 같은 파일을 고치면 `Edit`·`Write` matcher 의
   PostToolUse 훅은 발동하지 않음 (Claude Code 훅 문서 명시).

성능 판단 근거 (IMPORTANT — 완화책 재발의 방지용):
훅 비용의 지배 항목은 python 인터프리터 기동이며, 패턴 매칭 여부·텍스트
길이와 무관하게 매 Edit/Write 마다 발생함. 즉 "파일을 다시 읽어 정확도를
올리자"류의 개선은 정확도 대비 기동 비용을 바꾸지 못하는 대신 훅의 책임을
트리거에서 판정으로 확장시킴. 실배포 후 측정으로 문제가 확인되기 전에는
어떤 완화책도 추가하지 않는다.

실측(2026-09-17, macOS/python3.14, 20회 평균): 호출당 18.3~18.5ms 이고 매칭
여부에 따른 차이는 0.2ms. 그중 16.4ms 가 순수 인터프리터 기동이다 — 비용의
약 89%가 기동이라는 위 판단이 측정으로 확인됨.
"""

from __future__ import annotations

import json
import re
import sys
from typing import NamedTuple

# 확장자 화이트리스트 — 게이트 최앞단. iOS(.swift 등)는 "제외 코드"가 아니라
# 미포함 상태다: 지원이 필요해지면 여기 한 줄 추가로 끝난다.
# 부수 효과가 핵심: 이 플러그인의 skills/*/SKILL.md 는 addJavascriptInterface
# 같은 취약 예시를 본문에 담는다. 화이트리스트가 없으면 플러그인 문서를 편집할
# 때마다 훅이 자기 문서에 경고를 쏘게 된다 (.md 는 여기서 자연히 걸러진다).
ALLOWED_EXTS = (".java", ".kt", ".kts", ".xml", ".gradle", ".json", ".js", ".ts")

# 테스트·샘플 경로 제외 — 테스트 코드는 취약 패턴을 의도적으로 담는 일이 흔하다
# (이 플러그인 스킬들의 취약 예시 코드와 같은 이치).
EXCLUDED_PATH = re.compile(r"_test\.|(^|/)(test|androidTest|sample)/")

# 행 선두 주석 제외 — 이 한 줄 휴리스틱에서 멈춘다. 블록 주석 추적·문자열
# 상태 기계로 가면 훅의 책임이 "트리거"에서 "판정"으로 넘어간다.
COMMENT_LINE = re.compile(r"^\s*(//|#|\*)")


class PatternEntry(NamedTuple):
    """탐지 패턴 1건. 위치 인덱스 대신 이름으로 읽게 해 필드 추가에 강건하게 둔다.

    check-consistency.py 의 불변식 11 이 이 클래스의 `skill` 필드를 이름으로
    읽는다 — 튜플 인덱스였을 때는 필드를 끼워넣어도 터지지 않고 엉뚱한 원소를
    읽어 "실재하지 않는 스킬 'MASVS-...' 참조" 같은 오도하는 실패를 냈다.
    """

    name: str          # 탐지명 (메시지에 그대로 노출)
    pattern: re.Pattern[str]
    skill: str         # 안내 대상 스킬 — 불변식 11 이 실재를 검사함
    ids: str           # 컨트롤/요구사항 ID
    domestic: str      # "대응" | "미기재"


# 패턴 테이블 — 국내 49개 기준이 덮지 못하는 공백 영역만 담는다 (SQLi·XSS·
# 경로조작 등 국내 대응 영역은 secure-coding-java 소관). 좁게 시작해 실사용
# 관찰 후 확대한다 — 6개 이내 유지.
#
# `domestic` 필드는 현재 전부 "미기재"다. 위 "공백 영역만" 원칙의 **예외**로
# 국내가 일부 대응하는 항목(딥링크·키 저장 계열)을 편입할 여지를 남겨 둔 것이며,
# 편입 전까지 "대응" 분기는 도달하지 않는다.
# ⚠️ 편입한다면 주석만 고쳐서는 안 된다 — 아래 두 곳이 함께 깨진다:
#   ① build_message 의 note 분기 — "대응"이면 "구속력 없음" 병기가 빠진다
#   ② README.md 의 훅 절 — 병기를 무조건 한다고 서술해 두었다
#   "일부 대응"을 "국내 기준 대응 항목"으로 단정하면 근거 과대 진술이 되므로,
#   편입 시 note 문구부터 다시 설계할 것.
#
# ⚠️ ID 는 컨트롤/요구사항까지만 쓴다 — 스킬 절 번호는 개정마다 움직이는
# 가장 약한 링크이므로 메시지에 넣지 않는다.
PATTERNS: tuple[PatternEntry, ...] = (
    PatternEntry(
        "WebView 설정",
        re.compile(r"addJavascriptInterface|setJavaScriptEnabled|setAllowFileAccess"),
        "owasp-masvs", "MASVS-PLATFORM-2 / MASWE-0033~0035", "미기재"),
    PatternEntry(
        "생체인증",
        re.compile(r"BiometricPrompt|setUserAuthenticationRequired"),
        "owasp-masvs", "MASVS-AUTH-2 / MASWE-0020~0022", "미기재"),
    PatternEntry(
        "인증서 피닝·TLS",
        re.compile(r"CertificatePinner|network_security_config|TrustManager"),
        "owasp-masvs", "MASVS-NETWORK-2 / MASWE-0028", "미기재"),
    PatternEntry(
        "JWT",
        re.compile(r"JWTVerifier|io\.jsonwebtoken|SignedJWT"),
        "owasp-asvs", "ASVS V9(Self-contained Tokens)", "미기재"),
    PatternEntry(
        "OAuth·OIDC",
        re.compile(r"code_verifier|PKCE|client_secret"),
        "owasp-asvs", "ASVS V10(OAuth and OIDC)", "미기재"),
    PatternEntry(
        "브라우저 보안 헤더",
        re.compile(r"Content-Security-Policy|Access-Control-Allow-Origin|SameSite"),
        "owasp-asvs", "ASVS V3(Web Frontend Security)", "미기재"),
)

# 메시지 줄 수 상한 = 헤더 1 + 엔트리 MAX_ENTRIES + 꼬리 1 = 5줄.
# 상한을 코드로 강제하지 않으면 패턴을 6개까지 채우는 순간 동결된 "5줄 이내"
# 제약이 아무도 모르게 깨진다 (6개 전부 매칭 시 8줄).
MAX_ENTRIES = 3


def normalize(data: object) -> tuple[str, str] | None:
    """stdin JSON 에서 (file_path, 검사 대상 텍스트)를 추출함. 비대상이면 None.

    Write 는 tool_input.content(파일 전체), Edit 는 tool_input.new_string
    (변경분)으로 텍스트가 온다 — 필드 차이를 여기서 흡수해 이후 판정은
    단일 경로로 유지한다 (분기가 판정부까지 새면 테스트가 두 배가 된다).
    """
    if not isinstance(data, dict):
        return None
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not path:
        return None
    tool_name = data.get("tool_name")
    if tool_name == "Write":
        text = tool_input.get("content")
    elif tool_name == "Edit":
        text = tool_input.get("new_string")
    else:
        return None
    if not isinstance(text, str):
        return None
    return path, text


def find_matches(path: str, text: str) -> list[PatternEntry]:
    """(path, text) -> 매칭 엔트리 목록. 순수 판정 — 파일 I/O·JSON 없음.

    게이트 순서: ① 확장자 화이트리스트 ② 테스트·샘플 경로 제외
    ③ 행 선두 주석 제거 후 패턴 매칭.
    """
    if not path.endswith(ALLOWED_EXTS):
        return []
    if EXCLUDED_PATH.search(path):
        return []
    code = "\n".join(
        line for line in text.splitlines() if not COMMENT_LINE.match(line)
    )
    return [entry for entry in PATTERNS if entry.pattern.search(code)]


def note_for(entry: PatternEntry) -> str:
    """국내 대응 여부 표기 — "구속력 없음" 병기 규약을 이 한 곳에만 둔다.

    사용자용·모델용 두 템플릿이 각자 문구를 쓰면 규약이 복제되고, 불변식 8 은
    .md 만 검사해 기계도 누락을 못 잡는다. 두 템플릿 모두 이 함수를 쓴다.
    """
    if entry.domestic == "대응":
        return "국내 기준 대응 항목"
    return "국내 원문 미기재 — 현행 점검 권장(구속력 없음)"


def fold(matches: list[PatternEntry]) -> tuple[list[PatternEntry], int]:
    """(노출할 엔트리, 접힌 건수). 두 템플릿이 같은 상한을 쓰게 한다."""
    shown = matches[:MAX_ENTRIES]
    return shown, len(matches) - len(shown)


def build_message(matches: list[PatternEntry]) -> str:
    """사용자 화면용 메시지 — `systemMessage` 로 나간다 (모델에는 닿지 않음).

    엔트리는 MAX_ENTRIES 개까지만 나열하고 초과분은 꼬리 줄에 건수로 접는다 —
    줄을 새로 만들지 않아야 5줄 상한이 유지된다.
    """
    shown, overflow = fold(matches)
    lines = ["🔐 **시큐어코딩 점검 힌트** — 방금 쓴 코드가 다음 점검 대상에 해당함:"]
    for entry in shown:
        lines.append(f"- {entry.name}: `{entry.skill}` 스킬 · {entry.ids} — {note_for(entry)}")
    tail = "위반 확정이 아니라 점검 유도임 — 해당 스킬을 로드해 컨트롤 원문 기준으로 확인할 것."
    if overflow:
        tail = f"(외 {overflow}건 더 매칭됨) {tail}"
    lines.append(tail)
    return "\n".join(lines)


def build_context(matches: list[PatternEntry]) -> str:
    """모델 컨텍스트용 문자열 — `hookSpecificOutput.additionalContext` 로 나간다.

    `systemMessage` 는 사용자 화면 전용이라 모델에 닿지 않는다(공식 훅 문서).
    이 훅의 목적은 "해당 스킬을 로드하게 하는 트리거"이므로 모델용 채널이
    따로 필요하다 — 둘은 대체재가 아니라 수신자가 다른 별개 채널이다.

    ⚠️ 어조는 **사실 서술**로 유지한다. "…하라" 같은 명령형은 프롬프트 인젝션
    방어에 걸려, 모델이 컨텍스트로 쓰지 않고 사용자에게 노출해 버린다.
    """
    shown, overflow = fold(matches)
    lines = ["방금 쓴 코드에 국내 49개 보안약점 기준이 다루지 않는 영역의 API 가 있다."]
    for entry in shown:
        lines.append(
            f"- {entry.name}: `{entry.skill}` 스킬이 {entry.ids} 를 다룬다. {note_for(entry)}.")
    tail = "이 표기는 위반 확정이 아니라 점검 대상 식별이며, 판정 근거는 해당 스킬이 보유한다."
    if overflow:
        tail = f"매칭 {overflow}건이 더 있다. {tail}"
    lines.append(tail)
    return "\n".join(lines)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        sys.exit(0)

    normalized = normalize(data)
    if normalized is None:
        print(json.dumps({}))
        sys.exit(0)

    matches = find_matches(*normalized)
    if matches:
        # 두 채널 모두에 낸다 — systemMessage 는 사용자 화면, additionalContext 는
        # 모델 컨텍스트. 어느 한쪽만으로는 상대에게 닿지 않는다.
        print(json.dumps({
            "systemMessage": build_message(matches),
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": build_context(matches),
            },
        }))
    else:
        print(json.dumps({}))

    sys.exit(0)


if __name__ == "__main__":
    main()
