#!/usr/bin/env python3
"""Dark-theme Bloomberg-style infographics for the "SpaceX ate the sector" article.

Run with the matplotlib venv:
    /tmp/vmpl/bin/python docs/articles/spacex-half-the-sector/make_images.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Treat '$' as a literal character, not a mathtext delimiter, so dollar
# figures in captions render correctly.
matplotlib.rcParams["text.parse_math"] = False

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


# -- 1. HERO BANNER -----------------------------------------------------------
def hero():
    fig, ax = plt.subplots(figsize=(12, 6.3), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    _frame(ax)

    ax.text(0.5, 0.83, "SPACEX ATE THE SECTOR", fontsize=42, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.715, "ONE 4-DAY-OLD STOCK NOW EQUALS EVERY OTHER LISTED PLANE & MISSILE MAKER COMBINED",
            fontsize=12, color=GOLD, ha="center", fontweight="bold", fontfamily=MONO)

    tiles = [
        ("SPCX MKT CAP", "$2.5T", GOLD),
        ("= A&D FIRMS", "94", BLUE),
        ("FY25 NET", "-$4.9B", RED),
        ("TIME ELAPSED", "4 DAYS", GREEN),
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

    ax.text(0.5, 0.155, "HALF THE SECTOR BY MARKET CAP. A ROUNDING ERROR BY PROFIT.",
            fontsize=12.5, color=WHITE, ha="center", style="italic", fontfamily=MONO)
    ax.text(0.5, 0.065, "MOMENTUM PHINANCE  //  DATA AS OF 16 JUN 2026  //  NOT FINANCIAL ADVICE",
            fontsize=10, color=RED, ha="center", fontweight="bold", fontfamily=MONO)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/hero_banner.png", dpi=200, facecolor=BG)
    plt.close()
    print("hero_banner.png")


# -- 2. THE TREEMAP: SPACEX = THE REST ----------------------------------------
def treemap():
    fig, ax = plt.subplots(figsize=(12, 7.2), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_facecolor(BG)
    ax.axis("off")

    ax.text(0.5, 0.955, "ONE BLOCK = THE OTHER 94 BLOCKS", fontsize=27, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.905, "LISTED AEROSPACE & DEFENSE BY MARKET CAP  //  SOURCE: companiesmarketcap.com",
            fontsize=10.5, color=GREY, ha="center", fontfamily=MONO)

    # Left: the SpaceX monolith
    ax.add_patch(patches.FancyBboxPatch((0.04, 0.07), 0.43, 0.79,
                 boxstyle="round,pad=0.004", linewidth=2.4,
                 edgecolor=GOLD, facecolor="#1a1206"))
    ax.text(0.255, 0.58, "SPACEX", fontsize=40, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.255, 0.46, "$2.5T", fontsize=46, color=GOLD,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.255, 0.37, "ONE COMPANY", fontsize=12, color=GREY,
            ha="center", fontfamily=MONO)

    # Right: the rest of the sector, sized roughly to cap
    # (label, $B). Big names get their own tile; the long tail is bucketed.
    names = [
        ("GE AERO", 300), ("RTX", 247), ("BOEING", 190), ("SAFRAN", 163),
        ("AIRBUS", 160), ("ROLLS", 151), ("HONEYWELL", 144), ("LMT", 122),
        ("HOWMET", 100), ("NORTHROP", 77), ("BAE", 73), ("TRANSDIGM", 71),
        ("+ ~82 MORE", 702),
    ]
    rx, ry, rw, rh = 0.52, 0.07, 0.44, 0.79
    total = sum(v for _, v in names)
    # simple shelf-stacking treemap
    x = rx; y = ry; row_h = 0.0; remaining = total
    area = rw * rh
    cursor_y = ry
    # Build rows greedily by area share
    idx = 0
    rows = [names[0:3], names[3:6], names[6:9], names[9:13]]
    row_fracs = []
    for r in rows:
        row_fracs.append(sum(v for _, v in r))
    grand = sum(row_fracs)
    yy = ry + rh
    for r, frac in zip(rows, row_fracs):
        h = rh * (frac / grand)
        yy -= h
        rsum = sum(v for _, v in r)
        xx = rx
        for nm, v in r:
            w = rw * (v / rsum)
            tail = nm.startswith("+")
            ax.add_patch(patches.Rectangle((xx + 0.004, yy + 0.004), w - 0.008, h - 0.008,
                         linewidth=1.2, edgecolor="#30363d",
                         facecolor="#0e2a17" if not tail else "#11202e"))
            fs = 13 if (w > 0.13 and h > 0.13) else (10 if w > 0.085 else 7.5)
            ax.text(xx + w / 2, yy + h / 2 + (0.018 if h > 0.1 else 0.0), nm,
                    fontsize=fs, color=WHITE, ha="center", va="center",
                    fontweight="bold", fontfamily=MONO)
            if h > 0.1:
                ax.text(xx + w / 2, yy + h / 2 - 0.03, f"${v}B",
                        fontsize=max(fs - 3, 7), color=GREEN if not tail else BLUE,
                        ha="center", va="center", fontfamily=MONO)
            xx += w
    ax.text(0.74, 0.025, "94 FIRMS  //  SUMMED:  $2.5T", fontsize=13, color=GREEN,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.255, 0.025, "=", fontsize=13, color=WHITE, ha="center", fontfamily=MONO)
    # big equals between the two halves
    ax.text(0.495, 0.46, "=", fontsize=60, color=WHITE, ha="center", va="center",
            fontweight="bold", fontfamily=MONO)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/sector_treemap.png", dpi=200, facecolor=BG)
    plt.close()
    print("sector_treemap.png")


# -- 3. CAP VS SUBSTANCE ------------------------------------------------------
def cap_vs_substance():
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    _frame(ax)

    ax.text(0.5, 0.93, "HALF THE CAP. 3% OF THE REVENUE. NONE OF THE PROFIT.",
            fontsize=20.5, color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.87, "SPACEX (GOLD) vs THE OTHER 94 A&D FIRMS (GREEN), FY2025",
            fontsize=11.5, color=GREY, ha="center", fontfamily=MONO)

    # Three rows: market cap, revenue, net profit
    rows = [
        ("MARKET CAP", 50.0, 50.0, "$2.5T", "$2.5T", False),
        ("REVENUE", 3.2, 96.8, "$18B", "~$540B", False),
        ("NET PROFIT", None, None, "-$4.9B", ">$35B", True),
    ]
    bx, bw = 0.06, 0.88
    ys = [0.66, 0.46, 0.26]
    bh = 0.13
    for (label, sx, rest, sxv, restv, loss), y in zip(rows, ys):
        ax.text(bx, y + bh + 0.035, label, fontsize=13, color=WHITE,
                fontweight="bold", fontfamily=MONO, va="center")
        if not loss:
            # stacked proportional bar
            ax.add_patch(patches.Rectangle((bx, y), bw * sx / 100, bh,
                         facecolor=GOLD, edgecolor=BG, lw=1))
            ax.add_patch(patches.Rectangle((bx + bw * sx / 100, y), bw * rest / 100, bh,
                         facecolor="#0e2a17", edgecolor=GREEN, lw=1.4))
            # labels
            if sx > 8:
                ax.text(bx + bw * sx / 200, y + bh / 2, f"SPACEX {sxv}",
                        fontsize=11, color="#0a0a0a", ha="center", va="center",
                        fontweight="bold", fontfamily=MONO)
            else:
                ax.text(bx + bw * sx / 100 + 0.012, y + bh / 2, f"SPACEX {sxv} ({sx:.1f}%)",
                        fontsize=10.5, color=GOLD, ha="left", va="center",
                        fontweight="bold", fontfamily=MONO)
            ax.text(bx + bw * sx / 100 + bw * rest / 200, y + bh / 2,
                    f"SECTOR {restv}", fontsize=11, color=GREEN, ha="center", va="center",
                    fontweight="bold", fontfamily=MONO)
        else:
            # profit row: SpaceX in the red, sector deep green
            ax.add_patch(patches.Rectangle((bx, y), bw * 0.30, bh,
                         facecolor="#2a0e0e", edgecolor=RED, lw=1.6))
            ax.text(bx + bw * 0.15, y + bh / 2, f"SPACEX  {sxv}",
                    fontsize=12, color=RED, ha="center", va="center",
                    fontweight="bold", fontfamily=MONO)
            ax.add_patch(patches.Rectangle((bx + bw * 0.33, y), bw * 0.67, bh,
                         facecolor="#0e2a17", edgecolor=GREEN, lw=1.6))
            ax.text(bx + bw * 0.665, y + bh / 2, f"SECTOR  {restv} (and climbing)",
                    fontsize=12, color=GREEN, ha="center", va="center",
                    fontweight="bold", fontfamily=MONO)

    ax.text(0.5, 0.085,
            "SpaceX is half the sector by what the market will PAY, and a sliver of it by what the businesses EARN.",
            fontsize=11.5, color=GOLD, ha="center", style="italic", fontfamily=MONO)
    ax.text(0.5, 0.035,
            "Sector revenue ~$540B per industry trackers. Combined net >$35B from just the top 8 names. SpaceX figures per S-1 (FY25).",
            fontsize=8.5, color=GREY, ha="center", fontfamily=MONO)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/cap_vs_substance.png", dpi=200, facecolor=BG)
    plt.close()
    print("cap_vs_substance.png")


# -- 4. WHAT'S ACTUALLY IN THE $2.5T ------------------------------------------
def whats_inside():
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor=BG)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    _frame(ax)

    ax.text(0.5, 0.93, "WHAT YOU'RE ACTUALLY BUYING AT $2.5T", fontsize=23, color=WHITE,
            ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.875, "IT ISN'T A DEFENSE COMPANY. IT'S A SATELLITE-INTERNET CASH MACHINE BOLTED TO A MONEY-LOSING MOONSHOT.",
            fontsize=10.3, color=GOLD, ha="center", fontweight="bold", fontfamily=MONO)

    cards = [
        (GREEN, "STARLINK", "THE CASH MACHINE",
         ["$11.4B revenue", "+$4.4B operating profit", "Satellite internet,", "basically a telco"]),
        (BLUE, "ROCKETS", "THE PROFITABLE PART",
         ["Falcon / Starship", "Launch + contracts", "Profitable at the", "operating line"]),
        (RED, "THE AI SEGMENT", "THE COSTUME",
         ["-$6.35B operating loss", "All by itself", "The moonshot wearing", "the brightest colors"]),
    ]
    w = 0.29; gap = 0.025
    total = 3 * w + 2 * gap
    x0 = (1 - total) / 2
    for i, (col, head, sub, bullets) in enumerate(cards):
        x = x0 + i * (w + gap)
        ax.add_patch(patches.FancyBboxPatch((x, 0.30), w, 0.50,
                     boxstyle="round,pad=0.008", linewidth=2,
                     edgecolor=col, facecolor=PANEL))
        ax.add_patch(patches.Rectangle((x, 0.735), w, 0.065, color=col, alpha=0.18))
        ax.text(x + w / 2, 0.755, head, fontsize=15, color=col,
                ha="center", fontweight="bold", fontfamily=MONO)
        ax.text(x + w / 2, 0.685, sub, fontsize=11.5, color=WHITE,
                ha="center", fontweight="bold", fontfamily=MONO)
        for j, b in enumerate(bullets):
            ax.text(x + w / 2, 0.60 - j * 0.062, b, fontsize=10,
                    color=GREY, ha="center", va="center", fontfamily=MONO)

    ax.text(0.5, 0.205, "FY25 TOTAL:  $18B REVENUE  //  NET  -$4.9B  //  FY24 WAS  +$791M",
            fontsize=12.5, color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.5, 0.13, "The rockets and the dishes make money. The thing setting the income statement on fire",
            fontsize=10.5, color=GREY, ha="center", fontfamily=MONO)
    ax.text(0.5, 0.085, "is the part of the pitch wearing the brightest costume.",
            fontsize=10.5, color=GREY, ha="center", fontfamily=MONO)
    ax.text(0.5, 0.03, "Figures per SpaceX S-1, FY2025.", fontsize=8.5, color=GREY,
            ha="center", style="italic", fontfamily=MONO)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(f"{OUT}/whats_inside.png", dpi=200, facecolor=BG)
    plt.close()
    print("whats_inside.png")


if __name__ == "__main__":
    hero()
    treemap()
    cap_vs_substance()
    whats_inside()
    print("done ->", OUT)
