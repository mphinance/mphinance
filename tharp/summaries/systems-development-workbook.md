# Van Tharp — Developing a Winning Trading System That Fits You (Systems Development Workbook) — Summary

Source: `Van Tharp - Systems Development Workbook.PDF.pdf` (154 pages, 1996-2004 seminar workbook/transcript, ~$500k-account 3-day live course). Unlike the "Successful Investor" series, this PDF has a genuine (if slightly OCR-garbled — likely typo'd in the original scan, not re-OCR'd here) extractable text layer across all 154 pages — no image OCR needed. Extracted directly via `pypdf`; some words are mangled (missing spaces, "1" read as "l", etc.) — quotes below are cleaned up for readability but numbers/formulas are verified against the raw extraction.

This is the single richest primary source found so far for implementable mechanism — it's the actual seminar transcript behind the models cataloged more drily in the Definitive Guide.

## Structure (3-day seminar)
- **Day 1**: trading psychology (why trading is hard), Trading Simulation Game 1, ten psychological biases, system definition, the 10 Parts of a Good System, modeling top traders (Tom Basso quoted directly), expectancy formula + worked examples, objectives-setting.
- **Day 2**: Trading Simulation Game 2 (the real "marble game" — see below), entry technique concepts, random entry systems, setting initial stops, exit techniques.
- **Day 3**: filters, three full sections on money management (money-management-system money management, rule-based-system money management, "creative" pyramiding money management).

---

## The origin of the "same trades, different sizing" demonstration

This is very likely the actual ancestor of the "Position Sizing Game" mph originally asked about at the start of this whole research thread — it's a live, in-person version predating (or contemporaneous with) the software version cited elsewhere.

**Low-Risk Ideas team exercise** (Day 1 homework, 60 simulated trades over the 2nd/3rd seminar mornings): teams of attendees given **$500,000** in play money, $15 entry fee, an elected group manager with total control over strategy and capital allocation, competing both on 10-trade rolling leaderboards ($10 side-pot per round) and on final **reward-to-risk ratio** (total % gain ÷ max peak-to-trough drawdown %) for the bulk of the pot. Same odds table for every team:

| Marble | Odds | Payout (if long) |
|---|---|---|
| Solid Blue | 55/101 | Lose (win if short) what you risked |
| Solid White | 20/101 | Lose (win if short) 2x what you risked |
| Solid Black | 12/101 | Win 3x / lose 3x if short |
| Light Blue Center | 8/101 | Win 5x / lose 5x if short |
| Dark Blue Center | 5/101 | Win 10x / lose 10x if short |
| Solid Green | 1/101 | Win 20x / lose 20x if short |

