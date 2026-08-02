#!/usr/bin/env python3
"""Substack post HTML -> markdown, shared by the pxlse cross-posters.

Substack's published body_html (from /api/v1/posts/{slug} or the export zip) is regular
semantic HTML — p / h2-h6 / figure>img / blockquote / ul-ol / a / strong-em / hr — so a
focused bs4 walker converts it cleanly. Images are emitted as `![alt]({{IMG:n}})`
placeholders; the caller re-hosts each URL (collected into `images`) and swaps them in.
"""
import json
import re

INLINE = {"strong": "**", "b": "**", "em": "*", "i": "*"}
SKIP_CLASSES = ("subscribe-widget", "button-wrapper", "paywall", "footer",
                "subscription-widget", "poll-embed", "comments-page-link",
                "captioned-image-container")  # images handled separately


def _data_attrs(el):
    try:
        return json.loads(el.get("data-attrs") or "{}")
    except Exception:
        return {}


def _inline_md(node):
    from bs4 import NavigableString, Tag
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            cls = " ".join(c.get("class", []))
            # Substack renders $TICKER cashtags as an EMPTY span; the symbol lives in
            # data-attrs. Emit it as plain text so pxlse re-links it as a cashtag.
            if "cashtag-wrap" in cls or c.get("data-component-name") == "CashtagToDOM":
                sym = _data_attrs(c).get("symbol")
                if sym:
                    out.append(sym)
                continue
            if c.name == "a" and c.get("href"):
                txt = _inline_md(c).strip()
                if txt:
                    out.append(f"[{txt}]({c['href']})")
            elif c.name in INLINE:
                mark = INLINE[c.name]
                inner = _inline_md(c).strip()
                out.append(f"{mark}{inner}{mark}" if inner else "")
            elif c.name == "br":
                out.append("\n")
            elif c.name in ("code", "kbd"):
                out.append(f"`{_inline_md(c).strip()}`")
            else:
                out.append(_inline_md(c))
    return "".join(out)


def _emit_image(fig, blocks, images):
    img = fig.find("img")
    if not img:
        return
    src = img.get("src") or ""
    if not src:
        return
    idx = len(images)
    images.append(src)
    cap = fig.find("figcaption")
    alt = (cap.get_text(" ", strip=True) if cap else (img.get("alt") or "")).strip()
    blocks.append(f"![{alt}]({{{{IMG:{idx}}}}})")


def _walk_block(el, blocks, images):
    from bs4 import Tag
    cls = " ".join(el.get("class", []))
    comp = el.get("data-component-name")
    if el.name == "figure" or "captioned-image-container" in cls:
        fig = el if el.name == "figure" else el.find("figure")
        if fig:
            _emit_image(fig, blocks, images)
        return
    # Embedded post card (his cross-community shoutouts) -> a clean markdown link.
    if comp == "EmbeddedPostToDOM":
        a = _data_attrs(el)
        url = a.get("url")
        title = (a.get("title") or "").strip()
        pub = (a.get("publication_name") or "").strip()
        if url:
            label = " — ".join(x for x in (title, pub) if x) or url
            blocks.append(f"[{label}]({url})")
        return
    if any(sk in cls for sk in SKIP_CLASSES):
        return
    if el.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(el.name[1])
        blocks.append("#" * max(2, level) + " " + _inline_md(el).strip())
    elif el.name == "p":
        t = _inline_md(el).strip()
        if t:
            blocks.append(t)
    elif el.name == "blockquote":
        t = _inline_md(el).strip()
        if t:
            blocks.append("\n".join("> " + ln for ln in t.split("\n")))
    elif el.name == "hr":
        blocks.append("---")
    elif el.name in ("ul", "ol"):
        ordered = el.name == "ol"
        for i, li in enumerate(el.find_all("li", recursive=False), 1):
            prefix = f"{i}. " if ordered else "- "
            blocks.append(prefix + _inline_md(li).strip())
    elif el.name == "pre":
        blocks.append("```\n" + el.get_text() + "\n```")
    elif el.name in ("div", "section", "article"):
        kids = [c for c in el.find_all(recursive=False) if isinstance(c, Tag)]
        if kids:
            for child in kids:
                _walk_block(child, blocks, images)
        else:
            t = _inline_md(el).strip()
            if t:
                blocks.append(t)


