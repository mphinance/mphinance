"""Tests for dossier/capitulation_screener.py — Capitulation Reversal Screener."""

import pandas as pd
import pytest

from dossier.capitulation_screener import (
    _funnel_filter,
    _oversold_score,
    _reversal_candle_score,
    _stabilization_score,
    _volume_climax_score,
    score_capitulation,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _hammer_hist(n=40, price=50.0, decline_pct=-20.0, last_vol_ratio=3.0):
    """
    Synthetic OHLCV: a steady decline over `n` bars, ending in a
    hammer reversal candle (close near the day's high) with a
    volume spike on the final bar.
    """
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    start = price * (1 - decline_pct / 100)
    closes = [start + (price - start) * (i / (n - 1)) for i in range(n)]
    closes[-1] = price

    highs, lows, opens, vols = [], [], [], []
    for i, c in enumerate(closes):
        if i == n - 1:
            lows.append(c * 0.94)
            highs.append(c * 1.005)
            opens.append(c * 0.95)
            vols.append(1_000_000 * last_vol_ratio)
        else:
            r = c * 0.02
            highs.append(c + r / 2)
            lows.append(c - r / 2)
            opens.append(c + r * 0.1)
            vols.append(1_000_000)

    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
        index=idx,
    )


def _flat_decline_hist(n=40, price=50.0):
    """Steady decline that keeps declining at a constant pace (no stabilization)."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    closes = [price * (1.3 - 0.3 * i / (n - 1)) for i in range(n)]
    r = price * 0.02
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c + r / 2 for c in closes],
            "Low": [c - r / 2 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _stock(ticker="TEST", price=50.0, rsi=25, low_52w=48.0, market_cap=2e9, perf_1m=-25.0):
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "avg_vol_30d": 500_000,
        "market_cap": market_cap,
        "rsi": rsi,
        "perf_1m": perf_1m,
        "low_52w": low_52w,
    }


# ─── _oversold_score ────────────────────────────────────────────────

def test_oversold_score_deep_washout_scores_high():
    assert _oversold_score(rsi=18, pct_from_low=3.0) == 30


def test_oversold_score_mild_and_far_scores_low():
    assert _oversold_score(rsi=45, pct_from_low=30.0) == 0


def test_oversold_score_missing_rsi_gets_partial_credit():
    score = _oversold_score(rsi=None, pct_from_low=3.0)
    assert score == 20  # 10 (unknown RSI) + 10 (near the low)


# ─── _reversal_candle_score ─────────────────────────────────────────

def test_reversal_candle_hammer_green_scores_max():
    hist = pd.DataFrame({
        "Open": [95.0], "High": [101.0], "Low": [90.0], "Close": [100.0],
    })
    assert _reversal_candle_score(hist) == 25


def test_reversal_candle_red_close_near_low_scores_zero():
    hist = pd.DataFrame({
        "Open": [100.0], "High": [101.0], "Low": [90.0], "Close": [90.5],
    })
    assert _reversal_candle_score(hist) == 0


def test_reversal_candle_zero_range_returns_zero():
    hist = pd.DataFrame({"Open": [100.0], "High": [100.0], "Low": [100.0], "Close": [100.0]})
    assert _reversal_candle_score(hist) == 0


# ─── _volume_climax_score ────────────────────────────────────────────

def test_volume_climax_spike_scores_high():
    hist = _hammer_hist(last_vol_ratio=3.5)
    assert _volume_climax_score(hist) == 25


def test_volume_climax_average_volume_scores_low():
    hist = _hammer_hist(last_vol_ratio=1.0)
    assert _volume_climax_score(hist) <= 6


def test_volume_climax_short_history_returns_zero():
    hist = pd.DataFrame({"Volume": [1_000_000] * 10})
    assert _volume_climax_score(hist) == 0


# ─── _stabilization_score ────────────────────────────────────────────

def test_stabilization_flattening_tail_scores_above_zero():
    # Steep decline for the first 35 bars, then the last 5 bars go flat/up —
    # the 5-day pace is far better than the 20-day trailing pace implies.
    idx = pd.date_range("2024-01-01", periods=40, freq="B")
    closes = [70.0 - i * 0.5 for i in range(35)] + [52.5, 52.7, 53.0, 53.2, 53.5]
    hist = pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * 40,
        },
        index=idx,
    )
    assert _stabilization_score(hist) > 0


def test_stabilization_constant_decline_scores_zero():
    hist = _flat_decline_hist(n=40, price=50.0)
    assert _stabilization_score(hist) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_filter_keeps_near_low_liquid_stock():
    stocks = [_stock(ticker="KEEP", price=50.0, low_52w=48.0, market_cap=2e9)]
    survivors = _funnel_filter(stocks, verbose=False)
    assert len(survivors) == 1
    assert survivors[0]["ticker"] == "KEEP"


def test_funnel_filter_drops_small_cap():
    stocks = [_stock(ticker="TINY", market_cap=1e7)]
    assert _funnel_filter(stocks, verbose=False) == []


def test_funnel_filter_drops_stock_far_from_low():
    stocks = [_stock(ticker="FAR", price=80.0, low_52w=48.0)]
    assert _funnel_filter(stocks, verbose=False) == []


# ─── score_capitulation (full pipeline via monkeypatch) ─────────────

def test_score_capitulation_washout_qualifies(monkeypatch):
    import yfinance as yf

    hist = _hammer_hist(n=40, price=50.0, decline_pct=-25.0, last_vol_ratio=3.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    tv = _stock(price=last_close, rsi=22, low_52w=last_close * 0.97, perf_1m=-25.0)
    result = score_capitulation("WASH", tv_data=tv)

    assert result is not None
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    assert set(result["score_breakdown"]) == {
        "oversold_depth", "reversal_candle", "volume_climax", "decline_deceleration",
    }


def test_score_capitulation_far_from_low_returns_none(monkeypatch):
    import yfinance as yf

    hist = _hammer_hist(n=40, price=100.0, decline_pct=-5.0, last_vol_ratio=1.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(price=100.0, low_52w=50.0)  # 100% above the low
    assert score_capitulation("FAR", tv_data=tv) is None


def test_score_capitulation_empty_history_returns_none(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_capitulation("EMPTY") is None
