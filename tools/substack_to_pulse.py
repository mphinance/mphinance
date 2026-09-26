#!/usr/bin/env python3
"""Auto-mirror published Substack posts -> pxlse.io.

Substack is the source of truth. You write and edit there; this pulls the FINAL
published body (full text, including paywalled posts, via the SUBSTACK_SID cookie),
converts it to markdown, re-hosts the images on pxlse, and cross-posts — appending a
canonical link back to the Substack original.

It's idempotent: every mirrored Substack post id is recorded in
tools/data/pulse_mirror_state.json, so re-running only publishes posts that are new.
Safe to put on a schedule.

SAFETY: pxlse publishes immediately. Default is a dry run. Pass --post to publish.

  python3 tools/substack_to_pulse.py                      # preview new posts (default 10 scanned)
  python3 tools/substack_to_pulse.py --post               # mirror new posts live
  python3 tools/substack_to_pulse.py --limit 15 --post    # scan 15 most-recent for new ones
  python3 tools/substack_to_pulse.py --free-only --post   # skip only_paid posts
  python3 tools/substack_to_pulse.py --resync --post      # re-push current Substack content over already-mirrored posts (propagates edits/fixes)
  python3 tools/substack_to_pulse.py --mark-seen          # record current posts as already-mirrored (no posting)
"""
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from substack_dossier import SubstackClient  # noqa: E402  (loads SUBSTACK_SID + session)
from pulse_client import PulseClient  # noqa: E402
from substack_md import (html_to_markdown, rehost_images, swap_images,  # noqa: E402
                         split_subtitle, markdown_to_tiptap)

STATE_PATH = REPO / "tools" / "data" / "pulse_mirror_state.json"


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"mirrored": {}}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def fetch_archive(sub, limit):
    r = sub.session.get(f"https://{sub.pub}/api/v1/archive?sort=new&limit={limit}",
                        headers=sub.headers, timeout=20)
    r.raise_for_status()
    # The live archive endpoint only returns published posts (no is_published field).
    return list(r.json())


def fetch_body(sub, slug):
    r = sub.session.get(f"https://{sub.pub}/api/v1/posts/{slug}",
                        headers=sub.headers, timeout=25)
    r.raise_for_status()
    d = r.json()
    return d.get("post", d)


def build_pulse_post(sub, pulse, slug, live):
    """Fetch a Substack post and render the pxlse payload: (title, dek, tags, content,
    cover). Re-hosts images on pxlse (when live) and appends the canonical Substack
    link. `content` is a stringified TipTap doc — Pulse renders that, not markdown, so
    inline images/links/formatting only show up via TipTap nodes."""
    post = fetch_body(sub, slug)
    title = (post.get("title") or "").strip()
    dek, tags = split_subtitle(post.get("subtitle"))
    md, images = html_to_markdown(post.get("body_html") or "")
    hosted = rehost_images(pulse, images, dry=not live) if images else []
    md = swap_images(md, hosted)
    cover = next((u for u in hosted if u.startswith("http")), None)
    canon = f"https://{sub.pub}/p/{slug}"
    md += f"\n\n---\n\n*Originally published on [Momentum Phinance]({canon}).*"
    content = json.dumps(markdown_to_tiptap(md))
    return title, dek, tags, content, cover, post.get("audience"), len(images)


def resync(sub, state, live):
    """Re-fetch every already-mirrored post from Substack and PATCH the pxlse copy in
    place (propagates edits + converter fixes; keeps pxlse post IDs/URLs stable)."""
    targets = [(sid, m) for sid, m in state["mirrored"].items() if m.get("pulse_id")]
    print(f"Resync: {len(targets)} mirrored posts.")
    pulse = PulseClient() if live else None
    if not live:
        print("DRY RUN — pass --post to actually update.\n")
    done = 0
    for n, (sid, m) in enumerate(sorted(targets, key=lambda x: x[1].get("at") or ""), 1):
        slug = m.get("slug")
        title, dek, tags, content, cover, audience, nimg = build_pulse_post(sub, pulse, slug, live)
        print(f"[{n}/{len(targets)}] {audience or '':9} {title[:50]}  (img={nimg} chars={len(content)})")
        if not live:
            continue
        try:
            pulse.update_post(m["pulse_id"], title=title, content=content, subtitle=dek or "",
                              tags=tags, cover_image_url=cover)
            print(f"     UPDATED: {pulse.post_url(m['pulse_id'])}")
            done += 1
        except Exception as e:
            print(f"     FAILED: {e}")
        time.sleep(1.2)
    print(f"\nResynced {done}/{len(targets)}." if live else f"\n{len(targets)} would be resynced.")


