"""catalog 모듈 테스트(계획서 §8 36~39)."""

from __future__ import annotations

import json
import unittest
from typing import Any

from port_metrics import catalog as cat
from port_metrics import render, schema
from tests import helpers

Obj = dict[str, Any]
ALL_STAGES = ["S1", "S2", "S3", "S4", "S5"]


def scope(**over: Any) -> Obj:
    """기본 scope(전 단계·목적 없음·audio)에 덮어쓰기."""
    base: Obj = {
        "stages": ALL_STAGES,
        "purposes": [],
        "model_types": [],
        "input_kind": "audio",
    }
    base.update(over)
    return base


class CatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = helpers.catalog()
        self.raw: Obj = json.loads(helpers.CATALOG_PATH.read_text(encoding="utf-8"))

    def test_catalog_valid(self) -> None:
        self.assertEqual(cat.catalog_problems(self.raw), [])
        self.assertEqual(len(self.catalog.metrics), 45)
        for spec in self.catalog.metrics:
            if spec.abba_limit_pct is not None:
                self.assertNotEqual(spec.direction, "none", spec.id)

        def broken(key: str, value: Any, index: int = 0) -> list[str]:
            obj = helpers.clone(self.raw)
            obj["metrics"][index][key] = value
            return cat.catalog_problems(obj)

        self.assertTrue(broken("id", self.raw["metrics"][1]["id"]))
        self.assertTrue(broken("category", "XXX"))
        self.assertTrue(broken("value_type", "str"))
        self.assertTrue(broken("direction", "up"))
        self.assertTrue(broken("default_rules", [{"when": {}, "op": "<", "limit": 1}]))
        self.assertTrue(broken("default_rules", [{"when": {"x": "y"}, "op": "<="}]))
        rtf = [m["id"] for m in self.raw["metrics"]].index("SPD.rtf_max")
        self.assertTrue(broken("direction", "none", rtf))

    def test_required_by_scope(self) -> None:
        core = self.catalog.required(scope(), None).ids()
        self.assertIn("SPD.rtf_max", core)
        self.assertNotIn("SPD.units_per_sec", core)
        self.assertNotIn("CNV.audit_ok", core)
        self.assertNotIn("SPD.jitter", core)

        convert = self.catalog.required(scope(purposes=["convert"]), None).ids()
        self.assertIn("CNV.audit_ok", convert)
        self.assertNotIn("CNV.act_range_margin", convert)

        ship = self.catalog.required(scope(purposes=["ship"]), None).ids()
        self.assertTrue({"STB.soak_p99_ratio", "STB.deterministic"} <= ship)
        self.assertNotIn("STB.reuse_identical", ship)

        streaming = self.catalog.required(scope(model_types=["streaming"]), None)
        self.assertIn(("SPD.jitter", "S4"), streaming.run)
        self.assertNotIn(("SPD.jitter", "S2"), streaming.run)

        other = self.catalog.required(scope(input_kind="other"), None).ids()
        self.assertIn("SPD.units_per_sec", other)
        self.assertNotIn("SPD.rtf_max", other)

        regress = self.catalog.required(scope(purposes=["regress"]), None)
        self.assertIn(("DEC.match_rate", "regress", ""), regress.pair)
        self.assertEqual(
            set(regress.abba), {"SPD.rtf_max", "SPD.lat_p99", "RES.rss_peak_mib"}
        )
        self.assertIn(("DEC.severe_flip", "base", "S5"), regress.pair)

        partial = self.catalog.required(scope(purposes=["ship"]), ["S1", "S2"])
        self.assertEqual({s for _, s in partial.run}, {"S1", "S2"})
        self.assertEqual({c for _, c, _ in partial.pair}, {"S1-S2", "base"})

    def test_default_rules_disjoint(self) -> None:
        full = scope(purposes=list(cat.PURPOSES), model_types=list(cat.MODEL_TYPES))
        for sc in (full, scope(), scope(input_kind="other", purposes=["ship"])):
            thresholds = schema.default_thresholds(self.catalog, sc)
            self.assertEqual(schema.validate_thresholds(thresholds, self.catalog), [])
            rules = thresholds["rules"]
            self.assertTrue(rules)
            for i, a in enumerate(rules):
                for b in rules[i + 1 :]:
                    if a["metric"] == b["metric"]:
                        self.assertFalse(cat.whens_overlap(a["when"], b["when"]), a)

    def test_catalog_md_in_sync(self) -> None:
        text = helpers.CATALOG_MD.read_text(encoding="utf-8")
        region = render.extract_generated(text)
        self.assertIsNotNone(region)
        self.assertEqual(region, render.render_catalog_table(self.catalog))


if __name__ == "__main__":
    unittest.main()
