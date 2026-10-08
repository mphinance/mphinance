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
    const r = await fetch(`${DEV_BASE}${path}`, {
      headers: { 'X-API-Key': KEY, 'User-Agent': UA },
      signal: AbortSignal.timeout(30000),
    });
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
// The dev API only keeps snapshot history for a whitelist of index ETFs and
// megacaps. Everything else (single names like ASTS) gets 1-minute regular-
// session bars from Yahoo, reshaped to the same {snapshotTime, spotPrice} rows.
const hist = await api(`/gex/${sym}/historical?hours=168`).catch(async (err) => {
  if (!/only available for/i.test(err.message)) throw err;
  console.log(`no TDPro history for ${sym}, using Yahoo 1m bars`);
  const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1m&range=7d`, {
    headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000),
  });
  const res = (await r.json())?.chart?.result?.[0];
  if (!res?.timestamp) throw new Error(`${sym}: no price history from TDPro or Yahoo`);
  const close = res.indicators.quote[0].close;
  return res.timestamp
    .map((t, i) => ({ snapshotTime: new Date(t * 1000).toISOString(), spotPrice: close[i] }))
    .filter((p) => p.spotPrice != null);
});
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
const etParts = (d) => {
  const f = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', hour12: false,
  }).formatToParts(d).reduce((a, x) => ((a[x.type] = x.value), a), {});
  return { date: `${f.year}-${f.month}-${f.day}`, hour: parseInt(f.hour, 10) };
};
const todayET = etParts(new Date()).date;
let survivors = null, expiringShare = 0;
if (matrix?.rows?.length) {
  const live = matrix.expirations.map((e) => e > todayET);
  const sum = (arr, mask) => arr.reduce((a, v, i) => a + (mask[i] && v ? v : 0), 0);
  const all = matrix.expirations.map(() => true);
  survivors = new Map(matrix.rows.map((r) => [r.strike, sum(r.gex, live)]));
  // Summing signed gamma and THEN taking abs let a row's surviving magnitude
  // exceed its total (offsetting signs cancel in the total but not in the
  // subset), which can drive the headline share negative on exactly the
  // heavy-0DTE days this was built to flag. Sum magnitudes per expiry instead.
  const absSum = (arr, mask) => arr.reduce((a, v, i) => a + (mask[i] && v ? Math.abs(v) : 0), 0);
  const tot = matrix.rows.reduce((a, r) => a + absSum(r.gex, all), 0);
  const kept = matrix.rows.reduce((a, r) => a + absSum(r.gex, live), 0);
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
if (!ladder.length) throw new Error(`no strikes within ${(BAND * 100).toFixed(1)}% of spot`);
const maxAbs = Math.max(...ladder.map((s) => Math.abs(s.netGex)));
// Relative-only thresholds will happily label a "ceiling" in a book with a few
// thousand dollars of gamma in it. The absolute floor lets the chart say the
// structure is too thin to read instead of inventing one.
// Default is sized for SPY. A single name's whole book can be a few $M, so
// --minwall (in $M) lets it be read on its own scale instead of as THIN BOOK.
const MIN_WALL = parseFloat(arg('minwall', '50')) * 1e6;
const WALL = Math.max(maxAbs * 0.28, MIN_WALL);
const thinBook = maxAbs < MIN_WALL * 2;

const above = ladder.filter((s) => s.strike > spot);
const below = ladder.filter((s) => s.strike < spot);

// The ceiling: the heaviest long-gamma strike above spot. Taking the FIRST one
// instead breaks whenever the positive stack starts right at spot -- you get a
// "ceiling" sitting below the gamma flip, which is nonsense.
const gate = above.filter((s) => s.netGex > WALL).sort((a, b) => b.netGex - a.netGex)[0] || null;
// A big SHORT-gamma strike above spot does not stop a rally. Dealers are short
// gamma there, so they must buy into strength: price accelerates through it.
// This is the mirror of the downside lesson ("a crowd, not a floor") and it was
// previously mislabelled WALL / "needs volume", telling a reader to fade a level
// the model's own physics says should rip.
const accel = above.filter((s) => s.netGex < -WALL && s.strike !== magnet && (!gate || s.strike < gate.strike))
  .sort((a, b) => a.netGex - b.netGex)[0] || null;
// The pin is whatever price is actually wrestling with, so it has to be local.
// maxGammaStrike from the API is the biggest strike in the WHOLE book, which on
// a day with a far-off put wall is six points away and not a pin at all.
const near = ladder.filter((s) => Math.abs(s.strike - spot) <= 1.5);
const pin = near.length
  ? near.slice().sort((a, b) => Math.abs(b.netGex) - Math.abs(a.netGex))[0].strike
  : magnet;
// No `|| {netGex: 0}` here on purpose. A missing strike used to default to 0,
// and `0 < 0` is false, so the tool printed "long gamma, so it settles" -- the
// calmest possible read -- exactly when it had no data.
const pinLvl = ladder.find((s) => s.strike === pin) || null;
const pinNet = pinLvl ? pinLvl.netGex : null;

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

// Walk DOWN from spot the way price would. The first strike heavy enough to
// matter is the shelf (long gamma: something to lean on) or the trapdoor
// (short gamma: dealers sell into it). Below it, the strikes down to the put
// wall are either one CONTIGUOUS empty band or a grind.
//
// Contiguity is the fix. This used to collect every thin strike above the wall
// whether or not they touched, so on 2026-10-02 it printed "761 to 769 is
// empty" straight across a -$535M strike at 767. Same rules as the TraderMatrix
// chart-share port (backend/src/services/share/tomorrowMap.ts) -- change both.
const walk = below.slice().reverse(); // nearest first
const firstIdx = walk.findIndex((s) => Math.abs(s.netGex) >= WALL);
const firstHeavy = firstIdx >= 0 ? walk[firstIdx] : null;
const shelfLvl = firstHeavy && (!floor || firstHeavy.strike !== floor.strike) ? firstHeavy : null;

// The band that has to be empty: from the shelf (or from spot, when price is
// already standing in the air) down to the wall.
const bandTop = shelfLvl ? shelfLvl.strike : Infinity;
// The pin is never air: ASTS 2026-10-06 printed "57 PIN" inside "56 to 58,
// nothing here". When the pin sits under spot the band starts below it.
const between = floor
  ? walk.filter((s) => s.strike < bandTop && s.strike > floor.strike && (pin == null || pin >= spot || s.strike < pin))
  : [];

// The cushion: the best positive-gamma strike in that band. Dealers are long
// gamma there, so they buy into weakness -- structurally different from a big
// negative strike, which is a crowd, not a floor. Must carry a tenth of a wall
// to count; a $10M strike in a $1.4B book is not a bid.
const cushion = between.filter((s) => s.netGex >= WALL * 0.1).sort((a, b) => b.netGex - a.netGex)[0] || null;

// Air pocket: the band, but only if EVERY strike in it is thin.
let pocket = null;
if (floor && between.length >= 2 && between.every((s) => Math.abs(s.netGex) < WALL)) {
  pocket = {
    lo: Math.min(...between.map((s) => s.strike)),
    hi: Math.max(...between.map((s) => s.strike)),
    net: between.reduce((a, s) => a + Math.abs(s.netGex), 0),
    n: between.length,
  };
}

// ── the ledger: every map this tool publishes gets written down ────────────
// Without this the chart is a theory. With it, the left half of the picture can
// show whether last night's call actually happened, which is the only thing that
// makes the right half worth reading.
const LEDGER = join(ROOT, 'data/gamma_maps', `${sym}.json`);
let ledger = [];
let ledgerBroken = false;
if (existsSync(LEDGER)) {
  try {
    const parsed = JSON.parse(readFileSync(LEDGER, 'utf8'));
    if (!Array.isArray(parsed)) throw new Error('not an array');
    ledger = parsed;
  } catch (e) {
    // Treating this as "first run" and then overwriting would destroy the whole
    // grading history with no trace. Refuse to write instead.
    ledgerBroken = true;
    console.error(`LEDGER UNREADABLE (${e.message}) -- grading is off and nothing will be written. Fix ${LEDGER} by hand.`);
  }
}

const negGamma = gex.totalGEX < 0;
// When the flip sits on top of price it has no information: you get a crossing
// every few minutes and none of them mean anything. Say so rather than drawing
// two confident roads out of the same point.
const flipOnPrice = Math.abs(flip - spot) < spot * 0.0004;
const fmtM = (v) => {
  const a = Math.abs(v);
  if (a >= 1e9) return `${v < 0 ? '−' : ''}$${(a / 1e9).toFixed(2)}B`;
  if (a < 10e6) return `${v < 0 ? '−' : ''}$${(a / 1e6).toFixed(1)}M`;
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

// ── review every prior day before drawing a new one ─────────────────────────
// Grading is durable: once a session is scored the result is written into its
// ledger entry and never recomputed, because the history feed only reaches back
// ~5 sessions and an old map could not be re-graded later.
const lastSession = allSessions[allSessions.length - 1];
const sessionBars = (day) => allPts.filter((q) => dayKey(q.t) === day).map((q) => q.px);

if (!allPts.length) throw new Error('history feed returned no usable points');
const lastTick = allPts[allPts.length - 1].t;
const sessionClosed = lastSession < todayET || etParts(lastTick).hour >= 16;

// Draw fewer sessions than we measure: the map only references the last one,
// and three sessions gives the candles almost double the width.
const SHOW = parseInt(arg('sessions', '3'), 10);
const keep = new Set(allSessions.slice(-SHOW));
const pts = allPts.filter((q) => keep.has(dayKey(q.t)));
const sessions = allSessions.slice(-SHOW);

function gradeEntry(e, day, bars) {
  const open = bars[0], high = Math.max(...bars), low = Math.min(...bars), close = bars[bars.length - 1];

  // A level price never went near tells you nothing. Counting "never reached the
  // put wall" as a HIT on a quiet day is something a null model with arbitrary
  // round numbers scores just as well. Untested levels stay out of the ratio.
  //
  // Scored on the CLOSE (regraded 2026-10-08). "Rallies stall into long gamma"
  // means dealers sell the rip: 780 on 10/06 was wicked 1.58 through and closed
  // under. Across the first 10 sessions the brakes/ceilings held on the close
  // 5/5 and intraday 1/5. The wick is still reported, it just is not the claim.
  const tol = (e.expected || expected) * 0.25;
  const checks = [];
  const level = (lvl, side, label) => {
    if (lvl == null) return;
    const reached = side === 'low' ? low : high;
    const dist = Math.abs(reached - lvl);
    const wickHeld = side === 'low' ? low >= lvl : high <= lvl;
    const held = side === 'low' ? close >= lvl : close <= lvl;
    const thru = side === 'low' ? lvl - low : high - lvl;
    checks.push({ lvl, side, dist: +dist.toFixed(2), thru: +thru.toFixed(2), tested: dist <= tol || !wickHeld, ok: held, wickHeld, label });
  };
  // The flip is a ceiling when price is under it and a floor when price is over
  // it. It used to be graded as a ceiling every time, so every night drawn above
  // the flip booked a MISS ("broke 768.1 flip by 13.48") for being above it.
  const spot = e.spot;
  if (e.flip != null) level(e.flip, spot < e.flip ? 'high' : 'low', `${e.flip} flip`);
  level(e.cushion, 'low', `${e.cushion} cushion`);
  level(e.brake ?? e.battle, 'high', `${e.brake ?? e.battle} brake`);
  level(e.gate, 'high', `${e.gate} ceiling`);
  // The put wall is not scored: the map calls it "a crowd, not a floor", so a
  // close under it is not a miss and a close over it is not a hit. Reported only.
  const wallHit = e.wall != null && low <= e.wall + tol;

  // Which road the session took, read off the map's own first level each way.
  // Reported, never scored: the map lays out all three roads and does not pick.
  // (It used to award a point per session for "not a whipsaw", and defined UP
  // as "high over the flip", which is every day once price is above it.)
  const ups = [e.flip, e.brake ?? e.battle, e.gate].filter((v) => v != null && v > spot);
  const dns = [e.shelf, e.cushion, e.flip, e.wall].filter((v) => v != null && v < spot);
  const upTrig = ups.length ? Math.min(...ups) : null;
  const dnTrig = dns.length ? Math.max(...dns) : null;
  const wentUp = upTrig != null && high > upTrig;
  const wentDown = dnTrig != null && low < dnTrig;
  const branch = wentUp && wentDown ? 'WHIPSAW' : wentUp ? 'UP' : wentDown ? 'DOWN' : 'RANGE';
  const branchOk = branch !== 'WHIPSAW';

  // Baseline: the same number of levels each side, at plain $5 round numbers
  // stepping away from spot, scored by the same rule. A hit rate without this
  // is a number with nothing to compare it to.
  const nUp = checks.filter((c) => c.side === 'high').length;
  const nDn = checks.filter((c) => c.side === 'low').length;
  const nullHits = [], R = 5;
  for (let i = 0; i < nUp; i++) {
    const v = Math.ceil(spot / R) * R + R * i;
    if (high >= v - tol) nullHits.push(close <= v);
  }
  for (let i = 0; i < nDn; i++) {
    const v = Math.floor(spot / R) * R - R * i;
    if (low <= v + tol) nullHits.push(close >= v);
  }

  // The RANGE road's claim: on a day neither road fires, price settles near the
  // pin. Scored only on RANGE days, as "closed within half a typical day of
  // the pin", against the nearest $5 round number to spot by the same rule.
  if (branch === 'RANGE' && e.chartPin != null) {
    const near = tol * 2;
    checks.push({ lvl: e.chartPin, side: 'pin', dist: +Math.abs(close - e.chartPin).toFixed(2), thru: 0,
                  tested: true, ok: Math.abs(close - e.chartPin) <= near, wickHeld: true, label: `${e.chartPin} pin` });
    const r5 = Math.round(spot / R) * R;
    nullHits.push(Math.abs(close - r5) <= near);
  }

  const tested = checks.filter((c) => c.tested);
  const untested = checks.filter((c) => !c.tested);
  const verb = (c) => {
    if (c.side === 'pin') return c.ok ? `settled ${c.dist.toFixed(2)} from the ${c.label}` : `MISS closed ${c.dist.toFixed(2)} from the ${c.label}`;
    if (c.ok && !c.wickHeld) return `wicked ${c.thru.toFixed(2)} through ${c.label}, closed ${c.side === 'high' ? 'under' : 'over'}`;
    return `${c.ok ? 'held' : 'MISS closed through'} ${c.label}${c.ok ? ` by ${c.dist.toFixed(2)}` : ''}`;
  };
  return {
    day, open, high, low, close, branch, branchOk, checks, tested, untested,
    hits: tested.filter((c) => c.ok).length,
    total: tested.length,
    nullHits: nullHits.filter(Boolean).length,
    nullTotal: nullHits.length,
    summary: [
      branch === 'WHIPSAW' ? 'whipsawed both roads' : `took the ${branch} road`,
      ...tested.map(verb),
      wallHit ? `tagged the ${e.wall} put wall` : '',
      untested.length ? `${untested.length} level${untested.length > 1 ? 's' : ''} untested` : '',
    ].filter(Boolean).join(' · '),
  };
}

let ledgerDirty = false;
// --regrade: rescore every graded entry under the current rules from daily
// OHLC (Yahoo). The intraday feed only reaches ~5 sessions back, so this is the
// only way to put old entries on new rules. The previous grade is kept as
// graded_v1 so the change is auditable. Used once on 2026-10-08 (v2 rules).
if (argv.includes('--regrade') && !ledgerBroken) {
  const yr = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${sym}?interval=1d&range=6mo`, {
    headers: { 'User-Agent': 'Mozilla/5.0' }, signal: AbortSignal.timeout(30000),
  }).then((r) => r.json());
  const res = yr?.chart?.result?.[0];
  const qq = res.indicators.quote[0];
  const daily = res.timestamp.map((t, i) => ({ d: new Date(t * 1000).toISOString().slice(0, 10), o: qq.open[i], h: qq.high[i], l: qq.low[i], c: qq.close[i] }))
    .filter((b) => b.c != null);
  for (const e of ledger) {
    if (!e.graded) continue;
    const b = daily.find((x) => x.d > e.madeAfter);
    if (!b || b.d !== e.graded.day) { console.log(`regrade skip ${e.madeAfter}: no matching daily bar`); continue; }
    const g = gradeEntry(e, b.d, [b.o, b.h, b.l, b.c]);
    if (e.graded.v !== 2) e.graded_v1 = e.graded;
    e.graded = { v: 2, day: g.day, branch: g.branch, hits: g.hits, total: g.total,
                 nullHits: g.nullHits, nullTotal: g.nullTotal,
                 untested: g.untested.length, summary: g.summary,
                 checks: g.tested.map((c) => ({ lvl: c.lvl, side: c.side, ok: c.ok })), source: 'daily OHLC regrade' };
    console.log(`regraded ${e.madeAfter} -> ${g.day}: ${g.hits}/${g.total} (null ${g.nullHits}/${g.nullTotal}) | ${g.summary}`);
  }
  ledgerDirty = true;
}

