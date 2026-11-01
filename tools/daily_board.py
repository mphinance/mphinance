#!/usr/bin/env python3
"""Daily Board: one PNG, every position x five buckets, one action per cell.

    python3 tools/daily_board.py data/daily-board/2026-11-02/spec.json   -> board.html + board.png beside it

The spec is hand-written (the decisions). This script does the math:
  close + ATR(14) off the last daily bar, the five bands, NLV, cash %, weighted beta.

Bands (per the 10/29 board): flat = +/- max(1.5%, 0.30 ATR); big = beyond +/- max(ATR, 3%).
Prices in the spec (qty/px/basis/marks) come from the broker; bars come from yfinance.
"""
import json, sys, html, warnings
from pathlib import Path
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")
BUCKETS = [("BIG DOWN", "#FF4D5E"), ("SMALL DOWN", "#B5525C"), ("FLAT", "#6B7080"),
           ("SMALL UP", "#3FA36B"), ("BIG UP", "#2FD18B")]


def bars(t):
    d = yf.download(t, period="1y", progress=False, auto_adjust=False)
    d.columns = [c[0] for c in d.columns]
    return d


def atr(d, n=14):
    h, l, c = d.High, d.Low, d.Close
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(n).mean().iloc[-1])


def fmt(x):
    return f"{x:,.2f}"


def bands(c, a):
    f, b = max(0.015 * c, 0.30 * a), max(a, 0.03 * c)
    lo2, lo1, hi1, hi2 = c - b, c - f, c + f, c + b
    return [f"&lt; {fmt(lo2)}", f"{fmt(lo2)} - {fmt(lo1)}", f"{fmt(lo1)} - {fmt(hi1)}",
            f"{fmt(hi1)} - {fmt(hi2)}", f"&gt; {fmt(hi2)}"]


