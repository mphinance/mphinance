// app.js — orchestrator: state, persistence, panels, OCR ingest, editing.
import { SEED } from "./seed.js";
import { computeTrackRecord, deriveBookSummary, deriveRiskType } from "./engine.js";
import { drawEquityCurve, drawStrategyBars, gaugeHtml, drawDonut, money, moneyInt } from "./charts.js";
import { processScreenshot, mergeMonitorRows, forgetImages } from "./ocr.js";
import { renderQueue, pending as reviewPending, counts as reviewCounts } from "./review.js";
import { renderCardCanvas, copyCanvasToClipboard, downloadCanvas } from "./card.js";
import { exportJson, parseImport, readFileText, shouldNudge, daysSinceBackup } from "./backup.js";

const LS_KEY = "tt-tracker-state-v2";
const POS = "#27c19a", NEG = "#f6465c", GOLD = "#ffcb05", BLUE = "#4a90e2", VIOLET = "#9b6bff";

// --- state ------------------------------------------------------------------
let state = load();

function defaults() {
  return {
    trades: structuredClone(SEED.trades),
    openBook: structuredClone(SEED.openBook),
    summary: structuredClone(SEED.summary),
    monitor: [],
    review: [],
    fees: { enabled: false, perContractOpen: 1.0, perContractClose: 0, clearingReg: 0.15 },
    cardPrefs: { handle: "@yourhandle", showDollars: false, weekEnding: "" },
  };
}
function load() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return defaults();
    const s = JSON.parse(raw);
    return { ...defaults(), ...s };
  } catch { return defaults(); }
}
function save() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) { console.warn("persist failed", e); }
}
function resetSeed() {
  if (!confirm("Reset everything back to Ryan's verified seed data? Your edits and OCR'd rows will be cleared.")) return;
  state = defaults(); forgetImages(); save(); renderAll();
}

// --- tabs -------------------------------------------------------------------
function initTabs() {
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((x) => x.classList.remove("active"));
    t.classList.add("active");
    document.getElementById("panel-" + t.dataset.tab).classList.add("active");
    if (t.dataset.tab === "track") renderTrack();
    if (t.dataset.tab === "review") renderReview();
    if (t.dataset.tab === "share") renderShare();
  }));
}

function goToTab(name) {
  const t = document.querySelector(`.tab[data-tab="${name}"]`);
  if (t) t.click();
}

// --- TRACK RECORD panel -----------------------------------------------------
function renderTrack() {
  const m = computeTrackRecord(state.trades, state.fees);
  const grid = document.getElementById("kpis");
  const matches = Math.abs(m.grossTotal - 20299.62) < 0.5;
  grid.innerHTML = [
    kpi("Realized P/L", money(state.fees.enabled ? m.total : m.grossTotal, true), m.total >= 0 ? "pos" : "neg", state.fees.enabled ? "net of fees" : "gross"),
    kpi("Win Rate", m.winRate != null ? m.winRate + "%" : "—", "", `${m.wins}W · ${m.losses}L`),
    kpi("Profit Factor", m.profitFactor != null ? m.profitFactor.toFixed(2) : "—", "gold", "gross win ÷ gross loss"),
    kpi("Closed Trades", m.n, "", `${m.firstDate} → ${m.lastDate}`),
    kpi("Avg Win", money(m.avgWin), "pos"),
    kpi("Avg Loss", money(m.avgLoss), "neg"),
    kpi("Best", m.best ? money(m.best.pl, true) : "—", "pos", m.best ? m.best.ticker : ""),
    kpi("Worst", m.worst ? money(m.worst.pl, true) : "—", "neg", m.worst ? m.worst.ticker : ""),
  ].join("");

  document.getElementById("seed-check").innerHTML = matches
    ? `<span class="ok">✓ reconciles to verified seed</span> +$20,299.62 · 73.1% · 5.18 PF`
    : `<span class="warn">edited</span> gross now ${money(m.grossTotal, true)}`;

  // equity curve
  const tipBox = document.getElementById("eq-tip");
  drawEquityCurve(document.getElementById("equity"), m.equity, (p, e) => {
    if (!p) { tipBox.style.opacity = 0; return; }
    tipBox.style.opacity = 1;
    tipBox.innerHTML = `<b>${p.ticker}</b> ${money(p.pl, true)}<span>equity ${money(p.equity)} · ${p.date}</span>`;
    const r = document.getElementById("equity").getBoundingClientRect();
    tipBox.style.left = Math.min(e.clientX - r.left + 14, r.width - 150) + "px";
  });

  drawStrategyBars(document.getElementById("stratbars"), m.strategies);

  // closed trades table
  const tb = document.querySelector("#trades-table tbody");
  const rows = [...m.trades].sort((a, b) => String(b.date_closed).localeCompare(String(a.date_closed)));
  tb.innerHTML = rows.map((t) => {
    const v = state.fees.enabled ? t.plNet : t.gross;
    return `<tr>
      <td class="mono">${t.date_closed}</td>
      <td class="mono">${t.date_opened || "—"}</td>
      <td class="tk">${t.ticker}</td>
      <td>${t.strategy}</td>
      <td>${t.type ? `<span class="chip ${t.type}">${t.type}</span>` : ""}</td>
      <td class="mono r ${v >= 0 ? "pos" : "neg"}">${money(v, true)}</td>
      <td class="note">${escapeHtml(t.notes || "")}</td>
    </tr>`;
  }).join("");
  document.getElementById("trades-count").textContent = m.n;
}

