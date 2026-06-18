"""
watchlist_ingest.py — ingest + cross-reference the nightly analyst watchlist.

Phase 3.6 of DAILY_REVIEW_PLAN.md. One of Mike's contacts emails a free-text
watchlist every night (e.g. 2026-06-17: "NFLX UMAC UAMY HOOD QBTS WDC AMD RKLB").
This module turns that external email into a structured ticker list and then
cross-references it against the day's own signal sources so the report can say
"your guy flagged 8 — the system independently agrees on N, the rest are
off-radar (the narrow-universe gap the scanline layer is meant to close)."

Three pieces:
  - parse_watchlist(text)            : free-text email body -> ordered ticker list
  - cross_reference(watch, signals)  : watchlist x signal sources -> overlap report
  - fetch_latest_watchlist_email()   : STUB (returns None) — email plumbing TBD

Never raises. Every public function degrades to [] / {} / None on bad input so a
malformed email or missing mailbox can't sink the daily run.
"""
from __future__ import annotations

import re

# 1-5 uppercase letters, optionally $-prefixed, on word boundaries.
_TICKER_RE = re.compile(r"\$?\b([A-Z]{1,5})\b")

# Common English words that pattern-match the ticker shape but aren't tickers.
# Mixed in with prose, an email body is full of these — filter them out.
# (These are real Nasdaq/NYSE symbols in some cases, e.g. A, ALL, ON, OR, but in
# a free-text watchlist the false-positive risk vastly outweighs the chance the
# analyst literally means those tickers as bare uppercase words.)
_STOPWORDS = frozenset({
    "A", "I", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "HE", "IF", "IN", "IS",
    "IT", "ME", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "WE",
    "ALL", "AND", "ANY", "ARE", "BUT", "CAN", "DAY", "FOR", "GET", "GOT", "HAD",
    "HAS", "HER", "HIM", "HIS", "HOW", "ITS", "LET", "MAY", "NEW", "NOT", "NOW",
    "OFF", "OLD", "ONE", "OUR", "OUT", "OWN", "PER", "PUT", "SEE", "SHE", "THE",
    "TOO", "TOP", "TWO", "USE", "WAS", "WAY", "WHO", "WHY", "YES", "YET", "YOU",
    "ALSO", "BEEN", "BOTH", "CALL", "DOWN", "EACH", "ELSE", "FROM", "GOOD",
    "HAVE", "HERE", "HIGH", "INTO", "JUST", "KEEP", "LIKE", "LONG", "LOOK",
    "MAKE", "MORE", "MOST", "MUCH", "NEXT", "ONLY", "OVER", "PICK", "PUTS",
    "SAME", "SEEN", "SOME", "SUCH", "THAN", "THAT", "THEM", "THEN", "THEY",
    "THIS", "TIME", "VERY", "WANT", "WELL", "WHAT", "WHEN", "WILL", "WITH",
    "YOUR", "ABOUT", "AFTER", "AGAIN", "BELOW", "COULD", "EVERY", "GREAT",
    "HERES", "MIGHT", "NIGHT", "SHALL", "SHORT", "SINCE", "STILL", "THERE",
    "THESE", "THING", "THINK", "TODAY", "TRADE", "UNDER", "UNTIL", "WATCH",
    "WHERE", "WHICH", "WHILE", "WOULD",
    # finance prose that shouldn't be read as a symbol
    "BUY", "SELL", "HOLD", "CALLS", "STOP", "GAP", "RUN", "BIG", "LIST", "EOD",
    "PM", "AM", "ET", "PT", "CT", "EPS", "IPO", "ATH", "YOLO", "DD",
})


