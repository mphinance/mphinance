#!/usr/bin/env node
// Ticker Search's right rail, beside a Next-6-Weeks chart, in one image.
//
//   node tools/gamma_horizon.mjs HIMS --out /tmp/gh --bars 130 --wedge
//   node tools/ticker_rail.mjs HIMS --chart /tmp/gh/hims_horizon_2026-10-31.png --ivrank 48.8 --out /tmp/gh
//
// Cards follow the 10/25 Ticker Search order: technicals (entry chips above the
// gauge), top flows, apex levels, dealer gamma, then the plain IV read. If the
// chart's JSON sidecar carries a wedge, a wedge card goes on top.
// --ivrank comes from the TDPro MCP (get_iv_rank); the dev API has no route for it.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { homedir } from 'node:os';

const PW_HOME = join(homedir(), '.claude/skills/mph-figure/node_modules/playwright/index.mjs');
const { chromium } = await import(existsSync(PW_HOME) ? PW_HOME : 'playwright');

const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const sym = (argv[0] && !argv[0].startsWith('--') ? argv[0] : '').toUpperCase();
if (!sym) { console.error('usage: ticker_rail.mjs SYM --chart PNG [--ivrank N] [--out DIR]'); process.exit(1); }
const chart = arg('chart'), OUT = arg('out', '/tmp/gh'), ivRank = arg('ivrank') != null ? Number(arg('ivrank')) : null;

const ROOT = (() => { let d = resolve(process.cwd()); for (let i = 0; i < 8; i++) { if (existsSync(join(d, '.env_td_api'))) return d; d = dirname(d); } return process.cwd(); })();
const KEY = readFileSync(join(ROOT, '.env_td_api'), 'utf8').trim();
const AGENT = readFileSync(join(ROOT, '.env_agent_api'), 'utf8').trim();
const UA = 'Mozilla/5.0 (X11; Linux x86_64)';
const dev = (p) => fetch(`https://api.traderdaddy.pro/api/v1${p}`, { headers: { 'X-API-Key': KEY, 'User-Agent': UA } }).then((r) => r.json());
const agent = (p) => fetch(`https://traderdaddy-pro-whop-production.up.railway.app${p}`, { headers: { Authorization: `Bearer ${AGENT}`, 'User-Agent': UA } }).then((r) => r.json());

const [tk, flow, gexR, apexR] = await Promise.all([
  agent(`/api/agent/ticker/${sym}`),
  dev(`/unusual-activity?ticker=${sym}&timeFrame=week&pageSize=100`),
  dev(`/gex/${sym}`),
  dev(`/gex/${sym}/apex`),
]);
const t = tk.technicals, o = tk.options, gex = gexR.data, apex = apexR.data;
const side = chart && existsSync(chart.replace(/\.png$/, '.json')) ? JSON.parse(readFileSync(chart.replace(/\.png$/, '.json'), 'utf8')) : null;
const wedge = side?.wedge ?? null;

const C = { bg: '#0a0a0e', panel: '#101018', line: '#1f1f2e', text: '#e6e6ee', dim: '#8a8aa0', call: '#00d68f', put: '#ff4d6d', flip: '#a855f7', pin: '#ffb000', wedge: '#ff9f1c', kc: '#2dd4bf' };
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const $ = (v, d = 2) => (v == null ? '-' : `$${Number(v).toFixed(d)}`);
const money = (v) => (Math.abs(v) >= 1e6 ? `$${(v / 1e6).toFixed(2)}M` : `$${Math.round(v / 1e3)}K`);
const md = (iso) => iso.slice(5, 10).replace('-', '/');

// ── technicals: the same kind of entry chips Ticker Search puts above the gauge
const spot = tk.price;
const chips = [];
chips.push(t.keltnerState === 'inside'
  ? [`Inside Keltner (${$(t.keltnerLower)}–${$(t.keltnerUpper)})`, t.emaStack === 'bullish' ? C.call : C.dim]
  : [`Keltner ${t.keltnerState}`, C.pin]);
chips.push([`EMA stack ${t.emaStack}`, t.emaStack === 'bullish' ? C.call : t.emaStack === 'bearish' ? C.put : C.dim]);
if (t.squeezeRatio != null && t.squeezeRatio < 1) chips.push([`Squeeze on (${t.squeezeRatio.toFixed(2)}): coiled`, C.pin]);
if (t.adx < 20) chips.push([`ADX ${t.adx.toFixed(1)} · no trend`, C.dim]);
if (tk.earnings?.daysUntil != null) chips.push([`Earnings ${md(tk.earnings.date)} ${tk.earnings.reportTime} · ${tk.earnings.daysUntil}d`, C.put]);
const chipHtml = chips.map(([s, c]) => `<span class="chip" style="color:${c};border-color:${c}55">${esc(s)}</span>`).join('');

