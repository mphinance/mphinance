"""
Tests for dossier/sector_leadership.py — Sector Leadership Concentration.

Covers:
  1. compute_sector_leadership aggregation (leading sector/share/lift, empty/bad input)
  2. (leading_share, total_scored) → state classification
  3. history append/dedup + round-trip persistence (same pattern as score_dispersion)
  4. leadership_rotation vs N sessions back
  5. format_leadership_text summary line
"""

import json

from dossier.sector_leadership import (
    append_leadership,
    classify_leadership,
    compute_sector_leadership,
    format_leadership_text,
    leadership_rotation,
    load_history,
    record_leadership,
    save_history,
)


def _pick(ticker, score, sector):
    return {"ticker": ticker, "score": score, "sector": sector}


# ── compute_sector_leadership ───────────────────────────────────────────

def test_compute_sector_leadership_empty_input():
    d = compute_sector_leadership([])
    assert d["total_scored"] == 0
    assert d["leading_sector"] is None
    assert d["state"] == "insufficient"


def test_compute_sector_leadership_monolithic():
    # 5 Tech names dominate the top group entirely.
    ranked = [_pick(f"T{i}", 90 - i, "Technology") for i in range(5)]
    d = compute_sector_leadership(ranked, top_n=5)
    assert d["total_scored"] == 5
    assert d["leading_sector"] == "Technology"
    assert d["leading_share"] == 1.0
    assert d["state"] == "monolithic"
    assert d["color"] == "#e53935"


def test_compute_sector_leadership_concentrated():
    # Tech holds 3/6 = 50% of the top group → concentrated, not monolithic.
    ranked = (
        [_pick(f"T{i}", 90 - i, "Technology") for i in range(3)]
        + [_pick(f"E{i}", 80 - i, "Energy") for i in range(3)]
    )
    d = compute_sector_leadership(ranked, top_n=6)
    assert d["leading_sector"] == "Technology"
    assert d["leading_share"] == 0.5
    assert d["state"] == "concentrated"
    assert d["color"] == "#f0b400"


def test_compute_sector_leadership_broad_rotation():
    # 10 names spread evenly across 5 sectors → no sector clears 40%.
    sectors = ["Technology", "Energy", "Healthcare", "Financials", "Industrials"]
    ranked = [_pick(f"S{i}", 90 - i, sectors[i % len(sectors)]) for i in range(10)]
    d = compute_sector_leadership(ranked, top_n=10)
    assert d["state"] == "broad"
    assert d["color"] == "#00ff41"
    assert d["num_sectors_represented"] == 5


def test_compute_sector_leadership_insufficient_data():
    ranked = [_pick("A", 50, "Technology"), _pick("B", 40, "Energy")]
    d = compute_sector_leadership(ranked)
    assert d["total_scored"] == 2
    assert d["state"] == "insufficient"


def test_compute_sector_leadership_missing_sector_defaults_to_other():
    ranked = [{"ticker": "A", "score": 50}, {"ticker": "B", "score": 40}, {"ticker": "C", "score": 30}]
    d = compute_sector_leadership(ranked)
    assert d["leading_sector"] == "Other"


def test_compute_sector_leadership_never_raises_on_bad_values():
    # Missing/None scores fall back to 0.0 (still counted, same as score_dispersion).
    ranked = [{"ticker": "AAA", "score": None, "sector": "Tech"}, {"ticker": "BBB", "sector": "Tech"}]
    d = compute_sector_leadership(ranked)
    assert d["total_scored"] == 2
    assert d["leading_sector"] == "Tech"


def test_compute_sector_leadership_skips_unparseable_scores():
    ranked = [
        _pick("AAA", 40, "Tech"),
        {"ticker": "BBB", "score": "not-a-number", "sector": "Energy"},
        _pick("CCC", 30, "Tech"),
        _pick("DDD", 20, "Tech"),
    ]
    d = compute_sector_leadership(ranked)
    assert d["total_scored"] == 3
    assert d["leading_sector"] == "Tech"


