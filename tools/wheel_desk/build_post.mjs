#!/usr/bin/env node
// wheel_desk / build_post.mjs
// Builds the Substack DRAFT workspace for a published Wheel Desk.
//
//   node tools/wheel_desk/build_post.mjs --share <shareId>      (normal: after the TMPro button)
//   node tools/wheel_desk/build_post.mjs --date 2026-09-27      (local fallback, no permalink yet)
//
// Protect-the-writing rule: this fills DATA blocks only. Every prose slot is a
// `[MICHAEL: ...]` marker with fuel bullets under it. It never writes his words.
// The public artifact masks paid strikes, so full contract numbers come from the
// local draft.json for that date (same box that produced them).
//
// Output: ~/.mph-substack-cache/<date>_wheel-desk/{post.md, *.html, *.png}

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync, readFileSync as require_ } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { homedir } from 'node:os';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const API = process.env.TD_PUBLIC_API || 'https://api.traderdaddy.pro';
const SITE = process.env.TD_SITE || 'https://www.traderdaddy.pro';
const FIGURE = join(homedir(), '.claude/skills/mph-figure/scripts/render.mjs');
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36';

const argv = process.argv.slice(2);
const opt = (k) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : undefined; };

async function main() {
  let pub = null;
  const shareId = opt('share');
  if (shareId) {
    const r = await fetch(`${API}/api/share/${encodeURIComponent(shareId)}`, { headers: { 'User-Agent': UA, Accept: 'application/json' } });
    if (!r.ok) throw new Error(`share ${shareId}: HTTP ${r.status}`);
    const j = await r.json();
    pub = j.payload ?? j.artifact?.payload ?? j;
    if (pub?.kind && pub.kind !== 'wheel_desk') throw new Error(`share ${shareId} is a ${pub.kind}, not a wheel_desk`);
  }
  const date = pub?.date || opt('date');
  if (!date) throw new Error('need --share or --date');
  const draftPath = join(ROOT, 'data', 'wheel-desk', date, 'draft.json');
  if (!existsSync(draftPath)) throw new Error(`no local ${draftPath}; run publish.mjs draft first`);
  const draft = JSON.parse(await readFile(draftPath, 'utf8'));

  // Public order + Michael's edits win; local draft supplies full numbers.
  const full = new Map(draft.setups.map((s) => [s.ticker, s]));
  const setups = (pub?.setups || draft.setups).map((p) => {
    const f = full.get(p.ticker) || {};
    return { ...f, ...p, contract: f.contract || p.contract, michaelNote: p.michaelNote ?? null };
  });
  const permalink = shareId ? `${SITE}/share/wheel_desk/${shareId}` : `${SITE}/wheel`;

  const ws = join(homedir(), '.mph-substack-cache', `${date}_wheel-desk`);
  await mkdir(ws, { recursive: true });

  const selling = setups.filter((s) => s.verdict === 'selling');
  const watching = setups.filter((s) => s.verdict === 'watching');
  const passed = setups.filter((s) => s.verdict === 'passed');
  const freePicks = new Set(pub?.freePicks || selling.slice(0, 3).map((s) => s.ticker));
  const free = selling.filter((s) => freePicks.has(s.ticker));
  const paid = [...selling.filter((s) => !freePicks.has(s.ticker)), ...watching];

  // ---- figures -------------------------------------------------------------
  const figs = [];
  const card = async (s) => {
    const c = s.contract || {};
    const x = s.context || {};
    const basis = c.strike != null && c.premium != null ? (c.strike - c.premium).toFixed(2) : '-';
    const html = `<div style="font-family:Inter,system-ui;padding:18px;background:#0d1117;color:#e6edf3;border-radius:12px">
<div style="display:flex;justify-content:space-between;align-items:baseline"><div style="font-size:28px;font-weight:800">${s.ticker}</div>
<div style="font-size:14px;padding:4px 10px;border-radius:999px;background:${s.verdict === 'selling' ? '#1f6f43' : '#6b5b12'}">${s.verdict === 'selling' ? 'Selling' : 'Watching'} · ${s.grade || ''}</div></div>
<div style="font-size:20px;margin:6px 0 12px;color:#f0c14b">Sell the ${c.strike} put · ${c.expiry} (${c.dte}d) · $${c.premium}</div>
<table style="width:100%;font-size:14px;border-collapse:collapse">
${[['Price', `$${x.price}`], ['Strike vs price', `${pct(c.strike, x.price)}%`], ['Breakeven', `$${c.breakeven} (${c.cushionPct}%)`],
    ['Collateral', `$${c.collateral}`], ['Premium', `$${Math.round((c.premium || 0) * 100)} (${c.rocWeekly}%/wk)`], ['Basis if assigned', `$${basis}`],
    ['Delta / PoP', `${c.delta} / ${c.pop}%`], ['IV rank', `${c.ivRank ?? '-'} (${(c.ivRankZone || '-').replace(/_/g, ' ')})`], ['OI at floor / quotes', `${c.supportOI} / ${c.quoteQuality}`],
    ['Trend', `${x.trend} · ${x.vs50sma}% vs 50 · ${x.vs200sma}% vs 200`]]
    .map(([k, v]) => `<tr><td style="padding:4px 0;color:#8b949e">${k}</td><td style="text-align:right">${v}</td></tr>`).join('')}
</table></div>`;
    const f = join(ws, `${s.ticker}-card.html`);
    await writeFile(f, html);
    figs.push([f, join(ws, `${s.ticker}-card.png`)]);
    return `![${s.ticker} setup](${s.ticker}-card.png)`;
  };
  const passHtml = `<div style="font-family:Inter,system-ui;padding:18px;background:#0d1117;color:#e6edf3;border-radius:12px">
<div style="font-size:22px;font-weight:800;margin-bottom:10px">Passed, and why</div>
${passed.map((s) => `<div style="padding:8px 0;border-top:1px solid #30363d"><b>${s.ticker}</b> <span style="color:#8b949e">${s.contract?.strike}P ${s.contract?.expiry} · screen said yes</span><br><span style="font-size:14px">${esc(s.whyNot)}</span></div>`).join('')}
</div>`;
  await writeFile(join(ws, 'passed.html'), passHtml);
  figs.push([join(ws, 'passed.html'), join(ws, 'passed.png')]);

  // ---- post.md (native pusher format: # title, *subtitle*, ##, - bullets, ---) --
  const L = [];
  // Layout per SUBSTACK.md (Michael's hand layout, 2026-09-27): hero, blockquote TLDR,
  // subscribe button after the intro, $CASHTAG headings, TraderMatrix links + share
  // button before the paywall marker.
  const hero = await makeHero(ws, date, { selling: selling.length, passed: passed.length, total: setups.length });
  L.push(`# ${draft.title || "The Wheel Desk"}`, '', '*Trading 80% | Mindset 20%*', '');
  if (hero) L.push('![The Wheel Desk](hero.png)', '');
  L.push('> **TLDR: [MICHAEL: one line. Fuel: ' +
    `${setups.length} names screened, ${selling.length} I'd sell, ${passed.length} passed` + ']**', '');
  L.push('[MICHAEL: opening scene. Fuel:', `- ${selling.length} selling, ${watching.length} watching, ${passed.length} passed out of ${setups.length} the screen liked`,
    ...screenFuel(date, setups), '- delete this block before pushing]', '', '<!--subscribe-->', '');
  L.push('## The tape', '');
  for (const t of draft.tape || []) L.push(`- ${t}`);
  L.push('', '[MICHAEL: one-line read on the tape]', '');
  if (draft.institutional?.note) {
    L.push('## Where the funds went last week', '', draft.institutional.note, '');
    for (const b of (draft.institutional.buying || []).filter((x) => /^[A-Z]{1,5}$/.test(x.ticker)).slice(0, 6)) {
      L.push(`- ${b.ticker}: bought by ${b.fundCount} active funds${b.flags?.length ? ` (${b.flags.join(', ')})` : ''}`);
    }
    L.push('');
  }
  L.push("## What I'd actually sell", '');
  for (const s of free) {
    L.push(`## $${s.ticker}`, '', s.michaelNote ? s.michaelNote : `[MICHAEL: 1-2 lines on why this one. Desk said: ${s.deskNote}]`, '', await card(s), '',
      `Desk grade ${s.grade}. Risk: ${s.whyNot}`, '');
  }
  L.push('## Passed, and why', '', 'The screen liked every one of these. The desk did not, and here is why.', '', '![Passed, and why](passed.png)', '');
  for (const s of passed) L.push(`- $${s.ticker}: ${s.whyNot}`);
  L.push('');
  if (shareId) L.push(`Every name, every grade and a live cushion on each put: [the Wheel Desk](${permalink}). One tap adds the whole list to your watchlist.`, '');
  L.push('The screens behind this run on [TraderMatrix](https://www.tradermatrix.pro/?ref=MPHINANCE) (my referral link). Walkthroughs: [youtube.com/@TraderMatrixHQ](https://www.youtube.com/@TraderMatrixHQ).', '');
  L.push('<!--share-->', '', '<!--paywall-->', '');
  if (paid.length) {
    L.push('## The rest of the desk', '');
    for (const s of paid) {
      L.push(`## $${s.ticker} · ${s.verdict === 'selling' ? 'Selling' : 'Watching'}`, '', s.michaelNote || `[MICHAEL: optional line. Desk said: ${s.deskNote}]`, '', await card(s), '', `Risk: ${s.whyNot}`, '');
    }
  }
  L.push('## Management rules', '', '- Close at 50% of max profit. Do not ride it to expiry.',
    '- Tested (delta past about 0.40) with 7+ days left: roll down and out for a net credit.',
    '- No credit available: take the shares. The strike was the stop.', '');
  L.push('## If assigned', '');
  for (const s of [...free, ...paid]) if (s.assignment) L.push(`- $${s.ticker}: ${s.assignment}`);
  L.push('', '[MICHAEL: optional trade-rule block, only if you are taking one. Sign off the numbers first.]', '');
  L.push('*Education, not advice. Check the live chain and use limit orders.*', '', '~ Michael', '');
  await writeFile(join(ws, 'post.md'), L.join('\n'));

  for (const [inp, out] of figs) {
    try {
      execFileSync('node', [FIGURE, '--in', inp, '--out', out, '--html', '--width', '640'], { stdio: 'pipe', timeout: 120000 });
    } catch (e) {
      console.error(`figure failed ${inp}: ${String(e.stderr || e.message).slice(0, 200)}`);
    }
  }
  console.log(JSON.stringify({ workspace: ws, post: join(ws, 'post.md'), permalink, free: free.map((s) => s.ticker), paid: paid.map((s) => s.ticker), passed: passed.length }, null, 1));
}

