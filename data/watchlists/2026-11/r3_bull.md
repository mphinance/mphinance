# Round 3 — BULL case: trade construction and execution
### Nov 2026 longs: EQT, TXN, USB, NVDA, HIMS — ~1 month hold, LONG shares or LONG calls only, no put selling.
Data: dossier Fri 10/30 close + live yfinance option-chain pull 10/31 evening (spot + Dec18/Jan15 call chains, bid/ask/IV/OI — all verified live, prices below are real, not modeled). Deltas computed with Black-Scholes off those live IVs (r=4%) — **approximate**, not exchange-quoted greeks; flagged where it matters.

**Framework: 1R = one risk unit = a fixed, equal-weight starting allocation if this were a flat 5-way split. Sizes below are expressed as fraction of 1R per name, not dollars.**

---

## EQT

**Rebutting R2 bear's strongest remaining point:**

> "The deal is now fully specified: 0.987 fixed exchange ratio, zero cash, EQT issuing stock for 100% of the ~$12.8B deal, and multiple outlets explicitly attribute EQT's post-announcement drop to dilution concerns and merger-arbitrage activity... That flow doesn't show up as bearish options tape... it just quietly caps every rally in EQT shares for the next five months."

Partial rebuttal, not a knockdown: arb-driven short pressure front-loads right after a fixed-ratio deal is announced (10/26) and decays as the spread locks in — a lot of that selling has plausibly already happened in the four sessions since. UBS ($74, 10/29) and Bernstein ($71, 10/29) set their targets *after* seeing the dilution math and are still 28-34% above spot — sell-side already modeled the dilution and stayed bullish. I can't fully rebut the "caps rallies for five months" framing — it's structurally real for a stock-for-stock deal with a Q1 2027 close — so **concede that upside beyond the near resistance ladder is genuinely capped by mechanical arb flow, not just technical resistance.**

> "No verified winter-gas catalyst exists... EIA's own July 2026 STEO puts Q4 2026 Henry Hub around $3.57/MMBtu — unremarkable."

**Fully concede.** No counter-evidence found. Don't lean on a cold-winter story for this trade.

**Best trade construction:**

Given low ADX (15, no trend by its own standard) and an arb-driven ceiling, this is **shares, not calls.** A capped-upside, slow-grind name is exactly where paying extrinsic premium is the wrong instrument — theta bleeds while the stock chops under a known overhang. If calls are preferred for capital efficiency, use a **deep-ITM stock substitute**, not a lotto ticket: Dec 18 $52.50 call, live mid **$4.35** (bid 4.05/ask 4.65), delta ≈0.69 — moves almost dollar-for-dollar with the stock at ~12% of the capital outlay.

