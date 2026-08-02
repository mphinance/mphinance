#!/usr/bin/env python3
"""Watch (and archive) an AfterHour author's post feed.

The AfterHour social feed is a public, unauthenticated endpoint:
    https://api.afterhour.com/social/feed?take=100&contentTypes=post&authorId=prf_...
`take` caps at 100 server-side; paginate with the `cursor` returned in the body.

Usage:
    python3 tools/afterhour_watch.py              # mph, incremental, prints new posts
    python3 tools/afterhour_watch.py --full       # re-pull the entire history
    python3 tools/afterhour_watch.py --author prf_xxx --label someone
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.afterhour.com/social/feed"
UA = "Mozilla/5.0 (compatible; mphinance-archive/1.0)"
MPH = "prf_1d3e45fbdb93461eb593f842fccdc990"
ARCHIVE = Path(__file__).resolve().parent.parent / "data" / "afterhour"


def fetch(author_id, cursor=None, take=50, tries=5):
    """One page. The API 504s intermittently on deep pages, so retry with backoff."""
    params = {"take": take, "contentTypes": "post", "authorId": author_id}
    if cursor is not None:
        params["cursor"] = cursor
    req = urllib.request.Request(
        f"{API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": UA}
    )
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == tries - 1:
                raise
        except urllib.error.URLError:
            if attempt == tries - 1:
                raise
        time.sleep(2 ** attempt * 3)


def slim(item):
    post = item.get("post") or {}
    return {
        "id": item.get("id"),
        "createdAt": item.get("createdAt"),
        "body": post.get("body") or "",
        "viewCount": post.get("viewCount"),
        "reactions": sum((item.get("reactionCounts") or {}).values()),
        "comments": item.get("commentCount"),
        "tickers": [s.get("symbol") for s in item.get("securities") or []],
        "media": [m.get("url") for m in item.get("mediaAttachments") or []],
    }


def crawl(author_id, stop_at=None, max_pages=200):
    """Walk the feed newest-first. Stops early once `stop_at` post id is seen."""
    out, cursor, seen_stop = [], None, False
    for _ in range(max_pages):
        data = fetch(author_id, cursor)
        items = data.get("items") or []
        if not items:
            break
        for it in items:
            if stop_at and it.get("id") == stop_at:
                seen_stop = True
                break
            out.append(slim(it))
        if seen_stop:
            break
        cursor = data.get("cursor")
        if cursor is None:
            break
        time.sleep(0.3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default=MPH)
    ap.add_argument("--label", default="mphinance")
    ap.add_argument("--full", action="store_true", help="re-pull entire history")
    args = ap.parse_args()

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    path = ARCHIVE / f"{args.label}.json"
    known = []
    if path.exists() and not args.full:
        known = json.loads(path.read_text())

    newest_known = known[0]["id"] if known else None
    fresh = crawl(args.author, stop_at=newest_known)

    merged = fresh + known
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))

    if not fresh:
        print(f"no new posts for {args.label} ({len(merged)} archived)")
        return
    print(f"{len(fresh)} new post(s) for {args.label} ({len(merged)} archived)\n")
    for p in fresh:
        body = p["body"].strip().replace("\n", " ")
        print(f"[{p['createdAt']}] {p['viewCount']} views / {p['reactions']} reax / "
              f"{p['comments']} comments")
        print(f"  {body[:400]}{'...' if len(body) > 400 else ''}\n")


if __name__ == "__main__":
    main()
