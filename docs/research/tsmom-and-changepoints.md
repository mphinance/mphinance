# TSMOM + changepoints: notes from the CTA-Quant-Papers pass (2026-11-01)

Source list: github.com/jackywong1228/CTA-Quant-Papers (100 PDFs, no code).
Careful with it: its `23_Time_Series_Momentum_Moskowitz2012.pdf` is actually
Curdia/Woodford, *The Central-Bank Balance Sheet* (NBER w16208). The PDF here came
straight from Pedersen's NYU page.

## Moskowitz, Ooi, Pedersen (2012), Time Series Momentum, JFE 104
`time-series-momentum_moskowitz2012.pdf`

- An asset's own past 12-month return predicts its next month's return. They test
  58 liquid futures (equity indexes, FX, commodities, bonds). Returns persist for
  1-12 months, then partially reverse over longer horizons.
- Signal = sign(trailing 12m excess return). Position sized to constant volatility.
- Why it matters here: it's the cheapest honest baseline there is. A screener
  stack that can't beat "own what's up over 12 months" is just adding noise.
- **Wired in:** `score_history.mjs` → `_scorecard.json.tsmomBaseline` +
  `buckets.tsmomUp/tsmomDown`. Long-only and equity-only. 252 trading-day lookback,
  same 5-day hold as the list, no vol scaling (yet).

## Wood, Roberts, Zohren (2021), Slow Momentum with Fast Reversion
`slow-momentum-fast-reversion_wood2021.pdf`, arXiv:2105.13727

- Momentum strategies lose money at turning points, where the trend breaks and the
  slow signal is still pointing the old way.
- Fix: an online changepoint-detection (CPD) module (Gaussian-process based) gives
  each day a changepoint **severity** and **location**. Those feed an LSTM next to
  the momentum features.
- Result they report: adding CPD lifts Sharpe by about one-third over 1995-2020,
  and by about two-thirds over 2015-2020, when plain momentum was struggling.
- Steal the CPD part and skip the LSTM. A severity score for "the regime just
  changed" is exactly what the downtrend-breakout detector needs: lower highs
  from a major peak, then a changepoint at the break. It would also work as a
  veto on CSP entries.

## First baseline read (5-day forward, 1,049 picks / 74 days)

| | avg 5d | vs SPY |
|---|---|---|
| TSMOM basket (363-name universe) | +0.66% | +0.24% |
| stock-recap list | +0.40% | -0.02% |

The list beat the dumb rule on 46% of days. Inside the list, 12m-trend-up and
trend-down picks both hit 51%.
