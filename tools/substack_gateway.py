#!/usr/bin/env python3
"""Substack endpoints borrowed from jakub-k-slys/substack-gateway-oss (v3.7-4.0.1).

That repo is a FastAPI/MCP server; we only want the endpoint knowledge, so this is
a sync port on top of substack_dossier.SubstackClient (same SID cookie, no new deps).

  python3 tools/substack_gateway.py drafts [N]            # newest drafts (post_management)
  python3 tools/substack_gateway.py ai-check <draft_id>   # Pangram AI-writing scan
  python3 tools/substack_gateway.py prepublish <draft_id> # editor pre-publish errors/suggestions
  python3 tools/substack_gateway.py stats [DAYS]          # 30d views + subscriber series
  python3 tools/substack_gateway.py post-stats [post_id]  # engagement/traffic/growth (default: latest post)
  python3 tools/substack_gateway.py schedule <draft_id> <ISO time> --audience=everyone|only_paid
  python3 tools/substack_gateway.py unschedule <draft_id>

ai-check matters: Substack shows readers an AI disclosure driven by this scan, and
it is the same verdict a reader could see. Run it before anything goes out.
"""
import json
import os
import sys
from datetime import UTC, datetime, timedelta

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from substack_dossier import SubstackClient  # noqa: E402


class Gateway:
    def __init__(self, client=None):
        self.c = client or SubstackClient()
        self.base = f"https://{self.c.pub}/api/v1/"

    def _req(self, method, path, **kw):
        r = self.c.session.request(method, self.base + path, headers=self.c.headers,
                                   timeout=60, **kw)
        r.raise_for_status()
        return r.json() if r.content else None

    # --- drafts -----------------------------------------------------------------
    def list_drafts(self, limit=10, offset=0):
        d = self._req("GET", "post_management/drafts", params={
            "offset": offset, "limit": limit,
            "order_by": "draft_updated_at", "order_direction": "desc"})
        return d.get("posts", []) if isinstance(d, dict) else d

    def ai_detection(self, draft_id):
        """Pangram scan. type=success carries fraction_ai/_ai_assisted/_human;
        type=error means unscannable (e.g. video-only draft)."""
        d = self._req("GET", f"drafts/{draft_id}/pangram_detection")
        d.pop("disclosure", None)  # huge pub blob, not the verdict
        return d

    def prepublish(self, draft_id):
        return self._req("GET", f"drafts/{draft_id}/prepublish")

    def schedule(self, draft_id, when, audience):
        """Timed release. Outward-facing: publishes AND emails at `when`."""
        dt = when if isinstance(when, datetime) else datetime.fromisoformat(when.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        trigger = dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        self._req("POST", f"drafts/{draft_id}/scheduled_release", json={
            "trigger_at": trigger, "post_audience": audience, "email_audience": audience})
        return trigger

    def unschedule(self, draft_id):
        self._req("DELETE", f"drafts/{draft_id}/scheduled_release")

    # --- stats ------------------------------------------------------------------
    def views_30d(self):
        return self._req("GET", "publication/stats/publication_traffic/30d_views")

    def subscriber_series(self, days=30):
        """Rows of [date, paid, comps, free_trials, total]; header row dropped."""
        frm = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
        rows = self._req("GET", "publication/stats/subscribers/timeseries", params={"from": frm})
        return [r for r in (rows or [])[1:] if isinstance(r, list) and r]

    def post_stats(self, post_id, tab):
        """tab: engagement | traffic | growth | recipients | discussion."""
        return self._req("GET", f"post_management/detail/{post_id}/{tab}")

    def latest_post(self):
        a = self._req("GET", "archive", params={"sort": "new", "limit": 1})
        return a[0] if a else None


def fmt_ai(d):
    if d.get("type") != "success":
        return f"AI-CHECK: n/a ({d.get('header')})"
    ai, asst, hum = (round(100 * (d.get(k) or 0)) for k in
                     ("fraction_ai", "fraction_ai_assisted", "fraction_human"))
    flag = "  <-- readers may see an AI disclosure" if ai + asst >= 50 else ""
    return f"AI-CHECK: {d.get('header')} | ai {ai}% assisted {asst}% human {hum}%{flag}"


def fmt_prepublish(d):
    errs, sugg = d.get("errors") or [], d.get("suggestions") or []
    out = [f"PREPUBLISH: {len(errs)} error(s), {len(sugg)} suggestion(s)"]
    out += [f"  ERR  {json.dumps(e)[:160]}" for e in errs]
    out += [f"  hint {json.dumps(s)[:160]}" for s in sugg]
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    cmd, rest = args[0], args[1:]
    g = Gateway()
    if cmd == "drafts":
        for d in g.list_drafts(int(rest[0]) if rest else 10):
            print(f"{d.get('id')}  {(d.get('draft_updated_at') or '')[:10]}  "
                  f"{d.get('draft_title') or '(untitled)'}")
    elif cmd == "ai-check":
        print(fmt_ai(g.ai_detection(int(rest[0]))))
    elif cmd == "prepublish":
        print(fmt_prepublish(g.prepublish(int(rest[0]))))
    elif cmd == "stats":
        v = g.views_30d()
        print(f"30d views: {v.get('views30d')} ({v.get('viewsDelta30d'):+d} vs prior 30d)")
        rows = g.subscriber_series(int(rest[0]) if rest else 30)
        if rows:
            f, l = rows[0], rows[-1]
            print(f"paid {f[1]} -> {l[1]}   comps {f[2]} -> {l[2]}   ({f[0]} -> {l[0]})")
    elif cmd == "post-stats":
        post = {"id": int(rest[0])} if rest else g.latest_post()
        pid = post["id"]
        print(f"POST {pid} {post.get('title', '')}")
        e = g.post_stats(pid, "engagement")
        print(f"  likes {(e.get('likes') or {}).get('count', 0)}  "
              f"comments {(e.get('commentSummary') or {}).get('total', 0)}")
        refs = sorted(g.post_stats(pid, "traffic").get("referrers") or [],
                      key=lambda r: -(r.get("views") or 0))[:8]
        for r in refs:
            print(f"  {r.get('views', 0):>6} views  {r.get('source_category')}/{r.get('source')}"
                  f"  signups {r.get('signups', 0)} subs {r.get('subscribes', 0)}")
        gr = g.post_stats(pid, "growth")
        print(f"  growth: signups {(gr.get('signups') or {}).get('total', 0)}  "
              f"subscribes {((gr.get('subscribes') or {}).get('totals') or {}).get('subscribes', 0)}  "
              f"unsubs {(gr.get('unsubscribes') or {}).get('total', 0)}")
    elif cmd == "schedule":
        aud = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--audience=")), None)
        if aud not in ("everyone", "only_paid", "founding"):
            print("schedule needs an explicit --audience=everyone|only_paid"); sys.exit(2)
        print(f"SCHEDULED {rest[0]} for {g.schedule(int(rest[0]), rest[1], aud)} ({aud})")
    elif cmd == "unschedule":
        g.unschedule(int(rest[0])); print(f"UNSCHEDULED {rest[0]}")
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
