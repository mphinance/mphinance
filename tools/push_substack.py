#!/usr/bin/env python3
"""Push a workspace post.md to Substack as a DRAFT using native ProseMirror nodes.

Reuses substack_dossier.SubstackClient (the only proven-working path — rawHtml and
body_html are broken). Text renders; the 4 images are uploaded to Substack's S3 and
embedded as safe link nodes (a wrong inline-image node type crashes the whole draft,
so we don't gamble the post on it — drop the PNGs in the editor, set the paywall).

The italic line under the H1 is the subtitle. Current convention is a category
mix with percentages, `*Trading 60% | Mindset 40%*` (see VOICE.md / SUBSTACK.md);
it is passed straight through as the Substack subtitle. Substack's real discovery
tags are a separate manual step in the editor and are not driven from here.

  python3 tools/push_substack.py <workspace>/post.md [--dry-run]
"""
import base64
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from substack_dossier import SubstackClient, _ascii_safe, p, h, bold, italic, link  # noqa: E402

IMAGE_ENDPOINT = "https://substack.com/api/v1/image"  # base64 data-URI -> {url,...}


def upload_image(client, path):
    """Upload a PNG via Substack's working image endpoint. Returns the JSON
    (url + imageWidth/imageHeight + bytes) or None."""
    try:
        b64 = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
        r = client.session.post(IMAGE_ENDPOINT, json={"image": b64},
                                headers=client.headers, timeout=60)
        if r.status_code in (200, 201):
            return r.json()
        print(f"  image upload {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"  image upload error: {e}")
    return None


def image_node(up, alt):
    """Native Substack captionedImage > image2 node (renders inline)."""
    return {"type": "captionedImage", "content": [{
        "type": "image2",
        "attrs": {
            "src": up["url"], "alt": _ascii_safe(alt),
            "fullscreen": False, "imageSize": "normal",
            "height": up.get("imageHeight"), "width": up.get("imageWidth"),
            "type": up.get("contentType", "image/png"), "bytes": up.get("bytes"),
            "srcNoWatermark": None, "resizeWidth": None, "title": None,
            "href": None, "belowTheFold": False, "topImage": False,
            "internalRedirect": None,
        },
    }]}


def code(text):
    """Native Substack inline code mark (monospace `like this`). The article uses
    these heavily for column names (`ema8`, `rsi`); without this they rendered as
    literal backticks and had to be fixed by hand."""
    return {"type": "text", "text": _ascii_safe(text), "marks": [{"type": "code"}]}


def inline(text):
    """Split a line into PM text nodes honoring `code` spans, **bold**, [text](url)
    links, and *italic* runs. Code is matched first so its contents are not
    re-interpreted as bold/italic."""
    out, pos = [], 0
    pat = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)]+)\)|\*([^*\n]+?)\*")
    for m in pat.finditer(text):
        if m.start() > pos:
            out.append(_ascii_safe(text[pos:m.start()]))
        if m.group(1) is not None:
            out.append(code(m.group(1)))
        elif m.group(2) is not None:
            out.append(bold(_ascii_safe(m.group(2))))
        elif m.group(3) is not None:
            out.append(link(_ascii_safe(m.group(3)), m.group(4)))
        else:
            out.append(italic(_ascii_safe(m.group(5))))
        pos = m.end()
    if pos < len(text):
        out.append(_ascii_safe(text[pos:]))
    return out or [_ascii_safe(text)]


def code_block(text):
    """Native Substack code_block node (monospace, copyable). Newlines are kept
    inside a single text node, which is how PM code blocks carry their content."""
    return {"type": "code_block", "content": [{"type": "text", "text": _ascii_safe(text)}]}


def build_doc(md_path, client, dry):
    lines = open(md_path, encoding="utf-8").read().split("\n")
    title, subtitle, nodes, i = "", "", [], 0
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if not title and s.startswith("# "):
            title = _ascii_safe(s[2:].strip()); i += 1; continue
        # The italic line under the H1 is the subtitle (current convention is a
        # category mix like "*Trading 60% | Mindset 40%*"). Pass it straight through.
        if title and not subtitle and s.startswith("*") and s.endswith("*") and len(s) > 2:
            subtitle = _ascii_safe(s.strip("*").strip())
            i += 1; continue
        # Fenced code block: collect verbatim lines (preserve indentation) until the
        # closing fence. Must run BEFORE the blank-line skip so blank code lines survive.
        if s.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i]); i += 1
            i += 1  # skip closing fence
            nodes.append(code_block("\n".join(code_lines)))
            continue
        if not s:
            i += 1; continue
        if s.startswith("## "):
            nodes.append(h(2, _ascii_safe(s[3:].strip())))
        elif s.startswith("# "):
            nodes.append(h(2, _ascii_safe(s[2:].strip())))
        elif s == "---":
            nodes.append(p(_ascii_safe("* * *")))
        elif s.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
            if m:
                alt, fn = m.group(1), m.group(2)
                if dry:
                    nodes.append(p(bold(_ascii_safe(f"[IMAGE: {alt}]"))))
                else:
                    img_path = fn if os.path.isabs(fn) else os.path.join(os.path.dirname(md_path), fn)
                    up = upload_image(client, img_path)
                    if up and up.get("url"):
                        nodes.append(image_node(up, alt))
                    else:
                        nodes.append(p(bold(_ascii_safe(f"[CHART FAILED: {alt} — add by hand]"))))
        elif s.startswith("- "):
            nodes.append(p("* ", *inline(s[2:])))
        elif s.startswith("*") and s.endswith("*") and "**" not in s:
            nodes.append(p(italic(_ascii_safe(s.strip("*").strip()))))
        else:
            nodes.append(p(*inline(s)))
        i += 1
    return title, subtitle, {"type": "doc", "content": nodes}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    md_path, dry = args[0], "--dry-run" in sys.argv
    client = SubstackClient()
    if not dry:
        if not client.authenticate():
            print("AUTH FAILED — check SUBSTACK_SID in secrets.env"); sys.exit(2)
    title, subtitle, doc = build_doc(md_path, client, dry)
    print(f"TITLE:    {title}")
    print(f"SUBTITLE: {subtitle or '(none — set by hand in editor)'}")
    print(f"NODES:    {len(doc['content'])}  (images: {sum(n.get('type') == 'captionedImage' for n in doc['content'])})")
    if dry:
        print("DRY RUN — no API call."); return
    res = client.create_draft(title, subtitle, doc)
    if res and res.get("id"):
        print(f"DRAFT: https://mphinance.substack.com/publish/post/{res['id']}")
    else:
        print(f"CREATE FAILED: {res}")


if __name__ == "__main__":
    main()
