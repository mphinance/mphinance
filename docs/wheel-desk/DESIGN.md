# The Wheel Desk — design (v0 draft for critique)

Goal: automate what wheelstrategy.substack.com sells for $39/mo (15 weekly CSP setups + management
plan + daily top-10), but with data backup nobody else has (TMPro screens, dealer gamma, TickerTrace
fund option legs + institutional flow) and an independent Claude grade on every setup, INCLUDING the
ones we'd pass on and why. Michael reviews; one button turns his reviewed list into a public
permalink + a Substack draft.

## Loop

1. **Nightly 7pm CT (20:00 ET) Sun–Thu** — disclaw cron in #mphinance channel.
   - `tools/wheel_desk/gather.mjs` runs every TMPro screener at DEFAULT settings (Railway `/api/screeners/{id}/run`).
   - Day focus: **Sun** = full CSP playbook (+ last week's TickerTrace institutional buying), **Mon–Wed** = daily CSP top
     (the competitor's "daily top 10"), **Thu** = gamma-scan / Friday-expiry pin read + CSP.
   - Enrich every CSP row: TickerTrace `/api/v1/options/{T}` (which funds hold/wrote puts/calls near our strike),
     `/institutional?period=weekly` membership, TMPro chart data (trend vs 21/50/200, 52w position), IV rank zone,
     OI floor, quote quality, earnings, sector/factor cluster.
   - Output: `data/wheel-desk/<date>/packet.json` (committed).
2. **Claude grades independently** (the cron session itself): per setup → verdict TAKE / WATCH / PASS, grade,
   `why` (≤2 sentences), `whyNot` (the risk that kills it), management plan (50% take-profit, roll rule, stop),
   assignment plan (CC strike idea). Grade ignores the screen's own score. Clusters: only the best of a
   correlated cluster can be TAKE. PASSes are KEPT with the reason. → `grades.json`.
3. **Publish to TMPro (user 8)**:
   - Watchlist `Desk 09-28 CSP` (category csp; `Desk 10-02 Gamma` Thu). Note per ticker (≤500 chars):
     `TAKE A- · Sell 16P 10/16 @0.78 · why … · risk … · holders: BLOX 18/19P spread`. Rotate: keep last 5 desk lists (12-list cap).
   - POST structured draft to TMPro (new superuser/owner route) keyed to the watchlist id → stored as
     `shared_artifacts` kind `wheel_desk_draft` (never publicly readable).
   - Discord summary in the cron thread with the watchlist link.
4. **Michael reviews in TMPro** — edits notes, deletes names, adds his own.
5. **Button (user 8 / superuser only) on that watchlist: "Publish desk → Substack draft"**:
   - Backend merges current list (his edits win) with the draft's structured setups, freezes ref prices,
     writes public `wheel_desk` artifact → permalink `/share/wheel_desk/<id>`; stable `/desk` → latest.
   - Enqueues `agent_runs` lens `substack-draft` (notes = shareId). disclaw poller claims it (outbound-pull, no
     inbound port — unchanged), opens a Discord thread, the session builds the draft in /home/mph/mphinance via
     `tools/push_substack.py`, replies with the draft URL.
6. **Public permalink page**: setup cards (strike, expiry, premium, cushion, collateral, PoP, IV rank), the
   Claude grade + Michael's note, "who's in these contracts" (fund legs), the PASS list with reasons,
   live "since published" move per name (like Wex's board), methodology + disclaimer, ref link.

## Open decisions for the panel
- D1 Reuse `agent_runs` for the button vs a separate queue.
- D2 New share kind `wheel_desk` vs extending `partner_watchlist` (Wex's) with partnerKey `mphinance`.
- D3 Drafts stored as shared_artifacts `wheel_desk_draft` vs a new table.
- D4 How much of the Substack draft is machine-written, given Michael's rule "automate around the writing, never the words".
- D5 Grading rubric + what makes PASS notes credible; how to use TickerTrace without overclaiming (fund legs are income-ETF
  hedges/spreads, not "smart money" bets).
- D6 Public track record: show per-name move since published? A scorecard? (compliance: performance claims)
- D7 Free vs paid split on Substack; what's on the free permalink.

---

# DECISIONS (2026-09-27, after 3-critic panel: engineering, trader, product)

- **D1 — Reuse `agent_runs`** for the button, with a new internal lens `substack-draft`: scope-less (no domain/target
  required), its own prompt template (no coding house rules; keeps "nobody watching" + "foreground only"), hidden from
  the admin launcher. The disclaw poller gets a per-lens working dir (`substack-draft` → /home/mph/mphinance, no worktree).
  The prompt stays tiny and points at `.claude/skills/wheel-desk/SKILL.md` so the drafting logic lives in mphinance.
- **D2 — New share kind `wheel_desk`**, not Wex's `partner_watchlist` (that one carries the partner-enumeration gate and a
  different shape). Copies its patterns: server-frozen ref prices, a public `/live` route keyed on share id only.
- **D3 — Drafts get their own table `wheel_desk_drafts`**, NOT `shared_artifacts`: `GET /api/share/:id` returns any kind
  unfiltered, so a draft row there would be public to anyone with the id.
- **D4 — Protect the writing.** The Substack draft auto-fills data blocks (setup figures, PASS list, the fixed management
  rules, assignment plans, permalink). Every prose slot is `[MICHAEL: ...]` with fuel bullets. No machine paragraphs.
- **D5 — Grading rubric** in `.claude/skills/wheel-desk/SKILL.md` (gates: cushion, chart, IV context, liquidity; hard
  PASS rules; one Selling per correlation cluster; fund legs described as income-ETF overlays, never "smart money").
- **D6 — Public record = arithmetic per name** (live cushion; at expiry "expired OTM" / "assigned at $X"). No aggregate
  win rate until ~50 expired setups AND a delta-implied baseline next to it.
- **D7 — Free/paid.** Permalink is free except strike/premium on Selling names beyond Michael's free picks, which are
  masked until expiry, then unlock as the receipt. Substack: tape + top picks + full PASS list free; the rest paid.
- **Public labels**: Selling / Watching / Passed (not TAKE/PASS). **Name**: The Wheel Desk. **Stable URL**: /wheel.
- **Watchlists**: created by the cron session via the TDPro MCP as user 8 (`Desk MM-DD CSP`), rotate oldest `Desk *`
  list BEFORE creating (12-list cap). Notes ≤500 chars; structured data lives in the draft, not the note.
- **Mon–Wed**: permalink + Discord only, no daily Substack post.

## Draft contract — `POST /api/agent/wheel-desk/drafts` (AGENT_API_KEY; owner = env WHEEL_DESK_OWNER_USER_ID=8)

```jsonc
{
  "watchlistId": 123,            // must belong to the owner, else 404
  "date": "2026-09-27", "mode": "sunday|daily|thursday",
  "title": "The Wheel Desk · week of Sep 28",
  "tape": ["SPY ...", "..."],    // ≤6 short fact bullets
  "setups": [{                   // ≤40
    "ticker": "CIFR", "verdict": "selling|watching|passed", "grade": "B+",
    "deskNote": "≤300 chars", "whyNot": "≤300 chars",
    "seededNote": "exact note text written to the watchlist (used to detect Michael's edits)",
    "contract": { "strike": 16, "expiry": "2026-10-16", "dte": 19, "premium": 0.78, "collateral": 1600,
                  "delta": -0.28, "pop": 72.8, "breakeven": 15.21, "cushionPct": -14.18, "rocWeekly": 1.81,
                  "annualized": 94.3, "iv": 93.9, "ivRank": 8.2, "ivRankZone": "cheap",
                  "quoteQuality": "firm", "supportOI": 3009 },
    "context": { "price": 17.73, "sector": "...", "trend": "downtrend", "vs50sma": -2.6, "vs200sma": -3.4,
                 "rangePos52w": 35, "atrPct": 8.5, "cluster": "APLD+CIFR+...", "alsoOn": ["cc-wheel"],
                 "earningsInWindow": false },
    "fundOptions": [{ "fund": "BLOX", "expiry": "2026-10-02", "text": "+5069 18P / -5069 19P" }],  // ≤6
    "fundOptionsNote": "≤200 chars",
    "institutional": { "dir": "buying", "weightDelta": 0.4, "fundCount": 3 } ,   // or null
    "management": "≤500 chars", "assignment": "≤300 chars"
  }],
  "gamma": [{ "ticker": "KHC", "price": 23.6, "topWall": "CALL 24.5 ...", "regime": "POSITIVE", "flip": 22.0, "note": "≤200" }], // ≤15
  "institutional": { "asOf": "2026-09-25", "note": "≤400", "buying": [{ "ticker": "MU", "name": "...", "weightDelta": 2.47, "fundCount": 10, "flags": [] }], "selling": [] }, // ≤15 / ≤10
  "methodology": "≤1500 chars"
}
```
Upsert on watchlistId. Response `{ ok, draftId }`.
