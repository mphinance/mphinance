#!/usr/bin/env python3
"""
Factor Correlation — which individual technical/fundamental factors actually
predict forward returns?

screen_health.py already groups validated picks by strategy/grade/regime/EMA
stack and reports win rate per bucket. That answers "does this screen work."
It doesn't answer the sharper question TODO.md Priority 4 asks: of the raw
numeric inputs that feed momentum_picks.py's score (RSI, ADX, MACD histogram,
relative volume, IV rank, tech/fund sub-scores, the composite score itself),
which ones actually line up with what price does next — and which are dead
weight the model could drop?

This reads the same scan archive (docs/backtesting/scan_archive.jsonl,
populated by scan_logger.py) that screen_health.py reads, and for each
numeric factor computes the Pearson correlation coefficient against forward
return at two horizons (5d, 10d), ranked by |r|. A factor needs at least
MIN_PAIRS non-null (factor, return) pairs before it gets a correlation at
all — with too few points a correlation coefficient is noise dressed up as
signal, so it's reported as insufficient data instead of a misleading number.

Usage:
    python dossier/backtesting/factor_correlation.py          # Print report
    python dossier/backtesting/factor_correlation.py --json    # Write + print

Called by generate.py during the pipeline run (Stage 15h), same pattern as
screen_health.py's Stage 15g.
"""

import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCAN_ARCHIVE = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"
CORRELATION_API = PROJECT_ROOT / "docs" / "api" / "factor-correlation.json"

# Numeric fields scan_logger.py records per pick that plausibly drive the
# score. Categorical fields (ema_stack, regime, sector, trend) are already
# covered by screen_health.py's group breakdowns and don't correlate the
# same way, so they're intentionally left out here.
NUMERIC_FACTORS = [
    "score", "tech_score", "fund_score", "rsi_14", "adx_14", "macd_hist",
    "rel_vol", "iv_rank", "stoch_k", "atr_14", "squeeze_ratio", "cmf", "mfi",
]

HORIZONS = ["fwd_5d", "fwd_10d"]

# Below this many paired observations, a Pearson r is too noisy to trust.
MIN_PAIRS = 15


def _load_entries(path=None) -> list[dict]:
    """Load the scan archive. Missing file → []."""
    p = Path(path) if path is not None else SCAN_ARCHIVE
    if not p.exists():
        return []
    entries = []
    for line in p.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _pearson(pairs: list[tuple[float, float]]) -> float | None:
    """Pearson correlation coefficient for (x, y) pairs, or None if undefined."""
    n = len(pairs)
    if n < 2:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / math.sqrt(var_x * var_y)


def compute_factor_correlations(entries: list[dict], horizon: str, min_pairs: int = MIN_PAIRS) -> dict:
    """
    For each factor in NUMERIC_FACTORS, correlate it against `horizon`
    forward return across entries where both are present and numeric.
    Never raises — malformed/missing values are skipped per-pair.
    """
    ranked, insufficient = [], []
    for name in NUMERIC_FACTORS:
        pairs = []
        for e in entries:
            fv, hv = e.get(name), e.get(horizon)
            if fv is None or hv is None:
                continue
            try:
                pairs.append((float(fv), float(hv)))
            except (TypeError, ValueError):
                continue

        n = len(pairs)
        r = _pearson(pairs) if n >= min_pairs else None
        row = {"factor": name, "n": n, "correlation": round(r, 3) if r is not None else None}
        (ranked if r is not None else insufficient).append(row)

    ranked.sort(key=lambda f: abs(f["correlation"]), reverse=True)
    return {
        "horizon": horizon,
        "min_pairs_required": min_pairs,
        "factors_ranked": ranked,
        "factors_insufficient_data": insufficient,
    }


def compute_all_horizons(entries: list[dict], horizons: list[str] = HORIZONS, min_pairs: int = MIN_PAIRS) -> dict:
    """Aggregate compute_factor_correlations() across every horizon in `horizons`."""
    return {
        "generated_at": datetime.now().isoformat(),
        "total_entries": len(entries),
        "by_horizon": {h: compute_factor_correlations(entries, h, min_pairs) for h in horizons},
    }


def format_factor_correlation_text(report: dict, horizon: str = "fwd_5d") -> str:
    """One-line console summary of the top-ranked factors for `horizon`."""
    ranked = report.get("by_horizon", {}).get(horizon, {}).get("factors_ranked", [])
    if not ranked:
        return f"📉 Factor Correlation ({horizon}): insufficient data — need {MIN_PAIRS}+ validated picks per factor"
    top = ranked[:3]
    parts = ", ".join(f"{f['factor']} r={f['correlation']:+.2f} (n={f['n']})" for f in top)
    return f"📉 Factor Correlation ({horizon}): {parts}"


def write_factor_correlation_json() -> dict:
    """
    Compute correlations and write docs/api/factor-correlation.json.

    Always writes a file, even with zero/insufficient entries, so a future
    dashboard widget never 404s while the scan archive accumulates validated
    picks (same reasoning as screen_health.write_health_json()).
    """
    entries = _load_entries()
    report = compute_all_horizons(entries)
    CORRELATION_API.parent.mkdir(parents=True, exist_ok=True)
    with open(CORRELATION_API, "w") as f:
        json.dump(report, f, indent=2)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Factor Correlation")
    parser.add_argument("--json", action="store_true", help="Write docs/api/factor-correlation.json")
    args = parser.parse_args()

    if args.json:
        report = write_factor_correlation_json()
        print(f"✅ Factor correlation written to {CORRELATION_API}")
    else:
        report = compute_all_horizons(_load_entries())

    print(f"\n{'=' * 80}")
    print(f"  FACTOR CORRELATION — {report['total_entries']} scan archive entries")
    print(f"{'=' * 80}")
    for horizon in HORIZONS:
        print(f"\n  {format_factor_correlation_text(report, horizon)}")


if __name__ == "__main__":
    main()
