#!/usr/bin/env python3
"""Backfill Substack SEO fields (search_engine_title / search_engine_description)
on published posts that have none. Michael's subtitles are category-mix lines
("Trading 60% | Mindset 40%"), which is what Google shows when the SEO
description is empty, so every post was leaking a useless snippet.

  python3 tools/substack_seo_backfill.py fetch      # cache post text -> data/seo/posts.json
  python3 tools/substack_seo_backfill.py write      # claude -p writes SEO -> data/seo/seo.json
  python3 tools/substack_seo_backfill.py apply [--limit N]   # PUT fields, verify, log
  python3 tools/substack_seo_backfill.py all

Substack 429s fast, so every call backs off. apply only touches the two SEO
fields, skips posts that already have them, and logs before/after to
data/seo/applied.jsonl.
"""
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
from substack_dossier import SubstackClient  # noqa: E402

OUT = os.path.join(REPO, "data", "seo")
POSTS, SEO, LOG = (os.path.join(OUT, f) for f in ("posts.json", "seo.json", "applied.jsonl"))
BATCH = 15


def call(c, method, url, **kw):
    for k in range(8):
        r = c.session.request(method, url, timeout=60, **kw)
        if r.status_code != 429 and r.status_code < 500:
            return r
        time.sleep(min(20 * (k + 1), 120))
    return r


def text_of(n):
    return " ".join(text_of(x) for x in n.get("content", [])) if "content" in n else n.get("text", "")


def fetch(c):
    have = {p["id"]: p for p in json.load(open(POSTS))} if os.path.exists(POSTS) else {}
    allp, off = [], 0
    while True:
        j = call(c, "GET", f"https://{c.pub}/api/v1/post_management/published?offset={off}"
                 f"&limit=50&order_by=post_date&order_direction=desc").json()
        ps = j.get("posts", [])
        allp += ps
        if len(ps) < 50:
            break
        off += 50
        time.sleep(2)
    for i, p in enumerate(allp):
        if p["id"] in have:
            continue
        d = call(c, "GET", f"https://{c.pub}/api/v1/drafts/{p['id']}").json()
        try:
            txt = re.sub(r"\s+", " ", text_of(json.loads(d.get("draft_body") or "{}")))[:1500]
        except Exception:
            txt = ""
        have[p["id"]] = dict(id=p["id"], date=(p.get("post_date") or "")[:10], slug=p["slug"],
                             title=d.get("title"), subtitle=d.get("subtitle"),
                             seo_title=d.get("search_engine_title"),
                             seo_desc=d.get("search_engine_description"), text=txt)
        if i % 10 == 0:
            json.dump(list(have.values()), open(POSTS, "w"))
            print(f"fetched {i + 1}/{len(allp)}", flush=True)
        time.sleep(1.5)
    json.dump(list(have.values()), open(POSTS, "w"))
    print(f"fetch done: {len(have)} posts", flush=True)


PROMPT = """You write Substack SEO metadata for Michael's finance newsletter (mphinance: options, the wheel strategy, trading tools, AI for traders, and personal essays).

For EACH post below return search_engine_title and search_engine_description.

Rules:
- seo_title: max 60 characters. Lead with the concrete subject a person would search (ticker, strategy, tool, place). Plain words. No clickbait, no emojis, no "Ultimate"/"Unlock"/"Guide to".
- seo_desc: 120 to 155 characters. Say what the reader gets, specific (tickers, numbers, the actual idea). First person is fine if the post is personal. No hype, no em dashes or en dashes, no "dive into", "delve", "game-changer", "in this post". Never invent numbers that are not in the excerpt.
- Never use Michael's last name.

Return ONLY a JSON array: [{"id": <id>, "seo_title": "...", "seo_desc": "..."}]

POSTS:
"""


def write():
    posts = [p for p in json.load(open(POSTS)) if not p.get("seo_desc")]
    done = {s["id"]: s for s in json.load(open(SEO))} if os.path.exists(SEO) else {}
    todo = [p for p in posts if p["id"] not in done]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        body = "\n\n".join(f"### id={p['id']} | title: {p['title']} | subtitle: {p['subtitle']}\n{p['text'][:1200]}"
                           for p in chunk)
        for attempt in range(3):
            r = subprocess.run([os.path.expanduser("~/.local/bin/claude"), "-p", "--model", "claude-sonnet-5-5", PROMPT + body],
                               capture_output=True, text=True, env=env, timeout=600)
            m = re.search(r"\[.*\]", r.stdout, re.S)
            try:
                for s in json.loads(m.group(0)):
                    s["seo_title"] = s["seo_title"].replace("—", ",").replace("–", "-")[:70]
                    s["seo_desc"] = s["seo_desc"].replace("—", ",").replace("–", "-")[:170]
                    done[int(s["id"])] = s
                break
            except Exception as e:
                print(f"batch {i} attempt {attempt} parse fail: {e} {r.stderr[:200]}", flush=True)
        json.dump(list(done.values()), open(SEO, "w"), indent=1)
        print(f"seo written {len(done)}/{len(posts)}", flush=True)


def apply(c, limit=None):
    seo = json.load(open(SEO))
    applied = set()
    if os.path.exists(LOG):
        applied = {json.loads(l)["id"] for l in open(LOG) if l.strip()}
    n = 0
    for s in seo:
        if s["id"] in applied:
            continue
        url = f"https://{c.pub}/api/v1/drafts/{s['id']}"
        before = call(c, "GET", url).json()
        if before.get("search_engine_description"):
            continue
        r = call(c, "PUT", url, json={"search_engine_title": s["seo_title"],
                                      "search_engine_description": s["seo_desc"]})
        after = call(c, "GET", url).json()
        ok = after.get("search_engine_description") == s["seo_desc"]
        with open(LOG, "a") as f:
            f.write(json.dumps(dict(id=s["id"], status=r.status_code, ok=ok, title=after.get("title"),
                                    before=[before.get("search_engine_title"), before.get("search_engine_description")],
                                    after=[s["seo_title"], s["seo_desc"]])) + "\n")
        print(f"{'OK ' if ok else 'BAD'} {s['id']} {s['seo_title']}", flush=True)
        if not ok and n == 0:
            print("first write did not stick, aborting", flush=True)
            return
        n += 1
        if limit and n >= limit:
            break
        time.sleep(2)
    print(f"apply done: {n} updated", flush=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    lim = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--limit=")), None)
    c = SubstackClient()
    if cmd in ("fetch", "apply", "all") and not c.authenticate():
        sys.exit("auth failed")
    if cmd in ("fetch", "all"):
        fetch(c)
    if cmd in ("write", "all"):
        write()
    if cmd in ("apply", "all"):
        apply(c, lim)
