#!/usr/bin/env python3
"""
TraderDaddy Pro · Ops Board — local refresher.

Runs ON the Pi (or any always-on box). Reads keys from keys.env, pulls live data,
and overwrites data.json next to index.html. The kiosk browser only ever reads
data.json — the API keys NEVER leave this process or touch the page.

Hybrid feed:
  • TraderDaddy Pro  (X-API-Key)  → flow tape, convergence, gamma pin map, sentiment
  • Tradier          (Bearer)     → real-time index band + YOUR positions & P&L

Zero dependencies — standard library only. Python 3.9+.

Every source is wrapped so one failing API can't blank the board: on error it
keeps that section's previous values (from the existing data.json).
"""

import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "data.json")

TD_BASE  = os.environ.get("TD_NEW_API_URL", "https://api.traderdaddy.pro/api/v1")
TR_BASE  = os.environ.get("TRADIER_BASE",   "https://api.tradier.com")
TIMEOUT  = float(os.environ.get("OPS_TIMEOUT", "20"))
ET       = timezone(timedelta(hours=-4))  # ET (EDT); cosmetic only

SCREENERS = ["bullish-pullback", "momentum", "volatility-surge", "gamma-scan"]
SRC_TAG   = {"bullish-pullback": "PB", "momentum": "MO",
             "volatility-surge": "VS", "gamma-scan": "GS"}

SAM_LINES = [
    "Dealers are short gamma and so is your patience. Size down.",
    "Down day or up day, the stop goes in first. Non-negotiable.",
    "You don't have to catch the whale's trade. You have to not blow up.",
    "Don't be a hero into the print.",
    "Drink water. Set stop losses. Call your sponsor. In that order.",
    "Short gamma means the market lies fast. Believe the levels, not the wick.",
    "The setup will still be there after you've eaten lunch. Chasing won't.",
]


