#!/usr/bin/env node
// gamma_tomorrow.mjs — "Tomorrow's Map": one picture that says where price gets
// dragged, where it stalls, and where the floor drops out, before the bell.
//
// The thesis this chart encodes: net GEX per strike is a map of how hard dealers
// have to hedge at each price. Big positive = they sell rips / buy dips (damped).
// Big negative = they chase (amplified). Thin = nothing happens, price travels.
//
// Usage:
//   node gamma_tomorrow.mjs SPY [--out /tmp/gamma] [--band 1.4]
//
// Keys: .env_td_api (bare X-API-Key on one line). Same convention as render_chart.mjs.

import { readFileSync, mkdirSync, existsSync, writeFileSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { homedir } from 'os';

const PW_HOME = join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs');
const { chromium } = await import(existsSync(PW_HOME) ? PW_HOME : 'playwright');

const DEV_BASE = 'https://api.traderdaddy.pro/api/v1';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36';

// Gamma Map palette (docs/gex-chart/index.html).
const C = {
  bg: '#0a0a0e', panel: '#101018', line: '#1c1c28', text: '#e6e6ee', dim: '#8a8aa0',
  call: '#00d68f', put: '#ff4d6d', flip: '#a855f7', pin: '#ffb000',
  green: '#00ff88', cyan: '#00f3ff', coral: '#ff5c6c',
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

const api = async (path) => {
  const r = await fetch(`${DEV_BASE}${path}`, { headers: { 'X-API-Key': KEY, 'User-Agent': UA } });
  const j = await r.json();
  if (!j.success) throw new Error(`${path}: ${j.message || j.error}`);
  return j.data;
};

// ── args ────────────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const sym = (argv.find((a) => !a.startsWith('--')) || 'SPY').toUpperCase();
const arg = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const OUT = arg('out', '/tmp/gamma');
const BAND = parseFloat(arg('band', '1.4')) / 100;   // % of spot drawn above/below

const gex = await api(`/gex/${sym}`);
const hist = await api(`/gex/${sym}/historical?hours=168`);

const spot = gex.spotPrice;
const flip = gex.gammaFlipLevel;
const magnet = gex.maxGammaStrike;
const lo = spot * (1 - BAND), hi = spot * (1 + BAND);
const ladder = gex.byStrike.filter((s) => s.strike >= lo && s.strike <= hi).sort((a, b) => a.strike - b.strike);

// ── structure: read the ladder the way a trader would ───────────────────────
// A "wall" is a strike whose |netGEX| is a large share of the local book. An "air
// pocket" is a run of strikes that together carry less than one wall -- that is
// where price has nothing to lean on and covers ground fast.
const maxAbs = Math.max(...ladder.map((s) => Math.abs(s.netGex)));
const WALL = maxAbs * 0.28;   // wall threshold: ~a third of the biggest level

const above = ladder.filter((s) => s.strike > spot);
const below = ladder.filter((s) => s.strike < spot);

// The gate: first strike above spot where the book turns decisively long gamma.
const gate = above.find((s) => s.netGex > WALL) || null;
// The battle: biggest short-gamma strike above spot before that gate.
// The magnet is already tagged on its own; a "battle" is the *other* short-gamma
// shelf between spot and the gate, which is what actually stops a rally.
const battle = above.filter((s) => s.netGex < -WALL && s.strike !== magnet && (!gate || s.strike < gate.strike))
  .sort((a, b) => a.netGex - b.netGex)[0] || null;
// The floor: biggest short-gamma strike below spot.
const floor = below.filter((s) => s.netGex < -WALL).sort((a, b) => a.netGex - b.netGex)[0] || null;

// Air pocket: the run of thin strikes between spot and that floor.
let pocket = null;
if (floor) {
  const run = below.filter((s) => s.strike > floor.strike && Math.abs(s.netGex) < WALL);
  if (run.length >= 2) {
    pocket = {
      lo: Math.min(...run.map((s) => s.strike)),
      hi: Math.max(...run.map((s) => s.strike)),
      net: run.reduce((a, s) => a + Math.abs(s.netGex), 0),
      n: run.length,
    };
  }
}

const negGamma = gex.totalGEX < 0;
const fmtM = (v) => {
  const a = Math.abs(v);
  if (a >= 1e9) return `${v < 0 ? '−' : ''}$${(a / 1e9).toFixed(2)}B`;
  return `${v < 0 ? '−' : ''}$${Math.round(a / 1e6)}M`;
};
const oiFmt = (v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(Math.round(v)));

// ── price history: 1-min spot, grouped by session ───────────────────────────
const pts = hist.map((p) => ({ t: new Date(p.snapshotTime), px: p.spotPrice }));
const dayKey = (d) => d.toISOString().slice(0, 10);
const sessions = [...new Set(pts.map((p) => dayKey(p.t)))];

// ── geometry ────────────────────────────────────────────────────────────────
const W = 1600, H = 1000;
const PAD_L = 64, PAD_R = 168, PAD_T = 118;
const PLOT_H = 560;
const PLOT_W = W - PAD_L - PAD_R;
const PAST_W = Math.round(PLOT_W * 0.58);          // price history
const FWD_X = PAD_L + PAST_W;                       // "tomorrow" zone starts here
const FWD_W = PLOT_W - PAST_W;

const yLo = Math.min(lo, ...pts.map((p) => p.px)) - 0.25;
const yHi = Math.max(hi, ...pts.map((p) => p.px)) + 0.25;
const Y = (px) => PAD_T + PLOT_H - ((px - yLo) / (yHi - yLo)) * PLOT_H;
const X = (i) => PAD_L + (i / (pts.length - 1)) * PAST_W;

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

// ── scenarios: generated from the structure, not hand-written ───────────────
const scenarios = [
  {
    key: 'IF IT TRENDS DOWN',
    tint: C.put,
    lead: pocket
      ? `Lose ${pocket.hi + 1}, and the book thins out.`
      : `Lose ${Math.floor(spot)}, and dealers are chasing.`,
    body: pocket
      ? [
          `${pocket.lo}–${pocket.hi} holds only ${fmtM(pocket.net)} of net gamma across ${pocket.n} strikes — versus ${fmtM(Math.abs(magnetLevel().netGex))} sitting at ${magnet} alone.`,
          `That is an air pocket. Nothing for price to lean on, so it covers the distance fast.`,
          floor ? `First real shelf is ${floor.strike} (${oiFmt(floor.putOi)} put OI, ${fmtM(floor.netGex)}). Expect the fight there, not on the way.` : '',
        ]
      : [`No thin band below spot — every strike down to ${Math.round(lo)} carries size. Grinding tape, not a waterfall.`],
    levels: pocket ? [pocket.hi + 1, pocket.lo, floor && floor.strike].filter(Boolean) : [],
  },
  {
    key: 'IF IT TRENDS UP',
    tint: C.call,
    lead: `${flip.toFixed(2)} is the gate, ${gate ? gate.strike : '—'} is the ceiling.`,
    body: [
      `Under ${flip.toFixed(2)} dealers are short gamma — they chase, so up-moves keep going.`,
      battle ? `${battle.strike} is the battle (${oiFmt(battle.putOi)} put OI, ${fmtM(battle.netGex)}). Heavy volume required; vol spikes there.` : '',
      gate ? `Clear ${gate.strike} (${oiFmt(gate.callOi)} call OI, ${fmtM(gate.netGex)}) and the regime flips: dealers sell rips, the move damps, and you are pinned rather than trending.` : '',
    ],
    levels: [flip, battle && battle.strike, gate && gate.strike].filter(Boolean),
  },
  {
    key: 'IF IT RANGES',
    tint: C.pin,
    lead: `${magnet} is the magnet, and it is a ${negGamma ? 'negative' : 'positive'}-gamma one.`,
    body: [
      `Spot is wedged between the magnet at ${magnet} and the flip at ${flip.toFixed(2)} — a ${Math.abs(flip - magnet).toFixed(2)} point box.`,
      negGamma
        ? `A short-gamma pin does not sit still. It chops hard around ${magnet} and knifes both edges. Fade the edges, do not hold the middle.`
        : `A long-gamma pin is the quiet kind. Dealers sell the highs and buy the lows into it. Mean reversion, small range.`,
      `Range to trade: ${(magnet - 1.5).toFixed(0)}–${(flip + 0.5).toFixed(0)}.`,
    ],
    levels: [magnet, flip],
  },
];
function magnetLevel() { return ladder.find((s) => s.strike === magnet) || { netGex: 0 }; }

// ── svg ─────────────────────────────────────────────────────────────────────
let s = '';
const push = (x) => { s += x; };

push(`<rect width="${W}" height="${H}" fill="${C.bg}"/>`);

// header
const asof = new Date(gex.lastUpdated || Date.now());
push(`<text x="${PAD_L}" y="46" font-family="'Share Tech Mono',monospace" font-size="30" fill="${C.text}" letter-spacing="1">TOMORROW'S MAP <tspan fill="${C.green}">${esc(sym)}</tspan></text>`);
push(`<text x="${PAD_L}" y="72" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · flip ${flip.toFixed(2)} · magnet ${magnet} · net GEX ${fmtM(gex.totalGEX)}</text>`);
const pillC = negGamma ? C.coral : C.green;
push(`<rect x="${W - PAD_R - 300}" y="26" width="300" height="34" rx="17" fill="${negGamma ? '#1a0e11' : '#0c1a13'}" stroke="${pillC}" stroke-opacity="0.45"/>`);
push(`<text x="${W - PAD_R - 150}" y="48" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="14" fill="${pillC}">${negGamma ? 'NEGATIVE GAMMA — amplified' : 'POSITIVE GAMMA — damped'}</text>`);
push(`<text x="${W - PAD_R - 150}" y="74" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}">as of ${asof.toISOString().slice(0, 16).replace('T', ' ')}Z</text>`);

// plot frame
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${PLOT_W}" height="${PLOT_H}" fill="${C.panel}" stroke="${C.line}"/>`);
// tomorrow zone tint
push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${PLOT_H}" fill="#0d0d16"/>`);
push(`<line x1="${FWD_X}" y1="${PAD_T}" x2="${FWD_X}" y2="${PAD_T + PLOT_H}" stroke="${C.dim}" stroke-opacity="0.5" stroke-dasharray="3 4"/>`);
push(`<text x="${FWD_X + 10}" y="${PAD_T + 20}" font-family="'JetBrains Mono',monospace" font-size="12" fill="${C.dim}" letter-spacing="2">TOMORROW — THE BOOK AS IT STANDS</text>`);

// regime shading: below flip = short gamma
const yFlip = Y(flip);
push(`<rect x="${PAD_L}" y="${yFlip}" width="${PLOT_W}" height="${PAD_T + PLOT_H - yFlip}" fill="${C.put}" fill-opacity="0.045"/>`);
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${PLOT_W}" height="${yFlip - PAD_T}" fill="${C.call}" fill-opacity="0.04"/>`);

// air pocket
if (pocket) {
  const yp1 = Y(pocket.hi + 0.5), yp2 = Y(pocket.lo - 0.5);
  push(`<rect x="${FWD_X}" y="${yp1}" width="${FWD_W}" height="${yp2 - yp1}" fill="none" stroke="${C.coral}" stroke-opacity="0.35" stroke-dasharray="5 5"/>`);
  push(`<text x="${FWD_X + FWD_W / 2}" y="${(yp1 + yp2) / 2 + 4}" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="12" fill="${C.coral}" fill-opacity="0.8" letter-spacing="3">AIR POCKET</text>`);
}

// price rail
{
  const step = (yHi - yLo) > 18 ? 5 : 2;
  for (let v = Math.ceil(yLo / step) * step; v <= yHi; v += step) {
    push(`<line x1="${PAD_L}" y1="${Y(v)}" x2="${W - PAD_R}" y2="${Y(v)}" stroke="${C.line}" stroke-opacity="0.7"/>`);
    push(`<text x="${PAD_L - 8}" y="${Y(v) + 4}" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.dim}">${v}</text>`);
  }
}

// session separators + price line
sessions.forEach((d, k) => {
  if (k === 0) return;
  const i = pts.findIndex((p) => dayKey(p.t) === d);
  push(`<line x1="${X(i)}" y1="${PAD_T}" x2="${X(i)}" y2="${PAD_T + PLOT_H}" stroke="${C.line}"/>`);
});
sessions.forEach((d) => {
  const i = pts.findIndex((p) => dayKey(p.t) === d);
  push(`<text x="${X(i) + 6}" y="${PAD_T + PLOT_H - 8}" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.dim}">${d.slice(5)}</text>`);
});
push(`<polyline fill="none" stroke="${C.cyan}" stroke-width="1.6" points="${pts.map((p, i) => `${X(i).toFixed(1)},${Y(p.px).toFixed(1)}`).join(' ')}"/>`);

// ── the walls: horizontal netGEX bars in the tomorrow zone ──────────────────
const BAR_MAX = FWD_W * 0.62;
const rowH = Math.max(6, PLOT_H / (ladder.length * 1.35));
for (const st of ladder) {
  const w = (Math.abs(st.netGex) / maxAbs) * BAR_MAX;
  const col = st.netGex >= 0 ? C.call : C.put;
  const y = Y(st.strike) - rowH / 2;
  push(`<rect x="${FWD_X + 2}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${rowH.toFixed(1)}" fill="${col}" fill-opacity="${Math.abs(st.netGex) > WALL ? 0.72 : 0.28}" rx="1"/>`);
  if (Math.abs(st.netGex) > WALL) {
    push(`<text x="${FWD_X + w + 10}" y="${(y + rowH / 2 + 4).toFixed(1)}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${col}">${st.strike} · ${fmtM(st.netGex)}</text>`);
  }
}

// ── key lines with right-edge tags ──────────────────────────────────────────
// Lines run solid across the price history and fade to dotted across the book, so
// the strike bars and their labels stay readable underneath.
const tags = [];
const tag = (px, label, col, dash) => {
  const y = Y(px);
  push(`<line x1="${PAD_L}" y1="${y}" x2="${FWD_X}" y2="${y}" stroke="${col}" stroke-width="1.4" ${dash ? `stroke-dasharray="${dash}"` : ''} stroke-opacity="0.9"/>`);
  push(`<line x1="${FWD_X}" y1="${y}" x2="${W - PAD_R}" y2="${y}" stroke="${col}" stroke-width="1" stroke-dasharray="2 5" stroke-opacity="0.35"/>`);
  tags.push({ y, label, col });
};
if (gate) tag(gate.strike, `${gate.strike} CEILING`, C.call);
if (battle) tag(battle.strike, `${battle.strike} BATTLE`, C.put);
tag(flip, `${flip.toFixed(2)} GAMMA FLIP`, C.flip, '7 4');
tag(magnet, `${magnet} MAGNET`, C.pin);
if (floor) tag(floor.strike, `${floor.strike} FLOOR`, C.put);
tag(spot, `${spot.toFixed(2)} SPOT`, C.text, '2 3');

// De-collide the right-edge tags: anything closer than a tag height gets nudged
// down the rail, with a leader line back to its true level.
const TAG_H = 24;
tags.sort((a, b) => a.y - b.y);
let prevY = -Infinity;
for (const t of tags) {
  t.ty = Math.max(t.y, prevY + TAG_H);
  prevY = t.ty;
}
for (const t of tags) {
  if (Math.abs(t.ty - t.y) > 1) {
    push(`<line x1="${W - PAD_R}" y1="${t.y}" x2="${W - PAD_R + 4}" y2="${t.ty}" stroke="${t.col}" stroke-width="1" stroke-opacity="0.6"/>`);
  }
  push(`<rect x="${W - PAD_R + 4}" y="${t.ty - 11}" width="152" height="22" rx="4" fill="${t.col}"/>`);
  push(`<text x="${W - PAD_R + 12}" y="${t.ty + 4}" font-family="'JetBrains Mono',monospace" font-size="11.5" fill="#0a0a0e" font-weight="700">${esc(t.label)}</text>`);
}

// ── scenario cards ──────────────────────────────────────────────────────────
const CARD_T = PAD_T + PLOT_H + 34;
const CARD_W = (PLOT_W + PAD_R - 64) / 3 - 16;
scenarios.forEach((sc, i) => {
  const x = PAD_L + i * (CARD_W + 24);
  push(`<rect x="${x}" y="${CARD_T}" width="${CARD_W}" height="236" rx="10" fill="${C.panel}" stroke="${C.line}"/>`);
  push(`<rect x="${x}" y="${CARD_T}" width="4" height="236" rx="2" fill="${sc.tint}"/>`);
  push(`<text x="${x + 20}" y="${CARD_T + 30}" font-family="'JetBrains Mono',monospace" font-size="12" fill="${sc.tint}" letter-spacing="2">${esc(sc.key)}</text>`);
  push(`<text x="${x + 20}" y="${CARD_T + 56}" font-family="'JetBrains Mono',monospace" font-size="15" fill="${C.text}">${esc(sc.lead)}</text>`);
  let y = CARD_T + 84;
  for (const para of sc.body.filter(Boolean)) {
    for (const ln of wrap(para, Math.floor((CARD_W - 44) / 6.95))) {
      push(`<text x="${x + 20}" y="${y}" font-family="'JetBrains Mono',monospace" font-size="11.5" fill="${C.dim}">${esc(ln)}</text>`);
      y += 16;
    }
    y += 6;
  }
});

function wrap(t, n) {
  const out = []; let ln = '';
  for (const w of t.split(' ')) {
    if ((ln + ' ' + w).trim().length > n) { out.push(ln.trim()); ln = w; } else ln += ' ' + w;
  }
  if (ln.trim()) out.push(ln.trim());
  return out;
}

push(`<text x="${PAD_L}" y="${H - 18}" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.dim}">Net GEX by strike, ${sym} · bars = how hard dealers must hedge there · green damps, red amplifies, thin = price travels · not advice</text>`);

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${s}</svg>`;

// ── render ──────────────────────────────────────────────────────────────────
mkdirSync(OUT, { recursive: true });
const stamp = new Date().toISOString().slice(0, 10);
const png = join(OUT, `${sym.toLowerCase()}_tomorrow_${stamp}.png`);
const html = `<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>html,body{margin:0;background:${C.bg}}</style>${svg}`;
writeFileSync(join(OUT, `${sym.toLowerCase()}_tomorrow_${stamp}.html`), html);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
await page.setContent(html, { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await page.screenshot({ path: png });
await browser.close();

console.log(`spot ${spot} | flip ${flip} | magnet ${magnet} | netGEX ${fmtM(gex.totalGEX)}`);
console.log(`gate ${gate?.strike} | battle ${battle?.strike} | floor ${floor?.strike} | pocket ${pocket ? `${pocket.lo}-${pocket.hi}` : 'none'}`);
console.log(png);
