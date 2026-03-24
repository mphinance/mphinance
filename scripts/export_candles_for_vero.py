#!/usr/bin/env python3
"""
Export intraday OHLCV candles for PatternPulse (Vero).

Uses Tradier API as the primary data source (fast, reliable) with
yfinance as fallback. Writes JSON files that PatternPulse's FileSource
can consume directly.

Usage:
    python scripts/export_candles_for_vero.py
    python scripts/export_candles_for_vero.py --output-dir /path/to/output
    python scripts/export_candles_for_vero.py --symbols SPY QQQ --resolutions 5m 15m
    python scripts/export_candles_for_vero.py --yfinance-only  # skip Tradier
"""

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

# --- Defaults matching PatternPulse's pipeline ---

DEFAULT_SYMBOLS = ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "IWM", "EEM", "EFA"]
DEFAULT_RESOLUTIONS = ["5m", "15m", "30m", "1h"]

# Lookback days per resolution (matches PatternPulse's _get_fetch_range)
LOOKBACK_DAYS = {
    "5m": 30,
    "15m": 60,
    "30m": 59,   # yfinance caps intraday at 60 days
    "1h": 59,    # same limit applies
}

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "vero_export"

# Tradier timesales interval limits (max days of lookback per interval)
TRADIER_MAX_DAYS = {
    "5min": 20,
    "15min": 35,
}

# Map PatternPulse resolution names to Tradier interval names
PP_TO_TRADIER_INTERVAL = {
    "5m": "5min",
    "15m": "15min",
}


# ─── Tradier Data Fetcher ─────────────────────────────────────────

def _load_tradier_creds() -> tuple[str, str] | None:
    """Load Tradier credentials from environment or secrets.env."""
    token = os.environ.get("TRADIER_ACCESS_TOKEN") or os.environ.get("TRADIER_API_KEY")
    endpoint = os.environ.get("TRADIER_ENDPOINT", "https://api.tradier.com/v1")

    if not token:
        # Try loading from secrets.env
        secrets_path = Path(__file__).resolve().parent.parent / "secrets.env"
        if secrets_path.exists():
            for line in secrets_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("TRADIER_ACCESS_TOKEN="):
                    token = line.split("=", 1)[1]
                elif line.startswith("TRADIER_ENDPOINT="):
                    endpoint = line.split("=", 1)[1]

    if not token:
        return None
    return token, endpoint


def fetch_tradier_timesales(
    symbol: str,
    interval: str,
    start_date: date,
    end_date: date,
    token: str,
    endpoint: str,
) -> list[dict]:
    """Fetch intraday candles from Tradier's Time & Sales endpoint.

    Returns CandleRow-compatible dicts: [{t, o, h, l, c, v}, ...]
    """
    url = f"{endpoint}/markets/timesales"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "symbol": symbol,
        "interval": interval,
        "start": f"{start_date.isoformat()} 09:30",
        "end": f"{end_date.isoformat()} 16:00",
        "session_filter": "open",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    series = data.get("series", {})
    if not series:
        return []

    raw_data = series.get("data", [])
    if isinstance(raw_data, dict):
        raw_data = [raw_data]  # Single result comes as dict, not list

    candles = []
    for bar in raw_data:
        candles.append({
            "t": bar["time"],
            "o": round(float(bar["open"]), 4),
            "h": round(float(bar["high"]), 4),
            "l": round(float(bar["low"]), 4),
            "c": round(float(bar["close"]), 4),
            "v": int(bar["volume"]),
        })

    return candles


def fetch_tradier_daily(
    symbol: str,
    start_date: date,
    end_date: date,
    token: str,
    endpoint: str,
) -> list[dict]:
    """Fetch daily candles from Tradier's Historical endpoint.

    Used for 30m/1h where we need longer lookback — converts daily
    bars to the format PatternPulse expects. Note: this gives daily bars,
    not actual 30m/1h intraday. For those resolutions yfinance fallback
    is still better.
    """
    url = f"{endpoint}/markets/history"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    params = {
        "symbol": symbol,
        "interval": "daily",
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    history = data.get("history", {})
    if not history:
        return []

    days = history.get("day", [])
    if isinstance(days, dict):
        days = [days]

    candles = []
    for bar in days:
        candles.append({
            "t": bar["date"] + "T00:00:00",
            "o": round(float(bar["open"]), 4),
            "h": round(float(bar["high"]), 4),
            "l": round(float(bar["low"]), 4),
            "c": round(float(bar["close"]), 4),
            "v": int(bar["volume"]),
        })

    return candles


# ─── yfinance Fallback ────────────────────────────────────────────

def fetch_yfinance(symbol: str, resolution: str, lookback_days: int) -> list[dict]:
    """Fetch candles from yfinance (fallback)."""
    import yfinance as yf

    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    end_plus = end_date + timedelta(days=1)

    interval_map = {"5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h"}
    interval = interval_map.get(resolution, "5m")

    ticker = yf.Ticker(symbol)
    df = ticker.history(
        interval=interval,
        start=start_date.isoformat(),
        end=end_plus.isoformat(),
        prepost=False,
    )

    if df.empty:
        return []

    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "t": ts.isoformat(),
            "o": round(float(row["Open"]), 4),
            "h": round(float(row["High"]), 4),
            "l": round(float(row["Low"]), 4),
            "c": round(float(row["Close"]), 4),
            "v": int(row["Volume"]),
        })

    return candles


