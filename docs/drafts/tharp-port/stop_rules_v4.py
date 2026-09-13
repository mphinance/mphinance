import json
from datetime import datetime
import numpy as np

BASE = "/home/mph/mphinance/docs/drafts/tharp-port"

post = json.load(open(f"{BASE}/data/raw_bars.json"))["data"]["bars"]
pre = json.load(open(f"{BASE}/data/pre_entry_bars.json"))["data"]["bars"]
spy = json.load(open(f"{BASE}/data/spy_bars.json"))["data"]["bars"]["SPY"]

tickers = sorted(post.keys())
assert sorted(pre.keys()) == tickers, "pre/post ticker sets differ"

def as_series(bar_list):
    bar_list = sorted(bar_list, key=lambda b: b["t"])
    return {
        "dates": [b["t"][:10] for b in bar_list],
        "close": np.array([b["c"] for b in bar_list]),
        "high": np.array([b["h"] for b in bar_list]),
        "low": np.array([b["l"] for b in bar_list]),
    }

post_s = {t: as_series(post[t]) for t in tickers}
pre_s = {t: as_series(pre[t]) for t in tickers}

n_days = len(post_s[tickers[0]]["dates"])
dates = post_s[tickers[0]]["dates"]
for t in tickers:
    assert post_s[t]["dates"] == dates, f"{t} post-entry dates misaligned"
    assert pre_s[t]["dates"][-1] < dates[0], f"{t} pre/post overlap or out of order"

entry_price = {t: post_s[t]["close"][0] for t in tickers}
print(f"Entry date: {dates[0]}, final date: {dates[-1]}, {n_days} sessions")
print(f"Pre-entry coverage per ticker: {len(pre_s[tickers[0]]['dates'])} sessions "
      f"({pre_s[tickers[0]]['dates'][0]} .. {pre_s[tickers[0]]['dates'][-1]})")
for t in tickers:
    if len(pre_s[t]["dates"]) < 30:
        print(f"  THIN PRE-ENTRY DATA: {t} only has {len(pre_s[t]['dates'])} sessions")

# ---------- daily ATR14, TRAILING (proper, no lookahead) ----------
def true_range(prev_close, high, low):
    return max(high - low, abs(high - prev_close), abs(low - prev_close))

def daily_atr14_trailing(t):
    c = pre_s[t]["close"][-15:]
    h = pre_s[t]["high"][-14:]
    l = pre_s[t]["low"][-14:]
    prev_c = c[:-1]
    trs = [true_range(prev_c[i], h[i], l[i]) for i in range(14)]
    return sum(trs) / 14

# ---------- daily ATR14, LOOKAHEAD (v3's original method, for before/after) ----------
def daily_atr14_lookahead(t):
    h = post_s[t]["high"][:14]
    l = post_s[t]["low"][:14]
    c = post_s[t]["close"][:14]
    prev_c = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return tr.mean()

# ---------- weekly ATR14, trailing, ending last complete week before entry ----------
def weekly_bars(t):
    ds = pre_s[t]["dates"]
    c, h, l = pre_s[t]["close"], pre_s[t]["high"], pre_s[t]["low"]
    weeks = {}
    for i, d in enumerate(ds):
        iso = datetime.strptime(d, "%Y-%m-%d").isocalendar()
        key = (iso[0], iso[1])
        weeks.setdefault(key, []).append(i)
    ordered_keys = sorted(weeks.keys())
    wk_close, wk_high, wk_low = [], [], []
    for k in ordered_keys:
        idxs = weeks[k]
        wk_high.append(max(h[i] for i in idxs))
        wk_low.append(min(l[i] for i in idxs))
        wk_close.append(c[idxs[-1]])
    return np.array(wk_close), np.array(wk_high), np.array(wk_low)

def weekly_atr14(t):
    c, h, l = weekly_bars(t)
    c14, h14, l14 = c[-15:], h[-14:], l[-14:]
    prev_c = c14[:-1]
    trs = [true_range(prev_c[i], h14[i], l14[i]) for i in range(14)]
    return sum(trs) / 14

