"""judge 모듈 테스트(계획서 §8 28~35)."""

from __future__ import annotations

import unittest
from typing import Any

from port_metrics import judge
from port_metrics.judge import Rule
from tests import helpers


class JudgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = helpers.catalog()
        self.lower = self.catalog.get("NUM.max_abs")
        self.higher = self.catalog.get("NUM.cos_min")
        self.count = self.catalog.get("SPD.deadline_miss")
        self.flag = self.catalog.get("CNV.audit_ok")

    def test_judge_ops_boundary(self) -> None:
        le = Rule("NUM.max_abs", {}, "<=", 1e-3)
        ge = Rule("NUM.cos_min", {}, ">=", 0.99)
        eq = Rule("SPD.deadline_miss", {}, "==", 0)
        flag = Rule("CNV.audit_ok", {}, "==", True)
        self.assertEqual(judge.judge_value(self.lower, 1e-3, le, True).status, "pass")
        self.assertEqual(judge.judge_value(self.lower, 1.1e-3, le, True).status, "fail")
        self.assertEqual(judge.judge_value(self.higher, 0.99, ge, True).status, "pass")
        self.assertEqual(judge.judge_value(self.higher, 0.98, ge, True).status, "fail")
        self.assertEqual(judge.judge_value(self.count, 0, eq, True).status, "pass")
        self.assertEqual(judge.judge_value(self.count, 1, eq, True).status, "fail")
        self.assertEqual(judge.judge_value(self.flag, True, flag, True).status, "pass")
        self.assertEqual(judge.judge_value(self.flag, False, flag, True).status, "fail")

    def test_judge_noise_floor_both_ops(self) -> None:
        le = Rule("NUM.max_abs", {}, "<=", 1e-3, noise_floor=2e-3)
        ge = Rule("NUM.cos_min", {}, ">=", 0.99, noise_floor=0.98)
        ok = Rule("NUM.max_abs", {}, "<=", 1e-3, noise_floor=1e-3)
        self.assertEqual(
            judge.judge_value(self.lower, 1e-6, le, True).status, "not_established"
        )
        self.assertEqual(
            judge.judge_value(self.higher, 1.0, ge, True).status, "not_established"
        )
        self.assertEqual(judge.judge_value(self.lower, 1e-6, ok, True).status, "pass")

    def test_judge_judged_without_rule_not_established(self) -> None:
        got = judge.judge_value(self.lower, 0.0, None, True)
        self.assertEqual(got.status, "not_established")
        unjudged = self.catalog.get("SPD.lat_p50")
        self.assertEqual(
            judge.judge_value(unjudged, 1.0, None, True).status, "record_only"
        )

    def test_judge_record_rule(self) -> None:
        rule = Rule("NUM.max_abs", {}, "record", None)
        self.assertEqual(
            judge.judge_value(self.lower, 9.9, rule, True).status, "record_only"
        )

    def test_judge_null_limit_and_unfrozen(self) -> None:
        null = Rule("NUM.max_abs", {}, "<=", None)
        rule = Rule("NUM.max_abs", {}, "<=", 1e-3)
        self.assertEqual(
            judge.judge_value(self.lower, 0.0, null, True).status, "not_established"
        )
        self.assertEqual(
            judge.judge_value(self.lower, 0.0, rule, False).status, "not_established"
        )
        self.assertEqual(
            judge.judge_value(self.lower, None, rule, True).status, "not_established"
        )

    def test_select_rule_matching(self) -> None:
        rules: list[dict[str, Any]] = [
            {
                "metric": "NUM.max_abs",
                "when": {"pair": "S1-S2", "class": "fp"},
                "op": "<=",
                "limit": 1e-3,
                "noise_floor": 1e-5,
            },
            {
                "metric": "NUM.max_abs",
                "when": {"pair": "S1-S2", "class": "lowp"},
                "op": "record",
                "limit": None,
            },
            {"metric": "SPD.jitter", "when": {"stage": "S4"}, "op": "<=", "limit": 2},
            {
                "metric": "ACC.degradation",
                "when": {"subset": "overall"},
                "op": "<=",
                "limit": 0.3,
            },
            {
                "metric": "ACC.degradation",
                "when": {"subset": "each"},
                "op": "<=",
                "limit": 0.5,
            },
        ]
        fp = judge.select_rule(
            rules, "NUM.max_abs", {"pair": "S1-S2", "class": "fp", "subset": None}
        )
        assert fp is not None
        self.assertEqual((fp.op, fp.limit, fp.noise_floor), ("<=", 1e-3, 1e-5))
        lowp = judge.select_rule(
            rules, "NUM.max_abs", {"pair": "S1-S2", "class": "lowp"}
        )
        assert lowp is not None
        self.assertEqual(lowp.op, "record")
        self.assertIsNone(
            judge.select_rule(rules, "NUM.max_abs", {"pair": "S2-S3", "class": "fp"})
        )
        self.assertIsNone(judge.select_rule(rules, "SPD.jitter", {"stage": "S5"}))
        self.assertIsNotNone(judge.select_rule(rules, "SPD.jitter", {"stage": "S4"}))
        overall = judge.select_rule(
            rules, "ACC.degradation", {"stage": "S4", "subset": None}
        )
        each = judge.select_rule(
            rules, "ACC.degradation", {"stage": "S4", "subset": "noisy"}
        )
        assert overall is not None and each is not None
        self.assertEqual((overall.limit, each.limit), (0.3, 0.5))
        dup = rules + [dict(rules[2])]
        with self.assertRaises(ValueError):
            judge.select_rule(dup, "SPD.jitter", {"stage": "S4"})

    def test_worst_priority(self) -> None:
        self.assertEqual(
            judge.worst(["pass", "fail", "not_established", "invalid"]), "invalid"
        )
        self.assertEqual(
            judge.worst(["pass", "fail", "not_established"]), "not_established"
        )
        self.assertEqual(judge.worst(["pass", "fail", "record_only"]), "fail")
        self.assertEqual(judge.worst(["pass", "record_only"]), "pass")
        self.assertEqual(judge.worst(["record_only"]), "record_only")
        self.assertEqual(judge.worst([]), "record_only")

    def test_pair_class(self) -> None:
        fp = {
            "weight_storage": "fp16",
            "matmul_accum": "fp32",
            "activation_quant": "none",
        }
        lowp = {
            "weight_storage": "int8",
            "matmul_accum": "fp32",
            "activation_quant": "none",
        }
        half = dict(fp, matmul_accum="fp16")
        self.assertEqual(judge.pair_class(fp, fp), "fp")
        self.assertEqual(judge.pair_class(fp, lowp), "lowp")
        self.assertEqual(judge.pair_class(lowp, fp), "lowp")
        self.assertEqual(judge.pair_class(fp, half), "lowp")


if __name__ == "__main__":
    unittest.main()