def test_compute_sector_leadership_lift_reflects_overrepresentation():
    # Tech is 2/8 = 25% of the full universe but 2/2 = 100% of the top group.
    ranked = (
        [_pick("T1", 90, "Technology"), _pick("T2", 85, "Technology")]
        + [_pick(f"E{i}", 30 - i, "Energy") for i in range(6)]
    )
    d = compute_sector_leadership(ranked, top_n=2)
    assert d["leading_share"] == 1.0
    assert d["baseline_share"] == 0.25
    assert d["lift"] == 4.0


# ── classify_leadership ─────────────────────────────────────────────────

def test_classify_leadership_insufficient_below_min():
    s = classify_leadership(1.0, 2)
    assert s["state"] == "insufficient"


def test_classify_leadership_broad_low_share():
    s = classify_leadership(0.2, 10)
    assert s["state"] == "broad"


def test_classify_leadership_concentrated_mid_share():
    s = classify_leadership(0.5, 10)
    assert s["state"] == "concentrated"


def test_classify_leadership_monolithic_high_share():
    s = classify_leadership(0.7, 10)
    assert s["state"] == "monolithic"


def test_classify_leadership_boundaries():
    assert classify_leadership(0.39, 10)["state"] == "broad"
    assert classify_leadership(0.40, 10)["state"] == "concentrated"
    assert classify_leadership(0.64, 10)["state"] == "concentrated"
    assert classify_leadership(0.65, 10)["state"] == "monolithic"


# ── history append/dedup + persistence ────────────────────────────────

def _entry(date, sector="Technology", share=0.5):
    return {"date": date, "leading_sector": sector, "leading_share": share, "total_scored": 10}


def test_append_leadership_dedups_same_date():
    h = [_entry("2026-06-01", share=0.2)]
    h = append_leadership(h, _entry("2026-06-01", share=0.5))
    assert len(h) == 1
    assert h[0]["leading_share"] == 0.5


def test_append_leadership_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_leadership(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_leadership_round_trip(tmp_path):
    p = tmp_path / "sector_leadership_history.json"
    record_leadership(p, _entry("2026-06-01", share=0.1))
    record_leadership(p, _entry("2026-06-02", share=0.3))
    record_leadership(p, _entry("2026-06-02", share=0.4))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["leading_share"] == 0.4


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "sector_leadership_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── leadership_rotation ─────────────────────────────────────────────────

def test_leadership_rotation_insufficient_history():
    h = [_entry("2026-06-01"), _entry("2026-06-02")]
    t = leadership_rotation(h, "2026-06-02", lookback=5)
    assert t["rotated"] is False
    assert t["prior_sector"] is None
    assert t["lookback_date"] is None


def test_leadership_rotation_detects_change():
    h = [_entry(f"2026-06-{d:02d}", sector="Technology") for d in range(1, 6)]
    h.append(_entry("2026-06-06", sector="Energy"))
    t = leadership_rotation(h, "2026-06-06", lookback=5)
    assert t["rotated"] is True
    assert t["prior_sector"] == "Technology"
    assert t["lookback_date"] == "2026-06-01"


def test_leadership_rotation_no_change():
    h = [_entry(f"2026-06-{d:02d}", sector="Technology") for d in range(1, 6)]
    h.append(_entry("2026-06-06", sector="Technology"))
    t = leadership_rotation(h, "2026-06-06", lookback=5)
    assert t["rotated"] is False


# ── format_leadership_text ────────────────────────────────────────────────

def test_format_leadership_text_contains_key_fields():
    d = compute_sector_leadership([_pick("AAA", 60, "Technology"), _pick("BBB", 20, "Technology"), _pick("CCC", 10, "Energy")])
    text = format_leadership_text(d)
    assert "Sector Leadership" in text
    assert "Technology" in text
