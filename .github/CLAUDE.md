# Project Guide for Claude (GitHub App)

This is the focused brief for the **Claude GitHub App** when it answers `@claude`
mentions and reviews pull requests. It is loaded by the workflows in
`.github/workflows/claude*.yml` via `--append-system-prompt`.

> The root `CLAUDE.md` redirects to `AGENTS.md`, which is the full operator
> manual for the local "Sam" agent (logging rituals, deploy SSH, persona, etc.).
> **Do not follow those rituals here.** A PR-review or issue bot should not write
> ghost blog entries, touch `landing/blog/blog_entries.json`, or update
> `GHOST_HANDOFF.md`. Read `AGENTS.md` only when you need architecture or
> credential context to answer a question.

## What this repo is

`mphinance` is an AI-assisted quantitative trading + publishing platform:

- **`dossier/`** — a multi-stage Python pipeline (data fetch → momentum scoring →
  AI-written reports → charts) that runs weekday mornings via GitHub Actions and
  publishes to GitHub Pages (`docs/`).
- **`substack_social/`** — TypeScript/Node engagement + read-digest automation
  on top of a vendored `substack-api` fork (`vendor/substack-api/`). Run with
  `ts-node` (e.g. `npm run engage`, `npm run pulse`).
- **`landing/`** — static site (blog, landing page, ebook checkout) rsynced to a
  Vultr VPS.
- **`scripts/`** — one-off utilities (scrapers, infographic + Substack draft
  generators, backtests).
- **`algo/`, `vaultguard/`** — the live trading algo and the Firebase-backed
  secret vault (these run on a separate host; treat as read-mostly here).

**Stack:** Python 3.12 (pandas, numpy, yfinance, plotly, google-genai) and
Node/TypeScript (ts-node). Deps live in `requirements.txt` files and
`substack_social/package.json` — there is **no** `pyproject.toml`.

## Conventions

- Match the surrounding code style; do not reformat or re-wrap unrelated lines.
- Keep functions small and named clearly (`verb_noun()` in Python; private helpers
  prefixed with `_`). Comments explain *why*, not *what*.
- **Never commit secrets, API keys, or credentials.** Secrets come from GitHub
  Actions secrets (in CI) or VaultGuard / local `.env` (which `.gitignore` blocks).
  If something needs a new secret, say so in a comment instead of hardcoding it.
- There is **no formal test suite** (no pytest/jest). Don't claim tests pass when
  none exist. For a behavior change, either add a minimal check/script or state
  plainly how you validated it (ran the stage, diffed the JSON output, etc.).
- Commit messages use short, emoji-prefixed summaries (e.g. `fix(...)`, `feat(...)`,
  `👻` for the automated ghost log). Match that when you commit.
- **Substack / prose content:** no em dashes and no markdown tables (they render as
  garbage on Substack) — use commas/periods/colons and image-rendered tables.
  Sign-off in posts is `— Michael` only.

## When reviewing PRs

- Lead with **correctness bugs, security risks, and broken edge cases.** Those are
  the only things worth blocking on.
- Watch the things that have actually bitten this repo: silent network/API failures
  (probes that swallow errors), Windows-vs-Linux path issues, the `static` mount in
  `main.py` having to stay **last** so routes aren't shadowed, and Tradier returning
  the string `"null"` (not JSON null) for empty positions.
- Note missing validation on data that comes from external APIs.
- Flag when a change has no validation story at all (see the testing note above).
- Skip pure style/nitpick comments unless they cause a real problem.

## When implementing from an issue

- **Read the existing code first** and reuse the patterns already there before
  writing anything new.
- Scope tightly to what the issue asks. Don't add unrequested features.
- If the task is ambiguous or risky — deletes data, changes a schema or output
  format other stages depend on, bumps a major dependency, or rewrites a workflow —
  **comment with a plan and wait** instead of committing.
- **Do not delete** generated/expensive artifacts: `docs/ticker/*/deep_dive.*` and
  other `docs/` outputs are AI-generated and costly to rebuild.
- Note for Windows clones: a ticker directory named `CON` is a reserved device name
  and cannot exist on Windows. Avoid introducing more reserved-name paths
  (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).

## Ideas / backlog Claude can pick from

Standing improvements that are welcome (see `TODO.md` for the authoritative list):

- Wire `auto_backtest.py` in as a stage of the daily dossier pipeline.
- Integrate `scripts/tao_screener.py` into the main dossier output.
- Add input validation around external API responses in the dossier data-fetch
  stages (the most common source of silent breakage).
- Introduce a minimal test scaffold (`tests/` + a CI job) so behavior changes have
  somewhere to land — start with the momentum-scoring and parsing helpers.
- Increase resilience of the Substack engagement scripts in `substack_social/`
  (retries, clearer failures) on top of the vendored fork.
