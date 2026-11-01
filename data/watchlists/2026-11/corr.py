import yfinance as yf, pandas as pd, numpy as np
t=["EQT","TXN","USB","NVDA","HIMS","PCG","SPY"]
d=yf.download(t,period="9mo",interval="1d",auto_adjust=True,progress=False)
c=d["Close"].dropna()
print("last date",c.index[-1].date()); print(c.iloc[-1].round(2).to_dict())
r=c.pct_change().dropna()
for n in (63,126):
    print(f"\n== corr {n}d =="); print(r.tail(n).corr().round(2))
x=r.tail(126)
print("\nbeta126 / annvol126")
for s in t:
    b=np.cov(x[s],x["SPY"])[0,1]/x["SPY"].var(); print(s, round(b,2), round(x[s].std()*np.sqrt(252)*100,1))
# ATR14, levels
h,l=d["High"],d["Low"]
for s in t[:-1]:
    tr=pd.concat([h[s]-l[s],(h[s]-c[s].shift()).abs(),(l[s]-c[s].shift()).abs()],axis=1).max(axis=1)
    atr=tr.rolling(14).mean().iloc[-1]
    cc=c[s]
    print(f"{s} close {cc.iloc[-1]:.2f} ATR {atr:.2f} ema21 {cc.ewm(span=21).mean().iloc[-1]:.2f} sma50 {cc.rolling(50).mean().iloc[-1]:.2f} sma200 {cc.rolling(200).mean().iloc[-1] if len(cc)>=200 else float('nan'):.2f} 20dHi {h[s].tail(20).max():.2f} 20dLo {l[s].tail(20).min():.2f} 60dHi {h[s].tail(60).max():.2f} 60dLo {l[s].tail(60).min():.2f}")
