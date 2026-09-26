"""Tests for dossier/obv_divergence_screener.py — OBV Divergence Screener."""

import numpy as np
import pandas as pd
import pytest

from dossier.obv_divergence_screener import (
    _compression_score,
    _consistency_score,
    _conviction_score,
    _divergence_score,
    _funnel_filter,
    compute_obv,
    detect_obv_divergence,
    score_obv_divergence,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_divergence_hist(stable: int = 60, cycles: int = 10,
                          up_move: float = 0.3, up_vol: float = 3_000_000,
                          down1_move: float = 0.5, down2_move: float = 0.3,
                          down_vol: float = 300_000) -> pd.DataFrame:
    """
    Synthetic OHLCV history: `stable` flat bars, then `cycles` 3-bar blocks
    of (up-day on high volume, down-day, down-day on low volume).

    Bullish divergence params (defaults): net price drifts DOWN each cycle
    (up_move < down1_move + down2_move) while net OBV flow is UP (up_vol
    dominates). Pass negative *_vol deltas / swap move signs for bearish.
    """
    n = stable + cycles * 3
    idx = pd.date_range("2023-01-01", periods=n, freq="B")

    prices = [100.0] * stable
    vols = [500_000] * stable
    price = 100.0
    for _ in range(cycles):
        price += up_move
        prices.append(price)
        vols.append(up_vol)
        price -= down1_move
        prices.append(price)
        vols.append(down_vol)
        price -= down2_move
        prices.append(price)
        vols.append(down_vol)

    close = pd.Series(prices, index=idx)
    volume = pd.Series(vols, index=idx)
    return pd.DataFrame({
        "Open":   close,
        "High":   close * 1.003,
        "Low":    close * 0.997,
        "Close":  close,
        "Volume": volume,
    })


# ─── compute_obv ──────────────────────────────────────────────────

def test_compute_obv_basic():
    close = pd.Series([1.0, 2.0, 1.0, 3.0])
    volume = pd.Series([10.0, 20.0, 30.0, 40.0])
    obv = compute_obv(close, volume)
    assert list(obv) == [0.0, 20.0, -10.0, 30.0]


def test_compute_obv_flat_price_no_change():
    close = pd.Series([5.0, 5.0, 5.0])
    volume = pd.Series([100.0, 100.0, 100.0])
    obv = compute_obv(close, volume)
    assert list(obv) == [0.0, 0.0, 0.0]


# ─── detect_obv_divergence ────────────────────────────────────────

def test_detect_bullish_divergence():
    close = pd.Series([100.0, 99.8, 99.6, 99.4, 99.2])
    obv = pd.Series([0.0, 50_000.0, 100_000.0, 150_000.0, 200_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=5)
    assert result is not None
    assert result["direction"] == "bullish"
    assert result["obv_slope_norm"] > 0
    assert result["price_slope_pct"] <= 0.02


def test_detect_bearish_divergence():
    close = pd.Series([100.0, 100.2, 100.4, 100.6, 100.8])
    obv = pd.Series([0.0, -50_000.0, -100_000.0, -150_000.0, -200_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=5)
    assert result is not None
    assert result["direction"] == "bearish"
    assert result["obv_slope_norm"] < 0
    assert result["price_slope_pct"] >= -0.02


def test_detect_none_when_aligned_not_diverging():
    # Price and OBV both flat — no trend disagreement
    close = pd.Series([100.0] * 10)
    obv = pd.Series([0.0] * 10)
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=10)
    assert result is None


def test_detect_none_when_price_and_obv_agree():
    # Both price and OBV rising together — trend confirmation, not divergence
    close = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0])
    obv = pd.Series([0.0, 50_000.0, 100_000.0, 150_000.0, 200_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=5)
    assert result is None


def test_detect_none_insufficient_length():
    close = pd.Series([100.0, 99.0])
    obv = pd.Series([0.0, 10_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=10)
    assert result is None


def test_detect_none_zero_avg_volume():
    close = pd.Series([100.0, 99.0, 98.0])
    obv = pd.Series([0.0, 10_000.0, 20_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=0.0, lookback=3)
    assert result is None


def test_detect_none_with_nan():
    close = pd.Series([100.0, float("nan"), 98.0])
    obv = pd.Series([0.0, 10_000.0, 20_000.0])
    result = detect_obv_divergence(close, obv, avg_volume=100_000.0, lookback=3)
    assert result is None


# ─── _divergence_score ────────────────────────────────────────────

def test_divergence_score_max():
    assert _divergence_score(0.12) == 40
    assert _divergence_score(0.20) == 40


def test_divergence_score_tiers():
    assert _divergence_score(0.08) == 32
    assert _divergence_score(0.05) == 24
    assert _divergence_score(0.03) == 14


def test_divergence_score_below_floor():
    assert _divergence_score(0.01) == 6


def test_divergence_score_uses_magnitude_not_sign():
    assert _divergence_score(-0.12) == _divergence_score(0.12)


def test_divergence_score_monotone():
    assert _divergence_score(0.01) < _divergence_score(0.05) < _divergence_score(0.12)


# ─── _consistency_score ───────────────────────────────────────────

def test_consistency_score_high_bullish():
    diffs = pd.Series([1, 1, 1, 1, -1] * 4)  # 80% positive
    assert _consistency_score(diffs, "bullish") == 25


def test_consistency_score_high_bearish():
    diffs = pd.Series([-1, -1, -1, -1, 1] * 4)  # 80% negative
    assert _consistency_score(diffs, "bearish") == 25


def test_consistency_score_moderate():
    diffs = pd.Series([1, 1, 1, -1, -1] * 4)  # 60% positive
    assert _consistency_score(diffs, "bullish") == 18


def test_consistency_score_weak():
    diffs = pd.Series([1, -1, -1, -1, -1] * 4)  # 20% positive
    assert _consistency_score(diffs, "bullish") == 4


def test_consistency_score_empty():
    assert _consistency_score(pd.Series([], dtype=float), "bullish") == 0


# ─── _conviction_score ────────────────────────────────────────────

def test_conviction_score_strong_bullish():
    close = pd.Series([100, 101, 100.8, 102, 101.8])
    volume = pd.Series([1_000_000, 3_000_000, 300_000, 3_000_000, 300_000])
    score = _conviction_score(volume, close, "bullish")
    assert score == 20


def test_conviction_score_strong_bearish():
    close = pd.Series([100, 99, 99.2, 98, 98.2])
    volume = pd.Series([1_000_000, 3_000_000, 300_000, 3_000_000, 300_000])
    score = _conviction_score(volume, close, "bearish")
    assert score == 20


def test_conviction_score_no_down_days_bullish():
    close = pd.Series([100, 101, 102, 103])
    volume = pd.Series([1_000_000, 500_000, 500_000, 500_000])
    score = _conviction_score(volume, close, "bullish")
    assert score == 20  # no down days at all → treated as maximal conviction


def test_conviction_score_weak():
    close = pd.Series([100, 101, 100.5, 102, 101.5])
    volume = pd.Series([1_000_000, 500_000, 800_000, 500_000, 800_000])
    score = _conviction_score(volume, close, "bullish")
    assert score in (3, 8)


# ─── _compression_score ───────────────────────────────────────────

def test_compression_score_tight():
    assert _compression_score(1.0) == 15
    assert _compression_score(2.5) == 15


def test_compression_score_moderate():
    assert _compression_score(3.5) == 10
    assert _compression_score(5.0) == 5


def test_compression_score_wide():
    assert _compression_score(10.0) == 1


def test_compression_score_monotone():
    assert _compression_score(10.0) < _compression_score(5.0) < _compression_score(2.0)


# ─── _funnel_filter ───────────────────────────────────────────────

def _stock(ticker="TEST", market_cap=2e9, avg_vol_30d=500_000) -> dict:
    return {
        "ticker": ticker, "name": ticker, "price": 50.0, "change_pct": 0.5,
        "volume": 600_000, "avg_vol_30d": avg_vol_30d, "market_cap": market_cap,
        "rsi": 50.0, "adx": 20.0,
    }


def test_funnel_passes_good_candidate():
    assert len(_funnel_filter([_stock()], verbose=False)) == 1


def test_funnel_cuts_small_cap():
    assert len(_funnel_filter([_stock(market_cap=5e7)], verbose=False)) == 0


def test_funnel_cuts_illiquid():
    assert len(_funnel_filter([_stock(avg_vol_30d=50_000)], verbose=False)) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_mixed_batch():
    good = _stock("GOOD")
    small = _stock("TINY", market_cap=1e7)
    result = _funnel_filter([good, small], verbose=False)
    assert len(result) == 1
    assert result[0]["ticker"] == "GOOD"


# ─── score_obv_divergence (integration, monkeypatched) ────────────

def test_score_detects_bullish(monkeypatch):
    import yfinance as yf

    hist = _make_divergence_hist()  # default params → bullish

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_obv_divergence("TEST")
    assert result is not None
    assert result["direction"] == "bullish"
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    for key in ("divergence", "consistency", "conviction", "compression"):
        assert key in result["score_breakdown"]


def test_score_detects_bearish(monkeypatch):
    import yfinance as yf

    # Mirror the bullish params: price net UP, volume weighted to down-days
    hist = _make_divergence_hist(
        up_move=0.5, up_vol=300_000,
        down1_move=0.1, down2_move=0.05, down_vol=3_000_000,
    )

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_obv_divergence("TEST")
    assert result is not None
    assert result["direction"] == "bearish"


def test_score_direction_filter_excludes(monkeypatch):
    import yfinance as yf

    hist = _make_divergence_hist()  # bullish

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    assert score_obv_divergence("TEST", direction_filter="bearish") is None
    assert score_obv_divergence("TEST", direction_filter="bullish") is not None


def test_score_returns_none_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_obv_divergence("EMPTY") is None


def test_score_returns_none_short_history(monkeypatch):
    import yfinance as yf

    hist = _make_divergence_hist(stable=10, cycles=0)  # only 10 bars

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_obv_divergence("SHORT") is None


def test_score_tv_data_populates_name(monkeypatch):
    import yfinance as yf

    hist = _make_divergence_hist()

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_obv_divergence("NKLA", tv_data={"name": "Nikola Corp", "market_cap": 3e8})
    if result is not None:
        assert result["name"] == "Nikola Corp"
        assert result["market_cap"] == 3e8