def main(spec_path):
    spec_path = Path(spec_path)
    s = json.loads(spec_path.read_text())
    spy = bars("SPY").Close.pct_change()
    cache, beta = {}, {}
    for t in {x["t"] for x in s["stocks"]} | {o["under"] for o in s["options"]}:
        d = bars(t)
        cache[t] = (float(d.Close.iloc[-1]), atr(d), str(d.index[-1].date()))
        r = pd.concat([d.Close.pct_change(), spy], axis=1).dropna().tail(250)
        beta[t] = float(r.cov().iloc[0, 1] / r.iloc[:, 1].var())
    stock_val = sum(x["qty"] * x["px"] for x in s["stocks"])
    opt_val = sum(o["qty"] * 100 * o["mark"] for o in s["options"])
    nlv = stock_val + opt_val + s["cash"]
    wbeta = sum(x["qty"] * x["px"] * beta[x["t"]] for x in s["stocks"]) / nlv
    asof = {v[2] for v in cache.values()}
    if len(asof) != 1:
        sys.exit(f"bars disagree on the last date: {asof}")
    e = html.escape

    def cells(row, under):
        c, a, _ = cache[under]
        out = []
        for i, (rng, act) in enumerate(zip(bands(c, a), row["cells"])):
            tag = row.get("hl", {}).get(str(i))
            out.append(f'<div class="cell{" hl" if tag else ""}{" mute" if row.get("mute") else ""}">'
                       + (f'<span class="flag">{e(tag)}</span>' if tag else "")
                       + f'<div class="rng">{rng}</div><div class="act">{e(act)}</div></div>')
        return "".join(out)

    head = "".join(f'<div class="bh" style="--c:{c}">{n}</div>' for n, c in BUCKETS)
    rows = []
    for x in s["stocks"]:
        val = x["qty"] * x["px"]
        badge = f'<span class="badge">{e(x["badge"])}</span>' if x.get("badge") else ""
        extra = "".join(f'<div class="note">{e(n)}</div>' for n in x.get("notes", []))
        rows.append(f'<div class="lab{" mute" if x.get("mute") else ""}"><div class="tk">{x["t"]}{badge}</div>'
                    f'<div class="meta">{x["qty"]} sh &nbsp; ${val:,.0f} &nbsp; {val / nlv * 100:.1f}% of NLV</div>'
                    f'<div class="meta">basis {fmt(x["basis"])} &nbsp; close {fmt(x["px"])}</div>{extra}</div>'
                    + cells(x, x["t"]))
    orows = []
    for o in s["options"]:
        orows.append(f'<div class="olab"><b>{e(o["label"])}</b><br>{e(o["side"])} {o["qty"]}, paid ${o["paid"] * 100 * o["qty"]:.0f}'
                     f'<br>marks ${o["mark"] * 100 * o["qty"]:.0f}' + "".join(f"<br>{e(n)}" for n in o.get("notes", []))
                     + "</div>" + cells(o, o["under"]))
    paid = sum(o["paid"] * 100 * o["qty"] for o in s["options"])
    steps = "".join(f'<div class="step"><span class="num">{i + 1}</span><div><b>{e(t)}</b><br>{e(b)}</div></div>'
                    + ('<span class="arrow">&rarr;</span>' if i < len(s["steps"]) - 1 else "")
                    for i, (t, b) in enumerate(s["steps"]))
    rules = "".join(f'<div class="rule"><span class="rn">{i + 1}</span><div><b>{e(t)}</b><br>{e(b)}</div></div>'
                    for i, (t, b) in enumerate(s["rules"]))
    ctx = "<hr>".join(f"<p>{e(c)}</p>" for c in s["context"])
    stats = [("NLV", f"${nlv:,.0f}"), ("CASH", f"${s['cash']:,.0f} ({s['cash'] / nlv * 100:.1f}%)"),
             ("EQUITY", f"{(stock_val + opt_val) / nlv * 100:.1f}%"), ("BETA", f"{wbeta:.2f}"),
             ("POSITIONS", str(len(s["stocks"]) + len(s["options"]))), ("BUYING POWER", f"${s['buying_power']:,.0f}")]
    stat = "".join(f'<div class="stat"><span>{k}</span><b>{v}</b></div>' for k, v in stats)

    doc = f"""<html><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box }}
body {{ margin: 0; background: #0b0e14; color: #d9d6cf; font-family: 'DejaVu Sans', sans-serif; width: 1160px }}
.wrap {{ padding: 30px 26px 20px }}
.top {{ display: flex; justify-content: space-between; align-items: flex-start }}
h1 {{ font-size: 58px; letter-spacing: 6px; margin: 0; color: #eceae4; font-weight: 800 }}
.date {{ font-size: 22px; margin-top: 6px; color: #eceae4 }} .sub {{ color: #8B90A0; font-size: 14px; margin-top: 4px }}
.stats {{ display: grid; grid-template-columns: repeat(3, 128px); gap: 8px }}
.stat {{ background: #121722; border: 1px solid #232a36; border-radius: 8px; padding: 9px 11px }}
.stat span {{ display: block; font-size: 9px; letter-spacing: 1.5px; color: #8B90A0 }} .stat b {{ font-family: 'DejaVu Sans Mono'; font-size: 16px; color: #eceae4 }}
.panel {{ background: #0f131b; border: 1px solid #1f2633; border-radius: 10px; padding: 16px 14px; margin-top: 20px }}
.steps {{ display: flex; align-items: center; gap: 6px }}
.step {{ display: flex; gap: 10px; flex: 1; font-size: 11px; color: #9a9fae; line-height: 1.45 }}
.step b {{ color: #eceae4; letter-spacing: 2px; font-size: 13px }}
.num {{ flex: none; width: 28px; height: 28px; border: 2px solid #2FD18B; color: #2FD18B; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700 }}
.arrow {{ color: #E8B75A; font-size: 20px }}
.ph {{ display: flex; justify-content: space-between; align-items: baseline; margin: 0 4px 12px }}
.ph b {{ font-size: 17px; letter-spacing: 3px; color: #eceae4 }} .ph span {{ font-size: 11px; color: #8B90A0 }}
.grid {{ display: grid; grid-template-columns: 196px repeat(5, 1fr); gap: 8px }}
.bh {{ border-top: 3px solid var(--c); color: var(--c); text-align: center; font-weight: 700; letter-spacing: 2px; font-size: 12px; padding: 10px 0 4px }}
.lab {{ padding: 4px 4px 4px 4px }} .lab .tk {{ font-size: 25px; font-weight: 800; color: #eceae4; letter-spacing: 1px }}
.lab .meta {{ font-family: 'DejaVu Sans Mono'; font-size: 10px; color: #9a9fae; margin-top: 3px }}
.note {{ font-family: 'DejaVu Sans Mono'; font-size: 10px; color: #E8B75A; margin-top: 3px }}
.badge {{ font-size: 8px; letter-spacing: 1px; border: 1px solid #3a4150; color: #8B90A0; padding: 2px 5px; border-radius: 3px; margin-left: 8px; vertical-align: middle; font-weight: 700 }}
.mute .tk, .mute .rng {{ color: #7a7f8e !important }} .cell.mute .act {{ color: #6b7080 }}
.cell {{ position: relative; background: #121722; border: 1px solid #1f2633; border-radius: 7px; padding: 10px 10px; min-height: 92px }}
.cell.hl {{ border: 2px solid #E8B75A; background: #1c1a14 }}
.flag {{ position: absolute; top: -8px; right: 8px; background: #E8B75A; color: #111; font-size: 8px; font-weight: 800; letter-spacing: 1px; padding: 2px 5px; border-radius: 3px }}
.rng {{ font-family: 'DejaVu Sans Mono'; font-weight: 700; font-size: 14px; color: #eceae4 }}
.act {{ font-size: 10.5px; color: #a6abb8; margin-top: 6px; line-height: 1.4 }} .cell.hl .act {{ color: #eceae4 }}
.olab {{ font-family: 'DejaVu Sans Mono'; font-size: 10px; color: #a6abb8; padding: 4px; line-height: 1.5 }} .olab b {{ color: #eceae4; font-size: 11px }}
.bottom {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 14px; margin-top: 20px }}
.rule {{ display: flex; gap: 16px; background: #0f131b; border: 1px solid #1f2633; border-radius: 8px; padding: 12px 16px; margin-bottom: 9px; font-size: 11.5px; color: #9a9fae; line-height: 1.45 }}
.rule b {{ color: #eceae4; letter-spacing: 2px; font-size: 13px }} .rn {{ color: #E8B75A; font-size: 22px; font-weight: 800 }}
.ctx {{ background: #0f131b; border: 1px solid #1f2633; border-radius: 8px; padding: 18px 18px; font-size: 13px; color: #d9d6cf; line-height: 1.5 }}
.ctx h4 {{ margin: 0 0 10px; letter-spacing: 2px; font-size: 11px; color: #8B90A0 }} .ctx hr {{ border: 0; border-top: 1px solid #232a36; margin: 12px 0 }} .ctx p {{ margin: 0 }}
.foot {{ text-align: center; font-size: 10.5px; color: #8B90A0; margin-top: 12px }}
</style></head><body><div class="wrap">
<div class="top"><div><h1>DAILY BOARD</h1><div class="date">{e(s["title_date"])}</div><div class="sub">{e(s["subtitle"])}</div></div><div class="stats">{stat}</div></div>
<div class="panel steps">{steps}</div>
<div class="panel"><div class="ph"><b>THE BOARD MATRIX</b><span>Range is the price zone. Action sits below it.</span></div>
<div class="grid"><div></div>{head}{"".join(rows)}</div></div>
<div class="panel"><div class="ph"><b>THE OPTION LEGS</b><span>Keyed to the underlying's bucket. Net option premium at risk: ${paid:.0f}.</span></div>
<div class="grid"><div></div>{head}{"".join(orows)}</div></div>
<div class="bottom"><div>{rules}</div><div class="ctx"><h4>CONTEXT</h4>{ctx}</div></div>
<div class="foot">Levels measured off the {e(s["levels_from"])} close ({asof.pop()} bars). Recompute daily. Not financial advice.</div>
</div></body></html>"""
    out = spec_path.with_name("board.html")
    out.write_text(doc)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1160, "height": 800}, device_scale_factor=2)
        pg.set_content(doc, wait_until="load")
        pg.screenshot(path=str(spec_path.with_name("board.png")), full_page=True)
        b.close()
    print(json.dumps({"nlv": round(nlv, 2), "beta": round(wbeta, 2), "levels": {t: bands(*cache[t][:2]) for t in cache},
                      "beta_by": {t: round(v, 2) for t, v in beta.items()}}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