// Backfill: score any prior entry whose session has closed and is still in reach.
if (!ledgerBroken) {
  for (const e of ledger) {
    if (e.graded) continue;
    const i = allSessions.indexOf(e.madeAfter);
    const day = i >= 0 ? allSessions[i + 1] : null;
    if (!day) continue;
    if (day === lastSession && !sessionClosed) continue;
    const bars = sessionBars(day);
    if (!bars.length) continue;
    const g = gradeEntry(e, day, bars);
    e.graded = { v: 2, day: g.day, branch: g.branch, hits: g.hits, total: g.total,
                 nullHits: g.nullHits, nullTotal: g.nullTotal,
                 untested: g.untested.length, summary: g.summary,
                 checks: g.tested.map((c) => ({ lvl: c.lvl, side: c.side, ok: c.ok })) };
    ledgerDirty = true;
  }
}

// The running record. Not published until there are enough sessions for it to
// mean anything: a one-session "4/4" is a number, not a track record.
const MIN_GRADED = 10;
// Only sessions graded LIVE under the v2 rules count toward the public record.
// The 10 sessions before 2026-10-08 were regraded after the fact, under rules
// chosen while looking at them (close-grading came from seeing the brakes hold
// on the close). Scoring rules on the data that shaped them is in-sample, so
// those stay in the ledger as history and the public clock restarts.
const gradedAll = ledger.filter((e) => e.graded && e.graded.v === 2 && !e.graded.source);
const inSample = ledger.filter((e) => e.graded && e.graded.source);
const record = {
  inSample: { sessions: inSample.length, hits: inSample.reduce((a, e) => a + e.graded.hits, 0), total: inSample.reduce((a, e) => a + e.graded.total, 0),
              nullHits: inSample.reduce((a, e) => a + (e.graded.nullHits ?? 0), 0), nullTotal: inSample.reduce((a, e) => a + (e.graded.nullTotal ?? 0), 0) },
  // Gamma levels that are NOT $5 round numbers. On SPY most brakes are round
  // strikes, so the round-number baseline cannot separate them from gamma;
  // this split can. Reported, not published, until it has a sample.
  nonRound: (() => {
    const cs = gradedAll.flatMap((e) => e.graded.checks || []).filter((c) => c.side !== 'pin' && c.lvl % 5 !== 0);
    return { hits: cs.filter((c) => c.ok).length, total: cs.length };
  })(),
  sessions: gradedAll.length,
  hits: gradedAll.reduce((a, e) => a + e.graded.hits, 0),
  total: gradedAll.reduce((a, e) => a + e.graded.total, 0),
  nullHits: gradedAll.reduce((a, e) => a + (e.graded.nullHits ?? 0), 0),
  nullTotal: gradedAll.reduce((a, e) => a + (e.graded.nullTotal ?? 0), 0),
  // Every graded entry must be on the v2 rules before the record is claimable;
  // mixing the old flip-side bug into a published rate would be worse than none.
  publishable: gradedAll.length >= MIN_GRADED,
  minSessions: MIN_GRADED,
};

