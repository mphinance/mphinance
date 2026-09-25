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

// The dev API caps at 30 requests/minute. Two calls per run is nowhere near it
// in normal use, but iterating on the chart trips it constantly, and dying on a
// rate limit halfway through is a silly way to lose a render.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const api = async (path, tries = 4) => {
  for (let n = 1; ; n++) {
    const r = await fetch(`${DEV_BASE}${path}`, { headers: { 'X-API-Key': KEY, 'User-Agent': UA } });
    const j = await r.json().catch(() => ({}));
    if (j.success) return j.data;
    const limited = r.status === 429 || /requests per minute/i.test(j.message || j.error || '');
    if (!limited || n >= tries) throw new Error(`${path}: ${j.message || j.error || r.status}`);
    const wait = 20000 * n;
    console.log(`rate limited, waiting ${wait / 1000}s (attempt ${n}/${tries})`);
    await sleep(wait);
  }
};

// ── args ────────────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const sym = (argv.find((a) => !a.startsWith('--')) || 'SPY').toUpperCase();
const arg = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const OUT = arg('out', '/tmp/gamma');
const BAND = parseFloat(arg('band', '1.4')) / 100;   // % of spot drawn above/below

const gex = await api(`/gex/${sym}`);
const hist = await api(`/gex/${sym}/historical?hours=168`);
const matrix = await api(`/gex/${sym}/matrix`).catch(() => null);

const spot = gex.spotPrice;
const flip = gex.gammaFlipLevel;
const magnet = gex.maxGammaStrike;
const lo = spot * (1 - BAND), hi = spot * (1 + BAND);

// ── only count gamma that will still be here tomorrow ───────────────────────
// The snapshot's byStrike includes contracts expiring at tonight's close. Those
// are the loudest strikes on the board and they are gone by the open: on 9/23
// net GEX went from +$0.17B to -$2.09B across the bell as 0DTE rolled off. A map
// OF tomorrow built from a book that evaporates tonight is a map of nothing.
const todayET = new Date(Date.now() - 4 * 3600e3).toISOString().slice(0, 10);
let survivors = null, expiringShare = 0;
if (matrix?.rows?.length) {
  const live = matrix.expirations.map((e) => e > todayET);
  const sum = (arr, mask) => arr.reduce((a, v, i) => a + (mask[i] && v ? v : 0), 0);
  const all = matrix.expirations.map(() => true);
  survivors = new Map(matrix.rows.map((r) => [r.strike, sum(r.gex, live)]));
  const tot = matrix.rows.reduce((a, r) => a + Math.abs(sum(r.gex, all)), 0);
  const kept = matrix.rows.reduce((a, r) => a + Math.abs(sum(r.gex, live)), 0);
  expiringShare = tot ? 1 - kept / tot : 0;
}

const ladder = gex.byStrike
  .filter((s) => s.strike >= lo && s.strike <= hi)
  .map((s) => (survivors?.has(s.strike) ? { ...s, netGex: survivors.get(s.strike), gross: s.netGex } : s))
  .sort((a, b) => a.strike - b.strike);

// ── structure: read the ladder the way a trader would ───────────────────────
// A "wall" is a strike whose |netGEX| is a large share of the local book. An "air
// pocket" is a run of strikes that together carry less than one wall -- that is
// where price has nothing to lean on and covers ground fast.
const maxAbs = Math.max(...ladder.map((s) => Math.abs(s.netGex)));
const WALL = maxAbs * 0.28;   // wall threshold: ~a third of the biggest level

const above = ladder.filter((s) => s.strike > spot);
const below = ladder.filter((s) => s.strike < spot);

// The ceiling: the heaviest long-gamma strike above spot. Taking the FIRST one
// instead breaks whenever the positive stack starts right at spot -- you get a
// "ceiling" sitting below the gamma flip, which is nonsense.
const gate = above.filter((s) => s.netGex > WALL).sort((a, b) => b.netGex - a.netGex)[0] || null;
// The battle: biggest short-gamma strike above spot before that gate.
// The magnet is already tagged on its own; a "battle" is the *other* short-gamma
// shelf between spot and the gate, which is what actually stops a rally.
const battle = above.filter((s) => s.netGex < -WALL && s.strike !== magnet && (!gate || s.strike < gate.strike))
  .sort((a, b) => a.netGex - b.netGex)[0] || null;
