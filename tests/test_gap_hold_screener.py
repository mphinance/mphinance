"""Tests for dossier/gap_hold_screener.py — Gap-and-Hold Screener."""

import pandas as pd

from dossier.gap_hold_screener import (
    _follow_through_score,
    _gap_size_score,
    _gap_volume_score,
    _grade,
    _hold_quality_score,
    find_gap_day,
    score_gap_hold,
)


def _hist(n=40, gap_at=-5, gap_pct=8.0, vol_mult=3.0, after_drift=0.01, fill=False):
    """Flat 100 series with a gap-up `gap_at` bars from the end."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = [100.0] * n
    opens = [100.0] * n
    vol = [1_000_000.0] * n
    g = n + gap_at
    for i in range(g, n):
        opens[i] = close[i - 1] * (1 + gap_pct / 100) if i == g else close[i - 1]
        close[i] = close[g - 1] * (1 + gap_pct / 100) * (1 + after_drift * (i - g))
    vol[g] = 1_000_000.0 * vol_mult
    if fill:
        close[-1] = 99.0
    close_s = pd.Series(close, index=idx)
    return pd.DataFrame({
        "Open": opens, "High": close_s * 1.01, "Low": close_s * 0.99,
        "Close": close_s, "Volume": vol,
    }, index=idx)


def test_finds_held_gap():
    gap = find_gap_day(_hist())
    assert gap is not None
    assert gap["days_since_gap"] == 4
    assert abs(gap["gap_pct"] - 8.0) < 0.01


def test_filled_gap_rejected():
    assert find_gap_day(_hist(fill=True)) is None


def test_small_gap_rejected():
    assert find_gap_day(_hist(gap_pct=2.0)) is None


def test_low_volume_gap_rejected():
    assert find_gap_day(_hist(vol_mult=1.0)) is None


def test_stale_gap_rejected():
    assert find_gap_day(_hist(gap_at=-20)) is None


def test_gap_on_last_bar_not_yet_a_hold():
    assert find_gap_day(_hist(gap_at=-1)) is None


def test_missing_columns_and_short_history():
    assert find_gap_day(_hist().drop(columns=["Open"])) is None
    assert find_gap_day(_hist(n=10, gap_at=-3)) is None


def test_score_gap_hold_shape():
    r = score_gap_hold("TEST", hist=_hist())
    assert r is not None
    assert r["ticker"] == "TEST"
    assert r["score"] == sum(r["score_breakdown"].values())
    assert r["grade"] == _grade(r["score"])


def test_score_gap_hold_none_on_empty():
    assert score_gap_hold("TEST", hist=pd.DataFrame()) is None


def test_component_scores():
    assert _gap_size_score(16) == 25 and _gap_size_score(3) == 0
    assert _gap_volume_score(6) == 25 and _gap_volume_score(1.0) == 0
    assert _hold_quality_score(90, 100, 95) == 0
    assert _hold_quality_score(110, 100, 104) == 30
    assert _follow_through_score(-10) == 0
    assert _grade(80) == "A+" and _grade(34) == "D"
