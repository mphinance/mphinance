# GHOST_HANDOFF — Last Updated 2026-03-12

## What Just Shipped

### Pine Script v5 "Clean Edition"
- 885→809 lines, emoji signals→text labels, 14→10 dashboard rows
- EMA 21 warm gold ON by default, Hull/TRAMA visual speed hierarchy
- Momentum zone fill (EMA 8-55 gradient) toggleable
- Landing page `/ghost-alpha/` rewritten, deployed to Vultr

### Wheel Scanner → Dossier Pipeline
- `generate.py` Stage 7 reads `momentum-phund-tasty/watchlist.json` (runs 4:30 AM)
- Falls back to built-in CSP scanner if file missing/stale
- CSP picks grouped by capital tier: Micro/Small/Medium/Large (max 2/tier)

### Substack Strategy + RAG
- Analyzed 85 posts: stories=65% open rate, dossier=50%
- BUT: unique data wrapped in story is the real winner (Confessions=71%)
- `docs/SUBSTACK_ANALYSIS.md` saved for RAG ingestion
- `KNOWLEDGE_BASE` doc type added — `chunk_knowledge_base()` ingests `docs/*.md`

### Smart Draft Generator
- `scripts/build_latest_draft.py` — auto-populates `docs/substack/latest.md`
- Reads ghost blog entries + git commits since last publish
- Never overwrites Michael's content (append only)
- Frontmatter: `status: draft/published`, `author: sam/michael`
- Michael edits in GitHub browser when he posts to Substack

## What's Next
1. **Michael reschedules momentum-phund-tasty cron to 4:30 AM CST**
2. **Test wheel scanner → dossier pipeline end-to-end tomorrow morning**
3. **Paste Pine Script v5 into TradingView and verify compilation**
4. **Publish backtest data on Substack** — 754 entries, unique AI screener WR data
5. **Wire `build_latest_draft.py` into the pipeline** so draft auto-refreshes

## Key Files Changed
- `dossier/generate.py` — Stage 7 wheel scanner integration
- `dossier/daily_setups.py` — Capital tier bucketing
- `rag/config.py` — KNOWLEDGE_BASE doc type
- `rag/chunker.py` — chunk_knowledge_base() function
- `rag/ingest.py` — knowledge_base in chunker mapping
- `scripts/build_latest_draft.py` — NEW draft generator
- `docs/SUBSTACK_ANALYSIS.md` — NEW engagement analysis
- `docs/substack/latest.md` — Full session notes since March 10
- `docs/pine/ghost_alpha.pine` — v5 Clean Edition
- `landing/ghost-alpha/index.html` — Rewritten landing page