// The pin is whatever price is actually wrestling with, so it has to be local.
// maxGammaStrike from the API is the biggest strike in the WHOLE book, which on
// a day with a far-off put wall is six points away and not a pin at all.
const near = ladder.filter((s) => Math.abs(s.strike - spot) <= 1.5);
const pin = near.length
  ? near.slice().sort((a, b) => Math.abs(b.netGex) - Math.abs(a.netGex))[0].strike
  : magnet;
const pinNet = (ladder.find((s) => s.strike === pin) || { netGex: 0 }).netGex;

// The brake: heaviest LONG-gamma strike between spot and the ceiling. Dealers
// sell rips there too, so a rally stalls into it long before it reaches the
// ceiling. Missing this is why 9/24's map said "nothing gives until 772" and
// then 9/25 topped at 770.29 and turned.
const brake = gate
  ? above.filter((s) => s.netGex > WALL && s.strike < gate.strike)
      .sort((a, b) => b.netGex - a.netGex)[0] || null
  : null;

// The floor: biggest short-gamma strike below spot.
const floor = below.filter((s) => s.netGex < -WALL).sort((a, b) => a.netGex - b.netGex)[0] || null;

// The cushion: the best positive-gamma strike below spot. Dealers are long
// gamma there, so they buy into weakness. This is structurally different from a
// big negative strike, which is a crowd, not a floor.
const cushion = floor
  ? below.filter((s) => s.strike > floor.strike && s.netGex > 0).sort((a, b) => b.netGex - a.netGex)[0] || null
  : null;

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

// ── the ledger: every map this tool publishes gets written down ────────────
// Without this the chart is a theory. With it, the left half of the picture can
// show whether last night's call actually happened, which is the only thing that
// makes the right half worth reading.
const LEDGER = join(ROOT, 'data/gamma_maps', `${sym}.json`);
let ledger = [];
try { ledger = JSON.parse(readFileSync(LEDGER, 'utf8')); } catch { /* first run */ }

const negGamma = gex.totalGEX < 0;
// When the flip sits on top of price it has no information: you get a crossing
// every few minutes and none of them mean anything. Say so rather than drawing
// two confident roads out of the same point.
const flipOnPrice = Math.abs(flip - spot) < spot * 0.0004;
const fmtM = (v) => {
  const a = Math.abs(v);
  if (a >= 1e9) return `${v < 0 ? '−' : ''}$${(a / 1e9).toFixed(2)}B`;
  return `${v < 0 ? '−' : ''}$${Math.round(a / 1e6)}M`;
};
const oiFmt = (v) => (v >= 1000 ? `${Math.round(v / 1000)}k` : String(Math.round(v)));

// ── price history: 1-min spot, grouped by session ───────────────────────────
const dayKey = (d) => d.toISOString().slice(0, 10);
const allPts = hist.map((p) => ({ t: new Date(p.snapshotTime), px: p.spotPrice }));
const allSessions = [...new Set(allPts.map((p) => dayKey(p.t)))];

// How far price typically gets from where it started. Measured against the PRIOR
// close, not intraday high-to-low, because that is exactly what these roads
// project from: the previous session's finish. It therefore includes the
// overnight gap, which on 9/24 was 70% of the day's entire move.
const excursions = [];
for (let i = 1; i < allSessions.length; i++) {
  const prevPx = allPts.filter((q) => dayKey(q.t) === allSessions[i - 1]).map((q) => q.px);
  const dayPx = allPts.filter((q) => dayKey(q.t) === allSessions[i]).map((q) => q.px);
  if (!prevPx.length || !dayPx.length) continue;
  const pc = prevPx[prevPx.length - 1];
  excursions.push(Math.max(Math.abs(Math.max(...dayPx) - pc), Math.abs(Math.min(...dayPx) - pc)));
}
const expected = excursions.length
  ? excursions.slice().sort((a, b) => a - b)[Math.floor(excursions.length / 2)]
  : spot * 0.006;

// Draw fewer sessions than we measure: the map only ever references the last
// one, and three sessions gives the candles almost double the width.
const SHOW = parseInt(arg('sessions', '3'), 10);
const keep = new Set(allSessions.slice(-SHOW));
const pts = allPts.filter((q) => keep.has(dayKey(q.t)));
const sessions = allSessions.slice(-SHOW);

