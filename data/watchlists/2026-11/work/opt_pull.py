import yfinance as yf
import datetime as dt
import json

tickers = ["EQT","TXN","USB","NVDA","HIMS"]
out = {}
for t in tickers:
    tk = yf.Ticker(t)
    try:
        hist = tk.history(period="5d")
        last = float(hist['Close'].iloc[-1])
    except Exception as e:
        last = None
    try:
        exps = tk.options
    except Exception as e:
        exps = []
    out[t] = {"last": last, "expiries": exps}

print(json.dumps(out, indent=2, default=str))
