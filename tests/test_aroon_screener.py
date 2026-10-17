"""Tests for dossier/aroon_screener.py — Aroon Trend Birth Screener."""

import numpy as np
import pandas as pd

from dossier.aroon_screener import _grade, aroon, score_aroon, sessions_since_cross


def _frame(close):
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    c = pd.Series(np.asarray(close, float), index=idx)
    return pd.DataFrame({"Open": c, "High": c * 1.005, "Low": c * 0.995, "Close": c, "Volume": 1e6})


def _birth(n=260):
    """Decline to a low, bounce and fade without undercutting it, then new highs."""
    down = 200 * (0.997 ** np.arange(n - 24))
    low = down[-1]
    bounce = low * np.concatenate([np.linspace(1.01, 1.06, 4), np.linspace(1.06, 1.03, 14)])
    run = bounce[-1] * (1.015 ** np.arange(1, 7))
    return _frame(np.concatenate([down, bounce, run]))


def test_aroon_extremes():
    s = pd.Series(np.arange(1.0, 60.0))
    ar = aroon(s, s)
    assert ar["up"].iloc[-1] == 100.0
    assert ar["down"].iloc[-1] == 0.0
    rev = aroon(s[::-1].reset_index(drop=True), s[::-1].reset_index(drop=True))
    assert rev["up"].iloc[-1] == 0.0


def test_sessions_since_cross():
    up = pd.Series([40.0] * 8 + [60.0, 75.0, 80.0, 90.0])
    assert sessions_since_cross(up) == 2
    assert sessions_since_cross(pd.Series([90.0] * 12)) is None


def test_birth_qualifies():
    r = score_aroon("BORN", _birth())
    assert r is not None
    assert r["aroon_up"] >= 70 and r["aroon_down"] <= 30
    assert r["grade"] == _grade(r["score"])
    assert r["score"] == sum(r["score_breakdown"].values())


def test_downtrend_rejected():
    assert score_aroon("DOWN", _frame(200 * (0.998 ** np.arange(260)))) is None


def test_bad_input_rejected():
    assert score_aroon("NEW", _frame(np.linspace(10, 20, 50))) is None
    assert score_aroon("NONE", pd.DataFrame()) is None
