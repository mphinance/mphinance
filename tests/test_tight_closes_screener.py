"""Tests for dossier/tight_closes_screener.py — Tight Closes Screener."""

import numpy as np
import pandas as pd

from dossier.tight_closes_screener import (
    _duration_score,
    _grade,
    _near_high_score,
    _tightness_score,
    _trend_score,
    find_tight_weeks,
    score_tight_closes,
)


def _full(s):
    return pd.DataFrame({"Open": s, "High": s * 1.005, "Low": s * 0.995,
                         "Close": s, "Volume": 1_000_000.0}, index=s.index)


def _hist(tight_days=20, wobble=0.1, n=260):
    """Steady uptrend, then `tight_days` sessions of flat ~wobble% chop."""
    idx = pd.bdate_range("2024-01-01", periods=n)
    ramp = np.linspace(60.0, 100.0, n - tight_days)
    flat = 100.0 + wobble * np.sin(np.arange(tight_days))
    close = np.concatenate([ramp, flat])
    s = pd.Series(close, index=idx)
    return _full(s)


def test_finds_tight_base():
    tight = find_tight_weeks(_hist())
    assert tight is not None
    assert tight["weeks"] >= 3
    assert tight["spread_pct"] <= 1.5


def test_wide_weeks_not_tight():
    idx = pd.bdate_range("2024-01-01", periods=60)
    s = pd.Series(np.linspace(50, 100, 60), index=idx)
    hist = pd.DataFrame({"High": s, "Close": s}, index=idx)
    assert find_tight_weeks(hist) is None


def test_missing_columns_returns_none():
    assert find_tight_weeks(pd.DataFrame({"Close": [1.0, 2.0]})) is None


def test_score_full_setup():
    r = score_tight_closes("TEST", _hist())
    assert r is not None
    assert r["tight_weeks"] >= 3
    assert r["pivot"] >= r["price"]
    assert r["score"] == sum(r["score_breakdown"].values())
    assert r["grade"] in ("A+", "A", "B")


def test_downtrend_rejected():
    idx = pd.bdate_range("2024-01-01", periods=260)
    close = np.concatenate([np.linspace(150, 60, 240), np.full(20, 60.0)])
    s = pd.Series(close, index=idx)
    hist = _full(s)
    assert score_tight_closes("DOWN", hist) is None


def test_short_history_rejected():
    assert score_tight_closes("X", _hist(n=30)) is None


def test_score_helpers():
    assert _tightness_score(0.3) == 35 and _tightness_score(2.0) == 0
    assert _duration_score(3) == 8 and _duration_score(7) == 20
    assert _near_high_score(2) == 20 and _near_high_score(15) == 0
    assert _trend_score(10, 9, 8, 7) == 25
    assert _trend_score(10, 9, 8, None) == 17
    assert _grade(85) == "A+" and _grade(20) == "D"
