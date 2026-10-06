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

import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'fs';
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
// expiryStats carries per-expiry walls, flip and the implied expected move.
// The magnet (heaviest strike for that expiry alone) comes from the matrix.
const exps = matrix.expiryStats
  .filter((e) => e.dte > 0 && e.dte <= HORIZON)
  .map((e) => {
    const col = matrix.expirations.indexOf(e.expiry);
    let magnet = null, magGex = 0;
    for (const r of matrix.rows) {
      const v = r.gex[col];
      if (v != null && Math.abs(v) > Math.abs(magGex)) { magGex = v; magnet = r.strike; }
    }
    // The settle strike: heaviest strike within half the priced move. On a
    // name like ASTS the overall magnet IS the put wall, so a range road built
    // on it just retraces the down road and says nothing new.
    let settle = null, setGex = 0;
    for (const r of matrix.rows) {
      const v = r.gex[col];
      if (v != null && Math.abs(r.strike - spot) <= e.emPoints * 0.5 && Math.abs(v) > Math.abs(setGex)) { setGex = v; settle = r.strike; }
    }
    return { ...e, magnet, magGex, settle, setGex, major: e.oiSharePct >= MIN_SHARE || e.isLargest };
  });
if (!exps.length) throw new Error(`no expiries within ${HORIZON} days`);
const majors = exps.filter((e) => e.major);
const largest = exps.find((e) => e.isLargest) || majors.reduce((a, e) => (e.oiSharePct > a.oiSharePct ? e : a), majors[0]);
const last = exps[exps.length - 1];
const negGamma = gex.totalGEX < 0;

// ── the trade plan ──────────────────────────────────────────────────────────
// Built off the heaviest expiry, because that is where the size is. Entry is
// the put wall plus half an ATR; the stop sits a full ATR under the wall,
// since in short gamma a put wall is a crowd, not a floor, and a close through
// it is the signal the long was wrong. T1 is the call wall. T2 is the upper
// 2-ATR Keltner if it clears T1 by half an ATR, else one ATR past T1.
const r2 = (v) => Math.round(v * 100) / 100;
const pw = largest.putWall != null && largest.putWall < spot ? largest.putWall : r2(spot - atrNow);
const plan = {
  entryLo: pw,
  entryHi: r2(Math.min(spot, pw + atrNow * 0.5)),
  stop: r2(pw - atrNow),
  t1: largest.callWall != null && largest.callWall > spot ? largest.callWall : r2(kcU1[kcU1.length - 1]),
};
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
const fwdLv = [...exps.flatMap((e) => [e.callWall, e.putWall, e.magnet, e.settle, e.flip]).filter((v) => v != null && reach(v)), plan.stop, plan.t2];
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
push(`<text x="${PAD_L}" y="72" ${mono} font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · flip ${fmt(flipNow)} · net GEX ${fmtM(gex.totalGEX)} · options price a ±${largest.emPoints.toFixed(2)} move into ${md(largest.expiry)}, the heaviest expiry (${largest.oiSharePct.toFixed(0)}% of OI)</text>`);
const pillC = negGamma ? C.put : C.call;
push(`<rect x="${W - PAD_R - 330}" y="26" width="330" height="34" rx="17" fill="${negGamma ? '#1a0e11' : '#0c1a13'}" stroke="${pillC}" stroke-opacity="0.45"/>`);
push(`<text x="${W - PAD_R - 165}" y="48" text-anchor="middle" ${mono} font-size="14" fill="${pillC}">${negGamma ? 'NEGATIVE GAMMA / moves get amplified' : 'POSITIVE GAMMA / moves get damped'}</text>`);
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

