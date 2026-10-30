import yfinance as yf, numpy as np, pandas as pd
pop="NVDA AAPL TSLA MU INTC AMZN META NBIS SPCX AMD ASTS MSFT PLTR GOOGL IREN AVGO BE RKLB HOOD SNDK ONDS CRWV VST SOFI NFLX WMT ORCL MSTR AAOI MRVL COIN CIFR DELL MRNA CRWD SMCI NOW QCOM ARM APLD UBER PANW CRDO TSM RDDT RDW NOK LLY LRCX SMR NVTS UMAC BULL WDC USO GLXY OKLO IONQ RGTI QBTS ACHR JOBY LITE HIMS".split()
etf="SPY QQQ IWM XLK SMH SOXX IGV CIBR SKYY XLC XLY XLE XLV XLF XLU XLI ARKK IBIT WGMI URA NLR UFO WARP DRAM QTUM BOTZ FINX BLOK TAN GRID MAGS XBI IBB GLD SLV GDX".split()
allt=sorted(set(pop+etf))
px=yf.download(allt,period="1y",auto_adjust=True,progress=False)["Close"]
r=px.pct_change().tail(90); C=r.corr()
rows=[]
for t in pop:
    s=px[t].dropna()
    if len(s)<60: continue
    dd=(s.iloc[-1]/s.max()-1)*100; m1=(s.iloc[-1]/s.iloc[-22]-1)*100
    c=C[t].drop(t).dropna().sort_values(ascending=False)
    # exclude near-duplicates of same company
    c=c.drop([x for x in ["GOOG"] if x in c.index],errors="ignore")
    top=c.head(3)
    cous=", ".join(f"{k} {v:.2f} (β{r[t].cov(r[k])/r[k].var():.2f})" for k,v in top.items())
    rows.append((dd,t,m1,cous))
for dd,t,m1,cous in sorted(rows):
    print(f"{t:5} off-high {dd:4.0f}%  1m {m1:+4.0f}%  | {cous}")
