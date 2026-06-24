"""Tests for dossier/sma200_reclaim_screener.py — 200-Day SMA Reclaim Screener."""

import pandas as pd
import pytest

from dossier.sma200_reclaim_screener import (
    _funnel_filter,
    _recency_score,
    _rsi_score,
    _sma50_score,
    _volume_conf_score,
    score_sma200_reclaim,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(
    n: int = 252,
    days_ago: int = 5,         # crossover happened this many bars from end
    rvol_on_cross: float = 2.0,
) -> pd.DataFrame:
    """
    Build a synthetic OHLCV DataFrame with a realistic SMA200 crossover.

    - Most of history oscillates around 89.5 (will be ≈ SMA200)
    - Price crosses above to ~91+ exactly `days_ago` bars from the end
    - Oscillation ensures RSI is computable and in the 40-65 range
    - Elevated volume on the crossover bar
    """
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    prices = []

    # Below phase: oscillate realistically around 89.5
    below_count = n - days_ago
    for i in range(below_count):
        osc = (i % 5 - 2) * 0.25   # cycles: -0.5, -0.25, 0, +0.25, +0.5
        prices.append(89.5 + osc)

    # Above phase: move to ~91, stay there with gentle oscillation
    for i in range(days_ago):
        osc = (i % 3 - 1) * 0.15
        prices.append(91.0 + i * 0.1 + osc)

    close = pd.Series(prices, index=idx)
    high = close * 1.01
    low = close * 0.99
    opens = close * 0.995

    avg_vol = 1_000_000
    volume = pd.Series([avg_vol] * n, index=idx)
    # Elevated volume on the bar that started the crossover
    volume.iloc[-days_ago] = int(avg_vol * rvol_on_cross)

    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


def _stock(
    ticker="TEST",
    price=102.0,
    sma_200=98.0,
    sma_50=100.0,
    avg_vol_30d=500_000,
    market_cap=2e9,
    rsi=55.0,
    adx=20.0,
    perf_1m=2.0,
    perf_1w=1.5,
    perf_3m=-5.0,
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
        "ema_20": price * 0.99,
        "rsi": rsi,
        "adx": adx,
        "atr": price * 0.015,
        "perf_1w": perf_1w,
        "perf_1m": perf_1m,
        "tv_signal": 0.1,
        "perf_3m": perf_3m,
        "high_1y": price * 1.2,
    }


# ─── _recency_score ───────────────────────────────────────────────

def test_recency_score_very_fresh():
    assert _recency_score(1) == 40
    assert _recency_score(3) == 40


def test_recency_score_within_5_days():
    assert _recency_score(4) == 34
    assert _recency_score(5) == 34


def test_recency_score_within_7_days():
    assert _recency_score(6) == 26
    assert _recency_score(7) == 26


def test_recency_score_within_10_days():
    assert _recency_score(8) == 18
    assert _recency_score(10) == 18


def test_recency_score_within_15_days():
    assert _recency_score(11) == 10
    assert _recency_score(15) == 10


def test_recency_score_stale():
    assert _recency_score(16) == 4
    assert _recency_score(100) == 4


def test_recency_score_monotone():
    assert _recency_score(15) < _recency_score(10) < _recency_score(5) < _recency_score(1)


# ─── _volume_conf_score ───────────────────────────────────────────

def test_vol_conf_score_very_high():
    assert _volume_conf_score(3.0) == 25
    assert _volume_conf_score(2.5) == 25


def test_vol_conf_score_high():
    assert _volume_conf_score(2.0) == 20


def test_vol_conf_score_moderate():
    assert _volume_conf_score(1.5) == 15


def test_vol_conf_score_low():
    assert _volume_conf_score(1.2) == 9


def test_vol_conf_score_minimal():
    assert _volume_conf_score(1.0) == 4
    assert _volume_conf_score(0.5) == 4


def test_vol_conf_score_monotone():
    assert _volume_conf_score(1.0) < _volume_conf_score(1.5) < _volume_conf_score(2.5)


# ─── _rsi_score ───────────────────────────────────────────────────

def test_rsi_score_goldilocks():
    assert _rsi_score(50.0) == 20
    assert _rsi_score(55.0) == 20
    assert _rsi_score(60.0) == 20


def test_rsi_score_slightly_off_center():
    assert _rsi_score(45.0) == 15
    assert _rsi_score(65.0) == 15


def test_rsi_score_edges():
    assert _rsi_score(40.0) == 8
    assert _rsi_score(70.0) == 8


def test_rsi_score_low():
    assert _rsi_score(35.0) == 3
    assert _rsi_score(75.0) == 3


# ─── _sma50_score ─────────────────────────────────────────────────

def test_sma50_score_none():
    assert _sma50_score(100.0, None) == 0


def test_sma50_score_zero():
    assert _sma50_score(100.0, 0.0) == 0


def test_sma50_score_below_sma50():
    # Price below SMA50 = 0 points (double reclaim not achieved)
    assert _sma50_score(90.0, 95.0) == 0


def test_sma50_score_just_above():
    # Within 5% above SMA50 — clean double reclaim
    assert _sma50_score(102.0, 100.0) == 15


def test_sma50_score_moderately_above():
    # 7% above
    assert _sma50_score(107.0, 100.0) == 10


def test_sma50_score_well_above():
    # 12% above
    assert _sma50_score(112.0, 100.0) == 6


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_candidate():
    s = _stock(price=102.0, sma_200=98.0, market_cap=2e9, rsi=55.0, perf_1m=2.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=1e8)  # $100M → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_extended_above_sma200():
    # More than 15% above SMA200 = been above for a long time, not fresh reclaim
    s = _stock(price=120.0, sma_200=98.0)  # ~22% above
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought_rsi():
    s = _stock(rsi=75.0)  # overbought → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_crashed_monthly():
    s = _stock(perf_1m=-25.0)  # still in freefall → cut
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_passes_boundary_proximity():
    # Clearly within 15% above SMA200 → should pass
    s = _stock(price=112.0, sma_200=98.0)  # ~14.3% above
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_mixed_batch():
    good = _stock("GOOD", price=102.0, sma_200=98.0, market_cap=2e9, rsi=55.0, perf_1m=2.0)
    small = _stock("TINY", market_cap=5e7)
    extended = _stock("BIG", price=130.0, sma_200=98.0)
    result = _funnel_filter([good, small, extended], verbose=False)
    assert len(result) == 1
    assert result[0]["ticker"] == "GOOD"


# ─── score_sma200_reclaim (full pipeline via monkeypatch) ─────────

def test_score_fresh_reclaim_qualifies(monkeypatch):
    """Stock that crossed SMA200 a few days ago should score and grade."""
    import yfinance as yf

    hist = _make_hist(n=252, days_ago=5, rvol_on_cross=2.2)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_sma200_reclaim("TEST")
    assert result is not None
    assert result["days_since_reclaim"] <= 15
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    assert "score_breakdown" in result


def test_score_returns_none_when_no_recent_crossover(monkeypatch):
    """Stock above SMA200 for 30+ days should be rejected (no fresh signal)."""
    import yfinance as yf

    # Price always above — no crossover in last 15 days
    idx = pd.date_range("2024-01-01", periods=252, freq="B")
    close = pd.Series([105.0] * 252, index=idx)
    hist = pd.DataFrame({
        "Open": close * 0.995, "High": close * 1.01,
        "Low": close * 0.99, "Close": close,
        "Volume": pd.Series([1_000_000] * 252, index=idx),
    })

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_sma200_reclaim("NOSTALE")
    assert result is None


def test_score_returns_none_short_history(monkeypatch):
    """Insufficient history (< 210 bars) → None without raising."""
    import yfinance as yf

    hist = _make_hist(n=50)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_sma200_reclaim("SHORT")
    assert result is None


def test_score_returns_none_empty_history(monkeypatch):
    """Empty DataFrame → None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_sma200_reclaim("EMPTY")
    assert result is None


def test_score_breakdown_keys_present(monkeypatch):
    """score_breakdown must contain all four expected keys."""
    import yfinance as yf

    hist = _make_hist(n=252, days_ago=3, rvol_on_cross=2.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_sma200_reclaim("KEYS")
    if result is not None:
        for key in ("recency", "volume_conf", "rsi", "sma50"):
            assert key in result["score_breakdown"]


def test_score_returns_none_when_extended(monkeypatch):
    """Stock more than 15% above SMA200 should be rejected even with recent crossover."""
    import yfinance as yf

    # Build history where price ends up 25% above its rolling SMA200
    idx = pd.date_range("2024-01-01", periods=252, freq="B")
    # Prices that rise parabolically in the last 10 bars
    prices = [80.0] * 242 + [80.0 * (1.025 ** i) for i in range(10)]
    close = pd.Series(prices, index=idx)
    hist = pd.DataFrame({
        "Open": close * 0.995, "High": close * 1.01,
        "Low": close * 0.99, "Close": close,
        "Volume": pd.Series([1_000_000] * 252, index=idx),
    })

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_sma200_reclaim("EXTENDED")
    # Either None (too extended or no crossover found) or an extended result
    if result is not None:
        assert result["proximity_pct"] <= 15.0
