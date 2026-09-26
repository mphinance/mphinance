"""Tests for dossier/macd_cross_screener.py — MACD Bullish Crossover Screener."""

import numpy as np
import pandas as pd
import pytest

from dossier.macd_cross_screener import (
    _compute_macd,
    _days_since_bullish_cross,
    _freshness_score,
    _funnel_filter,
    _hist_strength_score,
    _trend_ctx_score,
    _volume_confirm_score,
    score_macd_cross,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _stock(
    ticker="TEST",
    price=50.0,
    sma_50=48.0,
    sma_200=44.0,
    avg_vol_30d=500_000,
    rsi=60,
    market_cap=2e9,
    perf_1w=5.0,
    macd=0.5,
    macd_signal=0.2,
) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": 1.5,
        "volume": 600_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap": market_cap,
        "sma_200": sma_200,
        "sma_50": sma_50,
        "rsi": rsi,
        "perf_1w": perf_1w,
        "perf_1m": 8.0,
        "macd": macd,
        "macd_signal": macd_signal,
    }


def _cross_series(flat_days=80, up_days=20, cross_days_ago=2):
    """
    Builds a synthetic close-price series that is flat/declining for
    `flat_days`, then ramps up for `up_days`, producing a genuine MACD
    bullish crossover a controllable number of sessions before the end.
    """
    idx = pd.date_range("2024-01-01", periods=flat_days + up_days, freq="B")
    flat = [100.0 - 0.05 * i for i in range(flat_days)]
    ramp_start = flat[-1]
    ramp = [ramp_start * (1 + 0.02) ** i for i in range(1, up_days + 1)]
    close = pd.Series(flat + ramp, index=idx)

    macd, signal = _compute_macd(close)
    # Trim the series so the crossover lands `cross_days_ago` sessions
    # before the final bar (searches forward from the ramp for the cross).
    diff = macd - signal
    cross_i = None
    for i in range(1, len(diff)):
        if diff.iloc[i] > 0 and diff.iloc[i - 1] <= 0:
            cross_i = i
            break
    assert cross_i is not None, "synthetic series failed to produce a crossover"
    end_i = cross_i + cross_days_ago
    close = close.iloc[: end_i + 1]

    high = close * 1.01
    low = close * 0.99
    opens = close * 0.995
    volume = pd.Series([1_000_000] * len(close), index=close.index)
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


# ─── _compute_macd ────────────────────────────────────────────────

def test_compute_macd_returns_two_series():
    close = pd.Series(np.linspace(100, 120, 100))
    macd, signal = _compute_macd(close)
    assert len(macd) == len(close)
    assert len(signal) == len(close)


# ─── _days_since_bullish_cross ────────────────────────────────────

def test_days_since_cross_today():
    macd = pd.Series([-1.0, -0.5, 0.2])
    signal = pd.Series([0.0, 0.0, 0.0])
    assert _days_since_bullish_cross(macd, signal) == 0


def test_days_since_cross_two_days_ago():
    macd = pd.Series([-1.0, 0.3, 0.4, 0.5])
    signal = pd.Series([0.0, 0.0, 0.0, 0.0])
    assert _days_since_bullish_cross(macd, signal) == 2


def test_days_since_cross_not_currently_bullish():
    macd = pd.Series([0.5, -0.2])
    signal = pd.Series([0.0, 0.0])
    assert _days_since_bullish_cross(macd, signal) is None


def test_days_since_cross_stale_outside_lookback():
    # Cross happened 10 bars ago — outside the default 5-day lookback
    macd = pd.Series([-1.0] + [0.5] * 10)
    signal = pd.Series([0.0] * 11)
    assert _days_since_bullish_cross(macd, signal, max_lookback=5) is None


def test_days_since_cross_short_series():
    assert _days_since_bullish_cross(pd.Series([0.5]), pd.Series([0.0])) is None


# ─── _freshness_score ─────────────────────────────────────────────

def test_freshness_score_today():
    assert _freshness_score(0) == 35


def test_freshness_score_stale_edge():
    assert _freshness_score(5) == 3


def test_freshness_score_monotone():
    assert (
        _freshness_score(5)
        < _freshness_score(3)
        < _freshness_score(1)
        < _freshness_score(0)
    )


# ─── _hist_strength_score ─────────────────────────────────────────

def test_hist_strength_score_strong():
    assert _hist_strength_score(60.0) == 25


def test_hist_strength_score_weak():
    assert _hist_strength_score(1.0) == 2


def test_hist_strength_score_monotone():
    assert (
        _hist_strength_score(1.0)
        < _hist_strength_score(5.0)
        < _hist_strength_score(15.0)
        < _hist_strength_score(60.0)
    )


# ─── _trend_ctx_score ─────────────────────────────────────────────

def test_trend_ctx_full_stack():
    assert _trend_ctx_score(100.0, 90.0, 80.0) == 25


def test_trend_ctx_above_sma50_only():
    assert _trend_ctx_score(100.0, 90.0, 110.0) == 10


def test_trend_ctx_below_all():
    assert _trend_ctx_score(80.0, 90.0, 95.0) == 0


def test_trend_ctx_missing_sma200():
    assert _trend_ctx_score(100.0, 90.0, None) == 10


# ─── _volume_confirm_score ────────────────────────────────────────

def test_volume_confirm_strong():
    assert _volume_confirm_score(2.0) == 15


def test_volume_confirm_mild():
    assert _volume_confirm_score(1.05) == 5


def test_volume_confirm_none():
    assert _volume_confirm_score(0.5) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_candidate():
    s = _stock(market_cap=2e9, avg_vol_30d=500_000, rsi=60, perf_1w=5.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=5e7)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_low_liquidity():
    s = _stock(avg_vol_30d=10_000)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought():
    s = _stock(rsi=85)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_parabolic():
    s = _stock(perf_1w=35.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


# ─── score_macd_cross (full pipeline via monkeypatch) ─────────────

def test_score_macd_cross_fresh_qualifies(monkeypatch):
    """A genuine fresh crossover with trend context should score and grade."""
    import yfinance as yf

    hist = _cross_series(cross_days_ago=1)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_macd_cross("TEST")
    assert result is not None
    assert result["days_since_cross"] == 1
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_macd_cross_no_cross_returns_none(monkeypatch):
    """A flat/declining series with no crossover should return None."""
    import yfinance as yf

    idx = pd.date_range("2024-01-01", periods=120, freq="B")
    close = pd.Series([100.0 - 0.1 * i for i in range(120)], index=idx)
    hist = pd.DataFrame({
        "Open": close * 0.995,
        "High": close * 1.01,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000_000] * 120, index=idx),
    })

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_macd_cross("NOCROSS")
    assert result is None


def test_score_macd_cross_short_history_returns_none(monkeypatch):
    """Insufficient history (< 60 bars) → return None without raising."""
    import yfinance as yf

    idx = pd.date_range("2024-01-01", periods=30, freq="B")
    close = pd.Series([100.0] * 30, index=idx)
    hist = pd.DataFrame({
        "Open": close, "High": close, "Low": close, "Close": close,
        "Volume": pd.Series([1_000_000] * 30, index=idx),
    })

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_macd_cross("SHORT")
    assert result is None


def test_score_macd_cross_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_macd_cross("EMPTY")
    assert result is None


def test_score_macd_cross_score_breakdown_keys(monkeypatch):
    """score_breakdown must contain all four expected keys."""
    import yfinance as yf

    hist = _cross_series(cross_days_ago=0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_macd_cross("BREAKDOWN")
    assert result is not None
    for key in ("freshness", "histogram", "trend", "volume"):
        assert key in result["score_breakdown"]
