"""Tests for dossier/rvol_screener.py — Relative Volume Breakout Screener."""

import pandas as pd
import pytest

from dossier.rvol_screener import (
    _compute_rvol,
    _ema_score,
    _funnel_filter,
    _high52_score,
    _price_conf_score,
    _rvol_score,
    score_rvol,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 120, trend: float = 0.003, rvol_last: float = 3.0) -> pd.DataFrame:
    """Synthetic OHLCV with a smooth uptrend and an elevated last-day volume."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    high = close * 1.01
    low = close * 0.99
    opens = close * 0.995
    avg = 1_000_000
    volume = pd.Series([avg] * n, index=idx)
    volume.iloc[-1] = int(avg * rvol_last)
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


def _stock(ticker="TEST", price=55.0, ema_20=52.0, sma_50=50.0,
           volume=3_000_000, avg_vol=1_000_000, rsi=55, adx=28,
           cap=2e9, change_pct=2.5, perf_1w=3.0, market_cap=2e9):
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": change_pct,
        "volume": volume,
        "avg_vol_30d": avg_vol,
        "market_cap": cap,
        "sma_200": price * 0.85,
        "sma_50": sma_50,
        "ema_20": ema_20,
        "rsi": rsi,
        "adx": adx,
        "atr": price * 0.015,
        "perf_1w": perf_1w,
        "perf_1m": 5.0,
        "tv_signal": 0.3,
        "stoch_k": 60,
        "high_1m": price * 1.05,
        "low_1m": price * 0.95,
        "perf_3m": 10.0,
    }


# ─── _compute_rvol ────────────────────────────────────────────────

def test_compute_rvol_basic():
    s = _stock(volume=3_000_000, avg_vol=1_000_000)
    assert _compute_rvol(s) == pytest.approx(3.0)


def test_compute_rvol_zero_avg():
    s = _stock(volume=5_000_000, avg_vol=0)
    assert _compute_rvol(s) == 0.0


def test_compute_rvol_normal_day():
    s = _stock(volume=1_000_000, avg_vol=1_000_000)
    assert _compute_rvol(s) == pytest.approx(1.0)


# ─── _rvol_score ──────────────────────────────────────────────────

def test_rvol_score_high():
    assert _rvol_score(5.5) == 35


def test_rvol_score_medium():
    score = _rvol_score(3.0)
    assert 20 <= score <= 28


def test_rvol_score_low_eligible():
    score = _rvol_score(1.9)
    assert 1 <= score <= 12


def test_rvol_score_monotone():
    assert _rvol_score(2.0) < _rvol_score(3.0) < _rvol_score(5.0)


# ─── _price_conf_score ────────────────────────────────────────────

def test_price_conf_score_strong():
    assert _price_conf_score(4.5) == 25


def test_price_conf_score_moderate():
    score = _price_conf_score(2.0)
    assert 14 <= score <= 20


def test_price_conf_score_weak():
    score = _price_conf_score(0.3)
    assert 1 <= score <= 8


def test_price_conf_score_monotone():
    assert _price_conf_score(0.3) < _price_conf_score(1.5) < _price_conf_score(4.0)


# ─── _ema_score ───────────────────────────────────────────────────

def test_ema_score_full_stack():
    # price > ema20 > sma50 → full points
    assert _ema_score(60.0, 55.0, 50.0) == 20


def test_ema_score_price_above_ema20_only():
    # price > ema20 but ema20 < sma50
    score = _ema_score(56.0, 55.0, 58.0)
    assert 10 <= score <= 15


def test_ema_score_price_above_sma50_only():
    score = _ema_score(51.0, None, 50.0)
    assert 5 <= score <= 10


def test_ema_score_price_below_all():
    assert _ema_score(45.0, 50.0, 52.0) == 0


# ─── _high52_score ────────────────────────────────────────────────

def test_high52_near_breakout():
    assert _high52_score(98.0, 100.0) == 20


def test_high52_within_10():
    score = _high52_score(93.0, 100.0)
    assert score == 15


def test_high52_far_from_high():
    assert _high52_score(65.0, 100.0) == 0


def test_high52_at_high():
    assert _high52_score(100.0, 100.0) == 20


def test_high52_zero_high():
    assert _high52_score(50.0, 0.0) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_rvol():
    s = _stock(volume=2_500_000, avg_vol=1_000_000, change_pct=2.0, rsi=55, perf_1w=4)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_low_rvol():
    # RVol 1.2× — below 1.8× threshold
    s = _stock(volume=1_200_000, avg_vol=1_000_000, change_pct=1.5)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_negative_change():
    # Volume surge on a DOWN day — not a bullish signal
    s = _stock(volume=3_000_000, avg_vol=1_000_000, change_pct=-1.5)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_small_cap():
    s = _stock(volume=3_000_000, avg_vol=1_000_000, change_pct=2.0, cap=1e8)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought_rsi():
    s = _stock(volume=3_000_000, avg_vol=1_000_000, change_pct=2.0, rsi=82)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_parabolic_weekly():
    # +20% in a week — already extended
    s = _stock(volume=3_000_000, avg_vol=1_000_000, change_pct=2.0, perf_1w=20)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_preserves_multiple():
    stocks = [
        _stock("AAA", volume=2_200_000, avg_vol=1_000_000, change_pct=1.5, rsi=50),
        _stock("BBB", volume=4_000_000, avg_vol=1_000_000, change_pct=3.0, rsi=60),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── score_rvol (full pipeline via monkeypatch) ───────────────────

def test_score_rvol_uptrend_qualifies(monkeypatch):
    """Clean uptrend with 3× RVol + 2.5% up-day should score and grade."""
    import yfinance as yf
    from dossier import rvol_screener

    hist = _make_hist(n=200, trend=0.003, rvol_last=3.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        volume=int(3e6), avg_vol=int(1e6), change_pct=2.5,
        ema_20=float(hist["Close"].iloc[-1] * 0.98),
        sma_50=float(hist["Close"].iloc[-1] * 0.95),
    )
    result = score_rvol("TEST", tv_data=tv)
    assert result is not None
    assert result["rvol"] >= 1.8
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_rvol_down_day_returns_none(monkeypatch):
    """A volume surge on a down day should not qualify."""
    import yfinance as yf

    hist = _make_hist(n=200, trend=-0.002, rvol_last=4.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(volume=int(4e6), avg_vol=int(1e6), change_pct=-1.5)
    result = score_rvol("DOWN", tv_data=tv)
    assert result is None


def test_score_rvol_short_history_returns_none(monkeypatch):
    """Insufficient history → must return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=30, rvol_last=3.0)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_rvol("SHORT")
    assert result is None


def test_score_rvol_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → must return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_rvol("EMPTY")
    assert result is None


def test_score_rvol_a_plus_requires_all_boxes(monkeypatch):
    """A+ grade requires strong RVol, up day, full EMA stack, near 52wk high."""
    import yfinance as yf
    from dossier import rvol_screener

    hist = _make_hist(n=252, trend=0.004, rvol_last=6.0)
    last_close = float(hist["Close"].iloc[-1])

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        volume=int(6e6),
        avg_vol=int(1e6),
        change_pct=4.5,
        ema_20=last_close * 0.97,   # price > ema20 > sma50
        sma_50=last_close * 0.93,
        rsi=62,
    )
    result = score_rvol("ROCKETSHIP", tv_data=tv)
    assert result is not None
    assert result["grade"] in ("A+", "A"), f"Expected A+/A, got {result['grade']}"
