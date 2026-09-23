"""
Tests for dossier/distribution_days.py — the IBD-style Distribution/
Accumulation Day count.

Covers:
  1. count_session_days (per-index session classification from OHLCV)
  2. compute_distribution_days aggregation across indexes (worst-index logic)
  3. classify_pressure state boundaries
  4. fetch_and_compute_distribution_days fail-open behavior on bad/missing data
  5. history append/dedup + round-trip persistence (same pattern as vol_risk_premium)
  6. distribution_trend delta vs N sessions back
  7. format_distribution_days_text summary line
"""

import json

import pandas as pd
import pytest

from dossier.distribution_days import (
    append_distribution_days,
    classify_pressure,
    compute_distribution_days,
    count_session_days,
    distribution_trend,
    fetch_and_compute_distribution_days,
    format_distribution_days_text,
    load_history,
    record_distribution_days,
    save_history,
)


def _hist(closes, volumes):
    idx = pd.date_range("2026-01-01", periods=len(closes), freq="D")
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


# ── count_session_days ──────────────────────────────────────────────────

def test_count_session_days_none_input():
    result = count_session_days(None)
    assert result == {
        "distribution_days": 0, "accumulation_days": 0,
        "sessions_counted": 0, "distribution_dates": [],
    }


def test_count_session_days_empty_df():
    assert count_session_days(pd.DataFrame())["sessions_counted"] == 0


def test_count_session_days_missing_columns():
    assert count_session_days(pd.DataFrame({"Open": [1, 2, 3]}))["sessions_counted"] == 0


def test_count_session_days_single_row_insufficient():
    assert count_session_days(_hist([100.0], [1_000_000]))["sessions_counted"] == 0


def test_count_session_days_classic_distribution_day():
    # Day 1 -> Day 2: down 1% on higher volume = distribution.
    hist = _hist([100.0, 99.0], [1_000_000, 1_500_000])
    result = count_session_days(hist)
    assert result["distribution_days"] == 1
    assert result["accumulation_days"] == 0
    assert result["sessions_counted"] == 1
    assert len(result["distribution_dates"]) == 1


def test_count_session_days_classic_accumulation_day():
    # Up 1% on higher volume = accumulation.
    hist = _hist([100.0, 101.0], [1_000_000, 1_500_000])
    result = count_session_days(hist)
    assert result["accumulation_days"] == 1
    assert result["distribution_days"] == 0


def test_count_session_days_down_on_lower_volume_is_neutral():
    # Down big, but on LOWER volume — not a distribution day.
    hist = _hist([100.0, 98.0], [1_000_000, 800_000])
    result = count_session_days(hist)
    assert result["distribution_days"] == 0
    assert result["accumulation_days"] == 0
    assert result["sessions_counted"] == 1


def test_count_session_days_small_move_below_threshold_is_neutral():
    # Down 0.1%, below the 0.2% threshold, even on higher volume.
    hist = _hist([100.0, 99.9], [1_000_000, 2_000_000])
    result = count_session_days(hist)
    assert result["distribution_days"] == 0
    assert result["accumulation_days"] == 0


def test_count_session_days_respects_window():
    # 30 sessions, alternating distribution days; window=25 should only
    # count the trailing 25.
    closes = []
    vols = []
    price = 100.0
    for i in range(31):
        if i % 2 == 1:
            price *= 0.99
        closes.append(price)
        vols.append(2_000_000 if i % 2 == 1 else 1_000_000)
    hist = _hist(closes, vols)
    result = count_session_days(hist, window=25)
    assert result["sessions_counted"] == 25


def test_count_session_days_nan_row_skipped():
    hist = _hist([100.0, float("nan"), 99.0], [1_000_000, 1_200_000, 1_500_000])
    result = count_session_days(hist)
    # First transition (100 -> nan) skipped; second (nan -> 99) also skipped.
    assert result["sessions_counted"] == 0


# ── classify_pressure ────────────────────────────────────────────────────

def test_classify_pressure_boundaries():
    assert classify_pressure(0)["state"] == "healthy"
    assert classify_pressure(2)["state"] == "healthy"
    assert classify_pressure(3)["state"] == "caution"
    assert classify_pressure(4)["state"] == "caution"
    assert classify_pressure(5)["state"] == "pressure"
    assert classify_pressure(10)["state"] == "pressure"


# ── compute_distribution_days ────────────────────────────────────────────

