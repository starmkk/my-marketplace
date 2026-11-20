"""규칙 선택·값 판정·상태 집계(순수 함수)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from port_metrics.catalog import MetricSpec

PASS = "pass"
FAIL = "fail"
INVALID = "invalid"
NOT_ESTABLISHED = "not_established"
RECORD_ONLY = "record_only"
STATUSES = (PASS, FAIL, INVALID, NOT_ESTABLISHED, RECORD_ONLY)
# 집계 우선순위: invalid > not_established > fail > pass (record_only 제외)
_PRIORITY = (INVALID, NOT_ESTABLISHED, FAIL, PASS)
_FP_WEIGHTS = ("fp32", "fp16", "bf16")


@dataclass(frozen=True)
class Rule:
    """thresholds.rules 1 건."""

    metric: str
    when: Mapping[str, str]
    op: str
    limit: float | bool | None
    noise_floor: float | None = None
    expected_fail: str | None = None  # 사전 등록한 예상 fail 사유(없으면 None)


@dataclass(frozen=True)
class Judgement:
    """판정 결과."""

    status: str
    reason: str


def _when_matches(when: Mapping[str, str], ctx: Mapping[str, str | None]) -> bool:
    for key, want in when.items():
        have = ctx.get(key)
        if key == "subset":
            if want == "overall":
                ok = have is None
            elif want == "each":
                ok = have is not None
            else:
                ok = have == want
        else:
            ok = have == want
        if not ok:
            return False
    return True


def select_rule(
    rules: Sequence[Mapping[str, Any]], metric: str, ctx: Mapping[str, str | None]
) -> Rule | None:
    """지표·문맥(pair·class·stage·subset)에 맞는 규칙 1 건. 없으면 None.

    ctx.subset = None 은 전체(overall). 둘 이상 맞으면(겹침 검사 미통과 입력) ValueError.
    """
    found: list[Mapping[str, Any]] = [
        r
        for r in rules
        if r.get("metric") == metric and _when_matches(r.get("when", {}), ctx)
    ]
    if not found:
        return None
    if len(found) > 1:
        raise ValueError(f"{metric}: 문맥 {dict(ctx)} 에 규칙 {len(found)} 건이 겹침")
    return rule_from(found[0])


def rule_from(rule: Mapping[str, Any]) -> Rule:
    """thresholds.rules 객체 → Rule."""
    return Rule(
        metric=rule["metric"],
        when=dict(rule.get("when", {})),
        op=rule["op"],
        limit=rule.get("limit"),
        noise_floor=rule.get("noise_floor"),
        expected_fail=rule.get("expected_fail"),
    )


def needs_noise_floor(
    spec: MetricSpec, rule: Rule | None, pair_ctx: str | None, purposes: Iterable[str]
) -> bool:
    """convert 목적의 S1-S2 NUM 판정 규칙인데 noise_floor 가 없는 경우."""
    return (
        rule is not None
        and rule.op != "record"
        and rule.noise_floor is None
        and spec.category == "NUM"
        and pair_ctx == "S1-S2"
        and "convert" in purposes
    )


def judge_value(
    spec: MetricSpec, value: float | bool | None, rule: Rule | None, frozen: bool
) -> Judgement:
    """값 1 건 판정. 조용히 pass 되지 않도록 근거가 없으면 not_established."""
    if not spec.judged:
        return Judgement(RECORD_ONLY, "기록 지표(judged=false)")
    if rule is None:
        return Judgement(NOT_ESTABLISHED, "판정 지표인데 매칭 규칙 없음")
    if rule.op == "record":
        return Judgement(RECORD_ONLY, "규칙 op=record")
    if not frozen:
        return Judgement(NOT_ESTABLISHED, "임계 미동결(frozen_at null)")
    limit = rule.limit
    if limit is None:
        return Judgement(NOT_ESTABLISHED, "limit null(프로젝트 미기입)")
    floor = rule.noise_floor
    if floor is not None and not isinstance(limit, bool):
        if rule.op == "<=" and floor > limit:
            return Judgement(NOT_ESTABLISHED, f"잡음 바닥 {floor} > limit {limit}")
        if rule.op == ">=" and floor < limit:
            return Judgement(NOT_ESTABLISHED, f"잡음 바닥 {floor} < limit {limit}")
    if value is None:
        return Judgement(NOT_ESTABLISHED, "값 없음(미측정·퇴화 입력)")
    if isinstance(value, bool) != isinstance(limit, bool):
        return Judgement(NOT_ESTABLISHED, "값과 limit 의 형 불일치")
    if rule.op == "<=":
        ok = value <= limit
    elif rule.op == ">=":
        ok = value >= limit
    elif rule.op == "==":
        ok = value == limit
    else:
        raise ValueError(f"미지 op {rule.op!r}")
    return Judgement(PASS if ok else FAIL, f"{rule.op} {_fmt_limit(limit)}")


def _fmt_limit(limit: float | bool) -> str:
    if isinstance(limit, bool):
        return "true" if limit else "false"
    return f"{limit:g}"


def worst(statuses: Iterable[str]) -> str:
    """상태 집계. 판정 대상이 없으면 record_only."""
    present = set(statuses)
    for status in _PRIORITY:
        if status in present:
            return status
    return RECORD_ONLY


def effective_class(effective: Mapping[str, Any]) -> str:
    """실효 3 필드 → 정밀도 class(fp·lowp)."""
    is_fp = (
        effective.get("weight_storage") in _FP_WEIGHTS
        and effective.get("matmul_accum") == "fp32"
        and effective.get("activation_quant") == "none"
    )
    return "fp" if is_fp else "lowp"


def pair_class(eff_a: Mapping[str, Any], eff_b: Mapping[str, Any]) -> str:
    """두 회차 비교의 class = 낮은 쪽."""
    if effective_class(eff_a) == "fp" and effective_class(eff_b) == "fp":
        return "fp"
    return "lowp"
