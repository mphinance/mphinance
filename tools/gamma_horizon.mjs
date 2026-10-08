#!/usr/bin/env node
// gamma_horizon.mjs -- the swing-trader cousin of Tomorrow's Map.
//
// Daily candles on the left, the next ~2 months of option expiries on the
// right. Each expiry is drawn at its own date with its own call wall, put wall,
// flip and heaviest strike, inside the options-implied expected-move cone. The
// three roads (up / down / range) are built only from expiries that carry real
// open interest, so a sleepy weekly cannot bend the path.
//
//   node tools/gamma_horizon.mjs ASTS --out /tmp/gamma
//
// Flags: --days N (forward horizon, default 60), --bars N (daily candles,
// default 65), --minshare PCT (OI share an expiry needs to steer a road,
// default 5), --out DIR.
//
// No ledger. Tomorrow's Map grades itself nightly; a two-month map cannot be
// graded until its expiries roll off, and that is a separate build.

import { readFileSync, mkdirSync, existsSync, writeFileSync, readdirSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { homedir } from 'os';

const PW_HOME = join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs');
const { chromium } = await import(existsSync(PW_HOME) ? PW_HOME : 'playwright');

const DEV_BASE = 'https://api.traderdaddy.pro/api/v1';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';
const C = {
  bg: '#0a0a0e', panel: '#101018', line: '#1c1c28', text: '#e6e6ee', dim: '#8a8aa0',
  call: '#00d68f', put: '#ff4d6d', flip: '#a855f7', pin: '#ffb000',
  green: '#00ff88', coral: '#ff5c6c', ema: '#4cc9f0', sma: '#8a8aa0',
  kc: '#2dd4bf', tp: '#ffd23f', stop: '#ff6b6b', entry: '#2dd4bf',
};

function repoRoot(start) {
  let d = resolve(start);
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(d, '.env_td_api'))) return d;
    const up = dirname(d);
    if (up === d) break;
    d = up;
  }
  return null;
}
const ROOT = repoRoot(process.cwd()) || repoRoot(new URL('.', import.meta.url).pathname);
const KEY = readFileSync(join(ROOT, '.env_td_api'), 'utf8').trim();

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const api = async (path, tries = 4) => {
  for (let n = 1; ; n++) {
    const r = await fetch(`${DEV_BASE}${path}`, {
      headers: { 'X-API-Key': KEY, 'User-Agent': UA },
      signal: AbortSignal.timeout(30000),
    });
    const j = await r.json().catch(() => ({}));
    if (j.success) return j.data;
    const limited = r.status === 429 || /requests per minute/i.test(j.message || j.error || '');
    if (!limited || n >= tries) throw new Error(`${path}: ${j.message || j.error || r.status}`);
    console.log(`rate limited, waiting ${20 * n}s (attempt ${n}/${tries})`);
    await sleep(20000 * n);
  }
};

// ── args ────────────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const sym = (argv.find((a) => !a.startsWith('--')) || 'SPY').toUpperCase();
const arg = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const OUT = arg('out', '/tmp/gamma');
const HORIZON = parseInt(arg('days', '60'), 10);
const BARS = parseInt(arg('bars', '65'), 10);
const MIN_SHARE = parseFloat(arg('minshare', '5'));

// ── plan ledger ─────────────────────────────────────────────────────────────
// Every plan this tool draws is written down and graded against the daily
// bars that follow, the same discipline as Tomorrow's Map: grades are durable
// once a plan resolves, and no hit rate is printed before MIN_GRADED plans
// have resolved with a fill. Do not lower that to make a post look better.
const LEDGER_DIR = join(ROOT, 'data/gamma_maps/horizon');
const MIN_GRADED = 10;
const etNow = () => {
  const f = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hour12: false })
    .formatToParts(new Date()).reduce((a, x) => ((a[x.type] = x.value), a), {});
  return { date: `${f.year}-${f.month}-${f.day}`, hour: parseInt(f.hour, 10) };
};
const dailyBars = async (s) => {
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${s}?interval=1d&range=1y`, {
    headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000),
  }).then((x) => x.json());
  const res = r?.chart?.result?.[0];
  if (!res?.timestamp) return null;
  const qq = res.indicators.quote[0];
  return res.timestamp.map((t, i) => ({
    d: new Date(t * 1000).toISOString().slice(0, 10), o: qq.open[i], h: qq.high[i], l: qq.low[i], c: qq.close[i],
  })).filter((b) => b.o != null && b.c != null);
};
// A plan fills on the first session after it was drawn whose low reaches the
// zone AND whose close holds the bottom of it (the "daily close that holds"
// rule printed on the chart). After the fill day: stop first if a bar touches
// both stop and T1, because a daily bar cannot say which came first.
const TERMINAL = new Set(['T1', 'STOP', 'EXPIRED', 'NO FILL']);
function gradePlan(e, bars) {
  if (TERMINAL.has(e.result?.status)) return e.result;
  const { date: today, hour } = etNow();
  const closed = bars.filter((b) => b.d > e.madeOn && b.d <= e.horizon && (b.d < today || hour >= 16));
  const p = e.plan;
  let filledOn = null, t2Hit = false;
  for (const b of closed) {
    if (!filledOn) {
      if (b.l <= p.entryHi && b.c >= p.entryLo) filledOn = b.d;
      continue;
    }
    if (b.l <= p.stop) return { status: 'STOP', filledOn, resolvedOn: b.d, ret: +((p.stop / p.mid - 1) * 100).toFixed(2) };
    if (b.h >= p.t1) {
      t2Hit = b.h >= p.t2;
      return { status: 'T1', filledOn, resolvedOn: b.d, t2Hit, ret: +(((t2Hit ? p.t2 : p.t1) / p.mid - 1) * 100).toFixed(2) };
    }
  }
  const pastHorizon = today > e.horizon || (today === e.horizon && hour >= 16);
  if (pastHorizon) {
    if (!filledOn) return { status: 'NO FILL' };
    const lastC = closed[closed.length - 1].c;
    return { status: 'EXPIRED', filledOn, resolvedOn: e.horizon, ret: +((lastC / p.mid - 1) * 100).toFixed(2) };
  }
  return { status: filledOn ? 'OPEN' : 'WAITING', filledOn };
}
const readLedger = (s) => {
  const f = join(LEDGER_DIR, `${s}.json`);
  return existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : [];
};
const writeLedger = (s, rows) => {
  mkdirSync(LEDGER_DIR, { recursive: true });
  writeFileSync(join(LEDGER_DIR, `${s}.json`), JSON.stringify(rows, null, 2) + '\n');
};
function recordSummary() {
  if (!existsSync(LEDGER_DIR)) return { resolved: 0, open: 0, t1: 0, stop: 0, expired: 0, nofill: 0 };
  const all = readdirSync(LEDGER_DIR).filter((f) => f.endsWith('.json')).flatMap((f) => JSON.parse(readFileSync(join(LEDGER_DIR, f), 'utf8')));
  const st = (k) => all.filter((e) => e.result?.status === k).length;
  const t1 = st('T1'), stop = st('STOP'), expired = st('EXPIRED');
  return { resolved: t1 + stop + expired, open: st('OPEN') + st('WAITING'), t1, stop, expired, nofill: st('NO FILL') };
}

// --grade: re-grade every ledger and print the scorecard, no chart.
if (argv.includes('--grade')) {
  const files = existsSync(LEDGER_DIR) ? readdirSync(LEDGER_DIR).filter((f) => f.endsWith('.json')) : [];
  for (const f of files) {
    const s = f.replace(/\.json$/, '');
    const rows = readLedger(s);
    const b = await dailyBars(s);
    if (!b) { console.log(`${s}: no bars`); continue; }
    for (const e of rows) e.result = gradePlan(e, b);
    writeLedger(s, rows);
    for (const e of rows) console.log(`${s.padEnd(6)} ${e.madeOn} entry ${e.plan.entryLo}-${e.plan.entryHi} stop ${e.plan.stop} T1 ${e.plan.t1}  ${e.result.status}${e.result.filledOn ? ` filled ${e.result.filledOn}` : ''}${e.result.resolvedOn ? ` -> ${e.result.resolvedOn}` : ''}${e.result.ret != null ? ` ${e.result.ret}%` : ''}`);
  }
  const r = recordSummary();
  console.log(`\nresolved ${r.resolved} (T1 ${r.t1} / stop ${r.stop} / expired ${r.expired}), no fill ${r.nofill}, still open ${r.open}`);
  console.log(r.resolved >= MIN_GRADED ? `T1 hit rate ${(r.t1 / r.resolved * 100).toFixed(0)}%` : `no hit rate until ${MIN_GRADED} resolved fills`);
  process.exit(0);
}

// ── data ────────────────────────────────────────────────────────────────────
const gex = await api(`/gex/${sym}`);
const matrix = await api(`/gex/${sym}/matrix`);
const yr = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1d&range=1y`, {
  headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000),
}).then((r) => r.json());
const yres = yr?.chart?.result?.[0];
if (!yres?.timestamp) throw new Error(`${sym}: no daily bars from Yahoo`);
const q = yres.indicators.quote[0];
const allBars = yres.timestamp.map((t, i) => ({
  d: new Date(t * 1000).toISOString().slice(0, 10), o: q.open[i], h: q.high[i], l: q.low[i], c: q.close[i],
})).filter((b) => b.o != null && b.c != null);

