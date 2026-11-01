# Super DD Template

One ticker, one document, one decision. This merges DoubleDownToWin's 10-section manual DD
(`docs/dd/sources/DoubleDownToWin_structure.md`) with the quant layer from the Watchlist Deep
Dive generator (`WATCHLIST_DEEP_DIVE_README.md`), then adds the pieces neither one has.

First worked example: TXN, 2026-11-01 (TraderMatrix blog, slug `txn-super-dd-texas-instruments`).

---

## Ground rules (apply to every section)

1. **Every number carries a source.** Put a `Source:` line under each block (his habit) or a
   source column in the figure. A number with no source is cut or marked `UNVERIFIED`.
2. **Dates are verified or absent.** Earnings, FOMC, CPI, deal deadlines: company IR, an SEC
   filing, or the Fed's own calendar. Aggregator dates are not enough. If it can't be
   verified, write "date not confirmed" and leave the date out.
3. **Unadjusted prices for levels, adjusted prices for returns.** yfinance `history()` is
   dividend-adjusted by default; use `auto_adjust=False` for any level a reader will place an
   order against. Check whether the last session was an ex-dividend date before calling a
   move a "selloff."
4. **Re-pull, don't inherit.** Numbers from a prior debate, dossier, or memory get re-pulled
   on the day of writing. When the re-pull disagrees, say which one you used and why.
5. **Opinion is labeled.** Sections 1 to 11 are evidence. Sections 12 to 15 are the call.
6. **Voice:** VOICE.md applies. No em/en dashes, no markdown tables in Substack (images
   instead; the TraderMatrix blog renders GFM tables but images still read better on a phone).

---

## Section order

Each section: the question it answers, the required fields, and where each field comes from.
Source keys: **YF** yfinance, **TDP** TDPro/TraderMatrix MCP (`mcp__claude_ai_TDPro__*`),
**SEC** EDGAR (`mcp__claude_ai_Trading__get_sec_filings` for the index, then fetch the
document with a `User-Agent` header), **IR** company investor relations, **WEB** web search
or fetch (name the outlet).

### 0. The pitch (top of post)
**Question:** in two sentences, what is this and why am I looking at it today?
- One-line pitch: "${COMPANY} (${TICKER}) is a ${what}. ${why now}." (his format)
- Score /10, size in R, and the one-word action (BUY ON TRIGGER / WAIT / SKIP), up front
- Price and date of the data (YF)
- Origin story if one exists (VOICE.md "life as alt-data")

### 1. Business and management
**Question:** what does it sell, to whom, and who is steering?
- Segments with revenue and op profit (SEC 10-Q segment note)
- End markets and their growth rates (earnings call transcript, WEB; quote the speaker)
- CEO and CFO, named from the filing signature block or press release (SEC/IR). Bios only
  with a source.
- Employees, market cap (YF)

### 2. The numbers
**Question:** is the business getting better or worse, and how fast?
- Latest quarter vs year-ago: revenue, gross margin, op profit, EPS (SEC 8-K Ex.99)
- TTM operating cash flow, capex, free cash flow (SEC 8-K Ex.99)
- Guidance range for next quarter (SEC 8-K Ex.99)
- Balance sheet: cash + short-term investments, total debt, current ratio (SEC 10-Q, YF)
- Inventory and days of inventory (SEC 10-Q MD&A)
- Dividend, payout ratio, buyback pace (SEC, YF). Check if buybacks have slowed and why.
- Earnings surprise history, last 4 to 8 quarters (YF `earnings_dates`)
- Composite scores 0-100: value, growth, quality, sentiment (Deep Dive spec section 4), plus
  TDPro quality score (`get_ticker_snapshot`)

### 3. Filing read (10-Q / 10-K / 8-K / S-series / 424B)
**Question:** what does the company say in writing that the headlines missed?
- Pull the filing index for the last 3 to 6 months (SEC). Read every 8-K item code, every
  424B5/FWP (debt or equity raise), every S-4 (merger).
- From the 10-Q: Item 1A changes (or "incorporated by reference"), subsequent events,
  acquisitions, credit facilities, legal proceedings, segment shifts
