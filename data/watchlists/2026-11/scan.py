import yfinance as yf, pandas as pd, numpy as np
cand=["FORM","FCX","LEVI","NEM","BSX","PYPL"]; book=["EQT","NVDA","AMZN","NFLX","USB","TXN"]
d=yf.download(cand+book+["SPY"],period="2y",interval="1d",auto_adjust=True,progress=False)
c,h,l,v=d["Close"],d["High"],d["Low"],d["Volume"]
r=c.pct_change().dropna().tail(126)
for s in cand:
    x=c[s].dropna(); H=h[s];L=l[s]
    tr=pd.concat([H-L,(H-x.shift()).abs(),(L-x.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean().iloc[-1]
    dl=x.diff(); up=dl.clip(lower=0).ewm(alpha=1/14).mean(); dn=(-dl.clip(upper=0)).ewm(alpha=1/14).mean(); rsi=(100-100/(1+up/dn)).iloc[-1]
    pdm=(H.diff()).where((H.diff()>-L.diff())&(H.diff()>0),0); mdm=(-L.diff()).where((-L.diff()>H.diff())&(-L.diff()>0),0)
    atrw=tr.ewm(alpha=1/14).mean(); pdi=100*pdm.ewm(alpha=1/14).mean()/atrw; mdi=100*mdm.ewm(alpha=1/14).mean()/atrw
    adx=(100*(pdi-mdi).abs()/(pdi+mdi)).ewm(alpha=1/14).mean()
    e21=x.ewm(span=21).mean().iloc[-1]; s50=x.rolling(50).mean().iloc[-1]; s200=x.rolling(200).mean().iloc[-1]
    beta=np.cov(r[s],r["SPY"])[0,1]/r["SPY"].var()
    cr=r.corr()[s][book].round(2).to_dict()
    print(f"\n{s} close {x.iloc[-1]:.2f} fri {100*(x.iloc[-1]/x.iloc[-2]-1):+.2f}% | e21 {e21:.2f} s50 {s50:.2f} s200 {s200:.2f} ({100*(x.iloc[-1]/s200-1):+.1f}% vs 200) | RSI {rsi:.1f} ADX {adx.iloc[-1]:.1f} +DI {pdi.iloc[-1]:.1f} -DI {mdi.iloc[-1]:.1f} | ATR% {100*atr/x.iloc[-1]:.1f}")
    print(f"   52wHi {H.tail(252).max():.2f} 52wLo {L.tail(252).min():.2f} | 1m {100*(x.iloc[-1]/x.iloc[-21]-1):+.1f}% 3m {100*(x.iloc[-1]/x.iloc[-63]-1):+.1f}% 6m {100*(x.iloc[-1]/x.iloc[-126]-1):+.1f}% | beta {beta:.2f} | corr {cr} maxcorr {max(cr.values())}")
    wc=H.resample("W-FRI").max().tail(12).round(1).tolist(); print("   last12 weekly highs", wc)
for s in cand:
    try:
        t=yf.Ticker(s); cal=t.calendar; print(s,"earnings:",cal.get("Earnings Date") if isinstance(cal,dict) else cal)
    except Exception as e: print(s,"cal err",e)
