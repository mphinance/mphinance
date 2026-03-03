"""
TickerTrace API client — institutional ETF activity data.

Calls the deployed TickerTrace API to get what institutions are buying/selling.
"""

import httpx
from dossier.config import TICKERTRACE_API_BASE


def _get(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to the TickerTrace API."""
    url = f"{TICKERTRACE_API_BASE}{endpoint}"
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"  [WARN] TickerTrace API error ({endpoint}): {e}")
        return {}


def get_signals() -> dict:
    """Full signal payload: buying/selling with conviction, sector flow, divergences."""
    return _get("/api/v1/signals")


def get_changes(direction: str = None, limit: int = 50) -> dict:
    params = {"limit": limit}
    if direction:
        params["direction"] = direction
    return _get("/api/v1/changes", params)


def get_sectors() -> dict:
    return _get("/api/v1/sectors")


def get_divergences() -> list:
    return _get("/api/v1/divergences")


def get_ticker_detail(ticker: str) -> dict:
    return _get(f"/api/v1/ticker/{ticker}")


def get_stats() -> dict:
    return _get("/api/v1/stats")


def fetch_institutional_data() -> dict:
    """Main entry point: fetch all institutional data needed for the report."""
    print("  Fetching TickerTrace institutional data...")

    payload = get_signals()
    if not payload:
        return {
            "as_of_date": "unknown",
            "stats": {},
            "top_buying": [],
            "top_selling": [],
            "sector_inflows": [],
            "sector_outflows": [],
            "divergences": [],
            "recent_changes": [],
        }

    signals = payload.get("signals", {})
    sector_flow = payload.get("sectorFlow", {})

    return {
        "as_of_date": payload.get("asOfDate", "unknown"),
        "stats": payload.get("stats", {}),
        "top_buying": signals.get("buying", []),
        "top_selling": signals.get("selling", []),
        "sector_inflows": sector_flow.get("inflows", []),
        "sector_outflows": sector_flow.get("outflows", []),
        "divergences": payload.get("divergences", []),
        "recent_changes": payload.get("changes", [])[:25],
    }
