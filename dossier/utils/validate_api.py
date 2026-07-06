"""
API response validators for the dossier data-fetch stages.

Three known failure shapes this repo has been burned by:
  1. yfinance .history() returns a DataFrame missing expected price columns
  2. yfinance .info returns None or an empty dict (silent fundamentals failure)
  3. Tradier returns the *string* "null" instead of JSON null for empty chains/positions

Usage:
    from dossier.utils.validate_api import (
        check_yfinance_history,
        check_yfinance_info,
        is_tradier_null,
        safe_json,
        safe_tradier_quote,
    )
"""

import sys

_REQUIRED_HISTORY_COLS = {"Close", "High", "Low", "Volume"}


def check_yfinance_history(df, ticker: str, min_rows: int = 2) -> tuple[bool, str]:
    """
    Validate a yfinance .history() DataFrame before any column access.

    Returns (ok, reason). When ok is False, reason explains what is wrong so
    the caller can log it and bail out instead of crashing on a KeyError.
    """
    if df is None:
        return False, f"{ticker}: history returned None"
    if df.empty:
        return False, f"{ticker}: history is empty"
    missing = _REQUIRED_HISTORY_COLS - set(df.columns)
    if missing:
        return False, f"{ticker}: history missing columns: {sorted(missing)}"
    if len(df) < min_rows:
        return False, f"{ticker}: only {len(df)} row(s) — need at least {min_rows}"
    return True, ""


def check_yfinance_info(info, ticker: str) -> dict:
    """
    Normalize a yfinance .info result to a non-None dict.

    Logs a warning when the response is empty so the caller knows fundamentals
    are unavailable rather than treating missing keys as zeros silently.
    """
    if not info:
        print(
            f"    [WARN] {ticker}: yfinance .info returned empty"
            " — fundamentals unavailable",
            file=sys.stderr,
        )
        return {}
    return info


def is_tradier_null(value) -> bool:
    """
    True when a Tradier API value represents "nothing here".

    Tradier returns the *string* "null" (not JSON null) for empty option
    chains, positions, and similar lists. This check catches that alongside
    the normal None / empty-collection cases.
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() == "null":
        return True
    if isinstance(value, (dict, list)) and len(value) == 0:
        return True
    return False


def safe_json(response, context: str = ""):
    """
    Parse a requests.Response as JSON; return None and log on failure.

    Prevents a single malformed HTML error page from crashing the pipeline
    with an opaque JSONDecodeError.
    """
    try:
        return response.json()
    except Exception as exc:
        label = f" [{context}]" if context else ""
        print(
            f"    [WARN]{label} Response is not valid JSON"
            f" (status={response.status_code}): {exc}",
            file=sys.stderr,
        )
        return None


def safe_tradier_quote(response, ticker: str = "") -> dict | None:
    """
    Parse a Tradier `/markets/quotes` response into a single quote dict.

    Three call sites (options_flow.py, sf_gex.py, gamma_pin_screener.py) used
    to do `response.json().get("quotes", {}).get("quote", {})` directly. That
    breaks with an AttributeError when Tradier returns the *string* "null"
    for `quotes` (the same quirk `is_tradier_null` was built for), and it
    doesn't normalize the single-symbol dict vs multi-symbol list shape of
    `quote`. Returns None (with a logged warning) instead of raising.
    """
    data = safe_json(response, context=f"Tradier quotes[{ticker}]" if ticker else "Tradier quotes")
    if not isinstance(data, dict):
        return None
    quotes = data.get("quotes")
    if is_tradier_null(quotes) or not isinstance(quotes, dict):
        print(
            f"    [WARN] Tradier quotes empty for {ticker or '?'}",
            file=sys.stderr,
        )
        return None
    quote = quotes.get("quote")
    if isinstance(quote, list):
        quote = quote[0] if quote else None
    if is_tradier_null(quote) or not isinstance(quote, dict):
        return None
    return quote
