"""results + thresholds → 리포트 모델 조립(원자료 행은 주입된 load_rows 로만 읽음)."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from port_metrics import calc, judge, schema
from port_metrics.catalog import Catalog, MetricSpec

Obj = dict[str, Any]
NO_BLOCK_REF = "(블록 없음)"  # 균형 대조 블록이 없는 항목의 ref(누락 표기와 구분)
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

    kind = run|pair|abba|balance|missing, ref = run_id·pair_id·abba_id, context = stage
    또는 pair 문맥, stage = 회차 stage(pair 는 target stage), subset = 서브셋 또는 텐서
    이름. expected_fail = 이 항목을 판정한 규칙의 예상 fail 사유(상태와 무관하게 남김).
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
    expected_fail: str | None = None

    @property
    def is_expected_fail(self) -> bool:
        """사전 등록된 예상 fail 인지(원판정 fail ∧ 규칙에 등록 사유 있음)."""
        return self.status == judge.FAIL and self.expected_fail is not None


@dataclass(frozen=True)
class ExpectedRule:
    """등록된 예상 fail 규칙 1 건과 그 규칙이 덮은 판정 항목 수."""

    label: str
    reason: str
    covered: int
    failed: int


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
    superseded_by: str | None = None  # 재측정으로 대체됨(판정 제외)
    superseded_reason: str = ""


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
    thresholds_path: str = ""  # 사용한 동결 파일 절대 경로(CLI 가 채움, 빈 값 = 미표시)
    expected_fail: int = 0  # 예상 fail 항목 수(counts["fail"] 에 포함된 원판정)
    expected_rules: tuple[ExpectedRule, ...] = ()  # 등록된 예상 fail 규칙


def _effective_status(item: Item) -> str:
    """종합 판정·종료 코드에 쓰는 상태: 예상 fail 은 pass 로 봄(원판정은 Item 에 보존)."""
    return judge.PASS if item.is_expected_fail else item.status


def exit_code_for(counts: Mapping[str, int]) -> int:
    """종료 코드: 판정 대상 ≥ 1 건이고 전부 pass(예상 fail 포함)일 때만 0.

    counts = 실효 상태(_effective_status) 집계 — 예상 fail 은 pass 로 세어 넘김.
    invalid·not_established·예상 밖 fail 이 하나라도 있으면 1.
    """
    judged = sum(n for status, n in counts.items() if status != judge.RECORD_ONLY)
    return 0 if judged > 0 and counts.get(judge.PASS, 0) == judged else 1


def rule_label(rule: Mapping[str, Any]) -> str:
    """규칙 표기 `지표 [when]`(when 키 정렬)."""
    when = ", ".join(f"{k}={v}" for k, v in sorted(rule["when"].items())) or "전체"
    return f"{rule['metric']} [{when}]"


def _rule_key(metric: str, when: Mapping[str, str]) -> tuple[str, tuple[Any, ...]]:
    return metric, tuple(sorted(when.items()))


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
        # 판정 대상 회차(대체된 회차 제외). 대체 회차는 신원·문제만 리포트에 남김
        self.active: dict[str, Obj] = {
            k: r for k, r in self.runs.items() if not schema.is_superseded(r)
        }
        self.blocks: list[Obj] = list(results.get("abba") or [])
        # 대상 블록 ID → 그 블록을 가리키는 A ↔ A 잡음 블록 ID 목록
        self.noise_for: dict[str, list[str]] = {}
        for block in self.blocks:
            if "noise_for" in block:
                self.noise_for.setdefault(block["noise_for"], []).append(
                    block["abba_id"]
                )
        # 예상 fail 규칙 키 → [덮은 판정 항목 수, 그중 fail 수]
        self.expected_hits: dict[tuple[str, tuple[Any, ...]], list[int]] = {}
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
            if run_id not in self.active:
                # 대체된 회차: 원자료를 읽지 않고 판정 값도 만들지 않음
                self.values[run_id] = {}
                continue
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
        # 규칙을 먼저 골라 invalid·not_established 항목에도 예상 fail 표지를 남김
        rule = judge.select_rule(self.rules, spec.id, ctx)
        if invalid:
            verdict = judge.Judgement(judge.INVALID, "; ".join(invalid))
        elif context not in spec.stages:
            verdict = judge.Judgement(judge.RECORD_ONLY, "카탈로그 stages 밖 문맥")
        elif spec.source == "generator" and not self.catalog.applicable(
            spec, self.scope, optional=True
        ):
            verdict = judge.Judgement(judge.RECORD_ONLY, "scope 밖 지표(자동 계산)")
        elif judge.needs_noise_floor(
            spec, rule, ctx.get("pair"), self.scope["purposes"]
        ):
            verdict = judge.Judgement(
                judge.NOT_ESTABLISHED,
                "convert 목적 S1-S2 NUM 규칙에 noise_floor 없음",
            )
        else:
            verdict = judge.judge_value(spec, value, rule, self.frozen)
        expected = None if rule is None else rule.expected_fail
        if rule is not None and expected is not None:
            if verdict.status != judge.RECORD_ONLY:
                hits = self.expected_hits.setdefault(
                    _rule_key(rule.metric, rule.when), [0, 0]
                )
                hits[0] += 1
                hits[1] += verdict.status == judge.FAIL
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
                expected_fail=expected,
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
        baseline = schema.select_acc_baseline(list(self.active.values()))
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
                invalid = [
                    f"쌍 구성: {p}" for p in self.cross.pairs.get(pair["pair_id"], [])
                ]
                invalid += self._run_invalid(ref["run_id"], spec)
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
        """ABBA 블록 판정: 쌍별 열화 % 의 중앙값 ≤ abba_limits_pct.

        A ↔ A 잡음 블록(noise_for)은 양방향 — |중앙값| ≤ 같은 허용폭(값은 부호 유지).
        """
        limits: Mapping[str, float] = self.thresholds["abba_limits_pct"]
        for block in self.blocks:
            abba_id = block["abba_id"]
            two_sided = "noise_for" in block
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
                elif two_sided:
                    status = judge.PASS if abs(value) <= limit else judge.FAIL
                    reason = f"|쌍별 Δ% 중앙값| <= {limit:g}(A ↔ A 잡음 블록, 양방향)"
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

    def apply_noise_controls(self) -> None:
        """대상 블록의 pass 를 A ↔ A 잡음 대조와 결합(judge_abba 뒤, 블록 순서 무관).

        대상 pass ∧ 그 지표를 가진 잡음 블록 항목이 pass 가 아님 → not_established.
        대상 fail·invalid 는 그대로. 그 지표를 가진 잡음 블록이 없으면 사유에만 병기.
        잡음 블록이 가리키지 않는 블록의 항목은 건드리지 않음(사유 바이트 불변).
        """
        noise_items = {(i.ref, i.metric): i for i in self.items if i.kind == "abba"}
        for index, item in enumerate(self.items):
            if item.kind != "abba" or item.status != judge.PASS:
                continue
            noise_ids = self.noise_for.get(item.ref)
            if not noise_ids:
                continue
            controls = [
                noise_items[(noise_id, item.metric)]
                for noise_id in noise_ids
                if (noise_id, item.metric) in noise_items
            ]
            failed = [c for c in controls if c.status != judge.PASS]
            if not controls:
                self.items[index] = _replace_status(
                    item, item.status, f"{item.reason} — 잡음 대조 없음"
                )
            elif failed:
                detail = ", ".join(f"{c.ref} {c.status}" for c in failed)
                self.items[index] = _replace_status(
                    item,
                    judge.NOT_ESTABLISHED,
                    f"A ↔ A 잡음 대조 미통과({detail}) — 허용폭은 넓히지 않음",
                )

    def _balance_item(
        self,
        metric: str,
        ref: str,
        stage: str,
        subset: str | None,
        value: Value,
        verdict: judge.Judgement,
    ) -> Item:
        return Item(
            metric=metric,
            kind="balance",
            ref=ref,
            context=stage,
            stage=stage,
            subset=subset,
            value=value,
            unit="건",
            status=verdict.status,
            reason=verdict.reason,
            category=self.catalog.get(metric).category,
        )

    def _balance_verdict(
        self, abba_id: str, side_a: Sequence[Item], side_b: Sequence[Item]
    ) -> tuple[Value, judge.Judgement]:
        """예상 fail 균형 1 건: b 쪽 fail 수 > a 쪽이면 fail(예상 아님)."""
        n_a = sum(i.status == judge.FAIL for i in side_a)
        n_b = sum(i.status == judge.FAIL for i in side_b)
        counts = f"a {len(side_a)}건 중 fail {n_a}, b {len(side_b)}건 중 fail {n_b}"
        composition = self.cross.abba.get(abba_id, [])
        unsettled = [
            f"{i.ref} {i.status}"
            for i in (*side_a, *side_b)
            if i.status in (judge.INVALID, judge.NOT_ESTABLISHED)
        ]
        if composition:
            reason = "; ".join(f"ABBA 구성: {p}" for p in composition)
            return None, judge.Judgement(judge.INVALID, reason)
        if not side_a or not side_b:
            reason = f"한쪽에 예상 fail 규칙 항목 없음({counts})"
            return None, judge.Judgement(judge.NOT_ESTABLISHED, reason)
        if unsettled:
            reason = f"규칙 항목 판정 불성립({', '.join(unsettled)})"
            return None, judge.Judgement(judge.NOT_ESTABLISHED, reason)
        if n_b > n_a:
            reason = f"b 쪽 fail {n_b} > a 쪽 {n_a}({counts})"
            return n_b - n_a, judge.Judgement(judge.FAIL, reason)
        reason = f"b 쪽 fail 수 <= a 쪽({counts})"
        return n_b - n_a, judge.Judgement(judge.PASS, reason)

    def _balance_key(self, item: Item) -> tuple[str, str, str, str | None]:
        """균형 덮음 단위: 회차 stage·pacing + 지표·서브셋."""
        run = self.runs[item.ref]
        return run["stage"], str(run.get("pacing", "-")), item.metric, item.subset

    def judge_balance(self) -> None:
        """예상 fail 균형: 대상 ABBA 블록의 a·b 쪽 예상 fail 수 비교.

        예상 fail 이 양쪽에 같이 나는 구조적 fail 인지 확인 — 대상(b) 쪽이 더 자주 fail
        하면 회귀를 덮은 것이므로 예상 밖 fail. 항목 = (블록, 지표, 서브셋) 당 1 건이며
        잡음 블록이 아닌 블록이 있으면 목적과 무관하게 만듦. regress 목적에서는 균형
        항목이 덮지 못한 예상 fail(회차 stage·pacing·지표·서브셋 단위)을 not_established 로 둠.
        """
        if not any("expected_fail" in rule for rule in self.rules):
            return
        marked = [
            i
            for i in self.items
            if i.kind == "run"
            and i.expected_fail is not None
            and i.status != judge.RECORD_ONLY
        ]
        covered: set[tuple[str, str, str, str | None]] = set()
        made: list[Item] = []
        for block in self.blocks:
            if "noise_for" in block:
                continue
            abba_id = block["abba_id"]
            side = {p["a"]: "a" for p in block["pairs"]}
            side.update({p["b"]: "b" for p in block["pairs"]})
            stage = self.runs[next(iter(side))]["stage"] if side else ""
            groups: dict[tuple[str, str | None], dict[str, list[Item]]] = {}
            for item in marked:
                if item.ref in side:
                    group = groups.setdefault(
                        (item.metric, item.subset), {"a": [], "b": []}
                    )
                    group[side[item.ref]].append(item)
                    covered.add(self._balance_key(item))
            for (metric, subset), group in groups.items():
                value, verdict = self._balance_verdict(abba_id, group["a"], group["b"])
                made.append(
                    self._balance_item(metric, abba_id, stage, subset, value, verdict)
                )
        if "regress" in self.scope["purposes"]:
            uncovered = dict.fromkeys(
                self._balance_key(i)
                for i in marked
                if i.is_expected_fail and self._balance_key(i) not in covered
            )
            for stage, pacing, metric, subset in uncovered:
                reason = (
                    f"균형 대조 블록 없음({stage}·{pacing} 회차의 예상 fail — regress 는 "
                    "그 지표를 판정하는 A ↔ B′ ABBA 블록으로 양쪽 fail 수를 대조)"
                )
                verdict = judge.Judgement(judge.NOT_ESTABLISHED, reason)
                made.append(
                    self._balance_item(
                        metric, NO_BLOCK_REF, stage, subset, None, verdict
                    )
                )
        self.items += made

    def expected_rules(self) -> tuple[ExpectedRule, ...]:
        """등록된 예상 fail 규칙과 덮은 항목 수(리포트 §0)."""
        out: list[ExpectedRule] = []
        for rule in self.rules:
            if "expected_fail" not in rule:
                continue
            hits = self.expected_hits.get(_rule_key(rule["metric"], rule["when"]))
            covered, failed = hits or (0, 0)
            out.append(
                ExpectedRule(rule_label(rule), rule["expected_fail"], covered, failed)
            )
        return tuple(out)

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
                    superseded_by=run.get("superseded_by"),
                    superseded_reason=str(run.get("superseded_reason", "")),
                )
            )
        return out


def _replace_status(item: Item, status: str, reason: str) -> Item:
    return dataclasses.replace(item, status=status, reason=reason)


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
    builder.apply_noise_controls()
    builder.judge_balance()
    missing = builder.add_missing(partial)
    # counts = 원판정(예상 fail 도 fail 로 셈), effective = 예상 fail 을 pass 로 본 집계
    counts = {status: 0 for status in _STATUS_ORDER}
    effective = {status: 0 for status in _STATUS_ORDER}
    for item in builder.items:
        counts[item.status] += 1
        effective[_effective_status(item)] += 1
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
        overall=judge.worst(_effective_status(i) for i in builder.items),
        exit_code=exit_code_for(effective),
        expected_fail=sum(i.is_expected_fail for i in builder.items),
        expected_rules=builder.expected_rules(),
    )
