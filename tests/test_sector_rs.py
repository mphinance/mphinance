"""
Tests for dossier/data_sources/sector_rs.py

Covers:
  1. _pct_return — edge cases (short series, zero entry, None)
  2. _excess_return — basic math and None propagation
  3. _rotation_signal — all six categories
  4. _composite_rs — weighted average with missing windows
  5. fetch_sector_rs — full flow with mocked yfinance (ranking + rotation)
  6. fetch_sector_rs — graceful empty return on benchmark failure
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dossier.data_sources.sector_rs import (
    _composite_rs,
    _excess_return,
    _pct_return,
    _rotation_signal,
    fetch_sector_rs,
)


# ── _pct_return ──────────────────────────────────────────────────────────────

def _series(*vals):
    return pd.Series(list(vals), dtype=float)


class TestPctReturn:
    def test_basic_gain(self):
        # price goes 100 → 110 over 5 bars → +10 %
        prices = _series(100, 101, 102, 103, 104, 110)
        assert _pct_return(prices, 5) == pytest.approx(10.0)

    def test_basic_loss(self):
        prices = _series(200, 190, 180, 170, 160, 150)
        assert _pct_return(prices, 5) == pytest.approx(-25.0)

    def test_none_on_too_short(self):
        assert _pct_return(_series(100, 110), 5) is None

    def test_none_on_zero_entry(self):
        prices = _series(0, 100, 110, 120, 130, 140)
        assert _pct_return(prices, 5) is None

    def test_none_on_none_input(self):
        assert _pct_return(None, 5) is None

    def test_exactly_enough_bars(self):
        # Need n_bars + 1 rows; n_bars = 1 → 2 rows
        prices = _series(100, 110)
        assert _pct_return(prices, 1) == pytest.approx(10.0)


# ── _excess_return ────────────────────────────────────────────────────────────

class TestExcessReturn:
    def test_outperformance(self):
        assert _excess_return(5.0, 3.0) == pytest.approx(2.0)

    def test_underperformance(self):
        assert _excess_return(-1.0, 2.0) == pytest.approx(-3.0)

    def test_none_propagates_sector(self):
        assert _excess_return(None, 3.0) is None

    def test_none_propagates_bench(self):
        assert _excess_return(5.0, None) is None

    def test_both_none(self):
        assert _excess_return(None, None) is None

    def test_equal_returns_zero(self):
        assert _excess_return(2.5, 2.5) == pytest.approx(0.0)


# ── _rotation_signal ──────────────────────────────────────────────────────────

class TestRotationSignal:
    def test_reversing_up(self):
        # Leading recently, was lagging over 3m
        assert _rotation_signal(rs_1w=2.0, rs_3m=-1.0) == "reversing_up"

    def test_reversing_down(self):
        # Lagging recently, was leading over 3m
        assert _rotation_signal(rs_1w=-1.0, rs_3m=3.0) == "reversing_down"

    def test_accelerating(self):
        # Both positive; 1w > 3m by more than 1.5 pp
        assert _rotation_signal(rs_1w=4.0, rs_3m=1.0) == "accelerating"

    def test_decelerating(self):
        # Both positive; 3m > 1w by more than 1.5 pp
        assert _rotation_signal(rs_1w=0.5, rs_3m=3.0) == "decelerating"

    def test_stable(self):
        # Both positive, close together
        assert _rotation_signal(rs_1w=2.0, rs_3m=2.0) == "stable"

    def test_stable_both_negative_close(self):
        assert _rotation_signal(rs_1w=-1.0, rs_3m=-1.0) == "stable"

    def test_unknown_none_1w(self):
        assert _rotation_signal(None, 2.0) == "unknown"

    def test_unknown_none_3m(self):
        assert _rotation_signal(1.0, None) == "unknown"

    def test_unknown_both_none(self):
        assert _rotation_signal(None, None) == "unknown"


# ── _composite_rs ─────────────────────────────────────────────────────────────

class TestCompositeRs:
    def test_all_windows_present(self):
        # weights: 1w=0.25, 1m=0.35, 3m=0.40 → sum = 1.0
        # weighted sum = 2*0.25 + 4*0.35 + 6*0.40 = 0.5 + 1.4 + 2.4 = 4.3
        rs = {"1w": 2.0, "1m": 4.0, "3m": 6.0}
        assert _composite_rs(rs) == pytest.approx(4.3)

    def test_missing_1w_renormalises(self):
        # Only 1m and 3m present; renormalise to 0.35+0.40=0.75
        rs = {"1w": None, "1m": 4.0, "3m": 6.0}
        expected = (4.0 * 0.35 + 6.0 * 0.40) / 0.75
        assert _composite_rs(rs) == pytest.approx(expected, abs=0.01)

    def test_all_none_returns_zero(self):
        rs = {"1w": None, "1m": None, "3m": None}
        assert _composite_rs(rs) == pytest.approx(0.0)

    def test_single_window(self):
        rs = {"1w": None, "1m": None, "3m": 5.0}
        assert _composite_rs(rs) == pytest.approx(5.0)


# ── fetch_sector_rs — mocked end-to-end ──────────────────────────────────────

def _mock_closes(returns_map: dict[str, list[float]]):
    """
    Build a fake yf.Ticker that returns preset closes.

    returns_map: ticker → list of closing prices (oldest first).
    """
    def _history(period=None):
        ticker = mock_ticker._current_ticker
        prices = returns_map.get(ticker, [100.0] * 70)
        return pd.DataFrame({"Close": prices})

    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = _history
    return mock_ticker


def _build_prices(n=70, start=100.0, total_return_pct=0.0):
    """Linear price path of n bars ending at start*(1+pct/100)."""
    end = start * (1 + total_return_pct / 100)
    step = (end - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _build_ohlcv(n=70, start=100.0, total_return_pct=0.0) -> pd.DataFrame:
    """Full OHLCV DataFrame required by check_yfinance_history."""
    closes = _build_prices(n, start, total_return_pct)
    return pd.DataFrame({
        "Close": closes,
        "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes],
        "Volume": [1_000_000] * n,
    })


class TestFetchSectorRs:
    """End-to-end tests with yfinance mocked out."""

    def _make_ticker_factory(self, df_map: dict[str, pd.DataFrame]):
        """Return a callable that mimics yf.Ticker(symbol).history(...)."""
        def _ticker(symbol):
            mock = MagicMock()
            df = df_map.get(symbol, _build_ohlcv())
            mock.history.return_value = df
            return mock

        return _ticker

    def test_ranking_order(self):
        """Sector with highest composite RS should rank #1."""
        # XLK up +20%, XLF up +5%, SPY up +10% → XLK leads, XLF lags
        df_map = {
            "SPY": _build_ohlcv(70, 100, 10.0),
            "XLK": _build_ohlcv(70, 100, 20.0),
            "XLF": _build_ohlcv(70, 100, 5.0),
        }
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = self._make_ticker_factory(df_map)
            result = fetch_sector_rs(sector_etfs=["XLK", "XLF"], benchmark="SPY")

        assert result
        ranked = result["ranked"]
        assert ranked[0]["ticker"] == "XLK"
        assert ranked[1]["ticker"] == "XLF"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2

    def test_leaders_and_laggards_populated(self):
        """leaders should be top N; laggards bottom N of ranked list."""
        etfs = ["XLK", "XLF", "XLE", "XLV", "XLI"]
        # Assign descending returns: XLK best, XLI worst
        returns = {etf: 20.0 - i * 4 for i, etf in enumerate(etfs)}
        df_map = {
            "SPY": _build_ohlcv(70, 100, 10.0),
            **{etf: _build_ohlcv(70, 100, r) for etf, r in returns.items()},
        }
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = self._make_ticker_factory(df_map)
            result = fetch_sector_rs(sector_etfs=etfs, benchmark="SPY")

        assert result["leaders"][0]["ticker"] == "XLK"
        assert result["laggards"][0]["ticker"] == "XLI"

    def test_rotation_present_in_each_row(self):
        df_map = {
            "SPY": _build_ohlcv(70, 100, 5.0),
            "XLK": _build_ohlcv(70, 100, 8.0),
        }
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = self._make_ticker_factory(df_map)
            result = fetch_sector_rs(sector_etfs=["XLK"], benchmark="SPY")

        assert "rotation" in result["ranked"][0]
        assert result["ranked"][0]["rotation"] in {
            "reversing_up", "reversing_down", "accelerating",
            "decelerating", "stable", "unknown",
        }

    def test_generated_at_present(self):
        df_map = {
            "SPY": _build_ohlcv(70),
            "XLK": _build_ohlcv(70),
        }
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = self._make_ticker_factory(df_map)
            result = fetch_sector_rs(sector_etfs=["XLK"], benchmark="SPY")

        assert "generated_at" in result
        assert result["generated_at"]  # non-empty string

    def test_benchmark_failure_returns_empty(self):
        """Pipeline must not crash if benchmark fetch fails."""
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = RuntimeError("network timeout")
            result = fetch_sector_rs(sector_etfs=["XLK"], benchmark="SPY")

        assert result == {}

    def test_sector_fetch_failure_skips_gracefully(self):
        """If one sector fails, others still rank."""
        def _ticker(symbol):
            mock = MagicMock()
            if symbol == "XLF":
                mock.history.side_effect = RuntimeError("timeout")
            else:
                mock.history.return_value = _build_ohlcv(70, 100, 5.0)
            return mock

        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _ticker
            result = fetch_sector_rs(sector_etfs=["XLK", "XLF"], benchmark="SPY")

        # XLF failed → only XLK in results
        tickers = [r["ticker"] for r in result.get("ranked", [])]
        assert "XLK" in tickers
        assert "XLF" not in tickers

    def test_rs_dict_keys(self):
        """Each ranked row must have rs with 1w, 1m, 3m keys."""
        df_map = {
            "SPY": _build_ohlcv(70, 100, 5.0),
            "XLK": _build_ohlcv(70, 100, 8.0),
        }
        with patch("dossier.data_sources.sector_rs.yf") as mock_yf:
            mock_yf.Ticker.side_effect = self._make_ticker_factory(df_map)
            result = fetch_sector_rs(sector_etfs=["XLK"], benchmark="SPY")

        row = result["ranked"][0]
        assert set(row["rs"].keys()) == {"1w", "1m", "3m"}
        assert set(row["abs_ret"].keys()) == {"1w", "1m", "3m"}
