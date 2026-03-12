#!/usr/bin/env python3
"""
Ghost Signal Intelligence Engine — The Crossover
═══════════════════════════════════════════════════

Connects Ghost Alpha's AI momentum picks with TraderDaddy Pro's
institutional options flow data. When a Ghost Alpha A/B pick
aligns with unusual options activity → "SIGNAL LOCK" 🔒

This is the bridge between two previously separate products:
  1. Ghost Alpha Dossier (AI screener, EMA stack, momentum scoring)
  2. TraderDaddy Pro Agent API (unusual activity, market pulse)

Output:  docs/api/intelligence-crossover.json
         docs/api/backtest-analytics.json (enriched backtest data for dashboard)

Usage:
    python scripts/intelligence_crossover.py               # Full run
    python scripts/intelligence_crossover.py --analytics    # Just rebuild analytics JSON
    python scripts/intelligence_crossover.py --crossover    # Just run crossover

© 2026 mphinance — Sam the Quant Ghost
"""

import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Paths ───────────────────────────────────────────────────
SCAN_ARCHIVE = PROJECT_ROOT / "docs" / "backtesting" / "scan_archive.jsonl"
SCREENS_BACKTEST = PROJECT_ROOT / "docs" / "backtesting" / "screens_backtest.json"
PICKS_PATH = PROJECT_ROOT / "docs" / "api" / "daily-picks.json"
DOSSIER_DIR = PROJECT_ROOT / "docs" / "api"
OUTPUT_CROSSOVER = PROJECT_ROOT / "docs" / "api" / "intelligence-crossover.json"
OUTPUT_ANALYTICS = PROJECT_ROOT / "docs" / "api" / "backtest-analytics.json"

# TraderDaddy Agent API
TRADERDADDY_BASE = "https://www.traderdaddy.pro/api/agent"


# ═══════════════════════════════════════════════════════════════
# ████  BACKTEST ANALYTICS ENGINE  ████
# ═══════════════════════════════════════════════════════════════

def _load_scan_archive() -> list[dict]:
    """Load the full scan archive."""
    if not SCAN_ARCHIVE.exists():
        return []
    entries = []
    for line in SCAN_ARCHIVE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _compute_equity_curve(entries: list[dict], return_key: str = "fwd_5d") -> list[dict]:
    """Build equity curve from sequential picks."""
    validated = sorted(
        [e for e in entries if e.get(return_key) is not None],
        key=lambda e: e.get("date", "")
    )
    cumulative = 0.0
    peak = 0.0
    curve = []
    for e in validated:
        ret = e[return_key]
        cumulative += ret
        peak = max(peak, cumulative)
        drawdown = cumulative - peak
        curve.append({
            "date": e["date"],
            "ticker": e["ticker"],
            "return": ret,
            "cumulative": round(cumulative, 2),
            "drawdown": round(drawdown, 2),
            "grade": e.get("grade", ""),
        })
    return curve


def _compute_grade_performance(entries: list[dict]) -> dict:
    """Performance breakdown by grade letter."""
    grades = defaultdict(list)
    for e in entries:
        if e.get("fwd_5d") is not None:
            grade = e.get("grade", "?")
            grades[grade].append(e)

    result = {}
    for grade in sorted(grades.keys()):
        subset = grades[grade]
        fwd_5d = [e["fwd_5d"] for e in subset]
        fwd_1d = [e["fwd_1d"] for e in subset if e.get("fwd_1d") is not None]
        fwd_10d = [e["fwd_10d"] for e in subset if e.get("fwd_10d") is not None]

        avg_5d = sum(fwd_5d) / len(fwd_5d) if fwd_5d else 0
        wins = sum(1 for r in fwd_5d if r > 0)
        win_rate = (wins / len(fwd_5d)) * 100 if fwd_5d else 0

        # Sharpe
        if len(fwd_5d) > 1:
            mean = avg_5d
            var = sum((r - mean) ** 2 for r in fwd_5d) / (len(fwd_5d) - 1)
            std = math.sqrt(var) if var > 0 else 1
            sharpe = round((mean / std) * math.sqrt(252 / 5), 2)
        else:
            sharpe = 0

        result[grade] = {
            "count": len(subset),
            "avg_1d": round(sum(fwd_1d) / len(fwd_1d), 2) if fwd_1d else 0,
            "avg_5d": round(avg_5d, 2),
            "avg_10d": round(sum(fwd_10d) / len(fwd_10d), 2) if fwd_10d else 0,
            "win_rate_5d": round(win_rate, 1),
            "sharpe_5d": sharpe,
            "best": round(max(fwd_5d), 2) if fwd_5d else 0,
            "worst": round(min(fwd_5d), 2) if fwd_5d else 0,
        }
    return result