def html_to_markdown(html):
    """Return (markdown_with_{{IMG:n}}_placeholders, image_src_list)."""
    from bs4 import BeautifulSoup, Tag
    soup = BeautifulSoup(html, "html.parser")
    blocks, images = [], []
    root = soup.body or soup
    top = [c for c in root.find_all(recursive=False) if isinstance(c, Tag)] or \
          [c for c in root.children if isinstance(c, Tag)]
    for el in top:
        _walk_block(el, blocks, images)
    md = "\n\n".join(b for b in blocks if b.strip())
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    # Tidy whitespace left by emptied web-components: "$DIS  at" -> "$DIS at",
    # "$BWA  : a clean" -> "$BWA: a clean".
    md = re.sub(r"[ \t]{2,}", " ", md)
    md = re.sub(r" +([:,.;])", r"\1", md)
    return md, images


def rehost_images(client, urls, dry=False):
    """Download each Substack image and re-upload to pxlse. Returns pxlse URLs (falls
    back to the original URL on failure or in dry-run)."""
    import os
    import requests
    out = []
    for u in urls:
        if dry:
            out.append(u); continue
        try:
            resp = requests.get(u, timeout=60)
            if resp.status_code == 200 and resp.content:
                fn = os.path.basename(u.split("?")[0]) or "image.png"
                ct = resp.headers.get("Content-Type", "image/png").split(";")[0]
                up = client.upload_media_bytes(resp.content, fn, content_type=ct)
                out.append(up["url"] if up else u)
            else:
                out.append(u)
        except Exception as e:
            print(f"    image fetch failed ({e}) — keeping substack url")
            out.append(u)
    return out


def swap_images(md, hosted_urls):
    for i, url in enumerate(hosted_urls):
        md = md.replace(f"{{{{IMG:{i}}}}}", url)
    return md


def _inline_tiptap(s, marks=None):
    """Parse inline markdown (**bold**, *italic*, `code`, [text](href)) into a list
    of TipTap text nodes. `marks` accumulates as we recurse into emphasis/links."""
    marks = list(marks or [])
    nodes = []

    def emit_text(txt):
        if not txt:
            return
        node = {"type": "text", "text": txt}
        if marks:
            node["marks"] = [dict(m) for m in marks]
        nodes.append(node)

    i, n = 0, len(s)
    buf = []
    while i < n:
        # inline code — no nested parsing
        if s[i] == "`":
            end = s.find("`", i + 1)
            if end != -1:
                emit_text("".join(buf)); buf = []
                node = {"type": "text", "text": s[i + 1:end],
                        "marks": [dict(m) for m in marks] + [{"type": "code"}]}
                nodes.append(node)
                i = end + 1
                continue
        # bold (check ** before *)
        if s.startswith("**", i):
            end = s.find("**", i + 2)
            if end != -1:
                emit_text("".join(buf)); buf = []
                nodes.extend(_inline_tiptap(s[i + 2:end], marks + [{"type": "bold"}]))
                i = end + 2
                continue
        if s[i] == "*":
            end = s.find("*", i + 1)
            if end != -1:
                emit_text("".join(buf)); buf = []
                nodes.extend(_inline_tiptap(s[i + 1:end], marks + [{"type": "italic"}]))
                i = end + 1
                continue
        # link [text](href)
        if s[i] == "[":
            close = s.find("]", i + 1)
            if close != -1 and close + 1 < n and s[close + 1] == "(":
                end = s.find(")", close + 2)
                if end != -1:
                    emit_text("".join(buf)); buf = []
                    href = s[close + 2:end]
                    nodes.extend(_inline_tiptap(
                        s[i + 1:close],
                        marks + [{"type": "link", "attrs": {"href": href, "target": "_blank"}}]))
                    i = end + 1
                    continue
        buf.append(s[i])
        i += 1
    emit_text("".join(buf))
    return nodes


