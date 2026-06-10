#!/usr/bin/env python3
"""Image generator for the "Three Doors" Trader Lady launch piece.

Dark, Bloomberg-terminal aesthetic. Writes hero_banner.png + two infographics
into this script's own directory.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).parent

BG = "#0d1117"
PANEL = "#161b22"
GREEN = "#00ff41"   # free / good
GOLD = "#f0b400"    # paid-easy / caution
PINK = "#ff2d78"    # trader lady brand
BLUE = "#4d9fff"    # serious / cockpit
INK = "#e6edf3"
MUTE = "#8b949e"
MONO = "monospace"


def _frame(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def hero():
    fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    _frame(ax)

    ax.text(0.5, 0.82, "THANK YOU, TRADINGVIEW", color=BLUE, fontsize=38,
            fontweight="bold", family=MONO, ha="center", va="center")
    ax.text(0.5, 0.655, "THREE DOORS I BUILT ON YOUR DATA", color=MUTE,
            fontsize=18, family=MONO, ha="center", va="center")
    ax.text(0.5, 0.545, "ONE OF THEM FREE", color=GREEN, fontsize=22,
            fontweight="bold", family=MONO, ha="center", va="center")

    doors = [
        ("TRADERDADDY PRO", "the full cockpit", BLUE),
        ("TRADER LADY", "$7.99 / mo  ask her", PINK),
        ("SCANLINE", "free  build it", GREEN),
    ]
    w, gap = 0.27, 0.04
    total = 3 * w + 2 * gap
    x0 = (1 - total) / 2
    for i, (name, sub, col) in enumerate(doors):
        x = x0 + i * (w + gap)
        box = FancyBboxPatch((x, 0.13), w, 0.26, boxstyle="round,pad=0.012,rounding_size=0.02",
                             linewidth=2, edgecolor=col, facecolor=PANEL)
        ax.add_patch(box)
        ax.text(x + w / 2, 0.305, name, color=col, fontsize=14, fontweight="bold",
                family=MONO, ha="center", va="center")
        ax.text(x + w / 2, 0.21, sub, color=INK, fontsize=11, family=MONO,
                ha="center", va="center")

    ax.text(0.5, 0.05, "momentum phinance   ·   built on TradingView data", color=MUTE,
            fontsize=11, family=MONO, ha="center", va="center")
    fig.savefig(OUT / "hero_banner.png", facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


def three_doors():
    fig, ax = plt.subplots(figsize=(12, 7), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    _frame(ax)

    ax.text(0.5, 0.95, "PICK YOUR DOOR", color=INK, fontsize=24,
            fontweight="bold", family=MONO, ha="center", va="center")

    cols = [
        ("TRADERDADDY PRO", BLUE, "traderdaddy.pro", "subscription", "serious traders",
         ["full screener stack", "options flow + GEX", "live lessons + signals",
          "the whole cockpit"]),
        ("TRADER LADY", PINK, "traderlady.pro", "$7.99 / month", "do not want to build",
         ["AI chat analyst", "reads flow in English", "gamma walls, dealers",
          "just ask, get an answer"]),
        ("SCANLINE", GREEN, "github / free", "$0  MIT licensed", "build it yourself",
         ["quant screener", "factor scoring + z-scores", "47 scans, six markets",
          "ships its own agent server"]),
    ]
    w, gap = 0.29, 0.025
    total = 3 * w + 2 * gap
    x0 = (1 - total) / 2
    for i, (name, col, url, price, who, feats) in enumerate(cols):
        x = x0 + i * (w + gap)
        box = FancyBboxPatch((x, 0.08), w, 0.78, boxstyle="round,pad=0.012,rounding_size=0.02",
                             linewidth=2, edgecolor=col, facecolor=PANEL)
        ax.add_patch(box)
        cx = x + w / 2
        ax.text(cx, 0.80, name, color=col, fontsize=14, fontweight="bold",
                family=MONO, ha="center", va="center")
        ax.text(cx, 0.745, url, color=MUTE, fontsize=10, family=MONO,
                ha="center", va="center")
        ax.text(cx, 0.685, price, color=INK, fontsize=13, fontweight="bold",
                family=MONO, ha="center", va="center")
        ax.text(cx, 0.625, "for: " + who, color=col, fontsize=10.5, family=MONO,
                ha="center", va="center", style="italic")
        for j, f in enumerate(feats):
            ax.text(x + 0.018, 0.55 - j * 0.075, "> " + f, color=INK, fontsize=10.5,
                    family=MONO, ha="left", va="center")

    fig.savefig(OUT / "infographic_1.png", facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


def what_each_sees():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=100)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    _frame(ax)

    ax.text(0.5, 0.94, "DIFFERENT SHAPES, NOT BETTER AND WORSE", color=INK,
            fontsize=20, fontweight="bold", family=MONO, ha="center", va="center")

    panels = [
        ("SCANLINE  (free)", GREEN,
         [("price / volume", True), ("technicals", True), ("fundamentals", True),
          ("factor scoring, whole market", True), ("z-score, percentile rank", True),
          ("options flow / sweeps", False), ("GEX, gamma walls", False),
          ("dealer positioning", False)]),
        ("TRADER LADY  ($7.99)", PINK,
         [("options flow / sweeps", True), ("GEX, gamma walls", True),
          ("dealer positioning", True), ("plain-English read", True),
          ("earnings setups", True), ("whole-market factor rank", False),
          ("computed columns you define", False), ("runs offline / self-host", False)]),
    ]
    w, gap = 0.43, 0.06
    total = 2 * w + gap
    x0 = (1 - total) / 2
    for i, (title, col, rows) in enumerate(panels):
        x = x0 + i * (w + gap)
        box = FancyBboxPatch((x, 0.08), w, 0.76, boxstyle="round,pad=0.012,rounding_size=0.02",
                             linewidth=2, edgecolor=col, facecolor=PANEL)
        ax.add_patch(box)
        ax.text(x + w / 2, 0.78, title, color=col, fontsize=14, fontweight="bold",
                family=MONO, ha="center", va="center")
        for j, (label, has) in enumerate(rows):
            y = 0.68 - j * 0.075
            mark = "+" if has else "-"
            mc = GREEN if has else "#e53935"
            ax.text(x + 0.03, y, mark, color=mc, fontsize=14, fontweight="bold",
                    family=MONO, ha="left", va="center")
            tc = INK if has else MUTE
            ax.text(x + 0.075, y, label, color=tc, fontsize=11, family=MONO,
                    ha="left", va="center")

    ax.text(0.5, 0.035, "she cannot do everything scanline does. scanline cannot do what she does.",
            color=GOLD, fontsize=11.5, family=MONO, ha="center", va="center", style="italic")
    fig.savefig(OUT / "infographic_2.png", facecolor=BG, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


if __name__ == "__main__":
    hero()
    three_doors()
    what_each_sees()
    print("wrote:", *[p.name for p in sorted(OUT.glob("*.png"))])
