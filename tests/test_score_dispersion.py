"""
Tests for dossier/score_dispersion.py — the Score Dispersion Index.

Covers:
  1. compute_dispersion aggregation (mean/median/stdev, empty/bad input)
  2. (mean_score, coefficient_of_variation) → state classification
  3. history append/dedup + round-trip persistence (same pattern as breadth_index)
  4. dispersion_trend delta vs N sessions back
  5. format_dispersion_text summary line
"""

import json

from dossier.score_dispersion import (
    append_dispersion,
    classify_dispersion,
    compute_dispersion,
    dispersion_trend,
    format_dispersion_text,
    load_history,
    record_dispersion,
    save_history,
)


def _pick(ticker, score):
    return {"ticker": ticker, "score": score}


# ── compute_dispersion ────────────────────────────────────────────────

def test_compute_dispersion_empty_input():
    d = compute_dispersion([])
    assert d["total_scored"] == 0
    assert d["top_score"] == 0.0
    assert d["state"] == "flat"


def test_compute_dispersion_single_pick():
    d = compute_dispersion([_pick("AAA", 60)])
    assert d["total_scored"] == 1
    assert d["top_score"] == 60.0
    assert d["median_score"] == 60.0
    assert d["stdev_score"] == 0.0
    assert d["coefficient_of_variation"] == 0.0


def test_compute_dispersion_broad_strength():
    # Tight cluster of strong scores → low CoV, high mean.
    ranked = [_pick(f"T{i}", 55 + i) for i in range(6)]  # 55..60
    d = compute_dispersion(ranked)
    assert d["total_scored"] == 6
    assert d["state"] == "broad"
    assert d["color"] == "#00ff41"


def test_compute_dispersion_concentrated_lone_standout():
    # One big score, rest mediocre and tight → high CoV.
    ranked = [_pick("GOLD", 90)] + [_pick(f"T{i}", 25) for i in range(9)]
    d = compute_dispersion(ranked)
    assert d["top_score"] == 90.0
    assert d["state"] == "concentrated"
    assert d["color"] == "#f0b400"


def test_compute_dispersion_flat_tape():
    ranked = [_pick(f"T{i}", 5) for i in range(5)]
    d = compute_dispersion(ranked)
    assert d["state"] == "flat"
    assert d["color"] == "#e53935"


def test_compute_dispersion_never_raises_on_bad_values():
    ranked = [{"ticker": "AAA", "score": None}, {"ticker": "BBB"}]
    d = compute_dispersion(ranked)
    assert d["total_scored"] == 2
    assert d["top_score"] == 0.0


def test_compute_dispersion_skips_unparseable_scores():
    ranked = [_pick("AAA", 40), {"ticker": "BBB", "score": "not-a-number"}]
    d = compute_dispersion(ranked)
    assert d["total_scored"] == 1
    assert d["top_score"] == 40.0


# ── classify_dispersion ───────────────────────────────────────────────

def test_classify_dispersion_flat_below_mean_floor():
    s = classify_dispersion(10.0, 0.1)
    assert s["state"] == "flat"


def test_classify_dispersion_concentrated_high_cov():
    s = classify_dispersion(50.0, 0.6)
    assert s["state"] == "concentrated"


def test_classify_dispersion_broad_low_cov():
    s = classify_dispersion(50.0, 0.1)
    assert s["state"] == "broad"


def test_classify_dispersion_boundaries():
    assert classify_dispersion(19.9, 0.1)["state"] == "flat"
    assert classify_dispersion(20.0, 0.45)["state"] == "concentrated"
    assert classify_dispersion(20.0, 0.44)["state"] == "broad"


# ── history append/dedup + persistence ────────────────────────────────

def _entry(date, cov=0.2):
    return {"date": date, "coefficient_of_variation": cov, "total_scored": 10}


def test_append_dispersion_dedups_same_date():
    h = [_entry("2026-06-01", 0.2)]
    h = append_dispersion(h, _entry("2026-06-01", 0.5))
    assert len(h) == 1
    assert h[0]["coefficient_of_variation"] == 0.5


def test_append_dispersion_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_dispersion(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_dispersion_round_trip(tmp_path):
    p = tmp_path / "score_dispersion_history.json"
    record_dispersion(p, _entry("2026-06-01", 0.1))
    record_dispersion(p, _entry("2026-06-02", 0.3))
    record_dispersion(p, _entry("2026-06-02", 0.4))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["coefficient_of_variation"] == 0.4


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "score_dispersion_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── dispersion_trend ───────────────────────────────────────────────────

def test_dispersion_trend_insufficient_history():
    h = [_entry("2026-06-01", 0.2), _entry("2026-06-02", 0.3)]
    t = dispersion_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_dispersion_trend_widening():
    h = [_entry(f"2026-06-{d:02d}", 0.2) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 0.5))
    t = dispersion_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "widening"
    assert t["delta"] == 0.3
    assert t["lookback_date"] == "2026-06-01"


def test_dispersion_trend_narrowing():
    h = [_entry(f"2026-06-{d:02d}", 0.6) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 0.2))
    t = dispersion_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "narrowing"


def test_dispersion_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 0.3) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 0.32))
    t = dispersion_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_dispersion_text ──────────────────────────────────────────────

def test_format_dispersion_text_contains_key_fields():
    d = compute_dispersion([_pick("AAA", 60), _pick("BBB", 20)])
    text = format_dispersion_text(d)
    assert "Dispersion" in text
    assert "top" in text
    assert "2" in text  # total_scored