def test_compute_distribution_days_empty_input():
    result = compute_distribution_days({})
    assert result["worst_index"] is None
    assert result["distribution_days"] == 0
    assert result["state"] == "healthy"


def test_compute_distribution_days_picks_worst_index():
    spy_hist = _hist([100.0, 99.0], [1_000_000, 1_500_000])  # 1 distribution day
    qqq_hist = _hist([100.0] * 3, [1_000_000] * 3)  # 0 distribution days
    result = compute_distribution_days({"SPY": spy_hist, "QQQ": qqq_hist})
    assert result["worst_index"] == "SPY"
    assert result["distribution_days"] == 1
    assert "per_index" in result
    assert set(result["per_index"]) == {"SPY", "QQQ"}


# ── fetch_and_compute_distribution_days (fail-open) ──────────────────────

def test_fetch_and_compute_distribution_days_all_fetches_fail(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            raise RuntimeError("network down")

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_distribution_days()
    assert result["available"] is False
    assert "reason" in result


def test_fetch_and_compute_distribution_days_empty_history(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            return pd.DataFrame()

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_distribution_days()
    assert result["available"] is False


def test_fetch_and_compute_distribution_days_success(monkeypatch):
    class _FakeTicker:
        def __init__(self, symbol):
            self.symbol = symbol

        def history(self, period=None):
            idx = pd.date_range("2026-01-01", periods=30, freq="D")
            closes = [100.0 + (i % 3) for i in range(30)]
            vols = [1_000_000 + i * 1000 for i in range(30)]
            return pd.DataFrame({"Close": closes, "High": closes, "Low": closes, "Volume": vols}, index=idx)

    monkeypatch.setattr("yfinance.Ticker", _FakeTicker)
    result = fetch_and_compute_distribution_days()
    assert result["available"] is True
    assert "distribution_days" in result
    assert set(result["per_index"]) == {"SPY", "QQQ"}


# ── history append/dedup + persistence ───────────────────────────────────

def _entry(date, distribution_days=1, accumulation_days=0):
    return {"date": date, "distribution_days": distribution_days, "accumulation_days": accumulation_days}


def test_append_distribution_days_dedups_same_date():
    h = [_entry("2026-06-01", 3)]
    h = append_distribution_days(h, _entry("2026-06-01", 8))
    assert len(h) == 1
    assert h[0]["distribution_days"] == 8


def test_append_distribution_days_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_distribution_days(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_distribution_days_round_trip(tmp_path):
    p = tmp_path / "distribution_days_history.json"
    record_distribution_days(p, _entry("2026-06-01", 2))
    record_distribution_days(p, _entry("2026-06-02", 4))
    record_distribution_days(p, _entry("2026-06-02", 6))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["distribution_days"] == 6


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "distribution_days_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── distribution_trend ────────────────────────────────────────────────────

def test_distribution_trend_insufficient_history():
    h = [_entry("2026-06-01", 1), _entry("2026-06-02", 2)]
    t = distribution_trend(h, "2026-06-02", lookback=5)
    assert t["direction"] == "flat"
    assert t["delta"] == 0
    assert t["lookback_date"] is None


def test_distribution_trend_building():
    h = [_entry(f"2026-06-{d:02d}", 1) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 5))
    t = distribution_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "building"
    assert t["delta"] == 4
    assert t["lookback_date"] == "2026-06-01"


def test_distribution_trend_clearing():
    h = [_entry(f"2026-06-{d:02d}", 6) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 1))
    t = distribution_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "clearing"


def test_distribution_trend_flat_small_delta():
    h = [_entry(f"2026-06-{d:02d}", 3) for d in range(1, 6)]
    h.append(_entry("2026-06-06", 4))
    t = distribution_trend(h, "2026-06-06", lookback=5)
    assert t["direction"] == "flat"


# ── format_distribution_days_text ────────────────────────────────────────

def test_format_distribution_days_text_available():
    data = {
        "available": True, "distribution_days": 3, "accumulation_days": 1,
        "worst_index": "SPY", **classify_pressure(3),
    }
    text = format_distribution_days_text(data)
    assert "Distribution Days" in text
    assert "3 distribution" in text
    assert "SPY" in text


def test_format_distribution_days_text_unavailable():
    text = format_distribution_days_text({"available": False, "reason": "SPY fetch failed"})
    assert "unavailable" in text
    assert "SPY fetch failed" in text
