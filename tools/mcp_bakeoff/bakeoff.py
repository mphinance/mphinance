#!/usr/bin/env python3
"""
TraderDaddy MCP model bake-off.

Freeze one TraderDaddy Pro data snapshot, fire the SAME question at N models
through OpenRouter, and print every answer side by side with latency + cost.

Usage:
  python3 bakeoff.py                      # runs the flagship question
  python3 bakeoff.py --q pin              # pick a sample query by key
  python3 bakeoff.py --list               # show the sample-query menu
  python3 bakeoff.py --models "anthropic/claude-opus-4.6,openai/gpt-5"

Needs: OPENROUTER_API_KEY in env.
"""
import os, sys, json, time, argparse, textwrap
from concurrent.futures import ThreadPoolExecutor
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://openrouter.ai/api/v1/chat/completions"
KEY = os.environ.get("OPENROUTER_API_KEY")

DEFAULT_MODELS = [
    "anthropic/claude-opus-4.6",
    "openai/gpt-5",
    "google/gemini-2.5-pro",
    "x-ai/grok-4.3",
    "deepseek/deepseek-chat-v3.1",
]

# ---- Sample queries over the MCP snapshot -----------------------------------
# Each is a real question a trader would ask Sam against TraderDaddy data.
SAMPLE_QUERIES = {
    "flagship": (
        "You are Sam, a blunt 0DTE/swing trading copilot. Using ONLY the snapshot, into the NEXT "
        "session give: (1) a one-line regime read, (2) the SINGLE highest-conviction index trade "
        "with entry / stop / target quoted off the gamma levels, (3) the one risk that voids it. "
        "Be specific with numbers. Under 110 words. No hedging, no disclaimers."
    ),
    "pin": (
        "Which index is most likely to PIN into next expiry and at what strike? Justify from gamma "
        "flip, max-gamma strike, and totalGEX sign. One paragraph, numbers only that matter."
    ),
    "divergence": (
        "SPY shows Negative Gamma while SPX/QQQ/IWM show Positive Gamma on the same tape. Explain how "
        "that's possible and which one I should trust for Monday's open. Under 90 words."
    ),
    "whale": (
        "A single $114M SMH 640C (exp 2026-07-17) print is the largest trade. Spot is far below 640. "
        "Is this a conviction bull bet, a hedge, or a roll — and how would you trade ALONGSIDE it "
        "without chasing? Under 100 words."
    ),
}

SYSTEM = (
    "You are a sharp options-flow trading analyst. Answer ONLY from the JSON snapshot provided. "
    "Gamma terms: positive/long gamma = dealers dampen moves (mean reversion, pinning); negative/short "
    "gamma = dealers amplify moves (trending, volatile). Never invent prices not derivable from the data."
)


def load_context():
    # newest context_*.json in this dir
    files = sorted(f for f in os.listdir(HERE) if f.startswith("context_") and f.endswith(".json"))
    if not files:
        sys.exit("No context_*.json found next to bakeoff.py")
    path = os.path.join(HERE, files[-1])
    return path, open(path).read()


