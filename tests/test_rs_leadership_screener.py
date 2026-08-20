"""Tests for dossier/rs_leadership_screener.py — RS Leadership Screener."""

import pandas as pd
import pytest

from dossier.rs_leadership_screener import (
    _funnel_filter,
    _leadership_bonus,
    _rs_momentum_score,
    _rs_proximity_score,
    _rs_series,
    _trend_score,
    score_rs_leadership,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 252, trend: float = 0.002) -> pd.DataFrame:
    """Synthetic OHLCV rising at a steady daily trend rate."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    return pd.DataFrame({
        "Open": close * 0.995,
        "High": close * 1.005,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _stock(
    ticker="TEST", price=99.0, ema_20=96.0, sma_50=90.0, sma_200=80.0,
    avg_vol_30d=500_000, rsi=62, adx=28, market_cap=2e9,
    perf_1m=5.0, perf_3m=15.0, perf_6m=20.0,
) -> dict:
    return {
        "ticker": ticker, "name": ticker, "price": price, "change_pct": 0.5,
        "volume": 600_000, "avg_vol_30d": avg_vol_30d, "market_cap": market_cap,
        "sma_200": sma_200, "sma_50": sma_50, "ema_20": ema_20, "rsi": rsi,
        "adx": adx, "perf_1m": perf_1m, "perf_3m": perf_3m, "perf_6m": perf_6m,
    }


# ─── _rs_series ───────────────────────────────────────────────────

def test_rs_series_aligns_on_common_dates():
    idx = pd.date_range("2024-01-01", periods=100, freq="B")
    stock = pd.Series([100.0] * 100, index=idx)
    spy = pd.Series([50.0] * 100, index=idx)
    rs = _rs_series(stock, spy)
    assert rs is not None
    assert len(rs) == 100
    assert rs.iloc[-1] == pytest.approx(2.0)


def test_rs_series_too_short_returns_none():
    idx = pd.date_range("2024-01-01", periods=30, freq="B")
    stock = pd.Series([100.0] * 30, index=idx)
    spy = pd.Series([50.0] * 30, index=idx)
    assert _rs_series(stock, spy) is None


def test_rs_series_partial_overlap():
    idx1 = pd.date_range("2024-01-01", periods=100, freq="B")
    idx2 = pd.date_range("2024-02-01", periods=100, freq="B")
    stock = pd.Series([100.0] * 100, index=idx1)
    spy = pd.Series([50.0] * 100, index=idx2)
    rs = _rs_series(stock, spy)
    assert rs is not None
    assert len(rs) == len(idx1.intersection(idx2))


# ─── _rs_proximity_score ──────────────────────────────────────────

def test_rs_prox_score_at_high():
    assert _rs_proximity_score(0.2) == 35


def test_rs_prox_score_far():
    assert _rs_proximity_score(9.0) == 0


def test_rs_prox_score_monotone():
    assert _rs_proximity_score(8.0) < _rs_proximity_score(4.0) < _rs_proximity_score(1.0) < _rs_proximity_score(0.3)


# ─── _rs_momentum_score ───────────────────────────────────────────

def test_rs_momentum_strong():
    assert _rs_momentum_score(15.0) == 25


def test_rs_momentum_negative():
    assert _rs_momentum_score(-3.0) == 0


def test_rs_momentum_monotone():
    assert _rs_momentum_score(-1.0) < _rs_momentum_score(0.0) < _rs_momentum_score(6.0) < _rs_momentum_score(12.0)


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_full_stack():
    assert _trend_score(100.0, 96.0, 90.0, 80.0) == 25


def test_trend_score_below_all():
    assert _trend_score(80.0, 90.0, 92.0, 95.0) == 0


def test_trend_score_nan_sma200():
    score = _trend_score(100.0, 96.0, 90.0, float("nan"))
    assert score < 25


# ─── _leadership_bonus ────────────────────────────────────────────

def test_leadership_bonus_early_divergence():
    # RS at new high, price still 5% below its own recent high
    assert _leadership_bonus(rs_dist_pct=0.5, price_dist_pct=5.0) == 15


def test_leadership_bonus_confirmed_together():
    # RS at new high, price also near its own high
    assert _leadership_bonus(rs_dist_pct=0.5, price_dist_pct=1.0) == 7


def test_leadership_bonus_no_rs_high():
    assert _leadership_bonus(rs_dist_pct=6.0, price_dist_pct=8.0) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_candidate():
    s = _stock(price=97.0, ema_20=95.0, market_cap=2e9, avg_vol_30d=500_000)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=5e7)
    assert _funnel_filter([s], verbose=False) == []


def test_funnel_cuts_illiquid():
    s = _stock(avg_vol_30d=10_000)
    assert _funnel_filter([s], verbose=False) == []


def test_funnel_cuts_price_below_ema20():
    s = _stock(price=80.0, ema_20=90.0)
    assert _funnel_filter([s], verbose=False) == []


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


# ─── score_rs_leadership (full pipeline via monkeypatch) ──────────

def test_score_rs_leadership_outperformer_qualifies(monkeypatch):
    """Stock rising faster than SPY should build a rising RS line and score."""
    import yfinance as yf

    stock_hist = _make_hist(n=252, trend=0.004)
    spy_hist = _make_hist(n=252, trend=0.0008)

    class _FakeTicker:
        def __init__(self, sym):
            self.sym = sym

        def history(self, **kwargs):
            return stock_hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(sym))

    last_close = float(stock_hist["Close"].iloc[-1])
    tv = _stock(price=last_close, ema_20=last_close * 0.97, sma_50=last_close * 0.9, sma_200=last_close * 0.8)
    result = score_rs_leadership("TEST", spy_hist, tv_data=tv)
    assert result is not None
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100
    # Outperforming SPY the whole way → RS ratio should be near its own high
    assert result["dist_to_rs_high_pct"] < 5.0


def test_score_rs_leadership_underperformer_low_score(monkeypatch):
    """Stock rising slower than SPY should have a falling RS line."""
    import yfinance as yf

    stock_hist = _make_hist(n=252, trend=0.0005)
    spy_hist = _make_hist(n=252, trend=0.004)

    class _FakeTicker:
        def history(self, **kwargs):
            return stock_hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    last_close = float(stock_hist["Close"].iloc[-1])
    tv = _stock(price=last_close)
    result = score_rs_leadership("LAGGARD", spy_hist, tv_data=tv)
    assert result is not None
    assert result["rs_new_high"] is False


def test_score_rs_leadership_short_history_returns_none(monkeypatch):
    import yfinance as yf

    stock_hist = _make_hist(n=30)
    spy_hist = _make_hist(n=252)

    class _FakeTicker:
        def history(self, **kwargs):
            return stock_hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_rs_leadership("SHORT", spy_hist)
    assert result is None


def test_score_rs_leadership_empty_history_returns_none(monkeypatch):
    import yfinance as yf

    spy_hist = _make_hist(n=252)

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_rs_leadership("EMPTY", spy_hist)
    assert result is None


def test_score_rs_leadership_score_breakdown_keys(monkeypatch):
    import yfinance as yf

    stock_hist = _make_hist(n=252, trend=0.003)
    spy_hist = _make_hist(n=252, trend=0.001)

    class _FakeTicker:
        def history(self, **kwargs):
            return stock_hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    last_close = float(stock_hist["Close"].iloc[-1])
    result = score_rs_leadership("BREAKDOWN", spy_hist, tv_data=_stock(price=last_close))
    assert result is not None
    for key in ("rs_proximity", "rs_momentum", "trend", "leadership_timing"):
        assert key in result["score_breakdown"]
