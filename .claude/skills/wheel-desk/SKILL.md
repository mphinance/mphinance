---
name: wheel-desk
description: >-
  The Wheel Desk: nightly (Sun-Thu 7pm CT) run of every TraderMatrix screen at defaults,
  an independent Claude grade on every cash-secured-put setup (rejects kept, with the
  reason), the persistent TMPro `Wheel Desk` list (grades as notes) whose live share link is
  the public permalink, plus a local Substack draft builder run on request. Use when the cron
  fires, when Michael says "run the desk", "wheel desk", "grade the CSP screen", "Sunday
  playbook", or "draft the desk" for the Substack post.
---

# The Wheel Desk

What wheelstrategy.substack.com sells for $39/mo, done automatically, with data they
don't have (dealer gamma, income-ETF option legs, fund flows) and a grade that is allowed
to say no. Design + decisions: `docs/wheel-desk/DESIGN.md`. Scripts: `tools/wheel_desk/`.

## Nightly run (cron, Sun-Thu 20:00 ET = 7pm CT)

Mode is picked from the Chicago weekday: **Sun = full playbook** (+ last week's fund
buying), **Mon-Wed = daily CSP**, **Thu = CSP + Friday gamma read**. Work in /home/mph/mphinance.

0. If `data/wheel-desk/<today CT>/watchlist.json` already exists, the desk already ran today
   (a manual run): post a one-line "already ran, list X" and stop. No duplicate lists.
1. `node tools/wheel_desk/gather.mjs` → `data/wheel-desk/<date>/packet.{json,md}`.
   Read the health line. If screeners < 10/12 or csp-wheel failed, say so in Discord and stop.
2. Read `packet.md`. **Render and LOOK at the charts** for every CSP name:
   `node .claude/skills/stock-recap/scripts/render_chart.mjs T1 T2 ... --out data/wheel-desk/<date>/charts --days 200`
   then Read the PNGs (tile them if many). The rubric below is useless without the chart.
3. Write `data/wheel-desk/<date>/grades.json` (schema below). Grade EVERY CSP row.
4. Verify every number/claim in `tape` against packet.json with jq. (2026-09-27: two
   tape claims were wrong on first draft: the gamma regime split and the IV-rank lookback.)
5. `node tools/wheel_desk/publish.mjs notes` → exact note strings.
6. TMPro watchlists via the TDPro MCP (acts as user 8). Two lists:
   - **`Wheel Desk`** (category `csp`): the ONE persistent list. Its live share link in TMPro is the public
     permalink, so never delete or rename it. Every night: `remove_from_watchlist` every ticker on it, then
     `add_to_watchlist` tonight's names in order Selling → Watching → Passed, with notes = the EXACT strings from step 5.
     If it doesn't exist yet, `create_watchlist` it once.
   - **`Desk MM-DD CSP`** (MM-DD = the NEXT trading day; Thu: `Desk MM-DD Gamma+CSP`): dated history, same names and notes.
     Before creating one, if you have 3+ `Desk MM-DD*` lists or would exceed 12 lists, `delete_watchlist` the OLDEST
     `Desk MM-DD*` list. Never delete any other list (never `Wheel Desk`).
   - Save `{"watchlistId":N,"name":...,"liveListId":M}` to `data/wheel-desk/<date>/watchlist.json`.
7. `node tools/wheel_desk/publish.mjs draft --watchlist-id N` → writes `draft.json` locally (the Substack builder reads it).
8. Commit: `git add -f data/wheel-desk/<date>/*.json data/wheel-desk/<date>/packet.md` (repo .gitignore has `*.json`;
   charts/ and raw/ stay out), commit, `git pull --rebase`, push.
9. Final message (Discord): mode, counts (selling/watching/passed), the Selling names with
   strike/expiry/premium one-liners, the best PASS reason, the list name, and:
   "Review it in TMPro (Watchlists → Desk MM-DD). Edit any note, delete any name, then hit
   **Publish + Draft to Substack**."

Mon-Wed: no Substack post is expected; the permalink + Discord is the product.

## Grading rubric (independent of the screen's own score)

