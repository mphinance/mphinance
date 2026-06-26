#!/usr/bin/env python3
"""
Track Record Builder  -  build.py

Reads a single hand-maintained CSV of options/futures trades and regenerates a
self-contained static HTML dashboard (equity curve, KPIs, per-strategy
breakdown, sortable trades table, open positions).

Usage:
    python build.py                      # uses data/trades_seed.csv -> dashboard.html
    python build.py data/my_trades.csv   # custom input
    python build.py in.csv out.html      # custom input + output

Dependencies: Python 3.8+ standard library only. pandas is used if present but
is NOT required (the script degrades gracefully to the csv module).

Built by Michael (Momentum Phinance) as a free gift + Automation Architect
case study. Data seeded from Ryan LePiane's public weekly recaps.
"""

import csv
import json
import sys
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------
# 1. INGEST
# ----------------------------------------------------------------------------
def load_rows(path):
    """Load trade rows as a list of dicts. Prefers pandas, falls back to csv."""
    try:
        import pandas as pd  # noqa
        df = pd.read_csv(path, dtype=str).fillna("")
        return [dict(r) for _, r in df.iterrows()]
    except Exception:
        with open(path, newline="", encoding="utf-8") as f:
            return [dict(r) for r in csv.DictReader(f)]


def num(v):
    """Parse a possibly-empty/commas/parens money string to float or None."""
    if v is None:
        return None
    s = str(v).strip().replace("$", "").replace(",", "")
    if s == "":
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


def clean(rows):
    """Split rows into closed (has realized_pl) and open (no realized_pl)."""
    closed, openp = [], []
    for r in rows:
        # ignore template example rows
        note = (r.get("notes") or "").upper()
        if "EXAMPLE" in note or "DELETE ME" in note:
            continue
        pl = num(r.get("realized_pl"))
        rec = {
            "date_opened": (r.get("date_opened") or "").strip(),
            "date_closed": (r.get("date_closed") or "").strip(),
            "ticker": (r.get("ticker") or "").strip(),
            "strategy": (r.get("strategy") or "Uncategorized").strip(),
            "type": (r.get("debit_or_credit") or "").strip().lower(),
            "entry": num(r.get("entry_price")),
            "exit": num(r.get("exit_price")),
            "max_profit": num(r.get("max_profit")),
            "max_loss": num(r.get("max_loss")),
            "breakeven": (r.get("breakeven") or "").strip(),
            "bp_used": num(r.get("bp_used")),
            "pl": pl,
            "notes": (r.get("notes") or "").strip(),
        }
        if pl is None:
            openp.append(rec)
        else:
            closed.append(rec)
    return closed, openp


# ----------------------------------------------------------------------------
# 2. COMPUTE
# ----------------------------------------------------------------------------
def compute(closed):
    closed = sorted(closed, key=lambda r: r["date_closed"] or "9999")
    pls = [r["pl"] for r in closed]
    wins = [p for p in pls if p > 0]
    losses = [p for p in pls if p < 0]
    total = round(sum(pls), 2)
    gross_win = round(sum(wins), 2)
    gross_loss = round(sum(losses), 2)
    n = len(pls)

    # equity curve (cumulative by close date)
    eq, run = [], 0.0
    for r in closed:
        run += r["pl"]
        eq.append({"date": r["date_closed"], "equity": round(run, 2),
                   "ticker": r["ticker"], "pl": r["pl"]})

    # per-strategy
    strat = {}
    for r in closed:
        s = strat.setdefault(r["strategy"], {"n": 0, "w": 0, "total": 0.0})
        s["n"] += 1
        s["w"] += 1 if r["pl"] > 0 else 0
        s["total"] += r["pl"]
    strat_rows = []
    for name, s in strat.items():
        strat_rows.append({
            "strategy": name,
            "count": s["n"],
            "wins": s["w"],
            "win_rate": round(100 * s["w"] / s["n"], 1) if s["n"] else 0,
            "total": round(s["total"], 2),
        })
    strat_rows.sort(key=lambda x: x["total"], reverse=True)

    best = max(closed, key=lambda r: r["pl"]) if closed else None
    worst = min(closed, key=lambda r: r["pl"]) if closed else None

    return {
        "total": total,
        "n": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(100 * len(wins) / n, 1) if n else 0,
        "avg_win": round(gross_win / len(wins), 2) if wins else 0,
        "avg_loss": round(gross_loss / len(losses), 2) if losses else 0,
        "gross_win": gross_win,
        "gross_loss": gross_loss,
        "profit_factor": round(gross_win / -gross_loss, 2) if gross_loss else None,
        "equity": eq,
        "strategies": strat_rows,
        "best": best,
        "worst": worst,
        "first_date": closed[0]["date_closed"] if closed else "",
        "last_date": closed[-1]["date_closed"] if closed else "",
        "trades": closed,
    }