# ── key loading ───────────────────────────────────────────────────────────────
def load_keys():
    """keys.env (KEY=VALUE per line) next to this script, then real env vars."""
    keys = {}
    path = os.path.join(HERE, "keys.env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("TD_API_KEY", "TRADIER_TOKEN", "TRADIER_BASE"):
        if os.environ.get(k):
            keys[k] = os.environ[k]
    # repo fallback for the TD key
    if not keys.get("TD_API_KEY"):
        for cand in (os.path.join(HERE, "..", "..", ".env_td_api"),):
            if os.path.exists(cand):
                keys["TD_API_KEY"] = open(cand).read().strip()
                break
    return keys


# ── http ────────────────────────────────────────────────────────────────────
def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def warn(section, e):
    print(f"[refresh] {section}: {e}", file=sys.stderr)


# ── TraderDaddy sources ───────────────────────────────────────────────────────
def td_market_stats(h):
    d = get_json(f"{TD_BASE}/market-stats", h)
    out = []
    for sym in ("SPY", "QQQ", "IWM"):
        pc = d.get(f"{sym.lower()}_put_call_ratio")
        rd = d.get(f"{sym.lower()}_sentiment")
        if pc is not None:
            out.append({"sym": sym, "pc": round(pc, 2), "read": rd or ("Bearish" if pc > 1 else "Bullish")})
    return out, d


def td_flow(h, market_open):
    tf = "today" if market_open else "week"
    url = f"{TD_BASE}/unusual-activity?minScore=70&minPremium=250000&timeFrame={tf}&page=1&pageSize=40"
    d = get_json(url, h)
    rows = d.get("data", d if isinstance(d, list) else [])
    flow = []
    biggest = 0
    for r in rows:
        prem = r.get("premium") or r.get("totalPremium") or 0
        biggest = max(biggest, prem)
    for r in rows[:14]:
        prem = r.get("premium") or r.get("totalPremium") or 0
        side = (r.get("type") or r.get("optionType") or r.get("putCall") or "").upper()
        sent = (r.get("sentiment") or r.get("sentimentLabel") or "").upper()
        if side not in ("CALL", "PUT"):
            side = "CALL" if sent == "BULLISH" else ("PUT" if sent == "BEARISH" else "CALL")
        if sent not in ("BULLISH", "BEARISH", "MIXED"):
            sent = "MIXED"
        note = r.get("flowDescription") or r.get("description") or r.get("conviction") or ""
        moneyness = r.get("moneyness")
        if moneyness and moneyness not in note:
            note = (note + " · " + moneyness).strip(" ·")
        flow.append({
            "ticker": r.get("ticker") or r.get("symbol") or "?",
            "side": side, "sentiment": sent, "premium": prem,
            "note": note or "unusual activity",
            "tier": "HIGH" if prem >= 5e6 else "MED",
        })
    return flow


def td_screeners(h):
    """Merge screeners → convergence rows ranked by #sources, then entry score."""
    agg = {}
    for sid in SCREENERS:
        try:
            d = get_json(f"{TD_BASE}/screeners/{sid}/run?limit=30", h)
        except Exception as e:
            warn(f"screener:{sid}", e); continue
        for row in d.get("results", []):
            t = row.get("symbol")
            if not t: continue
            m = row.get("metrics", {})
            grade = (m.get("entryGrade") or "B").split()[-1]  # strip emoji
            e = agg.setdefault(t, {"ticker": t, "sources": set(), "grade": grade,
                                   "price": row.get("price"), "chg": row.get("changePct"),
                                   "perf3m": m.get("perf3MPct"), "trend": m.get("trendStrength") or "",
                                   "score": m.get("entryScore") or 0})
            e["sources"].add(SRC_TAG.get(sid, sid[:2].upper()))
            if m.get("flowHits"):
                e["sources"].add("FLOW"); e["flowSentiment"] = m.get("flowSentiment")
            if (m.get("entryScore") or 0) > e["score"]:
                e["score"] = m.get("entryScore"); e["grade"] = grade
    rows = list(agg.values())
    rows.sort(key=lambda x: (len(x["sources"]), x["score"]), reverse=True)
    out = []
    for e in rows[:8]:
        out.append({
            "ticker": e["ticker"],
            "price": round(e["price"], 2) if e.get("price") else 0,
            "chg": round(e["chg"], 2) if e.get("chg") is not None else 0,
            "perf3m": round(e["perf3m"], 2) if e.get("perf3m") else 0,
            "grade": "A" if e["grade"].startswith("A") else ("C" if e["grade"].startswith("C") else e["grade"]),
            "sources": sorted(e["sources"]),
            "trend": e["trend"],
        })
    return out


def td_gex(h):
    pin, total = [], 0.0
    for sym in ("SPX", "SPY", "QQQ"):
        try:
            d = get_json(f"{TD_BASE}/gex/{sym}", h)
        except Exception as e:
            warn(f"gex:{sym}", e); continue
        b = d.get(sym, d)  # endpoint may wrap by symbol
        spot = b.get("spotPrice")
        total += b.get("totalGEX", 0) or 0
        levels = []
        for kl in (b.get("keyLevels") or [])[:6]:
            levels.append({"strike": kl.get("strike"),
                           "type": kl.get("type", "pin"),
                           "gex": round((kl.get("netGEX", 0) or 0) / 1e9, 2)})
        if spot and levels:
            pin.append({"sym": sym, "spot": round(spot, 2),
                        "regime": "SHORT GAMMA" if total < 0 else "LONG GAMMA", "levels": levels})
    bias = "SHORT_GAMMA" if total < 0 else "LONG_GAMMA"
    regime = {"bias": bias, "label": bias.replace("_", " "),
              "totalGEX": int(total),
              "interpretation": ("Dealers are net short gamma. Moves get amplified, vol runs hot. Trade smaller."
                                 if total < 0 else
                                 "Dealers are net long gamma. Moves get dampened, expect mean-reversion / pinning.")}
    return pin, regime


def td_economic(h):
    """Upcoming macro calendar → event countdowns (CPI / NFP / FOMC ...)."""
    d = get_json(f"{TD_BASE}/economic-calendar", h)
    out = []
    for e in d.get("events", []):
        date, t = e.get("date"), e.get("time")
        if not date:
            continue
        iso = f"{date}T08:30:00-04:00"
        if t:
            try:
                hm = datetime.strptime(t.strip(), "%I:%M %p")
                iso = f"{date}T{hm.hour:02d}:{hm.minute:02d}:00-04:00"
            except ValueError:
                pass
        # short label: first token / acronym in parens
        lbl = e.get("event", "")
        if "(" in lbl and ")" in lbl:
            lbl = lbl[lbl.index("(") + 1:lbl.index(")")]
        out.append({"label": lbl, "datetime": iso,
                    "impact": e.get("impact", "medium"), "kind": "macro"})
    return out


def td_earnings(h):
    """Upcoming earnings → flow rows + ER convergence tags + event countdowns."""
    d = get_json(f"{TD_BASE}/earnings?days=7", h)
    flow, events = [], []
    for x in d.get("earnings", [])[:6]:
        e = x.get("event", x)
        sym = e.get("symbol")
        if not sym: continue
        prem = e.get("preEarningsPremium") or 0
        mv = e.get("expectedMovePct") or 0
        bull = e.get("preEarningsBullishPct") or 0
        when = e.get("earningsTime") or ""
        date = e.get("earningsDate")
        flow.append({"ticker": sym, "side": "CALL",
                     "sentiment": (e.get("preEarningsSentiment") or "mixed").upper(),
                     "premium": prem,
                     "note": f"pre-earnings · {bull:.0f}% bull · ±{mv:.1f}% · {date} {when}",
                     "tier": "HIGH" if prem >= 5e6 else "LOW"})
        if date:
            hhmm = "16:00:00-04:00" if when == "AMC" else "08:00:00-04:00"
            events.append({"label": f"{sym} earnings", "datetime": f"{date}T{hhmm}",
                           "impact": "high", "kind": "earnings"})
    return flow, events


# ── Tradier sources ───────────────────────────────────────────────────────────
def _quote_list(d):
    q = (d.get("quotes") or {}).get("quote")
    if q is None: return []
    return q if isinstance(q, list) else [q]


def tr_clock(h):
    try:
        d = get_json(f"{TR_BASE}/v1/markets/clock", h)
        return (d.get("clock", {}).get("state") == "open")
    except Exception as e:
        warn("clock", e)
        # fallback: weekday 9:30–16:00 ET
        now = datetime.now(ET)
        return now.weekday() < 5 and (now.hour * 60 + now.minute) >= 570 and (now.hour * 60 + now.minute) < 960


def tr_indices(h):
    d = get_json(f"{TR_BASE}/v1/markets/quotes?symbols=SPY,QQQ,IWM", h)
    out = []
    for q in _quote_list(d):
        out.append({"sym": q.get("symbol"),
                    "price": q.get("last"),
                    "chg": round(q.get("change_percentage"), 2) if q.get("change_percentage") is not None else None})
    return out


def tr_timesales(h, sym="SPY", interval="5min"):
    """Today's intraday OHLC bars for the SPY hero chart (KLineChart format).
    Real-time on a funded Tradier token; 15-min delayed on a sandbox token."""
    today = datetime.now(ET).strftime("%Y-%m-%d")
    d = get_json(f"{TR_BASE}/v1/markets/timesales?symbol={sym}&interval={interval}"
                 f"&start={today}%2009:30&end={today}%2016:00&session_filter=open", h)
    series = (d.get("series") or {})
    if not series or series == "null":
        return []
    rows = series.get("data", [])
    rows = rows if isinstance(rows, list) else [rows]
    bars = []
    for r in rows:
        ts = r.get("timestamp")
        if ts is None:
            continue
        bars.append({"timestamp": int(ts) * 1000,
                     "open": r.get("open"), "high": r.get("high"),
                     "low": r.get("low"), "close": r.get("close"),
                     "volume": r.get("volume", 0)})
    return bars




# ── assemble ──────────────────────────────────────────────────────────────────
def main():
    keys = load_keys()
    prev = {}
    if os.path.exists(OUT):
        try: prev = json.load(open(OUT))
        except Exception: prev = {}

    td_h = {"X-API-Key": keys.get("TD_API_KEY", ""), "Accept": "application/json"}
    tr_h = {"Authorization": f"Bearer {keys.get('TRADIER_TOKEN','')}", "Accept": "application/json"}
    have_td = bool(keys.get("TD_API_KEY"))
    have_tr = bool(keys.get("TRADIER_TOKEN"))

    data = dict(prev)  # start from previous so failures degrade gracefully

    market_open = tr_clock(tr_h) if have_tr else \
        (datetime.now(ET).weekday() < 5 and 570 <= datetime.now(ET).hour * 60 + datetime.now(ET).minute < 960)

    flow, events = [], []

    if have_td:
        try:
            sent, _ = td_market_stats(td_h); data["sentiment"] = sent
        except Exception as e: warn("market-stats", e)
        try: data["convergence"] = td_screeners(td_h)
        except Exception as e: warn("screeners", e)
        try:
            pin, regime = td_gex(td_h)
            if pin: data["pinmap"] = pin; data["regime"] = regime
        except Exception as e: warn("gex", e)
        try: flow += td_flow(td_h, market_open)
        except Exception as e: warn("flow", e)
        try: events += td_economic(td_h)
        except Exception as e: warn("economic", e)
        try:
            ef, ev = td_earnings(td_h); flow += ef; events += ev
        except Exception as e: warn("earnings", e)

    if have_tr:
        try: data["indices"] = tr_indices(tr_h)
        except Exception as e: warn("indices", e)
        try:
            bars = tr_timesales(tr_h, "SPY")
            if bars:
                data.setdefault("chart", {})["spy"] = {"bars": bars}
        except Exception as e: warn("chart", e)

    # SPY hero chart: bars from Tradier (above), gamma walls from the GEX pin map.
    spy_pin = next((p for p in data.get("pinmap", []) if p["sym"] == "SPY"), None)
    if spy_pin:
        chart = data.setdefault("chart", {})
        spy = chart.setdefault("spy", {})
        spy["spot"] = spy_pin["spot"]
        spy["levels"] = spy_pin["levels"]

    if flow:
        flow.sort(key=lambda r: r["premium"], reverse=True)
        if flow[0]["premium"] > 0:
            flow[0]["tier"] = "WHALE"   # biggest trade shown gets the glow
        data["flow"] = flow
    if events: data["events"] = sorted(events, key=lambda e: e["datetime"])
    data.setdefault("sam_lines", SAM_LINES)
    data["meta"] = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "session": datetime.now(ET).strftime("%Y-%m-%d"),
                    "marketOpen": market_open, "source": "TraderDaddy Pro + Tradier",
                    "ref": "8DUEMWAJ"}

    tmp = OUT + ".tmp"
    json.dump(data, open(tmp, "w"), indent=2)
    os.replace(tmp, OUT)  # atomic — the kiosk never reads a half-written file
    print(f"[refresh] wrote {OUT} · open={market_open} · "
          f"flow={len(data.get('flow',[]))} conv={len(data.get('convergence',[]))} "
          f"pos={len(data.get('positions',[]))}")


if __name__ == "__main__":
    main()
