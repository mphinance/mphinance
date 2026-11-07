import yfinance as yf, pandas as pd, numpy as np
H=20
tk=['TSLA','HUM','PCVX','FNF','SPY','QQQ']
D={}
for t in tk:
    d=yf.download(t,period='5y',auto_adjust=False,progress=False)
    d.columns=d.columns.get_level_values(0); D[t]=d
def atr14(d):
    h,l,c=d.High,d.Low,d.Close
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/14,adjust=False).mean()
# plan: entry, stop, T1, size(R fraction)
PL={'TSLA':(353.5,335.0,385.19,0.5),'HUM':(414.93,399.35,433.21,0.25),
    'PCVX':(65.88,59.19,72.89,0.25),'FNF':(41.24,38.46,44.11,0.25)}
def sim(d,i,entry,sd,td):
    """enter at entry price after bar i; walk bars i+1..i+H. stop first on ties."""
    stop=entry-sd; tgt=entry+td
    for k in range(i+1,min(i+H,len(d)-1)+1):
        lo,hi=d.Low.iloc[k],d.High.iloc[k]
        if lo<=stop: return 'stop',-1.0
        if hi>=tgt: return 'T1',td/sd
    if i+H>len(d)-1: return None,None  # incomplete window
    return 'none',(d.Close.iloc[i+H]-entry)/sd
def summarize(res,size):
    res=[r for r in res if r[0] is not None]
    n=len(res)
    if n==0: return dict(n=0)
    o=[r[0] for r in res]; R=np.array([r[1] for r in res])
    return dict(n=n,T1=o.count('T1'),stop=o.count('stop'),none=o.count('none'),
        meanR=R.mean(),se=R.std(ddof=1)/np.sqrt(n) if n>1 else np.nan,sizedR=R.mean()*size)
out=[]
def fmt(s):
    if s['n']==0: return 'n=0'
    n=s['n']
    return (f"n={n}, T1 first {s['T1']} ({s['T1']/n:.0%}), stop first {s['stop']} ({s['stop']/n:.0%}), "
            f"neither {s['none']} ({s['none']/n:.0%}), mean R/trade {s['meanR']:+.3f} (se {s['se']:.3f}), at plan size {s['sizedR']:+.3f}"
            + ("  [n<20: MEANINGLESS]" if n<20 else ""))
summ={}
for t,(e,s,t1,size) in PL.items():
    d=D[t]; a=atr14(d); c=d.Close
    cur=c.iloc[-1]; A=a.iloc[-1]
    sd_m=(e-s)/A; td_m=(t1-e)/A
    sma50=c.rolling(50).mean()
    out.append(f"\n## {t}\nPlan entry {e}, stop {s}, T1 {t1}; today's close {cur:.2f}, ATR14 {A:.2f}. Stop = {sd_m:.2f} ATR, T1 = {td_m:.2f} ATR from entry; plan T1 R = {td_m/sd_m:.2f}; plan size {size}R. Bars: {len(d)} ({d.index[0].date()} to {d.index[-1].date()}).")
    # skip first 60 bars for warmup; exclude last signals via incomplete window handling
    sig=[];
    for i in range(60,len(d)-1):
        pc=c.iloc[i-1]; ap=a.iloc[i-1]
        if t=='TSLA':
            zh=pc-0.3*ap; zl=pc-1.0*ap
            if d.Low.iloc[i]<=zh and c.iloc[i]>=zl and c.iloc[i]<sma50.iloc[i]:
                sig.append((i,c.iloc[i],a.iloc[i]))
        elif t in('HUM','FNF'):
            dist=(cur-e)/A
            lim=pc-dist*ap
            if d.Low.iloc[i]<=lim:
                fill=min(lim,d.Open.iloc[i]); sig.append((i,fill,ap))
        elif t=='PCVX':
            if c.iloc[i]>c.iloc[i-20:i].max():
                sig.append((i,c.iloc[i],a.iloc[i]))
    # non-overlapping: skip signals within H bars of an accepted one (independent trades)
    def run(sg,overlap):
        res=[];last=-99
        for i,en,aa in sg:
            if not overlap and i<last+H: continue
            r=sim(d,i,en,sd_m*aa,td_m*aa); 
            if r[0] is None: continue
            res.append(r); last=i
        return res
    s_all=run(sig,True); s_ind=run(sig,False)
    out.append(f"Signals fired (all bars): {len(sig)}. Setup, all signals (overlapping, clustered): {fmt(summarize(s_all,size))}")
    out.append(f"Setup, non-overlapping (one trade per {H} sessions): {fmt(summarize(s_ind,size))}")
    # baseline: every day entry at close, same ATR multiples
    base=[]
    for i in range(60,len(d)-1):
        r=sim(d,i,c.iloc[i],sd_m*a.iloc[i],td_m*a.iloc[i])
        if r[0] is not None: base.append(r)
    bs=summarize(base,size)
    out.append(f"Random-day baseline (every day, entered at close): {fmt(bs)}")
    # random sample of 1 per 20 days for independent count
    bi=[];rng=np.random.default_rng(0)
    for i in range(60,len(d)-1-H,H):
        r=sim(d,i,c.iloc[i],sd_m*a.iloc[i],td_m*a.iloc[i]); bi.append(r)
    out.append(f"Baseline, every {H}th day (independent): {fmt(summarize(bi,size))}")
    si=summarize(s_ind,size)
    if si['n']>1:
        diff=si['meanR']-bs['meanR']; z=diff/np.sqrt(si['se']**2+bs['se']**2*0+ (si['se']**2*0)) if False else diff/si['se']
        out.append(f"Setup minus baseline (non-overlap setup vs all-day baseline): {diff:+.3f} R, approx t {z:.2f} on setup n={si['n']}")
    summ[t]=(si,bs,sd_m,td_m)
# correlations
r=pd.DataFrame({t:D[t].Close.pct_change() for t in tk}).dropna().tail(126)
cm=r.corr()
out.append("\n## Pairwise correlation of daily returns, last 126 sessions (n=%d, ending %s)\n"%(len(r),r.index[-1].date()))
out.append("```\n"+cm.round(2).to_string()+"\n```")
txt="# Quant lens, data as of 2026-11-06 close\n\nMethod: yfinance, auto_adjust=False, 5y daily. ATR14 Wilder, taken at the signal bar (no lookahead). Stop and T1 expressed in ATR multiples of today's plan, applied to each historical entry. Outcome window 20 sessions after entry; if stop and T1 are both inside one bar the stop counts first. 'Neither' is marked to the day 20 close in R. Unit R = stop distance. Entry rules: TSLA dip to 0.3-1.0 ATR under prior close, close at or above zone low, close under 50-day, enter at that close; HUM/FNF pullback limit at the plan's ATR distance below prior close (fill at limit, or open if gapped lower); PCVX close above prior 20-day closing high, enter at that close. TSLA plan entry taken as zone midpoint 353.5. Plan size multiplies R. T2 for TSLA not tested. Script: quant.py in this folder.\n"+"\n".join(out)+"\n"
open('/home/mph/mphinance/data/watchlists/2026-11/lenses/quant.md','w').write(txt)
print(txt)
