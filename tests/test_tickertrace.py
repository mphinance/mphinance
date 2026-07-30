"""
Tests for dossier/data_sources/tickertrace.py

Covers input validation on the TickerTrace API response: `fetch_institutional_data`
must never raise regardless of what shape `get_signals()` returns, since a
malformed/unexpected payload from an external API is exactly the silent-breakage
risk this repo has been burned by before.
"""

from dossier.data_sources import tickertrace


def _patch_signals(monkeypatch, payload):
    monkeypatch.setattr(tickertrace, "get_signals", lambda: payload)


class TestFetchInstitutionalData:
    def test_well_formed_payload(self, monkeypatch):
        _patch_signals(monkeypatch, {
            "asOfDate": "2026-07-29",
            "stats": {"total": 5},
            "signals": {
                "buying": [{"ticker": "AAPL"}, {"ticker": "912797RS8"}],
                "selling": [{"ticker": "MSFT"}],
            },
            "sectorFlow": {"inflows": [{"sector": "Tech"}], "outflows": []},
            "divergences": [{"ticker": "NVDA"}],
            "changes": [{"ticker": "TSLA"}],
        })
        result = tickertrace.fetch_institutional_data()
        assert result["as_of_date"] == "2026-07-29"
        assert [s["ticker"] for s in result["top_buying"]] == ["AAPL"]
        assert [s["ticker"] for s in result["top_selling"]] == ["MSFT"]
        assert result["sector_inflows"] == [{"sector": "Tech"}]
        assert result["divergences"] == [{"ticker": "NVDA"}]
        assert result["recent_changes"] == [{"ticker": "TSLA"}]

    def test_empty_dict_payload_is_unavailable(self, monkeypatch):
        _patch_signals(monkeypatch, {})
        result = tickertrace.fetch_institutional_data()
        assert result["unavailable"] is True
        assert result["top_buying"] == []

    def test_non_dict_payload_does_not_raise(self, monkeypatch):
        """A malformed API response (e.g. a bare JSON list or string) must
        degrade to 'unavailable' instead of crashing on `.get()`."""
        for bad_payload in (["not", "a", "dict"], "oops", 42, None):
            _patch_signals(monkeypatch, bad_payload)
            result = tickertrace.fetch_institutional_data()
            assert result["unavailable"] is True
            assert result["top_buying"] == []
            assert result["divergences"] == []

    def test_malformed_nested_fields_do_not_raise(self, monkeypatch):
        """`signals`/`sectorFlow` as the wrong type, or list fields as the
        wrong type, must be discarded rather than crashing on `.get()` or
        slicing."""
        _patch_signals(monkeypatch, {
            "asOfDate": "2026-07-29",
            "stats": "not-a-dict",
            "signals": ["not", "a", "dict"],
            "sectorFlow": None,
            "divergences": {"not": "a-list"},
            "changes": "not-a-list-either",
        })
        result = tickertrace.fetch_institutional_data()
        assert result["as_of_date"] == "2026-07-29"
        assert result["stats"] == {}
        assert result["top_buying"] == []
        assert result["top_selling"] == []
        assert result["sector_inflows"] == []
        assert result["sector_outflows"] == []
        assert result["divergences"] == []
        assert result["recent_changes"] == []

    def test_get_signals_exception_is_unavailable(self, monkeypatch):
        def _raise():
            raise RuntimeError("boom after retries")
        monkeypatch.setattr(tickertrace, "get_signals", _raise)
        result = tickertrace.fetch_institutional_data()
        assert result["unavailable"] is True

    def test_junk_tickers_filtered(self, monkeypatch):
        _patch_signals(monkeypatch, {
            "signals": {
                "buying": [{"ticker": "AAPL"}, {"ticker": "FGXXX"}, {"ticker": "912797RS8"}],
                "selling": [],
            },
            "sectorFlow": {},
            "divergences": [{"ticker": "CASH"}, {"ticker": "NVDA"}],
            "changes": [],
        })
        result = tickertrace.fetch_institutional_data()
        assert [s["ticker"] for s in result["top_buying"]] == ["AAPL"]
        assert [d["ticker"] for d in result["divergences"]] == ["NVDA"]
