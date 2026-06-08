"""
Portfolio Audit — holistic, book-level scoring for the Momentum Phund (IBKR).

The per-ticker dossier grades names in isolation. Nobody grades the *book*.
This module does: it takes a normalized account snapshot (positions + summary +
balances) and produces a single audit — concentration, sector clustering, cash
drag, P&L, and a set of plain-English flags ("you're 66% defensive and don't
know it").

SOURCE-AGNOSTIC ON PURPOSE. The live feed today is the IBKR account MCP
connector (interactive, agent-side). The 5AM dossier pipeline runs in GitHub
Actions and can't reach that socket, so the analysis core takes a plain dict and
doesn't care where it came from. Feed it the MCP output now; feed it a Flex
Query / REST payload when the pipeline gets wired up. `normalize_ibkr` adapts the
IBKR shapes; everything downstream is pure.

Pipeline:
    normalize_ibkr(positions, summary, balances)  -> book (account + holdings)
    audit_portfolio(book, ticker_dir=...)         -> audit dict (+ dossier fuse)
    render_markdown(audit) / render_html(audit)   -> report strings

CLI:
    python -m dossier.portfolio_audit --snapshot snapshot.json
        where snapshot.json = {"positions": {...}, "summary": {...},
                               "balances": {...}}  (raw IBKR MCP output)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TICKER_DIR = PROJECT_ROOT / "docs" / "ticker"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "portfolio"

# ── Audit thresholds (named so tests and tuning are honest) ──
CONCENTRATION_WARN = 25.0   # single risk-asset > 25% of risk sleeve → flag
CASH_DRAG_WARN = 40.0       # pure cash > 40% of net liq → flag
DEFENSIVE_WARN = 60.0       # cash + cash-equivalents > 60% → "defensive" flag
SECTOR_CLUSTER_WARN = 40.0  # one sector > 40% of risk sleeve → flag
DUST_VALUE = 25.0           # position market value < $25 → dust flag

# Treasury / money-market ETFs that are cash by another name. Held as "dry
# powder parked safely" (see the 4/26 broker-switch musing — SGOV/VBIL), so they
# should not count as risk exposure or as a concentration offender.
CASH_EQUIVALENTS = {
    "VBIL", "SGOV", "BIL", "SHV", "SHY", "USFR", "TBIL", "CLTL",
    "ICSH", "GBIL", "XHLF", "TFLO", "BILS",
}

# Static sector fallback for current/likely holdings. Dossier deep_dive.json
# sector wins when present; this fills the gap for names without coverage.
SECTOR_MAP = {
    "CECO": "Industrials",
    "EBAY": "Consumer Discretionary",
    "KMI": "Energy",
    "ONDS": "Technology",
    "XLV": "Healthcare",
    "VBIL": "Cash Equivalent",
}


def _pct(part, whole):
    """Percent of whole, guarding divide-by-zero. Returns float (e.g. 18.9)."""
    if not whole:
        return 0.0
    return round(part / whole * 100, 2)


def _round(val, digits=2):
    try:
        return round(float(val), digits)
    except (TypeError, ValueError):
        return 0.0


# ──────────────────────────────────────────────────────────────────────────
# 1. NORMALIZE — adapt the raw IBKR MCP shapes to a flat, stable book.
# ──────────────────────────────────────────────────────────────────────────
def normalize_ibkr(positions, summary, balances=None):
    """Turn raw IBKR MCP output into a normalized book.

    `positions` / `summary` / `balances` accept either the raw MCP envelope
    ({"positions": [...]}) or the already-unwrapped value — so a snapshot file
    and a live MCP call both work.
    """
    pos_list = positions.get("positions") if isinstance(positions, dict) else positions
    pos_list = pos_list or []

    holdings = []
    for p in pos_list:
        symbol = (p.get("contract_description") or p.get("symbol") or "").strip()
        qty = _round(p.get("position", 0), 4)
        mkt_val = _round(p.get("market_value", 0))
        avg = _round(p.get("average_price", 0), 4)
        cost_basis = _round(avg * qty)
        holdings.append({
            "symbol": symbol,
            "qty": qty,
            "market_price": _round(p.get("market_price", 0), 4),
            "market_value": mkt_val,
            "average_price": avg,
            "cost_basis": cost_basis,
            "unrealized_pnl": _round(p.get("unrealized_pnl", 0)),
            "asset_class": p.get("asset_class", "STK"),
            "is_cash_equivalent": symbol.upper() in CASH_EQUIVALENTS,
        })

    net_liq = _round(summary.get("net_liquidation", 0))
    cash = _round(summary.get("total_cash_value", summary.get("available_funds", 0)))
    account = {
        "net_liquidation": net_liq,
        "cash": cash,
        "gross_position_value": _round(summary.get("gross_position_value", 0)),
        "buying_power": _round(summary.get("buying_power", 0)),
        "leverage": summary.get("leverage"),
        "currency": summary.get("currency", "USD"),
    }
    return {"account": account, "holdings": holdings}


# ──────────────────────────────────────────────────────────────────────────
# 2. ANALYSIS — pure functions over the normalized book.
# ──────────────────────────────────────────────────────────────────────────
def split_sleeves(book):
    """Split holdings into risk assets vs cash-equivalents, and total each."""
    risk = [h for h in book["holdings"] if not h["is_cash_equivalent"]]
    cash_eq = [h for h in book["holdings"] if h["is_cash_equivalent"]]
    risk_value = round(sum(h["market_value"] for h in risk), 2)
    cash_eq_value = round(sum(h["market_value"] for h in cash_eq), 2)
    return {
        "risk": risk,
        "cash_equivalents": cash_eq,
        "risk_value": risk_value,
        "cash_equivalent_value": cash_eq_value,
    }


def compute_weights(book):
    """Weight each holding by net liq and by the risk sleeve; add HHI index.

    Returns {holdings: [...with weight_net/weight_risk...], hhi, top}.
    HHI is the Herfindahl index over the *risk* sleeve (0-10000); >2500 is a
    classic 'concentrated' line.
    """
    net_liq = book["account"]["net_liquidation"] or 1
    sleeves = split_sleeves(book)
    risk_value = sleeves["risk_value"] or 1

    enriched = []
    hhi = 0.0
    for h in book["holdings"]:
        weight_net = _pct(h["market_value"], net_liq)
        weight_risk = 0.0 if h["is_cash_equivalent"] else _pct(h["market_value"], risk_value)
        if not h["is_cash_equivalent"]:
            share = h["market_value"] / risk_value
            hhi += (share * 100) ** 2
        enriched.append({**h, "weight_net": weight_net, "weight_risk": weight_risk})

    risk_enriched = [h for h in enriched if not h["is_cash_equivalent"]]
    top = max(risk_enriched, key=lambda h: h["market_value"], default=None)
    return {"holdings": enriched, "hhi": round(hhi, 1), "top": top}


def sector_exposure(holdings, ticker_dir=TICKER_DIR):
    """Aggregate risk-sleeve market value by sector. Cash-equivalents excluded.

    Sector source priority: dossier deep_dive.json -> SECTOR_MAP -> 'Unknown'.
    Returns {sector: {value, weight_risk}} sorted by value desc.
    """
    risk = [h for h in holdings if not h["is_cash_equivalent"]]
    risk_value = sum(h["market_value"] for h in risk) or 1
    buckets = {}
    for h in risk:
        sector = _lookup_sector(h["symbol"], ticker_dir)
        buckets.setdefault(sector, 0.0)
        buckets[sector] += h["market_value"]
    out = {
        s: {"value": round(v, 2), "weight_risk": _pct(v, risk_value)}
        for s, v in sorted(buckets.items(), key=lambda kv: kv[1], reverse=True)
    }
    return out


def _lookup_sector(symbol, ticker_dir=TICKER_DIR):
    sym = (symbol or "").upper()
    if sym in CASH_EQUIVALENTS:
        return "Cash Equivalent"
    dd = Path(ticker_dir) / sym / "deep_dive.json"
    if dd.exists():
        try:
            data = json.loads(dd.read_text())
            if data.get("sector"):
                return data["sector"]
        except (json.JSONDecodeError, OSError):
            pass
    return SECTOR_MAP.get(sym, "Unknown")


def fuse_dossier(holdings, ticker_dir=TICKER_DIR):
    """Attach the dossier grade + valuation to each holding when coverage exists.

    Pulls scores.grade and the valuation block from docs/ticker/{SYM}/latest.json.
    Names without coverage get grade=None — surfaced as a 'blind spot' in flags.
    """
    out = []
    for h in holdings:
        sym = h["symbol"].upper()
        grade, valuation = None, None
        lj = Path(ticker_dir) / sym / "latest.json"
        if lj.exists():
            try:
                data = json.loads(lj.read_text())
                grade = (data.get("scores") or {}).get("grade")
                valuation = data.get("valuation")
            except (json.JSONDecodeError, OSError):
                pass
        out.append({**h, "grade": grade, "valuation": valuation})
    return out


def build_flags(book, weights, sleeves, sectors):
    """The opinionated layer — plain-English audit flags, worst-first.

    Each flag: {level: 'danger'|'warn'|'info', message: str}.
    """
    flags = []
    net_liq = book["account"]["net_liquidation"] or 1
    cash = book["account"]["cash"]
    cash_pct = _pct(cash, net_liq)
    defensive_pct = _pct(cash + sleeves["cash_equivalent_value"], net_liq)

    # Cash drag / defensive posture
    if cash_pct >= CASH_DRAG_WARN:
        flags.append({"level": "warn", "message":
            f"Cash drag: {cash_pct}% of the book is idle cash "
            f"(${cash:,.0f}). That's dry powder doing nothing."})
    if defensive_pct >= DEFENSIVE_WARN:
        flags.append({"level": "info", "message":
            f"Defensive posture: {defensive_pct}% is cash + T-bills "
            f"(${cash + sleeves['cash_equivalent_value']:,.0f}). Conservative "
            f"for a momentum book — intentional parking or fear?"})

    # Concentration (risk sleeve)
    top = weights["top"]
    if top and top["weight_risk"] >= CONCENTRATION_WARN:
        flags.append({"level": "warn", "message":
            f"Concentration: {top['symbol']} is {top['weight_risk']}% of your "
            f"risk sleeve (${top['market_value']:,.0f}). One name carrying a lot."})
    if weights["hhi"] >= 2500:
        flags.append({"level": "warn", "message":
            f"Concentrated book: HHI {weights['hhi']:.0f} (>2500). The risk "
            f"sleeve isn't as diversified as the position count suggests."})

    # Sector clustering
    for sector, info in sectors.items():
        if info["weight_risk"] >= SECTOR_CLUSTER_WARN:
            flags.append({"level": "warn", "message":
                f"Sector cluster: {info['weight_risk']}% of risk is in "
                f"{sector} (${info['value']:,.0f})."})

    # Dust
    dust = [h for h in book["holdings"]
            if not h["is_cash_equivalent"] and h["market_value"] < DUST_VALUE]
    if dust:
        names = ", ".join(h["symbol"] for h in dust)
        flags.append({"level": "info", "message":
            f"Dust positions (<${DUST_VALUE:.0f}): {names}. Below the noise floor."})

    # Coverage blind spots
    uncovered = [h["symbol"] for h in fuse_dossier(
        [h for h in book["holdings"] if not h["is_cash_equivalent"]])
        if h["grade"] is None]
    if uncovered:
        flags.append({"level": "info", "message":
            f"Dossier blind spots: {', '.join(uncovered)} have no daily grade. "
            f"You're holding names the screener never looks at."})

    if not flags:
        flags.append({"level": "info", "message":
            "No structural red flags. Balanced, diversified, sized sanely. "
            "Boring. Boring is good."})
    return flags


def audit_portfolio(book, ticker_dir=TICKER_DIR, asof=None):
    """Run the full audit over a normalized book. Pure given ticker_dir/asof."""
    asof = asof or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    account = book["account"]
    weights = compute_weights(book)
    sleeves = split_sleeves(book)
    sectors = sector_exposure(book["holdings"], ticker_dir)
    holdings = fuse_dossier(weights["holdings"], ticker_dir)
    holdings = sorted(holdings, key=lambda h: h["market_value"], reverse=True)

    total_upnl = round(sum(h["unrealized_pnl"] for h in book["holdings"]), 2)
    total_cost = round(sum(h["cost_basis"] for h in book["holdings"]), 2)
    net_liq = account["net_liquidation"] or 1
    winners = [h for h in book["holdings"] if h["unrealized_pnl"] > 0]
    losers = [h for h in book["holdings"] if h["unrealized_pnl"] < 0]

    return {
        "asof": asof,
        "account": account,
        "holdings": holdings,
        "concentration": {
            "hhi": weights["hhi"],
            "top": weights["top"]["symbol"] if weights["top"] else None,
            "top_weight_risk": weights["top"]["weight_risk"] if weights["top"] else 0,
        },
        "sleeves": {
            "risk_value": sleeves["risk_value"],
            "risk_pct": _pct(sleeves["risk_value"], net_liq),
            "cash_equivalent_value": sleeves["cash_equivalent_value"],
            "cash_equivalent_pct": _pct(sleeves["cash_equivalent_value"], net_liq),
            "cash": account["cash"],
            "cash_pct": _pct(account["cash"], net_liq),
        },
        "sectors": sectors,
        "pnl": {
            "unrealized": total_upnl,
            "unrealized_pct": _pct(total_upnl, total_cost),
            "cost_basis": total_cost,
            "winners": len(winners),
            "losers": len(losers),
        },
        "flags": build_flags(book, weights, sleeves, sectors),
    }


# ──────────────────────────────────────────────────────────────────────────
# 3. RENDER — markdown + HTML (3-color HUD theme).
# ──────────────────────────────────────────────────────────────────────────
_LEVEL_EMOJI = {"danger": "🔴", "warn": "🟡", "info": "🟢"}


def render_markdown(audit):
    a = audit["account"]
    s = audit["sleeves"]
    p = audit["pnl"]
    pnl_sign = "+" if p["unrealized"] >= 0 else ""
    lines = [
        f"# 🧮 Portfolio Audit — {audit['asof']}",
        "",
        f"**Net Liquidation:** ${a['net_liquidation']:,.2f}  ·  "
        f"**Cash:** ${a['cash']:,.2f} ({s['cash_pct']}%)  ·  "
        f"**Leverage:** {a.get('leverage', 'n/a')}",
        "",
        f"**Sleeves:** Risk ${s['risk_value']:,.0f} ({s['risk_pct']}%)  ·  "
        f"Cash-equiv ${s['cash_equivalent_value']:,.0f} ({s['cash_equivalent_pct']}%)  ·  "
        f"Cash ${s['cash']:,.0f} ({s['cash_pct']}%)",
        "",
        f"**Unrealized P&L:** {pnl_sign}${p['unrealized']:,.2f} "
        f"({pnl_sign}{p['unrealized_pct']}% on cost)  ·  "
        f"{p['winners']} green / {p['losers']} red",
        "",
        "## 🚩 Audit Flags",
        "",
    ]
    for f in audit["flags"]:
        lines.append(f"- {_LEVEL_EMOJI.get(f['level'], '•')} {f['message']}")

    lines += ["", "## 📊 Holdings", "",
              "| Symbol | Qty | Mkt Value | % Risk | % Net | uPnL | Grade |",
              "|--------|-----|-----------|--------|-------|------|-------|"]
    for h in audit["holdings"]:
        tag = " *(cash-eq)*" if h["is_cash_equivalent"] else ""
        wr = "—" if h["is_cash_equivalent"] else f"{h['weight_risk']}%"
        grade = h.get("grade") or "—"
        lines.append(
            f"| {h['symbol']}{tag} | {h['qty']:g} | ${h['market_value']:,.2f} | "
            f"{wr} | {h['weight_net']}% | {h['unrealized_pnl']:+.2f} | {grade} |")

    lines += ["", "## 🧭 Sector Exposure (risk sleeve)", ""]
    for sector, info in audit["sectors"].items():
        lines.append(f"- **{sector}:** {info['weight_risk']}% (${info['value']:,.0f})")
    lines += ["",
              f"*Concentration HHI: {audit['concentration']['hhi']:.0f}  ·  "
              f"Top risk name: {audit['concentration']['top']} "
              f"({audit['concentration']['top_weight_risk']}%)*",
              "",
              "*Not financial advice. Audited by AI. Set stop losses, drink water, "
              "call your sponsor — in that order.*"]
    return "\n".join(lines)


def render_html(audit):
    a = audit["account"]
    s = audit["sleeves"]
    p = audit["pnl"]
    pnl_color = "var(--green)" if p["unrealized"] >= 0 else "var(--danger)"
    pnl_sign = "+" if p["unrealized"] >= 0 else ""

    flag_rows = "".join(
        f'<li><span class="dot {f["level"]}"></span>{_esc(f["message"])}</li>'
        for f in audit["flags"])

    hold_rows = ""
    for h in audit["holdings"]:
        tag = ' <span class="muted">(cash-eq)</span>' if h["is_cash_equivalent"] else ""
        wr = "—" if h["is_cash_equivalent"] else f'{h["weight_risk"]}%'
        upnl_c = "var(--green)" if h["unrealized_pnl"] >= 0 else "var(--danger)"
        grade = h.get("grade") or "—"
        hold_rows += (
            f'<tr><td>{_esc(h["symbol"])}{tag}</td><td>{h["qty"]:g}</td>'
            f'<td>${h["market_value"]:,.2f}</td><td>{wr}</td>'
            f'<td>{h["weight_net"]}%</td>'
            f'<td style="color:{upnl_c}">{h["unrealized_pnl"]:+.2f}</td>'
            f'<td>{_esc(str(grade))}</td></tr>')

    sector_rows = "".join(
        f'<li><b>{_esc(sector)}</b> — {info["weight_risk"]}% '
        f'(${info["value"]:,.0f})</li>'
        for sector, info in audit["sectors"].items())

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Audit — {audit['asof']}</title>
<style>
  :root {{ --bg:#0a0e14; --panel:#11161f; --fg:#c8d0da; --muted:#6b7685;
    --green:#00ff41; --gold:#f0b400; --danger:#e53935; --border:#1d2530; }}
  * {{ box-sizing:border-box; }}
  body {{ background:var(--bg); color:var(--fg); font:14px/1.5 ui-monospace,
    SFMono-Regular,Menlo,Consolas,monospace; margin:0; padding:24px; }}
  h1 {{ font-size:20px; color:var(--green); margin:0 0 4px; }}
  h2 {{ font-size:14px; color:var(--gold); text-transform:uppercase;
    letter-spacing:1px; border-bottom:1px solid var(--border);
    padding-bottom:6px; margin:28px 0 12px; }}
  .wrap {{ max-width:860px; margin:0 auto; }}
  .stat {{ display:flex; flex-wrap:wrap; gap:18px; margin:12px 0; }}
  .stat div {{ background:var(--panel); border:1px solid var(--border);
    border-radius:8px; padding:10px 14px; }}
  .stat b {{ color:#fff; }}
  .muted {{ color:var(--muted); }}
  ul {{ list-style:none; padding:0; }}
  ul li {{ padding:6px 0; border-bottom:1px solid var(--border); }}
  .dot {{ display:inline-block; width:9px; height:9px; border-radius:50%;
    margin-right:8px; }}
  .dot.danger {{ background:var(--danger); }} .dot.warn {{ background:var(--gold); }}
  .dot.info {{ background:var(--green); }}
  table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
  th,td {{ text-align:right; padding:6px 10px; border-bottom:1px solid var(--border); }}
  th:first-child,td:first-child {{ text-align:left; }}
  th {{ color:var(--muted); font-weight:400; text-transform:uppercase;
    font-size:11px; }}
  .foot {{ color:var(--muted); font-size:12px; margin-top:28px; font-style:italic; }}
</style></head>
<body><div class="wrap">
<h1>🧮 Portfolio Audit — {audit['asof']}</h1>
<div class="stat">
  <div>Net Liq <b>${a['net_liquidation']:,.2f}</b></div>
  <div>Cash <b>${a['cash']:,.2f}</b> ({s['cash_pct']}%)</div>
  <div>Risk sleeve <b>${s['risk_value']:,.0f}</b> ({s['risk_pct']}%)</div>
  <div>Cash-equiv <b>${s['cash_equivalent_value']:,.0f}</b> ({s['cash_equivalent_pct']}%)</div>
  <div>uPnL <b style="color:{pnl_color}">{pnl_sign}${p['unrealized']:,.2f}</b>
    ({pnl_sign}{p['unrealized_pct']}%)</div>
  <div>Leverage <b>{a.get('leverage', 'n/a')}</b></div>
</div>
<h2>🚩 Audit Flags</h2>
<ul>{flag_rows}</ul>
<h2>📊 Holdings</h2>
<table><thead><tr><th>Symbol</th><th>Qty</th><th>Mkt Value</th><th>% Risk</th>
<th>% Net</th><th>uPnL</th><th>Grade</th></tr></thead>
<tbody>{hold_rows}</tbody></table>
<h2>🧭 Sector Exposure <span class="muted">(risk sleeve)</span></h2>
<ul>{sector_rows}</ul>
<p class="muted">Concentration HHI {audit['concentration']['hhi']:.0f} ·
  Top risk name {audit['concentration']['top']}
  ({audit['concentration']['top_weight_risk']}%)</p>
<p class="foot">Not financial advice. Audited by AI. Set stop losses, drink water,
  call your sponsor — in that order.</p>
</div></body></html>"""


