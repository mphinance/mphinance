// ocr.js — in-browser OCR of tastytrade screenshots (Tesseract.js / WASM).
// Everything runs on-device. Ported from tt_ocr.py: layout detection
// (brightness + aspect + keyword), gridline column/row segmentation for the
// Type A "Positions Spreadsheet", plus parsers for Order Chains (Type B) and the
// dark Active/Positions Monitor (Type E). NEVER fabricates — low-confidence reads
// emit null + a "needs review" flag.

import { numOrNull, deriveRiskType } from "./engine.js";

const TESS_VERSION = "5.1.1";
const TESS_CDN = `https://cdn.jsdelivr.net/npm/tesseract.js@${TESS_VERSION}/dist/tesseract.min.js`;

let _worker = null;
let _tessLoaded = false;

export async function ensureTesseract(progressCb) {
  if (_worker) return _worker;
  if (!_tessLoaded) {
    await loadScript(TESS_CDN);
    _tessLoaded = true;
  }
  // eslint-disable-next-line no-undef
  _worker = await Tesseract.createWorker("eng", 1, {
    logger: (m) => progressCb && progressCb(m),
  });
  return _worker;
}

function loadScript(src) {
  return new Promise((res, rej) => {
    if (document.querySelector(`script[src="${src}"]`)) return res();
    const s = document.createElement("script");
    s.src = src; s.onload = res; s.onerror = () => rej(new Error("Failed to load " + src));
    document.head.appendChild(s);
  });
}

// ---------------------------------------------------------------------------
// Image helpers
// ---------------------------------------------------------------------------
export function fileToImage(blob) {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => res(img);
    img.onerror = rej;
    img.src = URL.createObjectURL(blob);
  });
}

function imageToCanvas(img) {
  const c = document.createElement("canvas");
  c.width = img.naturalWidth || img.width;
  c.height = img.naturalHeight || img.height;
  c.getContext("2d").drawImage(img, 0, 0);
  return c;
}

function grayscale(ctx, w, h) {
  const d = ctx.getImageData(0, 0, w, h).data;
  const g = new Uint8Array(w * h);
  for (let i = 0, j = 0; i < d.length; i += 4, j++) {
    g[j] = (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114) | 0;
  }
  return g;
}

function meanBrightness(g) {
  let s = 0;
  for (let i = 0; i < g.length; i++) s += g[i];
  return s / g.length;
}

// ---------------------------------------------------------------------------
// Layout detection (port of tt_ocr.detect_layout, + monitor/ticket)
// ---------------------------------------------------------------------------
export function detectLayout(canvas, gray, ocrText) {
  const w = canvas.width, h = canvas.height, aspect = w / h;
  if (ocrText) {
    const t = ocrText.toLowerCase();
    if (t.includes("trade description") && t.includes("date opened")) return "spreadsheet";
    if (t.includes("portfolio summary") && t.includes("position mix")) return "spreadsheet";
    if (t.includes("order chains") || (t.includes("total p/l") && t.includes("avg trd"))) return "order_chains";
    if ((t.includes("p/l open") || t.includes("p/l opn")) && t.includes("days to expiration")) return "monitor";
    if (t.includes("bp eff") || (t.includes("max profit") && t.includes("pop"))) return "curve";
    if (t.includes("fill") && (t.includes("gtc") || t.includes("limit"))) return "ticket";
  }
  const bright = meanBrightness(gray);
  if (bright > 180) return "spreadsheet";
  if (w <= 760 && aspect >= 0.85 && aspect <= 1.2) return "order_chains";
  if (aspect >= 1.35) return bright < 60 ? "monitor" : "curve"; // wide dark grid = monitor
  return w <= 760 ? "order_chains" : "monitor";
}

