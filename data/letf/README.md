# Inverse / leveraged-short ETF map (2026-11-20)

- `inverse_map_all.csv` — every inverse ETF/ETN found (160, incl. -1x), with underlying, leverage, issuer, 20-day avg share + dollar volume.
- `inverse_leveraged_best.csv` — leverage -1.5x or deeper only (120 funds), deduped to one per underlying (81) by highest 20-day dollar volume. `all_tickers` lists the alternatives.

Universe: Nasdaq ETF screener (all US-listed ETFs), name-filtered for short/inverse/bear, bond-duration noise removed, then hand-mapped. Volume from Yahoo daily bars. Funds whose names don't say short/inverse/bear would be missed.
TraderMatrix only had flat ticker lists (sectorMatching.ts, megaBlocks.ts), no underlying map.
