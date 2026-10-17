"""Generate the three dark-theme infographics for the Position Doctor article.

Same house style as gen_institutional_infographics.py. Saves PNGs next to the README.
Every number is computed or copied from a cited source in the comments; nothing is drawn freehand.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["text.parse_math"] = False  # literal $ signs, no mathtext

BG = "#0a0a0a"
PANEL = "#15171c"
WHITE = "#e8e8e8"
DIM = "#8b949e"
GREEN = "#00ff41"
GOLD = "#f0b400"
RED = "#e53935"
MONO = "monospace"

OUT = "docs/articles/underwater-puts-position-doctor"


def new_ax(w, h):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    for gx in range(1, int(w)):
        ax.axvline(gx, color="#ffffff", alpha=0.02, lw=0.6)
    for gy in range(1, int(h)):
        ax.axhline(gy, color="#ffffff", alpha=0.02, lw=0.6)
    return fig, ax


def header(ax, w, h, title, sub):
    ax.text(0.4, h - 0.45, "M O M E N T U M   P H I N A N C E", color=GOLD,
            fontsize=11, family=MONO, fontweight="bold", va="center")
    ax.text(0.4, h - 1.0, title, color=WHITE, fontsize=24, family=MONO,
            fontweight="bold", va="center")
    ax.text(0.4, h - 1.5, sub, color=DIM, fontsize=12, family=MONO, va="center")
    ax.plot([0.4, w - 0.4], [h - 1.82, h - 1.82], color=GREEN, lw=1.5)


def save(fig, name):
    path = f"{OUT}/{name}"
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)
    print(f"saved {path}")


# ------------------------------------------------------------- WEEK
# Source: TDPro get_sector_flow window=5d, pulled 2026-10-17 (Fri 10/9 close -> Fri 10/16 close).
# SPY from TDPro agent chart-data: 778.57 -> 763.25. VIX level from get_sector_flow macro.vixLast.
WEEK = [
    ("SMH  semis", -10.53),
    ("CIBR cyber", -10.16),
    ("XLK  tech", -7.70),
    ("IGV  software", -7.39),
    ("SPY  S&P 500", -1.97),
    ("XLV  healthcare", 3.45),
    ("XLE  energy", 4.86),
    ("XLP  staples", 5.02),
]


def week():
    w, h = 12.0, 7.0
    fig, ax = new_ax(w, h)
    header(ax, w, h, "A TECH BEATING, NOT A MARKET CRASH",
           "5-day change, Fri 10/9 close to Fri 10/16 close")
    zero_x = 8.0
    scale = 0.30  # inches per percent
    top = h - 2.35
    row = 0.5
    for i, (label, pct) in enumerate(WEEK):
        y = top - i * row
        color = RED if pct < -5 else (GOLD if pct < 0 else GREEN)
        ax.text(0.5, y, label, color=WHITE, fontsize=14, family=MONO, va="center")
        ax.barh(y, pct * scale, left=zero_x, height=0.34, color=color, alpha=0.9)
        tx = zero_x + pct * scale + (0.12 if pct > 0 else -0.12)
        ax.text(tx, y, f"{pct:+.1f}%", color=color, fontsize=14, family=MONO,
                fontweight="bold", va="center", ha="left" if pct > 0 else "right")
    ax.plot([zero_x, zero_x], [top - 7 * row - 0.35, top + 0.35], color=DIM, lw=1)
    ax.text(0.5, 0.45, "VIX  19.99", color=GOLD, fontsize=18, family=MONO,
            fontweight="bold", va="center")
    ax.text(3.6, 0.45, "fear got priced in the exact sector you own",
            color=DIM, fontsize=13, family=MONO, va="center")
    ax.text(w - 0.4, 0.12, "source: TraderMatrix sector flow, 5d", color=DIM,
            fontsize=9, family=MONO, ha="right")
    save(fig, "week.png")


# --------------------------------------------------------- RECOVERY
# 100 sh bought at $62.00, stock at $53.00.
#   do nothing:        62.00
#   protective put:    62.00 + 1.80 premium = 63.80
#   call at basis:     62.00 - 0.60 premium = 61.40
#   1x2 repair (53/58, even money): 2 x (S - 53) x 100 = 900  ->  S = 57.50; +$100 at 58
#   sell + CSP $50 for 1.20: new basis if assigned 50.00 - 1.20 = 48.80
RECOVERY = [
    ("PROTECTIVE PUT", 63.80, RED, "+$1.80 harder: you paid for the floor"),
    ("DO NOTHING", 62.00, DIM, "your basis"),
    ("CALL AT BASIS", 61.40, GOLD, "-$0.60 easier, assignment at break-even"),
    ("1x2 REPAIR", 57.50, GREEN, "whole at $57.50, +$100 at $58, capped there"),
    ("SELL + WHEEL", 48.80, GREEN, "new basis if the $50 put is assigned"),
]


def recovery():
    w, h = 12.0, 7.0
    fig, ax = new_ax(w, h)
    header(ax, w, h, "THE PRICE YOU NEED TO GET BACK TO",
           "100 shares bought at $62.00, stock at $53.00, down $900")
    x0 = 4.2
    y0, y1 = 0.75, h - 2.4
    slots = [y1 - i * (y1 - y0) / 5 for i in range(6)]  # 5 rungs + spot line
    ax.plot([x0, x0], [y0 - 0.1, y1 + 0.2], color=DIM, lw=1)
    spot = (slots[3] + slots[5]) / 2 - 0.05
    for i, (label, price, color, note) in enumerate(RECOVERY):
        y = slots[i] if i < 4 else slots[5]
        ax.plot([x0, x0 + 0.5], [y, y], color=color, lw=3)
        ax.text(x0 + 0.7, y, f"${price:.2f}", color=color, fontsize=17, family=MONO,
                fontweight="bold", va="center")
        ax.text(x0 + 2.4, y + 0.14, label, color=WHITE, fontsize=12, family=MONO,
                fontweight="bold", va="center")
        ax.text(x0 + 2.4, y - 0.17, note, color=DIM, fontsize=10, family=MONO,
                va="center")
    ax.plot([x0 - 0.2, w - 0.4], [spot, spot], color=WHITE, lw=1, ls=":")
    ax.text(x0 - 0.3, spot, "SPOT $53.00", color=WHITE, fontsize=11, family=MONO,
            ha="right", va="center")
    ax.text(0.5, y1 - 0.2, "lower is\neasier", color=GREEN, fontsize=12,
            family=MONO, va="top")
    ax.text(0.5, y0 + 0.2, "the put is the only\nline ABOVE your basis", color=RED,
            fontsize=11, family=MONO, va="bottom")
    save(fig, "recovery.png")


# ----------------------------------------------------------- REPAIR
# 100 sh at $62 basis, spot $53. Buy 1 x $53 call, sell 2 x $58 calls, even money.
def repair_rows():
    rows = []
    for s in (50, 53, 55, 58, 62):
        shares = (s - 53) * 100
        long_c = max(s - 53, 0) * 100
        short_c = -2 * max(s - 58, 0) * 100
        total = shares + long_c + short_c
        rows.append((s, shares, long_c, short_c, total, total - 900))
    return rows


def money(v):
    return f"{'+' if v > 0 else ('-' if v < 0 else ' ')}${abs(v):,.0f}"


def repair():
    rows = repair_rows()
    # arithmetic guard: the row the first draft got wrong
    assert rows[3] == (58, 500, 500, 0, 1000, 100), rows[3]
    assert rows[4] == (62, 900, 900, -800, 1000, 100), rows[4]
    w, h = 12.0, 7.0
    fig, ax = new_ax(w, h)
    header(ax, w, h, "THE 1x2 REPAIR AT EXPIRATION",
           "100 sh @ $62, stock $53. Buy 1 x $53 call, sell 2 x $58 calls, ~even money")
    cols = ["STOCK", "SHARES", "LONG $53C", "2x SHORT $58C", "TOTAL", "NET vs -$900"]
    xs = [0.6, 2.3, 4.2, 6.2, 8.4, 10.1]
    yh = h - 2.4
    for x, c in zip(xs, cols):
        ax.text(x, yh, c, color=GOLD, fontsize=12, family=MONO, fontweight="bold",
                va="center")
    ax.plot([0.4, w - 0.4], [yh - 0.3, yh - 0.3], color=DIM, lw=0.8)
    for i, (s, sh, lc, sc, tot, net) in enumerate(rows):
        y = yh - 0.8 - i * 0.62
        if s == 58:
            ax.add_patch(plt.Rectangle((0.4, y - 0.3), w - 0.8, 0.6, color=GREEN,
                                       alpha=0.08))
        vals = [f"${s}", money(sh), money(lc), money(sc), money(tot), money(net)]
        for j, (x, v) in enumerate(zip(xs, vals)):
            color = WHITE
            if j == 5:
                color = GREEN if net > 0 else RED
            elif j == 3 and sc < 0:
                color = RED
            ax.text(x, y, v, color=color, fontsize=15, family=MONO,
                    fontweight="bold" if j in (0, 5) else "normal", va="center")
    ax.text(0.6, 0.65, "2-for-1 between $53 and $58. Whole at $57.50. Capped at $58.",
            color=GREEN, fontsize=13, family=MONO, va="center")
    ax.text(0.6, 0.25, "Below $53 it is the same as doing nothing. Not a hedge.",
            color=RED, fontsize=12, family=MONO, va="center")
    save(fig, "repair.png")


# ------------------------------------------------------- LIVE NAMES
# Source: data/doctor_2026-10-17.json, the production Position Doctor
# (diagnosePositionForSymbol) run 2026-10-17 off the 10/16 closing chain, 100 shares.
# Bars: data/bars_*.json from the TraderMatrix agent chart-data endpoint.
import json
import os

DATA = f"{OUT}/data"
LIVE = [
    # (symbol, basis, label)
    ("NBIS", 242.81, "bought 10/2"),
    ("NBIS", 221.07, "bought 10/9"),
    ("ASTS", 58.45, "bought 10/2"),
    ("ASTS", 50.97, "bought 10/9"),
]
REPAIR = {"NBIS": (165, 200), "ASTS": (40, 45)}  # long strike, short strike (Dec 18)


def charts():
    w, h = 12.0, 7.0
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    ax0 = fig.add_axes([0, 0, 1, 1]); ax0.axis("off"); ax0.set_xlim(0, w); ax0.set_ylim(0, h)
    header(ax0, w, h, "TWO ENTRY DATES, ONE CEILING",
           "Daily candles to Fri 10/16. Red = bought 10/2. Gold = bought 10/9. Green = 1x2 cap")
    for i, sym in enumerate(("NBIS", "ASTS")):
        bars = json.load(open(f"{DATA}/bars_{sym}.json"))[-25:]
        ax = fig.add_axes([0.06 + i * 0.49, 0.08, 0.42, 0.58], facecolor=BG)
        xs = range(len(bars))
        for x, b in zip(xs, bars):
            up = b["close"] >= b["open"]
            col = GREEN if up else RED
            ax.plot([x, x], [b["low"], b["high"]], color=col, lw=0.8, alpha=0.8)
            ax.add_patch(plt.Rectangle((x - 0.3, min(b["open"], b["close"])), 0.6,
                                       max(abs(b["close"] - b["open"]), 0.01), color=col, alpha=0.85))
        bases = [bb for (s_, bb, _) in LIVE if s_ == sym]
        lo_k, cap = REPAIR[sym]
        for bb, col in zip(bases, (RED, GOLD)):
            ax.axhline(bb, color=col, lw=1.2, ls="--")
            ax.text(len(bars) - 0.5, bb, f" ${bb:.2f}", color=col, fontsize=10, family=MONO, va="center")
        ax.axhline(cap, color=GREEN, lw=1.2, ls=":")
        ax.text(len(bars) - 0.5, cap, f" cap ${cap}", color=GREEN, fontsize=10, family=MONO, va="center")
        last = bars[-1]["close"]
        ax.text(0, ax.get_ylim()[0], "", color=WHITE)
        ax.set_title(f"${sym}  last ${last:.2f}", color=WHITE, family=MONO, fontsize=15,
                     fontweight="bold", loc="left")
        ax.tick_params(colors=DIM, labelsize=9)
        ax.set_xticks([0, len(bars) - 1])
        ax.set_xticklabels([bars[0]["date"][5:], bars[-1]["date"][5:]], family=MONO)
        for sp in ax.spines.values():
            sp.set_color("#2a2d33")
        ax.set_xlim(-1, len(bars) + 3)
    save(fig, "live_charts.png")


def money2(v):
    return f"${v:,.2f}"


def live_grid():
    D = json.load(open(f"{DATA}/doctor_2026-10-17.json"))
    w, h = 12.0, 7.0
    fig, ax = new_ax(w, h)
    header(ax, w, h, "RECOVERY PRICE, STRUCTURE BY STRUCTURE",
           "Production Position Doctor, 100 shares, Fri 10/16 closing chain. Lower is easier")
    cols = [f"{s} {lab}" for (s, _, lab) in LIVE]
    xs = [3.6, 5.75, 7.9, 10.05]
    yh = h - 2.35
    for x, (sym, basis, lab) in zip(xs, LIVE):
        ax.text(x, yh + 0.12, f"{sym}", color=GOLD, fontsize=13, family=MONO, fontweight="bold", va="center")
        ax.text(x, yh - 0.2, f"{lab} ${basis:.2f}", color=DIM, fontsize=9, family=MONO, va="center")
    ax.plot([0.4, w - 0.4], [yh - 0.45, yh - 0.45], color=DIM, lw=0.8)
    rows = [("DO NOTHING", None), ("PROTECTIVE PUT", "protective_put"),
            ("30-DELTA CALL", "covered_call"), ("CALL AT BASIS", "covered_call_at_basis"),
            ("1x2 REPAIR", "repair_spread"), ("COLLAR", "collar")]
    for i, (name, kind) in enumerate(rows):
        y = yh - 0.95 - i * 0.56
        ax.text(0.5, y, name, color=WHITE, fontsize=12, family=MONO, fontweight="bold", va="center")
        for x, (sym, basis, _) in zip(xs, LIVE):
            d = D[f"{sym}:{basis}"]
            if kind is None:
                rec, col = d["doNothing"]["recoveryPrice"], DIM
            else:
                c = next(c for c in d["candidates"] if c["kind"] == kind)
                rec = c["recoveryPrice"]
                if rec is None:
                    col = RED
                elif rec > basis:
                    col = RED
                elif rec < basis - 0.005:
                    col = GREEN
                else:
                    col = DIM
            txt = "CAN'T" if rec is None else money2(rec)
            ax.text(x, y, txt, color=col, fontsize=14, family=MONO, fontweight="bold", va="center")
    ax.text(0.5, 0.25, "CAN'T = the structure's cap sits under your basis. It shrinks the hole, it cannot close it.",
            color=DIM, fontsize=11, family=MONO, va="center")
    save(fig, "live_grid.png")


if __name__ == "__main__":
    week()
    recovery()
    repair()
    charts()
    live_grid()
