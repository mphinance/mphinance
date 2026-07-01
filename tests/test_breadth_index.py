"""
Tests for dossier/breadth_index.py — the Momentum Breadth Index.

Covers:
  1. compute_breadth aggregation (percentages, sector breakdown, empty input)
  2. breadth-score → state classification (expanding/neutral/contracting)
  3. history append/dedup + round-trip persistence (same pattern as mood_ring)
  4. breadth_trend delta vs N sessions back
  5. format_breadth_text summary line
"""

import json

from dossier.breadth_index import (
    append_breadth,
    breadth_trend,
    classify_breadth,
    compute_breadth,
    format_breadth_text,
    load_history,
    record_breadth,
    save_history,
)


def _pick(ticker, ema_stack="FULL BULLISH", adx=30, rsi=50, score=60,
          is_pullback=False, sector="Technology"):
    return {
        "ticker": ticker, "ema_stack": ema_stack, "adx": adx, "rsi": rsi,
        "score": score, "is_pullback_setup": is_pullback, "sector": sector,
    }


# ── compute_breadth ──────────────────────────────────────────────────

def test_compute_breadth_empty_input():
    b = compute_breadth([])
    assert b["total_scored"] == 0
    assert b["breadth_score"] == 0.0
    assert b["sectors"] == {}


def test_compute_breadth_all_strong():
    ranked = [_pick(f"T{i}", adx=30, rsi=50, is_pullback=True) for i in range(4)]
    b = compute_breadth(ranked)
    assert b["total_scored"] == 4
    assert b["bullish_pct"] == 100.0
    assert b["trending_pct"] == 100.0
    assert b["sweet_spot_pct"] == 100.0
    assert b["pullback_pct"] == 100.0
    assert b["breadth_score"] == 100.0


def test_compute_breadth_mixed():
    ranked = [
        _pick("AAA", ema_stack="FULL BULLISH", adx=30, rsi=50),
        _pick("BBB", ema_stack="FULL BEARISH", adx=10, rsi=80),
    ]
    b = compute_breadth(ranked)
    assert b["bullish_pct"] == 50.0
    assert b["trending_pct"] == 50.0
    assert b["sweet_spot_pct"] == 50.0
    assert b["breadth_score"] == 37.5  # (50+50+50+0)/4


def test_compute_breadth_sector_grouping():
    ranked = [
        _pick("AAA", sector="Technology", score=80),
        _pick("BBB", sector="Technology", score=40, ema_stack="FULL BEARISH"),
        _pick("CCC", sector="Energy", score=20, ema_stack="FULL BEARISH"),
    ]
    b = compute_breadth(ranked)
    assert b["sectors"]["Technology"]["count"] == 2
    assert b["sectors"]["Technology"]["bullish_pct"] == 50.0
    assert b["sectors"]["Technology"]["avg_score"] == 60.0
    assert b["sectors"]["Energy"]["count"] == 1


def test_compute_breadth_missing_sector_defaults_to_other():
    b = compute_breadth([{"ticker": "AAA", "score": 10}])
    assert "Other" in b["sectors"]


def test_compute_breadth_never_raises_on_bad_values():
    ranked = [{"ticker": "AAA", "adx": None, "rsi": None, "score": None}]
    b = compute_breadth(ranked)
    assert b["total_scored"] == 1


# ── classify_breadth ─────────────────────────────────────────────────

def test_classify_breadth_expanding():
    s = classify_breadth(80)
    assert s["state"] == "expanding"
    assert s["color"] == "#00ff41"


def test_classify_breadth_neutral():
    s = classify_breadth(50)
    assert s["state"] == "neutral"
    assert s["color"] == "#f0b400"


def test_classify_breadth_contracting():
    s = classify_breadth(10)
    assert s["state"] == "contracting"
    assert s["color"] == "#e53935"


def test_classify_breadth_boundaries():
    assert classify_breadth(65)["state"] == "expanding"
    assert classify_breadth(35)["state"] == "neutral"
    assert classify_breadth(34.9)["state"] == "contracting"


# ── history append/dedup + persistence ───────────────────────────────

def _entry(date, score=50.0):
    return {"date": date, "breadth_score": score, "total_scored": 10}


def test_append_breadth_dedups_same_date():
    h = [_entry("2026-06-01", 40.0)]
    h = append_breadth(h, _entry("2026-06-01", 70.0))
    assert len(h) == 1
    assert h[0]["breadth_score"] == 70.0


def test_append_breadth_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_breadth(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_breadth_round_trip(tmp_path):
    p = tmp_path / "breadth_history.json"
    record_breadth(p, _entry("2026-06-01", 30.0))
    record_breadth(p, _entry("2026-06-02", 60.0))
    record_breadth(p, _entry("2026-06-02", 65.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["breadth_score"] == 65.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "breadth_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── breadth_trend ─────────────────────────────────────────────────────

def test_breadth_trend_insufficient_history():
    h = [_entry("2026-06-01", 40.0), _entry("2026-06-02", 60.0)]
    t = breadth_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_breadth_trend_expanding():
    h = [_entry(f"2026-06-{d:02d}", 30.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 50.0))
    t = breadth_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "expanding"
    assert t["delta"] == 20.0
    assert t["lookback_date"] == "2026-06-01"


def test_breadth_trend_contracting():
    h = [_entry(f"2026-06-{d:02d}", 70.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 40.0))
    t = breadth_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "contracting"


def test_breadth_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 50.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 52.0))
    t = breadth_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_breadth_text ───────────────────────────────────────────────

def test_format_breadth_text_contains_key_fields():
    b = compute_breadth([_pick("AAA"), _pick("BBB", ema_stack="FULL BEARISH", adx=5, rsi=90)])
    text = format_breadth_text(b)
    assert "Breadth" in text
    assert "%" in text
    assert "2" in text  # total_scored
