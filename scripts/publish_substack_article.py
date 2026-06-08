#!/usr/bin/env python3
"""
publish_substack_article.py — Push any repo article to Substack as a draft.

Generalizes scripts/post_institutional_draft.py for any article living under
docs/. Parses the H1 title + the '*Tags:' subtitle line, converts the body
markdown to HTML, and rewrites local image filenames to absolute GitHub Pages
URLs so they resolve inside Substack.

Requires:
  /tmp/vmpl/bin/pip install markdown requests   # or any env with both
  export SUBSTACK_SID="s%3A..."                  # 'substack.sid' cookie value

Usage:
  python3 scripts/publish_substack_article.py docs/articles/<slug>/README.md --dry-run
  python3 scripts/publish_substack_article.py docs/articles/<slug>/README.md

The draft lands in Substack Dashboard -> Drafts. It does NOT auto-publish.
Confirm images, set the paywall break at <!--paywall-->, then publish manually.
"""
import os
import re
import sys

import markdown

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from substack_client import SubstackClient  # noqa: E402

PAGES_ROOT = "https://mphinance.github.io/mphinance/"


def pages_image_base(article_path: str) -> str:
    """Map a docs/ article dir to its GitHub Pages URL base."""
    art_dir = os.path.dirname(os.path.abspath(article_path))
    rel = os.path.relpath(art_dir, os.path.join(REPO, "docs"))
    if rel.startswith(".."):
        raise ValueError("Article must live under docs/ to resolve image URLs.")
    return PAGES_ROOT + rel.replace(os.sep, "/") + "/"


def parse_article(path: str):
    """Return (title, tags, body_md). Title is the H1; tags is the '*Tags:'
    line directly under it; body is everything after that line."""
    lines = open(path, encoding="utf-8").read().split("\n")
    title, tags, body_start = "", "", 0
    for i, line in enumerate(lines):
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue
        if title and not tags and line.strip().startswith("*Tags:"):
            tags = line.strip().strip("*").strip()
            if tags.lower().startswith("tags:"):
                tags = tags[5:].strip()
            body_start = i + 1
            break
    if not title:
        raise ValueError("No H1 title found in article")
    if not tags:
        raise ValueError("No '*Tags:' line found under the title")
    body_md = "\n".join(lines[body_start:]).strip()
    return title, tags, body_md


def md_to_html(body_md: str, img_base: str) -> str:
    """Rewrite bare local image filenames (no scheme, no slash) to GH Pages
    URLs, then render markdown to HTML."""
    body_md = re.sub(
        r"(!\[[^\]]*\]\()(?!https?://|/)([^)]+)(\))",
        lambda m: m.group(1) + img_base + m.group(2) + m.group(3),
        body_md,
    )
    return markdown.markdown(body_md, extensions=["extra"])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    article = args[0]
    dry = "--dry-run" in sys.argv

    title, tags, body_md = parse_article(article)
    img_base = pages_image_base(article)
    body_html = md_to_html(body_md, img_base)

    print(f"TITLE:    {title}")
    print(f"SUBTITLE: {tags}")
    print(f"IMG BASE: {img_base}")
    print(f"BODY:     {len(body_html)} chars of HTML, "
          f"{body_html.count('<img')} image(s)")

    if dry:
        out = os.path.splitext(article)[0] + "_substack_preview.html"
        open(out, "w", encoding="utf-8").write(body_html)
        print(f"DRY RUN -- HTML written to {out}, no API call made.")
        return

    client = SubstackClient()
    draft_id = client.create_draft(title, subtitle=tags, body_html=body_html)
    print(f"Draft created: https://mphinance.substack.com/publish/post/{draft_id}")
    print("Open it, set the paywall break at <!--paywall-->, confirm images, publish.")


if __name__ == "__main__":
    main()
