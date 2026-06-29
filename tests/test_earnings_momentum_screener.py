"""Tests for dossier/earnings_momentum_screener.py — Earnings Momentum Screener."""

import json
import os
import tempfile
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dossier.earnings_momentum_screener import (
    _adx_score,
    _earnings_days_away,
    _funnel_filter,
    _grade,
    _proximity_score,
    _rsi_score,
    _trend_score,
    _volume_score,
    score_earnings_momentum,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _stock(
    ticker="TEST",
    price=120.0,
    sma_200=100.0,
    sma_50=110.0,
    ema_20=115.0,
    avg_vol_30d=600_000,
    market_cap=2e9,
    rsi=55.0,
    adx=28.0,
    perf_1m=5.0,
) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": 0.8,
        "volume": 700_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap": market_cap,
        "sma_200": sma_200,
        "sma_50": sma_50,
        "ema_20": ema_20,
        "rsi": rsi,
        "adx": adx,
        "perf_1w": 1.5,
        "perf_1m": perf_1m,
        "perf_3m": 8.0,
        "stoch_k": 42.0,
    }


def _fake_hist(n=60, avg_vol=500_000, last_vol=750_000) -> pd.DataFrame:
    """Synthetic 60-day OHLCV with a modest price trend."""
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    close = pd.Series([100.0 + i * 0.3 for i in range(n)], index=idx)
    vols = [avg_vol] * n
    vols[-1] = last_vol
    return pd.DataFrame({
        "Open":   close * 0.995,
        "High":   close * 1.01,
        "Low":    close * 0.99,
        "Close":  close,
        "Volume": pd.Series(vols, index=idx),
    })


def _make_calendar(days_away: int) -> dict:
    """Build a yfinance-style calendar dict with earnings days_away from today."""
    ed = date.today() + timedelta(days=days_away)
    return {"Earnings Date": [ed]}


# ─── _proximity_score ─────────────────────────────────────────────

def test_proximity_score_imminent():
    assert _proximity_score(0) == 35
    assert _proximity_score(1) == 35
    assert _proximity_score(2) == 35


def test_proximity_score_this_week():
    assert _proximity_score(3) == 28
    assert _proximity_score(4) == 28


def test_proximity_score_next_week():
    assert _proximity_score(5) == 18
    assert _proximity_score(6) == 18


def test_proximity_score_at_boundary():
    assert _proximity_score(7) == 10


def test_proximity_score_monotone():
    assert _proximity_score(7) < _proximity_score(5) < _proximity_score(3) < _proximity_score(1)


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_perfect_setup():
    # Price above EMA20 (not extended), above SMA50, SMA50 above SMA200
    pts = _trend_score(115.0, 110.0, 108.0, 100.0)
    assert pts == 25  # 12 + 8 + 5


def test_trend_score_below_ema20():
    # Price below EMA20 but close (−2%) → 6 pts; above SMA50 → 8; SMA50>SMA200 → 5
    pts = _trend_score(107.8, 110.0, 105.0, 100.0)
    assert pts == 6 + 8 + 5


def test_trend_score_extended_above_ema():
    # Price 15% above EMA20 → 0 EMA pts; still above SMA50 → 8; SMA50>SMA200 → 5
    pts = _trend_score(126.5, 110.0, 105.0, 100.0)
    assert pts == 0 + 8 + 5


def test_trend_score_no_ema20():
    # ema_20=None → 0 EMA pts; above SMA50 → 8; SMA50>SMA200 → 5
    pts = _trend_score(115.0, None, 108.0, 100.0)
    assert pts == 0 + 8 + 5


def test_trend_score_no_sma_data():
    pts = _trend_score(115.0, None, None, None)
    assert pts == 0


def test_trend_score_sma50_below_sma200():
    # Golden structure broken → no SMA50-vs-SMA200 bonus
    pts = _trend_score(115.0, 110.0, 95.0, 100.0)
    # Price>EMA20 (within 10%) → 12; Price>SMA50 → 8; SMA50<SMA200 → 0
    assert pts == 12 + 8 + 0


