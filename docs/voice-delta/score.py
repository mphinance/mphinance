#!/usr/bin/env python3
"""Voice-delta scoring — turn the corpus into numbers.

Two questions, one script:

  Q1. "How close is the machine's GIVEN draft to what Michael SHIPPED?"
      Token Jaccard between given.md and shipped.md.  Baseline.

  Q2. "If we feed the same given.md through VOICE-DELTA.md (predict.py),
      do we move CLOSER to shipped.md?"
      Token Jaccard between predicted.md and shipped.md.  IF this number
      is reliably higher than Q1, VOICE-DELTA.md is doing work.

Plus a rule-hit detector: scan each diff for the documented edit patterns
(immediacy, self-correction, Sam=her, Phund/we, title transform, shoutout,
product-link, top-of-post disclaimer).  Reports which rules fired in which
pairs — that's the "did the rule actually generalize" check.

Usage:
    python3 score.py                       # score every pair, write ACCURACY.md
    python3 score.py --pair <name>         # score one pair, print JSON
    python3 score.py --json                # all pairs, JSON to stdout (no md write)
"""
import json, os, re, sys, glob, argparse, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = os.path.join(HERE, "pairs")
OUT_MD = os.path.join(HERE, "..", "..", "ACCURACY.md")

WORD = re.compile(r"[a-z0-9']+")
TITLE_LINE = re.compile(r"(?im)^\s*(?:TITLE:|#\s)(.+)$")


def tokens(text):
    return set(WORD.findall(text.lower()))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def diff_stats(a, b):
    al, bl = a.splitlines(), b.splitlines()
    sm = difflib.SequenceMatcher(a=al, b=bl, autojunk=False)
    added = removed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("replace", "delete"):
            removed += i2 - i1
        if tag in ("replace", "insert"):
            added += j2 - j1
    return {"lines_added": added, "lines_removed": removed,
            "ratio": round(sm.ratio(), 4)}


def first_title(text):
    m = TITLE_LINE.search(text)
    return m.group(1).strip() if m else ""


# ─── rule-hit detectors ──────────────────────────────────────────────────
# Each detector: did the SHIPPED text gain (or lose) the pattern relative
# to the GIVEN text?  Boolean per rule per pair.  Cheap, deterministic,
# and matches the rule categories in /VOICE-DELTA.md.

IMMEDIACY = re.compile(r"\b(last night|this morning|tonight|today|right now|just now)\b", re.I)
# Self-correction: parenthetical hedge OR bare-clause hedge.  Apostrophe class
# matches straight + Unicode curly because Substack's editor swaps them.
APOS = r"['‘’]"
SELF_CORRECT = re.compile(
    rf"\((that{APOS}s not true|that is not true|the screener didn{APOS}t know|sort of|kinda|i think|i couldn{APOS}t find it)[^)]*\)"
    rf"|\b(mostly|sort of|kinda)\.\s",
    re.I)
SAM_HER = re.compile(r"\b(sam|tradeerdaddybot|traderdaddybot)\b[^.]{0,40}\b(she|her|hers)\b", re.I)
SAM_HIM = re.compile(r"\b(sam|tradeerdaddybot|traderdaddybot)\b[^.]{0,40}\b(he|his|him)\b", re.I)
PHUND_WE = re.compile(r"\b(phund|we|our|us)\b", re.I)
SHOUTOUT = re.compile(r"https?://[\w./?=&-]*substack\.com|x\.com/|twitter\.com/", re.I)
PRODUCT_LINK = re.compile(r"traderdaddy(?:bot)?\.pro|tickertrace\.pro|mphinance\.substack\.com", re.I)
META_TRANSITION = re.compile(
    r"\b(here is the truth|here's the truth|here is the thing|here's the thing|"
    r"the bottom line|let me explain|now the confession)\b", re.I)
DISCLAIMER = re.compile(r"not financial advice|nfa", re.I)


def count(rgx, text):
    return len(rgx.findall(text))


def rule_hits(given, shipped):
    """Return dict of rule → True/False/Δ depending on rule type."""
    gT, sT = first_title(given), first_title(shipped)
    return {
        "R1_title_transform": bool(gT and sT and gT.strip().lower() != sT.strip().lower()),
        "R2_immediacy_added": count(IMMEDIACY, shipped) > count(IMMEDIACY, given),
        "R3_self_correction_added": count(SELF_CORRECT, shipped) > count(SELF_CORRECT, given),
        "R4_sam_her_repaired": (count(SAM_HIM, given) > 0 and count(SAM_HIM, shipped) < count(SAM_HIM, given))
                               or (count(SAM_HER, shipped) > count(SAM_HER, given)),
        "R5_phund_we_added": count(PHUND_WE, shipped) > count(PHUND_WE, given),
        "R6_shoutout_added": count(SHOUTOUT, shipped) > count(SHOUTOUT, given),
        "R7_product_link_added": count(PRODUCT_LINK, shipped) > count(PRODUCT_LINK, given),
        "R8_meta_transition_cut": count(META_TRANSITION, given) > count(META_TRANSITION, shipped),
        "R9_disclaimer_present": bool(DISCLAIMER.search(shipped)),
    }


# ─── per-pair scorer ─────────────────────────────────────────────────────