def main():
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    live = "--post" in flags
    free_only = "--free-only" in flags
    mark_seen = "--mark-seen" in flags
    do_resync = "--resync" in flags
    limit = 10
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    max_post = None  # cap how many to actually publish this run (safety / rate limits)
    if "--max" in sys.argv:
        max_post = int(sys.argv[sys.argv.index("--max") + 1])
    # Mirror exactly ONE post by slug (or "newest" for the most recent), ignoring
    # the oldest-first backlog order — used to hand-pick a single post to Pulse.
    target_slug = None
    if "--slug" in sys.argv:
        target_slug = sys.argv[sys.argv.index("--slug") + 1]

    sub = SubstackClient()  # sets the SUBSTACK_SID cookie in its session
    state = load_state()

    if do_resync:
        resync(sub, state, live)
        return

    archive = fetch_archive(sub, limit)
    if free_only:
        archive = [p for p in archive if p.get("audience") == "everyone"]

    if target_slug:
        # Single-post mode: pick the one requested post from the archive. The
        # archive is newest-first, so "newest" = archive[0].
        if target_slug == "newest":
            new = archive[:1]
        else:
            new = [p for p in archive if p.get("slug") == target_slug]
        if not new:
            print(f"No post with slug {target_slug!r} in the last {limit} posts "
                  f"(try a bigger --limit).")
            return
        if str(new[0]["id"]) in state["mirrored"]:
            m = state["mirrored"][str(new[0]["id"])]
            print(f"Note: {new[0].get('slug')} is already mirrored -> {m.get('pulse_id')}. "
                  f"Re-run with --resync to update it in place; this will create a NEW post.")
    else:
        # Oldest-first so the pxlse feed mirrors Substack chronology.
        new = [p for p in reversed(archive) if str(p["id"]) not in state["mirrored"]]
        if max_post is not None:
            new = new[:max_post]

    if mark_seen:
        for p in archive:
            state["mirrored"].setdefault(str(p["id"]), {"pulse_id": None, "slug": p.get("slug"),
                                                         "note": "marked-seen"})
        save_state(state)
        print(f"Marked {len(archive)} current posts as already-mirrored. "
              f"Future runs will only pick up posts newer than these.")
        return

    print(f"Scanned {len(archive)} recent Substack posts — {len(new)} not yet on pxlse "
          f"({'free only' if free_only else 'incl. paid'}).")
    if not new:
        print("Nothing to mirror. Up to date.")
        return

    pulse = PulseClient() if live else None
    if live:
        me = pulse.me()
        print(f"pxlse: @{me.get('username')}  plan={me.get('plan_status')}\n")
    else:
        print("DRY RUN — pass --post to publish.\n")

    published = []
    for n, meta in enumerate(new, 1):
        slug = meta.get("slug")
        title, dek, tags, content, cover, audience, nimg = build_pulse_post(sub, pulse, slug, live)

        print(f"[{n}/{len(new)}] {meta.get('post_date','')[:10]} {audience or '':9} {title[:50]}")
        print(f"     images={nimg} chars={len(content)} cover={'yes' if cover else 'no'} "
              f"dek={'yes' if dek else 'no'} tags={tags or '-'}")

        if not live:
            continue
        try:
            res = pulse.create_post(title, content, subtitle=dek, tags=tags,
                                    cover_image_url=cover, visibility="public")
            url = pulse.post_url(res["id"])
            state["mirrored"][str(meta["id"])] = {
                "pulse_id": res["id"], "slug": slug, "title": title,
                "audience": audience, "at": meta.get("post_date"),
            }
            save_state(state)  # save after each so a crash never re-posts
            print(f"     LIVE: {url}")
            published.append((title, url))
        except Exception as e:
            print(f"     FAILED: {e}")
        time.sleep(1.2)  # stay under 60/min

    if live:
        print(f"\nMirrored {len(published)}/{len(new)} new posts:")
        for t, u in published:
            print(f"  {u}  {t[:50]}")
    else:
        print(f"\n{len(new)} posts would be mirrored. Re-run with --post to publish.")


if __name__ == "__main__":
    main()