# ─── _rsi_score ───────────────────────────────────────────────────

def test_rsi_score_goldilocks():
    assert _rsi_score(45) == 20
    assert _rsi_score(55) == 20
    assert _rsi_score(65) == 20


def test_rsi_score_slightly_off():
    assert _rsi_score(42) == 13
    assert _rsi_score(68) == 13


def test_rsi_score_edge():
    assert _rsi_score(37) == 6
    assert _rsi_score(73) == 6


def test_rsi_score_extreme():
    assert _rsi_score(20) == 2
    assert _rsi_score(85) == 2


def test_rsi_score_monotone():
    assert _rsi_score(30) < _rsi_score(40) < _rsi_score(55)


# ─── _adx_score ───────────────────────────────────────────────────

def test_adx_score_strong():
    assert _adx_score(35) == 12
    assert _adx_score(50) == 12


def test_adx_score_trending():
    assert _adx_score(25) == 9
    assert _adx_score(30) == 9


def test_adx_score_moderate():
    assert _adx_score(20) == 6
    assert _adx_score(22) == 6


def test_adx_score_weak():
    assert _adx_score(15) == 3
    assert _adx_score(18) == 3


def test_adx_score_none():
    assert _adx_score(0) == 0
    assert _adx_score(10) == 0


def test_adx_score_monotone():
    assert _adx_score(10) < _adx_score(20) < _adx_score(25) < _adx_score(35)


# ─── _volume_score ────────────────────────────────────────────────

def test_volume_score_high():
    assert _volume_score(2.0) == 8
    assert _volume_score(3.0) == 8


def test_volume_score_moderate():
    assert _volume_score(1.5) == 6
    assert _volume_score(1.9) == 6


def test_volume_score_low():
    assert _volume_score(1.2) == 4


def test_volume_score_minimal():
    assert _volume_score(0.8) == 1


def test_volume_score_monotone():
    assert _volume_score(0.5) < _volume_score(1.2) < _volume_score(1.5) < _volume_score(2.0)


# ─── _grade ───────────────────────────────────────────────────────

def test_grade_buckets():
    assert _grade(85) == "A+"
    assert _grade(80) == "A+"
    assert _grade(79) == "A"
    assert _grade(65) == "A"
    assert _grade(64) == "B"
    assert _grade(50) == "B"
    assert _grade(49) == "C"
    assert _grade(35) == "C"
    assert _grade(34) == "D"
    assert _grade(0)  == "D"


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_good_candidate():
    s = _stock()
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=1e8)  # $100M → below $500M floor
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_missing_sma200():
    s = _stock()
    s["sma_200"] = None
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_low_volume():
    s = _stock(avg_vol_30d=100_000)  # below 300k floor
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_parabolic():
    s = _stock(perf_1m=30.0)  # +30% in a month
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_passes_boundary_perf():
    s = _stock(perf_1m=25.0)  # exactly 25% → passes (≤ 25)
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_mixed_batch():
    good  = _stock("GOOD")
    small = _stock("TINY", market_cap=5e7)
    blow  = _stock("BLOW", perf_1m=40.0)
    result = _funnel_filter([good, small, blow], verbose=False)
    assert len(result) == 1
    assert result[0]["ticker"] == "GOOD"


# ─── _earnings_days_away ──────────────────────────────────────────

def test_earnings_days_away_within_window(monkeypatch):
    import yfinance as yf
    mock_ticker = MagicMock()
    mock_ticker.calendar = _make_calendar(days_away=3)
    monkeypatch.setattr(yf, "Ticker", lambda sym: mock_ticker)
    result = _earnings_days_away("TEST", max_days=7)
    assert result == 3


