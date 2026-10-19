"""Tests for dossier/cmf_screener.py — CMF Accumulation Screener."""

import numpy as np
import pandas as pd

from dossier.cmf_screener import _grade, cmf_series, score_cmf


def _frame(close, close_pos=0.9, n_vol=1e6):
    """Bars whose close sits at `close_pos` of a 2%-wide daily range (1=high, 0=low)."""
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    c = pd.Series(np.asarray(close, float), index=idx)
    rng = c * 0.02
    low = c - close_pos * rng
    return pd.DataFrame({"Open": c, "High": low + rng, "Low": low, "Close": c, "Volume": n_vol})


def _base(n=260):
    return 100 + np.linspace(0, 20, n)  # steady uptrend, above 200 SMA


def test_cmf_bounds_and_sign():
    acc = cmf_series(_frame(_base(), close_pos=0.95)).dropna()
    dist = cmf_series(_frame(_base(), close_pos=0.05)).dropna()
    assert 0.5 < acc.iloc[-1] <= 1.0
    assert -1.0 <= dist.iloc[-1] < -0.5


def test_zero_range_bars_are_safe():
    df = _frame(_base())
    df["High"] = df["Low"] = df["Close"]
    assert cmf_series(df).dropna().iloc[-1] == 0


def test_accumulation_qualifies():
    r = score_cmf("ACC", _frame(_base(), close_pos=0.95))
    assert r is not None
    assert r["grade"] == _grade(r["score"])
    assert r["score"] == sum(r["score_breakdown"].values())


def test_distribution_rejected():
    assert score_cmf("DIST", _frame(_base(), close_pos=0.05)) is None


def test_far_below_high_rejected():
    close = np.concatenate([_base(240), np.linspace(120, 105, 20)])
    assert score_cmf("DROP", _frame(close, close_pos=0.95)) is None


def test_bad_input_rejected():
    assert score_cmf("NEW", _frame(np.linspace(10, 20, 50))) is None
    assert score_cmf("NONE", pd.DataFrame()) is None