function kpi(label, val, cls = "", sub = "") {
  return `<div class="kpi"><div class="kpi-v ${cls}">${val}</div><div class="kpi-l">${label}</div>${sub ? `<div class="kpi-s">${sub}</div>` : ""}</div>`;
}

// --- LIVE BOOK panel --------------------------------------------------------
function renderBook() {
  const book = state.openBook;
  const tb = document.querySelector("#book-table tbody");
  tb.innerHTML = book.map((o, i) => bookRow(o, i)).join("");
  document.getElementById("book-count").textContent = book.length;

  // wire editable cells
  tb.querySelectorAll("[data-edit]").forEach((cell) => {
    cell.addEventListener("blur", () => commitBookEdit(cell));
    cell.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); cell.blur(); } });
  });
  tb.querySelectorAll("select[data-field]").forEach((sel) => {
    sel.addEventListener("change", () => {
      const i = +sel.closest("tr").dataset.i;
      state.openBook[i][sel.dataset.field] = sel.value;
      save(); renderSummary();
    });
  });

  renderSummary();
}

function bookRow(o, i) {
  const reviewed = o.needsReview ? " review" : "";
  const riskDerived = o.risk_type_source === "derived";
  return `<tr data-i="${i}" class="${reviewed.trim()}">
    <td class="desc" data-edit data-field="trade_description" contenteditable="true">${escapeHtml(o.trade_description || "")}</td>
    <td class="mono r pos" data-edit data-field="credit_rcvd" contenteditable="true">${moneyInt(o.credit_rcvd)}</td>
    <td class="mono r neg" data-edit data-field="debit_paid" contenteditable="true">${moneyInt(o.debit_paid)}</td>
    <td class="mono r" data-edit data-field="max_profit" contenteditable="true">${moneyInt(o.max_profit)}</td>
    <td class="mono r" data-edit data-field="max_loss" contenteditable="true">${moneyInt(o.max_loss)}</td>
    <td class="mono r" data-edit data-field="bp_usd" contenteditable="true">${moneyInt(o.bp_usd)}</td>
    <td class="mono r dim">${o.bp_pct != null ? o.bp_pct + "%" : ""}</td>
    <td>${selectCell(i, "position_type", o.position_type, [["Core", "Core"], ["Supp", "Supp"]])}</td>
    <td>${selectCell(i, "risk_type", o.risk_type, [["Def", "Def"], ["Undef", "Undef"]])}${riskDerived ? '<span class="der" title="auto-derived">·d</span>' : ""}</td>
    <td class="mono r dim">${o.date_opened || ""}</td>
  </tr>`;
}

