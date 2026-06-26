# Track Record Builder

A free, single-file performance dashboard for options/futures writers who publish
trades but have no cumulative track record.

Built as a gift for **Ryan LePiane** ([LP Options Academy](https://ryanlepiane.substack.com))
and as a portfolio case study for the **Automation Architect** service from
[Michael / Momentum Phinance](https://momentumphinance.substack.com).

---

## The clog

Ryan publishes a detailed **Weekly Recap** every week: every trade gets a ticker,
a strategy (short put, call diagonal, short strangle, futures spread...), the
debit/credit, max profit/loss, breakeven, buying-power usage, and a single weekly
**Closed Profit/(Loss)** total.

The data is all there. It is just **trapped** in prose and broker screenshots,
one week at a time. A reader cannot answer the questions that actually build trust:

- What is the cumulative realized P/L? Is the equity curve smooth or lumpy?
- What is the real win rate and profit factor?
- **Which strategies actually make the money** and which bleed it?

There is no running scoreboard. Every week starts from zero.

## The approach: one CSV in, one dashboard out

Everything funnels through one generic CSV schema and one command:

```
trades.csv   ->   python build.py   ->   dashboard.html
```

The dashboard regenerates every run: KPIs, equity curve, per-strategy breakdown,
a sortable trades table, and an open-positions list. No server, no build step,
no database. Open `dashboard.html` in any browser, or screenshot it straight into
a Substack post. **Build once, works for any options writer.**

There are two ways to fill that CSV:

1. **Keep a sheet by hand** — the durable input Ryan owns
   (`data/trades_template.csv`). Add a row when you close a trade.
2. **`tt_ocr.py` — feed it your Tastytrade screenshots** and it produces the CSV
   for you. This is the convenience layer (see below). The CSV stays the source
   of truth either way, so the two paths interoperate.

### tt-ocr: Tastytrade screenshots -> structured trades

Ryan already screenshots his **Order Chains** (the realized-P&L table) and
**Curve / Trade Analysis** (the payoff plan) for every recap. `tt_ocr.py` reads a
folder of those PNGs, auto-detects which layout each one is, crops the rigid stat
regions, and extracts them to JSON + a `build.py`-ready CSV.

```bash
python tt_ocr.py samples/                 # folder -> data/ocr_trades.{json,csv}
python tt_ocr.py samples/ADBE_order_chains.png
python tt_ocr.py samples/ --debug crops/  # also save every cropped region
```

- **Layout detection** uses OCR keywords when available and a geometric fallback
  otherwise (Order Chains are small ~square images; Curve views are wide ~1.6:1).
  On the three real sample screenshots this classifies 3/3 correctly with no OCR
  engine at all.
- **Region-based extraction.** Because the Tastytrade layout is rigid, the tool
  crops fixed relative regions and reads only the cells that matter (ticker,
  Total P/L, Avg Trd Pr, strategy, stat bar). That is far more reliable than
  dumping the whole image into an OCR engine. The region map is verified against
  Ryan's real screenshots: the `total_pl` crop isolates exactly `-653.00` on the
  ADBE chain and `-910.95` on the /6EU6 chain.
- **It never fabricates.** If the OCR engine is missing or a field reads with low
  confidence, the value is emitted as `null` and added to a `flags` list. A track
  record built on guessed P&L is worse than none.
- **Status awareness.** An Order Chains "Total P/L" can be an *open* (unrealized)
  mark, not a realized close — the ADBE `-653.00` is exactly that, an open
  position. The tool flags open vs closed and only writes a `realized_pl` for
  chains it can confirm are closed, so open marks never pollute the equity curve.

**Build once, works for any Tastytrade user**, not just Ryan.

#### Honest status of the OCR read step

The hard, novel part of this tool is the layout detection + region map, and that
is done and verified against real images. The text-read step uses **pytesseract**
(requires the Tesseract binary). In the sandbox where this was assembled, Tesseract
could not be installed, so live text extraction was not executed end-to-end; the
tool correctly ran in crop-only mode (detect + crop + flag null). The region crops
were validated visually (the production "vision-LLM read" path): each crop isolates
exactly one value, which any OCR engine or vision model reads trivially.

To run the full pipeline:

```bash
apt-get install tesseract-ocr        # the OCR binary
pip install pytesseract pillow
python tt_ocr.py samples/
```

Per-leg row parsing (qty / expiry / DTE / strike / C-P / action) is implemented as
best-effort column banding and is the weakest link; for production-grade leg
fidelity, a vision-LLM pass over the saved crops is the recommended path. The
top-level fields (ticker, Total P/L, strategy) are the reliable ones.

## Files

| File | What it is |
|------|------------|
| `build.py` | Reads a trades CSV, computes all metrics, writes `dashboard.html`. Stdlib only (uses pandas if present, degrades gracefully without it). |
| `tt_ocr.py` | Tastytrade screenshot ingester: detects layout, crops regions, OCRs the stat cells, emits JSON + a `build.py`-ready CSV. Stdlib + Pillow; pytesseract optional. |
| `data/trades_template.csv` | The blank template a writer maintains by hand. Two example rows, clearly marked, that the builder ignores. |
| `data/trades_seed.csv` | **Real** closed trades extracted from Ryan's public recaps (see honesty note). |
| `data/open_book.csv` | **Real** 25-row live open book from Ryan's open-book/risk spreadsheet screenshot (verified row-by-row). Feeds the Live Book & Risk panel. |
| `data/portfolio_summary.json` | Position-mix + buying-power figures from the same spreadsheet (verified). |
| `samples/` | Four real public screenshots from Ryan's recaps (2 Order Chains, 1 Curve, 1 open-book spreadsheet) so `tt_ocr.py` runs out of the box. |
| `dashboard.html` | The generated, self-contained artifact (inline Chart.js via CDN). Two clearly-labeled panels: realized Track Record + Live Book & Risk. |

### Input schema

```
date_opened, date_closed, ticker, strategy, debit_or_credit, entry_price,
exit_price, max_profit, max_loss, breakeven, bp_used, realized_pl, notes
```

A row is a **closed trade** when `realized_pl` is filled, and an **open position**
when `realized_pl` (and `date_closed`) are blank. That one rule drives the whole
dashboard.

### Run it

```bash
python build.py                       # data/trades_seed.csv -> dashboard.html
python build.py data/my_trades.csv    # your own CSV
python build.py in.csv out.html       # custom input + output
```

## Honesty note on the seed data

This was the part that mattered most, so here is exactly what was done.

- **Source:** Ryan's public Substack archive (free posts only, no paywalled or
  private data). Twelve "Weekly Recap" posts, **04-02-26 through 06-19-26**, pulled
  via the public Substack API and parsed from the post text (ticker symbols live in
  Substack "cashtag" tags and were recovered programmatically).
- **What was extractable:** every closed trade's realized P/L is stated **in the
  prose** ("netting $2,620", "expired worthless for a $540 loss", "closed at 50% of
  max profit"). The broker screenshots could not be OCR'd here, and that turned out
  not to matter, because the numbers that build a track record are all in the words.
- **52 real closed trades** were extracted. **Zero sample/filler rows were needed.**
- **The reconciliation check:** for all 12 weeks, the individual trade P/L summed in
  this dataset matches Ryan's own reported weekly **Closed Profit/(Loss)** total to
  the penny. Every single week. That is the confidence that this is his real record,
  not a reconstruction.

What is *approximate*: `date_closed` is set to each recap's week-ending date (the
recaps are weekly; exact intra-week fill dates live in Ryan's own records).
`date_opened` is filled where he stated it explicitly, else left blank. Entry
premiums, breakevens, and BP figures are filled where disclosed and left blank
otherwise. The **12 open positions** are the ones whose full parameters appear in
the prose of recent recaps; Ryan reports ~25-30 total open at any time, most detailed
only in screenshots, so this is a disclosed subset, clearly labeled.

## What the dashboard reveals (seed data)

| Metric | Value |
|---|---|
| Realized P/L (Apr 2 - Jun 19, 2026) | **+$20,299.62** |
| Closed trades | 52 |
| Win rate | 73.1% |
| Profit factor | 5.18 |
| Avg win / avg loss | +$662 / -$347 |
| Best / worst trade | +$2,700 (/ES strangle) / -$540 (/NQ debit spread) |

The per-strategy split is the punchline. His **premium-selling** book (short puts,
short strangles, risk-free flies, put credit spreads) is a clean, high-win-rate
engine. His **cheap directional shots** (long butterflies, debit spreads, ITM credit
hedges) are where every losing dollar comes from. The screenshots never let you see
that. The dashboard makes it obvious in one glance.

## Second source: the Live Book & Risk panel (spreadsheet OCR)

Ryan also keeps a **Google-Sheets-style open-book / risk panel** and screenshots it
into his recaps (positions table on the left, Portfolio Summary sidebar on the
right). That is clean dark-text-on-white with gridlines, i.e. highly OCR-reliable.
The dashboard now has a second, clearly-labeled panel, **Live Book & Risk**, that
mirrors his own sheet (same columns: Trade Description, Credit Rcv'd, Debit Paid,
Max Profit, Max Loss, BP $, BP %, Position Type, Risk Type, Date Opened) plus the
Portfolio Summary card. The pitch: he stops hand-typing positions; the tool OCRs
his screenshot and shows the same view he already trusts, prettier and automated.

The two panels are deliberately separate sources: **Track Record** = realized,
closed trades (from recap prose); **Live Book** = current open positions (from the
spreadsheet). Open positions have no realized P/L, so they never touch the win
rate / equity curve.

### How the spreadsheet OCR works (`tt_ocr.py`, `spreadsheet` layout)

- **Layout auto-detected** by background brightness (his sheet is light; the
  tastytrade trade UIs are dark) and by the header keywords.
- **Real column segmentation, not guessing.** The tool detects the vertical and
  horizontal **gridlines** (full-height/width non-white runs) and slices cells at
  those boundaries. Demonstrated on `samples/open_book_spreadsheet.png`: it finds
  **12 vertical gridlines (-> the 10 documented columns) and 26 horizontal lines
  (-> 25 data rows)**. Run with `--debug` to dump the grid overlay + every cell.
- **Handles the infinity glyph** (`∞` Max Profit on naked/LEAP longs) -> unbounded,
  not a parse error. Blank cells (credit XOR debit) stay blank.
- **Risk Type is auto-derived** and editable: long options & spreads/flies/
  diagonals/condors/zebras/covered = **Defined**; naked shorts & long futures =
  **Undefined**. (The naive "long singles = undefined" rule is wrong; this
  corrected rule matches all 25 of Ryan's own rows.) **Position Type (Core/Supp)**
  can't be inferred from the broker; it's left to the user.

### OCR accuracy report (honest)

The text-read engine (Tesseract / `pytesseract`) could not be installed in this
sandbox, so `tt_ocr.py` ran in **segment + crop + flag-null** mode for the live
read; the cropped cells were validated by an independent vision read (the
production "vision-LLM pass" path). On the real `ryan_spreadsheet.png` sample, cell
segmentation was correct for **all 25 rows × 10 columns**, and the values seeded
into `data/open_book.csv` were verified field-by-field against the image. Findings:

- The big numeric cells (credit, debit, max profit/loss, BP $, BP %) read cleanly.
- The two small dropdown cells (Position / Risk) are the error-prone ones at full
  image resolution and **needed a zoom to read reliably** — exactly where a naive
  OCR would slip. Independent verification corrected four first-pass misreads:
  ADBE Risk (Def, not Undef), SPX Put Butterfly Risk (Def, not Undef), WMT Position
  (Supp, not Core), and the GLD date (**9/25/2025**, not 5/25/2026).
- Nothing was fabricated; the shipped `open_book.csv` is the verified-correct set.

### Fees

Fees are intentionally a no-op on the **current** numbers and are noted, not forced:
the closed Track Record uses Ryan's own **booked net results** (his stated realized
P/L already reflects what hit his account), and open positions carry no realized
P/L. A configurable per-contract/per-leg fee layer (gross vs net) is the right add
the day this consumes raw fills; it is documented as a follow-up rather than
bolted on where it would change nothing.

### Deployment status (static PWA)

The approved end state is a hosted static PWA at `docs/tt-tracker/`, served at
`https://mphinance.github.io/mphinance/tt-tracker/`, doing the OCR **in the
browser** via Tesseract.js (WASM) so screenshots never leave the device. That
browser port is **not done yet** and is the remaining work:

- [ ] Move/duplicate the app to `docs/tt-tracker/` with relative asset paths; add
      `docs/.nojekyll`.
- [ ] Port the layout-detection + gridline-segmentation + region maps (already
      proven here in Python) to JS, reading the canvas pixels.
- [ ] Wire Tesseract.js with the dark-UI preprocessing (upscale, grayscale,
      invert/threshold) and numeric char whitelist + per-field PSM.
- [ ] `manifest.json` + a service worker that caches the app shell **and** the
      Tesseract WASM + `eng.traineddata` (~10-15 MB) for offline / installable use.
- [ ] Surface the privacy promise in the UI (already drafted in the panel footer).

What is **done and runnable today** (this worktree): the spreadsheet OCR path, the
verified open-book data, and the combined two-panel dashboard. The Ryan result does
not depend on the PWA wrapper.

---

Credit and full context: **Ryan LePiane / LP Options Academy** -
https://ryanlepiane.substack.com . Go subscribe; the weekly recaps are free and
genuinely good.

*Educational only. Not investment advice. Past performance does not guarantee future results.*
