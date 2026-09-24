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
const W = 1600, H = 900;
const PAD_L = 64, PAD_R = 40, PAD_T = 116;
const PLOT_H = 600;
const PLOT_W = W - PAD_L - PAD_R;
const PAST_W = Math.round(PLOT_W * 0.36);          // the drive so far
const FWD_X = PAD_L + PAST_W;                       // tomorrow starts here
const FWD_W = PLOT_W - PAST_W;

const yLo = Math.min(lo, ...pts.map((p) => p.px)) - 0.25;
const yHi = Math.max(hi, ...pts.map((p) => p.px)) + 0.25;
const Y = (px) => PAD_T + PLOT_H - ((px - yLo) / (yHi - yLo)) * PLOT_H;
const X = (i) => PAD_L + (i / (pts.length - 1)) * PAST_W;

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

// ── the three roads ─────────────────────────────────────────────────────────
// One shared price axis, three branches out of spot. A waypoint is a price the
// tape has to deal with; its note says what the book does to price THERE, which
// is the whole point -- the same level behaves differently depending on which
// way you arrived at it.
const rangeLo = Math.min(magnet, Math.floor(spot)) - 1;
const rangeHi = Math.max(magnet, Math.ceil(flip));

const roads = [
  {
    key: 'UP',
    col: C.call,
    cond: `above ${flip.toFixed(2)}`,
    rule: gate
      ? `dealers brake. stalls at ${battle ? battle.strike : gate.strike}, dies at ${gate.strike}.`
      : `dealers brake. no ceiling in range.`,
    side: -1,
    pts: [
      { at: flip, tag: `${flip.toFixed(2)} FLIP`, note: 'dealers stop chasing, start braking' },
      battle ? { at: battle.strike, tag: `${battle.strike} WALL`, note: `${oiFmt(battle.putOi)} puts, needs volume` } : null,
      gate ? { at: gate.strike, tag: `${gate.strike} CEILING`, note: 'move dies here' } : null,
    ].filter(Boolean),
  },
  {
    key: 'RANGE',
    col: C.pin,
    isElse: true,
    labelBelow: true,
    cond: `between ${rangeLo} and ${rangeHi}`,
    rule: negGamma
      ? `chop around the ${magnet} pin. it knifes both edges.`
      : `quiet drift into the ${magnet} pin.`,
    side: -1,
    wave: true,
    pts: [{ at: magnet, tag: `${magnet} PIN`, note: negGamma ? 'short gamma, so it chops hard' : 'long gamma, so it settles' }],
  },
  {
    key: 'DOWN',
    col: C.put,
    cond: pocket ? `below ${pocket.hi + 1}` : `below ${Math.floor(spot)}`,
    rule: pocket
      ? `open air. ${pocket.lo} to ${pocket.hi} is empty. next stop ${floor.strike}.`
      : `every strike below carries size. grind, not a drop.`,
    side: 1,
    pts: pocket
      ? [
          { at: pocket.hi + 1, tag: `${pocket.hi + 1} LAST SHELF`, note: 'the last thing to lean on' },
          { at: (pocket.lo + pocket.hi) / 2, tag: 'EMPTY', note: `${pocket.lo} to ${pocket.hi}, nothing here`, open: true },
          { at: floor.strike, tag: `${floor.strike} FLOOR`, note: `${oiFmt(floor.putOi)} puts. the fight is here` },
        ]
      : [{ at: Math.round(lo), tag: `${Math.round(lo)}`, note: 'no thin band below' }],
  },
];

// ── svg ─────────────────────────────────────────────────────────────────────
let s = '';
const push = (x) => { s += x; };

push(`<rect width="${W}" height="${H}" fill="${C.bg}"/>`);