def markdown_to_tiptap(md):
    """Convert the markdown produced by html_to_markdown (already image-rehosted) into
    a TipTap/ProseMirror doc dict. Pulse renders `content` as TipTap — markdown image
    and formatting syntax otherwise shows as literal text. Handles headings, paragraphs,
    block images, bullet/ordered lists, blockquotes, hr, fenced code, and inline marks."""
    blocks = [b for b in re.split(r"\n{2,}", md.replace("\r\n", "\n")) if b.strip()]
    content = []
    i = 0
    img_re = re.compile(r"^!\[(.*?)\]\((.*?)\)$")
    ul_re = re.compile(r"^[-*] +(.*)$")
    ol_re = re.compile(r"^\d+\. +(.*)$")

    def list_item(text):
        return {"type": "listItem",
                "content": [{"type": "paragraph", "content": _inline_tiptap(text)}]}

    while i < len(blocks):
        b = blocks[i].strip()
        # fenced code
        if b.startswith("```"):
            body = b[3:]
            if body.endswith("```"):
                body = body[:-3]
            content.append({"type": "codeBlock",
                            "content": [{"type": "text", "text": body.strip("\n")}]})
            i += 1
            continue
        if b == "---":
            content.append({"type": "horizontalRule"})
            i += 1
            continue
        m = img_re.match(b)
        if m:
            content.append({"type": "image",
                            "attrs": {"src": m.group(2), "alt": m.group(1) or "", "title": None}})
            i += 1
            continue
        hm = re.match(r"^(#{1,6}) +(.*)$", b)
        if hm:
            level = max(2, min(6, len(hm.group(1))))
            content.append({"type": "heading", "attrs": {"level": level},
                            "content": _inline_tiptap(hm.group(2))})
            i += 1
            continue
        if b.startswith("> "):
            paras = [{"type": "paragraph", "content": _inline_tiptap(ln[2:] if ln.startswith("> ") else ln)}
                     for ln in b.split("\n")]
            content.append({"type": "blockquote", "content": paras})
            i += 1
            continue
        if ul_re.match(b):
            items = []
            while i < len(blocks) and ul_re.match(blocks[i].strip()):
                items.append(list_item(ul_re.match(blocks[i].strip()).group(1)))
                i += 1
            content.append({"type": "bulletList", "content": items})
            continue
        if ol_re.match(b):
            items = []
            while i < len(blocks) and ol_re.match(blocks[i].strip()):
                items.append(list_item(ol_re.match(blocks[i].strip()).group(1)))
                i += 1
            content.append({"type": "orderedList", "content": items})
            continue
        content.append({"type": "paragraph", "content": _inline_tiptap(b)})
        i += 1

    return {"type": "doc", "content": content}


def split_subtitle(subtitle):
    """Michael uses the Substack subtitle two ways: a real one-line dek, or an SEO
    keyword list ("Tags: a, b, c" or "amzn, cpi, options flow, ..."). Keyword lists read
    badly as a pxlse dek but map perfectly to pxlse's tags field. Return (dek_or_None,
    tags_list[<=5]); exactly one side is populated."""
    s = (subtitle or "").strip()
    if not s:
        return None, []
    if s.lower().startswith("tags:"):
        s = s.split(":", 1)[1].strip()
        return None, _clean_tags(s.split(","))
    parts = [p.strip() for p in s.split(",")]
    # Keyword list: 3+ short comma-separated items, no sentence punctuation.
    if len(parts) >= 3 and all(len(p.split()) <= 4 for p in parts) and not re.search(r"[.!?;:]", s):
        return None, _clean_tags(parts)
    return s, []


def _clean_tags(parts):
    out = []
    for p in parts:
        t = p.strip().strip(".").strip()
        if t and len(t) <= 40 and t.lower() not in (x.lower() for x in out):
            out.append(t)
    return out[:5]
