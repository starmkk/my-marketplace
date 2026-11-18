"""지표 카탈로그(catalog.json) 적재·검증·필수 범위 계산."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATALOG_SCHEMA = "port-metrics-catalog/1"
STAGES = ("S1", "S2", "S3", "S4", "S5")
CHAIN_PAIRS = ("S1-S2", "S2-S3", "S3-S4", "S4-S5")
PAIR_CONTEXTS = CHAIN_PAIRS + ("base", "regress")
CATEGORIES = ("NUM", "DEC", "ACC", "SPD", "RES", "THM", "STB", "MQ", "CNV", "PWR")
LEVELS = ("core", "purpose", "ext", "optional")
PURPOSES = ("convert", "regress", "optimize", "ship")
MODEL_TYPES = ("streaming", "llm", "classifier")
INPUT_KINDS = ("audio", "other")
SOURCES = ("generator", "project")
RUN_KINDS = ("perf", "sampler", "accuracy")
VALUE_TYPES = ("float", "int", "bool")
DIRECTIONS = ("lower", "higher", "none")
OPS = ("<=", ">=", "==", "record")
WHEN_KEYS = ("pair", "class", "stage", "subset")
CLASSES = ("fp", "lowp")

_METRIC_KEYS = (
    "id",
    "name",
    "category",
    "level",
    "purposes",
    "model_types",
    "scope",
    "stages",
    "input_kinds",
    "source",
    "run_kind",
    "value_type",
    "unit",
    "direction",
    "judged",
    "default_rules",
    "abba_limit_pct",
    "abba_required_for",
    "inputs",
    "definition",
)


def is_number(value: object) -> bool:
    """bool 을 제외한 int·float 여부."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def value_type_ok(value: object, value_type: str) -> bool:
    """value_type 엄격 검사(bool 은 int 가 아님)."""
    if value_type == "bool":
        return isinstance(value, bool)
    if value_type == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    return is_number(value)


def when_problems(when: object, where: str) -> list[str]:
    """규칙 when 절의 키·값 형식 문제."""
    if not isinstance(when, dict):
        return [f"{where}: when 은 객체여야 함"]
    out: list[str] = []
    for key, value in when.items():
        if key not in WHEN_KEYS:
            out.append(f"{where}: when 의 미지 키 {key!r}")
        elif not isinstance(value, str) or not value:
            out.append(f"{where}: when.{key} 는 비어 있지 않은 문자열이어야 함")
        elif key == "pair" and value not in PAIR_CONTEXTS:
            out.append(f"{where}: when.pair 값 {value!r} 위반")
        elif key == "class" and value not in CLASSES:
            out.append(f"{where}: when.class 값 {value!r} 위반")
        elif key == "stage" and value not in STAGES:
            out.append(f"{where}: when.stage 값 {value!r} 위반")
    return out


def whens_overlap(a: dict[str, str], b: dict[str, str]) -> bool:
    """공통 키 값이 모두 같으면 겹침(없는 키 = 와일드카드).

    subset 은 `each` 가 모든 이름과 겹치고, `overall` 은 자기 자신과만 겹침.
    """
    for key in a.keys() & b.keys():
        va, vb = a[key], b[key]
        if va == vb:
            continue
        if key == "subset" and "overall" not in (va, vb) and "each" in (va, vb):
            continue
        return False
    return True


def rule_limit_problems(
    op: object, limit: object, value_type: str, where: str
) -> list[str]:
    """규칙 op·limit 형식 문제(limit null 은 허용)."""
    if op not in OPS:
        return [f"{where}: op 값 {op!r} 위반"]
    if limit is None:
        return []
    if value_type == "bool":
        if not isinstance(limit, bool):
            return [f"{where}: bool 지표의 limit 은 bool 이어야 함"]
        if op not in ("==", "record"):
            return [f"{where}: bool 지표의 op 는 == 만 허용"]
        return []
    if not is_number(limit):
        return [f"{where}: limit 은 수 또는 null 이어야 함"]
    return []


