"""
RAG CLI — Command-line interface for indexing and querying.

Usage:
    python -m rag index [--type TYPE] [--reset]
    python -m rag search "query" [--ticker TICKER] [--type TYPE] [--top-k N]
    python -m rag ask "question" [--ticker TICKER] [--type TYPE]
    python -m rag stats
"""

import argparse
import sys
import json


def cmd_index(args):
    """Index content into the vector store."""
    from .ingest import index
    result = index(
        doc_type=args.type,
        reset=args.reset,
        show_progress=True
    )
    return result


def cmd_search(args):
    """Semantic search over indexed content."""
    from .query import search
    query = " ".join(args.query)
    if not query:
        print("❌ Provide a search query")
        sys.exit(1)

    results = search(
        question=query,
        top_k=args.top_k,
        ticker=args.ticker,
        doc_type=args.type,
    )

    if not results:
        print("No results found. Run `python -m rag index` first?")
        return

    print(f"\n🔍 Top {len(results)} results for: \"{query}\"\n")
    for i, r in enumerate(results):
        score = r["score"]
        meta = r["metadata"]
        doc_type = meta.get("doc_type", "?")
        ticker = meta.get("ticker", "")
        date = meta.get("date", "")

        # Header
        header = f"[{i+1}] {doc_type}"
        if ticker:
            header += f" | {ticker}"
        if date:
            header += f" | {date}"
        header += f" (score: {score:.3f})"

        print(f"{'=' * 70}")
        print(header)
        print(f"{'─' * 70}")

        # Truncate long text for display
        text = r["text"]
        if len(text) > 500:
            text = text[:500] + "..."
        print(text)
        print()


def cmd_ask(args):
    """RAG-powered Q&A."""
    from .query import ask
    question = " ".join(args.query)
    if not question:
        print("❌ Provide a question")
        sys.exit(1)

    print(f"🤔 Asking: \"{question}\"")
    print(f"{'─' * 70}")

    result = ask(
        question=question,
        ticker=args.ticker,
        doc_type=args.type,
    )

    print(f"\n👻 Sam says:\n")
    print(result["answer"])

    if result["sources"]:
        print(f"\n{'─' * 70}")
        print(f"📚 Sources ({len(result['sources'])} chunks retrieved):")
        for s in result["sources"]:
            parts = [s["doc_type"]]
            if s.get("ticker"):
                parts.append(s["ticker"])
            if s.get("date"):
                parts.append(s["date"])
            parts.append(f"score: {s['score']:.3f}")
            print(f"   - {' | '.join(parts)}")


def cmd_stats(args):
    """Show collection stats."""
    from .store import get_stats
    stats = get_stats()

    if stats["total_chunks"] == 0:
        print("📊 Vector store is empty. Run `python -m rag index` to populate it.")
        return

    print(f"\n📊 Ghost Alpha Vector Store")
    print(f"{'=' * 40}")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Unique tickers: {stats['unique_tickers']}")
    print(f"\nBy document type:")
    for doc_type, count in sorted(stats["by_type"].items()):
        print(f"   {doc_type}: {count}")
    print(f"\nTickers: {', '.join(stats['tickers'][:20])}")
    if len(stats["tickers"]) > 20:
        print(f"   ... and {len(stats['tickers']) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        prog="rag",
        description="Ghost Alpha RAG — Semantic search over your trading data"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # index
    p_index = subparsers.add_parser("index", help="Index content into vector store")
    p_index.add_argument("--type", help="Index specific type (deep_dives, blog, ticker_json, dossier, daily_picks, screener)")
    p_index.add_argument("--reset", action="store_true", help="Wipe and rebuild the collection")

    # search
    p_search = subparsers.add_parser("search", help="Semantic search")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("--ticker", help="Filter by ticker")
    p_search.add_argument("--type", help="Filter by doc type")
    p_search.add_argument("--top-k", type=int, default=5, help="Number of results (default: 5)")

    # ask
    p_ask = subparsers.add_parser("ask", help="RAG-powered Q&A")
    p_ask.add_argument("query", nargs="+", help="Question to ask")
    p_ask.add_argument("--ticker", help="Filter by ticker")
    p_ask.add_argument("--type", help="Filter by doc type")

    # stats
    subparsers.add_parser("stats", help="Show collection stats")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "index": cmd_index,
        "search": cmd_search,
        "ask": cmd_ask,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
