import json
import numpy as np

with open("/home/mph/mphinance/docs/drafts/tharp-port/data/raw_bars.json") as f:
    raw = json.load(f)
with open("/home/mph/mphinance/docs/drafts/tharp-port/data/spy_bars.json") as f:
    spy_raw = json.load(f)

bars = raw["data"]["bars"]
tickers = sorted(bars.keys())

series = {}
for t in tickers:
    b = bars[t]
    dates = [x["t"][:10] for x in b]
    close = np.array([x["c"] for x in b])
    high = np.array([x["h"] for x in b])
    low = np.array([x["l"] for x in b])
    series[t] = {"dates": dates, "close": close, "high": high, "low": low}

n_days = len(series[tickers[0]]["dates"])
dates = series[tickers[0]]["dates"]

spy_bars = spy_raw["data"]["bars"]["SPY"]
spy_close = np.array([x["c"] for x in spy_bars])

def atr14(t, idx=13):
    h = series[t]["high"][:idx+1]
    l = series[t]["low"][:idx+1]
    c = series[t]["close"][:idx+1]
    prev_c = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return tr.mean()

entry_price = {t: series[t]["close"][0] for t in tickers}
atr = {t: atr14(t) for t in tickers}
atr_pct = {t: atr[t] / entry_price[t] for t in tickers}
CAPITAL = 100_000.0
N = len(tickers)

def portfolio_value(shares, idx, cash):
    return sum(shares[t] * series[t]["close"][idx] for t in tickers) + cash

# --- Equal-$ ---
shares_eqw, cash_eqw = {}, 0.0
per_name = CAPITAL / N
for t in tickers:
    sh = int(per_name // entry_price[t])
    shares_eqw[t] = sh
    cash_eqw += per_name - sh * entry_price[t]

# --- ATR-weighted (percent-risk == percent-volatility, one row) ---
inv_atr_pct = {t: 1.0 / atr_pct[t] for t in tickers}
tot_inv_atr_pct = sum(inv_atr_pct.values())
atr_weight = {t: inv_atr_pct[t] / tot_inv_atr_pct for t in tickers}
shares_atrw, cash_atrw = {}, CAPITAL
for t in tickers:
    alloc = CAPITAL * atr_weight[t]
    sh = int(alloc // entry_price[t])
    shares_atrw[t] = sh
    cash_atrw -= sh * entry_price[t]

# --- 1-share baseline ---
shares_one = {t: 1 for t in tickers}
cash_one = CAPITAL - sum(entry_price[t] for t in tickers)

# --- SPY ---
spy_shares = CAPITAL / spy_close[0]

# month-end (or last available day) checkpoint indices
def month_end_indices():
    idxs = []
    for i, d in enumerate(dates):
        ym = d[:7]
        is_last_of_month = (i == n_days - 1) or (dates[i+1][:7] != ym)
        if is_last_of_month:
            idxs.append(i)
    return idxs

checkpoints = month_end_indices()

print(f"{'Month-end':<12}{'Equal-$':>14}{'ATR-weighted':>16}{'1-share':>12}{'SPY':>14}")
rows = []
for i in checkpoints:
    d = dates[i]
    v_eqw = portfolio_value(shares_eqw, i, cash_eqw)
    v_atrw = portfolio_value(shares_atrw, i, cash_atrw)
    v_one = portfolio_value(shares_one, i, cash_one)
    v_spy = spy_shares * spy_close[i]
    rows.append((d, v_eqw, v_atrw, v_one, v_spy))
    print(f"{d:<12}{v_eqw:>13,.0f} {v_atrw:>15,.0f} {v_one:>11,.0f} {v_spy:>13,.0f}")

with open("/home/mph/mphinance/docs/drafts/tharp-port/monthly_static.json", "w") as f:
    json.dump({"columns": ["date", "equal_dollar", "atr_weighted", "one_share", "spy"], "rows": rows}, f, indent=2)
print("\nSaved to monthly_static.json")