# ---------- 20-day-low stop ----------
def low20(t):
    return min(pre_s[t]["low"][-20:])

atr_daily_trailing = {t: daily_atr14_trailing(t) for t in tickers}
atr_daily_lookahead = {t: daily_atr14_lookahead(t) for t in tickers}
atr_weekly = {t: weekly_atr14(t) for t in tickers}
low_20d = {t: low20(t) for t in tickers}

stop_weekly = {t: entry_price[t] - 2 * atr_weekly[t] for t in tickers}
stop_20day = {t: low_20d[t] for t in tickers}  # stop level itself, distance = entry - stop
stop_fixed = {t: entry_price[t] * 0.92 for t in tickers}

# Dollar distances...
dist_weekly = {t: entry_price[t] - stop_weekly[t] for t in tickers}
dist_20day = {t: entry_price[t] - stop_20day[t] for t in tickers}
dist_fixed = {t: entry_price[t] - stop_fixed[t] for t in tickers}

# ...converted to PERCENT of entry price before normalizing. Same $-vs-%-of-price
# bug as the raw-ATR mistake from v1/v2: dollars_i for equal-$-risk-if-stopped
# sizing is proportional to 1/(dist_i / entry_price_i), NOT 1/dist_i raw. Skipping
# this conversion silently re-introduces "buy huge piles of cheap stocks."
dist_pct_weekly = {t: dist_weekly[t] / entry_price[t] for t in tickers}
dist_pct_20day = {t: dist_20day[t] / entry_price[t] for t in tickers}
dist_pct_fixed = {t: dist_fixed[t] / entry_price[t] for t in tickers}
atr_pct_trailing = {t: atr_daily_trailing[t] / entry_price[t] for t in tickers}
atr_pct_lookahead = {t: atr_daily_lookahead[t] / entry_price[t] for t in tickers}

CAPITAL = 100_000.0
N = len(tickers)

def portfolio_value(shares, idx, cash):
    return sum(shares[t] * post_s[t]["close"][idx] for t in tickers) + cash

def normalized_weights(dist):
    inv = {t: 1.0 / dist[t] for t in tickers}
    tot = sum(inv.values())
    return {t: inv[t] / tot for t in tickers}

