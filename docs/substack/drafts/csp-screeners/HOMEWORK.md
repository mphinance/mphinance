# CSP screener homework — 2026-08-30

Working notes for the "screeners I actually use" post. All five presets re-run live against
`api.traderdaddy.pro/api/v1/screeners/csp-wheel/run`. Numbers are pulled independently and
reproduce Michael's screenshots and CSV export exactly.

Screenshots: `batch1_1..5.png` (Small-Account, Blue-Chip, full filter panel), `batch2_1..3.png`
(High-IV Harvest, Wheel & Own, Earnings Gamble). Export: `Cash_Secured_Puts-2026-08-30.csv`.

---

## Finding 1: the screen didn't find high IV. It found Friday's wreckage.

**17 of the 18 names on the watchlist fell in the last session (Friday 2026-08-28).**
Average **-6.9%**, median -7.7%, worst -13.2%. Only TENB was green, by 0.14%.

Verified against daily closes, Thursday → Friday:
BTDR 11.33 → 10.32 · CIFR 16.77 → 15.17 · WULF 16.49 → 15.35 · NVTS 12.51 → 11.49.

This reframes everything below. The screen is not discovering names that happen to carry
rich premium. It is discovering names whose premium got rich *on Friday*, because they got
hit on Friday. IV is elevated as a consequence of the damage, and a premium-weighted
EdgeScore walks straight into it.

Which means the real question the screen is silently asking you is: **was Friday the end of
it, or the start?** Nothing in the tool answers that. That is the honest limit of a screener
and it belongs in the post.

Relative volume corroborates: TENB 36.9× · SLS 14.6× · KLAC 7.6× · CLSK 7.3× · S 2.2× · IREN 2.0×.
These are not quiet names having a quiet week.

## Finding 2: "10% OTM" is a meaningless number — convert it to sigmas

The cushion only means something relative to how far the stock is expected to travel before
expiry. One-sigma move over the holding period = `IV × √(DTE/365)`. Divide the OTM distance
by that and you get **how many standard deviations of protection you actually bought.**

| Sym | Px | Strike | DTE | IV | OTM % | 1σ move | **σ of cushion** | PoP | Fri % | Preset |
|-----|----|--------|-----|----|-------|---------|------------------|-----|-------|--------|
| SLS | 13.21 | 12.50 | 19 | 124 | 5.4% | 28.3% | **0.19σ** | 65% | -13.2 | Wheel & Own |
| CLSK | 11.66 | 11.00 | 19 | 81 | 5.7% | 18.5% | **0.31σ** | 69% | -10.0 | Wheel & Own |
| MARA | 10.67 | 10.00 | 19 | 82 | 6.3% | 18.7% | **0.34σ** | 70% | -10.1 | Wheel & Own |
| WULF | 15.35 | 14.50 | 12 | 74 | 5.5% | 13.4% | **0.41σ** | 73% | -6.9 | SAW + W&O + EG |
| HIMS | 28.84 | 27.00 | 19 | 63 | 6.4% | 14.4% | **0.44σ** | 73% | -8.9 | Wheel & Own |
| RIOT | 18.99 | 17.50 | 19 | 73 | 7.8% | 16.7% | **0.47σ** | 74% | -9.1 | Wheel & Own |
| RDW | 10.87 | 10.00 | 19 | 72 | 8.0% | 16.4% | **0.49σ** | 75% | -3.5 | Wheel & Own |
| BTDR | 10.32 | 9.50 | 12 | 88 | 7.9% | 16.0% | **0.50σ** | 75% | -8.9 | SAW + W&O |
| TENB | 37.67 | 35.00 | 19 | 61 | 7.1% | 13.9% | **0.51σ** | 75% | +0.1 | Wheel & Own |
| NVTS | 11.49 | 10.50 | 12 | 79 | 8.6% | 14.3% | **0.60σ** | 78% | -8.2 | SAW + EG |
| CIFR | 15.17 | 13.50 | 12 | 92 | 11.0% | 16.7% | **0.66σ** | 79% | -9.6 | SAW + EG |
| ORCL | 150.85 | 136.00 | 12 | 77 | 9.8% | 14.0% | **0.71σ** | 80% | -0.7 | Earnings Gamble |
| S | 21.54 | 20.00 | 12 | 55 | 7.1% | 10.0% | **0.72σ** | 81% | -5.2 | Wheel & Own |
| IREN | 35.45 | 32.00 | 12 | 73 | 9.7% | 13.2% | **0.74σ** | 81% | -12.5 | Earnings Gamble |
| APLD | 25.34 | 23.00 | 12 | 67 | 9.2% | 12.1% | **0.76σ** | 81% | -7.7 | Earnings Gamble |
| FLEX | 110.50 | 100.00 | 19 | 49 | 9.5% | 11.2% | **0.85σ** | 83% | -4.2 | Blue-Chip Income |
| KLAC | 175.54 | 158.00 | 19 | 48 | 10.0% | 11.0% | **0.91σ** | 85% | -4.5 | Blue-Chip Income |
| UAL | 110.60 | 100.00 | 19 | 42 | 9.6% | 9.6% | **1.00σ** | 86% | -1.6 | Blue-Chip Income |

