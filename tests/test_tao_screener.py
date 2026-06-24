"""Tests for dossier/tao_screener.py — TAO Pullback Screener helpers."""

import math
import numpy as np
import pandas as pd
import pytest

from dossier.tao_screener import _ema, _atr, _adx, _funnel_filter


# ─── Synthetic OHLCV data ─────────────────────────────────────────

def _make_ohlcv(n: int = 200, trend: float = 0.005) -> pd.DataFrame:
    """
    Build a synthetic OHLCV DataFrame with a smooth uptrend.
    close[i] = 100 * (1 + trend)^i, with ATR-consistent high/low.
    """
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    high = close * 1.01
    low = close * 0.99
    opens = close * 0.995
    volume = pd.Series([1_000_000] * n, index=idx)
    return pd.DataFrame({"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume})


# ─── _ema ─────────────────────────────────────────────────────────

def test_ema_returns_series():
    prices = pd.Series([float(i) for i in range(1, 21)])
    result = _ema(prices, 5)
    assert isinstance(result, pd.Series)
    assert len(result) == 20


def test_ema_span1_equals_original():
    prices = pd.Series([10.0, 12.0, 11.0, 13.0])
    result = _ema(prices, 1)
    pd.testing.assert_series_equal(result, prices)


def test_ema_monotone_rising_series():
    # EMA of a strictly rising series should itself be rising
    prices = pd.Series([float(i) for i in range(1, 30)])
    result = _ema(prices, 8)
    diffs = result.diff().dropna()
    assert (diffs > 0).all()


def test_ema_fast_above_slow_in_uptrend():
    # In a clear uptrend, EMA(8) should end above EMA(89)
    df = _make_ohlcv(250, trend=0.003)
    e8  = _ema(df["Close"], 8).iloc[-1]
    e89 = _ema(df["Close"], 89).iloc[-1]
    assert e8 > e89, "EMA8 should be above EMA89 in a sustained uptrend"


# ─── _atr ─────────────────────────────────────────────────────────

def test_atr_returns_positive():
    df = _make_ohlcv(100)
    atr = _atr(df, period=14)
    assert float(atr.iloc[-1]) > 0


def test_atr_volatile_market_has_higher_atr():
    calm = _make_ohlcv(150, trend=0.001)
    # Create volatile version with wider H-L range
    volatile = calm.copy()
    volatile["High"] = volatile["Close"] * 1.05
    volatile["Low"]  = volatile["Close"] * 0.95
    assert float(_atr(volatile, 14).iloc[-1]) > float(_atr(calm, 14).iloc[-1])


def test_atr_series_length_matches_input():
    df = _make_ohlcv(80)
    atr = _atr(df, period=14)
    assert len(atr) == 80


# ─── _adx ─────────────────────────────────────────────────────────

def test_adx_in_valid_range():
    df = _make_ohlcv(200)
    adx = _adx(df)
    assert 0 <= adx <= 100


def test_adx_higher_in_trend_than_chop():
    # A directional trend should produce higher ADX than a choppy range
    trending = _make_ohlcv(200, trend=0.005)
    # Choppy: alternating up/down each bar
    idx = pd.date_range("2022-01-01", periods=200, freq="B")
    chop_close = pd.Series([100.0 + (i % 2) * 0.5 for i in range(200)], index=idx)
    chop = pd.DataFrame({
        "Open": chop_close * 0.999,
        "High": chop_close * 1.005,
        "Low": chop_close * 0.995,
        "Close": chop_close,
        "Volume": pd.Series([1_000_000] * 200, index=idx),
    })
    adx_trend = _adx(trending)
    adx_chop = _adx(chop)
    assert adx_trend > adx_chop, f"trending ADX {adx_trend:.1f} should beat choppy {adx_chop:.1f}"


# ─── _funnel_filter ───────────────────────────────────────────────

def _tv(ticker, price, ema_20, rsi, adx, cap=1e9, avg_vol=5e5, perf_1w=0):
    """Helper to build a minimal TV stock dict for funnel tests."""
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "ema_20": ema_20,
        "rsi": rsi,
        "adx": adx,
        "market_cap": cap,
        "avg_vol_30d": avg_vol,
        "perf_1w": perf_1w,
        "change_pct": 0,
        "sma_200": price * 0.85,
        "sma_50": price * 0.92,
    }


def test_funnel_passes_healthy_pullback():
    stock = _tv("GOOD", price=52.0, ema_20=50.0, rsi=48, adx=28)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_extended_price():
    # Price 15% above EMA20 — too extended for a pullback
    stock = _tv("EXT", price=57.5, ema_20=50.0, rsi=70, adx=28)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_price_below_ema():
    # Price below EMA20 — trend broken, not a pullback
    stock = _tv("BREAK", price=47.0, ema_20=50.0, rsi=38, adx=22)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought_rsi():
    # RSI 72 — not a pullback, it's still running
    stock = _tv("HOT", price=51.5, ema_20=50.0, rsi=72, adx=30)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_oversold_rsi():
    # RSI 28 — too washed out, something is broken
    stock = _tv("CRASH", price=50.5, ema_20=50.0, rsi=28, adx=35)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_small_cap():
    # Market cap $100M — below $500M floor
    stock = _tv("MICRO", price=10.0, ema_20=9.8, rsi=50, adx=25, cap=1e8)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_low_volume():
    # avg vol 50K — below 300K floor
    stock = _tv("ILIQ", price=20.0, ema_20=19.5, rsi=50, adx=25, avg_vol=50_000)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_blow_off_weekly():
    # +20% weekly move — blow-off territory
    stock = _tv("MEME", price=55.0, ema_20=52.0, rsi=55, adx=40, perf_1w=22)
    result = _funnel_filter([stock], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    result = _funnel_filter([], verbose=False)
    assert result == []


def test_funnel_preserves_multiple_healthy():
    stocks = [
        _tv("AAA", price=51.0, ema_20=50.0, rsi=45, adx=30),
        _tv("BBB", price=102.5, ema_20=100.0, rsi=52, adx=28),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── Full TAO stack check via synthetic yfinance data ─────────────

def test_score_tao_full_stack(monkeypatch):
    """
    Monkeypatch yfinance so score_tao() receives clean uptrend data
    and must return a non-None result with a full EMA stack.
    """
    import yfinance as yf
    from dossier import tao_screener

    df = _make_ohlcv(500, trend=0.004)   # 500 bars of smooth uptrend

    class _FakeTicker:
        def history(self, **kwargs):
            return df

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = tao_screener.score_tao("TEST")
    assert result is not None, "Should find a TAO setup in a clean uptrend"
    assert result["ema_stack"] == 4, "Full stack expected in sustained uptrend"
    assert result["full_stack"] is True
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_tao_broken_trend_returns_none(monkeypatch):
    """
    A downtrend should produce a broken EMA stack and return None.
    """
    import yfinance as yf
    from dossier import tao_screener

    df = _make_ohlcv(300, trend=-0.004)  # Downtrend

    class _FakeTicker:
        def history(self, **kwargs):
            return df

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = tao_screener.score_tao("DOWN")
    assert result is None, "Downtrend should not qualify as a TAO pullback"


def test_score_tao_short_history_returns_none(monkeypatch):
    """Insufficient history → score_tao must return None, not crash."""
    import yfinance as yf
    from dossier import tao_screener

    df = _make_ohlcv(30, trend=0.003)   # Only 30 bars — below min_rows=150

    class _FakeTicker:
        def history(self, **kwargs):
            return df

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = tao_screener.score_tao("SHORT")
    assert result is None


def test_score_tao_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → must return None without raising."""
    import yfinance as yf
    from dossier import tao_screener

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = tao_screener.score_tao("EMPTY")
    assert result is None
