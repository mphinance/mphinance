"""Tests for dossier/trend_template_screener.py — Minervini trend template."""

import numpy as np
import pandas as pd

from dossier.trend_template_screener import (
    _grade,
    _near_high_score,
    _off_low_score,
    _return_score,
    _slope200_score,
    _slope50_score,
    evaluate_template,
    score_trend_template,
)


def _frame(close, wiggle=0.005):
    close = np.asarray(close, dtype=float)
    s = pd.Series(close, index=pd.bdate_range("2023-01-02", periods=len(close)))
    return pd.DataFrame({"Open": s, "High": s * (1 + wiggle), "Low": s * (1 - wiggle),
                         "Close": s, "Volume": 1e6})


def test_steady_uptrend_passes_all_rules():
    r = score_trend_template("T", _frame(20 * (1.005 ** np.arange(300))))
    assert r is not None
    assert r["pct_below_52w_high"] < 3
    assert r["pct_above_52w_low"] >= 30
    assert r["grade"] in ("A+", "A", "B", "C", "D")


def test_downtrend_is_dropped():
    assert score_trend_template("T", _frame(100 * (0.997 ** np.arange(300)))) is None


def test_too_far_below_high_is_dropped():
    up = 20 * (1.005 ** np.arange(280))
    crash = up[-1] * np.linspace(1, 0.6, 20)  # -40% off the high, below the 50-SMA
    assert score_trend_template("T", _frame(np.r_[up, crash])) is None


def test_short_history_or_missing_columns_return_none():
    assert score_trend_template("T", _frame(np.linspace(1, 2, 100))) is None
    assert score_trend_template("T", _frame(np.linspace(1, 2, 300)).drop(columns=["Close"])) is None


def test_evaluate_template_metrics():
    m = evaluate_template(_frame(20 * (1.005 ** np.arange(300))))
    assert m is not None and m["sma50"] > m["sma200"] and m["slope200"] > 0


def test_score_helpers_and_grades():
    assert _near_high_score(0.01) == 30 and _near_high_score(0.2) == 6
    assert _off_low_score(1.2) == 20 and _off_low_score(0.3) == 9
    assert _slope200_score(0.1) == 20 and _slope200_score(0.01) == 7
    assert _return_score(0.5) == 20 and _return_score(-0.1) == 3
    assert _slope50_score(0.05) == 10 and _slope50_score(-0.01) == 0
    assert [_grade(x) for x in (85, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
