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
spy_dates = [x["t"][:10] for x in spy_bars]
spy_close = np.array([x["c"] for x in spy_bars])
assert spy_dates == dates, "SPY date range must match the 25-ticker universe exactly"

def atr14(t, idx=13):
    h = series[t]["high"][:idx+1]
    l = series[t]["low"][:idx+1]
    c = series[t]["close"][:idx+1]
    prev_c = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return tr.mean()

entry_price = {t: series[t]["close"][0] for t in tickers}
atr = {t: atr14(t) for t in tickers}
CAPITAL = 100_000.0
N = len(tickers)

def portfolio_value(shares, idx, cash):
    return sum(shares[t] * series[t]["close"][idx] for t in tickers) + cash

def max_drawdown(values):
    values = np.array(values)
    peak = np.maximum.accumulate(values)
    return ((peak - values) / peak).max()

def end_top(shares, cash):
    end_w = {t: shares[t] * series[t]["close"][-1] for t in tickers}
    tot = sum(end_w.values()) + cash
    top_t = max(end_w, key=end_w.get)
    return top_t, end_w[top_t] / tot

# ---------- Equal-$ (unchanged, no bug here) ----------
shares_eqw, cash_eqw = {}, 0.0
per_name = CAPITAL / N
for t in tickers:
    sh = int(per_name // entry_price[t])
    shares_eqw[t] = sh
    cash_eqw += per_name - sh * entry_price[t]

# ---------- 1-share baseline (unchanged) ----------
shares_one = {t: 1 for t in tickers}
cash_one = CAPITAL - sum(entry_price[t] for t in tickers)

# ---------- CORRECTED Percent-risk: normalized inverse-stop-distance weights ----------
stop_dist = {t: 2 * atr[t] for t in tickers}
inv_stop = {t: 1.0 / stop_dist[t] for t in tickers}
tot_inv_stop = sum(inv_stop.values())
risk_weight = {t: inv_stop[t] / tot_inv_stop for t in tickers}
shares_risk, cash_risk = {}, CAPITAL
for t in tickers:
    alloc = CAPITAL * risk_weight[t]
    sh = int(alloc // entry_price[t])
    shares_risk[t] = sh
    cash_risk -= sh * entry_price[t]

# ---------- CORRECTED Percent-volatility: normalized inverse-ATR weights ----------
inv_atr = {t: 1.0 / atr[t] for t in tickers}
tot_inv_atr = sum(inv_atr.values())
vol_weight = {t: inv_atr[t] / tot_inv_atr for t in tickers}
shares_vol, cash_vol = {}, CAPITAL
for t in tickers:
    alloc = CAPITAL * vol_weight[t]
    sh = int(alloc // entry_price[t])
    shares_vol[t] = sh
    cash_vol -= sh * entry_price[t]

def run_static(shares, cash, label):
    curve = [portfolio_value(shares, i, cash) for i in range(n_days)]
    final = curve[-1]
    top_t, top_pct = end_top(shares, cash)
    deployed_pct = 1 - cash / CAPITAL
    return {"label": label, "final": final, "ret": final/CAPITAL - 1, "mdd": max_drawdown(curve),
            "top_ticker": top_t, "top_pct": top_pct, "deployed_pct": deployed_pct}

results = {}
results["eqw_static"] = run_static(shares_eqw, cash_eqw, "Equal-$ static")
results["risk_static"] = run_static(shares_risk, cash_risk, "Percent-risk static (corrected)")
results["vol_static"] = run_static(shares_vol, cash_vol, "Percent-volatility static (corrected)")
results["one_static"] = run_static(shares_one, cash_one, "1-share baseline static")

# ---------- Quarterly rebalance: Equal-$ and Percent-vol (corrected weights) ----------
def nearest_idx(target_date):
    diffs = [abs((np.datetime64(d) - np.datetime64(target_date)).astype(int)) for d in dates]
    return int(np.argmin(diffs))

rebal_idxs = [nearest_idx(d) for d in ["2026-03-31", "2026-06-30"]]

def run_rebalanced(weights, label):
    shares, cash = {}, CAPITAL
    for t in tickers:
        sh = int((CAPITAL * weights[t]) // entry_price[t])
        shares[t] = sh
        cash -= sh * entry_price[t]
    curve = []
    rb = 0
    for i in range(n_days):
        if rb < len(rebal_idxs) and i == rebal_idxs[rb]:
            val = portfolio_value(shares, i, cash)
            new_shares, spend = {}, 0.0
            for t in tickers:
                sh = int((val * weights[t]) // series[t]["close"][i])
                new_shares[t] = sh
                spend += sh * series[t]["close"][i]
            cash = val - spend
            shares = new_shares
            rb += 1
        curve.append(portfolio_value(shares, i, cash))
    final = curve[-1]
    top_t, top_pct = end_top(shares, cash)
    return {"label": label, "final": final, "ret": final/CAPITAL - 1, "mdd": max_drawdown(curve),
            "top_ticker": top_t, "top_pct": top_pct}

eqw_weight = {t: 1.0/N for t in tickers}
results["eqw_rebal"] = run_rebalanced(eqw_weight, "Equal-$ + quarterly rebalance")
results["vol_rebal"] = run_rebalanced(vol_weight, "Percent-vol + quarterly rebalance (corrected)")

# ---------- Monthly top-ups ($500/mo) ----------
def month_start_indices():
    seen, idxs = set(), []
    for i, d in enumerate(dates):
        ym = d[:7]
        if ym not in seen and d > "2026-01-02":
            seen.add(ym)
            idxs.append(i)
    return idxs

topup_idxs = month_start_indices()

def run_topups(shares_init, cash_init, weights, label, monthly=500.0):
    shares, cash, contributed = dict(shares_init), cash_init, CAPITAL
    tp = 0
    for i in range(n_days):
        if tp < len(topup_idxs) and i == topup_idxs[tp]:
            cash += monthly
            contributed += monthly
            for t in tickers:
                add = monthly * weights[t]
                cash -= add
                shares[t] += add / series[t]["close"][i]
            tp += 1
    final = sum(shares[t] * series[t]["close"][-1] for t in tickers) + cash
    top_t, top_pct = end_top(shares, cash)
    return {"label": label, "final": final, "contributed": contributed,
            "ret_vs_contributed": final/contributed - 1, "top_ticker": top_t, "top_pct": top_pct}

results["eqw_topup"] = run_topups(shares_eqw, cash_eqw, eqw_weight, "Equal-$ + monthly top-ups")
results["vol_topup"] = run_topups(shares_vol, cash_vol, vol_weight, "Percent-vol + monthly top-ups (corrected)")

# ---------- SPY benchmark ----------
spy_entry = spy_close[0]
spy_shares_static = CAPITAL / spy_entry
spy_curve = spy_shares_static * spy_close
results["spy_static"] = {"label": "SPY buy-and-hold static", "final": spy_curve[-1],
                          "ret": spy_curve[-1]/CAPITAL - 1, "mdd": max_drawdown(spy_curve)}

spy_shares, cash_spy, contributed = spy_shares_static, 0.0, CAPITAL
tp = 0
for i in range(n_days):
    if tp < len(topup_idxs) and i == topup_idxs[tp]:
        spy_shares += 500.0 / spy_close[i]
        contributed += 500.0
        tp += 1
spy_final_topup = spy_shares * spy_close[-1]
results["spy_topup"] = {"label": "SPY + monthly top-ups", "final": spy_final_topup,
                         "contributed": contributed, "ret_vs_contributed": spy_final_topup/contributed - 1}

print("=== CORRECTED RESULTS ===")
for k, r in results.items():
    print(k, r)

with open("/home/mph/mphinance/docs/drafts/tharp-port/results_summary_v2.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print("\nSaved to results_summary_v2.json")
