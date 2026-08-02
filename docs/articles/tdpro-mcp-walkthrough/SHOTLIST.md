# Screenshot shot list — TDPro MCP walk-through

Grab each from the product to match the step. File names are the placeholders
used in README.md. Snapshot state: 2026-07-09, ~7:10pm ET (after close).

| # | Filename | Product screen | What must be visible |
|---|---|---|---|
| 1 | `screener-bullish-pullback.png` | Screeners → Bullish Pullback | UCTT at top, entry score 80 / grade A, sector = semiconductor equipment |
| 2 | `sector-flow.png` | Sector Flow (today) | SMH +2.49% / $363M call flow; XLK +2.18%; ALL CYLINDERS pills on Financials + Cybersecurity |
| 3 | `gex-overview.png` | GEX Overview | Market-wide LONG_GAMMA read (~$23.6B), mean-reversion interpretation |
| 4 | `econ-calendar.png` | Economic Calendar | Current week, FOMC minutes already passed, nothing high-impact left |
| 5 | `unusual-uctt-empty.png` | Unusual Activity, filter = UCTT | Empty result — no prints. The red flag |
| 6 | `uctt-iv-and-chain.png` | UCTT IV / options chain | 117% ATM IV, wide bid/ask on the 95 put, earnings-in-window flag |
| 7 | `unusual-nvda.png` | Unusual Activity (unfiltered / NVDA) | NVDA $58M call block at 202.5, tight market |
| 8 | `nvda-gex.png` | NVDA GEX | Positive gamma, walls $200 / $202.5 pin / $205, flip $198 |
| 9 | `nvda-edge-xray.png` | NVDA Edge X-ray | Calls graded cheap (-2.5% residual), puts rich (+2.6%) |
| 10 | `nvda-strategy-ideas.png` | NVDA Strategy Ideas (bullish, cap $1k) | $200/$215 bull call spread, $647.50 risk, $852.50 max, BE $206.48 |

Note: three MCP endpoints (GEX Overview, Earnings Flow, Edge X-ray) return huge
by-strike payloads that overflow a context window. In the product the screens
are fine; via the API/MCP, read summarized fields only.
