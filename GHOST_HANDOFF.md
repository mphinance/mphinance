# Ghost Handoff — Last Updated 2026-09-26

## 2026-09-26 - Breast Cancer Awareness Pink Hat Mockups & Cricut Universal Cut Kit
- **What got done:**
  - Decoded Michael's QWERTY left-hand shifted typing ("diear mw rqo PNF" -> "first me two PNG").
  - Inspected DSG Adult All Sport Cap (Web ID `24qyfadsgllsprtcpdsg`, SKU `25309154`) in Fuego Pink / Pink Spirit.
  - Generated photorealistic studio product mockups for Breast Cancer Awareness hats:
    - Option 1 (Front + Side Temple): `FUCK CANCER` on front crown, `I LOVE BOOBS` on left temple.
    - Option 2 (Back Keyhole Arch): `FUCK CANCER` on front, `I LOVE BOOBS` arched over rear strap opening.
    - Option 3 (Unified Front Stack): `FUCK CANCER` stacked over `SAVE THE BOOBS`.
    - Multiple styling variants: Collegiate Varsity Arch, Vintage Baseball Script, Circular Roundel Badge, Modern Streetwear Box.
  - **Key Innovation (The Universal Add-Around Frame Kit):** Solved the problem of applying decals to existing caps with pre-sewn 3D embroidered ribbons. Engineered an SVG cut path that arches `FUCK CANCER` over the top of any standard 1.25"-1.5" sewn ribbon and grounds `SAVE THE BOOBS` beneath the tails with zero vinyl-on-thread overlap, printable on a single sheet of transfer tape.
  - Generated full vector SVGs (native cut paths, no font dependencies) and 300 DPI transparent PNG cut files in both white and black HTV variants.
  - Documented everything with Cricut press instructions, sizing, and weeding guidelines in `docs/cricut/README.md`.
  - Mirrored all assets to `landing/assets/cricut/` and `docs/cricut/`.
- **What's left:**
  - Send `docs/cricut/universal_ribbon_frame_kit.svg` to Mom for test-cutting on white HTV.
  - Optional: Host the SVGs as a free community download bundle for Breast Cancer Awareness month on `mphinance.com`.

## 2026-09-15 - Substack Pipeline Bake-Off, Ling 3.0 Flash Teardown & Alpha Soul Post
- **What got done:**
  - Tested Substack draft pipeline end-to-end using `tools/push_substack.py` with `.venv/bin/python` and authenticated session via `secrets.env`.
  - Ran bake-off using `inclusionai/ling-3.0-flash` on OpenRouter (key from `projects/alphaclaw/.env.alphaclaw`) to compare generative voice mimicry vs. structural red-team critique.
  - Used Ling 3.0 Flash across 2 rounds to ruthlessly audit the post (killed 3-adjective stacks, eliminated bullet symmetry, tightened transitions).
  - Wrote, restructured, and polished `articles/alphaclaw-soul/substack-post.md` (Title: *The Soul Of A Trading Agent*). Flipped structure to put NotebookLM free goods first for general readers, followed by the builder deep-dive on Alpha and `SOUL.md`.
  - Generated two bespoke 16:9 dark-theme Bloomberg/quant graphics (`hero_banner.png` and `second_brain_diagram.png`).
  - Uploaded both images directly to Substack's S3 media endpoint and pushed the complete post with native inline `captionedImage` nodes: **Draft #215920355**.
  - Weaved in Michael's public NotebookLM second brain instance (`b41f138d-7993-4085-84b4-2ef230a62007`).
- **What's left:**
  - Review and publish Draft #215920355 on Substack.
  - Michael's Big Book Ch. 10 essay (`articles/victims-of-our-destruction/substack-post.md`) is sitting untracked ready to push whenever he wants.

## 2026-06-28 - Convergence Scan vs. Competitor 7-Pick List
- **What got done:** Ran the full `stock-recap` end-to-end (gather.mjs) plus direct MCP pulls for sector flow, market stats, put/call. Graded the output against a competitor's 2026-06-28 list: HIVE, AMC, HTZ, PURR, QS, TE, WYNN.
- **Verdict:** Only **PURR** crossed (CSP Wheel screener — fat-IV / premium-sell flag, NOT a directional long). The other 6 appeared in ZERO legs (screeners, 13F/TickerTrace, CBOE listings).
- **Data caveat (important):** Weekend run. Live flow / unusual-activity feed returned **0 rows**; all put/call ratios came back 0 (no volume). Convergence this run = screeners + 13F overlap only. Sector flow + market stats still resolve (as-of 2026-06-26).
- **My honest shortlist:** LRCX (screener+cross-fund, clean uptrend pullback), KNX (best under-$100 shallow-pullback chart, Michael's setup), VSH (2 screeners+13F but parabolic — caution). QCOM flagged as a conflict (funds buy vs. chart breakdown). MU/CAT extended/high-priced.
- **Run artifacts:** `.claude/skills/stock-recap/runs/2026-06-28_1451/` (report.md, raw/, charts/).
- **What's left:** (1) market-closed guard so the flow leg fails loudly on weekends; (2) auto-chart competitor-overlap tickers (PURR rendered no chart); (3) a reusable "convergence vs. the field" diff tool.

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

