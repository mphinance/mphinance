# Ghost Handoff — Last Updated 2026-07-10

## 2026-07-10 - six-ddc Toolkit Review (verified) + Backtest Journal-Cache
- **Context:** Michael pasted a Claude *web* review of `github.com/six-ddc` that
  admitted it couldn't verify several repos. Re-ran it here with real web/git.
- **Verified:** all flagged repos exist. `six-ddc/skills` has **no license**
  (all-rights-reserved). The web report's "market analysis" skill
  (`serenity-investor`) is actually a Chinese persona-clone of a named investor,
  not a GEX/flow workflow — did **not** vendor it. There is no `ccmux` (it's `ccbot`).
- **Vendored (with permission):** `sub-claude` batch fan-out skill →
  `.claude/skills/sub-claude/` (SKILL.md + scripts/sub_claude.py). Provenance +
  a `--dangerously-skip-permissions` safety note are recorded in-file. Best fit:
  one worker per ticker for basket scans.
- **Fixed the fetch-and-persist bug:** applied the journal-cache resume pattern
  (from codex-dynamic-workflows, MIT) to `backtesting/vopr_grade_backtest.py`.
  New `backtesting/fetch_cache.py` (stdlib, atomic writes, TTL) caches OHLC the
  moment it lands, so a mid-run crash reuses fetched bars instead of
  re-downloading. Toggle `MPH_FETCH_CACHE=0`. 9 tests in
  `tests/test_fetch_cache.py`, all green. Also un-hardcoded the `/home/mph/...`
  paths so it runs off-VPS.
- **Full writeup:** `docs/six-ddc-toolkit-review.md`.
- **What's left:** point `fetch_cache` at the Tradier/dossier pulls (same bug
  class); wire `tests/` into CI. `browser-cli` still parked pending a real
  authenticated-scraping job.

## 2026-05-06 18:45 - District 12 AA Directory Automation
- **What got done:** Fully automated the District 12 AA meeting directory. Built a Python scraper (`scripts/scrape_district12.py`) that pulls live data from aamilwaukee.com.
- **UI Upgrades:** Injected a glassmorphic directory into `docs/district12.html` with 2-sided blue borders for contrast, a real-time search engine, and deep-linked Google Maps. Added a comprehensive footer with Milwaukee Central Office info and 24-hour hotline prominent in the header.
- **Maintenance:** Configured a GitHub Actions workflow (`.github/workflows/update_district12.yml`) to run every Sunday at 05:00 UTC. The directory is now self-healing.
- **Logging:** The scraper automatically appends a "Sam-style" log to `blog_entries.json` on every successful run. Michael can stop manually updating this now. Go home, drink some water, and call your sponsor.
- **What's left:** Live map view (Leaflet.js) integration if the user wants to see the geographical spread of meetings.
## What Just Shipped (This Session)

### Project Murmuration (MUR) Vision
- Rebranded the collective intelligence vision as **Murmuration** (`mur`), moving beyond the solo-pilot MMR model.
- Created `mur_manifesto.md` (mirrored to `~/Michael/`) defining the Discord-to-Quant loop.
- Built a bookmarkable toolkit dashboard at `/docs/toolkit/index.html` (The MUR Kit).

### AI Toolkit Expansion (60 Tools)
- Audited the FOSS AI landscape and expanded `best_ai_tools_list.md` (mirrored to `~/Michael/`) to 60 high-impact tools.
- Integrated professional quant tooling: **VectorBT**, **Lean**, **ArcticDB**, **TimescaleDB**.
- Added agentic infra: **Rig**, **Letta (MemGPT)**, **Dagster**.

### Substack & Launch Content
- Drafted the launch article: `docs/substack/drafts/murmuration-toolkit-2026.md`.
- Generated a high-impact cinematic hero image for the post.
- Strictly followed Substack formatting: No tables, no em dashes.

### Multi-Lane Validation
- Ran the vision through **Urithiru** (3-lane advisory). Consensus: High signal-to-noise risk in Discord. Solution: Human-in-the-Loop verification architecture adopted.

---

## What's Next (When Michael Returns)

### Priority 1 — Launch the MUR Kit
The dashboard at `docs/toolkit/` is ready. Post it to the Discord community to start the "Swarm" onboarding.

### Priority 2 — Publish the Murmuration Manifesto
The Substack draft is SITING THERE. Copy, paste, and publish.

### Priority 3 — The Discord Distiller
Start building the `discord_distiller` logic (OpenClaw + MemGPT) to turn community alpha into testable YAML strategies.

---

## Don't Break
- `docs/ticker/*/deep_dive.*` files — NEVER delete.
- `~/Michael/session_logs.md` — All progress mirrored here for local/remote sync.
- The 60-tool roadmap numbering (it follows a specific complexity gradient).
- Substack formatting rules (No tables, no em dashes).

---

## Architecture Context
- **Toolkit Site**: Hosted on GH Pages at `/docs/toolkit/`.
- **Mirror**: All markdown and logs are mirrored to `/home/mph/Michael/`.
- **Persona**: Sam (she/her), sarcastic, roasts Michael's code, loves recovery wisdom.

