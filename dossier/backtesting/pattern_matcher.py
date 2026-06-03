#!/usr/bin/env python3
"""
🔮 Ghost Alpha — RAG Pattern Matcher

"Have we seen this movie before?"

For each of today's picks, finds historically similar technical setups
from the scan archive and reports what actually happened.

This is NOT a traditional backtest with fixed rules. It's a semantic
similarity search across real historical data — essentially asking:
  "Last time we had a FULL BULLISH stack + RSI 38 + Storm regime,
   what was the 5-day return?"

Usage:
    python dossier/backtesting/pattern_matcher.py               # Full analysis
    python dossier/backtesting/pattern_matcher.py --ticker NVDA  # Single ticker
    python dossier/backtesting/pattern_matcher.py --json         # Machine output

Pipeline integration:
    Runs after scan_logger, adds conviction scores to picks.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCAN_ARCHIVE = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"
PICKS_PATH = PROJECT_ROOT / "docs" / "api" / "daily-picks.json"


def _load_archive() -> list[dict]:
    """Load scan archive entries that have validated forward returns."""
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


def _setup_signature(entry: dict) -> str:
    """Build a natural language description of a setup for semantic matching."""
    parts = [f"{entry.get('ticker', '?')} technical setup"]

    # EMA Stack
    stack = entry.get("ema_stack", "UNKNOWN")
    parts.append(f"EMA Stack: {stack}")

    # Trend
    trend = entry.get("trend", "")
    if trend:
        parts.append(f"Trend: {trend}")

    crossover = entry.get("crossover", "")
    if crossover:
        parts.append(f"Crossover: {crossover}")

    # Oscillators
    rsi = entry.get("rsi_14")
    if rsi:
        zone = "oversold" if rsi < 30 else ("overbought" if rsi > 70 else "neutral")
        parts.append(f"RSI: {rsi:.1f} ({zone})")

    adx = entry.get("adx_14")
    if adx:
        strength = "strong" if adx > 40 else ("moderate" if adx > 25 else "weak")
        parts.append(f"ADX: {adx:.1f} ({strength} trend)")

    stoch = entry.get("stoch_k")
    if stoch:
        parts.append(f"Stochastic: {stoch:.1f}")

    # Volume
    rvol = entry.get("rel_vol")
    if rvol:
        parts.append(f"Relative Volume: {rvol:.1f}x")

    # Volatility
    iv = entry.get("iv")
    if iv:
        parts.append(f"IV: {iv}")

    # Market context
    regime = entry.get("regime", "")
    if regime:
        parts.append(f"Market Regime: {regime}")

    # Sector
    sector = entry.get("sector", "")
    if sector:
        parts.append(f"Sector: {sector}")

    # Grade
    grade = entry.get("grade", "")
    if grade:
        parts.append(f"Grade: {grade}")

    return " | ".join(parts)


def _similarity_score(pick: dict, historical: dict) -> float:
    """Compute a simple similarity score between two setups (0-1).

    This is a fast heuristic filter before semantic search.
    """
    score = 0.0
    weights = 0.0

    # EMA Stack match (most important)
    if pick.get("ema_stack") and historical.get("ema_stack"):
        weights += 3.0
        if pick["ema_stack"] == historical["ema_stack"]:
            score += 3.0

    # RSI zone match
    p_rsi = pick.get("rsi_14")
    h_rsi = historical.get("rsi_14")
    if p_rsi and h_rsi:
        weights += 2.0
        diff = abs(p_rsi - h_rsi)
        if diff < 5:
            score += 2.0
        elif diff < 10:
            score += 1.5
        elif diff < 20:
            score += 1.0

    # ADX strength match
    p_adx = pick.get("adx_14")
    h_adx = historical.get("adx_14")
    if p_adx and h_adx:
        weights += 1.5
        diff = abs(p_adx - h_adx)
        if diff < 5:
            score += 1.5
        elif diff < 15:
            score += 1.0

    # Crossover match
    if pick.get("crossover") and historical.get("crossover"):
        weights += 1.0
        if pick["crossover"] == historical["crossover"]:
            score += 1.0

    # Same sector
    if pick.get("sector") and historical.get("sector"):
        weights += 0.5
        if pick["sector"] == historical["sector"]:
            score += 0.5

    # Same regime
    if pick.get("regime") and historical.get("regime"):
        weights += 1.0
        if pick["regime"] == historical["regime"]:
            score += 1.0

    # Relative volume similarity
    p_rvol = pick.get("rel_vol")
    h_rvol = historical.get("rel_vol")
    if p_rvol and h_rvol:
        weights += 0.5
        if abs(p_rvol - h_rvol) < 0.5:
            score += 0.5

    return score / weights if weights > 0 else 0.0


def find_similar_setups(pick: dict, history: list[dict],
                        min_similarity: float = 0.5,
                        max_results: int = 10) -> list[dict]:
    """Find historically similar setups for a given pick."""
    matches = []

    for h in history:
        # Don't match against the same ticker on the same date
        if h.get("ticker") == pick.get("ticker") and h.get("date") == pick.get("date"):
            continue

        sim = _similarity_score(pick, h)
        if sim >= min_similarity:
            matches.append({
                "ticker": h.get("ticker", "?"),
                "date": h.get("date", "?"),
                "similarity": round(sim, 3),
                "ema_stack": h.get("ema_stack", "?"),
                "rsi": h.get("rsi_14"),
                "adx": h.get("adx_14"),
                "regime": h.get("regime", "?"),
                "grade": h.get("grade", "?"),
                "sector": h.get("sector", "?"),
                "fwd_1d": h.get("fwd_1d"),
                "fwd_3d": h.get("fwd_3d"),
                "fwd_5d": h.get("fwd_5d"),
                "fwd_10d": h.get("fwd_10d"),
                "fwd_21d": h.get("fwd_21d"),
            })

    # Sort by similarity desc
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches[:max_results]


def analyze_pick(pick: dict, history: list[dict]) -> dict:
    """Analyze a single pick against historical analogues."""
    similar = find_similar_setups(pick, history)

    if not similar:
        return {
            "ticker": pick.get("ticker", "?"),
            "grade": pick.get("grade", "?"),
            "analogues_found": 0,
            "verdict": "NO_DATA",
            "message": "No similar historical setups found yet — keep scanning.",
        }

    # Aggregate forward returns from similar setups
    returns_5d = [m["fwd_5d"] for m in similar if m.get("fwd_5d") is not None]

    if not returns_5d:
        return {
            "ticker": pick.get("ticker", "?"),
            "grade": pick.get("grade", "?"),
            "analogues_found": len(similar),
            "verdict": "PENDING",
            "message": f"Found {len(similar)} similar setups but returns not yet validated.",
        }

    avg_5d = sum(returns_5d) / len(returns_5d)
    win_rate = sum(1 for r in returns_5d if r > 0) / len(returns_5d) * 100
    best = max(returns_5d)
    worst = min(returns_5d)

    # Conviction assessment
    if avg_5d > 2 and win_rate > 60:
        verdict = "HIGH_CONVICTION"
        emoji = "🟢"
    elif avg_5d > 0 and win_rate > 50:
        verdict = "MODERATE"
        emoji = "🔵"
    elif avg_5d < -2 or win_rate < 40:
        verdict = "CAUTION"
        emoji = "🔴"
    else:
        verdict = "NEUTRAL"
        emoji = "⚪"

    return {
        "ticker": pick.get("ticker", "?"),
        "grade": pick.get("grade", "?"),
        "ema_stack": pick.get("ema_stack", "?"),
        "rsi": pick.get("rsi_14"),
        "regime": pick.get("regime", "?"),
        "analogues_found": len(similar),
        "returns_validated": len(returns_5d),
        "avg_5d": round(avg_5d, 2),
        "win_rate": round(win_rate, 1),
        "best_5d": round(best, 2),
        "worst_5d": round(worst, 2),
        "verdict": verdict,
        "emoji": emoji,
        "message": f"{emoji} Similar setups averaged {avg_5d:+.2f}% over 5 days ({win_rate:.0f}% WR, {len(returns_5d)} analogues)",
        "top_analogues": similar[:5],
    }


def run_pattern_match(ticker_filter: str = None) -> list[dict]:
    """Run pattern matching for today's picks."""
    history = _load_archive()
    if not history:
        print("❌ No validated historical data in scan archive yet.")
        print("   Run: python dossier/backtesting/scan_logger.py --update-returns")
        return []

    # Load today's picks
    if not PICKS_PATH.exists():
        print("❌ No daily-picks.json found")
        return []

    picks_data = json.loads(PICKS_PATH.read_text())
    picks = picks_data.get("picks", [])

    # Load full technicals for each pick
    results = []
    for pick in picks:
        ticker = pick.get("ticker", "")
        if ticker_filter and ticker != ticker_filter.upper():
            continue

        # Load the latest technical snapshot
        json_path = PROJECT_ROOT / "docs" / "ticker" / ticker / "latest.json"
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text())
                ta = data.get("technical_analysis", {})
                pick_snapshot = {
                    "ticker": ticker,
                    "grade": pick.get("grade", ""),
                    "score": pick.get("score", 0),
                    "ema_stack": ta.get("ema_stack", ""),
                    "rsi_14": ta.get("oscillators", {}).get("rsi_14"),
                    "adx_14": ta.get("oscillators", {}).get("adx_14"),
                    "stoch_k": ta.get("oscillators", {}).get("stoch_k"),
                    "crossover": ta.get("trend", {}).get("crossover", ""),
                    "rel_vol": ta.get("volume", {}).get("rel_vol"),
                    "iv": data.get("impliedVolatility"),
                    "sector": data.get("sector", ""),
                    "regime": "",  # Would come from dossier
                }
            except Exception:
                pick_snapshot = {"ticker": ticker, "grade": pick.get("grade", "")}
        else:
            pick_snapshot = {"ticker": ticker, "grade": pick.get("grade", "")}

        analysis = analyze_pick(pick_snapshot, history)
        results.append(analysis)

    return results


