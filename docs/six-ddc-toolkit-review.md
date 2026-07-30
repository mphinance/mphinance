# six-ddc Toolkit — Verified Review & What We Actually Took

> Follow-up to a Claude **web** session that reviewed `github.com/six-ddc`'s
> repos but flagged that it *couldn't verify* several of them ("the tooling
> kept returning same-named repos by other authors"). This pass was run in
> Claude Code with real web + git access, so the ⚠️ VERIFY flags are now
> resolved. Where the web report was wrong, it's corrected below.
> Reviewed 2026-07-10.

## Verification results — the repos are real

Fetched the actual profile repo list and cloned the two that mattered. All the
previously-unverified repos exist under `six-ddc`:

| Repo | Exists? | License | Note |
|------|---------|---------|------|
| `skills` | ✅ yes | **none (all-rights-reserved)** | 3 skills: `serenity-investor`, `office-hours`, `sub-claude` |
| `codex-dynamic-workflows` | ✅ yes | **MIT** | journal-cache resume runner |
| `browser-cli` | ✅ yes | (not pulled) | parked, as planned |
| `claude-code-resume` | ✅ yes | (not pulled) | demoted — solves a pain we don't have |
| `ccbot` | ✅ yes | — | **correction:** there is no `ccmux` repo; it's `ccbot` |

## Corrections to the web report

1. **`serenity-investor` is NOT "source-agnostic market analysis."** The web
   report pitched it as an options/market workflow overlapping our TDPro
   GEX/flow/screener work. It isn't. It's a **Chinese-language persona clone
   of a specific named investor** (X/Twitter `@aleabitoreddit`, "Serenity"),
   built by distilling ~500 of his tweets into his voice, worldview, and
   position style. Output is *him*, not a neutral analysis. We did **not**
   take it: it's an unlicensed distillation of a named third party's content —
   wrong to republish into a TraderDaddy repo, and not what we wanted anyway.

2. **The licensing warning was right.** `six-ddc/skills` has **no LICENSE
   file** → all-rights-reserved by default. So nothing from that repo can be
   copied into our public repo *without the author's permission*.

3. **`ccmux` doesn't exist as a repo.** The bridge tool is `ccbot`. Still
   redundant with Nyx-on-Discord, so still skipped.

## What we actually implemented

### 1. Vendored the `sub-claude` skill (with permission)

Michael obtained the author's permission for `sub-claude` specifically, so it's
now a first-class loadable skill in this repo:

- `.claude/skills/sub-claude/SKILL.md`
- `.claude/skills/sub-claude/scripts/sub_claude.py`

It fans out `claude -p` workers over CSV/JSONL rows with concurrency control,
checkpoint/resume, cost tracking, retries, and structured output. The natural
fit here is a **basket scan — one worker per ticker**, results collected to a
single rankable file (an example prompt is in the SKILL.md).

**Provenance is recorded in-file** (source repo + commit `ff306e8`, permission
grant, no public re-license). **Safety note also in-file:** each worker runs
`--dangerously-skip-permissions`, so only point it at trusted inputs; use
`-- --tools ""` for pure-text tasks.

> Not vendored: `serenity-investor` (see above) and `office-hours` (not
> relevant to the pipeline).

### 2. Applied the journal-cache resume pattern to the backtest engine

This is the real fix for the recurring **fetch-and-persist** bug. The pattern
(from `codex-dynamic-workflows`, MIT + it's a pattern anyway) is: key every
expensive call by a stable hash of its inputs and persist the result the
instant it succeeds; a re-run reuses completed pulls and only re-fetches the
misses.

`backtesting/vopr_grade_backtest.py` had the exact anti-pattern — `fetch_data()`
downloaded OHLC inside the main loop and **never persisted it**, so any failure
downstream (an eval bug, a bad ticker, a rate-limit halfway through) killed the
run and the next run re-downloaded *everything*.

Changes:
- **`backtesting/fetch_cache.py`** — new, stdlib-only, clean-room. A tiny
  persistent key→object store with atomic writes (crash-safe), an optional TTL
  (day-old bars aren't silently reused by a fresh run), and `cached_fetch_map()`
  which fetches only the misses.
- **`backtesting/vopr_grade_backtest.py`** — `fetch_data()` now reuses cached
  bars; split raw download (`_download_data`) from the cache-backed wrapper.
  Toggle with `MPH_FETCH_CACHE=0`, TTL via `MPH_FETCH_CACHE_TTL`.
- **Portability fix (bonus):** the hardcoded `/home/mph/Antigravity/...` paths
  now fall back to a path relative to the file (or `MPH_BACKTEST_DIR` /
  `MPH_REPORTS_DIR`), so the backtest and its tests run in CI / a fresh clone.
- **`tests/test_fetch_cache.py`** — 9 tests, no network/pandas: hit/miss,
  resume-only-misses, window isolation, TTL expiry, corrupt-entry-is-a-miss,
  atomic write. All green.

Reuse this cache anywhere we fetch-then-process (the Tradier/dossier pulls are
the obvious next candidates).

## Still parked / skipped (unchanged from the plan)

- **`browser-cli`** — park until a concrete authenticated-scraping job
  (auction portal, broker data); read it against Vercel's agent-browser first.
- **`ccbot`** — redundant with Nyx on Discord.
- **`claude-code-resume`** — solves finding old *local* sessions; our serious
  work runs unattended.
- **`livecaption` / `termux-app` / `plow` / `hss` / `sql-builder`** — off-stack.
