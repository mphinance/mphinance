// engine.js — realized-PnL + track-record stats.
// Ported (semantics frozen) from the borrowed TS journal engine
//   - pnl.ts::computeRealizedPnl
//   - stats.ts::winRate / sumPnl / group-aggregate
//   - rowMapper.ts::numOrNull / strOrNull (tolerant OCR coercion)
// plus the equity-curve / avg-win-loss / profit-factor recipe from INTEGRATION_BRIEF.md,
// and build.py::compute() which reconciles the seed to +$20,299.62 / 73.1% / 5.18.

const OPTION_MULTIPLIER = 100;

// --- tolerant coercion (OCR + Postgres-string safe) -------------------------
export function numOrNull(v) {
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  let s = String(v).trim().replace(/\$/g, "").replace(/,/g, "");
  if (s === "" || s === "-" || s === "—") return null;
  let neg = false;
  if (s.startsWith("(") && s.endsWith(")")) { neg = true; s = s.slice(1, -1); }
  const x = parseFloat(s);
  if (!Number.isFinite(x)) return null;
  return neg ? -Math.abs(x) : x;
}

export function strOrNull(v) {
  if (v === null || v === undefined) return null;
  const s = String(v).trim();
  return s === "" ? null : s;
}

// --- realized P&L for a single per-leg row (BTO/STO/BTC/STC mapped to side) --
// side='short' profits when entry>exit; long profits when exit>entry. ×100 for options.
export function computeRealizedPnl(t) {
  if (t.status !== "closed") return null;
  const entry = numOrNull(t.entry_price);
  const exit_ = numOrNull(t.exit_price);
  const size = numOrNull(t.size);
  if (entry === null || exit_ === null || size === null) return null;
  const directional = t.side === "short" ? entry - exit_ : exit_ - entry;
  const multiplier = t.instrument_type === "option" ? OPTION_MULTIPLIER : 1;
  return directional * size * multiplier;
}

// Net a chain (array of leg rows sharing a chain) → realized total (null if any leg open).
export function chainRealizedPnl(legs) {
  let total = 0, sawClosed = false;
  for (const leg of legs) {
    const p = computeRealizedPnl(leg);
    if (p === null) return null; // an open leg => chain not fully realized
    total += p; sawClosed = true;
  }
  return sawClosed ? total : null;
}

// --- fee model (default no-op) ---------------------------------------------
// legCount is # of contract-legs traded (open + close). Off by default.
export function applyFees(grossPnl, legCount, fees) {
  if (!fees || !fees.enabled) return grossPnl;
  const per = (fees.perContractOpen || 0) + (fees.perContractClose || 0) + (fees.clearingReg || 0);
  return grossPnl - per * (legCount || 1);
}

// --- track record over a list of CLOSED trade records {pl, strategy, ticker, date_closed} ---
export function computeTrackRecord(closedTrades, fees) {
  const closed = closedTrades
    .filter((t) => numOrNull(t.pl) !== null)
    .map((t) => {
      const gross = numOrNull(t.pl);
      const net = applyFees(gross, t.legCount || 2, fees);
      return { ...t, gross, plNet: net };
    })
    .sort((a, b) => String(a.date_closed || "9999").localeCompare(String(b.date_closed || "9999")));

  const useNet = !!(fees && fees.enabled);
  const val = (t) => (useNet ? t.plNet : t.gross);

  const pls = closed.map(val);
  const wins = pls.filter((p) => p > 0);
  const losses = pls.filter((p) => p < 0);
  const grossWin = round2(sum(wins));
  const grossLoss = round2(sum(losses));
  const n = pls.length;

  // equity curve: cumulative by close date (realized booked at exit)
  let run = 0;
  const equity = closed.map((t) => {
    run += val(t);
    return { date: t.date_closed, equity: round2(run), ticker: t.ticker, pl: round2(val(t)) };
  });

  // per-strategy aggregation (group → {count, winRate, total})
  const stratMap = new Map();
  for (const t of closed) {
    const k = t.strategy || "Uncategorized";
    const s = stratMap.get(k) || { strategy: k, count: 0, wins: 0, total: 0 };
    s.count += 1;
    if (val(t) > 0) s.wins += 1;
    s.total += val(t);
    stratMap.set(k, s);
  }
  const strategies = [...stratMap.values()]
    .map((s) => ({ ...s, total: round2(s.total), winRate: s.count ? round1((100 * s.wins) / s.count) : 0 }))
    .sort((a, b) => b.total - a.total);

  const best = closed.length ? closed.reduce((a, b) => (val(b) > val(a) ? b : a)) : null;
  const worst = closed.length ? closed.reduce((a, b) => (val(b) < val(a) ? b : a)) : null;

  return {
    total: round2(sum(pls)),
    grossTotal: round2(sum(closed.map((t) => t.gross))),
    n,
    wins: wins.length,
    losses: losses.length,
    winRate: n ? round1((100 * wins.length) / n) : null,
    avgWin: wins.length ? round2(grossWin / wins.length) : null,
    avgLoss: losses.length ? round2(grossLoss / losses.length) : null,
    grossWin,
    grossLoss,
    profitFactor: grossLoss !== 0 ? round2(grossWin / -grossLoss) : null,
    expectancy: n ? round2(sum(pls) / n) : null,
    equity,
    strategies,
    best: best ? { pl: round2(val(best)), ticker: best.ticker } : null,
    worst: worst ? { pl: round2(val(worst)), ticker: worst.ticker } : null,
    firstDate: closed.length ? closed[0].date_closed : "",
    lastDate: closed.length ? closed[closed.length - 1].date_closed : "",
    trades: closed,
    useNet,
  };
}

