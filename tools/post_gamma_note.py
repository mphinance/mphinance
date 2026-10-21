#!/usr/bin/env python3
"""Post the nightly Tomorrow's Map as a Substack Note.

Reads the JSON sidecar written by tools/gamma_tomorrow.mjs, uploads the PNG to
Substack, and publishes a note with the chart attached.

  python3 tools/post_gamma_note.py /tmp/gamma/spy_tomorrow_2026-09-26.json [--dry-run] [--force]

The note is deliberately machine-generated: levels and the if/else, nothing
written in Michael's voice. The chart is the post; the words are a caption.

Guards, because this runs unattended:
  - refuses a book that was measured mid-session (sessionClosed false)
  - refuses a sidecar older than 20 hours
  - one note per calendar day, tracked in data/gamma_maps/.note_state.json

Changelog: any entry in data/gamma_maps/CHANGELOG.json with "posted": null is
appended to the next note under "What changed", then stamped with the date it
went out, so each change is announced exactly once. Whenever the map or its
grading changes, add an entry there: one or two plain sentences a reader who
has never seen the code would follow, saying what changed and why.

Auth: SUBSTACK_SID in secrets.env, same cookie the rest of the pipeline uses.
"""
import argparse
import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "data/gamma_maps/.note_state.json"
CHANGELOG = REPO / "data/gamma_maps/CHANGELOG.json"
# Was a fixed UTC-4, which is EDT only: every winter the once-a-day guard would
# roll over at 8pm ET instead of midnight.
ET = ZoneInfo("America/New_York")


