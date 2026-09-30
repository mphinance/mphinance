#!/usr/bin/env python3
"""Scheduled Substack Notes. Substack has no note-scheduling API, so this is a
local queue plus a systemd timer (substack-note-queue.timer, every 5 min) that
posts whatever is due.

Michael writes the words; this only holds them until the time he picked.

  python3 tools/note_queue.py add "2026-10-01 09:30" "note text"      # ET if no offset
  python3 tools/note_queue.py add "tue 09:30" path/to/note.md --image chart.png
  python3 tools/note_queue.py add "2026-10-01 09:30" "text" --link https://...
  python3 tools/note_queue.py list
  python3 tools/note_queue.py cancel <id>
  python3 tools/note_queue.py flush [--dry-run]                         # what the timer runs

Text supports **bold**, *italic* and [text](url); blank lines split paragraphs.
One note per day did 2.4x the likes of multi-note days (9/30 data), so `add`
warns when a day already has one queued.
"""
import base64
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
QUEUE = REPO / "data/notes_queue"
SENT = QUEUE / "sent"
ET = timezone(timedelta(hours=-4))
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def parse_when(s):
    s = s.strip().lower()
    m = re.fullmatch(r"(mon|tue|wed|thu|fri|sat|sun)\w*\s+(\d{1,2}):(\d{2})", s)
    if m:
        now = datetime.now(ET)
        ahead = (DAYS.index(m.group(1)) - now.weekday()) % 7
        dt = (now + timedelta(days=ahead)).replace(hour=int(m.group(2)), minute=int(m.group(3)),
                                                   second=0, microsecond=0)
        return dt if dt > now else dt + timedelta(days=7)
    dt = datetime.fromisoformat(s.upper().replace(" ", "T", 1))
    return dt if dt.tzinfo else dt.replace(tzinfo=ET)


INLINE = re.compile(r"\*\*(.+?)\*\*|\*([^*\n]+?)\*|\[([^\]]+)\]\(([^)]+)\)")


def inline(text):
    out, pos = [], 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            out.append({"type": "text", "text": text[pos:m.start()]})
        if m.group(1) is not None:
            out.append({"type": "text", "text": m.group(1), "marks": [{"type": "bold"}]})
        elif m.group(2) is not None:
            out.append({"type": "text", "text": m.group(2), "marks": [{"type": "italic"}]})
        else:
            out.append({"type": "text", "text": m.group(3), "marks": [{"type": "link", "attrs": {
                "href": m.group(4), "target": "_blank", "rel": "noopener noreferrer nofollow",
                "class": None}}]})
        pos = m.end()
    if pos < len(text):
        out.append({"type": "text", "text": text[pos:]})
    return out


def body_json(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    return {"type": "doc", "attrs": {"schemaVersion": "v1"},
            "content": [{"type": "paragraph", "content": inline(p.replace("\n", " "))} for p in paras]}


def post(item, dry=False):
    from substack_gateway import Gateway
    g = Gateway()
    att = []
    if item.get("image"):
        mime = "image/jpeg" if item["image"].lower().endswith((".jpg", ".jpeg")) else "image/png"
        b64 = f"data:{mime};base64," + base64.b64encode(Path(item["image"]).read_bytes()).decode()
        if not dry:
            url = g._sub("POST", "image", json={"image": b64})["url"]
            att.append(g._sub("POST", "comment/attachment/", json={"url": url, "type": "image"})["id"])
    elif item.get("link") and not dry:
        att.append(g._sub("POST", "comment/attachment/", json={"url": item["link"], "type": "link"})["id"])
    payload = {"bodyJson": body_json(item["text"]), "tabId": "for-you", "surface": "feed",
               "replyMinimumRole": "everyone"}
    if att:
        payload["attachmentIds"] = att
    if dry:
        print(json.dumps(payload)[:400]); return None
    return g._sub("POST", "comment/feed/", json=payload)


def load():
    QUEUE.mkdir(parents=True, exist_ok=True)
    return sorted((json.loads(p.read_text()) | {"_path": str(p)} for p in QUEUE.glob("*.json")),
                  key=lambda i: i["at"])


def main():
    a = sys.argv[1:]
    flag = lambda k: next((a[i + 1] for i, x in enumerate(a) if x == k and i + 1 < len(a)), None)
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and not (i and a[i - 1] in ("--image", "--link"))]
    cmd = pos[0] if pos else ""
    if cmd == "add" and len(pos) >= 3:
        when = parse_when(pos[1])
        src = Path(pos[2])
        text = src.read_text() if src.suffix in (".md", ".txt") and src.exists() else pos[2]
        img = flag("--image")
        if img:
            img = str(Path(img).resolve())
            if not Path(img).exists():
                sys.exit(f"no such image: {img}")
        nid = when.strftime("%Y%m%d-%H%M") + f"-{int(time.time()) % 10000:04d}"
        same_day = [i for i in load() if i["at"][:10] == when.isoformat()[:10]]
        (QUEUE / f"{nid}.json").write_text(json.dumps({
            "id": nid, "at": when.isoformat(), "text": text.strip(), "image": img,
            "link": flag("--link"), "queued": datetime.now(ET).isoformat()}, indent=1))
        print(f"QUEUED {nid} for {when.strftime('%a %b %d %I:%M %p ET')}")
        if same_day:
            print(f"  heads up: {len(same_day)} other note(s) already queued that day. "
                  "One-note days averaged 10 likes, multi-note days ~4.")
    elif cmd == "list":
        for i in load():
            at = datetime.fromisoformat(i["at"]).astimezone(ET)
            extra = " [img]" if i.get("image") else " [link]" if i.get("link") else ""
            print(f"{i['id']}  {at.strftime('%a %b %d %I:%M %p')}{extra}  {i['text'][:70].replace(chr(10), ' ')}")
    elif cmd == "cancel" and len(pos) >= 2:
        p = QUEUE / f"{pos[1]}.json"
        p.unlink() if p.exists() else sys.exit("not found")
        print(f"CANCELLED {pos[1]}")
    elif cmd == "flush":
        dry = "--dry-run" in a
        now = datetime.now(timezone.utc)
        for i in load():
            if datetime.fromisoformat(i["at"]) > now:
                continue
            path = Path(i.pop("_path"))
            try:
                r = post(i, dry)
            except Exception as e:  # leave it queued; the next tick retries
                print(f"FAILED {i['id']}: {e}"); continue
            if dry:
                continue
            SENT.mkdir(parents=True, exist_ok=True)
            i["posted"], i["note_id"] = now.isoformat(), (r or {}).get("id")
            (SENT / path.name).write_text(json.dumps(i, indent=1)); path.unlink()
            print(f"POSTED {i['id']} -> https://substack.com/@mphinance/note/c-{i['note_id']}")
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
