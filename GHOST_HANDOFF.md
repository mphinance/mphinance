# GHOST HANDOFF — 2026-03-12 Morning

## What Just Shipped (This Session)

### Scoring Overhaul (backtest-driven)
- **ADX scoring INVERTED** — fresh trend (<25) now gets max 18pts, exhaustion (>50) gets -5 PENALTY
  - Backtest: ADX<25 = 100% WR at 5d. ADX>40 = 25% WR. Was giving max points to exhaustion.
- **RVOL boosted** to 20pt max (was 15) — strongest single predictor (6.82R spread)
  - >3x = 20pts, >2x = 18pts, >1.5x = 14pts, <0.7x = -3 PENALTY
- Files: `dossier/momentum_picks.py`

### Finviz Screens Disabled
- All 5 screens showed 23-30% WR with negative returns at every horizon
- Commented out in `dossier/generate.py` Stage 2a
- File retained at `strategies/finviz_screens.py` for reference

### Backtest Analysis (1,972 entries, Feb-Mar 2026)
- Ran every indicator, combo, and categorical split across 1d/3d/5d/10d/21d
- Key findings: RVOL is king (6.82R spread), ADX<25 is holy grail, Grade A is worst performer
- Sector: Utilities/Mining/Energy outperform. Finance/Tech Services underperform.
- Date analysis: 19-73% WR swings based on market conditions alone

### Roadmap/Suggestions Fallback Updated
- `dossier/report/ghost_suggestions.py` — stale defaults replaced with current priorities

## What's Next (Priority Order)
1. **VIX/VVIX regime gating** — date analysis shows market conditions dominate indicator signals
2. **Add MFI, CCI, ATR to scan archive** — for R-multiple analysis and volume-weighted RSI
3. **Screen health scoring** — rolling WR tracker per screen with degradation alerts
4. **Gamma → pin level enrichment** — cross-reference gamma data for picks
5. **Dossier as PWA** (Michael requested)
6. **Cache candle data for API/sharing** (Michael requested)
7. **Fix TradingView link** on landing page (couldn't reproduce — may be cached/stale)
