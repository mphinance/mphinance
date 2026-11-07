# Options and flow lens (as of the Fri 2026-11-06 close)

Sources: TDPro MCP (gex, apex, iv rank, expected move, unusual activity, dark pool, short interest, insiders) and yfinance chains pulled Sat 11-07 (Friday closing quotes; after-hours bid/ask can be stale, so treat spreads as indicative). Realized vol is computed from yfinance daily closes (RV20, RV60, annualized). Where a tool returned nothing, it says so.

Tool limits worth knowing:
- Insider tool only covers the last 21 days, not 6 months. A 6 month read was not possible.
- Dark pool returned no summary for HUM, PCVX or FNF at 5 and 30 days (failed=false, 0 prints). That is a coverage gap on small names, not a signal.
- get_gex_ticker was only pulled for TSLA. For the other three the Apex tool's gammaFlip and strike ranking were used.
- Unusual activity for HUM, PCVX, FNF: 0 rows at minScore 60 for the 11-06 session.

## TSLA (spot 358.22). Verdict: WATCH, confidence low to med

Plan: dip to 352-355 holding, stop 335, T1 385.19, T2 398.50, expires 12/4.

Dealer levels
- Positive gamma (net GEX +65.9M), flip 344.05 (apex flip 346.57), so spot is 4.0% above the flip. Gamma pocket: long gamma against a short-gamma market, which the tool describes as pinned and mean reverting.
- Put support 355 and 350 (350 is also dPlus). Max gamma strike 362.5; 360 holds the largest absolute gamma (224.7M, call OI 9,250 / put OI 8,578), directly over the entry. Apex #1 magnet is 377.5 (score 100), #2 350 (95).
- The entry zone sits on the support walls, which helps. The stop at 335 is below the flip (344 to 347) and into negative-GEX strikes, so a break there is amplified, which is what a stop wants. Targets fight the regime: 385 sits between the 380 (call OI 12,314) and 385 (call OI 10,330) walls, and 398.5 is under the 400 wall (call OI 21,585). Positive gamma dampens a 27 to 40 point rally.

Vol
- IV rank 62.6 (rich), ATM IV up from 41.9% to 51.6% over 5 sessions (self tracked). Chain IV 52 to 58%. RV20 57.9%, RV60 47.1%. Calls are fair against the last 20 days, rich against 60.
- One week expected move 9.0% (band68 327 to 392, band95 299 to 429). Stop 335 is inside the 68% band, 6.5% below spot and 5 to 6% below the entry zone. The expected move swallows the stop.

Chain (calls, Fri close)
- Dec 4 (plan expiry): 355C 22.45 / 23.60, mid 23.03, OI 160 (thin). 360C 19.70 / 20.60, OI 728. 385C 9.50 / 9.80, mid 9.65, OI 1,539. 400C 5.75 / 5.90, OI 3,630.
- Dec 18: 350C 29.75 / 30.60, OI 7,609. 355C 27.00 / 27.50, OI 948. 385C 13.45 / 13.75, OI 2,144.
- Best expression if taken: Dec 4 355/385 call spread, mid debit 13.38 (355C 23.03 less 385C 9.65), width 30, max gain 16.62 at 385 and above, breakeven about 368.4. Pay about 14.10 working the natural sides. Risk is capped at the debit versus 20 per share on shares to the 335 stop. The 355C leg has OI 160, so work it as a limit. Annual meeting 12/3 falls inside the hold.

Flow
- 11-06 unusual activity: total premium $251.7M, bullish $134.0M vs bearish $117.6M, near balanced. Largest was a $20.1M put golden sweep, flagged bearish (puts opening). Many "bearish" prints are call closings and "bullish" prints are put closings, so the labels flip often (sentimentFlipped true on several). Read as two sided hedging, not a clean lean.
- Dark pool net: 5 day -$600.4M (accumulation $774.8M, distribution $1,375.2M, 1,188 prints), 30 day -$129.2M (accumulation $4,146M, distribution $4,275M). The 5 day lean is distribution; the 30 day is roughly flat.
- Short interest 69.35M shares, days to cover 2.22, -2.23% vs prior; daily short ratio 0.467.
- Insiders: 0 filings in the 21 day window.

