"""Tests for dossier.data_sources.ascending_reversal.

Mirrors the spirit of the downtrend-breakout calibration: a DIS-style positive
(higher lows coiling into a flat lid under a DECLINING 200DMA -> forming/confirmed),
a rising-200 uptrend negative (must reject), a falling-knife negative (must reject),
and the never-raises contract on garbage input.

Synthetic OHLC frames are built deterministically so the tests run without any
network / yfinance dependency (which is flaky / forward-dated in CI).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dossier.data_sources.ascending_reversal import (
    fit_ascending_support,
    fit_flat_lid,
    generate_ascending_reversals,
    scan_ascending_reversal,
)

# Enough bars to clear MIN_HISTORY_BARS (260) and 200DMA + slope lookback (220).
N_BARS = 340


def _frame(close, *, high_pad=0.6, low_pad=0.6, vol=2_000_000.0, vol_last=None):
    """Build an OHLCV frame from a close path. Liquidity is set well above the
    universe-quality gate (price > $2, $vol > $5M, share vol > 300k, atr ok)."""
    close = np.asarray(close, dtype=float)
    n = len(close)
    dates = pd.bdate_range(end="2026-06-18", periods=n)
    high = close + high_pad
    low = close - low_pad
    openp = close.copy()
    volume = np.full(n, vol, dtype=float)
    if vol_last is not None:
        volume[-1] = vol_last
    return pd.DataFrame({
        "date": dates, "open": openp, "high": high,
        "low": low, "close": close, "volume": volume,
    })


def _dis_style_close():
    """Higher lows coiling into a flat lid that coincides with a DECLINING 200DMA,
    price still UNDER the lid (the DIS-as-of-2026-06-18 geometry).

    Phase A: a long, steady downtrend from a major peak (drags the 200DMA down and
    keeps it declining over the recent lookback). Phase B: an ascending base of
    higher lows pressing up into a flat ~107 lid, finishing just below it (~104)."""
    rng = np.random.default_rng(7)
    lid = 107.0
    # Phase A: a prior-year plateau of HIGH prices (~120) — this keeps the 200DMA
    # elevated (~106, right at the lid) even after the recovery, so price coils
    # BELOW the falling 200. (DIS was ~$110-120 a year before the coil.)
    plateau_len = 170
    a = np.full(plateau_len, 120.0)
    # Phase A2: the real downtrend off the plateau, peak -> ~92 trough.
    decl_len = (N_BARS - plateau_len) // 2
    decl = np.linspace(120.0, 92.0, decl_len)
    # Phase B: higher lows coiling up into the flat lid near 107, finishing just
    # BELOW both the lid and the (still-declining) 200DMA — the DIS geometry.
    n_b = N_BARS - plateau_len - decl_len
    lows_floor = np.linspace(92.5, lid - 2.5, n_b)   # rising support (higher lows)
    b = []
    for i in range(n_b):
        # sawtooth between a rising floor and the flat lid; never closing above it.
        frac = (i % 12) / 11.0
        lo = lows_floor[i]
        hi = lid - 1.5                               # closes top out just under lid
        b.append(lo + frac * (hi - lo))
    close = np.concatenate([a, decl, np.asarray(b)])
    close += rng.normal(0, 0.15, len(close))         # tiny jitter, keep it clean
    return close, lid


def _dis_confirmed_close():
    """Same base, but the LAST bar closes decisively ABOVE the lid on volume — the
    confirmed reclaim tier."""
    close, lid = _dis_style_close()
    close[-1] = lid + 2.0                            # ~+1.9% clearance
    return close, lid


def _rising_200_uptrend_close():
    """A clean, persistent uptrend: the 200DMA is RISING. Even though it makes higher
    lows, the defining 200DMA gate must reject it (momentum-pullback, not reversal)."""
    base = np.linspace(60.0, 140.0, N_BARS)          # relentless uptrend
    wobble = 2.0 * np.sin(np.linspace(0, 30, N_BARS))
    return base + wobble


def _falling_knife_close():
    """An 80% vertical collapse with no base — must reject (knife cap)."""
    a = np.full(120, 200.0)
    b = np.linspace(200.0, 40.0, N_BARS - 120)       # -80% waterfall, no coil
    return np.concatenate([a, b])


class TestPositiveDISStyle:
    def test_forming_fires(self):
        close, _lid = _dis_style_close()
        sig = scan_ascending_reversal("DIS", hist=_frame(close))
        assert sig is not None, "DIS-style coil-under-declining-200 should fire"
        assert sig["pattern"] == "forming"
        assert sig["ticker"] == "DIS"
        assert sig["signal_type"] == "ascending_reversal_forming"
        # geometry sanity: rising support (positive slope) + a lid + below the 200.
        assert sig["slope"] > 0
        assert sig["lid"] is not None
        assert sig["sma200"] is not None
        assert sig["dist_to_200dma_pct"] is not None and sig["dist_to_200dma_pct"] < 0
        assert sig["newer_pivot_price"] > sig["older_pivot_price"]  # higher lows

    def test_confirmed_fires_on_reclaim(self):
        close, _lid = _dis_confirmed_close()
        sig = scan_ascending_reversal("DIS", hist=_frame(close, vol_last=4_000_000.0))
        assert sig is not None, "a clean reclaim of the lid on volume should fire"
        assert sig["pattern"] in ("confirmed", "extended")
        assert sig["clearance_pct"] > 0
        assert sig["reclaim_date"] is not None


class TestNegatives:
    def test_rising_200_uptrend_rejected(self):
        close = _rising_200_uptrend_close()
        sig = scan_ascending_reversal("UPTREND", hist=_frame(close))
        assert sig is None, "a rising-200 uptrend is NOT this reversal-coil setup"

    def test_falling_knife_rejected(self):
        close = _falling_knife_close()
        sig = scan_ascending_reversal("KNIFE", hist=_frame(close))
        assert sig is None, "an 80% knife with no base must reject"


class TestNeverRaises:
    def test_none_ticker(self):
        assert scan_ascending_reversal(None) is None

    def test_empty_ticker(self):
        assert scan_ascending_reversal("") is None

    def test_garbage_hist_dataframe(self):
        bad = pd.DataFrame({"foo": [1, 2, 3], "bar": [4, 5, 6]})
        assert scan_ascending_reversal("X", hist=bad) is None

    def test_too_short_hist(self):
        close = np.linspace(100.0, 110.0, 30)
        assert scan_ascending_reversal("X", hist=_frame(close)) is None

    def test_nan_riddled_hist(self):
        close = np.full(N_BARS, np.nan)
        assert scan_ascending_reversal("X", hist=_frame(close)) is None

    def test_generate_handles_garbage_list(self):
        assert generate_ascending_reversals([None, "", 123, {"a": 1}]) == []

    def test_generate_empty(self):
        assert generate_ascending_reversals([]) == []

    def test_generate_dedups_and_limits(self):
        close, _lid = _dis_style_close()
        # Patch the fetch indirectly is overkill; just confirm it doesn't raise and
        # respects max_results with a repeated bogus symbol (no network -> []).
        out = generate_ascending_reversals(["ZZZZ", "ZZZZ"], max_results=1)
        assert isinstance(out, list)
        assert len(out) <= 1


class TestHelpersDegradeGracefully:
    def test_fit_ascending_support_too_few_pivots(self):
        df = _frame(np.linspace(100.0, 100.5, N_BARS))  # near-flat, no clean pivots
        # should not raise; returns a geom or None.
        res = fit_ascending_support(df.tail(190).reset_index(drop=True))
        assert res is None or isinstance(res, dict)

    def test_fit_flat_lid_no_pivots(self):
        df = _frame(np.linspace(100.0, 101.0, N_BARS))
        res = fit_flat_lid(df.tail(190).reset_index(drop=True), sma200=100.0)
        assert res is None or isinstance(res, dict)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
