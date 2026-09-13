# Before You Click Buy — scratch outline

Companion piece to "The Exit Problem" (published artifact, 2026-09-05). That one covered what happens once you're in a trade. This one covers why you got in and how much of the account is on the line — the pre-trade side.

Source: same 30-day mine of TraderDiscord chat (vip-chat, general, beginner-questions, ask-an-analyst, expert-chat), pulled from `/data/vecstore/meta.db` on the bot container. Handles to be masked in any published version.

Note: the Fidelity `History_for_Account_237815769.csv` pulled in during scratch work is a **specified test/paper portfolio**, not a real account — not fair game as a personal-receipts anecdote, and not evidence of mph's own behavior. Dropped as a source. If a real personal anecdote is wanted later, it needs to come from an actual account.

**Format call:** one long piece, same shape as Exit Problem. Override me if you disagree.

**Title call:** going with **"Before You Click Buy"**. "The Line" is a good chapter title (see centerpiece) but a weak headline on its own — doesn't signal "pre-trade" the way Exit Problem's title signals "post-trade." Keeps the pairing legible.

**Leverage — unparked.** Folded in below as its own section (5), built on the CPPI research (deeper research pass in progress below). This is the "stay in the trade, just deleverage" idea you asked about.

**Through-line mph flagged:** it's not just about picking the right stocks — exits matter and almost nobody talks about them. That's the connective tissue between this piece and Exit Problem: this one is entries/sizing, that one was exits, and the server (like most retail chat) is loud on picks and silent on both.

---

## 1. Portfolio Allocation
How much of the account any one idea is allowed to eat.

**The spine of this section: our own simulation, not just a citation.** Built a Monte Carlo replication of the Van Tharp "same trades, different sizing" demonstration instead of just describing his game — real numbers, our own inputs, reproducible (`/tmp/.../scratchpad/sizing_sim.py` this session; re-derive/re-run when drafting).

- Setup: a positive-edge system — 40% win rate, wins average +2.5R, losses fixed at -1R (stop discipline), +0.39R expectancy per trade. One realistic trend-following profile, held constant across every test.
- Five sizing schemes applied to that *same* system, 5,000 independent 30-trade runs each, starting from $10k:

  | Sizing | Median final | Bust rate | Median max drawdown |
  |---|---|---|---|
  | All-in, 25% risk/trade | $8,631 (a loss) | 14.6% | 88.8% |
  | Full Kelly (~16%) | $15,198 | 0.7% | 70.5% |
  | Aggressive, 10% | $17,062 | 0% | 51.8% |
  | Half-Kelly (~8%) | $16,733 | 0% | 43.5% |
  | Textbook, 2% | $12,186 | 0% | 12.7% |

- **The headline stat:** the all-in trader running the *exact same positive-expectancy system* as everyone else has a median outcome that's a loss, and busts outright 14.6% of the time. The mean looks fine (~$124k average) because a few lucky compounding runs post absurd numbers — that's the trap. Mean is a lie here; median is what actually happens to a typical trader, and it's a loser on a system that objectively has an edge. Same trades, same edge — the only variable is bet size.
- Supporting citation, now secondary to our own numbers: **Van Tharp's Position Sizing Game** — same demonstration, anecdotal version, up to a third of a room going broke off identical signals. ([Van Tharp Institute](https://vantharpinstitute.com/van-tharps-position-sizing-trading-simulation-game/))
- Evidence (Discord): one member's "no matter what I do I lose $2k/month," down to $35k from a retirement carve-out — a sizing/concentration problem more than a bad-picks problem.
- Evidence (Discord): same trader posting 7 correlated LEAPS (mostly momentum/growth names) as one "gut check" — that's one bet wearing seven tickers, not diversification.
- Angle: correlation blindness — miners, AI-adjacent names, momentum LEAPS all move together. The server treats position *count* as diversification.
- To do: turn the simulation into an equity-curve chart for the actual post (a few "unlucky" all-in runs vs. a few textbook-2% runs, same starting line, wildly different endings — visual gut-punch version of the table above).