Sorted by sigma, and **profit probability sorts almost perfectly with it** — which is the
proof the frame is right, not a coincidence.

The punchline: **UAL's 9.6% cushion is worth more than CIFR's 11.0% cushion.** The bigger
percentage is the thinner protection. And SLS, the highest headline return in the entire
study at 3.32%/week, buys you **0.19σ** — a 5.4% cushion against a 28.3% expected move.
That is not a cushion. It is a coin flip with a fee attached.

Average cushion by preset, worst to best:

| Preset | Avg σ | n |
|---|---|---|
| Wheel & Own | 0.44σ | 10 |
| Small-Account Weeklies | 0.54σ | 4 |
| Earnings Gamble | 0.65σ | 6 |
| Blue-Chip Income | **0.92σ** | 3 |

This is the single most useful artifact from the study, and the math is arithmetic anyone
can check on a phone. It should be the free lesson in the post.

## Finding 3: four of the five presets are the same trade

**Four of the five presets are five different ways to sell puts on the same complex.**

Across the four presets that returned anything, 23 result slots, 18 unique tickers.
**14 of 23 slots (61%) are the AI-datacenter-power complex** — bitcoin miners pivoting to
HPC, plus the picks-and-shovels around them. Excluding Blue-Chip Income it is **14 of 20.**

| Preset | Count | Names |
|---|---|---|
| Small-Account Weeklies | 4 | BTDR CIFR WULF NVTS |
| Blue-Chip Income | 3 | FLEX UAL KLAC |
| High-IV Harvest | **0** | — |
| Wheel & Own | 10 | CLSK MARA BTDR WULF RIOT RDW HIMS SLS TENB S |
| Earnings Gamble | 6 | CIFR ORCL IREN WULF NVTS APLD |

WULF shows up in **three of the four** non-empty presets. BTDR, CIFR and NVTS each show up in two.

**Why:** every preset except Blue-Chip Income has an IV *floor* (35 / 55 / 60) and no
effective IV *ceiling*. `max_iv` defaults to 0 = off. An IV floor with no ceiling is an
instruction to go find whatever the market is most afraid of, and right now that is the
power/compute complex. Blue-Chip Income is the only preset that sets a ceiling which
actually binds (IV 25-50), and it is the only preset that escapes.

**`max_iv` is the most important filter in the tool and it ships off.** That is the
sentence the post is built around.

---

## Preset 1: Small-Account Weeklies

`max_capital 5000 · strike_otm_pct 0.10 · max_dte 14 · weekly_only true · min_roc_weekly 1.25`
Funnel **50 → 4**. Avg weekly ROC 1.73%, avg score 89.1.

| # | Sym | Px | Strike | Exp | DTE | Credit | Capital | wROC | Ann | PoP | Δ | IV | RSI | ADX | Put wall | Opt vol | Quote | Score | Adj |
|---|-----|----|--------|-----|-----|--------|---------|------|-----|-----|---|----|-----|-----|----------|---------|-------|-------|-----|
| 1 | BTDR | 10.32 | 9.5 | 09-11 | 12 | $35 | $950 | 2.15% | 112% | 75% | -0.29 | 88.2 | 47.1 | 17.3 | 5,075 | 582 | wide | 100.5 | +3 |
| 2 | CIFR | 15.17 | 13.5 | 09-11 | 12 | $40 | $1,350 | 1.73% | 90% | 79% | -0.21 | 92.5 | 41.0 | 11.4 | 7,785 | 1,941 | wide | 96.3 | +4 |
| 3 | WULF | 15.35 | 14.0 | 09-11 | 12 | $34 | $1,400 | 1.42% | 74% | 78% | -0.24 | 75.2 | 40.5 | 24.6 | 657 | 909 | **firm** | 84.8 | +2 |
| 4 | NVTS | 11.49 | 10.5 | 09-11 | 12 | $30 | $1,050 | 1.64% | 86% | 78% | -0.25 | 78.5 | 39.4 | 13.1 | 258 | 466 | wide | 74.6 | 0 |