// ---------------------------------------------------------------------------
// Gridline detection (port of tt_ocr.detect_gridlines) — pure pixel scan
// ---------------------------------------------------------------------------
function detectGridlines(gray, w, axis, region, lineFrac = 0.55) {
  const [l, t, r, b] = region;
  const hits = [];
  if (axis === "x") {
    const denom = Math.max(1, b - t);
    for (let x = l; x < r; x++) {
      let nonwhite = 0;
      for (let y = t; y < b; y++) if (gray[y * w + x] < 245) nonwhite++;
      if (nonwhite / denom > lineFrac) hits.push(x);
    }
  } else {
    const denom = Math.max(1, r - l);
    for (let y = t; y < b; y++) {
      let nonwhite = 0;
      for (let x = l; x < r; x++) if (gray[y * w + x] < 245) nonwhite++;
      if (nonwhite / denom > lineFrac) hits.push(y);
    }
  }
  const merged = [];
  for (const v of hits) {
    if (merged.length && v - merged[merged.length - 1][merged[merged.length - 1].length - 1] <= 3) {
      merged[merged.length - 1].push(v);
    } else merged.push([v]);
  }
  return merged.map((grp) => Math.round(grp.reduce((a, c) => a + c, 0) / grp.length));
}

const SPREADSHEET_COLUMNS = [
  "trade_description", "credit_rcvd", "debit_paid", "max_profit", "max_loss",
  "bp_usd", "bp_pct", "position_type", "risk_type", "date_opened",
];

// ---------------------------------------------------------------------------
// Parsers
// ---------------------------------------------------------------------------
export function parseMoney(text) {
  if (!text) return null;
  let t = String(text).replace(/,/g, "").replace(/\s/g, "");
  const neg = (t.startsWith("(") && t.endsWith(")")) || t.startsWith("-");
  const m = t.match(/-?\d+(\.\d{1,2})?/);
  if (!m) return null;
  const val = Math.abs(parseFloat(m[0]));
  return neg ? -val : val;
}

// ∞ → "inf"; blank/dash → null; else money
export function parseInf(text) {
  if (text == null) return null;
  const t = String(text).trim();
  if (!t || t === "-" || t === "—") return null;
  if (t.includes("∞") || /^(inf|infinity|oo|00)$/i.test(t)) return "inf";
  return parseMoney(t);
}

