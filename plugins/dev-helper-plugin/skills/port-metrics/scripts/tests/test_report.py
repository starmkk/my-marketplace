"""report·render 모듈 테스트(계획서 §8 40~44)."""

from __future__ import annotations

import unittest
from typing import Any

from port_metrics import render, report
from port_metrics.report import Item, ReportModel
from tests import helpers

Obj = dict[str, Any]


class ReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = helpers.catalog()
        self.results, self.thresholds, self.sha = helpers.example()

    def build(self, results: Obj | None = None, **kwargs: Any) -> ReportModel:
        return report.build_report(
            results or self.results,
            kwargs.get("thresholds", self.thresholds),
            self.sha,
            self.catalog,
            kwargs.get("load_rows", helpers.rows_loader()),
            kwargs.get("partial"),
        )

    def item(
        self, model: ReportModel, metric: str, ref: str, subset: str | None = None
    ) -> Item:
        found = [
            i
            for i in model.items
            if i.metric == metric and i.ref == ref and i.subset == subset
        ]
        self.assertEqual(len(found), 1, (metric, ref, subset, found))
        return found[0]

    def value(self, model: ReportModel, metric: str, ref: str) -> float:
        got = self.item(model, metric, ref).value
        assert isinstance(got, float)
        return got

    def test_build_report_example(self) -> None:
        model = self.build()
        self.assertAlmostEqual(
            self.value(model, "SPD.rtf_max", "s4_perf_b1"), 0.86 / 3.28, places=9
        )
        self.assertEqual(self.value(model, "SPD.lat_p50", "s4_perf_b1"), 42.0)
        self.assertEqual(self.value(model, "SPD.lat_p95", "s4_perf_b1"), 44.0)
        self.assertEqual(self.value(model, "SPD.lat_p99", "s4_perf_b1"), 44.0)
        self.assertEqual(self.value(model, "RES.rss_peak_mib", "s4_perf_b1"), 202.0)
        self.assertEqual(self.value(model, "RES.cpu_s_per_unit", "s4_sampler"), 2.5)
        overall = self.item(model, "ACC.degradation", "s4_acc")
        assert isinstance(overall.value, float)
        self.assertAlmostEqual(overall.value, 0.20, places=9)
        self.assertEqual(overall.status, "pass")
        noisy = self.item(model, "ACC.degradation", "s4_acc", "noisy")
        assert isinstance(noisy.value, float)
        self.assertAlmostEqual(noisy.value, 0.30, places=9)
        abba = self.item(model, "SPD.rtf_max", "abba_s4_patch")
        assert isinstance(abba.value, float)
        self.assertAlmostEqual(
            abba.value, (0.86 / 3.28 - 0.25) / 0.25 * 100.0, places=6
        )
        self.assertEqual(abba.status, "pass")
        self.assertEqual(self.item(model, "SPD.jitter", "s5_perf").status, "fail")
        self.assertEqual(model.missing, [])
        # thresholds.abba_limits_pct 에 항목이 없으면 통과가 아니라 not_established
        no_limit = helpers.clone(self.thresholds)
        del no_limit["abba_limits_pct"]["SPD.lat_p99"]
        unlimited = self.build(thresholds=no_limit)
        self.assertEqual(
            self.item(unlimited, "SPD.lat_p99", "abba_s4_patch").status,
            "not_established",
        )
        self.assertEqual(
            self.item(unlimited, "SPD.rtf_max", "abba_s4_patch").status, "pass"
        )
        self.assertEqual(model.counts["invalid"], 0)
        self.assertEqual(model.counts["not_established"], 0)
        self.assertEqual(model.counts["fail"], 1)
        self.assertGreater(model.counts["pass"], 0)
        self.assertEqual(model.overall, "fail")
        self.assertEqual(model.exit_code, 1)

    def test_build_report_missing_required(self) -> None:
        results = helpers.clone(self.results)
        run = helpers.run_by_id(results, "s2_acc")
        run["values"] = [v for v in run["values"] if v["metric"] != "CNV.audit_ok"]
        model = self.build(results)
        self.assertEqual(len(model.missing), 1)
        self.assertIn("CNV.audit_ok", model.missing[0])
        missing = [i for i in model.items if i.kind == "missing"]
        self.assertEqual([i.metric for i in missing], ["CNV.audit_ok"])
        self.assertEqual(missing[0].status, "not_established")
        self.assertEqual(model.overall, "not_established")

        # 서브셋이 한쪽에만 있으면 그 서브셋은 not_established(overall 만으로 통과 불가)
        subset = helpers.clone(self.results)
        s3 = helpers.run_by_id(subset, "s3_acc")
        s3["values"] = [v for v in s3["values"] if v.get("subset") != "noisy"]
        s5 = helpers.run_by_id(subset, "s5_acc")
        s5["values"].append({"metric": "ACC.primary", "value": 9.0, "subset": "far"})
        # 의도한 fail 을 없애 판정 불성립만으로 종료 코드 1 이 되는지 확인
        helpers.run_by_id(subset, "s5_perf")["timing"] = "timing_s4_b1.jsonl"
        one_sided = self.build(subset)
        self.assertEqual(one_sided.counts["fail"], 0)
        self.assertEqual(
            self.item(one_sided, "ACC.degradation", "s3_acc", "noisy").status,
            "not_established",
        )
        self.assertEqual(
            self.item(one_sided, "ACC.degradation", "s5_acc", "far").status,
            "not_established",
        )
        self.assertEqual(
            self.item(one_sided, "ACC.degradation", "s3_acc").status, "pass"
        )
        self.assertEqual(one_sided.counts["not_established"], 2)
        self.assertEqual(one_sided.exit_code, 1)

        partial = self.build(results, partial=["S3", "S4"])
        self.assertEqual(partial.missing, [])
        self.assertEqual(partial.partial, ["S3", "S4"])

    def test_invalid_propagation(self) -> None:
        results = helpers.clone(self.results)
        helpers.run_by_id(results, "s1_acc_cuda")["identity"]["git_dirty"] = True
        helpers.run_by_id(results, "s4_perf_a1")["identity"]["git_dirty"] = True
        model = self.build(results)
        self.assertEqual(
            self.item(model, "ACC.primary", "s1_acc_cuda").status, "invalid"
        )
        self.assertEqual(
            self.item(model, "DEC.severe_flip", "base_s4").status, "invalid"
        )
        self.assertEqual(
            self.item(model, "ACC.degradation", "s4_acc").status, "invalid"
        )
        self.assertEqual(
            self.item(model, "ACC.degradation", "s3_acc", "clean").status, "invalid"
        )
        self.assertEqual(
            self.item(model, "SPD.rtf_max", "abba_s4_patch").status, "invalid"
        )
        self.assertEqual(
            self.item(model, "DEC.match_rate", "chain_s2_s3").status, "pass"
        )
        self.assertEqual(model.overall, "invalid")

    def test_sampler_quality_invalidates_sampler_metrics_only(self) -> None:
        base = helpers.rows_loader()
        samples_path = helpers.run_by_id(self.results, "s4_sampler")["samples"]

        def short_rows(path: str) -> list[Obj]:
            rows = base(path)
            return rows[:50] if path == samples_path else rows

        model = self.build(load_rows=short_rows)
        for metric in ("RES.cpu_pct_mean", "RES.cpu_s_per_unit", "RES.pss_mean_mib"):
            self.assertEqual(self.item(model, metric, "s4_sampler").status, "invalid")
        self.assertEqual(self.item(model, "SPD.rtf_max", "s4_perf_b1").status, "pass")
        self.assertEqual(
            self.item(model, "RES.cpu_pct_mean", "s5_sampler").status, "record_only"
        )

    def test_render_call_path_and_input_set(self) -> None:
        # 단말 보고에서 "어떤 경로로·어떤 입력으로 쟀나" 질문이 반복된 원인(2026-11-19 리포트 A3)
        results = helpers.clone(self.results)
        identity = helpers.run_by_id(results, "s4_perf_a1")["identity"]
        identity["call_path"] = "cli:port_cli"
        identity["manifest_name"] = "golden_v1"
        text = render.render_report(self.build(results))
        self.assertIn("| s4_perf_a1 | cli:port_cli | golden_v1 (88c7275ef3ef) |", text)
        # S3~S5 의 선택 키 미기록은 (미기록), S1·S2 는 해당 없음(-)
        self.assertIn("| s3_acc | (미기록) | 88c7275ef3ef |", text)
        self.assertIn("| s1_perf | - | 88c7275ef3ef |", text)

    def test_checklist_device_lines_follow_scope(self) -> None:
        # 리뷰 Low 반영: S1·S2 만 재는 체크리스트에는 단말 안내가 잡음 — 분기 검증
        thresholds = helpers.clone(self.thresholds)
        thresholds["scope"]["stages"] = ["S1", "S2"]
        text = render.render_checklist(self.catalog, thresholds)
        self.assertNotIn("call_path", text)
        self.assertNotIn("chain pair", text)

    def test_render_counts(self) -> None:
        model = self.build()
        text = render.render_report(model)
        for status, count in model.counts.items():
            self.assertIn(f"| {status} | {count} |", text)
        self.assertEqual(sum(model.counts.values()), len(model.items))
        for item in model.items:
            if item.status == "fail":
                self.assertIn(item.metric, text)
        self.assertIn("SPD.jitter", text)
        self.assertEqual(model.rule_deviations, [])
        self.assertIn("카탈로그 기본 규칙과 다른 규칙: 0 건", text)
        for key, value in self.thresholds["validity"].items():
            self.assertIn(f"{key} = {value:g}", text)
        loose = helpers.clone(self.thresholds)
        for rule in loose["rules"]:
            if rule["metric"] == "SPD.jitter" and rule["when"] == {"stage": "S5"}:
                rule["limit"] = 4.0
        loose["rules"].append(
            {"metric": "SPD.lat_p50", "when": {}, "op": "record", "limit": None}
        )
        loosened = self.build(thresholds=loose)
        self.assertEqual(len(loosened.rule_deviations), 2)
        loose_text = render.render_report(loosened)
        self.assertIn("카탈로그 기본 규칙과 다른 규칙: 2 건", loose_text)
        self.assertIn("SPD.jitter [stage=S5]: 기본 <= 2.0 → <= 4.0", loose_text)
        # S5 는 출하 프로세스 상태만 측정 → 코어 집합이 리포트에 보여야 함(D6)
        for needle in ("cpus_allowed", "core_distribution", "top-app", "cpu4-6"):
            self.assertIn(needle, text)
        hidden = helpers.clone(self.results)
        del helpers.run_by_id(hidden, "s5_perf")["identity"]["cpuset"]
        self.assertIn("(누락)", render.render_report(self.build(hidden)))
        self.assertNotIn("(누락)", text)


if __name__ == "__main__":
    unittest.main()
