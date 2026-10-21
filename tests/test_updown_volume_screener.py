"""Tests for dossier/updown_volume_screener.py — Up/Down Volume Screener."""

import numpy as np
import pandas as pd

from dossier.updown_volume_screener import (
    _grade,
    heavy_day_balance,
    score_updown_volume,
    updown_ratio,
)


def _frame(close, volume):
    idx = pd.bdate_range("2024-01-02", periods=len(close))
    c = pd.Series(np.asarray(close, float), index=idx)
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c,
                         "Volume": pd.Series(np.asarray(volume, float), index=idx)})


def _accumulating(n=260):
    """Steady uptrend with an up/down zig-zag; up days trade double the volume."""
    close, vol, price = [], [], 100.0
    for i in range(n):
        up = i % 3 != 2
        price *= 1.006 if up else 0.996
        close.append(price)
        vol.append(2_000_000 if up else 1_000_000)
    return _frame(close, vol)


def test_ratio_known_values():
    close = pd.Series([10, 11, 10, 11, 12.0])
    vol = pd.Series([1, 100, 50, 100, 100.0])
    # up bars: 100+100+100=300, down bar: 50
    assert updown_ratio(close, vol, 5) == 6.0


def test_ratio_without_down_days_is_capped_not_infinite():
    close = pd.Series(np.arange(1.0, 30.0))
    vol = pd.Series(np.full(29, 1000.0))
    assert updown_ratio(close, vol, 20) == 99.0


def test_heavy_day_balance_counts_up_minus_down():
    close = np.full(80, 100.0)
    vol = np.full(80, 1000.0)
    close[-3:] = [101, 102, 101]
    vol[-3:] = [5000, 5000, 5000]
    assert heavy_day_balance(pd.Series(close), pd.Series(vol)) == 1


def test_accumulation_name_qualifies():
    r = score_updown_volume("T", _accumulating())
    assert r is not None
    assert r["updown_ratio_50d"] > 2.0
    assert r["accelerating"] is True
    assert r["grade"] in ("A+", "A", "B")


def test_distribution_name_is_dropped():
    df = _accumulating()
    df["Volume"] = np.where(df["Close"].diff() > 0, 1_000_000.0, 2_000_000.0)
    assert score_updown_volume("T", df) is None


def test_below_sma50_is_dropped():
    df = _accumulating()
    df.iloc[-1, df.columns.get_loc("Close")] = float(df["Close"].iloc[-60:].min()) * 0.8
    assert score_updown_volume("T", df) is None


def test_short_or_missing_history_returns_none():
    assert score_updown_volume("T", _accumulating(50)) is None
    assert score_updown_volume("T", pd.DataFrame({"Close": [1.0] * 300})) is None


def test_grade_bands():
    assert [_grade(x) for x in (90, 70, 55, 40, 10)] == ["A+", "A", "B", "C", "D"]
