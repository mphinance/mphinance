# KD / Kyndryl — article outline

Date: 2026-09-05 (Fri). Spot $13.15 (9/4 close). Not held. Nothing placed.

---

## First: two things in your premise need fixing

**1. "Low PE" is not true the way you mean it.**

- Trailing P/E: **~36x** (EPS $0.363). That is not cheap.
- Forward P/E: **7.1x**. That is the number you saw.
- The gap between those two is the whole article. Forward 7x is built on
  management's *adjusted pretax income* guide of $600-700M. GAAP Q1 FY27 was a
  **net loss of $55M, ($0.25)/share**.
- So the "low PE" is an adjusted-earnings number on a company currently losing
  money on a GAAP basis. Do not lead with P/E. You will get called on it.

**The metric that actually is cheap is free cash flow.** FY27 guide is
$400-500M FCF against a $2.86B market cap. That is a **14-17% FCF yield on
equity**, ~8-10% on EV ($4.83B: $4.07B debt less $2.10B cash). That is the real
bull case and it is defensible.

**2. "Avantis is buying" is true but smaller than it sounds.**

Verified against TickerTrace live holdings, as-of 2026-09-04:

| Fund | Shares | Weight | Day change |
|---|---|---|---|
| AVUV | 1,400,614 | 0.059% | **+32,725 (+2.4%)** |
| AVUS | 204,382 | 0.019% | 0 |
| AVSC | 149,973 | 0.064% | 0 |

- Three Avantis funds hold it. All three. Your read was right.
- But: AVUV is a **systematic small-cap value** fund. It owns KD because KD
  screens cheap on book value, not because a PM has a thesis. 0.059% weight is
  a rounding error in that portfolio.
- Total Avantis stake across all three ≈ 1.75M shares = **0.8% of shares out**,
  about $23M. Not a signal of conviction. It is a factor screen doing its job.
- **Trap avoided:** the API flags AVSC and AVUS as `type: NEW` with
  `previousShares: 0`. That is the provider file-refresh artifact, not new
  positions. The whole `/changes` feed that day shows CGDV/MSFT, CGUS/NVDA etc.
  as brand new 7% weights. Only the AVUV +32,725 is a real day-over-day move.

**Honest framing for the post:** "The quant value funds own it, which tells you
it screens cheap. It does not tell you it is safe." That is the line.

---

## The spine

> The one number that makes Kyndryl look cheap is free cash flow. The one thing
> the SEC is investigating is how Kyndryl manages the timing of its cash.

That is the article. Everything else is support.

---

## Section 1 — Open on the tape, not the story

- July 2025: $44. September 2025: $33. January 2026: $23.
- **The stock had already lost 45% before anything happened.** Six straight
  months of lower highs. The market was voting long before the news.
- **Feb 9, 2026:** opens $10.84, prints a low of $10.10, closes $10.59 on
  **61 million shares** against a 1.2M-share normal day. Down 55% in a session.
- What dropped that morning: KD told the SEC it could not file its December
  quarter on time, disclosed an SEC Division of Enforcement inquiry, flagged
  anticipated material weaknesses in internal controls, and the CFO
  (David Wyshner) and general counsel (Edward Sebold) left effective immediately.
- Then the guidance cut: constant-currency revenue from +1% to as much as -3%,
  and FY26 free cash flow from ~$550M to $325-375M. They cut the cash flow guide
  roughly in half in the same breath as disclosing an inquiry into cash
  management. Note that ordering.

**Your voice note:** this is the "news follows price" section. Write it as such.
The tape was leaving for six months. The headline just told everyone why.

## Section 2 — What the SEC is actually looking at

Be precise here, because most write-ups get it wrong.

- The investigation covers **cash management practices, related disclosures, and
  the efficacy of internal control over financial reporting.** Not revenue
  recognition. Several outlets said revenue rec. They are wrong.
- The 10-K/A (filed Feb 17, 2026) confirmed **no restatement**. Material
  weaknesses "did not result in errors in the historical financial statements."
- What they added was expanded MD&A disclosure describing how Kyndryl manages
  **the timing of cash collections and payments** and how that affects
  period-to-period cash flow presentation. The accounting did not change. The
  disclosure did.
- Investors have filed suit. CFO departed ahead of the accounting review.

**Why this matters and nobody says it plainly:** stretching payables and pulling
collections forward moves free cash flow between quarters without changing the
business. If the cheap-ness of this stock is a free cash flow yield, and the
open question is whether that free cash flow number means what it appears to
mean, then you cannot use the FCF yield as your margin of safety. That is
circular and it is the trap.

## Section 3 — The business underneath

Give the reader the actual thing they own.

- Spun out of IBM in 2021. Runs other companies' mission-critical infrastructure.
  $15B revenue, low margin by design (gross 21.8%, operating 1.7%, net 0.6%).
- Q1 FY27 (reported Aug 5, 2026): revenue $3.6B, **down 3%**, with ~3 points of
  that from the "evolving IBM relationship" running off. Adjusted pretax **loss
  of $37M** vs +$128M a year ago, driven by $152M of workforce rebalancing.
  Adjusted EBITDA margin 14.2%, down from 17.3%.
- The one genuinely good line: **Kyndryl Consult grew 14% over the trailing
  twelve months**, on agentic AI and hybrid IT modernization work. Signings
  $3.9B in the quarter, $14.2B trailing twelve months.
- FY27 outlook reaffirmed: revenue flat to -2% cc, adjusted pretax income
  $600-700M, FCF $400-500M.
- Balance sheet: $2.10B cash, $4.07B debt. Debt/equity 3.80. Current ratio 0.85.
  **Interest coverage is negative.** That last one is the number to sit with.

**The real question to pose to the reader:** is this a melting ice cube with a
growing consulting arm bolted on, or a consulting business emerging from under a
melting ice cube? Nobody knows yet. The revenue line says ice cube. Consult at
+14% says maybe not. Do not pretend to resolve it.

## Section 4 — The tape today (numbers verified 9/5)

- **Close $13.15.** EMA9 $13.13, EMA21 $13.06, EMA50 $12.87. Stacked bullish and
  compressed inside 2%. That is a coil, not a trend.
- **ADX 11.1.** No trend at all. +DI 21.5 / -DI 17.3. This is chop.
- **RSI 51.8.** Dead center. Was 62 twenty days ago. Rolled over and stalled.
- **ATR $0.61 = 4.6% of price.** Wide for a $13 stock. It moves when it moves.
- **Post-crash range: $10.11 (Feb 9) to $14.94 (Apr 21).** Seven months of it.
  Price sits at **63% of range**. Middle of nowhere.
- Volume 260K/day recently vs 850K+ around the crash. **0.85x its own 20-day
  average.** Nobody is here.
- Short interest **29.3M shares = 13.5% of shares out**, 6.2 days to cover,
  down 0.15% last cycle. Heavy, and not covering.
- Analysts: **0 buys out of 14.** 7 hold, 4 sell, 3 strong sell. Consensus Sell.
  That is close to the most negative sell-side book you will see on a $2.9B
  company that is not in bankruptcy.

