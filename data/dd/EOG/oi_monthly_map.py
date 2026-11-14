import json, numpy as np, pandas as pd, yfinance as yf, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as md
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter1d
import matplotlib.patheffects as pe
OUT=[pe.withStroke(linewidth=3.5,foreground='#0b0d12')]
oi=json.load(open("oi.json")); SPOT=158.32; TODAY=pd.Timestamp("2026-11-14")
MON=["2026-11-20","2026-12-18","2027-01-15","2027-03-19"]
YLO,YHI=118,202
d=yf.download("EOG",period="1y",auto_adjust=False,progress=False); d.columns=[c[0] for c in d.columns]; d=d.tail(90)
BG="#0b0d12"; GRN="#19d38b"; RED="#ff4d6d"; GOLD="#f2c14e"; DIM="#8a90a0"
fig,ax=plt.subplots(figsize=(18,10),dpi=150); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
# heat: OI still alive (monthlies only) per strike per future day
strikes=np.arange(YLO,YHI+0.01,0.5); days=pd.date_range(TODAY,pd.Timestamp("2027-03-26"))
grid=np.zeros((len(strikes),len(days)))
prof={}
for ex in MON:
    v=np.zeros(len(strikes))
    for side in ("c","p"):
        for k,n in oi[ex][side].items():
            k=float(k)
            if YLO<=k<=YHI: v[int(round((k-YLO)/0.5))]+=n
    prof[ex]=gaussian_filter1d(v,6)
for j,t in enumerate(days):
    for ex in MON:
        if pd.Timestamp(ex)>=t: grid[:,j]+=prof[ex]
grid=grid/np.maximum(grid.max(axis=0,keepdims=True),1e-9)
cmap=LinearSegmentedColormap.from_list("h",[BG,"#123b3a","#1f6f63","#c9a227","#ffd166"])
x0,x1=md.date2num(days[0]),md.date2num(days[-1])
ax.imshow(grid,origin="lower",aspect="auto",extent=[x0,x1,YLO,YHI],cmap=cmap,alpha=0.85,interpolation="bilinear",zorder=0)
# candles
for t,r in d.iterrows():
    c=GRN if r.Close>=r.Open else RED; x=md.date2num(t)
    ax.plot([x,x],[r.Low,r.High],color=c,lw=1,zorder=2)
    ax.add_patch(plt.Rectangle((x-0.35,min(r.Open,r.Close)),0.7,max(abs(r.Close-r.Open),0.05),color=c,zorder=3))
ax.axvline(md.date2num(TODAY),color="#3a3f4b",lw=1)
ax.axhline(SPOT,color="white",lw=1,ls=":",alpha=0.6); ax.text(md.date2num(TODAY)-1,SPOT+0.7,f"spot {SPOT}",color="white",fontsize=11,ha="right")
ax.axhline(165.93,color=GOLD,lw=0.8,ls="--",alpha=0.5); ax.text(md.date2num(d.index[0]),166.6,"all-time high 165.93",color=GOLD,fontsize=10,alpha=0.8)
# bubbles
fmt=lambda n:f"{n/1000:.1f}k" if n>=1000 else str(n)
for ex in MON:
    x=md.date2num(pd.Timestamp(ex))
    ax.axvline(x,color="#2a2f3a",lw=0.8,zorder=1)
    tot=sum(oi[ex]["c"].values())+sum(oi[ex]["p"].values())
    ax.text(x,YHI+0.8,f"{pd.Timestamp(ex):%b %d}\n{fmt(tot)} contracts",color="white",ha="center",va="bottom",fontsize=12,fontweight="bold",clip_on=False)
    for side,col,dx in (("c",GRN,3.5),("p",RED,-3.5)):
        items=[(float(k),n) for k,n in oi[ex][side].items() if n>=150 and YLO<=float(k)<=YHI]
        top=sorted(items,key=lambda z:-z[1])[:3]
        for k,n in items:
            ax.scatter(x+dx,k,s=n*0.55,color=col,alpha=0.55,edgecolor=col,lw=1.2,zorder=4)
        for k,n in top:
            ax.text(x+dx+(3+np.sqrt(n)*0.11 if side=="c" else -3-np.sqrt(n)*0.11),k,f"{fmt(n)} @ {k:g}",color=col,fontsize=11,fontweight="bold",va="center",ha="left" if side=="c" else "right",zorder=6,path_effects=OUT)
ax.set_ylim(YLO,YHI); ax.set_xlim(md.date2num(d.index[0])-1,x1+16)
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(colors=DIM,labelsize=12); ax.xaxis.set_major_locator(md.MonthLocator()); ax.xaxis.set_major_formatter(md.DateFormatter("%b")); ax.yaxis.tick_right()
ax.grid(axis="y",color="#1c2029",lw=0.6)
fig.text(0.04,0.94,"EOG: where the open interest sits, monthly expirations to March",color="white",fontsize=26,fontweight="bold")
fig.text(0.04,0.905,"Bubbles = open interest per strike (green calls, red puts), top 3 labelled. Glow = where the monthly OI still open on each date is concentrated.",color=DIM,fontsize=13)
fig.text(0.04,0.02,"Source: yfinance option chains, 11/13 close. Deep puts off the chart: 859 @ 110 and 606 @ 100 (Dec), 2.0k @ 100 and 1.5k @ 105 (Jan). Open interest is not a direction call.   ·   mphinance",color="#5b6070",fontsize=11)
plt.subplots_adjust(left=0.03,right=0.95,top=0.84,bottom=0.06)
plt.savefig("/home/mph/mphinance/data/dd/EOG/img/EOG_oi_monthly.png",facecolor=BG)
