#!/usr/bin/env python3
"""Daily Board: one PNG, every position x five buckets, one action per cell.

    python3 tools/daily_board.py data/daily-board/2026-11-02/spec.json   -> board.html + board.png beside it
    python3 tools/daily_board.py <spec> --theme dark                      -> the old dark terminal look

Default theme is "parchment" (sepia playbook, 11/03). Spec can pin one with "theme": "dark".

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
BUCKET_NAMES = ["BIG DOWN", "SMALL DOWN", "FLAT", "SMALL UP", "BIG UP"]

# Every color the board uses, per theme. CSS reads them as var(--name).
THEMES = {
    "dark": dict(
        buckets=["#FF4D5E", "#B5525C", "#6B7080", "#3FA36B", "#2FD18B"],
        page="#0b0e14", paper="#0b0e14", panel="#0f131b", card="#121722", line="#1f2633", line2="#232a36",
        ink="#eceae4", body="#d9d6cf", dim="#9a9fae", faint="#8B90A0", mute="#7a7f8e",
        accent="#E8B75A", accent_ink="#111", hl_bg="#1c1a14", go="#2FD18B",
        head="'DejaVu Sans', sans-serif", text="'DejaVu Sans', sans-serif", mono="'DejaVu Sans Mono', monospace",
        title="DAILY BOARD", h_case="uppercase", vignette="none", frame="none", radius="8px"),
    "parchment": dict(
        buckets=["#8F2D1A", "#A8613F", "#7A6A50", "#6E7F3A", "#3F5E2A"],
        page="#cdb48a", paper="radial-gradient(ellipse at 18% 8%, rgba(255,249,228,.6), transparent 55%), "
                            "radial-gradient(ellipse at 85% 95%, rgba(120,80,30,.22), transparent 60%), "
                            "radial-gradient(ellipse at 50% 45%, #f2e4c2 0%, #e9d5a8 68%, #dcc08c 100%)",
        panel="rgba(255,250,232,.32)", card="rgba(255,251,236,.55)", line="#b8996a", line2="#c9ad80",
        ink="#2b1d0e", body="#3a2a16", dim="#5e4a2e", faint="#7a6343", mute="#9a8768",
        accent="#8F2D1A", accent_ink="#f6ead0", hl_bg="rgba(143,45,26,.09)", go="#3F5E2A",
        head="'IM Fell English SC', 'Cormorant Garamond', serif", text="'Cormorant Garamond', Georgia, serif",
        mono="'Courier Prime', 'DejaVu Sans Mono', monospace",
        title="The Daily Playbook", h_case="none",
        vignette="inset 0 0 110px rgba(110,70,20,.45)", frame="1.5px solid #9c7c4d", radius="3px"),
}
FONTS = ('<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English+SC&family=IM+Fell+English:ital@0;1'
         '&family=Cormorant+Garamond:wght@500;600;700&family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">')


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


def main(spec_path, theme=None):
    spec_path = Path(spec_path)
    s = json.loads(spec_path.read_text())
    th = THEMES[theme or s.get("theme", "parchment")]
    parch = th["title"] != "DAILY BOARD"
    BUCKETS = list(zip(BUCKET_NAMES, th["buckets"]))
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
    sec = (lambda n, t: f'<span class="sn">{n}.</span> {t}') if parch else (lambda n, t: t.upper())
    ctx = "<hr>".join(f"<p>{e(c)}</p>" for c in s["context"])
    stats = [("NLV", f"${nlv:,.0f}"), ("CASH", f"${s['cash']:,.0f} ({s['cash'] / nlv * 100:.1f}%)"),
             ("EQUITY", f"{(stock_val + opt_val) / nlv * 100:.1f}%"), ("BETA", f"{wbeta:.2f}"),
             ("POSITIONS", str(len(s["stocks"]) + len(s["options"]))), ("BUYING POWER", f"${s['buying_power']:,.0f}")]
    stat = "".join(f'<div class="stat"><span>{k}</span><b>{v}</b></div>' for k, v in stats)

    doc = f"""<html><head><meta charset="utf-8">{FONTS if parch else ""}<style>
