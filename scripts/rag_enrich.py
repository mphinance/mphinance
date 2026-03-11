#!/usr/bin/env python3
"""
Substack Enrichment — RAG-powered comparison narratives for newsletters.

Generates "what changed since last week" comparisons for today's picks,
enriching Substack drafts with historical context from the vector store.

Usage:
    python scripts/rag_enrich.py                    # Today's gold pick
    python scripts/rag_enrich.py --ticker NVDA       # Specific ticker
    python scripts/rag_enrich.py --compare-weeks     # Compare last 2 dossiers
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def enrich_ticker(ticker: str) -> str:
    """Generate an enrichment narrative for a ticker using RAG context."""
    from rag.query import ask

    result = ask(
        question=f"What has changed for {ticker} recently? Compare the current "
                 f"technical setup, EMA stack, and grade to any previous analysis. "
                 f"Highlight shifts in trend, regime, or institutional signals.",
        ticker=ticker,
        top_k=8,
    )
    return result["answer"]


def enrich_gold_pick() -> str:
    """Enrich today's gold pick with historical comparison."""
    picks_path = PROJECT_ROOT / "docs" / "api" / "daily-picks.json"
    if not picks_path.exists():
        return "❌ No daily-picks.json found"

    data = json.loads(picks_path.read_text())
    picks = data.get("picks", [])
    if not picks:
        return "❌ No picks today"

    gold = picks[0]
    ticker = gold["ticker"]
    grade = gold.get("grade", "?")
    score = gold.get("score", 0)

    print(f"🥇 Enriching gold pick: {ticker} (Grade {grade}, Score {score})")

    narrative = enrich_ticker(ticker)

    header = (f"## 🥇 Gold Pick: {ticker}\n"
              f"**Grade {grade}** | Score: {score}/100\n\n")

    return header + narrative


def compare_dossiers() -> str:
    """Compare the last two dossier reports."""
    from rag.query import ask

    result = ask(
        question="Compare the two most recent Ghost Alpha Dossier reports. "
                 "What changed in market regime, VIX, gold/silver picks, "
                 "and signal counts? What's the trend?",
        doc_type="dossier",
        top_k=4,
    )
    return result["answer"]


def main():
    parser = argparse.ArgumentParser(description="RAG-powered Substack enrichment")
    parser.add_argument("--ticker", type=str, help="Enrich specific ticker")
    parser.add_argument("--compare-weeks", action="store_true", help="Compare recent dossiers")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    if args.ticker:
        print(enrich_ticker(args.ticker))
    elif args.compare_weeks:
        print(compare_dossiers())
    else:
        print(enrich_gold_pick())


if __name__ == "__main__":
    main()
