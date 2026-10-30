import yfinance as yf, pandas as pd, itertools, numpy as np
groups = {
 "eVTOL": ["ACHR","JOBY"],
 "AI neocloud": ["CRWV","NBIS","GLXY","IREN"],
 "Space": ["ASTS","RKLB","WARP","SPCX","UFO"],
 "Quantum": ["IONQ","RGTI","QBTS","QUBT"],
 "Nuclear": ["OKLO","SMR","NNE","LEU"],
 "Fintech/broker": ["SOFI","HOOD","BULL"],
 "Semis": ["NVDA","SMH","MU","DRAM"],
 "Robotics": ["RR","SERV","BOTZ"],
 "Streaming": ["NFLX","SPY"],
}
tick = sorted({t for g in groups.values() for t in g})
px = yf.download(tick, period="1y", auto_adjust=True, progress=False)["Close"]
ret = px.pct_change()
r90 = ret.tail(90)
def stats(t):
    s = px[t].dropna()
    if len(s)<20: return None
    return dict(last=s.iloc[-1], dd=(s.iloc[-1]/s.max()-1)*100, m1=(s.iloc[-1]/s.iloc[-22]-1)*100 if len(s)>22 else np.nan, n=len(s), first=str(s.index[0].date()))
for g,ts in groups.items():
    print(f"\n== {g}")
    for t in ts:
        st=stats(t); print(f"  {t:5} " + (f"${st['last']:.2f}  off-high {st['dd']:.0f}%  1m {st['m1']:+.0f}%  bars {st['n']} since {st['first']}" if st else "NO DATA"))
    for a,b in itertools.combinations(ts,2):
        c=r90[[a,b]].dropna()
        if len(c)>=20:
            beta=np.cov(c[a],c[b])[0,1]/np.var(c[b])
            print(f"   corr90 {a}-{b}: {c[a].corr(c[b]):.2f}  (n={len(c)}, beta {a}/{b} {beta:.2f})")
