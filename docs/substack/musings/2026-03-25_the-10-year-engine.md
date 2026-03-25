---
title: "The 10-Year 3x Engine: The Dissertation (Math, Tax Drag, and Why the Next NVDA is NVDA)"
date: "2026-03-25"
author: "Michael & Sam"
tags: ["Portfolio Architecture", "Tax Strategy", "Value Averaging", "Quant", "Kelly Criterion", "Systematic Trading"]
---

My brother and my grandma came to me this week with a very specific problem. 

They both have taxable accounts. They both want to triple their money in 10 years (which requires an **11.6% Compound Annual Growth Rate**). They understand they need growth, but they also need liquid "emergency" access to cash just in case life does what life does.

You can't hit 11.6% net-of-taxes over a decade by holding SPY and praying we don't hit a lost macroeconomic decade. And because these are *taxable* accounts, you can't just aggressively swing-trade high-beta tech names without Uncle Sam eating 30% of your compounding effect. 

Initially, I sketched out a basic "5 ETFs and 5 Stocks" port. But I realized that wasn't good enough. If this is real family money, we don't just throw "60/40" at the wall. We build a dissertation. We prove the math. We define the exact execution rules.

I had Sam (my relentlessly sarcastic AI copilot) run the structural probabilities and build an absolute masterclass on capital efficiency, tax drag, and Kelly Criterion sizing. 

Here is the exact blueprint for the 10-Year 3x Engine.

---

### Part 1: The Core Architecture & Cash Drag (60%)

We allocate exactly 60% of the capital to 5 Core ETFs. But wait—should this hold cash? 

Cash yields 5% right now. But a 5% yield mathematically drags an 11.6% target anchor heavily. Instead of structurally holding 10% cash (SGOV), we use an **Active Cash Buffer Mechanism**. We start fully invested, but use our Yield Engine to build the liquid emergency cash monthly.

1. **20% NTSX (WisdomTree 90/60 US Equity/Treasury)**
   *The Capital Efficiency.* NTSX provides 1.5x notional exposure. $10,000 buys $9,000 of the S&P 500 and $6k of laddered Treasury futures. Because it uses futures instead of swaps, it avoids massive forced taxable distributions. It essentially leverages a balanced portfolio for cheap. If Grandma has a massive emergency and the cash buffer is empty, NTSX is the most liquid, least volatile asset we can sell.
   
2. **15% QQQI (NEOS Nasdaq-100 High Income)**
   *The Yield Engine.* This is how we build Cash. QQQI writes NDX *index options*. Index options qualify as **Section 1256 Contracts**—taxed at 60% long-term / 40% short-term capital gains regardless of your holding period. The monthly tax-advantaged cash is swept into a money market fund. That becomes Grandma's emergency supply and our Value Averaging ammunition.

3. **15% AVUV (Avantis US Small Cap Value)**
   *The Structural Premium.* Large-cap tech is mathematically priced for perfection. Historically, to beat the S&P 500 over a 10-year horizon, you need a small-cap value tilt. Avantis actively screens out "value traps" (highly indebted zombie companies) and only buys profitable small caps.

4. **10% GDX (VanEck Gold Miners)**
   *The Chaos Hedge.* Gold provides asymmetric upside to fiat debasement. GDX historically exhibits a 0.25 correlation with QQQ. When Tech crashes 30%, Gold miners often rip higher, providing structural rebalancing power.

*(Note: Why no International factor like VXUS? Tax drag. Foreign ETF dividends are often "non-qualified" ordinary income. In a taxable account, you permanently lose the 15-20% margin to taxes every year, destroying compounding. Mega-cap US tech already derives 40%+ of its revenue globally anyway.)*

---

### Part 2: The Sizing Proof (The Kelly Criterion)

The remaining 40% is allocated to 5 specific satellite stocks. That equals an **8% position maximum**. 

Why 8%? Why not 20% in two stocks? 

We use the **Fractional Kelly Criterion**. The Kelly equation ($f^* = \frac{\mu - r}{\sigma^2}$) dictates the optimal percentage of a bankroll you should bet to maximize long-term logarithmic growth given your edge ($p - q$).
If a typical high-conviction growth stock gives us a 15% expected excess return over the risk-free rate, with a 40% annualized variance (volatility), Full Kelly suggests a 30-40% allocation. 

But Full Kelly is pure financial suicide because real-world volatility isn't normal. A Fractional Kelly (1/4th Kelly) approach provides ~90% of the compounding growth while massively reducing the depth of drawdowns. 1/4th of 35% is ~8%. 

By limiting individual stock exposure to 8%, we structurally ensure that even if a stock goes bankrupt (Enron, Wirecard), we only suffer an 8% portfolio drag—something the remaining 11.6% CAGR target can recover in 8 months.

---

### Part 3: The Satellites (Why the Next NVDA is NVDA)

We need massive asymmetric alpha to hit 3x. We hold exactly 5 stocks (8% weight each). 

**Slot A: The Mag 7 Anchor**
Everyone spends years trying to find "the next NVDA" while completely ignoring that NVDA is still NVDA. It doesn't *have* to be NVDA—if GOOGL breaks out above its 200 SMA on a relative strength matrix, we can rotate. But the rule is rigid: we stay anchored to whichever Mega-Cap Tech platform owns the infrastructure rails of the next decade. Right now, that’s NVDA.

**Slot B & C: The Compounders (Growth)**
We need two tax-efficient "buy and never sell" structural compounders.
- **The Screen:** Gross margin > 50%, ROIC > 15%, EPS 3-yr growth > 15%, trading > 200-day SMA.
- **Candidates today:** MSFT, COST.

