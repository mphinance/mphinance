# Watchlist Deep Dive — How It Works

A standalone recipe for the "edit `watchlist.txt`, get a published deep-dive
report in ~60 seconds" workflow that runs on GitHub Actions and deploys to
GitHub Pages.

## The 30-second pitch

1. You edit `watchlist.txt` and push to `main`.
2. A GitHub Actions workflow wakes up, pulls quote/fundamentals/options data
   from `yfinance`, computes a battery of technicals, asks Gemini to write a
   narrative deep-dive, and renders three artifacts per ticker:
   `deep_dive.md`, `deep_dive.json`, `deep_dive.html`.
3. Artifacts land under `docs/ticker/{TICKER}/`, the index page is
   regenerated, everything is committed back to `main` by a bot user, and
   the `docs/` tree is published to GitHub Pages.

That's the whole loop. Two files do the work: the workflow YAML and the
Python module it invokes.

## Repo layout you need

```
.
├── .github/workflows/watchlist_dive.yml      # the trigger + CI steps
├── dossier/
│   ├── watchlist_dive.py                     # main entry point
│   ├── config.py                             # reads GEMINI_API_KEY, AI_MODEL
│   ├── data_sources/ticker_enrichment.py     # shared TA helpers
│   └── generate.py                           # _update_index_page() helper
├── docs/                                     # GH Pages root
│   └── ticker/{TICKER}/                      # output lands here
└── watchlist.txt                             # one ticker per line, `#` comments
```

## The trigger (`.github/workflows/watchlist_dive.yml`)

Three things make this workflow tick:

- **Path-filtered push trigger.** Only fires when `watchlist.txt` itself
  changes on `main`. Code changes to the rest of the repo don't re-run
  reports unnecessarily.
- **`workflow_dispatch` with a `tickers` input.** Lets you manually
  re-generate one or many symbols from the Actions tab without touching
  `watchlist.txt`.
- **Pages deploy environment.** The job runs under
  `environment: github-pages` with `pages: write` and `id-token: write`
  permissions so it can publish the result.

Skeleton:

```yaml
name: Watchlist Deep Dive
on:
  push:
    branches: [main]
    paths: ['watchlist.txt']
  workflow_dispatch:
    inputs:
      tickers:
        description: 'Space-separated tickers (blank → use watchlist.txt)'
        required: false
        default: ''

permissions:
  contents: write
  pages: write
  id-token: write

jobs:
  generate:
    environment: { name: github-pages, url: ${{ steps.deployment.outputs.page_url }} }
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with: { python-version: '3.12' }

      - name: Install dependencies
        run: pip install yfinance pandas numpy httpx feedparser jinja2 tradingview-ta google-genai python-dotenv

      - name: Generate deep dives
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PYTHONPATH: ${{ github.workspace }}
        run: |
          if [ -n "${{ github.event.inputs.tickers }}" ]; then
            python -m dossier.watchlist_dive ${{ github.event.inputs.tickers }}
          else
            python -m dossier.watchlist_dive
          fi

      - name: Regenerate index page
        env: { PYTHONPATH: ${{ github.workspace }} }
        run: python -c "from dossier.generate import _update_index_page; _update_index_page()"

      - name: Commit and push
        run: |
          git config user.name "ghost-bot"
          git config user.email "ghost@example.com"
          git add docs/
          git diff --cached --quiet || git commit -m "Watchlist deep dives updated"
          git pull --rebase || true
          git push

      - uses: actions/configure-pages@v6
      - uses: actions/upload-pages-artifact@v5
        with: { path: 'docs' }
      - id: deployment
        uses: actions/deploy-pages@v5
```

### Required setup on the GitHub side

- **Repository secret** `GEMINI_API_KEY` (Settings → Secrets and variables → Actions).
  Without it the script falls back to a plain-template report instead of the
  AI narrative — it does not crash.
- **GitHub Pages enabled** with source set to "GitHub Actions" (Settings → Pages).
- **Workflow write permissions** (Settings → Actions → General → Workflow
  permissions → "Read and write"). The bot needs to push the regenerated
  `docs/` back to `main`.

## The script (`dossier/watchlist_dive.py`)

One module, one entry point. CLI:

```
python -m dossier.watchlist_dive              # process every ticker in watchlist.txt
python -m dossier.watchlist_dive PLTR NVDA    # process specific symbols
```

### What it does per ticker

1. **Read watchlist** — `_read_watchlist()` parses `watchlist.txt`, skipping
   blanks and `#` comments, dedupes while preserving order.
2. **Fetch market data** via `yfinance`:
   - `Ticker.history(period="6mo")` for OHLCV.
   - `Ticker.info` for fundamentals (P/E, margins, growth, analyst targets,
     dividends, company profile, …).
   - `Ticker.options[0]` + `option_chain(...)` for an ATM IV estimate plus
     IV rank/percentile across the chain.
