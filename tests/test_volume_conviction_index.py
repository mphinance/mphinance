"""
Tests for dossier/volume_conviction_index.py — the Volume Conviction Index.

Covers:
  1. compute_volume_conviction aggregation (universe vs leaders, empty/bad input)
  2. leaders_elevated_pct -> state classification
  3. history append/dedup + round-trip persistence (same pattern as follow_through_index)
  4. volume_conviction_trend delta vs N sessions back
  5. format_volume_conviction_text summary line
"""

import json

from dossier.volume_conviction_index import (
    append_volume_conviction,
    classify_volume_conviction,
    compute_volume_conviction,
    format_volume_conviction_text,
    load_history,
    record_volume_conviction,
    save_history,
    volume_conviction_trend,
)


def _pick(ticker, score, rel_vol=1.0):
    return {"ticker": ticker, "score": score, "rel_vol": rel_vol}


# ── compute_volume_conviction ───────────────────────────────────────────

def test_compute_volume_conviction_empty_input():
    v = compute_volume_conviction([])
    assert v["total_scored"] == 0
    assert v["leaders_n"] == 0
    assert v["conviction_gap"] == 0.0
    assert v["state"] == "insufficient"


def test_compute_volume_conviction_all_leaders_elevated():
    ranked = [_pick(f"T{i}", 90 - i, rel_vol=2.0) for i in range(5)]
    v = compute_volume_conviction(ranked, leader_count=5)
    assert v["total_scored"] == 5
    assert v["leaders_n"] == 5
    assert v["leaders_elevated_pct"] == 100.0
    assert v["universe_elevated_pct"] == 100.0
    assert v["conviction_gap"] == 0.0
    assert v["state"] == "confirmed"
    assert v["color"] == "#00ff41"


def test_compute_volume_conviction_leaders_thin():
    # 5 leaders all sub-average volume -> thin, even though the broader
    # universe is trading at normal-to-elevated volume.
    ranked = [_pick(f"T{i}", 90 - i, rel_vol=0.3) for i in range(5)]
    ranked += [_pick(f"U{i}", 10 - i, rel_vol=2.0) for i in range(5)]
    v = compute_volume_conviction(ranked, leader_count=5)
    assert v["leaders_elevated_pct"] == 0.0
    assert v["leaders_thin_pct"] == 100.0
    assert v["universe_elevated_pct"] == 50.0
    assert v["conviction_gap"] == -50.0
    assert v["state"] == "thin"
    assert v["color"] == "#e53935"


def test_compute_volume_conviction_mixed():
    ranked = [_pick("A", 90, rel_vol=2.0), _pick("B", 80, rel_vol=2.0),
              _pick("C", 70, rel_vol=0.5), _pick("D", 60, rel_vol=0.5),
              _pick("E", 50, rel_vol=1.0)]
    v = compute_volume_conviction(ranked, leader_count=5)
    assert v["leaders_elevated_pct"] == 40.0
    assert v["state"] == "mixed"
    assert v["color"] == "#f0b400"


def test_compute_volume_conviction_only_counts_top_leader_count():
    ranked = [_pick(f"T{i}", 100 - i, rel_vol=2.0) for i in range(10)]
    ranked.append(_pick("STRAGGLER", 1, rel_vol=0.1))
    v = compute_volume_conviction(ranked, leader_count=10)
    assert v["total_scored"] == 11
    assert v["leaders_n"] == 10
    assert v["leaders_elevated_pct"] == 100.0
    assert v["universe_elevated_pct"] < 100.0


def test_compute_volume_conviction_defensive_against_unsorted_input():
    ranked = [
        _pick("LOW", 10, rel_vol=3.0),
        _pick("HIGH", 99, rel_vol=0.2),
    ]
    v = compute_volume_conviction(ranked, leader_count=1)
    assert v["leaders_n"] == 1
    assert v["leaders_elevated_pct"] == 0.0


def test_compute_volume_conviction_insufficient_data_below_min():
    ranked = [_pick("A", 50, rel_vol=2.0), _pick("B", 40, rel_vol=2.0)]
    v = compute_volume_conviction(ranked)
    assert v["state"] == "insufficient"


def test_compute_volume_conviction_never_raises_on_bad_values():
    # Neither pick carries a usable rel_vol, so the universe has zero usable
    # data points — compute_volume_conviction reports leaders_n == 0 rather
    # than a confident verdict computed from nothing.
    ranked = [{"ticker": "AAA"}, {"ticker": "BBB", "score": None, "rel_vol": "not-a-number"}]
    v = compute_volume_conviction(ranked)
    assert v["total_scored"] == 2
    assert v["leaders_n"] == 0
    assert v["universe_avg_rel_vol"] == 0.0


# ── classify_volume_conviction ──────────────────────────────────────────

def test_classify_volume_conviction_insufficient_below_min():
    s = classify_volume_conviction(100.0, 2)
    assert s["state"] == "insufficient"


def test_classify_volume_conviction_boundaries():
    assert classify_volume_conviction(15.0, 10)["state"] == "thin"
    assert classify_volume_conviction(15.1, 10)["state"] == "mixed"
    assert classify_volume_conviction(49.9, 10)["state"] == "mixed"
    assert classify_volume_conviction(50.0, 10)["state"] == "confirmed"


# ── history append/dedup + persistence ──────────────────────────────────

def _entry(date, leaders_elevated_pct=50.0):
    return {"date": date, "leaders_elevated_pct": leaders_elevated_pct, "total_scored": 10}


def test_append_volume_conviction_dedups_same_date():
    h = [_entry("2026-06-01", 10.0)]
    h = append_volume_conviction(h, _entry("2026-06-01", 40.0))
    assert len(h) == 1
    assert h[0]["leaders_elevated_pct"] == 40.0


def test_append_volume_conviction_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_volume_conviction(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_volume_conviction_round_trip(tmp_path):
    p = tmp_path / "volume_conviction_history.json"
    record_volume_conviction(p, _entry("2026-06-01", 5.0))
    record_volume_conviction(p, _entry("2026-06-02", 15.0))
    record_volume_conviction(p, _entry("2026-06-02", 25.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["leaders_elevated_pct"] == 25.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "volume_conviction_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── volume_conviction_trend ──────────────────────────────────────────────

def test_volume_conviction_trend_insufficient_history():
    h = [_entry("2026-06-01", 10.0), _entry("2026-06-02", 20.0)]
    t = volume_conviction_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_volume_conviction_trend_strengthening():
    h = [_entry(f"2026-06-{d:02d}", 20.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 60.0))
    t = volume_conviction_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "strengthening"
    assert t["delta"] == 40.0
    assert t["lookback_date"] == "2026-06-01"


def test_volume_conviction_trend_fading():
    h = [_entry(f"2026-06-{d:02d}", 60.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 10.0))
    t = volume_conviction_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "fading"


def test_volume_conviction_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 20.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 25.0))
    t = volume_conviction_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_volume_conviction_text ─────────────────────────────────────────

def test_format_volume_conviction_text_contains_key_fields():
    ranked = [_pick("AAA", 90, rel_vol=2.0)]
    v = compute_volume_conviction(ranked, leader_count=1)
    text = format_volume_conviction_text(v)
    assert "Volume Conviction" in text
    assert "100" in text  # 100% of the 1 leader elevated
