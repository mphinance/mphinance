"""Tests for dossier/market_regime.py — VIX regime detection + hedging.

Covers the input-validation gap this module used to have: a malformed or
NaN-riddled yfinance response used to crash detect_regime() with a
KeyError/IndexError (uncaught by dossier/generate.py's Stage 4 call), which
took down the whole pipeline run instead of degrading to defaults.
"""

from unittest.mock import MagicMock, patch

import pandas as pd

from dossier.market_regime import check_yfinance_history, detect_regime, suggest_hedges


def _build_ohlcv(n=30, start=20.0, total_return_pct=0.0) -> pd.DataFrame:
    """Full OHLCV DataFrame required by check_yfinance_history."""
    end = start * (1 + total_return_pct / 100)
    step = (end - start) / (n - 1) if n > 1 else 0
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame({
        "Close": closes,
        "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes],
        "Volume": [1_000_000] * n,
    })


def _make_ticker_factory(df_map: dict[str, pd.DataFrame]):
    """Mimic yf.Ticker(symbol).history(period=...) keyed off df_map, falling
    back to a calm, quiet market for any symbol not explicitly overridden."""
    def _ticker(symbol):
        mock = MagicMock()
        mock.history.return_value = df_map.get(symbol, _build_ohlcv())
        return mock

    return _ticker


class TestDetectRegimeHappyPath:
    def test_calm_regime_classification(self):
        df_map = {
            "^VIX": _build_ohlcv(30, start=12.0),
            "^VIX3M": _build_ohlcv(30, start=14.0),
            "^VVIX": _build_ohlcv(30, start=90.0),
            "SPY": _build_ohlcv(30, start=500.0, total_return_pct=5.0),
        }
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["regime"] == "CALM"
        assert result["vix"]["vix_level"] == 12.0

    def test_panic_regime_classification(self):
        df_map = {
            "^VIX": _build_ohlcv(30, start=40.0),
            "^VIX3M": _build_ohlcv(30, start=30.0),
            "^VVIX": _build_ohlcv(30, start=140.0),
            "SPY": _build_ohlcv(30, start=400.0, total_return_pct=-8.0),
        }
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["regime"] == "PANIC"
        assert "WARNING" in result["market_context"]  # VIX/VIX3M inversion


class TestDetectRegimeDegradesGracefully:
    """The known failure shapes this repo has been burned by — none of these
    should raise, and each should fall back to detect_regime()'s defaults."""

    def test_missing_close_column_falls_back_to_default(self):
        malformed = pd.DataFrame({"High": [21.0, 22.0], "Low": [19.0, 19.5]})
        df_map = {"^VIX": malformed}
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["vix"]["vix_level"] == 20.0  # default, not a crash
        assert result["regime"] == "NORMAL"

    def test_all_nan_close_falls_back_to_default(self):
        nan_hist = _build_ohlcv(30, start=45.0)
        nan_hist["Close"] = float("nan")
        df_map = {"^VIX": nan_hist}
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["vix"]["vix_level"] == 20.0
        assert result["regime"] == "NORMAL"

    def test_empty_history_falls_back_to_default(self):
        df_map = {"^VIX": pd.DataFrame()}
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["vix"]["vix_level"] == 20.0

    def test_fetch_exception_falls_back_to_default(self):
        def _ticker(symbol):
            mock = MagicMock()
            mock.history.side_effect = RuntimeError("network timeout")
            return mock

        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _ticker
            result = detect_regime()

        assert result["regime"] == "NORMAL"  # default VIX 20.0 -> NORMAL band
        assert result["vix"]["vix_level"] == 20.0

    def test_partial_nan_drops_only_bad_rows(self):
        """A few NaN rows mid-series (holiday gaps) shouldn't poison the read —
        the last valid Close should still drive the classification."""
        hist = _build_ohlcv(30, start=12.0)
        hist.loc[hist.index[-3:-1], "Close"] = float("nan")
        df_map = {"^VIX": hist}
        with patch("dossier.market_regime.yf") as mock_yf:
            mock_yf.Ticker.side_effect = _make_ticker_factory(df_map)
            result = detect_regime()

        assert result["regime"] == "CALM"
        assert result["vix"]["vix_level"] == hist["Close"].dropna().iloc[-1]


class TestCheckYfinanceHistoryFallback:
    """dossier/market_regime.py can run as a standalone script (outside the
    dossier package), so it carries its own check_yfinance_history fallback
    when dossier.utils.validate_api isn't importable. Exercise that fallback
    directly since detect_regime() may instead be using the real one."""

    def test_none_is_invalid(self):
        ok, reason = check_yfinance_history(None, "^VIX")
        assert not ok
        assert "^VIX" in reason

    def test_empty_is_invalid(self):
        ok, _ = check_yfinance_history(pd.DataFrame(), "^VIX")
        assert not ok

    def test_too_few_rows_is_invalid(self):
        ok, _ = check_yfinance_history(_build_ohlcv(1), "^VIX", min_rows=2)
        assert not ok

    def test_valid_history_passes(self):
        ok, reason = check_yfinance_history(_build_ohlcv(5), "^VIX")
        assert ok
        assert reason == ""


class TestSuggestHedges:
    def test_panic_suggests_capital_protection(self):
        suggestions = suggest_hedges("PANIC", [])
        assert any("CRISIS" in s for s in suggestions)

    def test_calm_is_bullish(self):
        suggestions = suggest_hedges("CALM", [])
        assert any("BULLISH" in s for s in suggestions)

    def test_elevated_hedges_named_picks(self):
        suggestions = suggest_hedges("ELEVATED", ["NVDA"])
        assert any("NVDA" in s for s in suggestions)
