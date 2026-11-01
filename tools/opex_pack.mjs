// Opex pack: one PDF per options week. Title page "Opex MM/DD" + one stock per page.
//
//   node tools/opex_pack.mjs data/opex/2026-11-06/pack.json            -> opex-2026-11-06.pdf (all names)
//   node tools/opex_pack.mjs data/opex/2026-11-06/pack.json --free     -> opex-2026-11-06-free.pdf (free names only)
//
// pack.json lives next to the chart PNGs (<TICKER>.png). Dark theme, letter landscape-ish 11x8.5.
import { chromium } from "/home/mph/.claude/skills/mph-figure/node_modules/playwright/index.mjs";
import fs from "node:fs";
import path from "node:path";

const file = process.argv[2];
const free = process.argv.includes("--free");
const dir = path.dirname(path.resolve(file));
const p = JSON.parse(fs.readFileSync(file, "utf8"));
const stocks = p.stocks.filter((s) => !free || s.free);
// dates: [when, text, freeText?]. freeText null = paid-only line, dropped from the free edition.
const dates = p.dates.map(([d, e, f]) => [d, free && f !== undefined ? f : e]).filter(([, e]) => e);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const img = (f) => `data:image/png;base64,${fs.readFileSync(path.join(dir, f)).toString("base64")}`;
const scoreColor = (n) => (n >= 6 ? "#2FD18B" : n >= 5 ? "#E8B75A" : "#FF8A4C");

const css = `
@page { size: 11in 8.5in; margin: 0 }
* { box-sizing: border-box }
body { margin: 0; background: #0b0e14; color: #d9d6cf; font-family: 'DejaVu Sans', sans-serif }
.page { width: 11in; height: 8.5in; padding: .45in .55in; page-break-after: always; position: relative; overflow: hidden }
.page:last-child { page-break-after: auto }
.foot { position: absolute; bottom: .25in; left: .55in; right: .55in; font-size: 10px; color: #6b7080; display: flex; justify-content: space-between }
.gold { color: #E8B75A } .green { color: #2FD18B } .red { color: #FF5D6C } .blue { color: #6FA8FF }
/* title */
.cover { background: linear-gradient(90deg, #0b0e14 48%, rgba(11,14,20,.2)), var(--bg) right/cover no-repeat }
.kicker { letter-spacing: 6px; font-weight: 700; color: #E8B75A; font-size: 15px; margin-top: .4in }
.big { font-size: 86px; font-weight: 800; color: #f2efe8; line-height: 1; margin: 18px 0 10px }
.sub { font-size: 20px; color: #c8c6c0; max-width: 5.6in }
.read { margin-top: 26px; max-width: 5.4in; font-size: 14px; line-height: 1.55 }
.read li { margin-bottom: 6px }
.cols { display: flex; gap: 28px; margin-top: 22px; max-width: 6in }
.box { background: rgba(255,255,255,.04); border: 1px solid #232a36; border-radius: 10px; padding: 12px 16px; font-size: 12.5px; line-height: 1.6; flex: 1 }
.box b { color: #f2efe8 }
.roster { margin-top: 18px; font-size: 14px; letter-spacing: 1px; color: #8B90A0 }
.roster span { color: #f2efe8; font-weight: 700; margin-right: 12px }
/* stock */
.hdr { display: flex; align-items: baseline; gap: 16px }
.tk { font-size: 44px; font-weight: 800; color: #f2efe8 }
.nm { font-size: 18px; color: #8B90A0 }
.tag { margin-left: auto; font-size: 15px; color: #E8B75A; font-weight: 700 }
.pills { display: flex; gap: 10px; margin: 8px 0 10px }
.pill { border: 1px solid #2a3140; border-radius: 99px; padding: 3px 12px; font-size: 13px; font-weight: 700 }
.grid { display: grid; grid-template-columns: 1.7fr 1fr; gap: 18px; align-items: start }
.lower { display: grid; grid-template-columns: 1fr 1fr 0.9fr; gap: 22px; margin-top: 10px }
.chart { width: 100%; border-radius: 8px; border: 1px solid #1c2029 }
.plan { background: rgba(232,183,90,.07); border: 1px solid rgba(232,183,90,.35); border-left: 4px solid #E8B75A; border-radius: 10px; padding: 14px 16px; font-size: 14.5px; line-height: 1.6 }
.plan div { margin-bottom: 9px }
.plan div { margin-bottom: 6px }
.plan b { color: #f2efe8 }
.list { margin: 6px 0 0; padding-left: 18px; font-size: 14px; line-height: 1.5 }
.list li { margin-bottom: 4px }
.h { font-weight: 800; font-size: 14px; letter-spacing: 1px }
a { color: #6FA8FF }
`;