- Capital allocation outlook (capex range, CHIPS or other subsidies)
- Write down anything the bull/bear debate or the screen did not know. This section exists
  because it catches things (TXN: a pending $7.5B acquisition and $2B of new notes).

### 4. News, last 6 months
**Question:** what happened, in order, and did price lead or follow?
- `[event, date] + 2-3 line takeaway + Source` (his format)
- Price reaction the next session for each event (YF). News follows price: note when the
  move came before the story.
- TDP `get_ticker_news` for the catalyst filter; WEB for depth

### 5. Growth drivers
**Question:** what has to keep going right?
- Each driver with a number (segment growth, share of revenue, pricing, new capacity)
- Source each one

### 6. Risks
**Question:** what breaks the thesis, and which of those are dated?
- Market/cyclical, execution/financing, regulatory/geopolitical, concentration
- Each with a source and, where possible, a date it could hit
- Pending deal risk: spread between target price and deal price (YF), regulator status (WEB)

### 7. Competition and correlation
**Question:** who does it trade with, and who does it lose to?
- Peer table: fwd P/E, op margin, revenue growth, YTD (YF)
- Daily-return correlation 63d and 126d to peers, sector ETF, SPY, and any name with its own
  binary event this month (YF)
- Beta to SPY and to the sector ETF (YF)
- Where it wins vs each competitor, where it loses (WEB, filings)
- Peer catalyst dates (verified only): a 0.9-correlated peer's earnings is this name's event

### 8. Sentiment and positioning (people)
**Question:** what are the Street, insiders, and Congress doing?
- Analyst count, consensus, mean/median/low/high target (YF); last 30 days of rating and
  target changes (YF `upgrades_downgrades`)
- Insider transactions, 21 days and 6 months: name, title, code (P vs S vs S+OE), value,
  % of stake (TDP `get_insider_trades` with `direction: all`; cross-check SEC Form 4/144)
- Politician trades (TDP `get_politician_trades_by_ticker`)
- Retail chatter (Stocktwits MCP, named handles if quoting)

### 9. Options and flow (dealers and size)
**Question:** where are the walls, is premium rich or cheap, and is size moving?
- Gamma regime, flip level, dominant strike, call walls, put walls (TDP `get_gex_ticker`,
  `get_apex_levels`). If two models disagree on the flip, print both.
- Expected move ladder 1d/1w/1m/6w with hold rates (TDP `get_expected_move`)
- IV rank (TDP `get_iv_rank`), HV30 and its 1-year range (YF), implied vs realized
- Unusual options activity, last session (TDP `get_unusual_activity`,
  `timeFrame: todayOrLastSession`)
- Dark pool block flow 5d and 30d (TDP `get_dark_pool`). Check `failed` and `truncated`.
  Zero prints on a mega-cap is a coverage question, not a signal.
- Short interest, days to cover, daily short ratio (TDP `get_short_interest`)
- Option chain quotes for the proposed structure, bid/ask/mid/OI (YF `option_chain`)

### 10. Chart and technicals
**Question:** where is price in its own structure?
- Chart image with dealer levels:
  `node .claude/skills/stock-recap/scripts/render_chart.mjs TICKER --out DIR --days 300`.
  Read the PNG before using it.