All four graded **A**. All four cost **$4,750** together, which fits under the $5,000 cap.

### This is not four trades

BTDR = Bitdeer. CIFR = Cipher Mining. WULF = TeraWulf. Three bitcoin miners pivoting to
AI/HPC datacenters, all three filed under the same `Technology Services / Data Processing
Services` code. NVTS = Navitas, GaN power semis — looks like a diversifier, is the same
datacenter-power trade one layer down the stack.

Measured 60-session daily-return correlation:
**CIFR-WULF 0.87 · BTDR-CIFR 0.73 · BTDR-WULF 0.72 · BTDR-NVTS 0.65 · WULF-NVTS 0.63 · CIFR-NVTS 0.58**

90-day change: BTDR -14.6% · CIFR -15.9% · WULF -22.4% · NVTS -25.0%.

Sell all four and you have not spread $4,750 across four names. You have put $4,750 on one
theme with a 10% cushion, in a complex already down 15-25% in a quarter.

### Why the sort is backwards

EdgeScore = **Premium 40% / ROC 25% / Technical 20% / Liquidity 15%.** Premium is the
heaviest weight and premium is fear. BTDR ranks #1 (100.5) because it pays most, and it pays
most because at Δ -0.29 it is the likeliest of the four to come get you — 75% PoP, worst on
the list. The grade-adjustment column already disagrees with the sort: CIFR +4, BTDR +3,
because the adjustment rewards Δ proximity to 0.20 and a real put wall.

### My ranking (inverted from the screen's)

1. **CIFR** — best on everything that decides assignment: Δ -0.21 (nearest 0.20), 79% PoP,
   -13.65% breakeven cushion (deepest), 7,785 OI put wall, 1,941 option volume, ADX 11.4 —
   the most rangebound name here, which is what a put seller wants. Knock: wide quote, and
   92.5% IV is the highest on the list.
2. **BTDR** — cheapest ($950), best ROC (2.15%), healthiest tape (RSI 47.1, only -3.9% in
   30d). Knock: fattest delta, worst PoP, and 582 contracts of option volume is thin enough
   that a wide spread costs real basis points on a $35 credit.
3. **WULF** — the only **firm** quote (spread ≤ 30% of mid), so you fill near mid instead of
   donating the spread. Knock: ADX 24.6 is the highest here and it is trending *down*,
   -15.5% in 30 days. Trending into your strike is the one thing a CSP cannot tolerate.
   657 OI is a thin floor.
4. **NVTS** — 258 contracts of OI under the strike is not a put wall, it is a rounding error.
   Only name with **zero** grade adjustment, weakest RSI (39.4), worst 90-day (-25%).

**The answer is pick one.** CIFR at $1,350 leaves the rest of the account in cash to handle
assignment. Selling all four is not a portfolio.

---

## Preset 2: Blue-Chip Income

`min_price 80 · max_capital 50000 · max_adx 25 · min_roc_weekly 0.25 · golden_cross true
· min_grade B · min_iv 25 · max_iv 50`
Funnel **50 → 3**. Avg weekly ROC 0.45%, avg score 55.2.

