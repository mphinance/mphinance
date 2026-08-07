"""
Tests for dossier/follow_through_index.py — the Follow-Through Index.

Covers:
  1. compute_follow_through aggregation (universe vs leaders, empty/bad input)
  2. leaders_advance_pct -> state classification
  3. history append/dedup + round-trip persistence (same pattern as quality_breadth)
  4. follow_through_trend delta vs N sessions back
  5. format_follow_through_text summary line
"""

import json

from dossier.follow_through_index import (
    append_follow_through,
    classify_follow_through,
    compute_follow_through,
    follow_through_trend,
    format_follow_through_text,
    load_history,
    record_follow_through,
    save_history,
)


def _pick(ticker, score, change_pct=0.0):
    return {"ticker": ticker, "score": score, "change_pct": change_pct}


# ── compute_follow_through ────────────────────────────────────────────────

def test_compute_follow_through_empty_input():
    f = compute_follow_through([])
    assert f["total_scored"] == 0
    assert f["leaders_n"] == 0
    assert f["follow_through_gap"] == 0.0
    assert f["state"] == "insufficient"


def test_compute_follow_through_all_leaders_advancing():
    ranked = [_pick(f"T{i}", 90 - i, change_pct=1.5) for i in range(5)]
    f = compute_follow_through(ranked, leader_count=5)
    assert f["total_scored"] == 5
    assert f["leaders_n"] == 5
    assert f["leaders_advance_pct"] == 100.0
    assert f["universe_advance_pct"] == 100.0
    assert f["follow_through_gap"] == 0.0
    assert f["state"] == "confirmed"
    assert f["color"] == "#00ff41"


def test_compute_follow_through_leaders_unconfirmed():
    # 5 leaders all red -> unconfirmed, even though the broader universe is fine.
    ranked = [_pick(f"T{i}", 90 - i, change_pct=-1.0) for i in range(5)]
    ranked += [_pick(f"U{i}", 10 - i, change_pct=2.0) for i in range(5)]
    f = compute_follow_through(ranked, leader_count=5)
    assert f["leaders_advance_pct"] == 0.0
    assert f["universe_advance_pct"] == 50.0
    assert f["follow_through_gap"] == -50.0
    assert f["state"] == "unconfirmed"
    assert f["color"] == "#e53935"


def test_compute_follow_through_mixed():
    ranked = [_pick("A", 90, change_pct=1.0), _pick("B", 80, change_pct=1.0),
              _pick("C", 70, change_pct=-1.0), _pick("D", 60, change_pct=-1.0),
              _pick("E", 50, change_pct=0.0)]
    f = compute_follow_through(ranked, leader_count=5)
    assert f["leaders_advance_pct"] == 40.0
    assert f["state"] == "mixed"
    assert f["color"] == "#f0b400"


def test_compute_follow_through_only_counts_top_leader_count():
    ranked = [_pick(f"T{i}", 100 - i, change_pct=2.0) for i in range(10)]
    ranked.append(_pick("STRAGGLER", 1, change_pct=-5.0))
    f = compute_follow_through(ranked, leader_count=10)
    assert f["total_scored"] == 11
    assert f["leaders_n"] == 10
    assert f["leaders_advance_pct"] == 100.0
    assert f["universe_advance_pct"] < 100.0


def test_compute_follow_through_defensive_against_unsorted_input():
    ranked = [
        _pick("LOW", 10, change_pct=5.0),
        _pick("HIGH", 99, change_pct=-5.0),
    ]
    f = compute_follow_through(ranked, leader_count=1)
    assert f["leaders_n"] == 1
    assert f["leaders_advance_pct"] == 0.0


def test_compute_follow_through_insufficient_data_below_min():
    ranked = [_pick("A", 50, change_pct=1.0), _pick("B", 40, change_pct=1.0)]
    f = compute_follow_through(ranked)
    assert f["state"] == "insufficient"


def test_compute_follow_through_never_raises_on_bad_values():
    # Neither pick carries a usable change_pct (missing / non-numeric), so this
    # hits the "no usable data" early return — leaders_n is correctly 0, not 2.
    ranked = [{"ticker": "AAA"}, {"ticker": "BBB", "score": None, "change_pct": "not-a-number"}]
    f = compute_follow_through(ranked)
    assert f["total_scored"] == 2
    assert f["leaders_n"] == 0
    assert f["universe_avg_change_pct"] == 0.0


# ── classify_follow_through ─────────────────────────────────────────────

def test_classify_follow_through_insufficient_below_min():
    s = classify_follow_through(100.0, 2)
    assert s["state"] == "insufficient"


def test_classify_follow_through_boundaries():
    assert classify_follow_through(30.0, 10)["state"] == "unconfirmed"
    assert classify_follow_through(30.1, 10)["state"] == "mixed"
    assert classify_follow_through(69.9, 10)["state"] == "mixed"
    assert classify_follow_through(70.0, 10)["state"] == "confirmed"


# ── history append/dedup + persistence ────────────────────────────────

def _entry(date, leaders_advance_pct=50.0):
    return {"date": date, "leaders_advance_pct": leaders_advance_pct, "total_scored": 10}


def test_append_follow_through_dedups_same_date():
    h = [_entry("2026-06-01", 10.0)]
    h = append_follow_through(h, _entry("2026-06-01", 40.0))
    assert len(h) == 1
    assert h[0]["leaders_advance_pct"] == 40.0


def test_append_follow_through_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_follow_through(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_follow_through_round_trip(tmp_path):
    p = tmp_path / "follow_through_index_history.json"
    record_follow_through(p, _entry("2026-06-01", 5.0))
    record_follow_through(p, _entry("2026-06-02", 15.0))
    record_follow_through(p, _entry("2026-06-02", 25.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["leaders_advance_pct"] == 25.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "follow_through_index_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── follow_through_trend ─────────────────────────────────────────────────

def test_follow_through_trend_insufficient_history():
    h = [_entry("2026-06-01", 10.0), _entry("2026-06-02", 20.0)]
    t = follow_through_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_follow_through_trend_strengthening():
    h = [_entry(f"2026-06-{d:02d}", 20.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 60.0))
    t = follow_through_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "strengthening"
    assert t["delta"] == 40.0
    assert t["lookback_date"] == "2026-06-01"


def test_follow_through_trend_fading():
    h = [_entry(f"2026-06-{d:02d}", 60.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 10.0))
    t = follow_through_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "fading"


def test_follow_through_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 20.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 25.0))
    t = follow_through_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_follow_through_text ────────────────────────────────────────────

def test_format_follow_through_text_contains_key_fields():
    ranked = [_pick("AAA", 90, change_pct=1.0)]
    f = compute_follow_through(ranked, leader_count=1)
    text = format_follow_through_text(f)
    assert "Follow-Through" in text
    assert "100" in text  # 100% of the 1 leader advancing
