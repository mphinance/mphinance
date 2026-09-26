"""Tests for dossier/seasonality_screener.py — Calendar-Month Edge Finder."""

from datetime import date

import pandas as pd
import pytest

from dossier.seasonality_screener import (
    _letter_grade,
    _monthly_returns_by_year,
    _seasonality_stats,
    score_seasonality,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_seasonal_hist(month: int, returns_by_year: dict, base_price: float = 100.0) -> pd.DataFrame:
    """
    Synthetic multi-year daily history. For each (year, return_pct) pair,
    the given month's close ramps linearly from `base_price` to
    `base_price * (1 + return_pct / 100)` across the month's business
    days; every other month is flat at `base_price`.
    """
    frames = []
    for year, ret in sorted(returns_by_year.items()):
        idx = pd.bdate_range(f"{year}-01-01", f"{year}-12-31")
        df = pd.DataFrame(index=idx)
        df["Close"] = base_price
        month_idx = df.index[df.index.month == month]
        n = len(month_idx)
        end_price = base_price * (1 + ret / 100.0)
        ramp = [
            base_price + (end_price - base_price) * i / max(n - 1, 1)
            for i in range(n)
        ]
        df.loc[month_idx, "Close"] = ramp
        df["Open"] = df["Close"]
        df["High"] = df["Close"]
        df["Low"] = df["Close"]
        df["Volume"] = 1_000_000
        frames.append(df)
    return pd.concat(frames).sort_index()


# ─── _monthly_returns_by_year ──────────────────────────────────────

def test_monthly_returns_by_year_basic():
    hist = _make_seasonal_hist(8, {2019: 5.0, 2020: -3.0, 2021: 8.0})
    result = _monthly_returns_by_year(hist, 8)
    assert [r["year"] for r in result] == [2019, 2020, 2021]
    assert result[0]["return_pct"] == pytest.approx(5.0, abs=0.05)
    assert result[1]["return_pct"] == pytest.approx(-3.0, abs=0.05)
    assert result[2]["return_pct"] == pytest.approx(8.0, abs=0.05)


def test_monthly_returns_by_year_excludes_given_year():
    hist = _make_seasonal_hist(8, {2019: 5.0, 2020: -3.0, 2021: 8.0})
    result = _monthly_returns_by_year(hist, 8, exclude_year=2021)
    assert [r["year"] for r in result] == [2019, 2020]


def test_monthly_returns_by_year_skips_thin_month():
    hist = _make_seasonal_hist(8, {2019: 5.0, 2020: -3.0})
    result = _monthly_returns_by_year(hist, 8, min_days_in_month=999)
    assert result == []


def test_monthly_returns_by_year_empty_history():
    assert _monthly_returns_by_year(pd.DataFrame(), 8) == []
    assert _monthly_returns_by_year(None, 8) == []


# ─── _letter_grade ──────────────────────────────────────────────────

def test_letter_grade_boundaries():
    assert _letter_grade(80) == "A+"
    assert _letter_grade(79) == "A"
    assert _letter_grade(65) == "A"
    assert _letter_grade(64) == "B"
    assert _letter_grade(50) == "B"
    assert _letter_grade(49) == "C"
    assert _letter_grade(35) == "C"
    assert _letter_grade(34) == "D"
    assert _letter_grade(0) == "D"


# ─── _seasonality_stats ─────────────────────────────────────────────

def test_seasonality_stats_insufficient_years():
    yearly = [{"year": y, "return_pct": 5.0} for y in range(2020, 2023)]
    assert _seasonality_stats(yearly) is None


def test_seasonality_stats_strong_bullish_edge():
    yearly = [{"year": y, "return_pct": r} for y, r in
              zip(range(2016, 2022), [5.0, 6.0, 4.5, 5.5, 7.0, 6.0])]
    stats = _seasonality_stats(yearly)
    assert stats is not None
    assert stats["direction"] == "bullish"
    assert stats["win_rate"] == 1.0
    assert stats["years_of_data"] == 6
    assert stats["grade"] in ("A", "A+")


def test_seasonality_stats_choppy_low_conviction():
    yearly = [{"year": y, "return_pct": r} for y, r in
              zip(range(2016, 2022), [4.0, -6.0, 1.0, -2.0, 3.0, -5.0])]
    stats = _seasonality_stats(yearly)
    assert stats is not None
    assert stats["win_rate"] < 1.0
    assert stats["score"] < 65


def test_seasonality_stats_bearish_edge():
    yearly = [{"year": y, "return_pct": r} for y, r in
              zip(range(2016, 2022), [-4.0, -5.0, -3.5, -6.0, -4.5, -5.0])]
    stats = _seasonality_stats(yearly)
    assert stats is not None
    assert stats["direction"] == "bearish"
    assert stats["win_rate"] == 1.0


# ─── score_seasonality (integration, mocked yfinance) ────────────────

def test_score_seasonality_full_flow(monkeypatch):
    import yfinance as yf

    month = date.today().month
    current_year = date.today().year
    returns_by_year = {y: 5.0 for y in range(current_year - 6, current_year)}
    returns_by_year[current_year] = 999.0  # in-progress year — must be excluded
    hist = _make_seasonal_hist(month, returns_by_year)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_seasonality("TEST", month=month, lookback_years=10)
    assert result is not None
    assert result["ticker"] == "TEST"
    assert result["month"] == month
    assert all(y["year"] != current_year for y in result["years"])
    assert result["direction"] == "bullish"


def test_score_seasonality_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_seasonality("EMPTY", month=8) is None


def test_score_seasonality_insufficient_years(monkeypatch):
    import yfinance as yf

    month = date.today().month
    current_year = date.today().year
    hist = _make_seasonal_hist(month, {y: 5.0 for y in range(current_year - 2, current_year)})

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_seasonality("SHORT", month=month, lookback_years=10) is None


def test_score_seasonality_exception(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "Ticker", lambda sym: (_ for _ in ()).throw(Exception("network error")))
    assert score_seasonality("BOOM", month=8) is None
