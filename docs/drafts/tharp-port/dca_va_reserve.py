import json
from datetime import datetime

TICKERS = [l.strip() for l in open('/home/mph/mphinance/tharptestlist.txt') if l.strip()]

d = json.load(open('data/raw_bars.json'))
bars = d['data']['bars']

# build date-indexed close price series per ticker
series = {}
for t in TICKERS:
    series[t] = {b['t'][:10]: b['c'] for b in bars[t]}

all_dates = sorted(series[TICKERS[0]].keys())
entry_date = all_dates[0]
final_date = all_dates[-1]
print(f"Trading calendar: {entry_date} .. {final_date}, {len(all_dates)} sessions")

def true_range(prev_close, high, low):
    return max(high - low, abs(high - prev_close), abs(low - prev_close))

def atr14(t):
    rows = bars[t]
    trs = []
    for i in range(1, 15):
        trs.append(true_range(rows[i-1]['c'], rows[i]['h'], rows[i]['l']))
    return sum(trs) / len(trs)

entry_price = {t: series[t][entry_date] for t in TICKERS}
atr = {t: atr14(t) for t in TICKERS}

# v2 normalized weight, CORRECTED: weight by ATR as a % of price, not raw dollar ATR.
# Raw dollar ATR silently means "buy huge piles of cheap stocks" (the BB concentration bomb
# from the prior run) — % ATR actually equalizes volatility exposure regardless of share price.
atr_pct = {t: atr[t] / entry_price[t] for t in TICKERS}
inv_atr_pct = {t: 1.0 / atr_pct[t] for t in TICKERS}
tot_inv_atr_pct = sum(inv_atr_pct.values())
target_weight = {t: inv_atr_pct[t] / tot_inv_atr_pct for t in TICKERS}

TOTAL_CAPITAL = 100_000.0
CORE_FRACTION = 0.366  # v1 percent-volatility deployed fraction, used as "core" here
target_dollars = {t: target_weight[t] * TOTAL_CAPITAL for t in TICKERS}
core_dollars = {t: target_weight[t] * (CORE_FRACTION * TOTAL_CAPITAL) for t in TICKERS}
reserve_dollars = {t: target_dollars[t] - core_dollars[t] for t in TICKERS}

print(f"\nCore deployed at entry: ${sum(core_dollars.values()):,.0f} "
      f"({CORE_FRACTION:.1%} of ${TOTAL_CAPITAL:,.0f})")
print(f"Reserve to phase in: ${sum(reserve_dollars.values()):,.0f}")

# monthly contribution dates: first trading day on/after the 1st of each month, Feb..Sep
def first_trading_day_on_or_after(year, month):
    target = f"{year}-{month:02d}-01"
    for dt in all_dates:
        if dt >= target:
            return dt
    return None

contrib_dates = []
for m in range(2, 10):
    dt = first_trading_day_on_or_after(2026, m)
    if dt and dt <= final_date:
        contrib_dates.append(dt)
print(f"Contribution dates ({len(contrib_dates)}): {contrib_dates}")

N = len(contrib_dates)

# --- shares from core ---
shares_dca = {t: core_dollars[t] / entry_price[t] for t in TICKERS}
shares_va = {t: core_dollars[t] / entry_price[t] for t in TICKERS}
cash_dca = 0.0
cash_va = 0.0

per_period_reserve = {t: reserve_dollars[t] / N for t in TICKERS}
monthly_pool = sum(per_period_reserve.values())  # same total $ pool each month for both variants

for k, dt in enumerate(contrib_dates, start=1):
    # DCA: fixed proportional contribution regardless of price
    for t in TICKERS:
        price = series[t][dt]
        shares_dca[t] += per_period_reserve[t] / price

    # Value averaging (no-sell): target mark-to-market value path is linear from core to target
    frac = k / N
    shortfalls = {}
    for t in TICKERS:
        price = series[t][dt]
        current_value = shares_va[t] * price
        target_value = core_dollars[t] + (target_dollars[t] - core_dollars[t]) * frac
        shortfalls[t] = max(0.0, target_value - current_value)
    tot_shortfall = sum(shortfalls.values())
    for t in TICKERS:
        price = series[t][dt]
        if tot_shortfall > 0:
            alloc = monthly_pool * (shortfalls[t] / tot_shortfall)
        else:
            alloc = 0.0
        shares_va[t] += alloc / price
        cash_va += monthly_pool * (shortfalls[t] / tot_shortfall) - alloc  # no-op, kept for clarity
    # any pool leftover when all shortfalls are zero (shouldn't happen here) goes to cash
    if tot_shortfall == 0:
        cash_va += monthly_pool

final_value_dca = sum(shares_dca[t] * series[t][final_date] for t in TICKERS) + cash_dca
final_value_va = sum(shares_va[t] * series[t][final_date] for t in TICKERS) + cash_va

total_contributed = sum(core_dollars.values()) + monthly_pool * N

print(f"\nTotal contributed over the window: ${total_contributed:,.0f}")
print(f"\n=== Reserve phased in via DCA ===")
print(f"Final value: ${final_value_dca:,.0f}  ({final_value_dca/total_contributed - 1:+.1%} vs contributed)")

print(f"\n=== Reserve phased in via Value Averaging (no-sell) ===")
print(f"Final value: ${final_value_va:,.0f}  ({final_value_va/total_contributed - 1:+.1%} vs contributed)")

# concentration check at the end for both
def top_holding(shares):
    values = {t: shares[t] * series[t][final_date] for t in TICKERS}
    tot = sum(values.values())
    top_t = max(values, key=values.get)
    return top_t, values[top_t] / tot

top_dca = top_holding(shares_dca)
top_va = top_holding(shares_va)
print(f"\nDCA top holding: {top_dca[0]} at {top_dca[1]:.1%} of ending value")
print(f"VA  top holding: {top_va[0]} at {top_va[1]:.1%} of ending value")

# compare to lump-sum-day-one v2 result for context
lump_value = sum((target_dollars[t] / entry_price[t]) * series[t][final_date] for t in TICKERS)
print(f"\nFor context — full $100k lump sum on day one (v2 static): ${lump_value:,.0f} ({lump_value/TOTAL_CAPITAL-1:+.1%})")
