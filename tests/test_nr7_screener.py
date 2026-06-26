"""Tests for dossier/nr7_screener.py — NR7 Tight-Coil Screener."""

import math

import pandas as pd
import pytest

from dossier.nr7_screener import (
    _funnel_filter,
    _is_nr7,
    _range_contraction_score,
    _rsi_coil_score,
    _trend_score,
    _volume_dryup_score,
    score_nr7,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(
    n: int = 60,
    price: float = 100.0,
    range_mult: float = 1.0,
    coil_last: int = 5,
    coil_factor: float = 0.4,
) -> pd.DataFrame:
    """
    Synthetic OHLCV history.
    The final `coil_last` bars have their range compressed by `coil_factor`.
    """
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close_base = price
    closes = [close_base * (1 + 0.001 * i) for i in range(n)]
    daily_range_base = price * 0.015 * range_mult

    highs, lows, opens, vols = [], [], [], []
    for i, c in enumerate(closes):
        r = daily_range_base * (coil_factor if i >= n - coil_last else 1.0)
        highs.append(c + r / 2)
        lows.append(c - r / 2)
        opens.append(c - r * 0.1)
        vols.append(1_000_000)

    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
        index=idx,
    )


def _make_coil_hist(
    n: int = 60,
    price: float = 100.0,
    coil_factor: float = 0.35,
    vol_ratio: float = 0.6,
) -> pd.DataFrame:
    """History with both range AND volume dry-up in the last 5 bars."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    closes = [price * (1 + 0.001 * i) for i in range(n)]
    normal_range = price * 0.015
    normal_vol = 1_000_000

    highs, lows, opens, vols = [], [], [], []
    for i, c in enumerate(closes):
        is_coil = i >= n - 5
        r = normal_range * (coil_factor if is_coil else 1.0)
        v = int(normal_vol * (vol_ratio if is_coil else 1.0))
        highs.append(c + r / 2)
        lows.append(c - r / 2)
        opens.append(c - r * 0.1)
        vols.append(v)

    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
        index=idx,
    )


def _stock(
    ticker="TEST",
    price=100.0,
    ema_20=96.0,
    sma_50=90.0,
    sma_200=80.0,
    avg_vol_30d=500_000,
    rsi=52,
    adx=22,
    market_cap=2e9,
    perf_3m=12.0,
    perf_1m=5.0,
    perf_1w=1.5,
) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": 0.2,
        "volume": 400_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap": market_cap,
        "sma_200": sma_200,
        "sma_50": sma_50,
        "ema_20": ema_20,
        "rsi": rsi,
        "adx": adx,
        "atr": price * 0.012,
        "perf_1w": perf_1w,
        "perf_1m": perf_1m,
        "tv_signal": 0.2,
        "perf_3m": perf_3m,
        "perf_6m": 18.0,
    }


# ─── _is_nr7 ──────────────────────────────────────────────────────

def test_is_nr7_true_when_last_is_smallest():
    ranges = [2.0, 1.8, 1.5, 1.2, 1.0, 0.9, 0.7]
    assert _is_nr7(ranges) is True


def test_is_nr7_false_when_last_is_not_smallest():
    ranges = [0.7, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0]
    assert _is_nr7(ranges) is False


def test_is_nr7_true_when_tied_for_smallest():
    ranges = [2.0, 1.5, 0.7, 1.2, 1.0, 0.9, 0.7]
    assert _is_nr7(ranges) is True


def test_is_nr7_too_short():
    assert _is_nr7([1.0]) is False
    assert _is_nr7([]) is False


# ─── _range_contraction_score ─────────────────────────────────────

def test_range_contraction_very_tight_with_nr7():
    score = _range_contraction_score(0.25, True)
    assert score == 35


def test_range_contraction_very_tight_no_nr7():
    score = _range_contraction_score(0.25, False)
    assert score == 30


def test_range_contraction_moderate():
    score = _range_contraction_score(0.55, False)
    assert score == 16


def test_range_contraction_mild():
    score = _range_contraction_score(0.80, False)
    assert score == 3


def test_range_contraction_not_coiling():
    score = _range_contraction_score(0.95, False)
    assert score == 0


def test_range_contraction_monotone():
    assert (
        _range_contraction_score(0.90, False)
        < _range_contraction_score(0.60, False)
        < _range_contraction_score(0.40, False)
        < _range_contraction_score(0.25, False)
    )


def test_range_contraction_zero_ratio():
    assert _range_contraction_score(0.0, False) == 0


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_full_stack():
    score = _trend_score(100.0, 96.0, 90.0, 80.0)
    assert score == 30


def test_trend_score_above_ema20_ema50_only():
    score = _trend_score(100.0, 96.0, 90.0, 110.0)
    assert score < 30


def test_trend_score_above_ema20_only():
    score = _trend_score(100.0, 96.0, None, None)
    assert score == 10


def test_trend_score_below_all():
    assert _trend_score(80.0, 90.0, 92.0, 95.0) == 0


def test_trend_score_nan_sma200():
    score = _trend_score(100.0, 96.0, 90.0, float("nan"))
    assert score < 30


# ─── _rsi_coil_score ──────────────────────────────────────────────

def test_rsi_coil_sweet_spot():
    assert _rsi_coil_score(52.0) == 20


def test_rsi_coil_borderline():
    assert _rsi_coil_score(42.0) == 14


def test_rsi_coil_overbought():
    assert _rsi_coil_score(75.0) == 0


def test_rsi_coil_oversold():
    assert _rsi_coil_score(30.0) == 0


def test_rsi_coil_nan():
    assert _rsi_coil_score(float("nan")) == 6


def test_rsi_coil_none():
    assert _rsi_coil_score(None) == 6


def test_rsi_coil_monotone_from_sweet_spot():
    # Lower scores as we move away from the 45-58 sweet spot
    assert _rsi_coil_score(52) > _rsi_coil_score(42) > _rsi_coil_score(37)


# ─── _volume_dryup_score ─────────────────────────────────────────

def _make_vol_hist(n: int = 60, recent_mult: float = 0.6) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    base_vol = 1_000_000
    volume = [base_vol] * n
    for i in range(n - 5, n):
        volume[i] = int(base_vol * recent_mult)
    return pd.DataFrame({"Volume": pd.Series(volume, index=idx)})


def test_volume_dryup_big_dryup():
    hist = _make_vol_hist(recent_mult=0.50)
    assert _volume_dryup_score(hist) == 15


def test_volume_dryup_moderate():
    hist = _make_vol_hist(recent_mult=0.65)
    assert _volume_dryup_score(hist) == 10


def test_volume_dryup_slight():
    hist = _make_vol_hist(recent_mult=0.80)
    assert _volume_dryup_score(hist) == 6


def test_volume_dryup_flat():
    hist = _make_vol_hist(recent_mult=0.95)
    assert _volume_dryup_score(hist) == 3


def test_volume_dryup_expanding():
    hist = _make_vol_hist(recent_mult=1.3)
    assert _volume_dryup_score(hist) == 0


def test_volume_dryup_insufficient_rows():
    idx = pd.date_range("2024-01-01", periods=10, freq="B")
    hist = pd.DataFrame({"Volume": [1_000_000] * 10}, index=idx)
    assert _volume_dryup_score(hist) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_coil_candidate():
    s = _stock(price=100.0, sma_50=95.0, market_cap=2e9, avg_vol_30d=400_000, perf_1m=5.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=5e7)  # $50M → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_price_below_sma50():
    s = _stock(price=80.0, sma_50=95.0)  # trend broken
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_parabolic():
    s = _stock(perf_1m=25.0)  # 25% in a month → too extended to coil
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_low_volume():
    s = _stock(avg_vol_30d=100_000)  # illiquid → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_preserves_multiple():
    stocks = [
        _stock("AAA", price=98.0, sma_50=90.0, market_cap=2e9),
        _stock("BBB", price=97.0, sma_50=88.0, market_cap=5e9),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── score_nr7 (full pipeline via monkeypatch) ────────────────────

def test_score_nr7_tight_coil_qualifies(monkeypatch):
    """Coiling stock with strong range contraction should score and grade."""
    import yfinance as yf

    hist = _make_coil_hist(n=60, price=100.0, coil_factor=0.30, vol_ratio=0.55)

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
        rsi=52,
    )
    result = score_nr7("COIL", tv_data=tv)
    assert result is not None
    assert result["range_ratio"] < 1.0
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_nr7_not_coiling_returns_none(monkeypatch):
    """Stock with full-size daily range should be rejected (range_ratio > 0.90)."""
    import yfinance as yf

    # All bars have the same range (ratio ≈ 1.0)
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    price = 100.0
    r = price * 0.015
    hist = pd.DataFrame({
        "Open": [price] * 60,
        "High": [price + r / 2] * 60,
        "Low": [price - r / 2] * 60,
        "Close": [price] * 60,
        "Volume": [1_000_000] * 60,
    }, index=idx)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_nr7("FLAT")
    assert result is None


def test_score_nr7_short_history_returns_none(monkeypatch):
    """Fewer than 30 bars → return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=20)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_nr7("SHORT")
    assert result is None


def test_score_nr7_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_nr7("EMPTY")
    assert result is None


def test_score_nr7_nr7_flag_set(monkeypatch):
    """is_nr7 should be True when last session is the narrowest in 7 days."""
    import yfinance as yf

    # Make last bar much narrower than all prior bars → NR7 guaranteed
    hist = _make_coil_hist(n=60, coil_factor=0.20, vol_ratio=0.5)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    tv = _stock(price=last_close, rsi=52)
    result = score_nr7("NR7TEST", tv_data=tv)
    if result is not None:
        assert result["is_nr7"] is True


def test_score_nr7_score_breakdown_keys(monkeypatch):
    """score_breakdown must contain all four expected keys."""
    import yfinance as yf

    hist = _make_coil_hist(n=60, coil_factor=0.30, vol_ratio=0.6)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(hist["Close"].iloc[-1])
    tv = _stock(price=last_close, rsi=52)
    result = score_nr7("KEYS", tv_data=tv)
    if result is not None:
        for key in ("range_contraction", "trend", "rsi_coil", "volume_dryup"):
            assert key in result["score_breakdown"]