// Expiry columns: faint vertical, date at the bottom, monthly OPEX louder.
for (const e of exps) {
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
// Only majors steer a road. Start at spot, step through each major's level.
const roadPts = (key) => [[XF(0), spot], ...majors.filter((e) => e[key] != null).map((e) => [XF(e.dte), e[key]])];
const smooth = (p) => {
  let d = `M ${p[0][0].toFixed(1)} ${Y(clampY(p[0][1])).toFixed(1)}`;
  for (let i = 1; i < p.length; i++) {
    const [x0, v0] = p[i - 1], [x1, v1] = p[i], mx = (x0 + x1) / 2;
    d += ` C ${mx.toFixed(1)} ${Y(clampY(v0)).toFixed(1)}, ${mx.toFixed(1)} ${Y(clampY(v1)).toFixed(1)}, ${x1.toFixed(1)} ${Y(clampY(v1)).toFixed(1)}`;
  }
  return d;
};
const roads = [
  { key: 'callWall', col: C.call, name: 'UP', what: 'call wall' },
  { key: 'putWall', col: C.put, name: 'DOWN', what: 'put wall' },
  { key: 'settle', col: C.pin, name: 'RANGE', what: 'settles near' },
];
for (const r of roads) {
  const p = roadPts(r.key);
  if (p.length < 2) continue;
  push(`<path d="${smooth(p)}" fill="none" stroke="${r.col}" stroke-width="9" stroke-opacity="0.3" filter="url(#glowS)"/>`);
  push(`<path d="${smooth(p)}" fill="none" stroke="${r.col}" stroke-width="${r.key === 'settle' ? 2 : 2.6}" stroke-opacity="0.85" ${r.key === 'settle' ? 'stroke-dasharray="7 5"' : ''}/>`);
}
// Flip trajectory: purple dots per expiry, joined thinly.
const flipPts = exps.filter((e) => e.flip != null && reach(e.flip)).map((e) => [XF(e.dte), e.flip, e]);
if (flipPts.length > 1) push(`<polyline points="${flipPts.map(([x, v]) => `${x.toFixed(1)},${Y(clampY(v)).toFixed(1)}`).join(' ')}" fill="none" stroke="${C.flip}" stroke-width="1.2" stroke-opacity="0.6" stroke-dasharray="2 4"/>`);
for (const [x, v, e] of flipPts) push(`<rect x="${x - 4}" y="${Y(v) - 4}" width="8" height="8" transform="rotate(45 ${x} ${Y(v)})" fill="${C.flip}" fill-opacity="${e.major ? 0.9 : 0.4}"/>`);

// Per-expiry markers. Minor expiries are ticks only so they read as context.
for (const e of exps) {
  const x = XF(e.dte);
  const a = e.major ? 1 : 0.35;
  for (const [v, col] of [[e.callWall, C.call], [e.putWall, C.put]]) {
    if (v == null || !reach(v)) continue;
    const outside = Math.abs(v - spot) > e.emPoints;
    push(`<line x1="${x - 9}" x2="${x + 9}" y1="${Y(v)}" y2="${Y(v)}" stroke="${col}" stroke-width="3" stroke-opacity="${outside ? a * 0.5 : a}"/>`);
  }
  if (e.magnet != null && reach(e.magnet)) {
    const rad = 4 + Math.sqrt(e.oiSharePct) * 2.2;
    const col = e.magGex >= 0 ? C.call : C.put;
    push(`<circle cx="${x}" cy="${Y(e.magnet)}" r="${rad.toFixed(1)}" fill="${col}" fill-opacity="${0.18 * a + 0.05}" stroke="${C.pin}" stroke-opacity="${a}" stroke-width="1.6"/>`);
  }
}

// Now dot.
push(`<circle cx="${XF(0)}" cy="${Y(spot)}" r="5" fill="${C.text}"/>`);
push(`<text x="${XF(0) + 8}" y="${Y(spot) + 20}" ${mono} font-size="12" fill="${C.text}">${spot.toFixed(2)} now</text>`);

// Road names sit just inside the last expiry, above their own line.
for (const r of roads) {
  const p = roadPts(r.key); if (p.length < 2) continue;
  const v = p[p.length - 1][1];
  const e = majors.filter((m) => m[r.key] != null).slice(-1)[0];
  const outside = e && Math.abs(v - spot) > e.emPoints;
  push(`<text x="${XF(maxDte) - 14}" y="${Y(clampY(v)) + (r.key === 'putWall' ? 20 : -10)}" text-anchor="end" font-family="'Share Tech Mono',monospace" font-size="13" fill="${r.col}" fill-opacity="${outside ? 0.55 : 0.95}" letter-spacing="1">${r.name} · ${fmt(v)}${outside ? ' *' : ''}</text>`);
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
// The numbers behind every marker, under their own column. Saves the reader
// from reverse-engineering the chart.
const SY = PAD_T + PLOT_H + 26;
const rowsDef = [
  ['±move', (e) => e.emPoints.toFixed(2), C.text],
  ['call wall', (e) => fmt(e.callWall), C.call],
  ['magnet', (e) => fmt(e.magnet), C.pin],
  ['settle', (e) => fmt(e.settle), C.pin],
  ['put wall', (e) => fmt(e.putWall), C.put],
  ['flip', (e) => fmt(e.flip), C.flip],
  ['OI share', (e) => `${e.oiSharePct.toFixed(0)}%`, C.dim],
];
rowsDef.forEach(([label, f, col], ri) => {
  const y = SY + ri * 17;
  push(`<text x="${FWD_X + 10}" y="${y}" ${mono} font-size="10.5" fill="${C.dim}">${label}</text>`);
  for (const e of exps) push(`<text x="${XF(e.dte)}" y="${y}" text-anchor="middle" ${mono} font-size="10.5" fill="${col}" fill-opacity="${e.major ? 1 : 0.45}">${f(e)}</text>`);
});

// ── IF / IF / ELSE ──────────────────────────────────────────────────────────
// Read off the heaviest expiry: that is where the size is, so that is the
// level set price has to answer to.
const L0 = largest;
const front = exps[0];
const above = L0.callWall != null && L0.callWall > spot ? L0.callWall : null;
const below = L0.putWall != null && L0.putWall < spot ? L0.putWall : null;
const flipRef = flipNow;
const rules = [
  {
    kw: 'IF', col: C.call,
    cond: flipRef != null && flipRef > spot ? `it reclaims ${fmt(flipRef)}` : `it holds over ${fmt(flipRef)}`,
    rule: above
      ? `${flipRef > spot ? 'back above the flip, dealers stop chasing and start braking.' : 'above the flip, dealers brake.'} ${fmt(above)} is the ${md(L0.expiry)} call wall, ${above - spot > L0.emPoints ? 'outside what options price by then.' : 'inside the priced move.'}`
      : 'no call wall above spot in the heavy expiry. nothing caps it but the cone.',
  },
  {
    kw: 'IF', col: C.put,
    cond: below ? `it loses ${fmt(below)}` : `it breaks ${(spot - front.emPoints).toFixed(2)}`,
    rule: below
      ? `${fmt(below)} is the ${md(L0.expiry)} put wall. a crowd, not a floor: below it dealers sell into the drop. cone bottom ${(spot - L0.emPoints).toFixed(2)}.`
      : 'no put wall below spot in the heavy expiry.',
  },
  {
    kw: 'ELSE', col: C.pin,
    cond: below && above ? `it lives between ${fmt(below)} and ${fmt(above)}` : 'it ranges',
    rule: `settles ${majors.map((e) => fmt(e.settle)).join(' → ')}, biggest pile at ${fmt(L0.magnet)}, into ${md(majors[majors.length - 1].expiry)}. ${negGamma ? 'short gamma, so the range gets knifed at both edges.' : 'long gamma, so it gets pinned.'}`,
  },
];
rules.push({
  kw: 'PLAN', col: C.entry,
  cond: `long ${fmt(plan.entryLo)}-${fmt(plan.entryHi)}, stop ${fmt(plan.stop)}`,
  rule: `only on a daily close that holds ${fmt(plan.entryLo)}. T1 ${fmt(plan.t1)} (call wall), T2 ${fmt(plan.t2)} (${k2 > plan.t1 + atrNow * 0.5 ? 'upper 2-ATR Keltner' : 'T1 + 1 ATR'}). R:R ${plan.rr.toFixed(1)} / ${plan.rr2.toFixed(1)}.`,
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
  [C.pin, 'dot', 'magnet (heaviest strike), size = OI share'],
  [C.flip, 'dia', 'gamma flip per expiry'],
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
  expiries: exps.map(({ expiry, dte, emPoints, callWall, putWall, flip, magnet, magGex, settle, oiSharePct, major }) =>
    ({ expiry, dte, emPoints, callWall, putWall, flip, magnet, magGex, settle, oiSharePct, major })),
}, null, 2) + '\n');
console.log(`${base}.png`);
for (const e of exps) console.log(`${e.expiry} dte${e.dte} ±${e.emPoints.toFixed(2)} call ${e.callWall} put ${e.putWall} magnet ${e.magnet} settle ${e.settle} flip ${e.flip} oi ${e.oiSharePct.toFixed(1)}%${e.major ? ' *' : ''}`);