def _esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ──────────────────────────────────────────────────────────────────────────
# 4. CLI
# ──────────────────────────────────────────────────────────────────────────
def run_from_snapshot(snapshot, ticker_dir=TICKER_DIR, asof=None):
    """Snapshot dict {positions, summary, balances} -> audit dict."""
    book = normalize_ibkr(
        snapshot.get("positions", {}),
        snapshot.get("summary", {}),
        snapshot.get("balances", {}),
    )
    return audit_portfolio(book, ticker_dir=ticker_dir, asof=asof)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit the IBKR book (source-agnostic).")
    ap.add_argument("--snapshot", required=True,
                    help="JSON file with {positions, summary, balances} (raw IBKR MCP).")
    ap.add_argument("--out-dir", default=str(OUTPUT_DIR),
                    help="Where to write latest.md / latest.html / latest.json.")
    ap.add_argument("--asof", default=None, help="Override as-of date (YYYY-MM-DD).")
    ap.add_argument("--print", action="store_true", help="Print markdown to stdout only.")
    args = ap.parse_args(argv)

    snapshot = json.loads(Path(args.snapshot).read_text())
    audit = run_from_snapshot(snapshot, asof=args.asof)
    md = render_markdown(audit)

    if args.print:
        print(md)
        return audit

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.md").write_text(md)
    (out / "latest.html").write_text(render_html(audit))
    (out / "latest.json").write_text(json.dumps(audit, indent=2))
    print(f"✅ Portfolio audit written to {out}/ (latest.md / .html / .json)")
    return audit


if __name__ == "__main__":
    main()
