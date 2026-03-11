"""
Document Ingestion Pipeline — Scan, chunk, embed, and store content.
"""

import time
from typing import Optional

from .config import DocType
from .chunker import (
    chunk_all, chunk_deep_dives, chunk_blog_entries, chunk_ticker_json,
    chunk_dossier, chunk_daily_picks, chunk_screener_history, Chunk
)
from .embeddings import embed_documents
from .store import upsert_chunks, get_collection


def _chunker_for_type(doc_type: str):
    """Get the chunker function for a specific doc type."""
    mapping = {
        "deep_dive": chunk_deep_dives,
        "deep_dives": chunk_deep_dives,
        "blog": chunk_blog_entries,
        "ticker_json": chunk_ticker_json,
        "dossier": chunk_dossier,
        "daily_picks": chunk_daily_picks,
        "screener": chunk_screener_history,
    }
    return mapping.get(doc_type)


def index(doc_type: Optional[str] = None, reset: bool = False,
          show_progress: bool = True) -> dict:
    """
    Index content into the vector store.

    Args:
        doc_type: specific type to index (None = all)
        reset: if True, wipe and rebuild the collection
        show_progress: print progress info

    Returns:
        Dict with stats about the indexing run
    """
    start = time.time()

    if reset:
        get_collection(reset=True)

    # Get chunks
    if doc_type:
        chunker = _chunker_for_type(doc_type)
        if not chunker:
            raise ValueError(f"Unknown doc_type: {doc_type}. "
                           f"Valid: deep_dives, blog, ticker_json, dossier, daily_picks, screener")
        if show_progress:
            print(f"📄 Chunking {doc_type}...")
        chunks = chunker()
    else:
        if show_progress:
            print("📄 Chunking all content...")
        chunks = chunk_all()

    if not chunks:
        if show_progress:
            print("⚠️  No chunks generated. Check that content exists in docs/")
        return {"chunks": 0, "elapsed": 0}

    # Count by type
    type_counts = {}
    for c in chunks:
        t = c.doc_type.value
        type_counts[t] = type_counts.get(t, 0) + 1

    if show_progress:
        print(f"📊 Generated {len(chunks)} chunks:")
        for t, count in sorted(type_counts.items()):
            print(f"   {t}: {count}")

    # Embed
    if show_progress:
        print(f"\n🧠 Embedding {len(chunks)} chunks with Gemini text-embedding-004...")

    texts = [c.text for c in chunks]
    embeddings = embed_documents(texts, show_progress=show_progress)

    # Store
    if show_progress:
        print(f"\n💾 Upserting {len(chunks)} chunks into ChromaDB...")

    upsert_chunks(chunks, embeddings)

    elapsed = time.time() - start

    if show_progress:
        print(f"\n✅ Indexing complete in {elapsed:.1f}s")
        print(f"   Total chunks: {len(chunks)}")
        collection = get_collection()
        print(f"   Collection size: {collection.count()}")

    return {
        "chunks": len(chunks),
        "by_type": type_counts,
        "elapsed_seconds": round(elapsed, 1),
    }