def _compute_weekly_heatmap(entries: list[dict]) -> list[dict]:
    """Weekly performance heatmap data."""
    weeks = defaultdict(list)
    for e in entries:
        if e.get("fwd_5d") is not None and e.get("date"):
            try:
                dt = datetime.strptime(e["date"], "%Y-%m-%d")
                week_start = dt - timedelta(days=dt.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weeks[week_key].append(e["fwd_5d"])
            except ValueError:
                continue

    heatmap = []
    for week in sorted(weeks.keys()):
        returns = weeks[week]
        avg = sum(returns) / len(returns)
        wins = sum(1 for r in returns if r > 0)
        heatmap.append({
            "week": week,
            "avg_return": round(avg, 2),
            "total_return": round(sum(returns), 2),
            "picks": len(returns),
            "wins": wins,
            "win_rate": round((wins / len(returns)) * 100, 1),
        })
    return heatmap


def _compute_sector_performance(entries: list[dict]) -> dict:
    """Performance by sector."""
    sectors = defaultdict(list)
    for e in entries:
        if e.get("fwd_5d") is not None:
            sector = e.get("sector", "Unknown") or "Unknown"
            sectors[sector].append(e["fwd_5d"])

    result = {}
    for sector in sorted(sectors.keys()):
        returns = sectors[sector]
        avg = sum(returns) / len(returns)
        wins = sum(1 for r in returns if r > 0)
        result[sector] = {
            "count": len(returns),
            "avg_return": round(avg, 2),
            "win_rate": round((wins / len(returns)) * 100, 1),
            "total_return": round(sum(returns), 2),
        }
    return result


def _compute_regime_performance(entries: list[dict]) -> dict:
    """Performance by market regime."""
    regimes = defaultdict(list)
    for e in entries:
        if e.get("fwd_5d") is not None:
            regime = e.get("regime", "Unknown") or "Unknown"
            regimes[regime].append(e)

    result = {}
    for regime in sorted(regimes.keys()):
        subset = regimes[regime]
        returns = [e["fwd_5d"] for e in subset]
        avg = sum(returns) / len(returns)
        wins = sum(1 for r in returns if r > 0)
        result[regime] = {
            "count": len(subset),
            "avg_return": round(avg, 2),
            "win_rate": round((wins / len(returns)) * 100, 1),
            "avg_vix": round(sum(e.get("vix", 0) for e in subset) / len(subset), 1),
        }
    return result


def _compute_ema_stack_performance(entries: list[dict]) -> dict:
    """Performance by EMA stack alignment."""
    stacks = defaultdict(list)
    for e in entries:
        if e.get("fwd_5d") is not None:
            stack = e.get("ema_stack", "Unknown") or "Unknown"
            stacks[stack].append(e["fwd_5d"])

    result = {}
    for stack in sorted(stacks.keys()):
        returns = stacks[stack]
        avg = sum(returns) / len(returns)
        wins = sum(1 for r in returns if r > 0)
        result[stack] = {
            "count": len(returns),
            "avg_return": round(avg, 2),
            "win_rate": round((wins / len(returns)) * 100, 1),
        }
    return result


def _compute_best_worst(entries: list[dict], top_n: int = 10) -> dict:
    """Top best and worst picks."""
    validated = [e for e in entries if e.get("fwd_5d") is not None]
    best = sorted(validated, key=lambda e: e.get("fwd_5d", 0), reverse=True)[:top_n]
    worst = sorted(validated, key=lambda e: e.get("fwd_5d", 0))[:top_n]

    def _pick_summary(e):
        return {
            "ticker": e["ticker"],
            "date": e["date"],
            "score": e.get("score", 0),
            "grade": e.get("grade", ""),
            "fwd_1d": e.get("fwd_1d"),
            "fwd_5d": e.get("fwd_5d"),
            "fwd_10d": e.get("fwd_10d"),
            "sector": e.get("sector", ""),
            "ema_stack": e.get("ema_stack", ""),
            "regime": e.get("regime", ""),
        }

    return {
        "best": [_pick_summary(e) for e in best],
        "worst": [_pick_summary(e) for e in worst],
    }


def _compute_score_distribution(entries: list[dict]) -> list[dict]:
    """Distribution of scores for the histogram."""
    validated = [e for e in entries if e.get("fwd_5d") is not None]
    buckets = defaultdict(lambda: {"count": 0, "returns": []})
    for e in validated:
        score = e.get("score", 0)
        bucket = (score // 10) * 10  # 0-9, 10-19, ..., 90-100
        buckets[bucket]["count"] += 1
        buckets[bucket]["returns"].append(e["fwd_5d"])

    result = []
    for bucket in sorted(buckets.keys()):
        data = buckets[bucket]
        returns = data["returns"]
        avg = sum(returns) / len(returns) if returns else 0
        wins = sum(1 for r in returns if r > 0)
        result.append({
            "bucket": f"{bucket}-{bucket + 9}",
            "count": data["count"],
            "avg_return": round(avg, 2),
            "win_rate": round((wins / len(returns)) * 100, 1) if returns else 0,
        })
    return result


def _compute_streak_analysis(entries: list[dict]) -> dict:
    """Win/loss streak analysis."""
    validated = sorted(
        [e for e in entries if e.get("fwd_5d") is not None],
        key=lambda e: e.get("date", "")
    )

    if not validated:
        return {"max_win_streak": 0, "max_loss_streak": 0, "current_streak": 0}

    max_win = 0
    max_loss = 0
    current = 0
    current_type = None

    for e in validated:
        is_win = e["fwd_5d"] > 0
        if current_type is None:
            current = 1
            current_type = is_win
        elif is_win == current_type:
            current += 1
        else:
            if current_type:
                max_win = max(max_win, current)
            else:
                max_loss = max(max_loss, current)
            current = 1
            current_type = is_win

    # Final streak
    if current_type is not None:
        if current_type:
            max_win = max(max_win, current)
        else:
            max_loss = max(max_loss, current)

    return {
        "max_win_streak": max_win,
        "max_loss_streak": max_loss,
        "current_streak": current if current_type else -current,
        "current_streak_type": "win" if current_type else "loss",
    }


def build_analytics() -> dict:
    """Build the complete analytics JSON for the dashboard."""
    print("🧠 Building Ghost Alpha Analytics...")
    entries = _load_scan_archive()
    validated = [e for e in entries if e.get("fwd_5d") is not None]

    print(f"  📊 Total entries: {len(entries)}")
    print(f"  ✅ Validated (with returns): {len(validated)}")

    # Load screens backtest for strategy data
    strategy_data = {}
    if SCREENS_BACKTEST.exists():
        try:
            strategy_data = json.loads(SCREENS_BACKTEST.read_text())
        except Exception:
            pass

    analytics = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_entries": len(entries),
            "validated_entries": len(validated),
            "date_range": {
                "first": min((e.get("date", "") for e in entries), default=""),
                "last": max((e.get("date", "") for e in entries), default=""),
            },
            "unique_tickers": len(set(e["ticker"] for e in entries)),
        },
        "equity_curve": _compute_equity_curve(entries),
        "by_grade": _compute_grade_performance(entries),
        "weekly_heatmap": _compute_weekly_heatmap(entries),
        "by_sector": _compute_sector_performance(entries),
        "by_regime": _compute_regime_performance(entries),
        "by_ema_stack": _compute_ema_stack_performance(entries),
        "best_worst": _compute_best_worst(entries),
        "score_distribution": _compute_score_distribution(entries),
        "streak_analysis": _compute_streak_analysis(entries),
        # Include raw strategy data from screens backtest
        "by_strategy": strategy_data.get("by_screen", {}),
        "by_score_band": strategy_data.get("score_bands", {}),
        "pullback_analysis": strategy_data.get("pullback_analysis", {}),
        "gold_picks": strategy_data.get("gold_picks_simulation", {}),
    }

    # Write output
    OUTPUT_ANALYTICS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_ANALYTICS, "w") as f:
        json.dump(analytics, f, indent=2)

    print(f"  ✓ Analytics: {OUTPUT_ANALYTICS}")
    return analytics


