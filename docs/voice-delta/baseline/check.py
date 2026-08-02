#!/usr/bin/env python3
"""Baseline drift check — score a draft against pre-AI Michael.

Read-only diagnostic. Never rewrites, never scores "quality." It measures a
finished draft against the control corpus (109 AfterHour posts, Dec 2024 to
Mar 2025, written before any LLM was in the loop) and reports where the draft
drifts from how he actually writes when nobody is helping.

Baseline rates are computed live from control_corpus.md, not hardcoded, so
they stay honest if the corpus is ever rebuilt.

Two sections in the output:
  MEASURED  — things a regex can honestly check.
  ASK       — judgment calls the script refuses to fake. Answer them yourself.

Usage:
    python3 check.py draft.md
    python3 check.py ../../../docs/substack/drafts/*.md
"""
import os, re, sys, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "control_corpus.md")

# name -> (regex, direction) where direction is "want" or "avoid"
MARKERS = {
    "hedge on standing": (
        r"(?i)(do your own|not advice|i'm not trying to|not to brag|"
        r"double check me|i could be wrong|happy to be wrong|please do your own|"
        r"i'm not sure if)", "want"),
    "but I digress": (r"(?i)\bi digress\b", "want"),
    "inline arithmetic": (r"\(\(?\s*\d[\d,.]*\s*[-+*/]", "want"),
    "profanity": (r"(?i)(fuck|\bshit\b|sh\*t|damn|\bass\b|ffs)", "want"),
    "italic emphasis": (r"\*[A-Za-z][^*\n]{1,25}\*", "want"),
}

BANNED = {
    "em/en dash": r"[—–]",
    "here's the truth / real talk": r"(?i)(here'?s the truth|real talk|let me be honest)",
    "everyone/nobody wind-up": r"(?i)(everyone (gets|thinks|says|knows)|nobody (talks|tells)|no one tells)",
    "hype filler": r"(?i)(buckle up|changes everything|that last part is everything)",
    "markdown table": r"(?m)^\s*\|.*\|\s*$",
    "last name": r"(?i)\bhanko\b",
}

ASK = [
    "Does the thesis have a real-life origin, something you physically noticed?",
    "Is there anything in here that did NOT work, left visible?",
    "Is the call confident while the caller stays modest? Or does it read like a guru?",
    "Would your wife read a jargon line and ask if she's having a stroke?",
]


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if 2 < len(s.split()) < 80]


def strip_md(text):
    """Drop code fences, urls, ticker-list lines, and headers."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"https?://\S+", " ", text)
    lines = [l for l in text.split("\n")
             if not l.startswith("#") and l.strip() not in ("---", "")
             and not re.match(r"^\s*\$[A-Z.]+\s*(-->|\d|$)", l)]
    return "\n".join(lines)


def profile(text):
    body = strip_md(text)
    words = max(len(body.split()), 1)
    out = {"words": words}
    for name, (rx, _) in MARKERS.items():
        out[name] = len(re.findall(rx, body, re.M)) / words * 10000
    sents = sentences(body)
    out["median sentence"] = statistics.median(len(s.split()) for s in sents) if sents else 0
    return out


def load_baseline():
    if not os.path.exists(CORPUS):
        raise SystemExit(f"missing {CORPUS} — rebuild it from data/afterhour/mphinance.json")
    return profile(open(CORPUS).read())


def check(path, base):
    text = open(path).read()
    p = profile(text)
    print(f"\n{'=' * 66}\n{os.path.basename(path)}  ({p['words']} words)\n{'=' * 66}")

    hard = [f"  {name}: {n}" for name, rx in BANNED.items()
            if (n := len(re.findall(rx, text, re.M)))]
    if not re.search(r"(?m)^~ Michael\s*$", text):
        hard.append("  signature: no `~ Michael` line found")
    if hard:
        print("\nBANNED (fix these)")
        print("\n".join(hard))

    print(f"\nMEASURED  (per 10k words, draft vs pre-AI baseline)")
    print(f"  {'marker':22} {'draft':>8} {'baseline':>9}   drift")
    for name in MARKERS:
        d, b = p[name], base[name]
        if b == 0 and d == 0:
            continue
        flag = ""
        if b > 0:
            ratio = d / b
            if ratio < 0.4:
                flag = "  LOW"
            elif ratio > 2.5:
                flag = "  HIGH"
        print(f"  {name:22} {d:8.1f} {b:9.1f}{flag}")
    ds, bs = p["median sentence"], base["median sentence"]
    flag = "  LONG" if ds > bs + 6 else ("  SHORT" if ds < bs - 5 else "")
    print(f"  {'median sentence':22} {ds:8.1f} {bs:9.1f}{flag}")

    print("\nASK  (the script will not guess these)")
    for q in ASK:
        print(f"  [ ] {q}")


def main():
    paths = sys.argv[1:]
    if not paths:
        raise SystemExit(__doc__)
    base = load_baseline()
    for path in paths:
        check(path, base)
    print()


if __name__ == "__main__":
    main()
