"""Tests for dossier/ichimoku_screener.py — Ichimoku Cloud Breakout Screener."""

import numpy as np
import pandas as pd

from dossier.ichimoku_screener import (
    _chikou_score,
    _cloud_score,
    _fresh_score,
    _grade,
    _reach_score,
    _tk_score,
    compute_ichimoku,
    find_breakout,
    score_ichimoku,
)


def _frame(close):
    close = np.asarray(close, dtype=float)
    s = pd.Series(close, index=pd.bdate_range("2024-01-01", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s * 1.01, "Low": s * 0.99,
                         "Close": s, "Volume": 1_000_000.0})


def _basing_then_pop(pop_days=3):
    # long flat base keeps price inside the cloud, then a jump clears it
    base = np.full(150, 100.0)
    pop = np.linspace(112.0, 118.0, pop_days)
    return _frame(np.concatenate([base, pop]))


def test_fresh_breakout_detected():
    ich = compute_ichimoku(_basing_then_pop())
    bo = find_breakout(ich)
    assert bo is not None
    assert 1 <= bo["bars_above"] <= 3
    assert bo["cloud_top"] < float(ich["close"].iloc[-1])


def test_stale_breakout_rejected():
    # riding above the cloud for 40 bars is not a fresh break
    assert find_breakout(compute_ichimoku(_basing_then_pop(pop_days=40))) is None


def test_inside_cloud_rejected():
    assert score_ichimoku("TEST", _frame(np.full(160, 100.0))) is None


def test_missing_columns_returns_none():
    assert compute_ichimoku(pd.DataFrame({"Close": [1.0, 2.0]})) is None


def test_short_history_rejected():
    assert score_ichimoku("TEST", _frame(np.linspace(50.0, 60.0, 40))) is None


def test_score_shape():
    r = score_ichimoku("TEST", _basing_then_pop())
    assert r is not None
    assert r["score"] == sum(r["score_breakdown"].values())
    assert r["grade"] == _grade(r["score"])
    assert r["bars_above_cloud"] >= 1


def test_score_bands():
    assert _fresh_score(1) > _fresh_score(4) > _fresh_score(6) > _fresh_score(9)
    assert _cloud_score(True, 7) == 25 and _cloud_score(False, 0) == 0
    assert _tk_score(10, 9, 8) == 20 and _tk_score(7, 9, 8) == 12
    assert _chikou_score(10, 8, 9) == 15 and _chikou_score(10, 12, 13) == 0
    assert _reach_score(2) > _reach_score(8) > _reach_score(15) == 0
    assert _grade(80) == "A+" and _grade(65) == "A" and _grade(50) == "B"
    assert _grade(35) == "C" and _grade(10) == "D"
