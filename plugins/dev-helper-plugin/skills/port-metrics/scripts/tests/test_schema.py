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

    # ------------------------------------------------ 1.0.25(계획 §4·§7.2 T1~T5)

    def th_problems(self, thresholds: Obj) -> list[str]:
        return schema.validate_thresholds(thresholds, self.catalog)

    def test_expected_fail_format(self) -> None:
        # T1
        ok = helpers.expect_fail(self.thresholds, "SPD.jitter", "S5", regress=True)
        self.assertEqual(self.th_problems(ok), [])
        for bad in ("", 3):
            th = helpers.clone(self.thresholds)
            helpers.set_rule(th, "SPD.jitter", "S5", expected_fail=bad)
            self.assert_one(self.th_problems(th), "expected_fail")
        record = helpers.clone(self.thresholds)
        helpers.set_rule(record, "SPD.jitter", "S3", expected_fail="사유")
        self.assert_one(self.th_problems(record), "op=record 규칙에는 expected_fail")

    def test_expected_fail_scope_limit(self) -> None:
        # T1b: 목적의 핵심 판정(ACC·DEC·NUM·STB·CNV·pair)은 예상 fail 로 덮지 못함
        no_stage = helpers.clone(self.thresholds)
        for rule in no_stage["rules"]:
            if rule["metric"] == "SPD.tail_over_hop":
                rule["expected_fail"] = "사유"
        self.assert_one(self.th_problems(no_stage), "when.stage 가 있는 규칙만")
        seen: set[str] = set()
        for category in ("NUM", "DEC", "ACC", "STB", "CNV"):
            th = helpers.clone(self.thresholds)
            for rule in th["rules"]:
                spec = self.catalog.get(rule["metric"])
                if spec.category == category and rule["op"] != "record":
                    rule["expected_fail"] = "사유"
                    seen.add(spec.scope)
                    break
            else:
                self.fail(category)
            self.assert_one(self.th_problems(th), "SPD·RES·PWR·THM")
        self.assertEqual(seen, {"run", "pair"})

    def test_validity_optional_keys(self) -> None:
        # T5·T5b
        def with_validity(**extra: Any) -> list[str]:
            th = helpers.clone(self.thresholds)
            th["validity"].update(extra)
            return self.th_problems(th)

        self.assertEqual(with_validity(abba_start_battery_min_c=30.0), [])
        self.assertEqual(with_validity(abba_start_battery_min_c=34.0), [])
        for bad in ("30", True, None):
            self.assert_one(
                with_validity(abba_start_battery_min_c=bad), "abba_start_battery_min_c"
            )
        self.assert_one(with_validity(start_battery_min_c=30.0), "미지 키")
        self.assert_one(
            with_validity(abba_start_battery_min_c=34.5), "start_battery_max_c 이하"
        )

    def test_superseded_format(self) -> None:
        # T2
        def base() -> tuple[Obj, Obj]:
            results = helpers.clone(self.results)
            old = helpers.add_superseded(
                results, "s5_perf", "s5_perf_old", "2026-11-13T09:30:00+09:00"
            )
            return results, old

        results, old = base()
        self.assertEqual(self.errors(results), [])
        self.assertTrue(schema.is_superseded(old))
        active = schema.active_runs(results["runs"])
        self.assertEqual(len(active), len(results["runs"]) - 1)
        self.assertNotIn("s5_perf_old", [r["run_id"] for r in active])

        results, old = base()
        old["superseded_by"] = "no_such_run"
        self.assert_one(self.errors(results), "미지 run 참조")

        results, old = base()
        old["superseded_by"] = "s5_perf_old"
        self.assert_one(self.errors(results), "자기 참조")

        results, old = base()
        new = helpers.run_by_id(results, "s5_perf")
        new.update(superseded_by="s5_perf_old", superseded_reason="되돌림")
        self.assert_one(self.errors(results), "순환")

        results, old = base()
        old["superseded_by"] = "s4_perf_b1"
        self.assert_one(self.errors(results), "stage 다름")

        for key in ("superseded_by", "superseded_reason"):
            results, old = base()
            del old[key]
            self.assert_one(self.errors(results), "함께 있어야 함")
        results, old = base()
        old["superseded_reason"] = ""
        self.assert_one(self.errors(results), "superseded_reason")

    def test_superseded_role(self) -> None:
        # T2b: 같은 역할의 재측정만 대체로 인정
        def errors_with(change: Any) -> list[str]:
            results = helpers.clone(self.results)
            old = helpers.add_superseded(
                results, "s5_perf", "s5_perf_old", "2026-11-13T09:30:00+09:00"
            )
            change(old)
            return self.errors(results)

        def later(old: Obj) -> None:
            old["started_at"] = "2026-11-13T10:30:00+09:00"

        def manifest(old: Obj) -> None:
            old["identity"]["manifest_sha256"] = "0" * 64

        def pacing(old: Obj) -> None:
            old["pacing"] = "realtime"

        def git_sha(old: Obj) -> None:
            old["identity"]["git_sha"] = "41d7e05"

        self.assert_one(errors_with(later), "started_at 이 더 늦어야 함")
        self.assert_one(errors_with(manifest), "manifest_sha256 다름")
        self.assert_one(errors_with(pacing), "pacing 다름")
        self.assert_one(errors_with(git_sha), "git_sha 다름")

    def test_superseded_references(self) -> None:
        # T3: pairs·abba 참조 = 형식 문제, sampler 결속 참조 = sampler invalid(형식 문제 아님)
        pair = helpers.clone(self.results)
        helpers.add_superseded(
            pair, "s3_acc", "s3_acc_old", "2026-11-11T13:50:00+09:00"
        )
        helpers.by_id(pair["pairs"], "pair_id", "chain_s2_s3")["target"] = "s3_acc_old"
        self.assert_one(self.errors(pair), "대체된 회차 참조")

        abba = helpers.clone(self.results)
        helpers.add_superseded(
            abba, "s4_perf_a1", "s4_perf_a1_old", "2026-11-12T09:50:00+09:00"
        )
        abba["abba"][0]["pairs"][0]["a"] = "s4_perf_a1_old"
        self.assert_one(self.errors(abba), "대체된 회차 참조")

        bound = helpers.clone(self.results)
        helpers.add_superseded(
            bound, "s5_perf", "s5_perf_old", "2026-11-13T09:30:00+09:00"
        )
        helpers.run_by_id(bound, "s5_perf")["nonce"] = "n-s5-rerun"
        self.assertEqual(self.errors(bound), [])
        got = schema.cross_problems(bound, self.thresholds["validity"]).sampler
        self.assertEqual(set(got), {"s5_sampler"})
        self.assertIn("perf 짝 s5_perf_old 는 대체됨", "; ".join(got["s5_sampler"]))

    def test_noise_for_format(self) -> None:
        # T4·T4b
        def base(metrics: tuple[str, ...] = ("RES.rss_peak_mib",)) -> Obj:
            results = helpers.clone(self.results)
            helpers.add_noise_block(results, metrics=metrics)
            return results

        self.assertEqual(self.errors(base()), [])

        unknown = base()
        unknown["abba"][1]["noise_for"] = "no_such_block"
        self.assert_one(self.errors(unknown), "미지 블록")

        own = base()
        own["abba"][1]["noise_for"] = helpers.NOISE_ID
        self.assert_one(self.errors(own), "자기 참조")

        chained = base()
        chained["abba"][0]["noise_for"] = helpers.NOISE_ID
        self.assert_one(self.errors(chained), "잡음 블록을 가리킴")

        extra = base(("RES.rss_peak_mib", "SPD.lat_p50"))
        self.assert_one(self.errors(extra), "대상 블록 metrics 에 없음")


if __name__ == "__main__":
    unittest.main()
