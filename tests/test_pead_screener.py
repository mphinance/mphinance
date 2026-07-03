"""Tests for dossier/pead_screener.py — Post-Earnings Drift Screener."""

from datetime import date, timedelta

import pandas as pd
import pytest

from dossier.pead_screener import (
    _funnel_filter,
    _letter_grade,
    _recent_earnings_event,
    drift_score,
    gap_score,
    score_pead,
    surprise_score,
    volume_score,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _stock(ticker="TEST", market_cap=2e9, avg_vol_30d=600_000, perf_1w=2.0) -> dict:
    return {
        "ticker": ticker,
        "name": ticker,
        "price": 100.0,
        "change_pct": 1.0,
        "volume": 700_000,
        "avg_vol_30d": avg_vol_30d,
        "market_cap": market_cap,
        "sma_50": 95.0,
        "sma_200": 90.0,
        "rsi": 55.0,
        "earnings_ts": 0,
        "perf_1w": perf_1w,
        "perf_1m": 5.0,
    }


def _fake_earnings_df(days_ago: int, after_hours: bool = True,
                       surprise: float = 10.0, include_future_row: bool = True) -> pd.DataFrame:
    """Build a yfinance-style get_earnings_dates() frame, newest-first."""
    reported_ts = pd.Timestamp(date.today() - timedelta(days=days_ago))
    reported_ts = reported_ts.replace(hour=16 if after_hours else 7)
    rows = {"EPS Estimate": [], "Reported EPS": [], "Surprise(%)": []}
    idx = []

    if include_future_row:
        future_ts = pd.Timestamp(date.today() + timedelta(days=30)).replace(hour=16)
        idx.append(future_ts)
        rows["EPS Estimate"].append(1.5)
        rows["Reported EPS"].append(float("nan"))
        rows["Surprise(%)"].append(float("nan"))

    idx.append(reported_ts)
    rows["EPS Estimate"].append(1.0)
    rows["Reported EPS"].append(1.1)
    rows["Surprise(%)"].append(surprise)

    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx, name="Earnings Date"))


def _fake_history_with_gap(earnings_pos: int, reaction_pos: int, n: int = 70,
                           pre_close: float = 100.0, reaction_close: float = 110.0,
                           current_close: float = 112.0,
                           baseline_vol: float = 500_000, post_vol: float = 900_000) -> pd.DataFrame:
    """Synthetic OHLCV with a flat pre-earnings baseline, a gap at reaction_pos,
    and a flat post-reaction level through to the last bar."""
    idx = pd.bdate_range(end=pd.Timestamp(date.today()), periods=n)
    close = pd.Series(pre_close, index=idx)
    close.iloc[reaction_pos:] = reaction_close
    if reaction_pos + 1 < n:
        close.iloc[reaction_pos + 1:] = current_close
    close.iloc[-1] = current_close if reaction_pos < n - 1 else reaction_close

    volume = pd.Series(baseline_vol, index=idx)
    volume.iloc[reaction_pos:] = post_vol

    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": volume,
    })


def _earnings_date_for(days_since: int, after_hours: bool, n: int = 70):
    """Return (earnings_date, earnings_pos, reaction_pos) consistent with
    _fake_history_with_gap's bdate_range so score_pead sees `days_since`
    trading days between the reaction close and the last bar."""
    idx = pd.bdate_range(end=pd.Timestamp(date.today()), periods=n)
    reaction_pos = (n - 1) - days_since
    earnings_pos = reaction_pos - 1 if after_hours else reaction_pos
    assert earnings_pos >= 31, "not enough room for the pre-earnings baseline window"
    earnings_date = idx[earnings_pos].date()
    days_ago = (date.today() - earnings_date).days
    return earnings_date, earnings_pos, reaction_pos, days_ago


# ─── gap_score ─────────────────────────────────────────────────────

class TestGapScore:
    def test_huge_gap(self):
        assert gap_score(18.0) == 30

    def test_boundary_15(self):
        assert gap_score(15.0) == 30

    def test_boundary_10(self):
        assert gap_score(10.0) == 25

    def test_boundary_7(self):
        assert gap_score(7.0) == 20

    def test_boundary_5(self):
        assert gap_score(5.0) == 14

    def test_boundary_3(self):
        assert gap_score(3.0) == 8

    def test_below_min(self):
        assert gap_score(2.0) == 0

    def test_returns_int(self):
        assert isinstance(gap_score(10.0), int)


# ─── drift_score ────────────────────────────────────────────────────

class TestDriftScore:
    def test_strong_continuation(self):
        assert drift_score(12.0) == 35

    def test_boundary_10(self):
        assert drift_score(10.0) == 35

    def test_boundary_5(self):
        assert drift_score(5.0) == 28

    def test_boundary_2(self):
        assert drift_score(2.0) == 20

    def test_boundary_0(self):
        assert drift_score(0.0) == 12

    def test_mild_fade(self):
        assert drift_score(-2.0) == 4

    def test_boundary_neg3(self):
        assert drift_score(-3.0) == 4

    def test_faded_hard(self):
        assert drift_score(-10.0) == 0


# ─── surprise_score ─────────────────────────────────────────────────

class TestSurpriseScore:
    def test_none_is_neutral(self):
        assert surprise_score(None) == 10

    def test_huge_beat(self):
        assert surprise_score(20.0) == 20

    def test_boundary_8(self):
        assert surprise_score(8.0) == 16

    def test_boundary_3(self):
        assert surprise_score(3.0) == 11

    def test_boundary_0(self):
        assert surprise_score(0.0) == 6

    def test_miss(self):
        assert surprise_score(-5.0) == 0