// header
push(`<text x="${PAD_L}" y="46" font-family="'Share Tech Mono',monospace" font-size="30" fill="${C.text}" letter-spacing="1">TOMORROW'S MAP <tspan fill="${C.green}">${esc(sym)}</tspan></text>`);
push(`<text x="${PAD_L}" y="72" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · flip ${flip.toFixed(2)} · pin ${magnet} · net GEX ${fmtM(gex.totalGEX)}</text>`);
const pillC = negGamma ? C.coral : C.green;
push(`<rect x="${W - PAD_R - 330}" y="26" width="330" height="34" rx="17" fill="${negGamma ? '#1a0e11' : '#0c1a13'}" stroke="${pillC}" stroke-opacity="0.45"/>`);
push(`<text x="${W - PAD_R - 165}" y="48" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="14" fill="${pillC}">${negGamma ? 'NEGATIVE GAMMA / moves get amplified' : 'POSITIVE GAMMA / moves get damped'}</text>`);
push(`<text x="${W - PAD_R}" y="76" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}">as of ${new Date().toISOString().slice(0, 16).replace('T', ' ')}Z</text>`);

// plot frame + tomorrow tint
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${PLOT_W}" height="${PLOT_H}" fill="${C.panel}" stroke="${C.line}"/>`);
push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${PLOT_H}" fill="#0c0c14"/>`);

// price rail
{
  const step = (yHi - yLo) > 18 ? 5 : 2;
  for (let v = Math.ceil(yLo / step) * step; v <= yHi; v += step) {
    push(`<line x1="${PAD_L}" y1="${Y(v)}" x2="${W - PAD_R}" y2="${Y(v)}" stroke="${C.line}" stroke-opacity="0.7"/>`);
    push(`<text x="${PAD_L - 8}" y="${Y(v) + 4}" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.dim}">${v}</text>`);
  }
}

// the drive so far
push(`<polyline fill="none" stroke="${C.cyan}" stroke-width="1.6" stroke-opacity="0.85" points="${pts.map((p, i) => `${X(i).toFixed(1)},${Y(p.px).toFixed(1)}`).join(' ')}"/>`);
sessions.forEach((d) => {
  const i = pts.findIndex((p) => dayKey(p.t) === d);
  push(`<text x="${X(i) + 5}" y="${PAD_T + PLOT_H - 8}" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.dim}">${d.slice(5)}</text>`);
});
push(`<text x="${PAD_L + 8}" y="${PAD_T + 20}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}" letter-spacing="2">THE LAST 5 SESSIONS</text>`);
push(`<line x1="${FWD_X}" y1="${PAD_T}" x2="${FWD_X}" y2="${PAD_T + PLOT_H}" stroke="${C.dim}" stroke-opacity="0.45" stroke-dasharray="3 4"/>`);
push(`<text x="${FWD_X + 12}" y="${PAD_T + 20}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}" letter-spacing="2">TOMORROW</text>`);

// spot marker: where every road starts
const ys = Y(spot);
push(`<circle cx="${FWD_X}" cy="${ys}" r="5" fill="${C.text}"/>`);
push(`<text x="${FWD_X + 10}" y="${ys + 22}" font-family="'JetBrains Mono',monospace" font-size="12" fill="${C.text}">${spot.toFixed(2)} now</text>`);

// smooth a run of points into a path
function smooth(pp) {
  if (pp.length < 2) return '';
  let d = `M ${pp[0][0].toFixed(1)},${pp[0][1].toFixed(1)}`;
  for (let i = 1; i < pp.length - 1; i++) {
    const mx = (pp[i][0] + pp[i + 1][0]) / 2, my = (pp[i][1] + pp[i + 1][1]) / 2;
    d += ` Q ${pp[i][0].toFixed(1)},${pp[i][1].toFixed(1)} ${mx.toFixed(1)},${my.toFixed(1)}`;
  }
  const l = pp[pp.length - 1];
  d += ` L ${l[0].toFixed(1)},${l[1].toFixed(1)}`;
  return d;
}

const ROAD_X0 = FWD_X + 14;
const ROAD_W = FWD_W - 210;   // leave room for the waypoint labels

