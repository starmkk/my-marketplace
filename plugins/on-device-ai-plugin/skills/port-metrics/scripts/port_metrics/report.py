"""results + thresholds → 리포트 모델 조립(원자료 행은 주입된 load_rows 로만 읽음)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from port_metrics import calc, judge, schema
from port_metrics.catalog import Catalog, MetricSpec

Obj = dict[str, Any]
Value = float | bool | None
LoadRows = Callable[[str], list[Obj]]
_STATUS_ORDER = (
    judge.PASS,
    judge.FAIL,
    judge.INVALID,
    judge.NOT_ESTABLISHED,
    judge.RECORD_ONLY,
)


@dataclass(frozen=True)
class Item:
    """판정 항목 1 건.

    kind = run|pair|abba|missing, ref = run_id·pair_id·abba_id, context = stage 또는
    pair 문맥, stage = 회차 stage(pair 는 target stage), subset = 서브셋 또는 텐서 이름.
    """

    metric: str
    kind: str
    ref: str
    context: str
    stage: str
    subset: str | None
    value: Value
    unit: str
    status: str
    reason: str
    category: str


@dataclass(frozen=True)
class RunInfo:
    """리포트에 싣는 회차 신원·유효성."""

    run_id: str
    stage: str
    backend: str
    run_kind: str
    pacing: str
    profile: str
    effective: str
    precision_class: str
    started_at: str
    identity: Mapping[str, Any]
    thermal: Mapping[str, Any] | None
    problems: tuple[str, ...]
    sampler_problems: tuple[str, ...]


@dataclass(frozen=True)
class ReportModel:
    """렌더 입력."""

    project: str
    task_metric: str
    scope: Mapping[str, Any]
    partial: list[str] | None
    frozen_at: str | None
    thresholds_sha: str
    validity: Mapping[str, Any]
    rule_deviations: list[str]
    runs: list[RunInfo]
    items: list[Item]
    missing: list[str]
    abba_problems: Mapping[str, Sequence[str]]
    counts: dict[str, int]
    overall: str
    exit_code: int


def exit_code_for(counts: Mapping[str, int]) -> int:
    """종료 코드: 판정 대상 ≥ 1 건이고 전부 pass 일 때만 0."""
    judged = sum(n for status, n in counts.items() if status != judge.RECORD_ONLY)
    return 0 if judged > 0 and counts.get(judge.PASS, 0) == judged else 1


def _rule_text(rule: Mapping[str, Any]) -> str:
    return "record" if rule["op"] == "record" else f"{rule['op']} {rule['limit']}"


def rule_deviations(catalog: Catalog, thresholds: Mapping[str, Any]) -> list[str]:
    """카탈로그 기본 규칙과 다른 thresholds 규칙 목록(변경·추가·삭제).

    기본 limit=null 을 같은 op 로 채운 것은 프로젝트 필수 기입이라 제외.
    """
    defaults = {
        (r["metric"], tuple(sorted(r["when"].items()))): r
        for r in catalog.default_rules(dict(thresholds["scope"]))
    }
    out: list[str] = []
    seen: set[tuple[str, tuple[tuple[str, Any], ...]]] = set()
    for rule in thresholds["rules"]:
        key = (rule["metric"], tuple(sorted(rule["when"].items())))
        when = ", ".join(f"{k}={v}" for k, v in key[1]) or "전체"
        label = f"{rule['metric']} [{when}]"
        base = defaults.get(key)
        if base is None:
            out.append(f"{label}: 추가 {_rule_text(rule)}")
            continue
        seen.add(key)
        filled = base["limit"] is None and base["op"] == rule["op"]
        if rule["op"] != base["op"] or (rule["limit"] != base["limit"] and not filled):
            out.append(f"{label}: 기본 {_rule_text(base)} → {_rule_text(rule)}")
    for key, base in defaults.items():
        if key not in seen:
            when = ", ".join(f"{k}={v}" for k, v in key[1]) or "전체"
            out.append(f"{key[0]} [{when}]: 기본 {_rule_text(base)} 삭제")
    return out


def _typed(spec: MetricSpec, value: float | None) -> Value:
    if value is not None and spec.value_type == "int":
        return int(value)
    return value


class _Builder:
    """build_report 의 작업 상태."""

    def __init__(
        self,
        results: Mapping[str, Any],
        thresholds: Mapping[str, Any],
        thresholds_sha: str,
        catalog: Catalog,
        load_rows: LoadRows,
    ) -> None:
        self.results = results
        self.thresholds = thresholds
        self.sha = thresholds_sha
        self.catalog = catalog
        self.load_rows = load_rows
        self.scope: Obj = dict(thresholds["scope"])
        self.rules: list[Obj] = list(thresholds["rules"])
        self.frozen = thresholds.get("frozen_at") is not None
        self.task = results["project"]["task_metric"]
        self.runs: dict[str, Obj] = {r["run_id"]: r for r in results["runs"]}
        self.problems: dict[str, list[str]] = {}
        self.cross = schema.CrossProblems()
        # 회차별 sampler 지표 무효 사유(결속 + 품질)
        self.sampler_bad: dict[str, list[str]] = {}
        # 회차별 (지표, subset) → 값. ABBA·ACC.degradation 계산의 입력
        self.values: dict[str, dict[tuple[str, str | None], Value]] = {}
        self.items: list[Item] = []

    # ------------------------------------------------------------ 값 수집

    def _rows(self, run: Obj, key: str) -> list[Obj]:
        rows = self.load_rows(run[key])
        where = f"{run['run_id']}:{run[key]}"
        if key == "timing":
            probs = schema.timing_rows_problems(rows, where)
        else:
            probs = schema.sample_rows_problems(rows, where)
        if probs:
            shown = "; ".join(probs[:10])
            raise schema.FormatError(f"원자료 행 형식 오류({len(probs)} 건): {shown}")
        return rows

    def collect(self) -> None:
        """회차별 생성기 지표 계산 + 프로젝트 값 수집 + 유효성 검사."""
        validity: Mapping[str, Any] = self.thresholds["validity"]
        quality: dict[str, list[str]] = {}
        for run_id, run in self.runs.items():
            self.problems[run_id] = schema.run_problems(run, self.thresholds, self.sha)
            meta: Obj = run.get("meta") or {}
            generated: dict[str, float | None] = dict(calc.meta_metrics(meta))
            if run["run_kind"] == "perf":
                rows = self._rows(run, "timing")
                generated.update(calc.timing_metrics(rows, run["pacing"], meta))
                thermal = run.get("thermal")
                if thermal is not None:
                    generated["THM.start_battery_c"] = float(thermal["start_battery_c"])
                    generated["THM.pause_events"] = float(thermal["pause_events"])
            elif run["run_kind"] == "sampler":
                samples = self._rows(run, "samples")
                sampled = calc.sampler_metrics(samples, meta)
                generated.update(sampled)
                quality[run_id] = schema.sampler_quality_problems(
                    len(samples), sampled["MQ.sampler_gap_ratio"], validity
                )
            values: dict[tuple[str, str | None], Value] = {}
            for metric, value in generated.items():
                spec = self.catalog.get(metric)
                if value is not None and spec.run_kind in ("any", run["run_kind"]):
                    values[(metric, None)] = _typed(spec, value)
            for entry in run.get("values") or []:
                values[(entry["metric"], entry.get("subset"))] = entry["value"]
            self.values[run_id] = values
        self.cross = schema.cross_problems(self.results, validity)
        for run_id in self.runs:
            merged = self.cross.sampler.get(run_id, []) + quality.get(run_id, [])
            if merged:
                self.sampler_bad[run_id] = merged

    # ------------------------------------------------------------ 판정

    def _run_invalid(self, run_id: str, spec: MetricSpec) -> list[str]:
        reasons = list(self.problems[run_id])
        if spec.run_kind == "sampler":
            reasons += self.sampler_bad.get(run_id, [])
        return [f"{run_id}: {r}" for r in reasons]

    def _add(
        self,
        spec: MetricSpec,
        kind: str,
        ref: str,
        ctx: Mapping[str, str | None],
        stage: str,
        value: Value,
        invalid: Sequence[str],
        unit: str | None = None,
    ) -> None:
        context = str(ctx.get("pair") or ctx.get("stage"))
        if invalid:
            verdict = judge.Judgement(judge.INVALID, "; ".join(invalid))
        elif context not in spec.stages:
            verdict = judge.Judgement(judge.RECORD_ONLY, "카탈로그 stages 밖 문맥")
        elif spec.source == "generator" and not self.catalog.applicable(
            spec, self.scope, optional=True
        ):
            verdict = judge.Judgement(judge.RECORD_ONLY, "scope 밖 지표(자동 계산)")
        else:
            rule = judge.select_rule(self.rules, spec.id, ctx)
            if judge.needs_noise_floor(
                spec, rule, ctx.get("pair"), self.scope["purposes"]
            ):
                verdict = judge.Judgement(
                    judge.NOT_ESTABLISHED,
                    "convert 목적 S1-S2 NUM 규칙에 noise_floor 없음",
                )
            else:
                verdict = judge.judge_value(spec, value, rule, self.frozen)
        self.items.append(
            Item(
                metric=spec.id,
                kind=kind,
                ref=ref,
                context=context,
                stage=stage,
                subset=ctx.get("subset"),
                value=value,
                unit=spec.unit if unit is None else unit,
                status=verdict.status,
                reason=verdict.reason,
                category=spec.category,
            )
        )

    def _run_ctx(self, run: Obj, subset: str | None) -> dict[str, str | None]:
        return {
            "stage": run["stage"],
            "class": judge.effective_class(run["effective"]),
            "subset": subset,
        }

    def judge_runs(self) -> None:
        """회차 값 판정."""
        for run_id, run in self.runs.items():
            for (metric, subset), value in self.values[run_id].items():
                spec = self.catalog.get(metric)
                unit = self.task["unit"] if spec.unit == "task" else None
                self._add(
                    spec,
                    "run",
                    run_id,
                    self._run_ctx(run, subset),
                    run["stage"],
                    value,
                    self._run_invalid(run_id, spec),
                    unit,
                )

    def _acc(self, run_id: str) -> dict[str | None, float]:
        return {
            subset: float(value)
            for (metric, subset), value in self.values[run_id].items()
            if metric == "ACC.primary" and value is not None
        }

    def judge_acc_degradation(self) -> None:
        """ACC.degradation: S1 기준 회차 대비 열화량(서브셋별 + 전체)."""
        spec = self.catalog.get("ACC.degradation")
        primary = self.catalog.get("ACC.primary")
        baseline = schema.select_acc_baseline(list(self.runs.values()))
        if baseline is None:
            return
        base_id = baseline["run_id"]
        base = self._acc(base_id)
        sign = 1.0 if self.task["direction"] == "lower" else -1.0
        for run_id, run in self.runs.items():
            target = self._acc(run_id)
            if run["stage"] == "S1" or not target:
                continue
            invalid = self._run_invalid(base_id, primary)
            invalid += self._run_invalid(run_id, primary)
            subsets = list(base) + [s for s in target if s not in base]
            for subset in subsets:
                value: float | None = None
                extra = list(invalid)
                if subset in base and subset in target:
                    value = round(sign * (target[subset] - base[subset]), 12)
                ctx = self._run_ctx(run, subset)
                before = len(self.items)
                self._add(
                    spec,
                    "run",
                    run_id,
                    ctx,
                    run["stage"],
                    value,
                    extra,
                    self.task["unit"],
                )
                if value is None and self.items[before].status != judge.INVALID:
                    # 한쪽에만 있는 서브셋은 규칙과 무관하게 판정 불성립
                    side = "target" if subset in base else "기준(S1)"
                    self.items[before] = _replace_status(
                        self.items[before],
                        judge.NOT_ESTABLISHED,
                        f"{side} 에 서브셋 {subset or 'overall'} 없음",
                    )

    def judge_pairs(self) -> None:
        """pairs[] 값 판정."""
        for pair in self.results.get("pairs") or []:
            ref, target = self.runs[pair["ref"]], self.runs[pair["target"]]
            if pair["kind"] == "chain":
                pair_ctx = f"{ref['stage']}-{target['stage']}"
            else:
                pair_ctx = pair["kind"]
            precision = judge.pair_class(ref["effective"], target["effective"])
            for entry in pair["values"]:
                spec = self.catalog.get(entry["metric"])
                invalid = self._run_invalid(ref["run_id"], spec)
                invalid += self._run_invalid(target["run_id"], spec)
                ctx = {
                    "pair": pair_ctx,
                    "class": precision,
                    "subset": entry.get("tensor"),
                }
                self._add(
                    spec,
                    "pair",
                    pair["pair_id"],
                    ctx,
                    target["stage"],
                    entry["value"],
                    invalid,
                )

    def judge_abba(self) -> None:
        """ABBA 블록 판정: 쌍별 열화 % 의 중앙값 ≤ abba_limits_pct."""
        limits: Mapping[str, float] = self.thresholds["abba_limits_pct"]
        for block in self.results.get("abba") or []:
            abba_id = block["abba_id"]
            members = [p[k] for p in block["pairs"] for k in ("a", "b")]
            stage = self.runs[members[0]]["stage"] if members else ""
            for metric in block["metrics"]:
                spec = self.catalog.get(metric)
                invalid = [f"ABBA 구성: {p}" for p in self.cross.abba.get(abba_id, [])]
                for run_id in dict.fromkeys(members):
                    invalid += self._run_invalid(run_id, spec)
                pcts: list[float] = []
                degenerate = ""
                for pair in block["pairs"]:
                    a = self.values[pair["a"]].get((metric, None))
                    b = self.values[pair["b"]].get((metric, None))
                    if a is None or b is None:
                        degenerate = f"쌍 ({pair['a']}, {pair['b']}) 에 값 없음"
                        continue
                    pct = calc.worsening_pct(float(a), float(b), spec.direction)
                    if pct is None:
                        degenerate = (
                            f"쌍 ({pair['a']}, {pair['b']}) 의 a = 0(퇴화 입력)"
                        )
                        continue
                    pcts.append(pct)
                value = calc.median(pcts) if pcts and not degenerate else None
                limit = limits.get(metric)
                if invalid:
                    status, reason = judge.INVALID, "; ".join(invalid)
                elif not self.frozen:
                    status, reason = (
                        judge.NOT_ESTABLISHED,
                        "임계 미동결(frozen_at null)",
                    )
                elif limit is None:
                    status = judge.NOT_ESTABLISHED
                    reason = "thresholds.abba_limits_pct 에 한도 없음"
                elif value is None:
                    status = judge.NOT_ESTABLISHED
                    reason = degenerate or "쌍 없음"
                else:
                    status = judge.PASS if value <= limit else judge.FAIL
                    reason = f"쌍별 열화 % 중앙값 <= {limit:g}"
                self.items.append(
                    Item(
                        metric=metric,
                        kind="abba",
                        ref=abba_id,
                        context=stage,
                        stage=stage,
                        subset=None,
                        value=value,
                        unit="%",
                        status=status,
                        reason=reason,
                        category=spec.category,
                    )
                )

    def add_missing(self, partial: list[str] | None) -> list[str]:
        """필수 지표 누락 → not_established 항목 + 누락 목록."""
        reqs = self.catalog.required(self.scope, partial)
        have_run = {(i.metric, i.stage) for i in self.items if i.kind == "run"}
        have_pair = {(i.metric, i.context) for i in self.items if i.kind == "pair"}
        have_base = {
            (i.metric, i.stage)
            for i in self.items
            if i.kind == "pair" and i.context == "base"
        }
        have_abba = {i.metric for i in self.items if i.kind == "abba"}
        gaps: list[tuple[str, str, str, str]] = []
        for metric, stage in reqs.run:
            if (metric, stage) not in have_run:
                gaps.append((metric, stage, stage, f"{metric} @ {stage}"))
        for metric, ctx, target in reqs.pair:
            if ctx == "base":
                if (metric, target) not in have_base:
                    gaps.append((metric, ctx, target, f"{metric} @ base(S1→{target})"))
            elif (metric, ctx) not in have_pair:
                gaps.append((metric, ctx, target, f"{metric} @ {ctx}"))
        for metric in reqs.abba:
            if metric not in have_abba:
                gaps.append((metric, "abba", "", f"{metric} @ ABBA"))
        for metric, context, stage, _ in gaps:
            spec = self.catalog.get(metric)
            self.items.append(
                Item(
                    metric=metric,
                    kind="missing",
                    ref="",
                    context=context,
                    stage=stage,
                    subset=None,
                    value=None,
                    unit=spec.unit,
                    status=judge.NOT_ESTABLISHED,
                    reason="필수 지표 미측정",
                    category=spec.category,
                )
            )
        return [label for _, _, _, label in gaps]

    def run_infos(self) -> list[RunInfo]:
        """회차 신원 요약."""
        out: list[RunInfo] = []
        for run_id, run in self.runs.items():
            eff = run["effective"]
            out.append(
                RunInfo(
                    run_id=run_id,
                    stage=run["stage"],
                    backend=run["backend"],
                    run_kind=run["run_kind"],
                    pacing=str(run.get("pacing", "-")),
                    profile=run["profile"],
                    effective="/".join(str(eff[k]) for k in schema.EFFECTIVE_KEYS),
                    precision_class=judge.effective_class(eff),
                    started_at=run["started_at"],
                    identity=dict(run["identity"]),
                    thermal=run.get("thermal"),
                    problems=tuple(self.problems[run_id]),
                    sampler_problems=tuple(self.sampler_bad.get(run_id, [])),
                )
            )
        return out


def _replace_status(item: Item, status: str, reason: str) -> Item:
    return Item(
        metric=item.metric,
        kind=item.kind,
        ref=item.ref,
        context=item.context,
        stage=item.stage,
        subset=item.subset,
        value=item.value,
        unit=item.unit,
        status=status,
        reason=reason,
        category=item.category,
    )


def build_report(
    results: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    thresholds_sha: str,
    catalog: Catalog,
    load_rows: LoadRows,
    partial: list[str] | None,
) -> ReportModel:
    """검증을 통과한 results·thresholds 로 리포트 모델 생성.

    원자료 행 형식 오류는 schema.FormatError.
    """
    builder = _Builder(results, thresholds, thresholds_sha, catalog, load_rows)
    builder.collect()
    builder.judge_runs()
    builder.judge_acc_degradation()
    builder.judge_pairs()
    builder.judge_abba()
    missing = builder.add_missing(partial)
    counts = {status: 0 for status in _STATUS_ORDER}
    for item in builder.items:
        counts[item.status] += 1
    task = builder.task
    return ReportModel(
        project=results["project"]["name"],
        task_metric=f"{task['id']} ({task['unit']}, {task['direction']})",
        scope=builder.scope,
        partial=partial,
        frozen_at=thresholds.get("frozen_at"),
        thresholds_sha=thresholds_sha,
        validity=dict(thresholds["validity"]),
        rule_deviations=rule_deviations(catalog, thresholds),
        runs=builder.run_infos(),
        items=builder.items,
        missing=missing,
        abba_problems=dict(builder.cross.abba),
        counts=counts,
        overall=judge.worst(i.status for i in builder.items),
        exit_code=exit_code_for(counts),
    )
