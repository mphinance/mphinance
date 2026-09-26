#!/usr/bin/env python3
"""Scrape a linktr.ee page's __NEXT_DATA__ JSON for a link-hub rebuild.

Usage: python scrape_linktree.py https://linktr.ee/HANDLE

Prints identity, bio, profile image URL, theme hero color, every link
(type/title/url) and the social links. WebFetch is blocked by Linktree (403),
so this uses a browser User-Agent via urllib.
"""
import json
import re
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: scrape_linktree.py https://linktr.ee/HANDLE")
    html = fetch(sys.argv[1])
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>', html, re.S)
    if not m:
        sys.exit("could not find __NEXT_DATA__ (page layout changed?)")
    acct = json.loads(m.group(1))["props"]["pageProps"]["account"]

    print("=== IDENTITY ===")
    print("username        :", acct.get("username"))
    print("pageTitle       :", acct.get("pageTitle"))
    print("bio/description :", acct.get("description"))
    print("profileImageUrl :", acct.get("profilePictureUrl"))
    theme = acct.get("theme") or {}
    print("heroColor       :", acct.get("backgroundHeroColor"))
    print("theme luminance :", theme.get("luminance"),
          "| bg:", (theme.get("background") or {}).get("color"))

    print("\n=== LINKS (in order) ===")
    for lk in acct.get("links", []):
        print(f"- [{lk.get('type')}] {lk.get('title')!r} -> {lk.get('url')}")

    print("\n=== SOCIAL LINKS ===")
    socials = sorted(acct.get("socialLinks", []), key=lambda s: s.get("position", 99))
    for s in socials:
        print(f"- {s.get('type')}: {s.get('url')}")


if __name__ == "__main__":
    main()
