#!/usr/bin/env python3
"""Color (and optionally bold / highlight) phrases inside an EXISTING Substack draft,
in place, without touching anything else Michael edited by hand.

push_substack.py only creates new drafts from markdown. Once Michael has edited a
draft in the browser, re-pushing would throw his edits away. This patches the live
draft body instead: back it up, add textStyle color marks to exact phrases, PUT it.

  python3 tools/substack_draft_color.py <draft_id> "phrase=gold" "other phrase=#FF5D6C!" ...

  color   a PALETTE name from push_substack.py (gold, red, green, blue, pink, muted,
          brewers, packers) or any hex/rgb
  !       suffix = also bold         ~ suffix = highlighter instead of text color
  --dry-run  show what would change, no PUT

Each phrase is matched once (first occurrence) and must sit inside a single text run;
a phrase that spans bold/plain boundaries is reported as not found, so recolor a
smaller piece. Before running: Michael must CLOSE the draft tab, or the editor's
autosave will revert this write (feedback_substack_draft_editor_conflict).
Backups land in /tmp/substack_draft_<id>_<time>.json.
"""
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
from substack_dossier import SubstackClient  # noqa: E402
from push_substack import PALETTE  # noqa: E402


def text_of(n):
    return "".join(text_of(c) for c in n.get("content", [])) if "content" in n else n.get("text", "")


def mark_phrase(node, phrase, mark, bold):
    """Depth-first: split the first text run containing `phrase` and mark that slice."""
    content = node.get("content")
    if not content:
        return False
    for idx, ch in enumerate(content):
        if ch.get("type") == "text" and phrase in ch.get("text", ""):
            t = ch["text"]; i = t.index(phrase)
            base = [m for m in ch.get("marks", []) if m["type"] != mark["type"]]
            mid_marks = base + [mark]
            if bold and not any(m["type"] in ("strong", "bold") for m in base):
                mid_marks.append({"type": "strong"})
            parts = []
            if t[:i]:
                parts.append({**ch, "text": t[:i]})
            parts.append({"type": "text", "text": phrase, "marks": mid_marks})
            if t[i + len(phrase):]:
                parts.append({**ch, "text": t[i + len(phrase):]})
            node["content"] = content[:idx] + parts + content[idx + 1:]
            return True
        if mark_phrase(ch, phrase, mark, bold):
            return True
    return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) < 2:
        print(__doc__); sys.exit(1)
    draft_id, specs = args[0], args[1:]
    c = SubstackClient()
    if not c.authenticate():
        print("AUTH FAILED: check SUBSTACK_SID in secrets.env"); sys.exit(2)
    url = f"https://{c.pub}/api/v1/drafts/{draft_id}"
    d = c.session.get(url).json()
    backup = f"/tmp/substack_draft_{draft_id}_{time.strftime('%H%M%S')}.json"
    json.dump(d, open(backup, "w"))
    print(f"backup: {backup}  (title: {d.get('draft_title')})")
    body = json.loads(d["draft_body"])
    ok = 0
    for spec in specs:
        phrase, _, col = spec.rpartition("=")
        bold, hl = col.endswith("!"), col.endswith("~")
        col = col.rstrip("!~").strip()
        hexc = PALETTE.get(col.lower(), col)
        mark = ({"type": "highlight", "attrs": {"color": hexc}} if hl
                else {"type": "textStyle", "attrs": {"color": hexc}})
        if mark_phrase(body, phrase, mark, bold):
            ok += 1; print(f"  ok        {phrase!r} -> {hexc}{' bold' if bold else ''}{' highlight' if hl else ''}")
        else:
            print(f"  NOT FOUND {phrase!r} (check spelling, or it spans two formatting runs)")
    if dry or not ok:
        print("dry run, nothing written" if dry else "nothing matched, nothing written"); return
    r = c.session.put(url, json={"draft_body": json.dumps(body)})
    print(f"PUT {r.status_code}. Reopen the draft from the dashboard (not an old tab).")


if __name__ == "__main__":
    main()
