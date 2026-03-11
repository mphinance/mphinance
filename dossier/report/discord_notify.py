"""
Discord Dossier Notification — Auto-posts daily summary to #sam-mph.

Sends a clean, formatted Discord embed with the day's gold pick, regime,
signal count, and CTA to the full report. This runs as a pipeline stage
after the Summary API is generated.

Uses the WEBHOOK_SAM_MPH webhook from VaultGuard.

Usage (called by generate.py):
    from dossier.report.discord_notify import post_dossier_to_discord
    post_dossier_to_discord(summary_dict)
"""

import json
import subprocess
import os
from pathlib import Path


def _get_webhook() -> str:
    """Get Discord webhook from env or VaultGuard."""
    val = os.environ.get("WEBHOOK_SAM_MPH")
    if val:
        return val
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            sa = Path(__file__).resolve().parent.parent.parent / "service_account.json"
            cred = credentials.Certificate(str(sa))
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        doc = db.collection('secrets').document('WEBHOOK_SAM_MPH').get()
        if doc.exists:
            return doc.to_dict()['value']
    except Exception:
        pass
    return ""


def post_dossier_to_discord(summary: dict, dry_run: bool = False) -> bool:
    """
    Post the daily dossier summary to Discord #sam-mph.
    
    Args:
        summary: The dossier-summary.json dict
        dry_run: If True, print the message but don't send
    
    Returns: True if posted successfully
    """
    webhook = _get_webhook()
    if not webhook and not dry_run:
        print("  [WARN] No WEBHOOK_SAM_MPH available — skipping Discord")
        return False

    date = summary.get("meta", {}).get("date", "unknown")
    market = summary.get("market", {})
    picks = summary.get("picks", {})
    signals = summary.get("signals", {})
    sam = summary.get("sam", {})
    report_url_base = summary.get("meta", {}).get("report_url", "")
    report_url = f"{report_url_base}?utm_source=discord&utm_medium=notification&utm_campaign=dossier-{date}" if report_url_base else ""

    # Build the message
    regime_emoji = market.get("regime_emoji", "🟡")
    regime = market.get("regime", "Unknown")
    vix = market.get("vix", 0)
    spy = market.get("spy", {})
    spy_chg = spy.get("change_pct", 0)
    spy_dir = "▲" if spy_chg >= 0 else "▼"

    # Gold pick
    gold = picks.get("gold")
    gold_line = ""
    if gold:
        ticker = gold.get("ticker", "?")
        score = gold.get("score", 0)
        grade = gold.get("grade", "")
        upside = gold.get("upside_pct", 0)
        gold_line = f"\n🥇 **Gold Pick: {ticker}** — Score: {score}/100 ({grade}) · {upside:.1f}% upside"

    signal_count = signals.get("count", 0)
    quote = sam.get("quote", "")

    msg = (
        f"# 📊 Ghost Alpha Dossier — {date}\n"
        f"{regime_emoji} **{regime}** · SPY {spy_dir} {abs(spy_chg):.1f}% · VIX {vix:.1f}\n"
        f"{gold_line}\n\n"
        f"📡 **{signal_count} signals** across 6 strategies\n\n"
        f"> *\"{quote}\"* — Sam\n\n"
        f"**[📋 Full Report →]({report_url})**"
    )

    if dry_run:
        print(f"  [DRY RUN] Discord message ({len(msg)} chars):")
        print(msg)
        return True

    # Post via curl (Cloudflare blocks urllib)
    payload = json.dumps({
        "content": msg,
        "username": "Ghost Alpha 📊",
    })

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', webhook,
             '-H', 'Content-Type: application/json',
             '-d', payload,
             '-w', '\n%{http_code}'],
            capture_output=True, text=True, timeout=15
        )

        status_code = result.stdout.strip().split('\n')[-1]
        if status_code in ('200', '204'):
            print(f"  ✓ Discord notification posted ({len(msg)} chars)")
            return True
        else:
            print(f"  [WARN] Discord error: HTTP {status_code}")
            return False
    except Exception as e:
        print(f"  [WARN] Discord notification failed: {e}")
        return False