3. **Compute technicals** locally (no external TA library required — the
   helpers in `dossier/data_sources/ticker_enrichment.py` plus inline math):
   - SMAs (20/50/100/200), EMAs (8/21/34/55/89) and an "EMA stack" label
     (`FULL BULLISH` / `PARTIAL BULLISH` / `FULL BEARISH` / `TANGLED`).
   - RSI(14), Stochastic %K/%D, MACD line/signal/histogram, ADX(14), ATR(14/20).
   - Classic floor-trader pivots (R2/R1/PP/S1/S2).
   - 52-week range + position percent, Fibonacci retracements, Keltner channels.
   - 30-day historical volatility from log returns.
   - Relative volume vs 20-day average.
4. **Valuation + sentiment add-ons**:
   - `_intrinsic_value(info, price)` for a status/gap/target triple.
   - `_tradingview_summary(ticker, exchange)` (via `tradingview-ta`) for a
     `BUY/SELL/HOLD`-style recommendation string.
   - Composite 0–100 **Value / Growth / Quality / Sentiment** scores
     derived from `info` fields (clamped, missing inputs → `None`).
5. **Optional VoPR scanner integration** — if a sibling `VoPR/` repo is
   present at `../VoPR/` it adds VRP ratio, ATM IV, expected move, and the
   top option strikes to the report. Missing dir → silently skipped.
6. **Ask Gemini for the narrative** (`_gemini_deep_dive`). The prompt
   pins a strict markdown structure (Thesis → Numbers → Bull → Bear →
   Technicals → Playbook → Verdict) and feeds the full computed dataset
   as plain text. Model name comes from `dossier.config.AI_MODEL`. If
   `GEMINI_API_KEY` is unset or the call fails, the script falls back to
   a deterministic markdown template with the raw numbers.
7. **Write three artifacts** under `docs/ticker/{TICKER}/`:
   - `deep_dive.md` — the narrative (Gemini-authored or fallback template).
   - `deep_dive.json` — the full computed dataset, for downstream
     dashboards / API consumers.
   - `deep_dive.html` — a styled page that embeds the markdown body
     (regex-converted to HTML inline — no `markdown` library needed) and
     wraps it in a "Technical Gearbox" + "Fundamental Dashboard" of
     cards. The CSS is inlined; no JS framework required.

After the per-ticker loop, the workflow calls
`dossier.generate._update_index_page()` to refresh `docs/index.html` so the
new ticker shows up in the listing.

## Dependencies

Pinned in the workflow's `pip install` step, no `requirements.txt` needed
for this job in isolation:

```
yfinance pandas numpy httpx feedparser jinja2 tradingview-ta google-genai python-dotenv
```

Notes:
- `google-genai` is the official Gemini SDK; swap for OpenAI/Anthropic by
  rewriting `_gemini_deep_dive` only — the rest of the pipeline is
  provider-agnostic.
- `feedparser` and `httpx` are used by the shared `_fetch_news` helper in
  `ticker_enrichment.py`; harmless to leave in even if you strip news.
- `tradingview-ta` is optional — wrap the `_tradingview_summary` call in
  try/except and tolerate `N/A` if you'd rather not include it.

## Recreating it from scratch — minimum viable steps

1. Create a repo with `docs/` at the root and enable GitHub Pages (source:
   GitHub Actions).
2. Add `watchlist.txt` with one ticker per line.
3. Drop in the workflow YAML above.
4. Port `dossier/watchlist_dive.py` and the two helpers it imports
   (`dossier.config`, `dossier.data_sources.ticker_enrichment`). The
   `config` module only needs to export `GEMINI_API_KEY` (from env) and
   `AI_MODEL` (e.g. `"gemini-2.5-flash"`).
5. Add a `_update_index_page()` in `dossier/generate.py` that scans
   `docs/ticker/*/deep_dive.html` and writes a linked index — or skip
   that step entirely and serve a static `docs/index.html`.
6. Push `GEMINI_API_KEY` into repo secrets.
7. Edit `watchlist.txt`, commit, push. Watch the Action run, then visit
   `https://<user>.github.io/<repo>/ticker/<TICKER>/deep_dive.html`.

## Gotchas worth knowing up front

- **`yfinance` is unofficial and rate-limited.** Batch runs of 50+ tickers
  can throttle; the script processes them sequentially and tolerates
  `[SKIP]` / `[ERR]` per ticker without aborting.
- **The commit step uses `git pull --rebase || true` then `git push`.**
  That handles concurrent edits to `main` during the run but won't survive
  a hard conflict — keep the workflow's writes scoped to `docs/`.
- **Reports are persistent.** Once a ticker's folder exists under
  `docs/ticker/{TICKER}/`, removing the symbol from `watchlist.txt` won't
  delete its report. The header comment in `watchlist.txt` calls this
  out explicitly — don't `.gitignore` the output dir.
- **HTML rendering is a regex-based markdown shim**, not a real parser.
  It handles headings, bold/italic, lists, tables, hr — that's it. If the
  Gemini output starts using code fences or footnotes, extend `_render_html`.
- **Branding strings** (`ghost-bot`, "Ghost Alpha Dossier", the affiliate
  banner in `_render_html`) are easy to find and swap. Search for `Ghost`
  and the TraderDaddy link in `watchlist_dive.py`.