// --- portfolio summary from the open book (derives mix if not supplied) ------
export function deriveBookSummary(openBook) {
  // crude mix derivation as a cross-check when no summary card is OCR'd.
  let core = 0, supp = 0, undef = 0, def = 0, bp = 0;
  for (const o of openBook) {
    const w = numOrNull(o.bp_usd) || 0;
    bp += w;
    if (/^core/i.test(o.position_type || "")) core += w; else if (/^supp/i.test(o.position_type || "")) supp += w;
    if (/^undef/i.test(o.risk_type || "")) undef += w; else if (/^def/i.test(o.risk_type || "")) def += w;
  }
  const pct = (a, b) => (a + b ? round1((100 * a) / (a + b)) : null);
  return {
    totalBp: round2(bp),
    core_pct: pct(core, supp),
    supplemental_pct: pct(supp, core),
    undefined_pct: pct(undef, def),
    defined_pct: pct(def, undef),
  };
}

// --- helpers ----------------------------------------------------------------
function sum(a) { return a.reduce((x, y) => x + y, 0); }
function round2(n) { return Math.round((n + Number.EPSILON) * 100) / 100; }
function round1(n) { return Math.round((n + Number.EPSILON) * 10) / 10; }

// --- risk-type auto-derivation (matches Ryan's own sheet; port of tt_ocr.py) -
const DEFINED_HINTS = ["spread", "butterfly", "condor", "zebra", "diagonal", "covered", "long call", "long put", "leaps", "super bull"];
const UNDEFINED_HINTS = ["short put", "short call", "strangle", "straddle"];

export function deriveRiskType(description) {
  if (!description) return null;
  const d = description.toLowerCase();
  // long futures / stock (no premium cap) → undefined
  if (/\/\w+.*\blong\b/.test(d) && !d.includes("call") && !d.includes("put")) return "Undef";
  const hasNaked = UNDEFINED_HINTS.some((h) => d.includes(h)) && !d.includes("spread");
  const hasDefined = DEFINED_HINTS.some((h) => d.includes(h));
  if (hasNaked && !hasDefined) return "Undef";
  if (hasDefined && !hasNaked) return "Def";
  if (hasNaked && hasDefined) return "Undef"; // mixed w/ a naked short leg (e.g. Super Bull)
  return null;
}

// OCC symbol build/parse (port of marks.ts::buildOccSymbol + inverse)
export function buildOccSymbol(ticker, expiry, type, strike) {
  const d = new Date(expiry);
  const yy = String(d.getUTCFullYear()).slice(2);
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const cp = type === "call" ? "C" : "P";
  const k = String(Math.round(strike * 1000)).padStart(8, "0");
  return `${ticker.toUpperCase()}${yy}${mm}${dd}${cp}${k}`;
}
