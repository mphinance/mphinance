# Vero / PatternPulse Data Bridge

## What This Is

`export_candles_for_vero.py` dumps intraday OHLCV candles for Justin's PatternPulse app (formerly "Vero"). His app needs 8 symbols × 4 resolutions of raw candle data for its weekly chart-segment pipeline, and yfinance is flaky for backfills.

## Usage

```bash
# Default export (all symbols, all resolutions)
python scripts/export_candles_for_vero.py

# Custom output dir
python scripts/export_candles_for_vero.py --output-dir /path/to/wherever

# Subset
python scripts/export_candles_for_vero.py --symbols SPY QQQ --resolutions 5m 15m
```

Output: one JSON file per symbol-resolution pair + a `manifest.json`.

Justin sets `PP_DATA_SOURCE=file` and `PP_FILE_SOURCE_DIR=/path/to/exported/data` in his `.env` and the pipeline reads from files instead of hitting yfinance.

## Future: API Fallback

If this becomes a regular thing, spin up a lightweight endpoint on Venus or Vultr that serves cached OHLCV data for his symbol universe. Something like:

```text
GET /api/candles/{symbol}?resolution=5m&start=2026-02-01&end=2026-03-01
```

This would let PatternPulse pull data on-demand without needing file transfers. Could live on the existing Ghost Alpha FastAPI service (port 8002 on Venus) as a new router — the data fetching logic is already there in `dossier/data_sources/ticker_enrichment.py`.
