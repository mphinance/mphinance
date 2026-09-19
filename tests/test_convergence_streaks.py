"""
Tests for dossier/convergence_streaks.py — persistent multi-screen agreement
across days on top of screener_convergence.py's daily snapshot.
"""

import json

from dossier.convergence_streaks import (
    append_snapshot,
    compute_streaks,
    format_streaks_text,
    load_history,
    record_snapshot,
    save_history,
    snapshot_from_convergence,
)


def _snap(date, **ticker_counts):
    return {"date": date, "tickers": dict(ticker_counts)}


def _convergence(*entries):
    """entries: (ticker, screen_count) tuples -> a compute_convergence()-shaped payload."""
    return {"tickers": [{"ticker": t, "screen_count": c} for t, c in entries]}


# ── snapshot_from_convergence ───────────────────────────────────────────

def test_snapshot_from_convergence_extracts_ticker_counts():
    conv = _convergence(("AAPL", 3), ("NVDA", 2))
    snap = snapshot_from_convergence("2026-09-15", conv)
    assert snap == {"date": "2026-09-15", "tickers": {"AAPL": 3, "NVDA": 2}}


def test_snapshot_from_convergence_handles_malformed_input():
    assert snapshot_from_convergence("2026-09-15", {})["tickers"] == {}
    assert snapshot_from_convergence("2026-09-15", {"tickers": "garbage"})["tickers"] == {}
    assert snapshot_from_convergence("2026-09-15", {"tickers": [{"no_ticker": 1}]})["tickers"] == {}


# ── append/load/save history ────────────────────────────────────────────

def test_append_snapshot_dedups_same_date():
    history = [_snap("2026-09-14", AAPL=2)]
    history = append_snapshot(history, _snap("2026-09-14", AAPL=3))
    assert len(history) == 1
    assert history[0]["tickers"]["AAPL"] == 3


def test_append_snapshot_sorts_by_date():
    history = append_snapshot([], _snap("2026-09-15", AAPL=2))
    history = append_snapshot(history, _snap("2026-09-14", AAPL=2))
    assert [e["date"] for e in history] == ["2026-09-14", "2026-09-15"]


def test_load_history_missing_file_returns_empty(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert load_history(p) == []


def test_record_snapshot_round_trips(tmp_path):
    path = tmp_path / "convergence_history.json"
    record_snapshot(path, "2026-09-14", _convergence(("AAPL", 2)))
    updated = record_snapshot(path, "2026-09-15", _convergence(("AAPL", 3)))

    assert [e["date"] for e in updated] == ["2026-09-14", "2026-09-15"]
    on_disk = json.loads(path.read_text())
    assert on_disk == updated


# ── compute_streaks ──────────────────────────────────────────────────────

def test_compute_streaks_empty_history():
    result = compute_streaks([])
    assert result == {"as_of": None, "min_days": 2, "streak_count": 0, "tickers": []}


def test_single_day_is_not_a_streak():
    result = compute_streaks([_snap("2026-09-15", AAPL=3)])
    assert result["streak_count"] == 0


def test_two_consecutive_days_counts_as_streak():
    history = [
        _snap("2026-09-14", AAPL=2),
        _snap("2026-09-15", AAPL=3),
    ]
    result = compute_streaks(history)
    assert result["streak_count"] == 1
    entry = result["tickers"][0]
    assert entry["ticker"] == "AAPL"
    assert entry["streak_days"] == 2
    assert entry["first_seen"] == "2026-09-14"
    assert entry["screen_count"] == 3
    assert entry["trend"] == "growing"


def test_missing_day_breaks_the_streak():
    history = [
        _snap("2026-09-12", AAPL=3),
        _snap("2026-09-13", NVDA=2),  # AAPL absent — streak resets
        _snap("2026-09-14", AAPL=2),
        _snap("2026-09-15", AAPL=3),
    ]
    result = compute_streaks(history)
    entry = next(e for e in result["tickers"] if e["ticker"] == "AAPL")
    assert entry["streak_days"] == 2
    assert entry["first_seen"] == "2026-09-14"


def test_fading_and_flat_trends():
    history = [
        _snap("2026-09-14", FADE=4, FLAT=2),
        _snap("2026-09-15", FADE=2, FLAT=2),
    ]
    result = compute_streaks(history)
    by_ticker = {e["ticker"]: e for e in result["tickers"]}
    assert by_ticker["FADE"]["trend"] == "fading"
    assert by_ticker["FLAT"]["trend"] == "flat"


def test_min_days_filter():
    history = [
        _snap("2026-09-13", AAPL=2),
        _snap("2026-09-14", AAPL=2),
        _snap("2026-09-15", AAPL=2),
    ]
    assert compute_streaks(history, min_days=3)["streak_count"] == 1
    assert compute_streaks(history, min_days=4)["streak_count"] == 0


def test_ranks_longer_streaks_first():
    history = [
        _snap("2026-09-13", SHORT=2, LONG=2),
        _snap("2026-09-14", LONG=2),
        _snap("2026-09-15", SHORT=2, LONG=2),
    ]
    # SHORT breaks on 09-14, so its current streak is only the last day.
    result = compute_streaks(history, min_days=1)
    tickers = [e["ticker"] for e in result["tickers"]]
    assert tickers[0] == "LONG"


def test_as_of_is_most_recent_date():
    history = [_snap("2026-09-14", AAPL=2), _snap("2026-09-15", AAPL=2)]
    assert compute_streaks(history)["as_of"] == "2026-09-15"


def test_malformed_entries_are_skipped():
    history = [
        _snap("2026-09-14", AAPL=2),
        {"date": None, "tickers": {}},
        "garbage",
        _snap("2026-09-15", AAPL=2),
    ]
    result = compute_streaks(history)
    assert result["streak_count"] == 1


# ── format_streaks_text ──────────────────────────────────────────────────

def test_format_streaks_text_empty():
    text = format_streaks_text({"min_days": 2, "tickers": []})
    assert "none holding" in text


def test_format_streaks_text_with_leader():
    streaks = compute_streaks([
        _snap("2026-09-14", AAPL=2),
        _snap("2026-09-15", AAPL=3),
    ])
    text = format_streaks_text(streaks)
    assert "AAPL" in text
    assert "2d" in text
    assert "growing" in text
