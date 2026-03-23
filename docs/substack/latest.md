# I Gave My AI a Musical Equalizer for Stock Prices

**Status:** DRAFT IDEA — not written yet
**Inspired by:** [Variational Mode Decomposition - An Elegant Tool for Time Series](https://substack.com/inbox/post/190412761) by Sofien Kaabar, CFA (Engineering Alpha)
**Date added:** 2026-03-23

---

## The Hook

What if you could listen to a stock chart like music? Bass for the big trend. Mids for the swing. Treble for the noise. Then turn the treble knob to zero and trade on what's left.

That's VMD (Variational Mode Decomposition). We just built it into the pipeline.

## What VMD Does (In Human)

- Takes a price time series and separates it into K smooth oscillating modes
- Unlike EMAs: **zero lag**, adapts locally, doesn't blur the signal
- Unlike Fourier: **learns** the decomposition instead of forcing sine waves
- Python library: `vmdpy` — 6KB, installs in 2 seconds

## What It Does For Us (Show, Don't Tell)

Our `vmd_enrichment.py` already runs in the pipeline. Here's what today looked like:

| Ticker | Regime | Trend | Swing | Forecast |
|--------|--------|-------|-------|----------|
| SPY | transitioning | -0.24 📉 | oversold | bearish 83% |
| NVDA | mean_reverting | -0.12 📉 | oversold 17% | bearish 51% |
| DDD | mean_reverting | -0.04 📉 | mid_cycle 78% | neutral |
| **RR** | **transitioning** | **-0.41 📉** | **overbought 97%** | neutral |

RR showing overbought at swing level while everything else is oversold = the swing mode caught an inflection that RSI missed.

## Post Structure Ideas

1. **The equalizer metaphor** — bass/mid/treble visual with actual decomposed charts
2. **RSI vs VMD momentum** — side by side, show where VMD catches what RSI can't
3. **Regime detection** — SPY transitioning vs DDD mean-reverting, what that means for trading
4. **The code** — show the 10-line core (VMD call + mode sorting), link to full module
5. **Recovery tie-in** — "Separating signal from noise — in markets and in life"

## Key Quote from Source Article

> "VMD is like a self-tuning equalizer that listens to your time series and separates it into its main rhythms — fast, medium, and slow oscillations — without adding lag or distorting phase."

## Files to Reference
- `dossier/data_sources/vmd_enrichment.py` — our implementation
- Source article: https://substack.com/inbox/post/190412761