const spot = gex.spotPrice;
const flipNow = gex.gammaFlipLevel;

// Moving averages over the full year so the visible window starts warmed up.
const closes = allBars.map((b) => b.c);
const ema = []; const k21 = 2 / 22;
closes.forEach((c, i) => ema.push(i ? c * k21 + ema[i - 1] * (1 - k21) : c));
const sma = closes.map((_, i) => (i >= 49 ? closes.slice(i - 49, i + 1).reduce((a, v) => a + v, 0) / 50 : null));
const off = Math.max(0, allBars.length - BARS);
const bars = allBars.slice(off);

// Keltner: the 21 EMA ± 1 and 2 ATR(14), Wilder-smoothed. Same 21 EMA as the
// midline already on the chart, so the bands hang off a line he reads anyway.
const tr = allBars.map((b, i) => (i ? Math.max(b.h - b.l, Math.abs(b.h - allBars[i - 1].c), Math.abs(b.l - allBars[i - 1].c)) : b.h - b.l));
const atrA = [];
tr.forEach((t, i) => atrA.push(i < 14 ? (i ? (atrA[i - 1] * i + t) / (i + 1) : t) : (atrA[i - 1] * 13 + t) / 14));
const kc = (m) => ema.map((e, i) => e + m * atrA[i]);
const kcU1 = kc(1), kcL1 = kc(-1), kcU2 = kc(2), kcL2 = kc(-2);
const atrNow = atrA[atrA.length - 1];
const emaNow = ema[ema.length - 1];

// ── forward expiries ────────────────────────────────────────────────────────
// Every level here is built from the matrix GAMMA, and from the book that is
// still alive on that date: an expiry's walls are what dealers hedge once
// every earlier expiry has rolled off. Two bugs this replaced (2026-10-08):
// expiryStats' callWall/putWall are not gamma walls (MU 10/09 said call 1200
// while that expiry's gamma piled at 1100, and "put wall 1000" on every date),
// and each expiry was read alone, as if dealers hedged one date at a time.
const todayET = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/New_York' }).format(new Date());
const colOf = new Map(matrix.expirations.map((e, i) => [e, i]));
const bookFrom = (date) => {
  // Net GEX per strike summed over every expiry on or after `date`.
  const cols = matrix.expirations.map((e, i) => (e >= date && e > todayET ? i : -1)).filter((i) => i >= 0);
  return matrix.rows.map((r) => ({ strike: r.strike, g: cols.reduce((a, i) => a + (r.gex[i] || 0), 0) }));
};
// A strike only counts as a wall if it is big next to the rest of the board.
// MU's "put wall" was a -$15M strike four dollars under spot on a book with a
// +$155M strike: technically the most negative, meaningless as a level.
const SIG = 0.1;
const readBook = (book, em) => {
  const big = Math.max(...book.map((b) => Math.abs(b.g)), 1);
  const up = book.filter((b) => b.strike > spot && b.g > 0);
  const dn = book.filter((b) => b.strike < spot && Math.abs(b.g) >= big * SIG);
  const pick = (arr, f) => (arr.length ? arr.reduce((a, b) => (f(b) > f(a) ? b : a)) : null);
  const call = pick(up, (b) => b.g);
  const put = pick(dn.filter((b) => b.g < 0), (b) => -b.g);
  const cushion = pick(dn.filter((b) => b.g > 0), (b) => b.g);
  const mag = pick(book, (b) => Math.abs(b.g));
  const set = pick(book.filter((b) => Math.abs(b.strike - spot) <= em * 0.5), (b) => Math.abs(b.g));
  return {
    callWall: call?.strike ?? null, callGex: call?.g ?? 0,
    putWall: put?.strike ?? null, putGex: put?.g ?? 0,
    cushion: cushion?.strike ?? null,
    magnet: mag?.strike ?? null, magGex: mag?.g ?? 0,
    settle: set?.strike ?? null, setGex: set?.g ?? 0,
    net: book.reduce((a, b) => a + b.g, 0),
  };
};
const exps = matrix.expiryStats
  .filter((e) => e.dte > 0 && e.dte <= HORIZON && colOf.has(e.expiry))
  .map(({ expiry, dte, emPoints, oiSharePct, isLargest }) => ({
    expiry, dte, emPoints, oiSharePct, isLargest,
    ...readBook(bookFrom(expiry), emPoints),
    major: oiSharePct >= MIN_SHARE || isLargest,
  }));