**Slot D: The Dividend Growth King (Yield + Downside)**
We need one stock that guarantees rising cash flow regardless of price action.
- **The Screen:** 10+ years of rising dividends, payout ratio < 60%, FCF yield > 4%.
- **Candidates today:** AVGO, LMT.

**Slot E: The Alpha Engine (Pure Momentum)**
This is our aggressive swing slot.
- **The Screen:** RSI > 65, MACD histogram positive, ADX > 30 (strong trend), trading near 52-week highs.

---

### Part 4: The "If This, Then That" (IFTTT) Execution Rules

This is real money. You cannot just "buy and hold" and walk away. You need a mechanical playbook that removes human emotion. 

#### Rule 1: The Value Averaging Mechanism (The "Emergency" Fund)
The biggest mistake retail makes in taxable accounts is selling winners to buy losers (triggering massive capital gains taxes). 
- **IF** it is the 1st of the month...
- **THEN** we take the massive Section 1256 yield generated by `QQQI` and sweep it into cash. 
- **IF** Grandma has an emergency...
- **THEN** she draws directly from this cash buffer.
- **IF** the cash buffer is full and it is the end of the quarter...
- **THEN** we value-average. We use the cash to buy whichever of the 10 assets is furthest *below* its target allocation. This naturally averages down our cost basis on structurally sound assets (like AVUV) without ever clicking the "Sell" button on our winners.

#### Rule 2: Exiting Individual Stocks (The Satellites)
We do not marry the stock picks. They are math equations.
- **IF** a "Compounder" stock (like MSFT) drops its ROIC below 10% on an earnings report **AND** closes below its 200-day moving average for three consecutive weeks...
- **THEN** the fundamental thesis is broken. We sell the entire position immediately, take the tax hit, and rerun the *Compounder Screen* to find its replacement.

#### Rule 3: Managing the Core ETFs
- **IF** `AVUV` massively underperforms `QQQI` for 3 straight years...
- **THEN** we do nothing. That is the nature of the small-cap value premium. It is a 10-year hold designed to pop when mega-cap tech flatlines.
- **IF** any single asset drifts to more than +25% of its target allocation (e.g., NVDA goes from 8% to 10% of the total portfolio)...
- **THEN** we initiate a "Hard Rebalance" in December. We trim the excess down to the baseline and pay the taxes, shifting the capital to the laggards. 

#### Rule 4: Macro Regime Shifts
- **IF** the S&P 500 `VIX` index closes above 30 for two consecutive days...
- **THEN** we pause all value averaging. The `QQQI` cash yield is stockpiled in a money market fund yielding 5% (or NTSX) until the VIX breaks back below 25. We do not catch falling knives during structural market panics. 

---

### The Receipts: 10,000 Monte Carlo Paths

I told Sam to spin up a Monte Carlo simulation running 10,000 paths of this exact asset makeup over the next 10 years, using the last 5 years of daily covariance and mean returns.

*"Sure,"* Sam replied. *"But remember, the last five years of tech returns are a statistical anomaly. NVDA and QQQ skewed the drift so hard that the simulation literally gives this portfolio a 95.17% chance of tripling. Mean reversion comes for us all, don't forget the IFTTT rules."*

```text
--- 10-Year Monte Carlo Results (10,000 Paths) ---
Probability of Tripling (>3x): 95.17%
Median Portfolio Multiple: 9.77x
5th Percentile (Worst Case): 3.03x
```

Trading is simple. It is not easy. Stick to the system. The math works.

— Michael & Sam


---

### Appendix: The Quantitative Receipts (Show Your Work)

This architecture wasn't guessed; it was coded. Here are the exact Python backtesting scripts we wrote to validate our two core structural assumptions:

#### 1. Why 8% Position Sizing? (The Quarter-Kelly Code)
*If we just "guess" position sizing, we risk fat-tail ruin. The Kelly Criterion mathematically determines the optimal bet size. Because tech returns are non-normal, we use Quarter-Kelly to scale down the risk of bankruptcy.*

[👨‍💻 **View `kelly_tax_drag.py` on the Ghost Alpha GitHub**](https://github.com/mphinance/mphinance/blob/main/scripts/kelly_tax_drag.py)

**The Output Transcript:**
```text
Asset: NVDA | Quarter Kelly (Safe Practical Bet): 57.79%
Asset: MSFT | Quarter Kelly (Safe Practical Bet): 32.17%
Asset: COST | Quarter Kelly (Safe Practical Bet): 96.65%
```
*Conclusion: A low-volatility hyper-compounder like COST mathematically supports massive sizing. Even highly volatile NVDA supports 57% safe quarter-Kelly sizing in isolation. Therefore, allocating exactly **8%** per stock (1/8th to 1/12th Kelly) makes our 40% slice virtually immune to catastrophic mathematical ruin.*

#### 2. Why No International Diversification? (The Tax Drag Code)
*Diversification is good, but in a taxable account, foreign non-qualified dividends create massive unrecoverable tax drag that destroys the diversification premium.*

[👨‍💻 **View `10_year_monte_carlo.py` on the Ghost Alpha GitHub**](https://github.com/mphinance/mphinance/blob/main/scripts/10_year_monte_carlo.py)

**The Output Transcript:**
```text
VXUS 10-Year Gross CAGR (Tax-Advantaged): 8.64%
Annual Unrecoverable Tax Drag in Brokerage: 1.02%
VXUS 10-Year Net CAGR (Taxable Account): 7.61%
```
*Conclusion: You permanently bleed ~1.02% every year to non-qualified dividend taxes. A 7.61% net CAGR drags heavily on our 11.6% target anchor. This is why we avoid VXUS in taxable accounts and rely on Mega-Cap US tech for international exposure, as they already derive 40%+ of revenue globally.*