// ── score the last call ─────────────────────────────────────────────────────
// Find the map that was made the session BEFORE the most recent one, then check
// it against what that session actually printed.
const lastSession = sessions[sessions.length - 1];
const priorSession = sessions[sessions.length - 2];
const sessionBars = (day) => pts.filter((q) => dayKey(q.t) === day).map((q) => q.px);

// 16:00 ET is 20:00 UTC. Anything short of that is a session still in flight:
// worth SHOWING, never worth scoring or writing to the ledger as a final grade.
const lastTick = pts[pts.length - 1].t;
const sessionClosed = lastTick.getUTCHours() >= 20;

let report = null;
const prev = ledger.find((e) => e.madeAfter === priorSession);
if (prev) {
  const bars = sessionBars(lastSession);
  if (bars.length) {
    const open = bars[0], high = Math.max(...bars), low = Math.min(...bars), close = bars[bars.length - 1];
    const checks = [];
    const add = (ok, text) => checks.push({ ok, text });

    const wentDown = open < prev.shelf || low < prev.shelf;
    const wentUp = high > prev.flip;
    add(true, wentDown && !wentUp ? `took the DOWN road` : wentUp && !wentDown ? `took the UP road` : wentUp && wentDown ? `took both roads` : `stayed in the range`);
    if (prev.cushion != null) add(low >= prev.cushion - 0.75, `held ${prev.cushion} cushion (low ${low.toFixed(2)})`);
    if (prev.wall != null) add(low > prev.wall, `never reached ${prev.wall} put wall`);
    if (prev.flip != null) add(high < prev.flip, `capped under ${prev.flip} flip (high ${high.toFixed(2)})`);
    if (prev.battle != null) add(high < prev.battle, `never tested ${prev.battle}`);
    if (prev.brake != null) add(high < prev.brake + 0.75, `stalled into ${prev.brake} (high ${high.toFixed(2)})`);

    const scored = checks.slice(1);
    report = {
      partial: !sessionClosed,
      day: lastSession, open, high, low, close, checks,
      hits: scored.filter((c) => c.ok).length, total: scored.length,
      levels: [prev.shelf, prev.cushion, prev.wall, prev.flip, prev.battle, prev.brake, prev.gate].filter((v) => v != null),
      prev,
    };
  }
}

// ── candles ─────────────────────────────────────────────────────────────────
// The history feed is a 1-minute spot sample, not a bar feed, so the candles are
// aggregated here: open/high/low/close of each bucket's samples. Bucket size is
// chosen so a body never gets thinner than a few pixels.
function buildCandles(minutes) {
  const out = [];
  let cur = null;
  pts.forEach((q, i) => {
    const day = dayKey(q.t);
    const slot = Math.floor((q.t.getUTCHours() * 60 + q.t.getUTCMinutes()) / minutes);
    if (!cur || cur.day !== day || cur.slot !== slot) {
      cur = { day, slot, i0: i, i1: i, o: q.px, h: q.px, l: q.px, c: q.px };
      out.push(cur);
    }
    cur.i1 = i;
    cur.h = Math.max(cur.h, q.px);
    cur.l = Math.min(cur.l, q.px);
    cur.c = q.px;
  });
  return out;
}

// ── geometry ────────────────────────────────────────────────────────────────
const W = 1600, H = 950;
const PAD_L = 64, PAD_R = 40, PAD_T = 116;
const PLOT_H = 600;
const PLOT_W = W - PAD_L - PAD_R;
const PAST_W = Math.round(PLOT_W * 0.42);          // the drive so far
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
const rangeLo = Math.min(pin, Math.floor(spot)) - 1;
const rangeHi = Math.max(pin, Math.ceil(flip));

