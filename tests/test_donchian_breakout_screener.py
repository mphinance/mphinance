"""Tests for dossier/donchian_breakout_screener.py — Donchian Turtle Breakout Screener."""

import numpy as np
import pandas as pd

from dossier.donchian_breakout_screener import (
    _close_score,
    _fresh_score,
    _grade,
    _thrust_score,
    _trend_score,
    _volume_score,
    compute_channel,
    find_breakout,
    score_donchian_breakout,
)


def _frame(close, volume=None, wiggle=0.005):
    close = np.asarray(close, dtype=float)
    s = pd.Series(close, index=pd.bdate_range("2023-01-02", periods=len(close)))
    vol = np.full(len(close), 1_000_000.0) if volume is None else np.asarray(volume, float)
    return pd.DataFrame({"Open": s, "High": s * (1 + wiggle), "Low": s * (1 - wiggle),
                         "Close": s, "Volume": vol})


def _base_then_pop(pop_days=1, pop=8.0, vol_mult=3.0):
    base = 100 + np.tile([0.0, 1.0], 150)        # 300 flat bars
    closes = np.concatenate([base, base[-1] + pop + np.arange(pop_days) * 0.1])
    vols = np.full(len(closes), 1_000_000.0)
    vols[300] *= vol_mult
    return _frame(closes, vols)


def test_breakout_detected_on_pop_bar():
    r = score_donchian_breakout("T", _base_then_pop())
    assert r is not None
    assert r["bars_since_breakout"] == 0
    assert r["volume_ratio"] > 2.5
    assert r["stop_2n"] < r["channel_high"] < r["price"]
    assert r["grade"] in ("A+", "A")


def test_stale_breakout_outside_window_is_dropped():
    assert score_donchian_breakout("T", _base_then_pop(pop_days=8)) is None


def test_flat_tape_has_no_breakout():
    assert score_donchian_breakout("T", _frame(100 + np.tile([0.0, 1.0], 160))) is None


def test_failed_breakout_back_inside_channel_is_dropped():
    base = 100 + np.tile([0.0, 1.0], 150)
    closes = np.concatenate([base, [110.0, 108.0, 101.0]])
    hist = _frame(closes)
    assert find_breakout(hist, compute_channel(hist)) is None


def test_short_or_missing_columns_return_none():
    assert score_donchian_breakout("T", _frame(np.linspace(1, 2, 50))) is None
    assert score_donchian_breakout("T", _base_then_pop().drop(columns=["Volume"])) is None


def test_channel_excludes_current_bar():
    hist = _base_then_pop()
    ch = compute_channel(hist)
    assert ch["channel_high"].iloc[-1] < hist["High"].iloc[-1]


def test_score_helpers_and_grades():
    assert _fresh_score(0) > _fresh_score(1) > _fresh_score(2) > _fresh_score(3)
    assert _volume_score(2.5) == 25 and _volume_score(0.5) == 4
    assert _thrust_score(1.2) == 20 and _thrust_score(0.0) == 3
    assert _trend_score(10, 9, 8) == 15 and _trend_score(8, 9, 10) == 0
    assert _close_score(0.9) == 10 and _close_score(0.1) == 2
    assert [_grade(x) for x in (85, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
