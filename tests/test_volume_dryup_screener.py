"""Tests for dossier/volume_dryup_screener.py — Volume Dry-Up Screener."""

import pandas as pd
import pytest

from dossier.volume_dryup_screener import (
    _compute_vdu_ratio,
    _ema_score,
    _funnel_filter,
    _high52_score,
    _tightness_score,
    _vdu_score,
    score_vdu,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 200, trend: float = 0.002, vdu_last: float = 0.4,
                tight_tail: bool = True) -> pd.DataFrame:
    """Synthetic OHLCV with a smooth uptrend, a quiet last-day volume, and
    (optionally) a contracted recent trading range."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    avg = 1_000_000
    volume = pd.Series([avg] * n, index=idx)
    volume.iloc[-1] = int(avg * vdu_last)

    if tight_tail:
        range_pct = pd.Series([0.02] * (n - 5) + [0.005] * 5, index=idx)
    else:
        range_pct = pd.Series([0.02] * n, index=idx)

    high = close * (1 + range_pct / 2)
    low = close * (1 - range_pct / 2)
    opens = close * 0.999
    return pd.DataFrame(
        {"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


def _stock(ticker="TEST", price=55.0, ema_20=52.0, sma_50=50.0,
           volume=400_000, avg_vol=1_000_000, rsi=55, adx=28,
           cap=2e9, change_pct=0.5, perf_1w=1.0, market_cap=2e9):
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
        "stoch_k": 55,
        "high_1m": price * 1.05,
        "low_1m": price * 0.95,
        "perf_3m": 10.0,
    }


# ─── _compute_vdu_ratio ───────────────────────────────────────────

def test_compute_vdu_ratio_basic():
    s = _stock(volume=400_000, avg_vol=1_000_000)
    assert _compute_vdu_ratio(s) == pytest.approx(0.4)


def test_compute_vdu_ratio_zero_avg():
    s = _stock(volume=400_000, avg_vol=0)
    assert _compute_vdu_ratio(s) == 1.0


def test_compute_vdu_ratio_normal_day():
    s = _stock(volume=1_000_000, avg_vol=1_000_000)
    assert _compute_vdu_ratio(s) == pytest.approx(1.0)


# ─── _vdu_score ───────────────────────────────────────────────────

def test_vdu_score_deep_dryup():
    assert _vdu_score(0.3) == 35


def test_vdu_score_moderate():
    score = _vdu_score(0.5)
    assert 12 <= score <= 28


def test_vdu_score_borderline_eligible():
    score = _vdu_score(0.65)
    assert 1 <= score <= 12


def test_vdu_score_monotone():
    # Lower ratio (quieter) should score higher than a louder one
    assert _vdu_score(0.3) > _vdu_score(0.5) > _vdu_score(0.65)


# ─── _tightness_score ─────────────────────────────────────────────

def test_tightness_score_hard_contraction():
    assert _tightness_score(atr5=0.5, atr20=1.0) == 25


def test_tightness_score_moderate():
    score = _tightness_score(atr5=0.75, atr20=1.0)
    assert 10 <= score <= 18


def test_tightness_score_expanding_range():
    assert _tightness_score(atr5=1.2, atr20=1.0) == 0


def test_tightness_score_zero_baseline():
    assert _tightness_score(atr5=0.5, atr20=0.0) == 0


def test_tightness_score_monotone():
    assert _tightness_score(1.2, 1.0) < _tightness_score(0.8, 1.0) < _tightness_score(0.4, 1.0)


# ─── _ema_score ───────────────────────────────────────────────────

def test_ema_score_full_stack():
    assert _ema_score(60.0, 55.0, 50.0) == 20


def test_ema_score_price_above_ema20_only():
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


def test_high52_within_12():
    score = _high52_score(90.0, 100.0)
    assert score == 15


def test_high52_far_from_high():
    assert _high52_score(60.0, 100.0) == 0


def test_high52_zero_high():
    assert _high52_score(50.0, 0.0) == 0


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_quiet_coiled_stock():
    s = _stock(volume=400_000, avg_vol=1_000_000, change_pct=1.0, rsi=55)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 1


def test_funnel_cuts_normal_volume():
    # VDU ratio 0.9 — not a meaningful dry-up
    s = _stock(volume=900_000, avg_vol=1_000_000, change_pct=1.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_big_move():
    # Quiet volume but a 6% move — not "coiled", something already happened
    s = _stock(volume=400_000, avg_vol=1_000_000, change_pct=6.0)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_small_cap():
    s = _stock(volume=400_000, avg_vol=1_000_000, change_pct=1.0, cap=1e8)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_overbought_rsi():
    s = _stock(volume=400_000, avg_vol=1_000_000, change_pct=1.0, rsi=85)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_cuts_oversold_rsi():
    s = _stock(volume=400_000, avg_vol=1_000_000, change_pct=1.0, rsi=25)
    result = _funnel_filter([s], verbose=False)
    assert len(result) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


def test_funnel_preserves_multiple():
    stocks = [
        _stock("AAA", volume=350_000, avg_vol=1_000_000, change_pct=0.5, rsi=50),
        _stock("BBB", volume=450_000, avg_vol=1_000_000, change_pct=-1.0, rsi=60),
    ]
    result = _funnel_filter(stocks, verbose=False)
    assert len(result) == 2


# ─── score_vdu (full pipeline via monkeypatch) ────────────────────

def test_score_vdu_quiet_coil_qualifies(monkeypatch):
    """Quiet volume + tight recent range in an uptrend should score and grade."""
    import yfinance as yf

    hist = _make_hist(n=200, trend=0.002, vdu_last=0.3, tight_tail=True)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        volume=int(0.3e6), avg_vol=int(1e6), change_pct=0.8,
        ema_20=float(hist["Close"].iloc[-1] * 0.98),
        sma_50=float(hist["Close"].iloc[-1] * 0.95),
    )
    result = score_vdu("TEST", tv_data=tv)
    assert result is not None
    assert result["vdu_ratio"] <= 0.65
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_vdu_loud_day_returns_none(monkeypatch):
    """Volume at/above the 30d average should not qualify as a dry-up."""
    import yfinance as yf

    hist = _make_hist(n=200, trend=0.002, vdu_last=1.2)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(volume=int(1.2e6), avg_vol=int(1e6), change_pct=1.0)
    result = score_vdu("LOUD", tv_data=tv)
    assert result is None


def test_score_vdu_big_move_returns_none(monkeypatch):
    """Quiet volume but a large move disqualifies (not a coil anymore)."""
    import yfinance as yf

    hist = _make_hist(n=200, trend=0.002, vdu_last=0.3)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(volume=int(0.3e6), avg_vol=int(1e6), change_pct=6.5)
    result = score_vdu("MOVER", tv_data=tv)
    assert result is None


def test_score_vdu_short_history_returns_none(monkeypatch):
    """Insufficient history → must return None without raising."""
    import yfinance as yf

    hist = _make_hist(n=10, vdu_last=0.3)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_vdu("SHORT")
    assert result is None


def test_score_vdu_empty_history_returns_none(monkeypatch):
    """Empty DataFrame → must return None without raising."""
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_vdu("EMPTY")
    assert result is None


def test_score_vdu_a_plus_requires_all_boxes(monkeypatch):
    """A+ grade requires deep dry-up, tight range, full EMA stack, near 52wk high."""
    import yfinance as yf

    hist = _make_hist(n=252, trend=0.003, vdu_last=0.25, tight_tail=True)
    last_close = float(hist["Close"].iloc[-1])

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    tv = _stock(
        volume=int(0.25e6),
        avg_vol=int(1e6),
        change_pct=0.5,
        ema_20=last_close * 0.97,   # price > ema20 > sma50
        sma_50=last_close * 0.93,
        rsi=58,
    )
    result = score_vdu("COILED", tv_data=tv)
    assert result is not None
    assert result["grade"] in ("A+", "A"), f"Expected A+/A, got {result['grade']}"
