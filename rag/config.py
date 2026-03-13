"""
RAG Configuration — Models, paths, chunking params.
"""

import os
from enum import Enum
from pathlib import Path

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
TICKER_DIR = DOCS_DIR / "ticker"
API_DIR = DOCS_DIR / "api"
BLOG_PATH = PROJECT_ROOT / "landing" / "blog" / "blog_entries.json"
HANDOFF_PATH = PROJECT_ROOT / "GHOST_HANDOFF.md"
SUPERNOTE_DIR = PROJECT_ROOT / "data" / "supernote"  # Downloaded PDFs land here
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
SCAN_DATA_DIR = PROJECT_ROOT / "data" / "venus_scans"  # Historical screener CSVs from Venus
SCAN_ARCHIVE_PATH = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"

# === Embedding Model ===
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"
EMBEDDING_BATCH_SIZE = 20  # Gemini batch limit
EMBEDDING_DIMENSION = 768  # text-embedding-004 output dim

# === ChromaDB ===
COLLECTION_NAME = "ghost_alpha"

# === Chunking ===
CHUNK_MAX_CHARS = 2000  # ~500 tokens
CHUNK_OVERLAP_CHARS = 200  # overlap between chunks for context continuity


class DocType(str, Enum):
    DEEP_DIVE = "deep_dive"
    BLOG = "blog"
    TICKER_JSON = "ticker_json"
    DOSSIER = "dossier"
    SCREENER = "screener"
    DAILY_PICKS = "daily_picks"
    GIT_HISTORY = "git_history"
    HANDOFF = "handoff"
    SUPERNOTE = "supernote"
    KNOWLEDGE_BASE = "knowledge_base"
    SCAN_DATA = "scan_data"  # Venus historical screener entries
