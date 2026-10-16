"""Offline tests for the Michael-protégé retrieval layer. No LiveKit import:
CI installs requirements.txt only, and these modules are stdlib."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "livekit"))

from corpus import Corpus, Doc, tokenize  # noqa: E402
from meetings import Meeting, next_meetings, parse_meetings  # noqa: E402
from persona import build_instructions, disclosure_line, load_disclosure  # noqa: E402


# ---------- corpus ----------

def _mini_corpus() -> Corpus:
    return Corpus(
        [
            Doc("a", "2025-01-25", "afterhour", "", "Become the casino and get rich slowly. $RXRX calls at the top tick.", ["RXRX"]),
            Doc("b", "2025-03-26", "afterhour", "", "Every single one rejected due to felony DUI. Give them the finger.", []),
            Doc("c", "2026-03-04", "afterhour", "", "Human Michael at the top here. I generated this last night with the wheel screener.", []),
            Doc("d", "", "article", "Wheel Watchlist", "The wheel: sell a cash secured put, get assigned, sell the covered call.", []),
        ]
    )


def test_tokenize_keeps_tickers_and_drops_stopwords():
    toks = tokenize("The $GLXY wheel is a money glitch")
    assert "$glxy" in toks and "wheel" in toks and "glitch" in toks
    assert "the" not in toks and "is" not in toks


def test_search_ranks_the_relevant_doc_first():
    c = _mini_corpus()
    hits = c.search("casino rich slowly")
    assert hits and hits[0].doc.id == "a"
    assert "casino" in hits[0].snippet.lower()


def test_search_returns_empty_for_nonsense():
    assert _mini_corpus().search("zzqx plorb") == []


def test_pure_only_excludes_post_pivot_afterhour_posts():
    c = _mini_corpus()
    ids = {h.doc.id for h in c.search("wheel screener", k=5, pure_only=True)}
    assert "c" not in ids  # 2026-03-04 is after the 2026-01-31 pivot
    assert "d" in ids  # articles are not filtered by the pivot


def test_by_ticker_strips_dollar_sign():
    docs = _mini_corpus().by_ticker("$rxrx")
    assert [d.id for d in docs] == ["a"]


@pytest.mark.skipif(not (ROOT / "data" / "afterhour" / "mphinance.json").exists(), reason="archive not checked out")
def test_real_archive_loads_and_finds_the_dui_post():
    c = Corpus.load(ROOT)
    assert len(c.docs) > 1000
    hits = c.search("felony DUI unemployment professional trader", pure_only=True)
    assert hits and hits[0].doc.date == "2025-03-26"


# ---------- meetings ----------

SAMPLE = """
Sun Morning Hartford Group
Sunday - 10:30 AM
Codes: Handicap Access
Notes: Park in lower lot, rear entrance.

Group ID Number: 000083921
District Number: 12
Location:
Landmark Credit Union
1400 Schauer Dr
Hartford, WI 53027
County: Washington
Open Map in a New Window
Tuesday Night Big Book
Tuesday - 7:00 PM
Codes: Closed
Location:
Some Church
1 Main St
West Bend, WI 53095
County: Washington
"""


def test_parse_meetings_reads_day_time_and_location():
    ms = parse_meetings(SAMPLE)
    assert [m.name for m in ms] == ["Sun Morning Hartford Group", "Tuesday Night Big Book"]
    a, b = ms
    assert (a.weekday, a.hour, a.minute, a.city) == (6, 10, 30, "Hartford")
    assert (b.weekday, b.hour, b.minute, b.city) == (1, 19, 0, "West Bend")
    assert a.place == "Landmark Credit Union"


def test_next_meetings_orders_by_soonest_and_filters_by_city():
    ms = parse_meetings(SAMPLE)
    monday_noon = datetime(2026, 10, 12, 12, 0)  # a Monday
    soonest = next_meetings(ms, monday_noon, k=2)
    assert soonest[0].name == "Tuesday Night Big Book"
    only_hartford = next_meetings(ms, monday_noon, city="hartford", k=2)
    assert [m.name for m in only_hartford] == ["Sun Morning Hartford Group"]


def test_next_start_rolls_to_next_week_if_already_passed():
    m = Meeting("x", weekday=0, hour=9, minute=0)
    now = datetime(2026, 10, 12, 10, 0)  # Monday 10:00, after 9:00
    assert m.next_start(now) == datetime(2026, 10, 19, 9, 0)


# ---------- persona ----------

def test_persona_files_exist_and_build_instructions():
    text = build_instructions()
    assert "SOUL.md" in text and "IDENTITY.md" in text
    assert "SPOKEN MODE" in text
    assert "—" not in text and "–" not in text, "em/en dash in the persona files, VOICE.md bans them"


def test_disclosure_line_is_extracted_and_says_not_michael():
    line = load_disclosure()
    assert "not Michael" in line
    assert disclosure_line("no quote here").startswith("Quick thing")
