---
name: stock-recap
description: >-
  Daily market recap + convergence-ranked stock shortlist for TraderDaddy Pro.
  Runs ALL screeners at default settings, pulls the biggest options flows / smart
  money, new CBOE option listings, and hedge-fund (13F) activity, then finds the
  short list of names that multiple independent sources agree on — with technicals.
  Use when the user asks to "find good stocks", wants a "market recap", "what's
  flowing", "what are the funds doing", "run the screeners", "any setups", or
  "what should I be looking at" for trading ideas.
---

# Stock Recap — convergence-ranked picks

This skill produces a market recap and a **short list of stocks the data agrees on**,
each with technicals. It pulls four independent legs and ranks names by how many of
them point at the same ticker (equal-blend convergence):

1. **Screeners** — all 10 TraderDaddy Pro screeners at their default settings
   (Momentum Pullback, Gamma Scan, Coiled Springs, Daily Cuts, CSP Wheel, LEAPS,
   Leveraged, Small-Cap, Volatility Surge, Bullish Pullback). The two
   momentum-chase lists (**Leveraged**, **Volatility Surge**) are recorded for
   context but do **not** earn a convergence leg — they surface already-running
   names that aren't the pullback/reversal setups we rank for.
2. **Options flow** — the biggest premium / smart-money unusual activity today,
   including the `INSTITUTIONAL_ALPHA` tier and repeat-strike conviction.
3. **New CBOE option listings** — names that just became optionable.
4. **Hedge funds (13F)** — TickerTrace top buys/sells, **cross-fund convergence**
   (multiple funds into the same name), and divergences.

It also **renders candlestick charts** (from our own 90-day OHLC data) for the
top picks + reversal names and a **dedicated under-$100 section** so the list
isn't all $700+ mega-caps.

> **Mike's edge:** his best picks come from **Momentum Pullback names once they
> START reversing out** of the pullback. The **Reversal Watch** section flags
> pullback names whose stoch is **climbing out of oversold (StochK ~12–45)** with
> price **reclaiming the 21-EMA** and a bullish RSI zone / A-B grade — detected
> from the live read, **not** the screener's `stochCrossover` flag (which is
> ~always "No" because the screener surfaces names while still IN the pullback,
> before the cross prints — gating on it made this section fire ~never). It marks
> which of those already have bullish flow and fund buying behind them. Always
> call this out. Names tagged **🚀 extended** already ran (2-of-3 of: >8% over
> EMA21, RSI>78, big week/month/day move) — don't chase them.

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
   - The 2–4 **highest-conviction names** (most aligned legs, no conflict), with
     their key technicals, **what their chart shows**, and why they're interesting.
   - The **Reversal Watch** — any Momentum Pullback names turning up, especially
     ones with flow 🟢 and fund ✅ confirmation (his setup). Use the charts to
     confirm the turn is real.
   - The **💵 Under-$100** picks — Mike specifically wants accessible names, not
     just $700+ mega-caps. Always surface a few.
   - A one-line **flow/fund tone** read (net bullish vs bearish premium; what the
     funds are buying/selling; any notable cross-fund convergence).
   - **⚠️ Conflicts** — names where bullish sources disagree with bearish flow or
     fund selling (e.g. funds buying but options heavily bearish). Flag, don't bury.
   - New CBOE listings only if there's something worth noting.

5. Point Mike at the saved `report.md` for the full tables/charts, and mention the
   `raw/` JSON is there if he wants to dig in or backtest.

## Tuning (optional env vars)

- `RECAP_SHORTLIST=20` — shortlist size (default 15).
- `RECAP_MAX_PRICE=50` — cutoff for the under-$N affordable section (default 100).
- `RECAP_TIMEOUT_MS=90000` — per-request timeout (default 60s).
- `TD_API_URL` / `TD_NEW_API_URL` / `TICKERTRACE_API_URL` — override base URLs.
- `TD_API_KEY` (new dev API, `X-API-Key`) / `AGENT_API_KEY` (old Railway, `Bearer`)
  — override the keys; otherwise read from `.env_td_api` and `.env_agent_api`.

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
