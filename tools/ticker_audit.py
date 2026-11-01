"""Full-picture ticker audit: technical row + options walls + volume, one shot.
Start of the /audit command. Reuses the recap skill's sanctioned fetch.

  .venv/bin/python tools/ticker_audit.py DIS RSI AMD ...
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Same endpoint and key file as .claude/skills/stock-recap/scripts/render_chart.mjs.
# The old render_chart.py was deleted when the recap renderer moved to Node, so
# these live here now. The API bot filter 403s non-browser User-Agents.
TD_BASE = os.environ.get(
    "TD_API_URL", "https://traderdaddy-pro-whop-production.up.railway.app")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def load_agent_key():
    """Bare Bearer token on one line in <repo>/.env_agent_api (not KEY=value)."""
    try:
        return (REPO / ".env_agent_api").read_text().strip() or None
    except OSError:
        return None


KEY = load_agent_key()


def fetch(sym):
    if not KEY:
        raise RuntimeError(".env_agent_api missing or empty")
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
