#!/usr/bin/env python3
"""Generate dark-theme Bloomberg-style infographics for the SpaceX IPO article.

Run with the matplotlib venv:
    /tmp/vmpl/bin/python docs/articles/spacex-ipo-trading-plan/make_images.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))

BG = "#0a0a0a"
PANEL = "#161b22"
WHITE = "#e6edf3"
GREY = "#8b949e"
GREEN = "#00ff41"   # bullish / good
GOLD = "#f0b400"    # caution
RED = "#e53935"     # danger / overvalued
BLUE = "#58a6ff"
MONO = "monospace"


def _frame(ax):
    ax.set_facecolor(BG)
    ax.axis("off")
    for yy in np.linspace(0.1, 0.9, 5):
        ax.axhline(y=yy, color="#ffffff", alpha=0.02, linestyle="--", lw=0.6)


# ── 1. HERO BANNER ────────────────────────────────────────────────────────────
def hero():
    fig, ax = plt.subplots(figsize=(12, 6.3), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    _frame(ax)

    ax.text(0.5, 0.80, "THE SPACEX IPO TRADE", fontsize=42, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.685, "EVERYONE HAS A PLAN. MOST WILL DONATE THEIR ACCOUNT.",
            fontsize=15.5, color=GOLD, ha="center", fontweight="bold", fontfamily=MONO)

    # stat tiles
    tiles = [
        ("IPO PRICE", "$135", GREEN),
        ("VALUATION", "$1.77T", GOLD),
        ("FY25 NET", "-$4.9B", RED),
        ("LISTS (SPCX)", "FRI JUN 12", BLUE),
    ]
    n = len(tiles); w = 0.205; gap = 0.025
    total = n * w + (n - 1) * gap
    x0 = (1 - total) / 2
    for i, (label, val, col) in enumerate(tiles):
        x = x0 + i * (w + gap)
        ax.add_patch(patches.FancyBboxPatch((x, 0.30), w, 0.26,
                     boxstyle="round,pad=0.006", linewidth=1.6,
                     edgecolor=col, facecolor=PANEL))
        ax.text(x + w / 2, 0.475, label, fontsize=10.5, color=GREY,
                ha="center", fontfamily=MONO)
        ax.text(x + w / 2, 0.38, val, fontsize=22, color=col,
                ha="center", fontweight="bold", fontfamily=MONO)

    ax.text(0.5, 0.14, "A $1.77 TRILLION BET ON THE JOCKEY, NOT THE HORSE",
            fontsize=12.5, color=GREY, ha="center", style="italic", fontfamily=MONO)
    ax.text(0.5, 0.06, "MOMENTUM PHINANCE  //  NOT FINANCIAL ADVICE",
            fontsize=10.5, color=RED, ha="center", fontweight="bold", fontfamily=MONO)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/hero_banner.png", dpi=200, facecolor=BG)
    plt.close()
    print("hero_banner.png")


# ── 2. THREE-ACT TIMELINE ─────────────────────────────────────────────────────
def three_act():
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    _frame(ax)

    ax.text(0.5, 0.93, "THE THREE-ACT STRUCTURE", fontsize=30, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.865, "ONE STOCK, THREE DIFFERENT TRADES, THREE DIFFERENT RISKS",
            fontsize=12.5, color=GOLD, ha="center", fontfamily=MONO)

    acts = [
        (GREEN, "ACT 1  //  DAY 1", "CAUTIOUSLY LONG",
         ["Opens +15-20% -> ~$155-162", "Scalp targets: $175 / $200",
          "NO institutional floor yet", "Pure retail reflexivity"]),
        (GOLD, "ACT 2  //  ~15 DAYS", "NASDAQ-100 BID",
         ["'Fast Entry': add @ 15 days", "Forced ETF buy: 0.47-0.7%",
          "S&P 500 said NO -> no SPY bid", "Front-run, don't chase"]),
        (RED, "ACT 3  //  ~6 MONTHS", "THE LOCKUP CLIFF",
         ["Tranches @ 70/90/105/120/135d", "+ Q2/Q3 earnings unlocks",
          "Musk locked 366d; others early", "You are the exit liquidity"]),
    ]
    w = 0.29; gap = 0.025
    total = 3 * w + 2 * gap
    x0 = (1 - total) / 2
    for i, (col, head, sub, bullets) in enumerate(acts):
        x = x0 + i * (w + gap)
        ax.add_patch(patches.FancyBboxPatch((x, 0.16), w, 0.62,
                     boxstyle="round,pad=0.008", linewidth=2,
                     edgecolor=col, facecolor=PANEL))
        ax.add_patch(patches.Rectangle((x, 0.715), w, 0.065, color=col, alpha=0.18))
        ax.text(x + w / 2, 0.735, head, fontsize=12.5, color=col,
                ha="center", fontweight="bold", fontfamily=MONO)
        ax.text(x + w / 2, 0.655, sub, fontsize=15.5, color=WHITE,
                ha="center", fontweight="bold", fontfamily=MONO)
        for j, b in enumerate(bullets):
            ax.text(x + 0.018, 0.57 - j * 0.075, "> " + b, fontsize=10,
                    color=GREY, ha="left", va="center", fontfamily=MONO)
        if i < 2:
            ax.annotate("", xy=(x + w + gap, 0.47), xytext=(x + w, 0.47),
                        arrowprops=dict(arrowstyle="-|>", color=WHITE, alpha=0.4, lw=1.5))

    ax.text(0.5, 0.07, "BULLISH -> NEUTRAL -> BEARISH  AS  SCARCITY  TURNS  INTO  SUPPLY",
            fontsize=12, color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/three_act_timeline.png", dpi=200, facecolor=BG)
    plt.close()
    print("three_act_timeline.png")


# ── 3. LOCKUP CLIFF ───────────────────────────────────────────────────────────
def lockup_cliff():
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor=BG)
    ax.set_facecolor(BG)

    # Illustrative cumulative tradeable supply. Schedule per S-1 reporting:
    # 7% time-tranches at 70/90/105/120/135d, plus Q2/Q3 earnings + 180d remainder.
    days =   [0, 70, 70, 90, 90, 105, 105, 120, 120, 135, 135, 165, 165, 180, 180, 200]
    supply = [0.556, 0.556, 1.4, 1.4, 2.1, 2.1, 2.8, 2.8, 3.6, 3.6, 4.3, 4.3, 5.8, 5.8, 7.5, 7.5]

    ax.plot(days, supply, color=RED, lw=2.6, solid_joinstyle="miter")
    ax.fill_between(days, supply, color=RED, alpha=0.12)

    for d, label in [(70, "70d"), (90, "90d"), (105, "105d"), (120, "120d"),
                     (135, "135d"), (180, "180d")]:
        ax.axvline(d, color=GOLD, alpha=0.30, lw=1, linestyle="--")
        ax.text(d, 8.15, label, color=GOLD, ha="center", fontsize=9.5, fontfamily=MONO)

    ax.scatter([0], [0.556], color=GREEN, zorder=5, s=60)
    ax.annotate("IPO FLOAT\n555.6M shares (~4%)", xy=(0, 0.556), xytext=(12, 2.6),
                color=GREEN, fontsize=11, fontfamily=MONO, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, alpha=0.7))
    ax.annotate("~7.5B SHARES (est.)\nTHE SUPPLY DUMP", xy=(180, 7.5), xytext=(108, 4.7),
                color=RED, fontsize=12, fontfamily=MONO, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, alpha=0.7))
    ax.text(150, 1.3, "MUSK: locked 366 days.\nEveryone else: out early.",
            color=BLUE, fontsize=10.5, ha="center", fontfamily=MONO, fontweight="bold")

    ax.set_xlim(-5, 205); ax.set_ylim(0, 8.4)
    ax.set_title("THE LOCKUP CLIFF: TRADEABLE SUPPLY OVER 6 MONTHS  (ILLUSTRATIVE)",
                 color=WHITE, fontsize=17, fontweight="bold", fontfamily=MONO, pad=16)
    ax.set_xlabel("DAYS AFTER IPO", color=GREY, fontsize=12, fontfamily=MONO)
    ax.set_ylabel("CUMULATIVE TRADEABLE SHARES (BILLIONS)", color=GREY, fontsize=11, fontfamily=MONO)
    ax.tick_params(colors=GREY)
    for s in ax.spines.values():
        s.set_color("#30363d")
    ax.grid(True, color="#ffffff", alpha=0.04)
    ax.text(202, 0.2,
            "Float starts tiny, then unlocks in waves. Scarcity is the\nMonth-1 floor and the Month-6 ceiling. Schedule per S-1.",
            color=GREY, fontsize=10, ha="right", va="bottom", style="italic", fontfamily=MONO)

    plt.tight_layout()
    plt.savefig(f"{OUT}/lockup_cliff.png", dpi=200, facecolor=BG)
    plt.close()
    print("lockup_cliff.png")


if __name__ == "__main__":
    hero()
    three_act()
    lockup_cliff()
    print("done ->", OUT)
