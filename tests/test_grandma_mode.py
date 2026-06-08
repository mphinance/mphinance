"""
Tests for dossier/grandma_mode.py — the plain-English translation layer.

Covers:
  1. explain_regime — every regime + unknown, plus VIX/SPY embellishments
  2. define — case-insensitive glossary lookup
  3. glossary_for — whole-word, case-insensitive term detection
  4. plain_english — panel context from mood-ring data + optional top pick
"""

import pytest

from dossier.grandma_mode import (
    define,
    explain_regime,
    glossary_for,
    plain_english,
)


# ── explain_regime ───────────────────────────────────────────────────

@pytest.mark.parametrize("regime", ["CALM", "NORMAL", "ELEVATED", "FEAR", "PANIC"])
def test_explain_regime_known_is_nonempty(regime):
    out = explain_regime(regime)
    assert isinstance(out, str) and len(out) > 10


def test_explain_regime_is_case_insensitive():
    assert explain_regime("calm") == explain_regime("CALM")


@pytest.mark.parametrize("regime", [None, "", "WAT"])
def test_explain_regime_unknown_falls_back(regime):
    assert "foggy" in explain_regime(regime).lower()


def test_explain_regime_low_vix_reads_relaxed():
    assert "relaxed" in explain_regime("CALM", vix_level=12).lower()


def test_explain_regime_high_vix_reads_twitchy():
    assert "twitchy" in explain_regime("PANIC", vix_level=38).lower()


def test_explain_regime_spy_direction():
    assert "up a bit" in explain_regime("NORMAL", spy_change=0.8)
    assert "down a bit" in explain_regime("NORMAL", spy_change=-0.8)
    assert "flat" in explain_regime("NORMAL", spy_change=0.0)


def test_explain_regime_tolerates_garbage_numbers():
    # must not raise on non-numeric vix/spy
    out = explain_regime("CALM", vix_level="n/a", spy_change="n/a")
    assert isinstance(out, str) and len(out) > 10


# ── define ───────────────────────────────────────────────────────────

def test_define_known_term():
    assert "fear gauge" in define("VIX").lower()


def test_define_is_case_insensitive():
    assert define("vix") == define("VIX")


@pytest.mark.parametrize("term", [None, "", "blockchain"])
def test_define_unknown_returns_none(term):
    assert define(term) is None


# ── glossary_for ─────────────────────────────────────────────────────

def test_glossary_for_finds_terms_present():
    terms = dict(glossary_for("The VIX is high and momentum is fading."))
    assert "VIX" in terms
    assert "momentum" in terms


def test_glossary_for_is_whole_word():
    # "EMArketing" should NOT match the term "EMA"
    assert glossary_for("EMArketing strategy") == []


def test_glossary_for_empty_text():
    assert glossary_for("") == []


def test_glossary_for_preserves_glossary_order():
    # VIX is defined before momentum in the glossary, so it comes first
    found = [t for t, _ in glossary_for("momentum and VIX both matter")]
    assert found == ["VIX", "momentum"]


# ── plain_english ────────────────────────────────────────────────────

def _ring(regime="CALM", vix=13.0, spy=0.8):
    return {"regime": regime, "regime_name": regime, "vix_level": vix,
            "spy_change": spy, "emoji": "😎"}


def test_plain_english_empty_without_regime():
    assert plain_english({}) == {}
    assert plain_english({"regime": None}) == {}


def test_plain_english_basic_shape():
    out = plain_english(_ring())
    assert out["summary"]
    assert out["emoji"] == "😎"
    assert out["disclaimer"]
    assert out["pick_line"] == ""  # no pick supplied
    assert isinstance(out["glossary"], list)


def test_plain_english_includes_pick():
    out = plain_english(_ring(), top_pick={"ticker": "AVGO", "score": 92})
    assert "AVGO" in out["pick_line"]
    assert "92" in out["pick_line"]


def test_plain_english_pick_without_score():
    out = plain_english(_ring(), top_pick={"ticker": "NVDA"})
    assert "NVDA" in out["pick_line"]
    assert "out of 100" not in out["pick_line"]


def test_plain_english_attaches_core_glossary():
    # the core jargon set is always spelled out, regardless of regime
    out = plain_english(_ring(regime="PANIC", vix=38.0))
    terms = [g["term"] for g in out["glossary"]]
    assert "VIX" in terms
    assert all(g["definition"] for g in out["glossary"])