// The panel still shows yesterday, because that is reporting, not a claim.
const priorSession = allSessions[allSessions.length - 2];
const prev = ledgerBroken ? null : ledger.find((e) => e.madeAfter === priorSession);
let report = null;
if (prev) {
  const bars = sessionBars(lastSession);
  if (bars.length) report = { ...gradeEntry(prev, lastSession, bars), partial: !sessionClosed, prev,
    levels: [prev.shelf, prev.cushion, prev.wall, prev.flip, prev.battle, prev.brake, prev.gate]
      .filter((v) => v != null) };
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

const yRaw = [lo, hi, ...pts.map((p) => p.px)];
const ySpan = Math.max(...yRaw) - Math.min(...yRaw);
// Waypoint labels hang below their dot, so the bottom needs more room than the
// top or the furthest road gets its caption sliced off by the frame.
const yLo = Math.min(...yRaw) - ySpan * 0.06;
const yHi = Math.max(...yRaw) + ySpan * 0.03;
const Y = (px) => PAD_T + PLOT_H - ((px - yLo) / (yHi - yLo)) * PLOT_H;
const X = (i) => PAD_L + (pts.length > 1 ? i / (pts.length - 1) : 0.5) * PAST_W;

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

// ── the three roads ─────────────────────────────────────────────────────────
// One shared price axis, three branches out of spot. A waypoint is a price the
// tape has to deal with; its note says what the book does to price THERE, which
// is the whole point -- the same level behaves differently depending on which
// way you arrived at it.
const rangeLo = Math.min(pin, Math.floor(spot)) - 1;
const rangeHi = Math.max(pin, Math.ceil(flip));

const sideFilter = (pts_, up) => pts_.filter((w) => w && (up ? w.at > spot : w.at < spot));

const roads = [
  {
    key: 'UP',
    col: C.call,
    // Led by the brake, not the flip. In the first 10 graded sessions the flip
    // held on the close 3 of 6 times, a coin flip; brakes and ceilings held 5/5.
    // The flip is kept as context (which regime dealers are in), not as the
    // trigger a reader acts on.
    cond: brake ? `up into ${brake.strike}` : gate ? `up into ${gate.strike}` : 'higher',
    rule: gate
      ? ((flip > spot ? `under the flip (${flip.toFixed(2)}) dealers chase, so it can get there fast. ` : '') + (brake
          ? `${accel ? `rips through ${accel.strike}, then ` : ''}stalls at ${brake.strike}: it can wick over, it tends to close under. ceiling ${gate.strike}.`
          : `${accel ? `rips through ${accel.strike}. ` : ''}nothing gives until ${gate.strike}, and it tends to close under that.`))
      : `dealers brake. no ceiling in range.`,
    side: -1,
    pts: [
      flip > spot ? { at: flip, tag: `${flip.toFixed(2)} FLIP`, note: 'dealers stop chasing, start braking' } : null,
      accel ? { at: accel.strike, tag: `${accel.strike} ACCELERANT`, note: `${oiFmt(accel.callOi)} calls, dealers buy into strength` } : null,
      brake ? { at: brake.strike, tag: `${brake.strike} BRAKE`, note: 'wicks through, closes under' } : null,
      gate ? { at: gate.strike, tag: `${gate.strike} CEILING`, note: 'move dies here' } : null,
    ], up: true,
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
    pts: [{ at: pin, tag: `${pin} PIN`, note: pinNet === null ? 'no listed strike here, regime unknown'
        : pinNet < 0 ? 'short gamma, so it chops hard' : 'long gamma, so it settles' }],
  },
  {
    key: 'DOWN',
    col: C.put,
    cond: shelfLvl ? `below ${shelfLvl.strike}` : `below ${Math.floor(spot)}`,
    rule: (() => {
      // The shelf is a real listed strike (it came off the ladder), so the old
      // "missing strike defaults to a SHELF" trap cannot recur here.
      const lead = shelfLvl
        ? (shelfLvl.netGex >= 0 ? `leans on ${shelfLvl.strike}. lose it and ` : `trapdoor at ${shelfLvl.strike}. through it, `)
        : '';
      if (!floor) {
        return shelfLvl
          ? (shelfLvl.netGex >= 0 ? `leans on ${shelfLvl.strike}. ` : `trapdoor at ${shelfLvl.strike}. `) + 'no readable structure below it.'
          : 'no readable structure below spot.';
      }
      if (cushion) return `${lead}thin air. only real bid is ${cushion.strike}. then ${floor.strike}.`;
      if (pocket) return `${lead}open air. ${pocket.lo} to ${pocket.hi} is empty. next stop ${floor.strike}.`;
      return `${lead}no thin band above ${floor.strike}. grind, not a drop.`;
    })(),
    side: 1,
    pts: floor || shelfLvl
      ? [
          shelfLvl
            ? (shelfLvl.netGex >= 0
                ? { at: shelfLvl.strike, tag: `${shelfLvl.strike} LAST SHELF`, note: 'the last thing to lean on' }
                : { at: shelfLvl.strike, tag: `${shelfLvl.strike} TRAPDOOR`, note: `${oiFmt(shelfLvl.putOi)} puts, and dealers sell into it` })
            : null,
          cushion
            ? { at: cushion.strike, tag: `${cushion.strike} THIN CUSHION`, note: 'only dealer buying down here, and it is small', open: true }
            : pocket
              ? { at: (pocket.lo + pocket.hi) / 2, tag: 'EMPTY', note: `${pocket.lo} to ${pocket.hi}, nothing here`, open: true }
              : null,
          floor ? { at: floor.strike, tag: `${floor.strike} PUT WALL`, note: `${oiFmt(floor.putOi)} puts. the fight is here` } : null,
        ].filter(Boolean)
      : [{ at: Math.round(lo), tag: `${Math.round(lo)}`, note: 'no thin band below' }],
    up: false,
  },
];

// ── svg ─────────────────────────────────────────────────────────────────────
let s = '';
const push = (x) => { s += x; };

push(`<rect width="${W}" height="${H}" fill="${C.bg}"/>`);

// header
push(`<text x="${PAD_L}" y="46" font-family="'Share Tech Mono',monospace" font-size="30" fill="${C.text}" letter-spacing="1">TOMORROW'S MAP <tspan fill="${C.green}">${esc(sym)}</tspan></text>`);
push(`<text x="${PAD_L}" y="72" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">spot ${spot.toFixed(2)} · flip ${flip.toFixed(2)} · pin ${pin} · net GEX ${fmtM(gex.totalGEX)}${survivors && expiringShare >= 0.005 ? ` · levels exclude the ${(expiringShare * 100).toFixed(0)}% of gamma that does not survive to the next session` : ''}</text>`);
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
  const byLvl = Object.fromEntries(report.checks.map((c) => [c.lvl, c]));
  for (const lvl of report.levels) {
    const y = Y(lvl);
    if (y < PAD_T || y > PAD_T + PLOT_H) continue;
    const c = byLvl[lvl];
    // untested levels are drawn grey: price never went near them, so they were
    // neither right nor wrong and must not read as a green tick.
    const col = !c || !c.tested ? C.dim : c.ok ? C.call : C.put;
    push(`<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${col}" stroke-width="1.2" stroke-opacity="${c && c.tested ? 0.75 : 0.28}" stroke-dasharray="3 3"/>`);
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
if (thinBook) {
  push(`<rect x="${FWD_X + 12}" y="${PAD_T + 56}" width="440" height="24" rx="5" fill="${C.coral}" fill-opacity="0.12" stroke="${C.coral}" stroke-opacity="0.4"/>`);
  push(`<text x="${FWD_X + 22}" y="${PAD_T + 73}" font-family="'JetBrains Mono',monospace" font-size="11.5" fill="${C.coral}">THIN BOOK. these levels carry little size, read them lightly.</text>`);
}
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
  if (r.up !== undefined) r.pts = sideFilter(r.pts, r.up);
  if (!r.pts.length) continue;
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
      tag: last && !r.wave ? `${r.key} · ${w.tag}` : w.tag, note: w.note, col: r.col,
      faint: !(w.at <= emHi && w.at >= emLo),
    });
  });

  // Road name: folded into the final waypoint's tag for the directional roads
  // (see the label loop), drawn on its own only for the wave, which has no
  // waypoint at the far end to carry it.
  if (r.wave) {
    push(`<text x="${ROAD_X0 + ROAD_W + 12}" y="${Y(pin) + 4}" font-family="'Share Tech Mono',monospace" font-size="15" fill="${r.col}" letter-spacing="1">${r.key}</text>`);
  }
}

