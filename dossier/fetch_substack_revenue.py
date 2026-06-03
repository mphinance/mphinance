#!/usr/bin/env python3
"""
Substack Revenue Transparency — fetch live subscriber + ARR figures.

Replaces the Stripe-key dependency (dossier/fetch_revenue.py) with Substack's
own publisher dashboard API, authenticated by the SUBSTACK_SID cookie. ARR is
Substack's computed annual recurring revenue (reflects what subscribers
actually pay, including grandfathered rates), so it's the source of truth for
revenue regardless of current list prices.

Endpoints (all GET, cookie-auth, need a publisher Referer header):
    /api/v1/publish-dashboard/summary-v2?range=180   subs + ARR (now & 180d ago)

Usage:
    SUBSTACK_SID="s%3A..." python3 dossier/fetch_substack_revenue.py

Output:
    landing/data/revenue_stats.json
"""

import os
import sys
import json
import datetime
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Output path is overridable so the server cron can write straight to the live
# docroot (public_html/data) without depending on a landing/ -> public_html deploy.
OUTPUT_FILE = Path(os.environ.get(
    "REVENUE_STATS_OUT", PROJECT_ROOT / "landing" / "data" / "revenue_stats.json"))

PUB = os.environ.get("SUBSTACK_PUB_URL", "https://mphinance.substack.com").rstrip("/")

# Current list prices (USD). Substack's plans endpoint can lag manual price
# changes, so these are kept here as the display source of truth. Update if
# you change pricing.
PLAN_MONTHLY = 21
PLAN_ANNUAL = 144


def _session() -> requests.Session:
    # Strip stray whitespace/CR — env files edited on Windows can append \r,
    # which makes an invalid HTTP cookie header.
    sid = os.environ.get("SUBSTACK_SID", "").strip()
    if not sid:
        print("[ERR] SUBSTACK_SID not set.")
        sys.exit(1)
    s = requests.Session()
    s.cookies.set("substack.sid", sid, domain=".substack.com")
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        # A publisher Referer is required or the dashboard endpoints 403/404.
        "Referer": f"{PUB}/publish/home",
        "X-Requested-With": "XMLHttpRequest",
    })
    return s


def fetch() -> dict:
    s = _session()
    url = f"{PUB}/api/v1/publish-dashboard/summary-v2?range=180"
    print(f"  Fetching {url} ...")
    r = s.get(url, timeout=20)
    r.raise_for_status()
    if "json" not in r.headers.get("content-type", ""):
        raise RuntimeError("summary-v2 did not return JSON — SID likely expired.")
    d = r.json()

    total = int(d["totalSubscribersEnd"])
    paid = int(d["paidSubscribersEnd"])
    arr = round(float(d["arrEnd"]), 2)
    total_start = int(d.get("totalSubscribersStart", 0))
    paid_start = int(d.get("paidSubscribersStart", 0))
    arr_start = round(float(d.get("arrStart", 0)), 2)
    mrr = round(arr / 12.0, 2)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return {
        "updated": now,
        "source": "Substack publisher API",
        # ── Substack-native headline ──
        "arr": arr,
        "mrr": mrr,
        "paid_subscribers": paid,
        "total_subscribers": total,
        "free_subscribers": max(total - paid, 0),
        "plans": {"monthly": PLAN_MONTHLY, "annual": PLAN_ANNUAL},
        "growth_180d": {
            "total_start": total_start,
            "total_end": total,
            "paid_start": paid_start,
            "paid_end": paid,
            "arr_start": arr_start,
            "arr_end": arr,
        },
        # ── Back-compat aliases for the legacy transparency widget ──
        "gross_revenue": arr,
        "subscription_count": paid,
        "subscriptions": {"active": paid, "mrr": mrr, "arr": arr},
    }


def main():
    print("═══ Substack Revenue Fetch ═══\n")
    stats = fetch()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"\n  Paid subscribers : {stats['paid_subscribers']}")
    print(f"  Total subscribers: {stats['total_subscribers']}")
    print(f"  ARR              : ${stats['arr']:,.2f}")
    print(f"  MRR              : ${stats['mrr']:,.2f}")
    print(f"  6-mo growth      : paid {stats['growth_180d']['paid_start']}→{stats['growth_180d']['paid_end']}, "
          f"ARR ${stats['growth_180d']['arr_start']:,.0f}→${stats['growth_180d']['arr_end']:,.0f}")
    print(f"\n✅ Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
