"""Tests for dossier.repeat_offenders — tickers recurring across the daily archive."""

import json

from dossier.repeat_offenders import (
    compute_repeat_offenders,
    _hits_from_dossier,
    _load_daily_archive,
)


def _day(date, tickers):
    """Build a daily entry: tickers is a list of (ticker, source) tuples."""
    return {"date": date, "hits": [{"ticker": t, "source": s} for t, s in tickers]}


class TestComputeRepeatOffenders:
    def test_empty_input_returns_no_repeats(self):
        result = compute_repeat_offenders([])
        assert result["repeat_count"] == 0
        assert result["tickers"] == []
        assert result["window_days"] == 0
        assert "generated_at" in result

    def test_single_appearance_is_not_a_repeat(self):
        result = compute_repeat_offenders([_day("2026-08-01", [("AAPL", "gold")])])
        assert result["repeat_count"] == 0

    def test_two_day_repeat_counted(self):
        entries = [
            _day("2026-08-01", [("AAPL", "gold")]),
            _day("2026-08-02", [("AAPL", "silver")]),
        ]
        result = compute_repeat_offenders(entries)
        assert result["repeat_count"] == 1
        entry = result["tickers"][0]
        assert entry["ticker"] == "AAPL"
        assert entry["appearances"] == 2
        assert entry["first_seen"] == "2026-08-01"
        assert entry["last_seen"] == "2026-08-02"
        assert entry["sources"] == ["gold", "silver"]

    def test_same_day_multiple_sources_counts_as_one_appearance(self):
        entries = [_day("2026-08-01", [("AAPL", "gold"), ("AAPL", "signal:Ghost Alpha V2")])]
        result = compute_repeat_offenders(entries, min_appearances=1)
        assert result["tickers"][0]["appearances"] == 1
        assert result["tickers"][0]["sources"] == ["gold", "signal:Ghost Alpha V2"]

    def test_min_appearances_filter(self):
        entries = [
            _day("2026-08-01", [("AAPL", "gold")]),
            _day("2026-08-02", [("AAPL", "gold")]),
            _day("2026-08-03", [("AAPL", "gold")]),
        ]
        result = compute_repeat_offenders(entries, min_appearances=3)
        assert result["repeat_count"] == 1
        result = compute_repeat_offenders(entries, min_appearances=4)
        assert result["repeat_count"] == 0

    def test_ranks_more_appearances_first(self):
        entries = [
            _day("2026-08-01", [("TWO", "gold"), ("THREE", "silver")]),
            _day("2026-08-02", [("TWO", "gold"), ("THREE", "silver")]),
            _day("2026-08-03", [("THREE", "silver")]),
        ]
        result = compute_repeat_offenders(entries)
        tickers = [e["ticker"] for e in result["tickers"]]
        assert tickers == ["THREE", "TWO"]

    def test_window_days_counts_valid_daily_entries(self):
        entries = [
            _day("2026-08-01", [("AAPL", "gold")]),
            _day("2026-08-02", []),
            {"date": None, "hits": []},
            "garbage",
        ]
        result = compute_repeat_offenders(entries)
        assert result["window_days"] == 2

    def test_malformed_hits_are_skipped(self):
        entries = [
            _day("2026-08-01", [("AAPL", "gold")]),
            {"date": "2026-08-02", "hits": [{"ticker": None, "source": "gold"}, "garbage", {}]},
        ]
        result = compute_repeat_offenders(entries, min_appearances=1)
        assert result["repeat_count"] == 1
        assert result["tickers"][0]["appearances"] == 1

    def test_non_list_input_never_raises(self):
        result = compute_repeat_offenders(None)
        assert result["repeat_count"] == 0
        result = compute_repeat_offenders("not-a-list")
        assert result["repeat_count"] == 0


class TestHitsFromDossier:
    def test_extracts_pick_tiers_and_top_signals(self):
        payload = {
            "picks": {
                "gold": {"ticker": "AJG"},
                "silver": {"ticker": "DRI"},
                "bronze": {"ticker": "VLTO"},
            },
            "signals": {"top_5": [{"symbol": "NVDA", "strategy": "Ghost Alpha V2"}]},
        }
        hits = _hits_from_dossier(payload)
        pairs = {(h["ticker"], h["source"]) for h in hits}
        assert ("AJG", "gold") in pairs
        assert ("DRI", "silver") in pairs
        assert ("VLTO", "bronze") in pairs
        assert ("NVDA", "signal:Ghost Alpha V2") in pairs

    def test_missing_sections_return_empty(self):
        assert _hits_from_dossier({}) == []

    def test_malformed_picks_and_signals_are_ignored(self):
        payload = {"picks": "garbage", "signals": {"top_5": "garbage"}}
        assert _hits_from_dossier(payload) == []


class TestLoadDailyArchive:
    def test_loads_recent_files_within_window(self, tmp_path):
        for date in ("2026-08-01", "2026-08-02", "2026-08-03"):
            payload = {
                "meta": {"date": date},
                "picks": {"gold": {"ticker": "AAPL"}},
                "signals": {"top_5": []},
            }
            (tmp_path / f"dossier-{date}.json").write_text(json.dumps(payload))

        entries = _load_daily_archive(2, tmp_path)
        assert [e["date"] for e in entries] == ["2026-08-02", "2026-08-03"]

    def test_missing_dir_returns_empty(self, tmp_path):
        assert _load_daily_archive(10, tmp_path / "nope") == []

    def test_skips_unparseable_files(self, tmp_path):
        (tmp_path / "dossier-2026-08-01.json").write_text("not json")
        assert _load_daily_archive(10, tmp_path) == []
