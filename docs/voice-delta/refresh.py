#!/usr/bin/env python3
"""Voice-delta refresh engine — the deterministic half of the recurring agent.

The LLM half (reading diffs, rewriting /VOICE-DELTA.md) runs on top of this. This
script does only the mechanical, repeatable work:

  1. CAPTURE  — snapshot every machine-GIVEN draft that still exists locally into
                the corpus, before ~/.mph-substack-cache gets cleaned and the
                draft is gone forever. (Given-draft survival is the bottleneck.)
  2. INDEX    — pull the recent published archive (date | title | slug) so the
                agent can match a given draft to the slug it shipped under.
  3. REPORT   — print a manifest: which pairs have given/shipped, and which
                captured drafts are still unmatched to a ship.

Run it, then let the agent fetch the unmatched ships (fetch_shipped.py <slug>) and
refresh the rules. Safe to run repeatedly; it never overwrites an existing file.

    python3 refresh.py            # capture + index + report
    python3 refresh.py --report   # report only (no network, no writes)
"""
import json, os, re, sys, glob, hashlib, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = os.path.join(HERE, "pairs")
ARCHIVE_TSV = os.path.join(PAIRS, "_archive.tsv")
HOME = os.path.expanduser("~")
BASE = "https://mphinance.substack.com"
UA = {"User-Agent": "Mozilla/5.0 (voice-delta refresh)"}

# Where machine-given drafts live. Globs, newest wins. Each entry yields
# (date, slug, path) so we can name a pair dir <date>_<slug>.
GIVEN_SOURCES = [
    os.path.join(HOME, ".mph-substack-cache", "*", "post.md"),
    os.path.join(HERE, "..", "..", "articles", "*", "substack-post.md"),
]


def _slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def discover_given():
    """Return list of (pair_name, source_path) for every locally-surviving draft."""
    found = []
    for pat in GIVEN_SOURCES:
        for path in glob.glob(pat):
            m = re.search(r"(\d{4}-\d{2}-\d{2})_([^/]+)/post\.md$", path)
            if m:
                name = f"{m.group(1)}_{m.group(2)}"
            else:  # articles/<slug>/substack-post.md — no date in path
                name = "undated_" + _slugify(os.path.basename(os.path.dirname(path)))
            found.append((name, os.path.realpath(path)))
    return found


def _existing_given_hashes():
    """Content hashes of every given.md already in the corpus — so the same draft
    captured from a differently-named source (e.g. an undated articles/ path) is
    recognized as a dup and skipped."""
    seen = {}
    for path in glob.glob(os.path.join(PAIRS, "*", "given.md")):
        with open(path, "rb") as f:
            seen[hashlib.sha256(f.read()).hexdigest()] = path
    return seen


def capture():
    new = []
    seen = _existing_given_hashes()
    for name, src in discover_given():
        dst = os.path.join(PAIRS, name, "given.md")
        if os.path.exists(dst):
            continue
        with open(src, "rb") as f:
            raw = f.read()
        h = hashlib.sha256(raw).hexdigest()
        if h in seen:  # same draft already captured under another name
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(raw)
        seen[h] = dst
        new.append(name)
    return new


def index():
    try:
        data = json.loads(urllib.request.urlopen(
            urllib.request.Request(f"{BASE}/api/v1/archive?sort=new&limit=50&offset=0",
                                   headers=UA), timeout=30).read())
    except Exception as e:
        print(f"  ! archive fetch failed: {e}", file=sys.stderr)
        return 0
    with open(ARCHIVE_TSV, "w") as f:
        f.write("date\ttitle\tslug\taudience\n")
        for p in data:
            f.write(f"{(p.get('post_date') or '')[:10]}\t{p.get('title','')}"
                    f"\t{p.get('slug','')}\t{p.get('audience','')}\n")
    return len(data)


def report():
    rows = []
    for d in sorted(glob.glob(os.path.join(PAIRS, "*", ""))):
        name = os.path.basename(d.rstrip("/"))
        g = os.path.exists(os.path.join(d, "given.md"))
        s = os.path.exists(os.path.join(d, "shipped.md"))
        rows.append((name, g, s))
    print("\n  pair                                         given  shipped")
    print("  " + "-" * 60)
    unmatched = []
    for name, g, s in rows:
        print(f"  {name:44} {'  ✓ ' if g else '  · ':5} {'  ✓' if s else '  —'}")
        if g and not s:
            unmatched.append(name)
    print(f"\n  {len(rows)} pairs · {sum(s for _,_,s in rows)} complete · "
          f"{len(unmatched)} awaiting a shipped match")
    if unmatched:
        print("  next: match each to a slug in pairs/_archive.tsv, then")
        print("        python3 fetch_shipped.py <slug> > pairs/<name>/shipped.md")
    return unmatched


if __name__ == "__main__":
    report_only = "--report" in sys.argv[1:]
    if not report_only:
        new = capture()
        print(f"captured {len(new)} new given draft(s): {new or '—'}")
        n = index()
        print(f"indexed {n} recent published posts → pairs/_archive.tsv")
    report()
