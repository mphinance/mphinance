#!/usr/bin/env node
// stock-recap / gather.mjs
// Pulls every TraderDaddy Pro screener + flow + new CBOE option listings, plus
// TickerTrace 13F hedge-fund activity, builds a convergence-ranked shortlist,
// and writes a markdown report + raw JSON snapshots under runs/<timestamp>/.
//
// Auth: AGENT_API_KEY (read from repo-root .env_agent_api or env) for /api/agent/*.
// Screeners, options-listings and TickerTrace are public (no key needed).
// Runs on Node 18+ (uses global fetch). No external deps.

import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { detectDowntrendBreakout, detectSpring } from './detectors/downtrend.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

// ---- config ---------------------------------------------------------------
// Two TraderDaddy APIs, two keys, two auth schemes (hybrid — see SKILL.md):
//   NEW dev API (api.traderdaddy.pro/api/v1, X-API-Key td_live_*): screeners + flow.
//     Richer payloads (earningsDaysAway, perf3MPct, real flow aggregates) + bonus
//     /gex/:sym, /earnings, /market-stats.
//   OLD Railway API (Bearer, legacy key): chart-data (charts), options-listings
//     (CBOE), and the /api/agent/ticker/:sym technicals+options enrich — these are
//     NOT served by the new API with the new key, so they stay on the old base.
const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TD_NEW_BASE = process.env.TD_NEW_API_URL || 'https://api.traderdaddy.pro/api/v1';
const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
const TIMEOUT_MS = Number(process.env.RECAP_TIMEOUT_MS || 60000);
const SCREENER_CONCURRENCY = 4;
const SHORTLIST_SIZE = Number(process.env.RECAP_SHORTLIST || 15);

// Flow thresholds (the "biggest flows" filter)
const FLOW_MIN_SCORE = 70;
const FLOW_MIN_PREMIUM = 50000;
const FLOW_PAGES = 3;          // pageSize 100 each -> up to 300 alerts
const FLOW_PAGE_SIZE = 100;
// Weekly (market-closed) flow uses TIGHTER thresholds so the qualifying set is the
// few-hundred BIGGEST prints of the week — not a recent time-slice. The endpoint is
// time-ordered and ignores sort params, but at minScore85/$250k the whole week is
// ~240 rows (verified), fully covered by FLOW_PAGES*100. Page-1 aggregates carry the
// true week-wide bull/bear premium + largestTrades as a backstop.
const FLOW_WEEKLY_MIN_SCORE = 85;
const FLOW_WEEKLY_MIN_PREMIUM = 250000;
// Tier-3: 300-day OHLC for trendline detectors, GEX, earnings, RS-vs-SPY.
const OHLC_DAYS = 300;
const OHLC_MAX_NAMES = 40;
const EARNINGS_BLACKOUT_DAYS = 7;
const RS_SHORT = 20;
const RS_LONG = 60;
const ENABLE_GEX = process.env.RECAP_GEX !== '0';

// A ticker needs at least this many independent source-legs to make the shortlist.
const MIN_LEGS = 2;

// "Affordable" cutoff for the dedicated under-$N section (lower-priced names).
const MAX_AFFORDABLE_PRICE = Number(process.env.RECAP_MAX_PRICE || 100);

// ---- helpers --------------------------------------------------------------
function findRepoRoot(start) {
  let dir = start;
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(dir, '.env_agent_api')) || existsSync(join(dir, 'CLAUDE.md'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return resolve(SKILL_DIR, '../../..'); // best-effort
}

async function readKeyFile(name, envVar) {
  if (process.env[envVar]) return process.env[envVar].trim();
  const root = findRepoRoot(SKILL_DIR);
  const f = join(root, name);
  if (existsSync(f)) {
    const raw = (await readFile(f, 'utf8')).trim();
    // file may be a bare token or KEY=value (first line only)
    const first = raw.split(/\r?\n/)[0].trim();
    const m = first.match(/^[A-Z_]+=(.*)$/);
    return (m ? m[1] : first).trim();
  }
  return null;
}

// OLD Railway API key (Bearer) — charts, CBOE listings, ticker enrich.
async function loadAgentKey() { return readKeyFile('.env_agent_api', 'AGENT_API_KEY'); }
// NEW dev API key (X-API-Key td_live_*) — screeners + flow.
async function loadTdKey() { return readKeyFile('.env_td_api', 'TD_API_KEY'); }

// The Railway/edge WAF 403s requests carrying Node's default User-Agent, so we
// always present a browser-like UA. (curl works; bare `node-fetch` UA does not.)
const BASE_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  Accept: 'application/json',
};

async function getJson(url, { headers = {}, label = url } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: { ...BASE_HEADERS, ...headers }, signal: ctrl.signal });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { data = null; }
    if (!res.ok) return { ok: false, status: res.status, error: (data && data.error) || text.slice(0, 200), data };
    return { ok: true, status: res.status, data };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? `timeout after ${TIMEOUT_MS}ms` : e.message };
  } finally {
    clearTimeout(t);
  }
}

async function pool(items, size, fn) {
  const out = new Array(items.length);
  let i = 0;
  async function worker() {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx], idx);
    }
  }
  await Promise.all(Array.from({ length: Math.min(size, items.length) }, worker));
  return out;
}