def allocate(weights):
    shares, cash = {}, CAPITAL
    for t in tickers:
        alloc = CAPITAL * weights[t]
        sh = int(alloc // entry_price[t])
        shares[t] = sh
        cash -= sh * entry_price[t]
    return shares, cash

w_weekly = normalized_weights(dist_pct_weekly)
w_20day = normalized_weights(dist_pct_20day)
w_fixed = normalized_weights(dist_pct_fixed)
w_vol_trailing = normalized_weights(atr_pct_trailing)
w_vol_lookahead = normalized_weights(atr_pct_lookahead)

# confirm fixed-8% collapses to equal weighting
eq_check = all(abs(w_fixed[t] - 1.0 / N) < 1e-12 for t in tickers)
print(f"\nFixed-8%-stop collapses to equal-$ weighting: {eq_check} "
      f"(sample weights: {list(w_fixed.values())[:3]} vs 1/25={1/N:.6f})")

sh_weekly, cash_weekly = allocate(w_weekly)
sh_20day, cash_20day = allocate(w_20day)
sh_fixed, cash_fixed = allocate(w_fixed)
sh_vol_t, cash_vol_t = allocate(w_vol_trailing)
sh_vol_l, cash_vol_l = allocate(w_vol_lookahead)

# reference models
per_name = CAPITAL / N
sh_eqw, cash_eqw = {}, 0.0
for t in tickers:
    sh = int(per_name // entry_price[t])
    sh_eqw[t] = sh
    cash_eqw += per_name - sh * entry_price[t]
sh_one = {t: 1 for t in tickers}
cash_one = CAPITAL - sum(entry_price[t] for t in tickers)
spy_dates = [b["t"][:10] for b in sorted(spy, key=lambda b: b["t"])]
spy_close = np.array([b["c"] for b in sorted(spy, key=lambda b: b["t"])])
assert spy_dates == dates
spy_shares = CAPITAL / spy_close[0]

def month_end_indices():
    idxs = []
    for i, d in enumerate(dates):
        ym = d[:7]
        if i == n_days - 1 or dates[i + 1][:7] != ym:
            idxs.append(i)
    return idxs

checkpoints = month_end_indices()

cols = [
    ("Equal-$", sh_eqw, cash_eqw),
    ("PR-weekly2ATR", sh_weekly, cash_weekly),
    ("PR-20dayLow", sh_20day, cash_20day),
    ("PR-fixed8pct", sh_fixed, cash_fixed),
    ("PV-dailyATR(trail)", sh_vol_t, cash_vol_t),
    ("1-share", sh_one, cash_one),
]

header = "Month-end".ljust(11) + "".join(name.rjust(18) for name, _, _ in cols) + "SPY".rjust(14)
print("\n" + header)
rows = []
for i in checkpoints:
    d = dates[i]
    vals = [portfolio_value(sh, i, cash) for _, sh, cash in cols]
    spy_v = spy_shares * spy_close[i]
    rows.append([d] + vals + [spy_v])
    line = d.ljust(11) + "".join(f"{v:>18,.0f}" for v in vals) + f"{spy_v:>14,.0f}"
    print(line)

# final values summary
print("\n=== Final values (2026-09-04) ===")
for name, sh, cash in cols:
    fv = portfolio_value(sh, n_days - 1, cash)
    print(f"{name:20s} ${fv:>12,.0f}  ({fv/CAPITAL-1:+.1%})")
print(f"{'SPY':20s} ${spy_shares*spy_close[-1]:>12,.0f}  ({spy_shares*spy_close[-1]/CAPITAL-1:+.1%})")

# lookahead vs trailing PV comparison
fv_vol_t = portfolio_value(sh_vol_t, n_days - 1, cash_vol_t)
fv_vol_l = portfolio_value(sh_vol_l, n_days - 1, cash_vol_l)
print(f"\nPercent-volatility, TRAILING ATR (corrected): ${fv_vol_t:,.0f} ({fv_vol_t/CAPITAL-1:+.2%})")
print(f"Percent-volatility, LOOKAHEAD ATR (old v3 method): ${fv_vol_l:,.0f} ({fv_vol_l/CAPITAL-1:+.2%})")
print(f"Difference: ${abs(fv_vol_t-fv_vol_l):,.0f} ({abs(fv_vol_t/CAPITAL - fv_vol_l/CAPITAL):.2%} of capital)")

# weight divergence: weekly-ATR-stop vs 20-day-low-stop
diffs = {t: abs(w_weekly[t] - w_20day[t]) for t in tickers}
max_t = max(diffs, key=diffs.get)
print(f"\nWeekly-2xATR vs 20-day-low weight divergence:")
print(f"  Max diff ticker: {max_t}  weekly_w={w_weekly[max_t]:.4f}  20day_w={w_20day[max_t]:.4f}  diff={diffs[max_t]:.4f}")
top5 = sorted(diffs.items(), key=lambda kv: -kv[1])[:5]
for t, dv in top5:
    print(f"  {t:6s} weekly={w_weekly[t]:.4f}  20day={w_20day[t]:.4f}  diff={dv:.4f}  "
          f"(weekly_2xATR_pct={dist_pct_weekly[t]:.1%}, 20day_low_pct={dist_pct_20day[t]:.1%}, entry=${entry_price[t]:.2f})")

results = {
    "checkpoints": rows,
    "columns": ["date", "equal_dollar", "pr_weekly_2atr", "pr_20day_low", "pr_fixed_8pct",
                "pv_daily_atr_trailing", "one_share", "spy"],
    "fixed_8pct_equals_equal_weight": eq_check,
    "pv_trailing_vs_lookahead_final": {"trailing": fv_vol_t, "lookahead": fv_vol_l},
    "weight_divergence_weekly_vs_20day": {t: {"weekly": w_weekly[t], "twentyday": w_20day[t]} for t in tickers},
}
with open(f"{BASE}/monthly_v4.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to {BASE}/monthly_v4.json")
