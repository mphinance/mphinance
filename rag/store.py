"""
ChromaDB Vector Store — Collection management, upsert, and search.
"""

import chromadb
from pathlib import Path

from .config import VECTORSTORE_DIR, COLLECTION_NAME
from .embeddings import embed_query


def _get_client() -> chromadb.PersistentClient:
    """Get or create ChromaDB persistent client."""
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(VECTORSTORE_DIR))


def get_collection(reset: bool = False) -> chromadb.Collection:
    """Get or create the Ghost Alpha collection."""
    client = _get_client()
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  🗑️  Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass  # Collection doesn't exist yet

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def upsert_chunks(chunks: list, embeddings: list[list[float]]):
    """
    Upsert chunks with their embeddings into ChromaDB.

    Args:
        chunks: list of Chunk objects
        embeddings: corresponding embedding vectors
    """
    collection = get_collection()

    # ChromaDB wants string metadata values
    ids = [c.id for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {
            "doc_type": c.doc_type.value,
            "source": c.source,
        }
        # Add chunk-specific metadata (flatten to strings)
        for k, v in c.metadata.items():
            if v is not None and v != "":
                meta[k] = str(v)
        metadatas.append(meta)

    # Upsert in batches (ChromaDB handles large batches fine but let's be safe)
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.upsert(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )


def search(query: str, top_k: int = 5,
           where: dict = None, where_document: dict = None) -> list[dict]:
    """
    Semantic search over the collection.

    Args:
        query: natural language question
        top_k: number of results
        where: metadata filter (e.g. {"ticker": "NVDA"})
        where_document: document content filter

    Returns:
        List of dicts with keys: id, text, metadata, score
    """
    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = embed_query(query)

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(top_k, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    if where_document:
        kwargs["where_document"] = where_document

    results = collection.query(**kwargs)

    # Flatten results
    output = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            output.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # cosine distance → similarity
            })

    return output


def get_stats() -> dict:
    """Get collection statistics."""
    collection = get_collection()
    count = collection.count()

    if count == 0:
        return {"total_chunks": 0, "by_type": {}}

    # Sample metadata to get type distribution
    sample = collection.get(limit=count, include=["metadatas"])
    type_counts = {}
    ticker_set = set()

    for meta in sample["metadatas"]:
        doc_type = meta.get("doc_type", "unknown")
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        ticker = meta.get("ticker", "")
        if ticker:
            ticker_set.add(ticker)

    return {
        "total_chunks": count,
        "by_type": type_counts,
        "unique_tickers": len(ticker_set),
        "tickers": sorted(ticker_set),
    }
