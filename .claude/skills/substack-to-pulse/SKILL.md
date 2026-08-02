---
name: substack-to-pulse
description: >-
  Mirror a published Substack post (including paid/subscriber-only) onto
  mph's PERSONAL Pulse feed (pxlse.io) — no double-entry. Pulls the full body
  via the Substack SID cookie, converts HTML to markdown, re-hosts every image
  on Pulse's CDN, appends the canonical Substack link, and publishes under
  @mphinance's own feed (NOT the traderdaddy community). Idempotent per post.
  Use when Michael says "post this to Pulse too", "mirror my Substack to Pulse",
  "cross-post that article to pxlse", or "run it side by side on Pulse".
---

# Substack → Pulse (personal feed)

One command mirrors a published Substack post to Michael's **personal** Pulse
feed, so a paid Substack piece and its Pulse twin never get hand-entered twice.

Tool: `tools/substack_to_pulse.py` (run from `/home/mph/mphinance`).
State: `tools/data/pulse_mirror_state.json` (idempotent — a post is mirrored once).

## The flow it runs

1. Fetch the Substack archive (auth via `SUBSTACK_SID` cookie in `secrets.env`).
2. Pull the FULL body — SID cookie unlocks paid/subscriber-only bodies.
3. HTML → markdown → **TipTap doc**; re-host every image on Pulse's CDN (`POST /media`).
   Pulse renders `content` as TipTap, NOT markdown — raw `![](url)` shows as literal
   text and inline images vanish (only the separate `cover_image_url` renders). The
   mirror converts via `substack_md.markdown_to_tiptap` so images/links/bold/headings
   become real nodes.
4. `create_post(...)` with **no `community_slug`** → lands on the personal feed.
5. Append the canonical Substack link so readers can find the original.
6. Record the Pulse id in state so it's never re-posted.

## Commands (always from `/home/mph/mphinance`)

```bash
# See what's not yet mirrored (safe, no writes). --limit widens the scan window.
python3 tools/substack_to_pulse.py --limit 12

# Mirror exactly ONE post by slug (dry-run first, then --post to go live)
python3 tools/substack_to_pulse.py --slug <post-slug> --limit 6
python3 tools/substack_to_pulse.py --slug <post-slug> --limit 6 --post

# Mirror the single most-recent published post
python3 tools/substack_to_pulse.py --slug newest --limit 6 --post
```

- The slug is the last path segment of the Substack URL
  (e.g. `.../p/i-tokenized-my-glxy-do-you-actually` → `i-tokenized-my-glxy-do-you-actually`).
- Without `--slug`, the tool mirrors the oldest-first backlog of unmirrored
  posts; use `--slug` to hand-pick one and skip the backlog.
- If a slug is already mirrored, the tool warns and (without `--resync`) a fresh
  `--post` would create a NEW Pulse post — use `--resync` to update in place.

## Guardrails

- **Always dry-run first**, show Michael the title/images/chars/cover line, and
  **confirm before `--post`** — it publishes publicly and immediately to his feed.
- Personal feed only: never pass `community_slug` here. The traderdaddy-community
  autoposter lives in `tdpro-pulse/` and is a separate pipeline.
- Both repos auth as mphinance on Pulse; only the SID cookie is shared context.
- Cloudflare 1010: every HTTP client needs an explicit User-Agent (handled).
