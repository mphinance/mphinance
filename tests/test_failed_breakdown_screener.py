"""Tests for dossier/failed_breakdown_screener.py — Failed-Breakdown Screener."""

import pandas as pd

from dossier.failed_breakdown_screener import (
    _grade,
    _maturity_score,
    _reclaim_score,
    _undercut_score,
    _volume_score,
    find_failed_breakdown,
    score_failed_breakdown,
)


def _hist(n=60, trap_at=-3, undercut=2.0, vol_mult=3.0, close_back=True, lose_after=False):
    """Flat 100 series (lows 99) with a trap day `trap_at` bars from the end."""
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = [100.0] * n
    low = [99.0] * n
    high = [101.0] * n
    vol = [1_000_000.0] * n
    t = n + trap_at
    low[t] = 99.0 * (1 - undercut / 100)
    close[t] = 100.0 if close_back else 97.0
    high[t] = 101.0
    vol[t] = 1_000_000.0 * vol_mult
    if lose_after and t < n - 1:
        close[-1] = 97.0
    return pd.DataFrame(
        {"Open": close, "High": high, "Low": low, "Close": close, "Volume": vol},
        index=idx,
    )


def test_finds_trap():
    r = find_failed_breakdown(_hist())
    assert r is not None
    assert r["days_since_trap"] == 2
    assert abs(r["support"] - 99.0) < 1e-9
    assert abs(r["undercut_pct"] - 2.0) < 0.01
    assert r["close_pos"] > 0.5


def test_close_below_support_rejected():
    assert find_failed_breakdown(_hist(close_back=False)) is None


def test_lost_level_again_rejected():
    assert find_failed_breakdown(_hist(lose_after=True)) is None


def test_tiny_poke_rejected():
    assert find_failed_breakdown(_hist(undercut=0.1)) is None


def test_stale_trap_rejected():
    assert find_failed_breakdown(_hist(trap_at=-20)) is None


def test_missing_columns_and_short_history():
    assert find_failed_breakdown(_hist().drop(columns=["High"])) is None
    assert find_failed_breakdown(_hist(n=20, trap_at=-3)) is None


def test_score_shape():
    r = score_failed_breakdown("TEST", hist=_hist())
    assert r is not None
    assert r["ticker"] == "TEST"
    assert r["score"] == sum(r["score_breakdown"].values())
    assert r["grade"] == _grade(r["score"])


def test_score_none_on_empty():
    assert score_failed_breakdown("TEST", hist=pd.DataFrame()) is None


def test_component_scores():
    assert _reclaim_score(0.9) == 30 and _reclaim_score(0.1) == 6
    assert _volume_score(3.5) == 25 and _volume_score(0.5) == 2
    assert _undercut_score(4) == 15 and _undercut_score(0.1) == 0
    assert _maturity_score(25) == 10 and _maturity_score(4) == 4
    assert _grade(80) == "A+" and _grade(34) == "D"
