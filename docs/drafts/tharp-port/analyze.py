import json
import numpy as np

with open("/home/mph/mphinance/docs/drafts/tharp-port/data/raw_bars.json") as f:
    raw = json.load(f)

bars = raw["data"]["bars"]
tickers = sorted(bars.keys())

# Per-ticker arrays: dates, close, high, low
series = {}
for t in tickers:
    b = bars[t]
    dates = [x["t"][:10] for x in b]
    close = np.array([x["c"] for x in b])
    high = np.array([x["h"] for x in b])
    low = np.array([x["l"] for x in b])
    series[t] = {"dates": dates, "close": close, "high": high, "low": low}

n_days = len(series[tickers[0]]["dates"])
for t in tickers:
    assert len(series[t]["dates"]) == n_days, t
dates = series[tickers[0]]["dates"]
print(f"Common date range: {dates[0]} to {dates[-1]}, {n_days} trading days, {len(tickers)} tickers")

# --- ATR(14) as of entry (index 13, first day with 14 bars of range incl entry day) ---
def atr14(t, idx=13):
    # true range for days 0..idx (14 bars), using prior close for gap component where available
    h = series[t]["high"][:idx+1]
    l = series[t]["low"][:idx+1]
    c = series[t]["close"][:idx+1]
    prev_c = np.concatenate(([c[0]], c[:-1]))
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    return tr.mean()

entry_idx = 0
entry_price = {t: series[t]["close"][entry_idx] for t in tickers}
atr = {t: atr14(t) for t in tickers}

print("\nEntry prices and ATR(14):")
for t in tickers:
    print(f"  {t:6s} entry={entry_price[t]:>9.2f}  ATR14={atr[t]:>7.3f}  ATR%={atr[t]/entry_price[t]*100:5.2f}%")

CAPITAL = 100_000.0
N = len(tickers)

