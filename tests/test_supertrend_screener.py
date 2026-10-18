"""Tests for dossier/supertrend_screener.py — Supertrend Flip Screener."""

import numpy as np
import pandas as pd

from dossier.supertrend_screener import _grade, score_supertrend, sessions_since_flip, supertrend


def _frame(close):
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    c = pd.Series(np.asarray(close, float), index=idx)
    return pd.DataFrame({"Open": c, "High": c * 1.005, "Low": c * 0.995, "Close": c, "Volume": 1e6})


def _flip(n=260, rally=3):
    """Long decline, then `rally` sharp up sessions so the stop flips underneath."""
    down = 200 * (0.995 ** np.arange(n - rally))
    up = down[-1] * np.cumprod(np.full(rally, 1.12))
    return _frame(np.concatenate([down, up]))


def test_direction_in_trends():
    up = supertrend(_frame(100 * (1.01 ** np.arange(120))))
    assert up["direction"].iloc[-1] == 1
    assert up["line"].iloc[-1] < 100 * 1.01 ** 119
    down = supertrend(_frame(200 * (0.99 ** np.arange(120))))
    assert down["direction"].iloc[-1] == -1


def test_sessions_since_flip():
    d = pd.Series([-1, -1, -1, -1, 1, 1, 1])
    assert sessions_since_flip(d) == 2
    assert sessions_since_flip(pd.Series([1] * 8)) is None
    assert sessions_since_flip(pd.Series([-1, -1, 1, 1, -1])) is None


def test_flip_qualifies():
    r = score_supertrend("FLIP", _flip())
    assert r is not None
    assert r["stop"] < r["price"]
    assert r["grade"] == _grade(r["score"])
    assert r["score"] == sum(r["score_breakdown"].values())


def test_downtrend_rejected():
    assert score_supertrend("DOWN", _frame(200 * (0.998 ** np.arange(260)))) is None


def test_bad_input_rejected():
    assert score_supertrend("NEW", _frame(np.linspace(10, 20, 50))) is None
    assert score_supertrend("NONE", pd.DataFrame()) is None
