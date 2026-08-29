#!/usr/bin/env python3
"""
🎭 Insider Sentiment — net read across the buy-side and sell-side cluster screens

`insider_cluster_screener.py` flags 2+ distinct insiders buying together;
`insider_selling_cluster_screener.py` flags the exit-side mirror. Run
independently, neither ever tells you the thing that actually matters for a
writeup: is this name's insider activity CLEAN (buyers with no sellers
muddying the signal, or vice versa) or CONFLICTED (both clusters fired on
the same ticker in the same window — insiders disagreeing with each other)?

This module is pure post-processing, same spirit as screener_convergence.py:
it reads whatever docs/api/insider-*-cluster-screener.json already exist on
disk (no network calls, no re-scanning) and nets the two grades into one
signed score per ticker. Positive = net bullish (buy cluster stronger),
negative = net bearish (sell cluster stronger), and a ticker present in
BOTH source screens is flagged "conflicted" regardless of which side wins,
since insiders splitting on the same name in the same window is itself the
story.

Usage (standalone, reads today's already-saved JSON from docs/api/):
    python -m dossier.insider_sentiment
    python -m dossier.insider_sentiment --json

Output: docs/api/insider-sentiment.json (served via GitHub Pages)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Same grade scale as screener_convergence.py — reuse it rather than
# reinvent, so a "net_score" here is directly comparable in spirit.
_GRADE_WEIGHT = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}

BUY_FILE = "insider-cluster-screener.json"
SELL_FILE = "insider-selling-cluster-screener.json"


def compute_insider_sentiment(buy_results: list[dict], sell_results: list[dict]) -> dict:
    """
    Net insider-cluster buy and sell signals into one per-ticker sentiment read.

    Pure function — never raises on empty/malformed input; missing,
    non-list, or non-dict entries are treated as no hit from that side.

    Args:
        buy_results: results list from insider_cluster_screener.py (buying).
        sell_results: results list from insider_selling_cluster_screener.py (selling).

    Returns:
        {
          "generated_at": ISO timestamp,
          "buy_loaded": bool,       # buy screen had at least one result
          "sell_loaded": bool,      # sell screen had at least one result
          "counts": {"bullish": int, "bearish": int, "conflicted": int},
          "bullish": [{ticker, name, price, change_pct, market_cap,
                        net_score, buy: {...}, sell: None}, ...],
          "bearish": [{... "buy": None, "sell": {...}}, ...],
          "conflicted": [{... "buy": {...}, "sell": {...}}, ...],
        }
        Each of bullish/bearish is sorted strongest-first by abs(net_score);
        conflicted is sorted by combined activity (buy weight + sell weight).
    """
    by_ticker: dict[str, dict] = {}

    def _ingest(results, side):
        if not isinstance(results, list):
            return False
        loaded = False
        for r in results:
            if not isinstance(r, dict):
                continue
            ticker = r.get("ticker")
            grade = r.get("grade")
            if not ticker or grade not in _GRADE_WEIGHT:
                continue
            loaded = True
            entry = by_ticker.setdefault(ticker, {
                "ticker": ticker,
                "name": r.get("name", ticker),
                "price": r.get("price"),
                "change_pct": r.get("change_pct", 0),
                "market_cap": r.get("market_cap"),
                "buy": None,
                "sell": None,
            })
            entry[side] = {
                "score": r.get("score"),
                "grade": grade,
                "distinct_" + ("buyers" if side == "buy" else "sellers"):
                    r.get("distinct_buyers" if side == "buy" else "distinct_sellers"),
                "total_value": r.get("total_value"),
            }
        return loaded

    buy_loaded = _ingest(buy_results, "buy")
    sell_loaded = _ingest(sell_results, "sell")

    bullish, bearish, conflicted = [], [], []
    for ticker, entry in by_ticker.items():
        buy_w = _GRADE_WEIGHT[entry["buy"]["grade"]] if entry["buy"] else 0
        sell_w = _GRADE_WEIGHT[entry["sell"]["grade"]] if entry["sell"] else 0
        entry["net_score"] = buy_w - sell_w

        if entry["buy"] and entry["sell"]:
            conflicted.append(entry)
        elif entry["buy"]:
            bullish.append(entry)
        elif entry["sell"]:
            bearish.append(entry)

    bullish.sort(key=lambda e: e["net_score"], reverse=True)
    bearish.sort(key=lambda e: e["net_score"])
    conflicted.sort(
        key=lambda e: _GRADE_WEIGHT[e["buy"]["grade"]] + _GRADE_WEIGHT[e["sell"]["grade"]],
        reverse=True,
    )

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "buy_loaded": buy_loaded,
        "sell_loaded": sell_loaded,
        "counts": {
            "bullish": len(bullish),
            "bearish": len(bearish),
            "conflicted": len(conflicted),
        },
        "bullish": bullish,
        "bearish": bearish,
        "conflicted": conflicted,
    }


def _load_leg(filename: str) -> list[dict]:
    path = PROJECT_ROOT / "docs" / "api" / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("results", []) if isinstance(data, dict) else []


def _save_api_output(sentiment: dict) -> None:
    """Write machine-readable JSON to docs/api/insider-sentiment.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "insider-sentiment.json"
    out_path.write_text(json.dumps(sentiment, indent=2))
    total = sum(sentiment["counts"].values())
    print(f"\n  💾  Saved {total} insider-sentiment tickers → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Insider Sentiment — net read across insider buy/sell cluster screens"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    buy_results = _load_leg(BUY_FILE)
    sell_results = _load_leg(SELL_FILE)
    sentiment = compute_insider_sentiment(buy_results, sell_results)

    if args.json:
        print(json.dumps(sentiment, indent=2))
    else:
        if not sentiment["buy_loaded"]:
            print(f"  ⚠️  {BUY_FILE} not found or empty — run insider_cluster_screener.py first")
        if not sentiment["sell_loaded"]:
            print(f"  ⚠️  {SELL_FILE} not found or empty — run insider_selling_cluster_screener.py first")

        print(f"\n🎭  Insider Sentiment — {sentiment['counts']['bullish']} bullish, "
              f"{sentiment['counts']['bearish']} bearish, "
              f"{sentiment['counts']['conflicted']} conflicted")

        if sentiment["conflicted"]:
            print("\n  Conflicted (insiders split on the same name):")
            for e in sentiment["conflicted"]:
                print(f"    {e['ticker']:<6}  buy:{e['buy']['grade']}  sell:{e['sell']['grade']}  "
                      f"net:{e['net_score']:+d}")

        if sentiment["bullish"]:
            print("\n  Clean bullish (buy cluster, no selling noise):")
            for e in sentiment["bullish"]:
                print(f"    {e['ticker']:<6}  buy:{e['buy']['grade']}  net:{e['net_score']:+d}")

        if sentiment["bearish"]:
            print("\n  Clean bearish (sell cluster, no buying noise):")
            for e in sentiment["bearish"]:
                print(f"    {e['ticker']:<6}  sell:{e['sell']['grade']}  net:{e['net_score']:+d}")

    if not args.no_save:
        _save_api_output(sentiment)


if __name__ == "__main__":
    main()
