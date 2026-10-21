#!/usr/bin/env python3
"""Mentorship interest form — mentor.mphinance.com.

Dependency-free stdlib server. GET / serves the form, POST /submit appends one
JSON line to RESPONSES, GET /responses?key=ADMIN_KEY shows what came in.
Bound to the docker0 host IP so only coolify-proxy (Traefik) can reach it.
"""
import html
import threading
import urllib.request
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
BIND = os.environ.get("MENTOR_BIND", "10.0.0.1")
PORT = int(os.environ.get("MENTOR_PORT", "8772"))
RESPONSES = Path(os.environ.get(
    "MENTOR_RESPONSES", HERE.parents[1] / "data/mentor-interest/responses.jsonl"))
ADMIN_KEY = os.environ.get("MENTOR_ADMIN_KEY", "")
# Optional: ping a Discord channel/thread on each submission (nyx's bot token).
NOTIFY_TOKEN = os.environ.get("MENTOR_DISCORD_TOKEN", "")
NOTIFY_CHANNEL = os.environ.get("MENTOR_DISCORD_CHANNEL", "")

FIELDS = ["name", "email", "discord", "experience", "goal", "price", "timing"]
MAX_LEN = 2000
_last_post: dict[str, float] = {}


def page(name: str) -> bytes:
    return (HERE / name).read_bytes()


def notify(row: dict):
    """Best-effort Discord ping. A failure here never affects the submission."""
    if not (NOTIFY_TOKEN and NOTIFY_CHANNEL):
        return
    try:
        count = sum(1 for l in RESPONSES.read_text().splitlines() if l.strip())
        goal = row["goal"][:300] or "-"
        msg = (f"📝 **Mentor list #{count}**: {row['name'] or '(no name)'} · {row['email']}"
               f"{' · ' + row['discord'] if row['discord'] else ''}\n"
               f"Experience: {row['experience'] or '-'} · At $400: {row['price'] or '-'} · Calls: {row['timing'] or '-'}\n"
               f"> {goal}")
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{NOTIFY_CHANNEL}/messages",
            data=json.dumps({"content": msg[:1900], "allowed_mentions": {"parse": []}}).encode(),
            headers={"Authorization": f"Bot {NOTIFY_TOKEN}", "Content-Type": "application/json",
                     "User-Agent": "mentor-interest (mphinance, 1.0)"})
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        print(f"notify failed: {e}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _client(self) -> str:
        return self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self._send(200, page("index.html"))
        if url.path == "/thanks":
            return self._send(200, page("thanks.html"))
        if url.path == "/healthz":
            return self._send(200, b"ok", "text/plain")
        if url.path == "/responses":
            key = parse_qs(url.query).get("key", [""])[0]
            if not ADMIN_KEY or key != ADMIN_KEY:
                return self._send(404, b"not found", "text/plain")
            return self._send(200, self._admin())
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/submit":
            return self._send(404, b"not found", "text/plain")
        length = min(int(self.headers.get("Content-Length", 0)), 20000)
        form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        get = lambda k: form.get(k, [""])[0].strip()[:MAX_LEN]

        # Honeypot: humans never see the "website" field.
        if get("website"):
            return self._redirect("/thanks")
        ip = self._client()
        if time.time() - _last_post.get(ip, 0) < 10:
            return self._redirect("/thanks")
        if not get("email") or "@" not in get("email"):
            return self._send(400, b"An email is required. Go back and add one.", "text/plain")

        _last_post[ip] = time.time()
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ip": ip}
        row.update({k: get(k) for k in FIELDS})
        RESPONSES.parent.mkdir(parents=True, exist_ok=True)
        with RESPONSES.open("a") as f:
            f.write(json.dumps(row) + "\n")
        threading.Thread(target=notify, args=(row,), daemon=True).start()
        self._redirect("/thanks")

    def _redirect(self, to: str):
        self.send_response(303)
        self.send_header("Location", to)
        self.end_headers()

    def _admin(self) -> bytes:
        rows = []
        if RESPONSES.exists():
            rows = [json.loads(l) for l in RESPONSES.read_text().splitlines() if l.strip()]
        cols = ["ts"] + FIELDS
        head = "".join(f"<th>{c}</th>" for c in cols)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols) + "</tr>"
            for r in reversed(rows))
        return (f"<!doctype html><meta charset=utf-8><title>Responses</title>"
                f"<style>body{{font:14px system-ui;margin:24px}}table{{border-collapse:collapse}}"
                f"td,th{{border:1px solid #ddd;padding:6px;vertical-align:top;text-align:left}}"
                f"th{{background:#f4ecd6}}</style><h2>{len(rows)} responses</h2>"
                f"<table><tr>{head}</tr>{body}</table>").encode()

    def log_message(self, fmt, *args):
        print(f"{self._client()} {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"mentor-interest on {BIND}:{PORT} -> {RESPONSES}", flush=True)
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
