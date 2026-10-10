"""Tests for dossier/adx_ignition_screener.py — ADX Trend Ignition Screener."""

import numpy as np
import pandas as pd

from dossier.adx_ignition_screener import (
    _alignment_score,
    _direction_score,
    _fresh_score,
    _grade,
    _room_score,
    _slope_score,
    compute_adx,
    find_ignition,
    score_adx_ignition,
)


def _frame(close, wiggle=0.01):
    close = np.asarray(close, dtype=float)
    s = pd.Series(close, index=pd.bdate_range("2024-01-01", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s * (1 + wiggle), "Low": s * (1 - wiggle),
                         "Close": s, "Volume": 1_000_000.0})


def _chop_with_trend(trend_days):
    # alternating chop keeps ADX low, then a steady climb ignites it
    chop = 100 + np.tile([0.0, 1.0], 60)
    climb = chop[-1] + np.arange(1, trend_days + 1) * 1.5
    return _frame(np.concatenate([chop, climb]), wiggle=0.004)


def _find_ignition_day(frame):
    """Latest prefix length whose last bar is an ignition, scanning the climb."""
    hits = []
    for n in range(125, len(frame) + 1):
        ind = compute_adx(frame.iloc[:n])
        if find_ignition(ind) is not None:
            hits.append(n)
    return hits


def test_chop_then_trend_ignites():
    assert _find_ignition_day(_chop_with_trend(12))


def test_pure_chop_never_ignites():
    frame = _frame(100 + np.tile([0.0, 1.0], 80), wiggle=0.004)
    assert score_adx_ignition("CHOP", frame) is None


def test_downtrend_not_flagged():
    chop = 100 + np.tile([0.0, 1.0], 60)
    frame = _frame(np.concatenate([chop, chop[-1] - np.arange(1, 13) * 1.5]), wiggle=0.004)
    assert not _find_ignition_day(frame)


def test_missing_columns_returns_none():
    assert compute_adx(pd.DataFrame({"Close": [1.0, 2.0]})) is None


def test_short_history_returns_none():
    assert score_adx_ignition("X", _frame(np.linspace(100, 110, 30))) is None


def test_score_result_shape():
    frame = _chop_with_trend(12)
    n = _find_ignition_day(frame)[0]
    r = score_adx_ignition("TEST", frame.iloc[:n])
    assert r is not None
    assert r["adx"] >= 20 and r["plus_di"] > r["minus_di"]
    assert r["score"] == sum(r["score_breakdown"].values())
    assert r["grade"] == _grade(r["score"])


def test_component_scores_monotonic():
    assert _fresh_score(1) > _fresh_score(3) > _fresh_score(5) > _fresh_score(8)
    assert _slope_score(7) > _slope_score(4) > _slope_score(2) > _slope_score(0)
    assert _direction_score(20) > _direction_score(11) > _direction_score(6) > _direction_score(1)
    assert _alignment_score(10, 9, 8) == 20 and _alignment_score(8, 9, 10) == 0
    assert _room_score(25) > _room_score(33) > _room_score(45)


def test_grade_bands():
    assert [_grade(x) for x in (90, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
