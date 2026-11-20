"""report·render 모듈 테스트(계획서 §8 40~44)."""

from __future__ import annotations

import unittest
from typing import Any

from port_metrics import render, report, schema
from port_metrics.report import Item, ReportModel
from tests import helpers

Obj = dict[str, Any]


class ReportBase(unittest.TestCase):
    """예제 픽스처와 조회 도우미."""

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
        self,
        model: ReportModel,
        metric: str,
        ref: str,
        subset: str | None = None,
        kind: str | None = None,
    ) -> Item:
        found = [
            i
            for i in model.items
            if i.metric == metric and i.ref == ref and i.subset == subset
            if kind is None or i.kind == kind
        ]
        self.assertEqual(len(found), 1, (metric, ref, subset, found))
        return found[0]

    def value(self, model: ReportModel, metric: str, ref: str) -> float:
        got = self.item(model, metric, ref).value
        assert isinstance(got, float)
        return got


class ReportTest(ReportBase):
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


class Report125Test(ReportBase):
    """1.0.25: 예상 fail·균형·대체 회차·잡음 블록·키 검사(계획 §4·§7.2 T6~T18·T21)."""

    def expect(self, metric: str = "SPD.jitter", stage: str = "S5", **kw: Any) -> Obj:
        regress = bool(kw.pop("regress", False))
        return helpers.expect_fail(self.thresholds, metric, stage, regress, **kw)

    def balance(self, model: ReportModel) -> list[Item]:
        return [i for i in model.items if i.kind == "balance"]

    # ------------------------------------------------------------ F1 예상 fail

    def test_expected_fail_only_rc0(self) -> None:
        # T6
        model = self.build(thresholds=self.expect())
        item = self.item(model, "SPD.jitter", "s5_perf")
        self.assertEqual(item.status, "fail")
        self.assertTrue(item.is_expected_fail)
        self.assertEqual(item.expected_fail, helpers.EXPECTED_REASON)
        self.assertEqual(model.counts["fail"], 1)
        self.assertEqual(model.counts["invalid"] + model.counts["not_established"], 0)
        self.assertEqual(model.expected_fail, 1)
        self.assertEqual(model.overall, "pass")
        self.assertEqual(model.exit_code, 0)

    def test_expected_fail_rule_passing(self) -> None:
        # T7: 등록했지만 pass 인 항목에는 표지 없음
        model = self.build(thresholds=self.expect(limit=4.0))
        item = self.item(model, "SPD.jitter", "s5_perf")
        self.assertEqual(item.status, "pass")
        self.assertFalse(item.is_expected_fail)
        self.assertEqual(model.expected_fail, 0)
        self.assertEqual(model.counts["fail"], 0)
        self.assertEqual(model.exit_code, 0)
        self.assertNotIn("(예상)", render.render_report(model))

    def test_unexpected_fail_keeps_rc1(self) -> None:
        # T8
        thresholds = self.expect()
        helpers.set_rule(thresholds, "SPD.step_p95_over_hop", "S5", limit=0.5)
        model = self.build(thresholds=thresholds)
        unexpected = self.item(model, "SPD.step_p95_over_hop", "s5_perf")
        self.assertEqual(unexpected.status, "fail")
        self.assertFalse(unexpected.is_expected_fail)
        self.assertEqual(model.expected_fail, 1)
        self.assertGreater(model.counts["fail"], model.expected_fail)
        self.assertEqual(model.overall, "fail")
        self.assertEqual(model.exit_code, 1)

    def test_expected_fail_with_invalid_or_not_established(self) -> None:
        # T9
        dirty = helpers.clone(self.results)
        helpers.run_by_id(dirty, "s3_perf")["identity"]["git_dirty"] = True
        invalid = self.build(dirty, thresholds=self.expect())
        self.assertEqual(invalid.expected_fail, 1)
        self.assertEqual(invalid.counts["fail"], 1)
        self.assertGreater(invalid.counts["invalid"], 0)
        self.assertEqual(invalid.overall, "invalid")
        self.assertEqual(invalid.exit_code, 1)

        gap = helpers.clone(self.results)
        run = helpers.run_by_id(gap, "s2_acc")
        run["values"] = [v for v in run["values"] if v["metric"] != "CNV.audit_ok"]
        unsettled = self.build(gap, thresholds=self.expect())
        self.assertEqual(unsettled.expected_fail, 1)
        self.assertEqual(unsettled.counts["fail"], 1)
        self.assertEqual(unsettled.counts["not_established"], 1)
        self.assertEqual(unsettled.overall, "not_established")
        self.assertEqual(unsettled.exit_code, 1)

    # ------------------------------------------------------------ F1b 균형

    def rtf_s4(self, limit: float) -> Obj:
        """S4 rtf_max 예상 fail(a = 0.25, b = 0.262) + S5 지터는 통과시킴."""
        thresholds = self.expect("SPD.rtf_max", "S4", regress=True, limit=limit)
        helpers.set_rule(thresholds, "SPD.jitter", "S5", limit=4.0)
        return thresholds

    def test_balance_cases(self) -> None:
        # T10
        worse = self.build(thresholds=self.rtf_s4(0.255))
        item = self.item(worse, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertEqual((item.status, item.value), ("fail", 3))
        self.assertFalse(item.is_expected_fail)
        self.assertIn("b 쪽 fail 3 > a 쪽 0", item.reason)
        self.assertIn("a 3건 중 fail 0, b 3건 중 fail 3", item.reason)
        self.assertEqual(worse.expected_fail, 3)
        self.assertEqual(worse.counts["fail"], 4)
        self.assertEqual((worse.overall, worse.exit_code), ("fail", 1))
        self.assertIn(
            "- 예상 밖 fail 지표: `SPD.rtf_max` 예상 fail 균형",
            render.render_report(worse),
        )

        even = self.build(thresholds=self.rtf_s4(0.2))
        item = self.item(even, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertEqual((item.status, item.value), ("pass", 0))
        self.assertEqual(even.expected_fail, 6)
        self.assertEqual(even.counts["fail"], 6)
        self.assertEqual((even.overall, even.exit_code), ("pass", 0))

        thresholds = self.expect("SPD.jitter", "S4", regress=True, limit=1.049)
        better = self.build(thresholds=thresholds)
        item = self.item(better, "SPD.jitter", helpers.TARGET_ID, kind="balance")
        self.assertEqual((item.status, item.value), ("pass", -3))
        self.assertIn("a 3건 중 fail 3, b 3건 중 fail 0", item.reason)

        dirty = helpers.clone(self.results)
        helpers.run_by_id(dirty, "s4_perf_b1")["identity"]["git_dirty"] = True
        unsettled = self.build(dirty, thresholds=self.rtf_s4(0.2))
        item = self.item(unsettled, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertEqual(item.status, "not_established")
        self.assertIn("s4_perf_b1", item.reason)

    def test_balance_edges(self) -> None:
        # T10b-1: 블록이 덮지 않는 stage 의 예상 fail → 블록 항목 없음 + 대조 블록 없음 1 건
        uncovered = self.build(thresholds=self.expect(regress=True))
        found = self.balance(uncovered)
        self.assertEqual(
            [(i.ref, i.status) for i in found], [("(블록 없음)", "not_established")]
        )
        self.assertIn("균형 대조 블록 없음", found[0].reason)
        self.assertEqual(uncovered.expected_fail, 1)
        self.assertEqual(uncovered.exit_code, 1)
        # 등록만 되고 fail 이 없으면 항목을 만들지 않음. 예상 fail 규칙이 없는 입력도 같음
        passing = self.build(thresholds=self.expect(regress=True, limit=4.0))
        self.assertEqual(self.balance(passing), [])
        self.assertEqual(self.balance(self.build()), [])
        # regress 가 아니면 "대조 블록 없음" 은 만들지 않음. 대상 블록이 있으면 균형은 봄
        self.assertEqual(self.balance(self.build(thresholds=self.expect())), [])
        other = self.rtf_s4(0.255)
        other["scope"]["purposes"].remove("regress")
        found = self.balance(self.build(thresholds=other))
        self.assertEqual(
            [(i.ref, i.status) for i in found], [(helpers.TARGET_ID, "fail")]
        )

        # 덮인 stage 라도 블록이 그 지표(회차 pacing)를 판정하지 않으면 대조 블록 없음
        tail = helpers.clone(self.thresholds)
        helpers.set_rule(tail, "SPD.jitter", "S5", limit=4.0)
        rules = [r for r in tail["rules"] if r["metric"] == "SPD.tail_over_hop"]
        self.assertEqual([r["when"] for r in rules], [{}])
        rules[0].update(
            when={"stage": "S4"}, limit=0.5, expected_fail=helpers.EXPECTED_REASON
        )
        tail["rules"].append(
            {"metric": "SPD.tail_over_hop", "when": {"stage": "S5"}}
            | {"op": "<=", "limit": 1.0}
        )
        model = self.build(thresholds=tail)
        self.assertTrue(self.item(model, "SPD.tail_over_hop", "s4_rt").is_expected_fail)
        found = self.balance(model)
        self.assertEqual(
            [(i.metric, i.ref, i.status) for i in found],
            [("SPD.tail_over_hop", "(블록 없음)", "not_established")],
        )
        self.assertIn("S4·realtime", found[0].reason)
        self.assertEqual((model.overall, model.exit_code), ("not_established", 1))
        self.assertIn(
            "- not_established 지표: `SPD.tail_over_hop` 예상 fail 균형",
            render.render_report(model),
        )

        # T10b-2: 한쪽에만 규칙 항목이 있음
        thresholds = self.rtf_s4(0.2)
        helpers.set_rule(thresholds, "SPD.rtf_max", "S4")["when"]["class"] = "fp"
        lowp = helpers.clone(self.results)
        for n in (1, 2, 3):
            run = helpers.run_by_id(lowp, f"s4_perf_b{n}")
            run["effective"]["activation_quant"] = "int8"
        one_sided = self.build(lowp, thresholds=thresholds)
        item = self.item(one_sided, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertEqual(item.status, "not_established")
        self.assertIn("b 0건", item.reason)

        # T10b-3: 블록 구성 invalid
        short = helpers.clone(self.results)
        short["abba"][0]["pairs"].pop()
        broken = self.build(short, thresholds=self.rtf_s4(0.2))
        item = self.item(broken, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertEqual(item.status, "invalid")

        # T10b-5: balance 항목은 ABBA 필수 지표 누락 검사를 채우지 않음
        dropped = helpers.clone(self.results)
        dropped["abba"][0]["metrics"].remove("SPD.rtf_max")
        model = self.build(dropped, thresholds=self.rtf_s4(0.2))
        self.item(model, "SPD.rtf_max", helpers.TARGET_ID, kind="balance")
        self.assertIn("SPD.rtf_max @ ABBA", model.missing)

    # ------------------------------------------------------------ F2 대체 회차

    def superseded(self, **over: Any) -> Obj:
        results = helpers.clone(self.results)
        old = helpers.add_superseded(
            results, "s5_perf", "s5_perf_old", "2026-11-13T09:30:00+09:00"
        )
        old.update(over)
        return results

    def test_superseded_run_excluded(self) -> None:
        # T11·T11b: 원자료 파일이 없어도(읽지 않음) 리포트 생성
        base = self.build()
        model = self.build(self.superseded(timing="no_such_file.jsonl"))
        self.assertEqual([i for i in model.items if i.ref == "s5_perf_old"], [])
        self.assertEqual(model.counts, base.counts)
        self.assertEqual(model.exit_code, base.exit_code)
        info = [r for r in model.runs if r.run_id == "s5_perf_old"][0]
        self.assertEqual(info.superseded_by, "s5_perf")
        self.assertEqual(info.superseded_reason, "열 정지 재측정")
        # nonce 짝: 대체된 perf 는 1:1 계산에서 빠짐(같은 nonce 를 재측정이 이어 씀)
        sampler = [r for r in model.runs if r.run_id == "s5_sampler"][0]
        self.assertEqual(sampler.sampler_problems, ())
        text = render.render_report(model)
        self.assertIn("- 대체 회차 1 건(판정 제외)", text)
        self.assertIn(
            "| ok · 대체됨 → s5_perf(열 정지 재측정) · "
            "신원·열 검사 통과 회차 대체(원자료 품질 미검사) |",
            text,
        )
        self.assertNotIn("대체 회차", render.render_report(base))

        # 문제가 있는 회차를 대체: 회차 문제는 그대로 보이고 "유효 회차 대체" 표시는 없음
        bad = self.superseded()
        helpers.run_by_id(bad, "s5_perf_old")["identity"]["git_dirty"] = True
        bad_model = self.build(bad)
        self.assertEqual(bad_model.counts, base.counts)
        bad_text = render.render_report(bad_model)
        self.assertIn("| invalid · 대체됨 → s5_perf(열 정지 재측정) |", bad_text)
        self.assertIn("- 회차 `s5_perf_old` invalid: git_dirty", bad_text)
        self.assertNotIn("통과 회차 대체", bad_text)

    def test_superseded_not_baseline_nor_required(self) -> None:
        # T11: acc_baseline 후보·필수 지표 누락 검사에서 제외
        twin = helpers.clone(self.results)
        helpers.add_superseded(
            twin, "s1_acc_cuda", "s1_acc_cuda_old", "2026-11-11T09:30:00+09:00"
        )
        problems = schema.validate_results(
            twin, self.catalog, self.thresholds["scope"], None
        )
        self.assertEqual(problems, [])
        model = self.build(twin)
        self.assertEqual(model.counts, self.build().counts)
        self.assertEqual(self.item(model, "ACC.degradation", "s4_acc").status, "pass")

        gap = helpers.clone(self.results)
        helpers.add_superseded(gap, "s2_acc", "s2_acc_old", "2026-11-11T12:30:00+09:00")
        run = helpers.run_by_id(gap, "s2_acc")
        run["values"] = [v for v in run["values"] if v["metric"] != "CNV.audit_ok"]
        self.assertEqual(self.build(gap).missing, ["CNV.audit_ok @ S2"])

    # ------------------------------------------------------------ F3 잡음 블록

    def noise(self, b_rss_kb: int = 204800, **kw: Any) -> tuple[Obj, list[Obj]]:
        results = helpers.clone(self.results)
        runs = helpers.add_noise_block(results, b_rss_kb, **kw)
        return results, runs

    def rss(self, model: ReportModel, ref: str) -> Item:
        return self.item(model, "RES.rss_peak_mib", ref, kind="abba")

    def test_noise_block_two_sided(self) -> None:
        # T12: 중앙값 -3 %(허용 2 %) — 한쪽 판정이면 pass 였던 값
        results, _ = self.noise(198656)
        model = self.build(results)
        item = self.rss(model, helpers.NOISE_ID)
        self.assertEqual(item.value, -3.0)
        self.assertEqual(item.status, "fail")
        one_sided = helpers.clone(results)
        del one_sided["abba"][1]["noise_for"]
        self.assertEqual(
            self.rss(self.build(one_sided), helpers.NOISE_ID).status, "pass"
        )

    def test_noise_control_combination(self) -> None:
        # T13
        quiet, _ = self.noise()
        model = self.build(quiet)
        self.assertEqual(self.rss(model, helpers.NOISE_ID).status, "pass")
        self.assertEqual(self.rss(model, helpers.TARGET_ID).status, "pass")
        self.assertNotIn("잡음", self.rss(model, helpers.TARGET_ID).reason)
        # 잡음 블록에 그 지표가 없으면 대상 그대로 + 사유 병기
        other = self.item(model, "SPD.rtf_max", helpers.TARGET_ID, kind="abba")
        self.assertEqual(other.status, "pass")
        self.assertIn("잡음 대조 없음", other.reason)
        # 잡음 블록이 없는 입력의 사유는 그대로
        plain = self.item(self.build(), "SPD.rtf_max", helpers.TARGET_ID)
        self.assertEqual(plain.reason, "쌍별 열화 % 중앙값 <= 5")

        noisy, _ = self.noise(198656)
        model = self.build(noisy)
        target = self.rss(model, helpers.TARGET_ID)
        self.assertEqual(target.status, "not_established")
        self.assertIn(f"A ↔ A 잡음 대조 미통과({helpers.NOISE_ID} fail)", target.reason)
        self.assertEqual(target.value, 1.0)

        tight = helpers.clone(self.thresholds)
        tight["abba_limits_pct"]["RES.rss_peak_mib"] = 0.5
        model = self.build(noisy, thresholds=tight)
        self.assertEqual(self.rss(model, helpers.NOISE_ID).status, "fail")
        self.assertEqual(self.rss(model, helpers.TARGET_ID).status, "fail")

    def assert_noise_invalid(self, results: Obj, needle: str) -> None:
        model = self.build(results)
        self.assertIn(needle, "; ".join(model.abba_problems[helpers.NOISE_ID]))
        self.assertEqual(self.rss(model, helpers.NOISE_ID).status, "invalid")
        self.assertEqual(self.rss(model, helpers.TARGET_ID).status, "not_established")

    def test_noise_block_composition(self) -> None:
        # T14
        results, runs = self.noise()
        for run in runs:
            if run["run_id"].startswith("nz_b"):
                run["identity"]["git_sha"] = "9f3c2ab"
        self.assert_noise_invalid(results, "잡음 블록 안 git_sha 불일치")

        results, runs = self.noise()
        for run in runs:
            run["pacing"] = "realtime"
        self.assert_noise_invalid(results, "대상 블록과 pacing 불일치")

        # T14b
        results, runs = self.noise()
        for run in runs:
            run["stage"] = "S3"
        self.assert_noise_invalid(results, "대상 블록과 stage 불일치")

        results, runs = self.noise()
        for run in runs:
            run["identity"]["threads_effective"] = 2
        self.assert_noise_invalid(results, "대상 블록과 threads_effective 불일치")

        results, runs = self.noise()
        for run in runs:
            run["profile"] = "fp16-low-normal-t4"
        self.assert_noise_invalid(results, "대상 블록 a 쪽과 profile 불일치")

        results, runs = self.noise()
        for run in runs:
            run["identity"]["git_sha"] = "9f3c2ab"
        self.assert_noise_invalid(results, "대상 블록 a 쪽과 git_sha 불일치")

        # 리뷰 Low: A ↔ A 는 b 쪽 profile 도 a 쪽과 같아야 함
        results, runs = self.noise()
        for run in runs:
            if run["run_id"].startswith("nz_b"):
                run["profile"] = "fp16-low-normal-t4"
        self.assert_noise_invalid(results, "잡음 블록 안 profile 불일치")

    # ------------------------------------------------------------ F4 키 검사

    def pair_status(self, results: Obj, pair_id: str) -> tuple[str, str]:
        # base 쌍의 DEC.match_rate 는 기록 규칙이라 판정 지표(severe_flip)로 확인
        metric = "DEC.severe_flip" if pair_id.startswith("base") else "DEC.match_rate"
        item = self.item(self.build(results), metric, pair_id)
        return item.status, item.reason

    def test_pair_key_checks(self) -> None:
        # T15: manifest 는 모든 kind, threads 는 regress·S1 이 끼지 않은 chain
        manifest = helpers.clone(self.results)
        helpers.run_by_id(manifest, "s4_acc")["identity"]["manifest_sha256"] = "0" * 64
        for pair_id in ("chain_s3_s4", "base_s4", "regress_s4"):
            status, reason = self.pair_status(manifest, pair_id)
            self.assertEqual(status, "invalid", pair_id)
            self.assertIn("manifest_sha256 불일치", reason)
        self.assertEqual(self.pair_status(manifest, "chain_s2_s3")[0], "pass")

        threads = helpers.clone(self.results)
        helpers.run_by_id(threads, "s4_acc_old")["identity"]["threads_effective"] = 1
        status, reason = self.pair_status(threads, "regress_s4")
        self.assertEqual(status, "invalid")
        self.assertIn("threads_effective 불일치", reason)

        chain = helpers.clone(self.results)
        helpers.run_by_id(chain, "s3_acc")["identity"]["threads_effective"] = 1
        self.assertEqual(self.pair_status(chain, "chain_s2_s3")[0], "invalid")
        self.assertEqual(self.pair_status(chain, "chain_s3_s4")[0], "invalid")
        self.assertEqual(self.pair_status(chain, "base_s3")[0], "pass")

        s1 = helpers.clone(self.results)
        helpers.run_by_id(s1, "s1_golden_cpu")["identity"]["threads_effective"] = 1
        helpers.run_by_id(s1, "s1_acc_cuda")["identity"]["threads_effective"] = 1
        # chain_s1_s2 의 DEC.match_rate 는 기록 규칙 — invalid 로 바뀌지 않았는지만 확인
        self.assertEqual(self.pair_status(s1, "chain_s1_s2")[0], "record_only")
        self.assertEqual(self.build(s1).counts["invalid"], 0)
        self.assertEqual(self.pair_status(s1, "base_s2")[0], "pass")
        self.assertEqual(self.build(s1).counts, self.build().counts)

    def test_abba_threads_check(self) -> None:
        # T16
        results = helpers.clone(self.results)
        helpers.run_by_id(results, "s4_perf_b2")["identity"]["threads_effective"] = 2
        model = self.build(results)
        self.assertIn(
            "threads_effective 불일치",
            "; ".join(model.abba_problems[helpers.TARGET_ID]),
        )
        self.assertEqual(self.rss(model, helpers.TARGET_ID).status, "invalid")

    def test_abba_start_battery_min(self) -> None:
        # T17·T17b(예제 회차 시작 온도 = 33.2)
        def build(min_c: float, results: Obj | None = None) -> ReportModel:
            thresholds = helpers.clone(self.thresholds)
            thresholds["validity"]["abba_start_battery_min_c"] = min_c
            return self.build(results, thresholds=thresholds)

        self.assertEqual(self.build().abba_problems, {})
        cold = build(33.5)
        self.assertIn("< 하한 33.5", "; ".join(cold.abba_problems[helpers.TARGET_ID]))
        self.assertEqual(self.rss(cold, helpers.TARGET_ID).status, "invalid")
        # 블록 밖 회차는 하한을 보지 않음
        self.assertEqual(self.item(cold, "SPD.rtf_max", "s5_perf").status, "pass")
        edge = build(33.2)
        self.assertEqual(edge.abba_problems, {})
        self.assertEqual(self.rss(edge, helpers.TARGET_ID).status, "pass")
        bare = helpers.clone(self.results)
        del helpers.run_by_id(bare, "s4_perf_a2")["thermal"]
        got = build(33.2, bare).abba_problems[helpers.TARGET_ID]
        self.assertIn("s4_perf_a2: thermal 없음", "; ".join(got))

    # ------------------------------------------------------------ 렌더

    def test_render_expected_fail(self) -> None:
        # T18·T21
        thresholds = self.expect()
        helpers.set_rule(thresholds, "SPD.step_p95_over_hop", "S5", limit=0.5)
        text = render.render_report(self.build(thresholds=thresholds))
        self.assertIn("- 종합 판정: **fail** (종료 코드 1) — 예상 fail 1 건", text)
        self.assertIn("- 예상 밖 fail 지표: `SPD.step_p95_over_hop`", text)
        self.assertIn(
            f"- 예상 fail(사전 등록) `SPD.jitter` @ S5: {helpers.EXPECTED_REASON}", text
        )
        self.assertNotIn("- fail 지표:", text)
        self.assertIn("| fail(예상) |", text)
        self.assertIn("- 등록된 예상 fail 규칙: 1 건", text)
        self.assertIn(
            f"  - SPD.jitter [stage=S5]: {helpers.EXPECTED_REASON} — 덮은 항목 2, fail 1",
            text,
        )
        only = render.render_report(self.build(thresholds=self.expect()))
        self.assertIn(
            "- 종합 판정: **pass** (종료 코드 0) — 예상 fail 1 건을 pass 로 봄", only
        )
        self.assertNotIn("예상 밖 fail", only)
        # 등록이 없으면 줄도 없음(1.0.24 와 같은 출력)
        plain = render.render_report(self.build())
        self.assertNotIn("예상", plain)
        self.assertIn("- fail 지표: `SPD.jitter`", plain)

        checklist = render.render_checklist(self.catalog, thresholds)
        self.assertIn("## 등록된 예상 fail 규칙", checklist)
        self.assertIn(f"- SPD.jitter [stage=S5]: {helpers.EXPECTED_REASON}", checklist)
        self.assertNotIn("예상", render.render_checklist(self.catalog, self.thresholds))


if __name__ == "__main__":
    unittest.main()
