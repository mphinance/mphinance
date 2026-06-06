"""Tests for dossier.backtesting.auto_backtest pure helpers."""
import json
import os
import tempfile
from unittest.mock import patch

from dossier.backtesting.auto_backtest import (
    load_track_record,
    recalculate_stats,
    save_track_record,
)


def test_load_track_record_missing_file():
    with patch("dossier.backtesting.auto_backtest.TRACK_RECORD_PATH", "/tmp/_absent_track.json"):
        result = load_track_record()
    assert result == {"entries": [], "stats": {}}


def test_load_track_record_existing_file():
    data = {"entries": [{"ticker": "AAPL", "date": "2026-01-01", "fwd_5d": 3.0}], "stats": {}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        with patch("dossier.backtesting.auto_backtest.TRACK_RECORD_PATH", path):
            result = load_track_record()
        assert result == data
    finally:
        os.unlink(path)


def test_save_load_roundtrip():
    data = {"entries": [{"ticker": "TSLA", "date": "2026-06-01", "score": 90}], "stats": {"avg_5d_return": 1.5}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name
    try:
        with patch("dossier.backtesting.auto_backtest.TRACK_RECORD_PATH", path):
            save_track_record(data)
            loaded = load_track_record()
        assert loaded == data
    finally:
        os.unlink(path)


def test_recalculate_stats_empty_entries():
    tr = {"entries": [], "stats": {}}
    result = recalculate_stats(tr)
    assert result["stats"] == {}


def test_recalculate_stats_no_validated_entries():
    tr = {"entries": [{"ticker": "AAPL", "date": "2026-01-01", "score": 80, "grade": "A"}], "stats": {}}
    result = recalculate_stats(tr)
    assert result["stats"] == {}


def test_recalculate_stats_basic():
    entries = [
        {"ticker": "AAPL", "date": "2026-01-01", "fwd_5d": 5.0},
        {"ticker": "MSFT", "date": "2026-01-02", "fwd_5d": -2.0},
        {"ticker": "GOOG", "date": "2026-01-03", "fwd_5d": 3.0},
    ]
    tr = {"entries": entries, "stats": {}}
    result = recalculate_stats(tr)
    stats = result["stats"]

    assert stats["total_picks_tracked"] == 3
    assert stats["total_validated"] == 3
    assert stats["avg_5d_return"] == round((5.0 - 2.0 + 3.0) / 3, 2)
    assert stats["win_rate_5d"] == round(2 / 3 * 100, 2)
    assert stats["best_pick"]["ticker"] == "AAPL"
    assert stats["best_pick"]["return"] == 5.0
    assert stats["worst_pick"]["ticker"] == "MSFT"
    assert stats["worst_pick"]["return"] == -2.0


def test_recalculate_stats_worst_pick_return_field():
    """Regression: worst_pick['return'] must use fwd_5d, not a non-existent key."""
    entries = [
        {"ticker": "AAPL", "date": "2026-01-01", "fwd_5d": 5.0},
        {"ticker": "MSFT", "date": "2026-01-02", "fwd_5d": -3.5},
    ]
    tr = {"entries": entries, "stats": {}}
    result = recalculate_stats(tr)
    assert result["stats"]["worst_pick"]["return"] == -3.5


def test_recalculate_stats_single_winner():
    entries = [{"ticker": "SPY", "date": "2026-02-01", "fwd_5d": 1.2}]
    tr = {"entries": entries, "stats": {}}
    result = recalculate_stats(tr)
    stats = result["stats"]
    assert stats["win_rate_5d"] == 100.0
    assert stats["sharpe_5d"] == 0  # std = 0 → sharpe = 0


def test_recalculate_stats_partial_validated():
    entries = [
        {"ticker": "AAPL", "date": "2026-01-01"},           # not yet validated
        {"ticker": "MSFT", "date": "2026-01-02", "fwd_5d": 4.0},
    ]
    tr = {"entries": entries, "stats": {}}
    result = recalculate_stats(tr)
    stats = result["stats"]
    assert stats["total_picks_tracked"] == 2
    assert stats["total_validated"] == 1
    assert stats["avg_5d_return"] == 4.0
