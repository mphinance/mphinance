#!/usr/bin/env node
// Draw a ticker's real close line on top of AI-generated "chart as landscape" art,
// using the exact same x/y mapping the silhouette reference image used. Lets you see
// how faithfully the artwork traced the tape.
//
//   node tools/art_chart_overlay.mjs --art hero.png --candles c.json --from 2026-02-17 \
//        --out out.png [--strike 5] [--caption "..."] [--mode line|ghost|carve] [--stroke #e4e2dd] [--dim 0.14]

import { readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

const arg = (k, d) => {
  const i = process.argv.indexOf('--' + k);
  return i > -1 ? process.argv[i + 1] : d;
};

const artPath = arg('art');
const out = arg('out');
const from = arg('from');
const strike = arg('strike') ? parseFloat(arg('strike')) : null;
const caption = arg('caption', '');
const mode = arg('mode', 'line');
const stroke = arg('stroke', '#e4e2dd');
const dim = parseFloat(arg('dim', '0.14'));

const raw = JSON.parse(readFileSync(arg('candles'), 'utf8'));
const all = raw.chartData || raw.candles || raw;
const rows = all.filter((r) => !from || r.date >= from);

const W = 1376, H = 768;
// Silhouette geometry: the fill sat between these y values in a 700px canvas.
const Y_TOP = (47.7 / 700) * H, Y_BOT = (662.9 / 700) * H;

const closes = rows.map((r) => r.close);
const hi = Math.max(...closes), lo = Math.min(...closes);
const x = (i) => (i / (rows.length - 1)) * W;
const y = (p) => Y_TOP + ((hi - p) / (hi - lo)) * (Y_BOT - Y_TOP);

const pts = closes.map((c, i) => [x(i), y(c)]);
const d = pts.map(([a, b], i) => `${i ? 'L' : 'M'} ${a.toFixed(1)},${b.toFixed(1)}`).join(' ');

const b64 = readFileSync(artPath).toString('base64');
const fmt = (v) => '$' + v.toFixed(2);

const label = (px, py, text, fill, anchor = 'end') => `
  <rect x="${anchor === 'end' ? px - 62 : px}" y="${py - 12}" width="62" height="20" rx="3" fill="#000" opacity="0.55"/>
  <text x="${anchor === 'end' ? px - 8 : px + 8}" y="${py + 3}" fill="${fill}" font-size="13" font-weight="700"
        text-anchor="${anchor === 'end' ? 'end' : 'start'}" font-family="'JetBrains Mono',monospace">${text}</text>`;

// carve: no line drawn on top. Instead the painted rock is CLIPPED to the real price
// path, so the skyline literally is the tape. Sky comes from the art's own sky band,
// rock texture from its lower band, both stretched to frame.
const carve = () => {
  const back = pts.map(([a, b], i) => `${i ? 'L' : 'M'} ${(a * 0.985 + W * 0.012).toFixed(1)},${(b * 0.86 + H * 0.10).toFixed(1)}`).join(' ');
  const crop = (id, vb) => `<clipPath id="${id}"><path d="${id === 'ridge' ? d : back} L ${W},${H} L 0,${H} Z"/></clipPath>`;
  void crop;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
  <clipPath id="ridge"><path d="${d} L ${W},${H} L 0,${H} Z"/></clipPath>
  <clipPath id="ridgeBack"><path d="${back} L ${W},${H} L 0,${H} Z"/></clipPath>
  <filter id="rim" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="depth" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#050408" stop-opacity="0.72"/>
  </linearGradient>
  <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#000" stop-opacity="0.35"/>
    <stop offset="55%" stop-color="#000" stop-opacity="0"/>
  </linearGradient>
</defs>

<!-- sky: the art's own sky band, stretched -->
<svg x="0" y="0" width="${W}" height="${H}" viewBox="0 30 ${W} 300" preserveAspectRatio="none">
  <image href="data:image/png;base64,${b64}" x="0" y="0" width="${W}" height="${H}"/>
</svg>
<rect width="${W}" height="${H}" fill="url(#haze)"/>

<!-- far ridge: same tape, lifted and flattened, for depth -->
<g clip-path="url(#ridgeBack)">
  <svg x="0" y="0" width="${W}" height="${H}" viewBox="0 330 ${W} 430" preserveAspectRatio="none">
    <image href="data:image/png;base64,${b64}" x="0" y="0" width="${W}" height="${H}"/>
  </svg>
  <rect width="${W}" height="${H}" fill="#1a1206" opacity="0.55"/>
</g>
<path d="${back}" fill="none" stroke="#ffd27a" stroke-width="1.6" opacity="0.35" filter="url(#rim)"/>

<!-- near ridge: exact close-to-close path, filled with painted rock -->
<g clip-path="url(#ridge)">
  <svg x="0" y="0" width="${W}" height="${H}" viewBox="0 300 ${W} 468" preserveAspectRatio="none">
    <image href="data:image/png;base64,${b64}" x="0" y="0" width="${W}" height="${H}"/>
  </svg>
  <rect width="${W}" height="${H}" fill="url(#depth)"/>
</g>
<path d="${d}" fill="none" stroke="#ffcf6b" stroke-width="2.4" stroke-linejoin="round" opacity="0.9" filter="url(#rim)"/>

${strike ? `
<line x1="0" y1="${y(strike)}" x2="${W}" y2="${y(strike)}" stroke="#fff0c9" stroke-width="1.3" stroke-dasharray="10 8" opacity="0.5"/>
${label(W - 16, y(strike), fmt(strike) + ' K', '#ffe6a8')}` : ''}

${caption ? `<rect x="0" y="${H - 44}" width="${W}" height="44" fill="#000" opacity="0.55"/>
<text x="22" y="${H - 17}" fill="#f0ece2" font-size="15" letter-spacing="1.6"
      font-family="'JetBrains Mono',monospace">${caption}</text>
<text x="${W - 22}" y="${H - 17}" fill="#8a8394" font-size="13" letter-spacing="1.4" text-anchor="end"
      font-family="'JetBrains Mono',monospace">THE SKYLINE IS THE TAPE</text>` : ''}
</svg>`;
};

const svg = mode === 'carve' ? carve() : `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="fillg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="${stroke}" stop-opacity="0.14"/>
    <stop offset="100%" stop-color="${stroke}" stop-opacity="0"/>
  </linearGradient>
</defs>
<image href="data:image/png;base64,${b64}" x="0" y="0" width="${W}" height="${H}"/>
<rect width="${W}" height="${H}" fill="#000" opacity="${mode === 'ghost' ? 0.55 : dim}"/>

${strike ? `
<line x1="0" y1="${y(strike)}" x2="${W}" y2="${y(strike)}" stroke="#ffc44d" stroke-width="1.4" stroke-dasharray="9 7" opacity="0.6"/>
${label(W - 16, y(strike), fmt(strike) + ' K', '#ffc44d')}` : ''}

<path d="${d} L ${W},${H} L 0,${H} Z" fill="url(#fillg)"/>
<path d="${d}" fill="none" stroke="#000" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" opacity="0.35"/>
<path d="${d}" fill="none" stroke="${stroke}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity="0.92"/>

${label(W - 16, y(hi) - 2, fmt(hi), stroke)}
${label(W - 16, Math.min(y(lo) + 2, H - 62), fmt(lo), stroke)}
<circle cx="${Math.min(x(rows.length - 1), W - 7)}" cy="${y(closes[closes.length - 1])}" r="4.5" fill="${stroke}"/>

<rect x="0" y="${H - 44}" width="${W}" height="44" fill="#000" opacity="0.62"/>
<text x="22" y="${H - 17}" fill="#f0ece2" font-size="15" letter-spacing="1.6"
      font-family="'JetBrains Mono',monospace">${caption}</text>
<text x="${W - 22}" y="${H - 17}" fill="#8a8394" font-size="13" letter-spacing="1.4" text-anchor="end"
      font-family="'JetBrains Mono',monospace">ACTUAL DAILY CLOSES</text>
</svg>`;

const { chromium } = await import(join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs'));
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
await p.screenshot({ path: out });
await b.close();
console.log('wrote', out, `${rows.length} closes, ${rows[0].date} → ${rows[rows.length - 1].date}, ${fmt(lo)}–${fmt(hi)}`);
