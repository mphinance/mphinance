#!/usr/bin/env python3
"""Minimal Gemini image generator. Usage: gen_image.py "<prompt>" <out.png> [model]

Key resolution order:
  1. GEMINI_API_KEY in mphinance/secrets.env  (canonical)
  2. GEMINI_API_KEY_ALT in secrets.env         (fallback)
"""
import base64
import os
import sys

import requests

SECRETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "secrets.env")


def load_key():
    keys = {}
    for line in open(SECRETS):
        line = line.strip()
        if line.startswith("GEMINI_API_KEY="):
            keys["primary"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("GEMINI_API_KEY_ALT="):
            keys["alt"] = line.split("=", 1)[1].strip().strip('"')
    return keys


prompt, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "gemini-3-pro-image"
keys = load_key()

last_err = None
for label in ("primary", "alt"):
    key = keys.get(label)
    if not key:
        continue
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=180,
    )
    if r.status_code == 200:
        parts = r.json()["candidates"][0]["content"]["parts"]
        for p in parts:
            data = p.get("inlineData") or p.get("inline_data")
            if data:
                with open(out, "wb") as f:
                    f.write(base64.b64decode(data["data"]))
                print("Wrote", out, f"(key={label}, model={model})")
                sys.exit(0)
        print("No image in response:", str(parts)[:500])
        sys.exit(1)
    last_err = f"{label}: {r.status_code} {r.text[:200]}"

print("All keys failed:", last_err)
sys.exit(1)