- EMA 8/21/34/55/89 stack, SMA 20/50/100/200, % over 200-day (YF, unadjusted)
- RSI(14), MACD, ADX(14) with +DI/-DI (ADX has no direction; say which DI leads)
- ATR(14) and ATR(20); pivots; Keltner; Fib on the 52-week range (YF)
- 52-week high/low with dates, 20-day high/low, trend structure (HH/HL or range)
- Is it extended, ranging, or breaking a falling trendline? (his #1 setup)
- Levels map figure: every level, what it is, and its source

### 11. Sector and macro
**Question:** is the tide in or out?
- Benchmark table 1w/1m/3m/6m/YTD/1y for the ticker, sector ETF, SPY, QQQ (YF)
- Macro dates that matter this month, verified (Fed calendar, BLS)
- Market regime (TDP `get_market_health`, `get_macro_regime`)

### 12. Valuation
**Question:** what am I paying, against itself and against peers?
- Market cap, trailing and forward P/E, EV/EBITDA, P/S, FCF yield, dividend yield (YF)
- Graham / Lynch / analyst blend and the valuation gap (Deep Dive spec section 3)
- Ownership split institutional/insider (YF)

### 13. Steelman: bull vs bear
**Question:** what is the best honest case on each side?
- Three to five points each, the strongest version, with numbers
- What each side concedes (if a multi-agent debate was run, cite where scores moved)

### 14. What would make me wrong
**Question:** at what price or event do I stop believing this?
- Price invalidation level(s) with reason
- Event invalidation (guide cut, deal blocked, peer print)
- Thesis-break vs trade-break: the trade can stop out while the thesis survives. Say which.

### 15. Catalyst calendar
**Question:** what is dated between now and the expiry I'm buying?
- Only verified dates, each with its source. Unverified ones listed without a date.
- Company: earnings, dividend dates, investor/capital calls, deal deadlines, note settlements
- Peers with correlation > 0.7, plus any name with its own binary event (NVDA etc.)
- Macro: FOMC, CPI, opex

### 16. Trade plan
**Question:** exactly what do I do, and how big?
- Score /10, conviction, and size in R (and what sleeve it shares risk with)
- Trigger(s): price + condition (limit fill vs daily close). No-trade zone stated.
- Stop: level, close vs intraday, distance in ATR (flag stops under 1 ATR)
- Targets: T1, T2 with R multiple from the trigger
- Options expression: structure, expiry, strikes, live bid/ask/mid, debit, max value,
  breakeven, R:R on the debit. Expiry must clear every dated catalyst in section 15.
- Wheeler alternative: the CSP strike, premium, effective basis, and whether it fits the
  current list's rules
- Exit triggers that are not price (thesis break from section 14)

### 17. Closing
- What I might have missed; invite readers to say so (his close)
- Sign-off `~ Michael`, then one line: not financial advice
- Source list with raw URLs

---

## Comparison note: what was kept, cut, and added

**Kept from DoubleDownToWin:** the narrative order (business, news, drivers, risks,
competition, sentiment, chart, sector, valuation, plan), the one-line pitch, `Source:` under
every block, management named, a real competition section, opinions labeled as opinions, and
the closing invitation to say what he missed. His action plan (entry, allocation cap, hold
period, stop, exit triggers, take profit) is the skeleton of section 16.

**Cut from DoubleDownToWin:** LinkedIn-style bio padding (a bio stays only if it changes the
read), the emoji numerals (VOICE.md allows sparse emoji as markers, not a numbered list of
them), and stop/allocation expressed as a % of portfolio in place of a level. Stops here are
prices and sizes are in R.

**Kept from the Deep Dive generator:** the full indicator set (EMA stack, SMAs, RSI, MACD,
ADX, ATR, pivots, Fib, Keltner, HV, IV rank), the Graham/Lynch/analyst valuation blend, the
0-100 composite scores, and its narrative beats (Core Thesis, Bull, Bear, Technicals,
Playbook, Verdict) which map to sections 0, 13, 10, 16.

**Cut from the Deep Dive generator:** the 6-month price window as the 52-week source (it
mislabels a 6-month range as 52-week; use a real 252-session window), the front-month-only IV
read (use the expected-move ladder and the expiry you're actually trading), and the LLM
"catchy title + price target" one-shot. Here the price target is the plan's T1/T2, derived
from levels, not a narrative number.

**Added (neither source has it):** insider transactions with transaction codes, options
positioning and gamma walls, dark pool, short interest, politician trades, a dedicated
filing read, a verified-dates-only catalyst calendar, peer correlation and a shared-risk
sleeve, a bull/bear steelman, "what would make me wrong" with invalidation levels, a no-trade
zone, R-based sizing, an options expression priced from the live chain, and the wheeler's CSP
alternative.

**Why:** his structure is strong on story and weak on positioning; the generator is strong on
indicators and blind to filings, insiders, and dates. A wheeler or swing trader needs both,
plus the two questions that actually decide a trade: where am I wrong, and what's dated
before my expiry.