// Treasury bond-tick notation: 109'12 = 109 + 12/32 (NOT decimal). Returns {value, raw}.
export function parseBondTick(text) {
  if (!text) return null;
  const m = String(text).match(/(-?\d+)'(\d{1,2})/);
  if (!m) return null;
  const whole = parseInt(m[1], 10);
  const ticks = parseInt(m[2], 10);
  const sign = whole < 0 ? -1 : 1;
  return { value: Math.abs(whole) * sign + (sign * ticks) / 32, raw: m[0], notation: "32nds" };
}

export function parseTicker(text) {
  if (!text) return null;
  let t = String(text).replace(/order\s*chains/i, "").trim().toUpperCase();
  const m = t.match(/\/?[A-Z0-9]{1,6}/);
  return m ? m[0] : null;
}

// ---------------------------------------------------------------------------
// OCR a sub-rectangle of a canvas. dark=true → invert (light-on-dark UI text).
// ---------------------------------------------------------------------------
async function ocrRect(worker, canvas, rect, opts = {}) {
  const { dark = false, psm = 7, whitelist = null, scale = 2 } = opts;
  const sx = Math.max(0, Math.floor(rect.left));
  const sy = Math.max(0, Math.floor(rect.top));
  const sw = Math.min(canvas.width - sx, Math.ceil(rect.width));
  const sh = Math.min(canvas.height - sy, Math.ceil(rect.height));
  if (sw <= 1 || sh <= 1) return { text: "", confidence: 0 };
  const c = document.createElement("canvas");
  c.width = sw * scale; c.height = sh * scale;
  const cx = c.getContext("2d");
  cx.imageSmoothingEnabled = true;
  cx.drawImage(canvas, sx, sy, sw, sh, 0, 0, c.width, c.height);
  // grayscale (+ optional invert + light threshold)
  const id = cx.getImageData(0, 0, c.width, c.height);
  const d = id.data;
  for (let i = 0; i < d.length; i += 4) {
    let v = (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114) | 0;
    if (dark) v = 255 - v;
    v = v < 135 ? 0 : 255;
    d[i] = d[i + 1] = d[i + 2] = v;
  }
  cx.putImageData(id, 0, 0);
  const params = { tessedit_pageseg_mode: String(psm) };
  if (whitelist) params.tessedit_char_whitelist = whitelist;
  await worker.setParameters(params);
  const { data } = await worker.recognize(c);
  return { text: (data.text || "").trim(), confidence: data.confidence || 0 };
}

const LOW_CONF = 55; // below this, treat numeric reads as "needs review"

// ---------------------------------------------------------------------------
// TIER 1 — Type A Positions Spreadsheet
// ---------------------------------------------------------------------------
async function extractSpreadsheet(worker, canvas, gray) {
  const w = canvas.width, h = canvas.height;
  const flags = [];
  // Grid lives left of the Portfolio Summary side card. Detect ROW lines first
  // (they span the table width well), then scan COLUMN lines only within the
  // table's vertical band — robust to short / bottom-cropped sheets.
  const tableRight = Math.floor(w * 0.7);
  let hlines = detectGridlines(gray, w, "y", [0, 0, tableRight, h]);
  const bandTop = hlines.length >= 2 ? hlines[0] : 0;
  const bandBot = hlines.length >= 2 ? hlines[hlines.length - 1] : h;
  let vlines = detectGridlines(gray, w, "x", [0, bandTop, tableRight, bandBot]);

  const nCols = SPREADSHEET_COLUMNS.length;
  if (vlines.length < nCols + 1 || hlines.length < 3) {
    flags.push(`GRID_NOT_FOUND: found ${vlines.length} vlines / ${hlines.length} hlines (need ${nCols + 1}/3+). Try a sharper, full-width crop.`);
    return { layout: "spreadsheet", positions: [], geometry: { vlines, hlines }, flags };
  }
  const xedges = vlines.slice(0, nCols + 1);

  // bottom-cropped detection: if the last hline isn't near the image bottom,
  // rows below the fold are missing.
  const bottomGap = h - hlines[hlines.length - 1];
  if (bottomGap > h * 0.08) flags.push("BOTTOM_CROPPED: sheet appears cut off; rows below the last gridline are missing from this screenshot.");

  const positions = [];
  for (let ri = 1; ri < hlines.length - 1; ri++) {
    const y0 = hlines[ri], y1 = hlines[ri + 1];
    if (y1 - y0 < 8) continue;
    const rec = { id: "ocr-" + Math.random().toString(36).slice(2, 8) };
    let lowConf = false, anyText = false;
    for (let ci = 0; ci < nCols; ci++) {
      const col = SPREADSHEET_COLUMNS[ci];
      const cx0 = xedges[ci], cx1 = xedges[ci + 1];
      const isText = col === "trade_description" || col === "position_type" || col === "risk_type";
      const isDate = col === "date_opened";
      const { text, confidence } = await ocrRect(worker, canvas, {
        left: cx0 + 1, top: y0 + 1, width: cx1 - cx0 - 2, height: y1 - y0 - 2,
      }, {
        dark: false, psm: 7,
        whitelist: isText ? null : (isDate ? "0123456789/-" : "0123456789.,∞-/%"),
      });
      if (text) anyText = true;
      const moneyCols = ["credit_rcvd", "debit_paid", "max_profit", "max_loss", "bp_usd", "bp_pct"];
      if (moneyCols.includes(col)) {
        rec[col] = parseInf(text);
        if (text && confidence < LOW_CONF) lowConf = true;
      } else {
        rec[col] = text || null;
      }
    }
    if (!anyText) continue;
    // auto-derive Risk Type if the column read blank
    if (!rec.risk_type) {
      const d = deriveRiskType(rec.trade_description);
      if (d) { rec.risk_type = d; rec.risk_type_source = "derived"; }
    }
    rec.position_type = normPos(rec.position_type);
    rec.risk_type = normRisk(rec.risk_type);
    if (lowConf) rec.needsReview = true;
    rec.src = "ocr";
    positions.push(rec);
  }
  if (positions.some((p) => p.needsReview)) flags.push("LOW_CONFIDENCE: one or more numeric cells read with low confidence — flagged for review (highlighted).");
  return { layout: "spreadsheet", positions, geometry: { vlines, hlines }, flags };
}

function normPos(v) {
  if (!v) return v;
  if (/^core/i.test(v)) return "Core";
  if (/^supp/i.test(v)) return "Supp";
  return v;
}
function normRisk(v) {
  if (!v) return v;
  if (/^undef/i.test(v)) return "Undef";
  if (/^def/i.test(v)) return "Def";
  return v;
}

// ---------------------------------------------------------------------------
// TIER 2 — Type B Order Chains (dark). Only fully-CLSD chains book realized P&L.
// ---------------------------------------------------------------------------
const ORDER_CHAINS_REGIONS = {
  ticker:    { left: 0.0, top: 0.0, right: 0.55, bottom: 0.075 },
  total_pl:  { left: 0.5, top: 0.27, right: 0.82, bottom: 0.36 },
  body:      { left: 0.0, top: 0.36, right: 1.0, bottom: 1.0 },
};

async function extractOrderChains(worker, canvas) {
  const w = canvas.width, h = canvas.height;
  const flags = [];
  const rel = (r) => ({ left: r.left * w, top: r.top * h, width: (r.right - r.left) * w, height: (r.bottom - r.top) * h });

  const tk = await ocrRect(worker, canvas, rel(ORDER_CHAINS_REGIONS.ticker), { dark: true, psm: 7 });
  let ticker = parseTicker(tk.text);
  const tot = await ocrRect(worker, canvas, rel(ORDER_CHAINS_REGIONS.total_pl), { dark: true, psm: 7, whitelist: "0123456789.,'-()" });
  const body = await ocrRect(worker, canvas, rel(ORDER_CHAINS_REGIONS.body), { dark: true, psm: 6 });

  let totalPl = parseMoney(tot.text);
  let bondTick = null;
  if (tot.text && /'/.test(tot.text)) {
    bondTick = parseBondTick(tot.text);
    if (bondTick) { totalPl = bondTick.value; flags.push(`BOND_TICK: parsed '${bondTick.raw}' as ${bondTick.value} (points + 32nds), not decimal.`); }
  }

  const bodyText = (body.text || "").toLowerCase();
  // Gate: any "open pos" block => chain still live, do NOT book.
  const hasOpen = /open\s*pos/.test(bodyText);
  const hasClsd = /clsd|clos(ing|ed)/.test(bodyText);
  let isClosed = null;
  if (hasOpen) isClosed = false;
  else if (hasClsd) isClosed = true;

  if (isClosed === false) flags.push("OPEN_POS: chain contains an open block — treated as live/unrealized, not booked as realized P&L.");
  if (isClosed === null) flags.push("STATUS_UNKNOWN: could not confirm CLSD vs open; not booked as realized (review).");
  if (!ticker) { ticker = null; flags.push("LOW_CONFIDENCE:ticker (may be cropped off the top — set it manually)."); }
  if (totalPl === null) flags.push("LOW_CONFIDENCE:total_pl");

  // strategy guess from body keywords
  const strat = guessStrategy(bodyText);

  return {
    layout: "order_chains",
    ticker, total_pl: totalPl, is_closed: isClosed,
    strategy: strat, bondTick, confidence: Math.min(tk.confidence, tot.confidence),
    bookable: isClosed === true && totalPl !== null,
    flags,
  };
}

function guessStrategy(t) {
  const map = [
    ["broken-wing", "Broken-Wing Butterfly"], ["butterfly", "Butterfly"], ["condor", "Iron Condor"],
    ["strangle", "Short Strangle"], ["straddle", "Short Straddle"], ["calendar", "Calendar"],
    ["diagonal", "Diagonal"], ["vertical", "Vertical Spread"], ["ratio", "Ratio Spread"],
    ["zebra", "Zebra"], ["super bull", "Super Bull"], ["futures option", "Futures Option"],
    ["custom", "Custom"], ["option", "Option"],
  ];
  for (const [k, v] of map) if (t.includes(k)) return v;
  return null;
}

// ---------------------------------------------------------------------------
// TIER 3 — Type E dark Active/Positions Monitor (unrealized cross-check)
// ---------------------------------------------------------------------------
async function extractMonitor(worker, canvas) {
  const flags = [];
  const w = canvas.width, h = canvas.height;
  // full-grid OCR (PSM 6 = uniform block); then row-parse heuristically.
  const { text, confidence } = await ocrRect(worker, canvas, { left: 0, top: 0, width: w, height: h }, { dark: true, psm: 6, scale: 1.5 });
  const rows = [];
  for (const line of (text || "").split("\n")) {
    const s = line.trim();
    if (!s) continue;
    // underlying header rows look like: TICKER ... -2.78 632.51 ... P/L numbers
    const m = s.match(/^(\/?[A-Z]{1,6})\b.*?(-?\d[\d,]*\.\d{2})/);
    if (m) {
      const nums = (s.match(/-?\d[\d,]*\.\d{1,2}/g) || []).map(parseMoney);
      rows.push({ symbol: m[1], plOpen: nums[nums.length >= 1 ? 0 : 0] ?? null, raw: s });
    }
  }
  if (confidence < LOW_CONF) flags.push("LOW_CONFIDENCE: monitor grid OCR is noisy — use as a rough cross-check only.");
  flags.push("MONITOR_BETA: Type E parsing is heuristic (no fixed grid). Treat as an unrealized cross-check, not source-of-truth.");
  return { layout: "monitor", rows, flags };
}

// De-dup the symbol that spans a seam when 3 stitched monitor images are merged.
export function mergeMonitorRows(parts) {
  const out = [];
  const seen = new Set();
  for (const p of parts) for (const r of p.rows || []) {
    const key = r.symbol + "|" + (r.plOpen ?? "");
    if (seen.has(key)) continue;
    seen.add(key); out.push(r);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Driver — process one screenshot end-to-end.
// ---------------------------------------------------------------------------
export async function processScreenshot(blob, progressCb) {
  const img = await fileToImage(blob);
  const canvas = imageToCanvas(img);
  const gray = grayscale(canvas.getContext("2d"), canvas.width, canvas.height);
  const worker = await ensureTesseract(progressCb);

  // cheap full-image hint OCR for layout detection
  let hint = "";
  try {
    await worker.setParameters({ tessedit_pageseg_mode: "3", tessedit_char_whitelist: "" });
    const { data } = await worker.recognize(canvas);
    hint = data.text || "";
  } catch (e) { /* ignore */ }

  const layout = detectLayout(canvas, gray, hint);
  let result;
  if (layout === "spreadsheet") result = await extractSpreadsheet(worker, canvas, gray);
  else if (layout === "order_chains") result = await extractOrderChains(worker, canvas);
  else if (layout === "monitor") result = await extractMonitor(worker, canvas);
  else result = { layout, flags: [`SKIPPED: '${layout}' layout carries no track-record data (context only).`] };

  result.layout = layout;
  result.detectedFrom = hint ? "keyword+geometry" : "geometry";
  return result;
}

export async function terminateOcr() {
  if (_worker) { await _worker.terminate(); _worker = null; }
}
