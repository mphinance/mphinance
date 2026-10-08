"""Tests for dossier/ttm_squeeze_screener.py — TTM Squeeze Screener."""

import numpy as np
import pandas as pd

from dossier.ttm_squeeze_screener import (
    _duration_score,
    _grade,
    _momentum_score,
    _run_length,
    _tightness_score,
    _trend_score,
    score_ttm_squeeze,
    squeeze_series,
)


def _frame(close, wick=1.0):
    s = pd.Series(close, index=pd.bdate_range("2024-01-01", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s + wick, "Low": s - wick, "Close": s, "Volume": 1e6})


def _coil(n=260, calm=25):
    """Choppy uptrend (wide ranges, wide bands) then a flat, quiet coil."""
    rng = np.random.default_rng(1)
    up = np.linspace(50, 120, n - calm) + rng.normal(0, 1.5, n - calm)
    df_up = _frame(up, wick=0.5)
    df_calm = _frame(np.full(calm, up[-1]) + np.linspace(0, 0.5, calm), wick=0.5)
    df_calm.index = pd.bdate_range(df_up.index[-1] + pd.Timedelta(days=1), periods=calm)
    return pd.concat([df_up, df_calm])


def test_run_length():
    assert _run_length([False, True, True]) == 2
    assert _run_length([True, False]) == 0


def test_flat_coil_is_squeezing():
    r = score_ttm_squeeze("TEST", _coil())
    assert r is not None
    assert r["state"] == "squeezing"
    assert r["squeeze_bars"] >= 3
    assert r["score"] == sum(r["score_breakdown"].values())


def test_squeeze_series_flags_flat_tail():
    on, _ = squeeze_series(_coil())
    assert bool(on.iloc[-1])


def test_fired_after_release():
    df = _coil(calm=25)
    last = float(df["Close"].iloc[-1])
    ext = _frame(last + np.array([6.0, 12.0]), wick=0.5)
    ext.index = pd.bdate_range(df.index[-1] + pd.Timedelta(days=1), periods=2)
    r = score_ttm_squeeze("TEST", pd.concat([df, ext]))
    assert r is not None and r["state"] == "fired"
    assert 1 <= r["bars_since_fire"] <= 3


def test_wide_ranges_no_squeeze():
    rng = np.random.default_rng(2)
    assert score_ttm_squeeze("TEST", _frame(100 + rng.normal(0, 4, 260).cumsum() * 0.2, wick=0.2)) is None


def test_short_history_and_missing_cols():
    assert score_ttm_squeeze("TEST", _frame(np.linspace(50, 40, 100))) is None
    assert score_ttm_squeeze("TEST", _coil().drop(columns=["High"])) is None


def test_component_scores_and_grade():
    assert _duration_score(25) == 30 and _duration_score(2) == 0
    assert _tightness_score(0.5) == 25 and _tightness_score(0.99) == 5
    assert _momentum_score(1, 0) == 25 and _momentum_score(-1, -2) == 10 and _momentum_score(-2, -1) == 0
    assert _trend_score(True, True) == 20 and _trend_score(False, False) == 0
    assert [_grade(x) for x in (85, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
