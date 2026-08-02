#!/usr/bin/env python3
"""Render an annotated candlestick PNG for one or more tickers, from TraderDaddy
Pro's own /api/agent/ticker/:symbol/chart-data (90d OHLC + indicators).

No scraping, no TradingView account, no third-party chart API — our own data.
Run with the skill venv:  .venv/bin/python scripts/render_chart.py CRWD MRVL --out <dir>

Each chart: candlesticks + EMA 8/21/55 + SMA200 overlay, volume panel, RSI panel.
Prints one line per chart: "<TICKER>\t<png_path>" (or "<TICKER>\tERROR: ...").
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf

SKILL_DIR = Path(__file__).resolve().parent.parent
TD_BASE = os.environ.get("TD_API_URL", "https://traderdaddy-pro-whop-production.up.railway.app")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def find_repo_root(start: Path) -> Path:
    d = start
    for _ in range(8):
        if (d / ".env_agent_api").exists() or (d / "CLAUDE.md").exists():
            return d
        if d.parent == d:
            break
        d = d.parent
    return SKILL_DIR.parent.parent.parent


def load_agent_key() -> str | None:
    if os.environ.get("AGENT_API_KEY"):
        return os.environ["AGENT_API_KEY"].strip()
    f = find_repo_root(SKILL_DIR) / ".env_agent_api"
    if f.exists():
        raw = f.read_text().strip()
        return raw.split("=", 1)[1].strip() if raw[:1].isalpha() and "=" in raw and raw.split("=", 1)[0].isupper() else raw
    return None


def fetch_chart_data(symbol: str, key: str | None, days: int = 90) -> dict:
    url = f"{TD_BASE}/api/agent/ticker/{symbol}/chart-data?days={days}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def render(symbol: str, key: str | None, out_dir: Path, days: int = 90) -> str:
    data = fetch_chart_data(symbol, key, days)
    rows = data.get("chartData") or []
    if len(rows) < 10:
        raise ValueError(f"only {len(rows)} candles returned")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    ohlc = df[["open", "high", "low", "close", "volume"]].astype(float)

    def col(name):
        return df[name].astype(float) if name in df and df[name].notna().any() else None

    addplots = []
    for name, color, width in [("ema8", "#22d3ee", 0.9), ("ema21", "#f59e0b", 0.9), ("ema55", "#a78bfa", 0.9), ("sma200", "#94a3b8", 1.1)]:
        s = col(name)
        if s is not None:
            addplots.append(mpf.make_addplot(s, color=color, width=width))
    rsi = col("rsi")
    panel_ratios = (6, 1.4)
    if rsi is not None:
        addplots.append(mpf.make_addplot(rsi, panel=2, color="#e879f9", width=1.0, ylabel="RSI"))
        addplots.append(mpf.make_addplot(pd.Series(70, index=df.index), panel=2, color="#475569", width=0.6, linestyle="--"))
        addplots.append(mpf.make_addplot(pd.Series(30, index=df.index), panel=2, color="#475569", width=0.6, linestyle="--"))
        panel_ratios = (6, 1.4, 1.6)

    price = data.get("currentPrice")
    chg = data.get("changePercent")
    name = data.get("name", symbol)
    title = f"\n{symbol} — {name}    ${price}  ({chg:+.2f}%)" if isinstance(chg, (int, float)) else f"\n{symbol} — {name}"
    legend = "EMA8(cyan) EMA21(amber) EMA55(violet) SMA200(grey)"

    out_path = out_dir / f"{symbol}.png"
    fig, axes = mpf.plot(
        ohlc, type="candle", style="nightclouds", addplot=addplots, volume=True,
        panel_ratios=panel_ratios, figratio=(16, 9), figscale=1.3, tight_layout=True,
        title=title, ylabel="Price", datetime_format="%b %d", xrotation=0,
        returnfig=True,
    )
    # self-documenting EMA legend, top-left of the price panel
    axes[0].text(0.005, 0.985, legend, transform=axes[0].transAxes, fontsize=8,
                 va="top", ha="left", color="#cbd5e1",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#0f172a", ec="#334155", alpha=0.8))
    fig.savefig(str(out_path), dpi=110, bbox_inches="tight")
    plt.close(fig)
    return str(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--out", default=str(SKILL_DIR / "runs" / "_charts"))
    ap.add_argument("--days", type=int, default=90,
                    help="lookback in calendar days; use 300 to judge a multi-month trendline")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    key = load_agent_key()
    for sym in args.symbols:
        s = sym.upper().strip()
        try:
            p = render(s, key, out_dir, args.days)
            print(f"{s}\t{p}")
        except Exception as e:  # noqa: BLE001 — one bad symbol shouldn't kill the batch
            print(f"{s}\tERROR: {e}", file=sys.stderr)
            print(f"{s}\tERROR: {e}")


if __name__ == "__main__":
    main()
