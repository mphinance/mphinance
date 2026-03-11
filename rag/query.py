"""
RAG Query Engine — Search + Gemini-powered Q&A grounded in retrieved context.
"""

import os
from typing import Optional

from google import genai
from google.genai import types

from . import store


def search(question: str, top_k: int = 5,
           ticker: Optional[str] = None,
           doc_type: Optional[str] = None) -> list[dict]:
    """
    Semantic search with optional metadata filters.

    Args:
        question: natural language query
        top_k: number of results
        ticker: filter to specific ticker
        doc_type: filter to specific content type (deep_dive, blog, etc.)

    Returns:
        List of result dicts with text, metadata, score
    """
    where = {}
    if ticker:
        where["ticker"] = ticker.upper()
    if doc_type:
        where["doc_type"] = doc_type

    return store.search(
        query=question,
        top_k=top_k,
        where=where if where else None
    )


def ask(question: str, top_k: int = 8,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None) -> dict:
    """
    RAG-powered Q&A: retrieve relevant context, then generate grounded answer.

    Args:
        question: natural language question
        top_k: number of chunks to retrieve for context
        ticker: optional ticker filter
        doc_type: optional content type filter

    Returns:
        Dict with 'answer', 'sources', and 'context_chunks'
    """
    # Retrieve
    results = search(question, top_k=top_k, ticker=ticker, doc_type=doc_type)

    if not results:
        return {
            "answer": "No relevant content found in the vector store. Try running `python -m rag index` first.",
            "sources": [],
            "context_chunks": [],
        }

    # Build context
    context_parts = []
    sources = []
    for i, r in enumerate(results):
        context_parts.append(f"[Source {i+1}] (type: {r['metadata'].get('doc_type', '?')}, "
                           f"score: {r['score']:.3f})\n{r['text']}")
        source_info = {
            "doc_type": r["metadata"].get("doc_type", ""),
            "ticker": r["metadata"].get("ticker", ""),
            "date": r["metadata"].get("date", ""),
            "score": r["score"],
        }
        sources.append(source_info)

    context = "\n\n---\n\n".join(context_parts)

    # Generate answer with Gemini
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "answer": "No Gemini API key — showing raw search results instead.",
            "sources": sources,
            "context_chunks": [r["text"] for r in results],
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""You are Sam the Quant Ghost — a brilliant, sarcastic AI copilot for the Ghost Alpha trading platform.

Answer the following question using ONLY the provided context. Be specific, cite tickers and data points.
If the context doesn't contain enough info, say so — don't make things up.

Keep your answer concise but thorough. Use Sam's voice — sharp, witty, data-driven.

## Context (Retrieved from Ghost Alpha knowledge base)
{context}

## Question
{question}

## Answer (as Sam)"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
        )
    )

    return {
        "answer": response.text,
        "sources": sources,
        "context_chunks": [r["text"] for r in results],
    }
