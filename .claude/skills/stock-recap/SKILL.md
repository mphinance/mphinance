---
name: stock-recap
description: >-
  Daily/weekend market recap + convergence-ranked stock shortlist for TraderDaddy
  Pro. Runs ALL screeners, pulls the biggest options flows / smart money (today, or
  the trailing week on a closed market), new CBOE listings, hedge-fund (13F)
  activity, downtrend-breakout setups, GEX walls, and relative strength, then finds
  the names multiple independent sources agree on — with technicals + charts. Use
  when the user asks to "find good stocks", wants a "market recap", "what to watch
  this week", "what's flowing", "what are the funds doing", "run the screeners",
  "any setups / breakouts", or "what should I be looking at" for trading ideas.
---

# Stock Recap — convergence-ranked picks

This skill produces a market recap and a **short list of stocks the data agrees on**,
each with technicals. It pulls several independent legs and **quality-weight ranks**
names by how many of them point at the same ticker (convergence):

1. **Screeners** — all 10 TraderDaddy Pro screeners at their default settings
   (Momentum Pullback, Gamma Scan, Coiled Springs, Daily Cuts, CSP Wheel, LEAPS,
   Leveraged, Small-Cap, Volatility Surge, Bullish Pullback). The two
   momentum-chase lists (**Leveraged**, **Volatility Surge**) are recorded for
   context but do **not** earn a convergence leg — they surface already-running
   names that aren't the pullback/reversal setups we rank for.
2. **Options flow** — the biggest premium / smart-money unusual activity, including
   the `INSTITUTIONAL_ALPHA` tier and repeat-strike conviction. **Intraday it's
   today's flow; on a closed market it switches to the trailing week** (the biggest
   prints of the last ~5 sessions, not a recent slice — see notes).
3. **New CBOE option listings** — names that just became optionable.
4. **Hedge funds (13F)** — TickerTrace top buys/sells, **cross-fund convergence**
   (multiple funds into the same name), and divergences.
