"""Tests for dossier.mood_ring — regime history append/dedup and mood mapping."""

import json
import pytest
from pathlib import Path

from dossier.mood_ring import regime_to_mood, append_regime_history


# ── regime_to_mood ──────────────────────────────────────────────────────────

def test_calm_is_risk_on():
    m = regime_to_mood("CALM")
    assert m["label"] == "risk-on"
    assert m["color"] == "#00ff41"
    assert m["emoji"] == "🟢"


def test_normal_is_risk_on():
    m = regime_to_mood("NORMAL")
    assert m["label"] == "risk-on"
    assert m["color"] == "#00ff41"


def test_elevated_is_neutral():
    m = regime_to_mood("ELEVATED")
    assert m["label"] == "neutral"
    assert m["color"] == "#f0b400"
    assert m["emoji"] == "🟡"


def test_fear_is_risk_off():
    m = regime_to_mood("FEAR")
    assert m["label"] == "risk-off"
    assert m["color"] == "#e53935"
    assert m["emoji"] == "🔴"


def test_panic_is_risk_off():
    m = regime_to_mood("PANIC")
    assert m["label"] == "risk-off"
    assert m["color"] == "#e53935"


def test_unknown_regime_fallback():
    m = regime_to_mood("WHATEVER")
    assert m["label"] == "unknown"
    assert m["color"] == "#888888"
    assert m["emoji"] == "⚪"


# ── append_regime_history ────────────────────────────────────────────────────

def test_creates_file_on_first_write(tmp_path):
    p = tmp_path / "data" / "regime_history.json"
    result = append_regime_history("2026-06-01", "CALM", 14.5, 0.012, p)
    assert p.exists()
    assert len(result) == 1
    assert result[0]["date"] == "2026-06-01"
    assert result[0]["regime"] == "CALM"
    assert result[0]["vix_level"] == 14.5
    assert result[0]["spy_change"] == 0.012
    assert result[0]["emoji"] == "🟢"


def test_appends_new_dates(tmp_path):
    p = tmp_path / "regime_history.json"
    append_regime_history("2026-06-01", "CALM", 14.0, 0.01, p)
    result = append_regime_history("2026-06-02", "NORMAL", 16.0, -0.005, p)
    assert len(result) == 2
    # newest first
    assert result[0]["date"] == "2026-06-02"
    assert result[1]["date"] == "2026-06-01"


def test_dedup_same_date_overwrites(tmp_path):
    p = tmp_path / "regime_history.json"
    append_regime_history("2026-06-01", "CALM", 14.0, 0.01, p)
    result = append_regime_history("2026-06-01", "FEAR", 28.0, -0.03, p)
    assert len(result) == 1
    assert result[0]["regime"] == "FEAR"
    assert result[0]["vix_level"] == 28.0


def test_result_is_newest_first(tmp_path):
    p = tmp_path / "regime_history.json"
    for day in ["2026-06-03", "2026-06-01", "2026-06-02"]:
        append_regime_history(day, "NORMAL", 18.0, 0.0, p)
    data = json.loads(p.read_text())
    dates = [e["date"] for e in data]
    assert dates == sorted(dates, reverse=True)


def test_tolerates_corrupt_file(tmp_path):
    p = tmp_path / "regime_history.json"
    p.write_text("not valid json{{{{")
    result = append_regime_history("2026-06-01", "CALM", 14.0, 0.0, p)
    assert len(result) == 1


def test_regime_name_matches_regime(tmp_path):
    p = tmp_path / "regime_history.json"
    result = append_regime_history("2026-06-01", "ELEVATED", 22.0, -0.01, p)
    assert result[0]["regime_name"] == result[0]["regime"] == "ELEVATED"
