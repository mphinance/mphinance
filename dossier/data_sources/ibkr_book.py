"""
IBKR "Your Book" overlay — pull Mike's live holdings from the LOCAL gateway.

Headless/cron data source for the Daily Review's personalized "Your Book"
section (DAILY_REVIEW_PLAN.md Phase 3.5). The claude.ai IBKR MCP is an
interactive-only convenience and is absent in unattended runs, so this module
talks straight to the local FastAPI bridge instead:

    http://127.0.0.1:8765   (BRIDGE_HOST / BRIDGE_PORT in
                             /home/mph/ibkr/ibkr-gateway/bridge.py)

Routes used (all GET, read-only):
    /positions  -> [{account, symbol, secType, position, avgCost, ...}]
    /account    -> {NetLiquidation, BuyingPower, ...}   (flat string values)
    /pnl        -> {dailyPnL, unrealizedPnL, realizedPnL}  (ACCOUNT-LEVEL)

Auth note: the bridge's read-only data endpoints (/positions, /account, /pnl)
require NO token — only the mutating order endpoints (POST /order,
DELETE /order/{id}) check X-Bridge-Token (BRIDGE_TOKEN env var). We still
forward an X-Bridge-Token header when BRIDGE_TOKEN / IBKR_BRIDGE_TOKEN is set
in the environment, in case the bridge is ever locked down further.

CONTRACT: this module NEVER raises. A sleeping/stale gateway (503), a refused
connection, or a malformed payload must degrade gracefully so the daily
pipeline keeps running. Every public function returns an empty/ok=False shape
on any error.

ONDS framing (Phase 3.5 #5): ONDS is a deliberate covered-call income position
(scaling toward ~100 shares, selling the $10.50 calls). overlay_book() tags it
CC-INCOME and never flags it as a red laggard.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import requests  # the dossier already depends on it
except Exception:  # pragma: no cover - requests should always be present
    requests = None  # type: ignore[assignment]


# ── Configuration ────────────────────────────────────────────

_BRIDGE_HOST = os.environ.get("IBKR_BRIDGE_HOST", "127.0.0.1")
_BRIDGE_PORT = os.environ.get("IBKR_BRIDGE_PORT", "8765")
BRIDGE_URL = os.environ.get(
    "IBKR_BRIDGE_URL", f"http://{_BRIDGE_HOST}:{_BRIDGE_PORT}"
).rstrip("/")

# Optional — only needed if the bridge ever gates read endpoints. The bridge
# reads BRIDGE_TOKEN for its order auth; accept either name here.
_BRIDGE_TOKEN = (
    os.environ.get("IBKR_BRIDGE_TOKEN")
    or os.environ.get("BRIDGE_TOKEN")
    or ""
).strip()

_TIMEOUT = float(os.environ.get("IBKR_BRIDGE_TIMEOUT", "10"))

# ONDS is a deliberate covered-call income hold — never a laggard to trim.
# (DAILY_REVIEW_PLAN.md Phase 3.5 #5). The $10.50 strike is the live CC strike.
_CC_INCOME_TICKERS = {"ONDS": {"cc_strike": 10.50, "scaling_to": 100}}


# ── Helpers ──────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    h = {"Accept": "application/json"}
    if _BRIDGE_TOKEN:
        # Harmless on read endpoints; future-proofs against a locked-down bridge.
        h["X-Bridge-Token"] = _BRIDGE_TOKEN
    return h


def _get(path: str) -> tuple[Any, str | None]:
    """GET <BRIDGE_URL><path>. Returns (parsed_json, error). Never raises.

    error is None on success; a short human string on any failure (the
    gateway being asleep returns a 503 from the bridge's _require_client()).
    """
    if requests is None:
        return None, "requests library unavailable"
    url = f"{BRIDGE_URL}{path}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=_TIMEOUT)
    except Exception as e:  # connection refused, timeout, DNS, etc.
        return None, f"connection error to {url}: {e}"
    if resp.status_code != 200:
        # 503 = bridge up but not connected to IB Gateway (asleep/stale).
        body = (resp.text or "").strip()
        return None, f"HTTP {resp.status_code} from {path}: {body[:160]}"
    try:
        return resp.json(), None
    except Exception as e:
        return None, f"bad JSON from {path}: {e}"


def _to_float(v: Any) -> float | None:
    """Coerce a value (incl. the bridge's string account values) to float."""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    # Guard against IB's no-value sentinel leaking through.
    if f != f or abs(f) >= 1e300:  # NaN or sentinel
        return None
    return f


def _normalize_position(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a bridge /positions row to the dossier's position shape.

    Note: the bridge's /positions does NOT carry per-position market price,
    market value, or unrealized P&L (its docstring overstates it — the
    underlying ib_async positions() call only returns position + avgCost).
    /pnl is account-level only. So `last`, `market_value`, `unrealized_pnl`
    and `daily_pnl` are left None here and can be enriched downstream (e.g.
    from the day's quotes the dossier already fetches). avg_price for STK is
    per-share; for OPT it is per-contract (multiplier-inclusive) as IB reports.
    """
    sec = (raw.get("secType") or "STK").upper()
    asset_class = {
        "STK": "stock",
        "OPT": "option",
        "FUT": "future",
        "IND": "index",
        "CASH": "fx",
    }.get(sec, sec.lower())

    qty = _to_float(raw.get("position"))
    avg = _to_float(raw.get("avgCost"))

    return {
        "ticker": (raw.get("symbol") or "").upper(),
        "qty": qty,
        "avg_price": avg,
        "last": None,            # not provided by the bridge /positions
        "market_value": None,    # derive downstream from a live quote
        "unrealized_pnl": None,  # /pnl is account-level, not per-position
        "daily_pnl": None,       # account-level only
        "asset_class": asset_class,
        # passthroughs handy for the overlay / option positions
        "account": raw.get("account"),
        "sec_type": sec,
        "exchange": raw.get("exchange"),
        "currency": raw.get("currency"),
        "strike": _to_float(raw.get("strike")) or None,
        "right": (raw.get("right") or "") or None,
        "expiry": (raw.get("expiry") or "") or None,
    }


# ── Public API ───────────────────────────────────────────────

def get_book() -> dict[str, Any]:
    """Pull live IBKR holdings from the local bridge.

    Returns:
        {
          "positions": [ {ticker, qty, avg_price, last, market_value,
                          unrealized_pnl, daily_pnl, asset_class, ...}, ... ],
          "account":   { ...flat account values, plus account-level pnl... },
          "ok":        bool,
          "error":     str   # only present when ok is False
        }

    NEVER raises. On any connection error / 503 / missing payload returns
    {"positions": [], "account": {}, "ok": False, "error": "..."} so a
    sleeping gateway can't break the pipeline.
    """
    raw_positions, pos_err = _get("/positions")
    if pos_err is not None or not isinstance(raw_positions, list):
        return {
            "positions": [],
            "account": {},
            "ok": False,
            "error": pos_err or "unexpected /positions payload",
        }

    positions = [
        _normalize_position(p)
        for p in raw_positions
        if isinstance(p, dict) and p.get("symbol")
    ]

    # /account — flat tag->string values. Best-effort; absence is non-fatal.
    raw_account, acct_err = _get("/account")
    account: dict[str, Any] = {}
    if isinstance(raw_account, dict):
        account = dict(raw_account)
        # Add numeric mirrors of the headline figures for convenience.
        for tag in ("NetLiquidation", "TotalCashValue", "BuyingPower",
                    "GrossPositionValue", "AvailableFunds", "ExcessLiquidity"):
            num = _to_float(raw_account.get(tag))
            if num is not None:
                account[f"{tag}_num"] = num

    # /pnl — account-level daily/unrealized/realized. Best-effort.
    raw_pnl, _pnl_err = _get("/pnl")
    if isinstance(raw_pnl, dict):
        account["dailyPnL"] = _to_float(raw_pnl.get("dailyPnL"))
        account["unrealizedPnL"] = _to_float(raw_pnl.get("unrealizedPnL"))
        account["realizedPnL"] = _to_float(raw_pnl.get("realizedPnL"))

    result: dict[str, Any] = {
        "positions": positions,
        "account": account,
        "ok": True,
    }
    # Surface a soft warning if account/pnl failed but positions succeeded.
    if acct_err is not None:
        result["account_error"] = acct_err
    return result


def overlay_book(
    positions: list[dict[str, Any]],
    signals_by_ticker: dict[str, list[str]] | None,
) -> list[dict[str, Any]]:
    """Tag each holding HOLD / ADD / TRIM / WATCH and flag signal overlaps.

    Placeholder confluence logic — real directional signals get wired later.
    `signals_by_ticker` maps a ticker to a list of signal-source labels that
    fired on it today, e.g. {"LPTH": ["triangle", "flow_bull"], "TEM": [...]}.

    Rules (deliberately simple for v1):
      - ONDS (and any _CC_INCOME_TICKERS): tagged CC-INCOME, never TRIM/red.
        Carries cc_strike + assignment context.
      - A holding with >=2 agreeing signal sources -> ADD (building confluence).
      - A holding with exactly 1 signal source     -> WATCH (newly on radar).
      - A holding with a bearish/sell signal        -> TRIM (hedge flag).
      - Otherwise                                   -> HOLD.

    Never raises; tolerates missing fields.
    """
    signals_by_ticker = signals_by_ticker or {}
    # Normalize the lookup to upper-case tickers.
    sig_map = {
        (str(k).upper()): (list(v) if isinstance(v, (list, tuple, set)) else [v])
        for k, v in signals_by_ticker.items()
    }

    out: list[dict[str, Any]] = []
    for pos in positions or []:
        if not isinstance(pos, dict):
            continue
        ticker = (pos.get("ticker") or pos.get("symbol") or "").upper()
        sources = [str(s) for s in sig_map.get(ticker, [])]
        bearish = [
            s for s in sources
            if any(w in s.lower() for w in ("bear", "sell", "trim", "short", "put"))
        ]

        tagged = dict(pos)
        tagged["signal_sources"] = sources
        tagged["overlap"] = bool(sources)

        cc = _CC_INCOME_TICKERS.get(ticker)
        if cc is not None:
            # Income hold — frame as covered-call, never a laggard to trim.
            tagged["action"] = "CC-INCOME"
            tagged["cc_strike"] = cc["cc_strike"]
            tagged["cc_scaling_to"] = cc["scaling_to"]
            tagged["note"] = (
                f"Covered-call income hold — selling ${cc['cc_strike']:.2f} "
                f"calls, scaling toward {cc['scaling_to']} sh. "
                "Frame on premium yield / assignment risk, not unrealized P&L."
            )
            tagged["suppress_concentration_flag"] = True
        elif bearish:
            tagged["action"] = "TRIM"
            tagged["note"] = f"Bearish signal(s): {', '.join(bearish)}"
        elif len(sources) >= 2:
            tagged["action"] = "ADD"
            tagged["note"] = f"Confluence ({len(sources)} legs): {', '.join(sources)}"
        elif len(sources) == 1:
            tagged["action"] = "WATCH"
            tagged["note"] = f"Newly on radar: {sources[0]}"
        else:
            tagged["action"] = "HOLD"
            tagged["note"] = "No fresh signal."

        out.append(tagged)
    return out


# ── CLI smoke test ───────────────────────────────────────────

if __name__ == "__main__":
    import json

    print(f"\n── IBKR Book (bridge: {BRIDGE_URL}) ──")
    book = get_book()
    print(f"  ok={book.get('ok')}  positions={len(book.get('positions', []))}")
    if not book.get("ok"):
        print(f"  graceful-degrade: error={book.get('error')!r}")
    else:
        acct = book.get("account", {})
        nlv = acct.get("NetLiquidation") or acct.get("NetLiquidation_num")
        print(f"  NetLiquidation={nlv}  dailyPnL={acct.get('dailyPnL')}")
        for p in book["positions"]:
            print(
                f"    {p['ticker']:6} {p['asset_class']:8} "
                f"qty={p['qty']} avg={p['avg_price']}"
            )
        # Demo the overlay with a couple of stub signals.
        demo_signals = {
            "LPTH": ["triangle", "flow_bull"],
            "TEM": ["flow_bull"],
            "KMI": ["flow_bear"],
        }
        print("\n── overlay_book() demo (stub signals) ──")
        for row in overlay_book(book["positions"], demo_signals):
            print(f"    {row['ticker']:6} -> {row['action']:9} {row['note']}")

    print("\n" + json.dumps(book, indent=2, default=str)[:1200])
    print()