def parse_watchlist(text: str) -> list[str]:
    """Extract ticker symbols from a free-text watchlist email body.

    Tickers are uppercase 1-5 letter symbols, separated by spaces/commas/newlines,
    sometimes prefixed with `$`. Sentences and prose are tolerated — common English
    stopword false-positives are filtered out. Result is deduped, order preserved
    (first occurrence wins).

    Examples:
        "NFLX UMAC HOOD"                       -> ["NFLX", "UMAC", "HOOD"]
        "$AMD, $WDC and watch RKLB tomorrow"   -> ["AMD", "WDC", "RKLB"]

    Returns [] on empty / non-string / no-match input. Never raises.
    """
    if not text or not isinstance(text, str):
        return []

    out: list[str] = []
    seen: set[str] = set()
    try:
        for m in _TICKER_RE.finditer(text):
            sym = m.group(1)
            if sym in _STOPWORDS or sym in seen:
                continue
            seen.add(sym)
            out.append(sym)
    except Exception as e:  # pathological input — degrade, don't crash the run
        print(f"[watchlist_ingest] parse_watchlist failed: {e}")
        return out
    return out


def cross_reference(watch: list[str], signals_by_source: dict[str, list[str]]) -> dict:
    """Cross-reference the analyst watchlist against the day's signal sources.

    Args:
        watch: tickers from parse_watchlist().
        signals_by_source: e.g. {"universe": [...], "triangle": [...],
            "flow": [...], "institutional": [...], "momentum": [...]}. Values are
            ticker lists; matching is case-insensitive.

    Returns:
        {
          "tickers": [
            {"ticker": "AMD", "matched_sources": ["flow", "institutional"],
             "status": "confirmed"},
            {"ticker": "UMAC", "matched_sources": [], "status": "off_radar"},
            ...
          ],
          "summary": {
            "confirmed":     ["AMD", "WDC"],   # >=1 source agreed
            "off_radar":     ["UMAC", ...],    # 0 sources — narrow-universe gap
            "overlap_count": 2,
          },
        }

    status is "confirmed" when >=1 source contains the ticker, else "off_radar".
    Returns the empty shape on bad input. Never raises.
    """
    empty = {"tickers": [], "summary": {"confirmed": [], "off_radar": [], "overlap_count": 0}}
    if not watch or not isinstance(watch, list):
        return empty

    try:
        # Normalize each source into an uppercase set for O(1) membership tests.
        # Preserve source order as given so matched_sources reads predictably.
        source_sets: list[tuple[str, set[str]]] = []
        if isinstance(signals_by_source, dict):
            for src, tickers in signals_by_source.items():
                if not tickers:
                    source_sets.append((src, set()))
                    continue
                source_sets.append((src, {str(t).upper() for t in tickers if t}))

        per_ticker: list[dict] = []
        confirmed: list[str] = []
        off_radar: list[str] = []

        for raw in watch:
            tkr = str(raw).upper()
            matched = [src for src, s in source_sets if tkr in s]
            status = "confirmed" if matched else "off_radar"
            per_ticker.append({
                "ticker": tkr,
                "matched_sources": matched,
                "status": status,
            })
            (confirmed if matched else off_radar).append(tkr)

        return {
            "tickers": per_ticker,
            "summary": {
                "confirmed": confirmed,
                "off_radar": off_radar,
                "overlap_count": len(confirmed),
            },
        }
    except Exception as e:
        print(f"[watchlist_ingest] cross_reference failed: {e}")
        return empty


