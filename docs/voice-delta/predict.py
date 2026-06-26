#!/usr/bin/env python3
"""Voice-delta predictor — apply /VOICE-DELTA.md to a given.md to predict shipped.md.

This is the half of the accuracy harness that needs an LLM.  Given a pair's
machine draft and the documented edit rules, ask a model to produce the
version Michael would most likely ship.  We then diff the prediction against
the actual shipped post (score.py) — the closer the prediction lands, the
more accurate VOICE-DELTA.md is.

It is deliberately a PURE EDITOR, not a writer.  The prompt tells the model
to make Michael's edits and nothing more — no inventing new sections, no
adding facts the machine couldn't have known.  We grade the rules, not
imagination.

Modes (auto-detected):
  1. anthropic SDK + ANTHROPIC_API_KEY  → calls the API, writes predicted.md.
  2. neither                            → prints the prompt to stdout.  Pipe
                                          to your model of choice, save the
                                          response as pairs/<name>/predicted.md.

Usage:
    python3 predict.py <pair-name> [<pair-name> ...]
    python3 predict.py --all                     # every pair missing predicted.md
    python3 predict.py --print <pair-name>       # just print the prompt, no API
    python3 predict.py --model claude-opus-4-7 …
"""
import os, sys, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = os.path.join(HERE, "pairs")
RULES = os.path.normpath(os.path.join(HERE, "..", "..", "VOICE-DELTA.md"))

SYSTEM = """You are the Voice-Delta predictor for Michael Hanko's writing.

Your job: apply the documented edit rules in VOICE-DELTA.md to the machine's
GIVEN draft and output what Michael would most plausibly SHIP. You are an
editor, not a writer. Make his edits, not new posts.

Hard constraints:
- Output ONLY the predicted shipped markdown. No preamble, no commentary, no
  "Here's the prediction:" header. The first line of your output is the first
  line of the predicted post.
- Apply the rules in VOICE-DELTA.md. If a rule says "swap abstract metaphor
  for warm physical one," do it. If a rule says "cut meta-transitions like
  'Here is the truth,'" cut them. If a rule says "Sam is her," fix the
  pronouns.
- Do NOT invent net-new sections, new tickers, new trades, or facts the
  machine could not have known. If the actual shipped post added a personal
  story or a brand-new methodology section, you cannot predict that — and
  you should not try. Your prediction is the edit, not the rewrite.
- Keep the post's structure: same sections, same images (image alt text),
  same footer. Edit within them.
- Preserve typos he keeps (per the rules) — small imperfections read as
  human; do not sand them smooth.
- Title transform: the rule is "kill the generic noun, name the payoff."
  If the given title is mechanism-y, rewrite it; otherwise leave it alone.
"""

USER_TEMPLATE = """# VOICE-DELTA.md (rules)

{rules}

---

# GIVEN draft (machine output)

{given}

---

# Your task

Output the predicted SHIPPED version of the GIVEN draft above, applying the
rules in VOICE-DELTA.md. Output markdown only — no preamble.
"""


def build_prompt(pair_name):
    pair_dir = os.path.join(PAIRS, pair_name)
    given_path = os.path.join(pair_dir, "given.md")
    if not os.path.exists(given_path):
        raise SystemExit(f"no given.md for pair: {pair_name}")
    given = open(given_path).read()
    rules = open(RULES).read()
    return SYSTEM, USER_TEMPLATE.format(rules=rules, given=given)


def call_api(system, user, model):
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text"))


def have_api():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa
        return True
    except ImportError:
        return False


def all_pairs_needing_prediction():
    out = []
    for d in sorted(glob.glob(os.path.join(PAIRS, "*", ""))):
        if (os.path.exists(os.path.join(d, "given.md"))
                and os.path.exists(os.path.join(d, "shipped.md"))
                and not os.path.exists(os.path.join(d, "predicted.md"))):
            out.append(os.path.basename(d.rstrip("/")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--print", dest="print_only", action="store_true",
                    help="Print prompt to stdout, do not call API")
    ap.add_argument("--model", default="claude-opus-4-7")
    args = ap.parse_args()

    targets = list(args.pairs)
    if args.all:
        targets += all_pairs_needing_prediction()
    if not targets:
        print("nothing to do (pass pair names, or --all). "
              f"pairs awaiting prediction: {all_pairs_needing_prediction() or '—'}")
        return

    use_api = (not args.print_only) and have_api()
    for name in targets:
        sys_p, user_p = build_prompt(name)
        if args.print_only or not use_api:
            sep = "─" * 60
            print(f"{sep}\n# pair: {name}\n# (no API call — pipe this prompt to your model)\n{sep}")
            print("## SYSTEM\n" + sys_p)
            print("\n## USER\n" + user_p)
            print(f"{sep}\n# save model output to pairs/{name}/predicted.md\n{sep}\n")
            continue
        text = call_api(sys_p, user_p, args.model)
        dst = os.path.join(PAIRS, name, "predicted.md")
        with open(dst, "w") as f:
            f.write(text)
        print(f"wrote {dst} ({len(text)} chars, model={args.model})")


if __name__ == "__main__":
    main()
