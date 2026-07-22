"""Tests for dossier.backtesting.track_record_generator pure helpers.

Regression coverage for a bug where every pick stayed permanently
unvalidated: dossier summary files never populate a real "entry" price
(always 0), but _get_forward_returns() required price_at_pick > 0 before
fetching returns at all, so total_validated was stuck at 0 forever.
"""
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from dossier.backtesting.track_record_generator import (
    _compute_stats,
    _get_forward_returns,
)


def _fake_history(closes):
    return pd.DataFrame({"Close": closes})


def test_get_forward_returns_falls_back_to_actual_close_when_no_price():
    """price_at_pick=0 (the common case) must not skip validation."""
    closes = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = _fake_history(closes)

    with patch("yfinance.Ticker", return_value=fake_ticker):
        returns = _get_forward_returns("AAPL", "2026-01-01", 0)

    # base price should be closes[0] == 100.0, so fwd_1d = (101-100)/100*100 = 1.0
    assert returns["fwd_1d"] == 1.0
    assert returns["fwd_5d"] == 5.0


def test_get_forward_returns_uses_stored_price_when_available():
    closes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0]
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = _fake_history(closes)

    with patch("yfinance.Ticker", return_value=fake_ticker):
        returns = _get_forward_returns("AAPL", "2026-01-01", 50.0)

    # base price is the stored 50.0, not closes[0]
    assert returns["fwd_1d"] == round((110.0 - 50.0) / 50.0 * 100, 2)


def test_get_forward_returns_empty_history():
    fake_ticker = MagicMock()
    fake_ticker.history.return_value = pd.DataFrame()

    with patch("yfinance.Ticker", return_value=fake_ticker):
        returns = _get_forward_returns("AAPL", "2026-01-01", 0)

    assert returns == {}


def test_compute_stats_no_validated_entries():
    entries = [{"ticker": "AAPL", "date": "2026-01-01", "score": 80}]
    stats = _compute_stats(entries)
    assert stats["total_picks_tracked"] == 1
    assert stats["total_validated"] == 0
    assert stats["best_pick"] is None


def test_compute_stats_basic():
    entries = [
        {"ticker": "AAPL", "date": "2026-01-01", "fwd_5d": 5.0, "fwd_1d": 1.0},
        {"ticker": "MSFT", "date": "2026-01-02", "fwd_5d": -2.0, "fwd_1d": -0.5},
    ]
    stats = _compute_stats(entries)
    assert stats["total_validated"] == 2
    assert stats["win_rate_5d"] == 50.0
    assert stats["best_pick"]["ticker"] == "AAPL"
    assert stats["worst_pick"]["ticker"] == "MSFT"