- **Entry trigger:** wait for a **confirmation close above $55.50** (clears both Friday's close and the live gamma flip ~55.15) rather than buying blind into the 54.50-55.50 zone — ADX=15 means there's no trend to lean on, so don't front-run the reclaim.
- **Stop:** close < $52.75 (50SMA break, unchanged from dossier).
- **TP1:** $57.50 — take partial size here; this is the stacked gamma/call-wall level the bear correctly flagged as "major resistance," so treat it as a scale-out, not a pass-through.
- **TP2:** $60.25 — only pursue if $57.50 is cleared with volume/flow confirmation (a sign the arb-cap is breaking, e.g., spread convergence or an HSR-clearance headline). Otherwise trail the stop to breakeven after TP1 and don't assume TP2 happens on schedule.
- **R:R (honest, using the confirmation entry at $55.50, not the dossier's $55.00 mid):** risk $2.75 to stop; reward $2.00 to TP1 (R:R 0.73), $4.75 to TP2 (R:R 1.73). Worse than the dossier's framing — that's the real cost of waiting for confirmation instead of buying the zone blind, and it's the honest number given the conceded arb cap.
- **Size: full unit (1.0R).** It's the one name in the book you can hold in shares with a tight, well-defined stop and a real structural diversification benefit (negative beta) — the safety case survives contact with real execution even though the R:R is thinner than advertised.

---

## TXN

**Rebutting R2 bear's strongest remaining point:**

> "Consensus analyst price targets sitting around $305-324... against $300.84 close leave almost nothing on the table even in the bull scenario — and MarketBeat's consensus rating is Hold, not Buy... TXN doesn't need its own catalyst to fall in November — it just needs NVDA's 11/17 print to disappoint, given the 0.51/0.49 correlation."

Partial concession: the consensus-target compression is real, but it's an average masking a bifurcated Street (individual targets to $400/KeyCorp, $350/Rosenblatt) — targets lag momentum and a Hold-consensus average isn't the same as "no analyst sees more room." **The NVDA-correlation point I fully concede** — TXN genuinely has no catalyst of its own to offset a bad 11/17 print, and that has to shape position construction, not just conviction.

> "Four different TXN directors filed Sale+OE transactions on 10/27 and 10/29... each director cutting 12-28% of their personal stake."

Concede the fact, discount the signal: Sale+OE (option-exercise-linked) is the most routine insider-selling category and none were the CEO/CFO. Real, but low-information.

**Best trade construction:**

Since the real risk is a **correlated gap from someone else's earnings event**, not TXN's own fundamentals, cap the downside structurally rather than size down and hope: use a **Jan 15 2027 300/320 call debit spread** (clears Dec and runs past 11/17 with buffer). Live pricing: 300c mid $23.42, 320c mid $14.32 → **net debit $9.10**, max value $20 at expiry, breakeven $309.10. This caps capital at risk to the premium regardless of how NVDA's print goes, versus an outright call or shares that eat the full correlated move.

- **Entry trigger:** this is a chase at spot (bear's #1 R1 point, still valid) — **don't enter here.** Plan A (preferred): limit the spread on a pullback to **$288-292** (21EMA zone). Plan B: if no pullback comes, only enter on a **confirmed close above $310** (clears both stacked GEX walls at 310/315) — i.e., skip the no-man's-land in between rather than buying the zone the dossier proposes.
- **Stop/exit:** close below **$288.9** (21EMA) invalidates the uptrend-intact thesis — exit the spread; max loss is capped at the $9.10 debit regardless.
- **TP1:** $311.50 — take partial profit on the spread (value should be meaningfully above cost here, well before expiry).
- **TP2:** spread cap near $320 — close for ~90%+ of max value on a tag, don't hold for full intrinsic into expiry.
- **R:R:** $9.10 risked, ~$10.90 max reward at the cap → **~1.2R** at TP2. Thin, and that's honest — it reflects the bear's correctly-identified lack of a TXN-specific catalyst. The spread exists to make that thin edge survivable, not to manufacture a better number.
- **Earnings handling:** TXN has no 11/17 print of its own, but **treat NVDA's 11/17 as TXN's event too** — the Jan expiry buys duration through it, and the defined-risk structure means a bad NVDA print costs the premium, not an open-ended shares-style drawdown.
- **Size: half unit (0.5R).** Explicitly because this trade inherits binary risk from a name it doesn't control, with no fresh catalyst of its own to lean on.

---

## USB

**Rebutting R2 bear's strongest remaining point:**

> "The Fed's 10/28 decision was a hold with two hawkish dissents (Cook, Hammack) explicitly voting for a hike, and pre-meeting pricing had December-hike probability at 75-86%... it's a regime change for a rate-sensitive regional bank, not a one-day blip to buy through."

Partial rebuttal: a hike, if it happens, is not uniformly bad for USB specifically — this is a balance-sheet lender that's posted **three consecutive quarters of NIM expansion** (2.75% → 2.79% → 2.84%) with management guiding further expansion in Q4, inside a steepening curve (10Y-2Y +0.38%). A hawkish Fed defending against inflation in a steep-curve environment has historically helped asset-sensitive bank margins more than it's hurt them — the bear's framing treats "hike risk" as a generic negative without engaging that USB's own trend is already moving the right direction into it. **Fully concede the CRE overhang** (~$875B maturing in 2026, ~1/3 on regional-bank books) — real, standing, no fresh USB-specific data either way; treat as background tail risk, not a November catalyst.

**Best trade construction:**

Cheapest IV of the five (25.5-27.1%) makes this the one name where **straight long calls beat a spread** — there's no need to sell a leg to cheapen already-cheap premium. Live pricing: Jan 15 2027 $60 call, mid **$2.38** (delta ≈0.52), only ~4% of spot for defined-risk exposure. Use Jan expiry (not Dec) to carry past the Dec 8-9 FOMC without being forced to exit into the event.

- **Entry trigger:** **do not buy the 58.75-59.50 zone as proposed** — the dossier's own language calls the 50SMA ($59.57) a "lid" directly overhead, and the dominant Apex gamma magnet ($62.50) is 3+ dollars away, not acting as nearby support. Wait for a **confirmation close above $60.00** (clears the 50SMA lid and the rank-2 gamma strike) before entering.
- **Stop:** close back below **$59.00** (21EMA) after a confirmed entry — a quick stop-and-go rule, since a confirmation entry that round-trips below the level that triggered it has failed.
- **TP1 (revised up from the dossier):** **$62.50** — this is the real dominant gamma wall per the bear's own GEX read, not $61; treat it as the first meaningful resistance, not a mid-target.
- **TP2:** $65.40 stretch — pursue only on continuation through $62.50 with flow confirmation, not as a default hold.
- **R:R (honest):** entering the call near $60 at $2.38, breakeven ~$62.38 at expiry. Intrinsic at TP1 ($62.50) is roughly breakeven — **this trade only pays at TP2** (intrinsic ~$5.40 vs $2.38 cost ≈ 2.3R). This confirms rather than fixes the bear's correctly-flagged "weakest R:R of the five" — construction gets you cheap, long-dated, defined-risk convexity, but it doesn't manufacture a better reward profile than the stock actually offers.
- **Size: three-quarter unit (0.75R).** Cheap convexity and genuine diversification benefit (uncorrelated, low beta) earn more than a token allocation, but the thin, TP2-dependent R:R caps it below full.

---

## NVDA — earnings gap handled explicitly

**Rebutting R2 bear's strongest remaining point:**

> "Michael Burry's depreciation-accounting critique is a live, named, large bear position against this exact stock... a direct threat to the demand side of the bull case."

Partial rebuttal: the depreciation-schedule debate is a multi-year accounting argument, not a 1-month demand signal — even if directionally correct, it wouldn't move the 11/17 print. The round 2 bear itself flagged the cited **$1.1B short figure as "single-sourced, treat cautiously."** **Fully concede the China-export-status point** — unresolved, no fresh data, must be treated as a live tail risk the trade has to survive, though the Q3 guide ($108B ±2%) already assumes zero China revenue, meaning a beat doesn't require China to resolve.

**Honest answer on construction: the dossier's stop/TP table does not survive contact with the market's own priced move.** The 1-month implied move is 13% (band $179-234) — nearly double the distance from entry-mid to TP1, and it swallows both the stop ($194) and TP1 ($218.40). Holding full size through 11/17 on that structure is a disguised earnings bet wearing a swing-trade costume.

**Two honest paths, not one:**

- **Path A (default) — trade the pre-earnings technical setup only, flatten/de-risk before 11/17.** Entry trigger: wait for a confirmed **close back above $210** (the live gamma flip) rather than buying into 200-205 — the bear's negative-gamma argument (dealers chase momentum down, not up, below the flip) means catching the falling knife at the dossier's entry zone risks buying into an accelerating move. Vehicle: Dec 18 $200 call, live mid **$15.65** (delta ≈0.60), or shares at the $210 reclaim. Stop: close < $200 (both the 200SMA and the OI/gamma wall — if this breaks, the whole setup is dead by either side's read). TP1: $218.40 — **take profit or trail to breakeven before 11/17 close**, don't carry full size into the print. R:R on this leg: risk $10 (210→200), reward $8.40 to TP1 (R:R 0.84) — worse than the dossier's 1.9, because confirmation-entry + mandatory pre-earnings exit costs real reward. That's the honest price of respecting the gap.
- **Path B — if choosing to hold a clip through 11/17, cheapen it given IV rank 60 ("rich").** Dec 18 $205/$220 call debit spread: live mid 12.90 − 6.47 = **$6.43 net debit**, max value $15 (R:R ≈1.3 on width) — roughly half the capital at risk of an outright $205 call for the same breakeven distance, because you're selling rich upside premium back into the same event instead of buying it outright.

**Recommendation: Path A is the core position; Path B, if used at all, is a separate, clearly-labeled "I want upside convexity on the print" allocation — not sized as core thesis.**

- **Size: half unit (0.5R) for Path A.** If adding Path B, an additional quarter unit (0.25R), explicitly binary/lotto money. **Combined cap 0.75R, never full**, regardless of how clean the pre-earnings chart looks.

---

## HIMS — earnings gap handled explicitly

**Rebutting R2 bear's strongest remaining point:**

> "HIMS converting a higher-margin, vertically-integrated compounding business into a lower-margin reseller of a branded competitor's drug — a real structural headwind... lands during the exact quarter that has to prove out the new mix" + "a finance-leadership gap during a complex revenue-mix transition... exactly the kind of setup where reporting surprises get amplified" + "consensus is thin and specific ($892.7M rev / $0.06 EPS)... leaves almost no room for a GLP-1 transition cost."

**Largely concede** — this is real, structural, and was already conceded in round 2. One genuine pushback: management guided Q3 revenue ($880-900M) *above* the Street consensus that existed when they gave that guide, and a six-cent EPS consensus is a volatility amplifier in both directions, not a one-way bear signal — a small dollar beat or miss on EBITDA/opex can flip the percentage surprise large either way. Short interest (53.5M sh, 5 days to cover) remains real mechanical fuel if the print goes up, which the bear doesn't dispute, just doesn't lean on.

**Honest answer: don't trade this before 11/9 AMC.** Nothing in three rounds of research — bull or bear — fixes the core sizing problem: the stated stop (~7.5% below mid) is roughly half the market's own priced one-week move (±16%). That's not a thesis issue, it's arithmetic. **No pre-earnings position.**

**Post-earnings plan (two branches):**

- **If HIMS gaps up and holds** (confirms beat-and-raise + short-covering fuel — e.g., closes above the $30 call wall with volume, or a next-day higher-low): enter on confirmation, not the gap print itself (post-earnings IV crush means repricing the option before entering, not assuming the pre-print quote). Use a **Dec 18 or Jan 15 $30/$35 call debit spread** (live Dec18 pricing: 2.56 − 1.30 = **$1.26** net debit; Jan15: 3.20 − 1.86 = **$1.34**) rather than outright calls — HIMS historically stays vol-rich even post-crush, so cap cost/vega with a spread. Stop: close back below $28.44 (old gamma flip, now a support/resistance pivot to retest). TP1: $32.50 (roughly half the spread's max value). TP2: $35 (spread cap).
- **If HIMS gaps down or the reaction is mixed/negative:** stand aside for all of November. The quality score (13/100), confirmed margin compression, and CAO gap stack too high to justify fading a confirmed bad print — revisit in December, not as a dip-buy.

- **Size: zero pre-earnings. Post-earnings-up-confirmation only: quarter unit (0.25R) maximum**, regardless of how clean the confirmation looks — 81% annualized vol and 2.8 beta mean even a quarter-size position swings the book disproportionately. Never scale this to half or full on a single name this volatile.

---

## Portfolio level: splitting risk across the five

Given **NVDA-TXN correlation 0.51/0.49** (the one meaningfully correlated pair) and **three names with beta ≈2+** (HIMS 2.8, NVDA 2.1, TXN 2.0):

- **Treat NVDA + TXN as one combined "chip sleeve,"** not two independent bets — they share both daily-return correlation *and* a single transmission mechanism (NVDA's 11/17 print flows into TXN via correlation with no offsetting TXN catalyst, per the bear's strongest TXN point). Cap the **sleeve's combined size at ≤1.0R** (0.5R NVDA + 0.5R TXN), not 2.0R as it would be if each traded independently at full size. If both were sized full-unit separately, a single bad NVDA print would hit both legs simultaneously — that's double-counting one risk as two.
- **HIMS's beta (2.8) is a red herring for correlation purposes** — its correlation to NVDA/TXN is low (0.33/0.20), meaning its risk is idiosyncratic (an earnings-gap event), not shared chip-sector beta. It doesn't need to compete with NVDA/TXN for the same risk bucket, but its standalone volatility (81% ann.) means even its small quarter-unit allocation contributes outsized P&L swing on its own — size it small for its own reasons (binary event, weak quality score), not because it's "part of the chip sleeve."
- **EQT (beta −0.27) and USB (beta 0.43) are the real diversifiers** — both near-zero/negative correlation to the other four names and to SPY. These carry the book's ballast and are the only two names sized at or near full unit.

**Resulting allocation (fraction of 1R per name):**

| Name | Size | Rationale |
|---|---|---|
| EQT | 1.0R | True diversifier (negative beta), shares not calls, clean stop |
| USB | 0.75R | True diversifier (low beta/uncorrelated), cheap convexity, but thin R:R |
| TXN | 0.5R | Chip sleeve — inherits NVDA's binary risk with no own catalyst |
| NVDA | 0.5R (+0.25R optional lotto) | Chip sleeve — real earnings gap the stop/TP table can't defend; capped, de-risked into 11/17 |
| HIMS | 0R pre-earnings → 0.25R max post-confirmation | Binary event + worst quality score in the book; never more than a quarter unit |

**Total deployed: ~2.75-3.0R of a nominal 5.0R equal-weight budget.** That's intentionally under-levered — two names share one catalyst risk and one name is a flat coin-flip that shouldn't get full-unit sizing no matter how the research reads. The un-deployed ~2.0-2.25R is dry powder, sequenced around the two known binary dates: available to add to NVDA/TXN after 11/17 confirms, or to size HIMS up post-11/9 if that print confirms — the budget is staged around the catalysts, not dumped in on 11/2.

---

## Final bull conviction (1-10) and movement from Round 2

| Name | R2 bull | R3 bull | Δ | Why |
|---|---|---|---|---|
| EQT | 6 | **6** | — | Construction holds up (shares, full size, clean stop), but honest confirmation-entry R:R is thinner than the dossier implied — net unchanged |
| TXN | 6 | **5** | ↓1 | Real execution (Jan spread, wait-for-dip-or-confirm, half size) survives the correlated-gap risk, but the honest R:R that comes out the other end (~1.2R) is thin enough to trim conviction, not just caveat it |
| USB | 6 | **7** | ↑1 | Live option pricing confirms the cheap-convexity thesis is concretely executable (Jan 60c only $2.38) — a real, priced positive the research rounds couldn't quantify; raises conviction even though R:R stays TP2-dependent |
| NVDA | 8 | **6** | ↓2 | Business/technical conviction stays high, but construction forces the hardest concession of the debate: the stated trade plan doesn't survive the 13% implied move into 11/17. Must be traded smaller, de-risked, and largely exited before the print — that's a real comedown from round 2's enthusiasm, not a change in the business case |
| HIMS | 4 | **4** | — | Construction confirms rather than changes the picture: still "don't trade before 11/9," now with a real if/then plan for after. No new information moved it, execution just operationalized the wait |

Research only. No trades placed.
