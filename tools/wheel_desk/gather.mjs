#!/usr/bin/env node
// wheel_desk / gather.mjs
// Nightly data pull for The Wheel Desk. Runs every TMPro screener at DEFAULT
// settings, then enriches the CSP rows with the things a screen can't see:
// trend + support from 260 days of bars, which income ETFs hold/wrote options
// on the name (TickerTrace), weekly institutional buying, cross-screen overlap,
// and a return-correlation cluster so six bitcoin miners read as ONE bet.
//
// Writes data/wheel-desk/<date>/packet.json + packet.md. The grading is NOT
// done here — the cron session reads packet.md and grades every setup itself.
//
// Usage: node tools/wheel_desk/gather.mjs [--mode auto|sunday|daily|thursday] [--date YYYY-MM-DD]

import { writeFile, mkdir, readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const TT_BASE = process.env.TICKERTRACE_API_URL || 'https://api.tickertrace.pro/api/v1';
const TIMEOUT_MS = Number(process.env.DESK_TIMEOUT_MS || 90000);

// The Railway WAF 403s Node's default UA; curl-style/browser UAs pass.
const BASE_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
  Accept: 'application/json',
};

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, all) => {
    if (a.startsWith('--')) acc.push([a.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : true]);
    return acc;
  }, []),
);

function chicagoNow() {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short',
  }).formatToParts(new Date());
  const get = (t) => parts.find((p) => p.type === t).value;
  return { date: `${get('year')}-${get('month')}-${get('day')}`, weekday: get('weekday') };
}

const now = chicagoNow();
const DATE = args.date || now.date;
const WEEKDAY = args.date ? new Date(`${args.date}T12:00:00Z`).toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' }) : now.weekday;
// Sunday = full playbook, Thursday = Friday-expiry gamma read, else the daily CSP top list.
const MODE = args.mode && args.mode !== 'auto'
  ? args.mode
  : WEEKDAY === 'Sun' ? 'sunday' : WEEKDAY === 'Thu' ? 'thursday' : 'daily';
const OUT = join(ROOT, 'data', 'wheel-desk', DATE);

async function loadAgentKey() {
  if (process.env.AGENT_API_KEY) return process.env.AGENT_API_KEY.trim();
  const f = join(ROOT, '.env_agent_api');
  if (!existsSync(f)) return null;
  const raw = (await readFile(f, 'utf8')).trim();
  const m = raw.match(/^[A-Z_]+=(.*)$/);
  return (m ? m[1] : raw).trim();
}

async function getJson(url, headers = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { headers: { ...BASE_HEADERS, ...headers }, signal: ctrl.signal });
    const text = await res.text();
    let data = null;
    try { data = JSON.parse(text); } catch { /* non-json */ }
    return res.ok ? { ok: true, data } : { ok: false, status: res.status, error: data?.error || text.slice(0, 200) };
  } catch (e) {
    return { ok: false, error: e.name === 'AbortError' ? `timeout ${TIMEOUT_MS}ms` : e.message };
  } finally {
    clearTimeout(t);
  }
}

async function pool(items, size, fn) {
  const out = new Array(items.length);
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(size, items.length) }, async () => {
    while (i < items.length) { const k = i++; out[k] = await fn(items[k], k); }
  }));
  return out;
}

const r2 = (x) => (x == null || !Number.isFinite(x) ? null : Math.round(x * 100) / 100);
const pct = (a, b) => (a == null || b == null || !b ? null : r2(((a - b) / b) * 100));