def post_morning_setups(screener_results: dict, date: str = "", dry_run: bool = False) -> bool:
    """
    Post Ghost Alpha morning picks to Discord #sam-mph.

    Called after the screener runs in the pipeline. Posts each pick
    with GA grade, score, RVOL, and trend phase in Sam's voice.
    """
    webhook = _get_webhook()
    if not webhook and not dry_run:
        print("  [WARN] No WEBHOOK_SAM_MPH — skipping morning setups Discord")
        return False

    results = screener_results.get("results", [])
    a_plus = screener_results.get("a_plus", [])
    funnel = screener_results.get("funnel_stats", {})

    if not results:
        print("  [SKIP] No screener results to post")
        return False

    # Determine tier
    if a_plus:
        picks = a_plus[:8]
        tier = "A+"
        tier_emoji = "🏆"
    else:
        a_grade = [r for r in results if r.get("daily", {}).get("grade") == "A"
                   or r.get("daily", {}).get("score", 0) >= 4.5]
        if a_grade:
            picks = a_grade[:8]
            tier = "A (no A+ today)"
            tier_emoji = "🎯"
        else:
            b_grade = [r for r in results if r.get("daily", {}).get("score", 0) >= 3.5]
            picks = b_grade[:8]
            tier = "B (slim pickings)"
            tier_emoji = "📋"

    if not picks:
        return False

    from datetime import datetime as _dt
    if not date:
        date = _dt.now().strftime("%Y-%m-%d")

    # Build the picks list
    pick_lines = []
    for r in picks:
        d = r.get("daily", {})
        ticker = r.get("ticker", "?")
        grade = d.get("grade", "?")
        score = d.get("score", 0)
        rvol = d.get("rvol", 0)
        phase = d.get("trend_phase", "")
        sqz = d.get("sqz_days", 0)

        # Color emoji for grade
        if grade in ("A+", "A"):
            g_emoji = "🟢"
        elif grade == "B":
            g_emoji = "🔵"
        elif grade == "C":
            g_emoji = "🟡"
        else:
            g_emoji = "⚪"

        extras = []
        if rvol >= 1.2:
            extras.append(f"🔥 RVOL {rvol:.1f}x")
        elif rvol >= 0.8:
            extras.append(f"RVOL {rvol:.1f}x")
        if phase:
            extras.append(phase)
        if sqz >= 3:
            extras.append(f"⚡ {sqz}d squeeze")

        extra_str = " · ".join(extras) if extras else ""
        pick_lines.append(
            f"{g_emoji} **{ticker}** — {grade} ({score}/7.0)"
            + (f" — {extra_str}" if extra_str else "")
        )

    screened = funnel.get("stage1_start", 0)
    elapsed = funnel.get("elapsed_sec", 0)

    msg = (
        f"# ⚔️ Ghost Alpha Morning Setups — {date}\n"
        f"{tier_emoji} **Tier: {tier}** · {len(picks)} picks from {screened} screened ({elapsed}s)\n\n"
        + "\n".join(pick_lines)
        + f"\n\n> *Sam ran {screened} tickers through the 17-parameter funnel. "
        + f"These {len(picks)} survived. No guarantees, no refunds.* 👻\n\n"
        f"**[📋 Full Dossier →](https://mphinance.github.io/mphinance/)**"
    )

    if dry_run:
        print(f"  [DRY RUN] Discord morning setups ({len(msg)} chars):")
        print(msg)
        return True

    payload = json.dumps({
        "content": msg,
        "username": "Sam the Quant Ghost 👻",
    })

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', webhook,
             '-H', 'Content-Type: application/json',
             '-d', payload,
             '-w', '\n%{http_code}'],
            capture_output=True, text=True, timeout=15
        )

        status_code = result.stdout.strip().split('\n')[-1]
        if status_code in ('200', '204'):
            print(f"  ✓ Morning setups posted to Discord ({len(picks)} picks, {len(msg)} chars)")
            return True
        else:
            print(f"  [WARN] Discord morning setups error: HTTP {status_code}")
            return False
    except Exception as e:
        print(f"  [WARN] Discord morning setups failed: {e}")
        return False