if (!exps.length) throw new Error(`no expiries within ${HORIZON} days`);
const majors = exps.filter((e) => e.major);
if (!majors.length) throw new Error(`${sym}: no expiry inside ${HORIZON} days carries ${MIN_SHARE}% of open interest; the book is too thin to map`);
const largest = exps.find((e) => e.isLargest) || majors.reduce((a, e) => (e.oiSharePct > a.oiSharePct ? e : a), majors[0]);
const last = exps[exps.length - 1];
const negGamma = gex.totalGEX < 0;
// The book as it stands right now: everything that survives tonight.
const now = exps[0];

// Segments: the board is constant between two expiries and changes the
// moment one rolls off. Every expiry is a boundary, not just the big ones:
// MU's 1100 lid was held up by the small 10/12 expiry, so it goes 10/12.
const segs = exps.map((e, k) => ({ from: k ? exps[k - 1].dte : 0, to: e.dte, end: e.expiry, ...e }));

// ── the trade plan ──────────────────────────────────────────────────────────
// Built off the live book. Entry is the put wall plus half an ATR; the stop
// sits a full ATR under it, since a close through a put wall is the signal the
// long was wrong. T1 is the nearest call wall at least half an ATR away, on
// today's board or any later one. T2 is the upper 2-ATR Keltner if it clears
// T1 by half an ATR, else one ATR past T1.
const r2 = (v) => Math.round(v * 100) / 100;
// Entry: the heaviest significant strike at least half an ATR under spot,
// put wall or long-gamma cushion, whichever carries more gamma. Anything
// closer is not a pullback, it is buying here.
const nowBook = bookFrom(now.expiry);
const bigNow = Math.max(...nowBook.map((b) => Math.abs(b.g)), 1);
const support = nowBook
  .filter((b) => b.strike <= spot - atrNow * 0.5 && Math.abs(b.g) >= bigNow * SIG)
  .sort((a, b) => Math.abs(b.g) - Math.abs(a.g))[0] ?? null;
const pwUse = support ? support.strike : r2(spot - atrNow);
const planBasis = support ? (support.g < 0 ? 'put wall' : 'long-gamma cushion') : '1 ATR pullback';
const plan = {
  basis: planBasis,
  entryLo: pwUse,
  entryHi: r2(Math.min(spot, pwUse + atrNow * 0.5)),
  stop: r2(pwUse - atrNow),
};
const minT1 = spot + atrNow * 0.5;
const t1Wall = [now.callWall, ...segs.map((g) => g.callWall)].filter((v) => v != null && v >= minT1).sort((a, b) => a - b)[0];
plan.t1 = t1Wall ?? (kcU1[kcU1.length - 1] >= minT1 ? r2(kcU1[kcU1.length - 1]) : r2(spot + atrNow));
plan.t1Basis = t1Wall != null ? 'call wall' : kcU1[kcU1.length - 1] >= minT1 ? 'upper 1-ATR Keltner' : 'spot + 1 ATR';
const k2 = kcU2[kcU2.length - 1];
plan.t2 = r2(k2 > plan.t1 + atrNow * 0.5 ? k2 : plan.t1 + atrNow);
plan.mid = (plan.entryLo + plan.entryHi) / 2;
plan.rr = (plan.t1 - plan.mid) / (plan.mid - plan.stop);
plan.rr2 = (plan.t2 - plan.mid) / (plan.mid - plan.stop);

// ── geometry ────────────────────────────────────────────────────────────────
const W = 2000, H = 1188;
const PAD_L = 80, PAD_R = 50, PAD_T = 110, PLOT_H = 700;
const PLOT_W = W - PAD_L - PAD_R;
const LEFT_W = Math.round(PLOT_W * 0.5);
const FWD_X = PAD_L + LEFT_W;
const FWD_W = PLOT_W - LEFT_W;
const FWD_IN = 30;                       // breathing room after "now"
const FWD_R = 215;                       // room for the plan pills
const maxDte = last.dte;
const XF = (dte) => FWD_X + FWD_IN + (dte / maxDte) * (FWD_W - FWD_IN - FWD_R);
const XB = (i) => PAD_L + 14 + (i + 0.5) * ((LEFT_W - 28) / bars.length);
const barW = Math.max(2, ((LEFT_W - 28) / bars.length) * 0.62);

// Y range: what price actually did, plus the cone and the walls that live
// inside a stretched version of it. Walls far outside the cone would squash
// the candles for a level nobody is trading toward.
const coneHi = Math.max(...exps.map((e) => spot + e.emPoints));
const coneLo = Math.min(...exps.map((e) => spot - e.emPoints));
const reach = (v) => v >= coneLo - (spot - coneLo) * 0.4 && v <= coneHi + (coneHi - spot) * 0.4;
const fwdLv = [...exps.flatMap((e) => [e.callWall, e.putWall, e.magnet, e.settle]), ...segs.flatMap((g) => [g.callWall, g.putWall ?? g.cushion, g.settle])].filter((v) => v != null && reach(v)).concat([plan.stop, plan.t2]);
// Scale to the last ~6 weeks, not the whole window: one old spike (ASTS at 133
// in June) otherwise flattens everything that matters. Older candles clip.
const recent = bars.slice(-30);
let yMin = Math.min(...recent.map((b) => b.l), coneLo, ...fwdLv);
let yMax = Math.max(...recent.map((b) => b.h), coneHi, ...fwdLv);
const padY = (yMax - yMin) * 0.06; yMin -= padY; yMax += padY;
const Y = (v) => PAD_T + PLOT_H - ((v - yMin) / (yMax - yMin)) * PLOT_H;
const clampY = (v) => Math.min(yMax, Math.max(yMin, v));

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const mono = `font-family="'JetBrains Mono',monospace"`;
const fmt = (v) => (v == null ? '-' : Number.isInteger(v) ? String(v) : v.toFixed(2));
const fmtM = (v) => {
  const a = Math.abs(v), s = v < 0 ? '−' : '';
  if (a >= 1e9) return `${s}$${(a / 1e9).toFixed(2)}B`;
  if (a < 1e6) return `${s}$${Math.round(a / 1e3)}K`;
  if (a < 10e6) return `${s}$${(a / 1e6).toFixed(1)}M`;
  return `${s}$${Math.round(a / 1e6)}M`;
};
const md = (d) => d.slice(5).replace('-', '/');

