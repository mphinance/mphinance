"""
Tests for dossier/earnings_risk_flag.py — the Earnings Risk Flag.

Covers:
  1. compute_earnings_risk aggregation (leader selection, flagging, empty/bad input)
  2. history append/dedup + round-trip persistence (same pattern as follow_through)
  3. format_earnings_risk_text summary line
  4. save_api_output writes valid JSON
"""

import json

from dossier.earnings_risk_flag import (
    append_earnings_risk,
    compute_earnings_risk,
    format_earnings_risk_text,
    load_history,
    record_earnings_risk,
    save_api_output,
    save_history,
)


def _pick(ticker, score):
    return {"ticker": ticker, "score": score}


def _lookup_from(days_map):
    """Build a lookup_fn that returns days_map.get(ticker) without touching yfinance."""
    def _fn(ticker, max_days):
        return days_map.get(ticker)
    return _fn


# ── compute_earnings_risk ──────────────────────────────────────────────

def test_compute_earnings_risk_empty_input():
    r = compute_earnings_risk([], lookup_fn=_lookup_from({}))
    assert r["leaders_n"] == 0
    assert r["flagged_n"] == 0
    assert r["flagged_pct"] == 0.0
    assert r["flagged"] == []


def test_compute_earnings_risk_none_flagged():
    ranked = [_pick(f"T{i}", 90 - i) for i in range(5)]
    r = compute_earnings_risk(ranked, leader_count=5, lookup_fn=_lookup_from({}))
    assert r["leaders_n"] == 5
    assert r["flagged_n"] == 0
    assert r["flagged_pct"] == 0.0


def test_compute_earnings_risk_some_flagged():
    ranked = [_pick(f"T{i}", 90 - i) for i in range(5)]
    r = compute_earnings_risk(
        ranked, leader_count=5, lookup_fn=_lookup_from({"T0": 2, "T2": 5})
    )
    assert r["leaders_n"] == 5
    assert r["flagged_n"] == 2
    assert r["flagged_pct"] == 40.0
    # Sorted by soonest earnings first.
    assert [f["ticker"] for f in r["flagged"]] == ["T0", "T2"]


def test_compute_earnings_risk_only_counts_top_leader_count():
    ranked = [_pick(f"T{i}", 100 - i) for i in range(10)]
    ranked.append(_pick("STRAGGLER", 1))
    r = compute_earnings_risk(
        ranked, leader_count=10, lookup_fn=_lookup_from({"STRAGGLER": 1})
    )
    assert r["leaders_n"] == 10
    assert r["flagged_n"] == 0  # STRAGGLER didn't make the top 10


def test_compute_earnings_risk_never_raises_on_bad_values():
    ranked = [{"ticker": "AAA"}, {"score": None}, {"ticker": "BBB", "score": "nope"}]

    def _raising_lookup(ticker, max_days):
        raise ValueError("boom")

    r = compute_earnings_risk(ranked, lookup_fn=_raising_lookup)
    assert r["leaders_n"] == 2  # entries without a ticker are dropped
    assert r["flagged_n"] == 0


def test_compute_earnings_risk_defensive_against_unsorted_input():
    ranked = [_pick("LOW", 10), _pick("HIGH", 99)]
    r = compute_earnings_risk(
        ranked, leader_count=1, lookup_fn=_lookup_from({"HIGH": 3, "LOW": 1})
    )
    assert r["leaders_n"] == 1
    assert r["flagged"][0]["ticker"] == "HIGH"


# ── history append/dedup + persistence ─────────────────────────────────

def _entry(date, flagged_n=1):
    return {"date": date, "leaders_n": 10, "flagged_n": flagged_n}


def test_append_earnings_risk_dedups_same_date():
    h = [_entry("2026-06-01", 1)]
    h = append_earnings_risk(h, _entry("2026-06-01", 4))
    assert len(h) == 1
    assert h[0]["flagged_n"] == 4


def test_append_earnings_risk_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_earnings_risk(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_record_earnings_risk_round_trip(tmp_path):
    p = tmp_path / "earnings_risk_history.json"
    record_earnings_risk(p, _entry("2026-06-01", 1))
    record_earnings_risk(p, _entry("2026-06-02", 2))
    record_earnings_risk(p, _entry("2026-06-02", 5))  # overwrite, not duplicate

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["flagged_n"] == 5


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "earnings_risk_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── format_earnings_risk_text ───────────────────────────────────────────

def test_format_earnings_risk_text_insufficient():
    text = format_earnings_risk_text({"leaders_n": 0})
    assert "insufficient" in text.lower()


def test_format_earnings_risk_text_none_flagged():
    ranked = [_pick(f"T{i}", 90 - i) for i in range(3)]
    r = compute_earnings_risk(ranked, leader_count=3, lookup_fn=_lookup_from({}))
    text = format_earnings_risk_text(r)
    assert "none" in text.lower()


def test_format_earnings_risk_text_flagged_names():
    ranked = [_pick("AAA", 90), _pick("BBB", 80)]
    r = compute_earnings_risk(
        ranked, leader_count=2, lookup_fn=_lookup_from({"AAA": 1})
    )
    text = format_earnings_risk_text(r)
    assert "AAA" in text
    assert "1/2" in text


# ── save_api_output ──────────────────────────────────────────────────

def test_save_api_output_writes_valid_json(tmp_path):
    ranked = [_pick("AAA", 90)]
    r = compute_earnings_risk(ranked, leader_count=1, lookup_fn=_lookup_from({"AAA": 3}))
    save_api_output(r, tmp_path)

    saved = json.loads((tmp_path / "earnings-risk.json").read_text())
    assert saved["flagged_n"] == 1
    assert saved["flagged"][0]["ticker"] == "AAA"
    assert "generated_at" in saved
