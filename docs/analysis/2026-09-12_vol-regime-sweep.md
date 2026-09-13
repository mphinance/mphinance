# Vol Regime Sweep: VIX, Semis, Space, and Everything Else

**Date:** Saturday, 2026-09-12
**Data as of:** Friday 2026-09-11 close
**Method:** 4 parallel research agents (VIX/regime, semis, space, broad market) against TMPro MCP + verified web sources

---

## The one thing worth taking away

Vol rank and vol level have come completely apart, and they've come apart in the direction nobody expects. The loudest, most speculative corners of this market are trading at 52-week implied vol **floors**, while boring old-economy names are the only things on the board carrying rich premium by rank.

Everything below is a variation on that.

---

## VIX and the regime

**VIX 15.84, VVIX ~91, both down roughly 11% together** on Friday's in-line CPI (3.4% YoY vs 3.4% consensus).

Per the VVIX confirmation rule, that is confirming rather than diverging, so this is an honest post-catalyst vol crush and not a warning dressed up as calm. VIX sits in the bottom third of its 52-week band (13.38 low / 35.30 high).

### Term structure

Firm contango. VIX 15.84 vs VIX3M 18.60, IVTS **0.85**. The market is pricing this quiet as temporary and loading premium into the next 90 days.

That makes sense given what is stacked in the next six sessions:

| Event | Date | Verification |
|---|---|---|
| CPI (Aug data) | Fri 9/11, released | BLS release page + independent calendar |
| FOMC decision | **Wed 9/16, 2:00pm ET** | Two independent calendar sources |
| Quad witching / opex | **Fri 9/18** | Two independent sources |
| Next CPI (Sep data) | Thu 10/14, 8:30am ET | Two independent sources |

No unverified dates included. Anything not confirmed against a real source this session was left out.

### What is rotten underneath

- HYG **78.60**, below its 50dma of 79.49
- JNK **94.61**, below its 50dma of 95.69
- HY OAS **2.70%**, +7bps in 10 days
- RSP lagging SPY by ~180bps over 20 days
- 130 of 287 bullish earnings setups failed inside 14 days
- Market Health composite: **ELEVATED (3/7)**, two hard alerts

Credit is softening while the headline vol number naps. This is the metric that would actually change the regime.

### Gamma positioning

The index is long gamma. Small caps are short gamma.

| Index | Regime | Flip | Spot | Note |
|---|---|---|---|---|
| SPX | LONG_GAMMA | 7648.52 | 7656.85 | Max-gamma pin 7675, support 7625 |
| SPY | LONG_GAMMA | 764.61 | 764.29 | Essentially at flip |
| QQQ | LONG_GAMMA | 712.22 | +0.4% above | |
| IWM | **SHORT_GAMMA** | 290.72 | -0.6% below | Put skew 3.35 |
| DIA | **SHORT_GAMMA** | 525.33 | Just above | |

A shock gets absorbed at the index and amplified in small caps.

---

## On "VIX has nowhere to go but up"

Half right, and the half that is wrong is the expensive half.

**What supports it:** firm contango means the market already agrees. FOMC and opex are stacked. IV ranks are on the floor across the entire board. Credit is cracking underneath a sleepy VIX print.

**What kills it:** VIX 15.84 is not low, it is normal. The 52-week low is 13.38 and VIX has spent long historical stretches in the 11s. Vol can compress further and stay compressed for months, and the carry bleeds you the whole way down.

**The mechanical problem:** the contango that proves the thesis right is the same contango that charges for being right. IVTS at 0.85 means VXX and UVXY bleed hard on the roll, and they bleed most when the curve is steepest, which is now. Buying VIX products here is paying a premium for a view the entire market already holds.

**Better expression:** long optionality on the single names sitting at their own IV floors. Same convexity, no roll tax. The floor list is below.

---

## Semis: vol is dead exactly where the crowd is

| Ticker | Price | IV Rank | Zone |
|---|---|---|---|
| ARM | $264.79 | 31.3 | mid |
| INTC | $102.94 | 29.7 | mid |
| LRCX | $298.22 | 29.1 | mid |
| QCOM | $181.97 | 28.2 | mid |
| SMCI | $40.10 | 27.0 | mid |
| SOXL | $121.82 | 25.2 | mid |
| MU | $975.26 | 22.6 | cheap |
| SMH | $568.60 | 18.6 | cheap |
| MRVL | $236.10 | 18.1 | cheap |
| AMD | $516.13 | 15.3 | cheap |
| TSM | $433.24 | 5.6 | cheap |
| AMAT | $456.49 | 3.7 | floor |
| NVDA | $218.29 | 0.9 | floor |
| AVGO | $361.99 | 0.0 | clamped below band |

Eleven of fourteen are cheap or at the annual floor.

