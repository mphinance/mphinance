# From Blank Screen to a Trade: The TraderDaddy Pro Process

*A live walk-through. Every number here came off the tools in one sitting on
Wednesday 2026-07-09, ~7:10pm ET, after the close. Nothing is cherry-picked.
Each step maps to one screen in the product — grab the matching screenshot from
the SHOTLIST.*

---

## The one rule

Don't pick a stock. Let the process hand you one.

The whole point of the toolset is that you start with the market, not with a
ticker you already like. You scan, you narrow, you pressure-test. The name that
survives is the trade. If nothing survives, you don't trade. That is the entire
discipline.

What follows is that funnel, run for real. It even rejects its own first pick
halfway through — which is the best part, so read to the end.

---

## Step 1 — Scan. Get a name you didn't start with.

Open the **Screeners**. Run **Bullish Pullback** (Tao of Trading) at defaults.

> [SCREENSHOT: screener-bullish-pullback]

Top of the list: **UCTT** — entry score **80**, grade **🎯 A**, sector
**Producer Manufacturing (semiconductor equipment)**. Price 106.19, sitting
1.85% under its 21 EMA with a stochastic crossover firing. Deep pullback inside
a stack that is still stacked (8 > 21 > 34 > 55 > 89 EMAs, all rising).

What to read on this screen: the grade, the pullback depth, and the **sector**.
Hold that sector in your head. We check it next.

---

## Step 2 — Zoom out. Is the whole neighborhood hot?

Open **Sector Flow**. You are not asking about UCTT here. You are asking whether
the money is flowing *toward* what UCTT is.

> [SCREENSHOT: sector-flow]

- **Semiconductors (SMH): +2.49%, $363M of net call flow.**
- **Technology (XLK): +2.18%.**
- **Cybersecurity and Financials both flagged 🔥 ALL CYLINDERS.**

The screener handed us a semiconductor name. The flow board says semiconductors
are being bought hard today. That is two independent tools agreeing before we
have looked at a single chart. **The thesis is no longer "UCTT" — it is
"semiconductors."** That reframe is what protects you from falling in love with
one ticker.

---

## Step 3 — Check the regime. What kind of tape is this?

Open **GEX Overview**. This tells you whether the market amplifies moves or
dampens them today.

> [SCREENSHOT: gex-overview]

Read: **LONG_GAMMA, ~$23.6B total.** Market makers are net long gamma. They buy
dips and sell rips. Translation: mean-reverting, low-volatility tape. **Favor
defined-risk structures and levels, not big directional bets.** Chasing a
breakout into long gamma is fighting the dealers.

While you are here, open the **Economic Calendar** and clear the runway.

> [SCREENSHOT: econ-calendar]

FOMC minutes already dropped Wednesday afternoon. Nothing high-impact is left
this week. No landmine between us and the weekend. Good.

---

## Step 4 — Smart-money check on your name. This is the gate.

Now, and only now, point the tools at the actual ticker. Open **Unusual
Activity** and filter to **UCTT**.

> [SCREENSHOT: unusual-uctt-empty]

**Zero trades.** No blocks, no sweeps, no splits. Whatever institutions are
doing in semis today, they are not doing it in UCTT.

That is the first red flag. A clean chart with no smart money behind it is a
setup, not a signal. Keep going, but with your guard up.

---

## Step 5 — Liquidity and volatility reality check. The veto.

Before you ever think about a structure, confirm the options on this name are
actually tradeable. Pull **IV Rank**, the **Put/Call Ratio**, and glance at a
**Strategy Ideas** preview.

> [SCREENSHOT: uctt-iv-and-chain]

Here is what comes back on UCTT:

| Check | Reading | Verdict |
|---|---|---|
| ATM IV | **117%** | Premium is enormous |
| Bid/Ask (95 put) | **$9.30 / $13.10** | ~30% wide. Brutal slippage |
| Near-dated P/C volume | **0 / 0** | Nobody is trading the front |
| Earnings | **In 25 days, inside the window** | Event risk baked in |
| Expected move | **±29%** | Untradeable range |

The strategist flags `earnings_in_window: true` on every single structure it
builds. The quote quality comes back **"wide."**

