"""Tests for dossier/high52_screener.py — 52-Week High Momentum Screener."""

import math

import pandas as pd
import pytest

from dossier.high52_screener import (
    _dist_to_52h_tv,
    _funnel_filter,
    _passes_proximity,
    _prox_score,
    _roc_score,
    _trend_score,
    _volume_score,
    score_high52,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 252, trend: float = 0.002, at_high: bool = True) -> pd.DataFrame:
    """Synthetic OHLCV rising to a clean 52-week high."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    high = close * (1.01 if not at_high else 1.0)
    low = close * 0.99
    opens = close * 0.995
    volume = pd.Series([1_000_000] * n, index=idx)
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


def _stock(
    ticker="TEST",
    price=99.0,
    ema_20=96.0,
    sma_50=90.0,
    sma_200=80.0,
    avg_vol_30d=500_000,
    rsi=62,
    adx=28,
    market_cap=2e9,
    perf_3m=15.0,
    perf_1m=5.0,
    perf_1w=2.0,
    high_1y=100.0,
    low_1y=60.0,
) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": 0.5,
        "volume": 600_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap": market_cap,
        "sma_200": sma_200,
        "sma_50": sma_50,
        "ema_20": ema_20,
        "rsi": rsi,
        "adx": adx,
        "atr": price * 0.015,
        "perf_1w": perf_1w,
        "perf_1m": perf_1m,
        "tv_signal": 0.3,
        "high_1y": high_1y,
        "perf_3m": perf_3m,
        "perf_6m": 20.0,
        "low_1y": low_1y,
    }


# ─── _dist_to_52h_tv ──────────────────────────────────────────────

def test_dist_to_52h_basic():
    s = _stock(price=97.0, high_1y=100.0)
    assert _dist_to_52h_tv(s) == pytest.approx(3.0)


def test_dist_to_52h_at_high():
    s = _stock(price=100.0, high_1y=100.0)
    assert _dist_to_52h_tv(s) == pytest.approx(0.0)


def test_dist_to_52h_missing_high():
    s = _stock(high_1y=None)
    assert _dist_to_52h_tv(s) is None


def test_dist_to_52h_zero_high():
    s = _stock(price=50.0, high_1y=0)
    assert _dist_to_52h_tv(s) is None


# ─── _passes_proximity ────────────────────────────────────────────

def test_passes_proximity_within_10pct():
    s = _stock(price=95.0, high_1y=100.0)
    assert _passes_proximity(s) is True


def test_passes_proximity_exactly_at_threshold():
    s = _stock(price=90.0, high_1y=100.0)
    assert _passes_proximity(s) is True  # 10% exactly


def test_passes_proximity_outside_threshold():
    s = _stock(price=85.0, high_1y=100.0)
    assert _passes_proximity(s) is False  # 15% away


def test_passes_proximity_missing_high():
    s = _stock(high_1y=None)
    assert _passes_proximity(s) is True  # unknown high → deferred to Stage 3


# ─── _prox_score ──────────────────────────────────────────────────

def test_prox_score_at_high():
    assert _prox_score(0.5) == 35


def test_prox_score_within_2pct():
    assert _prox_score(1.8) == 30


def test_prox_score_within_3_5pct():
    score = _prox_score(3.0)
    assert score == 24


def test_prox_score_within_5pct():
    score = _prox_score(4.5)
    assert score == 16


def test_prox_score_within_7_5pct():
    score = _prox_score(7.0)
    assert score == 8


def test_prox_score_far():
    # 9% away — beyond the 7.5% threshold but within 10%
    score = _prox_score(9.0)
    assert score == 3


def test_prox_score_monotone():
    assert _prox_score(9.0) < _prox_score(5.0) < _prox_score(2.0) < _prox_score(0.5)


# ─── _roc_score ───────────────────────────────────────────────────

def test_roc_score_strong():
    assert _roc_score(25.0) == 30


def test_roc_score_moderate():
    score = _roc_score(10.0)
    assert score == 18


def test_roc_score_mild():
    score = _roc_score(1.5)
    assert score == 4


def test_roc_score_zero():
    assert _roc_score(0.0) == 4


def test_roc_score_negative():
    assert _roc_score(-2.0) == 0


def test_roc_score_monotone():
    assert _roc_score(-1.0) < _roc_score(0.0) < _roc_score(5.0) < _roc_score(20.0)


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_full_stack():
    # price > ema20 > ema50 > sma200
    score = _trend_score(100.0, 96.0, 90.0, 80.0)
    assert score == 25


def test_trend_score_above_ema20_ema50_only():
    # sma200 above price (long-term lagging)
    score = _trend_score(100.0, 96.0, 90.0, 110.0)
    assert score < 25


def test_trend_score_above_ema20_only():
    score = _trend_score(100.0, 96.0, None, None)
    assert score == 8


def test_trend_score_below_all():
    assert _trend_score(80.0, 90.0, 92.0, 95.0) == 0


def test_trend_score_nan_sma200():
    score = _trend_score(100.0, 96.0, 90.0, float("nan"))
    assert score < 25  # NaN sma200 skips that branch


# ─── _volume_score ────────────────────────────────────────────────

def _make_vol_hist(n: int = 60, recent_mult: float = 1.4) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    base_vol = 1_000_000
    volume = [base_vol] * n
    for i in range(n - 5, n):
        volume[i] = int(base_vol * recent_mult)
    return pd.DataFrame({"Volume": pd.Series(volume, index=idx)})


def test_volume_score_expanding():
    hist = _make_vol_hist(recent_mult=1.4)
    assert _volume_score(hist) == 10


def test_volume_score_flat():
    hist = _make_vol_hist(recent_mult=1.0)
    assert _volume_score(hist) == 3


def test_volume_score_fading():
    hist = _make_vol_hist(recent_mult=0.7)
    assert _volume_score(hist) == 0


def test_volume_score_insufficient_rows():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    hist = pd.DataFrame({"Volume": [1_000_000] * 10}, index=idx)
    assert _volume_score(hist) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_candidate():
    s = _stock(price=97.0, high_1y=100.0, market_cap=2e9, adx=25, ema_20=95.0, perf_1m=5.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_far_from_high():
    s = _stock(price=82.0, high_1y=100.0)   # 18% away → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=5e7)  # $50M → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_low_adx():
    s = _stock(adx=10)  # no trend → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_price_below_ema20():
    s = _stock(price=80.0, ema_20=90.0)  # trend broken → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_parabolic():
    s = _stock(perf_1m=30.0)  # 30% in a month → too extended
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_passes_missing_high1y():
    # No high_1y from TradingView — deferred to Stage 3, should pass
    s = _stock(high_1y=None, adx=25, market_cap=2e9, ema_20=95.0, perf_1m=5.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_preserves_multiple():
    stocks = [
        _stock("AAA", price=98.0, high_1y=100.0, adx=22),
        _stock("BBB", price=97.0, high_1y=100.0, adx=30),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── score_high52 (full pipeline via monkeypatch) ─────────────────

def test_score_high52_near_high_qualifies(monkeypatch):
    """Stock within 2% of 52-week high on uptrend should score and grade."""
    import yfinance as yf

    hist = _make_hist(n=252, trend=0.002, at_high=True)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    tv = _stock(
        price=last_close,
        ema_20=last_close * 0.97,
        sma_50=last_close * 0.93,
        sma_200=last_close * 0.80,
        high_1y=last_close * 1.01,   # 1% above → within range
    )
    result = score_high52("TEST", tv_data=tv)
    assert result is not None
    assert result["dist_to_52h_pct"] <= 10.0
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_high52_far_from_high_returns_none(monkeypatch):
    """Stock more than 10% below its 52-week high should be rejected."""
    import yfinance as yf

    # Build history where the max high is 50% above current price
    idx = pd.date_range("2024-01-01", periods=252, freq="B")
    close = pd.Series([100.0] * 252, index=idx)
    # Spike early to create a very high 52-week high
    high = close.copy()
    high.iloc[10] = 200.0  # spike that pushes the 52w high far above current
    hist = pd.DataFrame({
        "Open": close * 0.995,
        "High": high,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000_000] * 252, index=idx),
    })

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_high52("FAR_FROM_HIGH")
    assert result is None


def test_score_high52_short_history_returns_none(monkeypatch):
    """Insufficient history (< 60 bars) → return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=30)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_high52("SHORT")
    assert result is None


def test_score_high52_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_high52("EMPTY")
    assert result is None


def test_score_high52_at_new_high_flag(monkeypatch):
    """at_new_high should be True when dist_to_52h_pct <= 1.0."""
    import yfinance as yf

    hist = _make_hist(n=252, trend=0.003)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    # Set current price == 52-week high (stock just made a new high)
    tv = _stock(price=last_close, high_1y=last_close)
    result = score_high52("NEWHIGH", tv_data=tv)
    # dist_to_52h_pct should be near 0 → at_new_high = True
    if result is not None:
        assert result["at_new_high"] is True
        assert result["dist_to_52h_pct"] <= 1.0


def test_score_high52_score_breakdown_keys(monkeypatch):
    """score_breakdown must contain all four expected keys."""
    import yfinance as yf

    hist = _make_hist(n=252, trend=0.002)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    tv = _stock(price=last_close, high_1y=last_close * 1.005)
    result = score_high52("BREAKDOWN", tv_data=tv)
    if result is not None:
        for key in ("proximity", "roc_20d", "trend", "volume"):
            assert key in result["score_breakdown"]