The correlation is near perfect and it is inverse: **the bigger and more owned the AI name, the deader its options.**

NVDA was the most newsy ticker in the entire group this week (Burry dumping puts, a reported ~$10B Anthropic IPO stake, hot CPI) and its implied vol is at a 52-week low. That is not an all-clear. That is "everyone already owns it and there is nothing left to reprice."

What premium exists lives in the second tier (ARM, INTC, LRCX, QCOM), and none of those three highest-rank names has an actual catalyst behind it. News pulls came back empty or generic. It is residual chop, not event premium.

**Earnings:** MU **9/30 AMC** is the only confirmed date in the 28-day window ($438.4M pre-earnings premium, sentiment split 51% bull / 49% bear). Every other name did not appear in the feed, which means unconfirmed, not absent.

**NVDA gamma:** spot 218.29, flip 217.36, so 0.4% into positive gamma. Max gamma pin at **220**. Resistance ladder 220 / 225 / 230 / 235, support 217.50 right at the flip.

---

## Space: the cleanest rank-vs-level split on the board

| Ticker | IV Rank | Absolute IV | 5-session IV move |
|---|---|---|---|
| LUNR | 27.3 | ~86% | +5.3% |
| LMT | 27.1 | ~24% | -2.1% |
| ARKX | 20.8 | n/a | n/a |
| RTX | 19.5 | ~23% | flat |
| UFO | 15.6 | n/a | n/a |
| IRDM | 12.5 | ~28% | -8.4% |
| RDW | 12.4 | ~86% | +14.5% |
| KTOS | 7.3 | ~60% | +15.0% |
| BKSY | 3.1 | ~78% | flat |
| RKLB | 2.3 | ~68% | +1.7% |
| ASTS | 1.8 | ~68% | -6.5% |
| PL | 0.0 (below band) | ~68% | -0.9% |
| SPCE | 0.0 (below band) | ~75% | **+16.7%** |
| SATS | insufficient history | n/a | n/a |

**RKLB and ASTS read as the cheapest vol they have offered in a year while still charging ~68%.** That is roughly 3x what LMT (24%) and RTX (23%) charge.

PL and SPCE are clamped *below* their 52-week floor and still run 68 to 75 percent. SPCE's absolute IV actually **rose 16.7%** over five sessions while its rank printed zero. The whole distribution shifted up underneath a rank that says nothing is happening.

### Short interest

| Ticker | Days to cover | Shares short | Change |
|---|---|---|---|
| **ASTS** | **7.25** | 64.1M | **+11.6%** |
| LUNR | 4.43 | 35.5M | -0.03% |
| RDW | 3.39 | 40.2M | +0.95% |
| RKLB | 3.06 | 45.4M | +2.21% |

ASTS is the one with fuel.

### Catalysts

Neither RKLB nor ASTS has one right now. RKLB had a routine 16th Electron launch and a generic CPI market-wrap mention, topCatalyst null. ASTS returned zero headlines at all.

**KTOS is the odd one worth a look:** 52 to 60% absolute IV against the primes' 23%, genuinely hotter rather than flattered by rank math.

---

## What else looks like that

The floor club. At or below their 52-week IV band while still carrying large nominal premium.

**Nuclear and power**
- OKLO: rank 0.0 (below band), ~69% IV
- SMR: rank 0.25, ~75% IV
- CEG: rank 7.7, ~40% IV

**Quantum and spec AI**
- IONQ: rank 0.0 (below band), ~73% IV
- QBTS: rank 1.4, ~69% IV
- BBAI: rank 0.7, ~66% IV
- SOUN: rank 1.3, ~60% IV

**Crypto-adjacent**
- IBIT: rank 7.9, ~36% IV
- RIOT: rank 13.9, ~80% IV
- MSTR: rank 25.3, ~68% IV

**Megacap tech**
- MSFT: rank **0.0**, 23.1% IV
- GOOGL: rank 13.8, ~28% IV
- NFLX: rank 18.1, ~31% IV
- AMZN: rank 21.4, ~29% IV
- TSLA: rank 21.4, 39.6% IV

**Retail favorites**
- SOFI: rank 6.5, ~46% IV
- PLTR: rank 15.1, ~45% IV

Same signature as RKLB and NVDA. Structurally re-based vol, cheap by history, still loud in dollar terms.

### The single most interesting data point in the sweep

**SMR moved -15.7% in one session on 3.2x relative volume with an IV rank of 0.2.**

Realized vol spiking while implied stays pinned at the floor is an IV repricing lag. Worth watching.

---

## What doesn't look like that

The rich list is almost comically boring.