const pct = (a, b) => (a == null || !b ? '-' : (((a - b) / b) * 100).toFixed(1));
const esc = (s) => String(s ?? '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c]);
// Fuel from the packet: the screen's own #1 and what the desk did with it. Only
// emitted when true, so a fuel bullet can never be a made-up contrast.
// Hero from the mascot library (docs/substack/README.md). October = the pink BCA editions.
async function makeHero(ws, date, n) {
  const pink = process.env.DESK_PINK === '1' || argv.includes('--pink') || date.slice(5, 7) === '10';
  const pose = (opt('pose') || 'data_detective').replace(/^pink_/, '');
  try {
    execFileSync('python3', [join(ROOT, 'scripts/generate_hero.py'), '--pose', `${pink ? 'pink_' : ''}${pose}`,
      '--chalk', `${n.total} screened. ${n.selling} sold. ${n.passed} passed.`, '--out', join(ws, 'hero.png')], { stdio: 'pipe', timeout: 180000, cwd: ROOT });
    return true;
  } catch (e) {
    console.error(`hero failed: ${String(e.stderr || e.message).slice(0, 200)}`);
    return false;
  }
}

function screenFuel(date, setups) {
  try {
    const packet = JSON.parse(require_(join(ROOT, 'data', 'wheel-desk', date, 'packet.json')));
    const top = [...packet.csp].sort((a, b) => (b.screen?.score ?? 0) - (a.screen?.score ?? 0))[0];
    const v = setups.find((s) => s.ticker === top?.ticker)?.verdict;
    return top && v ? [`- the screen's #1 score was ${top.ticker} (${top.screen.score}); the desk has it ${v}`] : [];
  } catch { return []; }
}

main().catch((e) => { console.error(e.message || e); process.exit(1); });
