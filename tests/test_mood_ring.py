"""
Tests for dossier/mood_ring.py — the Market Mood Ring surfacing layer.

Covers:
  1. regime → mood mapping (all five regimes + unknown/None)
  2. history append/dedup (overwrite same date, sort, no duplicates)
  3. record_regime round-trip through a temp file
  4. build_mood_ring banner context (today selection + strip length)
"""

import json

import pytest

from dossier.mood_ring import (
    append_regime,
    build_mood_ring,
    load_history,
    record_regime,
    regime_to_mood,
    save_history,
)


# ── regime → mood mapping ────────────────────────────────────────────

@pytest.mark.parametrize("regime,expected_mood,expected_color", [
    ("CALM",     "risk-on",  "#00ff41"),
    ("NORMAL",   "risk-on",  "#00ff41"),
    ("ELEVATED", "neutral",  "#f0b400"),
    ("FEAR",     "risk-off", "#e53935"),
    ("PANIC",    "risk-off", "#e53935"),
])
def test_regime_to_mood_known(regime, expected_mood, expected_color):
    m = regime_to_mood(regime)
    assert m["mood"] == expected_mood
    assert m["color"] == expected_color
    assert m["emoji"]  # non-empty
    assert m["label"]


def test_regime_to_mood_is_case_insensitive():
    assert regime_to_mood("calm") == regime_to_mood("CALM")


@pytest.mark.parametrize("regime", [None, "", "WAT", "UNKNOWN"])
def test_regime_to_mood_unknown(regime):
    m = regime_to_mood(regime)
    assert m["mood"] == "unknown"
    assert m["color"] == "#888888"


def test_regime_to_mood_returns_a_copy():
    # callers may mutate the result; mutation must not leak into the next call
    m = regime_to_mood("CALM")
    m["color"] = "#000000"
    assert regime_to_mood("CALM")["color"] == "#00ff41"


# ── history append / dedup ───────────────────────────────────────────

def _entry(date, regime="NORMAL", vix=18.0):
    return {"date": date, "regime": regime, "regime_name": regime,
            "vix_level": vix, "spy_change": 0.1}


def test_append_adds_new_date():
    h = append_regime([], _entry("2026-06-01"))
    assert len(h) == 1
    assert h[0]["date"] == "2026-06-01"


def test_append_dedups_same_date_overwrites():
    h = [_entry("2026-06-01", "CALM", 12.0)]
    h = append_regime(h, _entry("2026-06-01", "FEAR", 28.0))
    assert len(h) == 1  # overwrote, did not duplicate
    assert h[0]["regime"] == "FEAR"
    assert h[0]["vix_level"] == 28.0


def test_append_sorts_by_date():
    h = []
    for d in ("2026-06-03", "2026-06-01", "2026-06-02"):
        h = append_regime(h, _entry(d))
    assert [e["date"] for e in h] == ["2026-06-01", "2026-06-02", "2026-06-03"]


def test_append_does_not_mutate_input():
    original = [_entry("2026-06-01")]
    append_regime(original, _entry("2026-06-02"))
    assert len(original) == 1  # input list untouched


# ── load / save / record round-trip ──────────────────────────────────

def test_load_history_missing_file(tmp_path):
    assert load_history(tmp_path / "nope.json") == []


def test_load_history_corrupt_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json")
    assert load_history(p) == []


def test_load_history_non_list(tmp_path):
    p = tmp_path / "obj.json"
    p.write_text('{"date": "2026-06-01"}')
    assert load_history(p) == []


def test_record_regime_round_trip(tmp_path):
    p = tmp_path / "regime_history.json"
    record_regime(p, _entry("2026-06-01", "CALM"))
    record_regime(p, _entry("2026-06-02", "FEAR"))
    # re-run same date → overwrite, not duplicate
    record_regime(p, _entry("2026-06-02", "PANIC"))

    saved = json.loads(p.read_text())
    assert [e["date"] for e in saved] == ["2026-06-01", "2026-06-02"]
    assert saved[-1]["regime"] == "PANIC"


def test_save_history_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "regime_history.json"
    save_history(p, [_entry("2026-06-01")])
    assert p.exists()


# ── build_mood_ring banner context ───────────────────────────────────

def test_build_mood_ring_empty_history():
    assert build_mood_ring([]) == {}


def test_build_mood_ring_uses_today_entry():
    history = [_entry("2026-06-01", "CALM"), _entry("2026-06-02", "FEAR")]
    ring = build_mood_ring(history, today=history[0])
    assert ring["date"] == "2026-06-01"
    assert ring["regime"] == "CALM"
    assert ring["color"] == "#00ff41"


def test_build_mood_ring_defaults_to_last_entry():
    history = [_entry("2026-06-01", "CALM"), _entry("2026-06-02", "FEAR")]
    ring = build_mood_ring(history)
    assert ring["date"] == "2026-06-02"
    assert ring["regime"] == "FEAR"


def test_build_mood_ring_strip_is_capped():
    history = [_entry(f"2026-06-{d:02d}") for d in range(1, 21)]  # 20 days
    ring = build_mood_ring(history, strip_len=10)
    assert len(ring["strip"]) == 10
    # strip keeps the most recent 10, in order
    assert ring["strip"][0]["date"] == "2026-06-11"
    assert ring["strip"][-1]["date"] == "2026-06-20"


def test_build_mood_ring_strip_entries_have_emoji_and_color():
    history = [_entry("2026-06-01", "PANIC")]
    ring = build_mood_ring(history)
    cell = ring["strip"][0]
    assert cell["emoji"]
    assert cell["color"] == "#e53935"
    assert cell["date"] == "2026-06-01"