// --- chart-derived context ---------------------------------------------------
function chartContext(rows, strike) {
  const bars = rows.filter((b) => b && b.close != null);
  if (bars.length < 30) return null;
  const last = bars[bars.length - 1];
  const closes = bars.map((b) => b.close);
  const yr = bars.slice(-252);
  const hi52 = Math.max(...yr.map((b) => b.high ?? b.close));
  const lo52 = Math.min(...yr.map((b) => b.low ?? b.close));
  const at = (n) => closes[closes.length - 1 - n];
  // Lowest low of the last 60 sessions = the nearest real floor a put seller leans on.
  const low60 = Math.min(...bars.slice(-60).map((b) => b.low ?? b.close));
  const trend =
    last.close > last.sma50 && last.sma50 > last.sma200 ? 'uptrend'
      : last.close < last.sma50 && last.sma50 < last.sma200 ? 'downtrend'
        : 'mixed';
  return {
    close: last.close,
    asOf: last.date,
    chg5d: pct(last.close, at(5)),
    chg20d: pct(last.close, at(20)),
    chg60d: pct(last.close, at(60)),
    vs21ema: pct(last.close, last.ema21),
    vs50sma: pct(last.close, last.sma50),
    vs200sma: pct(last.close, last.sma200),
    trend,
    pctFrom52wHigh: pct(last.close, hi52),
    pctAbove52wLow: pct(last.close, lo52),
    rangePos52w: r2(((last.close - lo52) / (hi52 - lo52 || 1)) * 100),
    atrPct: r2((last.atr / last.close) * 100),
    strikeVs60dLow: strike != null ? pct(strike, low60) : null,
    strikeBelowSma200: strike != null && last.sma200 ? strike < last.sma200 : null,
    strikeAtrsOTM: strike != null && last.atr ? r2((last.close - strike) / last.atr) : null,
    rsi: r2(last.rsi),
    adx: r2(last.adx),
    returns: closes.slice(-61).map((c, i, a) => (i ? Math.log(c / a[i - 1]) : null)).slice(1),
  };
}

function corr(a, b) {
  const n = Math.min(a.length, b.length);
  if (n < 20) return null;
  const x = a.slice(-n), y = b.slice(-n);
  const mx = x.reduce((s, v) => s + v, 0) / n, my = y.reduce((s, v) => s + v, 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i++) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; }
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : null;
}

// Complete-linkage clusters on 60d daily-return correlation: two groups merge
// only if EVERY cross pair clears the threshold. Single-linkage chained the
// 2026-09-27 list into one 12-name blob (miners -> APLD -> SMCI -> quantum ->
// ONDS), which says nothing; complete linkage keeps miners and quantum apart.
function clusters(rows, threshold = 0.7) {
  const withRet = rows.filter((r) => r.chart?.returns?.length >= 20);
  const c = new Map();
  const pairs = [];
  for (let i = 0; i < withRet.length; i++) {
    for (let j = i + 1; j < withRet.length; j++) {
      const v = corr(withRet[i].chart.returns, withRet[j].chart.returns);
      c.set(`${withRet[i].ticker}|${withRet[j].ticker}`, v);
      c.set(`${withRet[j].ticker}|${withRet[i].ticker}`, v);
      if (v != null && v >= 0.6) pairs.push([withRet[i].ticker, withRet[j].ticker, r2(v)]);
    }
  }
  let groups = withRet.map((r) => [r.ticker]);
  const link = (a, b) => Math.min(...a.flatMap((x) => b.map((y) => c.get(`${x}|${y}`) ?? -1)));
  for (;;) {
    let best = null;
    for (let i = 0; i < groups.length; i++) {
      for (let j = i + 1; j < groups.length; j++) {
        const l = link(groups[i], groups[j]);
        if (l >= threshold && (!best || l > best.l)) best = { i, j, l };
      }
    }
    if (!best) break;
    groups[best.i] = groups[best.i].concat(groups[best.j]);
    groups.splice(best.j, 1);
  }
  return { threshold, groups: groups.filter((g) => g.length > 1), pairs: pairs.sort((a, b) => b[2] - a[2]) };
}

// --- TickerTrace: who holds/wrote options on the name -----------------------
function summarizeFundLegs(tt, strike, spot) {
  const funds = tt?.funds || [];
  const legs = [];
  for (const f of funds) {
    for (const l of f.legs || []) {
      legs.push({
        fund: f.fund,
        type: l.optionType,
        strike: l.strike,
        expiry: l.expiry,
        contracts: l.contracts,
        side: l.contracts < 0 ? 'short' : 'long',
      });
    }
  }
  // Group each fund's legs on one expiry into a structure (a long+short put pair is a spread).
  const byFundExp = new Map();
  for (const l of legs) {
    const k = `${l.fund}|${l.expiry}`;
    if (!byFundExp.has(k)) byFundExp.set(k, []);
    byFundExp.get(k).push(l);
  }
  const structures = [...byFundExp.entries()].map(([k, ls]) => {
    const [fund, expiry] = k.split('|');
    const text = ls
      .sort((a, b) => a.strike - b.strike)
      .map((l) => `${l.side === 'short' ? '-' : '+'}${Math.abs(l.contracts)} ${l.strike}${l.type[0]}`)
      .join(' / ');
    const puts = ls.filter((l) => l.type === 'PUT').map((l) => l.strike);
    return {
      fund, expiry, text,
      nearestPutStrike: puts.length ? puts.reduce((a, b) => (Math.abs(b - strike) < Math.abs(a - strike) ? b : a)) : null,
    };
  });
  const puts = legs.filter((l) => l.type === 'PUT');
  return {
    fundCount: funds.length,
    structures,
    // Is any fund's put exposure at or below OUR strike (they share our downside zone)?
    putsAtOrBelowOurStrike: puts.filter((l) => strike != null && l.strike <= strike * 1.02).length,
    nearestFundPutPctFromSpot: puts.length && spot
      ? r2(Math.min(...puts.map((l) => Math.abs(pct(l.strike, spot)))))
      : null,
  };
}

