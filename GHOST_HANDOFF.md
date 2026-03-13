# Ghost Handoff — 2026-03-13

## What Happened This Session

### VoPR CSP Pipeline — Fixed from Dead Code to Working Pipeline
- **Problem**: `csp_setups.py` imported `strategies.cash_secured_puts` and `strategies.vopr_overlay` — NEITHER FILE EXISTED. The CSP pipeline was failing silently on every 5AM run.
- **Root cause**: `strategies/__init__.py` registered "Cash Secured Puts" strategy but the actual `.py` file was never written. Same for `vopr_overlay.py`.
- The `strategies/` directory WAS synced from Venus (Syncthing working) — it was just missing these two specific files.

**Created `strategies/cash_secured_puts.py`**:
- Stage 1: TradingView scan with EMA 21>34>55, Golden Cross, ADX≥20, RSI 30-70
- Stage 2: ATR proximity filter (not overextended)
- Stage 3: Options chain deep dive — OTM puts, 7-45 DTE, weekly ROC calculation

**Created `strategies/vopr_overlay.py`**:
- 4-model composite realized vol (CC, Parkinson, Garman-Klass, Rogers-Satchell)
- VRP ratio = IV / Composite_RV (the core quality signal)
- Vol regime classification (LOW/FALLING/RISING/HIGH)
- Black-Scholes put delta + daily theta
- Grading: A (VRP≥1.3 + calm vol), B (VRP≥1.2), C (VRP≥1.0), F (VRP<1.0)

**Updated `docs/vopr.html`**:
- Grade quality gate: only A/B shown by default
- Toggle checkbox to reveal C/F grades
- Explanatory message when no A/B setups exist ("VoPR says premium is cheap")

### Backtest Evidence (from earlier in conversation)
- 9 CSPs from March 5 snapshot — ALL Grade F, VRP < 1.0
- 100% expired worthless (lucky) but 3/9 breached strike intraday
- **0/9 would have passed the new momentum+VRP filters** — validation complete

### Intelligence Page Enhancements
- Navigation breadcrumbs (Home/Dossier/VoPR/Intelligence/Blog)
- "Last Updated" timestamp from enriched picks
- Weekly performance heatmap chart (data existed, had no renderer)
- VoPR CSP pipeline status section with backtest evidence
- Filtered numeric garbage sector IDs from charts

## Key Commits
- `1eb6af5` → `02e7ffb` — VoPR CSP pipeline: new strategy + overlay + grade gate
- `04b31ca` — Intelligence page: weekly heatmap, VoPR section, nav, sector fix

## What's Next
1. **Run the CSP pipeline live** — tomorrow's 5AM run will be the first real test
2. **Continue intelligence page** — more interactive features, live data integration
3. **Codemap** — generate full repository map for mphinance

## Important Files
- `strategies/cash_secured_puts.py` — [NEW] Momentum-filtered CSP strategy
- `strategies/vopr_overlay.py` — [NEW] VoPR enrichment engine (4-model RV + VRP + grading)
- `docs/vopr.html` — Grade filter added (A/B only by default)
- `docs/intelligence/index.html` — Nav + weekly heatmap + VoPR section
- `strategies/__init__.py` — Already had CSP registered, now has the backing file
