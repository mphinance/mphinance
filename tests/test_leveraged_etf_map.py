"""Tests for dossier/data_sources/leveraged_etf_map.py — _fetch_avg_volume.

Covers the silent-failure gap this used to have: a malformed/short yfinance
response returned 0.0 with a bare `except Exception: return 0.0` and no
trace of why. A silent 0.0 isn't just "no data" here — it feeds directly
into get_best_2x_etf()'s volume comparison, so it could make a genuinely
liquid ETF lose to a thinner one with nothing logged to explain it.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from dossier.data_sources.leveraged_etf_map import _fetch_avg_volume


def _make_ticker(hist: pd.DataFrame):
    mock = MagicMock()
    mock.history.return_value = hist
    return mock


def _build_hist(n=25, volume=1_000_000):
    return pd.DataFrame({
        "Close": [100.0 + i for i in range(n)],
        "High": [101.0 + i for i in range(n)],
        "Low": [99.0 + i for i in range(n)],
        "Volume": [volume] * n,
    })


class TestFetchAvgVolume:
    def test_valid_history_returns_mean_volume(self):
        with patch("yfinance.Ticker", return_value=_make_ticker(_build_hist(volume=2_000_000))):
            result = _fetch_avg_volume("NVDL")
        assert result == 2_000_000.0

    def test_empty_history_returns_zero(self):
        with patch("yfinance.Ticker", return_value=_make_ticker(pd.DataFrame())):
            result = _fetch_avg_volume("NVDL")
        assert result == 0.0

    def test_missing_columns_returns_zero_without_raising(self):
        malformed = pd.DataFrame({"High": [21.0, 22.0], "Low": [19.0, 19.5]})
        with patch("yfinance.Ticker", return_value=_make_ticker(malformed)):
            result = _fetch_avg_volume("NVDL")
        assert result == 0.0

    def test_fetch_exception_returns_zero(self):
        mock = MagicMock()
        mock.history.side_effect = RuntimeError("network timeout")
        with patch("yfinance.Ticker", return_value=mock):
            result = _fetch_avg_volume("NVDL")
        assert result == 0.0
