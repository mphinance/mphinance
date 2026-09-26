#!/usr/bin/env node
// wheel_campaign_chart.mjs — plot a whole wheel campaign on one chart.
//
// Candles from TD Pro, with every fill of the campaign drawn on top: share buys,
// share trims, calls written, assignments. The strike line runs across the whole
// window because on a wheel the strike, not the price, is the story.
//
// Usage:
//   node wheel_campaign_chart.mjs --events events.json --out /tmp/btg.png
//
// events.json: { symbol, from, strike, basis, events:[{date,type,qty,price,label}] }
//   type: buy | sell | call | put | assign

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { homedir } from 'os';

const PW = join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs');
const { chromium } = await import(existsSync(PW) ? PW : 'playwright');

const AGENT = 'https://traderdaddy-pro-whop-production.up.railway.app';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36';

const C = {
  bg: '#0a0a0e', line: '#1a1a24', text: '#f0ece2', dim: '#8a8394',
  up: '#f5b93a', down: '#a3535f', wick: '#7d7590',
  gold: '#ffc44d', goldDim: '#8a6b1f', strike: '#ffb000',
  buy: '#00d68f', sell: '#ff6b81', assign: '#c084fc', basis: '#5d8aa8',
};

function repoRoot(start) {
  let d = resolve(start);
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(d, '.env_agent_api'))) return d;
    const up = dirname(d);
    if (up === d) break;
    d = up;
  }
  return process.cwd();
}
const ROOT = repoRoot(process.cwd());
const KEY = readFileSync(join(ROOT, '.env_agent_api'), 'utf8').trim();

function arg(n, d) { const i = process.argv.indexOf('--' + n); return i > -1 ? process.argv[i + 1] : d; }

const spec = JSON.parse(readFileSync(resolve(arg('events')), 'utf8'));
const OUT = resolve(arg('out', '/tmp/wheel_campaign.png'));

const r = await fetch(`${AGENT}/api/agent/ticker/${spec.symbol}/chart-data?days=${arg('days', 260)}`, {
  headers: { Authorization: `Bearer ${KEY}`, 'User-Agent': UA },
});
if (!r.ok) throw new Error(`chart-data ${r.status}`);
const meta = await r.json();
const candles = meta.chartData.filter((c) => c.date >= spec.from);

const W = 1680, H = 940;
const PAD_L = 74, PAD_R = 108, PAD_T = 104, PAD_B = 118;
const PW_ = W - PAD_L - PAD_R, PH_ = H - PAD_T - PAD_B;

const n = candles.length;
const idx = new Map(candles.map((c, i) => [c.date, i]));
const levels = [spec.strike, spec.basis].filter(Boolean);
const lo = Math.min(...candles.map((c) => c.low), ...levels) * 0.965;
const hi = Math.max(...candles.map((c) => c.high), ...levels) * 1.035;
const y = (p) => PAD_T + PH_ - ((p - lo) / (hi - lo)) * PH_;
const x = (i) => PAD_L + (i + 0.5) * (PW_ / n);
const cw = Math.max(3, (PW_ / n) * 0.62);
const f2 = (v) => Number(v).toFixed(2);
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const o = [];
const p = (s) => o.push(s);

// grid
for (let g = 0; g <= 6; g++) {
  const price = lo + ((hi - lo) * g) / 6;
  const yy = y(price);
  p(`<line x1="${PAD_L}" y1="${yy}" x2="${PAD_L + PW_}" y2="${yy}" stroke="${C.line}"/>`);
  p(`<text x="${PAD_L + PW_ + 14}" y="${yy + 4}" fill="${C.dim}" font-size="13">$${f2(price)}</text>`);
}

