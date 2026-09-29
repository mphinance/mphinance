#!/usr/bin/env node
// wheel_desk / publish.mjs
// Merges the cron session's grades (grades.json) with the numbers in packet.json
// and ships the result to TMPro.
//
//   node tools/wheel_desk/publish.mjs notes   [--date D]              → prints the exact watchlist note per ticker (JSON)
//   node tools/wheel_desk/publish.mjs draft   [--date D] --watchlist-id N   → writes draft.json for build_post.mjs
//
// The watchlist itself is created by the Claude session through the TDPro MCP
// (it acts as user 8; the agent key can't pick a list). The notes it writes must
// be EXACTLY the strings `notes` prints, because the backend compares the live
// note to `seededNote` to tell Michael's edits from ours.

import { readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const TD_BASE = process.env.TD_API_URL || 'https://traderdaddy-pro-whop-production.up.railway.app';
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const [cmd, ...rest] = process.argv.slice(2);
const opt = (k) => { const i = rest.indexOf(`--${k}`); return i >= 0 ? (rest[i + 1] && !rest[i + 1].startsWith('--') ? rest[i + 1] : true) : undefined; };

function todayChicago() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago' }).format(new Date());
}
const DATE = opt('date') || todayChicago();
const DIR = join(ROOT, 'data', 'wheel-desk', DATE);

const clip = (s, n) => (s == null ? null : String(s).replace(/\s+/g, ' ').trim().slice(0, n));
const mmdd = (iso) => (iso ? `${iso.slice(5, 7)}/${iso.slice(8, 10)}` : '');

// The standing rules. Deliberately the same every week so readers learn to run them.
const DEFAULT_MANAGEMENT =
  'Close at 50% of max profit. If tested (delta past ~0.40) with 7+ days left, roll down and out for a net credit; ' +
  'if no credit is available, take the shares. No stop on a put you are willing to own: the strike was the stop.';
const defaultAssignment = (s) =>
  `If assigned, basis is $${(s.strike - s.perShare).toFixed(2)}. Day one: sell a ~0.30 delta call 2-5 weeks out at or above basis.`;

async function load() {
  const packet = JSON.parse(await readFile(join(DIR, 'packet.json'), 'utf8'));
  if (!existsSync(join(DIR, 'grades.json'))) throw new Error(`no grades.json in ${DIR}; grade the packet first`);
  const grades = JSON.parse(await readFile(join(DIR, 'grades.json'), 'utf8'));
  return { packet, grades };
}

const LABEL = { selling: 'SELLING', watching: 'WATCHING', passed: 'PASSED' };

function noteFor(g, s) {
  const contract = s ? `${s.strike}P ${mmdd(s.expiry)} @${s.perShare}` : '';
  const parts = [`${LABEL[g.verdict]} ${g.grade || ''}`.trim(), contract, g.deskNote, g.whyNot ? `Risk: ${g.whyNot}` : null];
  return clip(parts.filter(Boolean).join(' · '), 500);
}

function buildSetups(packet, grades) {
  const byTicker = new Map(packet.csp.map((s) => [s.ticker, s]));
  return grades.setups.map((g) => {
    const s = byTicker.get(g.ticker);
    if (!s) throw new Error(`graded ${g.ticker} is not in the packet`);
    if (!LABEL[g.verdict]) throw new Error(`${g.ticker}: verdict must be selling|watching|passed`);
    const c = s.chart || {};
    return {
      ticker: s.ticker,
      verdict: g.verdict,
      grade: clip(g.grade, 4),
      deskNote: clip(g.deskNote, 300),
      whyNot: clip(g.whyNot, 300),
      seededNote: noteFor(g, s),
      contract: {
        strike: s.strike, expiry: s.expiry, dte: s.dte, premium: s.perShare, collateral: s.collateral,
        delta: s.delta, pop: s.pop, breakeven: s.breakeven, cushionPct: s.cushionPct, rocWeekly: s.rocWeekly,
        annualized: s.annualized, iv: s.iv, ivRank: s.ivRank ?? null, ivRankZone: s.ivRankZone ?? null,
        quoteQuality: s.quoteQuality, supportOI: s.supportOI,
      },
      context: {
        price: s.price, sector: s.sector, trend: c.trend ?? null, vs50sma: c.vs50sma ?? null, vs200sma: c.vs200sma ?? null,
        rangePos52w: c.rangePos52w ?? null, atrPct: c.atrPct ?? null, cluster: s.cluster, alsoOn: s.alsoOn,
        earningsInWindow: !!s.earnings?.inWindow,
      },
      fundOptions: (s.fundOptions?.structures || []).slice(0, 6).map((f) => ({ fund: f.fund, expiry: f.expiry, text: f.text })),
      fundOptionsNote: clip(g.fundOptionsNote, 200),
      institutional: s.institutional ? { dir: s.institutional.dir, weightDelta: s.institutional.weightDelta, fundCount: s.institutional.fundCount } : null,
      management: g.verdict === 'passed' ? null : clip(g.management || DEFAULT_MANAGEMENT, 500),
      assignment: g.verdict === 'passed' ? null : clip(g.assignment || defaultAssignment(s), 300),
    };
  });
}

