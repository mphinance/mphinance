import yfinance as yf
import json

targets = {
    "EQT": {"spot": 55.38, "exp": ["2026-12-18","2027-01-15"], "strikes": [50,52.5,55,57.5,60]},
    "TXN": {"spot": 300.84, "exp": ["2026-12-18","2027-01-15"], "strikes": [280,290,300,310,320]},
    "USB": {"spot": 59.45, "exp": ["2026-12-18","2027-01-15"], "strikes": [55,57.5,59,60,62.5]},
    "NVDA": {"spot": 204.64, "exp": ["2026-12-18","2027-01-15"], "strikes": [190,195,200,205,210,220]},
    "HIMS": {"spot": 27.68, "exp": ["2026-12-18","2027-01-15"], "strikes": [25,27.5,30,32.5,35]},
}

for t, cfg in targets.items():
    tk = yf.Ticker(t)
    print(f"\n===== {t} spot {cfg['spot']} =====")
    for exp in cfg["exp"]:
        try:
            chain = tk.option_chain(exp)
            calls = chain.calls
        except Exception as e:
            print(f"  {exp}: ERROR {e}")
            continue
        print(f"  -- {exp} --")
        for k in cfg["strikes"]:
            row = calls[calls['strike']==k]
            if len(row)==0:
                continue
            r = row.iloc[0]
            bid = r['bid']; ask=r['ask']; iv=r.get('impliedVolatility', None)
            vol = r.get('volume', None); oi = r.get('openInterest', None)
            mid = (bid+ask)/2 if (bid is not None and ask is not None) else None
            print(f"    K={k}: bid={bid} ask={ask} mid={mid:.2f} iv={iv:.1%} vol={vol} oi={oi}" if mid is not None else f"    K={k}: bid={bid} ask={ask} iv={iv} vol={vol} oi={oi}")