5. **Downtrend-breakout** (Mike's #1 setup) — a `dtb_break` leg from
   `scripts/detectors/downtrend.mjs`, which fits the descending resistance line of
   lower-highs from a major peak on **300-day OHLC** and fires only on a **fresh**
   break + reclaim (also a 🪤 spring / failed-breakdown flag).
6. **Relative strength vs SPY** — an `rs_leader` flag (leads SPY over 20d **and**
   60d). It's a **rank booster only**, deliberately excluded from the
   "multiple-independent-sources" gate (it's derived off the same price series).

Two more legs **enrich** the shortlist (they don't gate it): **GEX** (gamma walls +
flip — room-to-call-wall, above/below the dealer-gamma flip) and an **earnings
blackout** (names reporting within 7 days are flagged 📅 and rank-capped, so a fresh
long isn't surfaced into a print).

It also **renders candlestick charts** (90-day candles from our own OHLC data) for the
top picks + reversal + downtrend-breakout names and a **dedicated under-$100 section**
so the list isn't all $700+ mega-caps.

> **Mike's edges (call these out first):**
> - **🔻→🟢 Downtrend-Breakout** (his #1) — break + reclaim of a multi-month falling
>   trendline of lower-highs from a major peak (NKE ~5/20 is the template). Its own
>   report section; only **fresh** breaks (≤5 bars, still near the line) are
>   actionable — `extended`/`forming` tiers are backward-looking context, marked
>   not-actionable. Always render+read its chart before trusting it.
> - **🔄 Reversal Watch** — Momentum Pullback names **starting to reverse out**:
>   stoch climbing out of oversold (StochK ~12–45), price **reclaiming the 21-EMA**,
>   bullish RSI zone / A-B grade. Detected from the live read, **not** the screener's
>   `stochCrossover` flag (≈always "No" because the screener surfaces names while
>   still IN the pullback). The flag is **reconciled against the chart's fresh last
>   bar** — a name that printed a hard down day or sits below the 21-EMA is
>   suppressed (kills screener-lag false positives like a -6% knife mislabeled
>   "reversing"). Marks which turns already have flow 🟢 / fund ✅ behind them.
> - **💎 Smart-Money-Early** (forced to the top) — the dream join: a fresh
>   downtrend-break **and** funds accumulating on 13F **and** fresh bullish weekly
>   flow, with no earnings landmine. Often legitimately empty (rare setup) — the
>   empty-state is honest, not a bug.
>
> Names tagged **🚀 extended** already ran (2-of-3 of: >8% over EMA21, RSI>78, big
> week/month/day move) — don't chase them. Fresh breakouts/reversals are exempt.

## How to run it

1. Run the gather script from the repo root:

   ```bash
   node .claude/skills/stock-recap/scripts/gather.mjs
   ```

   It writes a timestamped folder under `.claude/skills/stock-recap/runs/<date_time>/`
   containing `report.md` (the full recap) and `raw/*.json` (every raw API pull,
   for backtesting or a deeper look). It also prints the report to stdout and a
   final JSON line with `{reportPath, rawDir, shortlist, health}`.

   - Takes ~30–90s (screeners are the slow part; they're cached 5 min server-side).
   - **Hybrid API wiring (two keys):**
     - **New dev API** (`api.traderdaddy.pro/api/v1`, `X-API-Key` from repo-root
       `.env_td_api`) serves **screeners + options flow** — richer payloads
       (`earningsDaysAway`, `perf3MPct`, real flow aggregates).
     - **Old Railway API** (`Bearer` from `.env_agent_api`) still serves
       **chart-data (charts), CBOE options-listings, and the ticker technicals
       enrich** — the new API doesn't expose those with the new key yet.
     - TickerTrace (13F) unchanged. Presents a browser User-Agent (the edge WAF
       403s the bare Node UA).

   The script auto-renders charts as part of the run (it shells out to the skill's
   Python venv — `.venv/bin/python scripts/render_chart.py`). No separate step.

2. **Read the generated `report.md`** (the path is in the script's final output).

3. **Open every chart PNG** listed in the report's **"📉 Charts rendered"**
   section with the Read tool and look at each one. The chart is 90-day candles +
   EMA 8/21/55 + SMA200 + volume + RSI. For each, judge: trend direction and
   strength, where price sits vs the fast EMAs (pullback to support vs extended),
   any structure (breakout, base, blow-off/exhaustion wick, lower-high rollover).
   The visual read often **overrides the indicator table** — e.g. a name can rank
   high on flow but the chart shows a parabolic blow-off you should not chase.

4. **Present a tight, plain-English recap to Mike** — don't just dump the file.
   Lead with what matters:
   - **💎 Smart-Money-Early** first if it's non-empty — that's the dream join.
   - Any **🔻→🟢 Downtrend-Breakout** names (his #1), but only the **fresh** ones,
     and only after you've read the chart to confirm the line break is real.
   - The 2–4 **highest-conviction convergence names** (most aligned independent
     legs, no conflict), with their key technicals, **what their chart shows**, GEX
     posture (room to the call wall, above/below the gamma flip), and why.
   - The **🔄 Reversal Watch** — Momentum Pullback names turning up, especially with
     flow 🟢 and fund ✅. Use the charts to confirm the turn is real.
   - The **💵 Under-$100** picks — Mike wants accessible names. Remember small/mid
     caps mostly live here, in the backfill, and in Reversal Watch (they rarely get
     a flow/fund second leg), so treat them as single-signal ideas to confirm.
   - A one-line **flow/fund tone** read (net bullish vs bearish weekly premium; what
     the funds are buying/selling; any notable cross-fund convergence).
   - **⚠️ Conflicts** and **📅 earnings-this-week** names — flag, don't bury.
   - New CBOE listings only if there's something worth noting.

5. Point Mike at the saved `report.md` for the full tables/charts, and mention the
   `raw/` JSON is there if he wants to dig in or backtest.

## Tuning (optional env vars)

- `RECAP_SHORTLIST=20` — shortlist size (default 15).
- `RECAP_MAX_PRICE=50` — cutoff for the under-$N affordable section (default 100).
- `RECAP_TIMEOUT_MS=90000` — per-request timeout (default 60s).
- `RECAP_FLOW_WINDOW=5d` — flow window on a closed market (default `week`; the script
  uses `today` automatically while the market is open). Other values: `5d`/`7d`/`month`.
- `RECAP_GEX=0` — disable the GEX enrich/re-sort (default on).
- `TD_API_URL` / `TD_NEW_API_URL` / `TICKERTRACE_API_URL` — override base URLs.
- `TD_API_KEY` (new dev API, `X-API-Key`) / `AGENT_API_KEY` (old Railway, `Bearer`)
  — override the keys; otherwise read from `.env_td_api` and `.env_agent_api`.

Non-env constants worth knowing (top of `gather.mjs`): `OHLC_DAYS=300` (history for
the trendline detector; chart-data hard-caps ~350), `OHLC_MAX_NAMES=40` (detectors
run on the shortlist + reversal + pullback candidates, not the whole universe),
`EARNINGS_BLACKOUT_DAYS=7`, `RS_SHORT/RS_LONG=20/60`, and the weekly-flow thresholds
`FLOW_WEEKLY_MIN_SCORE=85` / `FLOW_WEEKLY_MIN_PREMIUM=250000`.

## Notes / gotchas

- **Weekend / closed-market runs are partial — by design, not failure.** Live
  options flow is intraday-only, so on a weekend/holiday the flow leg returns
  empty and the health table reads **"market closed — flow N/A"** (driven off the
  new API's `/market-stats` `marketOpen`). CBOE shows the last trading-day scan.
  A weekend run leans on **screeners + 13F**; the shortlist labels how many names
  are true 2+-leg convergence vs single-leg backfill so a thin list can't pretend
  to be 15 confirmed picks.
- **Convergence is directional and weighted.** Only bullish-aligned legs add to a
  name's score, and legs are **quality-weighted** (cross-fund / institutional-alpha
  flow = 3, A/B screener or normal flow / fund-buy = 2, CBOE = 0.5). A confirmed
  reversal gets a strong boost so a clean turn can outrank a weak multi-leg pair.
  Bearish flow or fund selling against a bullish name is a **conflict** (penalised,
  never agreement). Extended/already-run names are penalised too. Long-idea finder.
- **Weekly flow captures the biggest prints, not a recent slice.** The flow feed is
  time-ordered and ignores sort params, so on the weekly window we tighten thresholds
  (score≥85 / premium≥$250k) to collapse the qualifying set to a few hundred biggest
  prints that fully page; whole-week `bullish/bearishPremium` aggregates come off
  page 1. If a busy week exceeds the page budget, the per-ticker table degrades to a
  recent slice and the health row says so (the header totals stay whole-week).
- **Downtrend-breakout detector** (`scripts/detectors/downtrend.mjs`) runs on 300-day
  OHLC (`chart-data?days=300`, old API). It builds the descending resistance line
  from the convex hull of lower-highs off the major peak, gates on span/touches/
  decline, and only fires a `dtb_break` leg on a **fresh** close-through still near
  the line. On a broad-uptrend weekend it's often empty (most names' peak is recent,
  so there's no multi-month downtrend to break) — that's a legitimate empty-state.
- **GEX / earnings** are enrichers, not gates: GEX runs on the ranked shortlist only
  (per-symbol calls are pricey) as a bounded tie-breaker; earnings-blackout names are
  rank-capped (and the cap is re-applied after the GEX bump). A `gex_sample.json` is
  saved to `raw/` as a shape-drift tripwire.
- **"Small Cap Rockets" screener fails upstream every run** (vendor-side crash, hence
  9/10). Small/mid caps still come through the other pullback/squeeze/coiled screeners
  and surface in the Under-$100 + backfill + Reversal Watch sections.
- **Technicals enrichment:** names that arrive via flow/funds only (no technical
  screener) are back-filled from `/api/agent/ticker/:symbol` (RSI, ADX, EMA stack,
  call/put walls, expected move). Stochastic isn't available there, so the Stoch
  column shows `—` for those.
- **13F data is TickerTrace**, not TD Pro's `/api/institutional/*` (the agent key
  is scoped to `/api/agent/*` and can't reach it). If TickerTrace is down, the
  hedge-fund leg degrades gracefully and the rest still runs.
- Each run is a fresh point-in-time snapshot; nothing is overwritten. Old run
  folders are safe to delete (they're gitignored under `.claude/`).
- **Charts** are rendered from our own `/api/agent/ticker/:symbol/chart-data`
  (90d OHLC + indicators) — no TradingView scraping, no session cookies, no
  account risk, no third-party chart API. If the chart step fails, the data
  recap still completes; the health table shows the render status.
- **One-time setup** (already done on this machine): a Python venv lives at
  `.venv/` with `mplfinance` + `pandas`. If it's missing (fresh clone), recreate:
  `python3 -m venv .venv && .venv/bin/pip install mplfinance pandas`.