@dataclass(frozen=True)
class MetricSpec:
    """카탈로그 지표 1 건."""

    id: str
    name: str
    category: str
    level: str
    purposes: tuple[str, ...]
    model_types: tuple[str, ...]
    scope: str
    stages: tuple[str, ...]
    input_kinds: tuple[str, ...]
    source: str
    run_kind: str
    value_type: str
    unit: str
    direction: str
    judged: bool
    default_rules: tuple[dict[str, Any], ...]
    abba_limit_pct: float | None
    abba_required_for: tuple[str, ...]
    inputs: tuple[str, ...]
    definition: str


@dataclass(frozen=True)
class Requirements:
    """scope 기준 필수 지표 목록.

    run = (지표, stage), pair = (지표, 문맥, 대상 stage 또는 "") , abba = 지표.
    """

    run: tuple[tuple[str, str], ...]
    pair: tuple[tuple[str, str, str], ...]
    abba: tuple[str, ...]

    def ids(self) -> set[str]:
        """필수 지표 id 집합."""
        out = {m for m, _ in self.run}
        out |= {m for m, _, _ in self.pair}
        out |= set(self.abba)
        return out


def _str_list_problems(
    value: object, allowed: tuple[str, ...] | None, where: str
) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        return [f"{where}: 문자열 목록이어야 함"]
    if allowed is not None:
        return [f"{where}: 값 {v!r} 위반" for v in value if v not in allowed]
    return []


def _metric_problems(m: dict[str, Any], where: str) -> list[str]:
    out: list[str] = []
    missing = [k for k in _METRIC_KEYS if k not in m]
    if missing:
        return [f"{where}: 필수 키 누락 {missing}"]
    for key in ("id", "name", "unit", "definition"):
        if not isinstance(m[key], str) or not m[key]:
            out.append(f"{where}.{key}: 비어 있지 않은 문자열이어야 함")
    enums: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("category", CATEGORIES),
        ("level", LEVELS),
        ("scope", ("run", "pair")),
        ("source", SOURCES),
        ("run_kind", RUN_KINDS + ("any",)),
        ("value_type", VALUE_TYPES),
        ("direction", DIRECTIONS),
    )
    for key, allowed in enums:
        if m[key] not in allowed:
            out.append(f"{where}.{key}: 값 {m[key]!r} 위반")
    if out:
        return out
    if m["id"].split(".")[0] != m["category"] or "." not in m["id"]:
        out.append(f"{where}.id: <CAT>.<name> 형식 위반")
    stage_enum = STAGES if m["scope"] == "run" else PAIR_CONTEXTS
    out += _str_list_problems(m["purposes"], PURPOSES, f"{where}.purposes")
    out += _str_list_problems(m["model_types"], MODEL_TYPES, f"{where}.model_types")
    out += _str_list_problems(m["stages"], stage_enum, f"{where}.stages")
    out += _str_list_problems(m["input_kinds"], INPUT_KINDS, f"{where}.input_kinds")
    out += _str_list_problems(
        m["abba_required_for"], PURPOSES, f"{where}.abba_required_for"
    )
    out += _str_list_problems(m["inputs"], None, f"{where}.inputs")
    if not m["stages"] or not m["input_kinds"]:
        out.append(f"{where}: stages·input_kinds 는 비어 있을 수 없음")
    if not isinstance(m["judged"], bool):
        out.append(f"{where}.judged: bool 이어야 함")
    if m["level"] in ("purpose", "optional") and not m["purposes"]:
        out.append(f"{where}: level={m['level']} 인데 purposes 가 비어 있음")
    if m["level"] == "ext" and not m["model_types"]:
        out.append(f"{where}: level=ext 인데 model_types 가 비어 있음")
    abba = m["abba_limit_pct"]
    if abba is not None:
        if not is_number(abba) or abba < 0:
            out.append(f"{where}.abba_limit_pct: 0 이상의 수 또는 null 이어야 함")
        if m["direction"] == "none":
            out.append(f"{where}: abba_limit_pct 지표는 direction 이 none 일 수 없음")
        if m["scope"] != "run":
            out.append(f"{where}: abba_limit_pct 는 run 지표에만 허용")
    elif m["abba_required_for"]:
        out.append(f"{where}: abba_required_for 가 있는데 abba_limit_pct 가 null")
    rules = m["default_rules"]
    if not isinstance(rules, list):
        return out + [f"{where}.default_rules: 목록이어야 함"]
    whens: list[dict[str, str]] = []
    for i, rule in enumerate(rules):
        rw = f"{where}.default_rules[{i}]"
        if not isinstance(rule, dict) or set(rule) != {"when", "op", "limit"}:
            out.append(f"{rw}: 키는 when·op·limit 이어야 함")
            continue
        probs = when_problems(rule["when"], rw)
        probs += rule_limit_problems(rule["op"], rule["limit"], m["value_type"], rw)
        when = rule["when"] if isinstance(rule["when"], dict) else {}
        ctx_key = "stage" if m["scope"] == "run" else "pair"
        other = "pair" if m["scope"] == "run" else "stage"
        if other in when:
            probs.append(f"{rw}: scope={m['scope']} 지표에 when.{other} 사용")
        if ctx_key in when and when[ctx_key] not in m["stages"]:
            probs.append(f"{rw}: when.{ctx_key} 가 지표 stages 밖")
        if not probs and any(whens_overlap(when, w) for w in whens):
            probs.append(f"{rw}: 같은 지표의 다른 기본 규칙과 겹침")
        if not probs:
            whens.append(when)
        out += probs
    if rules and not m["judged"]:
        out.append(f"{where}: judged=false 지표에 default_rules 가 있음")
    return out


