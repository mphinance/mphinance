#!/usr/bin/env python3
"""Deterministic pre-post checks for Tomorrow's Map.

The nightly agent used to look at the chart and stop if it was visibly broken.
An unattended script cannot look, so it checks the things that actually broke in
the past: a NaN level, a missing branch, a road drawn the wrong way, an empty
chart. Run it on the sidecar JSON and PNG the tool just wrote, BEFORE posting.

    python3 tools/map_sanity.py <sidecar.json> <chart.png> [--allow-open]

Exit 0 when every check passes, 1 when any fails. Each check prints one line.
--allow-open skips the two "the book has settled" checks; it exists only for
supervised dry runs during the session.
"""
import json
import math
import struct
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
MIN_PNG_BYTES = 60_000
MIN_W, MIN_H = 1600, 900
MAX_AGE = timedelta(hours=2)
BAD_TEXT = ("NaN", "undefined", "Infinity", "None")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _walk_numbers(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _walk_numbers(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk_numbers(v, f"{path}[{i}]")
    elif isinstance(o, float) and not math.isfinite(o):
        yield path


def png_info(path):
    """(ok, width, height, size) without any imaging library."""
    p = Path(path)
    if not p.is_file():
        return False, 0, 0, 0
    b = p.read_bytes()
    if b[:8] != PNG_SIG or b[12:16] != b"IHDR":
        return False, 0, 0, len(b)
    w, h = struct.unpack(">II", b[16:24])
    return True, w, h, len(b)


def run_checks(d, png_path, allow_open=False, now=None):
    """Return a list of (name, ok, detail)."""
    now = now or datetime.now(timezone.utc)
    out = []

    def check(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    if not allow_open:
        check("book settled", d.get("sessionClosed") is True,
              f"sessionClosed={d.get('sessionClosed')!r} forSession={d.get('forSession')!r}")
        try:
            age = now - datetime.fromisoformat(str(d["asOf"]).replace("Z", "+00:00"))
            check("book is fresh", timedelta(0) <= age <= MAX_AGE, f"asOf age {age}")
        except Exception as e:  # noqa: BLE001
            check("book is fresh", False, f"asOf unreadable: {e}")

    bad = list(_walk_numbers(d))
    check("no NaN or infinity anywhere", not bad, ", ".join(bad[:4]))

    spot, flip, pin, exp = d.get("spot"), d.get("flip"), d.get("pin"), d.get("expected")
    core_ok = all(_num(v) and v > 0 for v in (spot, flip, pin, exp))
    check("spot, flip, pin, expected are positive numbers", core_ok, f"{spot} {flip} {pin} {exp}")
    if core_ok:
        check("pin within 5% of spot", abs(pin - spot) / spot < 0.05, f"pin {pin} spot {spot}")
        pct = exp / spot * 100
        check("typical day between 0.1% and 6% of spot", 0.1 <= pct <= 6, f"{pct:.2f}%")

    br = d.get("branches") or []
    kinds = [str(b.get("kind", "")).upper() for b in br]
    check("three roads: IF, IF, ELSE", kinds == ["IF", "IF", "ELSE"], f"kinds={kinds}")
    check("every road has a condition and a rule",
          all((b.get("cond") or "").strip() and (b.get("rule") or "").strip() for b in br))
    text = " ".join(f"{b.get('cond', '')} {b.get('rule', '')}" for b in br)
    check("no NaN/undefined text in the roads", not any(t in text for t in BAD_TEXT), text[:80])

    t = d.get("triggers") or {}
    up, dn = t.get("up"), t.get("down")
    if core_ok and _num(up) and _num(dn):
        check("up trigger above spot above down trigger", up > spot > dn, f"{up} > {spot} > {dn}")
    else:
        check("up trigger above spot above down trigger", False, f"up={up!r} down={dn!r}")
    band = t.get("band")
    if band:
        check("middle band is ordered", _num(band.get("lo")) and _num(band.get("hi")) and band["lo"] < band["hi"],
              str(band))

    regime, net = str(d.get("regime", "")).lower(), d.get("netGEX")
    if _num(net):
        want = "positive" if net > 0 else "negative"
        check("regime matches the sign of net GEX", want in regime, f"regime={regime!r} netGEX={net:.3g}")
    else:
        check("regime matches the sign of net GEX", False, f"netGEX={net!r}")

    es = d.get("expiringShare")
    check("expiring share between 0 and 1", es is None or (_num(es) and 0 <= es <= 1), f"{es!r}")

    nxt = d.get("nextSession")
    try:
        wd = datetime.strptime(nxt, "%Y-%m-%d").weekday()
        check("next session is a weekday", wd < 5, f"{nxt}")
    except Exception:  # noqa: BLE001
        check("next session is a weekday", False, f"nextSession={nxt!r}")
    check("calendar is not stale", d.get("calendarStale") is not True)

    for h in (d.get("scoreable") or {}).get("hard", []):
        if not _num(h.get("lvl")):
            check("graded levels are numbers", False, str(h))
            break
    else:
        check("graded levels are numbers", True)

    ok, w, h, size = png_info(png_path)
    check("chart is a PNG", ok, str(png_path))
    check("chart is big enough", ok and w >= MIN_W and h >= MIN_H, f"{w}x{h}")
    check("chart is not blank-small", size >= MIN_PNG_BYTES, f"{size} bytes")
    return out


def main(argv):
    allow_open = "--allow-open" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    d = json.loads(Path(args[0]).read_text())
    res = run_checks(d, args[1], allow_open=allow_open)
    for name, ok, detail in res:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    failed = [n for n, ok, _ in res if not ok]
    if failed:
        print(f"SANITY FAILED: {len(failed)} of {len(res)} checks")
        return 1
    print(f"SANITY OK: {len(res)} checks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
