# Daily Review — Dossier Extension Plan

> Handoff brief. Written 2026-06-17 from a TD Pro session after researching how to turn the
> existing **Ghost Alpha Dossier** into the "daily kick-ass review" Mike wants. Pick this up in a
> **fresh session rooted in `/home/mph/mphinance`** — everything needed to execute is here, so you
> don't need the TD Pro context that produced it.

## The goal (in Mike's words)

A daily, push-delivered market review that pulls all the screeners + flow + 13F, breaks out the
signals **especially noting confluence and tickers that migrate from one screener to the next**, and
lands somewhere he'll actually see it. He kept forgetting the dossier exists because it's *so
automated nothing pings him*.

## Key realization

**Don't build new. The engine already exists** — it's `mphinance/dossier` (this repo), live on
GitHub Actions (`.github/workflows/daily_dossier.yml`, cron `0 10 * * 1-5`), Python +
`tradingview_screener` (free data), with screeners + market regime + 13F + 21-day signal
persistence + Gemini narrative + charts + HTML/MD output + a Discord teaser. The work is **revive +
extend**, not rebuild. The dossier was last run/committed **2026-06-09** (8 days stale as of writing).

## Decisions locked (from Mike)

- ✅ **Extend in place** in `mphinance/dossier` (don't fork; keeps the live GH Actions deploy working).
- ✅ **Drop politician trades** entirely.
- ✅ **Tradier key is Mike's own** (already a GH Actions secret `TRADIER_API_KEY`) → options flow is in scope.
- ✅ **Earnings + screeners via TradingView** (the `tradingview_screener` lib the repo already uses).
- ✅ **Delivery: Discord first** (the teaser already exists; just dead in prod — see Phase 0). Email (SendGrid) only later if the *full* report in inbox is wanted.
- ✅ **SQLite/persistence**: reuse the existing 21-day `persistence/tracker.py` (GCS + local-file fallback). No new DB needed for v1.
- ✅ **Runner = this Hetzner box, as a Claude scheduled task (Option A).** Confirmed host is an always-on Hetzner vServer (`ubuntu-4gb-ash-1-traderdaddy`, Ashburn, Ubuntu 24.04), NOT Mike's laptop — Mike SSHes in from the laptop's Claude Desktop. A Happy daemon keeps Claude sessions alive 24/7 and Remote Control is connected (→ phone push works). So a **durable `CronCreate`** task here is reliable; we can run the whole review in Claude and **retire the Cloud Run / GitHub Actions deploy** (or keep GH Actions only as a silent floor). Caveat: fires only while a session is idle + box awake; recurring auto-expires after 7 days (durable survives restarts — confirm re-arm).
- ✅ **Review authored by Claude, not Gemini** — and Claude **reads the chart PNGs** (multimodal) the way the `stock-recap` skill does ("visual read overrides the indicator table"). The dossier's `charts.py` already renders candles; the Gemini narrator never looks at them. Option A fixes that.
- ✅ **IBKR holdings overlay** — add a personalized "Your Book" section (see Phase 3.5).

---

## Research findings (condensed — full detail was gathered by 4 agents)

### 1. Delivery is 90% built, dead for ONE reason
- `dossier/report/discord_notify.py::post_dossier_to_discord(summary)` builds a compact daily teaser
  (date, regime+emoji, SPY/VIX, 🥇 gold pick w/ score+grade+upside, signal count, Sam quote,
  deep-link to full report) and POSTs via **curl** (deliberately — Cloudflare blocks urllib).
- `generate.py` already calls it at the Stage-15 block (wrapped in try/except).
- **It reads `WEBHOOK_SAM_MPH` from env.** The live `daily_dossier.yml` env block passes Gemini/Tradier/
  Tickertrace/Substack secrets but **NOT `WEBHOOK_SAM_MPH`** → `_get_webhook()` returns empty → it prints
  `[WARN] No WEBHOOK_SAM_MPH available — skipping Discord` and bails. Firebase fallback needs a
  `service_account.json` not present in CI, so that path also no-ops.
- **Fix:** add `WEBHOOK_SAM_MPH: ${{ secrets.WEBHOOK_SAM_MPH }}` to the workflow env block, and add the
  GitHub Actions repo secret with the Discord webhook URL. (Webhook > bot token: no token mgmt, no
  Railway coupling. `.env.example` already documents the `WEBHOOK_*` convention.)
- Nit to fix while there: silent failure. A *broken* notifier recreates the "I forget it exists"
  problem — make it louder (non-zero exit or a fallback ping).

### 2. Triangle breakout = copy, not rebuild
- TD Pro's detector is **already pure Python, OHLCV-only, no DB/Tradier**:
  `TraderDaddy-Pro---Whop/backend/indicators/triangle_logic.py` (3,146 lines, ported from FinFunPub's
  breakout_scanner). CLI wrapper `backend/src/scripts/run_triangle_detection.py` feeds it yfinance daily bars.
- **Port = copy `triangle_logic.py` ~verbatim**, call `compute_breakout_snapshot(df, cfg)` with daily OHLCV
  (`cfg = replace(BreakoutConfig(), required_history_bars_qualified=300)`), then apply the CLI's 3 post-gates:
  1. Universe Quality OK (20d avg $vol ≥ $5M, price ≥ $2, 20d avg shares ≥ 300k, ≥ 300 bars).
  2. `TD Triangle == 1` → `triangle_breakout`, or `TD Triangle Forming == 1` → `triangle_forming`.
  3. **Cliff filter** `MAX_UPPER_SLOPE_PCT_PER_BAR = 0.45` (reject crashing-downtrend false ceilings) — this
     lives in the CLI, not the engine, so replicate it.
- Needs ~2y daily OHLCV (`period="2y"`, hard-requires ≥300 bars), `auto_adjust=True`. Volume needed for
  the universe/liquidity gate. `Trend Outlier` sub-block needs benchmark histories but the CLI passes
  `None` → it's a no-op, safe to drop.
- Output fields: `signal_type, pattern (confirmed|forming), signal_strength (strong≥70/moderate≥50/weak),
  composite_score, triangle_score, compression_ratio, descending_drop_pct, vertex_gap_pct, bars_to_vertex,
  breakout_pct, upper_line_price/slope, support_price/slope/touch_count, anchor_type, vertex_date, trend_stage`
  + chart-overlay anchor dates/prices.
- Key constants: lookback 60 / recent 5 / min support touches 2 / span ≥8 / compression ≤0.80 /
  descending drop ≤−2.5% / vertex gap ≤30% / bars-to-vertex ≤15 / breakout buffer 1.0% / breakout-recent ≤8.

### 3. Options flow via Tradier (daily batch) ≈ 75% of TD Pro's signal
- TD Pro scores 0–100 (bonuses → 200 cap): **Vol/OI (40) + premium size (30) + bid-ask spread (15) + DTE (15)**,
  plus bonuses (sweep +15, block +10, repeat +15/25, contra-market +10). Sentiment = exec price vs bid-ask mid.
  Tiers: UNUSUAL ≥85, HIGH_CONVICTION ≥95, INSTITUTIONAL_ALPHA ≥110, EXTREME ≥130.
- **Daily-batch reproduces the static base score fully** (Vol/OI + premium + spread + DTE). **Lost:** true
  sweep/block/split (needs intraday time&sales), reliable buy/sell sentiment (stale EOD quote), live alerting.
  For a daily watchlist that loss is acceptable — Vol/OI + premium-skew are the load-bearing terms.
- **No paid Tradier tier needed.** All on standard API: `/markets/options/expirations`,
  `/markets/options/chains?greeks=true`, `/markets/quotes`. OI posts T+1, so cleanest run is next morning
  (compare prior-day volume to freshly-posted OI). The dossier **already has a working Tradier client** inside
  `gamma_pin_screener.py` (`_get_tradier_key`, `_tradier_headers`, `get_options_chain`,
  `get_options_expirations`, `find_nearest_expiration`) — reuse it.
- **Recommended daily flow output per ticker:** unusual-volume strikes (vol≫OI, scored), largest-premium
  strikes, call/put premium skew (one bullish/bearish read), same-day repeat/accumulation, fresh-position flag
  (vol>OI), SHORT_DATED tag (0–3 DTE — TD Pro's own data says these underperform). Label trade-type honestly
  ("DAILY_VOLUME", not fake "SWEEP") and mark sentiment low-confidence/inferred.
- **Upgrade path:** persist each daily chain snapshot from day one → after ~30 trading days compute per-ticker
  Vol/OI & premium percentiles (port `calculateBaselines.ts`) → adaptive scoring ("unusual for AAPL ≠ for MARA").

### 4. Dossier is clean to extend
- `generate.py::run_pipeline()` = one sequential orchestrator; stages are numbered `print("[N/16]...")` blocks,
  most wrapped in try/except, each output a local dict/list threaded downstream. Only Stage 8 (ticker
  enrichment) is parallel (`ThreadPoolExecutor(max_workers=10)`).
- **Screener pattern:** modules of free functions in `data_sources/`. Per-ticker `scan_*/analyze_* -> dict|None`
  + batch `generate_*(tickers, max) -> list[dict]`; each dict carries `ticker, score, direction, rationale[]`.
  OHLCV via `yf.Ticker(t).history(period=...)`, guard `if df.empty or len(df) < N`. Reuse `_ema/_sma/_rsi/_safe`.
- **Persistence (`persistence/tracker.py`):** `update_persistence(tickers, date)` keys on bare ticker, 21-day
  window, classifies lifers (≥20d) / high_conviction (≥10d) / new (≤3d) + streak. **No signal-type dimension** —
  generalize to `update_persistence(tickers, date, namespace="scanner")` writing
  `signal_history_{namespace}.json` so triangle/flow get independent day-over-day history. Git-push already
  commits `persistence/data/`.
- **Report (Jinja2):** `report/builder.py::build_report(...)` renders `report/template.html` (each section is a
  `{% if var %}` panel; `<!-- ═══ DAILY CUTS ═══ -->` at template.html:389 is the copy-template; note
  `gamma_warnings` is passed but has no panel yet — a ready example to follow). Also `build_markdown(...)` for
  the `.md` twin and `report/summary_api.py` → `docs/api/dossier-summary.json` which feeds Discord/Substack.
- **Adding a section touches 3 places:** the `build_report(...)` call in `generate.py`; the signature +
  `template.render(...)` in `builder.py` (+ markdown + summary_api for the fanout); a panel in `template.html`.
- **Config/deploy:** `config.py` (dotenv; GEMINI/TICKERTRACE/watchlists; `TRADIER_API_KEY` read via `os.getenv`
  in the gamma screener, already a GH secret). Live = GitHub Actions cron above. Local run:
  `python -m dossier.generate --dry-run` (no git push), `--date YYYY-MM-DD`, `--no-pdf`.

---

## The plan — phased, highest-leverage first

### Phase 0 — Turn the lights back on (do first; smallest, biggest payoff)
Goal: the *existing* dossier starts pinging Mike daily again. Solves "I forget it exists."
1. Add `WEBHOOK_SAM_MPH: ${{ secrets.WEBHOOK_SAM_MPH }}` to the `Generate Alpha Dossier` env block in
   `.github/workflows/daily_dossier.yml`.
2. **[NEEDS MIKE]** Create a Discord webhook for the target channel and add it as GH Actions secret
   `WEBHOOK_SAM_MPH`. (Also mirror into local `.env` for test runs.)
3. Make `discord_notify` fail loud, not silent.
4. Do one **`--dry-run`** local run to confirm end-to-end (it's 8 days stale; verify TradingView/Tradier/Gemini
   still work) and that the teaser posts. **Don't push to prod until Mike OKs.**

### Phase 1 — Triangle breakout (your unique signal; easy)
1. Copy `TraderDaddy-Pro---Whop/backend/indicators/triangle_logic.py` → `dossier/data_sources/triangle_logic.py`.
2. New `dossier/data_sources/triangle_screener.py`: `scan_triangle(ticker)->dict|None` (yfinance 2y daily →
   `compute_breakout_snapshot` → 3 CLI gates) + `generate_triangles(tickers, max)->list[dict]` in the screener shape.
3. Add a pipeline stage in `generate.py` (after Stage 2/universe; doesn't need dossiers).
4. Add report section (3 places) + namespaced persistence (`namespace="triangle"`).

### Phase 2 — Options flow (your Tradier key)
1. Optionally refactor the Tradier client out of `gamma_pin_screener.py` into
   `dossier/data_sources/tradier_client.py`; else import from the gamma screener.
2. New `dossier/data_sources/options_flow.py`: per-ticker daily snapshot (Vol/OI, premium, spread, DTE static
   score; call/put skew; fresh-position; SHORT_DATED tag; honest labels). Port scoring from
   `TraderDaddy-Pro---Whop/backend/src/services/unusualActivity.ts` + filters from
   `backend/src/jobs/helpers/contractFiltering.ts` + tiers from `backend/src/services/filterConfig.ts`.
3. **Persist the raw daily chain snapshot** from day one (enables adaptive scoring in ~30 days).
4. Stage + section + persistence (`namespace="flow"`).

### Phase 3 — Confluence + migration (the synthesis Mike actually asked for)
1. Make `persistence/tracker.py` namespace-aware (per signal type).
2. New top-of-report **"Today's Watchlist"** section: rank tickers by how many independent legs agree
   (triangle + flow + 13F + momentum + regime), borrowing the directional-convergence logic from TD Pro's
   `.claude/skills/stock-recap/scripts/gather.mjs` (bullish legs add, bearish flow/fund selling = conflict).
3. **Day-over-day migration view:** new→high-conviction→lifer transitions, and cross-screener moves
   ("appeared in momentum Mon, now triangle+flow Wed = maturing setup, escalate"). This is the unique value.
4. Ensure the Discord teaser + `summary_api.py` surface the confluence watchlist + top migration.

### Phase 3.5 — IBKR holdings overlay ("Your Book")
Personalized section: pull Mike's live IBKR positions, cross-reference each against the day's signals.
1. **Data source — two paths:**
   - *Interactive/manual runs:* the claude.ai IBKR MCP (`mcp__claude_ai_Interactive_Brokers_IBKR__get_account_positions` / `get_account_summary` / `get_pa_allocation`). Confirmed working 2026-06-17.
   - *Unattended scheduled runs:* claude.ai MCPs may be absent headless — pull from the **local gateway at `/home/mph/ibkr/ibkr-gateway/`** instead (IBKR Client Portal / TWS API). Wire this for the cron path.
2. For each position, overlay today's signals: bullish confluence (flow + triangle + 13F-buy + regime) → **hold/add**; bearish flow or 13F-selling → **trim/hedge flag**; theme heat (e.g. LPTH = photonics) → note. Surface any holding that newly appears in a signal, and any laggard with a reversal/bounce setup.
3. Render as a "Your Book" panel + include the top 1-2 actionable holding calls in the Discord/phone push.
4. Small account (NLV ~$2k, mostly single-share starters as of 2026-06-17) — frame as conviction/idea signals, not position-sizing advice.
5. **Conviction context (Mike, 2026-06-17):** ONDS is a deliberate **covered-call income position he wants to SCALE to ~100 shares even at ~40% of the book** — premiums + chart have been excellent, selling the **$10.50 covered calls** with great results. Treat ONDS as a high-conviction wheel/income hold, NOT a laggard to trim. The review should surface ONDS CC context (IV/premium, $10.50 strike distance, upcoming expiry, assignment risk) rather than flag it red on unrealized P&L. (Funded by growing Substack revenue.)

### Phase 3.6 — Ingest the nightly analyst watchlist (external-input overlay)
One of Mike's contacts emails a watchlist every night (e.g. 2026-06-17: `NFLX UMAC UAMY HOOD QBTS WDC AMD RKLB`). Turn that into an automatic overlay.
1. **Ingest:** parse the latest watchlist email → ticker list. Interactive: Gmail MCP (`search_threads`/`get_thread`). Headless/cron caveat: claude.ai Gmail MCP may be absent → fall back to IMAP (app password) or a Gmail-filter-forward + parse. Identify the sender + a parse rule (tickers are usually a space/comma list).
2. **Cross-reference** the list against the day's signals + confluence: "Your guy flagged 8 — the system independently agrees on N (overlap + why); the rest are off-radar (mostly small/mid-caps our universe skips → exactly what the scanline layer should now catch)." Tag each as confirmed / new-to-us / our-system-disagrees.
3. **Surface** in the report + push ("analyst overlap" line). Validated 2026-06-17: of his 8, only AMD surfaced in the dossier (institutional battleground) — the other 7 were invisible due to the narrow-universe gap, which is the headline argument for the scanline universe layer.

### Phase 4 — Polish the push
- Attach the top pick's chart PNG to the Discord post (webhooks support multipart file upload + up to 10 embeds).
- Decide on email (SendGrid HTTP API from CI — greenfield; only if the *full* report in inbox is wanted).
- Optional: a lightweight scheduled-Claude task to editorialize the report before pushing (nice-to-have, not needed).

---

## What's needed from Mike before / during execution
- **Discord webhook URL** for the target channel + add it as GH secret `WEBHOOK_SAM_MPH` (Phase 0).
- **OK to push to the live `mphinance` repo / run the prod dossier** (production — deploys to GitHub Pages + posts Discord).
- Confirm the **ticker universe** for triangle/flow scans (reuse the dossier's `CORE_WATCHLIST` / scanner survivors? or a wider TradingView-screener universe?).

## Files to add / touch
- **Add:** `data_sources/triangle_logic.py` (copy), `data_sources/triangle_screener.py`,
  `data_sources/options_flow.py`, optionally `data_sources/tradier_client.py`.
- **Touch:** `generate.py` (new stages + `build_report` call), `report/builder.py` (signature + render + markdown),
  `report/template.html` (2 panels), `persistence/tracker.py` (namespace param), `report/summary_api.py` (fanout),
  `.github/workflows/daily_dossier.yml` (webhook secret), `requirements.txt` (only if new deps).

## How to run / kick off the fresh session
```bash
cd /home/mph/mphinance
git pull
python -m dossier.generate --dry-run        # safe local run, no git push, no Discord unless WEBHOOK set
# read docs/reports/<date>_alpha_dossier.md and latest.html
```
Start with Phase 0.

---

## Team Review — 2026-06-17 (5-agent audit, prioritized punch list)

**Plot twist:** the pipeline is NOT stale — it runs daily on GitHub Actions (latest `2026-06-17_alpha_dossier.md` confirmed). The local clone was just behind; reconciled 2026-06-17 (rebased `article/amzn-cpi-referee` onto origin/main, 5 writing commits preserved, WIP stashed/restored). So this is **extend + redirect delivery**, not revive.

### Pre-work refactors (do BEFORE adding features — cheap, high-leverage)
- **`build_report()` ctx-dict refactor** — collapse the 18-arg signature (`builder.py:17`, `generate.py:992`) into one `report_ctx` dict; each new section becomes a 2-file change. (origin already started extracting helpers → `dossier/utils/indicators.py`.)
- **Consolidate secrets in `config.py`** — canonical `TRADIER_API_KEY` + `WEBHOOK_SAM_MPH` from one `.env` (chmod 600); also unblocks the dead Discord push.
- **`persistence/tracker.py`: add `namespace` param** (`signal_history_{ns}.json`) AND **delete the dead GCS branch** (lines ~23-57).
- **Wrap all bare `try/except` stages in `timer.stage()`** so failures surface on `docs/status.html`.

### Reliability (before running on the box / as a Claude task)
- generate.py's in-Python `git push` is broken (no `pull --rebase`, no identity, `check=True` dies on no-op days) — CI masks it with a separate step. If we move runners, fix or replace it.
- **Pin `requirements.txt`** (zero pins today) — yfinance breaks often and underpins ~everything.
- **Atomic persistence write** (temp + `os.replace`) — a crash mid-write silently wipes 21-day streaks.
- **TradingView scanner has no retry** (`ghost_alpha_screener.py:141`) — one blip → near-empty dossier, silently.
- **yfinance from this static IP is the binding constraint** (~300-400 calls/run). Add a shared OHLCV cache (triangle's 2y fetches would otherwise ~double load); keep `ThreadPoolExecutor` at 5-8 for yfinance stages; consider capping the 200-deep-scan to 100-150.

### Signal quality (before building confluence)
- **`momentum_picks.py` scorer is self-contradictory** — docstring (`:9-18`), code weights (`:63-143`), and printed denominators (`:394-403`) all disagree; max is ~110 not 100. Fix before trusting any backtest. ML-importance-derived weights (`:59`) are unvalidated.
- **Persistence is circular** — fed only by Ghost-Alpha survivors (`generate.py:757`), so "21-day lifer" just means "stayed trendy." Feed ALL screeners, namespaced.
- **Confluence must collapse correlated legs** — EMA-stack + Ghost + technical-setups bullish = ONE trend leg, not three. Triangle + flow are the genuinely independent new legs. Require *directional* agreement (bullish adds, bearish flow/fund-selling = conflict, subtracts).
- **Sign discipline:** SHORT_DATED (0-3 DTE) flow = trap (~23% hit) → exclude/penalize, not just label. Gamma-pin = 1-3d mean-reversion, OPPOSITE sign to momentum → never sum as agreement.
- **Migration = ordered maturation sequence** (multibagger/early → triangle_forming → triangle_breakout+flow → momentum/Ghost-A+), with direction preserved and source leg persisting/handing off — NOT "ticker reappeared." Suppress migrations on names that appear in everything daily (mega-cap ubiquity).
- **Missing legs worth adding:** relative-strength vs SPY/sector, and breadth — both decorrelated from the current all-momentum stack.
- **Close the backtest loop** on archives already being written (`gamma-history/`, `daily_picks.json`) — nothing scores them vs forward returns yet. Snapshot regime/macro AS OF signal date (the `spy_lookahead` lesson) for any backtest.
- Smaller: `technical_setups.py` computes "SMA200" on 126 bars (`:75,:95`) — fetch 1y+. Two different "squeeze" definitions across screeners — don't cross-compare. `market_regime.py` ignores its own VIX term-structure in the label (`:57-72`). `multibagger` rewards 0-analyst obscurity (`:307-320`) — demote to manual-DD watchlist, never a confluence leg.

### UX / the push (the "kick-ass" part)
- Current report buries its best asset (the AI synthesis) under undifferentiated lists. Lead with decisions, not completeness.
- **Top-of-report ranked confluence watchlist** (sorted by # independent legs agreeing; show legs as visual pips/chips; amber on valuation/conflict veto; collapse single-leg long tail). Each row carries entry/stop/target (momentum module already computes them).
- **Migration panel = motion** (`🔼 FCX legs 1→3 streak 3d`), surface ONE "migration of the day" for the push.
- **Claude's chart read OVERRIDES the indicator table** when they disagree; render 1-2 sentences per top name; only read top ~3-5 PNGs.
- **`summary_api.py` → `dossier-summary.json` needs new fields first:** `confluence`, `migration`, `your_book`. The push is just a formatter over them.
- **Phone push (5 lines):** regime+VIX · top confluence pick (N legs) · **Your Book alert** · biggest migration · "skip-the-rest" line. Attach top pick's chart PNG. On a nothing-day, say so explicitly.

### IBKR (correction to Phase 3.5)
- **Primary headless source = the local FastAPI bridge `http://127.0.0.1:8765`** (`/positions`, `/account`, `/pnl`, token-auth, `ibkr-bridge.service`, backed by ib_async/TWS). New `data_sources/ibkr_book.py` → `requests.get` it; degrade gracefully on 503 (gateway asleep/stale). claude.ai IBKR MCP = interactive-only convenience. (Alt: `ibkr_client.py` Client Portal REST at :5000.)
- ONDS = CC-income framing (see Phase 3.5 #5); suppress the concentration red-flag for it specifically.

### Fold-ins from other repos
- **StrikeForge** (`/tmp/StrikeForge` clone; `github.com/mphinance/StrikeForge`, live at strikeforge-production.up.railway.app, MIT, last commit 2026-06-16) — a **40-module options-analytics engine** (option-chain X-ray; scoring brain ported from VoPR's "Edge Score 2.0"). Clean importable package: `from scanner import run_scan, run_auto_scan, ScannerConfig`; `run_scan("SPY","2026-03-21")["results"]` returns the graded chain. Runs keyless (yfinance) or with Tradier. Deps: yfinance, pandas, numpy, scipy, requests, tradingview-screener, fastmcp. NOTE: `MORNING_REPORT.md` is a build-status changelog, NOT a daily-market report — no overlap. Ignore `api/`, `auth/whop.py`, `frontend/` (product chrome). Full scanner-module catalog by fold-in priority:
  - **Tier 1 — fold in now (decorrelated from dossier, fill real gaps):**
    - `gex.py` — Gamma Exposure / dealer positioning (gamma flip, call/put walls, regime), ported from TD Pro. Adds a leg the dossier lacks.
    - `market_weather.py` — VIX/VIX3M/VVIX term-structure "should I trade today" regime — upgrades the dossier's level-only `market_regime.py` (which ignores term structure).
    - `structure.py` — "where price sits" structural support/resistance read — feeds setup quality & the Reversal Watch.
    - `earnings.py` — earnings-date awareness for the event-vol gate — feeds the earnings section.
    - `book.py` — **beta-weighted net Greeks + concentration → directly powers the IBKR "Your Book" risk overlay** (Phase 3.5). Better than rolling our own.
    - `capital.py` — Reg-T margin + return-on-capital → **the ONDS covered-call income framing** (premium yield, RoC on the $10.50 calls).
    - `backtest.py` — "does the signal actually predict?" harness → **closes the backtest-loop gap the audit flagged** (validate confluence/signals vs forward returns).
  - **Tier 2 — options/vol depth for the shortlist (VRP, IV rich/cheap):** `rv_forecast.py` (HAR-RV realized-vol forecast), `density.py` (Breeden-Litzenberger risk-neutral density → skew-aware POP/EV), `smile.py`/`surface.py`/`term_structure.py`/`volatility_models.py` (IV smile/surface), `iv_history.py`/`iv_tracker.py` (IV rank/percentile), `edge_score.py` (6-component composite: VRP/surface/regime/execution/technical/gap), `lenses.py` (4 trade-type re-scorings: premium-sell / LEAPS / directional / 0DTE). Deps: `pricing.py`, `greeks.py`, `forward.py`, `quotes.py`. Pull as a bundle only if we want per-name options depth on the watchlist.
  - **Tier 3 — Tradier data layer (accelerates our flow leg):** `tradier_client.py` + `quotes.py` + `data_ingestion.py` + `cache.py` + `filters.py` are a **more mature Tradier-primary/yfinance-fallback client than the dossier's gamma-screener one** — use these as the data foundation for the Phase-2 options-flow leg. (StrikeForge does NOT do unusual-activity *detection* itself — that's still our build — but it gives us the chains/greeks/quotes plumbing.)
  - **Tier 4 — overlaps scanline, prefer scanline:** `prescan.py`, `screen_presets.py`, `computed.py`, `universe.py` were ported from scanline; scanline is the cleaner standalone universe layer — use scanline, not these.
  - **Tier 5 — risk/strategy (future, for the IBKR book + idea generation):** `risk_matrix.py` (T+N P&L surface), `projection.py`, `stress.py`, `tail_risk.py`, `hedge.py`, `strategist.py` ("AI Shopper" suggested multi-leg builds), `execution.py`, `edge_calibration.py`.
  - Reference docs worth reading when implementing: `QUANT_SPEC.md`, `EDGE_SCORE_FINAL.md`, `docs/SCREENING_PLAN.md`, `docs/IV_DRIVERS.md`, `ROADMAP.md`.
- **`scanline`** (`/home/mph/scanline`, live, MIT) — **the screening/universe layer (first-class decision, not optional).** A clean programmable screener over the *whole* TradingView universe (US stocks/crypto/forex/futures/bonds) via `tradingview-screener`, with computed columns (sandboxed AST), in-result stats (`zscore`/`pctrank`/`rank`/`norm`), direction-aware weighted-z-score **factor scoring** (Momentum/Value/Quality/Growth/Low-Vol presets), and a **16-tool MCP server** (fastmcp). Architecture: `backend/pipeline.py::run_screen(ScreenRequest)` is one pure function shared by the HTTP API and MCP — import it directly. Deps are light (fastapi, tradingview-screener, pandas, fastmcp).
  - **Why central:** the dossier's narrow-universe gap (only Ghost-Alpha survivors get deep-screened → a clean bounce like CSCO never even gets evaluated) is exactly what scanline fixes.
  - **Fold-in mode 1 (in-pipeline):** add an early dossier stage that calls scanline's `run_screen()` to build a broad, factor-scored candidate universe, then feed THAT into the deep screeners (Bounce 2.0, triangle, flow) instead of only Ghost-Alpha survivors.
  - **Fold-in mode 2 (Claude task):** register scanline's MCP server so the daily Claude task screens in plain language (`run_factor_preset momentum`, `lookup_symbol CSCO`, `compare [...]`) — ad-hoc "where does X stand?" natively.
  - **Bonus:** scanline's factor scorer is a more principled ranker than `momentum_picks.py`'s self-contradictory composite — candidate to power the confluence score.
  - **Universe gotcha confirmed 2026-06-17:** TD Pro's momentum screener defaults to `include_mega_caps=false`, which is why **CSCO (~$465B) was hidden** at defaults and appeared once mega-caps were enabled. Whatever universe layer we use, be explicit about mega-cap inclusion.

### Runner migration (Cloud Run / GH Actions → Claude scheduled task on this Hetzner box)
- It's already a clean CLI (`python -m dossier.generate`) → migration is mostly *deletion*. Keep `daily_dossier.yml` as a **silent floor until the durable task is proven past 7 days**; never run both (double-commit/post). Drop GCS persistence + Gemini narrative (Claude authors it after reading charts; keep `_fallback_narrative()` as floor). Split: deterministic Python pipeline + Claude turn for judgment/chart-read/push. Risks: 7-day recurring expiry (use durable, verify re-arm), session-must-be-idle, static-IP yfinance throttling.

### Phase-0 dry-run result — PASSED (2026-06-17, on the Hetzner box)
`.venv/bin/python -m dossier.generate --dry-run` → **exit 0, 301.6s (5.0 min)**, full report generated (170 signals, 8 dossiers, 8 ticker pages, VIX 18.44, gold pick USB 47/100). Foundation validated — the whole pipeline runs here. Non-fatal items to fix during the build:
- 🔴 **TickerTrace per-ticker endpoint 404s** (`/api/v1/ticker/<X>`) — 13F *enrichment* dead + ~60s wasted in 3×backoff retries per name. Matches the TickerTrace freeze (2026-06-02). Cut the retries / pull 13F in-house. (The institutional list endpoint still works.)
- 🟡 yfinance dot-ticker (`BRK.B`→`BRK-B`) + a delisted name (`BITF`) fail — normalize symbols / skip cleanly.
- 🟡 `weasyprint` not installed → PDF skipped (fine; install if PDFs wanted). No `WEBHOOK_SAM_MPH` → Discord skipped (Phase-0 item).
- ⏱️ Date rollover: box is UTC, so the report date flips at 00:00 UTC (~8pm ET). The 10:00-UTC cron (~5am CT) is unaffected.

## Build log

### 2026-06-17 — universe layer built (`dossier/data_sources/universe_scan.py`) ✅
First build increment. Leverages scanline's `run_screen` (imported via `SCANLINE_DIR`, default `/home/mph/scanline` — NOT vendored) to produce a momentum-factor-ranked, **size-agnostic** candidate universe. `scan_universe()` / `universe_tickers()`; never raises (returns [] on failure).
- **Fixes the size-bias gap:** the native `_tv_fetch_all_stocks` sorts by market cap and deep-scans only the ~200 biggest names, so small/mid-cap movers (UMAC, etc.) never enter the candidate set. Key fix: **sort the TV query server-side by `Perf.1M`** so the *pool* is momentum-led (without it, TradingView returns biggest-first and small caps are never pulled), then re-rank by composite factor_score. Verified: now surfaces UMAC #24, WDC #40, HOOD #70 + a pool of small/mid movers (INDP, QURE, SIVEF…) the funnel missed.
- **Insight surfaced during the build:** the friend's nightly list spans *theses* — momentum winners (UMAC/WDC/HOOD/AMD, +1M%) AND contrarian/reversal/thematic names with *negative* 1M perf (RKLB −19%, UAMY −12%, NFLX −11%). No single factor catches all 8. So the universe should be a **UNION of a few screens** — momentum + unusual-volume + oversold-bounce — to cover the spread; the reversal/thematic names belong to the Reversal-Watch leg, not the momentum universe.
- **Next:** (a) wire `universe_scan` into `generate.py` as an early stage feeding the deep screeners (augment/replace the top-200-by-mcap funnel); (b) add the multi-screen union; (c) then triangle / flow / confluence.

### 2026-06-18 — branch cleanup + 6 data-source modules built (fanned out) ✅
- **Branch hygiene done:** dossier work now lives on a clean `feature/daily-review` (off origin/main). AMZN drafts + WIP + dry-run artifacts parked in a git stash (`stash@{0}`, retrievable); AMZN writing commits preserved on `article/amzn-cpi-referee`. Commits `dff46ac` (universe + plan) and `c9126dd` (the 6 modules).
- **Built + standalone-tested (all in `dossier/data_sources/`, all degrade gracefully, none wired into generate.py yet):**
  - `triangle_screener.py` + `triangle_logic.py` (verbatim port) — TD Pro triangle/forming from OHLCV; verified (UNH/C/V/PG breakouts).
  - `options_flow.py` — once-daily Tradier Vol/OI + premium-skew snapshot, static scoring ported from `unusualActivity.ts`; honest `DAILY_VOLUME` labels. ⚠️ was `.gitignore`d (some `*flow*` rule) — force-added; watch for that on future flow files. Pass `market_cap` from universe data so tier floors apply (defaults to large-cap otherwise).
  - `ibkr_book.py` — holdings from local bridge `http://127.0.0.1:8765` (read endpoints need NO token). ⚠️ bridge `/positions` returns only qty+avgCost — `last`/`market_value`/`unrealized_pnl` are None; **enrich from the dossier's own quotes downstream**. ONDS hard-wired CC-INCOME (never trim/red).
  - `universe_scan.py` — added `scan_universe_union()` (momentum + `unusual_volume` + `rsi_oversold` via scanline); union ~355 vs 200, now catches NFLX (oversold). Note: union's momentum leg uses `limit_per` (120) not 200 — bump if you want full momentum coverage. AMD/QBTS/RKLB/UAMY correctly don't hit these screens (Reversal-Watch names).
  - `sf_gex.py` / `sf_market_weather.py` — StrikeForge dealer-positioning (gamma flip/walls/regime, Tradier chains) + VIX/VIX3M term-structure regime (yfinance). Live-tested.
  - `watchlist_ingest.py` — `parse_watchlist` + `cross_reference` for the nightly analyst email; `fetch_latest_watchlist_email()` stubbed (Gmail MCP interactive / IMAP headless).
- **NEXT = integration (sequential, shared files — do NOT fan out):** (1) wire modules into `generate.py` as stages; (2) **confluence + day-over-day migration** layer (the synthesis — namespace `persistence/tracker.py` per signal type first); (3) report sections (`builder.py` ctx-dict refactor → `template.html` panels → `summary_api.py` fields); (4) IBKR quote-enrichment; (5) the push (`PushNotification`) + durable scheduled task. Tradier MCP is now installed Claude-wide (interactive flow fallback; cron still uses the raw client).

### 2026-06-17 — integration step 1: 7 stages wired into `generate.py` ✅
All built modules now run as pipeline stages (each wrapped in `timer.stage()` / try-except, never breaks the pipeline). Data is captured in local vars but **not yet threaded into `build_report`/`summary_api`/persistence** — that's steps 2-3.
- **`[2b]` Broad Universe Scan** — `scan_universe_union(limit_per=120)` → `universe_rows` + `universe_mcap` map + `candidate_pool` (union tickers ∪ strategy survivors, junk-filtered). This pool feeds the new legs. **Deliberate choice:** existing funnel (`scanned_tickers`, enrichment, gold pick) left UNTOUCHED to avoid perturbing today's report; only the NEW legs consume the broad pool. Revisit in step 2/3 if we want enrichment to see small/mid caps too.
- **`[4c]` Market Weather** — `market_weather()` VIX/VIX3M term structure → `market_weather_data`.
- **`[6b]` Triangle Breakout** — `generate_triangles(candidate_pool[:40], max_results=10)` → `triangle_signals`. Capped at 40 (each is a 2y yfinance fetch — static-IP load).
- **`[7b]` Options Flow** — `fetch_options_flow(candidate_pool[:15], max_results=10, market_caps=universe_mcap)` → `options_flow_signals`. Added an optional `market_caps` param to `fetch_options_flow` so per-ticker tier floors apply.
- **`[7c]` IBKR Book** — `get_book()` + `overlay_book(positions, signals_by_ticker)` → `book_overlay`; `signals_by_ticker` built from triangle+flow legs.
- **`[13d]` GEX** — `gex_read()` on top 5 dossier picks → `gex_reads`.
- **`[11d]` Analyst Watchlist Overlay** — `fetch_latest_watchlist_email()` (None headless) → `ANALYST_WATCHLIST` env fallback → `parse_watchlist` → `cross_reference` vs {universe,triangle,flow,institutional,momentum} → `analyst_overlay`.
- **Validated:** `py_compile` clean + isolated smoke test of every entry point (market weather live=normal/contango; union=120 real candidates; cross-ref matches AMD; IBKR bridge=12 positions; triangle/flow/gex importable). Full in-pipeline dry-run NOT yet run (5+ min).