const svg = [];
const push = (s) => svg.push(s);
push(`<defs>
  <filter id="glow" x="-10%" y="-300%" width="120%" height="700%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="glowS" x="-10%" y="-300%" width="120%" height="700%"><feGaussianBlur stdDeviation="3"/></filter>
  <linearGradient id="coneG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${C.call}" stop-opacity="0.16"/><stop offset="0.5" stop-color="${C.text}" stop-opacity="0.02"/><stop offset="1" stop-color="${C.put}" stop-opacity="0.16"/>
  </linearGradient>
  <linearGradient id="fwdBg" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#0e1020"/><stop offset="1" stop-color="#0a0b14"/>
  </linearGradient>
  <linearGradient id="entryG" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="${C.entry}" stop-opacity="0.04"/><stop offset="1" stop-color="${C.entry}" stop-opacity="0.22"/>
  </linearGradient>
</defs>`);
// A level line with a soft glow underneath, the way the TMPro cards draw them.
const glowLine = (x1, x2, v, col, { w = 2, dash = '', op = 0.95, glow = 0.55 } = {}) => {
  const y = Y(v).toFixed(1);
  push(`<line x1="${x1}" x2="${x2}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="${w * 4}" stroke-opacity="${glow}" filter="url(#glow)"/>`);
  push(`<line x1="${x1}" x2="${x2}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="${w}" stroke-opacity="${op}" ${dash ? `stroke-dasharray="${dash}"` : ''}/>`);
};

// ── header ──────────────────────────────────────────────────────────────────
push(`<text x="${PAD_L}" y="46" font-family="'Share Tech Mono',monospace" font-size="30" fill="${C.text}" letter-spacing="1">THE NEXT ${Math.round(maxDte / 7)} WEEKS <tspan fill="${C.green}">${esc(sym)}</tspan></text>`);
push(`<text x="${PAD_L}" y="72" ${mono} font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · ${flipNow != null ? `flip ${fmt(flipNow)}` : 'no flip in range'} · net GEX ${fmtM(gex.totalGEX)} · options price a ±${largest.emPoints.toFixed(2)} move into ${md(largest.expiry)}, the heaviest expiry (${largest.oiSharePct.toFixed(0)}% of OI)</text>`);
const pillC = negGamma ? C.put : C.call;
push(`<rect x="${W - PAD_R - 330}" y="26" width="330" height="34" rx="17" fill="${negGamma ? '#1a0e11' : '#0c1a13'}" stroke="${pillC}" stroke-opacity="0.45"/>`);
push(`<text x="${W - PAD_R - 165}" y="48" text-anchor="middle" ${mono} font-size="14" fill="${pillC}">${negGamma ? 'NEGATIVE GAMMA / moves get amplified' : 'POSITIVE GAMMA / moves get damped'}</text>`);
// Small names: say the book is thin rather than let the levels look solid.
if (Math.abs(gex.totalGEX) < 1e6) push(`<text x="${PAD_L}" y="92" ${mono} font-size="12" fill="${C.coral}">THIN BOOK: only ${fmtM(gex.totalGEX)} of net gamma. the levels show where open interest sits, not how hard dealers will defend them.</text>`);
{
  const rec = recordSummary();
  const recTxt = rec.resolved >= MIN_GRADED
    ? `plan record: T1 ${rec.t1}/${rec.resolved} (${(rec.t1 / rec.resolved * 100).toFixed(0)}%) · ${rec.open} open`
    : `plan record: ${rec.resolved} resolved, ${rec.open} open · no hit rate until ${MIN_GRADED}`;
  push(`<text x="${W - PAD_R}" y="94" text-anchor="end" ${mono} font-size="11" fill="${C.entry}" fill-opacity="0.85">${recTxt}</text>`);
}
push(`<text x="${W - PAD_R}" y="76" text-anchor="end" ${mono} font-size="11" fill="${C.dim}">as of ${new Date().toISOString().slice(0, 16).replace('T', ' ')}Z</text>`);