**Real-data companion to the synthetic sim — the Tharp Port backtest.** Same idea, done on 25 real, recognizable tickers (`tharptestlist.txt`: ARM, ASTS, AVGO, BB, BULL, CRWV, GLXY, GOOGL, HIMS, HL, HOOD, JOBY, LLY, MLI, MU, NBIS, NVDA, ONDS, OUST, RDDT, RKLB, TER, TMC, TSM, UAMY), $100k, bought 1/1/26, held through 9/4/26. No trading skill involved at all — same 25 names, same buy date, only the *sizing model* differs. Reproducible: `docs/drafts/tharp-port/data/raw_bars.json`, `analyze_v3.py`, `results_summary_v3.json` (v1/`analyze.py` and v2/`analyze_v2.py` kept as the before/after trail — see the bug-hunt story below, it's a real beat, not just process notes).

**v3, final and corrected — this is the version to write from:**

| Sizing model | Static buy-and-hold | + Quarterly rebalance | + Monthly top-ups ($500/mo) |
|---|---|---|---|
| Equal-$ / equal-weight | $122,471 (+22.5%), maxDD 31.2%, 97.7% deployed | $129,421 (+29.4%), maxDD 25.5% | $127,452 on $104,500 contributed (+22.0%) |
| Percent-risk (%ATR-stop implied) | $124,956 (+25.0%), maxDD 27.4%, 98.1% deployed | n/a | n/a |
| Percent-volatility (inverse %ATR) | $124,956 (+25.0%), maxDD 27.4%, 98.1% deployed | $132,856 (+32.9%), maxDD 21.4% | $130,042 on $104,500 contributed (+24.4%) |
| "1 share of each" (no model at all) | $101,223 (+1.2%), maxDD 1.2%, 3.8% deployed | n/a | n/a |
| **SPY buy-and-hold (benchmark)** | **$112,710 (+12.7%), maxDD 9.1%** | n/a | $117,545 on $104,500 contributed (+12.5%) |

**The v1→v2→v3 bug-hunt is itself worth a paragraph in the piece, not just process notes:**
- **v1:** the ATR-based models used a fixed per-trade risk-budget formula (built for sizing one position in an active account) applied naively across 25 simultaneous positions. Result: 17.5%/36.6% of capital deployed, the rest idle in cash — made "risk management" look like it just meant "make less money."
- **v2:** fixed the deployment by normalizing weights to sum to 100%. Deployment jumped to 98%+. But this surfaced a *second*, worse problem: weighting by raw dollar ATR silently means "buy huge piles of cheap stocks" — BB, a $3.80 stock with a tiny dollar ATR despite normal percentage volatility, ballooned to **60.8% of the entire portfolio**. It then happened to more than double, which is the only reason v2's "risk-managed" rows looked like they'd won.
- **v3 (final):** weight by ATR **as a percentage of price**, not raw dollars — the actual correct inverse-volatility approach. BB's weight drops to a sane ~10%, in line with equal-weight's own worst case (MU at 10.0%). This is the version above, and the version to actually cite.
- **Why this belongs in the writeup, explicitly:** the piece is *about* the danger of trusting a formula without checking what it actually does. Getting our own formula wrong twice before landing on the real one isn't an embarrassing footnote to cut, it's the single most honest demonstration of the whole thesis available — including to us.

**Findings that survive into v3:**
- **Percent-risk and Percent-volatility are mathematically identical models,** confirmed again under the corrected weighting (max weight difference across all 25 tickers: 0.00000000). The constant factor of 2 between "risk to a 2×ATR stop" and "raw ATR" cancels out completely once both are normalized. "Risk-based" and "volatility-based" sizing get marketed as different philosophies; here they're the same formula wearing two names.
- **Equal-weight concentration finding still holds:** every name in equal-$ started at an identical 4.0% weight, no decisions made. By 9/4, MU alone was 10.0% of the book, because MU ran +222% while JOBY (-53%), MLI (-45%), RDDT (-36%), and TMC (-35%) dragged. Nobody chose that, the math did.
- **Rebalancing finding, still real:** quarterly rebalancing helped both models it ran on — better return AND lower drawdown than static, for both equal-$ and percent-volatility. It also shifted percent-vol's top holding from BB to NVDA (9.5%) by trimming the winner back to target weight on schedule. Free money, not a tax on upside.
- **The SPY line, still the reality check:** equal-weight and the (now correctly weighted) percent-vol model both beat SPY's static +12.7%, by a believable margin (+22.5% / +25.0%–32.9%) rather than the implausible +43–70% v2 was showing. That believability is itself the point — a result that looks too good usually is, and v1→v2→v3 is the receipts for why you check.

**Bonus finding — what if the undeployed reserve gets phased in instead of dumped in day one?** Using the v1 percent-vol core (36.6% deployed at entry, correctly %ATR-weighted) plus the remaining 63.4% phased in over 8 monthly contributions: DCA landed at $116,604 (+16.6% vs. contributed), value-averaging (no-sell variant, buys more of whatever lagged its own target path) landed at $116,445 (+16.4%) — both meaningfully behind the $125,322 (+25.3%) of just deploying the full $100k on day one. Phasing in cost ~9 points of return in this specific 8-month window, because 2026 was a broadly rising tape for this basket — the classic "time in the market beats timing your entries" result, reproduced on real tickers instead of cited from a Vanguard study. Worth stating honestly which way this cuts: it's a property of this window being an up year, not a universal law that DCA is wrong. VA's slightly lower ending concentration (top holding 7.9% vs. DCA's 8.9%) is a small real edge for effectively no cost. Script: `docs/drafts/tharp-port/dca_va_reserve.py`.

### Sidebar: what "Kelly" means (plain-language explainer)

Needed because the table above name-drops "Full Kelly" / "Half-Kelly" — can't use those terms without explaining once, cleanly, no jargon-dump.

- **What it answers:** given you actually know your edge (win rate + average win/loss size), how much of your account should you risk on the next trade to grow it as fast as possible *without* risking ruin.
- **The formula, in plain English:** `Kelly % = win rate − [(1 − win rate) ÷ (avg win ÷ avg loss)]`. Plug in our system's numbers — 40% win rate, wins 2.5x the size of losses — and Kelly says risk 16% per trade.
- **The counterintuitive part, and the actual point of including this:** betting *more* than Kelly doesn't just add risk, it makes your expected growth rate go down. Not "riskier for the same reward" — actually worse, mathematically, because a big enough loss compounds a hole the next win literally can't undo at the same rate it was dug. That's the table above: "All-in 25%" underperforms "Full Kelly 16%" on every metric. It's not more aggressive, it's past the peak of the curve.
- **Why half-Kelly is the practitioner default, not full Kelly:** your win-rate and average-win estimates are guesses, not certainties. Overestimate your edge even slightly and "full Kelly" quietly becomes "past Kelly" without you knowing it. Halving the size gives up some theoretical growth but cuts the bumpiness roughly in half — the better trade-off when your inputs are guesses, which they always are.
- **The one-sentence version for readers:** Kelly isn't "bet more when you feel confident" — it's proof there's a precise point past which betting bigger makes you worse off, not just riskier. You don't need to compute it exactly. You need to know the peak exists.
- **The twist worth naming explicitly: Van Tharp doesn't use Kelly. He built his framework partly against it.** Kelly (1956) and Ralph Vince's "Optimal f" (the 1990s trading adaptation of Kelly) both try to mathematically derive the growth-maximizing bet size from a known edge. Tharp's actual position, in his own writing, is that both are dangerous in practice — they collapse a strategy's real outcomes into an oversimplified win/loss binary, ignore volatility, and calculate sizes that are "optimal" only in an infinite-repetition limit no real trader lives in, producing drawdowns nobody survives psychologically even when the math is technically right. His Percent Risk model exists as the deliberate alternative: pick a risk-per-trade number based on what you can actually stomach and what your system supports, not what a formula says maximizes theoretical growth. ([Position Sizing in Trading — QuantInsti](https://blog.quantinsti.com/position-sizing/))
- **Why this belongs in the piece, not just in these notes:** it reinforces the half-Kelly caution from two independent directions instead of one — the math itself says don't go full Kelly, and separately, the person behind the "same trades, different sizing" demonstration this whole section is built on doesn't trust Kelly-style optimization at all. That's a stronger, more honest beat than treating Kelly and Van Tharp as two friendly citations sitting next to each other.

## 2. Risk
Position sizing and stops as a system, not a vibe.

- Evidence: the 2%-of-account day-trader vs. the zero-stop-loss LEAPS trader — both valid, but beginners can't tell which philosophy is theirs to borrow.
- Evidence: "ATR can help people that need structure with position sizing and stops" — said in passing, never expanded on.
- Stat to use: a trader risking 10% of equity per trade who hits a 6-loss streak is down ~46% and needs an 85% recovery; at 1% per trade the same streak costs ~6% and needs 6.4% back. Same losing streak, wildly different hole. (Lunaro, position sizing brief)
- Angle: risk-per-trade as a number decided in advance, not discovered after the drawdown.

## 3. Technicals
Reading a chart vs. reacting to one.

- Evidence: confident callouts ("that's resistance," "stacked EMA") but real questions underneath — what a doji stage actually means, what the OI-heat coloring represents, how far back a pivot-point lookback goes.
- Angle: the server is fluent in TA vocabulary, shakier on when a signal is actually valid vs. just a word applied after the fact.

## 4. Fundamentals
The blind spot, not the confusion.

- Different shape than the other sections: there's almost no fundamentals talk at all. A stray CapEx or earnings comment here and there, otherwise ~100% flow/technicals-driven.
- Angle: this section isn't "clearing up confusion," it's "here's a lens you're not using at all." Probably the shortest section, but worth naming explicitly.

## 5. Leverage — staying in the trade without staying exposed
The parked point, now unparked. No name for the technique, and that's fine — doesn't need one.

- The idea, refined: this isn't only "de-risk when a position is losing." It also applies on a winner — sell the LEAPS, buy the shares; sell the 2x, buy the 1x. Same direction, less convexity/decay, still in the trade. Selling green still counts.
- **Pair it with IV timing, this is the real mechanism, not just "take profits":** buy the leveraged optionality (calls, LEAPS) when IV rank is low — cheap premium, and volatility mean-reverts, so it's more likely to expand later than stay depressed. Sell/convert to shares once IV has richened — captures the delta gain *and* the volatility give-back everyone else is about to eat, and gets you out of paying rich premium for convexity you don't need anymore. Standard options-desk logic (IV rank, variance risk premium), not exotic. ([Barchart: options for every IV scenario](https://www.barchart.com/story/news/35112485/best-options-trades-for-every-implied-volatility-scenario), [IV Rank explainer](https://www.marketmagicians.com/blog/implied-volatility-rank-ivr-options-trading))
- **Worked example (from the test-account data, framed as technique-in-action, not confession):** the BULL Jan '27 $7.5 LEAPS calls and the GLXY Jan '27 $25 LEAPS call — sold to close while green, proceeds rolled into plain shares of the same names. Bought the leverage, the underlying worked, sold the option (banking the gain and the rich premium) instead of holding it into decay, kept the shares. That's the mechanic, with real trade dates and prices to show, not describe.
- Research anchor for the "de-risk without exiting" idea generally: **CPPI (Constant Proportion Portfolio Insurance)** — mechanically cut risky exposure as a position loses value (not to zero), keep the rest, re-risk as it recovers. ([QuantPedia](https://quantpedia.com/introduction-to-cppi-constant-proportion-portfolio-insurance/), [Wikipedia](https://en.wikipedia.org/wiki/Constant_proportion_portfolio_insurance))
- **The honest complication, real-world, not theoretical:** risk-parity and vol-targeting funds do exactly this mechanically, and it went badly twice — Feb 2018 "Volmageddon" and March 2020 (VIX to 85), both times the funds deleveraged into the same falling market everyone else was deleveraging into, at the worst possible moment, because the models all fired the same rule at once. "Downshift, don't sell" can quietly turn into "you cut right before it turned, at scale, with everyone else." ([Forbes: risk parity and coronavirus](https://www.forbes.com/sites/katinastefanova/2020/03/23/coronavirus-strikes-a-deadly-blow-to-risk-parity/), [Volmageddon Feb 2018](https://www.sixfigureinvesting.com/2019/02/what-caused-the-february-5th-2018-volatility-spike-xiv-termination/))
- **Why almost nobody does this (behavioral angle):** Odean's 1998 disposition-effect study (10,000 discount brokerage accounts, 1987–93) — investors are 1.5–2x more likely to sell a winner than a loser, and the winners they sell go on to outperform the losers they keep holding. The deeper reason people default to hold-everything-or-sell-everything instead of a partial delever: any move that locks in less than the full position, win or lose, feels like admitting the bet is over — so most people don't make partial moves at all. ([Odean 1998, Journal of Finance](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00072), [Disposition effect overview](https://en.wikipedia.org/wiki/Disposition_effect))
- Connection to Section 1's Kelly sidebar: this is fractional-Kelly in practice — reduce size as conviction/edge changes, don't treat sizing as a one-time binary decision made at entry and never revisited.

## 6. Drawing the Line — commitment and admitting defeat (centerpiece)
- Evidence: the 7-LEAPS gut-check where every single answer was "hold" — nobody had pre-committed to an "I was wrong" condition.
- Evidence: "too much of a bag holder to sell... but I can DCA down heavy" — said as a joke, is actually the whole problem in one line.
- Evidence: the self-deprecating "I'm a degen / idiots like me" humor running through the chat — doing real work covering for undiscussed risk behavior.
- Angle: the discipline isn't picking the right stop-loss number, it's writing the "I was wrong" condition down *before* entry, when you're not emotionally invested in being right yet. Ties back to the LEAPS section of Exit Problem, but as the missing first step, not the last one.
