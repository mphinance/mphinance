"""Tests for dossier/rsi_divergence_screener.py — Bullish RSI Divergence Screener."""

import numpy as np
import pandas as pd

from dossier.rsi_divergence_screener import (
    _grade,
    compute_rsi,
    find_swing_lows,
    score_rsi_divergence,
)


def _frame(close, low=None):
    close = np.asarray(close, dtype=float)
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    s = pd.Series(close, index=idx)
    lo = s * 0.995 if low is None else pd.Series(np.asarray(low, float), index=idx)
    return pd.DataFrame({"Open": s, "High": s * 1.005, "Low": lo, "Close": s,
                         "Volume": np.full(len(close), 1_000_000.0)})


def _divergent_closes():
    """Fast crash to a deep low, bounce, slow grind to a slightly lower low, small lift."""
    path = list(np.linspace(130, 100, 12))        # sharp drop: RSI deeply oversold
    path += list(np.linspace(100, 112, 12))        # bounce
    path += list(np.linspace(112, 99, 30))         # slow grind lower: RSI holds up
    path += [99.5, 100.5, 101.5, 102.5]            # lift off the 2nd low
    return np.array([130.0] * 40 + path)


def test_rsi_bounds_and_flat_series():
    rsi = compute_rsi(pd.Series(np.linspace(1, 50, 60)))
    assert rsi.iloc[-1] == 100.0
    assert compute_rsi(pd.Series(np.full(40, 10.0))).iloc[-1] == 50.0


def test_swing_low_requires_strictly_lower_than_both_sides():
    low = pd.Series([5, 4, 3, 2, 3, 4, 5, 6, 7.0])
    assert find_swing_lows(low, side=3) == [3]
    assert find_swing_lows(pd.Series([3.0] * 9), side=3) == []


def test_divergence_detected():
    r = score_rsi_divergence("T", _frame(_divergent_closes()))
    assert r is not None
    assert r["low2"] < r["low1"]
    assert r["rsi_low2"] > r["rsi_low1"]
    assert r["invalidation"] == r["low2"]
    assert r["price"] > r["low2"]


def test_pure_downtrend_has_no_divergence():
    assert score_rsi_divergence("T", _frame(np.linspace(200, 100, 120))) is None


def test_taken_out_pivot_is_dropped():
    closes = _divergent_closes()
    closes[-1] = 90.0
    closes[-2] = 91.0
    hist = _frame(closes)
    assert score_rsi_divergence("T", hist) is None


def test_short_history_returns_none():
    assert score_rsi_divergence("T", _frame(np.linspace(100, 90, 30))) is None


def test_grade_bands():
    assert [_grade(x) for x in (90, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
