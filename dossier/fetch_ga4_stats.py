#!/usr/bin/env python3
"""
Fetch GA4 analytics stats and write to landing/data/ga4_stats.json.

Uses the GA4 Data API. Credentials are resolved in priority order so the
script works both locally (interactive browser) and headless (CI):

  1. Service account  — env GA4_SERVICE_ACCOUNT_JSON (raw JSON) or
     GA4_SERVICE_ACCOUNT_FILE (path to key file). Best for CI; grant the
     service account "Viewer" on each GA4 property.
  2. OAuth refresh token — env GA4_REFRESH_TOKEN + GA4_CLIENT_ID +
     GA4_CLIENT_SECRET. Reuses an existing user grant, no browser needed.
  3. Cached token file  — ga4_token.json next to the repo (local dev).
  4. Interactive flow   — opens a browser to authorize (local dev only;
     skipped when headless/non-TTY or GA4_NONINTERACTIVE is set).

Usage:
    python3 -m dossier.fetch_ga4_stats
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# GA4 Property IDs (numeric part of "properties/XXXXXX")
GA4_PROPERTIES = {
    "mphinance": {"property_id": "527334613", "measurement_id": "G-KTHVTFX699"},
    "traderdaddy": {"property_id": "527410613", "measurement_id": "G-FWSFCJKYEV"},
    "tickertrace": {"property_id": "526490745", "measurement_id": "G-SYRWGDY0Y3"},
    "substack": {"property_id": "358732142", "measurement_id": "G-LNLQLK7H8B"},
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "landing" / "data" / "ga4_stats.json"
CLIENT_FILE = PROJECT_ROOT.parent / "oauth_client.json"
TOKEN_FILE = PROJECT_ROOT.parent / "ga4_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
]


def _credential_source(env=None, token_file=None, client_file=None) -> str:
    """Decide which credential method will be used, in priority order.

    Pure/inspectable (no Google imports) so it can be unit-tested. Returns one
    of: 'service_account_json', 'service_account_file', 'refresh_token',
    'cached_token', 'interactive', 'none'.
    """
    env = os.environ if env is None else env
    token_file = TOKEN_FILE if token_file is None else token_file
    client_file = CLIENT_FILE if client_file is None else client_file

    if env.get("GA4_SERVICE_ACCOUNT_JSON"):
        return "service_account_json"
    if env.get("GA4_SERVICE_ACCOUNT_FILE"):
        return "service_account_file"
    if all(env.get(k) for k in ("GA4_REFRESH_TOKEN", "GA4_CLIENT_ID", "GA4_CLIENT_SECRET")):
        return "refresh_token"
    if Path(token_file).exists():
        return "cached_token"
    if Path(client_file).exists():
        return "interactive"
    return "none"


def _get_credentials():
    """Resolve GA4 credentials (see module docstring for priority order)."""
    from google.auth.transport.requests import Request

    source = _credential_source()

    # 1. Service account — ideal for CI / headless.
    if source in ("service_account_json", "service_account_file"):
        try:
            from google.oauth2 import service_account
            if source == "service_account_json":
                info = json.loads(os.environ["GA4_SERVICE_ACCOUNT_JSON"])
                creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
                print("  [+] Using service-account credentials (GA4_SERVICE_ACCOUNT_JSON)")
            else:
                path = os.environ["GA4_SERVICE_ACCOUNT_FILE"]
                creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
                print(f"  [+] Using service-account credentials ({path})")
            return creds
        except Exception as e:
            print(f"  [ERR] Service-account credentials failed: {e}")
            return None

    # 2. OAuth refresh token from env — headless, reuses an existing user grant.
    if source == "refresh_token":
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials(
                None,
                refresh_token=os.environ["GA4_REFRESH_TOKEN"],
                client_id=os.environ["GA4_CLIENT_ID"],
                client_secret=os.environ["GA4_CLIENT_SECRET"],
                token_uri="https://oauth2.googleapis.com/token",
                scopes=SCOPES,
            )
            creds.refresh(Request())
            print("  [+] Using OAuth refresh-token credentials (env)")
            return creds
        except Exception as e:
            print(f"  [ERR] Refresh-token credentials failed: {e}")
            return None

    # 3. Cached token file (local dev) — refresh if expired.
    if source == "cached_token":
        from google.oauth2.credentials import Credentials
        creds = None
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json())
            except Exception:
                creds = None
        if creds and creds.valid:
            return creds
        # cached token unusable → fall through to interactive (if allowed)

    # 4. Interactive browser flow — local dev only; never hang in CI.
    if not sys.stdin.isatty() or os.environ.get("GA4_NONINTERACTIVE"):
        print("  [ERR] No usable GA4 credentials and running headless.")
        print("        Set GA4_SERVICE_ACCOUNT_JSON / GA4_SERVICE_ACCOUNT_FILE, or")
        print("        GA4_REFRESH_TOKEN + GA4_CLIENT_ID + GA4_CLIENT_SECRET.")
        return None

    if not CLIENT_FILE.exists():
        print(f"  [ERR] OAuth client file not found: {CLIENT_FILE}")
        return None

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    creds = flow.run_local_server(port=8085, open_browser=True)
    TOKEN_FILE.write_text(creds.to_json())
    print("  [+] OAuth token cached")
    return creds


def _fetch_property_stats(client, property_id: str, property_label: str) -> dict:
    """Fetch 28-day stats for a single GA4 property."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Metric, Dimension, OrderBy
    )

    property_path = f"properties/{property_id}"

    # 28-day totals: pageviews, users, sessions
    try:
        totals_response = client.run_report(RunReportRequest(
            property=property_path,
            date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="sessions"),
            ],
        ))

        row = totals_response.rows[0] if totals_response.rows else None
        pageviews = int(row.metric_values[0].value) if row else 0
        users = int(row.metric_values[1].value) if row else 0
        sessions = int(row.metric_values[2].value) if row else 0
    except Exception as e:
        print(f"  [WARN] {property_label} totals failed: {e}")
        pageviews = users = sessions = 0

    # Top 5 pages
    top_pages = []
    try:
        pages_response = client.run_report(RunReportRequest(
            property=property_path,
            date_ranges=[DateRange(start_date="28daysAgo", end_date="today")],
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
            limit=5,
        ))

        for row in pages_response.rows:
            top_pages.append({
                "path": row.dimension_values[0].value,
                "views": int(row.metric_values[0].value),
            })
    except Exception as e:
        print(f"  [WARN] {property_label} top pages failed: {e}")

    # 7-day daily trend (for sparkline)
    daily_trend = []
    try:
        trend_response = client.run_report(RunReportRequest(
            property=property_path,
            date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="screenPageViews")],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))],
        ))

        for row in trend_response.rows:
            daily_trend.append({
                "date": row.dimension_values[0].value,
                "views": int(row.metric_values[0].value),
            })
    except Exception as e:
        print(f"  [WARN] {property_label} trend failed: {e}")

    return {
        "label": property_label,
        "pageviews": pageviews,
        "users": users,
        "sessions": sessions,
        "top_pages": top_pages,
        "daily_trend": daily_trend,
    }


