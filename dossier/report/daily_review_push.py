"""
daily_review_push.py — the private "kick-ass daily review" push.

This is the delivery layer Mike actually sees. Unlike the PUBLIC dossier teaser
(`discord_notify.post_dossier_to_discord`, which posts market analysis to a
public channel), this push is PRIVATE: it includes "Your Book" (Mike's live IBKR
holdings + actionable calls) and the nightly analyst-watchlist overlap, neither
of which may ever be published.

Two delivery paths (both fail-open):
  1. Always: write the payload to a PRIVATE local file under `dossier/private/`
     (NOT under docs/ — never git-committed by the pipeline's push step). The
     durable Claude scheduled task reads this file and delivers it via the
     harness `PushNotification` tool (→ Mike's phone via Remote Control).
  2. Optional: if `WEBHOOK_DAILY_REVIEW` is set in the env, POST the push
     immediately to that private Discord webhook (curl — Cloudflare blocks
     urllib), so delivery doesn't depend on a Claude turn firing.

The audit's "phone push (5 lines)" shape:
  regime+VIX · top confluence pick (N legs) · Your Book alert · biggest
  migration · "skip-the-rest" line.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PRIVATE_DIR = PROJECT_ROOT / "dossier" / "private"
PUSH_FILE = PRIVATE_DIR / "daily_review_push.json"


def _fmt_money(v) -> str:
    if not isinstance(v, (int, float)):
        return "—"
    if abs(v) >= 1000:
        return f"${v/1000:.1f}k"
    return f"${v:.0f}"


def _confluence_line(summary: dict) -> str:
    conf = (summary or {}).get("confluence") or {}
    top = conf.get("top")
    if not top:
        return "🎯 No multi-leg convergence today."
    legs = ", ".join(sorted({l.get("source", "") for l in top.get("legs", [])
                             if l.get("direction") != "bearish"}))
    flag = " ⚠️conflict" if top.get("conflict") else ""
    return f"🎯 {top['ticker']} — {top['n_legs']} legs ({legs}){flag}"


def _migration_line(summary: dict) -> str:
    mig = (summary or {}).get("migration") or {}
    motd = mig.get("migration_of_the_day")
    if not motd:
        return "🔼 No notable migrations."
    return f"🔼 {motd['ticker']}: {motd.get('note', 'matured')}"


def _book_line(your_book: dict) -> str:
    yb = your_book or {}
    if not yb.get("ok"):
        return "💼 Your Book: bridge offline."
    actionable = [p for p in (yb.get("positions") or [])
                  if p.get("action") in ("ADD", "TRIM") or p.get("overlap")]
    if not actionable:
        pnl = yb.get("daily_pnl")
        return f"💼 Your Book: no signal overlap (day P&L {_fmt_money(pnl)})."
    p = actionable[0]
    return f"💼 {p.get('ticker')}: {p.get('action')} — {p.get('note', '')}"


def _analyst_line(analyst_overlay: dict) -> str:
    summ = (analyst_overlay or {}).get("summary") or {}
    conf = summ.get("confirmed") or []
    off = summ.get("off_radar") or []
    if not conf and not off:
        return ""
    return f"📋 Analyst overlap: {len(conf)} confirmed ({', '.join(conf[:4])}); {len(off)} off-radar."


def _weather_line(summary: dict) -> str:
    mw = (summary or {}).get("market_weather") or {}
    market = (summary or {}).get("market") or {}
    if mw and mw.get("headline"):
        return f"🌤️ {mw['headline']}"
    return f"🌤️ {market.get('regime', 'UNKNOWN')} · VIX {market.get('vix', '?')}"


def build_push_payload(summary: dict, your_book: dict | None = None,
                       analyst_overlay: dict | None = None) -> dict:
    """Build the private daily-review push payload (5-line phone push + full text)."""
    summary = summary or {}
    date = (summary.get("meta") or {}).get("date", "")

    lines = [
        _weather_line(summary),
        _confluence_line(summary),
        _book_line(your_book or {}),
        _migration_line(summary),
    ]
    analyst = _analyst_line(analyst_overlay or {})
    if analyst:
        lines.append(analyst)

    # "skip-the-rest" line: if nothing actionable converged, say so explicitly.
    conf = (summary.get("confluence") or {})
    if not conf.get("top") and not (summary.get("migration") or {}).get("migration_of_the_day"):
        lines.append("😴 Quiet day — nothing screaming. Skip the rest.")

    title = f"📊 Daily Review // {date}"
    body = "\n".join(lines)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": date,
        "title": title,
        "phone_lines": lines,
        "body": body,
        "report_url": (summary.get("meta") or {}).get("report_url", ""),
    }


def _post_webhook(payload: dict, webhook: str) -> bool:
    """POST the push to a private Discord webhook via curl. Returns success."""
    content = f"**{payload['title']}**\n{payload['body']}"
    if payload.get("report_url"):
        content += f"\n{payload['report_url']}"
    try:
        result = subprocess.run(
            ["curl", "-sS", "-X", "POST", "-H", "Content-Type: application/json",
             "-d", json.dumps({"content": content[:1900]}), webhook],
            capture_output=True, text=True, timeout=20,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  [WARN] Daily-review webhook post failed: {e}")
        return False


def emit_push(summary: dict, your_book: dict | None = None,
              analyst_overlay: dict | None = None) -> dict:
    """Build + persist the private push payload; optionally post to a webhook.

    ALWAYS writes the payload to the private local file (for the Claude task to
    deliver via PushNotification). If WEBHOOK_DAILY_REVIEW is set, also posts now.
    Never raises — returns the payload (with delivery flags) for logging.
    """
    payload = build_push_payload(summary, your_book, analyst_overlay)

    # (1) private local file — the Claude scheduled task reads this.
    try:
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(PUSH_FILE, "w") as f:
            json.dump(payload, f, indent=2)
        payload["_file"] = str(PUSH_FILE)
    except Exception as e:
        print(f"  [WARN] Could not write private push file: {e}")

    # (2) optional immediate webhook delivery.
    webhook = os.environ.get("WEBHOOK_DAILY_REVIEW", "").strip()
    if webhook:
        payload["_webhook_sent"] = _post_webhook(payload, webhook)
    else:
        payload["_webhook_sent"] = False

    return payload
