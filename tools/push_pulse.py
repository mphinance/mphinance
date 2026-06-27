#!/usr/bin/env python3
"""Cross-post a workspace post.md to pxlse.io — the counterpart to push_substack.py.

Same post.md format the Substack pusher reads:
  # Title              -> title
  *italic dek*         -> subtitle (first italic line after the title)
  ![hero](hero.png)    -> first image becomes the cover; images are uploaded to pxlse
  ...markdown body...  -> content (pxlse renders markdown; $TICKERS auto-link)

SAFETY: pxlse has no draft state — a post goes live the instant it's created. So this
script previews by default and only publishes when you pass --post.

  python3 tools/push_pulse.py <workspace>/post.md                  # dry-run preview
  python3 tools/push_pulse.py <workspace>/post.md --post           # publish live
  python3 tools/push_pulse.py <workspace>/post.md --post --visibility followers
  python3 tools/push_pulse.py <workspace>/post.md --post --tag setups --tag options
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pulse_client import PulseClient  # noqa: E402

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def parse_post(md_path):
    """Return (title, subtitle, body_lines, image_refs). Strips the H1 title and the
    first italic dek out of the body; leaves everything else as markdown."""
    lines = open(md_path, encoding="utf-8").read().split("\n")
    title, subtitle, body = "", "", []
    for ln in lines:
        s = ln.strip()
        if not title and s.startswith("# "):
            title = s[2:].strip(); continue
        if title and not subtitle and s.startswith("*") and s.endswith("*") and len(s) > 2 and "**" not in s:
            subtitle = s.strip("*").strip(); continue
        body.append(ln)
    return title, subtitle, body


def process_images(client, md_path, body, dry):
    """Upload every local image referenced in the body, rewrite its markdown to the
    pxlse URL, and return (rewritten_text, cover_url). Remote http(s) images are left
    as-is (and can still serve as the cover)."""
    cover = None
    base_dir = os.path.dirname(os.path.abspath(md_path))
    text = "\n".join(body)

    def repl(m):
        nonlocal cover
        alt, src = m.group(1), m.group(2).strip()
        url = src
        if not src.startswith(("http://", "https://")):
            path = src if os.path.isabs(src) else os.path.join(base_dir, src)
            if dry:
                url = f"<upload:{os.path.basename(path)}>"
            else:
                up = client.upload_media(path)
                url = up["url"] if up else src
        if cover is None and url.startswith(("http://", "https://")):
            cover = url
        return f"![{alt}]({url})"

    text = IMG_RE.sub(repl, text)
    # Collapse 3+ blank lines and trim.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, cover


def main():
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    md_path = args[0]
    live = "--post" in flags
    visibility = "followers" if "--visibility" in sys.argv and \
        sys.argv[sys.argv.index("--visibility") + 1] == "followers" else "public"
    tags = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--tag"]

    client = PulseClient()
    title, subtitle, body = parse_post(md_path)
    content, cover = process_images(client, md_path, body, dry=not live)

    print(f"TITLE:      {title}")
    print(f"SUBTITLE:   {subtitle}")
    print(f"VISIBILITY: {visibility}")
    print(f"TAGS:       {tags or '(none)'}")
    print(f"COVER:      {cover or '(none)'}")
    print(f"CONTENT:    {len(content)} chars")
    if not live:
        print("\n--- CONTENT PREVIEW (first 600 chars) ---")
        print(content[:600])
        print("\nDRY RUN — pass --post to publish live to pxlse.")
        return
    res = client.create_post(title, content, subtitle=subtitle, tags=tags,
                             cover_image_url=cover, visibility=visibility)
    print(f"\nLIVE: {client.post_url(res['id'])}  (id={res['id']}, status={res.get('status')})")


if __name__ == "__main__":
    main()
