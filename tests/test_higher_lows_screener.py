"""Tests for dossier/higher_lows_screener.py — Higher Lows Screener."""

import numpy as np
import pandas as pd

from dossier.higher_lows_screener import (
    _cushion_score,
    _grade,
    _shallow_score,
    _streak_score,
    _trend_score,
    find_staircase,
    score_higher_lows,
)


def _frame(close, dip=0.01):
    s = pd.Series(close, index=pd.bdate_range("2024-01-01", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s * 1.005, "Low": s * (1 - dip),
                         "Close": s, "Volume": 1_000_000.0})


def _climb(n=260):
    # steady ramp: every week's low sits above the last
    return _frame(np.linspace(50.0, 120.0, n))


def test_finds_staircase_in_steady_climb():
    st = find_staircase(_climb())
    assert st is not None
    assert st["steps"] >= 10


def test_broken_by_lower_low():
    close = np.linspace(50.0, 120.0, 260)
    close[-3:] = close[-3] * 0.9  # last week undercuts the prior low
    df = _frame(close)
    st = find_staircase(df)
    assert st is None or st["steps"] < 4


def test_flat_has_no_staircase():
    assert find_staircase(_frame(np.full(120, 100.0))) is None


def test_missing_columns_returns_none():
    assert find_staircase(pd.DataFrame({"Close": [1.0, 2.0]})) is None


def test_score_climb_is_graded_and_shaped():
    r = score_higher_lows("TEST", _climb())
    assert r is not None
    assert r["rising_weeks"] >= 10
    assert r["grade"] in ("A+", "A")
    assert r["score"] == sum(r["score_breakdown"].values())


def test_downtrend_rejected():
    assert score_higher_lows("TEST", _frame(np.linspace(120.0, 50.0, 260))) is None


def test_short_history_rejected():
    assert score_higher_lows("TEST", _frame(np.linspace(50.0, 60.0, 30))) is None


def test_score_bands():
    assert _streak_score(12) > _streak_score(6) > _streak_score(4) > _streak_score(2) == 0
    assert _shallow_score(2) > _shallow_score(6) > _shallow_score(20) == 0
    assert _cushion_score(2) > _cushion_score(8) > _cushion_score(15) == 0
    assert _trend_score(10, 9, 8, 7) == 20
    assert _trend_score(10, 9, 8, None) == 14
    assert _grade(80) == "A+" and _grade(65) == "A" and _grade(50) == "B"
    assert _grade(35) == "C" and _grade(10) == "D"
