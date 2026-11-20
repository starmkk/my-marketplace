"""테스트 공용 도우미(예제 픽스처 적재)."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from port_metrics.catalog import Catalog, load_catalog

SCRIPTS = Path(__file__).resolve().parent.parent
ROOT = SCRIPTS.parent
EXAMPLE = ROOT / "assets" / "example"
CATALOG_PATH = ROOT / "assets" / "catalog.json"
CATALOG_MD = ROOT / "references" / "metric-catalog.md"

Obj = dict[str, Any]


def catalog() -> Catalog:
    """카탈로그 정본 적재."""
    return load_catalog(CATALOG_PATH)


def example() -> tuple[Obj, Obj, str]:
    """예제 (results, thresholds, thresholds sha256)."""
    raw = (EXAMPLE / "thresholds.json").read_bytes()
    results: Obj = json.loads((EXAMPLE / "results.json").read_text(encoding="utf-8"))
    thresholds: Obj = json.loads(raw.decode("utf-8"))
    return results, thresholds, hashlib.sha256(raw).hexdigest()


def rows_loader(base: Path = EXAMPLE) -> Callable[[str], list[Obj]]:
    """base 기준 상대 경로의 jsonl 을 읽는 load_rows."""

    def load_rows(path: str) -> list[Obj]:
        text = (base / path).read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    return load_rows


def run_by_id(results: Obj, run_id: str) -> Obj:
    """run_id 로 회차 객체 조회."""
    for run in results["runs"]:
        if run["run_id"] == run_id:
            found: Obj = run
            return found
    raise KeyError(run_id)


def by_id(items: list[Obj], key: str, value: str) -> Obj:
    """목록에서 key == value 인 객체 조회."""
    for item in items:
        if item[key] == value:
            return item
    raise KeyError(value)


def clone(obj: Obj) -> Obj:
    """깊은 복사."""
    return copy.deepcopy(obj)


EXPECTED_REASON = "2 모델 파이프라인 구조 지터(선례 kor-perf R1)"
NOISE_ID = "abba_s4_noise"
TARGET_ID = "abba_s4_patch"


def set_rule(thresholds: Obj, metric: str, stage: str, **changes: Any) -> Obj:
    """when == {stage} 인 규칙을 찾아 키를 덮어씀."""
    for rule in thresholds["rules"]:
        if rule["metric"] == metric and rule["when"] == {"stage": stage}:
            rule.update(changes)
            found: Obj = rule
            return found
    raise KeyError((metric, stage))


def expect_fail(
    thresholds: Obj, metric: str, stage: str, regress: bool, **changes: Any
) -> Obj:
    """규칙에 예상 fail 을 등록한 thresholds 사본. regress=False 면 목적에서 regress 제거."""
    out = clone(thresholds)
    set_rule(out, metric, stage, expected_fail=EXPECTED_REASON, **changes)
    if not regress:
        out["scope"]["purposes"].remove("regress")
    return out


def add_superseded(
    results: Obj,
    run_id: str,
    old_id: str,
    started_at: str,
    reason: str = "열 정지 재측정",
) -> Obj:
    """run_id 의 사본을 old_id 로 넣고 run_id 로 대체됨 표시(원본 앞에 삽입)."""
    old = clone(run_by_id(results, run_id))
    old.update(
        run_id=old_id,
        started_at=started_at,
        superseded_by=run_id,
        superseded_reason=reason,
    )
    index = [r["run_id"] for r in results["runs"]].index(run_id)
    results["runs"].insert(index, old)
    return old


def add_noise_block(
    results: Obj,
    b_rss_kb: int = 204800,
    metrics: tuple[str, ...] = ("RES.rss_peak_mib",),
) -> list[Obj]:
    """abba_s4_patch 의 A ↔ A 잡음 블록(전부 a 쪽 빌드)과 그 회차 6 건 추가."""
    times = {"a1": "15:00", "b1": "15:10", "b2": "15:20", "a2": "15:30"}
    times.update({"a3": "15:40", "b3": "15:50"})
    runs: list[Obj] = []
    for name, clock in times.items():
        run = clone(run_by_id(results, f"s4_perf_a{name[1]}"))
        run.update(
            run_id=f"nz_{name}",
            nonce=f"n-nz-{name}",
            started_at=f"2026-11-12T{clock}:00+09:00",
        )
        if name.startswith("b"):
            run["meta"]["rss_peak_kb"] = b_rss_kb
        runs.append(run)
    results["runs"] += runs
    results["abba"].append(
        {
            "abba_id": NOISE_ID,
            "noise_for": TARGET_ID,
            "metrics": list(metrics),
            "pairs": [{"a": f"nz_a{n}", "b": f"nz_b{n}"} for n in (1, 2, 3)],
        }
    )
    return runs