// strike band — the whole point of a wheel
if (spec.strike) {
  const ys = y(spec.strike);
  p(`<rect x="${PAD_L}" y="${ys - 1.5}" width="${PW_}" height="3" fill="${C.strike}" opacity="0.9"/>`);
  p(`<rect x="${PAD_L}" y="${PAD_T}" width="${PW_}" height="${ys - PAD_T}" fill="${C.strike}" opacity="0.045"/>`);
  // park the label wherever the tape is furthest below the line, so it never fights a candle
  const sx = PAD_L + PW_ * (spec.strikeLabelAt ?? 0.62);
  p(`<rect x="${sx - 100}" y="${ys + 9}" width="200" height="21" rx="3" fill="${C.bg}" opacity="0.88"/>`);
  p(`<text x="${sx}" y="${ys + 24}" fill="${C.strike}" font-size="13.5" font-weight="700" letter-spacing="1.5" text-anchor="middle">${esc(spec.strikeLabel || `THE $${f2(spec.strike)} STRIKE`)}</text>`);
}
if (spec.basis) {
  const yb = y(spec.basis);
  p(`<line x1="${PAD_L}" y1="${yb}" x2="${PAD_L + PW_}" y2="${yb}" stroke="${C.basis}" stroke-width="1.6" stroke-dasharray="8 6" opacity="0.85"/>`);
  const bx = PAD_L + 10 + PW_ * (spec.basisLabelAt ?? 0);
  p(`<text x="${bx}" y="${yb + 18}" fill="${C.basis}" font-size="13">${esc(spec.basisLabel || `AVG BASIS $${f2(spec.basis)}`)}</text>`);
}

// candles
for (let i = 0; i < n; i++) {
  const c = candles[i];
  const up = c.close >= c.open;
  const col = up ? C.up : C.down;
  p(`<line x1="${x(i)}" y1="${y(c.high)}" x2="${x(i)}" y2="${y(c.low)}" stroke="${up ? C.up : C.wick}" stroke-width="1.2" opacity="0.8"/>`);
  const yo = y(c.open), yc = y(c.close);
  p(`<rect x="${x(i) - cw / 2}" y="${Math.min(yo, yc)}" width="${cw}" height="${Math.max(1.4, Math.abs(yc - yo))}" fill="${col}" opacity="${up ? 0.95 : 0.9}"/>`);
}

// last price tag
const lastC = candles[n - 1];
p(`<line x1="${PAD_L}" y1="${y(lastC.close)}" x2="${PAD_L + PW_}" y2="${y(lastC.close)}" stroke="${C.text}" stroke-dasharray="3 5" opacity="0.5"/>`);
p(`<rect x="${PAD_L + PW_ + 4}" y="${y(lastC.close) - 12}" width="${PAD_R - 16}" height="24" rx="3" fill="${C.gold}"/>`);
p(`<text x="${PAD_L + PW_ + 14}" y="${y(lastC.close) + 5}" fill="#0a0a0e" font-size="14" font-weight="700">$${f2(lastC.close)}</text>`);

// events
const placed = [];
function slot(px_, py_, w, dir) {
  let ty = py_, tx = Math.max(PAD_L + 2, Math.min(px_, PAD_L + PW_ - w - 2));
  for (let g = 0; g < 24; g++) {
    const hit = placed.find((q) => Math.abs(q.y - ty) < 16 && tx < q.x + q.w + 8 && tx + w > q.x - 8);
    if (!hit) break;
    ty += dir * 19;
  }
  placed.push({ x: tx, y: ty, w });
  return [tx, ty];
}

