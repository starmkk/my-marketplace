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
