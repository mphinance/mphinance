"""
Tests for dossier/vol_risk_premium.py — the Volatility Risk Premium stat.

Covers:
  1. compute_realized_vol (annualized realized vol from a Close series)
  2. compute_vrp aggregation + vrp -> state classification (rich/fair/cheap)
  3. fetch_and_compute_vrp fail-open behavior on bad/missing data
  4. history append/dedup + round-trip persistence (same pattern as breadth_index)
  5. vrp_trend delta vs N sessions back
  6. format_vrp_text summary line
"""

import json

import numpy as np
import pandas as pd
import pytest

from dossier.vol_risk_premium import (
    append_vrp,
    classify_vrp,
    compute_realized_vol,
    compute_vrp,
    fetch_and_compute_vrp,
    format_vrp_text,
    load_history,
    record_vrp,
    save_history,
    vrp_trend,
)


def _spy_hist(closes):
    return pd.DataFrame({"Close": closes})


# ── compute_realized_vol ──────────────────────────────────────────────

def test_compute_realized_vol_flat_series_is_zero():
    vol = compute_realized_vol(_spy_hist([100.0] * 25))
    assert vol == 0.0


def test_compute_realized_vol_insufficient_rows_is_none():
    vol = compute_realized_vol(_spy_hist([100.0] * 10))
    assert vol is None


def test_compute_realized_vol_none_input():
    assert compute_realized_vol(None) is None


def test_compute_realized_vol_missing_close_column():
    assert compute_realized_vol(pd.DataFrame({"Open": [1, 2, 3]})) is None


def test_compute_realized_vol_alternating_series_is_positive():
    closes = [100.0, 105.0] * 15
    vol = compute_realized_vol(_spy_hist(closes))
    assert vol is not None
    assert vol > 0


# ── compute_vrp / classify_vrp ─────────────────────────────────────────

def test_compute_vrp_rich():
    v = compute_vrp(vix_level=25.0, realized_vol=15.0)
    assert v["vrp"] == 10.0
    assert v["state"] == "rich"
    assert v["available"] is True


def test_compute_vrp_cheap():
    v = compute_vrp(vix_level=12.0, realized_vol=20.0)
    assert v["vrp"] == -8.0
    assert v["state"] == "cheap"


def test_compute_vrp_fair():
    v = compute_vrp(vix_level=18.0, realized_vol=17.0)
    assert v["vrp"] == 1.0
    assert v["state"] == "fair"


def test_compute_vrp_ratio():
    v = compute_vrp(vix_level=20.0, realized_vol=10.0)
    assert v["vrp_ratio"] == 2.0


def test_classify_vrp_boundaries():
    assert classify_vrp(5.0)["state"] == "rich"
    assert classify_vrp(4.9)["state"] == "fair"
    assert classify_vrp(-5.0)["state"] == "fair"
    assert classify_vrp(-5.1)["state"] == "cheap"


# ── fetch_and_compute_vrp (fail-open) ───────────────────────────────────

def test_fetch_and_compute_vrp_bad_vix_ticker(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            return pd.DataFrame()

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_vrp()
    assert result["available"] is False
    assert "reason" in result


def test_fetch_and_compute_vrp_spy_fetch_raises(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            raise RuntimeError("network down")

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_vrp(vix_level=18.0)
    assert result["available"] is False
    assert "network down" in result["reason"]


def test_fetch_and_compute_vrp_skips_vix_fetch_when_level_given(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            assert self.symbol == "SPY"  # ^VIX must never be fetched here
            idx = pd.date_range("2026-01-01", periods=30, freq="D")
            closes = np.linspace(100, 110, 30)
            return pd.DataFrame(
                {"Close": closes, "High": closes, "Low": closes, "Volume": [1_000_000] * 30},
                index=idx,
            )

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_vrp(vix_level=20.0)
    assert result["available"] is True
    assert result["vix_level"] == 20.0


# ── history append/dedup + persistence ──────────────────────────────────

def _entry(date, vrp=5.0):
    return {"date": date, "vrp": vrp, "vix_level": 20.0, "realized_vol_20d": 15.0}


def test_append_vrp_dedups_same_date():
    h = [_entry("2026-06-01", 3.0)]
    h = append_vrp(h, _entry("2026-06-01", 8.0))
    assert len(h) == 1
    assert h[0]["vrp"] == 8.0


def test_append_vrp_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_vrp(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_vrp_round_trip(tmp_path):
    p = tmp_path / "vrp_history.json"
    record_vrp(p, _entry("2026-06-01", 3.0))
    record_vrp(p, _entry("2026-06-02", 6.0))
    record_vrp(p, _entry("2026-06-02", 9.0))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["vrp"] == 9.0


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "vrp_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── vrp_trend ────────────────────────────────────────────────────────────

def test_vrp_trend_insufficient_history():
    h = [_entry("2026-06-01", 3.0), _entry("2026-06-02", 6.0)]
    t = vrp_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0.0
    assert t["lookback_date"] is None


def test_vrp_trend_richening():
    h = [_entry(f"2026-06-{d:02d}", 2.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 10.0))
    t = vrp_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "richening"
    assert t["delta"] == 8.0
    assert t["lookback_date"] == "2026-06-01"


def test_vrp_trend_cheapening():
    h = [_entry(f"2026-06-{d:02d}", 10.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 2.0))
    t = vrp_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "cheapening"


def test_vrp_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 5.0) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 6.0))
    t = vrp_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_vrp_text ────────────────────────────────────────────────────

def test_format_vrp_text_available():
    v = compute_vrp(vix_level=25.0, realized_vol=15.0)
    text = format_vrp_text(v)
    assert "VRP" in text
    assert "25.0" in text


def test_format_vrp_text_unavailable():
    text = format_vrp_text({"available": False, "reason": "SPY fetch failed"})
    assert "unavailable" in text
    assert "SPY fetch failed" in text
