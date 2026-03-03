"""
Market Regime Detection — VIX + Sector Rotation.

Determines the current market environment for tactical positioning.
"""

import yfinance as yf
import pandas as pd
from dossier.config import VIX_REGIMES, SECTOR_ETFS


def detect_vix_regime() -> dict:
    """Fetch VIX level and classify the current market regime."""
    print("  Detecting VIX regime...")
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if hist.empty:
            return {"vix_level": 0, "regime_name": "Unknown", "regime_desc": "No VIX data"}

        vix_level = round(float(hist["Close"].iloc[-1]), 2)

        regime_name = "Unknown"
        regime_desc = ""
        for key, regime in VIX_REGIMES.items():
            if vix_level < regime["max"]:
                regime_name = regime["name"]
                regime_desc = regime["desc"]
                break

        return {
            "vix_level": vix_level,
            "regime_name": regime_name,
            "regime_desc": regime_desc,
        }
    except Exception as e:
        print(f"  [WARN] VIX fetch failed: {e}")
        return {"vix_level": 0, "regime_name": "Unknown", "regime_desc": str(e)}


def get_sector_rotation() -> list[dict]:
    """Fetch sector ETF performance across 1d, 5d, 20d timeframes."""
    print("  Fetching sector rotation data...")
    results = []

    for etf in SECTOR_ETFS:
        try:
            ticker = yf.Ticker(etf)
            hist = ticker.history(period="1mo")
            if hist.empty or len(hist) < 2:
                continue

            close = hist["Close"]
            current = float(close.iloc[-1])

            pct_1d = round(((current / float(close.iloc[-2])) - 1) * 100, 2) if len(close) >= 2 else 0
            pct_5d = round(((current / float(close.iloc[-min(5, len(close))])) - 1) * 100, 2) if len(close) >= 5 else 0
            pct_20d = round(((current / float(close.iloc[0])) - 1) * 100, 2)

            results.append({
                "sector": etf,
                "1d": pct_1d,
                "5d": pct_5d,
                "20d": pct_20d,
            })
        except Exception as e:
            print(f"  [WARN] Failed to fetch {etf}: {e}")
            continue

    results.sort(key=lambda x: x["5d"], reverse=True)
    return results


def fetch_market_regime() -> dict:
    """Main entry point: get full market regime data."""
    vix = detect_vix_regime()
    sectors = get_sector_rotation()

    return {
        "vix": vix,
        "sector_rotation": sectors,
        "sector_leaders": [s["sector"] for s in sectors[:3]],
        "sector_laggards": [s["sector"] for s in sectors[-3:]],
    }
