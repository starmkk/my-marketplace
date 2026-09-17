#!/usr/bin/env python3
"""secure-coding-plugin 정합성 검사.

이 플러그인은 진단 보고서 작성을 위해 기준번호·CWE를 언어별 스킬에 **의도적으로 복제**한다
(허브만 정본으로 두면 언어 스킬을 단독으로 쓸 수 없기 때문). 복제의 대가는 '낡음'이므로,
이 스크립트가 정본(secure-coding-kr/references/weakness-49.md)과의 어긋남을 잡는다.

사용법:
    python3 plugins/secure-coding-plugin/scripts/check-consistency.py
종료 코드: 0 = 통과, 1 = 문제 발견
"""

import importlib.util
import json
import pathlib
import re
import sys

# 불변식 11 이 훅 모듈을 import 한다 — 그 부산물로 hooks/__pycache__ 가 생기지
# 않게 막는다. 프로세스 전역 설정이므로 main() 중간이 아니라 여기서 선언한다.
sys.dont_write_bytecode = True

PLUGIN = pathlib.Path(__file__).resolve().parent.parent
SKILLS = PLUGIN / "skills"
CANON = SKILLS / "secure-coding-kr" / "references" / "weakness-49.md"

# frontmatter 예산: 스펙 한도는 1024자이나, 이 마켓플레이스 기존 스킬 최대치(801자)에 맞춰
# 850자를 운영 목표로 둔다. 초과하면 오발동 비용과 상시 로드 비용이 함께 커진다.
FM_BUDGET = 850

# 본문 줄수 상한: 트리거 1회당 컨텍스트에 들어가는 양. 넘으면 references로 내릴 후보다.
BODY_LIMIT = 650

# 과거 제거한 '빈 약속' — description이 트리거하는데 본문에 내용이 없던 표현.
BANNED_TRIGGERS = ["MISRA", "GPKI", "행정전자서명"]

# 제도 판정과 기술 권고를 뒤섞었던 표현. 재발하면 사용자가 부적합 판정을 받을 수 있다.
BANNED_PHRASES = ["최신 권고가 우선한다"]

# OWASP 계열 스킬(owasp-*)의 references 출처 고지 요건.
# 근거 문서가 CC BY-SA 4.0 이므로 저작자표시가 의무다. 국내 가이드(관행상 페이지 인용)와 달리
# 기계로 강제해야 누락이 남지 않는다. 버전·조회일까지 묶는 이유는 상류가 수시로 바뀌기 때문 —
# MASWE 는 main 브랜치에서 이미 78개를 넘어섰고 프로파일도 늘었다.
OWASP_PREFIX = "owasp-"
NOTICE_HEAD = 15           # 고지는 파일 상단에 있어야 읽는 쪽이 먼저 본다
NOTICE_KEYS = ["출처", "버전", "조회일", "CC BY-SA 4.0"]

