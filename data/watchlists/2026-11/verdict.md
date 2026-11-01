# JUDGE'S VERDICT — November 2026 Long List (EQT, TXN, USB, NVDA, HIMS)
### Neutral adjudication of 3-round bull/bear debate. Data as of Fri 10/30/26 close; verification run Sat 10/31/26 evening (live yfinance option-chain pulls + web search). Research only — no trades placed.

---

## 1. Factual adjudication

### (a) Option prices — bull's "live" numbers vs. bear's "chain is broken, use Black-Scholes"

I ran my own fresh `yfinance` option-chain pull (independent of both agents' sessions) against every contract the R3 bull quoted. **Every single one reproduced exactly:**

| Name | Contract | Bull's quote | My independent pull | Match? |
|---|---|---|---|---|
| EQT | Dec18 $52.50c | mid $4.35 (4.05/4.65) | bid 4.05 / ask 4.65, mid 4.35 | exact |
| TXN | Jan15 300/320 spread | net debit $9.10 | 300c mid 23.425, 320c mid 14.325 → $9.10 | exact |
| USB | Jan15 $60c | mid $2.38 (bid/ask) | bid 2.26 / ask 2.50, mid 2.38 | exact |
| NVDA | Dec18 $200c | mid $15.65 | bid 15.55 / ask 15.75, mid 15.65 | exact |
| NVDA | Dec18 205/220 spread | net debit $6.43 | 205c mid 12.90, 220c mid 6.475 → $6.43 | exact |
| HIMS | Dec18 30/35 spread | net debit $1.26 | 30c mid 2.56, 35c mid 1.305 → $1.255 | exact |
| HIMS | Jan15 30/35 spread | net debit $1.34 | 30c mid 3.20, 35c mid 1.86 → $1.34 | exact |

**Verdict: the bull's live prices are real and trustworthy.** The bear wasn't lying about the chain being broken — it is, but only in the **deep-ITM/legacy junk strikes** (NVDA sub-$50 strikes show IVs from 0.00001 to 14.0, crossed/zero bid-ask, clearly stale illiquid listings with no real market). The strikes actually used in every trade construction (NVDA 190-230, TXN 280-330, USB 55-65, HIMS 25-40, EQT 45-60) print a clean, monotonic IV smile with sane bid/ask spreads. The bear over-generalized from "the tails are garbage" to "the whole chain is unusable" and fell back to modeled Black-Scholes prices it didn't need to for TXN/USB/HIMS/EQT. Its NVDA caution was reasonable in spirit (that chain has the most junk) but the ATM/near-ATM NVDA strikes were fine too.

**Use the bull's real market quotes for trade construction below**, not the bear's modeled ones. The bear's *qualitative* conclusions (theta/vega bleed, negative option EV over the hold) stand regardless of this — they're about decay mechanics, not price level, and the modeled premiums were in the right ballpark anyway.

### (b) NVDA earnings: 11/17, not 11/18 — resolved definitively

Live search confirms NVIDIA's own investor-relations press release: call is **Tuesday, November 17, 2026, 2pm PT / 5pm ET**, covering the quarter ended 10/25/26. The 11/18 date floating on secondary aggregator sites carries its own disclaimer ("not yet officially confirmed"). **Trust 11/17.** This also resolves a related loose thread: TXN's Q3 report date conflict (10/21 vs. 10/27) — confirmed via TXN's own SEC 8-K filed 10/21/26. TXN truly has no November earnings event; the 10/27 date some tracker cited was wrong.

### (c) Bear's probability math (NVDA ~19% gap-through-stop, HIMS ~11% entry-fill) — recomputed, holds up

**NVDA:** stop $194 vs. spot $204.64 is a -5.34% move. Bear's derived one-day earnings sigma is 6.2%. Normal approximation: z = -0.0534/0.062 = -0.86 → P ≈ 19.5%. **Matches the bear's number.** Caveat: the 6.2% sigma is itself back-derived (gap between 2-week and 1-month implied vol), not a directly quoted number — a modeling assumption, not a live fact. Real earnings-gap distributions are fat-tailed vs. normal, so if anything this 19% is a **conservative (low) estimate** of true gap risk, not inflated.

**HIMS:** entry zone $26.50-27.70 vs. spot $27.68, 1-week sigma 16%. z1 = ln(26.50/27.68)/0.16 = -0.27; z2 = ln(27.70/27.68)/0.16 = 0.0045. P(inside zone) = Φ(0.0045)-Φ(-0.27) ≈ 50.2%-39.3% = **10.9% ≈ 11%. Matches.** Worth noting this finding is semi-tautological: the zone's upper bound (27.70) sits almost exactly on today's spot (27.68), so "~50% chance of printing above the zone" is nearly definitional, not a discovery. The real finding — and it's correct — is that the zone is narrow relative to a 16%-sigma week, so the stated plan has very low odds of ever being the plan that executes. **Both bear figures check out arithmetically; no correction needed.**

### (d) "December hike priced 75-86%" — corroborated, probably conservative

Web search (post-10/28-meeting reporting is thin, but pre-meeting data is solid) finds independent secondary sourcing (Motley Fool citing CME FedWatch) putting **December-hike odds at ~90% as of 10/20**, with other coverage discussing "two hikes by December" as a live scenario. Combined with the confirmed 10-2 FOMC hold with **two explicit hawkish dissents** (Cook, Hammack), this is not noise — the bear's 75-86% range is directionally right and arguably **light**. Treat "a December hike is a real, high-probability event" as well-corroborated. This matters most for USB.

---

## 2. What each side actually conceded (the real signal)

**EQT** — flat scores across all 3 rounds on both sides (bull 5→6→6, bear 6→7→7). Both sides agree: business is genuinely improving (guidance raise, capex discipline, fresh 28-34%-upside analyst targets) AND the chart has no trend (ADX 15) AND the RRC merger-arb flow mechanically caps near-term upside for ~5 months. This is a **timing/structure disagreement, not a quality disagreement** — the rare case where 3 rounds of adversarial pressure didn't move either side much, which is itself informative.

**TXN** — bear's score climbed every round (7→7→8) while bull's fell every round (7→6→5). Bull fully conceded the NVDA-correlation point ("no catalyst of its own to offset a bad 11/17 print") and the stale/already-priced consensus-target finding. Bear conceded fundamentals are clean throughout — this was never a "broken business" argument, only "bad entry, borrowed risk."

**USB** — the most one-directional case: bear climbed 7→8→9, never rebutted on its final, decisive point (a hike helps NIM later but hurts bank equities immediately via multiple compression — two-sided and laggy exactly when a 1-month trade needs the opposite). Bull conceded the 50SMA lid and the 2.52 bearish put/call OI reading stand unrebutted in all 3 rounds.

**NVDA** — bull's own construction section conceded in full: "the dossier's stop/TP table does not survive contact with the market's own priced move," forcing a split into a smaller, de-risked Path A/B structure (score 8→6 in round 3, the single biggest swing in the debate). Bear conceded quality score 99 and the textbook setup are real "if 200 holds" — this was never an argument that NVDA is a bad company, only that the binary 11/17 event breaks a full-size swing trade wrapped around it.

**HIMS** — bull collapsed into the bear's own conclusion by round 3 ("don't trade this before 11/9... no pre-earnings position"). The only surviving bull points (beat-and-raise guide, litigation resolved, short-interest fuel) are real but don't rescue the stated trade plan, which my own probability check confirms has roughly 1-in-9 odds of even being executable as written.

---

## 3. Scores (1-10, 10 = best long for November given his constraints)

| Name | Score | Confidence | One-line why |
|---|---|---|---|
| EQT | 6 | Medium-high | Clean business, true negative-beta hedge, tight stop — but capped by arb-driven dilution flow and no trend (ADX 15); it's ballast, not alpha |
| NVDA | 6 | Medium | Highest-quality business + best raw R:R on the list, but the binary 11/17 event (confirmed ~19% gap-through-stop) breaks the naive plan — only works if traded in two de-risked pieces, not full size |
| USB | 5 | Medium | Cheapest, most concretely tradeable convexity (real $2.38 Jan 60c) and a genuinely improving NIM/credit trend, but weakest R:R of the five and now faces a corroborated, two-sided December-hike risk this specific month |
| TXN | 5 | Medium | Clean balance sheet, no own catalyst — but you're chasing a vertical move into stacked resistance with thin/negative modeled option EV and a free-ride on NVDA's binary risk |
| HIMS | 3 | High (on "skip pre-earnings") | Worst quality score in the basket; the stated entry plan has ~11% odds of ever being fillable; only a legitimate trade as a small, confirmed post-earnings add |

---

## 4. Final trade cards (bull's R3 construction reconciled against bear's objections — using verified real market prices)

### EQT — BUY ON TRIGGER
- **Instrument:** Shares, or Dec 18 $52.50 call as a stock substitute (delta ≈0.69, **live mid $4.35**, bid 4.05/ask 4.65 — verified)
- **Entry:** confirmed daily close **> $55.50** (clears Friday's close and the gamma flip ~55.15). Don't buy the 54.50-55.50 zone blind — ADX 15 means there's no trend to front-run.
- **Stop:** close < $52.75 (50SMA)
- **TP1:** $57.50 (scale out — stacked gamma/call-wall resistance)
- **TP2:** $60.25 (pursue only if TP1 clears with volume/flow confirmation)
- **R:R:** ~0.73R / 1.73R (honest, confirmation-entry cost — thinner than the dossier's blind-entry framing)
- **Size: 1.0R** (full unit) — true portfolio diversifier (negative beta), but note this hedge is fair-weather: in a genuine panic, correlations go to 1 and the "negative beta" benefit disappears.

### TXN — WAIT (don't chase)
- **Instrument:** Jan 15 2027 300/320 call debit spread — **verified live net debit $9.10** (300c mid 23.42, 320c mid 14.33)
- **Entry:** Plan A (preferred) — limit on a pullback to **$288-292** (21EMA zone). Plan B — confirmed close **> $310** only (skip the no-man's-land in between; don't buy at today's $300.84, that's the spike top, not a pullback).
- **Stop:** close < $288.9 (21EMA) — exits the spread; max loss capped at the $9.10 debit regardless of gap size
- **TP1:** $311.50 (partial)
- **TP2:** ~$320 cap — close near max value before expiry, don't hold for full intrinsic
- **R:R:** ~1.2R at TP2 — thin, reflects the fact this name has no catalyst of its own
- **Size: 0.5R** — explicitly because this trade inherits NVDA's binary 11/17 risk by correlation (0.51/0.49) with none of NVDA's own upside if the print goes well

### USB — WAIT for confirmation
- **Instrument:** Jan 15 2027 $60 call — **verified live mid $2.38** (bid 2.26/ask 2.50), delta ≈0.5, only ~4% of spot
- **Entry:** confirmed close **> $60.00** (clears the dossier's own conceded "50SMA lid" at 59.57). Do not buy the 58.75-59.50 zone as proposed — you'd be buying directly under a level the plan itself calls a ceiling.
- **Stop:** close < $59.00 (21EMA) after a confirmed entry
- **TP1:** $62.50 (the real dominant gamma wall — intrinsic here is roughly breakeven on the call, not a profit zone)
- **TP2:** $65.40 stretch — this is the level that actually pays (~2.3R)
- **R:R:** thin until TP2; the trade only works if it runs the full stretch
- **Size: 0.75R** — cheap, real, verified convexity and genuine diversification value earn more than a token slot, but the weakest R:R of the five plus the now-corroborated two-sided December-hike risk (hurts bank equities immediately, helps NIM only later) cap it below full.

### NVDA — Two paths, earnings handled explicitly, never full size
- **Path A (core, 0.5R):** Dec 18 $200 call, **verified live mid $15.65** (bid 15.55/ask 15.75). Entry: confirmed close **> $210** (gamma flip) — don't catch the falling knife in the 200-205 zone the dossier proposes; below the flip, dealers amplify down-moves. Stop: close < $200 (200SMA + OI wall — both bull and bear frameworks agree this is where the whole setup dies). **TP1: $218.40 — take profit or trail to breakeven BEFORE the 11/17 close. Do not carry full size through the print.** R:R ≈0.84 (the honest cost of respecting the gap instead of the dossier's 1.9).
- **Path B (optional, lotto, 0.25R max):** Dec 18 205/220 call debit spread, **verified live net debit $6.43** (205c mid 12.90, 220c mid 6.475) — a separate, clearly-labeled bet for anyone who wants capped-risk convexity actually held through the 11/17 print.
- **Combined cap: 0.75R, never more** — the confirmed ~19% one-day gap-through-stop probability means this is a disguised earnings bet in a swing-trade costume if sized and held like the other four.

### HIMS — SKIP pre-earnings, WAIT UNTIL 11/10 for confirmation
- **No position before 11/9 AMC.** The stop (~7.5% below mid) is roughly half the market's own priced one-week move (±16%), and the stated entry zone has an independently-verified **~11% chance of ever being fillable as written.** This isn't a conviction call, it's arithmetic.
- **Contingent post-earnings plan (if HIMS gaps up and holds — e.g., closes above the $30 call wall with volume/higher-low):** Dec 18 or Jan 15 $30/$35 call debit spread. **Verified live:** Dec18 net debit $1.26 (30c mid 2.56, 35c mid 1.305); Jan15 net debit $1.34 (30c mid 3.20, 35c mid 1.86). Enter on confirmation the session *after* the print (post-crush repricing), not the gap itself. Stop: close < $28.44. TP1: $32.50. TP2: $35 (spread cap).
- **If HIMS gaps down or the reaction is mixed:** stand aside for all of November.
- **Size: 0R pre-earnings. 0.25R maximum post-confirmation-up.** Never scale this one up regardless of how clean the confirmation looks — 81% annualized vol / 2.8 beta means even a quarter-unit swings the book disproportionately.

---

## 5. Portfolio level

**Chip-sleeve cap:** NVDA (0.51/0.49 correlated to TXN) and TXN share one transmission mechanism — NVDA's 11/17 print flows into TXN with no offsetting TXN catalyst. **Cap the combined NVDA+TXN sleeve at ≤1.0R** (0.5 NVDA core + 0.5 TXN), not 1.0R apiece. This is sound, not conservative theater — it's the correct response to a real, measured correlation plus a shared binary event.

**Total deployed if every trigger fires at stated size:** EQT 1.0R + USB 0.75R + TXN 0.5R + NVDA 0.5R (+0.25R optional lotto) + HIMS 0R (pre-earnings) = **~2.75-3.0R of a nominal 5.0R equal-weight budget.** That's intentionally under-levered: two names share one catalyst risk, and the fifth is a confirmed coin-flip that gets zero size until it proves itself. The undeployed ~2.0-2.25R is dry powder staged around the two known binary dates (11/9 HIMS, 11/17 NVDA/TXN), not cash sitting idle by accident.

**What a bad week looks like:** Using Friday's *actual realized* behavior (NVDA -4.2%, TXN -3.9% in one session on a semis-specific day — realized vol running hotter than the 126-day regression beta would predict) plus the fact that NVDA and HIMS both sit in negative-gamma regimes (dealers amplify moves in a selloff, they don't dampen them), a genuine -3%-SPY stress week plausibly produces something like **EQT flat-to-slightly-up, USB -1 to -2%, TXN -9%, NVDA -9 to -10%, HIMS -12 to -13%** — a basket stress case roughly **double SPY's own decline**, concentrated in exactly the two names that also carry the worst option-construction math (NVDA, HIMS). The one thing to internalize: **EQT's hedge value is a fair-weather phenomenon.** Correlations go to 1 in a real liquidity panic, and both the negative beta and the merger-arb flow supporting it are things that stop working precisely when you'd need them most. Don't oversize EQT on the theory that it's a clean portfolio insurance policy — it's a diversifier in a normal month, not a crash hedge.

**Ranking, best to worst for November:**
1. **EQT** — cleanest execution, real (if capped) fundamental improvement, true diversifier, low drama.
2. **NVDA** — highest business quality and best raw edge on the list, but only if traded in the disciplined two-path, mostly-de-risked-before-11/17 structure above. Highest payoff, highest execution-discipline requirement.
3. **USB** — genuinely improving fundamentals and the cheapest real convexity in the book, undercut by the weakest R:R and a freshly-corroborated, two-sided rate risk landing inside the hold window.
4. **TXN** — clean business, but you're paying up to buy someone else's binary risk at a level the Street has already mostly priced in.
5. **HIMS** — skip it pre-earnings. Full stop. Revisit only on a confirmed up-gap, and only small.

Research only. No trades placed.
