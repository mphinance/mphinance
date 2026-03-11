# 📊 Backtesting Engine — Scan Logger & Forward Returns

> Tracks every pipeline pick with full technical context, then measures what actually happened.
> "Did our A-grade picks in Storm regime actually make money?"

## Quick Start

```bash
# Log today's picks (auto-runs in pipeline)
python dossier/backtesting/scan_logger.py

# Update forward returns for older entries (needs 7+ days)
python dossier/backtesting/scan_logger.py --update-returns

# View performance stats by grade, regime, EMA stack, RSI zone
python dossier/backtesting/scan_logger.py --stats

# Push scan data into RAG for semantic queries
python dossier/backtesting/scan_logger.py --reindex
```

---

## How It Works

### 1. Logging (Every Pipeline Run)

When the pipeline runs, the scan logger captures **every pick** with its full technical snapshot at that moment:

```
Pipeline runs → daily-picks.json has 8 picks
             → For each pick, pull latest.json technicals
             → Append to scan_archive.jsonl with timestamp + regime
```

**What's captured per entry:**

| Category | Fields |
|----------|--------|
| Pick | ticker, score, grade, medal, is_pullback, strategy |
| Market | regime (Zen/Calm/Storm/Chaos), VIX, SPY change |
| Price | current price, change % |
| Company | sector, industry |
| EMAs | ema_8, ema_21, ema_34, ema_55, ema_89, ema_stack |
| SMAs | sma_50, sma_200, crossover (Golden/Death) |
| Oscillators | rsi_14, adx_14, macd_hist, stoch_k |
| Pivots | pivot_r2, r1, pp, s1, s2 |
| Volume | rel_vol |
| Volatility | iv, hv, iv_rank |
| Scores | tech_score, fund_score |
| **Forward Returns** | fwd_1d, fwd_3d, fwd_5d, fwd_10d, fwd_21d (filled later) |

### 2. Forward Returns (Daily Update)

After 7+ calendar days (~5 trading days), the logger pulls closing prices from yfinance and calculates actual returns:

```
Entry: DAKT on 2026-03-03 at $22.50
Day 1:  $22.80 → fwd_1d = +1.33%
Day 3:  $23.10 → fwd_3d = +2.67%
Day 5:  $23.50 → fwd_5d = +4.44%
Day 10: $24.00 → fwd_10d = +6.67%
Day 21: $25.00 → fwd_21d = +11.11%
```

### 3. Stats Engine

Performance breakdown by every dimension:

```
📊 Scan Archive Stats
============================================================
Total logged: 46
With returns:  22

────────────────────────────────────────────────────────────
By Grade:
  Grade A (11 picks) — Avg 5d: -1.48% | Win Rate: 36%
  Grade B (7 picks)  — Avg 5d: +0.87% | Win Rate: 71%  ← best so far
  Grade C (4 picks)  — Avg 5d: +31.03% | Win Rate: 75%

By EMA Stack:
  FULL BULLISH (18)  — Avg 5d: +5.58% | Win Rate: 50%

By RSI Zone:
  RSI 30-70 (20)     — Avg 5d: +4.87% | Win Rate: 55%
  RSI > 70 (2)       — Avg 5d: +8.28% | Win Rate: 50%
```

---

## Data File

`docs/backtesting/scan_archive.jsonl` — append-only JSON Lines format. One JSON object per line, each representing one pick on one date.

---

## Pipeline Integration

Wired into `dossier/generate.py` as a post-pipeline step:

```python
# After Stage 15e, before RAG reindex
from dossier.backtesting.scan_logger import log_todays_picks, update_forward_returns
log_todays_picks()        # Append today's picks
update_forward_returns()  # Fill in returns for 7+ day old entries
```

---

## Relationship to Other Backtesting Files

| File | Purpose |
|------|---------|
| `scan_logger.py` | **NEW** — Full technical snapshots + forward returns per pick |
| `auto_backtest.py` | Legacy — Basic pick tracking (grade, EMA stack, no technicals) |
| `track_record.json` | Legacy output — Stats from auto_backtest |
| `screens_backtest.json` | Historical strategy-level stats (Vol Squeeze 63.5% WR, etc.) |
| `signal_history.csv` | Raw signal log |

The scan logger supersedes `auto_backtest.py` — it captures everything auto_backtest does plus full technicals, market regime, and more granular stats.
