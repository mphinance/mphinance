---
name: coil-scan
description: >-
  Daily scanner that finds stocks sitting in the "bottom of the coil" using a
  dual-timeframe Williams %R Trend Exhaustion indicator, then flags the ones
  that just triggered out. Silent data feed for Michael — he writes trade posts
  only when he likes a name.
  Use when the user asks about "coil scan", "bottom of the coil",
  "what's coiled", "daily coil", "%R exhaustion scan", "what's oversold and
  turning", or wants to find deeply oversold names that are just starting to
  reverse.
trigger_phrases:
  - coil scan
  - bottom of the coil
  - what's coiled
  - daily coil
  - "%R exhaustion scan"
  - what's oversold and turning
  - rte scan
  - williams %r coil
---

# Coil Scan — dual-timeframe %R Trend Exhaustion

Mirrors the **"%R Trend Exhaustion [upslidedown]"** TradingView indicator
(dual timeframe 21 + 112).  Finds stocks that are *both* deeply oversold AND
just starting to reverse.

## The indicator math

- **%R(n)** = Williams %R = `100 * (close - highestHigh_n) / (highestHigh_n - lowestLow_n)`, range −100…0.
- **Fast leg** = EMA(7) of %R(21).
- **Slow leg** = EMA(3) of %R(112).
- **Threshold (TH)** = −80.
- **In the coil**: both fast AND slow ≤ −80.  The short-term AND the structural
  picture are both deeply oversold.  This is the *stalk zone* — a name can sit
  here for days/weeks before the trigger fires.
- **Triggered out**: fast crossed back above −80 while it was recently (within
  ~20 bars) coiled on both legs.  The slow leg still lagging confirms the
  structural exhaustion hasn't reset — this is the bullish reversal signal.

## Two output buckets

### ⚡ TRIGGERED OUT (≤3 days ago)
Fast just crossed back above −80.  These are *actionable reversal candidates*.

A **sanity check** filters false-positives:
- If the close is already >5% above the price on the trigger date → tagged
  **"already ran — not fresh"** and downranked.
- If the close is now above EMA21 → same tag.

*The canonical false-positive this catches: SLB crossed up but had already run
+4% to just under its 21EMA by the time the scan ran — that's a chase, not an
entry.  It lands in the sanity-filtered section, not the fresh list.*

### 🟢 IN THE COIL (stalk candidates)
Both legs ≤ −80, no trigger yet.  Sorted deepest-first (most negative slow
leg = most structurally exhausted).

The **days-in-coil** counter comes from the persistent state file
(`state/coil_watch.json`), so the scan can say "IREN — day 6 in the coil."
A name stays in the store until it triggers or exits the coil entirely.

## Per-name display

```
SYM    fast%R   slow%R   depth    close   day-in-coil   vs SMA200  vs EMA21
IREN    -92.3    -88.1   -8.1    $7.42   day 3          below SMA200  below EMA21
```

- **depth**: `min(fast, slow) − (−80)`.  Negative = deeper in the hole.
- **above/below SMA200 + EMA21**: from live technicals endpoint.

## How to run

From the repo root or anywhere under it:

```bash
python .claude/skills/coil-scan/scripts/coil_scan.py
```

Options:

```bash
# smoke test against a short list
python coil_scan.py --universe IREN,RGTI,SMCI,SLB,FIG,GLD,ASTS

# limit universe size
python coil_scan.py --limit 50

# write JSON output
python coil_scan.py --json /tmp/coil_2026-07-19.json

# custom universe file (one ticker per line, or comma-separated)
python coil_scan.py --universe /tmp/my_watchlist.txt
```

Universe defaults to: all live TDPro screeners + stock-recap persistent watch
list (falls back to the most recent `stock-recap/runs/*/raw/screener_*.json`
if the live API is unavailable).  Aim: ~150–200 names.

## Persistence

`state/coil_watch.json` is keyed by ticker and tracks:
- `firstSeen` — date first seen in the coil
- `daysInCoil` — rolling counter updated each run
- `entryClose` / `lastClose` — price anchors
- `triggered` / `triggerDate` — when the cross fired

On each run: newly-coiled names are added, existing names increment their
counter, triggered names are flagged, and names that left the coil without
triggering are dropped.

## Data sources

- **Bars**: `GET /api/agent/ticker/{SYMBOL}/chart-data?days=365`
  (TraderDaddy Pro Railway API; Bearer token from `.env_agent_api`).
  Needs ≥115 bars for the slow %R(112) leg.
- **Live technicals**: `GET /api/agent/ticker/{SYMBOL}`
  (close, ema21, sma200, atr, rsi — used for sanity check + display).
- **Universe**: `GET /api/screeners` + `GET /api/screeners/{id}/run` × 10.

## Interpreting results for Michael

- **Empty IN THE COIL list**: tape is not oversold broadly — that's fine,
  nothing to stalk beats a list of knives.
- **Triggered + already ran**: it moved without you.  Note it for the next
  pullback but don't chase.
- **Triggered fresh + below EMA21**: highest-quality entry zone.  Fast is
  turning, structure is still washed out, price hasn't reclaimed the mean yet.
- **In coil day 10+**: structural exhaustion is deep.  The longer it coils, the
  more compressed the spring.  Watch for the fast leg to tick back above −80.

The scan is a *data layer* — Michael confirms setups on Ghost Flow (the %R
EXHAUST panel is visible there) before sizing.
