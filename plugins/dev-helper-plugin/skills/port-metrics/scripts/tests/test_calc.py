"""calc 모듈 테스트(계획서 §8 1~16)."""

from __future__ import annotations

import unittest
from typing import Any

from port_metrics import calc


def row(wall_ms: float, kind: str = "steady", **extra: Any) -> dict[str, Any]:
    """timing 행 생성."""
    base: dict[str, Any] = {
        "unit_id": "u",
        "wall_ms": wall_ms,
        "kind": kind,
        "paused": False,
    }
    base.update(extra)
    return base


def sample(t_sec: float, cpu_ticks: int, **extra: Any) -> dict[str, Any]:
    """samples 행 생성."""
    base: dict[str, Any] = {
        "t_sec": t_sec,
        "cpu_ticks": cpu_ticks,
        "rss_kb": 1000,
        "paused": False,
    }
    base.update(extra)
    return base


class NearestRankTest(unittest.TestCase):
    def test_nearest_rank_basic(self) -> None:
        values = [float(v) for v in range(1, 11)]
        self.assertEqual(calc.nearest_rank(values, 0.5), 5.0)
        self.assertEqual(calc.nearest_rank(values, 0.9), 9.0)
        self.assertEqual(calc.nearest_rank(values, 0.99), 10.0)

    def test_nearest_rank_single(self) -> None:
        for q in (0.01, 0.5, 0.99, 1.0):
            self.assertEqual(calc.nearest_rank([7.0], q), 7.0)

    def test_nearest_rank_invalid(self) -> None:
        with self.assertRaises(ValueError):
            calc.nearest_rank([], 0.5)
        for q in (0.0, -0.1, 1.01):
            with self.assertRaises(ValueError):
                calc.nearest_rank([1.0], q)


class TimingTest(unittest.TestCase):
    def test_timing_rtf_sum_over_sum(self) -> None:
        rows = [row(1000, audio_sec=2.0), row(3000, audio_sec=4.0)]
        out = calc.timing_metrics(rows, "max", {})
        rtf = out["SPD.rtf_max"]
        assert rtf is not None
        self.assertAlmostEqual(rtf, 4.0 / 6.0, places=9)
        self.assertNotAlmostEqual(rtf, 0.625, places=3)

    def test_timing_excludes_warmup_paused(self) -> None:
        rows = [
            row(9000, "warmup", audio_sec=1.0),
            row(100, audio_sec=1.0),
            row(200, audio_sec=1.0),
            row(8000, audio_sec=1.0, paused=True),
        ]
        out = calc.timing_metrics(rows, "max", {})
        self.assertAlmostEqual(out["SPD.rtf_max"] or 0.0, 0.15, places=9)
        self.assertEqual(out["SPD.lat_max"], 200.0)
        self.assertEqual(out["SPD.lat_p50"], 100.0)
        self.assertEqual(out["MQ.excluded_rows"], 2.0)

    def test_timing_flush_rtf_only(self) -> None:
        rows = [
            row(100, audio_sec=1.0),
            row(100, audio_sec=1.0),
            row(900, "flush", audio_sec=1.0),
        ]
        out = calc.timing_metrics(rows, "max", {})
        self.assertAlmostEqual(out["SPD.rtf_max"] or 0.0, 1.1 / 3.0, places=9)
        self.assertEqual(out["SPD.lat_max"], 100.0)
        self.assertEqual(out["SPD.jitter"], 1.0)
        self.assertEqual(out["MQ.excluded_rows"], 1.0)

    def test_timing_units_per_sec(self) -> None:
        rows = [row(500, units=10), row(1500, units=30)]
        out = calc.timing_metrics(rows, "max", {})
        self.assertEqual(out["SPD.units_per_sec"], 20.0)
        self.assertIsNone(out["SPD.rtf_max"])

    def test_timing_rtf_name_by_pacing(self) -> None:
        rows = [row(900, audio_sec=1.0), row(1000, audio_sec=1.0)]
        fast = calc.timing_metrics(rows, "max", {})
        self.assertIn("SPD.rtf_max", fast)
        self.assertNotIn("SPD.rtf_rt", fast)
        self.assertNotIn("SPD.tail_over_hop", fast)
        meta = {"wall_total_sec": 2.05, "audio_total_sec": 2.0, "hop_ms": 100}
        paced = calc.timing_metrics(rows, "realtime", meta)
        self.assertNotIn("SPD.rtf_max", paced)
        self.assertAlmostEqual(paced["SPD.rtf_rt"] or 0.0, 0.95, places=9)
        self.assertAlmostEqual(paced["SPD.tail_over_hop"] or 0.0, 0.5, places=9)
        # 음수 꼬리(전체 wall < 오디오 길이)는 통과 값이 아니라 미측정
        short = dict(meta, wall_total_sec=1.9)
        negative = calc.timing_metrics(rows, "realtime", short)
        self.assertIsNone(negative["SPD.tail_over_hop"])
        level = calc.timing_metrics(rows, "realtime", dict(meta, wall_total_sec=2.0))
        self.assertEqual(level["SPD.tail_over_hop"], 0.0)
        with self.assertRaises(ValueError):
            calc.timing_metrics(rows, "paced", {})

    def test_timing_streaming_fields(self) -> None:
        rows = [row(float(v), deadline_miss=v >= 99) for v in range(1, 101)]
        out = calc.timing_metrics(rows, "max", {"hop_ms": 190})
        self.assertEqual(out["SPD.jitter"], 99.0 / 50.0)
        self.assertEqual(out["SPD.step_p95_over_hop"], 0.5)
        self.assertEqual(out["SPD.deadline_miss"], 2.0)
        no_field = calc.timing_metrics([row(1.0)], "max", {})
        self.assertIsNone(no_field["SPD.deadline_miss"])
        self.assertIsNone(no_field["SPD.step_p95_over_hop"])
        # 일부 행만 필드가 있으면 0 건이 아니라 미측정(None) — 누락 행의 초과를 0 으로 세지 않음
        partial = calc.timing_metrics(
            [row(1.0, deadline_miss=False), row(2.0)], "max", {}
        )
        self.assertIsNone(partial["SPD.deadline_miss"])

    def test_timing_llm_fields(self) -> None:
        rows = [
            row(10, prefill_ms=100, ttft_ms=150, gen_tokens=10, decode_ms=500),
            row(10, prefill_ms=300, ttft_ms=350, gen_tokens=30, decode_ms=1500),
            row(10, prefill_ms=200, ttft_ms=250, gen_tokens=20, decode_ms=1000),
        ]
        out = calc.timing_metrics(rows, "max", {})
        self.assertEqual(out["SPD.decode_tok_s"], 20.0)
        self.assertEqual(out["SPD.prefill_ms_p50"], 200.0)
        self.assertEqual(out["SPD.ttft_ms_p50"], 250.0)

    def test_timing_degenerate_none(self) -> None:
        warm = calc.timing_metrics([row(10, "warmup", audio_sec=1.0)], "max", {})
        for key in ("SPD.rtf_max", "SPD.lat_p50", "SPD.lat_p99", "SPD.jitter"):
            self.assertIsNone(warm[key], key)
        zero = calc.timing_metrics([row(10, audio_sec=0.0)], "max", {})
        self.assertIsNone(zero["SPD.rtf_max"])
        self.assertEqual(zero["SPD.lat_p50"], 10.0)
        empty = calc.timing_metrics([], "realtime", {"hop_ms": 0})
        self.assertIsNone(empty["SPD.rtf_rt"])
        self.assertIsNone(empty["SPD.tail_over_hop"])

    def test_window_stats(self) -> None:
        rows = [row(10.0 + i, t_start_sec=float(i)) for i in range(4)]
        rows += [row(20.0 + i, t_start_sec=10.0 + i) for i in range(4)]
        stats = calc.window_stats(rows, 10.0)
        assert stats is not None
        self.assertEqual(stats[0], 23.0 / 13.0)
        self.assertAlmostEqual(stats[1] or 0.0, 21.5 / 11.5 - 1.0, places=9)
        self.assertIsNone(calc.window_stats(rows[:4], 10.0))
        self.assertIsNone(calc.window_stats([row(1.0)], 10.0))