:root {{ {"; ".join(f"--{k.replace('_', '-')}: {v}" for k, v in th.items() if k not in ("buckets", "title"))} }}
* {{ box-sizing: border-box }}
body {{ margin: 0; background: var(--page); color: var(--body); font-family: var(--text); width: 1160px }}
.wrap {{ padding: {"22px" if parch else "0"} }}
.sheet {{ position: relative; background: var(--paper); box-shadow: var(--vignette); padding: {"40px 40px 26px" if parch else "30px 26px 20px"}; border-radius: var(--radius) }}
.sheet:before {{ content: ""; position: absolute; inset: 12px; border: var(--frame); outline: var(--frame); outline-offset: 4px; opacity: .7; pointer-events: none }}
.top {{ display: flex; justify-content: space-between; align-items: flex-start }}
.kick {{ font-family: var(--head); letter-spacing: 4px; font-size: 14px; color: var(--faint) }}
h1 {{ font-family: var(--head); font-size: 58px; letter-spacing: {"1px" if parch else "6px"}; margin: 0; color: var(--ink); font-weight: {"400" if parch else "800"}; line-height: 1.05 }}
.date {{ font-family: var(--head); font-size: 24px; margin-top: 6px; color: var(--ink) }}
.sub {{ color: var(--faint); font-size: {"18px" if parch else "14px"}; margin-top: 4px; {"font-style: italic;" if parch else ""} max-width: 560px }}
.stats {{ display: grid; grid-template-columns: repeat(3, 128px); gap: 8px }}
.stat {{ background: var(--card); border: 1px solid var(--line2); border-radius: var(--radius); padding: 9px 11px }}
.stat span {{ display: block; font-family: var(--head); font-size: {"12px" if parch else "9px"}; letter-spacing: 1.5px; color: var(--faint) }}
.stat b {{ font-family: var(--mono); font-size: 16px; color: var(--ink) }}
.panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 14px; margin-top: 20px }}
.steps {{ display: flex; align-items: center; gap: 6px }}
.step {{ display: flex; gap: 10px; flex: 1; font-size: {"14px" if parch else "11px"}; color: var(--dim); line-height: {"1.25" if parch else "1.45"} }}
.step b {{ font-family: var(--head); color: var(--ink); letter-spacing: {"1px" if parch else "2px"}; font-size: {"16px" if parch else "13px"}; font-weight: {"400" if parch else "700"} }}
.num {{ flex: none; width: 28px; height: 28px; border: 2px solid var(--go); color: var(--go); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-family: var(--mono) }}
.arrow {{ color: var(--accent); font-size: 20px }}
.ph {{ display: flex; justify-content: space-between; align-items: baseline; margin: 0 4px 12px; {"border-bottom: 1px solid var(--line); padding-bottom: 6px;" if parch else ""} }}
.ph b, .rh {{ font-family: var(--head); font-size: {"25px" if parch else "17px"}; letter-spacing: {"1px" if parch else "3px"}; color: var(--ink); font-weight: {"400" if parch else "700"} }}
.rh {{ border-bottom: 1px solid var(--line); padding-bottom: 6px; margin: 0 2px 12px }}
.sn, .ph b .sn {{ color: var(--accent); font-size: 1.2em; font-style: normal }}
.ph > span {{ font-size: {"15px" if parch else "11px"}; color: var(--faint); {"font-style: italic;" if parch else ""} }}
.grid {{ display: grid; grid-template-columns: 196px repeat(5, 1fr); gap: 8px }}
.bh {{ border-top: 3px solid var(--c); color: var(--c); text-align: center; font-family: var(--head); font-weight: 700; letter-spacing: 2px; font-size: {"15px" if parch else "12px"}; padding: 10px 0 4px }}
.lab {{ padding: 4px }} .lab .tk {{ font-family: var(--head); font-size: {"29px" if parch else "25px"}; font-weight: {"400" if parch else "800"}; color: var(--ink); letter-spacing: 1px }}
.lab .meta {{ font-family: var(--mono); font-size: {"11px" if parch else "10px"}; color: var(--dim); margin-top: 3px }}
.note {{ font-family: var(--mono); font-size: {"11px" if parch else "10px"}; color: var(--accent); margin-top: 3px; {"font-weight: 700;" if parch else ""} }}
.badge {{ font-family: var(--mono); font-size: 8px; letter-spacing: 1px; border: 1px solid var(--line); color: var(--faint); padding: 2px 5px; border-radius: 3px; margin-left: 8px; vertical-align: middle; font-weight: 700 }}
.mute .tk, .mute .rng {{ color: var(--mute) !important }} .cell.mute .act {{ color: var(--mute) }}
.cell {{ position: relative; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 10px; min-height: 92px }}
.cell.hl {{ border: 2px solid var(--accent); background: var(--hl-bg) }}
.flag {{ position: absolute; top: -8px; right: 8px; background: var(--accent); color: var(--accent-ink); font-family: var(--mono); font-size: 8px; font-weight: 800; letter-spacing: 1px; padding: 2px 5px; border-radius: 3px }}
.rng {{ font-family: var(--mono); font-weight: 700; font-size: 14px; color: var(--ink) }}
.act {{ font-size: {"14.5px" if parch else "10.5px"}; color: var(--dim); margin-top: 6px; line-height: {"1.22" if parch else "1.4"} }} .cell.hl .act {{ color: var(--ink); {"font-weight: 700;" if parch else ""} }}
.olab {{ font-family: var(--mono); font-size: {"11px" if parch else "10px"}; color: var(--dim); padding: 4px; line-height: 1.5 }} .olab b {{ color: var(--ink); font-size: {"12px" if parch else "11px"} }}
.bottom {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 14px; margin-top: 20px }}
.rule {{ display: flex; gap: 16px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 12px 16px; margin-bottom: 9px; font-size: {"15px" if parch else "11.5px"}; color: var(--dim); line-height: {"1.3" if parch else "1.45"} }}
.rule b {{ font-family: var(--head); color: var(--ink); letter-spacing: {"1px" if parch else "2px"}; font-size: {"17px" if parch else "13px"}; font-weight: {"400" if parch else "700"} }}
.rn {{ color: var(--accent); font-size: 22px; font-weight: 800; font-family: var(--head) }}
.ctx {{ background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px; font-size: {"16px" if parch else "13px"}; color: var(--body); line-height: {"1.35" if parch else "1.5"} }}
.ctx h4 {{ margin: 0 0 10px; font-family: var(--head); letter-spacing: {"1px" if parch else "2px"}; font-size: {"22px" if parch else "11px"}; color: {"var(--ink)" if parch else "var(--faint)"}; font-weight: {"400" if parch else "700"} }}
.ctx hr {{ border: 0; border-top: 1px {"dashed" if parch else "solid"} var(--line); margin: 12px 0 }} .ctx p {{ margin: 0 }}
.foot {{ text-align: center; font-family: var(--mono); font-size: 10.5px; color: var(--faint); margin-top: 12px }}
</style></head><body><div class="wrap"><div class="sheet">
<div class="top"><div>{'<div class="kick">THE BOOK · TWO LOOKS · ONE ACTION PER CELL</div>' if parch else ""}<h1>{th["title"]}</h1><div class="date">{e(s["title_date"])}</div><div class="sub">{e(s["subtitle"])}</div></div><div class="stats">{stat}</div></div>
<div class="panel steps">{steps}</div>
<div class="panel"><div class="ph"><b>{sec("I", "The Plays")}</b><span>Range is the price zone. Action sits below it.</span></div>
<div class="grid"><div></div>{head}{"".join(rows)}</div></div>
<div class="panel"><div class="ph"><b>{sec("II", "The Option Legs")}</b><span>Keyed to the underlying's bucket. Net option premium at risk: ${paid:.0f}.</span></div>
<div class="grid"><div></div>{head}{"".join(orows)}</div></div>
<div class="bottom"><div>{'<div class="rh">' + sec("III", "House Rules") + "</div>" if parch else ""}{rules}</div><div class="ctx"><h4>{sec("IV", "The Tape") if parch else "CONTEXT"}</h4>{ctx}</div></div>
<div class="foot">Levels measured off the {e(s["levels_from"])} close ({asof.pop()} bars). Recompute daily. Not financial advice.</div>
</div></div></body></html>"""
    out = spec_path.with_name("board.html")
    out.write_text(doc)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1160, "height": 800}, device_scale_factor=2)
        pg.set_content(doc, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=str(spec_path.with_name("board.png")), full_page=True)
        b.close()
    print(json.dumps({"nlv": round(nlv, 2), "beta": round(wbeta, 2), "levels": {t: bands(*cache[t][:2]) for t in cache},
                      "beta_by": {t: round(v, 2) for t, v in beta.items()}}, indent=1))


if __name__ == "__main__":
    args = sys.argv[1:]
    t = args[args.index("--theme") + 1] if "--theme" in args else None
    main(args[0], t)