def test_earnings_days_away_outside_window(monkeypatch):
    import yfinance as yf
    mock_ticker = MagicMock()
    mock_ticker.calendar = _make_calendar(days_away=10)
    monkeypatch.setattr(yf, "Ticker", lambda sym: mock_ticker)
    result = _earnings_days_away("TEST", max_days=7)
    assert result is None


def test_earnings_days_away_no_calendar(monkeypatch):
    import yfinance as yf
    mock_ticker = MagicMock()
    mock_ticker.calendar = {}
    monkeypatch.setattr(yf, "Ticker", lambda sym: mock_ticker)
    result = _earnings_days_away("TEST", max_days=7)
    assert result is None


def test_earnings_days_away_exception(monkeypatch):
    import yfinance as yf
    monkeypatch.setattr(yf, "Ticker", lambda sym: (_ for _ in ()).throw(Exception("network error")))
    result = _earnings_days_away("TEST", max_days=7)
    assert result is None


def test_earnings_days_away_exactly_zero(monkeypatch):
    """Earnings today → 0 days away → within window."""
    import yfinance as yf
    mock_ticker = MagicMock()
    mock_ticker.calendar = _make_calendar(days_away=0)
    monkeypatch.setattr(yf, "Ticker", lambda sym: mock_ticker)
    result = _earnings_days_away("TEST", max_days=7)
    assert result == 0


# ─── score_earnings_momentum (integration) ───────────────────────

def test_score_returns_result_on_qualifying_setup(monkeypatch):
    """Earnings in 3 days + good hist → non-None scored result."""
    import yfinance as yf

    hist = _fake_hist(n=60)

    class _FakeTicker:
        calendar = _make_calendar(days_away=3)

        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock("NVDA", rsi=55.0, adx=30.0)
    result = score_earnings_momentum("NVDA", tv_data=tv, max_days=7)

    assert result is not None
    assert result["days_until_earnings"] == 3
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    assert "score_breakdown" in result
    for key in ("proximity", "trend", "rsi", "adx", "volume"):
        assert key in result["score_breakdown"]


def test_score_returns_none_when_no_upcoming_earnings(monkeypatch):
    """Earnings 30 days away → rejected."""
    import yfinance as yf

    class _FakeTicker:
        calendar = _make_calendar(days_away=30)

        def history(self, **kwargs):
            return _fake_hist()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_earnings_momentum("FAR", max_days=7) is None


def test_score_returns_none_on_empty_history(monkeypatch):
    """Earnings within window but history unavailable → rejected."""
    import yfinance as yf

    class _FakeTicker:
        calendar = _make_calendar(days_away=2)

        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_earnings_momentum("EMPTY", max_days=7) is None


def test_score_returns_none_on_short_history(monkeypatch):
    """Only 5 bars of history — below 20-row minimum."""
    import yfinance as yf

    class _FakeTicker:
        calendar = _make_calendar(days_away=2)

        def history(self, **kwargs):
            return _fake_hist(n=5)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_earnings_momentum("SHORT", max_days=7) is None


def test_score_proximity_reflected_in_breakdown(monkeypatch):
    """Days-away of 1 → proximity component should be 35."""
    import yfinance as yf

    class _FakeTicker:
        calendar = _make_calendar(days_away=1)

        def history(self, **kwargs):
            return _fake_hist(n=60)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_earnings_momentum("SOON", tv_data=_stock("SOON"), max_days=7)
    assert result is not None
    assert result["score_breakdown"]["proximity"] == 35


def test_score_tv_data_name_propagated(monkeypatch):
    """tv_data['name'] should appear in the result."""
    import yfinance as yf

    class _FakeTicker:
        calendar = _make_calendar(days_away=4)

        def history(self, **kwargs):
            return _fake_hist(n=60)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    tv = _stock("AAPL")
    tv["name"] = "Apple Inc."
    result = score_earnings_momentum("AAPL", tv_data=tv, max_days=7)
    if result is not None:
        assert result["name"] == "Apple Inc."