const roads = [
  {
    key: 'UP',
    col: C.call,
    cond: `above ${flip.toFixed(2)}`,
    rule: gate
      ? (battle
          ? `dealers brake. stalls at ${battle.strike}, dies at ${gate.strike}.`
          : brake
            ? `dealers brake. stalls into ${brake.strike}, dies at ${gate.strike}.`
            : `dealers brake all the way. nothing gives until ${gate.strike}.`)
      : `dealers brake. no ceiling in range.`,
    side: -1,
    pts: [
      { at: flip, tag: `${flip.toFixed(2)} FLIP`, note: 'dealers stop chasing, start braking' },
      battle ? { at: battle.strike, tag: `${battle.strike} WALL`, note: `${oiFmt(battle.putOi)} puts, needs volume` } : null,
      !battle && brake ? { at: brake.strike, tag: `${brake.strike} BRAKE`, note: 'dealers sell rips here, rallies stall' } : null,
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
      ? `chop around the ${pin} pin. it knifes both edges.`
      : `quiet drift into the ${pin} pin.`,
    side: -1,
    wave: true,
    pts: [{ at: pin, tag: `${pin} PIN`, note: pinNet < 0 ? 'short gamma, so it chops hard' : 'long gamma, so it settles' }],
  },
  {
    key: 'DOWN',
    col: C.put,
    cond: pocket ? `below ${Math.min(pocket.hi + 1, Math.floor(spot))}` : `below ${Math.floor(spot)}`,
    rule: pocket
      ? (cushion && cushion.strike < Math.min(pocket.hi + 1, Math.floor(spot))
          ? `thin air. only real bid is ${cushion.strike}. then ${floor.strike}.`
          : `open air. ${pocket.lo} to ${pocket.hi} is empty. next stop ${floor.strike}.`)
      : `every strike below carries size. grind, not a drop.`,
    side: 1,
    pts: pocket
      ? [
          (() => {
            const shelfK = Math.min(pocket.hi + 1, Math.floor(spot));
            const lv = ladder.find((s) => s.strike === shelfK) || { netGex: 0, putOi: 0 };
            return lv.netGex >= 0
              ? { at: shelfK, tag: `${shelfK} LAST SHELF`, note: 'the last thing to lean on' }
              : { at: shelfK, tag: `${shelfK} TRAPDOOR`, note: `${oiFmt(lv.putOi)} puts, and dealers sell into it` };
          })(),
          cushion && cushion.strike < Math.min(pocket.hi + 1, Math.floor(spot))
            ? { at: cushion.strike, tag: `${cushion.strike} THIN CUSHION`, note: 'only dealer buying down here, and it is small', open: true }
            : { at: (pocket.lo + pocket.hi) / 2, tag: 'EMPTY', note: `${pocket.lo} to ${pocket.hi}, nothing here`, open: true },
          { at: floor.strike, tag: `${floor.strike} PUT WALL`, note: `${oiFmt(floor.putOi)} puts. the fight is here` },
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
push(`<text x="${PAD_L}" y="72" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · flip ${flip.toFixed(2)} · pin ${pin} · net GEX ${fmtM(gex.totalGEX)}${survivors ? ` · levels exclude the ${(expiringShare * 100).toFixed(0)}% of gamma expiring tonight` : ''}</text>`);
const pillC = negGamma ? C.coral : C.green;
push(`<rect x="${W - PAD_R - 330}" y="26" width="330" height="34" rx="17" fill="${negGamma ? '#1a0e11' : '#0c1a13'}" stroke="${pillC}" stroke-opacity="0.45"/>`);
push(`<text x="${W - PAD_R - 165}" y="48" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="14" fill="${pillC}">${negGamma ? 'NEGATIVE GAMMA / moves get amplified' : 'POSITIVE GAMMA / moves get damped'}</text>`);
push(`<text x="${W - PAD_R}" y="76" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}">as of ${new Date().toISOString().slice(0, 16).replace('T', ' ')}Z</text>`);

// plot frame + tomorrow tint
push(`<rect x="${PAD_L}" y="${PAD_T}" width="${PLOT_W}" height="${PLOT_H}" fill="${C.panel}" stroke="${C.line}"/>`);
push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${PLOT_H}" fill="#0c0c14"/>`);

// Which side of the flip you are on is the single most important fact on this
// half of the chart, so it gets colour rather than a line to read.
{
  const yf = Math.max(PAD_T, Math.min(PAD_T + PLOT_H, Y(flip)));
  push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${yf - PAD_T}" fill="${C.call}" fill-opacity="0.05"/>`);
  push(`<rect x="${FWD_X}" y="${yf}" width="${FWD_W}" height="${PAD_T + PLOT_H - yf}" fill="${C.put}" fill-opacity="0.055"/>`);
  push(`<text x="${W - PAD_R - 10}" y="${yf - 10}" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.call}" fill-opacity="0.75">ABOVE THE FLIP / dealers brake</text>`);
  push(`<text x="${W - PAD_R - 10}" y="${yf + 20}" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.put}" fill-opacity="0.75">BELOW THE FLIP / dealers chase</text>`);
}

// Everything outside a typical day's excursion is a tail. Drawing 772 as far
// from spot as 761 made a 4-point move look as ordinary as a 7-point one.
const emHi = spot + expected, emLo = spot - expected;
{
  const y1 = Math.max(PAD_T, Y(emHi)), y2 = Math.min(PAD_T + PLOT_H, Y(emLo));
  push(`<rect x="${FWD_X}" y="${PAD_T}" width="${FWD_W}" height="${y1 - PAD_T}" fill="${C.bg}" fill-opacity="0.5"/>`);
  push(`<rect x="${FWD_X}" y="${y2}" width="${FWD_W}" height="${PAD_T + PLOT_H - y2}" fill="${C.bg}" fill-opacity="0.5"/>`);
  for (const yy of [y1, y2]) {
    push(`<line x1="${FWD_X}" y1="${yy}" x2="${W - PAD_R}" y2="${yy}" stroke="${C.dim}" stroke-width="0.8" stroke-opacity="0.45" stroke-dasharray="6 6"/>`);
  }
  push(`<text x="${FWD_X + 10}" y="${y1 - 8}" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.dim}">beyond a typical day (+/- ${expected.toFixed(2)})</text>`);
}

// price rail
{
  const step = (yHi - yLo) > 18 ? 5 : 2;
  for (let v = Math.ceil(yLo / step) * step; v <= yHi; v += step) {
    push(`<line x1="${PAD_L}" y1="${Y(v)}" x2="${W - PAD_R}" y2="${Y(v)}" stroke="${C.line}" stroke-opacity="0.7"/>`);
    push(`<text x="${PAD_L - 8}" y="${Y(v) + 4}" text-anchor="end" font-family="'JetBrains Mono',monospace" font-size="10.5" fill="${C.dim}">${v}</text>`);
  }
}

// the drive so far, as candles
const BUCKET = [5, 10, 15, 30, 60].find((m) => PAST_W / (pts.length / m) >= 5) || 60;
const candles = buildCandles(BUCKET);
const cw = Math.max(2, (PAST_W / candles.length) * 0.66);
for (const k of candles) {
  const x = (X(k.i0) + X(k.i1)) / 2;
  const up = k.c >= k.o;
  const col = up ? C.call : C.put;
  push(`<line x1="${x.toFixed(1)}" y1="${Y(k.h).toFixed(1)}" x2="${x.toFixed(1)}" y2="${Y(k.l).toFixed(1)}" stroke="${col}" stroke-width="1" stroke-opacity="0.9"/>`);
  const yTop = Y(Math.max(k.o, k.c)), yBot = Y(Math.min(k.o, k.c));
  push(`<rect x="${(x - cw / 2).toFixed(1)}" y="${yTop.toFixed(1)}" width="${cw.toFixed(1)}" height="${Math.max(1, yBot - yTop).toFixed(1)}" fill="${col}" fill-opacity="${up ? 0.85 : 0.95}"/>`);
}
push(`<text x="${PAD_L + 8}" y="${PAD_T + 36}" font-family="'JetBrains Mono',monospace" font-size="9.5" fill="${C.dim}">${BUCKET}m candles</text>`);
sessions.forEach((d, k) => {
  const i = pts.findIndex((p) => dayKey(p.t) === d);
  push(`<text x="${X(i) + 5}" y="${PAD_T + PLOT_H - 8}" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.dim}">${d.slice(5)}</text>`);
  // The overnight gap is the map's biggest single risk and it used to be
  // invisible: just white space between two candles.
  if (k === 0) return;
  const prevPx = pts.filter((q) => dayKey(q.t) === sessions[k - 1]).map((q) => q.px);
  const g = pts[i].px - prevPx[prevPx.length - 1];
  if (Math.abs(g) < 0.4) return;
  const y1 = Y(prevPx[prevPx.length - 1]), y2 = Y(pts[i].px);
  push(`<line x1="${X(i)}" y1="${y1}" x2="${X(i)}" y2="${y2}" stroke="${C.pin}" stroke-width="2" stroke-opacity="0.55"/>`);
  push(`<text x="${X(i) + 5}" y="${(y1 + y2) / 2 + 3}" font-family="'JetBrains Mono',monospace" font-size="9.5" fill="${C.pin}" fill-opacity="0.85">gap ${g > 0 ? '+' : ''}${g.toFixed(2)}</text>`);
});
push(`<text x="${PAD_L + 8}" y="${PAD_T + 20}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}" letter-spacing="2">THE LAST ${sessions.length} SESSIONS</text>`);
// Last night's call, drawn back over the session it was made for. Green means
// the level did what the map said it would; red means it did not.
if (report) {
  const idxs = pts.map((q, i) => (dayKey(q.t) === report.day ? i : -1)).filter((i) => i >= 0);
  const x0 = X(idxs[0]), x1 = X(idxs[idxs.length - 1]);
  push(`<rect x="${x0}" y="${PAD_T}" width="${x1 - x0}" height="${PLOT_H}" fill="${C.text}" fill-opacity="0.025"/>`);
  push(`<text x="${x0 + 3}" y="${PAD_T + 38}" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.dim}" letter-spacing="1">${report.partial ? 'TODAY SO FAR' : 'LAST CALL'}</text>`);
  const byLvl = {
    [report.prev.cushion]: report.checks.find((c) => c.text.includes('cushion')),
    [report.prev.wall]: report.checks.find((c) => c.text.includes('put wall')),
    [report.prev.flip]: report.checks.find((c) => c.text.includes('flip')),
    [report.prev.battle]: report.checks.find((c) => c.text.includes('never tested')),
  };
  for (const lvl of report.levels) {
    const y = Y(lvl);
    if (y < PAD_T || y > PAD_T + PLOT_H) continue;
    const c = byLvl[lvl];
    const col = c ? (c.ok ? C.call : C.put) : C.dim;
    push(`<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${col}" stroke-width="1.2" stroke-opacity="${c ? 0.75 : 0.3}" stroke-dasharray="3 3"/>`);
  }
  // where it actually turned
  const loI = idxs.reduce((b, i) => (pts[i].px < pts[b].px ? i : b), idxs[0]);
  const hiI = idxs.reduce((b, i) => (pts[i].px > pts[b].px ? i : b), idxs[0]);
  for (const [i, px] of [[loI, report.low], [hiI, report.high]]) {
    push(`<circle cx="${X(i)}" cy="${Y(px)}" r="4" fill="${C.bg}" stroke="${C.text}" stroke-width="1.6"/>`);
    push(`<text x="${X(i)}" y="${Y(px) + (px === report.low ? 16 : -8)}" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="10" fill="${C.text}">${px.toFixed(2)}</text>`);
  }
}

push(`<line x1="${FWD_X}" y1="${PAD_T}" x2="${FWD_X}" y2="${PAD_T + PLOT_H}" stroke="${C.dim}" stroke-opacity="0.45" stroke-dasharray="3 4"/>`);
push(`<text x="${FWD_X + 12}" y="${PAD_T + 20}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}" letter-spacing="2">TOMORROW</text>`);
if (flipOnPrice) {
  push(`<rect x="${FWD_X + 12}" y="${PAD_T + 28}" width="430" height="24" rx="5" fill="${C.pin}" fill-opacity="0.12" stroke="${C.pin}" stroke-opacity="0.4"/>`);
  push(`<text x="${FWD_X + 22}" y="${PAD_T + 45}" font-family="'JetBrains Mono',monospace" font-size="11.5" fill="${C.pin}">THE FLIP IS SITTING ON PRICE. it has no information today.</text>`);
}

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

const labels = [];
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
      const px = pin + Math.sin(f * Math.PI * 2 * cycles) * ((rangeHi - rangeLo) / 2) * 0.5;
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
      const reach = w.at <= emHi && w.at >= emLo;
      push(`<circle cx="${x}" cy="${y}" r="5.5" fill="${C.bg}" stroke="${r.col}" stroke-width="2.4" stroke-opacity="${reach ? 1 : 0.4}"/>`);
    }
    // The road arrives from the lower/upper left and leaves to the right, so the
    // only reliably empty quadrant is back over the shoulder. Last stop is the
    // exception: nothing follows it, so its label can sit out front.
    const last = i === n - 1;
    labels.push({
      x, y,
      tx: last ? x + 12 : x - 12,
      anchor: last ? 'start' : 'end',
      ty: y + (r.labelBelow ? 30 : r.side < 0 ? -28 : 24),
      tag: w.tag, note: w.note, col: r.col,
      faint: !(w.at <= emHi && w.at >= emLo),
    });
  });

  // road name at the far end
  const endY = r.wave ? Y(pin) : Y(r.pts[n - 1].at);
  push(`<text x="${ROAD_X0 + ROAD_W + 12}" y="${endY + 4}" font-family="'Share Tech Mono',monospace" font-size="15" fill="${r.col}" letter-spacing="1">${r.key}</text>`);
}

