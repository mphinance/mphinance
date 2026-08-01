"""
Tests for dossier/market_internals.py — Market Internals dashboard feed.

Covers:
  1. build_internals with all six history files present
  2. build_internals with missing/empty history files (never raises)
  3. _trend windowing (last N, skips missing field, sorts by date)
  4. write_internals_api round-trip persistence
"""

import json

from dossier.market_internals import build_internals, write_internals_api


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_build_internals_missing_files_never_raises(tmp_path):
    snapshot = build_internals(tmp_path)

    assert snapshot["breadth"]["trend"] == []
    assert snapshot["breadth"]["latest"] is None
    assert snapshot["dispersion"]["latest"] is None
    assert snapshot["sector_concentration"]["latest"] is None
    assert snapshot["junk_index"]["latest"] is None
    assert snapshot["extension"]["latest"] is None
    assert snapshot["factor_mix"]["latest"] is None


def test_build_internals_aggregates_all_six(tmp_path):
    _write(tmp_path / "breadth_history.json", [
        {"date": "2026-07-30", "breadth_score": 40.0, "state": "neutral"},
        {"date": "2026-07-31", "breadth_score": 72.0, "state": "expanding"},
    ])
    _write(tmp_path / "score_dispersion_history.json", [
        {"date": "2026-07-31", "coefficient_of_variation": 0.5, "state": "concentrated"},
    ])
    _write(tmp_path / "sector_leadership_history.json", [
        {"date": "2026-07-31", "leading_share": 0.6, "leading_sector": "Technology"},
    ])
    _write(tmp_path / "quality_breadth_history.json", [
        {"date": "2026-07-31", "leaders_flagged_pct": 20.0, "state": "mixed_leadership"},
    ])
    _write(tmp_path / "extension_index_history.json", [
        {"date": "2026-07-31", "net_extension": 35.0, "state": "balanced"},
    ])
    _write(tmp_path / "factor_leaderboard_history.json", [
        {"date": "2026-07-31", "factors": [{"factor": "adx", "avg_pct": 80.0}]},
    ])

    snapshot = build_internals(tmp_path, window=20)

    assert snapshot["window"] == 20
    assert snapshot["breadth"]["trend"] == [
        {"date": "2026-07-30", "value": 40.0},
        {"date": "2026-07-31", "value": 72.0},
    ]
    assert snapshot["breadth"]["latest"]["state"] == "expanding"
    assert snapshot["dispersion"]["latest"]["coefficient_of_variation"] == 0.5
    assert snapshot["sector_concentration"]["latest"]["leading_sector"] == "Technology"
    assert snapshot["junk_index"]["latest"]["leaders_flagged_pct"] == 20.0
    assert snapshot["extension"]["latest"]["net_extension"] == 35.0
    assert snapshot["factor_mix"]["latest"]["factors"][0]["factor"] == "adx"


def test_breadth_latest_gets_classified_when_missing_state(tmp_path):
    # compute_breadth() doesn't bake state/color/emoji/label into its return
    # value the way the other five compute_* functions do — market_internals
    # must classify it itself so the dashboard's "latest" shape is uniform.
    _write(tmp_path / "breadth_history.json", [
        {"date": "2026-07-31", "breadth_score": 72.0, "total_scored": 8},
    ])

    snapshot = build_internals(tmp_path)

    latest = snapshot["breadth"]["latest"]
    assert latest["breadth_score"] == 72.0
    assert latest["state"] == "expanding"
    assert latest["color"] == "#00ff41"
    assert "emoji" in latest and "label" in latest


def test_trend_windowing_keeps_only_last_n(tmp_path):
    history = [{"date": f"2026-07-{d:02d}", "breadth_score": float(d)} for d in range(1, 11)]
    _write(tmp_path / "breadth_history.json", history)

    snapshot = build_internals(tmp_path, window=3)

    assert [pt["value"] for pt in snapshot["breadth"]["trend"]] == [8.0, 9.0, 10.0]


def test_trend_skips_entries_missing_field(tmp_path):
    _write(tmp_path / "breadth_history.json", [
        {"date": "2026-07-30", "breadth_score": 40.0},
        {"date": "2026-07-31"},
    ])

    snapshot = build_internals(tmp_path)

    assert snapshot["breadth"]["trend"] == [{"date": "2026-07-30", "value": 40.0}]


def test_write_internals_api_round_trip(tmp_path):
    _write(tmp_path / "breadth_history.json", [
        {"date": "2026-07-31", "breadth_score": 55.0, "state": "neutral"},
    ])
    out_path = tmp_path / "api" / "market-internals.json"

    result = write_internals_api(out_path, tmp_path)

    assert out_path.exists()
    on_disk = json.loads(out_path.read_text())
    assert on_disk == result
    assert on_disk["breadth"]["latest"]["breadth_score"] == 55.0