def fetch_latest_watchlist_email() -> str | None:
    """STUB — fetch the body of the most recent nightly analyst watchlist email.

    Not implemented yet. Returns None so callers can fall back to a manually
    pasted watchlist (or skip the overlay) without error.

    Intended implementation (two paths, per DAILY_REVIEW_PLAN.md Phase 3.6):

      1. Interactive runs (Claude session w/ claude.ai Gmail MCP available):
         use `mcp__claude_ai_Gmail__search_threads` to find the latest thread
         from the known sender (e.g. `from:<analyst@example.com> newer_than:1d`),
         then `mcp__claude_ai_Gmail__get_thread` to pull the newest message body,
         and feed that text to parse_watchlist(). The Gmail MCP is interactive
         only — it won't be present on the headless cron.

      2. Headless / cron runs (claude.ai MCPs absent on the Hetzner box):
         use stdlib `imaplib` + `email` against Gmail IMAP with a dedicated
         APP PASSWORD (not the account password; store in the consolidated .env,
         chmod 600). Search the analyst's sender + most-recent date, extract the
         text/plain part, and parse. Alternative: a Gmail filter that
         forward-labels the watchlist mail, then read that label.

    TODO before implementing:
      - Identify the exact SENDER address (the analyst) to scope the search and
        avoid ingesting an unrelated email's tickers.
      - Confirm the PARSE RULE — current emails are a space/comma-separated
        ticker list; parse_watchlist() already handles prose, but verify the
        sender's format hasn't drifted (e.g. tables, attachments).
      - Decide recency window / dedupe so a stale night isn't re-ingested.
    """
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1 — clean sample (real 2026-06-17 watchlist)")
    print("=" * 60)
    sample = "NFLX UMAC UAMY HOOD QBTS WDC AMD RKLB"
    parsed_clean = parse_watchlist(sample)
    print(f"input : {sample!r}")
    print(f"output: {parsed_clean}")
    print(f"count : {len(parsed_clean)}")

    print()
    print("=" * 60)
    print("TEST 2 — noisy multiline variant ($ signs, commas, prose)")
    print("=" * 60)
    noisy = (
        "Hey, here's the list for tomorrow.\n"
        "Top conviction: $NFLX, $UMAC and UAMY.\n"
        "Also watching HOOD, QBTS, and $WDC for a breakout.\n"
        "I think AMD will run if the market is green, "
        "and keep an eye on RKLB too.\n"
        "Let me know what you see. Talk to you in the AM."
    )
    parsed_noisy = parse_watchlist(noisy)
    print("input :")
    for line in noisy.splitlines():
        print(f"    {line}")
    print(f"output: {parsed_noisy}")
    print(f"count : {len(parsed_noisy)}")

    # Confirm no stopwords leaked through the noisy parse.
    leaked = [t for t in parsed_noisy if t in _STOPWORDS]
    print(f"stopword leaks: {leaked if leaked else 'NONE ✅'}")
    expected = ["NFLX", "UMAC", "UAMY", "HOOD", "QBTS", "WDC", "AMD", "RKLB"]
    print(f"matches clean watchlist set: {set(parsed_noisy) == set(expected)}")

    print()
    print("=" * 60)
    print("TEST 3 — cross_reference (fake signals where AMD/WDC appear)")
    print("=" * 60)
    fake_signals = {
        "universe":      ["AMD", "WDC", "NVDA", "TSLA", "MSFT"],
        "triangle":      ["WDC", "FCX"],
        "flow":          ["AMD", "SPY", "AAPL"],
        "institutional": ["AMD", "GOOGL"],
        "momentum":      ["NVDA", "CSCO"],
    }
    xref = cross_reference(parsed_clean, fake_signals)
    print("signals_by_source:")
    for src, lst in fake_signals.items():
        print(f"    {src:14}: {lst}")
    print("\nper-ticker:")
    for row in xref["tickers"]:
        srcs = ", ".join(row["matched_sources"]) if row["matched_sources"] else "—"
        print(f"    {row['ticker']:6} {row['status']:10} [{srcs}]")
    print("\nsummary:")
    print(f"    confirmed    : {xref['summary']['confirmed']}")
    print(f"    off_radar    : {xref['summary']['off_radar']}")
    print(f"    overlap_count: {xref['summary']['overlap_count']}")

    print()
    print("=" * 60)
    print("TEST 4 — fetch_latest_watchlist_email() stub")
    print("=" * 60)
    print(f"returns: {fetch_latest_watchlist_email()!r} (stub, as expected)")
