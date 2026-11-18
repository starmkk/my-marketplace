"""results.json·thresholds.json·원자료 행 형식 검사와 회차 유효성 검사(순수 함수)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from port_metrics.catalog import (
    CHAIN_PAIRS,
    INPUT_KINDS,
    MODEL_TYPES,
    PURPOSES,
    RUN_KINDS,
    STAGES,
    Catalog,
    is_number,
    rule_limit_problems,
    value_type_ok,
    when_problems,
    whens_overlap,
)

RESULTS_SCHEMA = "port-metrics-results/1"
THRESHOLDS_SCHEMA = "port-metrics-thresholds/1"
BACKENDS = ("cpu", "cuda", "opencl", "vulkan")
PACINGS = ("max", "realtime")
PAIR_KINDS = ("chain", "base", "regress")
TIMING_KINDS = ("steady", "warmup", "flush", "aux")
EFFECTIVE_KEYS = ("weight_storage", "matmul_accum", "activation_quant")
RESERVED_SUBSETS = ("overall", "each")
ABBA_MIN_PAIRS = 3
DEFAULT_VALIDITY: dict[str, float] = {
    "start_battery_max_c": 34.0,
    "wait_max_sec": 600,
    "sampler_min_n": 100,
    "sampler_max_gap_ratio": 2.0,
}
# meta 키 → 0 을 허용하는지
_META_KEYS: dict[str, bool] = {
    "rss_peak_kb": True,
    "bundle_bytes": True,
    "hop_ms": False,
    "window_sec": False,
    "clk_tck": False,
    "sample_interval_sec": False,
    "work_amount": True,
    "wall_total_sec": True,
    "audio_total_sec": True,
}
_ID_COMMON = (
    "git_sha",
    "git_dirty",
    "manifest_sha256",
    "threads_effective",
    "thresholds_sha256",
)
_ID_S1 = ("torch_version", "device_name", "tf32", "checkpoint_sha256", "attn_impl")
_ID_S2 = ("mnn_commit", "bundle_files_sha256", "converter_args")
_ID_S3 = _ID_S2 + ("binary_sha256", "mnn_patches_sha256")
_ID_S4 = _ID_S3 + ("device_model", "soc", "android", "cpus_allowed")
_ID_S5 = _ID_S4 + (
    "apk_sha256",
    "so_sha256",
    "cpuset",
    "proc_state",
    "core_distribution",
)
IDENTITY_KEYS: dict[str, tuple[str, ...]] = {
    "S1": _ID_COMMON + _ID_S1,
    "S2": _ID_COMMON + _ID_S2,
    "S3": _ID_COMMON + _ID_S3,
    "S4": _ID_COMMON + _ID_S4,
    "S5": _ID_COMMON + _ID_S5,
}
_THERMAL_KEYS = ("start_battery_c", "clock_restored", "wait_sec", "pause_events")

Obj = dict[str, Any]


class FormatError(ValueError):
    """형식 오류(종료 코드 2)."""


@dataclass(frozen=True)
class CrossProblems:
    """회차 간 유효성 문제. sampler = 회차별 sampler 지표 무효 사유, abba = 블록별."""

    sampler: dict[str, list[str]] = field(default_factory=dict)
    abba: dict[str, list[str]] = field(default_factory=dict)


def _reject_constant(name: str) -> object:
    raise FormatError(f"JSON 에 {name} 은 허용하지 않음")


def parse_json(text: str) -> object:
    """JSON 파싱. NaN·Infinity·문법 오류는 FormatError."""
    try:
        return json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise FormatError(f"JSON 파싱 오류: {exc}") from exc


def parse_datetime(value: object) -> datetime | None:
    """타임존 포함 ISO 8601 datetime. 형식 위반이면 None."""
    if not isinstance(value, str):
        return None
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _is_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _missing(obj: Mapping[str, Any], keys: Sequence[str], where: str) -> list[str]:
    return [f"{where}.{k}: 필수 키 누락" for k in keys if k not in obj]


# ---------------------------------------------------------------- thresholds


def _scope_problems(scope: object) -> list[str]:
    if not isinstance(scope, dict):
        return ["scope: 객체여야 함"]
    out = _missing(scope, ("stages", "purposes", "model_types", "input_kind"), "scope")
    if out:
        return out
    lists = (
        ("stages", STAGES),
        ("purposes", PURPOSES),
        ("model_types", MODEL_TYPES),
    )
    for key, allowed in lists:
        value = scope[key]
        if not isinstance(value, list) or len(set(map(str, value))) != len(value):
            out.append(f"scope.{key}: 중복 없는 목록이어야 함")
            continue
        out += [f"scope.{key}: 값 {v!r} 위반" for v in value if v not in allowed]
    if isinstance(scope["stages"], list) and not scope["stages"]:
        out.append("scope.stages: 비어 있을 수 없음")
    if scope["input_kind"] not in INPUT_KINDS:
        out.append(f"scope.input_kind: 값 {scope['input_kind']!r} 위반")
    return out


def _rules_problems(rules: object, catalog: Catalog) -> list[str]:
    if not isinstance(rules, list):
        return ["rules: 목록이어야 함"]
    out: list[str] = []
    seen: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for i, rule in enumerate(rules):
        where = f"rules[{i}]"
        if not isinstance(rule, dict):
            out.append(f"{where}: 객체여야 함")
            continue
        probs = _missing(rule, ("metric", "when", "op", "limit"), where)
        allowed = ("metric", "when", "op", "limit", "noise_floor", "noise_source")
        probs += [
            f"{where}: 미지 키 {k!r}" for k in rule if k not in allowed + ("reason",)
        ]
        if probs:
            out += probs
            continue
        metric = rule["metric"]
        if not isinstance(metric, str) or not catalog.has(metric):
            out.append(f"{where}.metric: 미지 지표 {metric!r}")
            continue
        spec = catalog.get(metric)
        where = f"{where}({metric})"
        probs = when_problems(rule["when"], where)
        probs += rule_limit_problems(rule["op"], rule["limit"], spec.value_type, where)
        floor = rule.get("noise_floor")
        if floor is not None and not is_number(floor):
            probs.append(f"{where}.noise_floor: 수여야 함")
        for key in ("noise_source", "reason"):
            if key in rule and not isinstance(rule[key], str):
                probs.append(f"{where}.{key}: 문자열이어야 함")
        if not spec.judged and rule["op"] != "record":
            # 무시될 규칙을 조용히 받아들이지 않음
            probs.append(f"{where}: 기록 지표(judged=false)에는 op=record 만 허용")
        if probs:
            out += probs
            continue
        when: dict[str, str] = dict(rule["when"])
        for j, other in seen.setdefault(metric, []):
            if whens_overlap(when, other):
                out.append(f"{where}: rules[{j}] 와 when 겹침")
        seen[metric].append((i, when))
    return out


def validate_thresholds(obj: object, catalog: Catalog) -> list[str]:
    """thresholds.json 형식 문제 목록(빈 목록 = 정상)."""
    if not isinstance(obj, dict):
        return ["thresholds: 최상위는 객체여야 함"]
    keys = ("schema", "frozen_at", "scope", "validity", "rules", "abba_limits_pct")
    out = _missing(obj, keys, "thresholds")
    if out:
        return out
    if obj["schema"] != THRESHOLDS_SCHEMA:
        out.append(f"schema: {THRESHOLDS_SCHEMA!r} 이어야 함")
    if obj["frozen_at"] is not None and parse_datetime(obj["frozen_at"]) is None:
        out.append("frozen_at: 타임존 포함 ISO 8601 datetime 또는 null 이어야 함")
    out += _scope_problems(obj["scope"])
    validity = obj["validity"]
    if not isinstance(validity, dict):
        out.append("validity: 객체여야 함")
    else:
        for key in DEFAULT_VALIDITY:
            if not is_number(validity.get(key)) or validity[key] < 0:
                out.append(f"validity.{key}: 0 이상의 수여야 함")
    out += _rules_problems(obj["rules"], catalog)
    limits = obj["abba_limits_pct"]
    if not isinstance(limits, dict):
        out.append("abba_limits_pct: 객체여야 함")
    else:
        for metric, limit in limits.items():
            where = f"abba_limits_pct.{metric}"
            if not catalog.has(metric):
                out.append(f"{where}: 미지 지표")
            elif catalog.get(metric).abba_limit_pct is None:
                out.append(f"{where}: ABBA 대상 지표가 아님(abba_limit_pct 없음)")
            elif not is_number(limit) or limit < 0:
                out.append(f"{where}: 0 이상의 수여야 함")
    return out


def default_thresholds(catalog: Catalog, scope: Mapping[str, Any]) -> Obj:
    """scope 로 카탈로그 기본 규칙을 펼친 미동결 thresholds 객체."""
    sc: Obj = {
        "stages": [s for s in STAGES if s in scope["stages"]],
        "purposes": [p for p in PURPOSES if p in scope["purposes"]],
        "model_types": [m for m in MODEL_TYPES if m in scope["model_types"]],
        "input_kind": scope["input_kind"],
    }
    return {
        "schema": THRESHOLDS_SCHEMA,
        "frozen_at": None,
        "scope": sc,
        "validity": dict(DEFAULT_VALIDITY),
        "rules": catalog.default_rules(sc),
        "abba_limits_pct": catalog.default_abba_limits(sc),
    }


# ------------------------------------------------------------------- results


def _values_problems(
    values: object, catalog: Catalog, scope_kind: str, run_kind: str | None, where: str
) -> list[str]:
    """values[] 형식 문제. scope_kind = run|pair, 보조 키 = subset|tensor."""
    if not isinstance(values, list):
        return [f"{where}: 목록이어야 함"]
    sub_key = "subset" if scope_kind == "run" else "tensor"
    out: list[str] = []
    seen: set[tuple[str, str | None]] = set()
    for i, entry in enumerate(values):
        ew = f"{where}[{i}]"
        if not isinstance(entry, dict):
            out.append(f"{ew}: 객체여야 함")
            continue
        probs = _missing(entry, ("metric", "value"), ew)
        probs += [
            f"{ew}: 미지 키 {k!r}"
            for k in entry
            if k not in ("metric", "value", sub_key)
        ]
        if probs:
            out += probs
            continue
        metric = entry["metric"]
        if not isinstance(metric, str) or not catalog.has(metric):
            out.append(f"{ew}.metric: 미지 지표 {metric!r}")
            continue
        spec = catalog.get(metric)
        ew = f"{ew}({metric})"
        if spec.scope != scope_kind:
            out.append(f"{ew}: scope={spec.scope} 지표는 여기에 기입할 수 없음")
        if spec.source != "project":
            out.append(f"{ew}: generator 지표는 values 에 기입할 수 없음")
        if not value_type_ok(entry["value"], spec.value_type):
            out.append(f"{ew}.value: value_type={spec.value_type} 위반")
        if run_kind is not None and spec.run_kind not in ("any", run_kind):
            out.append(f"{ew}: run_kind={spec.run_kind} 회차 지표")
        sub = entry.get(sub_key)
        if sub_key in entry and not _is_str(sub):
            out.append(f"{ew}.{sub_key}: 비어 있지 않은 문자열이어야 함")
        elif sub_key == "subset" and sub in RESERVED_SUBSETS:
            out.append(f"{ew}.subset: 예약어 {sub!r} 사용(전체는 subset 생략)")
        elif (metric, sub) in seen:
            out.append(f"{ew}: 같은 지표·{sub_key} 값 중복")
        if sub is None or isinstance(sub, str):
            seen.add((metric, sub))
    return out


def _thermal_problems(thermal: object, where: str) -> list[str]:
    if not isinstance(thermal, dict):
        return [f"{where}: 객체여야 함"]
    out = _missing(thermal, _THERMAL_KEYS + ("source",), where)
    if out:
        return out
    for key in ("start_battery_c", "wait_sec"):
        if not is_number(thermal[key]):
            out.append(f"{where}.{key}: 수여야 함")
    if not isinstance(thermal["clock_restored"], bool):
        out.append(f"{where}.clock_restored: bool 이어야 함")
    if not value_type_ok(thermal["pause_events"], "int") or thermal["pause_events"] < 0:
        out.append(f"{where}.pause_events: 0 이상의 정수여야 함")
    if not _is_str(thermal["source"]):
        out.append(f"{where}.source: 비어 있지 않은 문자열이어야 함")
    return out


def _meta_problems(meta: object, where: str) -> list[str]:
    if not isinstance(meta, dict):
        return [f"{where}: 객체여야 함"]
    out: list[str] = []
    for key, value in meta.items():
        if key not in _META_KEYS:
            out.append(f"{where}.{key}: 미지 키")
        elif not is_number(value) or value < 0 or (value == 0 and not _META_KEYS[key]):
            bound = "0 이상" if _META_KEYS[key] else "양"
            out.append(f"{where}.{key}: {bound}의 수여야 함")
    return out


def _run_problems_format(
    run: Obj, catalog: Catalog, scope: Mapping[str, Any], where: str
) -> list[str]:
    required = ("run_id", "stage", "backend", "run_kind", "profile", "effective")
    out = _missing(run, required + ("started_at", "identity"), where)
    if out:
        return out
    for key in ("run_id", "profile"):
        if not _is_str(run[key]):
            out.append(f"{where}.{key}: 비어 있지 않은 문자열이어야 함")
    stage, kind = run["stage"], run["run_kind"]
    if stage not in STAGES:
        out.append(f"{where}.stage: 값 {stage!r} 위반")
    elif stage not in scope["stages"]:
        out.append(f"{where}.stage: {stage} 는 thresholds scope.stages 밖")
    if run["backend"] not in BACKENDS:
        out.append(f"{where}.backend: 값 {run['backend']!r} 위반")
    if kind not in RUN_KINDS:
        return out + [f"{where}.run_kind: 값 {kind!r} 위반"]
    if kind == "perf" and "pacing" not in run:
        out.append(f"{where}.pacing: 필수 키 누락(perf 회차)")
    if "pacing" in run and run["pacing"] not in PACINGS:
        out.append(f"{where}.pacing: 값 {run['pacing']!r} 위반")
    effective = run["effective"]
    if not isinstance(effective, dict):
        out.append(f"{where}.effective: 객체여야 함")
    else:
        for key in EFFECTIVE_KEYS:
            if not _is_str(effective.get(key)):
                out.append(f"{where}.effective.{key}: 비어 있지 않은 문자열이어야 함")
    if parse_datetime(run["started_at"]) is None:
        out.append(f"{where}.started_at: 타임존 포함 ISO 8601 datetime 이어야 함")
    if not isinstance(run["identity"], dict):
        out.append(f"{where}.identity: 객체여야 함")
    measured = kind in ("perf", "sampler")
    if measured and stage in ("S4", "S5") and "thermal" not in run:
        out.append(f"{where}.thermal: 필수 키 누락(S4·S5 perf·sampler 회차)")
    if "thermal" in run:
        out += _thermal_problems(run["thermal"], f"{where}.thermal")
    if measured and not _is_str(run.get("nonce")):
        out.append(f"{where}.nonce: 필수 키 누락(perf·sampler 회차)")
    for key, owner in (("timing", "perf"), ("samples", "sampler")):
        if kind == owner:
            if not _is_str(run.get(key)):
                out.append(f"{where}.{key}: 필수 키 누락({owner} 회차)")
        elif key in run:
            out.append(f"{where}.{key}: {owner} 회차가 아닌데 기입(회차 종류 위반)")
    if "meta" in run:
        out += _meta_problems(run["meta"], f"{where}.meta")
    if "values" in run:
        out += _values_problems(run["values"], catalog, "run", kind, f"{where}.values")
    if "acc_baseline" in run and not isinstance(run["acc_baseline"], bool):
        out.append(f"{where}.acc_baseline: bool 이어야 함")
    return out


def has_acc_primary(run: Mapping[str, Any]) -> bool:
    """회차가 ACC.primary 값을 갖는지."""
    values = run.get("values")
    if not isinstance(values, list):
        return False
    return any(isinstance(v, dict) and v.get("metric") == "ACC.primary" for v in values)


def acc_baseline_candidates(
    runs: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """S1 의 ACC.primary 회차 목록."""
    return [r for r in runs if r.get("stage") == "S1" and has_acc_primary(r)]


def select_acc_baseline(runs: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """S1 ACC 기준 회차 선택(schema·report 공용).

    후보 1 개면 그 회차, 2 개 이상이면 acc_baseline=true 가 정확히 1 개일 때 그 회차,
    그 외(후보 없음·모호)는 None.
    """
    candidates = acc_baseline_candidates(runs)
    if len(candidates) > 1:
        candidates = [r for r in candidates if r.get("acc_baseline") is True]
    return candidates[0] if len(candidates) == 1 else None


def _acc_baseline_problems(runs: Sequence[Obj]) -> list[str]:
    out: list[str] = []
    candidates = acc_baseline_candidates(runs)
    for run in runs:
        if run.get("acc_baseline") is True and run not in candidates:
            out.append(
                f"run {run.get('run_id')!r}: acc_baseline 은 "
                "S1 의 ACC.primary 회차에만 허용"
            )
    marked = [r for r in candidates if r.get("acc_baseline") is True]
    if len(candidates) >= 2 and select_acc_baseline(runs) is None:
        out.append(
            f"S1 ACC 기준 모호: ACC.primary 회차 {len(candidates)} 개 중 "
            f"acc_baseline=true 가 {len(marked)} 개(정확히 1 개여야 함)"
        )
    return out


def _known_run(ref: object, runs: Mapping[str, Mapping[str, Any]]) -> bool:
    return isinstance(ref, str) and ref in runs


def _pairs_problems(
    pairs: object, runs: Mapping[str, Obj], catalog: Catalog
) -> list[str]:
    if not isinstance(pairs, list):
        return ["pairs: 목록이어야 함"]
    out: list[str] = []
    seen: set[str] = set()
    for i, pair in enumerate(pairs):
        where = f"pairs[{i}]"
        if not isinstance(pair, dict):
            out.append(f"{where}: 객체여야 함")
            continue
        probs = _missing(pair, ("pair_id", "kind", "ref", "target", "values"), where)
        if probs:
            out += probs
            continue
        pair_id = pair["pair_id"]
        if not _is_str(pair_id):
            out.append(f"{where}.pair_id: 비어 있지 않은 문자열이어야 함")
        elif pair_id in seen:
            out.append(f"{where}.pair_id: {pair_id} 중복")
        seen.add(str(pair_id))
        if pair["kind"] not in PAIR_KINDS:
            out.append(f"{where}.kind: 값 {pair['kind']!r} 위반")
            continue
        unknown = [k for k in ("ref", "target") if not _known_run(pair[k], runs)]
        out += [f"{where}.{k}: 미지 run 참조 {pair[k]!r}" for k in unknown]
        out += _values_problems(
            pair["values"], catalog, "pair", None, f"{where}.values"
        )
        if unknown:
            continue
        ref_stage = runs[pair["ref"]].get("stage")
        target_stage = runs[pair["target"]].get("stage")
        if pair["ref"] == pair["target"]:
            out.append(f"{where}: ref 와 target 이 같은 회차")
        elif pair["kind"] == "chain":
            if f"{ref_stage}-{target_stage}" not in CHAIN_PAIRS:
                out.append(
                    f"{where}: chain 은 인접 단계만 허용({ref_stage}→{target_stage})"
                )
        elif pair["kind"] == "base":
            if ref_stage != "S1" or target_stage == "S1":
                out.append(f"{where}: base 는 ref=S1, target≠S1 이어야 함")
        elif ref_stage != target_stage:
            out.append(f"{where}: regress 는 같은 stage 여야 함")
    return out


def _abba_problems(
    blocks: object, runs: Mapping[str, Obj], catalog: Catalog
) -> list[str]:
    if not isinstance(blocks, list):
        return ["abba: 목록이어야 함"]
    out: list[str] = []
    seen: set[str] = set()
    for i, block in enumerate(blocks):
        where = f"abba[{i}]"
        if not isinstance(block, dict):
            out.append(f"{where}: 객체여야 함")
            continue
        probs = _missing(block, ("abba_id", "metrics", "pairs"), where)
        if probs:
            out += probs
            continue
        abba_id = block["abba_id"]
        if not _is_str(abba_id):
            out.append(f"{where}.abba_id: 비어 있지 않은 문자열이어야 함")
        elif abba_id in seen:
            out.append(f"{where}.abba_id: {abba_id} 중복")
        seen.add(str(abba_id))
        metrics = block["metrics"]
        if not isinstance(metrics, list) or not metrics:
            out.append(f"{where}.metrics: 비어 있지 않은 목록이어야 함")
        else:
            for metric in metrics:
                if not isinstance(metric, str) or not catalog.has(metric):
                    out.append(f"{where}.metrics: 미지 지표 {metric!r}")
                elif catalog.get(metric).abba_limit_pct is None:
                    out.append(f"{where}.metrics: {metric} 에 abba_limit 없음")
            if len(set(map(str, metrics))) != len(metrics):
                out.append(f"{where}.metrics: 지표 중복")
        if not isinstance(block["pairs"], list):
            out.append(f"{where}.pairs: 목록이어야 함")
            continue
        for j, pair in enumerate(block["pairs"]):
            pw = f"{where}.pairs[{j}]"
            if not isinstance(pair, dict) or set(pair) != {"a", "b"}:
                out.append(f"{pw}: 키는 a·b 여야 함")
                continue
            for key in ("a", "b"):
                if not _known_run(pair[key], runs):
                    out.append(f"{pw}.{key}: 미지 run 참조 {pair[key]!r}")
    return out


def validate_results(
    obj: object,
    catalog: Catalog,
    scope: Mapping[str, Any],
    partial: Sequence[str] | None,
) -> list[str]:
    """results.json 형식 문제 목록(빈 목록 = 정상). scope = thresholds.scope.

    회차 stage 는 항상 scope.stages 안이어야 하고, partial 도 scope.stages 의 부분집합.
    """
    if not isinstance(obj, dict):
        return ["results: 최상위는 객체여야 함"]
    out = _missing(obj, ("schema", "project", "runs"), "results")
    if out:
        return out
    if obj["schema"] != RESULTS_SCHEMA:
        out.append(f"schema: {RESULTS_SCHEMA!r} 이어야 함")
    if partial is not None:
        if not partial:
            out.append("partial: 비어 있을 수 없음")
        out += [
            f"partial: {s!r} 는 thresholds scope.stages 밖"
            for s in partial
            if s not in scope["stages"]
        ]
    project = obj["project"]
    task = project.get("task_metric") if isinstance(project, dict) else None
    if not isinstance(project, dict) or not _is_str(project.get("name")):
        out.append("project.name: 필수 키 누락")
    if not isinstance(task, dict):
        out.append("project.task_metric: 필수 키 누락")
    else:
        for key in ("id", "unit"):
            if not _is_str(task.get(key)):
                out.append(f"project.task_metric.{key}: 필수 키 누락")
        if task.get("direction") not in ("lower", "higher"):
            out.append("project.task_metric.direction: lower|higher 여야 함")
    runs = obj["runs"]
    if not isinstance(runs, list):
        return out + ["runs: 목록이어야 함"]
    by_id: dict[str, Obj] = {}
    for i, run in enumerate(runs):
        where = f"runs[{i}]"
        if not isinstance(run, dict):
            out.append(f"{where}: 객체여야 함")
            continue
        out += _run_problems_format(run, catalog, scope, where)
        run_id = run.get("run_id")
        if isinstance(run_id, str):
            if run_id in by_id:
                out.append(f"{where}.run_id: {run_id} 중복")
            by_id[run_id] = run
    out += _acc_baseline_problems([r for r in runs if isinstance(r, dict)])
    if "pairs" in obj:
        out += _pairs_problems(obj["pairs"], by_id, catalog)
    if "abba" in obj:
        out += _abba_problems(obj["abba"], by_id, catalog)
    return out


# ---------------------------------------------------------------- 원자료 행


def _rows_problems(
    rows: Sequence[object],
    where: str,
    numeric: Sequence[str],
    optional: Sequence[str],
) -> list[str]:
    out: list[str] = []
    for i, row in enumerate(rows):
        rw = f"{where}:{i + 1}"
        if not isinstance(row, dict):
            out.append(f"{rw}: 객체여야 함")
            continue
        for key in numeric:
            if not is_number(row.get(key)) or row[key] < 0:
                out.append(f"{rw}.{key}: 0 이상의 수여야 함(필수)")
        if not isinstance(row.get("paused"), bool):
            out.append(f"{rw}.paused: bool 이어야 함(필수)")
        for key in optional:
            if key in row and (not is_number(row[key]) or row[key] < 0):
                out.append(f"{rw}.{key}: 0 이상의 수여야 함")
    return out


def timing_rows_problems(rows: Sequence[object], where: str) -> list[str]:
    """timing.jsonl 행 형식 문제(§3.2)."""
    optional = ("audio_sec", "units", "t_start_sec", "prefill_ms", "decode_ms")
    out = _rows_problems(
        rows, where, ("wall_ms",), optional + ("gen_tokens", "ttft_ms")
    )
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        rw = f"{where}:{i + 1}"
        if "unit_id" not in row:
            out.append(f"{rw}.unit_id: 필수 키 누락")
        if row.get("kind") not in TIMING_KINDS:
            out.append(f"{rw}.kind: 값 {row.get('kind')!r} 위반")
        if "deadline_miss" in row and not isinstance(row["deadline_miss"], bool):
            out.append(f"{rw}.deadline_miss: bool 이어야 함")
    return out


def sample_rows_problems(rows: Sequence[object], where: str) -> list[str]:
    """samples.jsonl 행 형식 문제(§3.2). t_sec 는 단조 증가여야 함."""
    out = _rows_problems(
        rows, where, ("t_sec", "cpu_ticks", "rss_kb"), ("pss_kb", "hwm_kb")
    )
    if out:
        return out
    times = [row["t_sec"] for row in rows if isinstance(row, dict)]
    if any(b <= a for a, b in zip(times, times[1:])):
        out.append(f"{where}: t_sec 가 단조 증가하지 않음")
    return out


# ------------------------------------------------------------- 회차 유효성


def run_problems(
    run: Mapping[str, Any], thresholds: Mapping[str, Any], thresholds_sha: str
) -> list[str]:
    """회차 전체를 invalid 로 만드는 문제 목록(신원·동결 순서·열 조건)."""
    out: list[str] = []
    identity: Mapping[str, Any] = run.get("identity") or {}
    for key in IDENTITY_KEYS.get(str(run.get("stage")), _ID_COMMON):
        value = identity.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            out.append(f"신원 키 누락: identity.{key}")
    if "git_dirty" in identity and identity["git_dirty"] is not False:
        out.append("git_dirty 가 false 가 아님(측정 중 추적 파일 수정)")
    sha = identity.get("thresholds_sha256")
    if sha is not None and sha != thresholds_sha:
        out.append("thresholds_sha256 불일치(회차가 다른 동결 파일을 기준으로 측정됨)")
    frozen_at = parse_datetime(thresholds.get("frozen_at"))
    started_at = parse_datetime(run.get("started_at"))
    if frozen_at is not None and (started_at is None or started_at < frozen_at):
        out.append("started_at < frozen_at(임계 동결 전에 측정된 회차)")
    thermal = run.get("thermal")
    measured = run.get("run_kind") in ("perf", "sampler")
    if measured and run.get("stage") in ("S4", "S5"):
        validity: Mapping[str, Any] = thresholds.get("validity") or DEFAULT_VALIDITY
        if not isinstance(thermal, Mapping):
            return out + ["열 조건 기록(thermal) 없음"]
        max_c = validity["start_battery_max_c"]
        max_wait = validity["wait_max_sec"]
        if not is_number(thermal.get("start_battery_c")) or (
            thermal["start_battery_c"] > max_c
        ):
            out.append(
                f"시작 배터리 온도 {thermal.get('start_battery_c')} > {max_c} degC"
            )
        if thermal.get("clock_restored") is not True:
            out.append("상한 클럭 미복구(clock_restored 가 true 가 아님)")
        if not is_number(thermal.get("wait_sec")) or thermal["wait_sec"] > max_wait:
            out.append(f"대기 {thermal.get('wait_sec')} s > 상한 {max_wait} s")
    return out


def _sampler_pairing(runs: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    by_nonce: dict[str, dict[str, list[Mapping[str, Any]]]] = {}
    for run in runs:
        kind = run.get("run_kind")
        if kind in ("perf", "sampler"):
            group = by_nonce.setdefault(str(run.get("nonce")), {})
            group.setdefault(str(kind), []).append(run)
    for nonce, group in by_nonce.items():
        perfs = group.get("perf", [])
        samplers = group.get("sampler", [])
        for sampler in samplers:
            probs: list[str] = []
            if not perfs:
                probs.append(f"nonce {nonce!r} 의 perf 짝 없음")
            if len(perfs) > 1 or len(samplers) > 1:
                probs.append(
                    f"nonce {nonce!r} 1:1 위반(perf {len(perfs)}·"
                    f"sampler {len(samplers)})"
                )
            if len(perfs) == 1:
                perf = perfs[0]
                for key in ("stage", "backend", "profile"):
                    if perf.get(key) != sampler.get(key):
                        probs.append(f"perf 짝 {perf.get('run_id')} 과 {key} 불일치")
                sha_p = (perf.get("identity") or {}).get("git_sha")
                sha_s = (sampler.get("identity") or {}).get("git_sha")
                if sha_p != sha_s or sha_s is None:
                    probs.append(f"perf 짝 {perf.get('run_id')} 과 git_sha 불일치")
            if probs:
                out[str(sampler.get("run_id"))] = probs
    return out


def _abba_composition(
    block: Mapping[str, Any], runs: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    pairs: Sequence[Mapping[str, Any]] = block.get("pairs") or []
    out: list[str] = []
    if len(pairs) < ABBA_MIN_PAIRS:
        out.append(f"쌍 {len(pairs)} 개 < {ABBA_MIN_PAIRS}")
    orders: set[str] = set()
    used: list[str] = []
    members: list[Mapping[str, Any]] = []
    for pair in pairs:
        a, b = runs.get(pair["a"]), runs.get(pair["b"])
        used += [pair["a"], pair["b"]]
        if a is None or b is None:
            out.append("미지 run 참조")
            continue
        members += [a, b]
        ta, tb = (
            parse_datetime(a.get("started_at")),
            parse_datetime(b.get("started_at")),
        )
        if ta is None or tb is None or ta == tb:
            out.append(f"쌍 ({pair['a']}, {pair['b']}) 의 순서를 started_at 로 못 정함")
        else:
            orders.add("AB" if ta < tb else "BA")
    if len(orders) == 1:
        out.append(f"한쪽 순서({orders.pop()})만 있음(AB·BA 둘 다 필요)")
    if len(set(used)) != len(used):
        out.append("같은 회차가 여러 번 쓰임")
    if len({m.get("stage") for m in members}) > 1:
        out.append("stage 불일치")
    for key in ("run_kind", "pacing"):
        if len({str(m.get(key)) for m in members}) > 1:
            out.append(f"{key} 불일치(블록 내 모든 회차가 같아야 함)")
    for side in ("a", "b"):
        group = [runs[p[side]] for p in pairs if _known_run(p.get(side), runs)]
        shas = [(m.get("identity") or {}).get("git_sha") for m in group]
        if any(value != shas[0] for value in shas[1:]):
            out.append(f"{side} 쪽 회차끼리 git_sha 불일치")
        if len({str(m.get("profile")) for m in group}) > 1:
            out.append(f"{side} 쪽 회차끼리 profile 불일치")
    manifests = [(m.get("identity") or {}).get("manifest_sha256") for m in members]
    if any(value != manifests[0] for value in manifests[1:]):
        out.append("manifest_sha256 불일치")
    return out


def sampler_quality_problems(
    n: int, gap_ratio: float | None, validity: Mapping[str, Any]
) -> list[str]:
    """sampler 회차 품질 문제(표본 수·최대 간격 비). 원자료를 읽은 호출자가 값을 넘김."""
    out: list[str] = []
    min_n = validity["sampler_min_n"]
    max_gap = validity["sampler_max_gap_ratio"]
    if n < min_n:
        out.append(f"표본 수 {n} < {min_n}")
    if gap_ratio is None:
        out.append("표본 간격 비 계산 불가(meta.sample_interval_sec 없음)")
    elif gap_ratio > max_gap:
        out.append(f"표본 최대 간격 비 {gap_ratio:g} > {max_gap}")
    return out


def cross_problems(
    results: Mapping[str, Any], validity: Mapping[str, Any]
) -> CrossProblems:
    """회차 간 유효성 문제(sampler ↔ perf 결속·ABBA 구성).

    sampler 품질(표본 수·간격)은 원자료가 필요해 sampler_quality_problems 로 따로 검사.
    validity 는 계약 시그니처(§7)의 인자이며 현재 이 함수의 검사에는 쓰이지 않음.
    """
    runs: list[Mapping[str, Any]] = list(results.get("runs") or [])
    sampler = _sampler_pairing(runs)
    by_id = {str(r.get("run_id")): r for r in runs}
    abba: dict[str, list[str]] = {}
    for block in results.get("abba") or []:
        probs = _abba_composition(block, by_id)
        if probs:
            abba[str(block.get("abba_id"))] = probs
    return CrossProblems(sampler=sampler, abba=abba)