function selectCell(i, field, val, opts) {
  const cls = field === "position_type" ? (val === "Core" ? "core" : "supp") : (val === "Undef" ? "undef" : "def");
  const o = opts.map(([v, l]) => `<option value="${v}" ${v === val ? "selected" : ""}>${l}</option>`).join("");
  return `<select class="pillsel ${cls}" data-field="${field}">${o}<option value="" ${!val ? "selected" : ""}>—</option></select>`;
}

function commitBookEdit(cell) {
  const i = +cell.closest("tr").dataset.i;
  const f = cell.dataset.field;
  let txt = cell.textContent.trim();
  const o = state.openBook[i];
  if (["credit_rcvd", "debit_paid", "max_profit", "max_loss", "bp_usd"].includes(f)) {
    if (txt === "∞") o[f] = "inf";
    else if (txt === "") o[f] = null;
    else o[f] = Number(txt.replace(/[,$]/g, "")) || null;
  } else {
    o[f] = txt;
    if (f === "trade_description" && !o.risk_type) {
      const d = deriveRiskType(txt);
      if (d) { o.risk_type = d; o.risk_type_source = "derived"; }
    }
  }
  // editing a cell inline also resolves any pending review item for it
  (state.review || []).forEach((it) => { if (it.rowId === o.id && it.field === f) { it.confirmed = true; it.value = o[f]; } });
  if (!(state.review || []).some((it) => it.rowId === o.id && !it.confirmed)) delete o.needsReview;
  save(); renderBook(); refreshReviewUI();
}

function renderSummary() {
  const s = state.summary || {};
  const pm = s.position_mix || {};
  const bp = s.buying_power || {};
  const derived = deriveBookSummary(state.openBook);

  drawDonut(document.getElementById("mix-core"), [
    { pct: pm.core_pct ?? derived.core_pct ?? 0, color: BLUE },
    { pct: pm.supplemental_pct ?? derived.supplemental_pct ?? 0, color: VIOLET },
  ]);
  drawDonut(document.getElementById("mix-risk"), [
    { pct: pm.defined_pct ?? derived.defined_pct ?? 0, color: POS },
    { pct: pm.undefined_pct ?? derived.undefined_pct ?? 0, color: GOLD },
  ]);

  document.getElementById("mix-legend").innerHTML = `
    <div class="lg"><i style="background:${BLUE}"></i>Core ${fmtp(pm.core_pct ?? derived.core_pct)}</div>
    <div class="lg"><i style="background:${VIOLET}"></i>Supp ${fmtp(pm.supplemental_pct ?? derived.supplemental_pct)}</div>
    <div class="lg"><i style="background:${POS}"></i>Defined ${fmtp(pm.defined_pct ?? derived.defined_pct)}</div>
    <div class="lg"><i style="background:${GOLD}"></i>Undef ${fmtp(pm.undefined_pct ?? derived.undefined_pct)}</div>`;

  document.getElementById("bp-gauges").innerHTML =
    gaugeHtml("BP Target", bp.bp_target_pct, BLUE) +
    gaugeHtml("BP Usage", bp.bp_usage_pct, GOLD) +
    gaugeHtml("Trading Usage", bp.trading_usage_pct, VIOLET) +
    gaugeHtml("Stock Usage", bp.stock_usage_pct, BLUE) +
    `<div class="bp-foot">Total BP committed (book): <b>${money(derived.totalBp)}</b></div>`;
}
function fmtp(v) { return v != null ? v + "%" : "—"; }

