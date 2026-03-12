#!/usr/bin/env python3
"""
Screen Health Monitor — Rolling WR tracker per screen with degradation alerts.

Reads the scan archive and computes rolling performance metrics per screen/strategy.
Flags screens that have degraded below 40% WR and surfaces the strongest performers.

Usage:
    python dossier/backtesting/screen_health.py          # Print health dashboard
    python dossier/backtesting/screen_health.py --json    # Output as JSON for API
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCAN_ARCHIVE = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"
HEALTH_API = PROJECT_ROOT / "docs" / "api" / "screen-health.json"


def _load_validated_entries() -> list[dict]:
    """Load entries that have forward returns filled in."""
    if not SCAN_ARCHIVE.exists():
        return []
    entries = []
    for line in SCAN_ARCHIVE.read_text().strip().split("\n"):
        if line.strip():
            try:
                e = json.loads(line)
                if e.get("fwd_5d") is not None:
                    entries.append(e)
            except json.JSONDecodeError:
                continue
    return entries


def compute_health(entries: list[dict], window: int = 20) -> dict:
    """Compute rolling health metrics per screen/strategy."""

    # Group by strategy/grade
    by_strategy = defaultdict(list)
    by_grade = defaultdict(list)
    by_regime = defaultdict(list)
    by_ema = defaultdict(list)

    for e in entries:
        strategy = e.get("strategy", e.get("grade", "Unknown"))
        if strategy == "SCREEN_HISTORY":
            strategy = e.get("strategy", "Unknown")

        by_strategy[strategy].append(e)
        by_grade[e.get("grade", "?")].append(e)
        by_regime[e.get("regime", "?")].append(e)
        by_ema[e.get("ema_stack", "?")].append(e)

    periods = [
        ("fwd_1d", "1d"),
        ("fwd_3d", "3d"),
        ("fwd_5d", "5d"),
        ("fwd_10d", "10d"),
        ("fwd_21d", "21d"),
    ]

    def _calc_group(group: list[dict], label: str) -> dict:
        """Calculate metrics for a group of entries."""
        # Use most recent `window` entries
        recent = sorted(group, key=lambda x: x.get("date", ""))[-window:]

        result = {
            "label": label,
            "total_entries": len(group),
            "window_size": len(recent),
            "periods": {},
            "alert": None,
        }

        for field, plabel in periods:
            vals = [e[field] for e in recent if e.get(field) is not None]
            if not vals:
                continue

            wr = sum(1 for v in vals if v > 0) / len(vals) * 100
            avg = sum(vals) / len(vals)
            best = max(vals)
            worst = min(vals)

            result["periods"][plabel] = {
                "win_rate": round(wr, 1),
                "avg_return": round(avg, 2),
                "best": round(best, 2),
                "worst": round(worst, 2),
                "n": len(vals),
            }

        # Alert logic
        p5d = result["periods"].get("5d", {})
        wr5 = p5d.get("win_rate", 50)
        avg5 = p5d.get("avg_return", 0)

        if wr5 < 30 and p5d.get("n", 0) >= 5:
            result["alert"] = "🔴 CRITICAL — WR below 30%, consider disabling"
        elif wr5 < 40 and p5d.get("n", 0) >= 5:
            result["alert"] = "🟡 DEGRADED — WR below 40%, review signal quality"
        elif wr5 >= 70 and p5d.get("n", 0) >= 5:
            result["alert"] = "🟢 STRONG — WR above 70%, increase allocation"
        elif avg5 < -3 and p5d.get("n", 0) >= 5:
            result["alert"] = "⚠️ BLEEDING — negative avg returns, check for regime mismatch"

        return result

    health = {
        "generated_at": datetime.now().isoformat(),
        "total_validated": len(entries),
        "window": window,
        "by_strategy": {},
        "by_grade": {},
        "by_regime": {},
        "by_ema_stack": {},
        "alerts": [],
    }

    # Strategy health
    for strat, group in sorted(by_strategy.items(), key=lambda x: -len(x[1])):
        if len(group) >= 3:
            result = _calc_group(group, strat)
            health["by_strategy"][strat] = result
            if result["alert"]:
                health["alerts"].append(f"{strat}: {result['alert']}")

    # Grade health
    for grade in ["A", "B", "C", "D"]:
        if grade in by_grade and len(by_grade[grade]) >= 3:
            health["by_grade"][grade] = _calc_group(by_grade[grade], f"Grade {grade}")

    # Regime health
    for regime, group in sorted(by_regime.items(), key=lambda x: -len(x[1])):
        if len(group) >= 3:
            health["by_regime"][regime] = _calc_group(group, regime)

    # EMA Stack health
    for ema, group in sorted(by_ema.items(), key=lambda x: -len(x[1])):
        if len(group) >= 3:
            health["by_ema_stack"][ema] = _calc_group(group, ema)

    return health


def print_dashboard(health: dict):
    """Pretty-print the health dashboard."""
    print(f"\n{'='*80}")
    print(f"  SCREEN HEALTH MONITOR — {health['total_validated']} validated entries")
    print(f"  Window: last {health['window']} picks per group")
    print(f"  Generated: {health['generated_at']}")
    print(f"{'='*80}")

    # Alerts first
    if health["alerts"]:
        print(f"\n  🚨 ALERTS:")
        for alert in health["alerts"]:
            print(f"    {alert}")

    # Strategy breakdown
    if health["by_strategy"]:
        print(f"\n  {'─'*75}")
        print(f"  BY STRATEGY:")
        print(f"  {'Strategy':30s} {'n':>3s}  {'1d WR':>6s}  {'5d WR':>6s}  {'5d Avg':>7s}  {'10d WR':>6s}  Alert")
        for strat, data in health["by_strategy"].items():
            p1 = data["periods"].get("1d", {})
            p5 = data["periods"].get("5d", {})
            p10 = data["periods"].get("10d", {})
            alert = "⚠️" if data["alert"] else "  "
            print(f"  {strat:30s} {data['window_size']:3d}  "
                  f"{p1.get('win_rate', 0):5.0f}%  "
                  f"{p5.get('win_rate', 0):5.0f}%  "
                  f"{p5.get('avg_return', 0):+6.2f}%  "
                  f"{p10.get('win_rate', 0):5.0f}%  "
                  f"{alert}")

    # Grade breakdown
    if health["by_grade"]:
        print(f"\n  {'─'*75}")
        print(f"  BY GRADE:")
        for grade, data in health["by_grade"].items():
            p5 = data["periods"].get("5d", {})
            alert_str = f" ← {data['alert']}" if data["alert"] else ""
            print(f"  Grade {grade}: {p5.get('win_rate', 0):.0f}% WR at 5d "
                  f"({p5.get('avg_return', 0):+.2f}%, n={p5.get('n', 0)}){alert_str}")

    # Regime breakdown
    if health["by_regime"]:
        print(f"\n  {'─'*75}")
        print(f"  BY REGIME:")
        for regime, data in health["by_regime"].items():
            p5 = data["periods"].get("5d", {})
            print(f"  {regime:12s}: {p5.get('win_rate', 0):.0f}% WR at 5d "
                  f"({p5.get('avg_return', 0):+.2f}%, n={p5.get('n', 0)})")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Screen Health Monitor")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--window", type=int, default=20, help="Rolling window size")
    args = parser.parse_args()

    entries = _load_validated_entries()
    if not entries:
        print("❌ No validated entries in scan archive yet")
        return

    health = compute_health(entries, window=args.window)

    if args.json:
        # Write API endpoint
        HEALTH_API.parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_API, "w") as f:
            json.dump(health, f, indent=2)
        print(f"✅ Screen health written to {HEALTH_API}")
    else:
        print_dashboard(health)


if __name__ == "__main__":
    main()
