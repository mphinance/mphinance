"""Full-picture ticker audit: technical row + options walls + volume, one shot.
Start of the /audit command. Reuses the recap skill's sanctioned fetch.

  .venv/bin/python tools/ticker_audit.py DIS RSI AMD ...
"""
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / ".claude/skills/stock-recap/scripts"))
from render_chart import load_agent_key, TD_BASE, UA  # noqa: E402

KEY = load_agent_key()


def fetch(sym):
    req = urllib.request.Request(
        f"{TD_BASE}/api/agent/ticker/{sym}",
        headers={"User-Agent": UA, "Accept": "application/json",
                 "Authorization": f"Bearer {KEY}"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def pct_vs(price, ref):
    return f"{(price/ref-1)*100:+.0f}%" if ref else "—"


def main(syms):
    print(f"{'TKR':<6}{'price':>8}{'chg%':>7}{'relV':>6}{'RSI':>6}{'ADX':>6}"
          f"{'vs200':>7}{'stack':>14}{'trend':>11}{'buyZone':>15}"
          f"{'maxP':>7}{'callW':>7}{'putW':>7}")
    for sym in syms:
        s = sym.upper().strip()
        try:
            d = fetch(s)
            t = d.get("technicals") or {}
            o = d.get("options") or {}
            if not t:
                print(f"{s:<6}  (no technicals — uncovered or bad ticker)")
                continue
            price = t.get("close")
            print(f"{s:<6}{price:>8.2f}{t.get('change',0):>7.2f}"
                  f"{t.get('relVol',0):>6.2f}{t.get('rsi',0):>6.1f}{t.get('adx',0):>6.1f}"
                  f"{pct_vs(price,t.get('sma200')):>7}{str(t.get('emaStack','')):>14}"
                  f"{str(t.get('trendStatus','')):>11}{str(t.get('buyZone','')):>15}"
                  f"{str(o.get('maxPain','—')):>7}{str(o.get('callWall','—')):>7}"
                  f"{str(o.get('putWall','—')):>7}")
        except Exception as e:
            print(f"{s:<6}  ERROR: {str(e)[:50]}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["DIS", "RSI"])
