"""Tests for dossier/bb_walk_screener.py — Bollinger Band Walk Screener."""

import numpy as np
import pandas as pd

from dossier.bb_walk_screener import _grade, bollinger, mid_streak, score_bb_walk, walk_days


def _frame(close):
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    c = pd.Series(np.asarray(close, float), index=idx)
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": 1_000_000.0})


def _walker(n=260):
    """Quiet drift, then an accelerating run so price hugs the upper band."""
    close, price = [], 100.0
    for i in range(n):
        price *= 1.0005 + (0.0 if i < n - 15 else 0.012 + 0.0004 * (i - (n - 15)))
        close.append(price)
    return _frame(close)


def test_bollinger_pctb_on_flat_series_is_nan_not_error():
    bb = bollinger(pd.Series([10.0] * 40))
    assert bb["pctb"].iloc[-1] != bb["pctb"].iloc[-1]  # NaN


def test_walk_days_counts_upper_zone():
    pctb = pd.Series([0.5] * 5 + [0.9] * 3 + [0.7] * 2)
    assert walk_days(pctb) == 3


def test_mid_streak_stops_at_first_break():
    close = pd.Series([5, 5, 11, 12, 13.0])
    mid = pd.Series([10.0] * 5)
    assert mid_streak(close, mid) == 3


def test_walker_qualifies():
    r = score_bb_walk("WALK", _walker())
    assert r is not None
    assert r["walk_days_10d"] >= 6
    assert r["bandwidth_expansion"] > 1
    assert r["grade"] == _grade(r["score"])
    assert r["score"] == sum(r["score_breakdown"].values())


def test_downtrend_rejected():
    close = 200 * (0.998 ** np.arange(260))
    assert score_bb_walk("DOWN", _frame(close)) is None


def test_short_history_rejected():
    assert score_bb_walk("NEW", _frame(np.linspace(10, 20, 50))) is None
    assert score_bb_walk("NONE", pd.DataFrame()) is None