**Options structure (matters for how you'd play it):**
- **No weeklies.** Sep 18, Oct 16, Dec 18, Jan 15, Mar 19, Jan 2028 only.
- Gamma flip $12.92-13.19. Price is sitting right on it.
- Walls: $13 is the highest-scored strike (8,658 OI), $12 support (6,876 OI),
  $14 and $15 resistance. Positive gamma regime, so dealers dampen moves.
  Translation: pinned to $13 until something breaks it.
- IV 47%, **IV rank 18.5**. Cheap relative to KD's own year, because the year
  contains a 55% day.
- Edge X-ray grades near-the-money contracts **very_cheap / BUY** with spreads
  of **21-46%**. Zero unusual options activity on the tape.

**Wheel verdict (say this out loud, it is the useful part):** this fails your
own filter. No weeklies, 21-46% bid-ask, low IV rank, and a live regulatory
tail. You would be selling cheap premium at monthly cadence into spreads that
eat the credit, on a name where the bad news arrives as a gap, not a slide. If
you want exposure, own shares or buy the cheap calls. Do not wheel it.

## Section 5 — The setup, honestly graded

**What it is not:** this is not your downtrend breakout. The falling trendline
from $44 already broke down through, not out. Post-crash the highs are $13.69,
$14.94, $14.78, $13.01, $14.12, $14.71. Those are not lower highs. That is a
flat ceiling.

**What it is:** a seven-month rectangle. Floor $10.11-10.90 tested three times
(Feb 9, May 13, Jun 22, all held). Ceiling $14.71-14.94 rejected four times.
Price mid-range and coiled on compressed EMAs with ADX at 11.

**The trigger is mechanical, not a judgment call:**
- Long above **$14.94** on volume greater than 1.5x the 20-day average.
  Measured move = range height $4.83 added to the break = **$19.77**.
- Invalidation: loss of **$10.10**. That is the Feb 9 low. Below it there is no
  chart, only the 2021 spin-out history.
- Everything between $10.10 and $14.94 is noise and you have seven months of
  proof.

**The give-away / avoid (free section):** do not buy this here at $13.15. You
are paying mid-range for a name with 0 analyst buys, negative interest coverage,
a live SEC enforcement matter, and no volume. The whole edge is in waiting for
the ceiling to break or the floor to get retested.

**The paywalled piece:** the exact entry, the size against your cap, the option
structure if you want convexity instead of shares (the Jan 2027 and Jan 2028
strikes are where the cheap-graded contracts with survivable spreads sit), and
where the reinvest dollars go if it triggers.

## Section 6 — Close

Pull it back to the reader.

- The thing you own when you buy this is not a valuation. It is a bet that the
  SEC finding is a disclosure problem and not a cash problem, and that Consult
  at +14% outgrows the runoff before the balance sheet gets tested.
- That bet might be right. It is not a bet you take at 63% of a range on 0.85x
  volume with no catalyst until **November 10** (Q2 FY27).
- Reinvest angle: if it triggers, it goes in the book like everything else and
  you show the fills. If it never triggers, you never bought it, and that is
  also the post.

---

## Numbers to re-verify on publish day

- [ ] Spot price and where it sits vs $12.92 gamma flip
- [ ] Whether $14.94 or $10.10 has been touched since 9/5
- [ ] AVUV share count (does the +32,725 continue or was it one day)
- [ ] Confirm Q2 FY27 earnings date is 2026-11-10 before printing it
- [ ] Short interest at next settlement

## Data flags found during the pull

- TDPro `get_long_term_quality` returns `priceToFcf: 4.77` and
  `evToFcf: 32.48` for the same company. Those imply FCF of $600M and $150M
  respectively. Both disagree with the company's own $400-500M guide.
  **Do not use either field.** Compute from guidance.
- `get_ticker_news` returns zero headlines for KD. The news feed does not cover
  this name. Everything above came from web + filings.
- `get_insider_trades` ignores the ticker filter and returns the market-wide
  feed. No KD insider buys appear in the 90-day buy list.

## Title candidates

- The cheap number is the one under investigation
- Kyndryl fell 55% in a day and the chart has not moved since
- Zero analysts say buy this. Three quant funds own it anyway.
- What a 14% free cash flow yield is worth when the SEC is reading your cash

## Suggested hero image concept

The $44-to-$13 line as a landscape silhouette, one vertical cliff at Feb 9,
then seven months of flat horizon. Gold on charcoal. gen_image.py, `--ref` the
chart PNG.

---
---

# ADDENDUM 2026-09-05 — long-term verdict + setups

## Do I like it long term? No.

Not as a hold. It is a good trade and a bad investment, and the reason is one
line: **KD is not the cheap one in its own sector.**

Straight comparison against DXC, the value-trap poster child of IT services:

| | **KD** | **DXC** |
|---|---|---|
| Market cap | $2.86B | $1.86B |
| Price / book | **2.72** | **0.61** |
| Interest coverage | **-2.88** | **10.64** |
| Debt / equity | **3.80** | **1.15** |
| Current ratio | **0.85** | **1.41** |
| EV / FCF | ~10-12x | **3.67** |
| Quality score | **15** | 43 |
| Revenue growth | -0.62% | -2.42% |
| Analyst book | 0 buy / 7 hold / 7 sell | 0 buy / 10 hold / 7 sell |

DXC is declining faster and is cheaper on every single valuation and safety
metric. If the thesis is "buy cheap declining IT services," DXC is the trade and
KD is not. **KD is not cheap. KD has fallen. Those are different things,** and at
2.7x book it is the most expensive book value in the sector's bargain bin.

**The disqualifier: negative interest coverage.** TTM operating income does not
cover the interest bill. Net margin is 0.59% and operating margin is 1.7%, so
there is no cushion at all. A two-point revenue miss erases operating income
outright. You do not want a decade-long hold in a business with no margin, a
shrinking top line, $4.07B of debt, and a live SEC enforcement matter.

**And the thing almost nobody mentions:** in February 2026, the same month the
SEC news broke and the CFO walked, Kyndryl **drew $1 billion on its revolving
credit facility.** Companies draw revolvers when they are worried about access,
not when they are comfortable. That draw is a tell.

**The structural bear case:** this is headcount-based managed infrastructure.
Atos nearly went under. DXC has been "cheap" for eight years. Unisys the same.
The whole cohort is a graveyard. Worse, Kyndryl is selling agentic AI consulting
into a core business that agentic AI is deflationary to. Consult at +14% is real
and it is the only genuinely good number in the release. It is also being asked
to outgrow a runoff, on a balance sheet with no slack, before November.

**Where I could be wrong:** signings are $14.2B TTM against $15.0B revenue.
Book-to-bill just under 1. If that crosses and holds above 1 while Consult keeps
compounding at 14%, the revenue line inflects and the FCF yield is real. That is
the bull case, it is not crazy, and it is measurable. Watch book-to-bill, not P/E.

---

## The setups

### The two dateable catalysts (this is what makes it tradable)

1. **October 2026 — $700M of 2.05% notes mature.** Company says refinance or pay
   from the $2.1B cash. Refinancing clean removes an overhang. Note they issued
   Feb 2034 paper at **6.35%**, so a refi roughly triples the coupon: about
   +$30M/yr of interest, ~12% of operating income. Trouble refinancing and the
   thesis dies inside a week.
2. **November 10, 2026 — Q2 FY27.**

Both land inside January 2027 expiry. That is the whole reason the structure
below is what it is.

### Setup A — Range breakout (primary, mechanical, not yet triggered)

- **Trigger:** daily close above **$14.94** on volume > 1.5x the 20-day
  (roughly >390K shares)
- **Entry:** $15.00-15.20 on the close or the first retest
- **Stop:** **$12.85** (under EMA50 $12.87 and the $12.92 gamma flip)
- **Target:** **$19.75** (range height $4.83 added to the break)
- **R:R ≈ 2.2:1**
- Status today: price $13.15. **Not triggered. Do nothing.**

### Setup B — Floor retest (better risk, needs patience)

The floor has held three times: $10.11 (Feb 9), $10.88 (May 13), $10.37 (Jun 22).

- **Zone:** $10.90-11.20
- **Stop:** **$9.95**, below the Feb 9 low. Below that there is no chart left.
- **Target 1:** $13.15  **Target 2:** $14.90
- **R:R ≈ 3.5:1** to target 2
- This is the entry I actually want. It requires the market to hand it to you.

### Setup C — Buy convexity, not shares

Given negative interest coverage and the revolver draw, owning shares means
taking unlevered exposure to a levered balance sheet. Calls cap the loss at
premium. This is the structure, not an upgrade to the thesis.

Jan 15 2027 (132 DTE), live quotes:

| Contract | Bid/Ask | Mid | Spread | Delta | IV |
|---|---|---|---|---|---|
| **$13 call** | 1.90 / 2.10 | **$2.00** | **10%** | 0.60 | 59% |
| $14 call | 1.40 / 1.65 | $1.52 | 16% | 0.51 | 57% |
| $15 call | 1.05 / 1.25 | $1.15 | 17% | 0.43 | 56% |

- **The Jan-27 $13 call at ~$2.00 is the trade.** 10% spread is the tightest
  contract on the entire board. $200 risked per contract, max loss $200,
  breakeven $15.00, and it carries you through both the October refi and the
  November 10 print.
- The $15 call at $1.15 is the cheaper pure-breakout lottery if you want it.
- **Avoid Jan 2028 entirely.** Spreads run 24-65%, strikes are sparse, unusable.
- IV rank is 18.5, so you are buying volatility near the low end of its own year.
  That is the correct side of this one.

### What not to do

- **Do not short it.** 13.5% of float short, 6.2 days to cover, IV rank 18.
  That is squeeze fuel, and a clean October refi is exactly the spark.
- **Do not buy shares at $13.15.** Mid-range, ADX 11, 0.85x volume, no catalyst
  for nine weeks. There is nothing to be paid for here.
- **Do not size it as a core hold.** See the whole first half of this addendum.

### Reinvest-model note

Half of Substack revenue goes into whatever gets written about. That raises the
bar on this one specifically. If KD gets a post, the position should be the
defined-risk Jan-27 call, not shares, and the post should say so plainly. That
is the honest version and it is also the better trade.

## Data flag

Alpaca's option snapshot returns `openInterest: 0` on every KD contract. That is
a feed gap, not real. TDPro shows 8,658 OI at the $13 strike and 6,876 at $12.
Do not cite OI from the Alpaca pull.

---
---

# ADDENDUM 3 — chart read (corrects the structure call above)

Source: mph's dealer-HUD daily chart, 2026-09-05 08:18 CT.

## Correction: it is not a rectangle, it is an ascending triangle

Section 5 above called this a flat seven-month rectangle and said price was
"mid-range, do nothing." The seven-month range is real, but inside it the
structure since June is rising, and that is the operative pattern.

**Four rising swing lows, 5-bar pivots, verified:**

| Date | Low |
|---|---|
| 2026-06-22 | $10.37 |
| 2026-07-14 | $10.92 |
| 2026-07-23 | $11.43 |
| 2026-08-21 | $12.24 |

Rising trendline slope **$0.043/bar**, sitting at **$12.67 today**.
Ceiling flat at **$14.71-14.94**.

**That is an ascending triangle, and the apex math matters:**

- Trendline meets the $14.71 ceiling in **~47 trading bars**
- Meets $14.94 in **~52 bars**
- **Apex lands mid-November 2026, approximately Nov 12-18**
- **Q2 FY27 earnings is November 10**

The pattern runs out of room in the same week as the catalyst. This does not
resolve on its own schedule. **It resolves on the print.**

## What the HUD adds

- **POSITIVE GAMMA, moves get damped.** Dips bought, rips sold, breakouts stall
  and fade back. This is why it has chopped for seven months.
- **PIN 12.00** (6.9K OI), **strongest level 13.00** (8.7K OI). Cross-confirms
  TDPro exactly (6,876 and 8,658). Two independent sources agree.
- **FLIP 12.92** on the HUD vs **13.19** on the gex model. Spot $13.15 is
  *between them*. The HUD flags this as `SPLIT`. That is the definition of a
  coil: the market cannot decide which side of the flip it is on.
- **COILING at 13, ranges contracting into the level, 2 bars ago.** Confirms.
- **ROOM 1.6 ATR** to the pin, spot 0.4 ATR above flip.
- **Expected move ±9.2% for 09-18** = **$11.94 to $14.36**. The entire triangle
  fits inside one expected move. Nothing here is a big bet yet.

## The tension worth writing about

**TD Volume panel: SELLERS IN CONTROL. Buyer strength 21% (weak), seller
strength 79% (strong).**

So: rising lows, falling volume (0.85x the 20-day), sellers controlling the
recent tape, inside positive gamma that damps every attempt. That is not
accumulation. **That is a coil with no one pushing.**

Which is the actual insight: an ascending triangle on declining volume into an
apex that lands on an earnings date is not a technical breakout trade. **It is
an earnings-dated volatility trade wearing a chart pattern's clothes.** The
triangle will not break on its own. It will gap on November 10.

## Revised setups

### A. Ascending triangle long (upgraded from "do nothing")

- **Trigger:** daily close above **$14.94** on >1.5x 20-day volume
- **Stop:** **$12.55**, under the rising trendline ($12.67) with room
- **First target:** $19.75 (range height added). **Note the pin:** on a break
  below the trendline, the $12.00 pin with 6.9K OI is the magnet, so a failed
  triangle goes to $12.00 fast, not to $12.50.
- Better than the rectangle version because the stop is now $12.55 instead of
  mid-range guesswork, and the trendline rises $0.043/day toward your stop,
  tightening risk every session you wait.

### B. Floor retest — DOWNGRADE this one

The $10.90-11.20 zone from Addendum 2 is now **below the rising trendline**. If
price gets there the triangle is already broken and the higher-low sequence is
dead. Do not treat $11 as support any more. **If the trendline breaks, the
level is $12.00 (the pin), and below that the thesis is just gone.**

### C. Convexity — this is now clearly the right structure

The chart makes the case stronger, not weaker. A pattern that resolves on a gap,
inside positive gamma that damps everything until it does not, with the apex on
the earnings date, is exactly what a long call is for.

**Jan-27 $13 call, ~$2.00 mid, 10% spread, 0.60 delta.** 132 DTE covers the
October refi, the November 10 print, AND the mid-November apex. All three.
$200 max loss per contract. Breakeven $15.00, which is just above the triangle
ceiling, so you are paid exactly when the pattern pays.

Sep-18 contracts are a coin flip on a ±9.2% expected move that brackets the
whole triangle. Skip them.

### Trigger block draft (verify prices day-of before publishing)

```
trade rule for this post (LONG only)
ticker: KD
setup: ascending triangle, apex mid-Nov
trigger: daily close > 14.94 on vol > 1.5x 20d avg
stop: 12.55 (rising trendline)
target: 19.75
invalidation: close < 12.55 -> expect 12.00 pin
status as of 2026-09-05: NOT TRIGGERED (spot 13.15)
```

---
---

# ADDENDUM 4 — DXC, since it came up

To be clear about what I was doing in Addendum 2: DXC was a **yardstick**, used to
show KD is not cheap relative to its own sector. It was not a buy call. But the
question was asked, so here is a real answer.

## Yes. I like DXC better than KD, and it is not close.

**Valuation at $11.67** (159.8M shares, market cap $1.86B, EV $3.42B):

- FY27 free cash flow guide **~$600M**
- **P/FCF = 3.1x. FCF yield on equity = 32%.**
- EV/FCF = 5.7x
- FY27 non-GAAP EPS guide **$2.40-2.90** → **P/E of 4.0x to 4.9x**
- Interest coverage **10.6x**, debt/equity 1.15, current ratio 1.41, P/B 0.61

**Q1 FY27 (reported July 30, 2026):**

- Revenue $3.0B, **-6.7% organic**
- Non-GAAP EPS $0.40, down 41% YoY
- Adjusted EBIT margin 5.0%, down 180bp
- **Free cash flow $314M vs $97M a year ago**
- **Bookings $3.0B, +5% YoY. Book-to-bill 0.99x, the highest Q1 in three years.**
- Full-year guidance maintained

## The head-to-head

| | **KD** | **DXC** |
|---|---|---|
| FY27 FCF guide | $400-500M | **~$600M** |
| Market cap | $2.86B | **$1.86B** |
| **FCF yield on equity** | 14-17% | **32%** |
| Forward P/E | 7.1x (adjusted, on a GAAP loss) | **4.0-4.9x** |
| Revenue trend | -3% | **-6.7% organic (worse)** |
| Book-to-bill | ~0.95 | **0.99, best Q1 in 3 yrs** |
| Interest coverage | **-2.88** | **10.64** |
| Regulatory overhang | **live SEC enforcement** | none |
| ADX | 11 (no trend) | **32.5 (real trend)** |
| Tape (TD Volume) | **SELLERS in control, buyers 21%** | **BUYERS in control, buyers 60%** |

Both crashed. **DXC's crash was operational** (May 2026, -19% on a weak FY27
guide, bottomed $7.91 on May 13). **KD's crash was operational AND regulatory
AND balance-sheet** (Feb 9, -55%, SEC enforcement, CFO and GC out same day, $1B
revolver drawn that month). One of those is a business problem. The other is a
business problem with a lawyer attached.