// --- MONITOR panel ----------------------------------------------------------
function renderMonitor() {
  const tb = document.querySelector("#monitor-table tbody");
  if (!state.monitor.length) {
    tb.innerHTML = `<tr><td colspan="3" class="empty">Drop the dark "Active / Positions Monitor" screenshots (Type E) to populate live unrealized P/L. Type E parsing is beta — a rough cross-check only.</td></tr>`;
    return;
  }
  tb.innerHTML = state.monitor.map((r) => `<tr>
    <td class="tk">${escapeHtml(r.symbol)}</td>
    <td class="mono r ${r.plOpen >= 0 ? "pos" : "neg"}">${money(r.plOpen, true)}</td>
    <td class="note dim">${escapeHtml(r.raw || "")}</td>
  </tr>`).join("");
}

// --- FEE config -------------------------------------------------------------
function initFees() {
  const f = state.fees;
  document.getElementById("fee-enabled").checked = f.enabled;
  document.getElementById("fee-open").value = f.perContractOpen;
  document.getElementById("fee-close").value = f.perContractClose;
  document.getElementById("fee-clear").value = f.clearingReg;
  const sync = () => {
    state.fees.enabled = document.getElementById("fee-enabled").checked;
    state.fees.perContractOpen = +document.getElementById("fee-open").value || 0;
    state.fees.perContractClose = +document.getElementById("fee-close").value || 0;
    state.fees.clearingReg = +document.getElementById("fee-clear").value || 0;
    document.getElementById("fee-note").textContent = state.fees.enabled
      ? "Showing NET of fees. Estimated per-leg; not from broker statements."
      : "OFF — numbers are gross, exactly as Ryan reported. Toggle to model fees.";
    save(); renderTrack();
  };
  ["fee-enabled", "fee-open", "fee-close", "fee-clear"].forEach((id) => document.getElementById(id).addEventListener("input", sync));
  sync();
}

// --- OCR ingest -------------------------------------------------------------
let monitorParts = [];

function initIngest() {
  const dz = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  dz.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => handleFiles([...e.target.files]));
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("over"); }));
  dz.addEventListener("drop", (e) => handleFiles([...e.dataTransfer.files].filter((f) => f.type.startsWith("image/"))));
  window.addEventListener("paste", (e) => {
    const imgs = [...(e.clipboardData?.items || [])].filter((i) => i.type.startsWith("image/")).map((i) => i.getAsFile());
    if (imgs.length) handleFiles(imgs);
  });
  document.getElementById("monitor-merge").addEventListener("click", () => {
    if (!monitorParts.length) return;
    state.monitor = mergeMonitorRows(monitorParts);
    monitorParts = [];
    save(); renderMonitor();
    logLine(`Merged ${state.monitor.length} de-duped monitor rows.`, "ok");
  });
}

async function handleFiles(files) {
  if (!files.length) return;
  const log = document.getElementById("ocr-log");
  log.classList.add("show");
  for (const file of files) {
    logLine(`Reading ${file.name || "pasted image"}…`, "work");
    try {
      const res = await processScreenshot(file, (m) => {
        if (m.status && m.progress != null) setProgress(`${m.status} ${(m.progress * 100) | 0}%`);
      });
      ingestResult(res, file.name);
    } catch (err) {
      logLine(`✗ ${file.name}: ${err.message}`, "err");
    }
  }
  setProgress("");
}