Stated result: long positions **lose 74.3% of the time**, win 25.7% of the time — but the wins are fat-tailed (up to 20x). Every team gets the *exact same marbles drawn in the same sequence* (it's one shared "market"), and outcomes still diverge based purely on each team's staking decisions and manager discipline. This is the direct, hands-on precursor to the "identical trades, wildly different outcomes" claim.

**Trading Simulation Game 2** (Day 2-3, the fuller version): same marble mechanic, 30 trades/day over 2 days, drawn one at a time with 2 minutes to decide the next bet between draws — deliberately slow and deliberate rather than a instant simulation, so the psychological pressure of a live losing/winning streak is part of the exercise.

**The exact expectancy of this specific game, computed in the book:** −51¢ per dollar risked if long, **+51¢ per dollar risked if short** (the odds table is stacked short-favorable). Breaking down where that edge actually comes from (short side): 12 marbles pay 3:1 (+36), 8 pay 5:1 (+40), 5 pay 10:1 (+50), 1 pays 20:1 (+20) against 55 losses at 1:1 (−55) and 20 losses at 2:1 (−40) → net ≈ +51 per 101 marbles. **Explicit lesson drawn from this:** "all of the expectancy was due to the 20:1 marble and the five 10:1 marbles" — miss those rare, large-payout draws and the system doesn't actually make money despite a positive long-run expectancy. Directly relevant to fat-tail/skew risk in any strategy backtest.

**The Kelly Criterion for this specific game, stated directly: ~13%.** And immediately followed by, in the source's own emphasis: *"Note that the Kelly Criterion gives you a maximum ceiling for your bet. In reality, your maximum bet size should be nowhere near the Kelly %. It should be well below this level!!!!"* (four exclamation points in the original). This is the plainest, most direct primary-source statement of the "half-Kelly-or-less" caution found across all the Tharp material reviewed so far.

---

## Ten Parts of a Good System (Section 1-10)
1. Market Selection — is this a market I want to trade?
2. Market Direction
3. Setup — what conditions must be present before entry/exit?
4. Market Timing / Entry
5. Protective Stop
6. Re-entry — how do you get back in if stopped out of a good move?
7. Taking Profits
8. Money Management — "knowing that when I'm wrong I will lose X dollars, how big a position am I willing to take?"
9. Portfolio Selection
10. Multiple Systems — trading more than one system to smooth performance

## Expectancy — exact formula and worked examples (Section 1-11 homework)
`Expectancy = (P_win × Amt_win) − (P_loss × Amt_loss)`, generalizable to N discrete outcomes as a probability-weighted sum. **Critical caveat stated directly:** if your win/loss amounts aren't both exactly $1 (or the same unit), you must divide the raw expectancy by your average loss size to get "expectancy per dollar risked" — otherwise you can't compare two systems that risk different absolute amounts per trade.

Worked example (marble game 2, five-color version): P(win) = 0.375, P(loss) = 0.625, avg win = 3.0R, avg loss = 1.0R → expectancy = (0.375 × 3) − 0.625 = **0.5R** (50¢ per dollar risked). Verified two ways in the source (aggregate-then-divide vs. per-tier-probability sum) to the same answer — a good methodology check to reuse.

## Ten Parts / system evaluation criteria, plus the model chain: `Task 10: plug reliability + profit/loss ratio into money management formula → % of equity to risk per trade`. This is the explicit statement that position sizing is *downstream of* expectancy measurement, never decided first — matches this session's earlier point about "measure the real edge first."

---

## Entry, stop, and exit technique catalog (Sections 2-2 through 2-5, 3-2)

**Setting the initial stop (Section 2-4)** — three sound methods, explicitly *not* including a fixed arbitrary %:
1. Natural support/resistance (with the caveat that "obvious" levels get front-run by floor traders — stated as already true in the 1990s, long before algorithmic front-running was a mainstream concern).
2. **Volatility-based** — "if the range of the market over the last 10 days has been X, there's a good chance a move against you by more than that means your idea is wrong." Recommended multiple: **1.5 to 2× volatility**.
3. Technique-based (specific to your entry concept — e.g., a counter-trend entry can justify a tight stop because the entry itself implies a specific invalidation point).

**Exit technique taxonomy (Section 2-5)** — a genuinely useful classification scheme:
- **Static** (price targets) vs. **Adaptive** (ATR-trailing, moving average, parabolic, channel breakout — moves with the market).
- **Dependent** (shouldn't be your *only* exit — large adverse move, price target, time stop) vs. **Independent** (fully sufficient on their own — e.g., hits a 2-week adverse extreme) vs. **Psychological** (burnout, travel, personal state — explicitly named as a legitimate exit category, not just a discipline failure).
- **LeBeau Exit Efficiency Index** = actual profit ÷ maximum potential profit realized during the trade (capped at ~2x the trade's holding period when estimating the max). A genuine, nameable metric for grading exit quality independent of whether the trade was a win.
- Quoted: Michael Marcus (Market Wizards) — exits after the *third* straight limit-up day, cautious by the fourth: volatility/momentum "becoming absolutely insane" is itself an exit signal, not just a risk signal.

**Filters vs. entry signals (Section 3-2)** — a filter narrows the candidate set (e.g., "10-day DMI supports the trade," "ATR[10] < ATR[20]" for contraction), the final condition in the chain is the actual entry/exit trigger. Worth the distinction: a system's total win rate is a blend of how good the filters are at narrowing the field *and* how good the final trigger is — conflating the two makes it hard to diagnose which part of a system is actually adding value.

---

## Money Management for Money-Management Systems (Section 3-3) — the deepest section

**The three equity models, restated with an exact worked micro-example** (matches the Definitive Guide's Total/Core/Reduced-Total distinction, with cleaner arithmetic): a $1,000 trade sized at 10% risk, tracked three ways as price moves from $100→$90→$80 — Core Equity ratchets the base down with every raise of the stop (locks in "abolished risk" as it's earned), Reduced Total Equity is the middle ground, Total Equity would use full mark-to-market including unrealized paper moves.

**Real percentage guidelines** (his own stated numbers, not a generic "use 1-2%"):
- **0.1% to 1% per trade** when managing *other people's* money.
- **0.8% to 2% per trade** when trading your own money.
- **3% or greater is "being a gunslinger"** — attributed directly to Ed Seykota.
- **Total Portfolio Heat should not exceed 20-25%** (sum of risk across all simultaneously open positions) — this is Model 7 from the Definitive Guide's chapter 9, given a concrete number here that the Guide's TOC alone didn't specify.

**Tom Basso's exact risk-control worked example** — genuinely the single most useful implementable passage found across all Tharp material, because it's the mechanical version of "trim a winner, don't let it ride unchecked" that Section 5 of the Substack outline is built around:
- New position: buy gold at $400, stop at $390, $200k account, 1% risk → `$RISK = (400−390) × $100/pt = $1,000/contract`; allowable risk `1% × $200,000 = $2,000` → **2 contracts**.
- Position moves in your favor overnight: gold to $450, stop trails to $405, account now $210,000. New risk-per-contract = `(450−405) × $100 = $4,500`; with 2 contracts, current risk = $9,000 — **exceeds** the (now slightly higher, 2.5%-of-equity) $5,250 ongoing-risk ceiling. Solution: **sell down to 1 contract** (`$5,250 ÷ $4,500 = 1.167`, rounded down). This is a real, numeric, non-discretionary trim rule triggered purely by "your open position's current risk has outgrown your cap," independent of any profit target or reversal signal.
- Direct quote: *"Thus, every day the risk of your position is within a fixed range. Thus you are focused on the process of good trading, letting profits run and keeping risk to acceptable levels."*

**Full Kelly Criterion worked example, formula restated identically to the Definitive Guide** (`Kelly% = A − [(1−A)/B]`, A = win rate, B = avg win/avg loss), applied to a fair-coin-flip-pays-2:1 game → 25%, with the same "nowhere near the Kelly %, well below this level" warning repeated. **Optimal f critique repeated and sharpened**: "Optimal f gives you a *larger* bet size, so the Kelly Criterion is actually a more conservative number. Even though it is more conservative, it is still probably too large for most traders to use safely." States plainly that optimal f assumes you've already had your worst loss, which — given price-change variance may be effectively unbounded — is a dangerous assumption. Formula given again: `TWR = Σ [1 + (−trade_i / biggest_loss)]` over all trades, searched iteratively for the f that maximizes TWR.

**A genuinely new, quantitative table not found elsewhere in this research pass — "Recommended Maximum Portfolio Heat as a Function of Expectancy and Reward-to-Risk Ratio"** (heat number is then divided by the max number of simultaneous positions to get a per-position size):

| Reward:Risk | Exp 0.10 | 0.20 | 0.40 | 0.75 | 1.00 | 1.25 | 1.50 |
|---|---|---|---|---|---|---|---|
| 1:1 | — | 8% | 16% | 32% | 60% | — | — |
| 1.5:1 | 5.3% | 10.7% | 21.3% | 40% | 52.9% | 66.7% | — |
| 1.75:1 | 4.6% | 9.1% | 18.2% | 34.3% | 45.7% | 57.1% | 68.6% |
| 2:1 | 4% | 8% | 16% | 30% | 40% | 50% | 60% |
| 2.5:1 | 3.2% | 6.4% | 12.8% | 24% | 16%* | 40% | 48% |
| 3:1 | 2.7% | 5.3% | 10.6% | 20% | 26.7% | 33.3% | 40% |
| 3.5:1 | 2.3% | 4.5% | 9.1% | 17.1% | 22.9% | 28.6% | 34.3% |
| 4:1 | 2% | 4% | 8% | 15% | 20% | 25% | 30% |

*(the 16% at 2.5:1/1.00 cell is almost certainly an OCR/typo artifact in the source — the surrounding cells strongly imply it should read ~32%; flagged rather than silently corrected.)* **Explicit caveat printed with the table**: "these are designed for maximum return rates, not maximum reward-to-risk — if you've inaccurately estimated your expectancy or reward:risk, your risk could be way too high." This table is effectively a Kelly-style optimal-growth number *generalized across a grid of expectancy/payoff combinations* rather than the one-off single-system Kelly calc — genuinely useful as a lookup table if an agent ever computes live per-strategy expectancy and reward:risk and wants a heat ceiling that scales with those two numbers instead of a flat percentage.

**Volatility-based sizing, worked example, matches Percent Volatility model exactly** (limit position movement to ≤1% of equity based on $ATR): gold at $400, $3.00 average range → $300/contract; 1% of $200k = $2,000 → 6.67 → 6 contracts. **Explicit rule for combining risk-based and volatility-based sizing**: take the *smaller* of the two contract counts, not the larger, not an average.

## Money Management for Rule-Based Systems (Section 3-4)
- Fixed-$-per-unit model, same 55/21 breakout backtest numbers as the Definitive Guide's Table 8-1 (system unusable below ~$30-40k equity, total breakdown at $20k).
- **The Joe Ross Method**, named directly: trade 5 contract units, exit 3 as soon as marginally profitable (covers costs), raise stops on the remaining 2 to breakeven — a specific, nameable "scale out fast, let a small remainder ride risk-free" rule.
- **Larry Williams' Martingale variants**, presented here with less outright condemnation than the Definitive Guide's Chapter 15 (worth noting as a real tension between the two sources rather than smoothing it over): "System Expectations Are Low" — if a 65%-reliability system has only won 7 of the last 20 trades (35%, well below its historical 65%), *increase* size on the theory that reversion to the system's true win rate is due. "Minimal Martingale" — add one unit after every loss, drop back one unit after every win, floor at 1 unit. No caveat about ruin risk is attached to these two in this section, unlike Chapter 15 of the Definitive Guide, which lists Martingale strategies among the ones to avoid outright. **Flag this discrepancy explicitly if citing either source** — the workbook presents these more neutrally/descriptively than the book does.

## Creative Money Management — full pyramiding worked example (Section 3-5)
A complete, numeric, start-to-finish example of pyramiding into a winning corn trade using **the market's own unrealized gains as the source of new risk budget**, never risking more than a 4% ceiling on original capital even while scaling up to 14 total contracts as the trade runs from $3.025 to $3.50:
- Each add-on is sized at 2% of *reduced total equity* (excludes locked-in/abolished risk), with stops on *every* existing lot raised by that period's volatility unit (V) every time a new lot is added.
- Result: total risk to original capital stayed at $3,550-3,600 (3.55-3.6%) throughout, while total profit realized on exit was **$22,100** — a >6x return on the maximum capital actually put at risk, achieved entirely through disciplined position-building rather than a single large initial bet.
- Explicitly tied to a real historical event in the source: the author notes he was looking at an actual corn move above $4.80 while writing this example, and that pressing this exact method through that real move "could have made as much as a million dollars without risking over $3,600."
- Honest caveat included directly in the source, not added by this summary: ending up with 14 contracts is real added tail risk (a limit-move against you would hurt far more than the stated $3,600 "core equity" risk suggests) — mitigated in practice with options, not eliminated.

This is the single clearest, most complete real-world illustration found in any of the Tharp material for "add to a winner using the position's own gains as the funding source, tightening the stop each time" — the mechanical version of "sell some, don't capitulate; also, don't just hold and hope" from Section 5's discussion.

---

## Not yet extracted (flagged, same convention as the Definitive Guide summary)
- Random Entry Systems (Section 2-3) — skimmed for headers only, not read in depth. Likely a demonstration that entry technique matters less than exit/sizing (a very on-thesis section if fully extracted later).
- Appendix II (Answers to the Expectancy Practice Exercises from Section 1-11) — the exercises themselves were captured; the answer key was not reached in this pass.
- Appendix III (Calculating Various Indicators) — likely just standard TA formula reference, lower priority.
- Appendices IV/V (Course Update newsletters on "Parts & Self-Esteem" and "Feelings") — pure psychology content, explicitly out of scope per the triage directive.

## Flagged for future agent integration (not built yet — markdown reference only, per mph's instruction)
- **Tom Basso's trim-on-excess-risk rule** is the most directly implementable mechanism found in this entire research pass: recompute current $ risk on every open position daily (using the current trailing stop, not the entry stop), and if it exceeds the position's risk ceiling, sell down to the largest contract count that fits back under the cap. This requires no forecasting, no discretion, just current price + current stop + a fixed % ceiling.
- **The expectancy/reward-risk → portfolio-heat lookup table** is a ready-made function signature: given a strategy's live-measured expectancy and reward:risk ratio, return a maximum total heat %, then divide by concurrent position count. Worth implementing as a real function rather than a flat 2% rule.
- **The Creative Money Management pyramiding scheme** (add using unrealized gains as risk budget, raise every existing stop each time) is a concrete algorithm, not just a philosophy — directly codeable.
- The **Larry Williams vs. Definitive-Guide-Chapter-15 tension on Martingale-style "double down when underperforming expectation"** is worth resolving deliberately before any agent implements anything like it — the two sources disagree, and Chapter 15's explicit "almost guarantee ruin" warning is probably the more defensible default absent further reading.
