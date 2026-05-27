# Watchlist Deep Dive — Report Spec

What goes into one deep-dive report and how each number is derived, so the
same artifact can be recreated outside this repo. The GitHub Actions
plumbing is just a thin wrapper around `dossier/watchlist_dive.py` — the
report is the thing.

## Inputs (per ticker)

All pulled via `yfinance.Ticker(symbol)`.

### Price history
- `Ticker.history(period="6mo")` → daily OHLCV DataFrame. Everything
  technical is computed off the `Close`/`High`/`Low`/`Volume` columns of
  this frame. If it comes back empty, the ticker is skipped.

### Fundamentals / profile (`Ticker.info`)
Used fields, grouped by what they feed:

| Group | `info` keys |
|---|---|
| Profile | `longName`, `shortName`, `longBusinessSummary`, `website`, `fullTimeEmployees`, `exchange`, `sector`, `industry`, `floatShares`, `marketCap`, `beta` |
| Valuation | `trailingPE`, `forwardPE`, `priceToSalesTrailing12Months`, `priceToBook`, `pegRatio`, `enterpriseToEbitda`, `enterpriseToRevenue`, `freeCashflow` (→ P/FCF = `marketCap / freeCashflow`) |
| Growth | `revenueGrowth`, `earningsGrowth`, `earningsQuarterlyGrowth`, `revenuePerShare` |
| Profitability | `grossMargins`, `operatingMargins`, `profitMargins`, `returnOnEquity`, `returnOnAssets` |
| Health | `currentRatio`, `debtToEquity`, `totalDebt`, `totalCash`, `operatingCashflow` |
| Dividends | `dividendRate`, `dividendYield`, `payoutRatio`, `exDividendDate` |
| Analyst | `targetLowPrice`, `targetMedianPrice`, `targetHighPrice`, `targetMeanPrice`, `recommendationKey`, `numberOfAnalystOpinions` |

Dividend yield gotcha: `yfinance` sometimes returns it as a decimal
(0.0091) and sometimes as a percent (0.91). The script computes
`dividendRate / price * 100` when possible and only falls back to the
field, normalizing `<1 → ×100`.

### Options chain (front-month only)
- `Ticker.options[0]` → nearest expiry string.
- `Ticker.option_chain(expiry).calls` / `.puts` → DataFrames with
  `strike` and `impliedVolatility` columns.

Derived:
- **ATM IV** = strike-distance-weighted average IV of the 5 calls closest
  to spot. Weight per strike `K` = `1 / (1 + |K − spot| / spot)`.
- **IV Rank** = `(atm_iv − min_iv) / (max_iv − min_iv) × 100` over all
  IVs in calls+puts.
- **IV Percentile** = share of chain IVs `≤` ATM IV.

### TradingView consensus
- `tradingview_ta.TA_Handler` (via the shared
  `_tradingview_summary(symbol, exchange)` helper) → string like `BUY`,
  `STRONG_BUY`, `NEUTRAL`. Stored as `tv_rec`.

### Optional: VoPR options scanner
If a sibling `VoPR/` repo is on `sys.path`, `scanner.run_auto_scan(symbol,
min_dte=14, max_dte=50, top_n=2)` is called and the first result
contributes: VRP ratio, ATM IV (from chain), realized vol, expected move
(lower/upper), spot, expiry, DTE, Keltner band, and a `top_strikes` table
(strike, delta, theta, mid). Missing repo → silently skipped.

## Computed indicators

All on the 6-month daily series.

### Moving averages
- **EMAs**: 8, 21, 34, 55, 89.
- **SMAs**: 20, 50, 100, 200.
- **EMA Stack label** (off the last bar):
  - `e8 > e21 > e34 > e55 > e89` → `FULL BULLISH`
  - `e8 > e21 > e34` (but not full) → `PARTIAL BULLISH`
  - `e89 > e55 > e34 > e21 > e8` → `FULL BEARISH`
  - otherwise → `TANGLED` (or `UNKNOWN` if any are NaN).