**Verdict: UCTT is a beautiful stock setup and an unusable options name.** Thin,
wide, volatility through the roof, earnings landmine sitting in the window.

This is the process working exactly as designed. The screener found the name.
The smart-money and liquidity gates threw it back. **You did not lose money on
UCTT because the tools told you not to be there.**

---

## Step 6 — The fork.

You now have two honest choices:

1. **Trade UCTT shares** if you want that pullback — the equity setup is real,
   it is just the options that are broken.
2. **Express the semiconductor thesis through a liquid, flow-backed name** — the
   right move if you want an options trade in this regime.

We are here for the options walk-through, so take door 2. Back to the flow board
— this time looking for the theme's liquid leader.

---

## Step 7 — Find the theme's liquid leader.

Open **Unusual Activity** again, unfiltered, and read the semiconductor prints.

> [SCREENSHOT: unusual-nvda]

**NVDA: a $58M call block at the 202.5 strike.** Tight two-sided market. Deep,
liquid chain. No earnings for 48 days. Aggregate tape is $437M bullish vs $219M
bearish. This is where the semiconductor money actually is.

Note what just happened: NVDA was **not** our starting pick. The process routed
us here. It earned its slot by being the liquid, institutionally-backed
expression of a thesis the *screener* surfaced through a different name entirely.
That is the difference between "I like NVDA" and "the funnel put me in NVDA."

---

## Step 8 — Drill the earned name.

Now run the single-ticker stack on NVDA: **GEX**, **IV Rank**, **Edge X-ray**,
**Put/Call**.

> [SCREENSHOT: nvda-gex]
> [SCREENSHOT: nvda-edge-xray]

- **Gamma (GEX):** spot 202.78, **positive gamma**, flip at $198.26. Walls at
  **$200 support / $202.5 pin / $205 resistance.** Coiled in a dealer-defended
  box — consistent with the long-gamma read from Step 3.
- **IV Rank: 13.6.** ATM IV 39.5%. Premium is **cheap** versus NVDA's own band.
  That argues for *buying* premium, not selling it.
- **Edge X-ray (the confirm):** graded across the whole chain, **calls carry a
  −2.5% median IV residual (underpriced) and puts +2.6% (rich).** An independent
  tool, arriving at the same answer: buy cheap calls.
- **Put/Call: 0.38, bullish** — 1.2M calls vs 455K puts on the front.

Every layer points the same direction without being forced. Cheap calls, upside
defined by the $205 wall.

---

## Step 9 — The ticket.

Open **Strategy Ideas**. Direction bullish, capital ceiling $1,000.

> [SCREENSHOT: nvda-strategy-ideas]

Top-ranked structure:

**NVDA $200 / $215 bull call spread, expiring Aug 14 (36 DTE)**
- Cost / max loss: **$647.50**
- Max profit: **$852.50**
- Breakeven: **$206.48**
- Est. POP: **43%**
- No earnings in the window.

The ranker put the **debit** spread above every credit structure — because IV
is cheap, buying beats selling. The short strike ($215) sits just past the $205
gamma wall. The machine reasoned the same way a disciplined human would, and it
priced the legs off the live chain while doing it.

---

## The chain of evidence

Read back up the page. Every step narrowed, and each one was a real gate:

1. **Screener** → UCTT (a name you didn't start with)
2. **Sector Flow** → semiconductors are hot (thesis forms, ticker demoted)
3. **GEX + Calendar** → long-gamma, no catalysts (favor defined risk)
4. **Unusual Activity (UCTT)** → empty (first red flag)
5. **IV / P/C / Strategy preview** → 117% IV, wide, earnings in window (**veto**)
6. **Fork** → shares, or a liquid proxy
7. **Unusual Activity (theme)** → NVDA is where the money is (name earned)
8. **GEX / IV / Edge X-ray** → cheap calls, three tools agreeing
9. **Strategy Ideas** → the actual $200/$215 spread

The name was never chosen. It was the last one standing. And one perfectly
good-looking setup got thrown out along the way, which is the whole reason the
process is worth running.

*Snapshot frozen 2026-07-09, 7:10pm ET. Prices and flow move; the process
doesn't.*
