"""Tests for dossier/resilience_screener.py — Resilience Screener."""

import numpy as np
import pandas as pd

from dossier.resilience_screener import (
    _down_score,
    _grade,
    _hold_score,
    _trend_score,
    _up_score,
    capture_stats,
    score_resilience,
)


def _series(rets, start=100.0):
    idx = pd.bdate_range("2024-01-01", periods=len(rets) + 1)
    return pd.Series(start * np.cumprod(np.r_[1.0, 1.0 + np.asarray(rets)]), index=idx)


def _market(n=260):
    # alternating -1% / +1% days with a little drift: plenty of SPY down days
    return np.where(np.arange(n) % 2 == 0, -0.01, 0.0105)


def test_defensive_stock_scores_high():
    m = _market()
    spy = _series(m)
    # ignores selloffs, still rises with the rally
    stock = _series(np.where(m < 0, 0.002, 0.012))
    r = score_resilience("TEST", stock, spy)
    assert r is not None
    assert r["down_capture"] < 0
    assert r["grade"] in ("A+", "A")
    assert r["score"] == sum(r["score_breakdown"].values())


def test_high_beta_stock_rejected():
    m = _market()
    assert score_resilience("TEST", _series(m * 1.5), _series(m)) is None


def test_too_few_down_days_returns_none():
    spy = _series(np.full(200, 0.001))
    assert capture_stats(pd.DataFrame({"stock": np.full(120, 0.001), "spy": np.full(120, 0.001)})) is None
    assert score_resilience("TEST", _series(np.full(200, 0.002)), spy) is None


def test_short_history_rejected():
    m = _market(60)
    assert score_resilience("TEST", _series(m), _series(m)) is None


def test_capture_stats_values():
    rets = pd.DataFrame({"spy": [-0.01] * 8 + [0.01] * 4,
                         "stock": [-0.005] * 8 + [0.02] * 4})
    st = capture_stats(rets)
    assert st["down_days"] == 8
    assert abs(st["down_capture"] - 0.5) < 1e-9
    assert abs(st["up_capture"] - 2.0) < 1e-9
    assert st["hold_rate"] == 0.0  # fell exactly half as much: not strictly better


def test_score_bands():
    assert _down_score(-0.2) > _down_score(0.5) > _down_score(0.8) > _down_score(1.5) == 0
    assert _hold_score(0.8) > _hold_score(0.55) > _hold_score(0.1) == 0
    assert _up_score(1.3) > _up_score(1.0) > _up_score(0.7) > _up_score(None) == 0
    assert _trend_score(10, 9, 8) == 15
    assert _trend_score(10, 9, None) == 9
    assert _grade(80) == "A+" and _grade(65) == "A" and _grade(50) == "B"
    assert _grade(35) == "C" and _grade(10) == "D"