def fetch_ga4_stats() -> dict:
    """Fetch stats from all GA4 properties and return combined data."""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    print("  Fetching GA4 analytics...")

    creds = _get_credentials()
    if not creds:
        print("  [ERR] Could not get GA4 credentials")
        return {}

    client = BetaAnalyticsDataClient(credentials=creds)

    properties = {}
    total_views = 0
    total_users = 0
    total_sessions = 0

    for label, config in GA4_PROPERTIES.items():
        stats = _fetch_property_stats(client, config["property_id"], label)
        properties[label] = stats
        total_views += stats["pageviews"]
        total_users += stats["users"]
        total_sessions += stats["sessions"]

    # Find top page across all properties
    all_pages = []
    for p in properties.values():
        all_pages.extend(p.get("top_pages", []))
    all_pages.sort(key=lambda x: x["views"], reverse=True)
    top_page = all_pages[0]["path"] if all_pages else "/"

    result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "totals": {
            "pageviews": total_views,
            "users": total_users,
            "sessions": total_sessions,
            "top_page": top_page,
        },
        "properties": properties,
    }

    # Write to JSON
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ GA4 stats saved to {OUTPUT_PATH}")
    print(f"    Views: {total_views} | Users: {total_users} | Sessions: {total_sessions}")

    return result


if __name__ == "__main__":
    fetch_ga4_stats()
