# TT Tracker — tastytrade options track record + live book

A static, client-side **Progressive Web App** that turns tastytrade screenshots into a
clean options **track record** (equity curve, win rate, profit factor, per-strategy
breakdown) and a **live book & risk** view — all via **in-browser OCR**. No backend, no
broker login, no upload.

**Live:** https://mphinance.github.io/mphinance/tt-tracker/

It ships seeded with **Ryan LePiane's** verified public recap data so it looks alive on
first load: **52 closed trades, +$20,299.62 realized, 73.1% win rate, 5.18 profit factor**,
plus **25 open positions** and his portfolio-summary card. It generalizes to **any
tastytrade user** — drop your own screenshots and they replace the seed.

A free gift for Ryan, and a portfolio piece for [Momentum Phinance](https://momentumphinance.substack.com).
Go subscribe to [**Ryan LePiane — LP Options Academy**](https://ryanlepiane.substack.com).

---

## The privacy model (the whole point)

Everything runs **on your device**. Screenshots are read by **Tesseract.js (WASM)** inside
your browser tab and **never leave your computer**. There is no server to send them to.
State (your edits + OCR'd rows) persists to **localStorage** — still on-device. The only
network calls are the one-time fetch of the OCR engine + fonts from a CDN (then cached by
the service worker for offline use).

## How to use it

1. Open the app. It loads with Ryan's verified seed so you can see the shape of it.
2. Go to **Import**. Drag, paste (Ctrl/Cmd-V), or click to add tastytrade screenshots.
3. The app detects the layout, OCRs it on-device, and routes the data:
   - **Type A Positions Spreadsheet** → replaces the **Live Book**.
   - **Type B Order Chains** (fully CLSD only) → books a realized trade onto the **Track Record**.
   - **Type E Active Monitor** → fills the **Monitor** (unrealized cross-check, beta).
4. **Edit anything.** Every Live Book cell is click-to-edit; Position (Core/Supp) and Risk
   (Def/Undef) are dropdowns. Low-confidence OCR cells are highlighted "needs review".
5. **Reset** restores Ryan's seed. **Export** downloads your track record as CSV.
6. **Install** it (browser "Install app") for an offline, standalone PWA.

### Risk Type & Position Type
- **Risk Type is auto-derived** and editable: spreads / butterflies / condors / zebras /
  diagonals / covered / long options = **Defined**; naked short puts/calls, strangles/
  straddles, long futures = **Undefined**. (Derivation validated against all of Ryan's own
  rows — long LEAPS correctly read Defined.) A `·d` badge marks a derived value.
- **Position Type (Core/Supp)** is your discretionary tag — never derived, always editable.

### Fees
A fee model (per-contract open/close + clearing/reg) is included but **OFF by default** and
a no-op, so the headline numbers stay gross and reconcile exactly to Ryan's reported totals.
Toggle it on to see gross vs net; it's an estimate, not from broker statements.

---

## Architecture

Pure static files, no build step. ES modules.

| File | Role |
|---|---|
| `index.html` / `css/app.css` | App shell + tastytrade theme |
| `js/seed.js` | Verified seed data (auto-generated from the reconciled CSVs) |
| `js/engine.js` | Realized-PnL + stats. Ported (semantics frozen) from the borrowed TS journal engine (`computeRealizedPnl`, `winRate`, `sumPnl`, tolerant coercion) + equity-curve / avg-win-loss / profit-factor recipe. Reconciles to +$20,299.62 / 73.1% / 5.18. |
| `js/ocr.js` | Tesseract.js wrapper + layout detection + **gridline column/row segmentation** (ported from `tt_ocr.py`) + parsers (∞ glyph, bond-ticks, bottom-crop detection). Records per-cell bbox + confidence and emits review items. Holds the in-session image registry (crops never persisted). Never fabricates. |
| `js/validators.js` | Per-column validators (money/%/date/ticker/Core-Supp/Def-Undef + cross-foot). `confidence = min(OCR conf, validator pass)` — catches the dangerous high-confidence misreads (`1,250` → `1.250`). |
| `js/review.js` | The crop-thumbnail confirmation queue: shows only flagged cells with the cropped source pixels + editable field + suggested fix. Keyboard-first. |
| `js/charts.js` | Dependency-free inline-SVG equity curve (green/red payoff shading), strategy bars, BP gauges, mix donuts — so it works fully offline. |
| `js/card.js` | The Weekly Card export — a **deterministic Canvas 2D render** (1600×900, no external lib, works offline) → copy-to-clipboard / download PNG. |
| `js/backup.js` | First-class JSON export/import with a `schemaVersion` stamp + migration shim + >7-day backup nudge. |
| `js/app.js` | State, localStorage, panels, drag/drop + paste ingest, editing, review wiring, provisional ribbon, share. |
| `manifest.json` / `sw.js` | PWA manifest + service worker (scoped to `/mphinance/tt-tracker/`), caching the app shell **and** the Tesseract WASM + `eng.traineddata` for offline OCR. |

### Review loop, Weekly Card, backups (v0.2 additive)

- **Crop-thumbnail review loop (the trust surface).** High-confidence cells auto-accept and
  collapse; you only touch the flagged ones. Each flagged cell shows the **cropped source
  pixels** from your screenshot beside an editable field + a suggested fix — you confirm a
  picture, you don't re-read the source. Keyboard-first (Enter = accept, type = correct,
  Tab/skip = next), a counter that ticks down, 🔴 must-confirm / 🟡 check severity. A
  **"Provisional — N unconfirmed"** ribbon shows on every panel until the queue hits 0, and
  CSV export warns while provisional, so a wrong number can't be exported silently. The crop
  lives only in an in-session canvas registry — **image bytes are never written to disk or
  localStorage**; only the parsed value + bbox metadata persist.
- **Weekly Card.** A deterministic 1600×900 PNG: title + week-ending + your **handle**
  (the hero), mini equity curve, KPI tiles (Win rate / Profit factor / Trades / Net P&L),
  best/worst strategy. **Defaults to % + ratios with dollars OFF** (writers won't post
  account size); one toggle reveals $. **Copy-to-clipboard** is the primary action;
  Download PNG is the fallback. Muted `tt-tracker · mphinance` footer reads as a chart
  credit. Card prefs (handle, $/%, week) persist to localStorage for a 20-second ritual.
- **Backups.** JSON export/import is the lossless cross-device path; CSV stays for `build.py`
  interop. A nudge appears if your last JSON backup is >7 days old.

### BYOK vision accelerator (HYBRID OCR — opt-in, `js/vision.js`)

The default read path stays **pure on-device Tesseract** (privacy literal). The vision
accelerator is an **opt-in, provider-agnostic BYOK layer** offered only on flagged cells,
plugged into the same review-loop seam (`processScreenshot` → per-cell
`{value, bbox, confidence}` → validators → review items).

- **Adapter interface:** `{ id, label, defaultModel, family, stub?, custom?, buildRequest(dataUrl, prompt, cfg) → {url, headers, body}, parseResponse(json) → text }`.
- **Providers wired now (one OpenAI-compatible code path):**
  - **OpenRouter** (`openrouter.ai/api/v1/chat/completions`) — the **default**, editable model.
  - **OpenAI / ChatGPT** (`api.openai.com/v1/chat/completions`).
  - **Custom / local** — supply a base URL + model → **Ollama** (`http://localhost:11434/v1`), **LM Studio** (`http://localhost:1234/v1`), **vLLM**, **llama.cpp** with open-source vision models (llama3.2-vision, qwen2-VL…). No key required for local.
  - All three use the OpenAI vision message format (`content` array, `type:image_url`, data-URL base64 of the crop).
- **Next-pass stubs (registry slots present, not selectable for live send):** native **Anthropic** (messages API + `anthropic-dangerous-direct-browser-access`) and **Google Gemini** (`generateContent` / `inline_data`) — shown disabled in the picker, labelled "(next pass)".
- **Privacy + key handling:** vision is **OFF by default**. Only the **cropped cell** is ever sent — never the full screenshot. The API key lives in **sessionStorage only** — never localStorage, never persisted, sent only to the chosen endpoint (verified headless: absent from localStorage, present in sessionStorage). An explicit **per-use consent line names the provider**, plus a first-use confirm.
- **Re-enters the same loop:** a vision read flows back through the **same validators**, fills the proposed value, tags the item with the engine (`read by openrouter:<model>`), and **still requires human confirm/override** — never auto-booked. Refuse-to-guess preserved (model unsure → null + flag); the tight `{value,type}` JSON prompt makes `parseResponse` deterministic.

The theme: near-black charcoal surfaces, dense data-forward grid, JetBrains Mono tabular
numerics, green gains / red losses, a bright tasty-gold accent, and the platform's
GAIN/LOSS/OPEN/CLSD color language — a native-feeling extension of the tastytrade UI the
screenshots came from.

---

## OCR scope & honest accuracy

Validated against the real public screenshots in the build corpus (118 images, 8 weeks).
Tesseract.js runs in the browser, so character-level read accuracy can't be benchmarked in
CI here — what was validated is the **layout-detection and geometric segmentation** (the
JS pixel logic was replicated against the real images), which is what makes or breaks the
read. Honest status by layout:

- **TIER 1 — Type A Positions Spreadsheet (PRIMARY):** layout detection of the white grid
  is reliable (brightness gate). Gridline column/row segmentation cleanly isolates the 10
  columns on **6 of 7** real Type-A sheets (exactly 12 vertical lines → 11 column edges).
  The 7th is a low-contrast capture with dropdown carets that under-segments — it honestly
  emits a `GRID_NOT_FOUND` flag and reads zero rows rather than guessing. Bottom-cropped
  sheets are detected and flagged ("rows below the fold missing"). The ∞ glyph → `null`,
  blank credit-XOR-debit cells handled. **This is the strongest path.**
- **TIER 2 — Type B Order Chains:** ticker / Total P/L / status regions are cropped and
  OCR'd. **Gated correctly**: any "Open Pos" block ⇒ the chain is treated as live and is
  **not** booked as realized. Bond-tick notation (`109'12`) is parsed as 32nds, not decimal.
  Cropped headers (ticker scrolled off) flag low-confidence so you set the symbol manually.
- **TIER 3 — Type E Active Monitor:** **beta / heuristic.** It has no fixed grid, so this is
  a line-based parse used only as an unrealized cross-check. Stitched-image de-dup is
  implemented (merge button). Treat as rough, not source-of-truth.
- **SKIPPED:** Type C curves and Type F fill tickets (context only).

Guiding rule throughout: **never fabricate.** Low-confidence or unreadable values emit
`null` + a visible "needs review" flag.

---

## Checklist — what's done vs left

**Done**
- [x] Static client-side PWA under `docs/tt-tracker/`, relative paths, SW scoped to the subpath.
- [x] `docs/.nojekyll` created.
- [x] Track Record panel: equity curve, win rate, avg win/loss, profit factor, per-strategy, best/worst — **reconciles to +$20,299.62 / 73.1% / 5.18** (verified in a headless-browser run).
- [x] Live Book & Risk panel mirroring Ryan's 10-column sheet + Portfolio Summary (mix/risk donuts, BP gauges).
- [x] Monitor panel (Type E, beta).
- [x] In-browser OCR (Tesseract.js) with layout detection, Type-A gridline segmentation, Type-B chain gating, ∞/bond-tick/crop handling.
- [x] Auto-derived Risk Type (validated vs Ryan's sheet), editable; Core/Supp editable.
- [x] Editable + localStorage-persistent; Reset-to-seed; CSV export.
- [x] Fee config (OFF by default, no-op).
- [x] manifest + service worker (app shell + Tesseract WASM/traineddata offline cache).
- [x] Privacy promise visible in the UI.
- [x] **Crop-thumbnail review loop** — flagged-only queue with source-pixel crops, validators (`min(OCR conf, validator)`, catches `1,250`→`1.250`), keyboard-first, severity buckets, provisional ribbon, blank-cell suppression. Verified headless on a real sheet (163 flags → confirm ticks the counter; crops render).
- [x] **Weekly Card** — deterministic Canvas PNG (1600×900), handle hero, %-default / $-toggle, copy-to-clipboard + download, muted footer, persisted prefs. Verified headless ($-off vs $-on render differently; copy succeeds; console clean).
- [x] **JSON backup** — first-class export/import with `schemaVersion`, migration shim, >7-day nudge.
- [x] **BYOK vision accelerator (HYBRID)** — provider-agnostic adapter; OpenRouter (default) / OpenAI / Custom-local in one OpenAI-compatible path; opt-in, crop-only, key in sessionStorage, per-use consent; results re-enter the same validators + review item with human confirm. Verified headless: request shapes for all 3, key-never-in-localStorage, consent gate, and a mocked vision response flowing into the review item (re-validated).

**Left / honest caveats**
- [ ] **Browser-OCR character accuracy not benchmarked in CI** (no in-browser Tesseract in
      this environment). Segmentation/layout logic was validated against the real images;
      end-to-end read quality should be spot-checked by a human on first real use.
- [ ] **Type E (Monitor) is heuristic** — no fixed-grid parse; per-leg tree (underlying →
      strategy → legs) and futures micro-decimal marks are not fully structured yet.
- [ ] **Low-contrast Type-A sheets** (1 of 7 in the corpus) under-segment and flag rather
      than read. A future pass could fall back to OCR-word-cluster column inference.
- [ ] **Type B → row mapping is chain-total level**, not per-leg. The per-leg BTO/STO/BTC/STC
      → side/entry/exit engine exists (`computeRealizedPnl` / `chainRealizedPnl`) but the
      OCR doesn't yet emit clean per-leg rows to feed it; it books the chain Total P/L.
- [ ] **Type F fill tickets** intentionally unsupported (no computed P/L).
- [ ] **Weekly Card render is canvas, not html-to-image** — the brief suggested `html-to-image toPng`, but `chrome-headless-shell` drops its `<foreignObject>` HTML (only background/SVG rasterized → identical output regardless of content). Switched to a deterministic Canvas 2D render, which renders fully, validates headless, and works offline (no CDN). Same artifact, more robust path.
- [ ] **Review crops are session-only by design** — after a page reload the flag counts persist (metadata) but the crop image is gone (image bytes never stored). You can still edit/confirm from your own copy; the crop only shows during the import session.
- [ ] **BYOK adapters validated against MOCKS, not live APIs** — request construction, key handling, consent gate, and the mocked-response → review-item flow are verified headless; real calls to OpenRouter/OpenAI/your-local-endpoint need a one-time manual smoke (enable AI assist, paste a key or point at `http://localhost:11434/v1`, click "Read with AI" on a flagged cell). No network calls happen in CI.
- [ ] **Native Anthropic + Gemini adapters are stubs** — registry slots exist (disabled in the picker, "(next pass)"); their bespoke request/response shapes ship next pass. Selecting them throws a clear error rather than sending.
- [ ] **Whitelabel / rename deferred** (DECISION 2, next pass): no "LP Ledger" rebrand, brand-config abstraction, or "not affiliated with tastytrade" footer yet — current tastytrade-gold theme + naming kept, repo stays `tt-tracker`.
- [ ] Icons are generated placeholders (gold payoff mark on charcoal); swap for branded art if desired.

---

Built by Michael / Momentum Phinance. Seeded from Ryan LePiane's public LP Options Academy
weekly recaps. Educational only; not investment advice. Past performance ≠ future results.