// Gauge: a plain composite of the oscillators the TA card shows, -1 sell … +1 buy.
const vote = {
  RSI: t.rsi > 55 ? 1 : t.rsi < 45 ? -1 : 0,
  MACD: t.macd > 0 ? 1 : -1,
  Stoch: t.stochK > 80 ? -1 : t.stochK < 20 ? 1 : t.stochK > 50 ? 1 : -1,
  CCI: t.cci > 100 ? 1 : t.cci < -100 ? -1 : 0,
  '21 EMA': spot > t.ema21 ? 1 : -1, '50 SMA': spot > t.sma50 ? 1 : -1, '200 SMA': spot > t.sma200 ? 1 : -1,
};
const votes = Object.values(vote);
const vCol = (k) => (vote[k] == null ? C.text : vote[k] > 0 ? C.call : vote[k] < 0 ? C.put : C.dim);
const g = votes.reduce((a, v) => a + v, 0) / votes.length;
// Our own vote count, not TraderMatrix's gauge, so it says what it counted.
const nBull = votes.filter((v) => v > 0).length, nBear = votes.filter((v) => v < 0).length;
const gLabel = g > 0.15 ? `${nBull} of ${votes.length} lean bullish` : g < -0.15 ? `${nBear} of ${votes.length} lean bearish` : 'Mixed';
const gCol = g > 0.15 ? C.call : g < -0.15 ? C.put : C.dim;
const ang = Math.PI * (1 - (g + 1) / 2);
const gauge = `<svg width="200" height="112" viewBox="0 0 200 112">
  <defs><linearGradient id="gg" x1="0" x2="1"><stop offset="0" stop-color="${C.put}"/><stop offset=".5" stop-color="#555"/><stop offset="1" stop-color="${C.call}"/></linearGradient></defs>
  <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="url(#gg)" stroke-width="12" stroke-linecap="round" opacity=".85"/>
  <line x1="100" y1="100" x2="${100 + 66 * Math.cos(ang)}" y2="${100 - 66 * Math.sin(ang)}" stroke="${C.text}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="100" cy="100" r="6" fill="${C.text}"/></svg>`;
const stats = [['RSI', t.rsi.toFixed(1)], ['ADX', t.adx.toFixed(1)], ['Stoch', t.stochK.toFixed(0)], ['MACD', t.macd.toFixed(2)], ['CCI', t.cci.toFixed(0)], ['ATR', t.atr.toFixed(2)], ['21 EMA', $(t.ema21)], ['50 SMA', $(t.sma50)], ['200 SMA', $(t.sma200)]];

