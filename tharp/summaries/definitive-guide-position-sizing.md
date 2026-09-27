# Van Tharp's Definitive Guide to Position Sizing — Summary

Source: `Van-Tharps-Definitive-guide-to-position-sizing.pdf` (399 pages, 2008, scanned/image PDF — extracted via `pdftoppm` + `tesseract` OCR, not a native text layer). This file is being built incrementally; sections below are complete and OCR-verified, not paraphrased from secondary sources.

**Toolchain note for future extraction sessions:** `poppler-utils` and `tesseract-ocr` are installed on this box. `pdftoppm -f <first> -l <last> -r 150 -png <pdf> <prefix>` renders page ranges to PNG; `tesseract <page>.png -` OCRs one page to stdout. Batches larger than ~15-20 pages tend to exceed the 120s foreground timeout — run in background or in smaller batches.

## Table of Contents (full, OCR'd from pages 5-11)

**Part I — The Golden Rules of Trading and How to Evaluate System Quality**
- Ch 1: The Golden Rules of Trading
- Ch 2: Risk (R) and R-Multiples — Understanding R-Multiples, Using Total Risk to Track R-Multiples, What If You Don't Know Your Initial Risk, More on Expectancy, Variability, The Downside
- Ch 3: Evaluating System Quality — Rating Your System, Problems with SQN, Statistical Assumptions, Improving SQN
- Ch 4: What Can I Expect in the Future? — sample representativeness, system validity, multiple correlated trades
- Ch 5: Are You Doomed to Failure? — judgmental biases (locus of control, need to be right, percent gain bias, authority bias, law of small numbers, etc.)

