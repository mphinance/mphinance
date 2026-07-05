"""
Tests for dossier/factor_leaderboard.py — the Factor Leaderboard.

Covers:
  1. compute_leaderboard aggregation (avg pct per factor, ranking, empty input)
  2. never-raises on missing/malformed breakdown data
  3. history append/dedup + round-trip persistence (same pattern as breadth_index)
  4. factor_trend delta vs N sessions back
  5. format_leaderboard_text summary line
"""

import json

from dossier.factor_leaderboard import (
    MAX_POINTS,
    append_leaderboard,
    compute_leaderboard,
    factor_trend,
    format_leaderboard_text,
    load_history,
    record_leaderboard,
    save_history,
)


def _pick(ticker, **breakdown):
    return {"ticker": ticker, "breakdown": breakdown}


# ── compute_leaderboard ───────────────────────────────────────────────

def test_compute_leaderboard_empty_input():
    lb = compute_leaderboard([])
    assert lb["total_scored"] == 0
    assert lb["factors"] == []


def test_compute_leaderboard_maxed_out_factor_is_100_pct():
    ranked = [_pick(f"T{i}", adx=18, rsi=1) for i in range(3)]
    lb = compute_leaderboard(ranked)
    by_factor = {f["factor"]: f for f in lb["factors"]}
    assert by_factor["adx"]["avg_pct"] == 100.0
    assert by_factor["adx"]["avg_points"] == 18.0


def test_compute_leaderboard_ranks_descending():
    ranked = [_pick("AAA", adx=18, rsi=1), _pick("BBB", adx=0, rsi=1)]
    lb = compute_leaderboard(ranked)
    pcts = [f["avg_pct"] for f in lb["factors"]]
    assert pcts == sorted(pcts, reverse=True)
    assert lb["factors"][0]["factor"] == "adx"


def test_compute_leaderboard_negative_fortress_clamped_to_zero():
    ranked = [_pick("AAA", fortress=-10)]
    lb = compute_leaderboard(ranked)
    fortress = next(f for f in lb["factors"] if f["factor"] == "fortress")
    assert fortress["avg_pct"] == 0.0


def test_compute_leaderboard_ignores_unknown_and_missing_factors():
    ranked = [_pick("AAA", adx=10, some_other_key=999), {"ticker": "BBB"}]
    lb = compute_leaderboard(ranked)
    factors = {f["factor"] for f in lb["factors"]}
    assert "some_other_key" not in factors
    assert "adx" in factors
    assert next(f for f in lb["factors"] if f["factor"] == "adx")["n"] == 1


def test_compute_leaderboard_never_raises_on_bad_values():
    ranked = [{"ticker": "AAA", "breakdown": {"adx": None, "rsi": "not-a-number"}}]
    lb = compute_leaderboard(ranked)
    assert lb["total_scored"] == 1
    assert lb["factors"] == []


def test_max_points_covers_all_labeled_factors():
    from dossier.factor_leaderboard import FACTOR_LABELS
    assert set(MAX_POINTS) == set(FACTOR_LABELS)


# ── history append/dedup + persistence ────────────────────────────────

def _entry(date, factors=None):
    return {"date": date, "total_scored": 10, "factors": factors or []}


def test_append_leaderboard_dedups_same_date():
    h = [_entry("2026-06-01")]
    h = append_leaderboard(h, _entry("2026-06-01", [{"factor": "adx", "avg_pct": 70.0}]))
    assert len(h) == 1
    assert h[0]["factors"][0]["avg_pct"] == 70.0


def test_append_leaderboard_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_leaderboard(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_leaderboard_round_trip(tmp_path):
    p = tmp_path / "factor_leaderboard_history.json"
    record_leaderboard(p, _entry("2026-06-01"))
    record_leaderboard(p, _entry("2026-06-02", [{"factor": "adx", "avg_pct": 60.0}]))
    record_leaderboard(p, _entry("2026-06-02", [{"factor": "adx", "avg_pct": 65.0}]))  # overwrite

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["factors"][0]["avg_pct"] == 65.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "factor_leaderboard_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── factor_trend ───────────────────────────────────────────────────────

def test_factor_trend_insufficient_history():
    h = [_entry("2026-06-01"), _entry("2026-06-02")]
    t = factor_trend(h, "2026-06-02", "adx", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_factor_trend_rising():
    h = [_entry(f"2026-06-{d:02d}", [{"factor": "adx", "avg_pct": 30.0}]) for d in range(1, 6)]
    h.append(_entry("2026-06-06", [{"factor": "adx", "avg_pct": 50.0}]))
    t = factor_trend(h, "2026-06-06", "adx", lookback=5)
    assert t["direction"] == "rising"
    assert t["delta"] == 20.0
    assert t["lookback_date"] == "2026-06-01"


def test_factor_trend_fading():
    h = [_entry(f"2026-06-{d:02d}", [{"factor": "adx", "avg_pct": 70.0}]) for d in range(1, 6)]
    h.append(_entry("2026-06-06", [{"factor": "adx", "avg_pct": 40.0}]))
    t = factor_trend(h, "2026-06-06", "adx", lookback=5)
    assert t["direction"] == "fading"


def test_factor_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", [{"factor": "adx", "avg_pct": 50.0}]) for d in range(1, 6)]
    h.append(_entry("2026-06-06", [{"factor": "adx", "avg_pct": 52.0}]))
    t = factor_trend(h, "2026-06-06", "adx", lookback=5)
    assert t["direction"] == "flat"


def test_factor_trend_missing_factor_in_entry():
    h = [_entry(f"2026-06-{d:02d}", [{"factor": "rsi", "avg_pct": 50.0}]) for d in range(1, 7)]
    t = factor_trend(h, "2026-06-06", "adx", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0


# ── format_leaderboard_text ─────────────────────────────────────────────

def test_format_leaderboard_text_empty():
    text = format_leaderboard_text({"total_scored": 0, "factors": []})
    assert "no scored universe" in text


def test_format_leaderboard_text_contains_key_fields():
    lb = compute_leaderboard([_pick("AAA", adx=18, rsi=15), _pick("BBB", adx=0, rsi=1)])
    text = format_leaderboard_text(lb)
    assert "Factor Leaderboard" in text
    assert "%" in text
    assert "2" in text  # total_scored
