"""make_report CLI 테스트(계획서 §8 45~48)."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

import make_report
from port_metrics import schema
from tests import helpers

Obj = dict[str, Any]


def write_json(path: Path, obj: Obj) -> None:
    """JSON 파일 기록."""
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def copy_example(self) -> Path:
        dest = self.tmp / "example"
        shutil.copytree(helpers.EXAMPLE, dest, ignore=shutil.ignore_patterns("._*"))
        return dest

    def report_rc(self, base: Path, *extra: str) -> int:
        args = ["report", str(base / "results.json")]
        args += ["--thresholds", str(base / "thresholds.json")]
        args += ["-o", str(base / "report.md"), *extra]
        return make_report.main(args)

    def test_cli_report_rc(self) -> None:
        base = self.copy_example()
        self.assertEqual(self.report_rc(base), 1)
        text = (base / "report.md").read_text(encoding="utf-8")
        self.assertIn("SPD.jitter", text)

        # 판정 대상 0 건: S1 만·목적 없음·other 입력 → 필수 지표가 전부 기록 지표
        zero = self.tmp / "zero"
        zero.mkdir()
        rc = make_report.main(
            ["init-thresholds", "--stages", "S1", "--input-kind", "other"]
            + ["-o", str(zero / "thresholds.json")]
        )
        self.assertEqual(rc, 0)
        thresholds: Obj = json.loads((zero / "thresholds.json").read_text("utf-8"))
        thresholds["frozen_at"] = "2026-11-10T09:00:00+09:00"
        write_json(zero / "thresholds.json", thresholds)
        sha = hashlib.sha256((zero / "thresholds.json").read_bytes()).hexdigest()
        rows = [
            {"unit_id": f"u{i}", "wall_ms": 10.0, "kind": "steady", "paused": False}
            | {"units": 5}
            for i in range(4)
        ]
        (zero / "timing.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )
        results: Obj = {
            "schema": "port-metrics-results/1",
            "project": {
                "name": "zero",
                "task_metric": {"id": "F1", "unit": "%", "direction": "higher"},
            },
            "runs": [
                {
                    "run_id": "s1_perf",
                    "stage": "S1",
                    "backend": "cpu",
                    "run_kind": "perf",
                    "pacing": "max",
                    "profile": "fp32-high-normal-t4",
                    "effective": {
                        "weight_storage": "fp32",
                        "matmul_accum": "fp32",
                        "activation_quant": "none",
                    },
                    "started_at": "2026-11-11T10:00:00+09:00",
                    "identity": {
                        "git_sha": "abc",
                        "git_dirty": False,
                        "manifest_sha256": "m",
                        "threads_effective": 4,
                        "thresholds_sha256": sha,
                        "torch_version": "2.5.1",
                        "device_name": "cpu",
                        "tf32": False,
                        "checkpoint_sha256": "c",
                        "attn_impl": "eager",
                    },
                    "nonce": "n1",
                    "timing": "timing.jsonl",
                    "meta": {"rss_peak_kb": 1024},
                    "values": [{"metric": "ACC.primary", "value": 90.0}],
                }
            ],
        }
        write_json(zero / "results.json", results)
        model = make_report.load_model(
            zero / "results.json", zero / "thresholds.json", None
        )
        self.assertEqual(model.missing, [])
        judged = sum(n for s, n in model.counts.items() if s != "record_only")
        self.assertEqual(judged, 0)
        self.assertGreater(model.counts["record_only"], 0)
        self.assertEqual(self.report_rc(zero), 1)

    def test_cli_thresholds_tamper(self) -> None:
        base = self.copy_example()
        path = base / "thresholds.json"
        path.write_bytes(path.read_bytes() + b" ")
        model = make_report.load_model(base / "results.json", path, None)
        self.assertEqual(len(model.runs), 22)
        for run in model.runs:
            self.assertTrue(run.problems, run.run_id)
        measured = [i for i in model.items if i.kind != "missing"]
        self.assertTrue(measured)
        self.assertEqual({i.status for i in measured}, {"invalid"})
        self.assertEqual(self.report_rc(base), 1)

    def test_cli_schema_error_rc2(self) -> None:
        base = self.copy_example()
        good = (base / "results.json").read_text(encoding="utf-8")
        (base / "results.json").write_text(good[:-20], encoding="utf-8")
        self.assertEqual(self.report_rc(base), 2)
        (base / "results.json").write_text(
            good.replace('"schema"', '"x": NaN, "schema"', 1), encoding="utf-8"
        )
        self.assertEqual(self.report_rc(base), 2)
        obj: Obj = json.loads(good)
        del obj["runs"][0]["stage"]
        write_json(base / "results.json", obj)
        self.assertEqual(self.report_rc(base), 2)
        (base / "results.json").write_text(good, encoding="utf-8")
        self.assertEqual(self.report_rc(base, "--partial", "S9"), 2)
        self.assertEqual(self.report_rc(base), 1)

    def test_cli_init_and_checklist(self) -> None:
        out = self.tmp / "thresholds.json"
        rc = make_report.main(
            ["init-thresholds", "--stages", "S1,S2,S3,S4,S5"]
            + ["--purposes", "convert,regress,ship", "--model-types", "streaming"]
            + ["--input-kind", "audio", "-o", str(out)]
        )
        self.assertEqual(rc, 0)
        catalog = helpers.catalog()
        thresholds: Obj = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(schema.validate_thresholds(thresholds, catalog), [])
        self.assertIsNone(thresholds["frozen_at"])
        self.assertEqual(thresholds["validity"]["start_battery_max_c"], 34.0)
        checklist = self.tmp / "checklist.md"
        rc = make_report.main(
            ["checklist", "--thresholds", str(out), "-o", str(checklist)]
        )
        self.assertEqual(rc, 0)
        text = checklist.read_text(encoding="utf-8")
        required = catalog.required(thresholds["scope"], None).ids()
        self.assertGreater(len(required), 20)
        for metric_id in sorted(required):
            self.assertIn(f"`{metric_id}`", text)
        self.assertNotIn("SPD.units_per_sec", text)
        # convert 목적: S1-S2 NUM 판정 규칙(record 제외)마다 noise_floor 기입 요구
        self.assertEqual(text.count("noise_floor 기입(convert)"), 4)
        self.assertIn("`NUM.max_abs` [pair=S1-S2, class=fp]: noise_floor", text)
        self.assertNotIn("`NUM.max_abs` [pair=S2-S3]: noise_floor", text)


if __name__ == "__main__":
    unittest.main()
