#!/usr/bin/env python3
"""
Finviz Screen Scraper — Pulls results from Finviz screener URLs.

Each screen is a named function that returns a list of ticker dicts with metadata.
Results are deduped and merged into the pipeline's signal flow.

Usage:
    from strategies.finviz_screens import run_all_finviz_screens
    results = run_all_finviz_screens()
    # Returns: [{"ticker": "GME", "screen": "Short Squeeze", "score": 85, ...}, ...]
"""

import re
import time
import requests
from typing import Optional
from dataclasses import dataclass, field

# Finviz blocks default user agents
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Rate limit: 1 request per 2 seconds to avoid 429s
_last_request_time = 0.0


@dataclass
class FinvizResult:
    ticker: str
    screen: str
    company: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: str = ""
    price: float = 0.0
    change_pct: float = 0.0
    volume: str = ""
    extra: dict = field(default_factory=dict)


def _fetch_finviz(url: str, max_results: int = 20) -> list[dict]:
    """Fetch and parse Finviz screener results.

    Returns list of row dicts with columns from the screener table.
    """
    global _last_request_time

    # Rate limit
    elapsed = time.time() - _last_request_time
    if elapsed < 2.0:
        time.sleep(2.0 - elapsed)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        _last_request_time = time.time()

        if resp.status_code == 429:
            print("  ⚠️ Finviz rate limited, waiting 10s...")
            time.sleep(10)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            _last_request_time = time.time()

        if resp.status_code != 200:
            print(f"  ❌ Finviz returned {resp.status_code}")
            return []

        html = resp.text
    except Exception as e:
        print(f"  ❌ Finviz fetch error: {e}")
        return []

    # Parse the screener table — Finviz uses a specific table structure
    # Extract ticker symbols from the screener results
    rows = []

    # Pattern: screener table rows contain ticker links like <a class="screener-link-primary" href="quote.ashx?t=TICKER">TICKER</a>
    # More robust: find all table rows in the screener-body-table
    ticker_pattern = re.compile(
        r'<a[^>]*href="quote\.ashx\?t=([A-Z.]+)"[^>]*class="screener-link-primary"[^>]*>\1</a>',
        re.IGNORECASE
    )

    # Simpler approach: find all unique tickers in quote links
    tickers_found = re.findall(
        r'quote\.ashx\?t=([A-Z]{1,6})',
        html
    )

    # Dedupe while preserving order
    seen = set()
    unique_tickers = []
    for t in tickers_found:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)

    # For each ticker, try to extract basic data from the row
    for ticker in unique_tickers[:max_results]:
        rows.append({"ticker": ticker})

    return rows


# ═══════════════════════════════════════════════════════════
# SCREEN 1: Short Squeeze
# ═══════════════════════════════════════════════════════════

SHORT_SQUEEZE_URL = (
    "https://finviz.com/screener.ashx?v=131"
    "&f=sh_avgvol_o100,sh_instown_u50,sh_price_o2,sh_short_o15"
    "&ft=4&o=-shortinterestshare"
)