const byType = { buy: C.buy, sell: C.sell, call: C.strike, put: C.strike, assign: C.assign };
for (const e of spec.events) {
  let i = idx.get(e.date);
  if (i === undefined) { // nearest prior trading day
    const before = candles.filter((c) => c.date <= e.date);
    if (!before.length) continue;
    i = idx.get(before[before.length - 1].date);
  }
  const c = candles[i];
  const col = byType[e.type] || C.dim;
  const px_ = x(i);

  if (e.type === 'buy') {
    const s = 5 + Math.min(9, Math.sqrt(e.qty) * 1.35);
    const yy = y(c.low) + 13;
    p(`<path d="M ${px_} ${yy - s} L ${px_ - s} ${yy + s * 0.75} L ${px_ + s} ${yy + s * 0.75} Z" fill="${col}" opacity="0.95"/>`);
  } else if (e.type === 'sell') {
    const s = 5 + Math.min(9, Math.sqrt(e.qty) * 1.35);
    const yy = y(c.high) - 13;
    p(`<path d="M ${px_} ${yy + s} L ${px_ - s} ${yy - s * 0.75} L ${px_ + s} ${yy - s * 0.75} Z" fill="${col}" opacity="0.95"/>`);
  } else if (e.type === 'call' || e.type === 'put') {
    const yy = y(spec.strike);
    p(`<circle cx="${px_}" cy="${yy}" r="8.5" fill="${C.bg}" stroke="${col}" stroke-width="2.4"/>`);
    p(`<text x="${px_}" y="${yy + 4.5}" fill="${col}" font-size="11" font-weight="700" text-anchor="middle">${e.type === 'call' ? 'C' : 'P'}</text>`);
  } else if (e.type === 'assign') {
    const yy = y(spec.strike);
    p(`<circle cx="${px_}" cy="${yy}" r="12" fill="${C.assign}" opacity="0.22"/>`);
    p(`<path d="M ${px_ - 7} ${yy - 7} L ${px_ + 7} ${yy + 7} M ${px_ + 7} ${yy - 7} L ${px_ - 7} ${yy + 7}" stroke="${C.assign}" stroke-width="2.8" stroke-linecap="round"/>`);
  }

  if (e.label) {
    const w = e.label.length * 6.7 + 16;
    const down = e.type === 'buy';
    const anchorY = down ? y(c.low) + 36 : e.type === 'sell' ? y(c.high) - 32 : y(spec.strike) - 30;
    const [tx, ty] = slot(px_ - w / 2, anchorY, w, down ? 1 : -1);
    p(`<line x1="${px_}" y1="${down ? y(c.low) + 20 : e.type === 'sell' ? y(c.high) - 18 : y(spec.strike) - 12}" x2="${tx + w / 2}" y2="${ty - 4}" stroke="${col}" stroke-width="1" opacity="0.45"/>`);
    p(`<rect x="${tx}" y="${ty - 12}" width="${w}" height="17" rx="3" fill="${C.bg}" stroke="${col}" stroke-opacity="0.55"/>`);
    p(`<text x="${tx + w / 2}" y="${ty}" fill="${col}" font-size="11.5" text-anchor="middle">${esc(e.label)}</text>`);
  }
}

// x axis
const step = Math.max(1, Math.floor(n / 10));
for (let i = 0; i < n; i += step) {
  const d = new Date(candles[i].date + 'T00:00:00');
  p(`<line x1="${x(i)}" y1="${PAD_T}" x2="${x(i)}" y2="${PAD_T + PH_}" stroke="${C.line}" stroke-dasharray="2 9"/>`);
  p(`<text x="${x(i)}" y="${PAD_T + PH_ + 26}" fill="${C.dim}" font-size="12.5" text-anchor="middle">${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</text>`);
}

// header
p(`<text x="${PAD_L}" y="46" fill="${C.gold}" font-size="34" font-family="Share Tech Mono, monospace" letter-spacing="2">${esc(spec.symbol)}</text>`);
p(`<text x="${PAD_L + 118}" y="46" fill="${C.text}" font-size="26">$${f2(lastC.close)}</text>`);
p(`<text x="${PAD_L}" y="74" fill="${C.dim}" font-size="14.5">${esc(spec.title || '')}</text>`);

// legend
const leg = spec.legend
  ? spec.legend.map(([t, k]) => [t, byType[k] || C.dim])
  : [['share buy', C.buy], ['share trim', C.sell], ['option sold', C.strike], ['called away', C.assign]];
leg.forEach(([t, col], i) => {
  const lx = PAD_L + PW_ - 545 + i * 140;
  p(`<circle cx="${lx}" cy="${40}" r="5.5" fill="${col}"/>`);
  p(`<text x="${lx + 13}" y="${44.5}" fill="${C.dim}" font-size="12.5">${t}</text>`);
});

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs><linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#12100c"/><stop offset="100%" stop-color="#08080b"/></linearGradient></defs>
<rect width="${W}" height="${H}" fill="url(#bgg)"/>
<g font-family="JetBrains Mono, ui-monospace, monospace">${o.join('\n')}</g>
<text x="${PAD_L}" y="${H - 22}" fill="#524a3a" font-size="11.5">${esc(spec.footer || '')}</text>
</svg>`;

mkdirSync(dirname(OUT), { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
await page.setContent(
  `<html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap">
   <style>html,body{margin:0;background:${C.bg}}</style></head><body>${svg}</body></html>`,
  { waitUntil: 'networkidle' },
);
await page.screenshot({ path: OUT });
await browser.close();
console.log(OUT);