const sym = (r) => (r && (r.symbol || r.ticker || r.Symbol || r.Ticker) || '').toString().toUpperCase();
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : (v == null ? null : Number(v)));
const fmt$ = (n) => {
  if (n == null || !Number.isFinite(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return `${n < 0 ? '-' : ''}$${(a / 1e9).toFixed(1)}B`;
  if (a >= 1e6) return `${n < 0 ? '-' : ''}$${(a / 1e6).toFixed(1)}M`;
  if (a >= 1e3) return `${n < 0 ? '-' : ''}$${(a / 1e3).toFixed(0)}K`;
  return `${n < 0 ? '-' : ''}$${a.toFixed(0)}`;
};
const pct = (n) => (n == null || !Number.isFinite(n) ? '—' : `${n > 0 ? '+' : ''}${n.toFixed(1)}%`);
// weightDelta is a fraction (0.011 = +1.1%) from the per-ticker feeds, but an
// aggregate sum across funds in cross-fund convergence — show each correctly.
const wfmt = (v) => {
  if (v == null || !Number.isFinite(v)) return '';
  return Math.abs(v) < 1 ? pct(v * 100) : `Δ${v > 0 ? '+' : ''}${v.toFixed(2)} agg`;
};
const convStr = (v) => (v == null ? '' : (typeof v === 'number' ? v.toFixed(0) : String(v)));
// TickerTrace feeds put the fund TICKERS in `funds` (an array) and the integer in
// `fundCount`. The old `funds ?? fundCount` always took the array (truthy) → NaN.
// Prefer the explicit count; fall back to the array length.
const fundCount = (r) => {
  const n = num(r.fundCount ?? r.providerCount);
  if (n != null && Number.isFinite(n)) return n;
  if (Array.isArray(r.funds)) return r.funds.length;
  if (Array.isArray(r.providers)) return r.providers.length;
  const f = num(r.funds ?? r.providers);
  return f != null && Number.isFinite(f) ? f : null;
};

// 300-day OHLC fetch (OLD Railway API, Bearer) — the candle array is `chartData`
// (NOT candles/data; mislabeling silently zeros the detectors).
async function fetchChart(t, days, oldAuth) {
  const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(t)}/chart-data?days=${days}`,
    { headers: oldAuth, label: `ohlc:${t}` });
  const rows = r.ok && r.data ? r.data.chartData : null;
  return Array.isArray(rows) && rows.length ? { meta: r.data, candles: rows } : null;
}
// trailing n-bar return % off a candle array (for RS-vs-SPY).
function retPct(cd, n) {
  if (!cd || cd.length <= n) return null;
  const a = num(cd.at(-1).close), b = num(cd.at(-1 - n).close);
  return (a != null && b) ? (a - b) / b * 100 : null;
}

// ---- timestamp / output dir ----------------------------------------------
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const stamp = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
const OUT_DIR = join(SKILL_DIR, 'runs', stamp);
const RAW_DIR = join(OUT_DIR, 'raw');

async function saveRaw(name, obj) {
  await writeFile(join(RAW_DIR, `${name}.json`), JSON.stringify(obj, null, 2));
}

// ---------------------------------------------------------------------------
async function main() {
  await mkdir(RAW_DIR, { recursive: true });
  const AGENT_KEY = await loadAgentKey();   // OLD Railway (Bearer): charts, CBOE, enrich
  const TD_KEY = await loadTdKey();         // NEW dev API (X-API-Key): screeners, flow
  const oldAuth = AGENT_KEY ? { Authorization: `Bearer ${AGENT_KEY}` } : {};
  const newAuth = TD_KEY ? { 'X-API-Key': TD_KEY } : {};
  const authHeaders = oldAuth; // back-compat alias for the old-base legs below
  const health = {}; // leg -> status string

  // Market status (new API) — drives market-aware health labels so a closed-market
  // run reads "market closed — N/A" instead of looking like a dead/bearish leg.
  const mktR = await getJson(`${TD_NEW_BASE}/market-stats`, { headers: newAuth });
  await saveRaw('market_stats', mktR.data ?? { error: mktR.error });
  const marketOpen = !!(mktR.ok && mktR.data && mktR.data.marketOpen);
  const lastSession = (mktR.ok && mktR.data && mktR.data.tradingDate) || null;

  // candidate registry: TICKER -> { legs:Set, screeners:[], tech:{}, flow:{}, inst:{}, cboe:false, reversal:{} }
  const reg = new Map();
  const cand = (t) => {
    if (!reg.has(t)) reg.set(t, { ticker: t, legs: new Set(), screeners: [], tech: null, flow: null, inst: null, cboe: false, reversal: null, watch: null });
    return reg.get(t);
  };

  // Momentum-chase screeners: their hits are recorded for context but do NOT add
  // a bullish convergence leg (they surface already-running names Mike won't chase).
  const CHASE_SCREENERS = new Set(['leveraged', 'volatility-surge']);

  // === 1. SCREENERS (new dev API) ==========================================
  const list = await getJson(`${TD_NEW_BASE}/screeners`, { headers: newAuth });
  let screenerIds = [];
  if (list.ok && list.data && Array.isArray(list.data.screeners)) {
    screenerIds = list.data.screeners.map((s) => ({ id: s.id, name: s.name }));
  } else {
    // fallback to known ids
    screenerIds = ['momentum', 'bullish-pullback', 'volatility-squeeze', 'small-cap', 'volatility-surge', 'gamma-scan', 'csp-wheel', 'leaps', 'leveraged', 'daily-cuts'].map((id) => ({ id, name: id }));
  }

  const screenerResults = {};
  await pool(screenerIds, SCREENER_CONCURRENCY, async ({ id, name }) => {
    const r = await getJson(`${TD_NEW_BASE}/screeners/${id}/run`, { headers: newAuth });
    const rows = r.ok && r.data ? (r.data.results || r.data.data || []) : [];
    screenerResults[id] = { name, ok: r.ok, count: rows.length, error: r.error, rows };
    await saveRaw(`screener_${id}`, r.data ?? { error: r.error });
    if (!r.ok) return;
    const isChase = CHASE_SCREENERS.has(id);
    for (const row of rows) {
      const t = sym(row);
      if (!t) continue;
      const c = cand(t);
      c.screeners.push({ id, name, chase: isChase, grade: row.metrics?.entryGrade ?? null, score: row.metrics?.entryScore ?? null });
      // chase-screener hits are context only — they don't earn a convergence leg
      if (!isChase) c.legs.add('screener');
      // capture technicals (prefer momentum/bullish-pullback which carry the full stack)
      const m = row.metrics || {};
      const tech = {
        price: num(row.price), changePct: num(row.changePct),
        rsi: num(row.rsi), adx: num(row.adx), stochK: num(row.stochK), atr: num(row.atr),
        sector: m.sector ?? row.sector ?? null,
        entryGrade: m.entryGrade ?? null, entryScore: num(m.entryScore),
        stochCrossover: m.stochCrossover ?? null, rsiZone: m.rsiZone ?? null,
        pullbackDepth: m.pullbackDepth ?? null, trendStrength: m.trendStrength ?? null,
        relativeVolume: num(m.relativeVolume), priceVsEma21Pct: num(m.priceVsEma21Pct),
        perfWeekPct: num(m.perfWeekPct), perfMonthPct: num(m.perfMonthPct),
        src: id,
      };
      const isPullback = id === 'momentum' || id === 'bullish-pullback';
      if (!c.tech || (isPullback && c.tech.src !== 'momentum' && c.tech.src !== 'bullish-pullback') ||
          (c.tech.rsi == null && tech.rsi != null)) {
        c.tech = tech;
      }
      // momentum-pullback reversal detection (the user's edge).
      // NOTE: we deliberately do NOT gate on the screener's stochCrossover flag —
      // it's ~always "No" because the pullback screeners surface names while still
      // IN the pullback, before the cross prints. We detect the TURN from raw
      // fields instead: stoch climbing out of oversold + price reclaiming the
      // 21-EMA + bullish RSI / A-B grade. (stochCrossover still counts if present.)
      if (isPullback) {
        const cross = (m.stochCrossover || '').toLowerCase() === 'yes';
        const sk = num(row.stochK);
        const bullZone = /bull/i.test(m.rsiZone || '');
        const grade = (m.entryGrade || '').toUpperCase();
        const goodGrade = /A|B/.test(grade.replace(/[^A-Z]/g, ''));
        const vsEma21 = num(m.priceVsEma21Pct);
        const turningUp = sk != null && sk >= 12 && sk <= 45;   // out of oversold, not yet hot
        const reclaiming = vsEma21 != null && vsEma21 >= -1;     // at/above the 21-EMA = the turn
        const reversing = turningUp && reclaiming && (bullZone || goodGrade);
        if (reversing || cross) {
          c.reversal = {
            reversing, crossover: cross, stochK: sk, rsiZone: m.rsiZone ?? null,
            grade: m.entryGrade ?? null, entryScore: num(m.entryScore),
            pullbackDepth: m.pullbackDepth ?? null, priceVsEma21Pct: vsEma21,
          };
        }
      }
    }
  });
  const screenerOk = Object.values(screenerResults).filter((s) => s.ok).length;
  health.screeners = `${screenerOk}/${screenerIds.length} ran`;

  // === 2. FLOW (biggest flows + smart money — new dev API) =================
  // Window: intraday "today" when the market is open; weekly "week" on a closed
  // market (weekend/holiday) so the leg isn't dark. The endpoint is TIME-ordered
  // and silently ignores sort params (sortBy/sort/order are byte-identical), so a
  // naive 300-row page grab on a 14k-row week would be a recent slice, NOT the
  // biggest prints. FIX: on the weekly window we tighten the thresholds
  // (minScore>=85, minPremium>=$250k) so the qualifying universe shrinks to ~240
  // rows — fully covered by FLOW_PAGES*100 — AND we capture page-1 `aggregates`
  // (true week-wide bull/bear premium + largestTrades) as the authoritative totals
  // and a fold-in backstop for any giant print pagination missed.
  const flowWindow = marketOpen ? 'today' : (process.env.RECAP_FLOW_WINDOW || 'week');
  const isWeekly = flowWindow !== 'today' && flowWindow !== 'yesterday';
  const flowMinScore = isWeekly ? FLOW_WEEKLY_MIN_SCORE : FLOW_MIN_SCORE;
  const flowMinPrem = isWeekly ? FLOW_WEEKLY_MIN_PREMIUM : FLOW_MIN_PREMIUM;
  let flowAgg2top = null;
  const flowAlerts = [];
  let flowAuthFail = false;
  let flowTotal = null, flowMaxPages = FLOW_PAGES;
  for (let p = 1; p <= flowMaxPages; p++) {
    const r = await getJson(
      `${TD_NEW_BASE}/unusual-activity?minScore=${flowMinScore}&minPremium=${flowMinPrem}&timeFrame=${flowWindow}&page=${p}&pageSize=${FLOW_PAGE_SIZE}`,
      { headers: newAuth });
    if (!r.ok) { flowAuthFail = true; if (p === 1) await saveRaw('flow_error', { error: r.error, status: r.status }); break; }
    const rows = (r.data && r.data.data) || [];
    if (p === 1) {
      await saveRaw('flow_page1', r.data);
      if (r.data && r.data.aggregates) flowAgg2top = r.data.aggregates;
      flowTotal = num(r.data && r.data.total);
      // The feed is TIME-ordered, so capturing the BIGGEST prints (not a recent
      // slice) means paging the whole qualifying set. Bump the page budget to cover
      // `total`, capped at 10 pages (1000 rows) so a noisy week can't run away.
      if (flowTotal != null && flowTotal > FLOW_PAGES * FLOW_PAGE_SIZE) {
        flowMaxPages = Math.min(10, Math.ceil(flowTotal / FLOW_PAGE_SIZE));
      }
    }
    flowAlerts.push(...rows);
    if (rows.length < FLOW_PAGE_SIZE) break;
  }
  // if the qualifying universe still exceeds what we paged, the per-ticker table is
  // a recent slice (header aggregates remain whole-week correct) — flag it.
  const flowUndercovered = flowTotal != null && flowTotal > flowMaxPages * FLOW_PAGE_SIZE;
  // repeats (institutional-conviction repeated strikes)
  const repeatsR = await getJson(`${TD_NEW_BASE}/unusual-activity/repeats?hours=24&limit=50`, { headers: newAuth });
  const repeats = (repeatsR.ok && repeatsR.data && (repeatsR.data.repeatFlows || repeatsR.data.repeats)) || [];
  await saveRaw('flow_repeats', repeatsR.data ?? { error: repeatsR.error });

  // aggregate flow per ticker
  const flowAgg = new Map();
  for (const a of flowAlerts) {
    const t = sym(a); if (!t) continue;
    if (!flowAgg.has(t)) flowAgg.set(t, { ticker: t, bullPrem: 0, bearPrem: 0, count: 0, maxScore: 0, instAlpha: false, repeat: 0, topTradeType: null, topPrem: 0, conviction: null });
    const g = flowAgg.get(t);
    const prem = num(a.premium) || 0;
    const bull = /bull/i.test(a.sentiment || a.sentimentLabel || '');
    const bear = /bear/i.test(a.sentiment || a.sentimentLabel || '');
    if (bull) g.bullPrem += prem; else if (bear) g.bearPrem += prem;
    g.count++;
    g.maxScore = Math.max(g.maxScore, num(a.score) || 0);
    if (/institutional/i.test(a.tierDescription || '')) g.instAlpha = true;
    if (a.isRepeatFlow || (num(a.repeatCount) || 0) > 1) g.repeat = Math.max(g.repeat, num(a.repeatCount) || 1);
    if ((a.convictionLevel || '') && a.convictionLevel !== 'NORMAL') g.conviction = a.convictionLevel;
    if (prem > g.topPrem) { g.topPrem = prem; g.topTradeType = `${a.type} ${a.strike ?? ''} ${a.tradeType ?? ''}`.trim(); }
  }
  // BACKSTOP: fold the page-1 pre-ranked largestTrades so a giant print missed by
  // pagination still seeds its ticker. largestTrades carry no sentiment, so we use a
  // conservative CALL->bull / PUT->bear seed (only affects net for tickers NOT
  // already captured by a real per-row alert — and the whole ~240-row weekly set IS
  // captured, so this is a belt-and-suspenders safety net).
  const lastSessionDay = lastSession ? String(lastSession).slice(0, 10) : null;
  if (flowAgg2top && Array.isArray(flowAgg2top.largestTrades)) {
    for (const lt of flowAgg2top.largestTrades) {
      const t = sym(lt); if (!t) continue;
      const prem = num(lt.premium) || 0;
      if (!flowAgg.has(t)) {
        const isPut = /put/i.test(lt.type || '');
        flowAgg.set(t, { ticker: t, bullPrem: isPut ? 0 : prem, bearPrem: isPut ? prem : 0,
          count: 1, maxScore: flowMinScore, instAlpha: /block/i.test(lt.tradeType || ''), repeat: 0,
          topTradeType: `${lt.type || ''} ${lt.strike ?? ''} ${lt.tradeType ?? ''}`.trim(), topPrem: prem,
          conviction: null, fromBackstop: true, topDetectedAt: lt.detectedAt || null });
      } else {
        const g = flowAgg.get(t);
        if (prem > g.topPrem) { g.topPrem = prem; g.topTradeType = `${lt.type || ''} ${lt.strike ?? ''} ${lt.tradeType ?? ''}`.trim(); g.topDetectedAt = lt.detectedAt || null; }
      }
    }
  }
  for (const [t, g] of flowAgg) {
    g.net = g.bullPrem - g.bearPrem;
    g.dir = g.net > 0 ? 'Bullish' : (g.net < 0 ? 'Bearish' : 'Mixed');
    const meaningful = Math.abs(g.net) >= FLOW_MIN_PREMIUM && g.maxScore >= FLOW_MIN_SCORE;
    // join-freshness: intraday = always fresh; weekly = a net-bullish name (or one
    // whose biggest print landed in the last session) counts as a live join.
    g.fresh = isWeekly
      ? ((g.topDetectedAt && lastSessionDay && String(g.topDetectedAt).slice(0, 10) === lastSessionDay) || g.net > 0)
      : true;
    const c = cand(t); c.flow = g;
    // Only BULLISH net flow is a convergence leg (this is a long-idea finder).
    // Meaningful bearish flow is tracked as a conflict, never as agreement.
    if (meaningful && g.net > 0) c.legs.add('flow_bull');
    if (meaningful && g.net < 0) c.flowBearish = true;
  }
  const flowTotBull = num(flowAgg2top?.bullishPremium);
  const flowTotBear = num(flowAgg2top?.bearishPremium);
  const flowLargest = flowAgg2top?.largestTrade || (Array.isArray(flowAgg2top?.largestTrades) ? flowAgg2top.largestTrades[0] : null);
  health.flow = flowAuthFail && flowAlerts.length === 0
    ? `FAILED (${TD_KEY ? 'key rejected' : 'no TD_API_KEY'})`
    : (flowAlerts.length === 0 && !marketOpen
        ? `market closed — flow N/A (last session ${lastSession || '—'})`
        : (isWeekly
            ? `${flowAlerts.length} biggest prints (${flowWindow}), ${flowAgg.size} tickers — wk bull ${fmt$(flowTotBull)} vs bear ${fmt$(flowTotBear)}${flowLargest ? `, largest ${sym(flowLargest)} ${fmt$(num(flowLargest.premium))}` : ''}${flowUndercovered ? ` ⚠️ ${flowTotal} qualify > ${flowMaxPages * FLOW_PAGE_SIZE} paged — per-ticker table is a recent slice; header totals are whole-week` : ''}`
            : `${flowAlerts.length} alerts (${flowWindow}), ${flowAgg.size} tickers`));

  // === 3. NEW CBOE OPTION LISTINGS =========================================
  const cboeR = await getJson(`${TD_BASE}/api/options-listings`);
  await saveRaw('cboe_options_listings', cboeR.data ?? { error: cboeR.error });
  let newListings = [];
  if (cboeR.ok && cboeR.data && cboeR.data.latest) {
    const diff = cboeR.data.latest.diff || {};
    const opt = (diff.optionable && diff.optionable.new) || {};
    newListings = Object.keys(opt).map((k) => ({ symbol: k.toUpperCase(), name: opt[k] }));
    for (const l of newListings) { const c = cand(l.symbol); c.cboe = true; c.legs.add('cboe_new'); }
  }
  const cboeScanDate = (cboeR.ok && cboeR.data && cboeR.data.latest && (cboeR.data.latest.date || '').slice(0, 10)) || null;
  health.cboe = cboeR.ok
    ? (newListings.length
        ? `${newListings.length} new optionable`
        : `${marketOpen ? '0 new' : 'market closed'} (last scan ${cboeScanDate || '—'})`)
    : `FAILED (${cboeR.error})`;

  // === 3b. COMMUNITY WATCHING — REMOVED ====================================
  // The /community/watching endpoint never deployed (404 on both the old Railway
  // and new dev APIs across every run). Dropped to stop a guaranteed-404 round
  // trip and a misleading "pending deploy" health row. Re-add as a new-API leg if
  // TD Pro ever ships it.
  const communityWatch = [];

  // === 4. HEDGE FUNDS (TickerTrace 13F) ====================================
  const briefR = await getJson(`${TT_BASE}/briefing`);
  const instR = await getJson(`${TT_BASE}/institutional?limit=25`);
  const divR = await getJson(`${TT_BASE}/divergences`);
  await saveRaw('tickertrace_briefing', briefR.data ?? { error: briefR.error });
  await saveRaw('tickertrace_institutional', instR.data ?? { error: instR.error });
  await saveRaw('tickertrace_divergences', divR.data ?? { error: divR.error });

  const brief = briefR.ok ? briefR.data : {};
  const topBuys = brief.topBuys || [];
  const topSells = brief.topSells || [];
  const crossFund = brief.crossFundConvergence || [];
  const streaks = brief.activeStreaks || [];
  const instBuying = (instR.ok && instR.data && instR.data.buying) || [];
  const instSelling = (instR.ok && instR.data && instR.data.selling) || [];

  const attachInst = (rows, direction, leg) => {
    for (const r of rows) {
      const t = sym(r); if (!t) continue;
      const c = cand(t);
      c.inst = c.inst || {};
      c.inst.direction = direction;
      c.inst.weightDelta = num(r.weightDelta);
      c.inst.funds = fundCount(r);
      c.inst.conviction = r.conviction ?? null;
      c.inst.sector = r.sector ?? c.inst.sector ?? null;
      if (leg) c.legs.add(leg);
    }
  };
  attachInst(topBuys, 'BUYING', 'inst_buy');
  attachInst(instBuying, 'BUYING', 'inst_buy');
  attachInst(crossFund.filter((r) => /buy/i.test(r.direction || '')), 'BUYING (cross-fund)', 'inst_crossfund');
  // sells: annotate as a conflict, never a bullish leg
  for (const r of [...topSells, ...instSelling]) {
    const t = sym(r); if (!t) continue;
    const c = cand(t);
    c.instSelling = true;
    if (!c.inst) { c.inst = { direction: 'SELLING', weightDelta: num(r.weightDelta), funds: fundCount(r), sector: r.sector ?? null }; }
  }
  health.hedgeFunds = briefR.ok
    ? `${topBuys.length} top buys, ${crossFund.length} cross-fund, ${instBuying.length} buying`
    : `FAILED (${briefR.error})`;

  // Hoisted so the Tier-3 detectors below can add dtb_break / rs_leader as
  // first-class legs in the SAME legWeight()/rankScore pass.
  const BULLISH_LEGS = ['screener', 'flow_bull', 'inst_buy', 'inst_crossfund', 'cboe_new', 'dtb_break', 'rs_leader'];

  // === 4b. 300-DAY OHLC -> DOWNTREND-BREAKOUT + SPRING DETECTORS + RS-vs-SPY ==
  // Candidate set from RAW leg membership so it doesn't depend on the not-yet-built
  // shortlist. We include the SMART-MONEY names (13F buys, cross-fund, bullish
  // flow) even at a single leg — those beaten-down "funds accumulating" names are
  // exactly where a multi-month downtrend breaks, and they're required for the
  // 💎 Smart-Money-Early join to ever fire. Prioritised so they aren't crowded out
  // of the OHLC_MAX_NAMES budget by plain uptrending momentum names (which by
  // construction never sit below a falling trendline).
  const dtbPriority = (c) => {
    let p = 0;
    if (c.legs.has('inst_crossfund')) p += 4;
    if (c.legs.has('inst_buy')) p += 3;
    if (c.legs.has('flow_bull')) p += 2;
    if (c.reversal?.reversing) p += 2;
    if (c.flowBearish || c.instSelling) p += 1; // beaten-down → downtrend candidate
    return p;
  };
  const ohlcSet = [...reg.values()].filter((c) =>
    c.reversal?.reversing ||
    c.screeners.some((s) => s.id === 'momentum' || s.id === 'bullish-pullback') ||
    c.legs.has('inst_buy') || c.legs.has('inst_crossfund') || c.legs.has('flow_bull') ||
    (BULLISH_LEGS.some((l) => c.legs.has(l)) && c.legs.size >= 2)
  ).sort((a, b) => dtbPriority(b) - dtbPriority(a)).slice(0, OHLC_MAX_NAMES);

  // SPY baseline for relative strength (fetched once).
  const spy = await fetchChart('SPY', OHLC_DAYS, oldAuth);
  await saveRaw('ohlc_SPY', spy ? { meta: { ticker: 'SPY', candles: spy.candles.length } } : { error: 'no SPY chart' });
  const spy20 = retPct(spy?.candles, RS_SHORT), spy60 = retPct(spy?.candles, RS_LONG);

  let dtbCount = 0, springCount = 0, rsCount = 0, ohlcOk = 0;
  await pool(ohlcSet, 5, async (c) => {
    const ch = await fetchChart(c.ticker, OHLC_DAYS, oldAuth);
    if (!ch) return;
    ohlcOk++;
    c.ohlc = ch.candles;
    // --- Reversal reconciliation against the FRESH last candle. The screener row's
    // changePct / priceVsEma21Pct can lag the tape (a name prints a -6% knife while
    // the stale row still reads "at EMA21" -> false "reversing" tag, e.g. VSH/R).
    // Recompute day-change + vs-EMA21 from the chart's own last bar so the report
    // and the rendered PNG agree, then re-gate the reversal flag on real evidence of
    // a turn: latest bar green or reclaiming EMA21 AND RSI hooking up, with a hard
    // veto on down days / below-EMA21 / post-parabola knives.
    const cs = ch.candles;
    if (cs.length >= 2) {
      const last = cs[cs.length - 1], prev = cs[cs.length - 2];
      const fClose = num(last.close), pClose = num(prev.close), fOpen = num(last.open);
      const e21 = num(last.ema21), e55 = num(last.ema55), lrsi = num(last.rsi), prsi = num(prev.rsi);
      const fChg = (fClose != null && pClose) ? (fClose - pClose) / pClose * 100 : null;
      const fVsE21 = (fClose != null && e21) ? (fClose - e21) / e21 * 100 : null;
      // sync tech to the chart's last bar so report day% / vsEMA21 match the PNG
      if (fChg != null || fVsE21 != null) {
        c.tech = { ...(c.tech || {}) };
        if (fChg != null) c.tech.changePct = fChg;
        if (fVsE21 != null) c.tech.priceVsEma21Pct = fVsE21;
      }
      if (c.reversal?.reversing) {
        const greenOrReclaim = (fClose != null && fOpen != null && fClose >= fOpen) || (fVsE21 != null && fVsE21 >= 0);
        const rsiHook = (lrsi != null && prsi != null) ? lrsi >= prsi - 0.5 : true;
        const belowE21 = fVsE21 != null && fVsE21 < -1;
        const hardDown = fChg != null && fChg <= -3;
        const parabolic = (fClose != null && e55) ? (fClose / e55 - 1) > 0.5 : false;
        const knife = parabolic && fChg != null && fChg <= -4;
        if (belowE21 || hardDown || knife || !(greenOrReclaim && rsiHook)) {
          c.reversal.reversing = false;
          c.reversal.suppressed = belowE21 ? 'below EMA21 on fresh bar'
            : knife ? 'post-parabola down day'
            : hardDown ? 'hard down day'
            : 'no green reclaim / RSI not hooking up';
        }
      }
    }
    const opts = { ticker: c.ticker, earningsDaysAway: c.tech?.earningsDaysAway ?? null, gex: null };
    const dtb = detectDowntrendBreakout(ch.candles, opts);
    const sp = detectSpring(ch.candles, opts);
    c.dtb = dtb; c.spring = sp;
    if (dtb?.breakout) {
      c.legs.add('dtb_break');
      c.dtbFresh = dtb.dtbFresh ?? (dtb.bars_since_break != null && dtb.bars_since_break <= 5);
      dtbCount++;
    }
    if (sp?.spring) { c.springFlag = true; springCount++; }
    const r20 = retPct(ch.candles, RS_SHORT), r60 = retPct(ch.candles, RS_LONG);
    c.rs = {
      rs20: (r20 != null && spy20 != null) ? r20 - spy20 : null,
      rs60: (r60 != null && spy60 != null) ? r60 - spy60 : null,
    };
    if (c.rs.rs20 > 0 && c.rs.rs60 > 0) { c.legs.add('rs_leader'); rsCount++; }
  });
  // log ALL dtb tiers (not just breakouts) for the Downtrend-Breakout Watch section
  const dtbAll = [...reg.values()].filter((c) => c.dtb).sort((a, b) => (b.dtb.dtbScore || 0) - (a.dtb.dtbScore || 0));
  health.dtb = `${ohlcOk}/${ohlcSet.length} charts, ${dtbCount} breakouts, ${dtbAll.length} dtb signals, ${springCount} springs`;
  health.rs = (spy20 != null || spy60 != null)
    ? `SPY 20d ${pct(spy20)} / 60d ${pct(spy60)}; ${rsCount} leaders`
    : 'SPY chart unavailable';

  // === 4c. EARNINGS BLACKOUT CALENDAR (new API) ============================
  const earnR = await getJson(`${TD_NEW_BASE}/earnings`, { headers: newAuth });
  await saveRaw('earnings', earnR.data ?? { error: earnR.error });
  const earnMap = new Map();
  const earnToday = new Date();
  for (const e of (earnR.ok && earnR.data && earnR.data.events) || []) {
    const t = sym(e); if (!t) continue;
    const d = Math.round((new Date(e.date) - earnToday) / 864e5);
    earnMap.set(t, { days: d, time: e.time || null, date: e.date, name: e.companyName || null });
  }
  for (const c of reg.values()) {
    c.earnDays = c.tech?.earningsDaysAway ?? earnMap.get(c.ticker)?.days ?? null;
    c.earnTime = earnMap.get(c.ticker)?.time ?? null;
    c.earnSoon = c.earnDays != null && c.earnDays >= 0 && c.earnDays <= EARNINGS_BLACKOUT_DAYS;
  }
  health.earnings = earnR.ok ? `${earnMap.size} events (next ~5 sessions)` : `FAILED (${earnR.error})`;

  // === 5. CONVERGENCE RANKING =============================================
  // Per-leg quality weights — a cross-fund cluster or institutional-alpha flow is
  // worth more than a lone CBOE listing. Replaces the old "every leg = 1" model
  // where legCount*1e12 lexicographically buried A-grade reversals under any
  // 2-leg pair. legCount is still kept for display + the MIN_LEGS gate.
  const legWeight = (c) => {
    let w = 0;
    for (const l of c.legs) {
      if (l === 'screener') {
        const ab = c.screeners.some((s) => !s.chase && /A|B/.test((s.grade || '').replace(/[^A-Z]/g, '')));
        w += ab ? 2 : 1;                       // A/B-grade screener leg counts double
      } else if (l === 'flow_bull') {
        w += c.flow?.instAlpha ? 3 : 2;        // institutional-alpha flow is premium
      } else if (l === 'inst_crossfund') {
        w += 3;                                // multiple funds, same name — strongest
      } else if (l === 'inst_buy') {
        w += 2;
      } else if (l === 'dtb_break') {
        w += c.dtbFresh ? 5 : 4;               // fresh trendline break — Mike's #1 setup
      } else if (l === 'rs_leader') {
        w += 1.5;                              // leading SPY on both windows
      } else if (l === 'cboe_new') {
        w += 0.5;
      } else { w += 1; }
    }
    return w;
  };
  // Extended/parabolic guard — flag names that already ran so they stop topping
  // the list. 2-of-3 of {stretched past EMA21, RSI hot, already-ran} → extended.
  // A confirmed reversal is exempt (a fresh turn legitimately has a hot stoch/RSI).
  const extensionFlags = (t) => {
    if (!t) return [];
    const f = [];
    if (t.priceVsEma21Pct != null && t.priceVsEma21Pct > 8) f.push('>8% vs EMA21');
    if (t.rsi != null && t.rsi > 78) f.push('RSI>78');
    if ((t.perfWeekPct != null && t.perfWeekPct > 20) || (t.perfMonthPct != null && t.perfMonthPct > 40) ||
        (t.changePct != null && t.changePct > 6)) f.push('already ran');
    return f;
  };
  const all = [...reg.values()].map((c) => {
    // rs_leader is derived off the SAME price series (not an independent source).
    // Keep it as a rank booster (legWeight still uses it) but DON'T let it satisfy
    // the "multiple independent sources agree" gate — otherwise a screener+rs_leader
    // name masquerades as 2-leg convergence and pads out the honest single-leg
    // backfill of real reversals. legCount = independent legs only.
    c.legCount = [...c.legs].filter((l) => l !== 'rs_leader').length;
    const hasBullish = BULLISH_LEGS.some((l) => c.legs.has(l));
    // a name is conflicted when bullish sources disagree with bearish ones
    c.conflict = hasBullish && (c.flowBearish || c.instSelling);
    // extension flags (skipped for confirmed reversals AND fresh DTB breakouts — a
    // fresh trendline break legitimately runs hot, same exemption as a reversal).
    c.extFlags = (c.reversal?.reversing || c.dtbFresh) ? [] : extensionFlags(c.tech);
    c.extended = c.extFlags.length >= 2;
    // only count aligned (bullish) flow magnitude toward the rank
    const alignedFlowMag = c.flow && c.flow.net > 0 ? c.flow.net : 0;
    const entry = c.tech?.entryScore || 0;
    const revBoost = c.reversal?.reversing ? 1 : 0;
    c.legW = legWeight(c);
    // Additive, bounded score: weighted legs lead, a confirmed reversal can outrank
    // a weak multi-leg pair, grade matters, flow $ is a capped tie-breaker, and
    // conflict/extension push names down rather than off a cliff. Tier-3: spring
    // boost, dtbScore tie-breaker, and an earnings-blackout penalty + hard cap.
    c.rankScore = c.legW * 100
      + revBoost * 200
      + (entry / 100) * 80
      + Math.min(alignedFlowMag / 1e6, 50)
      - (c.conflict ? 120 : 0)
      - (c.extended ? 180 : 0)
      + (c.springFlag ? 60 : 0)
      + (c.dtb?.dtbScore ? Math.min(c.dtb.dtbScore, 100) * 0.4 : 0)
      - (c.earnSoon ? 90 : 0);
    // earnings-blackout names can't sit top-3: hard-cap so a fresh long isn't surfaced into a print.
    if (c.earnSoon) c.rankScore = Math.min(c.rankScore, 250);
    return c;
  });
  all.sort((a, b) => b.rankScore - a.rankScore);

  let shortlist = all.filter((c) => c.legCount >= MIN_LEGS);
  if (shortlist.length < 8) {
    // backfill with single-leg high-quality (A/B grade screener OR confirmed reversal OR strong flow)
    const extra = all.filter((c) => c.legCount === 1 &&
      (c.reversal?.reversing || /A|B/.test((c.tech?.entryGrade || '').replace(/[^A-Z]/g, '')) || (c.flow && Math.abs(c.flow.net) >= 250000)));
    shortlist = [...shortlist, ...extra];
  }
  shortlist = shortlist.slice(0, SHORTLIST_SIZE);

  // reversal watch list (the edge) — momentum/bullish-pullback names turning up
  const reversalWatch = all
    .filter((c) => c.reversal && c.reversal.reversing)
    .sort((a, b) => (b.reversal.entryScore || 0) - (a.reversal.entryScore || 0));

  // === 5b. ENRICH technicals for shortlist names that arrived via flow/funds only
  const needEnrich = shortlist.filter((c) => !c.tech || c.tech.rsi == null);
  let enriched = 0, enrichEmpty = 0;
  await pool(needEnrich, 4, async (c) => {
    const r = await getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(c.ticker)}`, { headers: authHeaders });
    if (!r.ok || !r.data) return;
    const tc = r.data.technicals || {};
    const op = r.data.options || {};
    const price = num(tc.close) ?? num(r.data.price);
    const ema21 = num(tc.ema21);
    const change = num(tc.change); // dollar change, not a percent
    const changePct = (change != null && price != null && (price - change) !== 0) ? (change / (price - change) * 100) : (c.tech?.changePct ?? null);
    c.tech = {
      ...(c.tech || {}),
      price: price ?? c.tech?.price ?? null,
      changePct,
      rsi: num(tc.rsi), adx: num(tc.adx),
      relativeVolume: num(tc.relVol),
      priceVsEma21Pct: (price != null && ema21) ? ((price - ema21) / ema21 * 100) : (c.tech?.priceVsEma21Pct ?? null),
      sector: c.tech?.sector ?? null,
      src: (c.tech?.src === 'momentum' || c.tech?.src === 'bullish-pullback') ? c.tech.src : 'ticker-api',
    };
    const em = op.expectedMove || {};
    c.optionsCtx = {
      callWall: num(op.callWall), putWall: num(op.putWall),
      expectedMovePct: num(em.percent), putCallOIRatio: num(op.putCallOIRatio), maxPain: num(op.maxPain),
    };
    // only count as enriched if a real technical actually came back — otherwise the
    // endpoint shape changed and we'd report "5/5 enriched" over an all-— table.
    if (num(tc.rsi) != null || num(tc.close) != null) enriched++; else enrichEmpty++;
  });
  health.enrich = needEnrich.length === 0
    ? 'none needed'
    : `${enriched}/${needEnrich.length} flow/fund names enriched${enrichEmpty ? ` (${enrichEmpty} returned no technicals — check endpoint shape)` : ''}`;

  // === 5b2. GEX ENRICH (new API) — shortlist-only, bounded re-sort tie-breaker ==
  // Per-symbol GEX over the whole prelim set is too expensive; run it on the ranked
  // shortlist AFTER rankScore, then apply a small bounded adjustment (above the
  // gamma flip = dealers short gamma = breakouts follow through; clean room to the
  // call wall = upside; price above the wall = stretched).
  let gexOk = 0;
  await pool(shortlist, 4, async (c) => {
    if (!ENABLE_GEX) return;
    const r = await getJson(`${TD_NEW_BASE}/gex/${encodeURIComponent(c.ticker)}`, { headers: newAuth });
    const d = r.ok && r.data && r.data.data;
    if (!d) return;
    if (gexOk === 0) await saveRaw('gex_sample', r.data);  // shape-drift tripwire / reproducibility

    const spot = num(d.spotPrice), wall = num(d.maxGammaStrike), flip = num(d.gammaFlipLevel);
    c.gex = {
      spot, wall, flip,
      regime: (d.interpretation && d.interpretation.marketRegime) || null,
      pcr: num(d.putCallGEXRatio),
      roomToWallPct: (spot && wall) ? (wall - spot) / spot * 100 : null,
      aboveFlip: (flip != null && spot != null) ? spot > flip : null,  // gammaFlipLevel CAN be null
    };
    gexOk++;
  });
  for (const c of shortlist) {
    let adj = 0; const g = c.gex;
    if (g) {
      if (g.aboveFlip === true) adj += 15;
      if (g.roomToWallPct != null && g.roomToWallPct > 2 && g.roomToWallPct < 12) adj += 15;
      if (g.roomToWallPct != null && g.roomToWallPct < 0) adj -= 10;
    }
    c.gexAdj = adj; c.rankScore += adj;
    // re-apply the earnings-blackout cap AFTER the GEX bump, else a +30 GEX adj can
    // lift a blackout name back over the cap it was barred to.
    if (c.earnSoon) c.rankScore = Math.min(c.rankScore, 250);
  }
  shortlist.sort((a, b) => b.rankScore - a.rankScore);
  health.gex = ENABLE_GEX ? `${gexOk}/${shortlist.length} shortlist names` : 'disabled (RECAP_GEX=0)';

  // === 5b3. SMART-MONEY-EARLY JOIN (Mike's #1 setup, forced to the top) ======
  // Fresh downtrend-breakout ∩ 13F fund accumulation ∩ live net-bullish flow ∩ not
  // in an earnings blackout. The whole edge: smart money in BEFORE the crowd.
  const smartEarly = [...reg.values()].filter((c) =>
    c.legs.has('dtb_break') &&
    (c.legs.has('inst_buy') || c.legs.has('inst_crossfund')) &&
    c.flow && c.flow.net > 0 && c.flow.fresh && !c.earnSoon
  ).sort((a, b) => b.rankScore - a.rankScore);

  // affordable (sub-threshold price) convergence names — surfaced separately so
  // the recap isn't all $700+ mega-caps. `all` is already rankScore-sorted.
  const affordable = all
    .filter((c) => c.tech?.price != null && c.tech.price > 0 && c.tech.price <= MAX_AFFORDABLE_PRICE)
    .filter((c) => c.legCount >= 2 || c.reversal?.reversing || /A|B/.test((c.tech?.entryGrade || '').replace(/[^A-Z]/g, '')))
    .slice(0, 10);

  // === 5c. RENDER CHARTS — top-5 convergence + reversal-watch + top-3 affordable
  //         + every dtb_break name + the smart-money-early names (so PNGs exist).
  const chartSyms = [...new Set([
    ...shortlist.slice(0, 5).map((c) => c.ticker),
    ...reversalWatch.map((c) => c.ticker),
    ...affordable.slice(0, 3).map((c) => c.ticker),
    ...[...reg.values()].filter((x) => x.legs.has('dtb_break')).slice(0, 5).map((c) => c.ticker),
    ...smartEarly.slice(0, 5).map((c) => c.ticker),
  ])];
  const charts = {}; // ticker -> png path
  if (chartSyms.length) {
    try {
      const { execFileSync } = await import('node:child_process');
      const py = join(SKILL_DIR, '.venv', 'bin', 'python');
      const script = join(SKILL_DIR, 'scripts', 'render_chart.py');
      const out = execFileSync(py, [script, ...chartSyms, '--out', join(OUT_DIR, 'charts')],
        { encoding: 'utf8', timeout: 180000, env: { ...process.env, AGENT_API_KEY: AGENT_KEY || '' } });
      for (const line of out.split('\n')) {
        const [t, p] = line.split('\t');
        if (t && p && !/^ERROR/.test(p.trim())) charts[t.trim()] = p.trim();
      }
    } catch (e) {
      health.charts = `render failed: ${(e && e.message || e).toString().slice(0, 120)}`;
    }
  }
  // attach chart paths back onto the candidates
  for (const c of all) if (charts[c.ticker]) c.chartPath = charts[c.ticker];
  if (!health.charts) health.charts = `${Object.keys(charts).length}/${chartSyms.length} rendered`;

  // === 6. WRITE REPORT =====================================================
  const md = buildReport({
    stamp, now, TD_BASE, TT_BASE, health,
    flowAlerts, flowAgg, repeats, newListings,
    topBuys, topSells, crossFund, streaks, instBuying,
    screenerResults, shortlist, reversalWatch, OUT_DIR, charts, affordable,
    communityWatch, marketOpen, lastSession,
    smartEarly, marketStatsAgg: flowAgg2top, flowWindow, isWeekly, earnMap, dtbAll, spy20, spy60,
  });
  const reportPath = join(OUT_DIR, 'report.md');
  await writeFile(reportPath, md);
  await saveRaw('shortlist', shortlist.map(serializeCand));
  await saveRaw('_health', health);

  // === 7. STDOUT recap =====================================================
  console.log(md);
  console.log(`\n──────────────────────────────────────────`);
  console.log(`📄 Report:   ${reportPath}`);
  console.log(`🗂  Raw JSON: ${RAW_DIR}`);
  console.log(JSON.stringify({ reportPath, rawDir: RAW_DIR, shortlist: shortlist.map((c) => c.ticker), health }, null, 0));
}

