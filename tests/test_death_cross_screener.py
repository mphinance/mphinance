"""Tests for dossier/death_cross_screener.py — Death Cross Alert Screener."""

import pandas as pd
import pytest

from dossier.death_cross_screener import (
    _funnel_filter,
    _recency_score,
    _rsi_score,
    _trend_score,
    _volume_score,
    detect_death_cross,
    score_death_cross,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_sma_series(length=20, cross_at: int | None = None):
    """
    Build aligned SMA50/SMA200 Series with an optional death cross.

    cross_at: how many bars ago (from the end) the cross happened.
    If None → SMA50 stays above SMA200 throughout (no cross).
    """
    idx = pd.RangeIndex(length)
    if cross_at is None:
        # SMA50 always above SMA200 — no cross
        sma50  = pd.Series([102.0] * length, index=idx)
        sma200 = pd.Series([100.0] * length, index=idx)
    else:
        # Before cross: SMA50 above SMA200; at cross: SMA50 flips below
        cross_idx = length - cross_at   # 0-based index where cross occurs
        sma50_vals  = [102.0] * length
        sma200_vals = [100.0] * length
        for i in range(cross_idx, length):
            sma50_vals[i] = 99.0   # below SMA200 after cross
        sma50  = pd.Series(sma50_vals,  index=idx)
        sma200 = pd.Series(sma200_vals, index=idx)
    return sma50, sma200


def _make_dc_hist(stable: int = 200, rally: int = 70, breakdown: int = 20,
                  rally_price: float = 108.0, breakdown_price: float = 88.0) -> pd.DataFrame:
    """
    Synthetic OHLCV history designed to produce a fresh death cross.

    Phase 1 — stable bars at 100 (with slight oscillation): SMA50 ≈ SMA200 ≈ 100
    Phase 2 — rally bars near rally_price: SMA50 rises above SMA200 (golden cross)
    Phase 3 — breakdown bars near breakdown_price with oscillation: SMA50 falls
               back below SMA200 while RSI stays in a reasonable range

    With rally=70 and breakdown=20 the death cross happens roughly 5 bars
    from the end (within the 15-day lookback window).
    Oscillation in the breakdown phase keeps RSI off the 0 extreme.
    """
    n = stable + rally + breakdown
    idx = pd.date_range("2023-01-01", periods=n, freq="B")

    prices = []
    # Phase 1: gentle oscillation around 100
    for i in range(stable):
        osc = (i % 5 - 2) * 0.2
        prices.append(100.0 + osc)

    # Phase 2: oscillation around rally_price
    for i in range(rally):
        osc = (i % 5 - 2) * 0.2
        prices.append(rally_price + osc)

    # Phase 3: oscillation around breakdown_price (keeps RSI healthy)
    for i in range(breakdown):
        osc = (i % 3 - 1) * 0.4
        prices.append(breakdown_price + osc)

    close  = pd.Series(prices, index=idx)
    avg_vol = 1_000_000
    vols = [avg_vol] * n
    # Elevated volume on the first breakdown bar only if breakdown > 0
    if breakdown > 0:
        vols[stable + rally] = int(avg_vol * 2.2)
    volume = pd.Series(vols, index=idx)
    return pd.DataFrame({
        "Open":   close * 1.005,
        "High":   close * 1.01,
        "Low":    close * 0.99,
        "Close":  close,
        "Volume": volume,
    })


def _stock(
    ticker="TEST", price=95.0, sma_200=100.0, sma_50=97.0,
    ema_20=96.0, avg_vol_30d=500_000, market_cap=2e9, rsi=42.0,
) -> dict:
    return {
        "ticker":      ticker,
        "name":        ticker,
        "price":       price,
        "change_pct":  -0.5,
        "volume":      600_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap":  market_cap,
        "sma_200":     sma_200,
        "sma_50":      sma_50,
        "ema_20":      ema_20,
        "rsi":         rsi,
        "adx":         22.0,
        "perf_1w":     -1.2,
        "perf_1m":     -4.0,
        "high_1y":     price * 1.4,
    }


# ─── detect_death_cross ───────────────────────────────────────────

def test_detect_cross_found_5_days_ago():
    sma50, sma200 = _make_sma_series(length=30, cross_at=5)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result == 5


def test_detect_cross_found_1_day_ago():
    sma50, sma200 = _make_sma_series(length=30, cross_at=1)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result == 1


def test_detect_cross_found_at_lookback_boundary():
    sma50, sma200 = _make_sma_series(length=40, cross_at=15)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result == 15


def test_detect_cross_none_when_sma50_always_above():
    sma50, sma200 = _make_sma_series(length=30, cross_at=None)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result is None


def test_detect_cross_none_when_cross_too_old():
    sma50, sma200 = _make_sma_series(length=40, cross_at=20)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result is None


def test_detect_cross_handles_nan_gracefully():
    idx = pd.RangeIndex(20)
    sma50  = pd.Series([float("nan")] * 5 + [101.0] * 9 + [99.0] * 6, index=idx)
    sma200 = pd.Series([float("nan")] * 5 + [100.0] * 15,              index=idx)
    result = detect_death_cross(sma50, sma200, lookback=10)
    assert result is not None
    assert result <= 10


def test_detect_cross_returns_most_recent():
    """When two crosses exist in the window, detect_death_cross returns the nearest one."""
    # Cross at bar 12 and also bar 22 — should report 3 (most recent)
    idx = pd.RangeIndex(25)
    s50_vals = [102.0] * 25
    s200_vals = [100.0] * 25
    # First cross at bar 12 (13 bars from end in 25-bar series)
    for i in range(12, 17):
        s50_vals[i] = 99.0
    # Rise back above, then cross again at bar 22 (3 bars from end)
    for i in range(17, 22):
        s50_vals[i] = 102.0
    for i in range(22, 25):
        s50_vals[i] = 99.0
    sma50  = pd.Series(s50_vals,  index=idx)
    sma200 = pd.Series(s200_vals, index=idx)
    result = detect_death_cross(sma50, sma200, lookback=15)
    assert result == 3


# ─── _recency_score ───────────────────────────────────────────────

def test_recency_score_very_fresh():
    assert _recency_score(1) == 40
    assert _recency_score(3) == 40


def test_recency_score_5_days():
    assert _recency_score(4) == 34
    assert _recency_score(5) == 34


def test_recency_score_7_days():
    assert _recency_score(6) == 26
    assert _recency_score(7) == 26


def test_recency_score_10_days():
    assert _recency_score(8) == 18
    assert _recency_score(10) == 18


def test_recency_score_15_days():
    assert _recency_score(11) == 10
    assert _recency_score(15) == 10


def test_recency_score_stale():
    assert _recency_score(16) == 4
    assert _recency_score(100) == 4


def test_recency_score_monotone():
    assert _recency_score(15) < _recency_score(10) < _recency_score(5) < _recency_score(1)


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_full_marks():
    # Price below EMA20, SMA50 well below SMA200 (gap ≥ 3%)
    assert _trend_score(90.0, 93.0, 94.0, 100.0) == 30


def test_trend_score_above_ema20():
    # Price above EMA20 → no EMA points, but gap still earns
    pts = _trend_score(101.0, 95.0, 96.0, 100.0)
    assert pts < 30


def test_trend_score_small_gap():
    # Gap between 0 and 1.5% → only 5 pts from gap component
    pts = _trend_score(90.0, 93.0, 98.8, 100.0)
    assert 0 < pts < 30


def test_trend_score_no_ema20():
    # ema20=None → no EMA component
    pts = _trend_score(90.0, None, 96.0, 100.0)
    assert pts <= 15


def test_trend_score_zero_sma200():
    pts = _trend_score(90.0, 93.0, 96.0, 0.0)
    assert pts >= 0


# ─── _rsi_score ───────────────────────────────────────────────────

def test_rsi_score_goldilocks():
    assert _rsi_score(35.0) == 20
    assert _rsi_score(45.0) == 20
    assert _rsi_score(52.0) == 20


def test_rsi_score_slightly_off():
    assert _rsi_score(30.0) == 13
    assert _rsi_score(58.0) == 13


def test_rsi_score_edge():
    assert _rsi_score(24.0) == 6
    assert _rsi_score(65.0) == 6


def test_rsi_score_extreme():
    assert _rsi_score(10.0) == 2
    assert _rsi_score(80.0) == 2


def test_rsi_score_monotone_from_center():
    assert _rsi_score(5.0) < _rsi_score(24.0) < _rsi_score(45.0)


# ─── _volume_score ────────────────────────────────────────────────

def test_volume_score_high():
    assert _volume_score(2.5) == 10
    assert _volume_score(2.0) == 10


def test_volume_score_moderate():
    assert _volume_score(1.5) == 7


def test_volume_score_low():
    assert _volume_score(1.2) == 4


def test_volume_score_minimal():
    assert _volume_score(0.8) == 1


def test_volume_score_monotone():
    assert _volume_score(1.0) < _volume_score(1.5) < _volume_score(2.0)


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_good_candidate():
    s = _stock(sma_50=97.0, sma_200=100.0, market_cap=2e9)
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=5e7)   # $50M → cut
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_missing_sma200():
    s = _stock()
    s["sma_200"] = None
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_missing_sma50():
    s = _stock()
    s["sma_50"] = None
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_extended_gap():
    # SMA50 more than 12% below SMA200 → stale cross
    s = _stock(sma_50=85.0, sma_200=100.0)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_passes_boundary_gap():
    # Exactly 12% below → passes (gap ≤ 12%)
    s = _stock(sma_50=88.0, sma_200=100.0)
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_mixed_batch():
    good  = _stock("GOOD",  sma_50=97.0, sma_200=100.0, market_cap=2e9)
    small = _stock("TINY",  market_cap=1e7)
    wide  = _stock("WIDE",  sma_50=80.0, sma_200=100.0)
    result = _funnel_filter([good, small, wide], verbose=False)
    assert len(result) == 1
    assert result[0]["ticker"] == "GOOD"