function ingestResult(res, name) {
  const flagTxt = (res.flags && res.flags.length) ? " — " + res.flags.join(" ") : "";
  const addReview = (items) => { if (items && items.length) { state.review.push(...items); } };
  if (res.layout === "spreadsheet") {
    if (res.positions.length) {
      // merge: replace book with OCR'd rows (user's authoritative current sheet)
      state.openBook = res.positions.map((p) => ({ ...p, bp_pct: p.bp_pct ?? null }));
      addReview(res.reviewItems);
      save(); renderBook(); refreshReviewUI();
      const nrev = (res.reviewItems || []).length;
      logLine(`✓ ${name}: Type A spreadsheet → ${res.positions.length} positions loaded${nrev ? `, ${nrev} cell(s) to confirm` : ""}.${flagTxt}`, nrev ? "warn" : "ok");
    } else logLine(`✗ ${name}: Type A detected but grid not segmented.${flagTxt}`, "err");
  } else if (res.layout === "order_chains") {
    if (res.bookable) {
      state.trades.push({
        id: res.tradeId || ("ocr-" + Math.random().toString(36).slice(2, 8)),
        date_opened: "", date_closed: new Date().toISOString().slice(0, 10),
        ticker: res.ticker || "?", strategy: res.strategy || "Uncategorized",
        type: "", pl: res.total_pl, notes: "OCR'd CLSD chain" + flagTxt, src: "ocr",
      });
      addReview(res.reviewItems);
      save(); renderTrack(); refreshReviewUI();
      logLine(`✓ ${name}: ${res.ticker || "?"} CLSD chain → realized ${money(res.total_pl, true)} booked.${flagTxt}`, "ok");
    } else {
      logLine(`• ${name}: order chain not booked (${res.is_closed === false ? "still open" : "status unclear"}).${flagTxt}`, "warn");
    }
  } else if (res.layout === "monitor") {
    monitorParts.push(res);
    document.getElementById("monitor-merge").classList.add("show");
    logLine(`• ${name}: Type E monitor part (${res.rows.length} rows). Drop all 3, then "Merge stitched".${flagTxt}`, "warn");
  } else {
    logLine(`• ${name}: ${res.layout} — skipped (context only).${flagTxt}`, "warn");
  }
}

function logLine(msg, cls) {
  const log = document.getElementById("ocr-log");
  const d = document.createElement("div");
  d.className = "ll " + (cls || "");
  d.innerHTML = escapeHtml(msg);
  log.insertBefore(d, log.firstChild);
}
function setProgress(t) { document.getElementById("ocr-progress").textContent = t; }

