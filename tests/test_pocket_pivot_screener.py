"""Tests for dossier/pocket_pivot_screener.py — Pocket Pivot Screener."""

import pandas as pd
import pytest

from dossier.pocket_pivot_screener import (
    _base_dist_pct,
    _base_proximity_score,
    _funnel_filter,
    _pocket_pivot_ratio,
    _rsi_momentum_score,
    _trend_score,
    _volume_dominance_score,
    score_pocket_pivot,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 60, base_vol: int = 500_000, today_vol: int = 1_500_000,
                worst_down_vol: int = 900_000, close_price: float = 55.0) -> pd.DataFrame:
    """Synthetic OHLCV: a flat/mild-uptrend history where day -3 is a down day
    with `worst_down_vol` volume, and today is an up day with `today_vol`."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([close_price * (1 + 0.0005) ** i for i in range(n)], index=idx)
    volume = pd.Series([base_vol] * n, index=idx)

    # Make day -3 (3rd from the end) a down day with elevated volume
    close.iloc[-3] = close.iloc[-4] * 0.97
    volume.iloc[-3] = worst_down_vol

    # Today is an up day with the pocket-pivot volume
    close.iloc[-1] = close.iloc[-2] * 1.02
    volume.iloc[-1] = today_vol

    high = close * 1.01
    low = close * 0.99
    opens = close * 0.999
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


def _stock(ticker="TEST", price=55.0, ema_20=52.0, sma_50=53.0,
           volume=1_500_000, avg_vol=500_000, rsi=55, adx=28,
           cap=2e9, change_pct=1.5, market_cap=2e9):
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
        "perf_1w": 1.0,
        "perf_1m": 5.0,
        "tv_signal": 0.3,
    }


# ─── _pocket_pivot_ratio ──────────────────────────────────────────

def test_pocket_pivot_ratio_basic():
    hist = _make_hist(today_vol=1_800_000, worst_down_vol=900_000)
    assert _pocket_pivot_ratio(hist) == pytest.approx(2.0, rel=0.01)


def test_pocket_pivot_ratio_below_threshold():
    hist = _make_hist(today_vol=400_000, worst_down_vol=900_000)
    assert _pocket_pivot_ratio(hist) < 1.0


def test_pocket_pivot_ratio_no_down_days():
    # Every day is a flat/up day — no down-day volume to compare against
    idx = pd.date_range("2024-01-01", periods=30, freq="B")
    close = pd.Series([100.0 * 1.001 ** i for i in range(30)], index=idx)
    volume = pd.Series([500_000] * 30, index=idx)
    hist = pd.DataFrame({
        "Open": close * 0.999, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": volume,
    })
    assert _pocket_pivot_ratio(hist) == 0.0


def test_pocket_pivot_ratio_insufficient_history():
    hist = _make_hist(n=5)
    assert _pocket_pivot_ratio(hist) == 0.0


# ─── _volume_dominance_score ──────────────────────────────────────

def test_volume_dominance_score_dominant():
    assert _volume_dominance_score(3.0) == 35


def test_volume_dominance_score_moderate():
    score = _volume_dominance_score(1.5)
    assert 12 <= score <= 28


def test_volume_dominance_score_borderline():
    assert _volume_dominance_score(1.0) == 12


def test_volume_dominance_score_below_bar():
    assert _volume_dominance_score(0.8) == 0


def test_volume_dominance_score_monotone():
    assert _volume_dominance_score(3.0) > _volume_dominance_score(1.5) > _volume_dominance_score(1.0)


# ─── _base_dist_pct ───────────────────────────────────────────────

def test_base_dist_pct_above():
    s = _stock(price=110.0, sma_50=100.0)
    assert _base_dist_pct(s) == pytest.approx(10.0)


def test_base_dist_pct_zero_sma():
    s = _stock(price=110.0, sma_50=0.0)
    assert _base_dist_pct(s) == 999.0


# ─── _base_proximity_score ────────────────────────────────────────

def test_base_proximity_score_ideal():
    assert _base_proximity_score(101.0, 100.0) == 25


def test_base_proximity_score_moderate():
    score = _base_proximity_score(106.0, 100.0)
    assert 10 <= score <= 18


def test_base_proximity_score_below_sma50():
    assert _base_proximity_score(95.0, 100.0) == 0


def test_base_proximity_score_extended():
    assert _base_proximity_score(140.0, 100.0) == 0


def test_base_proximity_score_zero_sma():
    assert _base_proximity_score(100.0, 0.0) == 0


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_full_stack():
    assert _trend_score(60.0, 55.0, 50.0) == 20


def test_trend_score_price_above_ema20_only():
    score = _trend_score(56.0, 55.0, 58.0)
    assert 10 <= score <= 15


def test_trend_score_price_above_sma50_only():
    assert _trend_score(51.0, None, 50.0) == 7


def test_trend_score_below_all():
    assert _trend_score(45.0, 50.0, 52.0) == 0


# ─── _rsi_momentum_score ──────────────────────────────────────────

def test_rsi_momentum_score_sweet_spot():
    assert _rsi_momentum_score(55) == 20


def test_rsi_momentum_score_wider_band():
    assert _rsi_momentum_score(42) == 12


def test_rsi_momentum_score_overbought():
    assert _rsi_momentum_score(85) == 0


def test_rsi_momentum_score_none():
    assert _rsi_momentum_score(None) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_up_day_near_base():
    s = _stock(price=103.0, sma_50=100.0, change_pct=1.0, rsi=55)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_down_day():
    s = _stock(change_pct=-1.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_extended_stock():
    # 40% above SMA50 — already extended, not an early pocket pivot
    s = _stock(price=140.0, sma_50=100.0, change_pct=1.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_below_sma50():
    s = _stock(price=95.0, sma_50=100.0, change_pct=1.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_small_cap():
    s = _stock(change_pct=1.0, cap=1e8)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought_rsi():
    s = _stock(change_pct=1.0, rsi=90)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_preserves_multiple():
    stocks = [
        _stock("AAA", price=103.0, sma_50=100.0, change_pct=0.5, rsi=50),
        _stock("BBB", price=105.0, sma_50=100.0, change_pct=2.0, rsi=60),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── score_pocket_pivot (full pipeline via monkeypatch) ───────────

def test_score_pocket_pivot_qualifies(monkeypatch):
    """A genuine pocket pivot (up day, dominant volume, near the 50-day) scores and grades."""
    import yfinance as yf

    hist = _make_hist(n=80, today_vol=2_000_000, worst_down_vol=900_000, close_price=55.0)
    last_close = float(hist["Close"].iloc[-1])

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        price=last_close,
        volume=int(hist["Volume"].iloc[-1]),
        change_pct=2.0,
        ema_20=last_close * 0.98,
        sma_50=last_close * 0.97,
    )
    result = score_pocket_pivot("TEST", tv_data=tv)
    assert result is not None
    assert result["pocket_pivot_ratio"] >= 1.0
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_pocket_pivot_weak_volume_returns_none(monkeypatch):
    """Volume that doesn't beat the worst recent down day disqualifies."""
    import yfinance as yf

    hist = _make_hist(n=80, today_vol=400_000, worst_down_vol=900_000)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(volume=400_000, change_pct=1.0)
    result = score_pocket_pivot("WEAK", tv_data=tv)
    assert result is None