for (const r of roads) {
  // waypoint x positions march evenly out along the road
  const n = r.pts.length;
  const xs = r.wave
    ? r.pts.map(() => ROAD_X0 + ROAD_W * 0.3)
    : r.pts.map((_, i) => ROAD_X0 + ROAD_W * ((i + 1) / n));

  let path;
  if (r.wave) {
    // the range road oscillates instead of going anywhere
    const wp = [[FWD_X, ys]];
    const cycles = 3.5, steps = 48;
    for (let i = 1; i <= steps; i++) {
      const f = i / steps;
      const px = magnet + Math.sin(f * Math.PI * 2 * cycles) * ((rangeHi - rangeLo) / 2) * 0.5;
      wp.push([ROAD_X0 + ROAD_W * f, Y(px)]);
    }
    path = smooth(wp);
    // the box it chops inside
    push(`<rect x="${FWD_X}" y="${Y(rangeHi)}" width="${ROAD_X0 + ROAD_W - FWD_X}" height="${Y(rangeLo) - Y(rangeHi)}" fill="${r.col}" fill-opacity="0.035" stroke="${r.col}" stroke-opacity="0.22" stroke-dasharray="4 5"/>`);
  } else {
    path = smooth([[FWD_X, ys], ...r.pts.map((w, i) => [xs[i], Y(w.at)])]);
  }
  push(`<path d="${path}" fill="none" stroke="${r.col}" stroke-width="${r.wave ? 2 : 2.6}" stroke-opacity="${r.wave ? 0.6 : 0.9}" stroke-linecap="round"/>`);

  // waypoints
  r.pts.forEach((w, i) => {
    const x = xs[i], y = Y(w.at);
    if (w.open) {
      // an air pocket is drawn as a gap in the road, not a stop on it
      push(`<circle cx="${x}" cy="${y}" r="4" fill="none" stroke="${r.col}" stroke-width="1.6" stroke-dasharray="2 2"/>`);
    } else {
      push(`<circle cx="${x}" cy="${y}" r="5.5" fill="${C.bg}" stroke="${r.col}" stroke-width="2.4"/>`);
    }
    // The road arrives from the lower/upper left and leaves to the right, so the
    // only reliably empty quadrant is back over the shoulder. Last stop is the
    // exception: nothing follows it, so its label can sit out front.
    const last = i === n - 1;
    const tx = last ? x + 12 : x - 12;
    const anchor = last ? 'start' : 'end';
    const ty = y + (r.labelBelow ? 30 : r.side < 0 ? -28 : 24);
    push(`<text x="${tx}" y="${ty}" text-anchor="${anchor}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${r.col}" font-weight="700">${esc(w.tag)}</text>`);
    push(`<text x="${tx}" y="${ty + 15}" text-anchor="${anchor}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}">${esc(w.note)}</text>`);
  });

  // road name at the far end
  const endY = r.wave ? Y(magnet) : Y(r.pts[n - 1].at);
  push(`<text x="${ROAD_X0 + ROAD_W + 12}" y="${endY + 4}" font-family="'Share Tech Mono',monospace" font-size="15" fill="${r.col}" letter-spacing="1">${r.key}</text>`);
}

// ── the if / else ───────────────────────────────────────────────────────────
const IF_T = PAD_T + PLOT_H + 40;
// UP and DOWN are the two IFs; the range case is what is left over.
const ifRows = [...roads.filter((r) => !r.isElse), ...roads.filter((r) => r.isElse)];
ifRows.forEach((r, i) => {
  const y = IF_T + i * 42;
  const kw = r.isElse ? 'ELSE' : 'IF';
  push(`<rect x="${PAD_L}" y="${y - 20}" width="${PLOT_W}" height="34" rx="6" fill="${r.col}" fill-opacity="0.06"/>`);
  push(`<text x="${PAD_L + 16}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${r.col}" font-weight="700">${kw}</text>`);
  push(`<text x="${PAD_L + 74}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.text}">${esc(kw === 'ELSE' ? `it holds ${r.cond}` : `it goes ${r.cond}`)}</text>`);
  push(`<text x="${PAD_L + 330}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">${esc(r.rule)}</text>`);
});

push(`<text x="${PAD_L}" y="${H - 16}" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.dim}">Levels are net gamma exposure by strike. Where dealers are long gamma they brake, where they are short they chase, where there is nothing price travels. Not advice.</text>`);

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