def score_pair(pair_dir):
    name = os.path.basename(pair_dir.rstrip("/"))
    g = os.path.join(pair_dir, "given.md")
    s = os.path.join(pair_dir, "shipped.md")
    p = os.path.join(pair_dir, "predicted.md")
    if not (os.path.exists(g) and os.path.exists(s)):
        return None
    given = open(g).read()
    shipped = open(s).read()
    out = {
        "pair": name,
        "tokens_given": len(tokens(given)),
        "tokens_shipped": len(tokens(shipped)),
        "j_given_shipped": round(jaccard(tokens(given), tokens(shipped)), 4),
        "diff_given_shipped": diff_stats(given, shipped),
        "rules": rule_hits(given, shipped),
        "predicted": False,
    }
    if os.path.exists(p):
        predicted = open(p).read()
        out["predicted"] = True
        out["tokens_predicted"] = len(tokens(predicted))
        out["j_predicted_shipped"] = round(jaccard(tokens(predicted), tokens(shipped)), 4)
        out["delta_vs_baseline"] = round(out["j_predicted_shipped"] - out["j_given_shipped"], 4)
        out["diff_predicted_shipped"] = diff_stats(predicted, shipped)
        out["pred_rules"] = rule_hits(given, predicted)
    return out


def score_all():
    results = []
    for d in sorted(glob.glob(os.path.join(PAIRS, "*", ""))):
        r = score_pair(d)
        if r:
            results.append(r)
    return results


def render_md(results):
    have_pred = [r for r in results if r["predicted"]]
    lines = [
        "# VOICE-DELTA Accuracy Report",
        "",
        "_Auto-generated by `docs/voice-delta/score.py`. Numbers, not vibes._",
        "",
        "**Prediction provenance.** `predicted.md` per pair is the output of "
        "`predict.py` — `given.md` + `/VOICE-DELTA.md` packaged as a system+user "
        "prompt and sent to a Claude model (default `claude-opus-4-7`). When "
        "the `anthropic` SDK + `ANTHROPIC_API_KEY` are present the script "
        "writes the prediction itself; when not, `predict.py --print` emits "
        "the deterministic prompt for a human to hand to the same model. "
        "Identical prompt → comparable outputs.",
        "",
        "## How to read this",
        "",
        "- **j(given, shipped)** — token Jaccard between the machine's draft and the version Michael shipped. "
        "A higher number means the machine was already close; a lower number means his edit budget was large.",
        "- **j(predicted, shipped)** — same, but for the prediction made by running `given.md` through `predict.py` "
        "with `/VOICE-DELTA.md` rules applied. **This is the accuracy metric.**",
        "- **Δ** — `j(predicted, shipped) − j(given, shipped)`. Positive means VOICE-DELTA.md moved the draft closer to "
        "what Michael actually shipped. Negative means the rules hurt.",
        "- **Rule hits** — did each VOICE-DELTA.md rule actually fire in this pair's diff? `✓` yes, `·` no.",
        "",
        "## Per-pair scores",
        "",
        "| Pair | j(G,S) | j(P,S) | Δ | edits (+/−) |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        jps = f"{r['j_predicted_shipped']:.3f}" if r["predicted"] else "—"
        delta = f"{r['delta_vs_baseline']:+.3f}" if r["predicted"] else "—"
        edits = f"{r['diff_given_shipped']['lines_added']}/{r['diff_given_shipped']['lines_removed']}"
        lines.append(f"| {r['pair']} | {r['j_given_shipped']:.3f} | {jps} | {delta} | {edits} |")
    if have_pred:
        avg_g = sum(r["j_given_shipped"] for r in have_pred) / len(have_pred)
        avg_p = sum(r["j_predicted_shipped"] for r in have_pred) / len(have_pred)
        lines += [
            "",
            f"**Average across predicted pairs (N={len(have_pred)}):** "
            f"baseline j(G,S) = {avg_g:.3f}, with VOICE-DELTA j(P,S) = {avg_p:.3f}, "
            f"Δ = {avg_p - avg_g:+.3f}.",
        ]
    lines += ["", "## Rule-hit matrix", "",
              "Did each rule fire in the actual shipped diff? (Anchor pairs first, held-out at the bottom.)",
              ""]
    rule_names = list(results[0]["rules"].keys()) if results else []
    header = "| Pair | " + " | ".join(r.replace("_", " ") for r in rule_names) + " |"
    sep = "|---" * (len(rule_names) + 1) + "|"
    lines += [header, sep]
    for r in results:
        row = "| " + r["pair"] + " | " + " | ".join("✓" if r["rules"][k] else "·" for k in rule_names) + " |"
        lines.append(row)
    if rule_names:
        coverage = {k: sum(1 for r in results if r["rules"][k]) for k in rule_names}
        lines += ["",
                  "**Per-rule coverage across the corpus:** "
                  + ", ".join(f"{k.split('_',1)[0]} {coverage[k]}/{len(results)}" for k in rule_names)
                  + ".",
                  ""]
    if have_pred:
        lines += ["## Prediction rule-hit matrix",
                  "",
                  "Same matrix, but for the **predicted** ship (what VOICE-DELTA suggested). "
                  "Compare against the row above for the same pair: matching ✓s = the rule was learned correctly.",
                  "",
                  header, sep]
        for r in have_pred:
            row = ("| " + r["pair"] + " | " +
                   " | ".join("✓" if r["pred_rules"][k] else "·" for k in rule_names) + " |")
            lines.append(row)
        lines += [""]
    lines += ["---",
              f"_Pairs: {len(results)} · with predictions: {len(have_pred)}_",
              ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", help="Score one pair by directory name")
    ap.add_argument("--json", action="store_true", help="Emit JSON to stdout instead of writing markdown")
    args = ap.parse_args()

    if args.pair:
        r = score_pair(os.path.join(PAIRS, args.pair))
        print(json.dumps(r, indent=2) if r else "no such pair (or missing given/shipped)")
        return
    results = score_all()
    if args.json:
        print(json.dumps(results, indent=2))
        return
    md = render_md(results)
    with open(OUT_MD, "w") as f:
        f.write(md)
    print(f"wrote {OUT_MD} ({len(results)} pairs, "
          f"{sum(1 for r in results if r['predicted'])} with predictions)")


if __name__ == "__main__":
    main()
