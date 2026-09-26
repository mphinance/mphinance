"""Tests for dossier/data_sources/technical_setups.py — Tao of Trading setups.

Covers an input-validation gap this module used to have: analyze_setup() only
guarded the yfinance fetch itself, not the column access right after it. A
response missing High/Low/Volume (the same shape yfinance is known to return
for some tickers) raised an uncaught KeyError, which crashed Stage 6 of the
whole daily pipeline (dossier/generate.py calls generate_setups() with no
try/except) instead of just skipping that one ticker.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from dossier.data_sources.technical_setups import analyze_setup, generate_setups


def _make_hist(n: int = 120, start: float = 100.0, trend: float = 0.003) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    close = pd.Series([start * (1 + trend) ** i for i in range(n)], index=idx)
    return pd.DataFrame({
        "Open": close * 0.995,
        "High": close * 1.01,
        "Low": close * 0.99,
        "Close": close,
        "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _mock_ticker(history_df, info=None):
    stock = MagicMock()
    stock.history.return_value = history_df
    stock.info = info or {"longName": "Test Co", "sector": "Technology"}
    return stock


class TestAnalyzeSetupValidation:
    def test_happy_path_returns_full_setup(self):
        with patch("dossier.data_sources.technical_setups.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_ticker(_make_hist())
            result = analyze_setup("TEST")

        assert result is not None
        assert result["ticker"] == "TEST"
        assert "data_sack" in result
        assert result["ema_stack"] in {
            "FULL BULLISH", "PARTIAL BULLISH", "FULL BEARISH",
            "PARTIAL BEARISH", "TANGLED", "INSUFFICIENT DATA",
        }

    def test_missing_columns_returns_none_not_keyerror(self):
        """The historical bug: dropping a required column used to raise a
        bare KeyError from df["High"] instead of degrading to None."""
        bad_hist = _make_hist().drop(columns=["High", "Low"])
        with patch("dossier.data_sources.technical_setups.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_ticker(bad_hist)
            result = analyze_setup("BADCOLS")

        assert result is None

    def test_empty_history_returns_none(self):
        with patch("dossier.data_sources.technical_setups.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_ticker(pd.DataFrame())
            result = analyze_setup("EMPTY")

        assert result is None

    def test_too_few_rows_returns_none(self):
        with patch("dossier.data_sources.technical_setups.yf") as mock_yf:
            mock_yf.Ticker.return_value = _mock_ticker(_make_hist(n=10))
            result = analyze_setup("SHORT")

        assert result is None

    def test_fetch_exception_returns_none(self):
        stock = MagicMock()
        stock.history.side_effect = RuntimeError("network timeout")
        with patch("dossier.data_sources.technical_setups.yf") as mock_yf:
            mock_yf.Ticker.return_value = stock
            result = analyze_setup("TIMEOUT")

        assert result is None


class TestGenerateSetupsResilience:
    def test_one_bad_ticker_does_not_crash_the_batch(self):
        """generate_setups() is called with no try/except from generate.py's
        Stage 6 — a single ticker raising must not take down the run."""
        def _side_effect(ticker):
            if ticker == "BOOM":
                raise ValueError("simulated unexpected failure")
            return {
                "ticker": ticker,
                "bounce_2_bullish": False,
                "in_buy_zone": False,
                "ema_stack": "TANGLED",
                "trend_status": "UNKNOWN",
            }

        with patch(
            "dossier.data_sources.technical_setups.analyze_setup",
            side_effect=_side_effect,
        ):
            results = generate_setups(["GOOD1", "BOOM", "GOOD2"], max_setups=6)

        tickers = {r["ticker"] for r in results}
        assert tickers == {"GOOD1", "GOOD2"}
