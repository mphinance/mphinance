import yfinance as yf, datetime as dt
spots={}
for t in ["SLV","AG"]:
    tk=yf.Ticker(t); s=tk.history(period="5d")["Close"].iloc[-1]; spots[t]=s
    print(f"\n### {t} spot {s:.2f}  expiries: {tk.options[:10]}")
    for e in tk.options:
        dte=(dt.date.fromisoformat(e)-dt.date(2026,10,29)).days
        if dte<1 or dte>60: continue
        ch=tk.option_chain(e); c=ch.calls; p=ch.puts
        k=c.iloc[(c.strike-s*1.05).abs().argsort()[:1]].iloc[0]
        kp=p.iloc[(p.strike-s*0.95).abs().argsort()[:1]].iloc[0]
        mid=lambda r:(r.bid+r.ask)/2 if r.ask>0 else r.lastPrice
        print(f"  {e} ({dte}d)  CALL {k.strike} ({(k.strike/s-1)*100:+.1f}%) bid {k.bid} ask {k.ask} last {k.lastPrice} mid {mid(k):.2f} iv {k.impliedVolatility:.2f} OI {k.openInterest}  |  PUT {kp.strike} bid {kp.bid} ask {kp.ask} mid {mid(kp):.2f} iv {kp.impliedVolatility:.2f} OI {kp.openInterest}")