// Waypoint labels are placed last, as one pass, so labels from different roads
// cannot land on top of each other. When a label has to move off its dot, a
// leader line keeps the two connected.
labels.sort((a, b) => a.ty - b.ty);
const LBL_H = 34;
let lastTy = -Infinity;
for (const L of labels) {
  if (L.ty - lastTy < LBL_H) L.ty = lastTy + LBL_H;
  lastTy = L.ty;
}
for (const L of labels) {
  if (Math.abs(L.ty - (L.y + 24)) > 26 || Math.abs(L.ty - L.y) > 40) {
    push(`<line x1="${L.x}" y1="${L.y}" x2="${L.tx}" y2="${(L.ty - 4).toFixed(1)}" stroke="${L.col}" stroke-width="0.8" stroke-opacity="0.35"/>`);
  }
  const op = L.faint ? 0.42 : 1;
  push(`<text x="${L.tx}" y="${L.ty.toFixed(1)}" text-anchor="${L.anchor}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${L.col}" fill-opacity="${op}" font-weight="700">${esc(L.tag)}${L.faint ? ' *' : ''}</text>`);
  push(`<text x="${L.tx}" y="${(L.ty + 15).toFixed(1)}" text-anchor="${L.anchor}" font-family="'JetBrains Mono',monospace" font-size="11" fill="${C.dim}" fill-opacity="${op}">${esc(L.note)}</text>`);
}

