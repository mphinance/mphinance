"""The short Tomorrow's Map note (tools/post_gamma_note.py compose_short).

Runs on a real sidecar captured 2026-11-27 (tests/fixtures). Pure string work:
nothing is posted and no network is touched.
"""
import copy
import importlib.util
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.modules.setdefault("requests", types.ModuleType("requests"))
_spec = importlib.util.spec_from_file_location("post_gamma_note", ROOT / "tools" / "post_gamma_note.py")
pgn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pgn)

FIX = json.loads((ROOT / "tests" / "fixtures" / "gamma_sidecar_2026-11-27.json").read_text())


def make(**over):
    d = copy.deepcopy(FIX)
    d.update(over)
    return d


def words(t):
    return len(t.split())


def paras(t):
    return t.split("\n\n")


def test_short_is_a_fraction_of_the_long_caption():
    d = make()
    short, long_ = pgn.compose_short(d), pgn.compose(d)
    assert words(short) < 260
    assert words(short) < words(long_) * 0.5


def test_the_roads_come_before_the_record():
    ps = paras(pgn.compose_short(make()))
    first_road = next(i for i, p in enumerate(ps) if p.startswith("If it goes up"))
    first_record = next(i for i, p in enumerate(ps) if p.startswith("Since "))
    assert first_road <= 1 < first_record


def test_header_names_the_session_and_spot():
    first = paras(pgn.compose_short(make()))[0]
    assert "Monday Nov 30" in first
    assert "Spot 728.68" in first


def test_early_close_is_named():
    first = paras(pgn.compose_short(make(nextSession="2026-11-27", nextSessionShort=True)))[0]
    assert "Friday Nov 27" in first and "early close at 1:00 PM ET" in first


def test_no_dashes_arrows_or_signoff():
    text = pgn.compose_short(make(lastCall={"day": "2026-11-25", "hits": 1, "total": 2, "summary": "took the UP road · MISS closed through 768.42 flip"}))
    assert not re.search(r"[—–]", text)
    assert "->" not in text
    assert "~ Michael" not in text and "~MPH" not in text


def test_sentences_start_capitalised():
    ps = paras(pgn.compose_short(make()))
    road = next(p for p in ps if p.startswith("If it goes up"))
    assert ": Rips through 730." in road


def test_graded_line_names_the_hard_levels_and_the_pin_condition():
    text = pgn.compose_short(make())
    assert "Graded tonight: 723.61 flip and 722 cushion." in text
    assert "730 pin counts only if the day grades RANGE" in text
    assert "markers the map reports and never grades" in text


def test_nothing_gradeable_says_so():
    d = make()
    d["scoreable"] = {"hard": [], "soft": []}
    assert "No level above is one the record can grade" in pgn.compose_short(d)


def test_record_line_is_plain_and_has_the_baseline_and_the_link():
    text = pgn.compose_short(make())
    assert "19 of 38 graded levels closed on the right side" in text
    assert "round numbers, same days, same rule: 19 of 40" in text
    assert "14 of 35 sessions scored nothing, so the rate covers 21" in text
    assert "That is not an edge yet." in text
    assert paras(text)[-2] == pgn.RECORD_URL


def test_lopsided_split_quotes_the_odds():
    d = make()
    d["record"]["paired"].update(inNoise=False, p=0.04)
    assert "about 4 times in 100" in pgn.compose_short(d)


def test_unpublishable_record_quotes_no_rate():
    d = make()
    d["record"] = {"publishable": False, "sessions": 6, "minSessions": 10}
    text = pgn.compose_short(d)
    assert "6 of 10 sessions graded" in text and "No hit rate" in text
    assert "closed on the right side" not in text


def test_last_call_variants():
    d = make(lastCall={"day": "2026-11-25", "hits": 1, "total": 2, "untested": 0,
                       "summary": "took the UP road · MISS closed through 768.42 flip"})
    assert "Last map (Nov 25 close): 1 of 2 levels price reached closed on the right side. Took the UP road; MISS closed through 768.42 flip." in pgn.compose_short(d)
    d = make(lastCall={"day": "2026-11-25", "total": 0, "untested": 2, "summary": "x"})
    assert "price never reached the levels it named" in pgn.compose_short(d)
    d = make(lastCall={"day": "2026-11-25", "total": 0, "untested": 0, "summary": "x"})
    assert "every level it named was a marker the map never grades" in pgn.compose_short(d)


def test_changes_are_listed_after_the_record():
    text = pgn.compose_short(make(), [{"text": "The note now names the session it covers."}])
    ps = paras(text)
    assert ps[-3] == "What changed in the map:"
    assert ps[-2] == "- The note now names the session it covers."


def test_long_style_is_untouched():
    assert pgn.compose(make()).startswith("SPY next session")
