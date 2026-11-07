# Quant lens, data as of 2026-11-06 close

Method: yfinance, auto_adjust=False, 5y daily. ATR14 Wilder, taken at the signal bar (no lookahead). Stop and T1 expressed in ATR multiples of today's plan, applied to each historical entry. Outcome window 20 sessions after entry; if stop and T1 are both inside one bar the stop counts first. 'Neither' is marked to the day 20 close in R. Unit R = stop distance. Entry rules: TSLA dip to 0.3-1.0 ATR under prior close, close at or above zone low, close under 50-day, enter at that close; HUM/FNF pullback limit at the plan's ATR distance below prior close (fill at limit, or open if gapped lower); PCVX close above prior 20-day closing high, enter at that close. TSLA plan entry taken as zone midpoint 353.5. Plan size multiplies R. T2 for TSLA not tested. Script: quant.py in this folder.

## TSLA
Plan entry 353.5, stop 335.0, T1 385.19; today's close 358.22, ATR14 16.71. Stop = 1.11 ATR, T1 = 1.90 ATR from entry; plan T1 R = 1.71; plan size 0.5R. Bars: 1255 (2021-11-08 to 2026-11-06).
Signals fired (all bars): 314. Setup, all signals (overlapping, clustered): n=314, T1 first 128 (41%), stop first 183 (58%), neither 3 (1%), mean R/trade +0.124 (se 0.075), at plan size +0.062
Setup, non-overlapping (one trade per 20 sessions): n=39, T1 first 17 (44%), stop first 21 (54%), neither 1 (3%), mean R/trade +0.223 (se 0.216), at plan size +0.111
Random-day baseline (every day, entered at close): n=1193, T1 first 443 (37%), stop first 739 (62%), neither 11 (1%), mean R/trade +0.021 (se 0.038), at plan size +0.011
Baseline, every 20th day (independent): n=59, T1 first 20 (34%), stop first 38 (64%), neither 1 (2%), mean R/trade -0.047 (se 0.169), at plan size -0.024
Setup minus baseline (non-overlap setup vs all-day baseline): +0.202 R, approx t 0.93 on setup n=39

## HUM
Plan entry 414.93, stop 399.35, T1 433.21; today's close 433.74, ATR14 17.22. Stop = 0.90 ATR, T1 = 1.06 ATR from entry; plan T1 R = 1.17; plan size 0.25R. Bars: 1255 (2021-11-08 to 2026-11-06).
Signals fired (all bars): 112. Setup, all signals (overlapping, clustered): n=112, T1 first 51 (46%), stop first 61 (54%), neither 0 (0%), mean R/trade -0.010 (se 0.103), at plan size -0.003
Setup, non-overlapping (one trade per 20 sessions): n=42, T1 first 18 (43%), stop first 24 (57%), neither 0 (0%), mean R/trade -0.069 (se 0.168), at plan size -0.017
Random-day baseline (every day, entered at close): n=1194, T1 first 574 (48%), stop first 620 (52%), neither 0 (0%), mean R/trade +0.045 (se 0.031), at plan size +0.011
Baseline, every 20th day (independent): n=59, T1 first 29 (49%), stop first 30 (51%), neither 0 (0%), mean R/trade +0.068 (se 0.143), at plan size +0.017
Setup minus baseline (non-overlap setup vs all-day baseline): -0.113 R, approx t -0.67 on setup n=42

## PCVX
Plan entry 65.88, stop 59.19, T1 72.89; today's close 63.89, ATR14 3.61. Stop = 1.85 ATR, T1 = 1.94 ATR from entry; plan T1 R = 1.05; plan size 0.25R. Bars: 1255 (2021-11-08 to 2026-11-06).
Signals fired (all bars): 160. Setup, all signals (overlapping, clustered): n=160, T1 first 64 (40%), stop first 71 (44%), neither 25 (16%), mean R/trade +0.001 (se 0.076), at plan size +0.000
Setup, non-overlapping (one trade per 20 sessions): n=35, T1 first 14 (40%), stop first 17 (49%), neither 4 (11%), mean R/trade -0.038 (se 0.167), at plan size -0.009
Random-day baseline (every day, entered at close): n=1176, T1 first 532 (45%), stop first 460 (39%), neither 184 (16%), mean R/trade +0.094 (se 0.028), at plan size +0.023
Baseline, every 20th day (independent): n=59, T1 first 26 (44%), stop first 23 (39%), neither 10 (17%), mean R/trade +0.072 (se 0.124), at plan size +0.018
Setup minus baseline (non-overlap setup vs all-day baseline): -0.132 R, approx t -0.79 on setup n=35

## FNF
Plan entry 41.24, stop 38.46, T1 44.11; today's close 43.84, ATR14 1.38. Stop = 2.01 ATR, T1 = 2.08 ATR from entry; plan T1 R = 1.03; plan size 0.25R. Bars: 1255 (2021-11-08 to 2026-11-06).
Signals fired (all bars): 28. Setup, all signals (overlapping, clustered): n=28, T1 first 12 (43%), stop first 15 (54%), neither 1 (4%), mean R/trade -0.096 (se 0.191), at plan size -0.024
Setup, non-overlapping (one trade per 20 sessions): n=20, T1 first 8 (40%), stop first 12 (60%), neither 0 (0%), mean R/trade -0.187 (se 0.228), at plan size -0.047
Random-day baseline (every day, entered at close): n=1194, T1 first 568 (48%), stop first 511 (43%), neither 115 (10%), mean R/trade +0.080 (se 0.028), at plan size +0.020
Baseline, every 20th day (independent): n=59, T1 first 29 (49%), stop first 26 (44%), neither 4 (7%), mean R/trade +0.080 (se 0.130), at plan size +0.020
Setup minus baseline (non-overlap setup vs all-day baseline): -0.267 R, approx t -1.17 on setup n=20

## Pairwise correlation of daily returns, last 126 sessions (n=126, ending 2026-11-06)

```
      TSLA   HUM  PCVX   FNF   SPY   QQQ
TSLA  1.00  0.10  0.18 -0.04  0.66  0.69
HUM   0.10  1.00  0.23 -0.07  0.18  0.14
PCVX  0.18  0.23  1.00 -0.03  0.28  0.23
FNF  -0.04 -0.07 -0.03  1.00  0.06 -0.16
SPY   0.66  0.18  0.28  0.06  1.00  0.92
QQQ   0.69  0.14  0.23 -0.16  0.92  1.00
```