| # | Sym | Px | Strike | Exp | DTE | Credit | Capital | wROC | Ann | PoP | Δ | IV | RSI | ADX | Wall | Quote | Score | Grade |
|---|-----|----|--------|-----|-----|--------|---------|------|-----|-----|---|----|-----|-----|------|-------|-------|-------|
| 1 | FLEX | 110.50 | 100 | 09-18 | 19 | $148 | $10,000 | 0.54% | 28.3% | 83% | -0.20 | 49.0 | 41.9 | 18.0 | 5,555 | wide | 61.9 | B |
| 2 | UAL | 110.60 | 100 | 09-18 | 19 | $80 | $10,000 | 0.30% | 15.5% | 86% | -0.13 | 42.4 | 37.0 | 18.5 | 6,129 | firm | 52.6 | B |
| 3 | KLAC | 175.54 | 158 | 09-18 | 19 | $220 | $15,800 | 0.51% | 26.7% | 85% | -0.18 | 47.7 | 35.9 | 18.1 | 6,146 | wide | 51.2 | B |

### The comparison that makes the post

Small-Account Weeklies grades **A** across the board at **75-79%** profit probability.
Blue-Chip Income grades **B** across the board at **83-86%.**

The screen calls the less-likely-to-work trades A and the more-likely-to-work trades B,
because grade derives from EdgeScore and EdgeScore is 40% premium. **Grade measures how much
you get paid, not whether you keep it.** Those two facts belong in adjacent sentences.

Also: three names, three genuinely different sectors (contract electronics / airlines /
semicap), all Δ -0.13 to -0.20, all ~6,000 OI walls. Blue-Chip gives you the diversification
Small-Account Weeklies only pretends to.

---

## Preset 3: High-IV Harvest — returns ZERO

`max_capital 50000 · strike_otm_pct 0.15 · min_profit_probability 80 · min_iv 55 · max_iv 100`
Funnel **50 → 0.** Empty list.

The preset that markets itself hardest — "fat premium, 15% OTM, 80%+ probability of profit" —
is the one that returns nothing. I diagnosed which constraint kills it by relaxing one at a time:

| Change | Results |
|---|---|
| As shipped | **0** |
| Drop the 80% PoP requirement | 3 (CIFR, NVTS, SMR) |
| Drop the IV band, keep 80% PoP | **0** |
| Keep everything, lower ROC floor 1.0% → 0.25% | **14** (IREN CLSK ORCL WULF APLD SMCI MSTR RKLB IONQ QBTS INTC AFRM …) |

So the binding constraint is the **inherited 1% weekly ROC default**, not the IV band.
High-IV Harvest is asking for 1% a week, 15% out of the money, at 80% probability of profit.
Those three numbers cannot be simultaneously true in this tape. 1%/week at 15% OTM is roughly
52%/yr on a cushion that deep, and nothing pays that unless it is genuinely likely to move
15%, which is exactly what 80% PoP forbids.

**An empty screen is the tool refusing to lie to you.** Every other CSP scanner would have
quietly loosened something and handed you a list. The fix is to lower the ROC ask, not to
widen the risk — drop `min_roc_weekly` to 0.25% and 14 names appear.

This is the most honest thing in the product and it should be written as a feature, not
apologised for.

---

## Preset 4: Wheel & Own

`max_capital 50000 · strike_otm_pct 0.07 · golden_cross true · ema_atr_filter true · min_grade B`
Funnel **50 → 10**. Avg weekly ROC 1.74, avg score 85.5.