// ── how the last one went ───────────────────────────────────────────────────
let SCORE_H = 0;
if (report) {
  const y = PAD_T + PLOT_H + 34;
  SCORE_H = 46;
  const allHit = report.hits === report.total;
  const col = report.partial ? C.cyan : allHit ? C.call : report.hits >= report.total / 2 ? C.pin : C.put;
  push(`<rect x="${PAD_L}" y="${y - 20}" width="${PLOT_W}" height="34" rx="6" fill="${col}" fill-opacity="0.07" stroke="${col}" stroke-opacity="0.25"/>`);
  push(`<text x="${PAD_L + 16}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${col}" font-weight="700">${report.partial ? 'IN FLIGHT' : 'LAST CALL'}</text>`);
  push(`<text x="${PAD_L + 130}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.text}">${report.partial ? `${report.day.slice(5)} still open` : `${report.hits}/${report.total} on ${report.day.slice(5)}`}</text>`);
  push(`<text x="${PAD_L + 290}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">${esc(report.checks.map((c) => (c.ok ? c.text : `MISS ${c.text}`)).join(' · '))}</text>`);
}

// ── the if / else ───────────────────────────────────────────────────────────
const IF_T = PAD_T + PLOT_H + 40 + SCORE_H;
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

// Write this map down so the next run can grade it.
const entry = {
  madeAfter: sessions[sessions.length - 1],
  asOf: new Date().toISOString(),
  spot, flip, pin: magnet,
  battle: battle ? battle.strike : null,
  brake: brake ? brake.strike : null,
  gate: gate ? gate.strike : null,
  shelf: pocket ? pocket.hi + 1 : null,
  cushion: cushion ? cushion.strike : null,
  wall: floor ? floor.strike : null,
};
if (sessionClosed) {
  const kept = ledger.filter((e) => e.madeAfter !== entry.madeAfter);
  kept.push(entry);
  kept.sort((a, b) => a.madeAfter.localeCompare(b.madeAfter));
  mkdirSync(dirname(LEDGER), { recursive: true });
  writeFileSync(LEDGER, JSON.stringify(kept.slice(-120), null, 2) + '\n');
} else {
  console.log('session still open: not writing to the ledger, and the score below is provisional');
}

if (report) console.log(`${report.partial ? 'in flight' : 'last call'}: ${report.hits}/${report.total} on ${report.day} | ` + report.checks.map((c) => `${c.ok ? 'HIT' : 'MISS'} ${c.text}`).join(' | '));
console.log(`spot ${spot} | flip ${flip} | magnet ${magnet} | netGEX ${fmtM(gex.totalGEX)}`);
console.log(`gate ${gate?.strike} | brake ${brake?.strike} | battle ${battle?.strike} | floor ${floor?.strike} | pocket ${pocket ? `${pocket.lo}-${pocket.hi}` : 'none'}`);
console.log(png);