Decided it: (1) positive gamma pinned over the entry with targets 27 to 40 points into call walls; (2) stop inside the one week 68% band with IV rank 62.6; (3) 5 day dark pool net -$600M distribution against balanced options flow.

## HUM (spot 433.74). Verdict: WATCH, confidence low

Plan: pullback trigger 414.93, stop 399.35, T1 433.21 (about spot).

Dealer levels
- Apex flip 406.64, net GEX +7.0M, so spot is 6.7% above the flip. Strikes 420 (score 76) and 430 (61) are positive-GEX support under spot; 410, 400 and 390 are negative GEX. Top magnet is 450 (score 100), then 460.
- The trigger 414.93 sits between support at 420 and the flip, so it is a dip into thinner support. The stop 399.35 is below the flip and on the 400 negative-GEX strike, which is coherent. T1 433.21 is the current price and a strike (430) with positive GEX, so there is no dealer headroom to T1; the magnet is 450 above it.

Vol
- IV rank 24.5 (cheap), but ATM IV fell from 58.7% to 45.5% over 5 sessions. Chain IV about 51 to 52%. RV20 32.9%, RV60 36.8%. Implied is roughly 15 vol points above realized, so calls are cheap by rank but not cheap against realized.
- One week expected move 7.7% (band68 401 to 469). Entry-to-stop is 15.58 (3.8%), about half the one week 1 sigma move, so the expected move swallows the stop.

Chain (calls, Fri close), illiquid
- Nov 20: 420C 22.20 / 27.70 (spread 5.50, about 22% of mid), OI 1,198. 415C 24.90 / 31.60, OI 31. 450C 7.40 / 13.20, OI 845.
- Dec 18: 430C 28.80 / 34.60 (spread 5.80), OI 1,206. 420C 34.20 / 38.40, OI 298.
- Jan 15: 430C 35.10 / 40.00, OI 238. 450C 26.00 / 31.80, OI 208.
- Flag: spreads of 5 to 6 dollars on 20 to 40 dollar mids. A spread would cross two of these. Best expression: shares only.

Flow
- 11-06 unusual activity: none (0 rows).
- Dark pool 5 and 30 day: no data (coverage gap).
- Short interest 3.67M shares, days to cover 1.98, +31.39% vs prior; short ratio 0.431.
- Insiders: 0 filings in 21 days.

Decided it: (1) T1 equals spot, no dealer headroom until the 450 magnet; (2) wide, thin chain makes options a poor expression; (3) no flow data at all (unusual activity and dark pool empty), short interest up 31%.

## PCVX (spot 63.89). Verdict: WATCH, confidence low

Plan: breakout trigger 65.88, stop 59.19, T1 72.89.

Dealer levels
- Apex flip 70.38, above spot, net GEX -0.67M, so spot is in a short-gamma regime (moves amplified), which suits a breakout. Magnets: 65 (score 100, 1.7% above spot), 60 (95), 70 (77, the only positive-GEX strike among the top four). Large legacy OI at 45 (17,779).
- Trigger 65.88 is just through the 65 magnet. The stop 59.19 sits under the 60 magnet. T1 72.89 is past both the 70 strike and the 70.38 flip, where regime turns long gamma and dampens; the move to 70 is supported, the last 2.9 points less so.

Vol
- IV rank 12.4 (cheap). ATM IV 55.5% (11/05, down from 64.0%). Chain IV 54 to 60%. RV20 53.5%, RV60 74.1%. Implied is about equal to RV20 and below RV60, so calls are cheap on both measures.
- One week expected move 11% (about $7.0; band68 57 to 72). Entry to stop is 6.69 (10.2%), below the one sigma move. The stop is swallowed; spot to stop (4.70) is also inside the band.

