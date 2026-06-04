"""
Tests for dossier/utils/validate_api.py

Covers the three known external-API failure shapes:
  1. yfinance .history() — empty / missing columns / insufficient rows
  2. yfinance .info — None / empty dict
  3. Tradier "null" string
  4. safe_json — bad JSON response
"""

import sys
import types

import pandas as pd
import pytest

from dossier.utils.validate_api import (
    check_yfinance_history,
    check_yfinance_info,
    is_tradier_null,
    safe_json,
)


# ── helpers ──────────────────────────────────────────────────────────

def _make_df(cols=("Close", "High", "Low", "Volume"), rows=5):
    """Minimal DataFrame with the specified columns."""
    data = {c: [float(i) for i in range(rows)] for c in cols}
    return pd.DataFrame(data)


class _FakeResponse:
    """Minimal stand-in for requests.Response."""
    def __init__(self, text, status_code=200):
        self._text = text
        self.status_code = status_code

    def json(self):
        import json
        return json.loads(self._text)


# ── check_yfinance_history ────────────────────────────────────────────

class TestCheckYfinanceHistory:
    def test_valid_df(self):
        df = _make_df()
        ok, reason = check_yfinance_history(df, "AAPL")
        assert ok
        assert reason == ""

    def test_none_df(self):
        ok, reason = check_yfinance_history(None, "AAPL")
        assert not ok
        assert "None" in reason

    def test_empty_df(self):
        ok, reason = check_yfinance_history(pd.DataFrame(), "AAPL")
        assert not ok
        assert "empty" in reason

    def test_missing_close_column(self):
        df = _make_df(cols=("High", "Low", "Volume"))
        ok, reason = check_yfinance_history(df, "TSLA")
        assert not ok
        assert "Close" in reason

    def test_missing_multiple_columns(self):
        df = _make_df(cols=("Close",))
        ok, reason = check_yfinance_history(df, "TSLA")
        assert not ok
        # All three missing cols should be named
        assert "High" in reason or "Low" in reason or "Volume" in reason

    def test_insufficient_rows(self):
        df = _make_df(rows=1)
        ok, reason = check_yfinance_history(df, "AAPL", min_rows=2)
        assert not ok
        assert "1" in reason

    def test_exactly_min_rows(self):
        df = _make_df(rows=2)
        ok, _ = check_yfinance_history(df, "AAPL", min_rows=2)
        assert ok

    def test_custom_min_rows(self):
        df = _make_df(rows=90)
        ok, _ = check_yfinance_history(df, "AAPL", min_rows=90)
        assert ok

    def test_extra_columns_ok(self):
        df = _make_df(cols=("Close", "High", "Low", "Volume", "Dividends"))
        ok, _ = check_yfinance_history(df, "AAPL")
        assert ok


# ── check_yfinance_info ───────────────────────────────────────────────

class TestCheckYfinanceInfo:
    def test_valid_dict(self):
        info = {"longName": "Apple Inc.", "sector": "Technology"}
        result = check_yfinance_info(info, "AAPL")
        assert result == info

    def test_none_returns_empty_dict(self, capsys):
        result = check_yfinance_info(None, "AAPL")
        assert result == {}
        captured = capsys.readouterr()
        assert "AAPL" in captured.err
        assert "empty" in captured.err.lower()

    def test_empty_dict_returns_empty_dict(self, capsys):
        result = check_yfinance_info({}, "NVDA")
        assert result == {}
        captured = capsys.readouterr()
        assert "NVDA" in captured.err

    def test_falsy_but_not_none(self, capsys):
        # e.g. yfinance occasionally returns an empty dict-like object
        result = check_yfinance_info({}, "XYZ")
        assert result == {}
        assert "XYZ" in capsys.readouterr().err


# ── is_tradier_null ───────────────────────────────────────────────────

class TestIsTradierNull:
    @pytest.mark.parametrize("value", [
        None,
        "null",
        "NULL",
        "Null",
        "  null  ",
        {},
        [],
    ])
    def test_null_cases(self, value):
        assert is_tradier_null(value)

    @pytest.mark.parametrize("value", [
        {"option": []},
        [{"strike": 100}],
        "AAPL",
        0,
        False,
        {"key": "value"},
    ])
    def test_non_null_cases(self, value):
        assert not is_tradier_null(value)

    def test_non_empty_list(self):
        assert not is_tradier_null([1, 2, 3])

    def test_non_empty_dict(self):
        assert not is_tradier_null({"date": ["2026-06-20"]})


# ── safe_json ─────────────────────────────────────────────────────────

class TestSafeJson:
    def test_valid_json(self):
        resp = _FakeResponse('{"data": [1, 2, 3]}')
        result = safe_json(resp)
        assert result == {"data": [1, 2, 3]}

    def test_invalid_json_returns_none(self, capsys):
        resp = _FakeResponse("<html>Error</html>", status_code=503)
        result = safe_json(resp, "TradingView scanner")
        assert result is None
        captured = capsys.readouterr()
        assert "TradingView scanner" in captured.err
        assert "503" in captured.err

    def test_invalid_json_no_context(self, capsys):
        resp = _FakeResponse("not json")
        result = safe_json(resp)
        assert result is None
        assert capsys.readouterr().err != ""

    def test_empty_json_object(self):
        resp = _FakeResponse("{}")
        result = safe_json(resp)
        assert result == {}

    def test_json_array(self):
        resp = _FakeResponse('[1, 2, 3]')
        result = safe_json(resp)
        assert result == [1, 2, 3]