class SamplerTest(unittest.TestCase):
    def test_sampler_cpu_pct(self) -> None:
        samples = [
            sample(0.0, 0),
            sample(1.0, 100),
            sample(2.0, 600, paused=True),
            sample(3.0, 1100),
            sample(4.0, 1300),
        ]
        out = calc.sampler_metrics(samples, {"clk_tck": 100})
        self.assertEqual(out["RES.cpu_pct_mean"], 150.0)
        self.assertEqual(out["RES.cpu_pct_max"], 200.0)
        one = calc.sampler_metrics(samples[:2], {"clk_tck": 100})
        self.assertEqual(one["RES.cpu_pct_mean"], 100.0)
        self.assertIsNone(calc.sampler_metrics(samples, {})["RES.cpu_pct_mean"])

    def test_sampler_cpu_s_per_unit_and_mib(self) -> None:
        samples = [sample(float(i), i * 200, pss_kb=1024 * (i + 1)) for i in range(20)]
        samples.append(sample(20.0, 4000, pss_kb=999999, paused=True))
        meta = {"clk_tck": 100, "work_amount": 20}
        out = calc.sampler_metrics(samples, meta)
        self.assertEqual(out["RES.cpu_s_per_unit"], 2.0)
        self.assertEqual(out["RES.pss_p95_mib"], 19.0)
        self.assertEqual(out["RES.pss_mean_mib"], 10.5)
        flat = calc.sampler_metrics([sample(0.0, 0, pss_kb=1024)], {})
        self.assertEqual(flat["RES.pss_mean_mib"], 1.0)
        self.assertIsNone(flat["RES.cpu_s_per_unit"])

    def test_sampler_quality(self) -> None:
        samples = [sample(0.0, 0), sample(3.0, 1), sample(9.0, 2), sample(12.0, 3)]
        out = calc.sampler_metrics(samples, {"sample_interval_sec": 3.0})
        self.assertEqual(out["MQ.sampler_n"], 4.0)
        self.assertEqual(out["MQ.sampler_gap_ratio"], 2.0)
        self.assertIsNone(calc.sampler_metrics(samples, {})["MQ.sampler_gap_ratio"])


class WorseningTest(unittest.TestCase):
    def test_worsening_pct_direction(self) -> None:
        self.assertAlmostEqual(
            calc.worsening_pct(100.0, 105.0, "lower") or 0.0, 5.0, places=9
        )
        self.assertAlmostEqual(
            calc.worsening_pct(100.0, 95.0, "higher") or 0.0, 5.0, places=9
        )
        self.assertIsNone(calc.worsening_pct(0.0, 1.0, "lower"))
        with self.assertRaises(ValueError):
            calc.worsening_pct(1.0, 2.0, "none")


if __name__ == "__main__":
    unittest.main()