def call_model(model, system, user, web=0, effort="low"):
    t0 = time.time()
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
        "max_tokens": 2000,  # reasoning models (gpt-5, gemini) need headroom or they truncate
        # Same reasoning budget for every model — without this, gpt-5 burns the whole
        # budget thinking and never emits a final answer. Fair + matches "blunt copilot".
        "reasoning": {"effort": effort},
        "usage": {"include": True},  # ask OpenRouter to return real $ cost
    }
    if web:
        # Same OpenRouter-hosted web plugin for EVERY model — the fair way to
        # add "what they'd get from searching in the webui." ~$0.004/result.
        body["plugins"] = [{"id": "web", "max_results": web}]
    try:
        r = requests.post(
            API,
            headers={
                "Authorization": f"Bearer {KEY}",
                "HTTP-Referer": "https://mphinance.substack.com",
                "X-Title": "TraderDaddy MCP Bake-off",
            },
            json=body,
            timeout=240,
        )
        dt = time.time() - t0
        if r.status_code != 200:
            return {"model": model, "ok": False, "dt": dt, "err": f"HTTP {r.status_code}: {r.text[:160]}"}
        j = r.json()
        choice = j["choices"][0]
        m = choice.get("message", {}) or {}
        msg = (m.get("content") or m.get("reasoning") or "").strip()
        if not msg:
            fr = choice.get("finish_reason")
            return {"model": model, "ok": False, "dt": time.time() - t0,
                    "err": f"empty content (finish_reason={fr}, likely reasoning-token starved)"}
        usage = j.get("usage", {}) or {}
        # count citations the model actually used, when present
        ann = m.get("annotations") or []
        n_cited = sum(1 for a in ann if a.get("type") == "url_citation")
        return {
            "model": model, "ok": True, "dt": dt, "text": msg,
            "in": usage.get("prompt_tokens"), "out": usage.get("completion_tokens"),
            "cost": usage.get("cost"), "cited": n_cited,
        }
    except Exception as e:
        return {"model": model, "ok": False, "dt": time.time() - t0, "err": str(e)[:160]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", default="flagship", help="sample query key")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--online", nargs="?", const=3, type=int, default=0,
                    help="give EVERY model the same web search (N results, default 3)")
    ap.add_argument("--effort", default="low", choices=["low", "medium", "high"],
                    help="reasoning effort, applied uniformly (default low)")
    args = ap.parse_args()

    if args.list:
        for k, v in SAMPLE_QUERIES.items():
            print(f"\n[{k}]\n{textwrap.fill(v, 96)}")
        return
    if not KEY:
        sys.exit("OPENROUTER_API_KEY not set")
    if args.q not in SAMPLE_QUERIES:
        sys.exit(f"Unknown query '{args.q}'. Options: {', '.join(SAMPLE_QUERIES)}")

    ctx_path, ctx = load_context()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    question = SAMPLE_QUERIES[args.q]
    user = f"SNAPSHOT (TraderDaddy Pro MCP):\n{ctx}\n\nQUESTION:\n{question}"

    print(f"Context : {os.path.basename(ctx_path)}")
    print(f"Query   : [{args.q}] {question[:70]}...")
    mode = f"ONLINE (web={args.online}/model, equal for all)" if args.online else "OFFLINE (snapshot only, controlled)"
    print(f"Mode    : {mode}")
    print(f"Models  : {len(models)}  |  firing concurrently...\n")

    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        results = list(ex.map(lambda m: call_model(m, SYSTEM, user, args.online, args.effort), models))

    # answers
    for res in sorted(results, key=lambda r: r["dt"]):
        print("=" * 92)
        if not res["ok"]:
            print(f"{res['model']}   [FAILED in {res['dt']:.1f}s]  {res['err']}")
            continue
        cost = f"${res['cost']:.5f}" if res.get("cost") is not None else "n/a"
        cited = f"  |  {res.get('cited',0)} cites" if args.online else ""
        print(f"{res['model']}   |  {res['dt']:.1f}s  |  {res['out']} out tok  |  {cost}{cited}")
        print("-" * 92)
        print(textwrap.fill(res["text"], 92, replace_whitespace=False))
        print()

    # scoreboard
    print("=" * 92)
    print(f"{'MODEL':34s} {'LATENCY':>9s} {'OUT TOK':>9s} {'COST':>10s}")
    print("-" * 92)
    for res in sorted(results, key=lambda r: (not r["ok"], r["dt"])):
        if res["ok"]:
            cost = f"${res['cost']:.5f}" if res.get("cost") is not None else "n/a"
            print(f"{res['model']:34s} {res['dt']:>8.1f}s {str(res['out']):>9s} {cost:>10s}")
        else:
            print(f"{res['model']:34s} {res['dt']:>8.1f}s   FAILED")


if __name__ == "__main__":
    main()