def test_score_pocket_pivot_down_day_returns_none(monkeypatch):
    """Even with dominant volume, a down day disqualifies (not a pocket pivot)."""
    import yfinance as yf

    hist = _make_hist(n=80, today_vol=2_000_000, worst_down_vol=900_000)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(volume=2_000_000, change_pct=-1.5)
    result = score_pocket_pivot("DOWN", tv_data=tv)
    assert result is None


def test_score_pocket_pivot_short_history_returns_none(monkeypatch):
    """Insufficient history → must return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=5)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_pocket_pivot("SHORT")
    assert result is None


def test_score_pocket_pivot_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → must return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_pocket_pivot("EMPTY")
    assert result is None


def test_score_pocket_pivot_a_plus_requires_all_boxes(monkeypatch):
    """A+ grade requires dominant volume, tight base proximity, full trend
    stack, and healthy (not overbought) RSI."""
    import yfinance as yf

    hist = _make_hist(n=100, today_vol=3_000_000, worst_down_vol=900_000, close_price=60.0)
    last_close = float(hist["Close"].iloc[-1])

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        price=last_close,
        volume=int(hist["Volume"].iloc[-1]),
        change_pct=1.8,
        ema_20=last_close * 0.99,   # price > ema20 > sma50
        sma_50=last_close * 0.98,
        rsi=55,
    )
    result = score_pocket_pivot("PIVOT", tv_data=tv)
    assert result is not None
    assert result["grade"] in ("A+", "A"), f"Expected A+/A, got {result['grade']}"