// ── top flows: the week's biggest prints, premium-ranked
const prints = (flow.data || []).filter((r) => r.ticker === sym).sort((a, b) => b.premium - a.premium).slice(0, 5);
const et = (iso) => new Date(iso).toLocaleString('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: '2-digit' });
const flowRows = prints.map((r) => {
  const bull = /bull/i.test(r.sentiment), col = bull ? C.call : C.put;
  const act = /open/i.test(r.sentimentAction || '') ? 'Opened' : /clos/i.test(r.sentimentAction || '') ? 'Closed' : 'Traded';
  const contract = r.isRedacted || r.strike == null ? r.type : `${r.strike}${r.type[0]} ${r.expiry ? md(r.expiry) : ''}`;
  return `<div class="row"><span class="tag" style="background:${col}22;color:${col}">${bull ? 'BULL' : 'BEAR'}</span><span class="w">${esc(contract)} · ${act}</span><span class="r">${money(r.premium)}</span><span class="sub">${et(r.tradeTime)} ET · score ${r.score}</span></div>`;
}).join('') || '<div class="dimline">No unusual prints this week.</div>';
const bullP = prints.filter((r) => /bull/i.test(r.sentiment)).reduce((a, r) => a + r.premium, 0);
const bearP = prints.filter((r) => /bear/i.test(r.sentiment)).reduce((a, r) => a + r.premium, 0);

// ── apex ladder: strikes high to low, bar = score, colour = gamma sign
const lv = [...apex.levels].sort((a, b) => b.strike - a.strike);
let spotDrawn = false;
const ladder = lv.map((l) => {
  let pre = '';
  if (!spotDrawn && l.strike < spot) { spotDrawn = true; pre = `<div class="spotline"><span>${sym} ${$(spot)}</span></div>`; }
  const col = l.netGEX >= 0 ? C.call : C.put;
  return `${pre}<div class="lad"><span class="k">${l.strike}</span><span class="bar t${l.score >= 80 ? 3 : l.score >= 50 ? 2 : 1}"><i style="width:${l.score}%;background:${col}"></i></span><span class="s">${l.score}</span><span class="oi">${(l.totalOI / 1000).toFixed(1)}K OI</span></div>`;
}).join('');

// ── IV: plain read first, numbers under it
const ivVerdict = ivRank == null ? null : ivRank >= 60 ? ['expensive', C.put, 'favors selling premium'] : ivRank <= 30 ? ['cheap', C.call, 'favors buying premium'] : ['fairly priced', C.text, 'no vol edge either way'];
const em = o.expectedMove;
const emEarn = tk.earnings && tk.earnings.date <= tk.expiration;

const neg = gex.totalGEX < 0;
const card = (title, body, accent = C.line) => `<section style="border-color:${accent}"><h3>${title}</h3>${body}</section>`;

const wedgeCard = wedge ? card('WEDGE', `
  <div class="kv"><span>Lid today</span><b style="color:${C.wedge}">${$(wedge.lid)}</b></div>
  <div class="kv"><span>Floor today</span><b style="color:${C.wedge}">${$(wedge.floor)}</b></div>
  <div class="kv"><span>Apex</span><b>~${wedge.apexDate} @ ${$(wedge.apexPx)}</b></div>
  <div class="note">Lid ≈ the ${o.callWall} call wall, floor sits just over the ${o.putWall} put wall.${tk.earnings ? ` Earnings ${md(tk.earnings.date)} land inside the coil.` : ''}</div>`, C.wedge) : '';

const rail = `
<div class="hero"><div class="sym">${sym}</div><div class="px">${$(spot)} <span style="color:${t.changePercent >= 0 ? C.call : C.put}">${t.changePercent >= 0 ? '+' : ''}${t.changePercent.toFixed(2)}%</span></div>
<div class="sub2">rel vol ${t.relVol.toFixed(2)} · 90d ${$(t.low90d)}–${$(t.high90d)}</div></div>
${wedgeCard}
${card('TECHNICALS', `<div class="chips">${chipHtml}</div>
  <div class="gauge">${gauge}<div class="glabel" style="color:${gCol}">${gLabel}<div style="font-size:10px;color:${C.dim};font-weight:400">7 signals · <span style="color:${C.put}">red</span> = bearish, <span style="color:${C.call}">green</span> = bullish</div></div></div>
  <div class="grid">${stats.map(([k, v]) => `<div><span>${k}</span><b style="color:${vCol(k)}">${v}</b></div>`).join('')}</div>
  ${t.squeezeRatio != null && t.squeezeRatio < 1 ? `<div class="note">Squeeze = Bollinger width ÷ Keltner width. Under 1 means the range is coiled tight, which usually comes before a bigger move.</div>` : ''}`)}
${card('TOP FLOWS · THIS WEEK', `${flowRows}<div class="split"><span style="color:${C.call}">bull ${money(bullP)}</span><span style="color:${C.put}">bear ${money(bearP)}</span></div>`)}
${card(`APEX LEVELS <em>${apex.expirationsUsed.length} expiries · ${md(apex.expirationsUsed[0])}–${md(apex.expirationsUsed.at(-1))}</em>`, ladder + '<div class="note">Bar = magnet score (55% OI, 45% gamma). Thick 80+ strong · medium 50-79 · thin under 50, context. Green long gamma, red short.</div>')}
${card('DEALER GAMMA', `
  <div class="kv"><span>Regime</span><b style="color:${neg ? C.put : C.call}">${neg ? 'Negative · moves amplified' : 'Positive · moves dampened'}</b></div>
  <div class="kv"><span>Gamma flip</span><b style="color:${C.flip}">${$(gex.gammaFlipLevel)}</b></div>
  <div class="kv"><span>Call wall / put wall</span><b><span style="color:${C.call}">${o.callWall}</span> / <span style="color:${C.put}">${o.putWall}</span></b></div>
  <div class="kv"><span>Max pain ${md(tk.expiration)}</span><b>${o.maxPain}</b></div>
  <div class="kv"><span>Net GEX</span><b>${gex.totalGEX < 0 ? '-' : ''}${money(Math.abs(gex.totalGEX))}</b></div>`)}
${card('IMPLIED VOLATILITY', `
  ${ivVerdict ? `<div class="iv">Options look <b style="color:${ivVerdict[1]}">${ivVerdict[0]}</b></div><div class="dimline">IV rank ${ivRank.toFixed(0)}/100 vs its own year · ${ivVerdict[2]}</div>` : ''}
  <div class="kv"><span>ATM IV</span><b>${o.atmIV.toFixed(0)}%</b></div>
  <div class="kv"><span>Priced move into ${md(tk.expiration)}</span><b>±${$(em.dollars)} (${em.percent.toFixed(0)}%)</b></div>
  <div class="kv"><span>Range</span><b>${$(em.lower)} – ${$(em.upper)}</b></div>
  ${emEarn ? `<div class="note">That move includes the ${md(tk.earnings.date)} print.</div>` : ''}`)}
`;

const W = 2560, H = 1188, CW = 2000;
const img = chart ? `data:image/png;base64,${readFileSync(chart).toString('base64')}` : '';
const html = `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}html,body{margin:0;background:${C.bg};color:${C.text};font-family:'JetBrains Mono',monospace}
.wrap{display:flex;width:${W}px;height:${H}px}
.chart{width:${CW}px;height:${H}px;flex:none}.chart img{width:100%;height:100%;display:block}
.rail{width:${W - CW}px;padding:22px 30px 12px 6px;display:flex;flex-direction:column;gap:6px;overflow:hidden}
.hero{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;padding:0 4px 4px}
.sym{font-family:'Share Tech Mono';font-size:30px;color:#00ff88}.px{font-size:20px;font-weight:700}.sub2{width:100%;font-size:11px;color:${C.dim}}
section{background:${C.panel};border:1px solid;border-radius:8px;padding:7px 12px}
h3{margin:0 0 7px;font-size:11px;letter-spacing:2px;color:${C.dim};font-weight:700}h3 em{font-style:normal;letter-spacing:0;font-weight:400;float:right}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:2px}.chip{font-size:10.5px;border:1px solid;border-radius:12px;padding:2px 8px}
.gauge{display:flex;align-items:flex-end;gap:12px;height:64px;overflow:hidden}.gauge svg{transform:scale(.58);transform-origin:left bottom;margin-right:-60px}
.glabel{font-size:14px;font-weight:700;padding-bottom:8px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px 10px;font-size:11px;margin-top:4px}.grid span{color:${C.dim};margin-right:6px}
.row{display:grid;grid-template-columns:44px 1fr auto;column-gap:8px;font-size:11.5px;padding:3px 0;border-bottom:1px solid ${C.line}}
.row .sub{grid-column:2/4;font-size:10px;color:${C.dim}}.tag{font-size:9.5px;font-weight:700;border-radius:4px;text-align:center;padding:1px 0;height:16px}.r{font-weight:700}
.split{display:flex;justify-content:space-between;font-size:11px;margin-top:5px}
.lad{display:grid;grid-template-columns:30px 1fr 26px 62px;gap:8px;align-items:center;font-size:11px;height:16px}.lad .k{text-align:right;font-weight:700}
.bar{height:8px;align-self:center;background:#1a1a26;border-radius:3px;overflow:hidden}.bar i{display:block;height:100%;opacity:.85}.bar.t1{height:3px}.bar.t1 i{opacity:.5}.bar.t2{height:7px}.bar.t3{height:12px}.bar.t3 i{opacity:1;box-shadow:0 0 6px currentColor}.lad .oi,.lad .s{color:${C.dim};font-size:10px}
.spotline{border-top:1px dashed #e6e6ee88;margin:3px 0 2px 38px;position:relative;height:0}.spotline span{position:absolute;left:40%;top:-8px;background:${C.panel};font-size:10px;padding:0 4px}
.kv{display:flex;justify-content:space-between;font-size:12px;padding:2px 0}.kv span{color:${C.dim}}
.note,.dimline{font-size:10.5px;color:${C.dim};margin-top:4px;line-height:1.35}.iv{font-size:15px}
</style></head><body><div class="wrap"><div class="chart">${img ? `<img src="${img}">` : ''}</div><div class="rail">${rail}</div></div></body></html>`;

const base = join(OUT, `${sym.toLowerCase()}_rail_${new Date().toISOString().slice(0, 10)}`);
writeFileSync(`${base}.html`, html);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1.6 });
await page.setContent(html, { waitUntil: 'networkidle' }).catch(() => {});
const over = await page.evaluate(() => { const r = document.querySelector('.rail'); return r.scrollHeight - r.clientHeight; });
if (over > 0) console.error(`rail overflows by ${over}px`);
await page.screenshot({ path: `${base}.png` });
await browser.close();
console.log(`${base}.png`);
