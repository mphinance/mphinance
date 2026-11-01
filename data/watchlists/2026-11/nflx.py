import yfinance as yf, pandas as pd, numpy as np
d=yf.download(["NFLX","SPY","NVDA"],period="2y",interval="1d",auto_adjust=True,progress=False)
c,h,l,v=d["Close"],d["High"],d["Low"],d["Volume"]
s=c["NFLX"].dropna(); H=h["NFLX"]; L=l["NFLX"]
print("last",s.index[-1].date(), round(s.iloc[-1],2))
print("last 10 closes:",s.tail(10).round(2).tolist())
print("10/30 chg %", round((s.iloc[-1]/s.iloc[-2]-1)*100,2), "SPY", round((c['SPY'].iloc[-1]/c['SPY'].iloc[-2]-1)*100,2))
for n in (8,21,50): print(f"ema{n}", round(s.ewm(span=n).mean().iloc[-1],2), "slope5", round(s.ewm(span=n).mean().iloc[-1]-s.ewm(span=n).mean().iloc[-6],2))
for n in (50,100,200): print(f"sma{n}", round(s.rolling(n).mean().iloc[-1],2), "slope10", round(s.rolling(n).mean().iloc[-1]-s.rolling(n).mean().iloc[-11],2))
dl=s.diff(); up=dl.clip(lower=0).ewm(alpha=1/14).mean(); dn=(-dl.clip(upper=0)).ewm(alpha=1/14).mean(); rsi=100-100/(1+up/dn)
print("RSI14 last5", rsi.tail(5).round(1).tolist())
tr=pd.concat([H-L,(H-s.shift()).abs(),(L-s.shift()).abs()],axis=1).max(axis=1); atr=tr.rolling(14).mean()
print("ATR", round(atr.iloc[-1],2), round(atr.iloc[-1]/s.iloc[-1]*100,2),"%")
# ADX
pdm=(H.diff()).where((H.diff()>-L.diff())&(H.diff()>0),0); mdm=(-L.diff()).where((-L.diff()>H.diff())&(-L.diff()>0),0)
atrw=tr.ewm(alpha=1/14).mean(); pdi=100*pdm.ewm(alpha=1/14).mean()/atrw; mdi=100*mdm.ewm(alpha=1/14).mean()/atrw
adx=(100*(pdi-mdi).abs()/(pdi+mdi)).ewm(alpha=1/14).mean()
print("ADX",round(adx.iloc[-1],1),"+DI",round(pdi.iloc[-1],1),"-DI",round(mdi.iloc[-1],1))
# 52w + major peak
y=s.tail(252); print("52w hi",round(H.tail(252).max(),2),H.tail(252).idxmax().date(),"52w lo",round(L.tail(252).min(),2),L.tail(252).idxmin().date())
# monthly closes last 14
print("monthly closes:", s.resample("ME").last().tail(14).round(1).to_dict())
# swing highs (weekly) since major peak for falling trendline
w=H.resample("W-FRI").max().dropna(); wc=s.resample("W-FRI").last()
pk=w.tail(60).idxmax(); print("major weekly peak",pk.date(),round(w[pk],2))
after=w[w.index>=pk]
sw=[(i,after.iloc[i]) for i in range(1,len(after)-1) if after.iloc[i]>=after.iloc[i-1] and after.iloc[i]>=after.iloc[i+1]]
print("weekly swing highs since peak:",[(after.index[i].date(),round(x,1)) for i,x in sw])
print("last 8 weekly H/C:",list(zip([x.date() for x in w.tail(8).index],w.tail(8).round(1),wc.tail(8).round(1))))
# volume
vv=v["NFLX"]; print("vol last5 vs 50d avg:", (vv.tail(5)/vv.rolling(50).mean().iloc[-1]).round(2).tolist())
r=c.pct_change().dropna().tail(63); print("corr63 NFLX-SPY",round(r.NFLX.corr(r.SPY),2),"NFLX-NVDA",round(r.NFLX.corr(r.NVDA),2), "beta",round(np.cov(r.NFLX,r.SPY)[0,1]/r.SPY.var(),2))
print("perf 1m/3m/6m %:",[round((s.iloc[-1]/s.iloc[-k]-1)*100,1) for k in (21,63,126)], "SPY:",[round((c.SPY.iloc[-1]/c.SPY.iloc[-k]-1)*100,1) for k in (21,63,126)])