**Part II — Understanding the Basics of Position Sizing**
- Ch 6: The Most Important Factor (Besides You) in Your Trading — low-risk ideas, psychological biases against proper sizing, gambler's fallacy
- Ch 7: CPR for Traders and Investors — the 3 components of position sizing, the CPR model, equity models (Total/Core/Reduced Total)
- Ch 8: Core Position Sizing Models — **Models 1-5** (see below, fully extracted)
- Ch 9: More Position Sizing Models — Model 6 (Group Control), Model 7 (Portfolio Heat), Model 8 (Long vs Short), Model 9 (Equity Crossover), Model 10 (Asset Allocation), Model 11 (Position Sizing for Portfolio Managers), Model 12 (for pros who don't track equity)
- Ch 10: Comparing the Impact of Various Models

**Part III — Using Position Sizing to Meet Your Objectives**
- Ch 11: Meeting Your Objectives — optimal bet size, expectancy/win rate vs. sizing
- Ch 12: Model 13 (Optimal Target Risk %), Model 14 (Market's Money Method), Model 15 (Scaling In)
- Ch 13: Model 16 (Fixed Ratio Position Sizing / FRPS) — full chapter on FRPS mechanics, advantages/disadvantages
- Ch 14: Position Sizing to Avoid Ruin — Model 17 (SQN-based risk limit), Model 18 (Two-tier), Model 19 (Multiple Tier), Model 21 (Scaling Out to Smooth Equity Curves), Model 22 (Basso-Schwager Asset Allocation)

**Part IV — Miscellaneous**
- Ch 15: Position Sizing Strategies to AVOID — Martingale models (23-26), Model 27 (Intuitive), Model 28 (Joe Ross Method), Model 29 (Percent Risk by Win Rate), **Model 30 (Kelly Criterion)**, **Model 31 (Optimal f)** (see below, fully extracted)
- Ch 16: Interview with Chris Anderson
- Ch 17: Position Sizing Software Examined
- Ch 18: Reader Q&A — misc, expectancy vs. sizing, risk of ruin, account size/liquidity, multiple accounts

*(Chapters 2, 3, 7, 9, and 14 now fully extracted below. Chapters 4, 5, 6, 10, 11, 12, 13, 16, 17, 18 not yet OCR'd in depth — flagged for a future pass if needed.)*

---

## Chapter 8 — The Five Core Models (fully extracted, PDF pages 118-129)

Test system used throughout the book's tables: Donchian 55-day channel breakout, 21-day trailing stop, $1M starting equity, 10 commodities, 1981-1991.

### Model 1: Units per Fixed Amount of Money
Trade one unit per $X of equity (e.g., 1 contract per $50,000). Simplest model — "you never reject a trade for being too risky," which is also its flaw. Real anecdote from the book: two CTAs, one on fixed-$-per-unit sizing, one on 2% percent-risk sizing, both offered the same Japanese Yen trade. The fixed-unit trader took it and had his firm's best month ever (+20%). The percent-risk trader's rules wouldn't let him take it — no gain that month, but also no exposure if it had gone the other way. Same signal, two outcomes, purely from the sizing rule.

Book's own backtest (Table 8-1): this system breaks down entirely below $30-40k in equity, with an 80%+ drawdown at $30k/unit and total ruin (402 rejected trades, 112% drawdown) at $20k/unit.

### Model 2: Equal Units / Equal Leverage
Divide capital into N equal-dollar units (e.g., 5 units of $10k in a $50k account), buy that dollar amount of each name. Used by real portfolio managers (book cites Louis Navallier managing ~20-stock equal-weight portfolios with periodic rebalancing back to target). **Disadvantage stated explicitly**: "although the exposure per unit seems to be equal, it might not be" — $50k of a low-volatility name and $50k of a high-volatility name can have 4x different actual dollar-volatility impact on the account despite "equal" sizing. (This is exactly the Equal-$ vs. %-volatility distinction our own backtest surfaced independently.)

### Model 3: Percent Margin
Size positions by capping the margin requirement (not the notional value or volatility) as a % of equity — e.g., no single position's margin can exceed 5% of account equity. First model that lets a small account scale up its exposure as it grows (unlike Models 1-2, which require equity to roughly double before adding a unit). Weakness: margin requirements are set arbitrarily by exchanges/brokers, loosely correlated with real volatility — two positions with equal margin can have very different real risk.

### Model 4: Percent Volatility
Size by making each position's daily volatility (average true range, not just high-low) a fixed % of equity. Worked example from the book: $50k account, 2% volatility cap = $1,000/position. Gold at $3/day range ($300/contract) → 3 contracts. Bonds at $0.75/day range ($750/contract) → 1 contract. Result: both positions now fluctuate by roughly the same dollar amount day to day, regardless of instrument.

Book's own backtest (Table 8-2) on the same system: 2% volatility allocation → 67-86%/year gain, but 69-86%/year max drawdown. Author's own conclusion: "few people could tolerate the drawdown" at the return-maximizing setting — the sizing that maximizes return is not the sizing you should actually use.

### Model 5: Percent Risk (a.k.a. Fixed Fractional Position Sizing)
Size by making the dollar loss-if-stopped-out a fixed % of equity: `shares = (equity × risk%) ÷ (entry − stop, in dollars)`. Ralph Vince and Ryan Jones both call this "fixed fractional" for the same reason — a percentage held constant trade to trade is a fixed fraction.

**Three distinct "equity models" for what "equity" means in that formula, when sizing a *sequence* of trades** (this is the part our own backtest structurally cannot test, since it only ever sizes once, on day one, against a static pool):
- **Total Equity Model**: use current account value including unrealized gains on still-open positions. Riskiest — a winning position immediately increases the size of your next bet.
- **Core Equity Model**: subtract the dollar risk already committed to open positions from cash first; size new positions only off what's left, ignoring unrealized gains until they're closed. Most conservative.
- **Reduced Total Equity Model**: a middle ground between the two (mentioned, not detailed in the extracted pages).

Worked example distinguishing them: $50k account, buy gold (risk $1,250), same-day short corn signal — Total Equity model still bases the corn trade's risk on the full $50k (since it's the same day, no unrealized move yet); Core Equity model bases it on $48,750 (the $1,250 already earmarked for gold is reserved). Six weeks later, gold has moved to a $11,000 open profit — Total Equity model now sizes the next trade off $61,000 (bigger positions from paper gains); Core Equity model still uses $48,750 regardless, unaffected by the open gain.

Book's own backtest (Table 8-3) on the same system: reward-to-risk ratio peaks around 20-25% risk-per-trade (ratio ~1.09-1.12), but with an 83-84% max drawdown at that peak. Author's direct comment: "you would have to tolerate an 84% drawdown in order to achieve it," and that trading this specific system with less than $100k and more than ~0.5% risk-per-trade isn't viable at all.

---

## Chapter 7 — CPR for Traders and Investors (fully extracted, PDF pages 112-117)

**The marble game — this is the actual primary-source version of the "same trades, different sizing" demonstration** (the thing mph originally set out to find at the start of this whole research thread; the Van Tharp Institute's public "Position Sizing Game" is a productized version of this same demo). Exact mechanics: a bag of 10 marbles — 7 are 1R losers, 1 is a 5R loser, 2 are 10R winners — drawn with replacement for 30 trades (this specific marble mix is "System 3-1" elsewhere in the book, expectancy 0.8R/trade). Tharp has run this live over 200 times to audiences up to 300 professional traders. His own words: "everyone gets the same trades... but usually everyone also has a completely different final equity, with the exception being those who go bankrupt. In fact, after starting out with $100,000, the final equities can easily range from zero to well over a million dollars." **Only two variables matter: psychology and position sizing.**

**Real academic citation worth using directly** (not secondhand): Brinson, Singer & Beebower, "Determinants of Portfolio Performance II: An Update," *Financial Analysts Journal* 47.3 (1991) — studied 82 portfolio managers over 10 years, found **91% of performance variance was explained by asset allocation** (how much to stocks/bonds/cash), not security selection. Tharp's framing: "asset allocation" is just institutional-language for "position sizing" — the same "how much" question, and most professionals (he singles out a Morgan Stanley chief strategist's book on asset allocation that never once defines or explains the "how much" question) don't actually understand why it's the dominant variable.

### The CPR formula
**P = C / R** — Position size = Cash-at-risk ÷ Risk-per-unit. Three variables: **C** = total dollars you're willing to risk this trade (e.g., 1% of a $50k account = $500 of C), **R** = dollar risk per unit/share/contract (entry − stop, in dollars), **P** = resulting position size.

Five worked examples straight from the book (useful as unit tests for any future sizing function):
1. $50 stock, stop at $45 (R=$5/share), risk 2% of $30k (C=$600) → P = 600/5 = **120 shares** ($6,000 notional, $600 total risk).
2. $30 stock, 30¢ stop (R=$0.30), risk 0.5% of $40k (C=$200) → P = 200/0.3 = **666.67 → ~700 shares** (~$20k notional, half the account, but only $200 actual risk).
3. Soybeans, 20¢ stop, 5,000 bu/contract → R = $1,000/contract. Willing to risk $500 (C=$500) → P = 500/1000 = **0.5 contracts — you CANNOT take this trade** (can't buy half a futures contract). Explicitly flagged as a trick question: "you need to know when your position has way too much risk [relative to your risk budget]."
4. Forex USD/CHF, stop distance 0.0078, $100k/contract → R=$780. $200k account, risk 2% (C=$4,000) → P = 4000/780 = **5.128 → 5 contracts** (round down, always).
5. QQQQ puts at $0.75, mental stop at $0.40 (R = 0.35 × 100 = $35/contract), $85k account, risk 5% (C=$4,250) → P = 4250/35 = **121 contracts**. Tharp's own aside: "this is a huge amount of risk, but I just wanted you to have some practice with options" — i.e., his own worked example is a cautionary tale about how big options position sizes can look once you actually run the math.

### The three Equity Models, fully defined with worked numbers (completes the gap in the Model 5 section above)
- **Core Equity**: subtract each new position's allocated risk from a running "core" balance as you open positions; only add back when a position closes. Example: $50k start, 10%/trade → open position 1 ($5,000 allocated) → core equity $45,000 → open position 2 ($4,500, i.e. 10% of the new $45k core) → core equity $40,500 → open position 3 ($4,050) → core equity $36,450. **New positions are always sized off the shrinking core, never off unrealized gains.** Most conservative — this is literally how a trader using "Market's Money" thinking (risk little of your own capital, more of the market's profits, but only once realized) operates.
- **Total Equity**: cash + current mark-to-market value of every open position, full stop. Example: $40k cash + open positions worth $15k, $7k, and −$2k (a loser) = **$60,000 total equity**, used directly for the next sizing decision. Tom Basso (cited by name, "taught me methods for maintaining a constant risk and a constant volatility") always used this model — if your goal is constant % risk to your *current* portfolio value, you have to use its current value, unrealized gains included. Riskiest of the three, because winning positions immediately inflate the next bet's size.
- **Reduced Total Equity**: a hybrid — starts like Core Equity (subtract new allocations), but *adds back* locked-in profit whenever you tighten a trailing stop (i.e., credits realized-via-stop-movement gains, not just realized-via-close gains). Worked example: $50k start, open position 1 ($5,000 allocated) → reduced total equity $45,000. Price rises, trailing stop tightens so only $3,000 of the position is now at risk → reduced total equity becomes $50,000 − $3,000 = **$47,000** (the $2,000 of now-protected profit gets added back immediately, before the position is even closed). A second position opens ($4,700 allocated), first position's stop later locks in $11,000 of profit → reduced total equity = $50,000 − $4,700 + $11,000 = **$56,300**. Middle risk level between Core and Total.

Tharp's own ranking, explicit: **Core Equity (most conservative) < Reduced Total Equity < Total Equity (riskiest)**. Every position-sizing model in the book (Models 1-31) can be run under any of the three equity methods — his own math: 31 models × 3 equity methods = "over 90 different position sizing models." Unless a model's discussion says otherwise, the book defaults to Total Equity when presenting examples.

---

## Chapter 9 — More Position Sizing Models, excerpted for Models 6-9 (fully extracted, PDF pages 132-136; Models 10-12 and Chapter 10 not yet extracted)

### Model 6: Group Control
Direct treatment of correlation risk. Worked example: a system with 41.7% win rate (5 of 12 trades) and 2.5:1 reward-to-risk, traded across 10 *independent* instruments simultaneously — Table 9-1 shows the resulting monthly P&L distribution has only a **14.2% chance of an overall losing month**, even though any single instrument alone loses money most months. The entire benefit depends on independence: "if you buy several home building stocks... you might suddenly find yourself in a position where a significant analyst downgrades the industry and all of your stocks start to plunge together. Instead of losing 1%, you've lost 4%." Same warning extended to commodity groupings (grains, metals, currencies, etc. moving as blocks). **Direct prescription: limit total exposure per correlated group** (e.g., cap total risk in any one interest-rate-sensitive group at 3% even if your per-position cap is 1%, meaning at most three 1%-risk positions in that whole group at once) — this is the exact mechanism missing from mph's Discord "7 correlated LEAPS" evidence and from our own 25-ticker backtest (which treated every name as independent).

### Model 7: Portfolio Heat — the single highest-value model in the book
Term coined by Ed Seykota and Dave Druz for **total simultaneous risk across the whole portfolio** — the sum of every open position's risk-if-stopped, as a % of equity. Direct quote on the ceiling: "20-25% portfolio heat is probably a maximum" for a good system — but the real prescription is that the ceiling should scale with System Quality Number (SQN), not be a flat number for everyone.

**Table 9-3, the actual lookup table — this is the concrete, implementable rule:**

| System Quality Number | Maximum Portfolio Heat |
|---|---|
| 5.0 or higher | 25% (20% if highly leveraged) |
| 4.0 to 4.99 | 20% (15% if highly leveraged) |
| 3.0 to 3.99 | 15% |
| 2.5 to 2.99 | 12% |
| 1.7 to 2.49 | 8% |
| 1.3 to 1.69 | 4% |
| Below 1.3 | 1% if you trade it at all |

Usage: look up max total heat from SQN, divide by the number of concurrent positions you expect to hold, and that quotient is your **per-position** risk cap. Worked example given directly: SQN between 1.7-2.49, holding 10 positions → max 0.8% risk per position. **Secondary hard rule, independent of the table**: max portfolio heat must always be less than `100% ÷ (largest plausible single-trade loss, in R)` — e.g., if any position could realistically produce a 5R loss, total heat must stay under 20% regardless of what the SQN table says, or a single freak trade could wipe the whole book.

Also explicit: portfolio heat is normally computed on total *risk*, but the same "cap the total" logic can be applied to total leverage, total volatility, or total margin exposure instead — "the guidelines could be different for each model."

### Model 8: Long vs. Short Positions
Some traders (cited: the Turtles, per Curtis Faith's *Way of the Turtle*) net long and short exposure against each other for heat purposes — one long position + one short position at equal risk levels count as one heat unit, not two. The Turtles' actual limit: 10% risk long + 10% risk short (not summed into "20% heat," treated as two separate 10% books) — and even at that discipline level, "many of the accounts still came close to ruin in October 1987." Only applies to equalizing models (2-5), not Model 1 (units-per-fixed-$).

### Model 9: Equity Crossover Position Sizing
Size up when your own account equity curve crosses above its moving average (system "working"), size down or stop when it crosses below (system possibly "breaking down"). Two distinct uses noted: an extreme/slow moving average to detect real regime breakdown vs. a faster one to detect short-term cooling. Tharp flags the *inverse* version — adding size specifically when the equity curve is already falling, on the theory that "it's due for a bounce" — as a **Martingale strategy that generally does not work**, with a narrow exception only if you have actual statistical evidence (a formal dependency/autocorrelation test on your own results) that your specific system exhibits real mean-reversion in its own equity curve.

*(Models 10-12 — Asset Allocation, Portfolio Managers, and Position Sizing Without Tracked Equity — and Chapter 10's model comparison were located, PDF pages 137-145+, but not yet OCR'd in full detail; flagged for next pass.)*

---

## Chapter 2 — Risk (R) and R-Multiples (fully extracted, PDF pages 30-41)

**R, defined precisely**: not volatility (Wall Street's definition) — "how much you'll lose per unit of your investment if you are wrong about the position." R = entry price − stop price, per share/contract/unit. Five worked examples straight from the book: $50 stock/$40 stop → R=$10; same stock/$48 stop → R=$2 (same entry, different R purely from where you place the stop); $24 stock with a 25% trailing stop → R=$6; soybean contract (5,000 bu) with a 10¢ stop → R=$500/contract; a $10k forex minimum unit with a $1,000 stop → R=$1,000.

**R-multiple** = actual profit or loss ÷ 1R. A loss bigger than planned (slippage/gap) is a "> 1R loss" — explicitly flagged as something "you want to avoid at all costs." A few of the book's own exercise answers, verbatim: a $2-per-share loss on a $4 R-value is a 0.5R loss; a $40-per-share gain on a $4 R-value is a 10R profit; a stock that gaps to worthless after you failed to honor your stop (his direct example: "this perfectly describes the situation with Enron, WorldCom") is however many R your actual, undisciplined loss turned out to be — the point being your realized R-multiple is only ever as good as your discipline in actually taking the planned exit.

**Total-risk method** (simpler than per-share tracking, and the one to actually use): pick a total dollar risk for the position (e.g., 1% of a $100k account = $1,000), size shares as `total_risk ÷ per-share_R`, and compute R-multiples off total profit/loss including transaction costs rather than per-share math. Worked example: 500 shares at $2/share risk = $1,000 total risk; stock gaps against you, total loss $4,500 + $24 costs = $4,524 → **4.524R loss** (vs. the cleaner 4.5R you'd get ignoring costs — use total-risk method specifically because it lets you fold in real transaction costs).

**When you don't know your initial risk** (no defined exit, or it was variable): use your **average loss** as a stand-in for 1R. Explicitly shown to be imperfect — in the book's own 10-trade sample, the true average risk was $1,000/trade but the average *loss* came out to $1,200.20 (20% high), producing a slightly-off expectancy estimate (0.811R using the estimate vs. 0.966R using real per-trade risk). Use it only when you have no better option, and know it's an approximation.

**Expectancy — three formulas, three different numbers from the exact same 10-trade sample, only one of them right:**
1. Original *Trade Your Way to Financial Freedom* (1st edition) formula — Tharp states outright this version was **wrong**: `Expectancy = [(Avg Profit)×(Win%)] − [(Avg Loss)×(Loss%)]`. This just computes average $ profit/loss per trade, not a true "expectancy per dollar risked" — his own complaint: "look up expectancy on the internet and notice how many sites have this wrong formula, which I suspect was often copied from my book."
2. **Corrected formula** (2nd edition): take that same average-profit/loss number and divide by average dollar amount risked. On the sample: ($1,575.20 − $600.10) ÷ $890 avg risk = **1.096**.
3. **Preferred/most accurate — expectancy is simply the mean of your actual R-multiples.** On the same sample: **0.966R.** (Using the average-loss-as-1R estimate from above instead of real per-trade risk gives 0.811R — close, but confirms the estimate method costs you real accuracy.)

**"Always calculate the average R-multiple for expectancy" is the direct, final instruction** — not formula 1 or 2, which are both approximations of what formula 3 gives you directly. Practical meaning: expectancy of 0.966R at 1% risk per trade → expect ~0.966% return per trade on average, compounding as equity grows (1% of $100k vs. 1% of $110k is not the same dollar amount — the position size keeps growing with the account).

**Variability matters as much as the average** — expectancy alone tells you nothing about how rough the ride is. Compute standard deviation of your R-multiples alongside the mean (book's own sample: mean 0.966R, StDev 2.66 — a genuinely wide spread around a modest edge). **The downside, illustrated concretely**: risking 10% of *remaining* equity through a realistic 5-loss streak (real R-multiples: −0.82, −1.53, −0.78, −1.13, −2.89) takes $100,000 down to **$45,211** — a −7.15R, ~55% drawdown, from ordinary variance in a system that isn't even broken. Tharp's own verdict on that example: **"10% is way too much risk for this system."**

---

## Chapter 3 — Evaluating the Quality of Your Trading System / SQN (fully extracted, PDF pages 42-58)

**The setup**: six sample systems (3-1 through 3-6) with deliberately scrambled win rates (10%-90%) and R-multiple distributions, ranked five different ways to show how badly naive ranking methods disagree with each other:
1. **By win rate** — picks System 3-3 (90% win rate) as best. It has **negative expectancy (−0.10R)** and will lose money over time. Ranking by win rate is the naive, wrong instinct most people default to.
2. **By expectancy alone** — better, but still incomplete; doesn't account for trade frequency or drawdown risk.
3. **By "expectunity"** (expectancy × trades/month) — accounts for opportunity, still ignores variance/drawdown.
4. **By simulated drawdown** (10,000 simulations of 100 trades per system) — the system with the *worst* expectancy among the positive ones can have the *best* drawdown profile, and vice versa; a system that ranked well on expectunity turned out worse for drawdowns than the flat-out losing system.
5. **By statistics — System Quality Number.** This is the one Tharp actually endorses.

**The SQN formula, exact, verbatim:**
> **System Quality Number™ = (Expectancy ÷ Standard Deviation of R) × √(Number of Trades)**

Stated directly to be mathematically equivalent to a one-sample t-score (testing whether your expectancy is significantly different from zero) — "if there is a 95% probability that it is different, you can reject the hypothesis that it has a negative or zero return on average."

**Rating table (Table 3-11), based on N=100 trades:**

| SQN | Rating |
|---|---|
| Below 1.0 | Probably very hard to trade |
| 1.01 – 2.00 | Average system (needs ~1.7 to be statistically significant) |
| 2.01 – 3.00 | Good system (significantly different from 0) |
| 3.01 – 5.00 | Excellent system |
| 5.01 – 7.00 | Superb system (few exist) |
| 7.01+ | "Holy Grail" system |

Reference points he gives from real life: a well-known monthly newsletter (Sjuggerud's *True Wealth*) scored ~3.0 despite heavy real-world constraints (must recommend only very liquid names). His own simple 25%-trailing-stop long-only system scored 4.08 over 23 trades. He explicitly expects "most people" to land at 1.75 or below, and states few real systems ever reach 5.0+.

**Two critical caveats that stop SQN from being naively trustworthy:**
1. **Sample-size inflation**: with fewer than ~30 trades, a SQN can look artificially great — with only 10 trades you'd need an SQN of *3.50* just to start trusting it as good (vs. 2.5 at 30 trades), because the √N term rewards trade count as much as real quality. Real example given: a system that looked like a "Holy Grail" (SQN ≈ 13) after 38 trades was actually only "SQN ≈ 8"-grade once honestly assessed, because the headline number wrongly used N=100 as the multiplier instead of the true 38.
2. **The reverse problem — too many trades inflates it too**: a 198-trade backtest scoring SQN 5.19 ("superb") drops to a more honest **3.68 ("excellent," not superb)** once you standardize to the book's N=100 convention. **Fix, stated directly**: if you have fewer than 100 real trades, use your actual N. If you have more than 100, compute the ratio (expectancy ÷ StDev) and multiply by **10** (i.e., cap the effective N at 100) rather than let a huge trade count inflate the score — "it's better to be conservative than to overestimate how good your system really is."

**What actually improves SQN — counterintuitive result worth keeping**: Tharp added two 30R winners to a system with expectancy 1.1 and SQN 4.51. Expectancy nearly doubled to 2.13 — but standard deviation grew even faster (to 5.99), and the **resulting SQN dropped over 20%, to 3.55.** His own reaction: "not what I would have predicted before doing the calculation myself." Lesson stated directly: to raise SQN, you generally need **more small, consistent winners**, not a few huge ones — variance is punished harder than the mean is rewarded.

**Validity caveats, briefly**: an SQN is only as trustworthy as the sample it's built from — it should ideally be built from a large sample (30+ minimum, 100+ ideal) spanning all six of Tharp's named market regimes (up-volatile, up-quiet, sideways-volatile, sideways-quiet, down-volatile, down-quiet), since a system tuned to one regime (his example: a trend-following system built only on 1998-99 tech-stock data) can look like a "monster" and then produce ruin the moment the regime changes (his example: 2000-2002). Also flags real historical price-shock events (Oct 1987, Sept 2001) as reminders that any SQN estimate assumes shocks that size aren't imminent, when they always might be.

---

## Chapter 14 — Position Sizing Methods to Help You Avoid Ruin (fully extracted, PDF pages 207-217)

**Framing**: the industry (and clients) judge you on peak-to-trough drawdown, not net return — his own example: an account goes from $50k → $80k → $52k. Net result is +4% from where it started, but it's judged as **"a 35% peak-to-trough drawdown,"** and from the client's perspective watching $28,000 disappear, that framing is fair. Most of a system's drawdown-avoidance job falls on position sizing, not the entry/exit rules themselves.

### Model 17: Using SQN to Determine How to Limit Risk — the actual heat-ceiling lookup tables
Ran 10,000 simulations of 100 trades for each of 7 model systems (SQN ≈ 1 through 7, the same SQN1-SQN7 systems built in Chapter 3) across risk levels from 0.2% to 10%, to find the risk level just before each system's probability of hitting a given drawdown ("ruin level") crosses a threshold.

**Table 14-1 — risk % just below a <1% chance of ruin:**

| Ruin level (drawdown) | SQN 1 | SQN 2 | SQN 3 | SQN 4 | SQN 5 | SQN 6 | SQN 7 |
|---|---|---|---|---|---|---|---|
| 25% | 0.2% | 1.4% | 2.2% | 2.4% | 3.2% | 4.6% | 4.8% |
| 50% | 0.6% | 3.2% | 4.8% | 5.2% | 6.8% | 9.4% | 9.8% |

**Table 14-2 — risk % just below a <10% chance of ruin (more permissive):**

| Ruin level (drawdown) | SQN 1 | SQN 2 | SQN 3 | SQN 4 | SQN 5 | SQN 6 | SQN 7 |
|---|---|---|---|---|---|---|---|
| 25% | 0.4% | 2.8% | 4.2% | 4.8% | 6.6% | 12.4% | 18.2% |
| 50% | 1.0% | 5.8% | 8.4% | 9.7% | 11.8% | 18.6% | 19.6% |

(Full tables in the book run every 5% ruin-level increment from 5% to 50% — these are excerpted rows; the shape holds throughout: better SQN buys meaningfully more usable risk at every ruin tolerance.)

**Usage, stated directly**: look up your system's SQN and your chosen ruin definition, read off the **portfolio heat** ceiling, then **divide by your maximum expected number of simultaneous positions** to get your per-position risk cap. Worked example: SQN=4, ruin defined as a 25% drawdown, willing to accept a 10% chance of it → 4.8% portfolio heat (Table 14-2) → ÷10 concurrent positions = **0.48% per position**. If you want under 1% ruin chance instead (Table 14-1) → 2.4% heat → **0.24% per position**. These tables assume a 5R worst-case single loss; a smaller worst-case (2R) roughly doubles the usable heat ceiling — but "there is always a worst-case loss you don't know about," so use the conservative 5R-based tables even if you've personally never seen worse than 3R.

### Model 18: Two-Tier Position Sizing
Risk a near-zero-ruin-chance base rate (e.g., 0.4%, ~1.4% ruin chance) until equity crosses a defined threshold, then switch to a materially more aggressive tier (e.g., 1.2%) for the remainder. Worked example (System 13-2, Table 14-3, simulated 10,000× for a target of +300%/100 trades with ruin defined as −25%): a max-return-optimized 8.2% risk level carries a **94.2% probability of ruin** — extreme, cautionary. The two-tier recipe chosen instead: base at 0.4% (1.4% ruin chance), switch to 1.2% once up ~40% from start, because even an immediate 40% drawdown from that elevated point ($140k → $84k) still stays above the ruin floor. **Tharp's own stated bias is against this model**, in favor of Model 14 (Market's Money, not yet extracted in this file) — his objection: the tier-switch jump risks giving back all accumulated profit in one move, whereas a gradual "market's money" approach is conservative continuously rather than at one discrete jump point.

### Model 19: Multiple Tier Approach
Same idea as Model 18 but staged: increment risk by a fixed step (e.g., +0.2%) every time equity climbs by a fixed increment (e.g., +5%), up to a max. Can be paired with a **dampening factor** that ratchets risk back down faster than it ratcheted up on the way down — a 50% dampening factor cuts risk back to the prior tier at half the equity-gain distance it took to earn that tier, so the model de-risks roughly twice as fast as it re-risks.

### Model 20: Using the Maximum R-Drawdown
Simulate the system, build the distribution of maximum peak-to-trough R-drawdown across many simulated 100-trade runs (book's example, Table 14-5: median max drawdown 38R, a 10% chance of 60R, a 1% chance of 93R), then **divide your acceptable dollar-drawdown-% by the R-drawdown at your chosen confidence level** to get your per-trade risk cap. Worked example: accepting a 25% max drawdown at the 10% probability level (60R) → 25% ÷ 60 = **0.4% risk per trade**; tightening to a 1% probability tolerance (93R) → 25% ÷ 93 ≈ **0.27%**. Explicit 5-step recipe given in the book, directly implementable.

### Model 21: Scaling Out to Smooth Equity Curves — the direct precedent for "trim, don't just hold or exit"
**Tom Basso's real, fully computerized method** (his computers recalculated open risk and open volatility roughly every minute and scaled positions down automatically whenever either exceeded a set %): monitor **open risk** (current price − current/trailing stop, in dollars) and **open volatility** (ATR-based) as a % of *current total equity*, and trim the position whenever either exceeds your chosen ceiling — **without touching the actual stop itself**. Two full worked examples:
- **Open-risk trim**: $200k account, 4 gold contracts bought at $400 with a $390 stop (initial open risk $4,000, i.e. 2%). Gold rallies to $440 (stop trails to $410, equity now $216k). New open risk is $30/contract × 4 = $12,000 — now 5.6% of equity, above the 3% ceiling. Since 3% of $216k = $6,480 ÷ $30/contract-of-risk ≈ 2 contracts affordable → **sell 2 of the 4 contracts**, keep the stop exactly where the system says it should be. Tharp's explicit answer to "why not just raise the stop instead?" — "position sizing is a separate part of your system that tells you how much... if you altered your stop, you wouldn't be following your trading system... your exit and your position sizing would start to merge."
- **Open-volatility trim**: $200k account, corn bought at $3.00 with volatility capped at 1% of equity ($2,000, giving 5 contracts at 8¢/day ATR = $400/contract). Corn rallies to $4.00 (equity now $225k, ATR now 20¢/contract = $1,000/contract). Vol ceiling is now 2% of $225k = $4,500; 5 contracts × $1,000 = $5,000 total volatility exceeds it → **sell 1 contract**.

**Why you don't buy back in when risk/volatility later drops** (Basso's own reasoning, direct): in a real sustained trend both open risk and open volatility keep *rising* toward the trend's conclusion — a sudden apparent decrease is usually temporary, and scaling back in "would either 1) have to get right back out again, or 2) find that you were suddenly putting yourself in danger of a serious financial setback."

### Model 22: Basso-Schwager Asset Allocation Technique Applied to Systems — the real study behind "rebalancing across strategies"
**The actual study**: Tom Basso's research on 720 real CTAs (79 active in 1983), testing all 79,079 possible 3-manager groupings from Jan 1983–Dec 1993, comparing a **static** allocation (each manager keeps 1/3 forever, drifting with performance) against a **monthly-rebalanced** allocation (reset to 1/3 each month — explicitly a Martingale-style "take from the winners, give to the losers" mechanic). Results: static averaged a slightly *higher* raw return (13.27% vs. 12.62%), but rebalanced cut max drawdown meaningfully (28.29% vs. 34.26%) and posted a better return/drawdown ratio (0.53 vs. 0.46) — good enough that levering the rebalanced group by 1.211x matched static's drawdown while beating its return at an annualized 15.28%. **This is a higher realized SQN from rebalancing alone, no change to the underlying managers/systems.**

Jack Schwager's critique (also directly reported): Basso's combinations weren't corrected for manager correlation, understating the real benefit; Schwager's own follow-up found low-correlation manager groups benefit from monthly rebalancing far more, and that group size itself reduces risk (5-manager groups cut risk 38.6%; 10-manager groups cut risk 45.3%).

**Direct, explicit extension to systems** (not just fund managers): trade 5+ genuinely non-correlated systems, rebalance the capital allocation across them monthly — "you will be taking money away from the systems that are performing the best and giving money to the systems that are performing poorly... it should give you a much better reward-to-risk ratio." Can be weighted by relative SQN rather than kept equal: worked example, three systems at SQN 2.7 / 4.1 / 5.7 → allocate 10% / 30% / 60% respectively, rebalanced monthly back to those target weights (not equal weights) — this is the direct, concrete recipe for weighting a multi-strategy allocation by measured system quality rather than by gut feel or equal-split default.

**Chapter's own 6-method summary**: (1) SQN-based portfolio heat ceiling, (2) two-tier position sizing, (3) multiple-tier position sizing with optional dampening, (4) max-R-drawdown-based risk sizing, (5) scaling out on open risk/volatility, (6) Martingale-style rebalancing across managers or systems, optionally SQN-weighted.

---

## Chapter 15 — Strategies to Avoid (fully extracted, PDF pages 231-237)

Core thesis of the chapter (stated directly): position sizing algorithms that maximize *average* ending equity are dangerous, because the sizing that maximizes the average also tends to carry a 90%+ chance of ruin — the average is being dragged up by a small number of extreme lucky outcomes, not describing the typical result.

### Model 29: Percent Risk Based on Win Rate
Assumes every win/loss is exactly 1R (win = loss size), formula `F = p − (1−p)`. His own table of implied "optimal" sizes: 55% win rate → 10% risk, 65% → 30%, 75% → 50%, 80% win rate → **60% risk per trade**. Presented specifically to show how quickly this class of formula produces insane numbers before even reaching Kelly.

### Model 30: Kelly Criterion (Thorp's version, with payoffs)
Formula, exact: **`Kelly % = W − [(1 − W)/R]`**, W = win rate, R = avg win ÷ avg loss. Book's worked example: W=0.5, R=2 → Kelly = 25%. Mentions the common practitioner hedge of using ~80% of Kelly divided by the number of concurrent open positions (e.g., 80% of 25% = 20%, ÷ 10 concurrent trades = 2%/trade) — but states this "portfolio heat" hack can still produce "absolute ruin" for return distributions with rare enormous winners (references a hypothetical system with 99 trades of 1R loss and one trade of 1,000R gain — an extreme skew that breaks the two-outcome assumption Kelly requires).

**Stated reasons for rejecting Kelly outright** (his words): (1) "it was developed for use when you had two possible outcomes... rather than the multiple outcomes you have with trading," (2) "it can grossly overestimate the position sizing you should use." Verdict: **"Avoid the Kelly Criterion totally."**

### Model 31: Optimal f (Ralph Vince)
Vince's own quote, cited directly: "if you are not trading for optimal profits, then you belong on a psychiatrist's couch rather than in the markets." Tharp's three specific objections: (1) optimal f is calibrated off your single worst historical loss, which wrongly assumes your worst-ever loss has already happened — "much more useful to assume that one's worst loss has never occurred"; (2) it protects against one catastrophic trade but not a long losing *streak*, a materially different risk; (3) the math (Terminal Wealth Relative, iterative search over f between 0.01-1.00) is needlessly opaque even for someone trained in math — "if this explanation is too complex for you, that's another reason to avoid it."

**The independently-reproduced "mean lies, median tells the truth" result** — directly comparable to our own Monte Carlo sim: Tharp ran a real, mediocre system (expectancy 0.09R, standard deviation 0.96R, SQN 0.21) at ~15% risk (the level Optimal-f-style sizing implied for it) through his own simulator, 50 trades. Result: **average ending equity +89.9%, but median ending equity negative, probability of ruin 42.5%, probability of reaching the stated objective only 28.8%.** His own conclusion: "huge levels of risk for a trading system that is at best poor — one that you really should not trade at all." This is the same phenomenon our own "All-in 25%" row showed (median a loss, mean inflated by rare lucky compounding) — his finding, independently, on a real system, is the strongest single piece of corroborating evidence available for that argument.

**Full list of Chapter 15's "avoid" models**, for completeness: 4 Martingale variants (23-26, "your bet size goes up as you lose" — "almost guarantee ruin," exception noted for Basso-Schwager rebalancing), Intuitive Position Sizing (27 — no correlation between trade confidence and trade success, possibly a slight *negative* correlation), the Joe Ross Method (28), Percent Risk by Win Rate (29), Kelly Criterion (30), Optimal f (31).

---

## Flagged for future agent integration (not built yet, per mph's "markdown for now" instruction)
- **Model 7, Portfolio Heat (Table 9-3), plus Model 17's SQN-based ruin tables (Ch. 14), are now a complete, closed-loop sizing pipeline, fully documented**: compute SQN per strategy (formula and rating table now in Ch. 3 above) → look up max total heat from either the Ch. 9 table (generic heat ceiling) or the Ch. 14 tables (heat ceiling for a *specifically chosen* max-drawdown/ruin tolerance, which is the more rigorous of the two) → divide by expected concurrent position count → per-position risk cap. This whole chain is now extracted, formula-complete, and ready to code as-is.
- **Model 6, Group Control**, is the natural companion to Portfolio Heat: cap total risk *per correlated group* (sector, asset class, or theme) separately from the account-wide heat cap, so an agent can't stack multiple "independent-looking" proposals that are actually one correlated bet.
- The Total/Core/Reduced-Total equity model distinction is the second most directly applicable concept — it's the actual position-sizing logic for an autonomous agent sizing sequential trades against a live, evolving NetLiq, not a static one-shot portfolio weighting scheme like our backtest. Recommend Core Equity or Reduced Total Equity over Total Equity, given Tharp's own ranking of Total Equity as the riskiest of the three (it lets paper gains inflate the next bet before anything is realized).
- **Model 21 (Scaling Out, Ch. 14) is the direct, fully-worked precedent for a "trim, don't just hold-or-exit" mechanism** — Tom Basso's real open-risk/open-volatility trim rule, with two complete numeric examples, is essentially a spec for a background job: recompute each open position's risk/volatility as a % of current equity on a schedule, trim (never add back) whenever a ceiling is crossed, leave the actual stop alone. This is a stronger, more concrete version of the rebalancing logic our own backtest already found added real value.
- **Model 22 (Basso-Schwager, Ch. 14) gives a concrete, SQN-weighted recipe for allocating capital across multiple strategies/systems** — not equal-split, not gut-feel: weight by relative SQN (worked example: SQN 2.7/4.1/5.7 → 10%/30%/60%), rebalance monthly back to those targets. Directly applicable if an agent ever runs more than one strategy concurrently.
- The CPR formula (`P = C/R`) is the simplest possible unit of this whole system and should probably be the literal function signature for whatever a sizing module ends up being — the five worked examples in Ch. 7 above are ready-made unit tests. Chapter 2's R-multiple/expectancy formulas (use the *mean R-multiple* definition, not either of the two dollar-based approximations) are the required upstream inputs to that function and to SQN itself.
- Chapter 3's counterintuitive SQN-optimization finding (adding rare huge winners can *lower* SQN by inflating variance faster than mean) is worth a runtime guard: don't let a strategy's SQN calculation get gamed by one lucky outlier trade — track it, but don't let it silently raise the strategy's allowed heat ceiling on the basis of one data point.
