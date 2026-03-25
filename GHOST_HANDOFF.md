# Ghost Handoff — 2026-03-25

## What Happened This Session

### VoPR Screener Archive (`docs/vopr.html`)
- Added full Screener Archive section with date pills, funnel stats bar, results table
- Supports both legacy format (`strategies.{name}.tickers`) and new format (`funnel_stats` + `results`)
- Fixed stale API fallback URL (was `http://mphinance.com:8002/alpha/api/csp`)

### Landing Page Date Fix (`dossier/generate.py`)
- Root cause: pipeline pushes `landing/data/` to git but landing page lives on Vultr — never rsynced
- Added auto-rsync to Vultr after git push in pipeline
- Manually rsynced to fix immediately

### Dossier Layout Consolidation (`dossier/report/template.html`)
- Merged 3 redundant VIX panels (VIX.REGIME, SECTOR.ROTATION, MARKET.REGIME) → 1 unified panel
- Moved AI.SYNTHESIS after market context
- Added 3 visual group dividers: alpha signals, dev log, deep analysis

### Code Audit Quick Wins
- **fetch_revenue.py**: Fixed 4 unclosed `open()` → `Path.read_text()`. Added try/except to wash sale date parsing.
- **vault_server.py**: Fixed deprecated `datetime.utcnow()`. Added `Depends()` auth. Added startup warning for empty API key. Added request audit logging. Health endpoint validates Firestore. Delete 404s on missing keys.
- **substack_cron.sh**: Fixed stale repo path. Fixed `both` mode calling old Playwright script.

## Key Commits
- `7e00b03` — VoPR archive + landing date fix + dossier layout consolidation
- `d84463c` — Audit quick wins: file handles, VaultGuard auth, cron path, wash sales

## What's Next
1. **Fix N+1 Stripe query** — `expand=['data.balance_transaction']` saves 100+ API calls
2. **Write 5 critical pytest tests** — test plan in `code_audit.md`
3. **Fix store.py `get_stats()` OOM** — paginate ChromaDB metadata instead of loading all
4. **Add ChromaDB backup** — rsync to Venus or GCS after pipeline runs
5. **VMD Substack post** — still queued from last session

## Important Files Changed
- `docs/vopr.html` — Screener archive section
- `dossier/generate.py` — Auto-rsync to Vultr
- `dossier/report/template.html` — Layout consolidation
- `dossier/fetch_revenue.py` — File handle + wash sale fixes
- `vaultguard/vault_server.py` — Auth + logging + health overhaul
- `scripts/substack_cron.sh` — Path + script fixes
