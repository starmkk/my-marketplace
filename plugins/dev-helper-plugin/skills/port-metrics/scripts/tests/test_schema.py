"""schema 모듈 테스트(계획서 §8 17~27)."""

from __future__ import annotations

import unittest
from typing import Any

from port_metrics import schema
from tests import helpers

Obj = dict[str, Any]


def mini_run(run_id: str, run_kind: str, nonce: str, **extra: Any) -> Obj:
    """cross_problems 용 최소 회차."""
    run: Obj = {
        "run_id": run_id,
        "stage": "S4",
        "backend": "cpu",
        "run_kind": run_kind,
        "profile": "fp16-high-normal-t4",
        "nonce": nonce,
        "started_at": "2026-11-11T10:00:00+09:00",
        "identity": {"git_sha": "abc", "manifest_sha256": "m"},
    }
    run.update(extra)
    return run


class SchemaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = helpers.catalog()
        self.results, self.thresholds, self.sha = helpers.example()
        self.scope = self.thresholds["scope"]

    def errors(self, results: Obj, scope: Obj | None = None) -> list[str]:
        return schema.validate_results(results, self.catalog, scope or self.scope, None)

    def assert_one(self, errors: list[str], needle: str) -> None:
        self.assertTrue(any(needle in e for e in errors), (needle, errors))

    def test_parse_json_rejects_nan(self) -> None:
        for text in ('{"v": NaN}', '{"v": Infinity}', '{"v": -Infinity}', "{"):
            with self.assertRaises(schema.FormatError):
                schema.parse_json(text)
        self.assertEqual(schema.parse_json('{"v": 1.5}'), {"v": 1.5})

    def test_validate_results_example_ok(self) -> None:
        self.assertEqual(self.errors(self.results), [])
        self.assertEqual(schema.validate_thresholds(self.thresholds, self.catalog), [])

    def test_validate_results_format_errors(self) -> None:
        missing = helpers.clone(self.results)
        del missing["runs"][0]["backend"]
        self.assert_one(self.errors(missing), "runs[0].backend")

        paced = helpers.clone(self.results)
        helpers.run_by_id(paced, "s4_perf_b1")["pacing"] = "paced"
        self.assert_one(self.errors(paced), "pacing")

        chain = helpers.clone(self.results)
        helpers.by_id(chain["pairs"], "pair_id", "chain_s1_s2")["target"] = "s3_acc"
        self.assert_one(self.errors(chain), "인접")

        dup = helpers.clone(self.results)
        dup["runs"][1]["run_id"] = dup["runs"][0]["run_id"]
        self.assert_one(self.errors(dup), "중복")

        narrow = dict(self.scope, stages=["S1", "S2", "S3", "S4"])
        self.assert_one(self.errors(self.results, narrow), "scope")

        unknown = helpers.clone(self.results)
        unknown["abba"][0]["pairs"][0]["a"] = "no_such_run"
        self.assert_one(self.errors(unknown), "no_such_run")

        kind = helpers.clone(self.results)
        helpers.run_by_id(kind, "s4_acc")["timing"] = "timing_s4_b1.jsonl"
        self.assert_one(self.errors(kind), "timing")

    def test_value_type_strict(self) -> None:
        flag = helpers.clone(self.results)
        values = helpers.run_by_id(flag, "s2_acc")["values"]
        helpers.by_id(values, "metric", "CNV.audit_ok")["value"] = 1
        self.assert_one(self.errors(flag), "CNV.audit_ok")

        count = helpers.clone(self.results)
        pair = helpers.by_id(count["pairs"], "pair_id", "base_s4")
        helpers.by_id(pair["values"], "metric", "DEC.flip")["value"] = False
        self.assert_one(self.errors(count), "DEC.flip")

        real = helpers.clone(self.results)
        pair = helpers.by_id(real["pairs"], "pair_id", "base_s4")
        helpers.by_id(pair["values"], "metric", "DEC.flip")["value"] = 1.0
        self.assert_one(self.errors(real), "DEC.flip")

    def test_generator_metric_in_values_rejected(self) -> None:
        bad = helpers.clone(self.results)
        helpers.run_by_id(bad, "s4_perf_b1")["values"].append(
            {"metric": "SPD.rtf_max", "value": 0.3}
        )
        self.assert_one(self.errors(bad), "SPD.rtf_max")
        unknown = helpers.clone(self.results)
        helpers.run_by_id(unknown, "s4_perf_b1")["values"].append(
            {"metric": "SPD.nope", "value": 0.3}
        )
        self.assert_one(self.errors(unknown), "SPD.nope")

    def test_validate_thresholds_overlap(self) -> None:
        def problems(th: Obj) -> list[str]:
            return schema.validate_thresholds(th, self.catalog)

        dup = helpers.clone(self.thresholds)
        dup["rules"].append(
            {"metric": "SPD.jitter", "when": {}, "op": "<=", "limit": 9.0}
        )
        self.assert_one(problems(dup), "겹침")

        named = helpers.clone(self.thresholds)
        named["rules"].append(
            {
                "metric": "ACC.degradation",
                "when": {"subset": "noisy"},
                "op": "<=",
                "limit": 9.0,
            }
        )
        self.assert_one(problems(named), "겹침")

        swapped = helpers.clone(self.thresholds)
        for rule in swapped["rules"]:
            if rule["metric"] == "ACC.degradation" and rule["when"] == {
                "subset": "each"
            }:
                rule["when"] = {"subset": "noisy"}
        self.assertEqual(problems(swapped), [])

        # 기록 지표(judged=false)에 판정 규칙을 쓰면 무시되지 않고 형식 오류
        unjudged = helpers.clone(self.thresholds)
        lat_rule: Obj = {"metric": "SPD.lat_p50", "when": {}, "op": "<=", "limit": 50.0}
        unjudged["rules"].append(lat_rule)
        self.assert_one(problems(unjudged), "record")
        lat_rule.update({"op": "record", "limit": None})
        self.assertEqual(problems(unjudged), [])

    def test_run_problems_identity(self) -> None:
        def problems(run: Obj, thresholds: Obj | None = None) -> list[str]:
            return schema.run_problems(run, thresholds or self.thresholds, self.sha)

        base = helpers.run_by_id(self.results, "s5_perf")
        self.assertEqual(problems(base), [])

        no_cpuset = helpers.clone(base)
        del no_cpuset["identity"]["cpuset"]
        got = problems(no_cpuset)
        self.assertEqual(len(got), 1)
        self.assertIn("cpuset", got[0])

        for blank in ("", "   "):
            empty = helpers.clone(base)
            empty["identity"]["proc_state"] = blank
            got = problems(empty)
            self.assertEqual(len(got), 1, got)
            self.assertIn("proc_state", got[0])

        dirty = helpers.clone(base)
        dirty["identity"]["git_dirty"] = True
        self.assertEqual(len(problems(dirty)), 1)

        sha = helpers.clone(base)
        sha["identity"]["thresholds_sha256"] = "0" * 64
        self.assertEqual(len(problems(sha)), 1)

        early = helpers.clone(base)
        early["started_at"] = "2026-11-01T00:00:00+09:00"
        self.assertEqual(len(problems(early)), 1)

        unfrozen = dict(self.thresholds, frozen_at=None)
        self.assertEqual(problems(early, unfrozen), [])

    def test_run_problems_thermal(self) -> None:
        base = helpers.run_by_id(self.results, "s4_perf_b1")
        cases: list[tuple[str, Any]] = [
            ("start_battery_c", 34.5),
            ("clock_restored", False),
            ("wait_sec", 601),
        ]
        for key, value in cases:
            run = helpers.clone(base)
            run["thermal"][key] = value
            got = schema.run_problems(run, self.thresholds, self.sha)
            self.assertEqual(len(got), 1, (key, got))
        edge = helpers.clone(base)
        edge["thermal"].update({"start_battery_c": 34.0, "wait_sec": 600})
        self.assertEqual(schema.run_problems(edge, self.thresholds, self.sha), [])

    def test_cross_sampler_pairing(self) -> None:
        validity = self.thresholds["validity"]
        runs = [
            mini_run("p_ok", "perf", "n1"),
            mini_run("s_ok", "sampler", "n1"),
            mini_run("s_alone", "sampler", "n2"),
            mini_run("p_prof", "perf", "n3", profile="w8a-low-normal-t4"),
            mini_run("s_prof", "sampler", "n3"),
            mini_run("p_multi", "perf", "n4"),
            mini_run("s_multi_1", "sampler", "n4"),
            mini_run("s_multi_2", "sampler", "n4"),
        ]
        got = schema.cross_problems({"runs": runs}, validity)
        self.assertEqual(
            set(got.sampler), {"s_alone", "s_prof", "s_multi_1", "s_multi_2"}
        )
        self.assertTrue(any("profile" in p for p in got.sampler["s_prof"]))
        sha_runs = [
            mini_run("p_sha", "perf", "n5"),
            mini_run("s_sha", "sampler", "n5", identity={"git_sha": "other"}),
        ]
        sha = schema.cross_problems({"runs": sha_runs}, validity)
        self.assertEqual(set(sha.sampler), {"s_sha"})
        self.assertTrue(any("git_sha" in p for p in sha.sampler["s_sha"]))
        self.assertEqual(len(schema.sampler_quality_problems(99, 1.0, validity)), 1)
        self.assertEqual(len(schema.sampler_quality_problems(100, 2.5, validity)), 1)
        self.assertEqual(len(schema.sampler_quality_problems(100, None, validity)), 1)
        self.assertEqual(len(schema.sampler_quality_problems(50, 3.0, validity)), 2)
        self.assertEqual(schema.sampler_quality_problems(100, 2.0, validity), [])
        self.assertEqual(
            schema.cross_problems(self.results, validity).sampler, {}, "예제는 정상"
        )

    def test_cross_abba_composition(self) -> None:
        validity = self.thresholds["validity"]
        self.assertEqual(schema.cross_problems(self.results, validity).abba, {})

        two = helpers.clone(self.results)
        two["abba"][0]["pairs"].pop()
        self.assertIn("abba_s4_patch", schema.cross_problems(two, validity).abba)

        one_order = helpers.clone(self.results)
        pairs = one_order["abba"][0]["pairs"]
        for pair in pairs:
            a = helpers.run_by_id(one_order, pair["a"])
            b = helpers.run_by_id(one_order, pair["b"])
            if a["started_at"] > b["started_at"]:
                a["started_at"], b["started_at"] = b["started_at"], a["started_at"]
        self.assertIn("abba_s4_patch", schema.cross_problems(one_order, validity).abba)

        stage = helpers.clone(self.results)
        stage["abba"][0]["pairs"][0]["b"] = "s5_perf"
        self.assertIn("abba_s4_patch", schema.cross_problems(stage, validity).abba)

        def reasons(results: Obj) -> str:
            got = schema.cross_problems(results, validity).abba
            return "; ".join(got.get("abba_s4_patch", []))

        pacing = helpers.clone(self.results)
        helpers.run_by_id(pacing, "s4_perf_b2")["pacing"] = "realtime"
        self.assertIn("pacing", reasons(pacing))

        mixed = helpers.clone(self.results)
        helpers.run_by_id(mixed, "s4_perf_a2")["identity"]["git_sha"] = "9f3c2ab"
        self.assertIn("a 쪽 회차끼리 git_sha", reasons(mixed))
        self.assertNotIn("b 쪽", reasons(mixed))

        profile = helpers.clone(self.results)
        helpers.run_by_id(profile, "s4_perf_b3")["profile"] = "w8a-low-normal-t4"
        self.assertIn("b 쪽 회차끼리 profile", reasons(profile))

        kind = helpers.clone(self.results)
        kind["abba"][0]["pairs"][2] = {"a": "s4_perf_a3", "b": "s4_sampler"}
        self.assertIn("run_kind", reasons(kind))

        twice = helpers.clone(self.results)
        twice["abba"][0]["pairs"][2] = {"a": "s4_perf_a1", "b": "s4_perf_b3"}
        self.assertIn("여러 번", reasons(twice))

        same_time = helpers.clone(self.results)
        a1 = helpers.run_by_id(same_time, "s4_perf_a1")
        helpers.run_by_id(same_time, "s4_perf_b1")["started_at"] = a1["started_at"]
        self.assertIn("순서", reasons(same_time))

    def test_acc_baseline_ambiguous(self) -> None:
        two = helpers.clone(self.results)
        helpers.run_by_id(two, "s1_golden_cpu")["values"] = [
            {"metric": "ACC.primary", "value": 5.0}
        ]
        self.assert_one(self.errors(two), "acc_baseline")
        helpers.run_by_id(two, "s1_acc_cuda")["acc_baseline"] = True
        self.assertEqual(self.errors(two), [])
        helpers.run_by_id(two, "s1_golden_cpu")["acc_baseline"] = True
        self.assert_one(self.errors(two), "acc_baseline")


if __name__ == "__main__":
    unittest.main()