# ═══════════════════════════════════════════════════════════════
# ████  TRADERDADDY CROSSOVER ENGINE  ████
# ═══════════════════════════════════════════════════════════════

def _fetch_unusual_activity(token: str = None) -> list[dict]:
    """Fetch unusual options activity from TraderDaddy Agent API."""
    import urllib.request
    import urllib.error

    url = f"{TRADERDADDY_BASE}/unusual-activity?timeFrame=today&minPremium=25000&minScore=70"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return data if isinstance(data, list) else data.get("data", [])
    except urllib.error.HTTPError as e:
        print(f"  ⚠️ Agent API returned {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"  ⚠️ Agent API error: {e}")
        return []


def _fetch_market_pulse(token: str = None) -> dict:
    """Fetch market pulse from TraderDaddy Agent API."""
    import urllib.request
    import urllib.error

    url = f"{TRADERDADDY_BASE}/market-pulse"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️ Market Pulse error: {e}")
        return {}


def _load_daily_picks() -> list[dict]:
    """Load today's Ghost Alpha daily picks."""
    if not PICKS_PATH.exists():
        return []
    try:
        data = json.loads(PICKS_PATH.read_text())
        return data.get("picks", [])
    except Exception:
        return []


def _crossover_analysis(picks: list[dict], flow: list[dict], pulse: dict) -> dict:
    """
    The magic: cross-reference Ghost Alpha picks with unusual options flow.

    SIGNAL LOCK 🔒 = Ghost Alpha A/B pick + unusual call/put activity
    This means both the AI screener AND institutional options flow agree.
    """
    pick_tickers = {p.get("ticker", "").upper() for p in picks}
    flow_tickers = defaultdict(list)
    for activity in flow:
        ticker = activity.get("ticker", "").upper()
        flow_tickers[ticker].append(activity)

    # Find overlaps
    signal_locks = []
    for pick in picks:
        ticker = pick.get("ticker", "").upper()
        grade = pick.get("grade", "")

        if ticker in flow_tickers:
            activities = flow_tickers[ticker]

            # Determine flow sentiment
            calls = [a for a in activities if a.get("type", "").lower() == "call"]
            puts = [a for a in activities if a.get("type", "").lower() == "put"]
            total_call_premium = sum(a.get("premium", 0) for a in calls)
            total_put_premium = sum(a.get("premium", 0) for a in puts)

            flow_sentiment = "BULLISH" if total_call_premium > total_put_premium else "BEARISH"
            ghost_sentiment = "BULLISH"  # Ghost Alpha picks are inherently bullish

            # Alignment check
            aligned = flow_sentiment == ghost_sentiment

            signal_locks.append({
                "ticker": ticker,
                "ghost_grade": grade,
                "ghost_score": pick.get("score", 0),
                "flow_sentiment": flow_sentiment,
                "aligned": aligned,
                "signal_type": "SIGNAL LOCK 🔒" if aligned and grade in ("A", "A+", "B") else "CROSSOVER ⚡",
                "call_flow": len(calls),
                "put_flow": len(puts),
                "total_call_premium": total_call_premium,
                "total_put_premium": total_put_premium,
                "net_premium": total_call_premium - total_put_premium,
                "activities": [
                    {
                        "type": a.get("type"),
                        "strike": a.get("strike"),
                        "expiry": a.get("expiry"),
                        "premium": a.get("premium"),
                        "volume": a.get("volume"),
                        "score": a.get("unusualScore"),
                    }
                    for a in activities[:5]  # Limit to top 5
                ],
            })

    # Summary
    total_picks = len(picks)
    overlaps = len(signal_locks)
    locks = sum(1 for s in signal_locks if "LOCK" in s["signal_type"])

    return {
        "timestamp": datetime.now().isoformat(),
        "market_pulse": pulse,
        "summary": {
            "total_picks": total_picks,
            "flow_overlaps": overlaps,
            "signal_locks": locks,
            "overlap_rate": round((overlaps / total_picks) * 100, 1) if total_picks else 0,
        },
        "signals": sorted(signal_locks, key=lambda s: s.get("ghost_score", 0), reverse=True),
        "ghost_picks": [
            {
                "ticker": p.get("ticker"),
                "grade": p.get("grade"),
                "score": p.get("score"),
                "price": p.get("price"),
                "has_flow": p.get("ticker", "").upper() in flow_tickers,
            }
            for p in picks
        ],
    }


def run_crossover(token: str = None) -> dict:
    """Run the full intelligence crossover."""
    print("🔒 Ghost Signal Intelligence — Running crossover...")

    # 1. Load Ghost Alpha picks
    picks = _load_daily_picks()
    print(f"  👻 Ghost Alpha picks: {len(picks)}")

    # 2. Fetch TraderDaddy unusual activity
    flow = _fetch_unusual_activity(token)
    print(f"  📡 Unusual activity entries: {len(flow)}")

    # 3. Fetch market pulse
    pulse = _fetch_market_pulse(token)
    print(f"  💓 Market pulse: {'loaded' if pulse else 'empty'}")

    # 4. Run crossover analysis
    result = _crossover_analysis(picks, flow, pulse)
    locks = result["summary"]["signal_locks"]
    overlaps = result["summary"]["flow_overlaps"]
    print(f"  🔒 Signal Locks: {locks}")
    print(f"  ⚡ Crossovers: {overlaps}")

    # 5. Write output
    with open(OUTPUT_CROSSOVER, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Crossover: {OUTPUT_CROSSOVER}")

    return result


# ═══════════════════════════════════════════════════════════════
# ████  MAIN  ████
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ghost Signal Intelligence Engine")
    parser.add_argument("--analytics", action="store_true", help="Build analytics JSON only")
    parser.add_argument("--crossover", action="store_true", help="Run crossover only")
    parser.add_argument("--token", type=str, default=None, help="JWT token for Agent API")
    args = parser.parse_args()

    if args.analytics:
        build_analytics()
    elif args.crossover:
        run_crossover(token=args.token)
    else:
        # Full run: analytics + crossover
        build_analytics()
        run_crossover(token=args.token)


if __name__ == "__main__":
    main()
