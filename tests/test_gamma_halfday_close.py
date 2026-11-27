"""Guards the half-day close fix in tools/gamma_tomorrow.mjs (found 2026-11-27).

The tool called a session closed only when the last tick was at or after 16:00 ET,
so a 13:00 ET half-day read as "still open" until midnight: no ledger write, and the
poster refused to post. Christmas Eve 2026 is a Thursday, i.e. a Map night.
"""
from pathlib import Path

SRC = (Path(__file__).resolve().parent.parent / "tools" / "gamma_tomorrow.mjs").read_text()


def test_close_hour_knows_half_days():
    assert "const closeHourET = MARKET_SHORT.has(lastSession) ? 13 : 16;" in SRC
    assert "etParts(lastTick).hour >= closeHourET" in SRC
    assert "etParts(lastTick).hour >= 16" not in SRC


def test_session_closed_is_declared_after_the_half_day_calendar():
    # a const read before its declaration throws at runtime
    assert SRC.count("const sessionClosed") == 1
    assert SRC.index("const MARKET_SHORT") < SRC.index("const sessionClosed")


if __name__ == "__main__":
    test_close_hour_knows_half_days()
    test_session_closed_is_declared_after_the_half_day_calendar()
    print("ok")
