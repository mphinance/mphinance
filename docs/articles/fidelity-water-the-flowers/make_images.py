"""Generate dark-theme Bloomberg-style infographics for the Water the Flowers article."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BG = "#0a0a0a"
PANEL = "#161b22"
WHITE = "#ffffff"
GREY = "#8b949e"
GREEN = "#00ff41"
GOLD = "#f0b400"
RED = "#e53935"
BLUE = "#58a6ff"
MONO = "monospace"
OUT = "docs/articles/fidelity-water-the-flowers"


def base(figsize=(12, 6.3)):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for y in (0.25, 0.5, 0.75):
        ax.axhline(y=y, color=WHITE, alpha=0.02, linestyle="--")
    for x in (0.25, 0.5, 0.75):
        ax.axvline(x=x, color=WHITE, alpha=0.02, linestyle="--")
    return fig, ax


def box(ax, x, y, w, h, color, fill=PANEL, lw=2, alpha=0.95):
    for i in range(1, 4):
        ax.add_patch(patches.Rectangle((x - 0.0015 * i, y - 0.0015 * i),
                     w + 0.003 * i, h + 0.003 * i, linewidth=1,
                     edgecolor=color, facecolor="none", alpha=0.08))
    ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=lw,
                 edgecolor=color, facecolor=fill, alpha=alpha))


# ---------------------------------------------------------------- HERO
fig, ax = base((12, 6.3))
ax.text(0.5, 0.86, "WATER THE FLOWERS", fontsize=44, color=WHITE, ha="center",
        fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.77, "THE PETER LYNCH RULE FOR LETTING WINNERS RUN", fontsize=15,
        color=GREEN, ha="center", fontweight="bold", fontfamily=MONO, alpha=0.85)

# ARM rising
box(ax, 0.08, 0.30, 0.36, 0.34, BLUE)
ax.text(0.26, 0.565, "ARM", fontsize=34, color=BLUE, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.26, 0.50, "4%  ->  6%", fontsize=22, color=GREEN, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.26, 0.43, "PROMOTED", fontsize=14, color=GREEN, ha="center", fontfamily=MONO)
ax.text(0.26, 0.37, "$628.85", fontsize=18, color=WHITE, ha="center", fontfamily=MONO)

# swap arrows
ax.text(0.5, 0.50, "<-->", fontsize=40, color=GOLD, ha="center", va="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.40, "SWITCHING\nSPOTS", fontsize=12, color=GOLD, ha="center", va="center", fontfamily=MONO)

# TER fading
box(ax, 0.56, 0.30, 0.36, 0.34, RED)
ax.text(0.74, 0.565, "TER", fontsize=34, color=RED, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.74, 0.50, "6%  ->  4%", fontsize=22, color=RED, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.74, 0.43, "DEMOTED", fontsize=14, color=RED, ha="center", fontfamily=MONO)
ax.text(0.74, 0.37, "$625.09", fontsize=18, color=WHITE, ha="center", fontfamily=MONO)

ax.text(0.5, 0.18, "WHEN THE 4% OVERTAKES THE 6%, IT EARNS THE BIGGER SEAT.", fontsize=14,
        color=WHITE, ha="center", fontfamily=MONO)
ax.text(0.5, 0.09, "MOMENTUM PHINANCE  |  THE PHUND  |  NOT FINANCIAL ADVICE", fontsize=11,
        color=GREY, ha="center", fontfamily=MONO)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig(f"{OUT}/hero_banner.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()


# ---------------------------------------------------------------- CROSSOVER
fig, ax = base((12, 6.6))
ax.text(0.5, 0.92, "THE CROSSOVER", fontsize=34, color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.85, "FIDELITY BASKET  |  CURRENT WEIGHT vs NEW TARGET", fontsize=13,
        color=GREEN, ha="center", fontweight="bold", fontfamily=MONO, alpha=0.85)

# column headers
cols = [("TICKER", 0.14), ("CURRENT WT", 0.40), ("VALUE", 0.62), ("NEW TARGET", 0.85)]
for label, cx in cols:
    ax.text(cx, 0.74, label, fontsize=13, color=GREY, ha="center", fontfamily=MONO, fontweight="bold")
ax.axhline(y=0.70, xmin=0.06, xmax=0.94, color=GREY, alpha=0.4, linewidth=1)

rows = [
    ("ARM", BLUE, "5.4%", "$628.85", "6.0%", GREEN, "+", 0.55),
    ("TER", RED,  "5.3%", "$625.09", "4.0%", RED,   "-", 0.34),
]
for tkr, tcol, cur, val, tgt, tgtcol, sign, y in rows:
    box(ax, 0.06, y, 0.88, 0.15, tcol, alpha=0.25)
    ax.text(0.14, y + 0.075, tkr, fontsize=26, color=tcol, ha="center", va="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.40, y + 0.075, cur, fontsize=24, color=WHITE, ha="center", va="center", fontweight="bold", fontfamily=MONO)
    ax.text(0.62, y + 0.075, val, fontsize=20, color=WHITE, ha="center", va="center", fontfamily=MONO)
    ax.text(0.85, y + 0.075, tgt, fontsize=24, color=tgtcol, ha="center", va="center", fontweight="bold", fontfamily=MONO)

ax.text(0.5, 0.18, "ARM STARTED AT 4%. TER STARTED AT 6%.", fontsize=15, color=WHITE, ha="center", fontfamily=MONO)
ax.text(0.5, 0.115, "THE 4% CLIMBED PAST THE 6%. SO THE SEATS SWAP.", fontsize=15,
        color=GOLD, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.04, "DELTA: $3.76  |  THE MOMENT LEADERSHIP CHANGES HANDS", fontsize=11,
        color=GREY, ha="center", fontfamily=MONO)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig(f"{OUT}/the_crossover.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()


# ---------------------------------------------------------------- THE RULE
fig, ax = base((12, 6.3))
ax.text(0.5, 0.91, "THE RULE", fontsize=34, color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.84, "POSITION SIZING FOLLOWS PERFORMANCE", fontsize=13,
        color=GREEN, ha="center", fontweight="bold", fontfamily=MONO, alpha=0.85)

box(ax, 0.08, 0.50, 0.84, 0.26, GREEN)
ax.text(0.5, 0.68, "WHEN A SMALLER TARGET OVERTAKES A LARGER ONE,", fontsize=17,
        color=WHITE, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.61, "SWAP THEIR TARGET WEIGHTS.", fontsize=17, color=GREEN, ha="center", fontweight="bold", fontfamily=MONO)
ax.text(0.5, 0.545, "A 4% THAT PASSES A 6% BECOMES THE NEW 6%.  A 2% THAT PASSES A 3% BECOMES THE 3%.",
        fontsize=11.5, color=GREY, ha="center", fontfamily=MONO)

# do / don't
box(ax, 0.08, 0.16, 0.40, 0.27, GREEN, alpha=0.18)
ax.text(0.28, 0.385, "WATER THE FLOWERS", fontsize=15, color=GREEN, ha="center", fontweight="bold", fontfamily=MONO)
for i, line in enumerate(["Promote the winner", "Reward strength with size", "Let the leaderboard decide", "Cap stays in place"]):
    ax.text(0.11, 0.33 - i * 0.045, "+ " + line, fontsize=12.5, color=WHITE, ha="left", fontfamily=MONO)

box(ax, 0.52, 0.16, 0.40, 0.27, RED, alpha=0.18)
ax.text(0.72, 0.385, "WATER THE WEEDS", fontsize=15, color=RED, ha="center", fontweight="bold", fontfamily=MONO)
for i, line in enumerate(["Trim every winner to target", "Average down the laggard", "Cap your best ideas", "The default advice"]):
    ax.text(0.55, 0.33 - i * 0.045, "x " + line, fontsize=12.5, color=GREY, ha="left", fontfamily=MONO)

ax.text(0.5, 0.06, "PETER LYNCH, 1989: \"CUTTING THE FLOWERS AND WATERING THE WEEDS.\"", fontsize=11,
        color=GOLD, ha="center", fontfamily=MONO)
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
plt.savefig(f"{OUT}/the_rule.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()

print("Generated hero_banner.png, the_crossover.png, the_rule.png")
