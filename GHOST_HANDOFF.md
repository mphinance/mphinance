# Ghost Handoff — 2026-03-23

## What Happened This Session

### Pipeline Fixes (P0/P1)
- Fixed `ghost_daily.yml` — missing `generate_track_record` call, wrong picks path
- Fixed `track_record.py` — missing `generate_track_record()` function
- Fixed `ghost_alpha_screener.py` — missing `scan_logger` import
- Fixed `screens_backtest.py` — wrong import path for `ticker_enrichment`
- Fixed `csp_setups.py` — wrong import path for `cash_secured_puts`
- Fixed `intelligence/index.html` — broken JSON loading for track record widget

### Blog Quality Gate
- Purged 19 hollow "brain is offline" blog entries from `blog_entries.json`
- Added quality gate to `ghost_daily.yml` so templated/failed entries never get committed again

### Landing Page Updates
- Added 6 new product cards: AMU, Substack, Ghost Alpha, TraderDaddy Pro, TickerTrace, PowerClaw
- Updated stats: 7 products, 28 subs, 5 repos

### Revenue Transparency Restored
- Rebuilt `fetch_revenue.py` with full Stripe + TastyTrade OAuth integration
- TastyTrade: `Bearer` token auth, account 5WI21242, live positions/premiums
- Fixed BITF showing different P&L in different places (closed position tracking)
- Picked up ASM→BTG trade, DDD premium increase
- NLV: $962.99, Total Premium: $88.18

### PowerClaw Dashboard Improvements (powerclaw.mphinance.com)
- **Pure black theme** — replaced navy (#06060f, #0c0c1a, #111128) with OLED black (#000, #0a0a0a, #0d0d0d)
- **MCP config** → SSE endpoint at `sam.mphinance.com/mcp/mcp`
- **New `/api/brokerage` endpoint** — serves TastyTrade positions from unified `revenue_stats.json`
- **Brokerage panel** — "📈 Trade" nav tab with NLV, premium, positions, wheel status
- Symlinked `brokerage.json` → mphinance `revenue_stats.json` (single source of truth)

### 🆕 VMD Time Series Decomposition
- New enrichment module: `dossier/data_sources/vmd_enrichment.py`
- Decomposes price into trend/swing/noise modes via Variational Mode Decomposition
- Derives: regime, denoised momentum, noise ratio, swing position, 3-day forecast
- Wired as Stage 8b in dossier pipeline (after ticker enrichment, before market regime)
- Tested: SPY transitioning/bearish, NVDA mean-reverting, RR overbought swing

## ✍️ Content Ideas — WRITE ABOUT THIS

### VMD for Trading — Substack Post
**Source article:** https://substack.com/inbox/post/190412761
"Variational Mode Decomposition - An Elegant Tool for Time Series" by Sofien Kaabar, CFA (Engineering Alpha)

**What it does for us:**
- Separates price into pure trend, swing, and noise — like an equalizer for candlesticks
- Our `vmd_enrichment.py` already uses it! Regime detection, denoised momentum, swing extremes
- Better than EMAs because VMD adapts locally and doesn't lag
- Better than Fourier because it learns the decomposition instead of using fixed sine waves
- Python library: `vmdpy` — 6KB, zero drama

**Angles for the post:**
1. "I gave my AI a musical equalizer for stock prices" — show the 3-mode decomposition
2. Compare VMD momentum vs raw RSI — VMD filters out noise RSI can't
3. Show regime detection in action: SPY transitioning vs DDD mean-reverting
4. The overbought/oversold swing detection is basically a better Stochastic

## Key Commits
- `160bddb` — P0+P1 pipeline fixes
- `0dce63c` — Landing page: 6 new product cards
- `603eb34` — Pipeline health alerting + ghost blog
- `48f6504` — Purge hollow blog entries + quality gate
- `6745de6` — Revenue refresh: TastyTrade live
- `d034e88` — Track closed positions with premium
- `de436f3` — Fix BITF P&L consistency + new trades
- `5b0609d` — VMD Time Series Decomposition
- `fdc23d8` — Add vmdpy to requirements

## What's Next
1. **Run tomorrow's 5AM pipeline** — VMD enrichment will fire for the first time in production
2. **VMD Substack post** — write it up using the angles above
3. **Relay bank export** — when Michael has it, update allocation actuals in revenue_stats.json
4. **PowerClaw dashboard** — the data is there, panels could use more real-time updates

## Important Files
- `dossier/data_sources/vmd_enrichment.py` — [NEW] VMD enrichment module
- `dossier/generate.py` — Stage 8b VMD integration added
- `dossier/fetch_revenue.py` — [REBUILT] Full Stripe+TastyTrade+allocation
- `landing/data/revenue_stats.json` — Live revenue data
- `landing/blog/blog_entries.json` — Cleaned (19 hollow entries purged)
