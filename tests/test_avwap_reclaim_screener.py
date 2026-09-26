"""Tests for dossier/avwap_reclaim_screener.py — Anchored VWAP Reclaim Screener."""

import pandas as pd
import pytest

from dossier.avwap_reclaim_screener import (
    _anchored_vwap,
    _letter_grade,
    _reclaim_streak,
    _score_reclaim,
    score_avwap_reclaim,
)


# ─── Helpers ──────────────────────────────────────────────────────

def _make_hist(closes: list[float], volumes: list[float] | None = None) -> pd.DataFrame:
    n = len(closes)
    idx = pd.bdate_range("2024-01-01", periods=n)
    vols = volumes or [1_000_000] * n
    df = pd.DataFrame({
        "Open": closes, "High": closes, "Low": closes, "Close": closes, "Volume": vols,
    }, index=idx)
    return df


# ─── _anchored_vwap ─────────────────────────────────────────────────

def test_anchored_vwap_flat_price_equals_price():
    df = _make_hist([100.0] * 5)
    avwap = _anchored_vwap(df, 0)
    assert len(avwap) == 5
    assert avwap == pytest.approx([100.0] * 5)


def test_anchored_vwap_from_middle_ignores_prior_days():
    df = _make_hist([50.0, 50.0, 100.0, 100.0, 100.0])
    avwap = _anchored_vwap(df, 2)
    assert len(avwap) == 3
    assert avwap[0] == pytest.approx(100.0)


def test_anchored_vwap_weights_by_volume():
    # Day 0: price 90, huge volume. Day 1: price 110, tiny volume.
    # VWAP on day 1 should sit much closer to 90 than a simple average (100).
    df = _make_hist([90.0, 110.0], volumes=[1_000_000, 1])
    avwap = _anchored_vwap(df, 0)
    assert avwap[1] < 100.0
    assert avwap[1] == pytest.approx(90.0, abs=0.5)


# ─── _reclaim_streak ─────────────────────────────────────────────────

def test_reclaim_streak_fresh_single_day():
    closes = [10, 9, 8, 12]
    avwap = [10, 10, 10, 10]
    r = _reclaim_streak(closes, avwap, max_lookback=10)
    assert r is not None
    assert r["streak"] == 1
    assert r["reclaim_idx"] == 3


def test_reclaim_streak_multi_day():
    closes = [10, 8, 11, 12, 13]
    avwap = [10, 10, 10, 10, 10]
    r = _reclaim_streak(closes, avwap, max_lookback=10)
    assert r is not None
    assert r["streak"] == 3
    assert r["reclaim_idx"] == 2


def test_reclaim_streak_currently_below_returns_none():
    closes = [10, 12, 8]
    avwap = [10, 10, 10]
    assert _reclaim_streak(closes, avwap, max_lookback=10) is None


def test_reclaim_streak_stale_beyond_lookback_returns_none():
    closes = [10, 8, 11, 12, 13]
    avwap = [10, 10, 10, 10, 10]
    assert _reclaim_streak(closes, avwap, max_lookback=2) is None


def test_reclaim_streak_whole_window_above_cannot_confirm():
    # Never actually observed a dip below within the visible window.
    closes = [12, 13, 14]
    avwap = [10, 10, 10]
    assert _reclaim_streak(closes, avwap, max_lookback=10) is None


def test_reclaim_streak_too_short_series():
    assert _reclaim_streak([10], [10], max_lookback=10) is None


# ─── _letter_grade ──────────────────────────────────────────────────

def test_letter_grade_boundaries():
    assert _letter_grade(80) == "A+"
    assert _letter_grade(65) == "A"
    assert _letter_grade(50) == "B"
    assert _letter_grade(35) == "C"
    assert _letter_grade(34) == "D"


# ─── _score_reclaim ─────────────────────────────────────────────────

def test_score_reclaim_best_case_is_high_grade():
    s = _score_reclaim(pct_above=1.0, streak=1, max_lookback=10,
                        rel_vol_at_reclaim=2.5, above_sma50=True)
    assert s["grade"] in ("A+", "A")
    assert s["score"] > 80


def test_score_reclaim_stale_and_extended_scores_low():
    s = _score_reclaim(pct_above=15.0, streak=10, max_lookback=10,
                        rel_vol_at_reclaim=0.8, above_sma50=False)
    assert s["score"] < 50


def test_score_reclaim_missing_sma_is_neutral_not_punitive():
    with_sma = _score_reclaim(pct_above=1.0, streak=1, max_lookback=10,
                               rel_vol_at_reclaim=1.5, above_sma50=False)
    without_sma = _score_reclaim(pct_above=1.0, streak=1, max_lookback=10,
                                  rel_vol_at_reclaim=1.5, above_sma50=None)
    assert without_sma["trend_pts"] > with_sma["trend_pts"]


# ─── score_avwap_reclaim (integration, mocked yfinance) ──────────────

def test_score_avwap_reclaim_full_flow(monkeypatch):
    import yfinance as yf

    # 100 flat days at 50 (sets the pre-anchor baseline), then: the 52-week
    # low print at 40 on heavy volume, a sharp rally to 70 that pulls the
    # anchored VWAP up fast, a pullback to 50 that dips BELOW that VWAP, and
    # a clean reclaim back above it over the next two sessions.
    closes = [50.0] * 100 + [40.0, 70.0, 50.0, 56.0, 58.0]
    volumes = [1_000_000] * 100 + [5_000_000, 5_000_000, 1_000_000, 2_000_000, 2_000_000]
    hist = _make_hist(closes, volumes)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())

    result = score_avwap_reclaim("TEST", lookback=10)
    assert result is not None
    assert result["ticker"] == "TEST"
    assert result["price"] == pytest.approx(58.0)
    assert result["days_since_reclaim"] == 2
    assert result["anchor_date"] is not None
    assert result["grade"] in ("A+", "A", "B", "C", "D")


def test_score_avwap_reclaim_no_dip_returns_none(monkeypatch):
    import yfinance as yf

    # Straight uptrend, never dips below its own anchored VWAP after the low.
    closes = [50.0 + i * 0.5 for i in range(80)]
    hist = _make_hist(closes)

    class _FakeTicker:
        def history(self, **kwargs):
            return hist

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_avwap_reclaim("TEST") is None


def test_score_avwap_reclaim_empty_history(monkeypatch):
    import yfinance as yf

    class _FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker())
    assert score_avwap_reclaim("EMPTY") is None


def test_score_avwap_reclaim_exception(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "Ticker", lambda sym: (_ for _ in ()).throw(Exception("network error")))
    assert score_avwap_reclaim("BOOM") is None
