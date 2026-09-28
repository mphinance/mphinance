"""Tests for dossier/data_sources/itch_screener.py — Itch Slot Screener."""

import pandas as pd
import pytest

from dossier.data_sources.itch_screener import score_underlying


def _make_hist(n: int = 252, trend: float = 0.002) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([100.0 * (1 + trend) ** i for i in range(n)], index=idx)
    high = close * 1.01
    low = close * 0.99
    opens = close * 0.995
    volume = pd.Series([1_000_000] * n, index=idx)
    return pd.DataFrame({"Open": opens, "High": high, "Low": low, "Close": close, "Volume": volume})


class _FakeTicker:
    def __init__(self, hist=None, raises=None):
        self._hist = hist
        self._raises = raises

    def history(self, **kwargs):
        if self._raises is not None:
            raise self._raises
        return self._hist


def test_score_underlying_qualifies(monkeypatch):
    import yfinance as yf

    hist = _make_hist(trend=0.003)
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist=hist))

    result = score_underlying("NVDA")
    assert result is not None
    assert result["ticker"] == "NVDA"
    assert 0 <= result["score"] <= 100
    assert result["grade"] in ("A", "B", "C", "D")


def test_score_underlying_empty_history_returns_none(monkeypatch):
    import yfinance as yf

    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist=pd.DataFrame()))

    assert score_underlying("NVDA") is None


def test_score_underlying_short_history_returns_none(monkeypatch):
    import yfinance as yf

    hist = _make_hist(n=5)
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist=hist))

    assert score_underlying("NVDA") is None


def test_score_underlying_network_error_returns_none(monkeypatch):
    """A raised exception from yfinance must not propagate — one bad ticker
    used to crash the entire universe loop in main()."""
    import yfinance as yf

    monkeypatch.setattr(
        yf, "Ticker", lambda sym: _FakeTicker(raises=ConnectionError("boom"))
    )

    assert score_underlying("NVDA") is None


def test_score_underlying_missing_columns_returns_none(monkeypatch):
    """A malformed response missing required OHLCV columns must not raise."""
    import yfinance as yf

    idx = pd.date_range("2024-01-01", periods=252, freq="B")
    bad_hist = pd.DataFrame({"Close": [100.0] * 252}, index=idx)
    monkeypatch.setattr(yf, "Ticker", lambda sym: _FakeTicker(hist=bad_hist))

    assert score_underlying("NVDA") is None