**And DXC has recovered while KD has not.** DXC is +48% off its low with ADX
32.5, RSI 63, EMAs stacked 11.32 / 11.02 / 10.62, riding a clean rising channel.
KD is coiling sideways at ADX 11 with sellers in control.

## The honest bear case on DXC

The reason it trades at 3x free cash flow is that the market thinks the cash
flow converges down. **-6.7% organic revenue decline is worse than Kyndryl's.**
Margins are compressing too: adjusted EBIT margin 5.0% and falling. This is a
melting ice cube. The only question that matters is whether the melt rate beats
the yield.

**The measurable test is the same one I gave for KD, and DXC is the one passing
it: book-to-bill.** 0.99x and the best first quarter in three years, on bookings
+5%. Cross 1.0 and hold it, and the revenue decline decelerates and a 3x FCF
multiple re-rates violently. Fail to cross and you are clipping a 32% yield on a
shrinking base, which still works for a while but ends badly.

That is a real, dated, checkable thesis. KD does not have one.

## DXC setup

**The wall is the whole story: $12.00 is 3,277 call OI against 120 put OI.**
netGEX 91,446, the dominant strike by a mile. Positive gamma, and TDPro returns
**no gamma flip level at all**, matching the HUD's `REGIME UNKNOWN / NO GAMMA
FLIP IN THIS CHAIN`.

Translation: dealers are long a mountain of $12 calls. Every rally into $12 gets
sold. Spot is $11.66, less than 3% below it.

- **Trigger:** close above **$12.00** on >1.5x volume. Above the wall there is
  almost nothing until $13 (915 OI). Air.
- **Stop:** **$10.95**, under the $11 support shelf and the channel's lower rail.
- **Target:** $13.00 first, then the April high $13.53.
- **Do not chase into $12.** Buying at $11.90 is buying directly into the wall.
  Either wait for the break and retest, or bid the channel bottom near $10.90.
- Max pain $10.00, expected move ±8.6% for 09-18.

**Next catalyst: November 4** (Q2 FY27). Guide is for organic decline to
*improve* in the second half, so that print is the test of the whole thesis.

## What this does to the article

The KD post gets materially stronger with DXC in it. The argument stops being
"here is a cheap stock" and becomes **"here is how you tell a cheap stock from a
fallen one, using two companies in the same industry that both fell 50%."**

Same sector, same fiscal calendar, same declining-revenue problem, both hated by
the sell side. One has 32% FCF yield, 10x interest coverage, an improving order
book and buyers in control. The other has 14-17% FCF yield, negative interest
coverage, an SEC enforcement matter reading its cash management, and sellers in
control. The market is not being irrational about KD. It is being precise.

That is a better post than a KD write-up, and it is genuinely useful to a reader
in a way "I found a cheap stock" is not.

---
---

# ADDENDUM 5 — the AVUV list (EXP, SON, KD, MGRC)

## First, the finding that reframes everything

**On 2026-09-04, AVUV added to 497 of its 794 positions (63%) and cut 8 (1%).**
Median move among movers: **+0.15%**.

That is an inflow / rebalance day. The fund was putting new money to work across
the entire book. **"AVUV is buying KD" on that date is close to meaningless as a
per-name signal.** Any screen keyed on "Avantis added shares" fires on 63% of
the portfolio that day.

What still carries information is the *relative* size of the add:

| Ticker | Share change | Rank of 505 movers | Percentile |
|---|---|---|---|
| **SON** | **+7.27%** | **10** | **top 2%** |
| MGRC | +3.18% | 32 | top 6% |
| EXP | +3.10% | 34 | top 7% |
| KD | +2.39% | 45 | top 9% |
| DXC | +0.09% | 386 | bottom half |

All four of your names are above-median adds, which is presumably why they
surfaced. But **SON is the real standout and KD is the weakest of the four.**

## The list, ranked

| | **SON** | **EXP** | **MGRC** | **KD** |
|---|---|---|---|---|
| Business | Packaging | Cement / building mat. | Modular + equip rental | IT infrastructure |
| Quality score | 59 | **74** | 69 | **15** |
| P/E | **8.24** | 14.95 | 17.50 | 33 (fwd 7.1 adj) |
| P/B | 1.44 | 4.05 | 2.15 | 2.72 |
| Revenue growth | **+12.05%** | +1.68% | -0.92% | -0.62% |
| EPS growth | **+12.74%** | -6.86% | -39.54% | -70.31% |
| Net margin | 8.41% | **17.32%** | 16.38% | **0.59%** |
| ROE | 17.85% | **26.87%** | 12.44% | 7.54% |
| Interest coverage | 4.59 | **202.10** | 7.98 | **-2.88** |
| Debt / equity | 1.24 | 1.18 | **0.47** | **3.80** |
| Current ratio | 0.99 | **3.23** | 1.22 | **0.85** |
| Dividend | **4.07%** (33% payout) | 0.53% | 1.82% | none |
| Beta | **0.36** | 1.31 | 0.49 | 1.75 |
| Analyst book | **5SB/5B/7H/0 sell** | 1SB/4B/11H/1S | **3SB/5B/1H/0 sell** | **0 buy / 7H / 7 sell** |
| Next earnings | 11/04 | 10/22 | 10/22 | 11/10 |

**Tape:**

| | Last | RSI | ADX | vs EMA50 | 52w position |
|---|---|---|---|---|---|
| SON | $51.93 | **32.5** | 17.7 | **-6.3%** | 65% |
| EXP | $194.37 | 39.3 | 11.1 | -5.6% | **30%** |
| MGRC | $111.54 | 36.6 | 10.6 | -3.7% | 56% |
| KD | $13.15 | 51.8 | 11.1 | +2.2% | **13%** |

## Read

**SON is the best name on this list.** It is the only one growing anything:
revenue +12% and EPS +12.7%. P/E 8.2, price/book 1.44, ROE 17.9%, a 4.07%
dividend at a 33% payout, and beta 0.36. Analysts are 10 buys to zero sells,
which is the inverse of KD's book. And it is **oversold on a pullback**: RSI
32.5, 6.3% under the 50 EMA, still at 65% of its 52-week range. That is a
pullback in a grower, not a falling knife. It was also AVUV's biggest add of
your four by a factor of two.

Watch: current ratio 0.99 and interest coverage 4.59 are the soft spots. Not
alarming, but it is not a fortress.

**EXP is the highest-quality business** by a distance. Interest coverage 202x,
current ratio 3.23, ROE 26.9%, net margin 17.3%. It is at 30% of its 52-week
range with RSI 39, so the pullback is deep. The catch: EPS is -6.9%, and at 4x
book it is the priciest book value here. This is a cyclical waiting on a
construction cycle. Good business, no catalyst yet.

**MGRC has the cleanest balance sheet** (D/E 0.47) and 48.5% gross margins, but
EPS is down 39.5% and revenue is slightly negative at a 17.5x multiple. You are
paying a growth multiple for a shrinking earner. Least interesting of the four.

**KD is last and it is not close.** It is the only name here with negative
interest coverage, the only one with an SEC enforcement matter, the only one
with zero analyst buys, quality 15 against 59-74 for the others, and it sits at
**13% of its 52-week range** because it fell there rather than because it is
cheap.

## The uncomfortable conclusion for the article

You went to the AVUV list and got interested in the single worst name on it.
That is not a knock, it is the most useful thing in this whole file, because it
is exactly the trap the screen is built to create: **a factor fund holding a
name tells you it screens cheap on book value. It does not tell you the business
works.** KD, EXP, SON and MGRC all clear the same value screen. One of them has
negative interest coverage and a regulator reading its cash management.

That is the post. Not "Kyndryl is cheap." **"I ran my own screen and got pulled
toward the worst name on it, and here is the checklist that caught it."** The
other three names are the proof the checklist works, and SON is what you find
when you apply it properly.

## Data flag (again)

TDPro's `priceToFcf` / `evToFcf` fields do not reconcile with
`cashFlowPerShare x sharesOutstanding` for EXP (says 31.6, computes to ~11.0)
or MGRC (says 38.6, computes to ~12.0). They roughly agree for SON (6.59 vs
6.4). **Do not cite FCF multiples from this endpoint without recomputing.**
Same defect flagged for KD in Addendum 1.

---
---

# ADDENDUM 6 — SON chart (corrects Addendum 5)

Addendum 5 called SON "a pullback in a grower, not a falling knife." **The chart
says that is wrong.** Correcting it.

## The higher-low sequence broke yesterday

SON's 2026 uptrend was a clean higher-low sequence:

| Date | Swing low |
|---|---|
| 2026-05-19 | $45.48 |
| 2026-06-08 | $46.38 |
| **2026-07-15** | **$52.46** ← the low that defined the trend |

It made a new 52-week high at **$60.07 on July 28**.

**Close on 2026-09-04 was $51.93. The 9/3 low was $50.85.** Both are below
$52.46. **The last defended higher low has failed.** That is not a pullback
inside an uptrend. That is a broken uptrend, as of one session ago.

## The slide has the wrong character

From the Aug 21 high of $59.58 to $51.93 is **-12.8% in ten sessions**, with
**nine of the last eleven sessions closing lower.**

Volume confirms it is distribution, not drying-up:

| | Sessions | Avg volume |
|---|---|---|
| Down days (last 12) | **8** | **58,895** |
| Up days (last 12) | 4 | 51,867 |
| 20-day average | | 48,238 |

Down days are running ~14% heavier than up days and ~22% above the 20-day
average. A healthy pullback goes quiet. This one is getting louder.

## It sliced the strongest options level

The HUD shows **PIN 55.00, 1.6K OI, STRONGEST**. Price went straight through it
and is now $3 below. **The $55 pin is overhead resistance now, not support.**
`COILING at 55` is stale, the coil resolved downward.

Gamma flip **$49.99**, spot 1.2 ATR above it. Expected move ±7.9% for 09-18 puts
the floor at **$47.85**.

## What caused it

**B of A Securities downgraded Sonoco to Neutral on 2026-09-03 and cut the
target to $60.** That is the -3.7% day on 107,101 shares, 2.4x normal.

**Correction to Addendum 5:** the "5 strong buy / 5 buy / 7 hold / 0 sell" book
I quoted is from TDPro's analyst snapshot dated **2026-09-01**, which is two
days *before* the BofA cut. That figure is stale. It is no longer 10 buys to
zero sells.

Note also SON has form here: **April 22, 2026 it fell 14.1% in one session** to
$48.80 when freight and energy costs pushed full-year EPS to the low end of
guidance. This name reacts violently to cost pressure.

## What has NOT changed

The business is the same as it was on Wednesday:

- Revenue +12.05%, EPS +12.74%, still the only grower on the AVUV list
- P/E 8.24, P/B 1.44, ROE 17.85%, beta 0.36
- **4.07% dividend at a 33% payout.** At $50 that yield is 4.3%
- **No earnings until November 4.** No company news drove this
- **BofA's price target is $60, above the current price.** They downgraded on
  valuation, not on the business

So: a good business whose chart just broke on a sell-side rating change. Those
are different problems, and the second one is the tradable one.

## Revised SON setup

**Do not buy at $51.93.** You are in mid-air between a broken low ($52.46) and
the next real shelf. There is nothing to lean on here.

**The shelf is $49.30 to $50.61** — the March 20 low $49.30, the March 9 low
$50.61, with the **$49.99 gamma flip sitting inside the zone.** Three separate
reasons for a bid in a $1.30 band. That is where this gets interesting.

- **Entry:** $49.30-50.60
- **Stop:** **$48.70**, under the April 22 capitulation close of $48.80
- **Target 1:** $55.00 (the pin, now resistance). **Target 2:** $57.40
- **R:R ≈ 3:1** to target 1
- At $50 you are collecting a **4.3% dividend** while you wait

**Alternative confirmation entry:** a daily close back above **$55.00** reclaims
the pin and says the break was a shakeout. You pay up ~6% for the certainty.

**Invalidation:** below $48.70 the May-June base at $45.48-46.38 is the next
stop, and the whole 2026 uptrend is gone.

## The lesson for the article

This is the second time in one session the screen pointed at a name and the
chart said something different. KD screened cheap and is a distressed balance
sheet. SON screened as a quality grower on sale and is a broken uptrend on
distribution volume.

**Same checklist, and it caught both.** Fundamentals tell you what to want. The
tape tells you when. Neither one is optional, and the AVUV list gives you the
first without the second.

---
---

# ADDENDUM 7 — EXP, MGRC, ESP. And the pattern behind all of them.

## ESP (Espey Mfg & Electronics) — kill it, and here is the one-line reason

**ESP has no listed options at all.** The chain comes back empty. Consolidated
volume is **28,657 shares/day**, about $1.8M notional, on a **$190M market cap
with only 3.0M shares outstanding.**

You write posts with a machine-readable trade-rule block that fires a real IBKR
limit order. You cannot do that here. It is untradeable for your purposes, full
stop, and no amount of good fundamentals fixes that.

Which is a shame, because the business is the best one anyone has looked at all
session:

- **Quality score 89** (vs KD 15, SON 59, MGRC 69, EXP 74)
- Net margin **25.49%**, operating margin **25.45%**, gross 36.52%
- ROE 20.38%, ROA 12.48%
- **Debt/equity 0.00.** No debt at all, which is why interest coverage returns null
- Current ratio 2.32, beta 0.36, dividend 2.57% at a 44.5% payout
- EPS +41.5%, though revenue is -8.1%
- Defense electronics: power supplies and transformers for military programs.
  Genuinely on-theme for the power/defense narrative.
- **Earnings 2026-09-17**

Chart is fine too: $63.15, RSI 53.3, ADX 14.2, EMAs compressed at 63.15/62.65/
61.97, coiling at 75% of a $36.00-$74.77 range. You were right that it does not
look bad.

**Verdict: a great business you cannot trade. File it, do not write it.** The
analyst book (0 buy / 3 hold / 5 sell on a $190M microcap) is almost certainly a
data artifact and should not be cited either.

## EXP (Eagle Materials) — a real downtrend, not a pullback

| | |
|---|---|
| Price | $194.37 |
| Swing highs | 6/25 **$245.30** → 7/28 **$225.09** (LOWER) |
| Swing lows | 7/08 $201.98 → 7/23 **$199.00** (LOWER) |
| Price vs last swing low | **BELOW. Broken.** |
| Drawdown from 52w high | **-20.8%** |
| RSI / ADX | 39.3 / 11.1 |
| Volume last 12 | up 5d avg 24,593 / down 7d avg 24,608 (neutral) |
| Consolidated volume | 430,372/day (borderline for your liquidity screen) |

Lower highs AND lower lows since June 25. That is a downtrend, and RSI 39 in a
downtrend is not a bargain, it is a trend. Volume is neutral, so there is no
capitulation and no accumulation. Nothing to trade.

**But keep it on the list.** Interest coverage **202x**, current ratio 3.23, ROE
26.9%, net margin 17.3%, quality 74. This is a genuinely excellent cyclical
getting marked down. Real support is the March low **$172.03**. And the lower
highs from $245.30 are the beginning of a falling trendline, which makes EXP a
future candidate for **your #1 setup, the downtrend breakout.** It is just far
too early. Earnings 10/22.

## MGRC (McGrath RentCorp) — broke, and too thin anyway

| | |
|---|---|
| Price | $111.54 |
| Swing lows | 7/08 $111.76 → 7/30 **$112.85** (rising) |
| Price vs last swing low | **$111.54, BELOW $112.85. Just broke.** |
| Volume last 12 | up 3d avg 4,689 / **down 9d avg 6,444** |
| Consolidated volume | **154,628/day — too thin** |
| RSI / ADX | 36.6 / 10.6 |

Same failure as SON: a rising-low sequence that broke this week, on down-volume
running 37% heavier than up-volume, 9 of the last 12 sessions lower.

And independently, **154K shares/day disqualifies it.** Best balance sheet of
the group (D/E 0.47, 48.5% gross margin) but EPS is -39.5% at a 17.5x multiple.
Pass.

## THE PATTERN — this is the actual article

Run the whole list through one test: **is price above its most recent swing low?**

| Ticker | Last swing low | Price | Structure |
|---|---|---|---|
| KD | rising trendline $12.67 | $13.15 | **above, intact** (the only one) |
| SON | $52.46 (7/15) | $51.93 | **BROKEN** |
| EXP | $199.00 (7/23) | $194.37 | **BROKEN**, and lows are falling |
| MGRC | $112.85 (7/30) | $111.54 | **BROKEN** |
| ESP | n/a | $63.15 | intact, but no options and no volume |

**Four out of five are technically damaged.** That is not bad luck. That is
mechanical, and here is why:

**AVUV is a small-cap VALUE fund. A value factor buys things that have already
fallen — that is the literal definition of the factor.** So screening "what is
AVUV holding" or "what did AVUV add" returns, by construction, a list of stocks
in downtrends. The screen is working exactly as designed. It is just not
designed to do what you were using it for.

Add the inflow-day finding from Addendum 5 (AVUV added to 63% of its book on
9/4, cutting 8 of 794) and the picture is complete: **a value fund's daily adds
are neither stock selection nor conviction. They are a factor definition plus
new cash.**

**That is the post.** Not Kyndryl. Not Sonoco.

> "I went looking through a smart-money list for my next idea. Four of the five
> names I pulled were below their last swing low, and one of them had an SEC
> investigation. Here is what I learned about where these lists actually come
> from, and the four checks I now run before a name gets written up."

The four checks, each of which caught something real today:
1. **Is it above its last swing low?** (caught SON, EXP, MGRC)
2. **Is interest coverage positive?** (caught KD at -2.88)
3. **Can I actually trade it — options, and real volume?** (caught ESP and MGRC)
4. **Did the fund add to this name specifically, or to its whole book?** (caught
   the AVUV inflow day, 497 of 794 positions)

You have receipts for all four from a single morning's work. That is a far
stronger post than any one ticker, and it is the kind of thing a reader keeps.

---
---

# ADDENDUM 8 — ESP deep dive (revisiting the kill)

Correcting Addendum 7: I disqualified ESP on liquidity using an institutional
screen (500K shares/day). That was the wrong yardstick for a personal position.
At ~$1.8M of notional a day you are not moving this stock with a few thousand
dollars. **The options objection stands. The volume objection does not.**

And on a closer look this is the most interesting name of the day.

## The business

Espey Mfg & Electronics (NYSE American: ESP), Saratoga Springs NY. Specialized
military and industrial **power supplies, transformers and power distribution**.
Fiscal year ends **June 30**.

- Market cap **$190M**, only **3.0M shares outstanding**
- Revenue TTM $42.2M
- **Net margin 25.49%**, operating 25.45%, gross 36.52%. Software-like margins
  on hardware.
- ROE 20.38%, ROA 12.48%
- **Debt/equity 0.00.** No debt at all, which is why interest coverage is null.
- Current ratio 2.32, beta 0.36
- **Quality score 89** — the highest of anything screened today (KD 15, SON 59,
  MGRC 69, EXP 74, DXC 43)

## The numbers that matter

**9M FY2026, through 3/31/26:**

| | 9M FY26 | 9M FY25 |
|---|---|---|
| Sales | $32.65M | $34.35M (-5%) |
| Net income | **$7.84M** | $5.21M (**+50%**) |
| Diluted EPS | **$2.74** | $1.95 (**+40%**) |

Earnings up 50% on revenue down 5%. That is mix shift into higher-margin
magnetics work, not cost-cutting.

**Backlog — the bull case:**

- **$137.1M at 3/31/26** vs $138.0M a year earlier. Essentially flat.
- That is **3.2x trailing annual revenue.** Enormous visibility for a $190M company.
- Recognition schedule: 11% in FY2026, **38% in FY2027**, 22% in FY2028, rest after
- 38% of $137.1M = **~$52.1M scheduled for FY2027** against ~$42M trailing.
  If that converts, it is roughly **+23% revenue growth** next fiscal year.
- **Customer advance payments +46%.** They are being paid before doing the work.

**New orders — the bear case, and it is serious:**

- **9M FY2026 new orders: $30.0M. 9M FY2025: $75.1M. Down 60%.**
- Book-to-bill for the nine months: $30.0M / $32.65M = **0.92**
- Revenue -8.09% YoY

Flat backlog plus collapsing orders means they are living off the book. The
backlog buys two to three years of visibility, and then it does not. **This is
the single number that decides the thesis.**

## Ownership explains the tape

- **~42.5% insider-owned**, ~26.7% institutional, ~31% retail. (One source says
  ~25% insider; treat the exact figure as unverified, the direction is not.)
- With 3.0M shares out, the real float is roughly **1.7M shares.**
- Institutional holders are Renaissance, Dimensional, Vanguard, Two Sigma,
  Geode, Arrowstreet — **quant and index money, not fundamental conviction.**
  Do not write this up as "smart money likes it." They own it because it fits a
  microcap factor bucket.

That float is why a 177% move happened on modest buying, and why the book looks
the way it does below.

## The tradeability reality — precise version

- **Quoted spread right now: bid $58.00 x100, ask $68.64 x100. That is 16.8%.**
- **But actual prints cluster tight**: $61.81, $61.91, $62.06, $62.10, $62.15,
  $62.21, $62.54. Trades happen in a ~1% band around last.
- Print sizes are 1, 3, 30, 32, 37, 100 shares. **An odd-lot, retail-only tape.**
- Consolidated volume 28,657/day.
- **No listed options at all.** The chain is empty.

Practical translation: you can build a position with patient limit orders inside
the print band. You **cannot** exit quickly, and you **cannot** hedge or define
risk with options. So this can only ever be a position you are willing to sit
in, never a trade you intend to manage.

## The chart — and it is the only intact structure of the five

$26.12 in March 2025 to a **$71.99 high in April 2026. +177%.** Then five months
of coiling.

**Falling highs:** $71.99 (Apr) → $71.85 (May) → $67.24 (Jun) → $67.28 (Jul) →
$65.97 (Aug) → $63.26 (Sep)
**Rising lows:** $55.43 (May) → $55.86 (Jun) → $56.02 (Jul) → $60.07 (Aug) →
$62.00 (Sep)

That is a **symmetrical triangle**, and the compression is extreme:

| Month | Range | Width |
|---|---|---|
| Apr | $56.35-71.99 | **27.8%** |
| Jun | $55.86-67.24 | 20.4% |
| Jul | $56.02-67.28 | 20.1% |
| Aug | $60.07-65.97 | 9.8% |
| **Sep** | **$62.00-63.26** | **2.0%** |

**The monthly range has compressed 93% since April.** RSI 53.3, ADX 14.2,
ATR 1.6%, and EMA8/21/55 are all bunched at $61-63 with price sitting on them.
Price is above a **rising 200-day SMA around $57**.

**And it passes the test the others failed:** last swing low $62.00 (Sep), prior
$60.07 (Aug), price $63.35. **Rising lows, structure intact.** It is the only
one of KD / SON / EXP / MGRC / ESP that is not below its most recent swing low.

## The catalyst, and it is 12 days out

**September 17, 2026: Q4 AND FULL-YEAR FY2026 results.** Because the fiscal year
ends June 30, this is the big annual print, and it carries **year-end backlog
and full-year new orders** — exactly the two numbers the thesis turns on.

Also: the board declared a **special dividend of $0.75 plus the regular $0.25**
in August 2026. Last year's pattern was the special paid 9/26/25 to holders of
record 9/19/25, which put it right on top of the same earnings window. Total
2025 payout was $1.75, about **2.8% at today's price**, not the $1.00 the
screens show.

## Verdict

**As an article: yes. This is exactly the shape you described.** Sexy sector
(defense electronics and power), a name nobody talks about, a real business with
89 quality and zero debt, and a dated, legitimate setup. It is a far better
story than Kyndryl.

**As a trade before 9/17: no.** You would be buying a binary annual print, in a
1.7M-share float, with a 17% quoted spread and no options to define risk. If
the orders number is bad there is no exit that does not hurt.

**The move:** wait for September 17. Let the print resolve the coil and hand you
the year-end backlog and the full-year orders figure. Then buy the direction
with the actual number in hand. You give up the gap and you eliminate the coin
flip, and given you cannot hedge this, that trade is clearly correct.

**What to watch on 9/17, in priority order:**
1. **Full-year new orders.** Did the $30.0M nine-month pace continue, or did Q4
   book? Anything that puts the year near $75M+ changes everything.
2. **Year-end backlog vs $137.1M.** Growing is the bull case confirmed.
3. **Margins.** Is 25% net sustainable or was it a mix quirk?
4. The special dividend confirmation and its record date.

**Levels if it does resolve:** the coil breaks above **$63.30** or below
**$62.00**. Upside targets the $65.97 August high then $67.28. Downside targets
$60.07 then the rising 200-day near $57. Measured move off the April-to-now
triangle is roughly $8, so a clean break projects to about **$71** or **$54**.

**The honest bear case in one line:** new orders fell 60% and the entire bull
case is a backlog that is being consumed faster than it is being replaced.

---
---

# ADDENDUM 9 — where the list came from, and a real bug in stock-recap

## The source

Yesterday's stock-recap (`.claude/skills/stock-recap/history/2026-09-04.md`),
"Hedge funds" section, **Hot streaks** line:

> `EXP (AVUV, 9d up) · SON (AVUV, 9d up) · MGRC (AVUV, 9d up) · MAN (AVUV, 9d up)`

That is the origin of the whole morning. The skill flagged a 9-day AVUV
accumulation streak in four names.

## The bug

**AVUV added to 497 of its 794 positions (63%) on 2026-09-04 and cut 8 (1%).
Median add +0.15%.** A fund taking inflows adds to most of its book most days.
So a "9-day buying streak" in AVUV is **the base rate, not a signal.** The
streak detector never normalizes against the fund's own daily breadth, so it
will manufacture streaks indefinitely for any fund with steady inflows.

**The fix:** before flagging a streak, compute the share of that fund's book
moving the same direction that day. Flag only if the name sits in (say) the top
decile of that day's moves, or if the fund's breadth was narrow. Rank by
percentile-within-fund, not by consecutive days.

## The receipt — all four flagged names failed

| Ticker | What the streak claimed | What was actually true |
|---|---|---|
| **SON** | 9d accumulation | Broke its $52.46 higher low; down-volume 14% heavier than up |
| **EXP** | 9d accumulation | Lower highs AND lower lows since 6/25, -20.8% from the high |
| **MGRC** | 9d accumulation | Broke its $112.85 higher low; 154K shares/day, too thin |
| **MAN** | 9d accumulation | **95% of its 52-week range, RSI 65.6, ADX 42.2, +17.2% over EMA50** |

**Four for four.** Not one was a usable entry.

**MAN (ManpowerGroup)** deserves its own line because it is KD wearing a
different suit: **net margin 0.56%, operating margin 1.54%, interest coverage
2.26, quality 42, payout ratio 79.9%** — and it has run from $25.15 to $63.88,
+154%, to sit at 95% of its range. Terrible business, terrible entry, flagged as
smart-money accumulation.

## Also worth knowing about the skill

- Its own printed track record: **shortlist hit-rate 47%, median -0.3%;
  Reversal Watch 43%, median -4.0%.** A coin flip with a slightly negative
  median. It says so at the top of every run, which is to its credit.
- The convergence shortlist that day was AAPL, TSLA, AMZN, META, MSTR, GOOGL,
  AVGO. **Convergence ranking mechanically surfaces the most-traded names**, so
  it is structurally incapable of finding an underfollowed GARP name. Right tool,
  wrong job.
- Four data legs failed on rate limits that run (earnings, economic, sector
  flow, regime gate), so the run was already degraded.

---

# ADDENDUM 10 — the GARP answer

Definition applied: real earnings, a reasonable multiple against **durable**
growth (never a base-effect EPS number), positive interest coverage recomputed
by hand, and structure still intact.

| | P/E | Rev gr | EPS gr | Quality | Coverage | D/E | ROE | Verdict |
|---|---|---|---|---|---|---|---|---|
| **TILE** | **9.70** | +4.1% | +127.8%* | **87** | 9.30 | 0.32 | **33.5%** | ✅ |
| **VCTR** | 14.86 | **+51.5%** | +68.3% | **94** | 9.39 | 0.41 | 19.3% | ✅ |
| SON | 8.24 | +12.1% | +12.7% | 59 | 4.59 | 1.24 | 17.9% | GARP, chart broken |
| FIGS | 40.78 | +24.7% | +686%* | 71 | 50.5 | 0 | 14.4% | ❌ PEG 1.59 |
| MOD | 67.80 | +29.5% | **-24.0%** | 45 | 6.14 | 0.44 | 12.6% | ❌ |
| ATRO | 39.91 | +14.5% | +1987%* | 59 | 3.54 | 1.57 | 52.0% | ❌ neg FCF |
| MAN | 27.07 | +6.7% | n/a | 42 | 2.26 | 0.50 | 5.1% | ❌ + extended |
| U | **none** | +14.0% | n/a | 35 | -15.5 | 0.74 | -18.9% | ❌ no earnings |

*base effect, unusable for PEG

## TILE — Interface Inc. The best entry.

$37.23 · $2.15B cap · 475K shares/day · earnings **2026-10-30**

Modular carpet tile. Deeply boring, which is the point.

- **P/E 9.70.** ROE **33.5%**, ROA 17.8%. Operating margin 18.9%, net 15.4%.
- Coverage 9.3x, **D/E 0.32**, current ratio 2.53. Quality **87**.
- Analysts 3 strong buy / 5 buy / 1 hold / **0 sell**.
- **Top of BOTH the bullish-pullback and momentum screeners at entryScore 87,
  grade A+** — the only name appearing in both, and the highest grade on either.
  Confirmed stochastic crossover, relative volume 1.41, 3-day institutional
  buying streak.
- **Structure intact:** rising lows $24.37 → $26.44 → $28.12 → $31.08 → $31.54,
  price well above. RSI 51.5, **ADX 18.6** (quiet, not extended), +4.3% over
  EMA50, sitting -0.26% off EMA21. Only -7.8% from the 52-week high.
- **Volume signature is accumulation:** up days average 36,226 against down days
  24,719. Nine of twelve sessions were red but on materially lighter volume.
  That is the exact inverse of SON, and it is what a real pullback looks like.

**Entry $36.50-37.30** (on the EMA21). **Stop $31.40**, under the last swing low.
**Target $40.40** (the 52-week high) then measured continuation. Add on a close
above $40.40.

**The risk:** revenue growth is only +4.1%, so the +127.8% EPS number is margin
expansion, not demand. Commercial flooring is tied to office refit cycles. If
margins normalize the 9.7x becomes 15x on flat revenue and it is dead money.

## VCTR — Victory Capital. The best business.

$113.86 · $6.68B cap · 595K shares/day · earnings **2026-10-29**

- **Quality 94 — the highest score of anything screened today.**
- **Revenue +51.5%, EPS +68.3%** (acquisition-driven, verify the organic split).
- **Operating margin 41.2%**, net 29.6%, gross 82.7%. ROE 19.3%.
- P/E 14.86, forward 12.51. Coverage 9.4x, D/E 0.41.
- **Dividend 2.42% at a 36% payout.**
- Structure intact, rising lows, last swing low $112.11 (8/20). RSI 54.4,
  **ADX 36.0** (real trend), -7.6% from the high.

**The catch on entry:** it is at **86% of its 52-week range and +7.9% above its
EMA50.** That is a shallower discount than TILE. Better business, worse entry.

**Entry:** wait for $105-108 (the EMA50 zone) rather than paying up here.
**Stop $99.** Or buy a starter now and add on the pullback.

## Bottom line

**TILE for the entry, VCTR for the business.** Both pass GARP, both have positive
coverage recomputed by hand, both have intact structure, both report in late
October. If it has to be one name: **TILE**, because a 9.7x multiple with 33.5%
ROE and an A+ pullback grade gives you margin for error that VCTR at 86% of its
range does not.
