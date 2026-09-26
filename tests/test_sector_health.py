"""Tests for dossier.backtesting.sector_health.

screen_health.py breaks the validated scan archive down by strategy/grade/
regime/EMA stack but never by sector, even though every archived entry
already carries a `sector` field (scan_logger.py's snapshot). This covers
the new per-sector rollup: win rate/avg return per sector, the hot/cold
trend split, and that write_health_json() always produces a valid file
(including the zero-entries case) so the API endpoint never 404s.
"""
import json
import math

from dossier.backtesting import screen_health, sector_health
from dossier.backtesting.sector_health import compute_sector_health


def _entry(date, fwd_5d, sector="Technology"):
    return {
        "date": date,
        "sector": sector,
        "fwd_1d": None,
        "fwd_5d": fwd_5d,
        "fwd_10d": None,
        "fwd_21d": None,
    }


def test_compute_sector_health_empty_entries_is_a_valid_no_op_shape():
    health = compute_sector_health([], window=20)
    assert health["total_validated"] == 0
    assert health["by_sector"] == {}
    assert health["hottest_sector"] is None
    assert health["coldest_sector"] is None


def test_compute_sector_health_win_rate_and_avg_return():
    entries = [_entry(f"2026-07-{i:02d}", fwd_5d=v) for i, v in enumerate([2.0, -1.0, 3.0], start=1)]
    health = compute_sector_health(entries, window=20)
    sector = health["by_sector"]["Technology"]
    p5 = sector["periods"]["5d"]
    assert p5["n"] == 3
    assert p5["win_rate"] == round(2 / 3 * 100, 1)
    assert p5["avg_return"] == round((2.0 - 1.0 + 3.0) / 3, 2)


def test_compute_sector_health_ignores_groups_below_min_size():
    entries = [_entry("2026-07-01", fwd_5d=2.0), _entry("2026-07-02", fwd_5d=-1.0)]
    health = compute_sector_health(entries, window=20)
    assert health["by_sector"] == {}


def test_compute_sector_health_missing_sector_buckets_as_unknown():
    entries = [{"date": f"2026-07-0{i}", "fwd_5d": 1.0, "fwd_1d": None,
                "fwd_10d": None, "fwd_21d": None} for i in range(1, 4)]
    health = compute_sector_health(entries, window=20)
    assert "Unknown" in health["by_sector"]


def test_compute_sector_health_flags_heating_up_trend():
    older = [_entry(f"2026-06-{i:02d}", fwd_5d=-1.0) for i in range(1, 4)]
    newer = [_entry(f"2026-07-{i:02d}", fwd_5d=4.0) for i in range(1, 4)]
    health = compute_sector_health(older + newer, window=20)
    trend = health["by_sector"]["Technology"]["trend"]
    assert trend is not None
    assert trend["direction"] == "🔥 heating up"
    assert trend["delta"] > 0


def test_compute_sector_health_flags_cooling_off_trend():
    older = [_entry(f"2026-06-{i:02d}", fwd_5d=4.0) for i in range(1, 4)]
    newer = [_entry(f"2026-07-{i:02d}", fwd_5d=-1.0) for i in range(1, 4)]
    health = compute_sector_health(older + newer, window=20)
    trend = health["by_sector"]["Technology"]["trend"]
    assert trend is not None
    assert trend["direction"] == "🧊 cooling off"
    assert trend["delta"] < 0


def test_compute_sector_health_no_trend_below_min_trend_entries():
    entries = [_entry(f"2026-07-{i:02d}", fwd_5d=1.0) for i in range(1, 4)]
    health = compute_sector_health(entries, window=20)
    assert health["by_sector"]["Technology"]["trend"] is None


def test_compute_sector_health_ignores_nan_forward_returns():
    # scan_logger.py can write a plain float('nan') when yfinance can't price
    # an entry; json round-trips that as a bare NaN token that must not
    # poison the sector's avg/win-rate the way a naive sum()/len() would.
    entries = [
        _entry("2026-07-01", fwd_5d=float("nan")),
        _entry("2026-07-02", fwd_5d=2.0),
        _entry("2026-07-03", fwd_5d=4.0),
    ]
    health = compute_sector_health(entries, window=20)
    p5 = health["by_sector"]["Technology"]["periods"]["5d"]
    assert p5["n"] == 2
    assert p5["avg_return"] == 3.0
    assert not math.isnan(p5["avg_return"])


def test_compute_sector_health_ranks_hottest_and_coldest_sector():
    hot = [_entry(f"2026-07-{i:02d}", fwd_5d=5.0, sector="Energy") for i in range(1, 4)]
    cold = [_entry(f"2026-07-{i:02d}", fwd_5d=-5.0, sector="Healthcare") for i in range(1, 4)]
    health = compute_sector_health(hot + cold, window=20)
    assert health["hottest_sector"] == "Energy"
    assert health["coldest_sector"] == "Healthcare"


def test_write_health_json_writes_file_with_zero_entries(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    sector_api = tmp_path / "sector-health.json"
    monkeypatch.setattr(screen_health, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(sector_health, "SECTOR_HEALTH_API", sector_api)

    result = sector_health.write_health_json()

    assert result["total_validated"] == 0
    assert sector_api.exists()
    on_disk = json.loads(sector_api.read_text())
    assert on_disk["total_validated"] == 0


def test_write_health_json_reads_validated_entries_from_archive(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    sector_api = tmp_path / "api" / "sector-health.json"
    lines = [json.dumps(_entry(f"2026-07-{i:02d}", fwd_5d=1.5)) for i in range(1, 4)]
    scan_archive.write_text("\n".join(lines))
    monkeypatch.setattr(screen_health, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(sector_health, "SECTOR_HEALTH_API", sector_api)

    result = sector_health.write_health_json()

    assert result["total_validated"] == 3
    assert sector_api.exists()  # parent dir created even when nested
