#!/usr/bin/env python3
"""pxlse.io (Trader Social) public-API client — the cross-post counterpart to the
Substack pusher. Lives next to tools/push_substack.py.

Unlike Substack (drafts that you publish later), the pxlse public API has no draft
state: POST /posts publishes immediately to your pxlse audience. Treat every
create_post() call as a live, outward-facing publish.

Auth + base URL come from secrets.env (PULSE_API_KEY / PULSE_API_BASE), loaded the
same way substack_dossier.SubstackClient loads SUBSTACK_SID.

API surface used:
  POST /posts   {title, content(markdown), subtitle?, tags?<=5, cover_image_url?, visibility}
  POST /media   multipart file=<png/webp/...> -> {storage_key, url}
  GET  /me      -> {username, plan_status, rate_limit_per_minute, ...}

Ticker mentions ($AAPL) in `content` are auto-linked by pxlse — no separate field.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = "https://api.pxlse.io/api/public/v1"


def load_secrets():
    """Mirror substack_dossier._load_secrets — parse secrets.env into a dict."""
    secrets = {}
    env_path = PROJECT_ROOT / "secrets.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                secrets[k] = v.strip().strip('"')
    return secrets


class PulseClient:
    def __init__(self, api_key=None, base=None):
        import requests
        self.session = requests.Session()
        secrets = load_secrets()
        self.api_key = api_key or os.environ.get("PULSE_API_KEY") or secrets.get("PULSE_API_KEY", "")
        self.base = (base or os.environ.get("PULSE_API_BASE") or
                     secrets.get("PULSE_API_BASE") or DEFAULT_BASE).rstrip("/")
        if not self.api_key:
            raise RuntimeError("PULSE_API_KEY missing — add it to secrets.env")
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "mphinance-crosspost/1.0",
        })

    def me(self):
        r = self.session.get(f"{self.base}/me", timeout=20)
        r.raise_for_status()
        return r.json()

    def upload_media(self, path, content_type=None):
        """Upload an image. Returns {storage_key, url} or None."""
        import mimetypes
        ct = content_type or mimetypes.guess_type(str(path))[0] or "image/png"
        with open(path, "rb") as f:
            r = self.session.post(
                f"{self.base}/media",
                files={"file": (os.path.basename(str(path)), f, ct)},
                timeout=90,
            )
        if r.status_code in (200, 201):
            return r.json()
        print(f"  media upload {r.status_code}: {r.text[:160]}")
        return None

    def upload_media_bytes(self, data, filename, content_type="image/png"):
        """Upload raw bytes (e.g. a remote image we just fetched)."""
        import io
        r = self.session.post(
            f"{self.base}/media",
            files={"file": (filename, io.BytesIO(data), content_type)},
            timeout=90,
        )
        if r.status_code in (200, 201):
            return r.json()
        print(f"  media upload {r.status_code}: {r.text[:160]}")
        return None

    def create_post(self, title, content, subtitle=None, tags=None,
                    cover_image_url=None, visibility="public"):
        """Publish a post live. Returns the response JSON (incl. id) or raises."""
        body = {"title": title[:500], "content": content, "visibility": visibility}
        if subtitle:
            body["subtitle"] = subtitle[:1000]
        if tags:
            body["tags"] = list(tags)[:5]
        if cover_image_url:
            body["cover_image_url"] = cover_image_url[:2048]
        r = self.session.post(f"{self.base}/posts", json=body, timeout=60)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"create_post {r.status_code}: {r.text[:300]}")
        return r.json()

    def update_post(self, post_id, title=None, content=None, subtitle=None,
                    tags=None, cover_image_url=None):
        """PATCH an existing post (propagate a Substack edit). Only non-None fields
        are sent. Returns the response JSON or raises."""
        body = {}
        if title is not None:
            body["title"] = title[:500]
        if content is not None:
            body["content"] = content
        if subtitle is not None:
            body["subtitle"] = subtitle[:1000]
        if tags is not None:
            body["tags"] = list(tags)[:5]
        if cover_image_url is not None:
            body["cover_image_url"] = cover_image_url[:2048]
        r = self.session.patch(f"{self.base}/posts/{post_id}", json=body, timeout=60)
        if r.status_code not in (200, 201):
            raise RuntimeError(f"update_post {r.status_code}: {r.text[:300]}")
        return r.json()

    def post_url(self, post_id):
        return f"https://pxlse.io/post/{post_id}"


if __name__ == "__main__":
    # Smoke test: who am I + rate limits.
    c = PulseClient()
    me = c.me()
    print(f"pxlse: @{me.get('username')}  plan={me.get('plan_status')}  "
          f"limits={me.get('rate_limit_per_minute')}/min {me.get('rate_limit_per_day')}/day")