- **Trend timeframes** (3 arrows in the report):
  - Short: EMA8 vs EMA21
  - Mid: EMA21 vs SMA50
  - Long: SMA50 vs SMA200
- **Trend / Crossover** strings: `Bullish` if `SMA50 > SMA200` (label
  `Golden Cross`), else `Bearish` / `Death Cross`.

### Momentum / oscillators
- **RSI(14)**, **MACD**(12, 26, 9) — line, signal, histogram.
- **Stochastic %K(14) / %D(3 SMA of %K)** computed inline.
- **ADX(14)**: simplified (`+DM`/`−DM` from `high.diff()`/`-low.diff()`,
  normalized by 14-period ATR, then `DX` smoothed 14).

### Volatility
- **ATR(14)** and **ATR(20)** = mean of true range
  (`max(H−L, |H−Cprev|, |L−Cprev|)`).
- **HV(30)**, annualized = `stdev(log returns, 30) × sqrt(252) × 100`.
- **IV / IV Rank / IV Percentile** (see Inputs).

### Levels
- **Pivot Points** (classic floor-trader, off the **previous** day's H/L/C):
  - `PP = (H + L + C) / 3`
  - `R1 = 2·PP − L`, `S1 = 2·PP − H`
  - `R2 = PP + (H − L)`, `S2 = PP − (H − L)`
- **Fibonacci retracements** of the 6-month range
  (`high.max()` → `low.min()`): 0.236, 0.382, 0.500, 0.618.
- **Keltner Channels**: mid = SMA20, upper/lower = `mid ± 2·ATR20`.
- **52-week range + position %**: `(price − low) / (high − low) × 100`
  using the full 6-month frame (effectively the displayed window's high/low).

### Volume
- **Relative Volume** = `today_volume / SMA20(volume)`.

### Valuation overlay
- `dossier.data_sources.ticker_enrichment._intrinsic_value(info, price)`
  returns `{status, gap_pct, target_price}` — a fair-value triple the
  report shows as "Valuation: …".

## Composite scores (0–100)

All clamped to `[0, 100]`, integer rounded, `None` if no inputs.

```
value_score   = mean of available terms:
                  max(0, 100 − trailingPE × 2)        # if 0 < PE < 100
                  max(0, 100 − priceToBook × 10)      # if 0 < PB < 50
                  max(0, 100 − pegRatio × 20)         # if 0 < PEG < 10

growth_score  = mean of available terms:
                  clamp(50 + revenueGrowth × 200, 0, 100)
                  clamp(50 + earningsGrowth × 100, 0, 100)

quality_score = mean of available terms (each only if > 0):
                  min(100, grossMargins × 120)
                  min(100, operatingMargins × 200)
                  min(100, returnOnEquity × 200)

sentiment_score = recommendationKey → {STRONG_BUY:90, BUY:75, HOLD:50,
                                       SELL:25, STRONG_SELL:10}
```

Render bands in the UI: `≥65` green, `40–64` amber, `<40` red, `None` "—".

## The narrative (Gemini)

`google-genai` client called with the prompt below. The model is read
from `dossier.config.AI_MODEL` (currently a Gemini model id). Without
`GEMINI_API_KEY` the script writes a deterministic fallback markdown
table instead — useful as the baseline structure to mimic.

### Prompt template
```
You are Sam the Quant Ghost — a sharp, witty quantitative analyst who
writes deep-dive stock reports that retail traders love. Write a FULL
deep-dive report for {TICKER} using the data below. Use this exact
structure:

## [{TICKER}] Deep Dive: [Create a catchy thesis title]
**Date:** {date}
**Price:** ~${price} | **Verdict:** [Your verdict]

[1-2 sentence hook]

### The Core Thesis
[What the market sees vs reality. 2-3 paragraphs.]

### 📊 The Numbers You Need
[Revenue, margins, growth rates. Use the fundamentals data.]

### 🚀 The Bull Case
[3-4 catalysts with specifics]

### ⚠️ The Bear Case: Risks
[2-3 real risks]

### 📉 The Technicals
[EMAs, RSI, support/resistance, pivots]

### 📝 Trading Playbook
**Scenario A — The Breakout (Bullish):**
**Scenario B — The Dip Buy (Preferred):**
**Scenario C — Trend Failure (Hedge):**

### 🏁 Final Verdict
[One-liner + price target]

---
DATA:
- Price: $..., Change: ...%
- Market Cap, Beta, 52W Range, Sector, Industry
- Revenue Growth, Profit Margin, P/E, Forward P/E
- EMA Stack + EMA 8/21/34, SMA 50/200
- Trend, Crossover, RSI(14), ADX
- Pivots R2/R1/PP/S1/S2, ATR, Rel Vol
- Analyst Target, TradingView rec
- Valuation status/gap/target
```

The full computed data dict is interpolated as plain text — the model
isn't given JSON, just a labeled list. Sign-off line is enforced:
`— Ghost out.`.

## Output artifacts

Written to `docs/ticker/{TICKER}/`:

### `deep_dive.md`
The Gemini narrative verbatim (or fallback template). This is the
canonical text of the report. The fallback structure when the AI call
fails is:

```
## [TICKER] Deep Dive
**Date:** ... | **Price:** $X (±Y%)

### Market Snapshot   (table: cap, sector, beta, 52w, analyst target, TV)
### Technicals        (EMA stack, trend, EMAs, SMAs, RSI, ADX, pivots, ATR, RVol)
### Valuation         (status, gap %, target)
### Fundamentals      (rev growth, profit margin, P/E, fwd P/E)
```

### `deep_dive.json`
The complete computed dataset (~80 keys) — every input and derived field
referenced above. This is the "API-shaped" version of the report; consume
this if you want to render your own UI. Key groups:

- Quote: `date`, `price`, `change_pct`, `market_cap`, `beta`, `range_52w`,
  `w52_low/high/pos`, `sector`, `industry`
- Trend: `ema_8/21/34`, `sma_20/50/100/200`, `ema_stack`, `trend`,
  `crossover`, `trend_short/med/long`
- Momentum: `rsi`, `adx`, `stoch_k/d`, `macd`, `macd_signal`, `macd_hist`
- Volatility: `atr`, `rel_vol`, `iv`, `hv`, `iv_rank`, `iv_percentile`
- Levels: `pivot`, `r1/r2/s1/s2`, `fib_236/382/500/618`,
  `kelt_upper/mid/lower`
- Valuation/sentiment: `analyst_target`, `tv_rec`, `val_status`,
  `val_gap`, `val_target`, `pe`, `fwd_pe`, `ps_ratio`, `pb_ratio`,
  `peg_ratio`, `ev_ebitda`, `ev_revenue`, `price_to_fcf`
- Growth/profitability: `rev_growth`, `earnings_growth`,
  `earnings_q_growth`, `rev_per_share`, `gross_margin`,
  `operating_margin`, `net_margin`, `roe`, `roa`
- Health: `current_ratio`, `debt_equity`, `total_debt`, `total_cash`,
  `fcf`, `operating_cf`
- Dividends: `div_yield`, `div_rate`, `payout_ratio`, `ex_div_date`
- Analyst targets: `target_low/median/high`, `rec_key`, `num_analysts`
- Scores: `value_score`, `growth_score`, `quality_score`,
  `sentiment_score`
- Profile: `company_name`, `description` (≤3 sentences from
  `longBusinessSummary`), `website`, `employees`, `exchange`,
  `float_shares`
- Optional: `vopr` block (see Inputs)

### `deep_dive.html`
Single self-contained styled page. Two "instrument" sections wrap the
narrative:

1. **Header** — `{TICKER} DEEP.DIVE`, sector·industry·date, price + %.
2. **Narrative block** — markdown body rendered via an inline regex
   converter (headings, **bold**, *italic*, unordered/ordered lists,
   `---` → `<hr>`, pipe rows → `<table>`). No real markdown parser, no JS.
3. **Technical Gearbox** (cyan border):
   - Row of vol cards: IV, HV30, IV Rank, IV Percentile.
   - Trend panel: three arrows (short/mid/long) + EMA Stack label +
     TradingView rec + crossover.
   - Moving Averages panel: SMA20/50/100/200 with `%` distance from
     price, plus EMA 8/21/34/55/89.
   - Oscillators row: RSI(14) (color-banded ≤30/≥70), Stoch %K/%D,
     MACD hist, ADX.
   - 52-Week range bar with current-position dot.
   - Fibonacci panel + Keltner/Pivots panel (R2…S2 line).
   - Optional VoPR Edge Scanner panel with VRP, ATM IV, expected move,
     DTE, and the top-strikes table.
4. **Fundamental Dashboard** (amber border):
   - Profile cards (company, market cap, employees, exchange) + summary
     description + website.
   - **Scores Overview** — 4 large numeric cards (Value, Growth, Quality,
     Sentiment), banded by the thresholds above.
   - Valuation grid: P/E, Fwd P/E, P/S, P/B, EV/EBITDA, PEG + sub-line
     for EV/Revenue and P/FCF.
   - Growth + Profitability side-by-side (rev growth, EPS growth, qtr
     EPS growth, rev/share / gross, op, net margin, ROE, ROA, beta).
   - Financial Health grid (current ratio, D/E, debt, cash, FCF, op CF).
   - Dividends + Analyst Estimates side-by-side, including a target
     low→high bar with current-price dot.

Styling: dark terminal aesthetic, `Share Tech Mono` + `JetBrains Mono`,
all CSS inlined, no runtime JS beyond a Google Analytics snippet. Color
tokens: `#00ff41` positive, `#ff3e3e` negative, `#ffb000` neutral/warn,
`#00f3ff` accent.

## Recreating the report only (no GH Actions)

If you just want the artifacts on your machine:

```bash
pip install yfinance pandas numpy httpx feedparser jinja2 \
            tradingview-ta google-genai python-dotenv
export GEMINI_API_KEY=...                # optional; omit for fallback md
python -m dossier.watchlist_dive AAPL    # one or more symbols
# → docs/ticker/AAPL/deep_dive.{md,json,html}
```

Open the `.html` file directly. The whole report is offline-renderable
after the run — fonts load from Google, everything else is inline.

## Swapping the LLM

`_gemini_deep_dive(ticker, data)` is the only model-coupled function.
To swap providers:
1. Replace the `google.genai.Client` construction with the target SDK.
2. Keep the prompt verbatim — the section headings are what drive the
   downstream HTML markdown shim.
3. Keep the failure mode: return `""` so the deterministic fallback
   template kicks in.

## Reproduction gotchas

- **`yfinance.Ticker.info` is unstable.** Field availability and units
  drift across releases (the dividend yield issue above is the loudest
  example). Treat every `info.get(...)` as nullable and normalize at the
  edge.
- **6-month window is the design constant.** Stretching it changes
  SMA200 (won't have enough bars), the 52w range labels (misleading),
  and Fib levels (range basis differs). Either keep 6mo or audit every
  consumer.
- **Pivots use the previous day's H/L/C, not the current day's.** That's
  the textbook definition; easy to get wrong by reading `iloc[-1]`.
- **The Stochastic uses a single-bar snapshot for %K and a rolling-mean
  series for %D.** Keep that asymmetry if you port it; otherwise the
  numbers won't match.
- **Composite scores deliberately allow partial inputs.** Missing
  `pegRatio` shouldn't null the value score; it just averages over what
  exists. Replicate this or your scores will be sparser than the
  reference.
