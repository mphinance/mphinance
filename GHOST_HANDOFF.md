# Ghost Handoff — 2026-03-12

## What Was Built

### Ghost Alpha Intelligence Dashboard
- **Location**: `docs/intelligence/index.html` (live at mphinance.github.io/mphinance/intelligence/)
- **Data**: `docs/api/backtest-analytics.json` (mega analytics, inlined into HTML)
- **Engine**: `scripts/intelligence_crossover.py` (crossover engine + analytics builder)

### Dashboard Sections (15+ interactive charts)
1. Top stats cards (Gold Picks, Score 70+ performance)
2. Gold picks equity curve (+12.13% cumulative, 25 picks)
3. Sam's Optimal Screener (ML feature importance + filter tests)
4. RSI-14 / ADX-14 / Stochastic %K zone performance charts
5. IV Rank / Relative Volume zone analysis
6. EMA stack + curated strategy breakdown
7. Multi-timeframe score band analysis (5D/10D/21D)
8. Screen strategy comparison (1,795 historical picks, 7 strategies)
9. Pullback vs non-pullback multi-timeframe
10. Sector performance (15 sectors)
11. Grade performance cards (B: 71.4% WR, C: 75% WR)
12. Full technical data table (RSI/ADX/Stoch/RVOL/EMA + 1D/5D/10D/21D)
13. Streak analysis

### Key Findings
- **RVOL >= 1.5x**: 85.7% WR, +19.36% avg 5D (strongest single predictor)
- **RVOL 1.5x + Full Bullish EMA**: 100% 1D WR, 80% 5D WR, +23.39% avg
- **RSI 50-70**: 70% WR, +12.71% avg 5D
- **Feature importance** (ML, 99% acc): stoch_val 22.3%, adx_val 19.2%, rel_vol 18.9%, rsi_val 17.8%
- **Score 70+ picks**: 66.3% WR across 196 entries
- **Volatility Squeeze** (curated): 63.5% WR

## What's Next
1. **Build 21D/30D swing analysis** — test which filters work for longer holds vs 5D trades
2. **Wire RVOL into screener scoring** — strongest predictor not fully weighted in score calc
3. **Wire TraderDaddy Agent API auth** — crossover engine ready, needs JWT token
4. **Add intelligence stage to pipeline** — Stage 17 in generate.py for daily auto-refresh
