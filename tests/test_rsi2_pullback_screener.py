"""Tests for dossier/rsi2_pullback_screener.py — RSI(2) Pullback Screener."""

import numpy as np
import pandas as pd

from dossier.rsi2_pullback_screener import (
    _down_streak,
    _grade,
    _oversold_score,
    _pullback_score,
    _streak_score,
    _trend_score,
    rsi,
    score_rsi2_pullback,
)


def _frame(close):
    s = pd.Series(close, index=pd.bdate_range("2024-01-01", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s, "Low": s, "Close": s, "Volume": 1_000_000.0})


def _dip(n=260, flush=4, step=0.03):
    up = np.linspace(50.0, 120.0, n - flush)
    tail = [up[-1] * (1 - step) ** (i + 1) for i in range(flush)]
    return _frame(np.concatenate([up, tail]))


def test_rsi_bounds_and_flat():
    assert rsi(pd.Series(np.linspace(1, 10, 30))).iloc[-1] == 100.0
    assert rsi(pd.Series(np.full(30, 5.0))).iloc[-1] == 50.0
    assert rsi(pd.Series(np.linspace(10, 1, 30))).iloc[-1] < 1


def test_down_streak():
    assert _down_streak(pd.Series([5, 4, 3, 4, 3, 2.0])) == 2
    assert _down_streak(pd.Series([1, 2, 3.0])) == 0


def test_dip_in_uptrend_scores():
    r = score_rsi2_pullback("TEST", _dip())
    assert r is not None
    assert r["rsi2"] <= 10
    assert r["down_days"] == 4
    assert r["score"] == sum(r["score_breakdown"].values())


def test_steady_uptrend_not_oversold():
    assert score_rsi2_pullback("TEST", _frame(np.linspace(50, 120, 260))) is None


def test_downtrend_rejected():
    assert score_rsi2_pullback("TEST", _frame(np.linspace(120, 50, 260))) is None


def test_short_history_rejected():
    assert score_rsi2_pullback("TEST", _frame(np.linspace(50, 40, 100))) is None


def test_missing_column_rejected():
    assert score_rsi2_pullback("TEST", _frame(np.linspace(50, 40, 300)).drop(columns=["Close"])) is None


def test_component_scores_and_grade():
    assert _oversold_score(1) == 40 and _oversold_score(11) == 0
    assert _trend_score(3, 20) == 25 and _trend_score(-1, 0) == 0
    assert _streak_score(5) == 15 and _streak_score(1) == 0
    assert _pullback_score(8) == 20 and _pullback_score(0) == 0
    assert [_grade(x) for x in (85, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
