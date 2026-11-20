"""리포트·체크리스트·카탈로그 표 → Markdown 문자열(순수 함수)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from port_metrics import judge
from port_metrics.catalog import STAGES, Catalog, MetricSpec
from port_metrics.report import Item, ReportModel, RunInfo, rule_label

MARK_BEGIN = "<!-- port-metrics:catalog-table:begin -->"
MARK_END = "<!-- port-metrics:catalog-table:end -->"
_ITEM_HEAD = ("지표", "대상", "문맥", "서브셋·텐서", "값", "단위", "상태")
_PROBLEM_STATUSES = (judge.FAIL, judge.INVALID, judge.NOT_ESTABLISHED)
_CALL_PATH_STAGES = frozenset({"S3", "S4", "S5"})  # 호출 경로(CLI·앱 JNI)가 갈리는 단계


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(head: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return lines


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _item_name(item: Item) -> str:
    """지표 표기. 균형 항목은 같은 지표의 회차·ABBA 항목과 구분되게 이름을 덧붙임."""
    return f"`{item.metric}`" + (" 예상 fail 균형" if item.kind == "balance" else "")


def _item_rows(items: Iterable[Item], reason: bool = False) -> list[list[object]]:
    rows: list[list[object]] = []
    for i in items:
        # 예상 fail 표지는 이 함수 한 곳에서만 붙임
        row: list[object] = [
            _item_name(i),
            i.ref or "(누락)",
            i.context,
            i.subset or "-",
            _fmt(i.value),
            i.unit,
            i.status + ("(예상)" if i.is_expected_fail else ""),
        ]
        if reason:
            row.append(i.reason)
        rows.append(row)
    return rows


def _identity_text(run: RunInfo, key: str) -> str:
    value = run.identity.get(key)
    if value is None or value == "":
        return "(누락)"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _call_path_text(run: RunInfo) -> str:
    """S3~S5 는 미기록을 드러내고, 호출 경로가 하나뿐인 S1·S2 는 "-". (누락) 은 필수 키 전용."""
    value = run.identity.get("call_path")
    if value:
        return str(value)
    return "(미기록)" if run.stage in _CALL_PATH_STAGES else "-"


def _input_set_text(run: RunInfo) -> str:
    sha = run.identity.get("manifest_sha256")
    short = str(sha)[:12] if sha else "(누락)"
    name = run.identity.get("manifest_name")
    return f"{name} ({short})" if name else short


def _validity_text(run: RunInfo) -> str:
    """§1 유효성 칸. 대체된 회차는 대체 표시를 덧붙임(열은 늘리지 않음)."""
    text = "invalid" if run.problems else "ok"
    if run.superseded_by is None:
        return text
    text += f" · 대체됨 → {run.superseded_by}({run.superseded_reason})"
    if not run.problems and not run.sampler_problems:
        # 대체 회차는 원자료를 읽지 않아 신원·열 검사만 통과한 것임을 드러냄
        text += " · 신원·열 검사 통과 회차 대체(원자료 품질 미검사)"
    return text


def _summary_names(items: Iterable[Item]) -> list[str]:
    """§0 지표 목록 표기(지표 ID 순 — 균형 항목은 같은 지표 뒤에 구분해 실음)."""
    keys = sorted({(i.metric, i.kind == "balance") for i in items})
    return [f"`{m}`" + (" 예상 fail 균형" if balance else "") for m, balance in keys]


def _summary_problem_lines(model: ReportModel) -> list[str]:
    """§0 상태별 지표 목록. 예상 fail 이 없으면 1.0.24 와 같은 줄."""
    lines: list[str] = []
    for status in _PROBLEM_STATUSES:
        found = [i for i in model.items if i.status == status]
        if status == judge.FAIL and model.expected_fail:
            names = _summary_names(i for i in found if not i.is_expected_fail)
            if names:
                lines += ["", "- 예상 밖 fail 지표: " + ", ".join(names)]
            expected = {
                (i.metric, i.context): i.expected_fail
                for i in found
                if i.is_expected_fail
            }
            for (metric, context), reason in sorted(expected.items()):
                lines += [
                    "",
                    f"- 예상 fail(사전 등록) `{metric}` @ {context}: {_cell(reason)}",
                ]
            continue
        names = _summary_names(found)
        if names:
            lines += ["", f"- {status} 지표: " + ", ".join(names)]
    if model.expected_rules:
        lines += ["", f"- 등록된 예상 fail 규칙: {len(model.expected_rules)} 건"]
        lines += [
            f"  - {_cell(r.label)}: {_cell(r.reason)} — "
            f"덮은 항목 {r.covered}, fail {r.failed}"
            for r in model.expected_rules
        ]
    superseded = sum(r.superseded_by is not None for r in model.runs)
    if superseded:
        lines += ["", f"- 대체 회차 {superseded} 건(판정 제외)"]
    return lines


def _section(title: str, items: Sequence[Item]) -> list[str]:
    lines = ["", f"## {title}", ""]
    if not items:
        return lines + ["- 해당 항목 없음"]
    return lines + _table(_ITEM_HEAD, _item_rows(items))


def render_report(model: ReportModel) -> str:
    """리포트 모델 → Markdown(절 0~9)."""
    measured = [i for i in model.items if i.kind != "missing"]
    lines = [f"# port-metrics 리포트 — {model.project}", ""]
    lines += ["## 0. 요약", ""]
    if model.partial is not None:
        stages = ", ".join(model.partial)
        lines.append(
            f"- **부분 리포트**: 필수 검사를 {stages} 로 축소함(전체 판정 아님)"
        )
    scope = model.scope
    overall = f"- 종합 판정: **{model.overall}** (종료 코드 {model.exit_code})"
    if model.expected_fail:
        overall += (
            f" — 예상 fail {model.expected_fail} 건을 pass 로 봄(원판정 fail 보존)"
        )
    lines += [
        overall,
        f"- 태스크 지표: {model.task_metric}",
        f"- 범위: stages {', '.join(scope['stages'])} / 목적 "
        f"{', '.join(scope['purposes']) or '-'} / 유형 "
        f"{', '.join(scope['model_types']) or '-'} / 입력 {scope['input_kind']}",
        f"- 임계 동결: {model.frozen_at or '미동결(전 판정 not_established)'}",
        f"- 임계 파일: `{model.thresholds_path or '-'}`",
        f"- thresholds sha256: `{model.thresholds_sha}`",
        "- 유효성 한도: "
        + ", ".join(f"{k} = {_fmt(v)}" for k, v in model.validity.items()),
        f"- 카탈로그 기본 규칙과 다른 규칙: {len(model.rule_deviations)} 건",
    ]
    lines += [f"  - {_cell(text)}" for text in model.rule_deviations]
    lines.append("")
    lines += _table(("상태", "건수"), model.counts.items())
    lines += _summary_problem_lines(model)

    lines += ["", "## 1. 측정 신원", ""]
    run_rows = [
        (
            r.run_id,
            r.stage,
            r.backend,
            r.run_kind,
            r.pacing,
            r.profile,
            f"{r.effective} ({r.precision_class})",
            r.started_at,
            r.identity.get("git_sha", "-"),
            _validity_text(r),
        )
        for r in model.runs
    ]
    head = ("회차", "단계", "백엔드", "종류", "pacing", "프로파일", "실효(class)")
    lines += _table(head + ("시작", "git_sha", "유효성"), run_rows)
    lines += [
        "",
        "- 호출 경로 = `identity.call_path`(S3~S5) · 입력 집합 = `manifest_name` "
        "(`manifest_sha256` 앞 12자)",
        "",
    ]
    lines += _table(
        ("회차", "호출 경로", "입력 집합"),
        [(r.run_id, _call_path_text(r), _input_set_text(r)) for r in model.runs],
    )

    lines += _section("2. 단계 사슬 동등성", [i for i in measured if i.kind == "pair"])
    runs = [i for i in measured if i.kind == "run"]
    lines += _section("3. 태스크 정확도", [i for i in runs if i.category == "ACC"])
    lines += _section("4. 속도", [i for i in runs if i.category == "SPD"])
    lines += _section("5. 자원", [i for i in runs if i.category in ("RES", "PWR")])
    lines += _section(
        "6. A/B(같은 세션 ABBA)",
        [i for i in measured if i.kind in ("abba", "balance")],
    )
    for abba_id, problems in model.abba_problems.items():
        lines += ["", f"- ABBA `{abba_id}` invalid: " + "; ".join(problems)]

    conditions = [i for i in runs if i.category in ("THM", "MQ", "STB", "CNV")]
    lines += _section("7. 측정 조건", conditions)
    lines.append("")
    if "S5" in scope["stages"]:
        lines.append(
            "- S4↔S5 성능 차 = JNI + 프로세스 상태 합산 효과(JNI 오버헤드로 해석하지 않음)"
        )
    core_rows = [
        (
            r.run_id,
            r.stage,
            _identity_text(r, "cpus_allowed"),
            *(
                _identity_text(r, key) if r.stage == "S5" else "-"
                for key in ("cpuset", "proc_state", "core_distribution")
            ),
        )
        for r in model.runs
        if r.stage in ("S4", "S5")
    ]
    if core_rows:
        core_head = ("회차", "단계", "cpus_allowed", "cpuset", "proc_state")
        lines += [""] + _table(core_head + ("core_distribution",), core_rows)
    thermal_rows = [
        (
            r.run_id,
            _fmt(r.thermal.get("start_battery_c")),
            _fmt(r.thermal.get("clock_restored")),
            _fmt(r.thermal.get("wait_sec")),
            _fmt(r.thermal.get("pause_events")),
            r.thermal.get("source", "-"),
        )
        for r in model.runs
        if r.thermal is not None
    ]
    if thermal_rows:
        thermal_head = ("회차", "시작 배터리 degC", "클럭 복구", "대기 s", "정지 횟수")
        lines += [""] + _table(thermal_head + ("출처",), thermal_rows)
    for r in model.runs:
        if r.problems:
            lines += ["", f"- 회차 `{r.run_id}` invalid: " + "; ".join(r.problems)]
        if r.sampler_problems:
            text = "; ".join(r.sampler_problems)
            lines += ["", f"- 회차 `{r.run_id}` sampler 지표 invalid: {text}"]

    lines += ["", "## 8. 판정 상세", ""]
    judged = [i for i in model.items if i.status != judge.RECORD_ONLY]
    if judged:
        order = {s: n for n, s in enumerate(_PROBLEM_STATUSES + (judge.PASS,))}
        judged.sort(key=lambda i: order[i.status])
        lines += _table(_ITEM_HEAD + ("근거",), _item_rows(judged, reason=True))
    else:
        lines.append("- 판정 대상 0 건(종료 코드 1)")

    lines += ["", "## 9. 누락 지표", ""]
    if model.missing:
        lines += [
            f"- `{label.split(' @ ')[0]}` @ {label.split(' @ ')[1]}"
            for label in model.missing
        ]
    else:
        lines.append("- 없음")
    return "\n".join(lines) + "\n"


def _level(spec: MetricSpec) -> str:
    tags = spec.purposes + spec.model_types
    return spec.level + (f"({'·'.join(tags)})" if tags else "")


def _when_text(when: Mapping[str, Any]) -> str:
    return ", ".join(f"{k}={v}" for k, v in when.items()) or "(전체)"


def render_checklist(catalog: Catalog, thresholds: Mapping[str, Any]) -> str:
    """thresholds scope 기준 측정 전 체크리스트(필수 지표·미기입 임계)."""
    scope = thresholds["scope"]
    reqs = catalog.required(scope, None)
    frozen = thresholds.get("frozen_at")
    lines = [
        "# port-metrics 측정 체크리스트",
        "",
        f"- 범위: stages {', '.join(scope['stages'])} / 목적 "
        f"{', '.join(scope['purposes']) or '-'} / 유형 "
        f"{', '.join(scope['model_types']) or '-'} / 입력 {scope['input_kind']}",
        f"- 임계 동결: {frozen or '미동결 — 측정 전에 frozen_at 을 기입하고 커밋'}",
        "- 회차마다 identity.thresholds_sha256 = 동결 파일 sha256 기록",
    ]
    stages = set(scope["stages"])
    if stages & _CALL_PATH_STAGES:
        lines.append(
            "- S3~S5 회차마다 identity.call_path = 호출 경로(`cli:<바이너리>` · `app:<클래스>→<so>`) 기록"
        )
    if {"S3", "S4"} <= stages:
        lines.append(
            "- 입력 집합은 identity.manifest_sha256(+ manifest_name)으로 대조 — 단말 결과는 같은 "
            "manifest 의 S3-S4 chain pair 로 host 와 비교"
        )
    for stage in STAGES:
        ids = [m for m, s in reqs.run if s == stage]
        if not ids:
            continue
        lines += ["", f"## {stage} 회차 지표", ""]
        rows = []
        for metric in ids:
            spec = catalog.get(metric)
            rows.append(
                (
                    f"- [ ] `{metric}`",
                    spec.name,
                    spec.run_kind,
                    spec.source,
                    ", ".join(spec.inputs),
                )
            )
        lines += _table(("지표", "이름", "회차 종류", "출처", "필요 원자료"), rows)
    if reqs.pair:
        lines += ["", "## 비교(pair) 지표", ""]
        pair_rows = [
            (
                f"- [ ] `{metric}`",
                catalog.get(metric).name,
                ctx,
                f"S1→{target}" if ctx == "base" else "-",
            )
            for metric, ctx, target in reqs.pair
        ]
        lines += _table(("지표", "이름", "문맥", "base 대상"), pair_rows)
    if reqs.abba:
        lines += ["", "## ABBA(같은 세션 3 쌍 이상, AB·BA 둘 다)", ""]
        limits = thresholds.get("abba_limits_pct", {})
        abba_rows = [
            (f"- [ ] `{m}`", catalog.get(m).name, _fmt(limits.get(m)))
            for m in reqs.abba
        ]
        lines += _table(("지표", "이름", "허용 열화 %"), abba_rows)
    todo: list[str] = []
    for rule in thresholds.get("rules", []):
        if rule["op"] == "record":
            continue
        label = f"`{rule['metric']}` [{_when_text(rule['when'])}]"
        if rule["limit"] is None:
            todo.append(f"- [ ] {label}: limit 기입")
        spec = catalog.get(rule["metric"])
        if judge.needs_noise_floor(
            spec, judge.rule_from(rule), rule["when"].get("pair"), scope["purposes"]
        ):
            todo.append(f"- [ ] {label}: noise_floor 기입(convert)")
    lines += ["", "## 동결 전 기입할 임계", ""]
    lines += todo or ["- 없음"]
    expected = [r for r in thresholds.get("rules", []) if "expected_fail" in r]
    if expected:
        # 예상 fail 은 측정 전에만 등록(측정 뒤 추가 = 사후 완화) — 매번 드러냄
        lines += ["", "## 등록된 예상 fail 규칙", ""]
        lines += [f"- {rule_label(r)}: {r['expected_fail']}" for r in expected]
    return "\n".join(lines) + "\n"


def _rule_text(rule: Mapping[str, Any]) -> str:
    if rule["op"] == "record":
        return "record"
    limit = "null(프로젝트 기입)" if rule["limit"] is None else _fmt(rule["limit"])
    return f"{rule['op']} {limit}"


def render_catalog_table(catalog: Catalog) -> str:
    """catalog.json → metric-catalog.md 생성 구간(지표 표 + 기본 규칙 표)."""
    lines = ["", f"### 지표 표({len(catalog.metrics)} 종)", ""]
    metric_rows = [
        (
            f"`{m.id}`",
            m.name,
            _level(m),
            m.scope,
            " ".join(m.stages),
            "·".join(m.input_kinds),
            f"{m.source}/{m.run_kind}",
            f"{m.value_type}, {m.unit}",
            m.direction,
            "판정" if m.judged else "기록",
            "-" if m.abba_limit_pct is None else _fmt(m.abba_limit_pct),
            "·".join(m.abba_required_for) or "-",
        )
        for m in catalog.metrics
    ]
    head = ("id", "이름", "수준", "범위", "단계·문맥", "입력", "출처/회차", "형, 단위")
    lines += _table(head + ("방향", "판정", "ABBA %", "ABBA 필수 목적"), metric_rows)
    lines += ["", "### 기본 규칙 표", ""]
    rule_rows = [
        (f"`{m.id}`", _when_text(rule["when"]), _rule_text(rule))
        for m in catalog.metrics
        for rule in m.default_rules
    ]
    lines += _table(("지표", "조건(when)", "규칙"), rule_rows)
    lines += [
        "",
        "- 규칙이 없는 판정 지표 값은 not_established, 기록 지표는 record_only",
    ]
    return "\n".join(lines) + "\n\n"


def extract_generated(text: str) -> str | None:
    """문서의 생성 구간(마커 사이, 마커 줄 제외). 마커가 없으면 None."""
    begin = text.find(MARK_BEGIN)
    end = text.find(MARK_END)
    if begin < 0 or end < begin:
        return None
    region = text[begin + len(MARK_BEGIN) : end]
    return region[1:] if region.startswith("\n") else region


def replace_generated(text: str, table: str) -> str:
    """문서의 생성 구간을 table 로 교체(마커 밖은 그대로)."""
    begin = text.find(MARK_BEGIN)
    end = text.find(MARK_END)
    if begin < 0 or end < begin:
        raise ValueError("생성 구간 마커를 찾지 못함")
    return text[: begin + len(MARK_BEGIN)] + "\n" + table + text[end:]
