#!/usr/bin/env python3
"""Lint a draft against VOICE.md's "What This Voice NEVER Does" list.

Why this exists: the rules are written down, a self-edit pass is written down
(SUBSTACK.md), and the tells still ship in first drafts, because a model writing
prose reaches for them by default and only catches them when it rereads. This
makes the reread mechanical. It is a floor, not a judge: it cannot see forced
triads, aphorism-ending bullets or a moral bow on its own. Read the WARNs; the
ERRORs are hard bans.

  python3 tools/voice_lint.py <post.md>            # lint a markdown file
  python3 tools/voice_lint.py --draft <id>         # lint a live Substack draft
  python3 tools/voice_lint.py - < post.md          # stdin
  --strict   exit non-zero on warnings too

Exit: 0 clean (or warnings only), 1 errors (or warnings with --strict), 2 usage.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── hard bans (ERROR) ──────────────────────────────────────────────────────────
BANNED_PHRASES = [
    r"here'?s the truth", r"real talk", r"let me be honest", r"buckle up",
    r"this changes everything", r"that last part is everything",
    r"in this (article|post), (we|i) will",
    r"nobody talks about", r"no one talks about", r"everyone gets (this|it) wrong",
    r"(the part )?(that )?no ?one tells you", r"what nobody tells you",
]
AI_VOCAB = r"\b(delve[sd]?|delving|testament|tapestry|showcas(e|es|ed|ing)|foster(s|ed|ing)?|boast(s|ed|ing)?)\b"

# ── heuristics (WARN) ──────────────────────────────────────────────────────────
SOFT_VOCAB = r"\b(landscape|navigat(e|es|ing)|robust|pivotal|seamless(ly)?|genuinely|truly)\b"
WINDUPS = [
    r"^here'?s (what|the thing|why|how|where)\b", r"\bi want to be clear\b", r"\bto be clear\b",
    r"\bmake no mistake\b", r"\blet that sink in\b", r"\bthat was the problem\b",
    r"\bthat'?s the (whole )?(point|problem|post)\b", r"\bit'?s the whole post\b",
    r"\bkeep that (last sentence|in mind)\b", r"\bthe rest of this post\b",
    r"\bat the end of the day\b", r"\bthe real lesson\b", r"\btaught me\b",
]
# "isn't X, it's Y" inside one sentence
CONTRAST_INLINE = re.compile(
    r"\b(isn'?t|wasn'?t|aren'?t|weren'?t|is not|was not|was never|is never|not just|not only)\b"
    r"[^.!?]{0,90}?[,;:]\s*(it'?s|it is|it was|they'?re|it just|just|but)\b", re.I)
# "... wasn't X. It was Y." across two sentences
NEG_SENT = re.compile(r"\b(isn'?t|wasn'?t|aren'?t|weren'?t|never|not|none|no)\b", re.I)
POS_FOLLOW = re.compile(r"^(it'?s|it is|it was|it|they|that|what (i|you|we)\b[^.]*\bwas|this)\b", re.I)
CONTRAST_MAX_WORDS = 22
SIGNOFF = "~ Michael"


def blocks_from_markdown(md):
    """-> list of (kind, text). kind: h (heading), li (list item), p (paragraph)."""
    out, in_code = [], False
    for raw in md.split("\n"):
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code; continue
        if in_code or not s or s.startswith("![") or s.startswith("<!--") or s == "---":
            continue
        if s.startswith("#"):
            out.append(("h", s.lstrip("#").strip()))
        elif re.match(r"^([-*]|\d+\.)\s", s):
            out.append(("li", re.sub(r"^([-*]|\d+\.)\s+", "", s)))
        elif s.startswith("|"):
            out.append(("table", s))
        else:
            out.append(("p", s.lstrip("> ").strip()))
    return out


def blocks_from_prosemirror(doc):
    out = []

    def text_of(n):
        if n.get("type") == "text":
            return n.get("text", "")
        return "".join(text_of(c) for c in n.get("content", []) or [])

    def walk(n):
        t = n.get("type")
        if t == "heading":
            out.append(("h", text_of(n)))
        elif t == "listItem" or t == "list_item":
            out.append(("li", text_of(n)))
        elif t == "paragraph":
            txt = text_of(n).strip()
            if txt:
                out.append(("p", txt))
        elif t in ("captionedImage", "image2", "image", "codeBlock", "code_block"):
            return
        else:
            for c in n.get("content", []) or []:
                walk(c)
    walk(doc)
    return out


def plain(s):
    """Strip markdown emphasis/links so patterns see the prose."""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[*_`]", "", s)
    return s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def sentences(s):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", s) if x.strip()]


def lint(blocks, check_signoff=True):
    errs, warns = [], []

    def e(i, msg): errs.append((i, msg))
    def w(i, msg): warns.append((i, msg))

    for i, (kind, raw) in enumerate(blocks):
        t = plain(raw)
        low = t.lower()
        if kind == "table":
            e(i, "markdown table (Substack renders garbage; make an image)"); continue
        if re.search(r"[—–]", raw) or re.search(r"\s--\s", raw):
            e(i, "em/en dash")
        for pat in BANNED_PHRASES:
            if re.search(pat, low):
                e(i, f"banned phrase /{pat}/")
        m = re.search(AI_VOCAB, low)
        if m:
            e(i, f"AI vocabulary: '{m.group(0)}'")
        m = re.search(SOFT_VOCAB, low)
        if m:
            w(i, f"soft AI vocabulary: '{m.group(0)}'")
        for pat in WINDUPS:
            if re.search(pat, low):
                w(i, f"wind-up / announced point /{pat}/")
        if re.search(r"\b(managing partner)\b", low) or re.search(r"[-—]\s*michael\b", low):
            e(i, "byline/title or dashed sign-off (use '~ Michael')")
        if kind == "h":
            continue
        m = CONTRAST_INLINE.search(t)
        if m:
            w(i, f"staged contrast (not X, it's Y): '{m.group(0)[:70]}'")
        ss = sentences(t)
        pairs = list(zip(ss, ss[1:])) + [(a, c) for a, c in zip(ss, ss[2:])]
        for a, b in pairs:
            if NEG_SENT.search(a) and POS_FOLLOW.search(b) and len(a.split()) <= CONTRAST_MAX_WORDS and len(b.split()) <= CONTRAST_MAX_WORDS:
                w(i, f"staged contrast across sentences: '{a[:45]}' / '{b[:45]}'")
                break
        # repeated openings, 3 in a row
        # questions are exempt: the question ladder ("Do you... Do you... Do you...")
        # is one of his native openers (VOICE.md, Structural Patterns)
        firsts = [x.split()[0].lower() for x in ss if x.split() and not x.endswith("?")]
        for k in range(len(firsts) - 2):
            if firsts[k] == firsts[k + 1] == firsts[k + 2] and firsts[k] not in ("i",):
                w(i, f"three sentences in a row start with '{firsts[k]}'"); break
        # stacked fragments: "It's fine. It's table stakes."
        if re.search(r"\b(it'?s|that'?s) \w+( \w+)?\. (it'?s|that'?s) \w+( \w+)?\.", low):
            w(i, "stacked fragments ('It's X. It's Y.')")

    # one-line button paragraphs at the end of a section
    for i, (kind, raw) in enumerate(blocks):
        if kind != "p":
            continue
        t = plain(raw)
        nxt = blocks[i + 1][0] if i + 1 < len(blocks) else None
        n_words = len(t.split())
        if n_words <= 12 and len(sentences(t)) <= 2 and nxt in ("h", None) and t != SIGNOFF \
                and not t.startswith("~"):
            w(i, f"short button paragraph closing a section: '{t[:60]}'")

    # heading template
    heads = [plain(r) for k, r in blocks if k == "h"]
    # "The chatbot is the demo" / "The tab that asks me questions"; a bare noun
    # heading like "The Ledger" is fine, so require a clause (4+ words).
    the_heads = [h for h in heads if re.match(r"^(the|what|why|how) ", h, re.I) and len(h.split()) >= 4]
    if len(heads) >= 4 and len(the_heads) >= max(3, len(heads) // 2):
        w(-1, f"{len(the_heads)}/{len(heads)} headings share the 'The X that Y' template: {the_heads}")
    heads_low = [h.lower() for h in heads]
    if any("nobody" in h or "no one" in h for h in heads_low):
        w(-1, "heading uses nobody/no one")

    digress = sum("but i digress" in plain(r).lower() for _, r in blocks)
    if digress > 1:
        w(-1, f"'but I digress' used {digress}x (it's a tic, once max, only after a real tangent)")

    # subtitle / signature
    if check_signoff:
        tail = [plain(r).strip() for k, r in blocks if k == "p"]
        if not tail or tail[-1] != SIGNOFF:
            e(-1, f"last paragraph must be exactly '{SIGNOFF}' (found: '{tail[-1][:40] if tail else ''}')")
    if any(re.match(r"^tags:", plain(r), re.I) for _, r in blocks):
        e(-1, "old '*Tags: ...*' subtitle; use '*Trading 60% | Mindset 40%*'")
    return errs, warns


def fetch_draft(draft_id):
    sys.path.insert(0, REPO)
    from substack_dossier import SubstackClient
    c = SubstackClient()
    r = c.session.get(f"https://{c.pub}/api/v1/drafts/{draft_id}", headers=c.headers, timeout=20)
    r.raise_for_status()
    d = r.json()
    body = d.get("draft_body")
    doc = json.loads(body) if isinstance(body, str) else body
    return d.get("draft_title", ""), blocks_from_prosemirror(doc or {})


def report(blocks, errs, warns, label):
    def where(i):
        if i < 0:
            return "doc"
        k, t = blocks[i]
        return f"{k}#{i} \"{plain(t)[:50]}\""
    print(f"voice_lint: {label}")
    for i, m in errs:
        print(f"  ERROR  {m}\n         at {where(i)}")
    for i, m in warns:
        print(f"  warn   {m}\n         at {where(i)}")
    print(f"  {len(errs)} error(s), {len(warns)} warning(s)")


def run_file(path, strict=False):
    """Entry point for other tools (push_substack). Returns (n_errors, n_warnings)."""
    md = open(path, encoding="utf-8").read()
    blocks = blocks_from_markdown(md)
    errs, warns = lint(blocks)
    report(blocks, errs, warns, path)
    return len(errs), len(warns)


def main():
    argv = sys.argv[1:]
    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]
    if not argv:
        print(__doc__); sys.exit(2)
    if argv[0] == "--draft":
        if len(argv) < 2:
            print(__doc__); sys.exit(2)
        title, blocks = fetch_draft(argv[1])
        label = f"draft {argv[1]} ({title})"
    else:
        md = sys.stdin.read() if argv[0] == "-" else open(argv[0], encoding="utf-8").read()
        blocks, label = blocks_from_markdown(md), argv[0]
    errs, warns = lint(blocks)
    report(blocks, errs, warns, label)
    sys.exit(1 if errs or (strict and warns) else 0)


if __name__ == "__main__":
    main()