// Waypoint labels are placed last, as one pass, so labels from different roads
// cannot land on top of each other. When a label has to move off its dot, a
// leader line keeps the two connected.
labels.sort((a, b) => a.ty - b.ty);
const LBL_H = 34;
let lastTy = -Infinity;
for (const L of labels) {
  if (L.ty - lastTy < LBL_H) L.ty = lastTy + LBL_H;
  L.ty = Math.min(Math.max(L.ty, PAD_T + 16), PAD_T + PLOT_H - 40); // -40 leaves room for the note line that hangs 15px below the tag
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
  push(`<text x="${PAD_L + 130}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.text}">${report.partial ? `${report.day.slice(5)} still open` : `${report.hits}/${report.total} tested on ${report.day.slice(5)}`}</text>`);
  push(`<text x="${PAD_L + 290}" y="${y + 3}" font-family="'JetBrains Mono',monospace" font-size="13" fill="${C.dim}">${esc(report.summary)}</text>`);
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
  // `pin` was always the API's maxGammaStrike (787 on 10/06 with spot 779), not
  // the pin the chart draws, so the RANGE road could never be graded. Kept for
  // continuity; chartPin is the one the map actually claims.
  spot, flip, pin: magnet, chartPin: pin, expected,
  accel: accel ? accel.strike : null,
  brake: brake ? brake.strike : null,
  gate: gate ? gate.strike : null,
  shelf: shelfLvl ? shelfLvl.strike : null,
  cushion: cushion ? cushion.strike : null,
  wall: floor ? floor.strike : null,
};
if (ledgerBroken) {
  console.log('not writing the ledger: it is unreadable and overwriting it would lose the history');
} else if (sessionClosed || ledgerDirty) {
  const kept = ledger.filter((e) => e.madeAfter !== entry.madeAfter);
  if (kept.length) writeFileSync(`${LEDGER}.bak`, JSON.stringify(ledger, null, 2) + '\n');
  if (sessionClosed) kept.push(entry);
  kept.sort((a, b) => a.madeAfter.localeCompare(b.madeAfter));
  mkdirSync(dirname(LEDGER), { recursive: true });
  writeFileSync(LEDGER, JSON.stringify(kept.slice(-120), null, 2) + '\n');
} else {
  console.log('session still open: not writing to the ledger, and the score below is provisional');
}

