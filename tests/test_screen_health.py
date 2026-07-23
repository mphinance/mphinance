"""Tests for dossier.backtesting.screen_health.

Regression coverage for the "sat dormant" gap: screen_health.py existed but
was never wired into the pipeline, so docs/api/screen-health.json never got
written. write_health_json() must always produce a valid file — including
the zero-entries case on day one before the scan archive has any validated
picks — so the dashboard page never 404s.
"""
import json

from dossier.backtesting import screen_health
from dossier.backtesting.screen_health import compute_health


def _entry(date, fwd_5d, fwd_1d=None, strategy="TAO", grade="A", regime="NORMAL", ema_stack="FULL BULLISH"):
    return {
        "date": date,
        "strategy": strategy,
        "grade": grade,
        "regime": regime,
        "ema_stack": ema_stack,
        "fwd_1d": fwd_1d,
        "fwd_5d": fwd_5d,
        "fwd_10d": None,
        "fwd_21d": None,
    }


def test_compute_health_empty_entries_is_a_valid_no_op_shape():
    health = compute_health([], window=20)
    assert health["total_validated"] == 0
    assert health["by_strategy"] == {}
    assert health["alerts"] == []


def test_compute_health_win_rate_and_avg_return():
    entries = [_entry(f"2026-07-{i:02d}", fwd_5d=v) for i, v in enumerate([2.0, -1.0, 3.0], start=1)]
    health = compute_health(entries, window=20)
    strat = health["by_strategy"]["TAO"]
    p5 = strat["periods"]["5d"]
    assert p5["n"] == 3
    assert p5["win_rate"] == round(2 / 3 * 100, 1)
    assert p5["avg_return"] == round((2.0 - 1.0 + 3.0) / 3, 2)


def test_compute_health_flags_critical_alert_below_30pct_win_rate():
    losers = [_entry(f"2026-07-{i:02d}", fwd_5d=-2.0) for i in range(1, 6)]
    winner = [_entry("2026-07-06", fwd_5d=1.0)]
    health = compute_health(losers + winner, window=20)
    strat = health["by_strategy"]["TAO"]
    assert strat["alert"] == "🔴 CRITICAL — WR below 30%, consider disabling"
    assert any("CRITICAL" in a for a in health["alerts"])


def test_compute_health_flags_strong_alert_above_70pct_win_rate():
    winners = [_entry(f"2026-07-{i:02d}", fwd_5d=2.0) for i in range(1, 6)]
    loser = [_entry("2026-07-06", fwd_5d=-1.0)]
    health = compute_health(winners + loser, window=20)
    strat = health["by_strategy"]["TAO"]
    assert strat["alert"] == "🟢 STRONG — WR above 70%, increase allocation"


def test_compute_health_ignores_groups_below_min_size():
    entries = [_entry("2026-07-01", fwd_5d=2.0), _entry("2026-07-02", fwd_5d=-1.0)]
    health = compute_health(entries, window=20)
    assert health["by_strategy"] == {}


def test_write_health_json_writes_file_with_zero_entries(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    health_api = tmp_path / "screen-health.json"
    monkeypatch.setattr(screen_health, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(screen_health, "HEALTH_API", health_api)

    result = screen_health.write_health_json()

    assert result["total_validated"] == 0
    assert health_api.exists()
    on_disk = json.loads(health_api.read_text())
    assert on_disk["total_validated"] == 0


def test_write_health_json_reads_validated_entries_from_archive(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    health_api = tmp_path / "api" / "screen-health.json"
    lines = [json.dumps(_entry(f"2026-07-{i:02d}", fwd_5d=1.5)) for i in range(1, 4)]
    scan_archive.write_text("\n".join(lines))
    monkeypatch.setattr(screen_health, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(screen_health, "HEALTH_API", health_api)

    result = screen_health.write_health_json()

    assert result["total_validated"] == 3
    assert health_api.exists()  # parent dir created even when nested