// --- main ---------------------------------------------------------------------
async function main() {
  await mkdir(join(OUT, 'raw'), { recursive: true });
  const key = await loadAgentKey();
  const auth = key ? { Authorization: `Bearer ${key}` } : {};
  const health = {};

  // 1. Every screener at defaults.
  const list = await getJson(`${TD_BASE}/api/screeners`);
  const ids = list.ok ? list.data.screeners.map((s) => s.id) : [
    'bullish-pullback', 'momentum', 'volatility-squeeze', 'small-cap', 'volatility-surge',
    'gamma-scan', 'csp-wheel', 'cc-wheel', 'leaps', 'leveraged', 'daily-cuts', 'accumulation-watch',
  ];
  const screens = {};
  await pool(ids, 4, async (id) => {
    const r = await getJson(`${TD_BASE}/api/screeners/${id}/run`);
    const rows = r.ok ? (r.data?.results || []) : [];
    screens[id] = { ok: r.ok, error: r.ok ? undefined : r.error, count: rows.length, rows };
    await writeFile(join(OUT, 'raw', `screen_${id}.json`), JSON.stringify(r.ok ? r.data : r, null, 1));
  });
  health.screeners = `${Object.values(screens).filter((s) => s.ok).length}/${ids.length} ran`;

  const tickerScreens = new Map();
  for (const [id, s] of Object.entries(screens)) {
    for (const row of s.rows) {
      const t = (row.symbol || row.ticker || '').toUpperCase();
      if (!t) continue;
      if (!tickerScreens.has(t)) tickerScreens.set(t, []);
      tickerScreens.get(t).push(id);
    }
  }

  // 2. Weekly institutional buying/selling (TickerTrace, 62 active-equity funds, income funds excluded).
  const inst = await getJson(`${TT_BASE}/institutional?period=weekly&limit=40`);
  await writeFile(join(OUT, 'raw', 'tt_institutional_weekly.json'), JSON.stringify(inst.data ?? inst, null, 1));
  const instBuy = new Map((inst.data?.buying || []).map((b) => [b.ticker, b]));
  const instSell = new Map((inst.data?.selling || []).map((b) => [b.ticker, b]));
  health.institutional = inst.ok ? `asOf ${inst.data.asOfDate}, ${inst.data.buying?.length || 0} buying` : `FAILED ${inst.error}`;

  // 3. CSP rows → enrich.
  const cspRows = (screens['csp-wheel']?.rows || []).map((row) => {
    const m = row.metrics || {};
    return {
      ticker: row.symbol,
      price: row.price,
      sector: m.sector, industry: m.industry,
      marketCap: row.marketCap,
      strike: m.strike, expiry: m.expiry, dte: m.dte,
      premium: m.premiumRaw, perShare: m.premiumRaw != null ? r2(m.premiumRaw / 100) : null,
      collateral: m.capitalRaw,
      rocWeekly: m.rocWeekly, rocTotal: m.rocTotal, annualized: m.annualizedReturn,
      delta: m.deltaRaw, breakeven: m.breakevenRaw, cushionPct: m.breakevenPct,
      strikeOTMPct: pct(m.strike, row.price),
      pop: m.profitProbability,
      iv: m.ivRaw, ivRank: m.ivRank52w, ivRankZone: m.ivRank52wZone,
      quoteQuality: m.quoteQuality, optVolume: m.optVolume, supportOI: m.supportOI,
      earnings: { inWindow: !!m.earningsInWindow, date: m.earningsDate },
      screen: { grade: m.grade, score: m.score, setup: m.tradeSetup },
      rsi: r2(row.rsi), adx: r2(row.adx),
    };
  });

  await pool(cspRows, 6, async (r) => {
    const [chart, tt, ivr] = await Promise.all([
      getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(r.ticker)}/chart-data?days=300`, auth),
      getJson(`${TT_BASE}/options/${encodeURIComponent(r.ticker)}`),
      // The REST screener skips the IV-rank enrichment the MCP tool adds, so fetch it.
      r.ivRank == null ? getJson(`${TD_BASE}/api/agent/ticker/${encodeURIComponent(r.ticker)}/iv-rank`, auth) : null,
    ]);
    if (ivr?.ok && ivr.data?.ivRank != null) {
      r.ivRank = r2(ivr.data.ivRank);
      r.ivRankZone = ivr.data.ivRankZone;
      r.ivRankSample = ivr.data.sampleSize;
      r.ivRankSource = ivr.data.source;
    }
    const rows = chart.ok ? (chart.data?.chartData || chart.data?.data || []) : [];
    r.chart = chartContext(rows, r.strike);
    // 404 "No tracked fund holds options on X" is an answer, not a failure.
    r.fundOptions = tt.ok ? summarizeFundLegs(tt.data, r.strike, r.price)
      : tt.status === 404 ? { fundCount: 0, structures: [], putsAtOrBelowOurStrike: 0, nearestFundPutPctFromSpot: null }
        : { error: tt.error };
    r.alsoOn = (tickerScreens.get(r.ticker) || []).filter((id) => id !== 'csp-wheel');
    const b = instBuy.get(r.ticker), s = instSell.get(r.ticker);
    r.institutional = b ? { dir: 'buying', weightDelta: b.weightDelta, fundCount: b.fundCount, funds: b.funds }
      : s ? { dir: 'selling', weightDelta: s.weightDelta, fundCount: s.fundCount, funds: s.funds } : null;
  });
  health.chart = `${cspRows.filter((r) => r.chart).length}/${cspRows.length} charts`;
  health.tickertrace = `${cspRows.filter((r) => r.fundOptions && !r.fundOptions.error).length}/${cspRows.length} option lookups`;

  const cl = clusters(cspRows);
  for (const r of cspRows) {
    const g = cl.groups.find((grp) => grp.includes(r.ticker));
    r.cluster = g ? g.slice().sort().join('+') : null;
    if (r.chart) delete r.chart.returns; // only needed for clustering
  }

  // 4. Gamma scan (Thursday focus: Friday-expiry pins), trimmed.
  const gamma = (screens['gamma-scan']?.rows || []).map((row) => ({
    ticker: row.symbol, price: row.price, changePct: row.changePct,
    expiration: row.metrics?.expiration, walls: row.metrics?.wallSummary,
    topWall: `${row.metrics?.topWallType} ${row.metrics?.topWallStrike} (${row.metrics?.topWallOIFormatted}) ${row.metrics?.topWallPosition} ${row.metrics?.topWallPctAway}%`,
    atrsToWall: row.metrics?.atrsToWall, regime: row.metrics?.gammaRegime,
    flip: row.metrics?.gammaFlipLevel, pctToFlip: row.metrics?.gammaPctToFlip,
    squeeze: row.metrics?.squeezeScore, ivRankZone: row.metrics?.ivRank52wZone,
  }));

  // 5. Institutional digest with artifact flags (single-fund moves and non-US
  //    local tickers are the usual fakes: a new fund's first file reads as "buying").
  const flagInst = (b) => {
    const flags = [];
    if (b.fundCount < 2) flags.push('single-fund');
    if (!/^[A-Z]{1,5}(\.[A-Z])?$/.test(b.ticker)) flags.push('non-US ticker');
    if (!b.previousBlendedWeight) flags.push('new position (first file?)');
    return { ticker: b.ticker, name: b.name, sector: b.sector, weightDelta: r2(b.weightDelta), fundCount: b.fundCount, funds: b.funds, flags };
  };
  const institutional = inst.ok ? {
    asOf: inst.data.asOfDate, fundCount: inst.data.fundCount,
    buying: (inst.data.buying || []).map(flagInst),
    selling: (inst.data.selling || []).map(flagInst),
  } : null;

  const packet = {
    desk: 'wheel-desk', version: 1, date: DATE, weekday: WEEKDAY, mode: MODE,
    generatedAt: new Date().toISOString(), health,
    screensSummary: Object.fromEntries(Object.entries(screens).map(([id, s]) => [id, {
      ok: s.ok, count: s.count, tickers: s.rows.slice(0, 25).map((r) => r.symbol || r.ticker),
    }])),
    csp: cspRows,
    clusters: cl,
    gamma,
    institutional,
  };
  await writeFile(join(OUT, 'packet.json'), JSON.stringify(packet, null, 1));
  await writeFile(join(OUT, 'packet.md'), renderMd(packet));
  console.log(JSON.stringify({ out: OUT, mode: MODE, health, csp: cspRows.length, clusters: cl.groups }, null, 1));
}

function renderMd(p) {
  const L = [];
  L.push(`# Wheel Desk packet ${p.date} (${p.weekday}, mode=${p.mode})`, '');
  L.push(`Health: ${Object.entries(p.health).map(([k, v]) => `${k} ${v}`).join(' | ')}`, '');
  L.push('## Screens (defaults)');
  for (const [id, s] of Object.entries(p.screensSummary)) L.push(`- ${id}: ${s.ok ? s.count : 'FAILED'} ${s.tickers.slice(0, 12).join(' ')}`);
  L.push('', `## Correlation clusters (60d daily returns, complete linkage >= ${p.clusters.threshold}): ${p.clusters.groups.map((g) => g.join('+')).join(' | ') || 'none'}`, '');
  L.push('## CSP setups');
  for (const r of p.csp) {
    const c = r.chart || {};
    const fo = r.fundOptions || {};
    L.push(`### ${r.ticker} — Sell ${r.strike}P ${r.expiry} (${r.dte}d) @ ${r.perShare}  [screen ${r.screen.grade}/${r.screen.score}]`);
    L.push(`px ${r.price} · OTM ${r.strikeOTMPct}% · BE ${r.breakeven} (${r.cushionPct}%) · Δ ${r.delta} · PoP ${r.pop}% · ${r.rocWeekly}%/wk · collateral $${r.collateral}`);
    L.push(`IV ${r.iv} · IVR ${r.ivRank} (${r.ivRankZone}, n=${r.ivRankSample}, ${r.ivRankSource}) · quote ${r.quoteQuality} · optVol ${r.optVolume} · OI floor ${r.supportOI} · earnings ${r.earnings.inWindow ? r.earnings.date : 'clear'}`);
    L.push(`trend ${c.trend} · 5d ${c.chg5d}% 20d ${c.chg20d}% 60d ${c.chg60d}% · vs21e ${c.vs21ema}% vs50 ${c.vs50sma}% vs200 ${c.vs200sma}% · 52w pos ${c.rangePos52w}% (${c.pctFrom52wHigh}% from high) · ATR ${c.atrPct}% · strike ${c.strikeAtrsOTM} ATRs OTM, vs 60d low ${c.strikeVs60dLow}%, below 200sma ${c.strikeBelowSma200} · RSI ${c.rsi} ADX ${c.adx}`);
    L.push(`sector ${r.sector} / ${r.industry} · cluster ${r.cluster || '-'} · also on: ${r.alsoOn.join(', ') || '-'} · inst: ${r.institutional ? `${r.institutional.dir} ${r.institutional.weightDelta} (${r.institutional.fundCount} funds)` : '-'}`);
    L.push(`fund options (TickerTrace): ${fo.error ? `ERR ${fo.error}` : fo.fundCount ? fo.structures.map((s) => `${s.fund} ${s.expiry}: ${s.text}`).join(' ; ') : 'none'}`, '');
  }
  L.push('## Gamma scan (defaults)');
  for (const g of p.gamma.slice(0, 15)) L.push(`- ${g.ticker} ${g.price} (${g.changePct}%) exp ${g.expiration} · ${g.topWall} · ${g.atrsToWall} ATRs · ${g.regime} flip ${g.flip} (${g.pctToFlip}%) · walls ${g.walls}`);
  if (p.institutional) {
    L.push('', `## Institutional weekly (TickerTrace, asOf ${p.institutional.asOf}, ${p.institutional.fundCount} funds)`);
    L.push('Buying:');
    for (const b of p.institutional.buying.slice(0, 20)) L.push(`- ${b.ticker} (${b.name}) +${b.weightDelta} · ${b.fundCount} funds ${b.flags.length ? `⚠ ${b.flags.join(', ')}` : ''}`);
    L.push('Selling:');
    for (const b of p.institutional.selling.slice(0, 10)) L.push(`- ${b.ticker} (${b.name}) ${b.weightDelta} · ${b.fundCount} funds ${b.flags.length ? `⚠ ${b.flags.join(', ')}` : ''}`);
  }
  return L.join('\n') + '\n';
}

main().catch((e) => { console.error(e); process.exit(1); });