console.log(`record so far: ${record.sessions} session(s) graded${record.publishable ? '' : ` -- not publishable until ${MIN_GRADED}`}`);
if (report) console.log(`${report.partial ? 'in flight' : 'last call'}: ${report.hits}/${report.total} tested on ${report.day} | ${report.summary}`);
console.log(`spot ${spot} | flip ${flip} | magnet ${magnet} | netGEX ${fmtM(gex.totalGEX)}`);
console.log(`gate ${gate?.strike} | brake ${brake?.strike} | accel ${accel?.strike} | floor ${floor?.strike} | pocket ${pocket ? `${pocket.lo}-${pocket.hi}` : 'none'}`);
// Sidecar so downstream publishers (the daily Substack note) never have to
// re-derive the map or scrape it back out of the PNG.
const sidecar = join(OUT, `${sym.toLowerCase()}_tomorrow_${stamp}.json`);
writeFileSync(sidecar, JSON.stringify({
  symbol: sym,
  asOf: new Date().toISOString(),
  forSession: sessionClosed ? 'next' : 'intraday-provisional',
  sessionClosed,
  spot, flip, pin, expected,
  regime: negGamma ? 'negative gamma' : 'positive gamma',
  netGEX: gex.totalGEX,
  expected,
  expiringShare,
  flipOnPrice,
  thinBook,
  levels: {
    ceiling: gate ? gate.strike : null,
    brake: brake ? brake.strike : null,
    accel: accel ? accel.strike : null,
    shelf: shelfLvl ? shelfLvl.strike : null,
    cushion: cushion ? cushion.strike : null,
    putWall: floor ? floor.strike : null,
  },
  branches: ifRows.map((r) => ({
    kind: r.isElse ? 'ELSE' : 'IF',
    cond: r.isElse ? `it holds ${r.cond}` : `it goes ${r.cond}`,
    rule: r.rule,
  })),
  record,
  lastCall: report && !report.partial
    ? { day: report.day, hits: report.hits, total: report.total, branch: report.branch,
        untested: report.untested.length, summary: report.summary }
    : null,
  png,
}, null, 2) + '\n');

console.log(png);
console.log(sidecar);