// --- util -------------------------------------------------------------------
function escapeHtml(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

// --- REVIEW panel + provisional ribbon -------------------------------------
function renderReview() {
  const c = document.getElementById("review-queue");
  if (!c) return;
  renderQueue(c, state, { save, refresh: refreshReviewUI });
}

// Keep the badge, ribbon, and (if open) the queue + dashboards in sync.
function refreshReviewUI() {
  const ct = reviewCounts(state);
  // nav badge
  const badge = document.getElementById("review-badge");
  if (badge) {
    badge.textContent = ct.total;
    badge.classList.toggle("show", ct.total > 0);
    badge.classList.toggle("must", ct.must > 0);
  }
  // provisional ribbon
  const ribbon = document.getElementById("provisional");
  if (ribbon) {
    ribbon.classList.toggle("show", ct.total > 0);
    if (ct.total > 0) ribbon.querySelector("b").textContent = ct.total;
  }
  // if review tab is open, re-render the queue
  const active = document.querySelector(".tab.active");
  if (active && active.dataset.tab === "review") renderReview();
  // book/track rows may have changed via confirmations
  renderBook(); renderTrack();
}

// --- SHARE panel: Weekly Card + JSON backup --------------------------------
function renderShare() {
  const p = state.cardPrefs || (state.cardPrefs = { handle: "@yourhandle", showDollars: false, weekEnding: "" });
  const handle = document.getElementById("card-handle");
  const dollars = document.getElementById("card-dollars");
  const week = document.getElementById("card-week");
  if (handle) handle.value = p.handle || "";
  if (dollars) dollars.checked = !!p.showDollars;
  if (week) week.value = p.weekEnding || "";
  // backup status
  const bs = document.getElementById("backup-status");
  if (bs) {
    const d = daysSinceBackup();
    bs.textContent = d === Infinity ? "No JSON backup yet." : `Last JSON backup ${d < 1 ? "today" : Math.floor(d) + "d ago"}.`;
    bs.classList.toggle("nudge", shouldNudge());
  }
  buildCardPreview();
}

function cardOpts() {
  const p = state.cardPrefs;
  return {
    handle: p.handle, weekEnding: p.weekEnding, showDollars: p.showDollars,
    metrics: computeTrackRecord(state.trades, state.fees), provisional: reviewCounts(state).total,
  };
}

async function buildCardPreview() {
  const wrap = document.getElementById("card-preview");
  if (!wrap) return;
  const cv = await renderCardCanvas(cardOpts(), 1);
  cv.style.width = "100%"; cv.style.height = "auto"; cv.style.display = "block";
  wrap.innerHTML = "";
  wrap.appendChild(cv);
  wrap.style.height = "auto";
}

async function exportCard(action) {
  const status = document.getElementById("card-status");
  status.textContent = "Rendering…";
  try {
    const ct = reviewCounts(state);
    const cv = await renderCardCanvas(cardOpts(), 2);
    if (action === "copy") {
      await copyCanvasToClipboard(cv);
      status.textContent = ct.total ? `Copied (⚠ ${ct.total} cells still unconfirmed).` : "Copied to clipboard ✓";
    } else {
      downloadCanvas(cv, "track-record-card.png");
      status.textContent = "Downloaded ✓";
    }
  } catch (err) {
    status.textContent = "✗ " + err.message + " — try Download instead.";
  }
}

function initShare() {
  const onPref = () => {
    state.cardPrefs.handle = document.getElementById("card-handle").value || "@yourhandle";
    state.cardPrefs.showDollars = document.getElementById("card-dollars").checked;
    state.cardPrefs.weekEnding = document.getElementById("card-week").value || "";
    save(); buildCardPreview();
  };
  ["card-handle", "card-dollars", "card-week"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", onPref);
  });
  document.getElementById("card-copy").addEventListener("click", () => exportCard("copy"));
  document.getElementById("card-download").addEventListener("click", () => exportCard("download"));
  document.getElementById("json-export").addEventListener("click", () => { exportJson(state); renderShare(); });
  document.getElementById("json-import").addEventListener("click", () => document.getElementById("json-file").click());
  document.getElementById("json-file").addEventListener("change", async (e) => {
    const f = e.target.files[0]; if (!f) return;
    const txt = await readFileText(f);
    const r = parseImport(txt);
    const status = document.getElementById("json-status");
    if (!r.ok) { status.textContent = "✗ " + r.error; return; }
    if (!confirm("Replace current data with the imported backup?")) return;
    state = { ...defaults(), ...r.state }; forgetImages(); save(); renderAll();
    status.textContent = "Imported ✓" + (r.warning ? " (" + r.warning + ")" : "");
  });
}

// --- CSV export (build.py interop) -----------------------------------------
function exportCsv() {
  const ct = reviewCounts(state);
  if (ct.total && !confirm(`${ct.total} cell(s) are still unconfirmed (provisional). Export anyway?`)) return;
  const m = computeTrackRecord(state.trades, state.fees);
  const head = "date_closed,date_opened,ticker,strategy,type,realized_pl,notes";
  const rows = m.trades.map((t) => [t.date_closed, t.date_opened, t.ticker, t.strategy, t.type, state.fees.enabled ? t.plNet : t.gross, `"${(t.notes || "").replace(/"/g, '""')}"`].join(","));
  const blob = new Blob([head + "\n" + rows.join("\n")], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "tt-track-record.csv";
  a.click();
}

function renderAll() {
  renderTrack(); renderBook(); renderMonitor(); initFees(); refreshReviewUI();
}

// --- boot -------------------------------------------------------------------
function boot() {
  initTabs();
  initIngest();
  initShare();
  document.getElementById("reset-seed").addEventListener("click", resetSeed);
  document.getElementById("export-csv").addEventListener("click", exportCsv);
  const goRev = document.getElementById("provisional-go");
  if (goRev) goRev.addEventListener("click", () => goToTab("review"));
  renderAll();
  window.addEventListener("resize", () => {
    const a = document.querySelector(".tab.active");
    if (!a) return;
    if (a.dataset.tab === "track") renderTrack();
    if (a.dataset.tab === "share") buildCardPreview();
  });
  // register service worker (scoped to this subpath)
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js", { scope: "./" }).catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", boot);
