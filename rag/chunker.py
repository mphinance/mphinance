"""
Smart Document Chunker — Splits content by type with metadata preservation.
"""

import json
import re
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .config import (
    DocType, TICKER_DIR, BLOG_PATH, API_DIR,
    HANDOFF_PATH, SUPERNOTE_DIR, PROJECT_ROOT,
    SCAN_DATA_DIR, SCAN_ARCHIVE_PATH,
    CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS
)


@dataclass
class Chunk:
    """A single indexed chunk with metadata."""
    id: str
    text: str
    doc_type: DocType
    source: str  # file path or identifier
    metadata: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.md5(self.text.encode()).hexdigest()


def _split_text(text: str, max_chars: int = CHUNK_MAX_CHARS,
                overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Split text into overlapping chunks, breaking at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars

        # Try to break at paragraph boundary
        if end < len(text):
            # Look for double newline near the end
            break_point = text.rfind("\n\n", start + max_chars // 2, end)
            if break_point == -1:
                # Fall back to single newline
                break_point = text.rfind("\n", start + max_chars // 2, end)
            if break_point == -1:
                # Fall back to space
                break_point = text.rfind(" ", start + max_chars // 2, end)
            if break_point != -1:
                end = break_point + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)

    return chunks


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


# ============================================================
# Deep Dives — split on ## headers
# ============================================================

def chunk_deep_dives() -> list[Chunk]:
    """Chunk all deep_dive.md files by section headers."""
    chunks = []

    for ticker_dir in sorted(TICKER_DIR.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name
        deep_dive = ticker_dir / "deep_dive.md"
        if not deep_dive.exists():
            continue

        text = deep_dive.read_text(encoding="utf-8")
        if not text.strip():
            continue

        # Split on ## or ### headers
        sections = re.split(r'(?=^#{2,3}\s)', text, flags=re.MULTILINE)

        for i, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 50:
                continue

            # Extract section title
            title_match = re.match(r'^#{2,3}\s+(.+)', section)
            section_title = title_match.group(1) if title_match else f"Section {i}"

            # Further split if section is too long
            sub_chunks = _split_text(section)
            for j, sub in enumerate(sub_chunks):
                chunk_id = f"deep_dive_{ticker}_{i}_{j}"
                chunks.append(Chunk(
                    id=chunk_id,
                    text=f"[{ticker}] {sub}",
                    doc_type=DocType.DEEP_DIVE,
                    source=str(deep_dive),
                    metadata={
                        "ticker": ticker,
                        "section": section_title,
                        "chunk_index": j,
                    }
                ))

    return chunks


# ============================================================
# Blog Entries — each entry is one chunk
# ============================================================

def chunk_blog_entries() -> list[Chunk]:
    """Chunk blog entries from blog_entries.json."""
    chunks = []

    if not BLOG_PATH.exists():
        return chunks

    entries = json.loads(BLOG_PATH.read_text(encoding="utf-8"))

    for i, entry in enumerate(entries):
        date = entry.get("date", "unknown")
        ghost_log = entry.get("ghost_log", "")
        suggestions = entry.get("suggestions", "")
        period = entry.get("period", "")
        chart_ticker = entry.get("chart_ticker", "")

        # Clean HTML from ghost_log and suggestions
        clean_log = _strip_html(ghost_log)
        clean_suggestions = _strip_html(suggestions)

        if not clean_log or len(clean_log) < 20:
            continue

        text = f"Ghost Blog — {date}"
        if period:
            text += f" ({period})"
        text += f"\n\n{clean_log}"
        if clean_suggestions:
            text += f"\n\nSam's Suggestions: {clean_suggestions}"

        # Blog entries can be long — split if needed
        sub_chunks = _split_text(text)
        for j, sub in enumerate(sub_chunks):
            entry_key = entry.get("entry_key", f"{date}_{i}")
            chunk_id = f"blog_{entry_key}_{j}"
            chunks.append(Chunk(
                id=chunk_id,
                text=sub,
                doc_type=DocType.BLOG,
                source=str(BLOG_PATH),
                metadata={
                    "date": date,
                    "period": period,
                    "ticker": chart_ticker,
                    "commits": entry.get("commits", 0),
                    "files_changed": entry.get("files_changed", 0),
                }
            ))

    return chunks


# ============================================================
# Ticker JSON — flatten structured data to prose
# ============================================================

def _flatten_ticker_json(ticker: str, data: dict) -> str:
    """Convert ticker JSON to readable prose for embedding — captures ALL technical data."""
    lines = [f"[{ticker}] Market Data Summary"]

    # Basic info
    name = data.get("companyName", ticker)
    price = data.get("currentPrice", 0)
    change_pct = data.get("priceChangePct", 0)
    sector = data.get("sector", "")
    industry = data.get("industry", "")
    lines.append(f"{name} ({ticker}) — {sector}/{industry}")
    lines.append(f"Price: ${price:.2f} ({change_pct:+.2f}%)")

    # Trend
    trend = data.get("trendOverall", "")
    if trend:
        lines.append(f"Overall Trend: {trend} | Short: {data.get('trendShort', '')} | Med: {data.get('trendMed', '')} | Long: {data.get('trendLong', '')}")

    # Technicals — capture EVERYTHING
    ta = data.get("technical_analysis", {})
    if ta:
        # EMA Stack status
        ema_stack = ta.get("ema_stack", "")
        if ema_stack:
            lines.append(f"EMA Stack: {ema_stack}")

        # Individual EMA values
        emas = ta.get("ema", {})
        if emas:
            ema_parts = [f"EMA{k}=${v}" for k, v in sorted(emas.items(), key=lambda x: int(x[0]))]
            lines.append(f"EMAs: {', '.join(ema_parts)}")

        # Trend + SMAs
        trend_info = ta.get("trend", {})
        if trend_info:
            sma50 = trend_info.get("sma_50", "N/A")
            sma200 = trend_info.get("sma_200", "N/A")
            crossover = trend_info.get("crossover", "None")
            outlook = trend_info.get("outlook", "")
            lines.append(f"SMA 50: ${sma50} | SMA 200: ${sma200} | Crossover: {crossover} | Outlook: {outlook}")

        # Oscillators — ALL of them
        osc = ta.get("oscillators", {})
        if osc:
            lines.append(f"RSI(14): {osc.get('rsi_14', 'N/A')} | ADX(14): {osc.get('adx_14', 'N/A')} | MACD Hist: {osc.get('macd_hist', 'N/A')} | Stoch K: {osc.get('stoch_k', 'N/A')}")

        # Pivot Points
        pivots = ta.get("pivots", {})
        if pivots:
            pivot_parts = [f"{k}: ${v}" for k, v in sorted(pivots.items())]
            lines.append(f"Pivots: {', '.join(pivot_parts)}")

        # Fibonacci levels
        fibs = ta.get("fibonacci", {})
        if fibs:
            fib_parts = [f"{k}%: ${v}" for k, v in sorted(fibs.items(), key=lambda x: float(x[0]), reverse=True)]
            lines.append(f"Fibonacci: {', '.join(fib_parts)}")

        # Volume
        vol = ta.get("volume", {})
        if vol:
            lines.append(f"Volume: {vol.get('current', 'N/A')} (Avg 20d: {vol.get('avg_20d', 'N/A')}) | Rel Vol: {vol.get('rel_vol', 'N/A')}x ({vol.get('rel_vol_pct', 'N/A')}%)")

    # Valuation
    val = data.get("valuation", {})
    if val:
        lines.append(f"Valuation: {val.get('status', 'N/A')} — Target ${val.get('target_price', 0):.2f} ({val.get('gap_pct', 0):.1f}% gap) via {val.get('method', '')}")

    # Scores
    scores = data.get("scores", {})
    if scores:
        lines.append(f"Grade: {scores.get('grade', 'N/A')} (Tech: {scores.get('technical', 0)}, Fund: {scores.get('fundamental', 0)})")

    # AI analysis
    ai = data.get("ai_analysis", "")
    if ai:
        clean_ai = _strip_html(ai)
        lines.append(f"AI Synthesis: {clean_ai}")

    # Volatility & Options
    iv = data.get("impliedVolatility")
    hv = data.get("historicVolatility")
    iv_rank = data.get("ivRank")
    iv_pct = data.get("ivPercentile")
    if any(v is not None for v in [iv, hv, iv_rank, iv_pct]):
        lines.append(f"IV: {iv} | HV(30d): {hv} | IV Rank: {iv_rank} | IV Percentile: {iv_pct}")

    vol_stats = data.get("volumeStats", {})
    if vol_stats:
        lines.append(f"Options Volume — Calls: {vol_stats.get('callVolume', 'N/A')} | Puts: {vol_stats.get('putVolume', 'N/A')} | Total: {vol_stats.get('totalVolume', 'N/A')} | P/C Vol: {vol_stats.get('pcRatioVol', 'N/A')}")
        lines.append(f"Open Interest — Calls: {vol_stats.get('callOpenInt', 'N/A')} | Puts: {vol_stats.get('putOpenInt', 'N/A')} | Total: {vol_stats.get('totalOpenInt', 'N/A')} | P/C OI: {vol_stats.get('pcRatioOi', 'N/A')}")

    # Expected Moves
    exp_moves = data.get("expectedMoves", [])
    if exp_moves:
        move_strs = [f"{m.get('period', '?')}: ±{m.get('move_pct', '?')}%" for m in exp_moves if isinstance(m, dict)]
        if move_strs:
            lines.append(f"Expected Moves: {' | '.join(move_strs)}")

    # Market Snapshot
    snap = data.get("market_snapshot", {})
    if snap:
        parts = []
        if snap.get("market_cap"):
            parts.append(f"Cap: {snap['market_cap']}")
        if snap.get("beta"):
            parts.append(f"Beta: {snap['beta']}")
        if snap.get("range_52w"):
            parts.append(f"52w: {snap['range_52w']}")
        if snap.get("analyst_target"):
            parts.append(f"Analyst Target: ${snap['analyst_target']}")
        if parts:
            lines.append(f"Snapshot: {' | '.join(parts)}")

    # TradingView
    tv = data.get("tradingview", {})
    if tv:
        rec = tv.get("recommendation", "")
        buy = tv.get("buy", 0)
        sell = tv.get("sell", 0)
        neutral = tv.get("neutral", 0)
        if rec:
            lines.append(f"TradingView: {rec} (Buy: {buy}, Sell: {sell}, Neutral: {neutral})")

    # Insider Transactions
    insiders = data.get("insider_transactions", [])
    if insiders:
        insider_lines = []
        for txn in insiders[:3]:
            if isinstance(txn, dict):
                name = txn.get("name", "?")
                action = txn.get("transactionType", txn.get("action", "?"))
                shares = txn.get("shares", "?")
                insider_lines.append(f"{name}: {action} ({shares} shares)")
        if insider_lines:
            lines.append(f"Insiders: {'; '.join(insider_lines)}")

    # SEC Insights
    sec = data.get("sec_insights")
    if sec:
        if isinstance(sec, (list, tuple)):
            lines.append(f"SEC Insights: {', '.join(str(s) for s in list(sec)[:3])}")
        elif isinstance(sec, str):
            lines.append(f"SEC Insights: {sec[:200]}")

    # TickerTrace
    tt = data.get("tickertrace", {})
    if tt:
        detail = tt.get("detail", {})
        fund_count = detail.get("fundCount", 0)
        if fund_count:
            lines.append(f"Held by {fund_count} ETFs (TickerTrace)")
        signal = tt.get("signal", {})
        direction = signal.get("direction", "")
        conviction = signal.get("conviction", 0)
        if direction:
            lines.append(f"Institutional Signal: {direction.upper()} (conviction: {conviction:.1f})")

    return "\n".join(lines)


def chunk_ticker_json() -> list[Chunk]:
    """Chunk ticker JSON files — latest.json AND historical dated snapshots."""
    chunks = []

    for ticker_dir in sorted(TICKER_DIR.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name

        # Collect all JSON files: latest.json + dated snapshots (2026-03-11.json)
        json_files = []
        latest = ticker_dir / "latest.json"
        if latest.exists():
            json_files.append(latest)

        # Historical dated snapshots for backtesting
        for dated_json in sorted(ticker_dir.glob("2???-??-??.json")):
            # Skip if it's the same day as latest (avoid duplicates)
            if latest.exists():
                try:
                    latest_data = json.loads(latest.read_text(encoding="utf-8"))
                    latest_date = latest_data.get("generated_at", "")[:10]
                    if dated_json.stem == latest_date:
                        continue
                except Exception:
                    pass
            json_files.append(dated_json)

        for json_path in json_files:
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            text = _flatten_ticker_json(ticker, data)
            if len(text) < 50:
                continue

            date = data.get("generated_at", json_path.stem)
            is_historical = json_path.name != "latest.json"
            chunk_id = f"ticker_json_{ticker}_{json_path.stem}" if is_historical else f"ticker_json_{ticker}"

            chunks.append(Chunk(
                id=chunk_id,
                text=text,
                doc_type=DocType.TICKER_JSON,
                source=str(json_path),
                metadata={
                    "ticker": ticker,
                    "price": data.get("currentPrice", 0),
                    "grade": data.get("scores", {}).get("grade", ""),
                    "trend": data.get("trendOverall", ""),
                    "date": date,
                    "historical": is_historical,
                }
            ))

    return chunks


# ============================================================
# Dossier Summary — daily market intel
# ============================================================

def chunk_dossier() -> list[Chunk]:
    """Chunk dossier summary JSON into prose."""
    chunks = []

    for json_file in sorted(API_DIR.glob("dossier-*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        meta = data.get("meta", {})
        date = meta.get("date", json_file.stem)
        market = data.get("market", {})
        picks = data.get("picks", {})
        signals = data.get("signals", {})
        sam = data.get("sam", {})
        narrative = data.get("narrative", {})

        lines = [f"Ghost Alpha Dossier — {date}"]

        # Market
        spy = market.get("spy", {})
        qqq = market.get("qqq", {})
        vix = market.get("vix", 0)
        regime = market.get("regime", "")
        lines.append(f"SPY: ${spy.get('price', 0):.2f} ({spy.get('change_pct', 0):+.2f}%) | QQQ: ${qqq.get('price', 0):.2f} | VIX: {vix} | Regime: {regime}")

        # Picks
        for tier in ["gold", "silver", "bronze"]:
            pick = picks.get(tier, {})
            if pick.get("ticker"):
                lines.append(f"{tier.title()} Pick: {pick['ticker']} (Score: {pick.get('score', 0)}, Grade: {pick.get('grade', '')})")

        # Signals
        sig_count = signals.get("count", 0)
        if sig_count:
            lines.append(f"Total Signals: {sig_count}")
            top5 = signals.get("top_5", [])
            for s in top5:
                lines.append(f"  - {s.get('symbol', '?')} via {s.get('strategy', '?')} (score: {s.get('score', 0)})")

        # Narrative
        one_liner = narrative.get("one_liner", "")
        if one_liner:
            lines.append(f"Narrative: {one_liner}")

        # Sam
        quote = sam.get("quote", "")
        if quote:
            lines.append(f"Sam's Quote: \"{quote}\"")

        text = "\n".join(lines)
        chunk_id = f"dossier_{json_file.stem}"
        chunks.append(Chunk(
            id=chunk_id,
            text=text,
            doc_type=DocType.DOSSIER,
            source=str(json_file),
            metadata={
                "date": date,
                "regime": regime,
                "vix": vix,
                "gold_pick": picks.get("gold", {}).get("ticker", ""),
            }
        ))

    return chunks


# ============================================================
# Daily Picks
# ============================================================

def chunk_daily_picks() -> list[Chunk]:
    """Chunk daily-picks.json into per-pick entries."""
    chunks = []
    picks_path = API_DIR / "daily-picks.json"
    if not picks_path.exists():
        return chunks

    try:
        data = json.loads(picks_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return chunks

    # Handle nested format: {"picks": [...], "all_ranked": [...]}
    if isinstance(data, dict):
        picks_list = data.get("picks", [])
        # Also include all_ranked if available
        all_ranked = data.get("all_ranked", [])
        data = picks_list + [r for r in all_ranked if r.get("ticker") not in
                             {p.get("ticker") for p in picks_list}]

    for i, pick in enumerate(data):
        ticker = pick.get("ticker", pick.get("symbol", ""))
        if not ticker:
            continue

        lines = [f"Daily Pick: {ticker}"]
        for key in ["score", "grade", "strategy", "entry", "target", "stop",
                     "upside_pct", "sector", "industry", "name"]:
            val = pick.get(key)
            if val:
                lines.append(f"  {key}: {val}")

        text = "\n".join(lines)
        chunks.append(Chunk(
            id=f"daily_pick_{ticker}_{i}",
            text=text,
            doc_type=DocType.DAILY_PICKS,
            source=str(picks_path),
            metadata={"ticker": ticker, "grade": pick.get("grade", "")}
        ))

    return chunks


# ============================================================
# Screener History
# ============================================================

def chunk_screener_history() -> list[Chunk]:
    """Chunk screener history snapshots."""
    chunks = []
    history_dir = API_DIR / "screener-history"
    if not history_dir.exists():
        return chunks

    for json_file in sorted(history_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        date = json_file.stem  # e.g. "2026-03-01"

        # Screener data can be large — extract top signals only
        if isinstance(data, dict):
            strategies = data.get("strategies", data)
            lines = [f"Ghost Alpha Screener — {date}"]
            for strat_name, signals in strategies.items():
                if isinstance(signals, list) and signals:
                    top = signals[:5]
                    tickers = [s.get("ticker", s.get("symbol", "?")) for s in top]
                    lines.append(f"  {strat_name}: {', '.join(tickers)}")

            text = "\n".join(lines)
        elif isinstance(data, list):
            lines = [f"Ghost Alpha Screener — {date}"]
            for item in data[:10]:
                ticker = item.get("ticker", item.get("symbol", "?"))
                strat = item.get("strategy", "")
                score = item.get("score", "")
                lines.append(f"  {ticker} — {strat} (score: {score})")
            text = "\n".join(lines)
        else:
            continue

        if len(text) < 30:
            continue

        # Split if very large
        sub_chunks = _split_text(text)
        for j, sub in enumerate(sub_chunks):
            chunks.append(Chunk(
                id=f"screener_{date}_{j}",
                text=sub,
                doc_type=DocType.SCREENER,
                source=str(json_file),
                metadata={"date": date}
            ))

    return chunks


# ============================================================
# Git Commit History
# ============================================================

def chunk_git_history(max_commits: int = 200) -> list[Chunk]:
    """Chunk git commit history into groups of 10."""
    import subprocess
    chunks = []

    try:
        result = subprocess.run(
            ['git', 'log', f'--max-count={max_commits}',
             '--format=%H|%ai|%s'],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode != 0:
            return chunks
    except Exception:
        return chunks

    lines = result.stdout.strip().split('\n')
    if not lines or not lines[0]:
        return chunks

    # Group commits in batches of 10
    batch_size = 10
    for i in range(0, len(lines), batch_size):
        batch = lines[i:i + batch_size]
        batch_lines = ["Git Commit History"]
        dates = []
        for line in batch:
            parts = line.split('|', 2)
            if len(parts) == 3:
                sha, date, msg = parts
                short_sha = sha[:7]
                short_date = date[:10]
                dates.append(short_date)
                batch_lines.append(f"  [{short_sha}] {short_date}: {msg}")

        text = '\n'.join(batch_lines)
        date_range = f"{dates[-1]}_to_{dates[0]}" if dates else str(i)
        chunks.append(Chunk(
            id=f"git_history_{i}",
            text=text,
            doc_type=DocType.GIT_HISTORY,
            source="git log",
            metadata={"date": dates[0] if dates else "", "batch": i // batch_size}
        ))

    return chunks


# ============================================================
# GHOST_HANDOFF — session continuity notes
# ============================================================

def chunk_handoff() -> list[Chunk]:
    """Chunk GHOST_HANDOFF.md by section headers."""
    chunks = []

    if not HANDOFF_PATH.exists():
        return chunks

    text = HANDOFF_PATH.read_text(encoding='utf-8')
    if not text.strip():
        return chunks

    # Also check for handoff files in the .gemini brain dirs
    handoff_files = [HANDOFF_PATH]
    brain_dir = Path.home() / '.gemini' / 'antigravity' / 'brain'
    if brain_dir.exists():
        for conv_dir in brain_dir.iterdir():
            handoff = conv_dir / 'GHOST_HANDOFF.md'
            if handoff.exists() and handoff != HANDOFF_PATH:
                handoff_files.append(handoff)

    for hf in handoff_files:
        text = hf.read_text(encoding='utf-8').strip()
        if not text or len(text) < 30:
            continue

        # Split on ## headers
        sections = re.split(r'(?=^#{1,2}\s)', text, flags=re.MULTILINE)

        for i, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 20:
                continue

            title_match = re.match(r'^#{1,2}\s+(.+)', section)
            title = title_match.group(1) if title_match else f"Section {i}"

            # Extract date from title if present
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
            date = date_match.group(1) if date_match else ""

            source_name = 'GHOST_HANDOFF.md' if hf == HANDOFF_PATH else str(hf)
            chunk_id = f"handoff_{hf.parent.name}_{i}"

            sub_chunks = _split_text(section)
            for j, sub in enumerate(sub_chunks):
                chunks.append(Chunk(
                    id=f"{chunk_id}_{j}",
                    text=f"GHOST HANDOFF: {sub}",
                    doc_type=DocType.HANDOFF,
                    source=source_name,
                    metadata={"section": title, "date": date}
                ))

    return chunks


# ============================================================
# Supernote PDFs — handwritten notes (text-extracted)
# ============================================================

def chunk_supernote() -> list[Chunk]:
    """Chunk Supernote PDF text extracts from data/supernote/.

    Expects either .txt files (pre-extracted) or .pdf files.
    For PDFs, attempts basic text extraction.
    Download from Google Drive first:
        gdown --folder 1UCPHJBoZSo9a0mP3O0eW8C7ra5kbmZjk -O data/supernote/
    """
    chunks = []

    if not SUPERNOTE_DIR.exists():
        return chunks

    # Process .txt files (pre-extracted OCR)
    for txt_file in sorted(SUPERNOTE_DIR.glob('*.txt')):
        text = txt_file.read_text(encoding='utf-8').strip()
        if not text or len(text) < 30:
            continue

        # Extract date from filename (YYYYMMDD_HHMMSS.txt)
        date_match = re.match(r'(\d{8})', txt_file.stem)
        date = ''
        if date_match:
            raw = date_match.group(1)
            date = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"

        sub_chunks = _split_text(text)
        for j, sub in enumerate(sub_chunks):
            chunks.append(Chunk(
                id=f"supernote_{txt_file.stem}_{j}",
                text=f"Supernote ({date}): {sub}",
                doc_type=DocType.SUPERNOTE,
                source=str(txt_file),
                metadata={"date": date, "filename": txt_file.name}
            ))

    # Process .md files (if someone converts handwriting to markdown)
    for md_file in sorted(SUPERNOTE_DIR.glob('*.md')):
        text = md_file.read_text(encoding='utf-8').strip()
        if not text or len(text) < 30:
            continue

        date_match = re.match(r'(\d{8})', md_file.stem)
        date = ''
        if date_match:
            raw = date_match.group(1)
            date = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"

        sub_chunks = _split_text(text)
        for j, sub in enumerate(sub_chunks):
            chunks.append(Chunk(
                id=f"supernote_{md_file.stem}_{j}",
                text=f"Supernote ({date}): {sub}",
                doc_type=DocType.SUPERNOTE,
                source=str(md_file),
                metadata={"date": date, "filename": md_file.name}
            ))

    return chunks


# ============================================================
# Knowledge Base — standalone docs/*.md reference files
# ============================================================

def chunk_knowledge_base() -> list[Chunk]:
    """Chunk standalone .md files in docs/ root — project knowledge, analyses, guides.

    Ingests: SUBSTACK_ANALYSIS.md, BACKTESTING.md, and any future reference docs.
    Skips: index.html, ticker dirs, api dir — those have their own chunkers.
    """
    chunks = []
    docs_dir = PROJECT_ROOT / "docs"

    for md_file in sorted(docs_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text or len(text) < 50:
            continue

        # Split on ## headers for section-aware chunking
        sections = re.split(r'(?=^#{1,2}\s)', text, flags=re.MULTILINE)

        for i, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 30:
                continue

            title_match = re.match(r'^#{1,2}\s+(.+)', section)
            section_title = title_match.group(1) if title_match else f"Section {i}"

            sub_chunks = _split_text(section)
            for j, sub in enumerate(sub_chunks):
                chunk_id = f"kb_{md_file.stem}_{i}_{j}"
                chunks.append(Chunk(
                    id=chunk_id,
                    text=sub,
                    doc_type=DocType.KNOWLEDGE_BASE,
                    source=str(md_file),
                    metadata={
                        "document": md_file.stem,
                        "section": section_title,
                        "chunk_index": j,
                    }
                ))

    return chunks


# ============================================================
# Scan Data — Venus historical screener entries with full technicals
# ============================================================

def chunk_scan_data() -> list[Chunk]:
    """Chunk historical screener scan data from Venus CSVs and scan_archive.
    
    Sources:
      1. data/venus_scans/*_History.csv — raw screener CSVs with ADX, RSI, Stoch, etc.
      2. docs/backtesting/scan_archive.jsonl — enriched entries with forward returns
    
    Each (ticker, date, strategy) becomes a searchable chunk with technicals.
    """
    import csv
    chunks = []
    seen = set()  # Dedup key: (ticker, date, strategy)
    
    def _safe_float(v, default=None):
        try:
            f = float(v)
            return f if abs(f) < 1e9 else default
        except (ValueError, TypeError):
            return default
    
    def _entry_to_text(entry: dict) -> str:
        """Convert a scan entry to natural-language text for embedding."""
        ticker = entry.get('ticker', '?')
        date = entry.get('date', '?')
        strategy = entry.get('strategy', '?')
        lines = [f"Screener Scan: {ticker} — {strategy} — {date}"]
        
        close = entry.get('close') or entry.get('price', 0)
        if close:
            lines.append(f"Price: ${close:.2f}")
        
        change = entry.get('change_pct', 0)
        if change:
            lines.append(f"Day Change: {change:+.2f}%")
        
        sector = entry.get('sector', '')
        if sector:
            lines.append(f"Sector: {sector}")
        
        # Technicals
        tech_parts = []
        adx = entry.get('adx') or entry.get('adx_14')
        if adx is not None:
            strength = 'No Trend' if adx < 15 else 'Weak' if adx < 25 else 'Strong' if adx < 40 else 'Very Strong' if adx < 60 else 'Extreme'
            tech_parts.append(f"ADX: {adx:.1f} ({strength})")
        
        rsi = entry.get('rsi') or entry.get('rsi_14')
        if rsi is not None:
            zone = 'Oversold' if rsi < 30 else 'Weak' if rsi < 45 else 'Neutral' if rsi < 55 else 'Strong' if rsi < 70 else 'Overbought'
            tech_parts.append(f"RSI: {rsi:.1f} ({zone})")
        
        stoch = entry.get('stoch_k')
        if stoch is not None:
            sz = 'Oversold' if stoch < 20 else 'Low' if stoch < 40 else 'Mid' if stoch < 60 else 'High' if stoch < 80 else 'Overbought'
            tech_parts.append(f"Stoch: {stoch:.1f} ({sz})")
        
        rvol = entry.get('rel_vol')
        if rvol is not None:
            rv = 'Dead' if rvol < 0.5 else 'Below Avg' if rvol < 1 else 'Above Avg' if rvol < 2 else 'High' if rvol < 4 else 'Extreme'
            tech_parts.append(f"RVOL: {rvol:.2f}x ({rv})")
        
        if tech_parts:
            lines.append(f"Technicals: {' | '.join(tech_parts)}")
        
        # EMA Stack
        ema = entry.get('ema_stack', '')
        if ema:
            lines.append(f"EMA Stack: {ema}")
        
        # EMAs
        ema_vals = []
        for k in ['ema8', 'ema21', 'ema34', 'ema55', 'ema89']:
            v = entry.get(k)
            if v:
                ema_vals.append(f"{k.upper()}=${v:.2f}")
        if ema_vals:
            lines.append(f"EMAs: {', '.join(ema_vals)}")
        
        sma50 = entry.get('sma50')
        if sma50:
            lines.append(f"SMA50: ${sma50:.2f}")
        ema200 = entry.get('ema200')
        if ema200:
            lines.append(f"EMA200: ${ema200:.2f}")
        
        # Fundamentals
        fund_parts = []
        for k, label in [('pe_ratio','P/E'), ('roe','ROE'), ('op_margin','OpMargin'),
                        ('rev_growth','RevGrowth'), ('debt_equity','D/E'), ('current_ratio','CurrentRatio')]:
            v = entry.get(k)
            if v is not None and v != 0:
                fund_parts.append(f"{label}: {v:.2f}")
        if fund_parts:
            lines.append(f"Fundamentals: {' | '.join(fund_parts)}")
        
        # Forward returns
        ret_parts = []
        for k, label in [('fwd_1d','1D'), ('fwd_3d','3D'), ('fwd_5d','5D'), ('fwd_10d','10D'), ('fwd_21d','21D')]:
            v = entry.get(k)
            if v is not None:
                ret_parts.append(f"{label}: {v:+.2f}%")
        if ret_parts:
            lines.append(f"Forward Returns: {' | '.join(ret_parts)}")
        
        # Market context
        vix = entry.get('vix')
        spy = entry.get('spy_change')
        if vix and vix > 0:
            lines.append(f"VIX: {vix:.1f}")
        if spy and spy != 0:
            lines.append(f"SPY Change: {spy:+.2f}%")
        
        return '\n'.join(lines)
    
    # Source 1: Venus CSVs in data/venus_scans/
    if SCAN_DATA_DIR.exists():
        for csvf in sorted(SCAN_DATA_DIR.glob('*_History.csv')):
            strategy = csvf.stem.replace('_History', '').replace('_', ' ')
            if 'Fake' in strategy:
                continue
            try:
                with open(csvf) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ticker = row.get('ticker', '')
                        if ':' in ticker: ticker = ticker.split(':')[-1]
                        if not ticker or len(ticker) > 8: continue
                        
                        date = (row.get('timestamp', '') or '')[:10]
                        key = (ticker, date, strategy)
                        if key in seen: continue
                        seen.add(key)
                        
                        entry = {
                            'ticker': ticker, 'strategy': strategy, 'date': date,
                            'close': _safe_float(row.get('close'), 0),
                            'change_pct': _safe_float(row.get('change'), 0),
                            'sector': row.get('sector', ''),
                            'adx': _safe_float(row.get('ADX')) if _safe_float(row.get('ADX'), 0) < 200 else None,
                            'rsi': _safe_float(row.get('RSI')) if _safe_float(row.get('RSI'), 0) < 200 else None,
                            'stoch_k': _safe_float(row.get('Stoch_K')) if _safe_float(row.get('Stoch_K'), 0) < 200 else None,
                            'rel_vol': _safe_float(row.get('relative_volume_10d_calc')) if _safe_float(row.get('relative_volume_10d_calc'), 0) < 1000 else None,
                            'sma50': _safe_float(row.get('SMA50')),
                            'ema200': _safe_float(row.get('EMA200')),
                            'ema8': _safe_float(row.get('EMA8')),
                            'ema21': _safe_float(row.get('EMA21')),
                            'ema34': _safe_float(row.get('EMA34')),
                            'ema55': _safe_float(row.get('EMA55')),
                            'ema89': _safe_float(row.get('EMA89')),
                        }
                        # Fundamentals
                        for k, col in [('pe_ratio','price_earnings_ttm'),('roe','return_on_equity'),
                                      ('op_margin','operating_margin'),('rev_growth','total_revenue_yoy_growth_ttm'),
                                      ('debt_equity','debt_to_equity'),('current_ratio','current_ratio')]:
                            if col in (reader.fieldnames or []):
                                entry[k] = _safe_float(row.get(col))
                        
                        # Derive EMA stack
                        emas = [entry.get(f'ema{p}', 0) or 0 for p in [8,21,34,55,89]]
                        if all(e > 0 for e in emas):
                            if emas[0]>emas[1]>emas[2]>emas[3]>emas[4]:
                                entry['ema_stack'] = 'FULL BULLISH'
                            elif emas[0]>emas[1]:
                                entry['ema_stack'] = 'PARTIAL BULLISH'
                            elif emas[4]>emas[3]>emas[2]>emas[1]>emas[0]:
                                entry['ema_stack'] = 'FULL BEARISH'
                            else:
                                entry['ema_stack'] = 'TANGLED'
                        
                        text = _entry_to_text(entry)
                        chunk_id = f"scan_{ticker}_{date}_{strategy.replace(' ','_')}"
                        chunks.append(Chunk(
                            id=chunk_id, text=text,
                            doc_type=DocType.SCAN_DATA,
                            source=str(csvf),
                            metadata={
                                'ticker': ticker, 'date': date,
                                'strategy': strategy, 'sector': entry.get('sector', ''),
                                'adx': str(round(entry['adx'], 1)) if entry.get('adx') else '',
                                'rsi': str(round(entry['rsi'], 1)) if entry.get('rsi') else '',
                            }
                        ))
            except Exception as ex:
                print(f"  [WARN] Error reading {csvf.name}: {ex}")
    
    # Source 2: scan_archive.jsonl (enriched entries with forward returns)
    if SCAN_ARCHIVE_PATH.exists():
        for line in open(SCAN_ARCHIVE_PATH):
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            ticker = entry.get('ticker', '')
            date = entry.get('date', '')[:10]
            strategy = entry.get('strategy', 'Ghost Alpha')
            if entry.get('grade') and entry['grade'] != 'SCREEN_HISTORY':
                strategy = f"Ghost Alpha ({entry['grade']})"
            
            key = (ticker, date, strategy)
            if key in seen: continue
            seen.add(key)
            
            # Normalize field names
            norm = dict(entry)
            if 'rsi_14' in norm and 'rsi' not in norm:
                norm['rsi'] = norm['rsi_14']
            if 'adx_14' in norm and 'adx' not in norm:
                norm['adx'] = norm['adx_14']
            if 'price' in norm and 'close' not in norm:
                norm['close'] = norm['price']
            norm['strategy'] = strategy
            
            text = _entry_to_text(norm)
            if len(text) < 30: continue
            
            chunk_id = f"archive_{ticker}_{date}_{strategy.replace(' ','_').replace('(','').replace(')','')}"
            chunks.append(Chunk(
                id=chunk_id, text=text,
                doc_type=DocType.SCAN_DATA,
                source=str(SCAN_ARCHIVE_PATH),
                metadata={
                    'ticker': ticker, 'date': date,
                    'strategy': strategy, 'sector': entry.get('sector', ''),
                }
            ))
    
    return chunks


# ============================================================
# Master Chunker
# ============================================================

def chunk_all() -> list[Chunk]:
    """Chunk all content types."""
    all_chunks = []
    all_chunks.extend(chunk_deep_dives())
    all_chunks.extend(chunk_blog_entries())
    all_chunks.extend(chunk_ticker_json())
    all_chunks.extend(chunk_dossier())
    all_chunks.extend(chunk_daily_picks())
    all_chunks.extend(chunk_screener_history())
    all_chunks.extend(chunk_scan_data())
    all_chunks.extend(chunk_git_history())
    all_chunks.extend(chunk_handoff())
    all_chunks.extend(chunk_supernote())
    all_chunks.extend(chunk_knowledge_base())
    return all_chunks
