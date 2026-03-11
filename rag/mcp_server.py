#!/usr/bin/env python3
"""
Ghost Alpha RAG MCP Server — AI agent access to the knowledge base.

Tools:
  rag_search(query, ticker?, doc_type?, top_k?) — Semantic search over Ghost Alpha content
  rag_ask(question, ticker?, doc_type?) — RAG-powered Q&A with Sam's voice
  rag_stats() — Collection stats (chunk counts, tickers, doc types)
  rag_reindex(doc_type?, reset?) — Reindex content into the vector store

Usage:
  python rag/mcp_server.py                    # Start SSE server on port 8005
  RAG_MCP_PORT=9000 python rag/mcp_server.py  # Custom port
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path so `rag` package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from fastmcp import FastMCP

mcp = FastMCP("GhostAlphaRAG")


@mcp.tool()
def rag_search(query: str, ticker: str = "", doc_type: str = "", top_k: int = 5) -> str:
    """Semantic search over Ghost Alpha content (deep dives, blog, dossier, ticker data, screener).

    Args:
        query: Natural language search query
        ticker: Optional ticker filter (e.g. "NVDA")
        doc_type: Optional filter: deep_dive, blog, ticker_json, dossier, daily_picks, screener
        top_k: Number of results (default 5)
    """
    from rag.query import search
    results = search(
        question=query,
        top_k=top_k,
        ticker=ticker or None,
        doc_type=doc_type or None,
    )

    if not results:
        return "No results found. Has the index been built? Run rag_reindex()."

    lines = [f"🔍 Top {len(results)} results for: \"{query}\"\n"]
    for i, r in enumerate(results):
        meta = r["metadata"]
        header = f"[{i+1}] {meta.get('doc_type', '?')}"
        if meta.get("ticker"):
            header += f" | {meta['ticker']}"
        if meta.get("date"):
            header += f" | {meta['date']}"
        header += f" (score: {r['score']:.3f})"
        lines.append(header)

        text = r["text"][:600] + "..." if len(r["text"]) > 600 else r["text"]
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def rag_ask(question: str, ticker: str = "", doc_type: str = "") -> str:
    """RAG-powered Q&A — retrieves relevant context and generates a grounded answer as Sam.

    Args:
        question: Natural language question about Ghost Alpha data
        ticker: Optional ticker filter
        doc_type: Optional filter: deep_dive, blog, ticker_json, dossier, daily_picks, screener
    """
    from rag.query import ask
    result = ask(
        question=question,
        ticker=ticker or None,
        doc_type=doc_type or None,
    )

    sources = []
    for s in result.get("sources", []):
        parts = [s["doc_type"]]
        if s.get("ticker"):
            parts.append(s["ticker"])
        if s.get("date"):
            parts.append(s["date"])
        sources.append(" | ".join(parts))

    output = result["answer"]
    if sources:
        output += f"\n\n📚 Sources: {', '.join(sources)}"

    return output


@mcp.tool()
def rag_stats() -> str:
    """Get Ghost Alpha vector store statistics — chunk counts, tickers, doc types."""
    from rag.store import get_stats
    stats = get_stats()

    if stats["total_chunks"] == 0:
        return "Vector store is empty. Run rag_reindex() to populate it."

    lines = [
        f"📊 Ghost Alpha Vector Store",
        f"Total chunks: {stats['total_chunks']}",
        f"Unique tickers: {stats['unique_tickers']}",
        "",
        "By document type:",
    ]
    for doc_type, count in sorted(stats["by_type"].items()):
        lines.append(f"  {doc_type}: {count}")
    lines.append(f"\nTickers: {', '.join(stats['tickers'][:30])}")

    return "\n".join(lines)


@mcp.tool()
def rag_reindex(doc_type: str = "", reset: bool = False) -> str:
    """Reindex Ghost Alpha content into the vector store.

    Args:
        doc_type: Optional — index only this type (deep_dives, blog, ticker_json, dossier, daily_picks, screener)
        reset: If true, wipe and rebuild the entire collection
    """
    from rag.ingest import index
    result = index(
        doc_type=doc_type or None,
        reset=reset,
        show_progress=True,
    )
    return f"✅ Indexed {result['chunks']} chunks in {result.get('elapsed_seconds', 0)}s\nBy type: {result.get('by_type', {})}"


if __name__ == "__main__":
    mcp.run(transport="sse")
