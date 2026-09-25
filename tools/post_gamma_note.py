#!/usr/bin/env python3
"""Post the morning Tomorrow's Map as a Substack Note.

Reads the JSON sidecar written by tools/gamma_tomorrow.mjs, uploads the PNG to
Substack, and publishes a note with the chart attached.

  python3 tools/post_gamma_note.py /tmp/gamma/spy_tomorrow_2026-09-26.json [--dry-run] [--force]

The note is deliberately machine-generated: levels and the if/else, nothing
written in Michael's voice. The chart is the post; the words are a caption.

Guards, because this runs unattended:
  - refuses a book that was measured mid-session (sessionClosed false)
  - refuses a sidecar older than 20 hours
  - one note per calendar day, tracked in data/gamma_maps/.note_state.json

Auth: SUBSTACK_SID in secrets.env, same cookie the rest of the pipeline uses.
"""
import argparse
import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "data/gamma_maps/.note_state.json"
ET = timezone(timedelta(hours=-4))


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


def compose(d):
    """The caption. Short, factual, no voice."""
    sym = d["symbol"]
    lines = [f"{sym} tomorrow, from tonight's options book."]

    lc = d.get("lastCall")
    if lc:
        part = f"Last map: {lc['hits']}/{lc['total']} on the levels price actually tested ({lc['day'][5:]})"
        if lc.get("untested"):
            part += f", {lc['untested']} never came into play"
        lines.append(part + ".")

    for b in d["branches"]:
        lines.append(f"{b['kind']} {b['cond']} -> {b['rule']}")

    lines.append(
        f"Flip {d['flip']:.2f}. Pin {d['pin']}. "
        f"A typical day from here is about {d['expected']:.2f} points."
    )
    if d.get("expiringShare"):
        lines.append(
            f"Levels exclude the {d['expiringShare'] * 100:.0f}% of gamma that expires tonight."
        )
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

    text = compose(d)
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


if __name__ == "__main__":
    main()
