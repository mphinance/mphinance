"""tools/map_sanity.py: the deterministic stand-in for the agent's eyeball check."""
import copy
import importlib.util
import json
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("map_sanity", ROOT / "tools" / "map_sanity.py")
ms = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ms)

FIX = json.loads((ROOT / "tests" / "fixtures" / "gamma_sidecar_2026-11-27.json").read_text())
NOW = datetime(2026, 11, 27, 20, 45, tzinfo=timezone.utc)  # 15 minutes after the fixture's asOf


def good(**over):
    d = copy.deepcopy(FIX)
    d["sessionClosed"] = True
    d.update(over)
    return d


def png(tmp_path, w=3200, h=1900, size=70_000, name="c.png"):
    body = ms.PNG_SIG + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", w, h) + b"\x08\x02\x00\x00\x00"
    p = tmp_path / name
    p.write_bytes(body + b"\x00" * max(0, size - len(body)))
    return p


def failed(d, p, **kw):
    return {n for n, ok, _ in ms.run_checks(d, p, now=NOW, **kw) if not ok}


def test_a_good_map_passes(tmp_path):
    assert failed(good(), png(tmp_path)) == set()


def test_open_book_fails_unless_allowed(tmp_path):
    d = good(sessionClosed=False)
    assert "book settled" in failed(d, png(tmp_path))
    assert failed(d, png(tmp_path), allow_open=True) == set()


def test_stale_book_fails(tmp_path):
    d = good(asOf="2026-11-27T10:00:00Z")
    assert "book is fresh" in failed(d, png(tmp_path))


def test_nan_level_fails(tmp_path):
    d = good(flip=float("nan"))
    f = failed(d, png(tmp_path))
    assert "no NaN or infinity anywhere" in f
    assert "spot, flip, pin, expected are positive numbers" in f


def test_missing_branch_fails(tmp_path):
    d = good()
    d["branches"] = d["branches"][:2]
    assert "three roads: IF, IF, ELSE" in failed(d, png(tmp_path))


def test_road_drawn_the_wrong_way_fails(tmp_path):
    d = good()
    d["triggers"]["up"], d["triggers"]["down"] = 700, 760
    assert "up trigger above spot above down trigger" in failed(d, png(tmp_path))


def test_regime_must_match_net_gex(tmp_path):
    d = good(regime="negative gamma")
    assert "regime matches the sign of net GEX" in failed(d, png(tmp_path))


def test_absurd_typical_day_fails(tmp_path):
    d = good(expected=90.0)
    assert "typical day between 0.1% and 6% of spot" in failed(d, png(tmp_path))


def test_weekend_next_session_fails(tmp_path):
    assert "next session is a weekday" in failed(good(nextSession="2026-11-28"), png(tmp_path))


def test_stale_calendar_fails(tmp_path):
    assert "calendar is not stale" in failed(good(calendarStale=True), png(tmp_path))


def test_bad_text_in_a_road_fails(tmp_path):
    d = good()
    d["branches"][0]["rule"] = "rips through NaN"
    assert "no NaN/undefined text in the roads" in failed(d, png(tmp_path))


def test_missing_or_tiny_or_non_png_chart_fails(tmp_path):
    assert "chart is a PNG" in failed(good(), tmp_path / "nope.png")
    assert "chart is not blank-small" in failed(good(), png(tmp_path, size=2_000))
    assert "chart is big enough" in failed(good(), png(tmp_path, w=800, h=400))
    bad = tmp_path / "x.png"
    bad.write_bytes(b"not a png" * 20000)
    assert "chart is a PNG" in failed(good(), bad)


def test_cli_exit_codes(tmp_path):
    side = tmp_path / "s.json"
    side.write_text(json.dumps(good(asOf=NOW.isoformat())))
    p = png(tmp_path)
    assert ms.main([str(side), str(p), "--allow-open"]) == 0
    side.write_text(json.dumps(good(flip=-1)))
    assert ms.main([str(side), str(p), "--allow-open"]) == 1
    assert ms.main([]) == 2
