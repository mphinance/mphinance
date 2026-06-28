"""Tests for dossier/golden_cross_screener.py — Golden Cross Alert Screener."""

import pandas as pd
import pytest

from dossier.golden_cross_screener import (
    _funnel_filter,
    _recency_score,
    _rsi_score,
    _trend_score,
    _volume_score,
    detect_golden_cross,
    score_golden_cross,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_sma_series(length=20, cross_at: int | None = None):
    """
    Build aligned SMA50/SMA200 Series with an optional golden cross.

    cross_at: how many bars ago (from the end) the cross happened.
    If None → SMA50 stays below SMA200 throughout (no cross).
    """
    idx = pd.RangeIndex(length)
    if cross_at is None:
        # SMA50 always below SMA200 — no cross
        sma50  = pd.Series([98.0] * length, index=idx)
        sma200 = pd.Series([100.0] * length, index=idx)
    else:
        # Before cross: SMA50 below SMA200; at cross: SMA50 flips above
        cross_idx = length - cross_at   # 0-based index where cross occurs
        sma50_vals  = [98.0] * length
        sma200_vals = [100.0] * length
        for i in range(cross_idx, length):
            sma50_vals[i] = 101.0   # above SMA200 after cross
        sma50  = pd.Series(sma50_vals,  index=idx)
        sma200 = pd.Series(sma200_vals, index=idx)
    return sma50, sma200


def _make_gc_hist(stable: int = 200, drop: int = 70, recovery: int = 20,
                  drop_price: float = 92.0, recovery_price: float = 112.0) -> pd.DataFrame:
    """
    Synthetic OHLCV history designed to produce a fresh golden cross.

    Phase 1 — stable bars at 100 (with slight oscillation): SMA50 ≈ SMA200 ≈ 100
    Phase 2 — drop bars near drop_price: SMA50 falls below SMA200 (death cross)
    Phase 3 — recovery bars near recovery_price with oscillation: SMA50 rises
               back above SMA200 while RSI stays in a reasonable range

    With drop=70 and recovery=20 the golden cross happens roughly 5 bars
    from the end (within the 15-day lookback window).
    Oscillation in the recovery phase keeps RSI off the 100 extreme.
    """
    n = stable + drop + recovery
    idx = pd.date_range("2023-01-01", periods=n, freq="B")

    prices = []
    # Phase 1: gentle oscillation around 100
    for i in range(stable):
        osc = (i % 5 - 2) * 0.2
        prices.append(100.0 + osc)

    # Phase 2: oscillation around drop_price
    for i in range(drop):
        osc = (i % 5 - 2) * 0.2
        prices.append(drop_price + osc)

    # Phase 3: oscillation around recovery_price (keeps RSI healthy)
    for i in range(recovery):
        osc = (i % 3 - 1) * 0.4
        prices.append(recovery_price + osc)

    close  = pd.Series(prices, index=idx)
    avg_vol = 1_000_000
    vols = [avg_vol] * n
    # Elevated volume on the first recovery bar only if recovery > 0
    if recovery > 0:
        vols[stable + drop] = int(avg_vol * 2.2)
    volume = pd.Series(vols, index=idx)
    return pd.DataFrame({
        "Open":   close * 0.995,
        "High":   close * 1.01,
        "Low":    close * 0.99,
        "Close":  close,
        "Volume": volume,
    })


def _stock(
    ticker="TEST", price=105.0, sma_200=100.0, sma_50=103.0,
    ema_20=104.0, avg_vol_30d=500_000, market_cap=2e9, rsi=58.0,
) -> dict:
    return {
        "ticker":      ticker,
        "name":        ticker,
        "price":       price,
        "change_pct":  0.5,
        "volume":      600_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap":  market_cap,
        "sma_200":     sma_200,
        "sma_50":      sma_50,
        "ema_20":      ema_20,
        "rsi":         rsi,
        "adx":         22.0,
        "perf_1w":     1.2,
        "perf_1m":     4.0,
        "high_1y":     price * 1.15,
    }


# ─── detect_golden_cross ──────────────────────────────────────────

def test_detect_cross_found_5_days_ago():
    sma50, sma200 = _make_sma_series(length=30, cross_at=5)
    result = detect_golden_cross(sma50, sma200, lookback=15)
    assert result == 5


def test_detect_cross_found_1_day_ago():
    sma50, sma200 = _make_sma_series(length=30, cross_at=1)
    result = detect_golden_cross(sma50, sma200, lookback=15)
    assert result == 1


def test_detect_cross_found_at_lookback_boundary():
    sma50, sma200 = _make_sma_series(length=40, cross_at=15)
    result = detect_golden_cross(sma50, sma200, lookback=15)
    assert result == 15


def test_detect_cross_none_when_sma50_always_below():
    sma50, sma200 = _make_sma_series(length=30, cross_at=None)
    result = detect_golden_cross(sma50, sma200, lookback=15)
    assert result is None


def test_detect_cross_none_when_cross_too_old():
    sma50, sma200 = _make_sma_series(length=40, cross_at=20)
    result = detect_golden_cross(sma50, sma200, lookback=15)
    assert result is None


def test_detect_cross_handles_nan_gracefully():
    idx = pd.RangeIndex(20)
    sma50  = pd.Series([float("nan")] * 5 + [99.0] * 9 + [101.0] * 6, index=idx)
    sma200 = pd.Series([float("nan")] * 5 + [100.0] * 15,              index=idx)
    result = detect_golden_cross(sma50, sma200, lookback=10)
    assert result is not None
    assert result <= 10


def test_detect_cross_returns_most_recent():
    """When two crosses exist in the window, detect_golden_cross returns the nearest one."""
    # Cross at bar -3 and also -10 — should report 3 (most recent)
    idx = pd.RangeIndex(25)
    s50_vals = [98.0] * 25
    s200_vals = [100.0] * 25
    # First cross at bar 12 (13 bars from end in 25-bar series)
    for i in range(12, 17):
        s50_vals[i] = 101.0
    # Drop back below, then cross again at bar 22 (3 bars from end)
    for i in range(17, 22):
        s50_vals[i] = 98.0
    for i in range(22, 25):
        s50_vals[i] = 101.0
    sma50  = pd.Series(s50_vals,  index=idx)
    sma200 = pd.Series(s200_vals, index=idx)
    result = detect_golden_cross(sma50, sma200, lookback=15)
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
    # Price above EMA20, SMA50 well above SMA200 (gap ≥ 3%)
    assert _trend_score(110.0, 107.0, 106.0, 100.0) == 30


def test_trend_score_below_ema20():
    # Price below EMA20 → no EMA points, but gap still earns
    pts = _trend_score(99.0, 105.0, 104.0, 100.0)
    assert pts < 30


def test_trend_score_small_gap():
    # Gap between 0 and 1.5% → only 5 pts from gap component
    pts = _trend_score(110.0, 107.0, 101.2, 100.0)
    assert 0 < pts < 30


def test_trend_score_no_ema20():
    # ema20=None → no EMA component
    pts = _trend_score(110.0, None, 104.0, 100.0)
    assert pts <= 15


def test_trend_score_zero_sma200():
    pts = _trend_score(110.0, 107.0, 104.0, 0.0)
    assert pts >= 0


# ─── _rsi_score ───────────────────────────────────────────────────

def test_rsi_score_goldilocks():
    assert _rsi_score(50.0) == 20
    assert _rsi_score(60.0) == 20
    assert _rsi_score(65.0) == 20


def test_rsi_score_slightly_off():
    assert _rsi_score(45.0) == 13
    assert _rsi_score(68.0) == 13


def test_rsi_score_edge():
    assert _rsi_score(38.0) == 6
    assert _rsi_score(74.0) == 6


def test_rsi_score_extreme():
    assert _rsi_score(20.0) == 2
    assert _rsi_score(85.0) == 2


def test_rsi_score_monotone_from_center():
    assert _rsi_score(80.0) < _rsi_score(68.0) < _rsi_score(55.0)


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
    s = _stock(sma_50=103.0, sma_200=100.0, market_cap=2e9)
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
    # SMA50 more than 12% above SMA200 → stale cross
    s = _stock(sma_50=115.0, sma_200=100.0)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_passes_boundary_gap():
    # Exactly 12% → passes (gap ≤ 12%)
    s = _stock(sma_50=112.0, sma_200=100.0)
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_mixed_batch():
    good  = _stock("GOOD",  sma_50=103.0, sma_200=100.0, market_cap=2e9)
    small = _stock("TINY",  market_cap=1e7)
    wide  = _stock("WIDE",  sma_50=120.0, sma_200=100.0)
    result = _funnel_filter([good, small, wide], verbose=False)
    assert len(result) == 1
    assert result[0]["ticker"] == "GOOD"


# ─── score_golden_cross (integration, monkeypatched) ─────────────

def test_score_returns_result_on_fresh_cross(monkeypatch):
    """Price history with a recent golden cross should yield a scored result."""
    import yfinance as yf

    hist = _make_gc_hist(stable=200, drop=70, recovery=20)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_golden_cross("TEST")
    assert result is not None
    assert result["days_since_cross"] <= 15
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    assert "score_breakdown" in result
    for key in ("recency", "trend", "rsi", "volume"):
        assert key in result["score_breakdown"]


def test_score_returns_none_when_no_recent_cross(monkeypatch):
    """Golden cross that happened 30+ days ago should be rejected."""
    import yfinance as yf

    # Cross happened ~30 bars ago (recovery=50 → cross ~35 bars from end)
    hist = _make_gc_hist(stable=200, drop=70, recovery=50)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_golden_cross("OLD")
    assert result is None


def test_score_returns_none_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_golden_cross("EMPTY") is None


def test_score_returns_none_short_history(monkeypatch):
    import yfinance as yf

    # Only 50 bars — far below the 210-bar minimum
    hist = _make_gc_hist(stable=50, drop=0, recovery=0)
    hist = hist.iloc[:50]  # ensure it stays short

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_golden_cross("SHORT") is None


def test_score_tv_data_populates_name(monkeypatch):
    """tv_data['name'] should appear in the returned dict."""
    import yfinance as yf

    hist = _make_gc_hist(stable=200, drop=70, recovery=20)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_golden_cross("NVDA", tv_data={"name": "NVIDIA Corp", "market_cap": 3e12})
    if result is not None:
        assert result["name"] == "NVIDIA Corp"
        assert result["market_cap"] == 3e12