const cover = `<section class="page cover" style="--bg:url('${img("hero_bg.png")}')">
  <div class="kicker">THE OPEX PACK${free ? " · FREE EDITION" : ""}</div>
  <div class="big">${esc(p.title)}</div>
  <div class="sub">${esc(p.subtitle)}</div>
  <ul class="read">${p.read.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
  <div class="cols">
    <div class="box"><b class="gold">KEY DATES</b><br>${dates.map(([d, e]) => `<b>${esc(d)}</b> ${esc(e)}`).join("<br>")}</div>
    <div class="box"><b class="gold">${free ? "FULL PACK" : "FOLLOW LIVE"}</b><br>${free ? `All ${p.stocks.length} names, the live watchlists and every trigger are for paid subs at <a href="https://mphinance.substack.com">mphinance.substack.com</a>` : p.links.map(([l, u]) => `<a href="${u}">${esc(l)}</a>`).join("<br>")}</div>
  </div>
  <div class="roster">${stocks.map((s) => `<span>${s.t}</span>`).join("")}</div>
  <div class="foot"><span>${esc(p.asof)}</span><span>Not financial advice. ~ Michael</span></div>
</section>`;

const page = (s, i) => `<section class="page">
  <div class="hdr"><span class="tk">${s.t}</span><span class="nm">${esc(s.name)}</span><span class="tag">${esc(s.tag)}</span></div>
  <div class="pills"><span class="pill" style="color:${scoreColor(s.score)}">${s.score}/10</span><span class="pill blue">${esc(s.size)}</span><span class="pill" style="color:#8B90A0">${esc(p.title)}</span></div>
  <div class="grid">
    <div><img class="chart" src="${img(s.t + ".png")}"></div>
    <div class="plan">
      <div><b class="green">TRIGGER</b><br>${esc(s.trigger)}</div>
      <div><b class="red">STOP</b><br>${esc(s.stop)}</div>
      <div><b class="green">TARGETS</b><br>${esc(s.targets)}</div>
      <div><b>HOW</b><br>${esc(s.how)}</div>
      ${s.deadline ? `<div><b class="gold">DEADLINE</b><br>${esc(s.deadline)}</div>` : ""}
    </div>
  </div>
  <div class="lower">
    <div><div class="h green">WHY IT'S HERE</div><ul class="list">${s.why.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>
    <div><div class="h red">WATCH</div><ul class="list">${s.watch.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>
    <div>${s.dd ? `<div class="h blue">DEEP DIVE</div><div style="font-size:13px;margin-top:6px;line-height:1.5"><a href="${s.dd}">${esc(s.dd.replace("https://www.", ""))}</a></div>` : ""}</div>
  </div>
  <div class="foot"><span>${esc(p.title)} · ${i + 2} of ${stocks.length + 1} · ${esc(p.asof)}</span><span>Not financial advice. ~ Michael</span></div>
</section>`;

const html = `<html><head><meta charset="utf-8"><style>${css}</style></head><body>${cover}${stocks.map(page).join("")}</body></html>`;
if (free) {
  // the free edition must never name a paid ticker, anywhere
  const paid = p.stocks.filter((s) => !s.free).map((s) => s.t).filter((t) => new RegExp(`\\b${t}\\b`).test(html.replace(/data:image[^"')]+/g, "")));
  for (const [, u] of p.links) if (html.includes(u)) { console.error(`free edition links a paid list: ${u}`); process.exit(1); }
  if (paid.length) { console.error(`free edition names paid tickers: ${paid.join(", ")}`); process.exit(1); }
}
const out = path.join(dir, `opex-${p.opex}${free ? "-free" : ""}.pdf`);
fs.writeFileSync(out.replace(".pdf", ".html"), html);
const b = await chromium.launch();
const pg = await b.newPage();
await pg.setContent(html, { waitUntil: "load" });
await pg.pdf({ path: out, width: "11in", height: "8.5in", printBackground: true });
await b.close();
console.log(out);