Four gates, each graded, then a letter (A-F):
- **Cushion (30%)**: breakeven vs the REAL floor (60-day low, OI support lines on the chart).
  A strike 20% above the 60-day low has less cushion than its % OTM suggests.
- **Chart health (30%)**: trend vs 50/200, lower highs/lower lows, ADX with direction. A put on
  an active waterfall is a limit order to buy a falling knife.
- **IV context (20%)**: IV rank vs its own history. Low rank on a violent name = you're paid least
  where it gaps most. Say which lookback (`ivRankSource`: cboe = 52-week, self_tracked ≈ 3 months, see `ivRankSample`).
  IV rank ~100 on a quiet chart = something is being priced; find out or pass.
- **Liquidity (20%)**: quote quality, option volume, OI at the strike. Wide + thin = you may not get out.

**Hard PASS** (any one): earnings inside expiry; active waterfall; wide quotes AND OI < ~200;
dead range gaming the math; numbers that look like artifacts.
**Clusters**: names in the same `cluster` (60-day return correlation, complete linkage ≥ 0.7)
are ONE bet. Only the best chart+cushion in a cluster can be **selling**; one more may be
**watching** as the alternate; the rest are **passed** "correlated to X".
**Extended names** (big 60-day run, far over the 21 EMA) → watching with a pullback plan, never selling.
**Michael's own positions** (ONDS wheel etc., see memory): say so; it's a sizing decision, not a fresh idea.
Don't force a count. One Selling on a bad night is honest.

**Fund options (TickerTrace)** are income-ETF overlays (BLOX, ULTI, YieldMax...): spreads and
collars run for yield. Describe them as that: "income ETF running a put spread near X". Never
"smart money", never a directional read.
**Institutional (Sunday)**: read `fundCount`, not blended weight: one concentrated new fund (e.g.
Roundhill DRAM) moves the weight. Flag `single-fund`, `non-US ticker`, name/ticker mismatches
(TickerTrace labels STX "Strike Energy"). Put junk tickers in `institutional.exclude`.
**Thursday gamma**: a wall between spot and strike is a management note (pinning), not a grade change.
**Dates**: no earnings/macro dates in any text unless verified (feedback_no_unverified_dates).
**Voice**: no em dashes, plain words, one grade per name. Labels: Selling / Watching / Passed.

### grades.json

```json
{
 "tape": ["≤6 fact bullets, each verified against packet.json"],
 "setups": [{"ticker":"MARA","verdict":"selling|watching|passed","grade":"B",
   "deskNote":"why it's interesting (≤300)","whyNot":"the risk that kills it (≤300)",
   "fundOptionsNote":"optional ≤200","management":"optional, default standing rules",
   "assignment":"optional, default basis + 0.30Δ call"}],
 "institutional": {"note":"Sunday only ≤400","exclude":["CXMT"]},
 "gamma": [{"ticker":"KHC","note":"Thursday only ≤200"}]
}
```

## Draft to Substack (only when Michael asks: "draft the desk", "Sunday post", etc.)

Everything runs on this box. TMPro is only the live list (TDPro MCP) plus its share link.

1. `node tools/wheel_desk/build_post.mjs --date <desk date> [--pink]` → `~/.mph-substack-cache/<date>_wheel-desk/`
   with post.md, a mascot hero (pink_* editions in October), and PNG setup cards. It reads that night's draft.json.
   Before building, pull Michael's CURRENT notes from the `Wheel Desk` list (TDPro MCP `list_watchlists`): a note that
   differs from the seeded one is his, and it replaces the `[MICHAEL]` slot for that name. A ticker he removed drops out.
   (That merge is manual for now: edit post.md.)
2. The permalink line uses the live share URL in `data/wheel-desk/live-share.json` (`{"url": "..."}`). Michael creates
   it once in TMPro: Watchlists → Wheel Desk → Share → Live link. If the file is missing, the builder omits the line.
3. Never fill a `[MICHAEL: ...]` slot with prose (protect the writing). Fix formatting and verify numbers only.
4. `python3 tools/voice_lint.py post.md`, then `python3 tools/push_substack.py <workspace>/post.md` (DRAFT only).
5. Report the draft URL and the manual steps: [MICHAEL] slots, paywall position, discovery tags.