| Ticker | IV Rank | IV Level |
|---|---|---|
| XOM | **61.4** | ~29% |
| TLT | 54.5 | 11.1% |
| XLE | 52.2 | ~29% |
| JNJ | 51.3 | ~22% |
| AAPL | 44.7 | ~25% |
| FCX | 43.6 | ~46% |
| KO | 43.5 | ~18% |
| XLP | 39.6 | ~12% |
| GDX | 39.1 | ~43% |
| META | 38.7 | ~36% |
| GME | 35.2 | ~44% |
| COIN | 33.0 | ~65% |

Energy, rates, staples, pharma. Quiet names whose premium is expensive relative to their own quiet history.

**XLE is also the only sector besides XLK flagged all-cylinders bullish** on flow plus technicals plus price. Rich vol there reflects real two-sided positioning around a live trend, not stale premium. That is the one place on the board where rich vol and a real move agree.

**Metals are the no-edge middle:** GLD 28.8, SLV 32.4, GDX 39.1, NEM 29.2, FCX 43.6. Nothing to do. FCX's +12% five-day IV pop is the only watch item.

### Sector flow context

- Macro regime: **RISK-ON LEAN**. SPX 7656.98, net options flow +$455M into calls, call/put 2.03.
- All-cylinders sectors (flow + technicals + price aligned): **XLK and XLE only.**
- Broad divergence signature: ITA, SHLD, TAN, KRE, LIT, XLV, XLU, XLB, XLP, XLI, BOTZ, QTUM, XLY, XLRE, XLC, CIBR all show bullish or flat price with bearish TD technicals.
- Gamma wall events: SMH cleared its $570 call wall (held 3 sessions). XLF lost $57 put support. XLV and XLP breaking $165 / $83 put support.

---

## Data caveats

These matter more than usual on this pull.

1. **Everything is Friday 9/11's close.** It is Saturday afternoon.
2. **The unusual-activity feed returned zero rows market-wide** at both score thresholds (70 and 60), including ticker-filtered scans. That is a weekend gap, not a "no flow" signal. Do not read it in either direction.
3. **`get_iv_rank` pulls from CBOE for most tickers, and CBOE withholds raw ATM IV and percentile.** Most "IV level" figures above are the tool's self-tracked 5-day proxy, which sits on a different scale than atmIv. Ranks are solid. Levels are approximate.
4. **A lot of names clamped below their 52-week band simultaneously.** Given VIX is genuinely in the bottom third of its own year, that is probably real, and there is honest dispersion in the data (0 to 61) rather than one verdict printing everywhere, so it does not smell like the falsy-default bug class. But it is enough simultaneous floor-clamping to be worth knowing about.
5. **The risk-on read and the bearish index put/call are not a contradiction.** Single names get call-bought (call/put 2.03) while the index gets hedged into FOMC and opex (SPY 1.86, QQQ 2.57, IWM 2.16). The $73.4M SPY 766 put print was 9/11 expiry, already dead, ignore it.
6. **No HV or IV-HV spread anywhere.** The tool does not return those fields for any ticker. Not omitted, not available.
7. **SATS has no IV rank history at all** (insufficient_history). Cannot be characterized either way.

---

## What I would actually do with this

### Do not sell premium in the floor club on rank alone

The wheel screener will keep handing over SMR, OKLO, SOUN, RGTI, MARA, CIFR, WULF, IREN, CLSK at 53 to 95% annualized ROC, all grade A, because their absolute IV is 60 to 75%. The dollars are real.

But that is selling the cheapest vol those names have offered in twelve months, on tickers that can drop 15% in a session. SMR just proved it.

If the shares are wanted anyway, that is a defensible wheel. If the sale is purely for credit, it is the least compensation available all year for that exact risk.

### The rich-vol premium sale is XOM, not the space names

IV rank 61.4, atm IV 29.4%, a real uptrend behind it, and energy is one of only two sectors with flow and technicals aligned.

Tool-derived structure: 155p/150p to 180c/185c iron condor, POP 65%, $164 max credit against $336 risk.

### If long optionality is the play, this is the cheapest it has been

RKLB, ASTS, OKLO, IONQ, SMR, and megacap tech are all at or below their annual IV floors going into FOMC Wednesday and quad witching Friday, with contango saying the market itself expects vol back. The asymmetry is sitting right there, and it does not carry the VIX-product roll bleed.

OKLO tool-derived structure: 35/40 bull call debit spread, $197 risk / $303 max profit, POP 43%.

### Watch credit, not VIX

HYG and JNK below the 50dma with spreads widening while VIX prints 15.84 is the actual tell in this data.

---

## Open questions

- Does the SMR realized-vs-implied gap close by IV repricing up, or does realized just fade back? Worth tracking as a live case for the whole floor club.
- Does ASTS's 7.25 days-to-cover plus 11.6% short build matter without a catalyst in the feed? No news at all is unusual for that name.
- Re-pull the unusual-activity feed Monday to confirm the zero-row result was a weekend artifact.
