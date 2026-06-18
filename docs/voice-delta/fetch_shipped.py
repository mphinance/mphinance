#!/usr/bin/env python3
"""Fetch the SHIPPED version of an mphinance Substack post as clean text.

The voice-delta corpus pairs a machine-GIVEN draft (from the repo / local cache)
against the version Michael actually SHIPPED. His in-editor edits never come back
to the repo, so the live post is the only record of the final form. This grabs it.

Usage:
    python3 fetch_shipped.py <slug> [<slug> ...]
    python3 fetch_shipped.py --list           # recent posts: date | title | slug

Notes:
- Public endpoint, no auth. For only_paid posts you get the free portion (up to
  the paywall), which is still a usable delta on everything above the wall.
- Find slugs with --list, or from the cache dir names (<date>_<slug>).
"""
import json, re, html, sys, urllib.request

BASE = "https://mphinance.substack.com"
UA = {"User-Agent": "Mozilla/5.0 (voice-delta fetcher)"}


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def strip_html(h):
    h = h or ""
    h = re.sub(r"(?is)<(script|style).*?</\1>", "", h)
    h = re.sub(r"(?i)<br\s*/?>", "\n", h)
    h = re.sub(r"(?i)</p>", "\n\n", h)
    h = re.sub(r"(?i)<h[1-6][^>]*>", "\n## ", h)
    h = re.sub(r"(?i)</h[1-6]>", "\n", h)
    h = re.sub(r"(?i)<li[^>]*>", "\n- ", h)
    h = re.sub(r"(?i)<figcaption[^>]*>", "\n[caption] ", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    return re.sub(r"\n{3,}", "\n\n", h).strip()


def list_recent(limit=50):
    data = json.loads(_get(f"{BASE}/api/v1/archive?sort=new&limit={limit}&offset=0"))
    for p in data:
        print(f"{(p.get('post_date') or '')[:10]} | {p.get('title','')[:60]:60} | {p.get('slug','')}")


def fetch(slug):
    d = json.loads(_get(f"{BASE}/api/v1/posts/{slug}"))
    if isinstance(d, dict) and d.get("errors"):
        raise SystemExit(f"error for {slug}: {d['errors']}")
    body = strip_html(d.get("body_html", ""))
    return (f"TITLE: {d.get('title')}\n"
            f"SUBTITLE: {d.get('subtitle')}\n"
            f"AUDIENCE: {d.get('audience')}\n\n{body}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
    elif args[0] == "--list":
        list_recent()
    else:
        for slug in args:
            sys.stdout.write(fetch(slug))
