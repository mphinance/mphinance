"""Tests for dossier/ema_pullback_screener.py — EMA Pullback Screener."""

import numpy as np
import pandas as pd

from dossier.ema_pullback_screener import (
    _dryup_score,
    _grade,
    _pullback_score,
    _reversal_score,
    _tag_score,
    _trend_score,
    compute_indicators,
    is_stacked_uptrend,
    score_ema_pullback,
)


def _frame(close, volume=None, wiggle=0.008):
    close = np.asarray(close, dtype=float)
    s = pd.Series(close, index=pd.bdate_range("2024-01-02", periods=len(close)))
    vol = np.full(len(close), 1_000_000.0) if volume is None else np.asarray(volume, float)
    return pd.DataFrame({"Open": s, "High": s * (1 + wiggle), "Low": s * (1 - wiggle),
                         "Close": s, "Volume": vol})


def _uptrend_with_dip(dip_bars=8, dip_pct=0.06):
    up = 50 * (1.004 ** np.arange(200))
    peak = up[-1]
    # glide down toward the 21-EMA over dip_bars
    dip = peak * (1 - dip_pct * np.arange(1, dip_bars + 1) / dip_bars)
    return np.concatenate([up, dip])


def test_dip_into_ema21_in_uptrend_is_flagged():
    found = None  # sweep dip shapes: at least one must tag EMA21 with enough depth
    for bars in range(4, 14):
        for pct in (0.03, 0.05, 0.07, 0.09):
            r = score_ema_pullback("T", _frame(_uptrend_with_dip(bars, pct), np.r_[np.full(200 + bars - 3, 1e6), np.full(3, 5e5)]))
            if r:
                found = r
    assert found is not None
    assert found["pullback_atr"] >= 1.0
    assert found["volume_ratio_3d"] < 1.0
    assert found["grade"] in ("A+", "A", "B", "C", "D")


def test_straight_uptrend_without_dip_is_dropped():
    assert score_ema_pullback("T", _frame(50 * (1.004 ** np.arange(220)))) is None


def test_downtrend_is_dropped():
    assert score_ema_pullback("T", _frame(100 * (0.997 ** np.arange(220)))) is None


def test_short_or_missing_columns_return_none():
    assert score_ema_pullback("T", _frame(np.linspace(1, 2, 50))) is None
    assert score_ema_pullback("T", _frame(np.linspace(1, 2, 200)).drop(columns=["Volume"])) is None


def test_stacked_uptrend_helper():
    h = _frame(50 * (1.004 ** np.arange(200)))
    assert is_stacked_uptrend(compute_indicators(h), h["Close"])
    d = _frame(100 * (0.997 ** np.arange(200)))
    assert not is_stacked_uptrend(compute_indicators(d), d["Close"])


def test_score_helpers_and_grades():
    assert _tag_score(0.05, True) == 30 and _tag_score(-0.4, False) == 10
    assert _pullback_score(2.0) == 20 and _pullback_score(0.2) == 6
    assert _dryup_score(0.5) == 20 and _dryup_score(2.0) == 2
    assert _trend_score(4) == 20 and _trend_score(0.5) == 7
    assert _reversal_score(2, 1) == 10 and _reversal_score(1, 2) == 3
    assert [_grade(x) for x in (85, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
