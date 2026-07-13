#!/usr/bin/env python3
"""
🧭 Screener Convergence — multi-screen agreement across ALL screens, not just 3

`screener_overlap.py` finds tickers that clear the bar on 2+ of {TAO, VCP,
PEAD} because those three run inside the daily pipeline and their results
are already in memory. But the repo now has ten independent screens
(capitulation, golden cross, SMA-200 reclaim, 52-week high, NR7, RVOL,
sector rotation, plus TAO/VCP/PEAD) — most of them only get run ad hoc
(via the batch-scanner skill or standalone), so their scores never get a
chance to cross-confirm each other.

This module is pure post-processing, same spirit as screener_overlap.py:
it reads whatever `docs/api/*.json` screener outputs already exist on disk
(no network calls, no re-scanning) and ranks tickers by how many
*independent* screens flagged them today. A ticker that shows up in 4 of
these lenses at once is a much stronger "worth writing about" signal than
any single screen's A+ grade.

Screens that haven't been run today are simply absent from the count —
this never claims full coverage it doesn't have; the report lists exactly
which screens contributed.

Usage (standalone, reads today's already-saved JSON from docs/api/):
    python -m dossier.screener_convergence
    python -m dossier.screener_convergence --json
    python -m dossier.screener_convergence --min-screens 3

Output: docs/api/convergence-report.json (served via GitHub Pages)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Grade → numeric weight so "combined_score" reflects letter grades, not raw
# scores (each screener's 0-100 scale isn't directly comparable to another's
# — see each module's own docstring for its scoring rubric).
_GRADE_WEIGHT = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1}

# screen name -> its docs/api output filename. Not all follow the same
# "<name>-screener.json" convention (see each module's own "Output:" line),
# so this is an explicit registry rather than a glob guess.
SCREEN_FILES = {
    "tao": "tao-screener.json",
    "vcp": "vcp-screener.json",
    "pead": "pead-screener.json",
    "capitulation": "capitulation-screener.json",
    "golden_cross": "golden-cross.json",
    "sma200_reclaim": "sma200-reclaim.json",
    "high52": "high52-screener.json",
    "nr7": "nr7-screener.json",
    "rvol": "rvol-screener.json",
    "sector_rotation": "sector-rotation.json",
}


def compute_convergence(results_by_screen: dict[str, list[dict]], min_screens: int = 2) -> dict:
    """
    Find tickers appearing in `min_screens`+ of the given screens and rank them.

    Pure function — never raises on empty/malformed input; missing,
    non-list, or non-dict entries are treated as no hit from that screen.

    Args:
        results_by_screen: {screen_name: [{"ticker": ..., "grade": ..., "score": ...}, ...]}
        min_screens: minimum number of distinct screens a ticker must appear
            in to be included (default 2).

    Returns:
        {
          "generated_at": ISO timestamp,
          "screens_loaded": [screen names with at least one result],
          "min_screens": int,
          "convergence_count": int,
          "tickers": [
            {
              "ticker": str,
              "screen_count": int,
              "screens": ["capitulation", "tao", ...],
              "combined_grade_weight": int,   # sum of per-screen grade weights
              "details": {"tao": {"score": int, "grade": str}, ...},
            },
            ...
          ],
        }
    """
    by_ticker: dict[str, dict] = {}
    screens_loaded = []

    for screen_name, leg_results in results_by_screen.items():
        if not isinstance(leg_results, list) or not leg_results:
            continue
        screens_loaded.append(screen_name)
        for r in leg_results:
            if not isinstance(r, dict):
                continue
            ticker = r.get("ticker")
            grade = r.get("grade")
            score = r.get("score")
            if not ticker or grade not in _GRADE_WEIGHT:
                continue
            entry = by_ticker.setdefault(ticker, {"ticker": ticker, "details": {}})
            entry["details"][screen_name] = {"score": score, "grade": grade}

    convergence = []
    for ticker, entry in by_ticker.items():
        screens = sorted(entry["details"].keys())
        if len(screens) < min_screens:
            continue
        combined = sum(_GRADE_WEIGHT[d["grade"]] for d in entry["details"].values())
        convergence.append({
            "ticker": ticker,
            "screen_count": len(screens),
            "screens": screens,
            "combined_grade_weight": combined,
            "details": entry["details"],
        })

    convergence.sort(key=lambda e: (e["screen_count"], e["combined_grade_weight"]), reverse=True)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "screens_loaded": sorted(screens_loaded),
        "min_screens": min_screens,
        "convergence_count": len(convergence),
        "tickers": convergence,
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


def _save_api_output(convergence: dict) -> None:
    """Write machine-readable JSON to docs/api/convergence-report.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "convergence-report.json"
    out_path.write_text(json.dumps(convergence, indent=2))
    print(f"\n  💾  Saved {convergence['convergence_count']} convergence tickers → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Screener Convergence — multi-screen agreement across all screens"
    )
    parser.add_argument("--min-screens", type=int, default=2,
                         help="Minimum number of screens a ticker must appear in (default 2)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    results_by_screen = {name: _load_leg(filename) for name, filename in SCREEN_FILES.items()}
    convergence = compute_convergence(results_by_screen, min_screens=args.min_screens)

    missing = sorted(set(SCREEN_FILES) - set(convergence["screens_loaded"]))

    if args.json:
        print(json.dumps(convergence, indent=2))
    else:
        loaded = ", ".join(convergence["screens_loaded"]) or "none"
        print(f"\n🧭  Screener Convergence — {convergence['convergence_count']} tickers "
              f"in {args.min_screens}+ screens")
        print(f"  Screens loaded today: {loaded}")
        if missing:
            print(f"  Screens not run today (excluded, not zero-weighted): {', '.join(missing)}")
        print()
        for e in convergence["tickers"]:
            grades = ", ".join(f"{leg}:{d['grade']}" for leg, d in e["details"].items())
            print(f"  {e['ticker']:<6}  {e['screen_count']}x  {grades}")

    if not args.no_save:
        _save_api_output(convergence)


if __name__ == "__main__":
    main()