function serializeCand(c) {
  return { ticker: c.ticker, legs: [...c.legs], legCount: c.legCount, legW: c.legW, rankScore: c.rankScore, extended: c.extended, extFlags: c.extFlags, conflict: c.conflict, screeners: c.screeners, tech: c.tech, flow: c.flow, inst: c.inst, cboe: c.cboe, reversal: c.reversal,
    dtb: c.dtb, spring: c.spring, springFlag: c.springFlag, dtbFresh: c.dtbFresh, rs: c.rs, gex: c.gex, gexAdj: c.gexAdj, earnDays: c.earnDays, earnSoon: c.earnSoon };
}

// ---- report builder -------------------------------------------------------
function buildReport(ctx) {
  const { stamp, now, TD_BASE, TT_BASE, health, flowAgg, newListings,
    topBuys, topSells, crossFund, streaks, screenerResults, shortlist, reversalWatch, charts = {}, affordable = [],
    communityWatch = [], marketOpen = true, lastSession = null,
    smartEarly = [], marketStatsAgg = null, flowWindow = 'today', isWeekly = false, earnMap = new Map(), dtbAll = [], spy20 = null, spy60 = null } = ctx;
  const relChart = (p) => (p ? p.split('/').slice(-2).join('/') : null); // charts/TICKER.png
  const L = [];
  L.push(`# 📈 Stock Recap — ${stamp.replace('_', ' ')}`);
  L.push('');
  L.push(`_Generated ${now.toString()}_`);
  L.push('');
  // data health
  L.push('**Data sources**');
  L.push('');
  L.push(`| Leg | Status |`);
  L.push(`|---|---|`);
  L.push(`| Market | ${marketOpen ? 'open' : `closed${lastSession ? ` — last session ${lastSession}` : ''}`} |`);
  L.push(`| Screeners (TD Pro) | ${health.screeners || '—'} |`);
  L.push(`| Options flow (TD Pro) | ${health.flow || '—'} |`);
  L.push(`| New CBOE listings (TD Pro) | ${health.cboe || '—'} |`);
  L.push(`| Hedge funds / 13F (TickerTrace) | ${health.hedgeFunds || '—'} |`);
  L.push(`| Downtrend-breakout scan | ${health.dtb || '—'} |`);
  L.push(`| GEX enrich | ${health.gex || '—'} |`);
  L.push(`| Earnings calendar | ${health.earnings || '—'} |`);
  L.push(`| RS vs SPY | ${health.rs || '—'} |`);
  L.push(`| Technicals enrichment | ${health.enrich || '—'} |`);
  L.push(`| Charts rendered | ${health.charts || '—'} |`);
  L.push('');

  // ===== SMART-MONEY-EARLY (forced top — Mike's #1 setup) =====
  L.push('## 💎 Smart-Money-Early');
  L.push('');
  L.push('_The rarest, highest-conviction join: a multi-month **falling trendline breaking** ∩ **13F funds accumulating** ∩ **live net-bullish options flow** ∩ **not** in an earnings blackout. Smart money positioning in before the crowd._');
  L.push('');
  if (smartEarly.length) {
    L.push(`| Ticker | DTB (bars / score) | Funds | Net flow | RS20/RS60 | GEX room ▲/▼flip | Price vs line | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|`);
    for (const c of smartEarly) {
      const d = c.dtb || {}; const g = c.gex; const r = c.rs || {};
      const fundsTxt = `${c.inst?.direction || 'BUYING'}${c.inst?.funds ? ' (' + c.inst.funds + ')' : ''}`;
      const rsTxt = `${r.rs20 != null ? pct(r.rs20) : '—'}/${r.rs60 != null ? pct(r.rs60) : '—'}`;
      const gexTxt = g ? `${g.roomToWallPct != null ? (g.roomToWallPct > 0 ? '+' : '') + g.roomToWallPct.toFixed(1) + '%' : '—'} ${g.aboveFlip === true ? '▲flip' : (g.aboveFlip === false ? '▼flip' : '')}`.trim() : '—';
      const vsLine = d.clearance_pct != null ? `${pct(d.clearance_pct)} (line $${d.lineToday})` : '—';
      L.push(`| **${c.ticker}** | ${d.bars_since_break ?? '—'}d / ${d.dtbScore ?? '—'} | ${fundsTxt} | ${fmt$(c.flow?.net)} 🟢 | ${rsTxt} | ${gexTxt} | ${vsLine} | ${c.springFlag ? '🪤spring ' : ''}${c.dtbFresh ? '🆕fresh' : ''} |`);
    }
    L.push('');
    for (const c of smartEarly) {
      const d = c.dtb || {};
      L.push(`- **${c.ticker}** — falling trendline broke ${d.bars_since_break != null ? d.bars_since_break + ' bar(s)' : 'recently'} ago${d.break_date ? ` (${String(d.break_date).slice(0, 10)})` : ''}, ${c.inst?.funds ? c.inst.funds + ' funds' : 'funds'} accumulating on 13F, ${fmt$(c.flow?.net)} net-bullish ${isWeekly ? 'weekly ' : ''}flow${(c.rs?.rs20 > 0 && c.rs?.rs60 > 0) ? ', leading SPY on 20d+60d' : ''} — smart money early.`);
    }
  } else {
    L.push('_No name currently satisfies the full triad (fresh trendline break ∩ fund buying ∩ live bullish flow, earnings-excluded). This is the rarest setup — empty is normal; the Downtrend-Breakout Watch below lists partial signals._');
  }
  L.push('');

  // ===== RECAP =====
  L.push('## 📊 Market Recap');
  L.push('');

  // flow
  const flows = [...flowAgg.values()].sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
  const totBull = flows.reduce((s, f) => s + f.bullPrem, 0);
  const totBear = flows.reduce((s, f) => s + f.bearPrem, 0);
  L.push(`### 💰 Options flow (biggest premium — ${flowWindow})`);
  L.push('');
  if (flows.length) {
    if (isWeekly && marketStatsAgg) {
      // Weekly: the per-row sum is now a thresholded SUBSET, so surface the true
      // week-wide aggregates from page-1 + the single largest print of the week.
      const lg = marketStatsAgg.largestTrade || (Array.isArray(marketStatsAgg.largestTrades) ? marketStatsAgg.largestTrades[0] : null);
      L.push(`Week-wide **bullish ${fmt$(num(marketStatsAgg.bullishPremium))}** vs **bearish ${fmt$(num(marketStatsAgg.bearishPremium))}** (total ${fmt$(num(marketStatsAgg.totalPremium))})${lg ? `. Largest print: **${sym(lg)}** ${fmt$(num(lg.premium))} ${lg.type || ''} ${lg.tradeType || ''}` : ''}.`);
      L.push('');
      L.push(`_Window is the last ~5 sessions tightened to score ≥ ${FLOW_WEEKLY_MIN_SCORE} / premium ≥ ${fmt$(FLOW_WEEKLY_MIN_PREMIUM)} so the rows below are the **biggest prints of the week**, not a recent time-slice. The endpoint is time-ordered and ignores sort params, so threshold-tightening is how we capture the biggest flows._`);
    } else {
      L.push(`Total bullish premium **${fmt$(totBull)}** vs bearish **${fmt$(totBear)}** across tracked alerts.`);
    }
    L.push('');
    L.push(`| Ticker | Net flow | Dir | Top trade | Score | Inst-α | Repeat |`);
    L.push(`|---|---|---|---|---|---|---|`);
    for (const f of flows.slice(0, 12)) {
      L.push(`| **${f.ticker}** | ${fmt$(f.net)} | ${f.dir} | ${f.topTradeType || '—'} | ${f.maxScore} | ${f.instAlpha ? '🛡️' : ''} | ${f.repeat > 1 ? '🔁×' + f.repeat : ''} |`);
    }
  } else if (!marketOpen) {
    L.push(`_Market closed — the weekly flow window (${flowWindow}) returned nothing this run (last session ${lastSession || '—'}). Not a bearish read._`);
  } else {
    L.push('_No qualifying flow (quiet tape or flow leg unavailable)._');
  }
  L.push('');

  // hedge funds
  L.push('### 🏛️ Hedge funds (13F — TickerTrace)');
  L.push('');
  if (topBuys.length || crossFund.length) {
    if (crossFund.length) {
      L.push(`**Cross-fund convergence** (multiple funds into the same name — strongest signal):`);
      L.push(crossFund.slice(0, 6).map((r) => `\`${sym(r)}\` (${fundCount(r) ?? '?'} funds${/sell/i.test(r.direction || '') ? ', selling' : ', buying'})`).join(' · '));
      L.push('');
    }
    L.push(`**Top buys:** ` + (topBuys.slice(0, 6).map((r) => `\`${sym(r)}\``).join(' · ') || '—'));
    L.push('');
    L.push(`**Top sells:** ` + (topSells.slice(0, 6).map((r) => `\`${sym(r)}\``).join(' · ') || '—'));
    L.push('');
    if (streaks.length) {
      L.push(`**Hot streaks:** ` + streaks.slice(0, 6).map((s) => `${sym(s)} (${s.fund}, ${s.days}d ${s.direction})`).join(' · '));
      L.push('');
    }
  } else {
    L.push('_Hedge-fund leg unavailable._');
    L.push('');
  }

  // (Community-watching section removed — endpoint never deployed.)

  // CBOE
  L.push('### 🆕 New CBOE optionable listings');
  L.push('');
  if (newListings.length) {
    L.push(newListings.slice(0, 25).map((l) => `\`${l.symbol}\``).join(' · '));
    if (newListings.length > 25) L.push(`\n…and ${newListings.length - 25} more.`);
  } else {
    L.push('_None new in latest scan._');
  }
  L.push('');

  // screener hit counts
  L.push('### 🔎 Screener hits');
  L.push('');
  L.push(`| Screener | Hits |`);
  L.push(`|---|---|`);
  for (const [id, s] of Object.entries(screenerResults)) {
    L.push(`| ${s.name || id} | ${s.ok ? s.count : '⚠️ ' + (s.error || 'failed')} |`);
  }
  L.push('');

  // ===== SHORTLIST =====
  L.push('## 🎯 Shortlist — convergence ranked');
  L.push('');
  const multiLeg = shortlist.filter((c) => c.legCount >= 2).length;
  const backfill = shortlist.length - multiLeg;
  L.push(`_Ranked by weighted source agreement. ${shortlist.length} names — **${multiLeg} with 2+ legs**${backfill ? `, ${backfill} single-leg backfill (quality screener / reversal / strong flow)` : ''}._`);
  if (!marketOpen && backfill > multiLeg) {
    L.push('');
    L.push(`_Heads-up: market's closed, so flow + CBOE legs are dark — this run leans on screeners + 13F. Real cross-source convergence is thin; treat the backfill names as single-signal ideas, not confirmed._`);
  }
  L.push('');
  if (shortlist.length) {
    L.push(`| # | Ticker | Legs | Sources | Price | Tech (RSI/ADX/Stoch) | RS20/RS60 | GEX | Grade | Flow | Hedge funds | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|---|---|---|---|`);
    shortlist.forEach((c, i) => {
      const t = c.tech || {};
      const sources = legLabels(c);
      const tech = `${t.rsi != null ? t.rsi.toFixed(0) : '—'}/${t.adx != null ? t.adx.toFixed(0) : '—'}/${t.stochK != null ? t.stochK.toFixed(0) : '—'}`;
      const r = c.rs || {};
      const rsTxt = (r.rs20 != null || r.rs60 != null) ? `${r.rs20 != null ? pct(r.rs20) : '—'}/${r.rs60 != null ? pct(r.rs60) : '—'}` : '—';
      const g = c.gex;
      const gexTxt = g ? `${g.roomToWallPct != null ? (g.roomToWallPct > 0 ? '+' : '') + g.roomToWallPct.toFixed(0) + '%' : '—'}${g.aboveFlip === true ? '▲' : (g.aboveFlip === false ? '▼' : '')}` : '—';
      const flow = c.flow && Math.abs(c.flow.net) >= 1 ? `${fmt$(c.flow.net)} ${c.flow.dir}${c.flow.instAlpha ? ' 🛡️' : ''}` : '—';
      const inst = c.inst ? `${c.inst.direction}${c.inst.funds ? ' (' + c.inst.funds + ')' : ''}` : '—';
      const edge = [c.legs.has('dtb_break') ? (c.dtbFresh ? '🔻→🟢🆕' : '🔻→🟢') : '', c.springFlag ? '🪤' : '', c.reversal?.reversing ? '🔄 reversing' : '', c.extended ? '🚀 extended' : '', c.conflict ? '⚠️ conflict' : '', c.earnSoon ? `📅${c.earnDays}d` : ''].filter(Boolean).join(' ');
      L.push(`| ${i + 1} | **${c.ticker}** | ${c.legCount} | ${sources} | ${t.price != null ? '$' + t.price.toFixed(2) : '—'} | ${tech} | ${rsTxt} | ${gexTxt} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    });
    L.push('');
    L.push('_New high-weight legs: **DTB🔻→🟢** (w=5 fresh / 4) = a multi-month falling trendline just broke; **RS-leader** (w=1.5) = outperforming SPY on BOTH the 20d and 60d windows. GEX col = room to the call wall % with ▲/▼ = above/below the gamma flip (above flip = dealers short gamma = breakouts follow through)._');
  } else {
    L.push('_No multi-source convergence found this run._');
  }
  L.push('');

  // per-pick detail for the top picks
  const detail = shortlist.slice(0, 8);
  if (detail.length) {
    L.push('### 🔬 Top picks — detail');
    L.push('');
    for (const c of detail) {
      const t = c.tech || {};
      L.push(`**${c.ticker}** — ${c.legCount} legs: ${legLabels(c)}`);
      const bits = [];
      if (t.price != null) bits.push(`price $${t.price.toFixed(2)} (${pct(t.changePct)})`);
      if (t.sector) bits.push(t.sector);
      if (t.rsi != null) bits.push(`RSI ${t.rsi.toFixed(0)}`);
      if (t.adx != null) bits.push(`ADX ${t.adx.toFixed(0)}`);
      if (t.stochK != null) bits.push(`StochK ${t.stochK.toFixed(0)}`);
      if (t.rsiZone) bits.push(`zone ${t.rsiZone}`);
      if (t.pullbackDepth) bits.push(`pullback ${t.pullbackDepth}`);
      if (t.entryGrade) bits.push(`grade ${t.entryGrade}`);
      if (t.perfWeekPct != null) bits.push(`1w ${pct(t.perfWeekPct)}`);
      if (bits.length) L.push('- ' + bits.join(' · '));
      if (c.screeners.length) L.push(`- Screeners: ${c.screeners.map((s) => s.name + (s.grade ? ` (${s.grade})` : '')).join(', ')}`);
      if (c.flow) L.push(`- Flow: net ${fmt$(c.flow.net)} ${c.flow.dir}, ${c.flow.count} alerts, max score ${c.flow.maxScore}${c.flow.instAlpha ? ', 🛡️ institutional-alpha tier' : ''}${c.flow.repeat > 1 ? `, 🔁 repeat ×${c.flow.repeat}` : ''}`);
      if (c.inst) { const w = wfmt(c.inst.weightDelta); const cv = convStr(c.inst.conviction); L.push(`- Hedge funds: ${c.inst.direction}${c.inst.funds ? `, ${c.inst.funds} funds` : ''}${w ? `, ${w}` : ''}${cv ? `, conviction ${cv}` : ''}`); }
      if (c.optionsCtx) { const o = c.optionsCtx; const ob = []; if (o.callWall != null) ob.push(`call wall ${o.callWall}`); if (o.putWall != null) ob.push(`put wall ${o.putWall}`); if (o.expectedMovePct != null) ob.push(`exp move ±${o.expectedMovePct.toFixed(1)}%`); if (o.putCallOIRatio != null) ob.push(`P/C OI ${o.putCallOIRatio.toFixed(2)}`); if (ob.length) L.push(`- Options: ${ob.join(' · ')}`); }
      if (c.cboe) L.push(`- 🆕 Newly optionable on CBOE`);
      if (c.conflict) L.push(`- ⚠️ **Conflict:** bullish source(s) disagree with ${c.flowBearish ? 'bearish options flow' : ''}${c.flowBearish && c.instSelling ? ' and ' : ''}${c.instSelling ? 'fund selling' : ''} — confirm before sizing.`);
      if (c.extended) L.push(`- 🚀 **Extended / already ran** (${(c.extFlags || []).join(', ')}) — likely chasing here; wait for a pullback.`);
      if (c.reversal?.reversing) L.push(`- 🔄 **Reversing out of pullback** — StochK ${c.reversal.stochK?.toFixed(0)} climbing, back at/above EMA21 (${pct(c.reversal.priceVsEma21Pct)}), ${c.reversal.rsiZone || ''}, grade ${c.reversal.grade || ''}${c.reversal.crossover ? ', stoch crossover confirmed' : ''}`);
      if (c.dtb) { const d = c.dtb; L.push(`- 🔻→🟢 **Downtrend-breakout (${d.tier})** — falling trendline (today $${d.lineToday}, ${d.slope_pct_per_bar}%/bar, ${d.touches} touches over ${d.span_bars} bars, ${pct(d.decline_pct * 100)} decline)${d.bars_since_break != null ? `, broke ${d.bars_since_break} bar(s) ago` : ''}, ${pct(d.clearance_pct)} clearance, dtbScore ${d.dtbScore} (lineQ ${d.sub?.lineQ}/fresh ${d.sub?.fresh}/vol ${d.sub?.vol}/momo ${d.sub?.momo}/ctx ${d.sub?.ctx})${c.dtbFresh ? ' — 🆕 fresh, extension-exempt' : ''}`); }
      if (c.springFlag && c.spring) L.push(`- 🪤 **Failed-breakdown spring** — reclaimed support $${c.spring.support} ${c.spring.bars_since} bar(s) ago, vol ${c.spring.vol_ratio != null ? c.spring.vol_ratio.toFixed(1) + 'x' : '—'}, spring score ${c.spring.dtbScore} (co-signal boost).`);
      if (c.rs) { const r = c.rs; if (r.rs20 != null || r.rs60 != null) L.push(`- 📊 RS vs SPY: 20d ${r.rs20 != null ? pct(r.rs20) : '—'}, 60d ${r.rs60 != null ? pct(r.rs60) : '—'}${(r.rs20 > 0 && r.rs60 > 0) ? ' — **RS-leader** (leads SPY on both windows)' : ''}`); }
      if (c.gex) { const g = c.gex; const gb = []; if (g.spot != null) gb.push(`spot $${g.spot.toFixed(2)}`); if (g.wall != null) gb.push(`call wall ${g.wall}${g.roomToWallPct != null ? ` (room ${pct(g.roomToWallPct)})` : ''}`); gb.push(`flip ${g.flip != null ? g.flip : '—'}${g.aboveFlip === true ? ' (above → dealers short gamma, breakouts follow through)' : (g.aboveFlip === false ? ' (below → dealers long gamma, moves dampened)' : '')}`); if (g.pcr != null) gb.push(`P/C GEX ${g.pcr.toFixed(2)}`); if (g.regime) gb.push(g.regime); L.push(`- 🧲 GEX: ${gb.join(' · ')}`); }
      if (c.earnSoon) L.push(`- 📅 **Earnings in ${c.earnDays}d${c.earnTime ? ` (${c.earnTime})` : ''}** — rank-capped (not surfaced as a fresh long into a print).`);
      if (c.chartPath) L.push(`- 📉 Chart: \`${relChart(c.chartPath)}\``);
      L.push('');
    }
  }

  // ===== AFFORDABLE (under threshold) =====
  L.push(`## 💵 Under $${MAX_AFFORDABLE_PRICE} — affordable picks`);
  L.push('');
  L.push(`_Same convergence logic, filtered to names trading at or below $${MAX_AFFORDABLE_PRICE} so the list isn't all mega-caps._`);
  L.push('');
  if (affordable.length) {
    L.push(`| Ticker | Price | Legs | Sources | Tech (RSI/ADX/Stoch) | Grade | Flow | Hedge funds | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|---|`);
    for (const c of affordable) {
      const t = c.tech || {};
      const tech = `${t.rsi != null ? t.rsi.toFixed(0) : '—'}/${t.adx != null ? t.adx.toFixed(0) : '—'}/${t.stochK != null ? t.stochK.toFixed(0) : '—'}`;
      const flow = c.flow && Math.abs(c.flow.net) >= 1 ? `${fmt$(c.flow.net)} ${c.flow.dir}` : '—';
      const inst = c.inst ? `${c.inst.direction}${c.inst.funds ? ' (' + c.inst.funds + ')' : ''}` : '—';
      const edge = [c.reversal?.reversing ? '🔄 reversing' : '', c.extended ? '🚀 extended' : '', c.conflict ? '⚠️ conflict' : '', c.chartPath ? '📉' : ''].filter(Boolean).join(' ');
      L.push(`| **${c.ticker}** | $${t.price.toFixed(2)} | ${c.legCount} | ${legLabels(c)} | ${tech} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    }
  } else {
    L.push(`_No qualifying names under $${MAX_AFFORDABLE_PRICE} this run._`);
  }
  L.push('');

  // ===== REVERSAL WATCH (the edge) =====
  L.push('## 🔄 Momentum Pullback — Reversal Watch');
  L.push('');
  L.push('_Your edge: pullback names that are **starting to reverse out** — stoch climbing out of oversold, price reclaiming the 21-EMA, RSI turning bullish / A-B grade. (Detected from the live read, not the screener\'s rarely-set crossover flag.)_');
  L.push('');
  if (reversalWatch.length) {
    L.push(`| Ticker | StochK | RSI zone | Grade | Entry | vs EMA21 | Pullback | Flow confirm | Fund confirm |`);
    L.push(`|---|---|---|---|---|---|---|---|---|`);
    for (const c of reversalWatch.slice(0, 20)) {
      const r = c.reversal;
      const flowC = c.flow && c.flow.net > 0 ? `${fmt$(c.flow.net)} 🟢` : (c.flow && c.flow.net < 0 ? `${fmt$(c.flow.net)} 🔴` : '—');
      const fundC = c.inst && /BUY/i.test(c.inst.direction) ? `BUYING ✅` : (c.inst ? c.inst.direction : '—');
      L.push(`| **${c.ticker}** | ${r.stochK != null ? r.stochK.toFixed(0) : '—'} | ${r.rsiZone || '—'} | ${r.grade || '—'} | ${r.entryScore != null ? r.entryScore.toFixed(0) : '—'} | ${r.priceVsEma21Pct != null ? pct(r.priceVsEma21Pct) : '—'} | ${r.pullbackDepth || '—'} | ${flowC} | ${fundC} |`);
    }
    L.push('');
    L.push('> Names with **both** a 🟢 flow confirm and a fund ✅ are the highest-conviction reversals — your setup with smart money already leaning in.');
  } else {
    L.push('_No pullback names showing a fresh reversal cross this run._');
  }
  L.push('');

  // ===== DOWNTREND-BREAKOUT WATCH (Mike's #1 setup) =====
  L.push('## 🔻→🟢 Downtrend-Breakout Watch');
  L.push('');
  L.push('_Multi-month falling trendlines (lower highs from a major peak) and where price sits vs that line today. **Confirmed** = fresh close-through (≤3 bars), ≤8% clearance, 2-of-3 vol/RSI/EMA confirm — actionable. **Extended / retest / forming** are context, clearly not-actionable. Fresh breaks (≤5 bars) are flagged 🆕 and are extension-exempt._');
  L.push('');
  if (dtbAll.length) {
    L.push(`| Ticker | Tier | Line today | Bars since | dtbScore (lineQ/fresh/vol/momo/ctx) | Spring? | Price vs line | RS20/RS60 | Flow/Fund confirm |`);
    L.push(`|---|---|---|---|---|---|---|---|---|`);
    for (const c of dtbAll.slice(0, 25)) {
      const d = c.dtb; const s = d.sub || {};
      const tierTxt = `${d.tier === 'confirmed' ? '✅ confirmed' : d.tier}${c.dtbFresh ? ' 🆕' : ''}`;
      const r = c.rs || {};
      const rsTxt = (r.rs20 != null || r.rs60 != null) ? `${r.rs20 != null ? pct(r.rs20) : '—'}/${r.rs60 != null ? pct(r.rs60) : '—'}` : '—';
      const flowC = c.flow && c.flow.net > 0 ? `${fmt$(c.flow.net)} 🟢` : (c.flow && c.flow.net < 0 ? `${fmt$(c.flow.net)} 🔴` : '—');
      const fundC = c.inst && /BUY/i.test(c.inst.direction) ? 'fund✅' : '';
      L.push(`| **${c.ticker}** | ${tierTxt} | $${d.lineToday} | ${d.bars_since_break ?? '—'} | ${d.dtbScore} (${s.lineQ}/${s.fresh}/${s.vol}/${s.momo}/${s.ctx}) | ${c.springFlag ? '🪤' : '—'} | ${pct(d.clearance_pct)} | ${rsTxt} | ${[flowC === '—' ? '' : flowC, fundC].filter(Boolean).join(' ') || '—'} |`);
    }
    L.push('');
    L.push('> Confirmed names with a 🟢 flow confirm + fund✅ are the highest conviction — see the 💎 Smart-Money-Early block at the top.');
  } else {
    L.push('_No downtrend-breakout signals in the scanned candidate set this run (no name has price at/above a qualifying multi-month falling trendline). Normal in a broad uptrend; the scan re-runs every pull._');
  }
  L.push('');

  // ===== EARNINGS THIS WEEK (blackout list) =====
  const earnSoonList = [...earnMap.entries()].filter(([, e]) => e.days != null && e.days >= 0 && e.days <= EARNINGS_BLACKOUT_DAYS).sort((a, b) => a[1].days - b[1].days);
  if (earnSoonList.length) {
    L.push('### 📅 Earnings this week (blackout)');
    L.push('');
    L.push('_Names reporting within the next ~5 sessions. Any of these appearing as a long idea above was **rank-capped** — don\'t open a fresh swing into a print._');
    L.push('');
    L.push(earnSoonList.slice(0, 30).map(([t, e]) => `\`${t}\` (${e.days}d${e.time ? ' ' + e.time : ''})`).join(' · '));
    L.push('');
  }

  // ===== CHARTS INDEX (for visual analysis) =====
  const chartEntries = Object.entries(charts);
  if (chartEntries.length) {
    L.push('## 📉 Charts rendered (open these for visual analysis)');
    L.push('');
    L.push('_90-day candles + EMA 8/21/55 + SMA200, volume, RSI. Read each PNG and check trend, structure, and where price sits vs the fast EMAs._');
    L.push('');
    for (const [t, p] of chartEntries) L.push(`- **${t}** — \`${p}\``);
    L.push('');
  }
  L.push('---');
  L.push(`_Raw JSON snapshots saved alongside this report under \`raw/\`. Charts under \`charts/\`. Re-run the skill any time for a fresh pull._`);
  return L.join('\n');
}

function legLabels(c) {
  const map = { screener: 'screener', flow_bull: 'flow🟢', flow_bear: 'flow🔴', inst_buy: 'funds-buy', inst_crossfund: 'cross-fund', cboe_new: 'new-CBOE', community_watch: 'watching👀', dtb_break: 'DTB🔻→🟢', rs_leader: 'RS-leader' };
  return [...c.legs].map((l) => map[l] || l).join(', ');
}

main().catch((e) => { console.error('gather.mjs fatal:', e); process.exit(1); });
