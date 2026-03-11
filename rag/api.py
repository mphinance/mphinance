"""
RAG FastAPI — HTTP endpoints for remote access to the Ghost Alpha knowledge base.

Mount this into any FastAPI app, or run standalone:
    uvicorn rag.api:app --port 8006

Endpoints:
    POST /rag/search  — Semantic search
    POST /rag/ask     — RAG Q&A
    GET  /rag/stats   — Collection stats
    POST /rag/reindex — Trigger reindex
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional


app = FastAPI(title="Ghost Alpha RAG", version="1.0")


class SearchRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    doc_type: Optional[str] = None
    top_k: int = 5


class AskRequest(BaseModel):
    question: str
    ticker: Optional[str] = None
    doc_type: Optional[str] = None
    top_k: int = 8


class ReindexRequest(BaseModel):
    doc_type: Optional[str] = None
    reset: bool = False


@app.post("/rag/search")
def api_search(req: SearchRequest):
    """Semantic search over Ghost Alpha content."""
    from .query import search
    results = search(
        question=req.query,
        top_k=req.top_k,
        ticker=req.ticker,
        doc_type=req.doc_type,
    )
    return {"results": results, "count": len(results)}


@app.post("/rag/ask")
def api_ask(req: AskRequest):
    """RAG-powered Q&A with Sam's voice."""
    from .query import ask
    result = ask(
        question=req.question,
        top_k=req.top_k,
        ticker=req.ticker,
        doc_type=req.doc_type,
    )
    return result


@app.get("/rag/stats")
def api_stats():
    """Collection stats."""
    from .store import get_stats
    return get_stats()


@app.post("/rag/reindex")
def api_reindex(req: ReindexRequest):
    """Trigger reindex of content."""
    from .ingest import index
    result = index(
        doc_type=req.doc_type,
        reset=req.reset,
        show_progress=False,
    )
    return result
