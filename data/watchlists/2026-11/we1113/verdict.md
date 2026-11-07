# Verdict, week ending 2026-11-13 (baseline Fri 2026-11-06 close)

Regime is RISK-OFF (-40, haircut 0.55): VIX/VIX3M inverted, credit under its 50d, SPY in negative gamma. The brief is to stay small. Total deployed is 1.0R across 3 names, against about 4R last week.

## Kept
- TSLA (6, 0.5R): dip to 352-356 that holds, stop 343 (under the 344 flip), targets 362.5 and 377.5. Positive gamma, lowest ATR, no earnings until February. Largest size on the board because it is the only name where dealers dampen the move; risk about 10 vs about 8.5 and 23.5 reward.
- TSM (5, 0.25R): dip to 369-372 that holds, stop 357.8, targets 380 and 390. First target is under 1:1; it earns a slot only on the second.
- INTC (5, 0.25R): dip to 55-56 closing in the upper half, stop 52.6, targets 59.8 and 60.9. Real CEO purchase, but negative gamma and a poor recent record.

TSM and INTC correlate at 0.73, so the pair is capped at 0.5R combined (it is exactly that).

## Why the rest went
The bull case itself found only about 4 arguable names. Fixed rule applied: reward to a realistic first target must be near or above 1:1 after a realistic fill, and nothing is held through earnings. NVDA (11-17 print), MU and SPCX (dark pool against, about 1:1), AMD, LRCX, IONQ fail on that. Miners and quantum (RIOT, IREN, APLD, IONQ) have ATR 8-14% and no edge beyond oversold. Agreement count was not used as a reason: the scorecard shows 4+ legs beat SPY 45% of the time with median excess -0.7%, and 12 of the 16 are one correlated AI/semis/miner bet.

## Lessons from w/e 11/06 applied
- Strong-name breakout entries: none of the kept names is strong; all three are dips at named supports, so no breakout leg was warranted. NVDA's breakout was cut on payoff and earnings.
- T1 must clear a realistic fill: checked per card; TSM's T1 (380 from about 370.5) is the weak one and is flagged.
- Stops are ATR-scaled and off round numbers (343, 357.8, 52.6).
- Largest size justified above; correlated cluster capped.

## Gaps
No XLF or defensive sector ETF is on the board. The sector scan favors them but there are no chart levels for them in the inputs, and I did not invent any. Add them only after levels are pulled. Dark pool lean is inferred; GEX for TSLA was cached at 11-06 21:01Z and includes an expired expiry, so its pin is overstated. Option spreads are post-close; re-check at the open. SPCX instrument type remains unverified. Nothing was posted, sealed, ordered or committed.

## Revisions after review (stop and reward-to-risk fixes)
Original plan saved as plan_1113.pre_fix.json. No target was moved out to pass a check; names that fail at real levels were cut.
- TSLA stop 343 -> 335: old stop was 0.54-0.66 ATR (ATR14 16.71) and inside the 11/05 low of 338.15. New stop is below that low and about 1.1 ATR under the 354 mid.
- TSLA targets 362.5/377.5 -> 385.19/398.5: old ones were mechanical half-steps with T1 at 0.77:1. New T1 is the 11/04 close, T2 the 11/03 close. From a 354 fill risk is 19: T1 1.64:1, T2 2.3:1. At a 356 fill T1 is about 1.4:1, so favour the lower half of the zone. sizeR kept at 0.5.
- TSM kept -> cut: a 1-ATR stop is 351 (below the 351.19 low), risk 19.5; the nearest real level, the 11/04 close 395.75, gives 1.29:1. Fails.
- INTC kept -> cut: a 1-ATR stop is about 49, risk 6.5; real levels 58.27 and 60.55 give 0.43:1 and 0.78:1; only the far 10/30 close 65.76 passes, which would be reaching. Fails.
- Trigger status: TSLA close 358.22 is above the 352-356 zone (0.6% above), so the dip has not fired. INTC (now cut) closed 56.28, 0.28 over its zone, and the 11/06 low 54.56 already traded through it, so it was nearly triggered anyway.
- Totals now: 0.5R across 1 name (was 1.0R across 3). The TSM/INTC correlation cap is moot. Earlier checks (bars, options, no TSLA earnings in the 45-day calendar, TSLA corr under 0.7) still hold; TSM's own report date was never independently confirmed.
- The dry-run validator checks structure only; it does not test ATR stops or reward to risk, so these were checked by hand.
- Superseded text above (the Kept section and the "Lessons" bullets about stops 343/357.8/52.6 and TSM's T1) describes the pre-fix plan.

## Revisions after review (TSLA reward-to-risk across the zone)
Prior file saved as plan_1113.pre_rr_fix.json. T1 (385.19), T2 (398.5), stop (335) and sizeR (0.5) are unchanged; no target was moved.
- TSLA dip zone 352-356 -> 352-355. At a 356 fill, risk 21 vs reward 29.19 to T1 = 1.39:1, below 1.5. At 355: 30.19/20 = 1.51:1 (passes, thin margin); at 352: 33.19/17 = 1.95:1. Every fill inside the new zone clears 1.5 to T1.
- Trigger text updated to "Dip to $352-355 that holds"; the why text's "about 1.4:1 at the 356 top" line replaced with the 355 arithmetic.
- The 11/06 close of 358.22 is 3.22 above the new zone top, so the dip still has not fired. A bounce off 356 will not fill; that is accepted rather than stretching the zone.
- The 1.51 at the top is only just over the bar; a fill at 352-354 is the cleaner entry.
