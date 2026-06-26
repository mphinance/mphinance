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
| `data/trades_seed.csv` | **Real** trades extracted from Ryan's public recaps (see honesty note). |
| `samples/` | Three real public Tastytrade screenshots from Ryan's recaps (2 Order Chains, 1 Curve) so `tt_ocr.py` is runnable out of the box. |
| `dashboard.html` | The generated, self-contained artifact (inline Chart.js via CDN). |

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

---

Credit and full context: **Ryan LePiane / LP Options Academy** -
https://ryanlepiane.substack.com . Go subscribe; the weekly recaps are free and
genuinely good.

*Educational only. Not investment advice. Past performance does not guarantee future results.*
