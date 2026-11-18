"""원자료 행 → 지표 값 계산(순수 함수, 파일 I/O 없음)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

Row = Mapping[str, Any]


def nearest_rank(values: Sequence[float], q: float) -> float:
    """nearest-rank 분위수: k = ceil(q·n), 보간 없음."""
    if not values:
        raise ValueError("nearest_rank: 빈 입력")
    if not 0.0 < q <= 1.0:
        raise ValueError(f"nearest_rank: q={q} 는 (0, 1] 범위여야 함")
    ordered = sorted(values)
    # 부동소수 곱 오차(0.07 × 100 = 7.000000000000001)로 한 칸 밀리는 것을 막음
    k = max(1, math.ceil(q * len(ordered) - 1e-9))
    return float(ordered[k - 1])


def median(values: Sequence[float]) -> float:
    """중앙값(짝수 개면 가운데 두 값의 평균)."""
    if not values:
        raise ValueError("median: 빈 입력")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def worsening_pct(a: float, b: float, direction: str) -> float | None:
    """a 대비 b 의 열화 %(양수 = 나빠짐). a = 0 이면 None."""
    if direction not in ("lower", "higher"):
        raise ValueError(f"worsening_pct: direction={direction!r} 위반")
    if a == 0:
        return None
    if direction == "lower":
        return (b - a) / a * 100.0
    return (a - b) / a * 100.0


def _num(meta: Mapping[str, Any], key: str) -> float | None:
    value = meta.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _field_values(rows: Sequence[Row], key: str) -> list[float]:
    return [float(r[key]) for r in rows if r.get(key) is not None]


def _ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den == 0:
        return None
    return num / den


def window_stats(
    rows: Sequence[Row], window_sec: float
) -> tuple[float | None, float | None] | None:
    """soak 창 통계: (마지막 창 p99 ÷ 첫 창 p99, 마지막 창 중앙값 ÷ 첫 창 중앙값 − 1).

    kind=steady·paused=false·t_start_sec 있는 행만 사용. 창이 2 개 미만이면 None.
    """
    if window_sec <= 0:
        raise ValueError("window_stats: window_sec 는 양수여야 함")
    used = [
        r
        for r in rows
        if r.get("kind") == "steady"
        and not r.get("paused")
        and r.get("t_start_sec") is not None
    ]
    if not used:
        return None
    origin = min(float(r["t_start_sec"]) for r in used)
    windows: dict[int, list[float]] = {}
    for r in used:
        index = int((float(r["t_start_sec"]) - origin) // window_sec)
        windows.setdefault(index, []).append(float(r["wall_ms"]))
    if len(windows) < 2:
        return None
    first = windows[min(windows)]
    last = windows[max(windows)]
    p99_ratio = _ratio(nearest_rank(last, 0.99), nearest_rank(first, 0.99))
    med_ratio = _ratio(median(last), median(first))
    drift = None if med_ratio is None else med_ratio - 1.0
    return p99_ratio, drift


def timing_metrics(
    rows: Sequence[Row], pacing: str, meta: Mapping[str, Any]
) -> dict[str, float | None]:
    """timing.jsonl 행 → 시간 지표(키 = 카탈로그 지표 id, 계산 불가 = None).

    RTF·처리량 = kind≠warmup ∧ ¬paused 의 Σ/Σ, 지연 분위수 = kind=steady ∧ ¬paused.
    """
    if pacing not in ("max", "realtime"):
        raise ValueError(f"timing_metrics: pacing={pacing!r} 위반")
    agg = [r for r in rows if r.get("kind") != "warmup" and not r.get("paused")]
    steady = [r for r in agg if r.get("kind") == "steady"]
    out: dict[str, float | None] = {}

    wall_sec = sum(float(r["wall_ms"]) for r in agg) / 1000.0
    audio_sec = sum(_field_values(agg, "audio_sec"))
    rtf_id = "SPD.rtf_max" if pacing == "max" else "SPD.rtf_rt"
    out[rtf_id] = _ratio(wall_sec, audio_sec) if agg else None
    units = _field_values(agg, "units")
    out["SPD.units_per_sec"] = _ratio(sum(units), wall_sec) if units else None

    lat = [float(r["wall_ms"]) for r in steady]
    p50 = nearest_rank(lat, 0.5) if lat else None
    p95 = nearest_rank(lat, 0.95) if lat else None
    p99 = nearest_rank(lat, 0.99) if lat else None
    out["SPD.lat_p50"] = p50
    out["SPD.lat_p95"] = p95
    out["SPD.lat_p99"] = p99
    out["SPD.lat_max"] = max(lat) if lat else None
    out["SPD.jitter"] = _ratio(p99, p50)
    hop_ms = _num(meta, "hop_ms")
    out["SPD.step_p95_over_hop"] = _ratio(p95, hop_ms)
    if pacing == "realtime":
        wall_total = _num(meta, "wall_total_sec")
        audio_total = _num(meta, "audio_total_sec")
        tail_ms = None
        if wall_total is not None and audio_total is not None:
            tail_ms = (wall_total - audio_total) * 1000.0
        # 음수 꼬리(전체 wall < 오디오 길이)는 계측 오류 — 통과 값으로 쓰지 않음
        if tail_ms is not None and tail_ms < 0:
            tail_ms = None
        out["SPD.tail_over_hop"] = _ratio(tail_ms, hop_ms)
    # deadline_miss 필드가 없는 행이 있으면 0 건으로 세지 않고 미측정으로 둠
    if agg and all(isinstance(r.get("deadline_miss"), bool) for r in agg):
        out["SPD.deadline_miss"] = float(sum(1 for r in agg if r["deadline_miss"]))
    else:
        out["SPD.deadline_miss"] = None

    prefill = _field_values(agg, "prefill_ms")
    ttft = _field_values(agg, "ttft_ms")
    out["SPD.prefill_ms_p50"] = nearest_rank(prefill, 0.5) if prefill else None
    out["SPD.ttft_ms_p50"] = nearest_rank(ttft, 0.5) if ttft else None
    dec_rows = [
        r
        for r in agg
        if r.get("gen_tokens") is not None and r.get("decode_ms") is not None
    ]
    tok_per_ms = _ratio(
        sum(float(r["gen_tokens"]) for r in dec_rows),
        sum(float(r["decode_ms"]) for r in dec_rows),
    )
    out["SPD.decode_tok_s"] = (
        tok_per_ms * 1000.0 if tok_per_ms is not None and dec_rows else None
    )

    out["MQ.excluded_rows"] = float(len(rows) - len(steady))
    rss_peak_kb = _num(meta, "rss_peak_kb")
    out["RES.rss_peak_mib"] = None if rss_peak_kb is None else rss_peak_kb / 1024.0

    window_sec = _num(meta, "window_sec")
    stats = None if window_sec is None else window_stats(rows, window_sec)
    out["STB.soak_p99_ratio"] = None if stats is None else stats[0]
    out["THM.drift"] = None if stats is None else stats[1]
    return out


def sampler_metrics(
    samples: Sequence[Row], meta: Mapping[str, Any]
) -> dict[str, float | None]:
    """samples.jsonl 행 → 자원 지표(키 = 카탈로그 지표 id, 계산 불가 = None)."""
    out: dict[str, float | None] = {"MQ.sampler_n": float(len(samples))}
    gaps = [float(b["t_sec"]) - float(a["t_sec"]) for a, b in zip(samples, samples[1:])]
    interval = _num(meta, "sample_interval_sec")
    out["MQ.sampler_gap_ratio"] = _ratio(max(gaps), interval) if gaps else None

    clk_tck = _num(meta, "clk_tck")
    pcts: list[float] = []
    cpu_sec_sum = 0.0
    dt_sum = 0.0
    if clk_tck is not None and clk_tck > 0:
        for a, b in zip(samples, samples[1:]):
            dt = float(b["t_sec"]) - float(a["t_sec"])
            if a.get("paused") or b.get("paused") or dt <= 0:
                continue
            cpu_sec = (float(b["cpu_ticks"]) - float(a["cpu_ticks"])) / clk_tck
            pcts.append(cpu_sec / dt * 100.0)
            cpu_sec_sum += cpu_sec
            dt_sum += dt
    out["RES.cpu_pct_mean"] = cpu_sec_sum / dt_sum * 100.0 if pcts else None
    out["RES.cpu_pct_max"] = max(pcts) if pcts else None

    total_cpu_sec = None
    if clk_tck is not None and clk_tck > 0 and len(samples) >= 2:
        ticks = float(samples[-1]["cpu_ticks"]) - float(samples[0]["cpu_ticks"])
        total_cpu_sec = ticks / clk_tck
    out["RES.cpu_s_per_unit"] = _ratio(total_cpu_sec, _num(meta, "work_amount"))

    pss = _field_values([s for s in samples if not s.get("paused")], "pss_kb")
    out["RES.pss_mean_mib"] = sum(pss) / len(pss) / 1024.0 if pss else None
    out["RES.pss_p95_mib"] = nearest_rank(pss, 0.95) / 1024.0 if pss else None
    return out


def meta_metrics(meta: Mapping[str, Any]) -> dict[str, float | None]:
    """회차 종류와 무관한 meta 유래 지표."""
    bundle_bytes = _num(meta, "bundle_bytes")
    return {
        "RES.bundle_mib": None if bundle_bytes is None else bundle_bytes / 1048576.0
    }