// ── panels + grid ───────────────────────────────────────────────────────────
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${LEFT_W}" height="${PLOT_H}" fill="${C.panel}"/>`);
push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${PLOT_H}" fill="url(#fwdBg)"/>`);
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${PLOT_W}" height="${PLOT_H}" fill="none" stroke="${C.line}"/>`);
const span = yMax - yMin;
const step = [0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100].find((s) => span / s <= 10) || 100;
for (let v = Math.ceil(yMin / step) * step; v <= yMax; v += step) {
  push(`<line x1="${PAD_L}" x2="${W - PAD_R}" y1="${Y(v)}" y2="${Y(v)}" stroke="${C.line}" stroke-opacity="0.6"/>`);
  push(`<text x="${PAD_L - 8}" y="${Y(v) + 4}" text-anchor="end" ${mono} font-size="10.5" fill="${C.dim}">${fmt(+v.toFixed(2))}</text>`);
}
push(`<line x1="${FWD_X}" x2="${FWD_X}" y1="${PAD_T}" y2="${PAD_T + PLOT_H}" stroke="${C.dim}" stroke-dasharray="3 4" stroke-opacity="0.6"/>`);

// Flip band: above / below today's flip, across the forward panel only.
if (flipNow != null && flipNow > yMin && flipNow < yMax) {
  const yf = Y(flipNow);
  push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${yf - PAD_T}" fill="${C.call}" fill-opacity="0.025"/>`);
  push(`<rect x="${FWD_X}" y="${yf}" width="${FWD_W}" height="${PAD_T + PLOT_H - yf}" fill="${C.put}" fill-opacity="0.03"/>`);
}

// ── left: daily candles ─────────────────────────────────────────────────────
const clippedHiPre = bars.some((b) => b.h > yMax);
push(`<defs><clipPath id="lp"><rect x="${PAD_L}" y="${PAD_T}" width="${LEFT_W}" height="${PLOT_H}"/></clipPath></defs><g clip-path="url(#lp)">`);
// Keltner fills first so candles sit on top of them.
const band = (up, dn, op) => {
  const a = up.slice(off).map((v, i) => `${XB(i).toFixed(1)},${Y(v).toFixed(1)}`);
  const b = dn.slice(off).map((v, i) => `${XB(i).toFixed(1)},${Y(v).toFixed(1)}`).reverse();
  push(`<polygon points="${[...a, ...b].join(' ')}" fill="${C.kc}" fill-opacity="${op}"/>`);
};
band(kcU2, kcL2, 0.045);
band(kcU1, kcL1, 0.07);
for (const [arr, op, dash] of [[kcU2, 0.55, '6 4'], [kcL2, 0.55, '6 4'], [kcU1, 0.4, '2 4'], [kcL1, 0.4, '2 4']]) {
  const p = arr.slice(off).map((v, i) => `${XB(i).toFixed(1)},${Y(v).toFixed(1)}`);
  push(`<polyline points="${p.join(' ')}" fill="none" stroke="${C.kc}" stroke-width="1.2" stroke-opacity="${op}" stroke-dasharray="${dash}"/>`);
}
// The plan, ghosted across history so the levels can be read against price.
for (const [v, col] of [[plan.t2, C.tp], [plan.t1, C.tp], [plan.stop, C.stop]]) push(`<line x1="${PAD_L}" x2="${FWD_X}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-opacity="0.22" stroke-dasharray="3 5"/>`);
push(`<rect x="${PAD_L}" y="${Y(plan.entryHi)}" width="${LEFT_W}" height="${Y(plan.entryLo) - Y(plan.entryHi)}" fill="${C.entry}" fill-opacity="0.05"/>`);
bars.forEach((b, i) => {
  const x = XB(i), up = b.c >= b.o, col = up ? C.call : C.put;
  push(`<line x1="${x}" x2="${x}" y1="${Y(b.h)}" y2="${Y(b.l)}" stroke="${col}" stroke-width="1"/>`);
  const y1 = Y(Math.max(b.o, b.c)), y2 = Y(Math.min(b.o, b.c));
  push(`<rect x="${x - barW / 2}" y="${y1}" width="${barW}" height="${Math.max(1, y2 - y1)}" fill="${col}"/>`);
});
const line = (vals, col, dash = '') => {
  const p = vals.map((v, i) => (v == null ? null : `${XB(i).toFixed(1)},${Y(v).toFixed(1)}`)).filter(Boolean);
  if (p.length > 1) push(`<polyline points="${p.join(' ')}" fill="none" stroke="${col}" stroke-width="1.6" stroke-opacity="0.8" ${dash ? `stroke-dasharray="${dash}"` : ''}/>`);
};
line(ema.slice(off), C.ema);
line(sma.slice(off), C.sma, '5 4');
push('</g>');
push(`<rect x="${PAD_L + 1}" y="${PAD_T + 1}" width="420" height="${clippedHiPre ? 64 : 44}" fill="${C.panel}" fill-opacity="0.85"/>`);
// Say so when old candles run off the top or bottom.
const clippedHi = bars.filter((b) => b.h > yMax), clippedLo = bars.filter((b) => b.l < yMin);
if (clippedHi.length) push(`<text x="${XB(bars.indexOf(clippedHi[0]))}" y="${PAD_T + 52}" ${mono} font-size="10" fill="${C.dim}">↑ off chart, high ${Math.max(...clippedHi.map((b) => b.h)).toFixed(2)}</text>`);
if (clippedLo.length) push(`<text x="${XB(bars.indexOf(clippedLo[0]))}" y="${PAD_T + PLOT_H - 24}" ${mono} font-size="10" fill="${C.dim}">↓ off chart, low ${Math.min(...clippedLo.map((b) => b.l)).toFixed(2)}</text>`);
// Month ticks along the bottom.
let lastMon = '';
bars.forEach((b, i) => {
  const mon = b.d.slice(0, 7);
  if (mon !== lastMon) {
    lastMon = mon;
    const name = new Date(`${b.d}T12:00:00Z`).toLocaleString('en-US', { month: 'short', timeZone: 'UTC' }).toUpperCase();
    push(`<line x1="${XB(i)}" x2="${XB(i)}" y1="${PAD_T + PLOT_H - 6}" y2="${PAD_T + PLOT_H}" stroke="${C.dim}"/>`);
    push(`<text x="${XB(i) + 4}" y="${PAD_T + PLOT_H - 8}" ${mono} font-size="10" fill="${C.dim}">${name}</text>`);
  }
});
push(`<text x="${PAD_L + 10}" y="${PAD_T + 20}" ${mono} font-size="11" fill="${C.dim}" letter-spacing="2">THE LAST ${bars.length} SESSIONS</text>`);
push(`<text x="${PAD_L + 10}" y="${PAD_T + 36}" ${mono} font-size="9.5" fill="${C.dim}">daily candles · <tspan fill="${C.ema}">21 EMA</tspan> · <tspan fill="${C.sma}">50 SMA</tspan> · <tspan fill="${C.kc}">Keltner 1 / 2 ATR (${atrNow.toFixed(2)})</tspan></text>`);
const hi = recent.reduce((a, b) => (b.h > a.h ? b : a)), lo = recent.reduce((a, b) => (b.l < a.l ? b : a));
for (const [b, v, dy] of [[hi, hi.h, -8], [lo, lo.l, 16]].filter(([, v]) => v <= yMax && v >= yMin)) {
  const i = bars.indexOf(b);
  push(`<text x="${XB(i)}" y="${Y(v) + dy}" text-anchor="middle" ${mono} font-size="10" fill="${C.text}">${v.toFixed(2)}</text>`);
}

// ── right: expected-move cone ───────────────────────────────────────────────
push(`<text x="${FWD_X + 12}" y="${PAD_T + 20}" ${mono} font-size="11" fill="${C.dim}" letter-spacing="2">THE NEXT ${maxDte} DAYS · BY EXPIRY</text>`);
const cone = [[XF(0), spot], ...exps.map((e) => [XF(e.dte), spot + e.emPoints])];
const coneB = [[XF(0), spot], ...exps.map((e) => [XF(e.dte), spot - e.emPoints])];
const pts = [...cone, ...coneB.slice().reverse()].map(([x, v]) => `${x.toFixed(1)},${Y(clampY(v)).toFixed(1)}`);
push(`<polygon points="${pts.join(' ')}" fill="url(#coneG)" stroke="${C.dim}" stroke-opacity="0.35" stroke-dasharray="4 4"/>`);
const lastConeY = Y(clampY(spot + last.emPoints));
push(`<text x="${XF(last.dte) - 6}" y="${lastConeY - 8}" text-anchor="end" ${mono} font-size="10" fill="${C.dim}">options-implied move (±1σ)</text>`);

// Daily/near-daily expiries (MU, SPCX) collide in the strip. Majors always
// get a column; a minor only gets one if it has room.
const shown = [];
for (const e of [...majors, ...exps.filter((x) => !x.major)]) {
  if (shown.every((o) => Math.abs(XF(o.dte) - XF(e.dte)) >= 58)) shown.push(e);
}
const showSet = new Set(shown.map((e) => e.expiry));
// Expiry columns: faint vertical, date at the bottom, monthly OPEX louder.
for (const e of exps.filter((x) => showSet.has(x.expiry))) {
  const x = XF(e.dte);
  const op = e.major ? 0.35 : 0.12;
  push(`<line x1="${x}" x2="${x}" y1="${PAD_T + 30}" y2="${PAD_T + PLOT_H}" stroke="${e.isLargest ? C.pin : C.dim}" stroke-opacity="${op}" stroke-dasharray="2 5"/>`);
  push(`<text x="${x}" y="${PAD_T + PLOT_H - 8}" text-anchor="middle" ${mono} font-size="${e.major ? 10.5 : 9}" fill="${e.isLargest ? C.pin : C.dim}" fill-opacity="${e.major ? 1 : 0.6}">${md(e.expiry)}</text>`);
}

// ── plan levels across the forward panel ────────────────────────────────────
const PX1 = FWD_X + 2, PX2 = XF(maxDte) + 6;
push(`<rect x="${PX1}" y="${Y(plan.entryHi)}" width="${PX2 - PX1}" height="${Y(plan.entryLo) - Y(plan.entryHi)}" fill="url(#entryG)"/>`);
push(`<rect x="${PX1}" y="${Y(plan.entryHi)}" width="${PX2 - PX1}" height="${Y(plan.entryLo) - Y(plan.entryHi)}" fill="${C.entry}" fill-opacity="0.12" filter="url(#glow)"/>`);
glowLine(PX1, PX2, plan.entryHi, C.entry, { w: 1.2, dash: '2 3', glow: 0.25 });
glowLine(PX1, PX2, plan.entryLo, C.entry, { w: 1.2, dash: '2 3', glow: 0.25 });
glowLine(PX1, PX2, plan.t1, C.tp, { w: 2 });
glowLine(PX1, PX2, plan.t2, C.tp, { w: 1.6, op: 0.7, glow: 0.35 });
glowLine(PX1, PX2, plan.stop, C.stop, { w: 2, dash: '8 5' });
if (flipNow != null && reach(flipNow)) glowLine(PX1, PX2, flipNow, C.flip, { w: 1.6, dash: '8 6', op: 0.8, glow: 0.4 });
// Triangles at the left edge: ▲ target, ▼ stop.
const tri = (v, col, up) => { const x = FWD_X + 14, y = Y(v); push(`<path d="M ${x - 7} ${up ? y + 5 : y - 5} L ${x + 7} ${up ? y + 5 : y - 5} L ${x} ${up ? y - 7 : y + 7} Z" fill="${col}"/>`); };
tri(plan.t1, C.tp, true); tri(plan.t2, C.tp, true); tri(plan.stop, C.stop, false);

// ── roads ───────────────────────────────────────────────────────────────────
// Each road is a staircase, not a curve: the board holds still until a major
// expiry rolls off, then steps to what the surviving book says. The old
// spline through per-expiry points drew MU at 1200 by Friday when the live
// lid was 1100 until 10/09.
const roads = [
  { key: 'up', col: C.call, name: 'UP', what: 'call wall', val: (g) => g.callWall },
  { key: 'down', col: C.put, name: 'DOWN', what: 'put wall', val: (g) => g.putWall ?? g.cushion, whatAlt: (g) => (g.putWall == null && g.cushion != null ? 'long-gamma cushion' : null) },
  { key: 'settle', col: C.pin, name: 'RANGE', what: 'settles near', val: (g) => g.settle },
];
const stair = (r) => {
  let d = '', prev = null;
  segs.forEach((g, k) => {
    const v = r.val(g);
    if (v == null) { prev = null; return; }
    const x0 = XF(g.from), x1 = XF(g.to);
    const ramp = Math.min(k ? 26 : 60, (x1 - x0) * 0.45);
    const y = Y(clampY(v)).toFixed(1);
    if (prev == null) {
      const [sx, sv] = k ? [x0, v] : [XF(0), spot];
      d += ` M ${sx.toFixed(1)} ${Y(clampY(sv)).toFixed(1)}`;
      prev = sv;
    }
    const yp = Y(clampY(prev)).toFixed(1);
    d += ` C ${(x0 + ramp / 2).toFixed(1)} ${yp}, ${(x0 + ramp / 2).toFixed(1)} ${y}, ${(x0 + ramp).toFixed(1)} ${y} L ${x1.toFixed(1)} ${y}`;
    prev = v;
  });
  return d.trim();
};
for (const r of roads) {
  const d = stair(r);
  if (!d) continue;
  push(`<path d="${d}" fill="none" stroke="${r.col}" stroke-width="9" stroke-opacity="0.3" filter="url(#glowS)"/>`);
  push(`<path d="${d}" fill="none" stroke="${r.col}" stroke-width="${r.key === 'settle' ? 2 : 2.6}" stroke-opacity="0.85" ${r.key === 'settle' ? 'stroke-dasharray="7 5"' : ''}/>`);
  // Name the hand-off where a wall rolls off and the next one takes over.
  if (r.key === 'settle') continue;
  let lastX = -1e9;
  for (let k = 1; k < segs.length; k++) {
    const a = r.val(segs[k - 1]), b = r.val(segs[k]);
    if (a == null || b == null || a === b) continue;
    const x = XF(segs[k - 1].to);
    if (x - lastX < 140) continue;
    lastX = x;
    push(`<text x="${x + 32}" y="${Y(clampY(b)) + (r.key === 'down' ? 16 : -8)}" ${mono} font-size="9.5" fill="${r.col}" fill-opacity="0.8">${fmt(b)} once ${md(segs[k - 1].end)} rolls off</text>`);
  }
}

// Per-expiry markers: the walls of the book still alive on that date. Minor
// expiries are faint ticks; the magnet bubble is sized by its gamma.
const maxMag = Math.max(...exps.map((e) => Math.abs(e.magGex)), 1);
for (const e of exps) {
  const x = XF(e.dte);
  const a = e.major ? 1 : 0.35;
  for (const [v, col] of [[e.callWall, C.call], [e.putWall, C.put]]) {
    if (v == null || !reach(v)) continue;
    const outside = Math.abs(v - spot) > e.emPoints;
    push(`<line x1="${x - 9}" x2="${x + 9}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-width="3" stroke-opacity="${outside ? a * 0.5 : a}"/>`);
  }
  if (e.magnet != null && reach(e.magnet)) {
    const rad = 4 + Math.sqrt(Math.abs(e.magGex) / maxMag) * 13;
    const col = e.magGex >= 0 ? C.call : C.put;
    push(`<circle cx="${x}" cy="${Y(e.magnet)}" r="${rad.toFixed(1)}" fill="${col}" fill-opacity="${0.18 * a + 0.05}" stroke="${C.pin}" stroke-opacity="${a}" stroke-width="1.6"/>`);
  }
}

// Now dot.
push(`<circle cx="${XF(0)}" cy="${Y(spot)}" r="5" fill="${C.text}"/>`);
push(`<text x="${XF(0) + 8}" y="${Y(spot) + 20}" ${mono} font-size="12" fill="${C.text}">${spot.toFixed(2)} now</text>`);

// Road names sit just inside the last expiry, above their own line.
for (const r of roads) {
  const g = segs[segs.length - 1];
  const v = r.val(g); if (v == null) continue;
  const outside = Math.abs(v - spot) > g.emPoints;
  push(`<text x="${XF(maxDte) - 14}" y="${Y(clampY(v)) + (r.key === 'down' ? 20 : -10)}" text-anchor="end" font-family="'Share Tech Mono',monospace" font-size="13" fill="${r.col}" fill-opacity="${outside ? 0.55 : 0.95}" letter-spacing="1">${r.name} · ${fmt(v)}${outside ? ' *' : ''}</text>`);
}

// Plan pills down the right edge, pushed apart so none overlap.
const pills = [
  { tag: 'T2', val: `$${plan.t2.toFixed(2)}`, v: plan.t2, col: C.tp },
  { tag: 'T1', val: `$${plan.t1.toFixed(2)}`, v: plan.t1, col: C.tp },
  flipNow != null && reach(flipNow) ? { tag: 'FLIP', val: `$${flipNow.toFixed(2)}`, v: flipNow, col: C.flip } : null,
  { tag: sym, val: `$${spot.toFixed(2)}`, v: spot, col: C.text },
  { tag: 'ENTRY', val: `$${plan.entryLo.toFixed(2)}-${plan.entryHi.toFixed(2)}`, v: (plan.entryLo + plan.entryHi) / 2, col: C.entry, fill: true },
  { tag: 'STOP', val: `$${plan.stop.toFixed(2)}`, v: plan.stop, col: C.stop },
].filter(Boolean).map((p) => ({ ...p, y: Y(p.v) })).sort((a, b) => a.y - b.y);
for (let i = 1; i < pills.length; i++) if (pills[i].y - pills[i - 1].y < 30) pills[i].y = pills[i - 1].y + 30;
const over = pills[pills.length - 1].y - (PAD_T + PLOT_H - 30);
if (over > 0) pills.forEach((p) => (p.y -= over));
const LX = XF(maxDte) + 16;
for (const P of pills) {
  if (Math.abs(P.y - Y(P.v)) > 3) push(`<line x1="${PX2}" x2="${LX - 4}" y1="${Y(P.v)}" y2="${P.y}" stroke="${P.col}" stroke-opacity="0.4"/>`);
  const w = 16 + (P.tag.length + P.val.length) * 8.6 + 8;
  push(`<rect x="${LX - 6}" y="${P.y - 14}" width="${w}" height="26" rx="6" fill="${P.col}" fill-opacity="${P.fill ? 0.16 : 0.08}" stroke="${P.col}" stroke-opacity="0.35"/>`);
  push(`<text x="${LX + 2}" y="${P.y + 5}" font-family="'JetBrains Mono',monospace" font-size="14" font-weight="700" fill="${P.col}">${esc(P.tag)} <tspan font-weight="400" font-size="12" fill-opacity="0.8">${esc(P.val)}</tspan></text>`);
}
// Reward to risk, off the middle of the entry zone.
push(`<text x="${LX - 4}" y="${PAD_T + 22}" ${mono} font-size="11" fill="${C.dim}">R:R ${plan.rr.toFixed(1)} to T1 · ${plan.rr2.toFixed(1)} to T2</text>`);

// ── expiry strip ────────────────────────────────────────────────────────────
// The numbers behind every marker, under their own column: the board as it
// stands on that date, after every earlier expiry has rolled off.
const SY = PAD_T + PLOT_H + 26;
const rowsDef = [
  ['±move', (e) => e.emPoints.toFixed(2), C.text],
  ['call wall', (e) => fmt(e.callWall), C.call],
  ['magnet', (e) => fmt(e.magnet), C.pin],
  ['settle', (e) => fmt(e.settle), C.pin],
  ['put wall', (e) => (e.putWall != null ? fmt(e.putWall) : e.cushion != null ? `(${fmt(e.cushion)})` : '-'), C.put],
  ['OI share', (e) => `${e.oiSharePct.toFixed(0)}%`, C.dim],
];
rowsDef.forEach(([label, f, col], ri) => {
  const y = SY + ri * 17;
  push(`<text x="${FWD_X - 10}" y="${y}" text-anchor="end" ${mono} font-size="10.5" fill="${C.dim}">${label}</text>`);
  for (const e of shown) push(`<text x="${XF(e.dte)}" y="${y}" text-anchor="middle" ${mono} font-size="10.5" fill="${col}" fill-opacity="${e.major ? 1 : 0.45}">${f(e)}</text>`);
});
push(`<text x="${FWD_X - 10}" y="${SY + rowsDef.length * 17 - 2}" text-anchor="end" ${mono} font-size="9" fill="${C.dim}" fill-opacity="0.7">board alive on each date · (x) = long-gamma cushion, no put wall</text>`);

// ── IF / IF / ELSE ──────────────────────────────────────────────────────────
// Read off the live board, and say when it changes: a wall that rolls off
// next week is a different trade from one that holds for six.
const handoff = (val) => {
  const k = segs.findIndex((g, i) => i > 0 && val(g) !== val(segs[0]) && val(g) != null);
  return k > 0 ? { at: segs[k - 1].end, to: val(segs[k]) } : null;
};
const above = now.callWall != null && now.callWall > spot ? now.callWall : null;
const below = now.putWall != null && now.putWall < spot ? now.putWall : null;
const cushion = below == null && now.cushion != null && now.cushion < spot ? now.cushion : null;
const upNext = handoff((g) => g.callWall);
const dnNext = handoff((g) => g.putWall ?? g.cushion);
const flipRef = flipNow;
const em0 = largest.emPoints;
const rules = [
  {
    kw: 'IF', col: C.call,
    cond: flipRef == null ? (above ? `it pushes toward ${fmt(above)}` : 'it rallies') : flipRef > spot ? `it reclaims ${fmt(flipRef)}` : `it holds over ${fmt(flipRef)}`,
    rule: above
      ? `${flipRef == null ? 'no flip in range, so the call wall is the whole story.' : flipRef > spot ? 'back above the flip, dealers stop chasing and start braking.' : 'above the flip, dealers brake.'} ${fmt(above)} is the lid${upNext ? ` until ${md(upNext.at)}, then ${fmt(upNext.to)}` : ''}.`
      : 'no call wall above spot. nothing caps it but the cone.',
  },
  {
    kw: 'IF', col: C.put,
    cond: below ? `it loses ${fmt(below)}` : cushion ? `it loses ${fmt(cushion)}` : `it breaks ${(spot - em0).toFixed(2)}`,
    rule: below
      ? (negGamma
        ? `${fmt(below)} is the put wall${dnNext ? ` until ${md(dnNext.at)}, then ${fmt(dnNext.to)}` : ''}. a crowd, not a floor: below it dealers sell into the drop.`
        : `${fmt(below)} is the put wall${dnNext ? ` until ${md(dnNext.at)}, then ${fmt(dnNext.to)}` : ''}. ${flipRef != null && flipRef < below ? `long gamma holds down to ${fmt(flipRef)}; lose that and dealers start chasing.` : 'below it the cushion thins.'}`)
      : cushion
        ? `no put wall. ${fmt(cushion)} is long gamma below spot, real dealer buying${dnNext ? ` until ${md(dnNext.at)}` : ''}. under it the board is thin.`
        : 'nothing below spot on the board.',
  },
  {
    kw: 'ELSE', col: C.pin,
    cond: (below ?? cushion) && above ? `it lives between ${fmt(below ?? cushion)} and ${fmt(above)}` : 'it ranges',
    rule: `settles ${segs.map((g) => g.settle).filter((v, i, a) => v != null && v !== a[i - 1]).map(fmt).join(' → ') || fmt(now.magnet)}, biggest pile at ${fmt(now.magnet)}, into ${md(segs[segs.length - 1].end)}. ${negGamma ? 'short gamma, so the range gets knifed at both edges.' : 'long gamma, so it gets pinned.'}`,
  },
];
rules.push({
  kw: 'PLAN', col: C.entry,
  cond: `long ${fmt(plan.entryLo)}-${fmt(plan.entryHi)}, stop ${fmt(plan.stop)}`,
  rule: `${plan.basis} entry, only on a daily close that holds ${fmt(plan.entryLo)}. T1 ${fmt(plan.t1)} (${plan.t1Basis}), T2 ${fmt(plan.t2)} (${k2 > plan.t1 + atrNow * 0.5 ? 'upper 2-ATR Keltner' : 'T1 + 1 ATR'}). R:R ${plan.rr.toFixed(1)} / ${plan.rr2.toFixed(1)}.`,
});
const IY = SY + rowsDef.length * 17 + 14;
rules.forEach((r, i) => {
  const y = IY + i * 38;
  push(`<rect x="${PAD_L}" y="${y - 20}" width="${PLOT_W}" height="34" rx="6" fill="${r.col}" fill-opacity="0.05"/>`);
  push(`<text x="${PAD_L + 16}" y="${y + 2}" ${mono} font-size="13" fill="${r.col}" font-weight="700">${r.kw}</text>`);
  push(`<text x="${PAD_L + 74}" y="${y + 2}" ${mono} font-size="13" fill="${C.text}">${esc(r.cond)}</text>`);
  push(`<text x="${PAD_L + 400}" y="${y + 2}" ${mono} font-size="12.5" fill="${C.dim}">${esc(r.rule)}</text>`);
});

// Legend for the left side of the strip area.
const LY = SY;
const legend = [
  [C.call, 'bar', 'call wall (green tick)'],
  [C.put, 'bar', 'put wall (red tick)'],
  [C.pin, 'dot', 'magnet (heaviest strike), size = its gamma'],
  [C.flip, 'bar', 'gamma flip (today)'],
  [C.kc, 'bar', 'Keltner 1 / 2 ATR'],
  [C.tp, 'bar', 'T1 / T2 take profit'],
  [C.stop, 'bar', 'stop'],
  [C.dim, 'txt', '* = beyond the priced move'],
];
legend.forEach(([col, kind, label], i) => {
  const x = PAD_L + 10 + (i % 3) * 230, y = LY + Math.floor(i / 3) * 22;
  if (kind === 'bar') push(`<line x1="${x}" x2="${x + 16}" y1="${y - 4}" y2="${y - 4}" stroke="${col}" stroke-width="3"/>`);
  if (kind === 'dot') push(`<circle cx="${x + 8}" cy="${y - 4}" r="6" fill="none" stroke="${col}" stroke-width="1.6"/>`);
  if (kind === 'dia') push(`<rect x="${x + 4}" y="${y - 8}" width="8" height="8" transform="rotate(45 ${x + 8} ${y - 4})" fill="${col}"/>`);
  push(`<text x="${x + (kind === 'txt' ? 0 : 24)}" y="${y}" ${mono} font-size="10.5" fill="${C.dim}">${esc(label)}</text>`);
});
push(`<text x="${PAD_L + 10}" y="${LY + 76}" ${mono} font-size="10.5" fill="${C.dim}" data-y="x">faded expiries carry under ${MIN_SHARE}% of open interest and do not steer the roads.</text>`);

push(`<text x="${PAD_L}" y="${H - 16}" ${mono} font-size="10.5" fill="${C.dim}">Levels are net gamma exposure by strike and expiry. Long gamma brakes, short gamma chases, the cone is what options are pricing. Not advice.</text>`);

// ── render ──────────────────────────────────────────────────────────────────
const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>html,body{margin:0;background:${C.bg}}</style></head>
<body><svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${svg.join('\n')}</svg></body></html>`;
mkdirSync(OUT, { recursive: true });
const stamp = new Date().toISOString().slice(0, 10);
// Log this plan (one per symbol per ET day; a re-run replaces that day's row)
// and re-grade the symbol's older plans against the bars we already have.
{
  const madeOn = etNow().date;
  const rows = readLedger(sym).filter((e) => e.madeOn !== madeOn);
  for (const e of rows) e.result = gradePlan(e, allBars);
  rows.push({
    v: 2, madeOn, asOf: new Date().toISOString(), spot, regime: negGamma ? 'negative' : 'positive',
    horizon: segs[segs.length - 1].end, plan: { ...plan }, result: { status: 'WAITING' },
  });
  rows.sort((a, b) => a.madeOn.localeCompare(b.madeOn));
  if (!argv.includes('--no-log')) writeLedger(sym, rows);
}
const base = join(OUT, `${sym.toLowerCase()}_horizon_${stamp}`);
writeFileSync(`${base}.html`, html);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1.6 });
await page.setContent(html, { waitUntil: 'networkidle' }).catch(() => {});
await page.screenshot({ path: `${base}.png` });
await browser.close();
writeFileSync(`${base}.json`, JSON.stringify({
  symbol: sym, asOf: new Date().toISOString(), spot, flip: flipNow, netGEX: gex.totalGEX,
  regime: negGamma ? 'negative gamma' : 'positive gamma', largest: largest.expiry,
  atr14: atrNow, ema21: emaNow, keltner: { u1: kcU1.at(-1), l1: kcL1.at(-1), u2: kcU2.at(-1), l2: kcL2.at(-1) }, plan,
  expiries: exps.map(({ expiry, dte, emPoints, callWall, putWall, cushion, magnet, magGex, settle, oiSharePct, major }) =>
    ({ expiry, dte, emPoints, callWall, putWall, cushion, magnet, magGex, settle, oiSharePct, major })),
  segments: segs,
}, null, 2) + '\n');
console.log(`${base}.png`);
for (const g of segs) console.log(`seg ${g.from}-${g.to}d to ${g.end}: call ${g.callWall} put ${g.putWall ?? `(${g.cushion})`} settle ${g.settle} magnet ${g.magnet}`);
