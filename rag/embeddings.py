"""
Gemini Embeddings Wrapper — Batch embedding with rate limiting.
"""

import os
import time
from typing import Optional

from google import genai
from google.genai import types

from .config import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE, EMBEDDING_TASK_TYPE, QUERY_TASK_TYPE


def _get_client() -> genai.Client:
    """Get a Gemini client, checking for API key."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY env var.\n"
            "Check VaultGuard: python -c \"from firebase_admin import credentials, firestore; ...\""
        )
    return genai.Client(api_key=api_key)


def embed_documents(texts: list[str], task_type: str = EMBEDDING_TASK_TYPE,
                    show_progress: bool = False) -> list[list[float]]:
    """
    Embed a list of texts using Gemini text-embedding-004.

    Handles batching and rate limiting automatically.
    Returns list of embedding vectors (same order as input).
    """
    client = _get_client()
    all_embeddings = []
    total = len(texts)

    for i in range(0, total, EMBEDDING_BATCH_SIZE):
        batch = texts[i:i + EMBEDDING_BATCH_SIZE]
        batch_num = i // EMBEDDING_BATCH_SIZE + 1
        total_batches = (total + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

        if show_progress:
            print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)...")

        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                )
            )
            all_embeddings.extend([e.values for e in result.embeddings])
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"  ⏳ Rate limited, waiting 30s...")
                time.sleep(30)
                # Retry this batch
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                    )
                )
                all_embeddings.extend([e.values for e in result.embeddings])
            else:
                raise

        # Small delay between batches to avoid rate limits
        if i + EMBEDDING_BATCH_SIZE < total:
            time.sleep(0.5)

    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single query text for retrieval."""
    client = _get_client()
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(
            task_type=QUERY_TASK_TYPE,
        )
    )
    return result.embeddings[0].values