# ─── volume_score ───────────────────────────────────────────────────

class TestVolumeScore:
    def test_surging(self):
        assert volume_score(2.5) == 15

    def test_boundary_1_5(self):
        assert volume_score(1.5) == 11

    def test_boundary_1_2(self):
        assert volume_score(1.2) == 7

    def test_boundary_1_0(self):
        assert volume_score(1.0) == 3

    def test_declining(self):
        assert volume_score(0.8) == 0


# ─── _letter_grade ───────────────────────────────────────────────────

class TestLetterGrade:
    def test_a_plus(self):
        assert _letter_grade(80) == "A+"

    def test_a(self):
        assert _letter_grade(65) == "A"

    def test_b(self):
        assert _letter_grade(50) == "B"

    def test_c(self):
        assert _letter_grade(35) == "C"

    def test_d(self):
        assert _letter_grade(0) == "D"


# ─── _funnel_filter ──────────────────────────────────────────────────

class TestFunnelFilter:
    def test_liquidity_floor(self):
        stocks = [_stock("BIG", market_cap=5e9, avg_vol_30d=1e6),
                  _stock("TINY", market_cap=1e8, avg_vol_30d=50_000)]
        survivors = _funnel_filter(stocks, verbose=False)
        assert [s["ticker"] for s in survivors] == ["BIG"]

    def test_cratering_cut(self):
        stocks = [_stock("OK", perf_1w=1.0), _stock("CRASH", perf_1w=-20.0)]
        survivors = _funnel_filter(stocks, verbose=False)
        assert [s["ticker"] for s in survivors] == ["OK"]

    def test_missing_perf_kept(self):
        stocks = [_stock("NOPERF")]
        stocks[0]["perf_1w"] = None
        survivors = _funnel_filter(stocks, verbose=False)
        assert len(survivors) == 1


# ─── _recent_earnings_event ──────────────────────────────────────────

def test_recent_earnings_event_within_window(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=5, after_hours=True, surprise=12.5)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    event = _recent_earnings_event("TEST", max_days=16)
    assert event is not None
    assert event["after_hours"] is True
    assert event["surprise_pct"] == 12.5


def test_recent_earnings_event_before_market(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=3, after_hours=False)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    event = _recent_earnings_event("TEST", max_days=16)
    assert event is not None
    assert event["after_hours"] is False


def test_recent_earnings_event_outside_window(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=40)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert _recent_earnings_event("TEST", max_days=16) is None


def test_recent_earnings_event_no_data(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert _recent_earnings_event("TEST", max_days=16) is None


def test_recent_earnings_event_exception(monkeypatch):
    import yfinance as yf
    monkeypatch.setattr(yf, "Ticker", lambda sym: (_ for _ in ()).throw(Exception("network error")))
    assert _recent_earnings_event("TEST", max_days=16) is None


def test_recent_earnings_event_skips_future_row(monkeypatch):
    """The next (unreported) earnings row must be skipped in favor of the past one."""
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=2, include_future_row=True)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    event = _recent_earnings_event("TEST", max_days=16)
    assert event is not None
    assert (date.today() - event["date"]).days == 2


# ─── score_pead (integration) ────────────────────────────────────────

def test_score_pead_qualifying_drift(monkeypatch):
    """Positive gap, continued positive drift → scored result, not None."""
    import yfinance as yf

    earnings_date, e_pos, r_pos, days_ago = _earnings_date_for(days_since=4, after_hours=True)
    hist = _fake_history_with_gap(e_pos, r_pos, pre_close=100.0,
                                  reaction_close=112.0, current_close=120.0)

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=days_ago, after_hours=True, surprise=18.0)

        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_pead("DRIFT", tv_data=_stock("DRIFT"), lookback_days=10)

    assert result is not None
    assert result["gap_pct"] > 0
    assert result["drift_pct"] > 0
    assert result["grade"] in ("A+", "A", "B", "C")
    assert 0 <= result["score"] <= 100
    assert result["name"] == "DRIFT"
    for key in ("gap", "drift", "surprise", "volume"):
        assert key in result["score_breakdown"]


def test_score_pead_faded_gap_rejected(monkeypatch):
    """Small gap, hard fade, weak surprise and drying volume → D grade → None."""
    import yfinance as yf

    earnings_date, e_pos, r_pos, days_ago = _earnings_date_for(days_since=6, after_hours=True)
    hist = _fake_history_with_gap(e_pos, r_pos, pre_close=100.0,
                                  reaction_close=103.0, current_close=95.0,
                                  baseline_vol=500_000, post_vol=400_000)

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=days_ago, after_hours=True, surprise=-2.0)

        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    result = score_pead("FADED", lookback_days=10)
    assert result is None


def test_score_pead_no_earnings_in_window(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=40)

        def history(self, **kwargs):
            return _fake_history_with_gap(35, 36)

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_pead("FAR", lookback_days=10) is None


def test_score_pead_small_gap_rejected(monkeypatch):
    """Reaction under MIN_GAP_PCT should be gated out even with a good surprise."""
    import yfinance as yf

    earnings_date, e_pos, r_pos, days_ago = _earnings_date_for(days_since=2, after_hours=True)
    hist = _fake_history_with_gap(e_pos, r_pos, pre_close=100.0,
                                  reaction_close=101.0, current_close=102.0)

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=days_ago, after_hours=True, surprise=25.0)

        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_pead("SMALLGAP", lookback_days=10) is None


def test_score_pead_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def get_earnings_dates(self, limit=6):
            return _fake_earnings_df(days_ago=3)

        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_pead("EMPTY", lookback_days=10) is None
