import yfinance as yf, numpy as np, itertools
groups={"neocloud":["CRWV","GLXY","IREN","WULF","NBIS"],
"metals":["SLV","GLD","GDX","SIL","AG","PAAS","AEM","NEM","BTG"]}
tick=sorted({t for g in groups.values() for t in g})
px=yf.download(tick,period="1y",auto_adjust=True,progress=False)["Close"]
r=px.pct_change().tail(90)
for g,ts in groups.items():
    print("==",g)
    for t in ts:
        s=px[t].dropna(); print(f"  {t:5} ${s.iloc[-1]:.2f} off-high {(s.iloc[-1]/s.max()-1)*100:.0f}% 1m {(s.iloc[-1]/s.iloc[-22]-1)*100:+.0f}% 3m {(s.iloc[-1]/s.iloc[-64]-1)*100:+.0f}%")
    print("  corr matrix (90d):")
    print(r[ts].corr().round(2).to_string())
    print("  beta vs:")
    for a,b in itertools.permutations(ts,2):
        if b in ("GDX","SLV","GLD","SIL","IREN"):
            c=r[[a,b]].dropna(); print(f"   {a}/{b} {np.cov(c[a],c[b])[0,1]/np.var(c[b]):.2f}", end="")
    print()
