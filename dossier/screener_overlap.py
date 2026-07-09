#!/usr/bin/env python3
"""
🎯 Screener Overlap — multi-screen agreement across TAO / VCP / PEAD

TAO (EMA-stack pullback), VCP (volatility contraction) and PEAD (post-earnings
drift) each hunt a *different* setup shape. When the same ticker clears the
bar on two or three of them simultaneously, that's not noise — it's three
independent lenses agreeing the stock is doing something right, and it's the
kind of cross-confirmation that turns "one more screener hit" into a name
worth writing about.

This module is pure post-processing: it takes the already-scored result
lists the three screener stages in generate.py produce (no extra network
calls, no re-scanning) and finds tickers that appear in 2+ of them.

Usage (standalone, reads today's already-saved JSON from docs/api/):
    python -m dossier.screener_overlap
    python -m dossier.screener_overlap --json

Output: docs/api/screener-overlap.json (served via GitHub Pages)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Grade → numeric weight so "combined_score" reflects letter grades, not raw
# scores (the three screeners' 0-100 scales aren't directly comparable —
# see each module's own docstring for its scoring rubric).
_GRADE_WEIGHT = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}


def compute_screener_overlap(
    tao_results: list[dict],
    vcp_results: list[dict],
    pead_results: list[dict],
) -> dict:
    """
    Find tickers appearing in 2+ of {TAO, VCP, PEAD} and rank the overlap.

    Pure function — never raises on empty/malformed input; missing or
    non-list args are treated as no hits from that screen.

    Returns:
        {
          "generated_at": ISO timestamp,
          "overlap_count": int,
          "tickers": [
            {
              "ticker": str,
              "screen_count": int,
              "screens": ["tao", "vcp", ...],
              "combined_grade_weight": int,   # sum of per-screen grade weights
              "details": {"tao": {"score": int, "grade": str}, ...},
            },
            ...
          ],
        }
    """
    legs = {"tao": tao_results, "vcp": vcp_results, "pead": pead_results}
    by_ticker: dict[str, dict] = {}

    for leg_name, leg_results in legs.items():
        if not isinstance(leg_results, list):
            continue
        for r in leg_results:
            if not isinstance(r, dict):
                continue
            ticker = r.get("ticker")
            grade = r.get("grade")
            score = r.get("score")
            if not ticker or grade not in _GRADE_WEIGHT:
                continue
            entry = by_ticker.setdefault(ticker, {"ticker": ticker, "details": {}})
            entry["details"][leg_name] = {"score": score, "grade": grade}

    overlap = []
    for ticker, entry in by_ticker.items():
        screens = sorted(entry["details"].keys())
        if len(screens) < 2:
            continue
        combined = sum(_GRADE_WEIGHT[d["grade"]] for d in entry["details"].values())
        overlap.append({
            "ticker": ticker,
            "screen_count": len(screens),
            "screens": screens,
            "combined_grade_weight": combined,
            "details": entry["details"],
        })

    overlap.sort(key=lambda e: (e["screen_count"], e["combined_grade_weight"]), reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overlap_count": len(overlap),
        "tickers": overlap,
    }


def _save_api_output(overlap: dict) -> None:
    """Write machine-readable JSON to docs/api/screener-overlap.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "screener-overlap.json"
    out_path.write_text(json.dumps(overlap, indent=2))
    print(f"\n  💾  Saved {overlap['overlap_count']} overlap tickers → {out_path}")


def _load_leg(name: str) -> list[dict]:
    path = PROJECT_ROOT / "docs" / "api" / f"{name}-screener.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("results", []) if isinstance(data, dict) else []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Screener Overlap — multi-screen agreement across TAO/VCP/PEAD"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    tao_results = _load_leg("tao")
    vcp_results = _load_leg("vcp")
    pead_results = _load_leg("pead")

    overlap = compute_screener_overlap(tao_results, vcp_results, pead_results)

    if args.json:
        print(json.dumps(overlap, indent=2))
    else:
        print(f"\n🎯  Screener Overlap — {overlap['overlap_count']} tickers in 2+ screens\n")
        for e in overlap["tickers"]:
            grades = ", ".join(f"{leg}:{d['grade']}" for leg, d in e["details"].items())
            print(f"  {e['ticker']:<6}  {e['screen_count']}x  {grades}")

    if not args.no_save:
        _save_api_output(overlap)


if __name__ == "__main__":
    main()
