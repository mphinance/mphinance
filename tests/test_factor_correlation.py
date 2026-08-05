"""Tests for dossier.backtesting.factor_correlation.

Regression coverage for the same "sat dormant" gap screen_health.py's tests
guard against: write_factor_correlation_json() must always produce a valid
file, including the zero/insufficient-entries case, so a future dashboard
widget never 404s before the scan archive has enough validated picks.
"""
import json

from dossier.backtesting import factor_correlation
from dossier.backtesting.factor_correlation import (
    _pearson,
    compute_all_horizons,
    compute_factor_correlations,
    format_factor_correlation_text,
)


def _entry(rsi_14=None, score=None, fwd_5d=None, fwd_10d=None):
    return {
        "date": "2026-07-01",
        "rsi_14": rsi_14,
        "score": score,
        "fwd_5d": fwd_5d,
        "fwd_10d": fwd_10d,
    }


# ── _pearson ──────────────────────────────────────────────────────────

def test_pearson_perfect_positive_correlation():
    pairs = [(1.0, 2.0), (2.0, 4.0), (3.0, 6.0), (4.0, 8.0)]
    assert _pearson(pairs) == 1.0


def test_pearson_perfect_negative_correlation():
    pairs = [(1.0, 8.0), (2.0, 6.0), (3.0, 4.0), (4.0, 2.0)]
    assert _pearson(pairs) == -1.0


def test_pearson_undefined_below_two_points():
    assert _pearson([]) is None
    assert _pearson([(1.0, 1.0)]) is None


def test_pearson_undefined_when_no_variance():
    # Every x identical → var_x is 0, correlation is undefined not divide-by-zero.
    assert _pearson([(5.0, 1.0), (5.0, 2.0), (5.0, 3.0)]) is None


# ── compute_factor_correlations ─────────────────────────────────────────

def test_compute_factor_correlations_empty_entries():
    result = compute_factor_correlations([], "fwd_5d")
    assert result["horizon"] == "fwd_5d"
    assert result["factors_ranked"] == []
    assert len(result["factors_insufficient_data"]) == len(factor_correlation.NUMERIC_FACTORS)


def test_compute_factor_correlations_below_min_pairs_is_insufficient():
    # Only 3 paired (rsi_14, fwd_5d) observations — below the default min of 15.
    entries = [_entry(rsi_14=r, fwd_5d=r) for r in (30.0, 50.0, 70.0)]
    result = compute_factor_correlations(entries, "fwd_5d", min_pairs=15)
    names = {f["factor"] for f in result["factors_insufficient_data"]}
    assert "rsi_14" in names
    assert result["factors_ranked"] == []


def test_compute_factor_correlations_ranks_strong_factor_above_weak_one():
    # rsi_14 correlates perfectly with fwd_5d; score is random noise.
    entries = [
        _entry(rsi_14=float(i), score=(i * 37) % 5, fwd_5d=float(i))
        for i in range(20)
    ]
    result = compute_factor_correlations(entries, "fwd_5d", min_pairs=15)
    ranked_names = [f["factor"] for f in result["factors_ranked"]]
    assert ranked_names[0] == "rsi_14"
    assert result["factors_ranked"][0]["correlation"] == 1.0


def test_compute_factor_correlations_skips_non_numeric_values():
    entries = [_entry(rsi_14="not-a-number", fwd_5d=1.0)] * 20
    result = compute_factor_correlations(entries, "fwd_5d", min_pairs=15)
    rsi_row = next(
        f for f in result["factors_insufficient_data"] if f["factor"] == "rsi_14"
    )
    assert rsi_row["n"] == 0


# ── compute_all_horizons ─────────────────────────────────────────────────

def test_compute_all_horizons_shape():
    report = compute_all_horizons([_entry(rsi_14=1.0, fwd_5d=1.0, fwd_10d=2.0)])
    assert report["total_entries"] == 1
    assert set(report["by_horizon"].keys()) == {"fwd_5d", "fwd_10d"}


# ── format_factor_correlation_text ────────────────────────────────────

def test_format_factor_correlation_text_insufficient_data():
    report = compute_all_horizons([])
    text = format_factor_correlation_text(report, "fwd_5d")
    assert "insufficient data" in text


def test_format_factor_correlation_text_with_ranked_factors():
    entries = [_entry(rsi_14=float(i), fwd_5d=float(i)) for i in range(20)]
    report = compute_all_horizons(entries)
    text = format_factor_correlation_text(report, "fwd_5d")
    assert "rsi_14" in text
    assert "r=+1.00" in text


# ── write_factor_correlation_json ────────────────────────────────────────

def test_write_factor_correlation_json_writes_file_with_zero_entries(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    out_path = tmp_path / "api" / "factor-correlation.json"
    monkeypatch.setattr(factor_correlation, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(factor_correlation, "CORRELATION_API", out_path)

    result = factor_correlation.write_factor_correlation_json()

    assert result["total_entries"] == 0
    assert out_path.exists()
    on_disk = json.loads(out_path.read_text())
    assert on_disk["total_entries"] == 0


def test_write_factor_correlation_json_reads_entries_from_archive(tmp_path, monkeypatch):
    scan_archive = tmp_path / "scan_archive.jsonl"
    out_path = tmp_path / "api" / "factor-correlation.json"
    lines = [json.dumps(_entry(rsi_14=float(i), fwd_5d=float(i))) for i in range(5)]
    scan_archive.write_text("\n".join(lines))
    monkeypatch.setattr(factor_correlation, "SCAN_ARCHIVE", scan_archive)
    monkeypatch.setattr(factor_correlation, "CORRELATION_API", out_path)

    result = factor_correlation.write_factor_correlation_json()

    assert result["total_entries"] == 5
    assert out_path.exists()