| # | Sym | Px | Strike | DTE | Credit | Capital | wROC | Ann | PoP | Δ | IV | ADX | Wall | Opt vol | Quote | Score | G |
|---|-----|----|--------|-----|--------|---------|------|-----|-----|---|----|-----|------|---------|-------|-------|---|
| 1 | CLSK | 11.66 | 11.0 | 19 | $56 | $1,100 | 1.89% | 98.7% | 69% | -0.33 | 81.4 | 10.8 | 10,422 | 3,792 | firm | 103.9 | A |
| 2 | MARA | 10.67 | 10.0 | 19 | $50 | $1,000 | 1.82% | 95.1% | 70% | -0.32 | 81.8 | 19.7 | 34,359 | 15,351 | firm | 103.2 | A |
| 3 | BTDR | 10.32 | 9.5 | 12 | $35 | $950 | 2.15% | 112.1% | 75% | -0.29 | 88.2 | 17.3 | 5,075 | 582 | wide | 100.5 | A |
| 4 | WULF | 15.35 | 14.5 | 12 | $50 | $1,450 | 1.99% | 103.8% | 73% | -0.32 | 74.4 | 24.6 | 7,597 | 909 | firm | 99.0 | A |
| 5 | RIOT | 18.99 | 17.5 | 19 | $64 | $1,750 | 1.35% | 70.3% | 74% | -0.29 | 72.8 | 11.5 | 5,638 | 4,960 | firm | 87.6 | A |
| 6 | RDW | 10.87 | 10.0 | 19 | $40 | $1,000 | 1.47% | 76.8% | 75% | -0.30 | 72.5 | 19.3 | 1,269 | 1,120 | firm | 86.8 | A |
| 7 | HIMS | 28.84 | 27.0 | 19 | $90 | $2,700 | 1.22% | 63.7% | 73% | -0.30 | 63.2 | 11.4 | 5,504 | 5,688 | firm | 85.0 | A |
| 8 | SLS | 13.21 | 12.5 | 19 | $112 | $1,250 | 3.32% | 172.9% | 65% | -0.35 | 124.3 | 34.7 | 1,758 | 880 | wide | 68.6 | B |
| 9 | TENB | 37.67 | 35.0 | 19 | $102 | $3,500 | 1.08% | 56.3% | 75% | -0.28 | 61.3 | 15.1 | **59** | 336 | wide | 63.1 | B |
| 10 | S | 21.54 | 20.0 | 12 | $38 | $2,000 | 1.09% | 57.0% | 81% | -0.22 | 55.1 | 23.5 | **41** | 73 | wide | 57.1 | B |

Notes:
- Described as "close strikes on quality you'd happily hold through a dip." It returns
  **CLSK, MARA, BTDR, WULF, RIOT** in the top five — five bitcoin miners. "Quality" is doing
  no work here: the only quality gates are `golden_cross` + `ema_atr_filter` + grade B, and
  miners currently pass a golden cross. If you would not happily own CLSK at $11, this
  preset is not describing your trade.
- **Worst profit probabilities of any preset: 65-75%.** That is correct behaviour for a
  screen named "Own" — 7% OTM means Δ -0.28 to -0.35 and you are supposed to *want* the
  shares. But it deserves saying out loud, because "quality you'd happily hold" reads as
  the safe preset and it is the most assignment-prone one in the set.
- **SLS is a trap.** 3.32% weekly / 172.9% annualized at 124.3% IV, ADX 34.7, 65% PoP, wide
  quote. It has the highest headline return in the entire study and the lowest probability
  of working. Good illustration figure.
- **TENB (59 OI) and S (41 OI)** barely clear the hard OI ≥ 25 floor. Those are quotes, not
  markets. Argument for raising `min_open_interest` off zero — the built-in floor of 25 is
  far too low to protect anyone.
- MARA is the liquidity standout: 34,359 OI wall, 15,351 option volume, firm quote. If you
  are going to express this theme, express it in the name where you can actually get out.

---

## Preset 5: Earnings Gamble

`max_capital 50000 · weekly_only true · include_earnings_flagged true · min_iv 60`
Funnel **50 → 6**. Avg weekly ROC 1.38, avg score 81.4.

| # | Sym | Px | Strike | DTE | Credit | Capital | wROC | Ann | PoP | Δ | IV | Wall | Opt vol | Quote | Score | G |
|---|-----|----|--------|-----|--------|---------|------|-----|-----|---|----|------|---------|-------|-------|---|
| 1 | CIFR | 15.17 | 13.5 | 12 | $40 | $1,350 | 1.73% | 90.1% | 79% | -0.21 | 92.5 | 7,785 | 1,941 | wide | 96.3 | A |
| 2 | ORCL | 150.85 | 136.0 | 12 | $315 | $13,600 | 1.35% | 70.5% | 80% | -0.23 | 77.0 | 2,030 | 9,719 | firm | 85.8 | A |
| 3 | IREN | 35.45 | 32.0 | 12 | $63 | $3,200 | 1.15% | 59.9% | 81% | -0.21 | 72.6 | 2,167 | 10,793 | firm | 85.4 | A |
| 4 | WULF | 15.35 | 14.0 | 12 | $34 | $1,400 | 1.42% | 73.9% | 78% | -0.24 | 75.2 | 657 | 909 | firm | 84.8 | A |
| 5 | NVTS | 11.49 | 10.5 | 12 | $30 | $1,050 | 1.64% | 85.5% | 78% | -0.25 | 78.5 | 258 | 466 | wide | 74.6 | A |
| 6 | APLD | 25.34 | 23.0 | 12 | $40 | $2,300 | 1.01% | 52.9% | 81% | -0.21 | 66.9 | 470 | 1,328 | wide | 61.4 | B |

