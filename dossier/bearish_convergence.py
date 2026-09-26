#!/usr/bin/env python3
"""
🐻🧭 Bearish Convergence — multi-screen agreement on the short side

`screener_convergence.py` sums grade weight across bullish-only screens and
deliberately excludes death_cross_screener, obv_divergence_screener, and
seasonality_screener because their A+ can mean either direction — mixing
that into a bullish sum would misrepresent conviction. This module is the
mirror it left as a TODO: it isolates the bearish-direction rows from those
direction-aware screens, adds the screens whose grade is *always* bearish
(death_cross, insider_selling_cluster), and reuses
`screener_convergence.compute_convergence` (already a pure, grade-weight
function agnostic to what "bullish" or "bearish" means) to rank tickers
multiple independent bearish lenses agree on.

Pure post-processing, same spirit as screener_convergence.py: reads
whatever `docs/api/*.json` screener outputs already exist on disk (no
network calls, no re-scanning). New bearish-oriented screens need an entry
in ALWAYS_BEARISH_SCREEN_FILES (whole leg counts) or
DIRECTION_AWARE_SCREEN_FILES (only rows with direction == "bearish" count);
nothing else in this module changes.

Usage (standalone, reads today's already-saved JSON from docs/api/):
    python -m dossier.bearish_convergence
    python -m dossier.bearish_convergence --json
    python -m dossier.bearish_convergence --min-screens 3

Output: docs/api/bearish-convergence-report.json (served via GitHub Pages)
"""

import argparse
import json
from pathlib import Path

from dossier.screener_convergence import _load_leg, compute_convergence

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Screens whose grade is UNAMBIGUOUSLY bearish — every row belongs in the sum.
ALWAYS_BEARISH_SCREEN_FILES = {
    "death_cross": "death-cross.json",
    "insider_selling_cluster": "insider-selling-cluster-screener.json",
}

# Screens that grade the strength of an edge that can point either way —
# only the rows marked direction == "bearish" belong in a bearish sum.
DIRECTION_AWARE_SCREEN_FILES = {
    "obv_divergence": "obv-divergence.json",
    "seasonality": "seasonality-screener.json",
}

BEARISH_SCREEN_FILES = {**ALWAYS_BEARISH_SCREEN_FILES, **DIRECTION_AWARE_SCREEN_FILES}


def _load_bearish_only(filename: str) -> list[dict]:
    """Keep only the bearish-direction rows from a direction-aware screen leg."""
    return [r for r in _load_leg(filename) if isinstance(r, dict) and r.get("direction") == "bearish"]


def load_bearish_legs() -> dict[str, list[dict]]:
    """Load every registered bearish leg, filtering direction-aware ones."""
    legs = {name: _load_leg(filename) for name, filename in ALWAYS_BEARISH_SCREEN_FILES.items()}
    legs.update({name: _load_bearish_only(filename) for name, filename in DIRECTION_AWARE_SCREEN_FILES.items()})
    return legs


def _save_api_output(convergence: dict) -> None:
    """Write machine-readable JSON to docs/api/bearish-convergence-report.json."""
    out_dir = PROJECT_ROOT / "docs" / "api"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bearish-convergence-report.json"
    out_path.write_text(json.dumps(convergence, indent=2))
    print(f"\n  💾  Saved {convergence['convergence_count']} bearish convergence tickers → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bearish Convergence — multi-screen agreement on the short side"
    )
    parser.add_argument("--min-screens", type=int, default=2,
                         help="Minimum number of screens a ticker must appear in (default 2)")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--no-save", action="store_true", help="Don't write JSON to docs/")
    args = parser.parse_args()

    convergence = compute_convergence(load_bearish_legs(), min_screens=args.min_screens)

    missing = sorted(set(BEARISH_SCREEN_FILES) - set(convergence["screens_loaded"]))

    if args.json:
        print(json.dumps(convergence, indent=2))
    else:
        loaded = ", ".join(convergence["screens_loaded"]) or "none"
        print(f"\n🐻🧭  Bearish Convergence — {convergence['convergence_count']} tickers "
              f"in {args.min_screens}+ bearish screens")
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