function titleFor(packet) {
  const d = new Date(`${packet.date}T12:00:00Z`);
  const next = new Date(d); next.setUTCDate(d.getUTCDate() + 1);
  const fmt = (x) => x.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
  return packet.mode === 'sunday' ? `The Wheel Desk · week of ${fmt(next)}`
    : packet.mode === 'thursday' ? `The Wheel Desk · Friday gamma read, ${fmt(next)}`
      : `The Wheel Desk · ${fmt(next)}`;
}

async function main() {
  const { packet, grades } = await load();
  const setups = buildSetups(packet, grades);

  if (cmd === 'notes') {
    console.log(JSON.stringify(setups.map((s) => ({ ticker: s.ticker, verdict: s.verdict, note: s.seededNote })), null, 1));
    return;
  }
  if (cmd !== 'draft') throw new Error('usage: publish.mjs notes|draft [--date D] [--watchlist-id N]');

  const watchlistId = Number(opt('watchlist-id'));
  if (!Number.isInteger(watchlistId) || watchlistId <= 0) throw new Error('--watchlist-id N required');

  const gammaNotes = new Map((grades.gamma || []).map((g) => [g.ticker, g.note]));
  const exclude = new Set(grades.institutional?.exclude || []);
  const body = {
    watchlistId,
    date: packet.date,
    mode: packet.mode,
    title: clip(grades.title || titleFor(packet), 120),
    tape: (grades.tape || []).slice(0, 6).map((t) => clip(t, 200)),
    setups,
    gamma: packet.mode === 'thursday' || gammaNotes.size
      ? packet.gamma.slice(0, 15).map((g) => ({ ticker: g.ticker, price: g.price, topWall: g.topWall, regime: g.regime, flip: g.flip, note: clip(gammaNotes.get(g.ticker), 200) }))
      : [],
    institutional: packet.mode === 'sunday' && packet.institutional ? {
      asOf: packet.institutional.asOf,
      note: clip(grades.institutional?.note, 400),
      buying: packet.institutional.buying.filter((b) => !exclude.has(b.ticker)).slice(0, 15),
      selling: packet.institutional.selling.filter((b) => !exclude.has(b.ticker)).slice(0, 10),
    } : null,
    methodology: clip(grades.methodology || METHODOLOGY, 1500),
  };
  await writeFile(join(DIR, 'draft.json'), JSON.stringify(body, null, 1));
  // Local only: the TMPro desk route was removed 2026-09-28. build_post.mjs reads this file.
  console.log(`wrote ${join(DIR, 'draft.json')} (${setups.length} setups)`);
}

const METHODOLOGY =
  'Every name starts from TraderMatrix screens run at default settings, then gets graded by the desk independently of the ' +
  "screen's own score. Four gates: cushion (breakeven vs recent real support), chart health (trend vs the 50/200, lower lows), " +
  'IV context (rank vs its own history, not just the raw number), and liquidity (quote width, open interest at the strike). ' +
  'Names that move together (60-day return correlation) count as one bet, so only the best of a cluster can be a Sell. ' +
  'Fund option positions come from daily income-ETF holdings files: they are income overlays, not directional calls. ' +
  'Passed names stay on the board with the reason. Education, not advice: verify the live chain and use limit orders.';

main().catch((e) => { console.error(e.message || e); process.exit(1); });
