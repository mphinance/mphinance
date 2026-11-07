# Candidates for a second look (data as of the Fri 2026-11-06 close)

Market: SPY 735.29, under its 50-day, RSI 35.2, -2.70% on the week. Market Health HIGH (4.5 of 5), VIX/VIX3M inverted at 1.04, credit ETFs under their 50-day. Money left semis and tech and went to financials and defensives.

Neither of the two runs found a screen with a backtested edge over a random pick: the best was +0.23% at 5 days (t 0.79). So none of these names has a validated screen behind it. The question is whether any of them is a reasonable discretionary trade anyway, and at what size.

## TSLA (run A, posted to the forum, unsealed)
- Close 358.22. Plan: dip to $352-355 that holds (daily close back at or above $352), stop $335, targets $385.19 (11/4 close, on the 200-day) and $398.50 (11/3 close, 0.5 retrace). 0.5R. Expires 12/4.
- The stop and targets were moved after the first plan failed a reward-to-risk test (first plan: zone 352-356, stop 343, targets 362.50/377.50).
- Signals that flagged it: the cc-wheel screener, 2 bullish flow alerts ($6.2M), net +$3.68M of XLY-sector flow. Thin.
- Readings: RSI 42.4, ADX 16.8 with -DI leading, under all nine moving averages (50-day 372.14, 200-day 383.87), failed breakout at 414 on 11/2, low 338.15 on 11/5. Positive gamma, flip about 344 to 347, put walls 355 and 350, call walls 362.50 to 380. IV rank 62.6. Dark pool -$600M net over 5 days. Annual meeting 12/3 inside the hold.
- Full due diligence: /home/mph/mphinance/data/dd/TSLA/2026-11-07.json and .md

## HUM, PCVX, FNF (run B, only with the reward-to-risk gate lowered from 1.5 to 1.0; run B's own board is empty)
All three came from screen families that failed run B's backtest. Each was 0.25R.

| ticker | mode | trigger | stop | T1 | R to T1 | RSI | 20d | 60d | above 200d | own replay: n, T1 first, stopped | families |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HUM | pullback | 414.93 | 399.35 | 433.21 | 1.17 | 61.4 | +0.6% | +12.9% | yes | 23, 3, 1 | base-breakout, rs-flow |
| PCVX | breakout | 65.88 | 59.19 | 72.89 | 1.05 | 52.5 | -10.5% | +8.5% | yes | 19, 3, 0 | pullback-recovery, rs-flow |
| FNF | pullback | 41.24 | 38.46 | 44.11 | 1.03 | 64.5 | +13.0% | -9.4% | no | 15, 0, 2 | pullback-recovery, rs-flow |

Run B's own notes: HUM's T1 (433.21) is about today's price (433.74), so the entry needs a 4.5% dip to reach a target below spot. FNF is an extended bounce inside a downtrend. Every R to T1 is about 1:1 before costs.