# ─── score_death_cross (integration, monkeypatched) ───────────────

def test_score_returns_result_on_fresh_cross(monkeypatch):
    """Price history with a recent death cross should yield a scored result."""
    import yfinance as yf

    hist = _make_dc_hist(stable=200, rally=70, breakdown=20)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_death_cross("TEST")
    assert result is not None
    assert result["days_since_cross"] <= 15
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    assert "score_breakdown" in result
    for key in ("recency", "trend", "rsi", "volume"):
        assert key in result["score_breakdown"]


def test_score_returns_none_when_no_recent_cross(monkeypatch):
    """Death cross that happened 30+ days ago should be rejected."""
    import yfinance as yf

    # Cross happened ~30 bars ago (breakdown=50 → cross ~35 bars from end)
    hist = _make_dc_hist(stable=200, rally=70, breakdown=50)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_death_cross("OLD")
    assert result is None


def test_score_returns_none_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_death_cross("EMPTY") is None


def test_score_returns_none_short_history(monkeypatch):
    import yfinance as yf

    # Only 50 bars — far below the 210-bar minimum
    hist = _make_dc_hist(stable=50, rally=0, breakdown=0)
    hist = hist.iloc[:50]  # ensure it stays short

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_death_cross("SHORT") is None


def test_score_tv_data_populates_name(monkeypatch):
    """tv_data['name'] should appear in the returned dict."""
    import yfinance as yf

    hist = _make_dc_hist(stable=200, rally=70, breakdown=20)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_death_cross("NKLA", tv_data={"name": "Nikola Corp", "market_cap": 3e8})
    if result is not None:
        assert result["name"] == "Nikola Corp"
        assert result["market_cap"] == 3e8