def screen_short_squeeze(max_results: int = 10) -> list[FinvizResult]:
    """High short interest + low institutional ownership = squeeze candidates."""
    print("  🩳 Running Short Squeeze screen...")
    rows = _fetch_finviz(SHORT_SQUEEZE_URL, max_results)
    return [
        FinvizResult(
            ticker=r["ticker"],
            screen="Short Squeeze",
            extra={"short_interest": "high", "institutional": "low"}
        )
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# SCREEN 2: CANSLIM
# ═══════════════════════════════════════════════════════════

CANSLIM_URL = (
    "https://finviz.com/screener.ashx?v=111"
    "&f=fa_eps5years_o20,fa_epsqoq_o20,fa_epsyoy_o20,"
    "fa_sales5years_o20,fa_salesqoq_o20,sh_curvol_o200"
    "&ft=4"
)

def screen_canslim(max_results: int = 10) -> list[FinvizResult]:
    """CANSLIM: C=Current Earnings, A=Annual, N=New, S=Supply/Demand, L=Leader, I=Institutional, M=Market."""
    print("  📊 Running CANSLIM screen...")
    rows = _fetch_finviz(CANSLIM_URL, max_results)
    return [
        FinvizResult(
            ticker=r["ticker"],
            screen="CANSLIM",
            extra={"methodology": "O'Neil growth"}
        )
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# SCREEN 3: Weekly Earnings Gap Up
# ═══════════════════════════════════════════════════════════

EARNINGS_GAP_URL = (
    "https://finviz.com/screener.ashx?v=141"
    "&f=earningsdate_tomorrowafter,sh_avgvol_o400,"
    "sh_curvol_o50,sh_short_u25,ta_averagetruerange_o0.5,ta_gap_u2"
    "&ft=4&o=-perfytd"
)

def screen_earnings_gap(max_results: int = 10) -> list[FinvizResult]:
    """Upcoming earnings + gap potential + volume + low short interest."""
    print("  📅 Running Earnings Gap Up screen...")
    rows = _fetch_finviz(EARNINGS_GAP_URL, max_results)
    return [
        FinvizResult(
            ticker=r["ticker"],
            screen="Earnings Gap Up",
            extra={"catalyst": "earnings", "gap_direction": "up"}
        )
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# SCREEN 4: Consistent Growth + Bullish Trend
# ═══════════════════════════════════════════════════════════

CONSISTENT_GROWTH_URL = (
    "https://finviz.com/screener.ashx?v=141"
    "&f=fa_eps5years_pos,fa_epsqoq_o20,fa_epsyoy_o25,"
    "fa_epsyoy1_o15,fa_estltgrowth_pos,fa_roe_o15,"
    "sh_instown_o10,sh_price_o15,"
    "ta_highlow52w_a90h,ta_rsi_nos50"
    "&ft=4&o=-perfytd"
)

def screen_consistent_growth(max_results: int = 10) -> list[FinvizResult]:
    """Consistent multi-year growth + strong technicals + near 52w high."""
    print("  📈 Running Consistent Growth screen...")
    rows = _fetch_finviz(CONSISTENT_GROWTH_URL, max_results)
    return [
        FinvizResult(
            ticker=r["ticker"],
            screen="Consistent Growth",
            extra={"eps_growth": ">20% QoQ", "near_52w_high": True}
        )
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# SCREEN 5: Oversold + Upcoming Earnings
# ═══════════════════════════════════════════════════════════

OVERSOLD_EARNINGS_URL = (
    "https://finviz.com/screener.ashx?v=141"
    "&f=cap_smallover,earningsdate_thismonth,"
    "fa_epsqoq_o15,fa_grossmargin_o20,"
    "sh_avgvol_o750,sh_curvol_o1000,"
    "ta_perf_52w10o,ta_rsi_nob50"
    "&ft=4&o=perfytd"
)

def screen_oversold_earnings(max_results: int = 10) -> list[FinvizResult]:
    """Beaten-down stocks with upcoming earnings catalyst + quality fundamentals."""
    print("  🔻 Running Oversold + Earnings screen...")
    rows = _fetch_finviz(OVERSOLD_EARNINGS_URL, max_results)
    return [
        FinvizResult(
            ticker=r["ticker"],
            screen="Oversold + Earnings",
            extra={"catalyst": "earnings", "setup": "oversold_reversal"}
        )
        for r in rows
    ]


# ═══════════════════════════════════════════════════════════
# Master Runner
# ═══════════════════════════════════════════════════════════

ALL_SCREENS = [
    screen_short_squeeze,
    screen_canslim,
    screen_earnings_gap,
    screen_consistent_growth,
    screen_oversold_earnings,
]


def run_all_finviz_screens(max_per_screen: int = 10) -> list[dict]:
    """Run all Finviz screens and return unified signal list.

    Returns list of dicts compatible with the pipeline's scanner_signals format:
        {"symbol": str, "strategy": str, "direction": str, "score": float, ...}
    """
    all_signals = []
    seen_tickers = set()

    for screen_fn in ALL_SCREENS:
        try:
            results = screen_fn(max_results=max_per_screen)
            for r in results:
                if r.ticker in seen_tickers:
                    continue
                seen_tickers.add(r.ticker)

                all_signals.append({
                    "symbol": r.ticker,
                    "strategy": f"Finviz: {r.screen}",
                    "direction": "LONG",
                    "score": 0,  # No score from Finviz — Ghost Alpha will grade it
                    "rationale": [r.screen],
                    "extra": r.extra,
                })
        except Exception as e:
            print(f"  ⚠️ Screen failed: {e}")

    print(f"  ✅ Finviz total: {len(all_signals)} unique tickers from {len(ALL_SCREENS)} screens")
    return all_signals


if __name__ == "__main__":
    results = run_all_finviz_screens()
    for r in results:
        print(f"  {r['symbol']:6s} — {r['strategy']}")
