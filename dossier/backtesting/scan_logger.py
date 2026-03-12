#!/usr/bin/env python3
"""
Scan Logger — Append-only archive of every pipeline scan with full technicals.

Each run appends today's picks + their FULL technical context to a JSONL file.
A separate pass checks forward returns (1d/3d/5d/10d/21d) for older entries.

This gives us the raw data for:
  "How did A-grade picks perform in Storm regime?"
  "What's the win rate for Volatility Squeeze signals with RSI < 40?"
  "Show me every time a FULL BULLISH EMA stack pick lost money"

Usage:
    python dossier/backtesting/scan_logger.py                # Log today's picks
    python dossier/backtesting/scan_logger.py --update-returns  # Fill in forward returns
    python dossier/backtesting/scan_logger.py --stats         # Print performance stats
    python dossier/backtesting/scan_logger.py --reindex       # Push to RAG vector store

Data lives in:
    docs/backtesting/scan_archive.jsonl  (append-only, one JSON per line)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCAN_ARCHIVE = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"
PICKS_PATH = PROJECT_ROOT / "docs" / "api" / "daily-picks.json"
DOSSIER_DIR = PROJECT_ROOT / "docs" / "api"


def _load_archive() -> list[dict]:
    """Load existing scan entries."""
    if not SCAN_ARCHIVE.exists():
        return []
    entries = []
    for line in SCAN_ARCHIVE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _append_entry(entry: dict):
    """Append a single entry to the JSONL archive."""
    with open(SCAN_ARCHIVE, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _get_ticker_snapshot(ticker: str) -> dict:
    """Pull full technical snapshot from latest.json if available."""
    json_path = PROJECT_ROOT / "docs" / "ticker" / ticker / "latest.json"
    if not json_path.exists():
        return {}
    try:
        data = json.loads(json_path.read_text())
        ta = data.get("technical_analysis", {})
        return {
            "price": data.get("currentPrice", 0),
            "change_pct": data.get("priceChangePct", 0),
            "sector": data.get("sector", ""),
            "industry": data.get("industry", ""),
            "trend": data.get("trendOverall", ""),
            "trend_short": data.get("trendShort", ""),
            "trend_med": data.get("trendMed", ""),
            "trend_long": data.get("trendLong", ""),
            # EMAs
            "ema_stack": ta.get("ema_stack", ""),
            "ema_8": ta.get("ema", {}).get("8"),
            "ema_21": ta.get("ema", {}).get("21"),
            "ema_34": ta.get("ema", {}).get("34"),
            "ema_55": ta.get("ema", {}).get("55"),
            "ema_89": ta.get("ema", {}).get("89"),
            # SMAs
            "sma_50": ta.get("trend", {}).get("sma_50"),
            "sma_200": ta.get("trend", {}).get("sma_200"),
            "crossover": ta.get("trend", {}).get("crossover", ""),
            # Oscillators
            "rsi_14": ta.get("oscillators", {}).get("rsi_14"),
            "adx_14": ta.get("oscillators", {}).get("adx_14"),
            "macd_hist": ta.get("oscillators", {}).get("macd_hist"),
            "stoch_k": ta.get("oscillators", {}).get("stoch_k"),
            # Pivots
            "pivot_r2": ta.get("pivots", {}).get("R2"),
            "pivot_r1": ta.get("pivots", {}).get("R1"),
            "pivot_pp": ta.get("pivots", {}).get("PP"),
            "pivot_s1": ta.get("pivots", {}).get("S1"),
            "pivot_s2": ta.get("pivots", {}).get("S2"),
            # Volume
            "rel_vol": ta.get("volume", {}).get("rel_vol"),
            # Volatility
            "iv": data.get("impliedVolatility"),
            "hv": data.get("historicVolatility"),
            "iv_rank": data.get("ivRank"),
            # Grade & Scores
            "grade": data.get("scores", {}).get("grade", ""),
            "tech_score": data.get("scores", {}).get("technical", 0),
            "fund_score": data.get("scores", {}).get("fundamental", 0),
            # NEW: ATR, squeeze, DI+/DI- from technical_analysis
            "atr_14": ta.get("momentum", {}).get("atr") or ta.get("volume", {}).get("atr"),
            "squeeze_ratio": ta.get("momentum", {}).get("squeeze_ratio"),
            "di_plus": osc.get("di_plus"),
            "di_minus": osc.get("di_minus"),
            # Williams %R and CMF from oscillators (if available)
            "williams_r": osc.get("williams_r") or osc.get("willr"),
            "cmf": ta.get("volume", {}).get("cmf"),
            "mfi": osc.get("mfi"),
        }
    except Exception:
        return {}


def _get_market_context() -> dict:
    """Get current market regime from the latest dossier."""
    for f in sorted(DOSSIER_DIR.glob("dossier-*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            market = data.get("market", {})
            return {
                "regime": market.get("regime", ""),
                "vix": market.get("vix", 0),
                "vvix": market.get("vvix", 0),
                "vix_vix3m_ratio": market.get("vix_vix3m_ratio", 0),
                "spy_change": market.get("spy", {}).get("change_pct", 0),
                "spy_vs_sma200": market.get("spy_vs_sma200", 0),
            }
        except Exception:
            continue
    return {}


def log_todays_picks():
    """Append today's picks to the scan archive with full technicals."""
    if not PICKS_PATH.exists():
        print("❌ No daily-picks.json found")
        return

    data = json.loads(PICKS_PATH.read_text())
    picks = data.get("picks", [])
    all_ranked = data.get("all_ranked", [])
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Check what's already logged for today
    existing = _load_archive()
    existing_pairs = {(e["ticker"], e["date"]) for e in existing}

    market = _get_market_context()
    logged = 0

    # Log top picks (gold/silver/bronze + rest of picks)
    for pick in picks:
        ticker = pick.get("ticker", "")
        if not ticker or (ticker, date) in existing_pairs:
            continue

        snapshot = _get_ticker_snapshot(ticker)

        entry = {
            "date": date,
            "logged_at": datetime.now().isoformat(),
            "ticker": ticker,
            "score": pick.get("score", 0),
            "grade": pick.get("grade", ""),
            "medal": pick.get("medal", ""),
            "is_pullback": pick.get("is_pullback_setup", False),
            "strategy": pick.get("strategy", ""),
            # Market context
            "regime": market.get("regime", ""),
            "vix": market.get("vix", 0),
            "vvix": market.get("vvix", 0),
            "vix_vix3m_ratio": market.get("vix_vix3m_ratio", 0),
            "spy_change": market.get("spy_change", 0),
            "spy_vs_sma200": market.get("spy_vs_sma200", 0),
            # Full technical snapshot
            **snapshot,
            # Forward returns (filled later)
            "fwd_1d": None,
            "fwd_3d": None,
            "fwd_5d": None,
            "fwd_10d": None,
            "fwd_21d": None,
        }

        _append_entry(entry)
        logged += 1
        print(f"  📝 {ticker} (Grade {entry.get('grade', '?')}, Score {entry.get('score', 0)})")

    print(f"\n✅ Logged {logged} picks for {date} (regime: {market.get('regime', '?')})")