# ----------------------------------------------------------------------------
# 3. RENDER
# ----------------------------------------------------------------------------
def money(v, sign=False):
    if v is None:
        return "&mdash;"
    s = "+" if (sign and v > 0) else ""
    return f"{s}${v:,.2f}".replace("$-", "-$")


def fmt_book_money(v):
    """Book cells: int dollars with commas, the infinity glyph, or blank."""
    if v in (None, ""):
        return ""
    if str(v).lower() in ("inf", "infinity", "∞"):
        return "&infin;"
    try:
        return f"{float(v):,.0f}"
    except (ValueError, TypeError):
        return str(v)


def render(m, openp, out_path, book=None, summary=None):
    payload = {
        "equity": m["equity"],
        "strategies": m["strategies"],
        "trades": [
            {"do": t["date_opened"], "dc": t["date_closed"], "tk": t["ticker"],
             "st": t["strategy"], "ty": t["type"], "pl": t["pl"], "nt": t["notes"]}
            for t in m["trades"]
        ],
    }
    data_json = json.dumps(payload)

    def kpi(label, value, cls=""):
        return f'<div class="kpi"><div class="kpi-v {cls}">{value}</div><div class="kpi-l">{label}</div></div>'

    pf = m["profit_factor"]
    kpis = "".join([
        kpi("Total Realized P/L", money(m["total"], sign=True),
            "pos" if m["total"] >= 0 else "neg"),
        kpi("Win Rate", f'{m["win_rate"]}%'),
        kpi("Profit Factor", f"{pf}" if pf is not None else "&mdash;"),
        kpi("Closed Trades", m["n"]),
        kpi("Avg Win", money(m["avg_win"]), "pos"),
        kpi("Avg Loss", money(m["avg_loss"]), "neg"),
        kpi("Best Trade",
            f'{money(m["best"]["pl"], sign=True)}<span class="sub">{m["best"]["ticker"]}</span>' if m["best"] else "&mdash;",
            "pos"),
        kpi("Worst Trade",
            f'{money(m["worst"]["pl"], sign=True)}<span class="sub">{m["worst"]["ticker"]}</span>' if m["worst"] else "&mdash;",
            "neg"),
    ])

    # strategy table
    strat_tr = ""
    for s in m["strategies"]:
        cls = "pos" if s["total"] >= 0 else "neg"
        strat_tr += (f'<tr><td>{s["strategy"]}</td><td class="r">{s["count"]}</td>'
                     f'<td class="r">{s["win_rate"]}%</td>'
                     f'<td class="r {cls}">{money(s["total"], sign=True)}</td></tr>')

    # ---- Live Book & Risk panel (mirrors Ryan's own spreadsheet) -----------
    if book:
        book_tr = ""
        for o in book:
            def pill(val, kind):
                v = (o.get(val) or "").strip()
                if not v:
                    return "&mdash;"
                klass = ""
                if v.lower().startswith("core"):
                    klass = "core"
                elif v.lower().startswith("supp"):
                    klass = "supp"
                elif v.lower().startswith("def"):
                    klass = "defr"
                elif v.lower().startswith("undef"):
                    klass = "undefr"
                return f'<span class="bpill {klass}">{v}</span>'
            book_tr += (
                f'<tr><td class="desc">{o.get("trade_description","")}</td>'
                f'<td class="r pos">{fmt_book_money(o.get("credit_rcvd"))}</td>'
                f'<td class="r neg">{fmt_book_money(o.get("debit_paid"))}</td>'
                f'<td class="r">{fmt_book_money(o.get("max_profit"))}</td>'
                f'<td class="r">{fmt_book_money(o.get("max_loss"))}</td>'
                f'<td class="r">{fmt_book_money(o.get("bp_usd"))}</td>'
                f'<td class="r">{(o.get("bp_pct") or "")}{"%" if o.get("bp_pct") else ""}</td>'
                f'<td>{pill("position_type","")}</td>'
                f'<td>{pill("risk_type","")}</td>'
                f'<td class="r">{o.get("date_opened","")}</td></tr>')

        summ = summary or {}
        pm = summ.get("position_mix", {})
        bp = summ.get("buying_power", {})

        def gauge(label, pct):
            try:
                p = float(pct)
            except (TypeError, ValueError):
                p = 0
            return (f'<div class="g-row"><span>{label}</span>'
                    f'<span class="g-val">{pct}%</span></div>'
                    f'<div class="g-bar"><i style="width:{min(p,100)}%"></i></div>')

        def mixrow(label, pct):
            return (f'<div class="mix-row"><span>{label}</span>'
                    f'<b>{pct}%</b></div>')

        summary_card = ""
        if summ:
            summary_card = f"""
      <aside class="summary">
        <h3>Portfolio Summary</h3>
        <div class="s-label">Position Mix</div>
        {mixrow("Core", pm.get("core_pct","&mdash;"))}
        {mixrow("Supplemental", pm.get("supplemental_pct","&mdash;"))}
        <div class="mix-gap"></div>
        {mixrow("Undefined", pm.get("undefined_pct","&mdash;"))}
        {mixrow("Defined", pm.get("defined_pct","&mdash;"))}
        <div class="s-label">Buying Power</div>
        {gauge("BP Target", bp.get("bp_target_pct","&mdash;"))}
        {gauge("BP Usage", bp.get("bp_usage_pct","&mdash;"))}
        {gauge("Trading Usage", bp.get("trading_usage_pct","&mdash;"))}
        {gauge("Stock Usage", bp.get("stock_usage_pct","&mdash;"))}
      </aside>"""

        open_section = f"""
  <section class="card srclabel" data-src="SOURCE 2 &middot; LIVE OPEN BOOK (from spreadsheet OCR)">
    <h2>Live Book &amp; Risk <span class="muted">/ {len(book)} open positions &mdash; an upgraded, auto-filled mirror of Ryan's own sheet</span></h2>
    <div class="book-wrap">
      <div class="scroll book-scroll"><table class="book">
        <thead><tr>
          <th>Trade Description</th><th class="r">Credit Rcv'd</th><th class="r">Debit Paid</th>
          <th class="r">Max Profit</th><th class="r">Max Loss</th><th class="r">BP $</th>
          <th class="r">BP %</th><th>Position</th><th>Risk</th><th class="r">Opened</th>
        </tr></thead>
        <tbody>{book_tr}</tbody>
      </table></div>
      {summary_card}
    </div>
    <p class="privacy">&#128274; In the browser version, this is OCR'd from your tastytrade screenshots entirely on your device &mdash; your screenshots never leave your computer and no broker login is required. Risk Type is auto-derived (long options &amp; spreads = Defined; naked shorts &amp; long futures = Undefined) and stays editable; Position Type (Core/Supp) is your call.</p>
  </section>"""
    elif openp:
        open_tr = ""
        for o in openp:
            mp = money(o["max_profit"]) if o["max_profit"] is not None else "&mdash;"
            ml = money(o["max_loss"]) if o["max_loss"] is not None else "&mdash;"
            bpv = money(o["bp_used"]) if o["bp_used"] is not None else "&mdash;"
            open_tr += (f'<tr><td>{o["date_opened"]}</td><td class="tk">{o["ticker"]}</td>'
                        f'<td>{o["strategy"]}</td><td>{o["type"]}</td>'
                        f'<td class="r">{mp}</td><td class="r neg">{ml}</td>'
                        f'<td class="r">{bpv}</td><td class="nt">{o["notes"]}</td></tr>')
        open_section = f"""
  <section class="card">
    <h2>Open Positions <span class="muted">/ {len(openp)} disclosed in prose</span></h2>
    <div class="scroll"><table>
      <thead><tr><th>Opened</th><th>Ticker</th><th>Strategy</th><th>Type</th>
        <th class="r">Max Profit</th><th class="r">Max Loss</th><th class="r">BP Used</th><th>Notes</th></tr></thead>
      <tbody>{open_tr}</tbody>
    </table></div>
  </section>"""
    else:
        open_section = ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LP Options Academy &mdash; Track Record</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg:#0b0f17; --panel:#121826; --panel2:#0e1421; --line:#1f2a3d;
    --ink:#e8edf6; --mut:#8a97ad; --pos:#22d29a; --neg:#ff5d6c;
    --accent:#5b8cff; --accent2:#9b6bff;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background-image:radial-gradient(900px 400px at 12% -8%, rgba(91,140,255,.12), transparent 60%),
      radial-gradient(800px 380px at 92% -10%, rgba(155,107,255,.10), transparent 60%); }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:34px 22px 70px; }}
  header.hero {{ display:flex; justify-content:space-between; align-items:flex-end;
    flex-wrap:wrap; gap:14px; margin-bottom:24px; }}
  .hero h1 {{ font-size:25px; margin:0 0 4px; letter-spacing:-.4px; }}
  .hero .who {{ color:var(--accent); font-weight:600; }}
  .hero p {{ margin:0; color:var(--mut); font-size:13.5px; }}
  .badge {{ font-size:11.5px; color:var(--mut); border:1px solid var(--line);
    padding:7px 12px; border-radius:999px; background:var(--panel); }}
  .badge b {{ color:var(--ink); }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:22px; }}
  .kpi {{ background:linear-gradient(180deg,var(--panel),var(--panel2));
    border:1px solid var(--line); border-radius:14px; padding:15px 16px; }}
  .kpi-v {{ font-size:23px; font-weight:700; letter-spacing:-.5px; }}
  .kpi-v .sub {{ display:block; font-size:11px; color:var(--mut); font-weight:600; margin-top:2px; letter-spacing:0; }}
  .kpi-l {{ color:var(--mut); font-size:12px; margin-top:5px; text-transform:uppercase; letter-spacing:.5px; }}
  .pos {{ color:var(--pos); }} .neg {{ color:var(--neg); }}
  .card {{ background:linear-gradient(180deg,var(--panel),var(--panel2));
    border:1px solid var(--line); border-radius:16px; padding:20px 20px 22px; margin-bottom:20px; }}
  .card h2 {{ font-size:15px; margin:0 0 14px; letter-spacing:.2px; }}
  .card h2 .muted, .muted {{ color:var(--mut); font-weight:400; font-size:12.5px; }}
  .grid2 {{ display:grid; grid-template-columns:1.4fr 1fr; gap:20px; }}
  canvas {{ max-width:100%; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th,td {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }}
  th {{ color:var(--mut); font-weight:600; font-size:11.5px; text-transform:uppercase;
    letter-spacing:.4px; cursor:pointer; user-select:none; position:sticky; top:0; background:var(--panel); }}
  th.r,td.r {{ text-align:right; }}
  td.tk {{ font-weight:700; }}
  td.nt {{ white-space:normal; color:var(--mut); min-width:240px; }}
  tbody tr:hover {{ background:rgba(91,140,255,.06); }}
  .scroll {{ max-height:520px; overflow:auto; border-radius:10px; }}
  .pill {{ font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--line); }}
  .pill.credit {{ color:var(--pos); }} .pill.debit {{ color:var(--accent); }}
  /* source ribbons so the two data sources are unmistakable */
  .srclabel {{ position:relative; }}
  .srclabel::before, .card.track::before {{ content:attr(data-src); position:absolute; top:-9px; left:16px;
    font-size:10px; letter-spacing:.7px; font-weight:700; color:#0b0f17;
    background:var(--accent2); padding:2px 9px; border-radius:6px; }}
  .card.track::before {{ background:var(--accent); }}
  /* Live Book panel */
  .book-wrap {{ display:grid; grid-template-columns:1fr 190px; gap:14px; align-items:start; }}
  table.book th, table.book td {{ padding:5px 6px; font-size:11.5px; }}
  table.book td.desc {{ font-weight:600; white-space:normal; min-width:150px; max-width:210px; line-height:1.25; }}
  table.book .bpill {{ padding:1px 7px; font-size:10px; }}
  .bpill {{ font-size:10.5px; padding:2px 9px; border-radius:999px; border:1px solid var(--line); color:var(--mut); }}
  .bpill.core {{ color:#7fb0ff; border-color:#2c4a7a; }}
  .bpill.supp {{ color:#c4a6ff; border-color:#4a3a7a; }}
  .bpill.defr {{ color:var(--pos); border-color:#1f6e57; }}
  .bpill.undefr {{ color:#ffb86b; border-color:#7a5a2c; }}
  .summary {{ background:var(--panel2); border:1px solid var(--line); border-radius:12px; padding:15px 16px; }}
  .summary h3 {{ font-size:13px; margin:0 0 12px; }}
  .s-label {{ color:var(--mut); font-size:10.5px; text-transform:uppercase; letter-spacing:.6px; margin:14px 0 7px; }}
  .mix-row {{ display:flex; justify-content:space-between; font-size:12.5px; padding:3px 0; }}
  .mix-row b {{ font-weight:700; }}
  .mix-gap {{ height:6px; }}
  .g-row {{ display:flex; justify-content:space-between; font-size:12px; margin-top:9px; }}
  .g-val {{ color:var(--ink); font-weight:600; }}
  .g-bar {{ height:6px; background:#0b1119; border-radius:6px; overflow:hidden; margin-top:3px; }}
  .g-bar i {{ display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); }}
  .privacy {{ color:var(--mut); font-size:11.5px; margin:14px 0 0; line-height:1.6;
    border-top:1px dashed var(--line); padding-top:12px; }}
  footer {{ color:var(--mut); font-size:12px; margin-top:26px; line-height:1.7; }}
  footer a {{ color:var(--accent); text-decoration:none; }}
  @media (max-width:820px) {{ .kpis{{grid-template-columns:repeat(2,1fr);}} .grid2{{grid-template-columns:1fr;}}
    .book-wrap{{grid-template-columns:1fr;}} }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div>
      <h1><span class="who">LP Options Academy</span> &mdash; Track Record</h1>
      <p>Cumulative realized performance &middot; {m["first_date"]} &rarr; {m["last_date"]} &middot; built from public weekly recaps</p>
    </div>
    <div class="badge">Realized P/L &nbsp;<b class="{ 'pos' if m['total']>=0 else 'neg' }">{money(m['total'], sign=True)}</b> &nbsp;&middot;&nbsp; <b>{m['n']}</b> closed trades</div>
  </header>

  <div class="kpis">{kpis}</div>

  <section class="card track" data-src="SOURCE 1 &middot; REALIZED TRACK RECORD (from recap prose)">
    <h2>Cumulative Realized P/L <span class="muted">/ equity curve, each step = one closed trade</span></h2>
    <canvas id="equity" height="120"></canvas>
  </section>

  <div class="grid2">
    <section class="card">
      <h2>Performance by Strategy</h2>
      <canvas id="strat" height="200"></canvas>
    </section>
    <section class="card">
      <h2>Strategy Detail</h2>
      <div class="scroll"><table>
        <thead><tr><th>Strategy</th><th class="r">#</th><th class="r">Win%</th><th class="r">Total P/L</th></tr></thead>
        <tbody>{strat_tr}</tbody>
      </table></div>
    </section>
  </div>

  <section class="card">
    <h2>Closed Trades <span class="muted">/ click a header to sort</span></h2>
    <div class="scroll"><table id="trades">
      <thead><tr>
        <th data-k="dc">Closed</th><th data-k="do">Opened</th><th data-k="tk">Ticker</th>
        <th data-k="st">Strategy</th><th data-k="ty">Type</th>
        <th class="r" data-k="pl">Realized P/L</th><th data-k="nt">Notes</th>
      </tr></thead>
      <tbody></tbody>
    </table></div>
  </section>
{open_section}

  <footer>
    Track Record Builder &mdash; a free tool by <a href="https://momentumphinance.substack.com">Michael / Momentum Phinance</a>.
    Data extracted from the public <a href="https://ryanlepiane.substack.com">LP Options Academy</a> weekly recaps by
    <b>Ryan LePiane</b> (go subscribe). Trade-level P/L reconciles exactly to Ryan's reported weekly "Closed Profit/(Loss)" totals across every week.
    Educational only; not investment advice. Past performance does not guarantee future results.
  </footer>
</div>

<script>
const DATA = {data_json};
const POS = '#22d29a', NEG = '#ff5d6c', GRID = 'rgba(255,255,255,.06)', MUT = '#8a97ad';
Chart.defaults.color = MUT;
Chart.defaults.font.family = "-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";

// --- equity curve ---
(function(){{
  const eq = DATA.equity;
  const ctx = document.getElementById('equity');
  const g = ctx.getContext('2d').createLinearGradient(0,0,0,260);
  g.addColorStop(0,'rgba(91,140,255,.34)'); g.addColorStop(1,'rgba(91,140,255,0)');
  new Chart(ctx, {{
    type:'line',
    data:{{ labels: eq.map((d,i)=>d.date),
      datasets:[{{ data: eq.map(d=>d.equity), borderColor:'#5b8cff', borderWidth:2,
        backgroundColor:g, fill:true, tension:.25, pointRadius:2, pointHoverRadius:5,
        pointBackgroundColor:'#5b8cff' }}] }},
    options:{{ responsive:true, plugins:{{ legend:{{display:false}},
      tooltip:{{ callbacks:{{ title:(it)=>'Closed '+eq[it[0].dataIndex].date,
        label:(it)=>{{const d=eq[it.dataIndex]; return ['Equity: $'+d.equity.toLocaleString(),
          d.ticker+'  '+(d.pl>=0?'+':'')+'$'+d.pl.toLocaleString()];}} }} }} }},
      scales:{{ x:{{ grid:{{color:GRID}}, ticks:{{maxTicksLimit:12, maxRotation:0}} }},
        y:{{ grid:{{color:GRID}}, ticks:{{callback:v=>'$'+v.toLocaleString()}} }} }} }}
  }});
}})();

// --- strategy bar ---
(function(){{
  const s = DATA.strategies;
  new Chart(document.getElementById('strat'), {{
    type:'bar',
    data:{{ labels:s.map(x=>x.strategy),
      datasets:[{{ data:s.map(x=>x.total),
        backgroundColor:s.map(x=>x.total>=0?'rgba(34,210,154,.85)':'rgba(255,93,108,.85)'),
        borderRadius:5 }}] }},
    options:{{ indexAxis:'y', responsive:true, plugins:{{ legend:{{display:false}},
      tooltip:{{ callbacks:{{ label:(it)=>{{const x=s[it.dataIndex];
        return [(x.total>=0?'+':'')+'$'+x.total.toLocaleString(), x.count+' trades  '+x.win_rate+'% win'];}} }} }} }},
      scales:{{ x:{{ grid:{{color:GRID}}, ticks:{{callback:v=>'$'+v.toLocaleString()}} }},
        y:{{ grid:{{display:false}}, ticks:{{font:{{size:11}}}} }} }} }}
  }});
}})();

// --- sortable trades table ---
(function(){{
  const tb = document.querySelector('#trades tbody');
  let rows = DATA.trades.slice(), dir = {{}};
  function money(v){{const s=v>=0?'+':'';return s+'$'+Math.abs(v).toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}});}}
  function draw(){{
    tb.innerHTML = rows.map(t=>{{
      const cls = t.pl>=0?'pos':'neg';
      const ty = t.ty?('<span class="pill '+t.ty+'">'+t.ty+'</span>'):'';
      return '<tr><td>'+t.dc+'</td><td>'+(t.do||'&mdash;')+'</td><td class="tk">'+t.tk+'</td>'+
        '<td>'+t.st+'</td><td>'+ty+'</td><td class="r '+cls+'">'+money(t.pl)+'</td>'+
        '<td class="nt">'+(t.nt||'')+'</td></tr>';
    }}).join('');
  }}
  document.querySelectorAll('#trades th').forEach(th=>{{
    th.addEventListener('click',()=>{{
      const k=th.dataset.k; dir[k]=!dir[k]; const sgn=dir[k]?1:-1;
      rows.sort((a,b)=>{{const x=a[k],y=b[k];
        if(typeof x==='number') return (x-y)*sgn;
        return String(x).localeCompare(String(y))*sgn;}});
      draw();
    }});
  }});
  // default: newest close first
  rows.sort((a,b)=>String(b.dc).localeCompare(String(a.dc)));
  draw();
}})();
</script>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


# ----------------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    in_path = args[0] if len(args) >= 1 else os.path.join(HERE, "data", "trades_seed.csv")
    out_path = args[1] if len(args) >= 2 else os.path.join(HERE, "dashboard.html")
    if not os.path.isabs(in_path):
        in_path = os.path.join(os.getcwd(), in_path)
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.getcwd(), out_path)

    rows = load_rows(in_path)
    closed, openp = clean(rows)
    m = compute(closed)

    # Optional second source: the live open-book / risk panel (spreadsheet OCR)
    book, summary = None, None
    book_path = os.path.join(HERE, "data", "open_book.csv")
    summ_path = os.path.join(HERE, "data", "portfolio_summary.json")
    if os.path.exists(book_path):
        book = load_rows(book_path)
    if os.path.exists(summ_path):
        with open(summ_path) as f:
            summary = json.load(f)

    render(m, openp, out_path, book=book, summary=summary)

    print(f"Read    : {in_path}")
    print(f"Closed  : {m['n']} trades   Open(prose): {len(openp)}   "
          f"Live book: {len(book) if book else 0} positions")
    print(f"Realized: ${m['total']:,.2f}   Win rate: {m['win_rate']}%   "
          f"Profit factor: {m['profit_factor']}")
    print(f"Wrote   : {out_path}")


if __name__ == "__main__":
    main()
