# 🔎 Screen & Strategy Reference

> Complete catalog of every screen/strategy in the Ghost Alpha pipeline.
> 13 total: 8 TradingView + 5 Finviz. All results tracked by the scan logger.

---

## Pipeline Flow

```
TradingView Strategies (Stage 2)     →  Deduped signal pool
Finviz Screens (Stage 2a)            →  (unique tickers only)
Ghost Alpha 7-Axis Screener (2b)     →  Grades everything A+ to D
                                     →  Top 8 get full dossier enrichment
                                     →  Scan logger tracks forward returns
```

---

## TradingView Strategies (`strategies/`)

All use the `tradingview_screener` Python package to query TradingView's scanner API.

### ✅ Active in Pipeline

#### 1. Momentum with Pullback (`momentum.py`)
- **What**: Full EMA stack (8>21>34>55>89) aligned on daily, weekly, AND monthly timeframes + Stochastic < 40 + price within 1 ATR of EMA21
- **Edge**: Multi-timeframe trend confirmation with timing filter — catches stocks pulling back to support in strong uptrends
- **Filters**: Vol ≥ 500K, ADX 20-100, SMA50 > EMA200 on all timeframes
- **Historical WR**: 59% (from screens_backtest.json)

#### 2. Volatility Squeeze (`volatility_squeeze.py`)
- **What**: NATR compression detection — EMA(8) of NATR crossing above EMA(34) of NATR ("The Snap")
- **Edge**: Catches the moment volatility starts expanding after a quiet period — coiled spring
- **Filters**: Common stock only, price > $2, RVOL ≥ 1.3x, ADX ≥ 20, EMA stack aligned, SqueezeRatio < 1.0, >1% below 52w high (filters buyout targets)
- **Historical WR**: 63.5% (best performer historically)

#### 3. EMA Cross Momentum (`ema_cross.py`)
- **What**: EMA(8) freshly crossing above EMA(34) — sorted by proximity (smallest spread = freshest cross)
- **Edge**: Catches trend initiation at the earliest recognizable point
- **Filters**: Price > EMA200, ADX ≥ 20, RVOL ≥ 1.2x, max 2% spread between EMA8-EMA34

#### 4. Gamma Scan
- **What**: Options gamma exposure scanner
- **Edge**: Identifies stocks where dealer hedging could amplify moves

#### 5. Small Cap Multibaggers (`small_cap_multibaggers.py`) — *newly activated*
- **What**: $10M-$1B market cap, FCF positive, gross margin 30-100%, revenue growth >15% YoY, Net Debt/EBITDA 0-2x
- **Edge**: Quality small caps with real business fundamentals — the antidote to meme stocks
- **Historical**: N/A (was dormant, now tracking)

#### 6. Bearish EMA Cross (`ema_cross_down.py`) — *newly activated*
- **What**: Short/hedge signals — EMA(8) crossing below EMA(34)
- **Edge**: Identifies breakdown initiation for hedging or short opportunities

### ❌ Dormant (Built, Not in Pipeline)

#### 7. Cash Secured Puts
- **What**: CSP candidates for income strategies
- **Note**: Separate flow — see CSP Setups (Stage 7)

#### 8. MEME Screen (`meme_scanner.py`)
- **What**: Top 200 by volume → ranked by implied volatility → top 30
- **Note**: Heavy on yfinance API calls (200 IV lookups), slow
- **Kept dormant**: Too many API calls for daily pipeline

---

## Finviz Screens (`strategies/finviz_screens.py`)

All scrape [Finviz](https://finviz.com) screener pages with rate limiting (2s between requests). Returns up to 10 tickers per screen, deduped across all screens.

### ✅ All Active in Pipeline (Stage 2a)

#### 1. 🩳 Short Squeeze
- **URL Filter**: Short interest >15%, institutional ownership <50%, price >$2, avg vol >100K
- **Edge**: Crowded short trades vulnerable to squeeze. **Zero overlap** with TradingView screens.
- **Typical tickers**: Small caps with high borrow costs

#### 2. 📊 CANSLIM
- **URL Filter**: EPS growth (5yr >20%, QoQ >20%, YoY >20%), sales growth (5yr >20%, QoQ >20%), current volume >200K
- **Edge**: William O'Neil's institutional-quality growth methodology. Finds stocks institutions are accumulating.
- **Covers**: C (Current Earnings), A (Annual Growth), S (Supply/Demand via volume)

#### 3. 📅 Earnings Gap Up
- **URL Filter**: Earnings tomorrow or after, avg vol >400K, current vol >50K, short <25%, ATR >0.5, gap >2%
- **Edge**: Event-driven catalyst screening. **Technicals can't predict earnings.**

#### 4. 📈 Consistent Growth + Bullish
- **URL Filter**: EPS growth (5yr positive, QoQ >20%, YoY >25%, next year >15%), ROE >15%, institutional >10%, price >$15, within 90% of 52w high, RSI >50
- **Edge**: "Boring money" — multi-year compounders near all-time highs. These are the stocks pension funds buy.

#### 5. 🔻 Oversold + Upcoming Earnings
- **URL Filter**: Small cap+, earnings this month, EPS QoQ >15%, gross margin >20%, avg vol >750K, current vol >1000K, 52w performance >10% (not a lost cause), RSI <50
- **Edge**: Contrarian + catalyst combo. Beaten-down quality stocks with an upcoming earnings event to trigger a reversal.

---

## Ghost Alpha 7-Axis Screener (`dossier/ghost_alpha_screener.py`)

The master screener. Scans the entire US equity universe via TradingView's scanner API, then scores each stock on 7 axes:

1. **Trend Phase** — EMA stack alignment quality
2. **Momentum** — RSI, ADX, MACD histogram
3. **Volume** — Relative volume vs 10d average
4. **Volatility** — Squeeze ratio (ATR compression)
5. **Multi-Timeframe** — Daily + Weekly + Monthly agreement
6. **Mean Reversion** — Stochastic for timing
7. **Institutional** — Hull MA trend, SMA crossover

Grades: **A+** (multi-TF aligned, all axes green) through **D** (technical mess).

Top picks go into the dossier for full enrichment (deep dive AI analysis, TickerTrace institutional data, charts, etc.).

---

## Coverage Map

| Signal Type | TradingView | Finviz | Ghost Alpha |
|-------------|:-----------:|:------:|:-----------:|
| EMA Stack / Trend | ✅ (3 screens) | — | ✅ (Axis 1, 5) |
| Volatility Squeeze | ✅ | — | ✅ (Axis 4) |
| Relative Volume | ✅ | — | ✅ (Axis 3) |
| Momentum (RSI/ADX) | ✅ | — | ✅ (Axis 2) |
| **Short Interest** | — | ✅ | — |
| **Earnings Catalysts** | — | ✅ | — |
| **Fundamental Growth** | ✅ (Small Cap) | ✅ (CANSLIM, Growth) | — |
| **Value (P/E, PEG)** | — | — | — |
| **Insider Activity** | — | — | — (captured in RAG) |
| Bearish/Shorts | ✅ | — | — |
| Options/Gamma | ✅ | — | ✅ (Axis 4) |

### Remaining Gaps (Future Screens)
- **Value investing** (low P/E, PEG, dividend yield)
- **Insider buying** clusters
- **Sector rotation** momentum
- **Dark pool / unusual options** activity