# ─── Unified Fetch ────────────────────────────────────────────────

def fetch_candles(
    symbol: str,
    resolution: str,
    lookback_days: int,
    tradier_creds: tuple[str, str] | None = None,
) -> tuple[list[dict], str]:
    """Fetch candles using Tradier first, yfinance as fallback.

    Returns (candles, source_name).
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)

    # Try Tradier for 5m/15m (supports intraday timesales)
    if tradier_creds and resolution in PP_TO_TRADIER_INTERVAL:
        tradier_interval = PP_TO_TRADIER_INTERVAL[resolution]
        max_days = TRADIER_MAX_DAYS.get(tradier_interval, 20)
        tradier_start = max(start_date, end_date - timedelta(days=max_days))

        try:
            token, endpoint = tradier_creds
            candles = fetch_tradier_timesales(
                symbol, tradier_interval, tradier_start, end_date, token, endpoint,
            )
            if candles:
                return candles, "tradier"
        except Exception as e:
            print(f"    Tradier failed: {e}, falling back to yfinance")

    # Fallback to yfinance
    try:
        candles = fetch_yfinance(symbol, resolution, lookback_days)
        return candles, "yfinance"
    except Exception as e:
        print(f"    yfinance also failed: {e}")
        return [], "none"


# ─── Export Runner ────────────────────────────────────────────────

def export_all(
    symbols: list[str],
    resolutions: list[str],
    output_dir: Path,
    yfinance_only: bool = False,
) -> dict:
    """Fetch all symbols × resolutions and write JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    tradier_creds = None if yfinance_only else _load_tradier_creds()
    if tradier_creds:
        print(f"  ✓ Tradier credentials loaded (primary source)")
    else:
        print(f"  ⚠ No Tradier credentials — using yfinance only")

    manifest = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "symbols": symbols,
        "resolutions": resolutions,
        "files": {},
    }

    total = len(symbols) * len(resolutions)
    done = 0

    for symbol in symbols:
        for resolution in resolutions:
            done += 1
            lookback = LOOKBACK_DAYS.get(resolution, 30)
            fname = f"{symbol}_{resolution}.json"
            fpath = output_dir / fname

            print(f"  [{done}/{total}] {symbol}@{resolution} (lookback={lookback}d)...", end=" ", flush=True)

            candles, source = fetch_candles(symbol, resolution, lookback, tradier_creds)

            if candles:
                with open(fpath, "w") as f:
                    json.dump(candles, f)

                manifest["files"][fname] = {
                    "symbol": symbol,
                    "resolution": resolution,
                    "candle_count": len(candles),
                    "lookback_days": lookback,
                    "source": source,
                }
                print(f"{len(candles)} candles via {source} ✓")
            else:
                manifest["files"][fname] = {
                    "symbol": symbol,
                    "resolution": resolution,
                    "error": "no data from any source",
                }
                print("FAILED (no data)")

            # Brief pause between API calls to be nice
            time.sleep(0.3)

    # Write manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest written to {manifest_path}")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Export OHLCV candles for PatternPulse (Vero)"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--symbols", nargs="+", default=DEFAULT_SYMBOLS,
        help=f"Symbols to export (default: {DEFAULT_SYMBOLS})",
    )
    parser.add_argument(
        "--resolutions", nargs="+", default=DEFAULT_RESOLUTIONS,
        help=f"Resolutions to export (default: {DEFAULT_RESOLUTIONS})",
    )
    parser.add_argument(
        "--yfinance-only", action="store_true",
        help="Skip Tradier, use yfinance for everything",
    )
    args = parser.parse_args()

    print(f"Exporting candles for PatternPulse (Vero)")
    print(f"  Symbols:     {args.symbols}")
    print(f"  Resolutions: {args.resolutions}")
    print(f"  Output:      {args.output_dir}")
    print()

    manifest = export_all(args.symbols, args.resolutions, args.output_dir, args.yfinance_only)

    # Summary
    succeeded = sum(1 for f in manifest["files"].values() if "error" not in f)
    failed = sum(1 for f in manifest["files"].values() if "error" in f)
    total_candles = sum(f.get("candle_count", 0) for f in manifest["files"].values())
    sources_used = set(f.get("source", "") for f in manifest["files"].values() if "source" in f)

    print(f"\nDone: {succeeded} files, {failed} failures, {total_candles:,} candles")
    print(f"Sources used: {', '.join(sources_used) or 'none'}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
