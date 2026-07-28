"""
Tests for dossier/extension_index.py — Tape Extension Index.

Covers:
  1. compute_extension_index aggregation (chase-risk/capitulation/balanced, empty/bad input)
  2. (net_extension, total_scored) → state classification
  3. history append/dedup + round-trip persistence (same pattern as sector_leadership)
  4. extension_trend vs N sessions back
  5. format_extension_text summary line
"""

import json

from dossier.extension_index import (
    append_extension,
    classify_extension,
    compute_extension_index,
    extension_trend,
    format_extension_text,
    load_history,
    record_extension,
    save_history,
)


def _pick(ticker, rsi, stoch_k):
    return {"ticker": ticker, "rsi": rsi, "stoch_k": stoch_k}


# ── compute_extension_index ─────────────────────────────────────────────

def test_compute_extension_index_empty_input():
    d = compute_extension_index([])
    assert d["total_scored"] == 0
    assert d["net_extension"] == 0.0
    assert d["state"] == "insufficient"


def test_compute_extension_index_chase_risk():
    # 4/5 names overbought, 0 oversold → net_extension = 80 → chase risk.
    ranked = [_pick(f"T{i}", 75, 85) for i in range(4)] + [_pick("N1", 50, 50)]
    d = compute_extension_index(ranked)
    assert d["total_scored"] == 5
    assert d["overbought_pct"] == 80.0
    assert d["oversold_pct"] == 0.0
    assert d["net_extension"] == 80.0
    assert d["state"] == "chase_risk"
    assert d["color"] == "#e53935"
    assert "T0" in d["overbought_tickers"]


def test_compute_extension_index_capitulation():
    # 4/5 names oversold, 0 overbought → net_extension = -80 → capitulation.
    ranked = [_pick(f"T{i}", 20, 10) for i in range(4)] + [_pick("N1", 50, 50)]
    d = compute_extension_index(ranked)
    assert d["overbought_pct"] == 0.0
    assert d["oversold_pct"] == 80.0
    assert d["net_extension"] == -80.0
    assert d["state"] == "capitulation"
    assert d["color"] == "#00ff41"
    assert "T0" in d["oversold_tickers"]


def test_compute_extension_index_balanced():
    ranked = [_pick(f"N{i}", 50, 50) for i in range(6)]
    d = compute_extension_index(ranked)
    assert d["net_extension"] == 0.0
    assert d["state"] == "balanced"
    assert d["color"] == "#f0b400"


def test_compute_extension_index_insufficient_data():
    ranked = [_pick("A", 75, 85), _pick("B", 50, 50)]
    d = compute_extension_index(ranked)
    assert d["total_scored"] == 2
    assert d["state"] == "insufficient"


def test_compute_extension_index_requires_both_rsi_and_stoch():
    # High RSI alone (without Stoch confirmation) should not count as overbought.
    ranked = [_pick(f"N{i}", 75, 50) for i in range(6)]
    d = compute_extension_index(ranked)
    assert d["overbought_pct"] == 0.0


def test_compute_extension_index_missing_fields_default_to_zero():
    ranked = [{"ticker": "A"}, {"ticker": "B"}, {"ticker": "C"}, {"ticker": "D"}, {"ticker": "E"}]
    d = compute_extension_index(ranked)
    assert d["total_scored"] == 5
    assert d["overbought_pct"] == 0.0
    assert d["oversold_pct"] == 100.0  # rsi=0 <= 30 and stoch_k=0 <= 20


def test_compute_extension_index_skips_unparseable_values():
    ranked = [
        _pick("AAA", 75, 85),
        {"ticker": "BBB", "rsi": "not-a-number", "stoch_k": 85},
        _pick("CCC", 75, 85),
        _pick("DDD", 75, 85),
        _pick("EEE", 75, 85),
    ]
    d = compute_extension_index(ranked)
    assert d["total_scored"] == 4
    assert d["overbought_pct"] == 100.0


def test_compute_extension_index_caps_ticker_lists():
    ranked = [_pick(f"T{i}", 75, 85) for i in range(15)]
    d = compute_extension_index(ranked)
    assert len(d["overbought_tickers"]) == 10


# ── classify_extension ──────────────────────────────────────────────────

def test_classify_extension_insufficient_below_min():
    s = classify_extension(80.0, 2)
    assert s["state"] == "insufficient"


def test_classify_extension_chase_risk():
    s = classify_extension(20.0, 10)
    assert s["state"] == "chase_risk"


def test_classify_extension_capitulation():
    s = classify_extension(-20.0, 10)
    assert s["state"] == "capitulation"


def test_classify_extension_balanced():
    s = classify_extension(0.0, 10)
    assert s["state"] == "balanced"


def test_classify_extension_boundaries():
    assert classify_extension(14.9, 10)["state"] == "balanced"
    assert classify_extension(15.0, 10)["state"] == "chase_risk"
    assert classify_extension(-14.9, 10)["state"] == "balanced"
    assert classify_extension(-15.0, 10)["state"] == "capitulation"


# ── history append/dedup + persistence ──────────────────────────────────

def _entry(date, net_extension=0.0):
    return {"date": date, "net_extension": net_extension, "total_scored": 10}


def test_append_extension_dedups_same_date():
    h = [_entry("2026-06-01", net_extension=20.0)]
    h = append_extension(h, _entry("2026-06-01", net_extension=50.0))
    assert len(h) == 1
    assert h[0]["net_extension"] == 50.0


def test_append_extension_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_extension(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_extension_round_trip(tmp_path):
    p = tmp_path / "extension_index_history.json"
    record_extension(p, _entry("2026-06-01", net_extension=10.0))
    record_extension(p, _entry("2026-06-02", net_extension=30.0))
    record_extension(p, _entry("2026-06-02", net_extension=40.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["net_extension"] == 40.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "extension_index_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── extension_trend ──────────────────────────────────────────────────────

def test_extension_trend_insufficient_history():
    h = [_entry("2026-06-01"), _entry("2026-06-02")]
    t = extension_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["lookback_date"] is None


def test_extension_trend_detects_more_extended():
    h = [_entry(f"2026-06-{d:02d}", net_extension=0.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", net_extension=25.0))
    t = extension_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "more_extended"
    assert t["delta"] == 25.0
    assert t["lookback_date"] == "2026-06-01"


def test_extension_trend_detects_more_capitulated():
    h = [_entry(f"2026-06-{d:02d}", net_extension=0.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", net_extension=-25.0))
    t = extension_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "more_capitulated"


def test_extension_trend_flat_no_change():
    h = [_entry(f"2026-06-{d:02d}", net_extension=10.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", net_extension=10.0))
    t = extension_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_extension_text ────────────────────────────────────────────────

def test_format_extension_text_contains_key_fields():
    d = compute_extension_index([_pick(f"T{i}", 75, 85) for i in range(4)] + [_pick("N1", 50, 50)])
    text = format_extension_text(d)
    assert "Tape Extension" in text
    assert "overbought" in text