def secrets():
    out = {}
    for line in (REPO / "secrets.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k] = v.strip().strip('"')
    return out


def session():
    s = requests.Session()
    sec = secrets()
    s.cookies.set("substack.sid", sec.get("SUBSTACK_SID", ""), domain=".substack.com")
    s.headers.update({"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return s, sec.get("SUBSTACK_PUB_URL", "mphinance.substack.com")


def pending_changes():
    if not CHANGELOG.exists():
        return []
    return [c for c in json.loads(CHANGELOG.read_text()) if not c.get("posted")]


def _day(iso):
    """2026-09-23 -> Sep 23."""
    dt = datetime.strptime(iso, "%Y-%m-%d")
    return f"{dt:%b} {dt.day}"


def last_call_line(d):
    """How the previous map actually did, in plain words.

    The chart has carried a LAST CALL row for weeks but the note never did, so a
    reader on Substack saw tomorrow's claim and never the last one being scored.
    Dated rather than "last night": on a Sunday run the graded session is Friday.
    Grades are on the close, which is why a wick through a level is reported here
    as a hold and not a miss.
    """
    lc = d.get("lastCall") or {}
    if not lc.get("day") or not lc.get("summary"):
        return None
    total = lc.get("total") or 0
    if total:
        head = (
            f"The last map, graded on the {_day(lc['day'])} close: {lc.get('hits', 0)} of "
            f"{total} level{'' if total == 1 else 's'} price actually reached closed on "
            f"the right side."
        )
    else:
        # A level price never approached is not a hit or a miss, and scoring it
        # either way is how a quiet session flatters a map.
        head = (
            f"The last map, graded on the {_day(lc['day'])} close: price came nowhere "
            f"near the levels it named, so there was nothing to score."
        )
    detail = "; ".join(p.strip() for p in lc["summary"].split("·") if p.strip())
    if not detail:
        return head
    return f"{head} {detail[0].upper()}{detail[1:]}."


def compose(d, changes=()):
    """The caption. Short, factual, no voice."""
    sym = d["symbol"]
    lines = [f"{sym} next session, from the book as it settled."]

    # An accuracy number is a claim, and a claim needs a sample. Until the ledger
    # has enough graded sessions this says how many days are on the clock and
    # nothing about how well it has done.
    rec = d.get("record") or {}
    # Always say how long the map has run and when the record restarted. Counting
    # only from the restart ("1 session graded") made a two-week-old map look new.
    history = ""
    if rec.get("firstMap") and rec.get("restartedOn"):
        old = (rec.get("inSample") or {}).get("sessions", 0)
        history = (
            f"This map has posted nightly since {_day(rec['firstMap'])}. The grading rules "
            f"were fixed on {_day(rec['restartedOn'])}, so the record restarted then"
            + (f" ({old} earlier sessions are kept as history, not counted)" if old else "")
            + ". "
        )
    if rec.get("publishable"):
        # Never a rate without its baseline: the same number of plain $5 round
        # numbers, scored the same way on the same days. On SPY the gamma brakes
        # are often round strikes, so the gap between the two IS the claim.
        lines.append(
            history
            + f"Since the restart: {rec['hits']}/{rec['total']} tested levels closed on the "
            f"right side across {rec['sessions']} sessions. Plain $5 round numbers, "
            f"same days, same rule: {rec.get('nullHits', 0)}/{rec.get('nullTotal', 0)}."
        )
    elif rec.get("sessions"):
        need = rec.get("minSessions", 10)
        lines.append(
            history
            + f"{rec['sessions']} of {need} sessions graded under the current rules. "
            f"No hit rate until there are {need}."
        )

    # The last session's grade goes before tomorrow's roads: the record is the
    # reason to read the forecast, so it should not be buried under it.
    graded = last_call_line(d)
    if graded:
        lines.append(graded)

    for b in d["branches"]:
        lines.append(f"{b['kind']} {b['cond']} -> {b['rule']}")

    # The three roads are exhaustive but not comparable: when an IF trigger sits
    # a rounding error from the close, that road has already fired at the bell.
    # Saying so beats letting the reader assume the ELSE is the default branch.
    if d.get("triggerNote"):
        lines.append(f"Read the roads with this: {d['triggerNote']}")

    lines.append(
        f"Flip {d['flip']:.2f}. Pin {d['pin']}. "
        f"A typical day from here is about {d['expected']:.2f} points."
    )
    if (d.get("expiringShare") or 0) >= 0.005:
        # Runs at 21:00 ET, so "expires tonight" is already past tense, and on a
        # Sunday run nothing expired that night at all.
        lines.append(
            f"Levels exclude the {d['expiringShare'] * 100:.0f}% of gamma that does not "
            f"survive into the next session."
        )
    if changes:
        # One paragraph per item: the note body is paragraphs split on blank
        # lines, and a bare newline inside a paragraph does not render.
        lines.append("What changed in the map:")
        lines.extend(f"- {c['text']}" for c in changes)
    lines.append("Where dealers are long gamma they brake, where they are short they chase. Not advice.")
    return "\n\n".join(lines)


def body_json(text):
    return {
        "type": "doc",
        "attrs": {"schemaVersion": "v1"},
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": para}]}
            for para in text.split("\n\n")
        ],
    }


def upload_png(s, path):
    b64 = "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode()
    r = s.post("https://substack.com/api/v1/image", json={"image": b64}, timeout=90)
    r.raise_for_status()
    return r.json()["url"]


def attach_image(s, pub, url):
    r = s.post(f"https://{pub}/api/v1/comment/attachment/",
               json={"url": url, "type": "image"}, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def publish(s, pub, text, attachment_ids):
    payload = {
        "bodyJson": body_json(text),
        "tabId": "for-you",
        "surface": "feed",
        "replyMinimumRole": "everyone",
    }
    if attachment_ids:
        payload["attachmentIds"] = attachment_ids
    r = s.post(f"https://{pub}/api/v1/comment/feed/", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sidecar")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="ignore the once-a-day guard")
    a = ap.parse_args()

    d = json.loads(Path(a.sidecar).read_text())

    if not d.get("sessionClosed") and not a.force:
        sys.exit("refusing: this book was measured mid-session, so it is not a map of tomorrow")

    age = datetime.now(timezone.utc) - datetime.fromisoformat(d["asOf"].replace("Z", "+00:00"))
    if age > timedelta(hours=20) and not a.force:
        sys.exit(f"refusing: sidecar is {age.total_seconds() / 3600:.1f}h old, regenerate it first")

    today = datetime.now(ET).strftime("%Y-%m-%d")
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if state.get("lastPosted") == today and not a.force:
        sys.exit(f"already posted a note today ({today}); use --force to override")

    changes = pending_changes()
    text = compose(d, changes)
    print("─" * 70)
    print(text)
    print("─" * 70)
    print(f"chart: {d['png']}")

    if a.dry_run:
        print("\n[dry run] nothing posted")
        return

    s, pub = session()
    img = upload_png(s, d["png"])
    print(f"uploaded: {img}")
    att = attach_image(s, pub, img)
    print(f"attachment: {att}")
    res = publish(s, pub, text, [att])
    nid = res.get("id") or (res.get("comment") or {}).get("id")
    print(f"posted note {nid}")

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"lastPosted": today, "noteId": nid}, indent=2) + "\n")

    if changes:
        log = json.loads(CHANGELOG.read_text())
        for c in log:
            if not c.get("posted"):
                c["posted"] = today
                c["noteId"] = nid
        CHANGELOG.write_text(json.dumps(log, indent=2) + "\n")
        print(f"changelog: announced {len(changes)} change(s)")


if __name__ == "__main__":
    main()