**Not one of the six is actually flagged for earnings.** `earningsFlag` is empty and
`earningsDate` is null across the board. That is not a bug — it is 30 August, earnings
season is over, and there is nothing reporting inside 12 days that clears a 60% IV floor
with weekly options. So today the "Earnings Gamble" preset is just High-IV Weeklies wearing
a different hat.

Worth saying plainly in the post: **this preset is seasonal.** Run it in the second week of
a reporting cycle and it is a different tool. Run it now and the ⚡ column is empty, which
means the thing you are being paid for is not the event you think it is.

Interesting: ORCL is the only large-cap in any non-blue-chip preset, and it is here purely
because 77% IV on a $151 stock is extraordinary. That one is worth its own paragraph.

---

## The filter panel: 28 parameters, and the ones that matter

- **`max_capital` silently rewrites `max_price`** (cap ÷ 100, lower wins). At $5,000 the
  fixed criteria come back "Price: 5 - 50," not the 5-200 default. The single most
  misunderstood knob: the small-account preset is a *price filter wearing a capital-filter
  costume*, and that is precisely why it dumps you into low-priced high-beta names every
  single time.
- **`min_iv` / `max_iv`** — the real style dial, and the headline of this whole study. Floor
  with no ceiling = go find the scariest thing on the tape. Blue-Chip Income is the only
  preset with a binding ceiling and the only one that escapes the miner complex. Cynce's
  elevated band is 55-75.
- **`min_roc_weekly`** is the throttle, and it is what silently empties High-IV Harvest.
  1.25%/week is ~65%/yr; nothing calm clears that bar. Raising this is functionally the same
  as raising your IV floor.
- **`strike_otm_pct`** sets the cushion, but **delta is what actually reports the risk.**
  10% OTM at 90% IV is Δ -0.29. 10% OTM at 42% IV is Δ -0.13. Same "10%," radically
  different trade. This is the best single teaching point in the post.
- **`min_open_interest`** sits on top of a hard floor of OI ≥ 25 that runs regardless of the
  slider. 25 is far too low — NVTS cleared it at 258, S at 41. Set this to ~500 and most of
  the junk evaporates.
- **`quoteQuality`** is not a filter, it is a returned field: firm / wide / indicative.
  Most underused number on the card. On a $0.30 credit, a wide spread is a tax you pay twice.
- **`golden_cross` + `ema_atr_filter`** are the only "quality" gates in the tool, and Wheel &
  Own proves they are not enough — bitcoin miners pass both right now.
- **`weekly_only`** overrides `max_dte` entirely.
- **`exclude_earnings`** (on, 14-day buffer) + **`include_earnings_flagged`** is the Earnings
  Gamble mechanism: keep them, flag them with ⚡, rather than dropping them.
- **`min_profit_probability`** is off by default (0). Turning it on is the fastest way to
  make the tool honest — it is what exposes that High-IV Harvest is asking the impossible.

---

## Structural suggestion for the post

Open with the empty screen. "The best-sounding preset I built returns zero results, and
that's the one I trust most." Then the miner overlap. Then the A-vs-B grade inversion. Then
the paywall break, then the ranked small-account picks.

Give away: the `max_capital` → `max_price` trap, the delta-vs-OTM% point, the empty High-IV
Harvest diagnosis. Those are the generous, checkable, no-subscription-needed lessons.
Paywall: the ranked four, the correlation matrix, and which one you're actually selling.

## Open items

- Michael's full watchlist export (pending).
- **Re-pull every quote on publish day.** These marks are 2026-08-30, a weekend. The 09-11
  chain will have moved and the CSV `Change %` column reads 0.00% because the market is shut.
- Decide whether to name a real trade. If yes, sign off the numbers first per the trade-rule
  block convention.

---

## The two share links

`https://www.traderdaddy.pro/watchlist/share/OeJbcgc5`
`https://www.traderdaddy.pro/watchlist/share/1FrEWEAQ`

Endpoint: `GET https://api.traderdaddy.pro/api/watchlist/share/{id}` (no auth required —
public by design).

