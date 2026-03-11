# 🧠 RAG Vector Search — Ghost Alpha Knowledge Base

> Semantic search and AI Q&A across all Ghost Alpha data.
> Powered by Gemini text-embedding-004 + ChromaDB.

## Quick Start

```bash
# Index everything (reset = wipe and rebuild)
python -m rag index --reset

# Search (returns top-k relevant chunks)
python -m rag search "55 EMA on NVDA" --top-k 5

# Ask Sam (RAG-powered Q&A — retrieves context then generates answer)
python -m rag ask "What was DAKT's setup when it was first flagged?"

# Stats
python -m rag stats
```

---

## What's Indexed (9 Content Types)

| Type | Source | What You Can Ask |
|------|--------|-----------------|
| `ticker_json` | `docs/ticker/*/latest.json` + dated JSONs | "What's NVDA's EMA55?" "RSI on PLTR last Tuesday?" |
| `deep_dive` | `docs/ticker/*/deep_dive.md` | "Bull case for RKLB?" "What's the thesis on AVGO?" |
| `blog` | `landing/blog/blog_entries.json` | "What did we ship last week?" "When did we fix VoPR?" |
| `daily_picks` | `docs/api/daily-picks.json` | "Today's A-grade picks?" "Gold pick score?" |
| `dossier` | `docs/api/dossier-*.json` | "Current market regime?" "VIX level?" |
| `screener` | `docs/api/screener-history/` | "Weekly screener top signals?" |
| `git_history` | `git log` (200 commits) | "When did we add the MEME scanner?" |
| `handoff` | `GHOST_HANDOFF.md` + brain dirs | "What's left from last session?" |
| `supernote` | `data/supernote/` (txt/md) | "What did Michael write in his notes?" |

### Ticker Data Captured (Everything)

Every field from `latest.json` is flattened into searchable text:

- **EMAs**: 8, 21, 34, 55, 89 (individual values)
- **SMAs**: 50, 200 + crossover status (Golden/Death Cross)
- **EMA Stack**: FULL BULLISH / PARTIAL / TANGLED / BEARISH
- **Oscillators**: RSI(14), ADX(14), MACD histogram, Stochastic K
- **Pivots**: R2, R1, PP, S1, S2
- **Fibonacci**: 23.6%, 38.2%, 50%, 61.8%, 78.6%
- **Volatility**: IV, HV(30d), IV Rank, IV Percentile
- **Options**: Call/put volume, total OI, P/C ratio (vol + OI)
- **Expected Moves**: By expiration period
- **Market Snapshot**: Cap, beta, 52w range, analyst target
- **TradingView**: Recommendation (buy/sell/neutral counts)
- **Insiders**: Recent 3 transactions (name, type, shares)
- **SEC Insights**: Top 3 filings
- **TickerTrace**: ETF count, institutional signal direction/conviction
- **AI Synthesis**: Full AI analysis text

### Historical Snapshots

Dated JSON files (`2026-03-03.json`, `2026-03-04.json`, etc.) are indexed alongside `latest.json`. This enables time-series queries:

```bash
python -m rag ask "Compare DAKT's EMA stack on March 3 vs March 4"
```

---

## Architecture

```
rag/
├── __init__.py
├── __main__.py          # python -m rag entry point
├── cli.py               # CLI commands (index, search, ask, stats)
├── config.py            # Paths, DocType enum, embedding settings
├── chunker.py           # 9 chunker functions → Chunk dataclass
├── embeddings.py        # Gemini text-embedding-004 batch embedder
├── ingest.py            # Orchestrator: chunk → embed → upsert
├── query.py             # search() and ask() functions
├── store.py             # ChromaDB collection management
├── api.py               # FastAPI endpoints for remote access
└── mcp_server.py        # MCP server for AI agent access
```

### Data Flow

```
Source Files → chunker.py → Chunk objects → embeddings.py → vectors → ChromaDB
                                                                ↓
CLI/API/MCP ← query.py ← ChromaDB semantic search ← user query embedding
```

---

## Integrations

### 1. Pipeline Auto-Reindex

After every 5AM pipeline run, the RAG store is automatically refreshed:

```python
# In dossier/generate.py (post-pipeline)
from rag.ingest import index as rag_index
rag_index(reset=False, show_progress=False)
```

### 2. FastAPI (Remote Access)

```bash
# Start the API server
uvicorn rag.api:app --port 8300

# Endpoints:
GET  /rag/search?q=NVDA+EMA&top_k=5
GET  /rag/ask?q=How+did+DAKT+perform
GET  /rag/stats
POST /rag/reindex
```

### 3. MCP Server (AI Agent Access)

```bash
python rag/mcp_server.py
# Provides 4 tools: rag_search, rag_ask, rag_stats, rag_reindex
```

### 4. Discord Grounding

Sam's Discord summaries are enriched with RAG context. When someone mentions a ticker in Discord, the monitor extracts it and queries the RAG store for relevant data before generating the summary.

```python
# In scripts/sam_discord_monitor.py
context = _get_rag_context(message_text)
# Injects Ghost Alpha data into the Gemini prompt
```

### 5. Substack Enrichment

```bash
# Generate "what changed" narrative for a ticker
python scripts/rag_enrich.py --ticker RKLB

# Compare recent dossiers
python scripts/rag_enrich.py --compare-dossiers
```

---

## Configuration

All config in `rag/config.py`:

```python
EMBEDDING_MODEL = "text-embedding-004"    # Gemini embeddings
EMBEDDING_DIM = 768                       # Vector dimension
COLLECTION_NAME = "ghost_alpha"           # ChromaDB collection
CHUNK_SIZE = 1500                         # Max chars per chunk
CHUNK_OVERLAP = 200                       # Overlap between chunks
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"  # Vector store path
```

Requires `GEMINI_API_KEY` in `.env`.

---

## Adding New Content Sources

1. Add a `DocType` enum in `config.py`
2. Write a `chunk_your_source()` function in `chunker.py`
3. Add it to `chunk_all()` at the bottom of `chunker.py`
4. Run `python -m rag index --reset` to rebuild
