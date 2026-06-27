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

const __dirname = dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = resolve(__dirname, '..');

// ---- config ---------------------------------------------------------------
const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
const TIMEOUT_MS = Number(process.env.RECAP_TIMEOUT_MS || 60000);
const SCREENER_CONCURRENCY = 4;
const SHORTLIST_SIZE = Number(process.env.RECAP_SHORTLIST || 15);

// Flow thresholds (the "biggest flows" filter)
const FLOW_MIN_SCORE = 70;
const FLOW_MIN_PREMIUM = 50000;
const FLOW_PAGES = 3;          // pageSize 100 each -> up to 300 alerts
const FLOW_PAGE_SIZE = 100;

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

async function loadAgentKey() {
  if (process.env.AGENT_API_KEY) return process.env.AGENT_API_KEY.trim();
  const root = findRepoRoot(SKILL_DIR);
  const f = join(root, '.env_agent_api');
  if (existsSync(f)) {
    const raw = (await readFile(f, 'utf8')).trim();
    // file may be a bare token or KEY=value
    const m = raw.match(/^[A-Z_]+=(.*)$/);
    return (m ? m[1] : raw).trim();
  }
  return null;
}

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
  const AGENT_KEY = await loadAgentKey();
  const authHeaders = AGENT_KEY ? { Authorization: `Bearer ${AGENT_KEY}` } : {};
  const health = {}; // leg -> status string

  // candidate registry: TICKER -> { legs:Set, screeners:[], tech:{}, flow:{}, inst:{}, cboe:false, reversal:{} }
  const reg = new Map();
  const cand = (t) => {
    if (!reg.has(t)) reg.set(t, { ticker: t, legs: new Set(), screeners: [], tech: null, flow: null, inst: null, cboe: false, reversal: null, watch: null });
    return reg.get(t);
  };

  // === 1. SCREENERS ========================================================
  const list = await getJson(`${TD_BASE}/api/screeners`);
  let screenerIds = [];
  if (list.ok && list.data && Array.isArray(list.data.screeners)) {
    screenerIds = list.data.screeners.map((s) => ({ id: s.id, name: s.name }));
  } else {
    // fallback to known ids
    screenerIds = ['momentum', 'bullish-pullback', 'volatility-squeeze', 'small-cap', 'volatility-surge', 'gamma-scan', 'csp-wheel', 'leaps', 'leveraged', 'daily-cuts'].map((id) => ({ id, name: id }));
  }

  const screenerResults = {};
  await pool(screenerIds, SCREENER_CONCURRENCY, async ({ id, name }) => {
    const r = await getJson(`${TD_BASE}/api/screeners/${id}/run`);
    const rows = r.ok && r.data ? (r.data.results || r.data.data || []) : [];
    screenerResults[id] = { name, ok: r.ok, count: rows.length, error: r.error, rows };
    await saveRaw(`screener_${id}`, r.data ?? { error: r.error });
    if (!r.ok) return;
    for (const row of rows) {
      const t = sym(row);
      if (!t) continue;
      const c = cand(t);
      c.screeners.push({ id, name, grade: row.metrics?.entryGrade ?? null, score: row.metrics?.entryScore ?? null });
      c.legs.add('screener');
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
      // momentum-pullback reversal detection (the user's edge)
      if (isPullback) {
        const cross = (m.stochCrossover || '').toLowerCase() === 'yes';
        const sk = num(row.stochK);
        const bullZone = /bull/i.test(m.rsiZone || '');
        const grade = (m.entryGrade || '').toUpperCase();
        const goodGrade = /A|B/.test(grade.replace(/[^A-Z]/g, ''));
        const turningUp = sk != null && sk >= 10 && sk <= 50; // climbing out of oversold, not yet hot
        const reversing = cross && turningUp && (bullZone || goodGrade);
        if (reversing || cross) {
          c.reversal = {
            reversing, crossover: cross, stochK: sk, rsiZone: m.rsiZone ?? null,
            grade: m.entryGrade ?? null, entryScore: num(m.entryScore),
            pullbackDepth: m.pullbackDepth ?? null, priceVsEma21Pct: num(m.priceVsEma21Pct),
          };
        }
      }
    }
  });
  const screenerOk = Object.values(screenerResults).filter((s) => s.ok).length;
  health.screeners = `${screenerOk}/${screenerIds.length} ran`;

  // === 2. FLOW (biggest flows + smart money) ===============================
  const flowAlerts = [];
  let flowAuthFail = false;
  for (let p = 1; p <= FLOW_PAGES; p++) {
    const r = await getJson(
      `${TD_BASE}/api/agent/unusual-activity?minScore=${FLOW_MIN_SCORE}&minPremium=${FLOW_MIN_PREMIUM}&timeFrame=today&page=${p}&pageSize=${FLOW_PAGE_SIZE}`,
      { headers: authHeaders });
    if (!r.ok) { flowAuthFail = true; if (p === 1) await saveRaw('flow_error', { error: r.error, status: r.status }); break; }
    const rows = (r.data && r.data.data) || [];
    if (p === 1) await saveRaw('flow_page1', r.data);
    flowAlerts.push(...rows);
    if (rows.length < FLOW_PAGE_SIZE) break;
  }
  // repeats (institutional-conviction repeated strikes)
  const repeatsR = await getJson(`${TD_BASE}/api/unusual-activity/repeats?hours=24&limit=50`, { headers: authHeaders });
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
  for (const [t, g] of flowAgg) {
    g.net = g.bullPrem - g.bearPrem;
    g.dir = g.net > 0 ? 'Bullish' : (g.net < 0 ? 'Bearish' : 'Mixed');
    const meaningful = Math.abs(g.net) >= FLOW_MIN_PREMIUM && g.maxScore >= FLOW_MIN_SCORE;
    const c = cand(t); c.flow = g;
    // Only BULLISH net flow is a convergence leg (this is a long-idea finder).
    // Meaningful bearish flow is tracked as a conflict, never as agreement.
    if (meaningful && g.net > 0) c.legs.add('flow_bull');
    if (meaningful && g.net < 0) c.flowBearish = true;
  }
  health.flow = flowAuthFail && flowAlerts.length === 0
    ? `FAILED (${AGENT_KEY ? 'key rejected' : 'no AGENT_API_KEY'})`
    : `${flowAlerts.length} alerts, ${flowAgg.size} tickers`;

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
  health.cboe = cboeR.ok ? `${newListings.length} new optionable` : `FAILED (${cboeR.error})`;

  // === 3b. COMMUNITY WATCHING (TD Pro — what users are piling into) =========
  // Replaces the retired Discord "👀 is watching" scraper: pulls the community
  // watchlist leaderboard straight from TD Pro. Graceful — if the endpoint
  // isn't deployed yet (404) this leg simply degrades and the run is unaffected.
  const watchR = await getJson(
    `${TD_BASE}/api/agent/community/watching?timeframe=24h&limit=20`,
    { headers: authHeaders });
  await saveRaw('community_watching', watchR.data ?? { error: watchR.error, status: watchR.status });
  let communityWatch = [];
  if (watchR.ok && watchR.data && Array.isArray(watchR.data.tickers)) {
    communityWatch = watchR.data.tickers.filter((w) => w && w.ticker);
    for (const w of communityWatch) {
      // only a net-positive crowd lean (more adds than removes) is a bullish leg
      if ((w.net ?? 0) > 0) {
        const c = cand(String(w.ticker).toUpperCase());
        c.watch = { watchers: w.watchers ?? 0, adds: w.adds ?? 0, removes: w.removes ?? 0, net: w.net ?? 0 };
        c.legs.add('community_watch');
      }
    }
  }
  health.communityWatch = watchR.ok
    ? `${communityWatch.length} watched`
    : (watchR.status === 404 ? 'endpoint not live yet (pending deploy)' : `FAILED (${watchR.error})`);

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
      c.inst.funds = num(r.funds ?? r.fundCount);
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
    if (!c.inst) { c.inst = { direction: 'SELLING', weightDelta: num(r.weightDelta), funds: num(r.funds ?? r.fundCount), sector: r.sector ?? null }; }
  }
  health.hedgeFunds = briefR.ok
    ? `${topBuys.length} top buys, ${crossFund.length} cross-fund, ${instBuying.length} buying`
    : `FAILED (${briefR.error})`;

  // === 5. CONVERGENCE RANKING =============================================
  const BULLISH_LEGS = ['screener', 'flow_bull', 'inst_buy', 'inst_crossfund', 'cboe_new', 'community_watch'];
  const all = [...reg.values()].map((c) => {
    c.legCount = c.legs.size;
    const hasBullish = BULLISH_LEGS.some((l) => c.legs.has(l));
    // a name is conflicted when bullish sources disagree with bearish ones
    c.conflict = hasBullish && (c.flowBearish || c.instSelling);
    // only count aligned (bullish) flow magnitude toward the rank
    const alignedFlowMag = c.flow && c.flow.net > 0 ? c.flow.net : 0;
    const entry = c.tech?.entryScore || 0;
    const revBoost = c.reversal?.reversing ? 1 : 0;
    c.rankScore = c.legCount * 1e12 + revBoost * 5e11 - (c.conflict ? 2.5e11 : 0) + alignedFlowMag + entry * 1e6;
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
  let enriched = 0;
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
    enriched++;
  });
  health.enrich = `${enriched}/${needEnrich.length} flow/fund names enriched`;

  // affordable (sub-threshold price) convergence names — surfaced separately so
  // the recap isn't all $700+ mega-caps. `all` is already rankScore-sorted.
  const affordable = all
    .filter((c) => c.tech?.price != null && c.tech.price > 0 && c.tech.price <= MAX_AFFORDABLE_PRICE)
    .filter((c) => c.legCount >= 2 || c.reversal?.reversing || /A|B/.test((c.tech?.entryGrade || '').replace(/[^A-Z]/g, '')))
    .slice(0, 10);

  // === 5c. RENDER CHARTS — top-5 convergence + reversal-watch + top-3 affordable
  const chartSyms = [...new Set([
    ...shortlist.slice(0, 5).map((c) => c.ticker),
    ...reversalWatch.map((c) => c.ticker),
    ...affordable.slice(0, 3).map((c) => c.ticker),
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
    communityWatch,
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
  return { ticker: c.ticker, legs: [...c.legs], legCount: c.legCount, screeners: c.screeners, tech: c.tech, flow: c.flow, inst: c.inst, cboe: c.cboe, reversal: c.reversal };
}

// ---- report builder -------------------------------------------------------
function buildReport(ctx) {
  const { stamp, now, TD_BASE, TT_BASE, health, flowAgg, newListings,
    topBuys, topSells, crossFund, streaks, screenerResults, shortlist, reversalWatch, charts = {}, affordable = [],
    communityWatch = [] } = ctx;
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
  L.push(`| Screeners (TD Pro) | ${health.screeners || '—'} |`);
  L.push(`| Options flow (TD Pro agent) | ${health.flow || '—'} |`);
  L.push(`| New CBOE listings (TD Pro) | ${health.cboe || '—'} |`);
  L.push(`| Community watching (TD Pro) | ${health.communityWatch || '—'} |`);
  L.push(`| Hedge funds / 13F (TickerTrace) | ${health.hedgeFunds || '—'} |`);
  L.push(`| Technicals enrichment | ${health.enrich || '—'} |`);
  L.push(`| Charts rendered | ${health.charts || '—'} |`);
  L.push('');

  // ===== RECAP =====
  L.push('## 📊 Market Recap');
  L.push('');

  // flow
  const flows = [...flowAgg.values()].sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
  const totBull = flows.reduce((s, f) => s + f.bullPrem, 0);
  const totBear = flows.reduce((s, f) => s + f.bearPrem, 0);
  L.push('### 💰 Options flow (biggest premium today)');
  L.push('');
  L.push(`Total bullish premium **${fmt$(totBull)}** vs bearish **${fmt$(totBear)}** across tracked alerts.`);
  L.push('');
  if (flows.length) {
    L.push(`| Ticker | Net flow | Dir | Top trade | Score | Inst-α | Repeat |`);
    L.push(`|---|---|---|---|---|---|---|`);
    for (const f of flows.slice(0, 10)) {
      L.push(`| **${f.ticker}** | ${fmt$(f.net)} | ${f.dir} | ${f.topTradeType || '—'} | ${f.maxScore} | ${f.instAlpha ? '🛡️' : ''} | ${f.repeat > 1 ? '🔁×' + f.repeat : ''} |`);
    }
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
      L.push(crossFund.slice(0, 6).map((r) => `\`${sym(r)}\` (${r.funds ?? r.providers ?? '?'} funds${/sell/i.test(r.direction || '') ? ', selling' : ', buying'})`).join(' · '));
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

  // community watching (TD Pro members)
  L.push('### 👀 What TD Pro people are watching');
  L.push('');
  if (communityWatch && communityWatch.length) {
    const top = communityWatch.slice(0, 12);
    L.push('_Tickers TD Pro members are piling into (net watchlist adds, last 24h). Net-positive names count as a bullish convergence leg._');
    L.push('');
    L.push(top.map((w) => `\`${w.ticker}\` (+${w.net}${w.watchers ? `, ${w.watchers} ppl` : ''})`).join(' · '));
    L.push('');
  } else {
    const why = (health.communityWatch || '').includes('not live')
      ? '_Community-watch endpoint not deployed yet — leg pending (will light up after the TD Pro deploy)._'
      : '_No community-watch data this run._';
    L.push(why);
    L.push('');
  }

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
  L.push(`_Ranked by how many independent sources point at the same ticker. ${shortlist.length} names._`);
  L.push('');
  if (shortlist.length) {
    L.push(`| # | Ticker | Legs | Sources | Price | Tech (RSI/ADX/Stoch) | Grade | Flow | Hedge funds | Edge |`);
    L.push(`|---|---|---|---|---|---|---|---|---|---|`);
    shortlist.forEach((c, i) => {
      const t = c.tech || {};
      const sources = legLabels(c);
      const tech = `${t.rsi != null ? t.rsi.toFixed(0) : '—'}/${t.adx != null ? t.adx.toFixed(0) : '—'}/${t.stochK != null ? t.stochK.toFixed(0) : '—'}`;
      const flow = c.flow && Math.abs(c.flow.net) >= 1 ? `${fmt$(c.flow.net)} ${c.flow.dir}${c.flow.instAlpha ? ' 🛡️' : ''}` : '—';
      const inst = c.inst ? `${c.inst.direction}${c.inst.funds ? ' (' + c.inst.funds + ')' : ''}` : '—';
      const edge = [c.reversal?.reversing ? '🔄 reversing' : '', c.conflict ? '⚠️ conflict' : ''].filter(Boolean).join(' ');
      L.push(`| ${i + 1} | **${c.ticker}** | ${c.legCount} | ${sources} | ${t.price != null ? '$' + t.price.toFixed(2) : '—'} | ${tech} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    });
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
      if (c.reversal?.reversing) L.push(`- 🔄 **Reversing out of pullback** — stoch crossover up, StochK ${c.reversal.stochK?.toFixed(0)}, ${c.reversal.rsiZone || ''}, ${c.reversal.grade || ''}`);
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
      const edge = [c.reversal?.reversing ? '🔄 reversing' : '', c.conflict ? '⚠️ conflict' : '', c.chartPath ? '📉' : ''].filter(Boolean).join(' ');
      L.push(`| **${c.ticker}** | $${t.price.toFixed(2)} | ${c.legCount} | ${legLabels(c)} | ${tech} | ${t.entryGrade || '—'} | ${flow} | ${inst} | ${edge} |`);
    }
  } else {
    L.push(`_No qualifying names under $${MAX_AFFORDABLE_PRICE} this run._`);
  }
  L.push('');

  // ===== REVERSAL WATCH (the edge) =====
  L.push('## 🔄 Momentum Pullback — Reversal Watch');
  L.push('');
  L.push('_Your edge: pullback names that are **starting to reverse out** (stochastic crossing up from oversold, RSI turning bullish, A/B entry grade)._');
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
  const map = { screener: 'screener', flow_bull: 'flow🟢', flow_bear: 'flow🔴', inst_buy: 'funds-buy', inst_crossfund: 'cross-fund', cboe_new: 'new-CBOE', community_watch: 'watching👀' };
  return [...c.legs].map((l) => map[l] || l).join(', ');
}

main().catch((e) => { console.error('gather.mjs fatal:', e); process.exit(1); });
