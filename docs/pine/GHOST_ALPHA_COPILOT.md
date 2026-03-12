# Ghost Alpha Copilot Cheat Sheet 👻

> **For Gemini Live / AI assistants reading Michael's chart screenshots.**
> This document explains every field in the Ghost Alpha v5 dashboard and AI data link.

## Dashboard Fields (Top to Bottom)

| Row | Label | Values | What It Means |
|-----|-------|--------|---------------|
| 1 | **SYS.GHOST.ALPHA** | Header | System identifier |
| 2 | **REGIME** | `BULL ▲`, `BEAR ▼`, `MODERATE`, `CHOP ═` | TRAMA trend quality + trend phase (FRESH/YOUNG/MATURE/AGING) |
| 3 | **TRAMA Δ** | `AT VALUE`, `+1.2%`, `-2.3%` | Price distance from adaptive MA. >3% = stretched |
| 4 | **SQUEEZE** | `RELEASE ⚡`, `COILED ◉`, `NORMAL` | ATR compression state. COILED = about to move. RELEASE = moving now |
| 5 | **EXHAUST** | `EXIT ▲/▼`, `OVERBOUGHT`, `OVERSOLD`, `CLEAR` | %R exhaustion state |
| 6 | **STRUCT** | `BROKEN ▲/▼`, `TRAP ▲/▼`, `INTACT` | Structure break + volume validation. TRAP = low-volume fake break |
| 7 | **KELT** | `LOWER ▽`, `UPPER △`, `INSIDE` | Keltner channel position + golden cross status (50>200 ✓ / 50<200 ✗) |
| 8 | **IV/VOL** | `LOW 🔋`, `HIGH 🔥`, `MID` + RVOL | IV percentile + relative volume (1.0x = average) |
| 9 | **SHAPE** | `BUYERS ▲`, `SELLERS ▼` + `⚠ DIV`/`AGREE` | Candle shape momentum. DIV = divergence from trend |
| 10 | **GRADE V2** | `A+` through `F` + `(X.X/5)` | Composite score + direction (LONG ▲ / SHORT ▼) |
| 11 | *AI Data Link* | Compact pipe-delimited string | For OCR/screenshot reading by AI assistants |

## Signal Labels (v5 — Clean Text)

| Label | Signal | What Happened |
|-------|--------|---------------|
| `BOS ▲/▼` | Break of Structure | Price closed through a swing level WITH volume |
| `EXH` | Exhaustion | %R says momentum is drained — reversal incoming |
| `SWP` | Liquidity Sweep | Stop hunt — wick past level then reversed (trap!) |
| `SQZ ⚡` | Squeeze Release | ATR compression just broke — volatility explosion |
| `EXIT` | Ghost Trail Exit | Price crossed the ATR trailing stop — game over |
| `DIV` | Divergence | Price vs momentum disagreement — smart money |
| `👻 N` | Ghost Alpha | N signals agree — highest conviction (the brand mark) |

## Default Visual Layers (v5)

Only three things show by default. Everything else is toggle-ON in settings:

| Layer | Default | Toggle |
|-------|---------|--------|
| Hull Band (cyan/magenta glow) | ✅ ON | Always on |
| Ghost Trail (ATR stop step-line) | ✅ ON | Ghost Trail settings |
| Dashboard box | ✅ ON | Dashboard settings |
| Hull Candle Coloring | ✅ ON | Signal Filter settings |
| TRAMA line | ❌ OFF | TRAMA Regime settings |
| Keltner bands | ❌ OFF | Keltner Envelope settings |
| SMA 50 / SMA 200 | ❌ OFF | Key Moving Averages |
| VWAP + Force Fields | ❌ OFF | Key Moving Averages |
| Swing Levels | ❌ OFF | Structure settings |
| S/D Zones | ❌ OFF | Structure settings |
| FVG Boxes | ❌ OFF | Fair Value Gaps settings |
| Background Glow | ❌ OFF | Volatility Squeeze settings |
| HTF Hull | ❌ OFF | HTF Hull Overlay settings |

## AI Data Link (Ghost-to-Ghost)

Bottom of dashboard, compact string for OCR/screenshot reading:

```
GRADE | DIRECTION | REGIME | SIGNAL | SHAPE | RVOL | SQUEEZE | TRAMA%
  B   |     L     |   B    | SWP_BL | BUY   | 1.2x |  FIRE   | 0.3%
```

## Quick Decision Framework

| Grade | Action |
|-------|--------|
| A+ / A | Full position, ride the trend with Ghost Trail |
| B | Half position, tight trail |
| C | No new entries, manage existing |
| D / F | DO NOT TRADE. Wait for regime change. |