def print_results(results: list[dict]):
    """Pretty-print pattern match results."""
    print(f"\n🔮 Ghost Alpha Pattern Matcher — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    print("'Have we seen this movie before?'\n")

    for r in results:
        ticker = r["ticker"]
        grade = r.get("grade", "?")
        verdict = r.get("verdict", "?")

        print(f"  {r.get('emoji', '❓')} {ticker} (Grade {grade})")

        if verdict == "NO_DATA":
            print(f"     └─ {r['message']}")
        elif verdict == "PENDING":
            print(f"     └─ {r['message']}")
        else:
            print(f"     └─ {r['message']}")
            print(f"        Best: {r.get('best_5d', '?'):+.2f}% | Worst: {r.get('worst_5d', '?'):+.2f}%")

            # Show top analogues
            analogues = r.get("top_analogues", [])
            if analogues:
                print(f"        Analogues:")
                for a in analogues[:3]:
                    sim_pct = int(a["similarity"] * 100)
                    print(f"          {a['ticker']} ({a['date']}) — {sim_pct}% similar → 5d: {a.get('fwd_5d', '?'):+.2f}%")

        print()

    # Summary
    high = [r for r in results if r.get("verdict") == "HIGH_CONVICTION"]
    caution = [r for r in results if r.get("verdict") == "CAUTION"]
    if high:
        print(f"  🟢 HIGH CONVICTION: {', '.join(r['ticker'] for r in high)}")
    if caution:
        print(f"  🔴 CAUTION: {', '.join(r['ticker'] for r in caution)}")


def main():
    parser = argparse.ArgumentParser(description="🔮 Ghost Alpha Pattern Matcher")
    parser.add_argument("--ticker", type=str, help="Analyze a single ticker")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    results = run_pattern_match(ticker_filter=args.ticker)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
