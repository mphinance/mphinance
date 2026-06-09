#!/usr/bin/env python3
"""AMZN-into-CPI technical scan + charts. Dark Bloomberg-terminal aesthetic.
Computes EMAs/SMAs/RSI/MACD/ADX/ATR/channel from raw IBKR daily bars in data.json,
prints the scorecard, and renders hero + scorecard + daily chart + intraday chart."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).parent
D = json.loads((HERE / "data.json").read_text())

BG = "#0d1117"; PANEL = "#161b22"; GRID = "#21262d"
GREEN = "#00ff41"; GOLD = "#f0b400"; RED = "#e53935"; TXT = "#c9d1d9"; MUTE = "#6e7681"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "font.family": "monospace", "text.color": TXT, "axes.labelcolor": TXT,
    "xtick.color": TXT, "ytick.color": TXT, "axes.edgecolor": GRID,
})

c = np.array(D["close"], float); h = np.array(D["high"], float); l = np.array(D["low"], float)
o = np.array(D["open"], float); v = np.array(D["volume"], float)
n = len(c)

def ema(x, span):
    a = 2 / (span + 1); out = np.empty_like(x); out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out

def sma(x, w):
    return np.convolve(x, np.ones(w) / w, "valid")

def rsi(x, p=14):
    d = np.diff(x); g = np.where(d > 0, d, 0.0); ls = np.where(d < 0, -d, 0.0)
    ag = g[:p].mean(); al = ls[:p].mean(); out = [np.nan] * p
    for i in range(p, len(d)):
        ag = (ag * (p - 1) + g[i]) / p; al = (al * (p - 1) + ls[i]) / p
        out.append(100 - 100 / (1 + (ag / al if al else np.inf)))
    return np.array(out + [out[-1]])  # pad to len(x)

def wilder(x, p):
    out = np.empty_like(x); out[:p] = np.nan; out[p - 1] = x[:p].mean()
    for i in range(p, len(x)):
        out[i] = (out[i - 1] * (p - 1) + x[i]) / p
    return out

def adx(h, l, c, p=14):
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    up = h[1:] - h[:-1]; dn = l[:-1] - l[1:]
    pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr = wilder(tr, p); pdi = 100 * wilder(pdm, p) / atr; ndi = 100 * wilder(ndm, p) / atr
    dx = 100 * abs(pdi - ndi) / (pdi + ndi)
    adxv = wilder(dx[~np.isnan(dx)], p)
    return adxv[-1], pdi[-1], ndi[-1], atr[-1]

e8, e21, e34, e55, e89 = (ema(c, s) for s in (8, 21, 34, 55, 89))
s20 = sma(c, 20)[-1]; s50 = sma(c, 50)[-1]; s200 = sma(c, 200)[-1] if n >= 200 else np.nan
macd_line = ema(c, 12) - ema(c, 26); signal = ema(macd_line, 9); hist = macd_line - signal
rsi14 = rsi(c)[-1]
adxv, pdi, ndi, atr = adx(h, l, c)
last = c[-1]
avgvol = v[-21:-1].mean()
relvol = D["today_volume"] / avgvol
hi52 = h[-min(n, 252):].max(); lo52 = l[-min(n, 252):].min()

# descending channel via linear regression on last 25 closes
N = 25; xs = np.arange(N); seg = c[-N:]
slope, intercept = np.polyfit(xs, seg, 1)
mid_now = slope * (N - 1) + intercept
resid = seg - (slope * xs + intercept)
upper = mid_now + resid.max(); lower = mid_now + resid.min()
wk_slope_pct = slope * 5 / last * 100

stack_bull = e8[-1] > e21[-1] > e34[-1] > e55[-1] > e89[-1]
LO, RAIL, HI = 237.00, 243.00, 250.43

scan = {
    "last": last, "rsi": rsi14, "adx": adxv, "pdi": pdi, "ndi": ndi, "atr": atr,
    "e8": e8[-1], "e21": e21[-1], "e34": e34[-1], "e55": e55[-1], "e89": e89[-1],
    "s20": s20, "s50": s50, "s200": s200, "macd": macd_line[-1], "signal": signal[-1],
    "hist": hist[-1], "relvol": relvol, "stack_bull": stack_bull,
    "chan_slope_wk_pct": wk_slope_pct, "chan_lower": lower, "chan_upper": upper,
    "hi52": hi52, "lo52": lo52,
}
print("=== AMZN TECHNICAL SCAN (computed from IBKR daily bars) ===")
for k, val in scan.items():
    print(f"{k:>16}: {val}")

# ---------- HERO ----------
def hero():
    fig, ax = plt.subplots(figsize=(12, 6.2)); ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc=BG, zorder=0))
    ax.text(0.5, 0.80, "AMZN", color=TXT, fontsize=58, fontweight="bold", ha="center")
    ax.text(0.5, 0.66, "The One Chart That Calls CPI", color=GOLD, fontsize=22, ha="center")
    ax.text(0.5, 0.50, f"${last:,.2f}", color=RED, fontsize=40, fontweight="bold", ha="center")
    ax.text(0.5, 0.42, "-0.5%  ·  range $237.00 - $250.43  ·  failed-rally reversal", color=MUTE, fontsize=13, ha="center")
    for i, (lab, val, col) in enumerate([
        ("BREAKDOWN", "$237", RED), ("RAIL / PIVOT", "$243", GOLD), ("INVALIDATION", "$250", GREEN)]):
        x = 0.20 + i * 0.30
        ax.text(x, 0.24, lab, color=MUTE, fontsize=11, ha="center")
        ax.text(x, 0.14, val, color=col, fontsize=26, fontweight="bold", ha="center")
    ax.text(0.5, 0.03, "Momentum Phinance  ·  TraderDaddy Pro convergence read  ·  2026-06-09", color=MUTE, fontsize=10, ha="center")
    fig.savefig(HERE / "hero_banner.png", dpi=110, bbox_inches="tight"); plt.close(fig)

# ---------- SCORECARD ----------
def scorecard():
    fig, ax = plt.subplots(figsize=(12, 7)); ax.axis("off")
    ax.add_patch(Rectangle((0.02, 0.02), 0.96, 0.96, transform=ax.transAxes, fc=PANEL, ec=GRID, lw=1.5))
    ax.text(0.5, 0.93, "AMZN  ·  TECHNICAL SCAN", color=TXT, fontsize=22, fontweight="bold", ha="center")
    ax.text(0.5, 0.875, "computed from 123 daily bars, IBKR  ·  bearish lean into CPI", color=MUTE, fontsize=12, ha="center")
    rows = [
        ("EMA STACK (8>21>34>55>89)", "FULL BULLISH" if stack_bull else "BROKEN",
         GREEN if stack_bull else RED, f"8 {e8[-1]:.1f} / 21 {e21[-1]:.1f} / 55 {e55[-1]:.1f}"),
        ("PRICE vs EMA21", f"{(last/e21[-1]-1)*100:+.1f}%", RED if last < e21[-1] else GREEN, f"price {last:.2f} vs {e21[-1]:.2f}"),
        ("RSI (14)", f"{rsi14:.1f}", GOLD if 45 <= rsi14 <= 60 else (RED if rsi14 < 45 else GREEN), "neutral-soft, room either way"),
        ("ADX (14)", f"{adxv:.1f}", GOLD if adxv < 25 else GREEN, f"+DI {pdi:.0f} / -DI {ndi:.0f}  ({'bears' if ndi>pdi else 'bulls'} lead)"),
        ("MACD HIST", f"{hist[-1]:+.2f}", RED if hist[-1] < 0 else GREEN, f"line {macd_line[-1]:+.2f} vs sig {signal[-1]:+.2f}"),
        ("DESCENDING CHANNEL", f"{wk_slope_pct:+.1f}%/wk", RED, f"rail {lower:.0f} - {upper:.0f}, price on floor"),
        ("REL VOLUME", f"{relvol:.2f}x", GOLD, f"{D['today_volume']/1e6:.0f}M vs {avgvol/1e6:.0f}M avg"),
        ("ATR (14)", f"${atr:.2f}", GOLD, f"~{atr/last*100:.1f}% daily range typical"),
    ]
    y = 0.80
    for lab, val, col, note in rows:
        ax.text(0.07, y, lab, color=TXT, fontsize=13, va="center")
        ax.text(0.56, y, val, color=col, fontsize=15, fontweight="bold", va="center")
        ax.text(0.74, y, note, color=MUTE, fontsize=10.5, va="center")
        ax.plot([0.07, 0.93], [y - 0.042, y - 0.042], color=GRID, lw=0.7)
        y -= 0.092
    ax.text(0.5, 0.06, "Verdict: price below the whole EMA stack, -DI over +DI, MACD negative, volume 1.9x. Bearish coil on the floor. CPI decides.",
            color=GOLD, fontsize=11, ha="center", style="italic")
    fig.savefig(HERE / "infographic_1.png", dpi=110, bbox_inches="tight"); plt.close(fig)

# ---------- DAILY CHART: the descending PARALLEL CHANNEL (how the setup was found) ----------
def daily_chart():
    M = 55; idx = np.arange(M)
    co, cc, ch, cl = o[-M:], c[-M:], h[-M:], l[-M:]
    # fit the channel on the down-leg: from the swing high in the window to today
    win_high = int(np.argmax(h[-M:]))                 # peak index within the window
    fx = np.arange(win_high, M)
    sl, ic = np.polyfit(fx, c[-M:][win_high:], 1)     # regression on closes of the down-leg
    mid = sl * fx + ic
    # parallel rails: same slope, offset to the extreme high and low of the leg
    up_off = (h[-M:][win_high:] - (sl * fx + ic)).max()
    dn_off = (l[-M:][win_high:] - (sl * fx + ic)).min()
    proj = np.arange(win_high, M + 6)                 # project the channel a week forward
    midp = sl * proj + ic
    fig, ax = plt.subplots(figsize=(12, 7)); ax.set_facecolor(BG)
    # shade the channel body
    ax.fill_between(proj, midp + dn_off, midp + up_off, color=RED, alpha=0.06, zorder=0)
    # candles
    for i in range(M):
        up = cc[i] >= co[i]; col = GREEN if up else RED
        ax.plot([i, i], [cl[i], ch[i]], color=col, lw=0.9, zorder=3)
        ax.add_patch(Rectangle((i - 0.34, min(co[i], cc[i])), 0.68, max(abs(cc[i] - co[i]), 0.05),
                               fc=col, ec=col, zorder=4))
    # the three parallel lines
    ax.plot(proj, midp + up_off, color=RED, lw=1.6, zorder=5)
    ax.plot(proj, midp + dn_off, color=GREEN, lw=1.6, zorder=5)
    ax.plot(proj, midp, color=MUTE, lw=1.0, ls="--", alpha=0.8, zorder=5)
    ax.text(proj[-1], midp[-1] + up_off, "  upper rail (supply)", color=RED, fontsize=10, va="center")
    ax.text(proj[-1], midp[-1] + dn_off, "  lower rail (demand)", color=GREEN, fontsize=10, va="center")
    ax.text(proj[-1], midp[-1], "  mid", color=MUTE, fontsize=9, va="center")
    # "you are here" marker on the lower rail
    ax.scatter([M - 1], [cc[-1]], s=70, facecolor=GOLD, edgecolor=BG, zorder=6)
    ax.annotate("you are here\n$244, on the floor", xy=(M - 1, cc[-1]), xytext=(M - 16, cc[-1] - 12),
                color=GOLD, fontsize=10, arrowprops=dict(color=GOLD, arrowstyle="->"))
    # CPI trigger levels
    for lvl, col, lab in [(LO, RED, "237 breakdown"), (HI, GREEN, "250 invalidation")]:
        ax.axhline(lvl, color=col, lw=1.0, ls=":", alpha=0.55, zorder=1)
        ax.text(0.3, lvl, f"{lab} ", color=col, fontsize=9, va="bottom")
    ax.set_xlim(-1, M + 11); ax.grid(color=GRID, lw=0.5, axis="y")
    ax.set_title(f"AMZN  ·  daily  ·  descending parallel channel, {sl*5:+.1f}/wk slope  ·  price riding the lower rail into CPI",
                 color=TXT, fontsize=13, loc="left")
    ax.set_xticks([]); ax.tick_params(labelsize=10)
    fig.savefig(HERE / "infographic_2.png", dpi=110, bbox_inches="tight"); plt.close(fig)

# ---------- INTRADAY ----------
def intraday_chart():
    t = D["intraday_5m_time"]; px = np.array(D["intraday_5m_close"], float); idx = np.arange(len(px))
    fig, ax = plt.subplots(figsize=(12, 6)); ax.set_facecolor(BG)
    ax.plot(idx, px, color="#58a6ff", lw=1.6, zorder=3)
    ax.fill_between(idx, px, px.min() - 1, color="#58a6ff", alpha=0.07)
    ax.axhline(247.68, color=MUTE, lw=1, ls=":", alpha=0.8); ax.text(0.3, 247.9, "open 247.68", color=MUTE, fontsize=9)
    ax.scatter([px.argmax()], [px.max()], color=GREEN, zorder=5)
    ax.text(px.argmax() + 0.5, px.max() + 0.1, f"high {px.max():.2f}", color=GREEN, fontsize=9)
    ax.axhline(RAIL, color=GOLD, lw=1.1, ls=":", alpha=0.9); ax.text(len(px) - 12, RAIL + 0.15, "243 rail", color=GOLD, fontsize=9)
    ax.scatter([len(px) - 1], [px[-1]], color=RED, zorder=5)
    ax.text(len(px) - 9, px[-1] - 0.5, f"close {px[-1]:.2f}", color=RED, fontsize=9)
    ax.annotate("237.00 wick\n(between bars)", xy=(22, 243.65), xytext=(30, 240.0),
                color=RED, fontsize=9, arrowprops=dict(color=RED, arrowstyle="->"))
    step = 12
    ax.set_xticks(idx[::step]); ax.set_xticklabels([t[i] for i in idx[::step]], fontsize=9)
    ax.grid(color=GRID, lw=0.5); ax.set_ylabel("price")
    ax.set_title("AMZN  ·  06-09 intraday (5-min)  ·  green open rejected, sold to 237, closed red on the rail",
                 color=TXT, fontsize=13, loc="left")
    fig.savefig(HERE / "infographic_3.png", dpi=110, bbox_inches="tight"); plt.close(fig)

hero(); scorecard(); daily_chart(); intraday_chart()
print("\nwrote: hero_banner.png, infographic_1.png, infographic_2.png, infographic_3.png")