def update_forward_returns():
    """Check forward returns for older entries using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        print("❌ yfinance not installed")
        return

    entries = _load_archive()
    if not entries:
        print("❌ No entries in scan archive")
        return

    today = datetime.now()
    updated = 0

    # Rewrite the entire file with updated entries
    updated_entries = []
    for entry in entries:
        if entry.get("fwd_5d") is not None:
            updated_entries.append(entry)
            continue

        scan_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        days_since = (today - scan_date).days

        # Need at least 7 calendar days for 5 trading days
        if days_since < 7:
            updated_entries.append(entry)
            continue

        ticker = entry["ticker"]
        entry_price = entry.get("price", 0)
        if not entry_price:
            updated_entries.append(entry)
            continue

        try:
            end = scan_date + timedelta(days=45)
            hist = yf.download(ticker, start=scan_date, end=end,
                             interval="1d", progress=False)
            if hist.empty:
                updated_entries.append(entry)
                continue

            prices = hist["Close"]
            for d, key in [(1, "fwd_1d"), (3, "fwd_3d"), (5, "fwd_5d"),
                          (10, "fwd_10d"), (21, "fwd_21d")]:
                if len(prices) > d:
                    ret = (float(prices.iloc[d]) - entry_price) / entry_price * 100
                    entry[key] = round(ret, 2)

            updated += 1
            print(f"  📊 {ticker} ({entry['date']}): 5d={entry.get('fwd_5d', '?')}%")
            time.sleep(0.5)  # Rate limit

        except Exception as e:
            print(f"  ⚠️ {ticker}: {e}")

        updated_entries.append(entry)

    # Rewrite archive
    with open(SCAN_ARCHIVE, "w") as f:
        for entry in updated_entries:
            f.write(json.dumps(entry, default=str) + "\n")

    print(f"\n✅ Updated {updated} entries with forward returns")


def print_stats():
    """Print performance breakdown by grade, regime, strategy."""
    entries = _load_archive()
    validated = [e for e in entries if e.get("fwd_5d") is not None]

    print(f"\n📊 Scan Archive Stats")
    print(f"{'='*60}")
    print(f"Total logged: {len(entries)}")
    print(f"With returns:  {len(validated)}")

    if not validated:
        print("\n⏳ No validated returns yet — entries need 7+ days to mature")
        # Still show what's been logged
        print(f"\nPending picks:")
        for e in entries[:10]:
            print(f"  {e['date']} | {e['ticker']} | Grade {e.get('grade', '?')} | {e.get('regime', '?')}")
        return

    import numpy as np

    def _stats(subset, label):
        if not subset:
            return
        returns_5d = [e["fwd_5d"] for e in subset]
        avg = np.mean(returns_5d)
        win = sum(1 for r in returns_5d if r > 0) / len(returns_5d) * 100
        print(f"\n  {label} ({len(subset)} picks)")
        print(f"    Avg 5d: {avg:+.2f}% | Win Rate: {win:.0f}%")
        if len(returns_5d) > 1:
            sharpe = avg / np.std(returns_5d) if np.std(returns_5d) > 0 else 0
            print(f"    Sharpe: {sharpe:.2f} | Best: {max(returns_5d):+.2f}% | Worst: {min(returns_5d):+.2f}%")

    # By Grade
    print(f"\n{'─'*60}")
    print("By Grade:")
    for grade in ["A", "B", "C", "D"]:
        subset = [e for e in validated if e.get("grade") == grade]
        _stats(subset, f"Grade {grade}")

    # By Regime
    print(f"\n{'─'*60}")
    print("By Market Regime:")
    regimes = set(e.get("regime", "Unknown") for e in validated)
    for regime in sorted(regimes):
        subset = [e for e in validated if e.get("regime") == regime]
        _stats(subset, regime)

    # By EMA Stack
    print(f"\n{'─'*60}")
    print("By EMA Stack:")
    stacks = set(e.get("ema_stack", "Unknown") for e in validated)
    for stack in sorted(stacks):
        subset = [e for e in validated if e.get("ema_stack") == stack]
        _stats(subset, stack)

    # Pullback setups vs regular
    print(f"\n{'─'*60}")
    pullbacks = [e for e in validated if e.get("is_pullback")]
    non_pullbacks = [e for e in validated if not e.get("is_pullback")]
    _stats(pullbacks, "Pullback Setups")
    _stats(non_pullbacks, "Non-Pullback")

    # RSI Zones
    print(f"\n{'─'*60}")
    print("By RSI Zone:")
    oversold = [e for e in validated if e.get("rsi_14") and e["rsi_14"] < 30]
    neutral = [e for e in validated if e.get("rsi_14") and 30 <= e["rsi_14"] <= 70]
    overbought = [e for e in validated if e.get("rsi_14") and e["rsi_14"] > 70]
    _stats(oversold, "RSI < 30 (Oversold)")
    _stats(neutral, "RSI 30-70 (Neutral)")
    _stats(overbought, "RSI > 70 (Overbought)")


def reindex_to_rag():
    """Push scan archive into the RAG vector store."""
    from rag.chunker import Chunk, DocType, _split_text

    entries = _load_archive()
    if not entries:
        print("❌ No entries to index")
        return

    chunks = []
    for entry in entries:
        ticker = entry.get("ticker", "?")
        date = entry.get("date", "?")
        grade = entry.get("grade", "?")
        regime = entry.get("regime", "?")

        lines = [f"Scan Log: {ticker} on {date}"]
        lines.append(f"Grade: {grade} | Score: {entry.get('score', 0)} | Medal: {entry.get('medal', '')}")
        lines.append(f"Regime: {regime} | VIX: {entry.get('vix', 0)} | SPY: {entry.get('spy_change', 0):+.2f}%")
        lines.append(f"Price: ${entry.get('price', 0):.2f} | EMA Stack: {entry.get('ema_stack', '?')}")

        if entry.get("ema_55"):
            lines.append(f"EMAs: 8=${entry.get('ema_8', '?')}, 21=${entry.get('ema_21', '?')}, "
                        f"34=${entry.get('ema_34', '?')}, 55=${entry.get('ema_55', '?')}, "
                        f"89=${entry.get('ema_89', '?')}")
        if entry.get("rsi_14"):
            lines.append(f"RSI: {entry['rsi_14']} | ADX: {entry.get('adx_14', '?')} | "
                        f"MACD: {entry.get('macd_hist', '?')} | Stoch: {entry.get('stoch_k', '?')}")
        if entry.get("crossover"):
            lines.append(f"Crossover: {entry['crossover']} | Rel Vol: {entry.get('rel_vol', '?')}x")
        if entry.get("is_pullback"):
            lines.append("Setup: Pullback")

        # Forward returns
        if entry.get("fwd_5d") is not None:
            lines.append(f"\nForward Returns:")
            for key, label in [("fwd_1d", "1d"), ("fwd_3d", "3d"), ("fwd_5d", "5d"),
                              ("fwd_10d", "10d"), ("fwd_21d", "21d")]:
                val = entry.get(key)
                if val is not None:
                    emoji = "✅" if val > 0 else "❌"
                    lines.append(f"  {emoji} {label}: {val:+.2f}%")

        text = "\n".join(lines)
        chunks.append(Chunk(
            id=f"scan_{ticker}_{date}",
            text=text,
            doc_type=DocType.GIT_HISTORY,  # Reuse type for now
            source="scan_archive.jsonl",
            metadata={
                "ticker": ticker,
                "date": date,
                "grade": grade,
                "regime": regime,
            }
        ))

    # Index into RAG
    from rag.embeddings import embed_documents
    from rag.store import get_collection, upsert_chunks

    print(f"\n🧠 Embedding {len(chunks)} scan entries...")
    texts = [c.text for c in chunks]
    embeddings = embed_documents(texts)

    collection = get_collection(reset=False)
    upsert_chunks(chunks, embeddings)
    print(f"✅ Indexed {len(chunks)} scan entries into RAG")


def main():
    parser = argparse.ArgumentParser(description="Scan Logger — full technical archival")
    parser.add_argument("--update-returns", action="store_true", help="Fill forward returns")
    parser.add_argument("--stats", action="store_true", help="Print performance stats")
    parser.add_argument("--reindex", action="store_true", help="Push to RAG vector store")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    if args.update_returns:
        update_forward_returns()
    elif args.stats:
        print_stats()
    elif args.reindex:
        reindex_to_rag()
    else:
        log_todays_picks()


if __name__ == "__main__":
    main()
