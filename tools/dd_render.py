#!/usr/bin/env python3
"""Render a filled Super DD JSON (docs/dd/super_dd_template.json -> report_schema) to markdown.

    python3 tools/dd_render.py data/dd/TXN/2026-11-01.json              # prints markdown
    python3 tools/dd_render.py data/dd/TXN/2026-11-01.json --blog OUT.md   # TraderMatrix blog file

Section order and headings come from the template, not the JSON, so every DD reads the same.
Fails loudly on em/en dashes and on process-narration phrases (template ground rule 6).
"""
import json, re, sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "docs/dd/super_dd_template.json"
BANNED = [r"almost missed", r"\bthe template\b", r"\bAI[- ]assisted\b", r"\bagents?\b", r"\bdebate\b",
          r"\bour (?:first|earlier|prior) pass\b", r"\bround (?:one|two|three|\d)\b", "—", "–"]


def esc(s):
    return s.replace('"', '\\"')


def render(r, blog=False):
    tmpl = {s["n"]: s for s in json.load(open(TEMPLATE))["sections"]}
    m, v = r["meta"], r["verdict"]
    out = []
    if blog:
        out += ["---", f'title: "{esc(m["title"])}"', f'subtitle: "{esc(m.get("subtitle", "Due Diligence"))}"', f'date: {m["date"]}',
                f'description: "{esc(m["description"])}"', f'cover: {m["cover"]}', "---", ""]
    else:
        out += [f'# {m["title"]}', ""]
    out += [f'**{m["company"]} ({m["ticker"]})** · **${m["price"]:.2f}** at the {m["price_asof"]}', "",
            v["pitch"], "",
            f'**Score: {v["score"]}/10 · Size: {v["size_R"]}R · Action: {v["action"]}**', ""]
    secs = {s["n"]: s for s in r["sections"]}
    for n in sorted(tmpl):
        if n in (0, 16, 17) or (n == 15 and r.get("catalysts")):
            continue
        s = secs.get(n)
        if not s:
            continue
        out += [f'## {n}. {tmpl[n]["title"]}', ""]
        if s.get("summary"):
            out += [s["summary"], ""]
        if s.get("figure"):
            out += [f'![{s.get("caption", "")}]({s["figure"]})', ""]
        for b in s.get("bullets", []):
            src = f' *({b["source"]})*' if b.get("source") else ""
            out.append(f'- {b["text"]}{src}')
        out.append("")
    if r.get("catalysts"):
        out += ["## 15. Catalyst calendar", ""]
        for c in r["catalysts"]:
            d = c["date"] or "date not confirmed"
            out.append(f'- **{d}:** {c["event"]}' + (f' *({c["source"]})*' if c.get("source") else ""))
        out.append("")
    t = r["trade_plan"]
    out += ["## 16. Trade plan", ""]
    if t.get("figure"):
        out += [f'![{t.get("caption", "")}]({t["figure"]})', ""]
    for tr in t["triggers"]:
        out.append(f'- **{tr["label"]}:** {tr["condition"]}. Stop: {tr["stop"]}.')
    if t.get("no_trade_zone"):
        out.append(f'- **No-trade zone:** {t["no_trade_zone"]}')
    out.append(f'- **Targets:** {" / ".join(t["targets"])}')
    o = t.get("options") or {}
    if o.get("structure"):
        out.append(f'- **Options:** {o["structure"]}, {o["expiry"]}. Debit {o["debit"]}, max value {o["max_value"]}, breakeven {o["breakeven"]}.')
    if t.get("wheeler_alternative"):
        out.append(f'- **Put-selling alternative:** {t["wheeler_alternative"]}')
    for x in t.get("notes", []):
        out.append(f'- {x}')
    for x in t.get("exit_if", []):
        out.append(f'- **Exit if:** {x}')
    out.append("")
    if r.get("unverified"):
        out += ["## Unverified", ""] + [f"- {u}" for u in r["unverified"]] + [""]
    out += ["~ Michael", "", "*Not financial advice. Data as of the " + m["price_asof"] + ".*", ""]
    if r.get("sources"):
        out += ["**Sources:** " + " · ".join(f'[{s["label"]}]({s["url"]})' if s.get("url") else s["label"] for s in r["sources"]), ""]
    md = "\n".join(out)
    hits = [p for p in BANNED if re.search(p, md, re.I)]
    if hits:
        sys.exit(f"dd_render: banned phrasing found {hits}; fix the JSON, not the output")
    return md


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    r = json.load(open(sys.argv[1]))
    if "--blog" in sys.argv:
        dest = sys.argv[sys.argv.index("--blog") + 1]
        Path(dest).write_text(render(r, blog=True))
        print(f"wrote {dest}")
    else:
        print(render(r))