def catalog_problems(obj: object) -> list[str]:
    """카탈로그 객체의 형식 문제 목록(빈 목록 = 정상)."""
    if not isinstance(obj, dict):
        return ["catalog: 최상위는 객체여야 함"]
    if obj.get("schema") != CATALOG_SCHEMA:
        return [f"catalog.schema: {CATALOG_SCHEMA!r} 이어야 함"]
    metrics = obj.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        return ["catalog.metrics: 비어 있지 않은 목록이어야 함"]
    out: list[str] = []
    seen: set[str] = set()
    for i, m in enumerate(metrics):
        where = f"metrics[{i}]"
        if not isinstance(m, dict):
            out.append(f"{where}: 객체여야 함")
            continue
        probs = _metric_problems(m, where)
        out += probs
        mid = m.get("id")
        if isinstance(mid, str):
            if mid in seen:
                out.append(f"{where}.id: {mid} 중복")
            seen.add(mid)
    return out


def _scope_stages(scope: dict[str, Any], partial: list[str] | None) -> list[str]:
    stages = [s for s in STAGES if s in scope["stages"]]
    if partial is not None:
        stages = [s for s in stages if s in partial]
    return stages


class Catalog:
    """지표 정의 집합."""

    def __init__(self, metrics: tuple[MetricSpec, ...]) -> None:
        self.metrics = metrics
        self._by_id = {m.id: m for m in metrics}

    def has(self, metric_id: str) -> bool:
        """지표 존재 여부."""
        return metric_id in self._by_id

    def get(self, metric_id: str) -> MetricSpec:
        """지표 조회(없으면 KeyError)."""
        return self._by_id[metric_id]

    def applicable(
        self, spec: MetricSpec, scope: dict[str, Any], optional: bool = False
    ) -> bool:
        """scope(목적·유형·입력 종류)에 해당하는 지표인지.

        optional=True 면 목적이 맞는 optional 지표도 포함(필수는 아니지만 판정 대상).
        """
        if scope["input_kind"] not in spec.input_kinds:
            return False
        if spec.level == "core":
            return True
        if spec.level == "purpose" or (optional and spec.level == "optional"):
            return bool(set(spec.purposes) & set(scope["purposes"]))
        if spec.level == "ext":
            return bool(set(spec.model_types) & set(scope["model_types"]))
        return False

    def _pair_contexts(
        self, spec: MetricSpec, scope: dict[str, Any], stages: list[str]
    ) -> list[tuple[str, str]]:
        """scope 에서 성립하는 (pair 문맥, 대상 stage) 목록."""
        out: list[tuple[str, str]] = []
        for ctx in spec.stages:
            if ctx == "base":
                if "S1" in stages:
                    out += [("base", s) for s in stages if s != "S1"]
            elif ctx == "regress":
                if "regress" in scope["purposes"] and stages:
                    out.append(("regress", ""))
            else:
                ref, target = ctx.split("-")
                if ref in stages and target in stages:
                    out.append((ctx, target))
        return out

    def required(
        self, scope: dict[str, Any], partial: list[str] | None
    ) -> Requirements:
        """thresholds scope 기준 필수 지표(§5.3). partial 은 stage 축소."""
        stages = _scope_stages(scope, partial)
        run: list[tuple[str, str]] = []
        pair: list[tuple[str, str, str]] = []
        abba: list[str] = []
        for spec in self.metrics:
            if (
                spec.abba_limit_pct is not None
                and set(spec.abba_required_for) & set(scope["purposes"])
                and scope["input_kind"] in spec.input_kinds
                and any(s in spec.stages for s in stages)
            ):
                abba.append(spec.id)
            if not self.applicable(spec, scope):
                continue
            if spec.scope == "run":
                run += [(spec.id, s) for s in stages if s in spec.stages]
            else:
                pair += [
                    (spec.id, ctx, target)
                    for ctx, target in self._pair_contexts(spec, scope, stages)
                ]
        return Requirements(tuple(run), tuple(pair), tuple(abba))

    def default_rules(self, scope: dict[str, Any]) -> list[dict[str, Any]]:
        """scope 에 해당하는 카탈로그 기본 규칙 전개(thresholds.rules 형식)."""
        stages = _scope_stages(scope, None)
        out: list[dict[str, Any]] = []
        for spec in self.metrics:
            if not self.applicable(spec, scope, optional=True):
                continue
            if spec.scope == "run":
                contexts = {s for s in stages if s in spec.stages}
            else:
                contexts = {c for c, _ in self._pair_contexts(spec, scope, stages)}
            if not contexts:
                continue
            key = "stage" if spec.scope == "run" else "pair"
            for rule in spec.default_rules:
                when = dict(rule["when"])
                if key in when and when[key] not in contexts:
                    continue
                out.append(
                    {
                        "metric": spec.id,
                        "when": when,
                        "op": rule["op"],
                        "limit": rule["limit"],
                    }
                )
        return out

    def default_abba_limits(self, scope: dict[str, Any]) -> dict[str, float]:
        """scope 에 해당하는 ABBA 허용 열화 % 기본값."""
        out: dict[str, float] = {}
        for spec in self.metrics:
            if spec.abba_limit_pct is None:
                continue
            if self.applicable(spec, scope, optional=True):
                out[spec.id] = spec.abba_limit_pct
        return out