**They are the same list.** Byte-identical payloads: same title `CSP20260904`, same 50
tickers in the same order, same 50 notes, same enrichment. The only differences are
`shareId`, `viewCount`, and `createdAt` — **13:15:29.787Z vs 13:15:35.109Z, 5.3 seconds apart.**

So it is not two lists. It is one list shared twice. **The share-create endpoint is not
idempotent** — every click mints a fresh shareId instead of returning the existing one for
that list. Minor bug, but it means share links accumulate silently and there is no way to
revoke one, which matters because of the next item.

### ⚠️ The share link publishes his whole book

The list is titled `CSP20260904` and the UI says "18 on this list." The **share payload
contains 50 tickers.** 18 are from the CSP screens. The other **32 are his own positions and
trade history**, carried in the `notes` field:

- **Open positions, in plain text:** `RR — 400 sh + Sep 11 '26 $2.5 C + Sep 18 '26 $2 C —
  open` · `SOFI — Sep 18 '26 $20 C — open` · `BTG — 20 sh + Sep 18 '26 $5 P — open` ·
  `ONDS — 60 sh — open`
- **2026 transaction counts and last-trade dates on 28 more names:** DDD 32 txns (last
  2026-05-15), GDXW 23, UAMY 18, VBIL 15 (last 2026-08-06), BITF 10, BOXX 8, ASM 6, SLV 5
  options (last 2026-08-12), and so on.

Anyone with the URL — no login — gets share size, strikes, expiries and activity cadence.
**Do not put either link in the post as-is.** Two options: build a clean list containing only
the 18 screen names and share that, or ask the team to scope the share payload to the
selected list instead of the whole board. I would do both.

This is worth filing as a product bug regardless of the post: *share scope leaks
cross-list notes.*

## The watchlist notes are better attribution than my own tally

The tool auto-annotated each name with which preset(s) surfaced it, which independently
confirms the overlap finding and is cleaner than my count:

- **WULF — Small-Account Weeklies + Wheel & Own + Earnings Gamble** (three of five presets)
- **BTDR** — Small-Account Weeklies + Wheel & Own
- **CIFR** — Small-Account Weeklies + Earnings Gamble
- **NVTS** — Small-Account Weeklies + Earnings Gamble

23 slots across 5 presets collapse to 18 unique names. Screenshot that annotation — it makes
the argument for me, in the product's own voice.

## ORCL is the best idea in the whole study and score does not find it

`Sell ORCL 136P, expiry 2026-09-11, 12 DTE, $315 credit, 1.35%/wk, 80% PoP, 0.71σ cushion, IV 77%.`

ORCL is the only large-cap anywhere outside Blue-Chip Income, and its 77% IV on a $151 stock
is not fear about the business — the enriched feed puts **earnings at 2026-09-14, 15 days
out.** The put expires **2026-09-11, three days before the print.**

So the trade is: sell IV that is inflated purely by earnings anticipation, and be out of the
contract before the event that could hurt you. The elevated vol is the whole payment and you
never take the binary risk that created it.

It also explains why ORCL slipped into Earnings Gamble at all: at 15 days it sits **one day
outside** the preset's 14-day earnings buffer, so `exclude_earnings` never touched it and the
⚡ flag never fired. An off-by-one in your favour.

It ranks 2nd of 6 by score, and nothing in the scoring model knows why it is interesting.
That is a good argument for the post's larger point: the screen narrows the field, the
operator picks the trade.

🚨 **Verify the 2026-09-14 earnings date independently before this goes in a post.** The dev
econ-calendar feed has served wrong dates before and it cost a deleted post on 6/28. No
unverified dates in published content.

## Revised structure for the post

1. **Open on Friday.** 17 of 18 names down, average -6.9%. The screen found the wreckage,
   not the opportunity. Honest, and it earns the right to everything after it.
2. **The sigma table.** Free. It is the most useful thing here and it is checkable arithmetic.
3. **The empty screen.** High-IV Harvest returns zero and why that is the feature.
4. **The A-vs-B grade inversion.** Grade measures what you get paid, not what you keep.
5. Paywall.
6. **The overlap** — four presets, one trade, WULF in three of them — plus the ranked
   small-account picks and the correlation matrix.

Give away the process. Paywall the position.
