#!/usr/bin/env python3
"""Backfill recent Substack posts into pxlse.io from a Substack export .zip.

Reads posts.csv (the export index) for titles/subtitles/dates/audience, converts each
post's exported HTML body to markdown, re-hosts its images on pxlse, appends a
canonical link back to the Substack original, and cross-posts the N most recent.

SAFETY: pxlse publishes immediately. Default is a dry run that writes preview markdown
to the scratchpad and posts nothing. Pass --post to actually publish.

  python3 tools/backfill_pulse.py 0622.zip --limit 15                 # preview 15
  python3 tools/backfill_pulse.py 0622.zip --limit 15 --post          # publish 15
  python3 tools/backfill_pulse.py 0622.zip --limit 15 --post --free-only

Notes:
  - --free-only skips audience=only_paid posts.
  - Posts are published oldest->newest of the selected window so the pxlse feed ends up
    in the same chronological order as Substack.
"""
import csv
import io
import os
import re
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pulse_client import PulseClient  # noqa: E402
from substack_md import html_to_markdown as _html_to_md, rehost_images as _rehost  # noqa: E402

PUB_URL = "https://mphinance.substack.com"
SCRATCH = "/tmp/claude-1000/-home-mph-mphinance/7c495568-7351-408b-a0fe-e8086a077785/scratchpad/pulse_preview"

# HTML -> markdown + image re-hosting both live in substack_md (shared with the live
# mirror). Imported above as _html_to_md / _rehost.


# ── Backfill driver ─────────────────────────────────────────────────────────────
def load_index(z):
    rows = list(csv.DictReader(io.StringIO(z.read("posts.csv").decode("utf-8", "replace"))))
    pub = [r for r in rows if r.get("is_published") == "true"]
    pub.sort(key=lambda r: r["post_date"], reverse=True)
    return pub


def body_name(z, post_id):
    stem = post_id.split(".")[0]
    for n in z.namelist():
        if n.startswith(f"posts/{stem}") and n.endswith(".html"):
            return n
    return None


def slug_of(post_id):
    # "202525640.the-whole-market-in-my-pocket" -> "the-whole-market-in-my-pocket"
    return post_id.split(".", 1)[1] if "." in post_id else post_id


def main():
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    zip_path = args[0]
    live = "--post" in flags
    free_only = "--free-only" in flags
    limit = 15
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    z = zipfile.ZipFile(zip_path)
    pub = load_index(z)
    if free_only:
        pub = [r for r in pub if r["audience"] == "everyone"]
    window = pub[:limit]
    # Publish oldest-first so the pxlse feed mirrors Substack chronology.
    window = list(reversed(window))

    os.makedirs(SCRATCH, exist_ok=True)
    client = None
    if live:
        client = PulseClient()
        me = client.me()
        print(f"pxlse: @{me.get('username')}  plan={me.get('plan_status')}  "
              f"limit={me.get('rate_limit_per_minute')}/min\n")
    else:
        # Need a client instance for nothing in dry-run; skip network.
        print(f"DRY RUN — previews -> {SCRATCH}\n")

    print(f"{'PUBLISH' if live else 'PREVIEW'} {len(window)} posts "
          f"({'free only' if free_only else 'incl. paid'})\n")

    results = []
    for n, r in enumerate(window, 1):
        pid = r["post_id"]
        title = r["title"].strip()
        subtitle = (r["subtitle"] or "").strip()
        audience = r["audience"]
        bn = body_name(z, pid)
        if not bn:
            print(f"[{n}/{len(window)}] SKIP {title[:50]} — no HTML body"); continue
        html = z.read(bn).decode("utf-8", "replace")
        md, images = _html_to_md(html)
        # Re-host images, swap placeholders.
        hosted = _rehost(client, images, dry=not live) if images else []
        for i, url in enumerate(hosted):
            md = md.replace(f"{{{{IMG:{i}}}}}", url)
        cover = next((u for u in hosted if u.startswith("http")), None)
        # Canonical footer back to Substack.
        canon = f"{PUB_URL}/p/{slug_of(pid)}"
        md += f"\n\n---\n\n*Originally published on [Momentum Phinance]({canon}).*"
        visibility = "public"

        print(f"[{n}/{len(window)}] {r['post_date'][:10]} {audience:9} {title[:48]}")
        print(f"     images={len(images)} chars={len(md)} cover={'yes' if cover else 'no'}")

        if not live:
            preview = os.path.join(SCRATCH, f"{r['post_date'][:10]}_{slug_of(pid)[:40]}.md")
            with open(preview, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n")
                if subtitle:
                    f.write(f"*{subtitle}*\n")
                f.write("\n" + md + "\n")
            continue

        try:
            res = client.create_post(title, md, subtitle=subtitle or None,
                                     cover_image_url=cover, visibility=visibility)
            url = client.post_url(res["id"])
            print(f"     LIVE: {url}")
            results.append((title, url))
        except Exception as e:
            print(f"     FAILED: {e}")
        time.sleep(1.2)  # stay under 60/min

    if live:
        print(f"\nPublished {len(results)}/{len(window)}:")
        for t, u in results:
            print(f"  {u}  {t[:50]}")
    else:
        print(f"\nWrote {len(window)} previews to {SCRATCH}")
        print("Review them, then re-run with --post to publish live.")


if __name__ == "__main__":
    main()