# ---------- Model 1: Equal-$ ----------
shares_eqw = {}
cash_eqw = 0.0
per_name = CAPITAL / N
for t in tickers:
    sh = int(per_name // entry_price[t])
    shares_eqw[t] = sh
    cash_eqw += per_name - sh * entry_price[t]

# ---------- Model 2: Percent-risk (ATR-stop implied) ----------
# theoretical stop = entry - 2*ATR ; risk budget per name = 2% * 100k / 25
risk_budget_per_name = CAPITAL * 0.02 / N
shares_risk = {}
cash_risk = 0.0
for t in tickers:
    stop_dist = 2 * atr[t]
    dollars = risk_budget_per_name / stop_dist * entry_price[t]  # dollars to allocate = shares*entry ; shares = risk_budget/stop_dist
    sh_exact = risk_budget_per_name / stop_dist
    sh = int(sh_exact)
    shares_risk[t] = sh
    cash_risk += 0  # will true up cash after seeing total spent

spent_risk = sum(shares_risk[t] * entry_price[t] for t in tickers)
cash_risk = CAPITAL - spent_risk

# ---------- Model 3: Percent-volatility (inverse ATR, raw $) ----------
vol_budget_per_name = CAPITAL * 0.02 / N
shares_vol = {}
for t in tickers:
    sh_exact = vol_budget_per_name / atr[t]
    shares_vol[t] = int(sh_exact)
spent_vol = sum(shares_vol[t] * entry_price[t] for t in tickers)
cash_vol = CAPITAL - spent_vol

# ---------- Model 4: 1 share of each ----------
shares_one = {t: 1 for t in tickers}
spent_one = sum(entry_price[t] for t in tickers)
cash_one = CAPITAL - spent_one  # rest sits in cash (this is the point)

def portfolio_value(shares, idx, cash):
    return sum(shares[t] * series[t]["close"][idx] for t in tickers) + cash

def max_drawdown(values):
    values = np.array(values)
    peak = np.maximum.accumulate(values)
    dd = (peak - values) / peak
    return dd.max()

def run_static(shares, cash, label):
    curve = [portfolio_value(shares, i, cash) for i in range(n_days)]
    final = curve[-1]
    ret = final / CAPITAL - 1
    mdd = max_drawdown(curve)
    end_weights = {t: shares[t] * series[t]["close"][-1] for t in tickers}
    total_end = sum(end_weights.values()) + cash
    top_t = max(end_weights, key=end_weights.get)
    top_pct = end_weights[top_t] / total_end
    return {"label": label, "final": final, "ret": ret, "mdd": mdd, "top_ticker": top_t, "top_pct": top_pct, "curve": curve}

results = {}
results["eqw_static"] = run_static(shares_eqw, cash_eqw, "Equal-$ static")
results["risk_static"] = run_static(shares_risk, cash_risk, "Percent-risk static")
results["vol_static"] = run_static(shares_vol, cash_vol, "Percent-volatility static")
results["one_static"] = run_static(shares_one, cash_one, "1-share baseline static")

print("\n=== STATIC RESULTS ===")
for k, r in results.items():
    print(f"{r['label']:30s} final=${r['final']:>12,.2f}  ret={r['ret']:+7.2%}  maxDD={r['mdd']:6.2%}  "
          f"top={r['top_ticker']} ({r['top_pct']:.1%} of book)")

# ---------- Quarterly rebalance (Equal-$ and Percent-volatility) ----------
# find index closest to quarter-end dates within range
def nearest_idx(target_date):
    # dates are YYYY-MM-DD strings sorted
    diffs = [abs((np.datetime64(d) - np.datetime64(target_date)).astype(int)) for d in dates]
    return int(np.argmin(diffs))

rebal_dates = ["2026-03-31", "2026-06-30"]
rebal_idxs = [nearest_idx(d) for d in rebal_dates]
print(f"\nRebalance indices/dates used: {[(i, dates[i]) for i in rebal_idxs]}")

def run_rebalanced(target_weights_fn, label):
    # target_weights_fn(t) -> weight fraction at entry, used at every rebalance too
    weights = {t: target_weights_fn(t) for t in tickers}
    tot_w = sum(weights.values())
    weights = {t: w / tot_w for t, w in weights.items()}

    shares = {}
    cash = CAPITAL
    for t in tickers:
        alloc = CAPITAL * weights[t]
        sh = int(alloc // entry_price[t])
        shares[t] = sh
        cash -= sh * entry_price[t]

    curve = []
    rb_pointer = 0
    for i in range(n_days):
        if rb_pointer < len(rebal_idxs) and i == rebal_idxs[rb_pointer]:
            val = portfolio_value(shares, i, cash)
            new_shares = {}
            spend_total = 0.0
            for t in tickers:
                alloc = val * weights[t]
                sh = int(alloc // series[t]["close"][i])
                new_shares[t] = sh
                spend_total += sh * series[t]["close"][i]
            cash = val - spend_total
            shares = new_shares
            rb_pointer += 1
        curve.append(portfolio_value(shares, i, cash))
    final = curve[-1]
    ret = final / CAPITAL - 1
    mdd = max_drawdown(curve)
    end_weights = {t: shares[t] * series[t]["close"][-1] for t in tickers}
    total_end = sum(end_weights.values()) + cash
    top_t = max(end_weights, key=end_weights.get)
    top_pct = end_weights[top_t] / total_end
    return {"label": label, "final": final, "ret": ret, "mdd": mdd, "top_ticker": top_t, "top_pct": top_pct}

eqw_weight_fn = lambda t: 1.0
vol_weight_fn = lambda t: (0.02 * CAPITAL / N) / atr[t] * entry_price[t]  # proportional $ alloc implied by percent-vol model

results["eqw_rebal"] = run_rebalanced(eqw_weight_fn, "Equal-$ + quarterly rebalance")
results["vol_rebal"] = run_rebalanced(vol_weight_fn, "Percent-vol + quarterly rebalance")

print("\n=== REBALANCED RESULTS ===")
for k in ["eqw_rebal", "vol_rebal"]:
    r = results[k]
    print(f"{r['label']:30s} final=${r['final']:>12,.2f}  ret={r['ret']:+7.2%}  maxDD={r['mdd']:6.2%}  "
          f"top={r['top_ticker']} ({r['top_pct']:.1%} of book)")

# ---------- Monthly top-ups ($500/mo, no rebalance of existing shares) ----------
def month_start_indices():
    seen_months = set()
    idxs = []
    for i, d in enumerate(dates):
        ym = d[:7]
        if ym not in seen_months and d[:10] > "2026-01-02":
            seen_months.add(ym)
            idxs.append(i)
    return idxs

topup_idxs = month_start_indices()
print(f"\nTop-up indices/dates: {[(i, dates[i]) for i in topup_idxs]}")

def run_topups(shares_init, cash_init, weight_fn, label, monthly=500.0):
    weights = {t: weight_fn(t) for t in tickers}
    tot_w = sum(weights.values())
    weights = {t: w / tot_w for t, w in weights.items()}

    shares = dict(shares_init)
    cash = cash_init
    contributed = CAPITAL
    tp_pointer = 0
    for i in range(n_days):
        if tp_pointer < len(topup_idxs) and i == topup_idxs[tp_pointer]:
            cash += monthly
            contributed += monthly
            for t in tickers:
                add_dollars = monthly * weights[t]
                cash -= add_dollars
                # buy fractional-effective by tracking as extra cash if can't afford whole share; keep simple: allow fractional shares here for top-up buys
                shares[t] += add_dollars / series[t]["close"][i]
            tp_pointer += 1
        # note: shares[t] may now be float due to fractional top-up buys; portfolio_value handles that fine
    curve_final = sum(shares[t] * series[t]["close"][-1] for t in tickers) + cash
    ret_vs_contributed = curve_final / contributed - 1
    end_weights = {t: shares[t] * series[t]["close"][-1] for t in tickers}
    total_end = sum(end_weights.values()) + cash
    top_t = max(end_weights, key=end_weights.get)
    top_pct = end_weights[top_t] / total_end
    return {"label": label, "final": curve_final, "contributed": contributed,
            "ret_vs_contributed": ret_vs_contributed, "top_ticker": top_t, "top_pct": top_pct}

results["eqw_topup"] = run_topups(shares_eqw, cash_eqw, eqw_weight_fn, "Equal-$ + monthly top-ups")
results["vol_topup"] = run_topups(shares_vol, cash_vol, vol_weight_fn, "Percent-vol + monthly top-ups")

print("\n=== TOP-UP RESULTS (return measured vs total contributed capital, not just initial 100k) ===")
for k in ["eqw_topup", "vol_topup"]:
    r = results[k]
    print(f"{r['label']:30s} final=${r['final']:>12,.2f}  contributed=${r['contributed']:>10,.2f}  "
          f"ret_vs_contributed={r['ret_vs_contributed']:+7.2%}  top={r['top_ticker']} ({r['top_pct']:.1%})")

# ---------- Save summary JSON ----------
summary = {}
for k, r in results.items():
    summary[k] = {kk: vv for kk, vv in r.items() if kk != "curve"}
with open("/home/mph/mphinance/docs/drafts/tharp-port/results_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print("\nSaved summary to results_summary.json")
