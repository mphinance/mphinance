"""
Tests for dossier/quality_breadth.py — the Junk Rally Index.

Covers:
  1. compute_quality_index aggregation (universe vs leaders, empty/bad input)
  2. leaders_flagged_pct -> state classification
  3. history append/dedup + round-trip persistence (same pattern as score_dispersion)
  4. quality_trend delta vs N sessions back
  5. format_quality_text summary line
"""

import json

from dossier.quality_breadth import (
    append_quality,
    classify_quality,
    compute_quality_index,
    format_quality_text,
    load_history,
    quality_trend,
    record_quality,
    save_history,
)


def _pick(ticker, score, quality_score=100, flags=None):
    return {
        "ticker": ticker,
        "score": score,
        "quality_score": quality_score,
        "quality_flags": flags or {},
    }


# ── compute_quality_index ───────────────────────────────────────────────

def test_compute_quality_index_empty_input():
    q = compute_quality_index([])
    assert q["total_scored"] == 0
    assert q["leaders_n"] == 0
    assert q["junk_index"] == 0.0
    assert q["state"] == "clean_leadership"


def test_compute_quality_index_all_clean():
    ranked = [_pick(f"T{i}", 90 - i) for i in range(5)]
    q = compute_quality_index(ranked, leader_count=5)
    assert q["total_scored"] == 5
    assert q["leaders_n"] == 5
    assert q["leaders_flagged_pct"] == 0.0
    assert q["leaders_avg_quality"] == 100.0
    assert q["junk_index"] == 0.0
    assert q["state"] == "clean_leadership"
    assert q["color"] == "#00ff41"
    assert q["top_flags"] == {}


def test_compute_quality_index_junk_rally():
    # 4 of 5 leaders flagged (80%) -> junk rally.
    ranked = [
        _pick("AAA", 90, quality_score=40, flags={"is_penny": True}),
        _pick("BBB", 85, quality_score=55, flags={"is_recent_ipo": True}),
        _pick("CCC", 80, quality_score=60, flags={"is_penny": True}),
        _pick("DDD", 75, quality_score=70, flags={"is_low_liquidity": True}),
        _pick("EEE", 70, quality_score=100),
    ]
    q = compute_quality_index(ranked, leader_count=5)
    assert q["leaders_flagged_pct"] == 80.0
    assert q["state"] == "junk_rally"
    assert q["color"] == "#e53935"
    assert q["top_flags"]["is_penny"] == 2


def test_compute_quality_index_mixed_leadership():
    # 1 of 5 leaders flagged (20%) -> mixed.
    ranked = [_pick(f"T{i}", 90 - i) for i in range(4)] + [
        _pick("JUNK", 50, quality_score=40, flags={"is_shell": True})
    ]
    q = compute_quality_index(ranked, leader_count=5)
    assert q["leaders_flagged_pct"] == 20.0
    assert q["state"] == "mixed_leadership"
    assert q["color"] == "#f0b400"


def test_compute_quality_index_only_counts_top_leader_count():
    # 10 clean leaders, then a flagged straggler outside leader_count=10.
    ranked = [_pick(f"T{i}", 100 - i) for i in range(10)]
    ranked.append(_pick("STRAGGLER", 1, quality_score=10, flags={"is_spac": True}))
    q = compute_quality_index(ranked, leader_count=10)
    assert q["total_scored"] == 11
    assert q["leaders_n"] == 10
    assert q["leaders_flagged_pct"] == 0.0
    # But the universe-wide figure should still see the straggler.
    assert q["universe_flagged_pct"] > 0.0


def test_compute_quality_index_defensive_against_unsorted_input():
    # all_ranked arrives out of score order — leaders should still be top-N by score.
    ranked = [
        _pick("LOW", 10, quality_score=100),
        _pick("HIGH", 99, quality_score=20, flags={"is_penny": True}),
    ]
    q = compute_quality_index(ranked, leader_count=1)
    assert q["leaders_n"] == 1
    assert q["leaders_flagged_pct"] == 100.0


def test_compute_quality_index_never_raises_on_bad_values():
    ranked = [{"ticker": "AAA"}, {"ticker": "BBB", "score": None, "quality_flags": "not-a-dict"}]
    q = compute_quality_index(ranked)
    assert q["total_scored"] == 2
    assert q["leaders_n"] == 2
    assert q["universe_avg_quality"] == 100.0


# ── classify_quality ──────────────────────────────────────────────────

def test_classify_quality_boundaries():
    assert classify_quality(19.9)["state"] == "clean_leadership"
    assert classify_quality(20.0)["state"] == "mixed_leadership"
    assert classify_quality(49.9)["state"] == "mixed_leadership"
    assert classify_quality(50.0)["state"] == "junk_rally"


# ── history append/dedup + persistence ──────────────────────────────────

def _entry(date, junk_index=10.0):
    return {"date": date, "junk_index": junk_index, "total_scored": 10}


def test_append_quality_dedups_same_date():
    h = [_entry("2026-06-01", 10.0)]
    h = append_quality(h, _entry("2026-06-01", 40.0))
    assert len(h) == 1
    assert h[0]["junk_index"] == 40.0


def test_append_quality_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_quality(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_quality_round_trip(tmp_path):
    p = tmp_path / "quality_breadth_history.json"
    record_quality(p, _entry("2026-06-01", 5.0))
    record_quality(p, _entry("2026-06-02", 15.0))
    record_quality(p, _entry("2026-06-02", 25.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["junk_index"] == 25.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "quality_breadth_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── quality_trend ────────────────────────────────────────────────────────

def test_quality_trend_insufficient_history():
    h = [_entry("2026-06-01", 10.0), _entry("2026-06-02", 20.0)]
    t = quality_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_quality_trend_getting_junkier():
    h = [_entry(f"2026-06-{d:02d}", 10.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 40.0))
    t = quality_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "getting_junkier"
    assert t["delta"] == 30.0
    assert t["lookback_date"] == "2026-06-01"


def test_quality_trend_cleaning_up():
    h = [_entry(f"2026-06-{d:02d}", 40.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 5.0))
    t = quality_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "cleaning_up"


def test_quality_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 10.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 12.0))
    t = quality_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_quality_text ───────────────────────────────────────────────────

def test_format_quality_text_contains_key_fields():
    ranked = [_pick("AAA", 90, quality_score=40, flags={"is_penny": True})]
    q = compute_quality_index(ranked, leader_count=1)
    text = format_quality_text(q)
    assert "Junk Index" in text
    assert "100" in text  # 100% of the 1 leader flagged
    assert "is_penny" in text