problems: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def parse_frontmatter(path: pathlib.Path) -> tuple[str, str]:
    """(frontmatter 원문, 본문) 반환."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        fail(f"{path.relative_to(PLUGIN)}: frontmatter 없음")
        return "", text
    return m.group(1), text[m.end():]


def canonical_criteria() -> dict[str, set[str]]:
    """정본에서 '기준번호 -> {CWE...}' 추출. 총괄표의 파이프 테이블 행만 읽는다."""
    table: dict[str, set[str]] = {}
    for line in CANON.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        cwes = set(re.findall(r"CWE-\d+", line))
        if cwes:
            table.setdefault(cells[0], set()).update(cwes)
    return table


def main() -> int:
    if not CANON.exists():
        fail(f"정본 파일 없음: {CANON.relative_to(PLUGIN)}")
        print_report()
        return 1

    canon = canonical_criteria()
    notes.append(f"정본에서 기준 {len(canon)}개 / CWE {sum(len(v) for v in canon.values())}개 추출")

    # 1) JSON 유효성
    for jf in [PLUGIN / ".claude-plugin" / "plugin.json"]:
        try:
            json.loads(jf.read_text())
        except json.JSONDecodeError as e:
            fail(f"{jf.relative_to(PLUGIN)}: JSON 파싱 실패 — {e}")

    skill_dirs = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    names = {d.name for d in skill_dirs}

    for d in skill_dirs:
        skill = d / "SKILL.md"
        rel = skill.relative_to(PLUGIN)
        if not skill.exists():
            fail(f"{d.name}: SKILL.md 없음")
            continue

        fm, body = parse_frontmatter(skill)

        # 2) frontmatter 예산 — 상시 로드 비용
        if len(fm) > FM_BUDGET:
            fail(f"{rel}: frontmatter {len(fm)}자 > 예산 {FM_BUDGET}자")

        # 3) name과 디렉터리 일치
        nm = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
        if not nm:
            fail(f"{rel}: name 필드 없음")
        elif nm.group(1) != d.name:
            fail(f"{rel}: name '{nm.group(1)}' != 디렉터리 '{d.name}'")

        # 4) 본문 비대 — 트리거 1회당 비용
        if len(body.splitlines()) > BODY_LIMIT:
            fail(f"{rel}: 본문 {len(body.splitlines())}줄 > 상한 {BODY_LIMIT}줄 "
                 f"(references로 내릴 덩어리 검토)")

        # 5) 빈 약속 — 트리거하는데 본문에 내용이 없는 표현
        for word in BANNED_TRIGGERS:
            if word in fm and word not in body:
                fail(f"{rel}: 빈 약속 '{word}' — description에만 있고 본문에 없음")

        # 6) references 상호참조.
        #    언어별 스킬은 허브의 weakness-49.md를 교차 참조하므로, 인용된 파일이
        #    자기 references 에 없더라도 다른 스킬에 있으면 정상이다.
        refdir = d / "references"
        actual = {p.name for p in refdir.glob("*.md")} if refdir.exists() else set()
        elsewhere = {p.name for p in SKILLS.glob("*/references/*.md")} - actual
        cited = set(re.findall(r"references/([\w.-]+\.md)", body))
        for miss in sorted(cited - actual - elsewhere):
            fail(f"{rel}: 어느 스킬에도 없는 references/{miss} 참조")
        for orphan in sorted(actual - cited):
            fail(f"{rel}: references/{orphan} 가 본문에서 참조되지 않음")

        # 7) 기준번호-CWE 정합성 — 복제본이 정본과 어긋나는지.
        #    '기준#' 열을 가진 표를 찾고, 그 표의 데이터 행 첫 칸을 기준번호로 읽는다.
        #    (데이터 행은 "| 1 | SQL 삽입 | CWE-89 |" 처럼 '기준' 문구 없이 숫자만 온다.)
        in_table = False
        checked = 0
        for line in body.splitlines():
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if any(c.replace(" ", "").startswith("기준#") for c in cells):
                in_table = True           # 헤더 행
                continue
            if not in_table or set(line) <= set("|- :"):
                continue                  # 구분선
            if not cells or not cells[0].isdigit():
                continue
            num = cells[0]
            cwes = set(re.findall(r"CWE-\d+", line))
            if not cwes:
                continue
            checked += 1
            if num not in canon:
                fail(f"{rel}: 기준 {num} 은 정본에 없음 — {line.strip()[:70]}")
            elif not cwes & canon[num]:
                fail(f"{rel}: 기준 {num} CWE 불일치 — 문서 {sorted(cwes)} vs "
                     f"정본 {sorted(canon[num])}")
        if checked:
            notes.append(f"{d.name}: 기준#-CWE 행 {checked}건 정본 대조")

    # 8) 제도/기술 권고를 뒤섞는 표현 재발 검사
    for md in sorted(PLUGIN.rglob("*.md")):
        text = md.read_text()
        for phrase in BANNED_PHRASES:
            if phrase in text:
                fail(f"{md.relative_to(PLUGIN)}: 금지 표현 '{phrase}' — "
                     f"제도 판정과 기술 권고를 분리해 서술할 것")

    # 9) 스킬 간 상호링크 (고립 스킬 탐지)
    for d in skill_dirs:
        text = (d / "SKILL.md").read_text()
        linked = {n for n in names if n != d.name and f"`{n}`" in text}
        if not linked:
            fail(f"{d.name}: 다른 스킬을 하나도 링크하지 않음 (라우팅 고립)")
        else:
            notes.append(f"{d.name} → {len(linked)}개 스킬 링크")

    # 10) OWASP references 출처 고지 — CC BY-SA 4.0 저작자표시 의무를 기계로 강제.
    #     주 출처 1개를 지정하고 부출처는 본문에 병기한다(문서가 여럿인 파일이 있다).
    checked_notices = 0
    for d in skill_dirs:
        if not d.name.startswith(OWASP_PREFIX):
            continue
        for ref in sorted((d / "references").glob("*.md")):
            head = "\n".join(ref.read_text().splitlines()[:NOTICE_HEAD])
            missing = [k for k in NOTICE_KEYS if k not in head]
            rel = ref.relative_to(PLUGIN)
            if missing:
                fail(f"{rel}: 출처 고지 누락 {missing} — 상단 {NOTICE_HEAD}줄 안에 "
                     f"출처·버전·조회일·라이선스를 모두 적을 것")
            else:
                checked_notices += 1
    if checked_notices:
        notes.append(f"OWASP references 출처 고지 {checked_notices}건 확인")

    # 11) 훅 → 스킬 라우팅 정합성 — 훅은 트리거만 담당하고 판정은 스킬에 위임하므로,
    #     스킬 삭제·개명 시 훅 메시지가 죽은 곳을 가리키게 된다. 이를 기계로 잡는다.
    #     텍스트 추출 대신 import 로 패턴 테이블을 직접 읽는 이유: 테이블 서식이
    #     바뀌어도 검사가 조용히 무력화되지 않는다 (import 실패는 시끄럽게 죽는다).
    #     hooks/ 미보유 상태(과거 판본·방어적)에서도 통과해야 하므로 존재 검사 선행.
    hook_py = PLUGIN / "hooks" / "secure_coding_hint.py"
    if hook_py.exists():
        spec = importlib.util.spec_from_file_location("secure_coding_hint", hook_py)
        if spec is None or spec.loader is None:
            fail("hooks/secure_coding_hint.py: 모듈 스펙을 만들 수 없음 — 파일 손상 여부 확인")
        else:
            hook_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(hook_mod)
            # 위치 인덱스가 아니라 필드명으로 읽는다 — PatternEntry 에 필드가
            # 추가돼도 이 검사가 엉뚱한 원소를 읽지 않는다.
            hook_skills = {entry.skill for entry in hook_mod.PATTERNS}
            for missing_skill in sorted(hook_skills - names):
                fail(f"hooks/secure_coding_hint.py: 실재하지 않는 스킬 '{missing_skill}' 참조 — "
                     f"스킬 개명·삭제 시 훅 패턴 테이블도 함께 고칠 것")
            if hook_skills <= names:
                notes.append(f"훅 패턴 {len(hook_mod.PATTERNS)}개 → 스킬 {len(hook_skills)}종 실재 확인")

    print_report()
    return 1 if problems else 0


def print_report() -> None:
    for n in notes:
        print(f"  · {n}")
    print()
    if problems:
        print(f"문제 {len(problems)}건:")
        for p in problems:
            print(f"  [FAIL] {p}")
    else:
        print("정합성 검사 통과")


if __name__ == "__main__":
    sys.exit(main())