def catalog_from_obj(obj: object) -> Catalog:
    """검증 후 Catalog 생성(문제 있으면 ValueError)."""
    problems = catalog_problems(obj)
    if problems:
        raise ValueError("카탈로그 형식 오류: " + "; ".join(problems))
    assert isinstance(obj, dict)
    specs = []
    for m in obj["metrics"]:
        abba = m["abba_limit_pct"]
        specs.append(
            MetricSpec(
                id=m["id"],
                name=m["name"],
                category=m["category"],
                level=m["level"],
                purposes=tuple(m["purposes"]),
                model_types=tuple(m["model_types"]),
                scope=m["scope"],
                stages=tuple(m["stages"]),
                input_kinds=tuple(m["input_kinds"]),
                source=m["source"],
                run_kind=m["run_kind"],
                value_type=m["value_type"],
                unit=m["unit"],
                direction=m["direction"],
                judged=m["judged"],
                default_rules=tuple(m["default_rules"]),
                abba_limit_pct=None if abba is None else float(abba),
                abba_required_for=tuple(m["abba_required_for"]),
                inputs=tuple(m["inputs"]),
                definition=m["definition"],
            )
        )
    return Catalog(tuple(specs))


def load_catalog(path: str | Path) -> Catalog:
    """catalog.json 적재."""
    text = Path(path).read_text(encoding="utf-8")
    return catalog_from_obj(json.loads(text))
