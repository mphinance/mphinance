#!/usr/bin/env python3
"""
TraderDaddy Pro · Ops Board — local server with a real-time SPY price tap.

Serves the board's static files AND a tiny `/api/spy` endpoint that returns the
latest SPY quote from Tradier (cached ~2s). The kiosk polls /api/spy every few
seconds to keep the SPY candle live between the slower data.json refreshes.

The Tradier token is read here, server-side — it never reaches the browser.
Stdlib only, no pip. Bind is localhost-only.

  python3 serve.py            # → http://localhost:8077/
  OPS_PORT=9000 python3 serve.py

Falls back gracefully: with no token, /api/spy returns {"error": ...} and the
board just keeps using its 30–90s data.json candles.
"""

import json, os, time, urllib.request, urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE    = os.path.dirname(os.path.abspath(__file__))
PORT    = int(os.environ.get("OPS_PORT", "8077"))
TR_BASE = os.environ.get("TRADIER_BASE", "https://api.tradier.com")
CACHE_TTL = 2.0  # seconds — don't hammer Tradier on every poll


def load_keys():
    keys, path = {}, os.path.join(HERE, "keys.env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("TRADIER_TOKEN", "TRADIER_BASE"):
        if os.environ.get(k):
            keys[k] = os.environ[k]
    return keys


KEYS  = load_keys()
TOKEN = KEYS.get("TRADIER_TOKEN", "")
_cache = {"t": 0.0, "data": None}


def fetch_spy():
    if not TOKEN:
        return {"error": "no Tradier token"}
    now = time.time()
    if _cache["data"] and now - _cache["t"] < CACHE_TTL:
        return _cache["data"]
    base = KEYS.get("TRADIER_BASE", TR_BASE)
    req = urllib.request.Request(
        f"{base}/v1/markets/quotes?symbols=SPY",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode())
        q = (d.get("quotes") or {}).get("quote") or {}
        if isinstance(q, list):
            q = q[0]
        out = {"symbol": "SPY", "price": q.get("last"),
               "change": q.get("change"), "changePct": q.get("change_percentage"),
               "ts": int(now * 1000)}
    except Exception as e:
        out = {"error": str(e)}
    _cache.update(t=now, data=out)
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/spy":
            body = json.dumps(fetch_spy()).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[serve] ops board on http://localhost:{PORT}/  ·  SPY tap: {'on' if TOKEN else 'OFF (no token)'}")
    srv.serve_forever()