Chain (calls, Fri close), illiquid
- Nov 20: 70C 0.65 / 1.25, OI 448 (spread 0.60). 65C 1.85 / 4.00, OI 451.
- Dec 18: 70C 1.00 / 2.75, mid 1.88, OI 1,310 (spread 1.75, about 93% of mid). 65C 3.70 / 6.50, OI 274. 75C 1.00 / 4.90.
- Jan 15: 70C 3.00 / 4.50, mid 3.75, OI 1,019, volume 30. 65C 3.70 / 7.50, OI 219. 75C 0.70 / 3.80.
- Flag: best liquidity is Jan 15 70C (spread 1.50 on 3.75 mid, 40%). A call spread would cross two wide markets. If options at all, a Jan 15 70C limit near mid for the cheap-IV exposure, sized as a small lottery; otherwise shares.

Flow
- 11-06 unusual activity: none.
- Dark pool 5 and 30 day: no data (coverage gap).
- Short interest 14.62M shares, days to cover 2.89, -15.42%; daily short ratio 0.771.
- Insiders (21 days): two small sales on 11-02, CAO 3,000 sh at 60.92 ($182,753, -10% of holdings) and COO 2,250 sh at 60.90 ($137,024, -2%), both Sale+OE; no buys.

Decided it: (1) short-gamma regime and cheap IV rank 12.4 fit a breakout; (2) stop inside the one week expected move on a name that swings 11% a week; (3) options markets are wide and flow is blank, so size must stay small.

## FNF (spot 43.84). Verdict: CUT, confidence med

Plan: pullback trigger 41.24, stop 38.46, T1 44.11.

Dealer levels
- Apex gammaFlip null (no flip computed), net GEX -0.65M. Only four expirations exist. Walls: 40 (score 100, OI 4,962, negative GEX) under spot, 45 (93, OI 4,305) above. T1 44.11 is 0.27 above spot and a point under the 45 wall; the 40 strike sits between trigger and stop, and the stop 38.46 is below it.

Vol
- IV rank 58.3 (rich); ATM IV 38.4% (11/05, from 44.2%). Chain IV 37 to 54%. RV20 29.0%, RV60 27.3%. Implied runs roughly 10 vol points above realized, so calls are expensive.
- One week expected move 11% (band68 39 to 50). Entry to stop is 2.78 (6.7%) against a one sigma of about $4.8, so the stop is swallowed. (Hold rate for the band is 0.99, i.e. options have historically overstated this name's moves.)

Chain (calls, Fri close), illiquid
- Nov 20: 45C 0.15 / 1.35, OI 455. 40C 3.80 / 6.10, OI 347.
- Dec 18: 45C 1.05 / 1.70, mid 1.38, OI 249 (spread 0.65, about 47%). 40C 3.70 / 6.70, OI 192.
- Flag: the chain is thin and wide. No sensible options expression; shares only, and the plan's own gap is R 1.03 to T1.

Flow
- 11-06 unusual activity: none.
- Dark pool 5 and 30 day: no data (coverage gap).
- Short interest 11.98M shares, days to cover 4.88, +2.55%; daily short ratio 0.815.
- Insiders: 0 filings in 21 days.

Decided it: (1) rich IV rank 58.3 and implied above realized, with a thin 45 wall right over T1; (2) stop inside the one week expected move, and the plan's own replay was 0 T1 first, 2 stopped; (3) an extended bounce in a downtrend with no flow evidence of sponsorship.

## Summary table

- TSLA: watch, low to med. Dec 4 355/385 call spread, mid 13.38 debit (work toward 14.10 natural).
- HUM: watch, low. Shares only; chain spreads of 5 to 6 dollars.
- PCVX: watch, low. Shares, or Jan 15 70C near 3.75 mid as a small lottery.
- FNF: cut, med. No options expression; shares only if at all.
