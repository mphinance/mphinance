"""Tests for dossier/dividend_growth_screener.py — Dividend Growth Screener."""

import math

import pandas as pd
import pytest

from dossier.dividend_growth_screener import (
    _dividend_growth_streak,
    _funnel_filter,
    _payout_score,
    _resolve_yield_pct,
    _streak_score,
    _trend_score,
    _yield_score,
    score_dividend_growth,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(n: int = 252, price: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([price] * n, index=idx)
    return pd.DataFrame({
        "Open": close * 0.995,
        "High": close * 1.01,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _make_dividends(yearly_amounts: dict[int, float]) -> pd.Series:
    """Build a synthetic quarterly dividend series that sums to `yearly_amounts` per year."""
    dates = []
    values = []
    for year, total in sorted(yearly_amounts.items()):
        per_payment = total / 4
        for month in (2, 5, 8, 11):
            dates.append(pd.Timestamp(year=year, month=month, day=15))
            values.append(per_payment)
    return pd.Series(values, index=pd.DatetimeIndex(dates))


def _stock(
    ticker="TEST",
    price=100.0,
    sma_200=90.0,
    rsi=55,
    market_cap=5e9,
    perf_1y=10.0,
    perf_3m=3.0,
    tv_yield_pct=3.0,
) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": price,
        "change_pct": 0.2,
        "volume": 500_000,
        "avg_vol_30d": 400_000,
        "market_cap": market_cap,
        "sector": "Consumer Defensive",
        "tv_yield_pct": tv_yield_pct,
        "sma_200": sma_200,
        "rsi": rsi,
        "perf_1y": perf_1y,
        "perf_3m": perf_3m,
    }


# ─── _resolve_yield_pct ───────────────────────────────────────────

def test_resolve_yield_prefers_rate_over_price():
    info = {"dividendRate": 2.0, "dividendYield": 0.5}
    assert _resolve_yield_pct(info, price=100.0, tv_yield_pct=1.0) == pytest.approx(2.0)


def test_resolve_yield_falls_back_to_decimal_field():
    info = {"dividendYield": 0.025}
    assert _resolve_yield_pct(info, price=100.0, tv_yield_pct=None) == pytest.approx(2.5)


def test_resolve_yield_falls_back_to_already_scaled_field():
    # Some yfinance versions ship dividendYield already as a percentage (e.g. 2.5, not 0.025)
    info = {"dividendYield": 2.5}
    assert _resolve_yield_pct(info, price=100.0, tv_yield_pct=None) == pytest.approx(2.5)


def test_resolve_yield_falls_back_to_tv_field():
    info = {}
    assert _resolve_yield_pct(info, price=100.0, tv_yield_pct=3.4) == pytest.approx(3.4)


def test_resolve_yield_none_when_no_data():
    assert _resolve_yield_pct({}, price=100.0, tv_yield_pct=None) is None


# ─── _dividend_growth_streak ──────────────────────────────────────

def test_streak_counts_consecutive_raises():
    div = _make_dividends({2020: 1.0, 2021: 1.1, 2022: 1.2, 2023: 1.3, 2024: 1.4})
    streak, cagr = _dividend_growth_streak(div, as_of_year=2026)
    assert streak == 4
    assert cagr > 0


def test_streak_breaks_on_a_cut():
    div = _make_dividends({2020: 1.0, 2021: 1.1, 2022: 0.9, 2023: 1.0, 2024: 1.1})
    streak, _ = _dividend_growth_streak(div, as_of_year=2026)
    # 2024 > 2023 and 2023 > 2022 extend the streak; 2022 < 2021 stops it there.
    assert streak == 2


def test_streak_drops_in_progress_current_year():
    # 2026 (as_of_year) has a lower partial-year total than 2025 — must be excluded, not
    # read as a cut.
    div = _make_dividends({2023: 1.0, 2024: 1.1, 2025: 1.2, 2026: 0.3})
    streak, _ = _dividend_growth_streak(div, as_of_year=2026)
    assert streak == 2


def test_streak_zero_for_empty_series():
    assert _dividend_growth_streak(None) == (0, 0.0)
    assert _dividend_growth_streak(pd.Series(dtype=float)) == (0, 0.0)


def test_streak_zero_for_single_year():
    div = _make_dividends({2024: 1.0})
    streak, cagr = _dividend_growth_streak(div, as_of_year=2026)
    assert streak == 0
    assert cagr == 0.0


def test_streak_caps_cagr_lookback_at_5_years():
    div = _make_dividends({
        2015: 1.0, 2016: 1.05, 2017: 1.1, 2018: 1.15, 2019: 1.2,
        2020: 1.25, 2021: 1.3, 2022: 1.35, 2023: 1.4, 2024: 1.45,
    })
    streak, cagr = _dividend_growth_streak(div, as_of_year=2026)
    assert streak == 9
    assert cagr > 0


# ─── _yield_score ─────────────────────────────────────────────────

def test_yield_score_sweet_spot():
    assert _yield_score(3.0) == 25


def test_yield_score_too_low():
    assert _yield_score(0.8) == 4


def test_yield_score_too_high_is_a_trap_signal():
    assert _yield_score(8.5) == 4


def test_yield_score_none_or_zero():
    assert _yield_score(None) == 0
    assert _yield_score(0) == 0


def test_yield_score_moderately_high():
    assert _yield_score(6.0) == 18


# ─── _streak_score ────────────────────────────────────────────────

def test_streak_score_monotone():
    assert _streak_score(0) < _streak_score(1) < _streak_score(5) < _streak_score(10)


def test_streak_score_caps_at_30():
    assert _streak_score(25) == 30


# ─── _payout_score ────────────────────────────────────────────────

def test_payout_score_sustainable_band():
    assert _payout_score(45.0) == 25


def test_payout_score_over_100_is_red_flag():
    assert _payout_score(120.0) == 0


def test_payout_score_unreported_gets_partial_credit():
    assert _payout_score(None) == 10
    assert _payout_score(0) == 10


def test_payout_score_high_but_under_100():
    assert _payout_score(90.0) == 5


# ─── _trend_score ─────────────────────────────────────────────────

def test_trend_score_above_sma200_and_positive_year():
    assert _trend_score(100.0, 90.0, 5.0) == 20


def test_trend_score_below_sma200_and_negative_year():
    assert _trend_score(80.0, 90.0, -15.0) == 0


def test_trend_score_nan_sma200_does_not_crash():
    score = _trend_score(100.0, float("nan"), 5.0)
    assert score == 8   # only the perf_1y >= 0 component


# ─── _funnel_filter ───────────────────────────────────────────────

def test_funnel_passes_healthy_candidate():
    s = _stock(price=100.0, sma_200=90.0, rsi=55, market_cap=5e9, perf_1y=10.0)
    assert len(_funnel_filter([s], verbose=False)) == 1


def test_funnel_cuts_small_cap():
    s = _stock(market_cap=2e8)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_price_below_sma200():
    s = _stock(price=80.0, sma_200=90.0)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_distressed_rsi():
    s = _stock(rsi=20)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_cuts_deep_drawdown():
    s = _stock(perf_1y=-40.0)
    assert len(_funnel_filter([s], verbose=False)) == 0


def test_funnel_empty_input():
    assert _funnel_filter([], verbose=False) == []


# ─── score_dividend_growth (full pipeline via monkeypatch) ────────

class _FakeTicker:
    def __init__(self, hist, info, dividends):
        self._hist = hist
        self.info = info
        self.dividends = dividends

    def history(self, **kwargs):
        return self._hist


def test_score_dividend_growth_qualifies(monkeypatch):
    import yfinance as yf

    hist = _make_hist(price=100.0)
    info = {"dividendRate": 3.0, "payoutRatio": 0.45}
    dividends = _make_dividends({2020: 1.0, 2021: 1.1, 2022: 1.2, 2023: 1.3, 2024: 1.4})

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist, info, dividends))

    tv = _stock(price=100.0, sma_200=90.0, perf_1y=10.0)
    result = score_dividend_growth("TEST", tv_data=tv)
    assert result is not None
    assert result["yield_pct"] == pytest.approx(3.0)
    assert result["growth_streak_years"] == 4
    assert result["grade"] in ("A+", "A", "B", "C", "D")
    assert 0 <= result["score"] <= 100


def test_score_dividend_growth_no_dividend_returns_none(monkeypatch):
    import yfinance as yf

    hist = _make_hist(price=100.0)
    info = {"dividendRate": None, "dividendYield": None}
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist, info, pd.Series(dtype=float)))

    result = score_dividend_growth("NODIV", tv_data=_stock(tv_yield_pct=None))
    assert result is None


def test_score_dividend_growth_short_history_returns_none(monkeypatch):
    import yfinance as yf

    hist = _make_hist(n=30)
    info = {"dividendRate": 2.0}
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist, info, pd.Series(dtype=float)))

    result = score_dividend_growth("SHORT")
    assert result is None


def test_score_dividend_growth_empty_history_returns_none(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(
        yf, "Ticker", lambda sym: _FakeTicker(pd.DataFrame(), {}, pd.Series(dtype=float))
    )
    result = score_dividend_growth("EMPTY")
    assert result is None


def test_score_dividend_growth_score_breakdown_keys(monkeypatch):
    import yfinance as yf

    hist = _make_hist(price=50.0)
    info = {"dividendRate": 1.5, "payoutRatio": 0.3}
    dividends = _make_dividends({2022: 0.5, 2023: 0.55, 2024: 0.6})
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist, info, dividends))

    tv = _stock(price=50.0)
    result = score_dividend_growth("BREAKDOWN", tv_data=tv)
    assert result is not None
    for key in ("yield", "growth_streak", "payout_safety", "trend"):
        assert key in result["score_breakdown"]
