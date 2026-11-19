import json,sys
micro="NVDA AAPL TSLA AMZN META GOOGL MSFT MU INTC SPCX AMD BAC BA AVGO CSCO XOM JPM NFLX NEM PLTR PFE WMT".split()
std="ABBV ADBE AMGN AMAT BRK.B BKNG CAT CVX KO CMCSA COP COST LLY HD IBM JNJ LMT MA MCD MRK ORCL PANW PEP PG PLD QCOM CRM SBUX TXN UNH VZ V DIS".split()
opts="AAPL AMZN GOOG GOOGL META MSFT NVDA TSLA AMD AVGO INTC MRVL MU SNDK TSM NFLX ORCL PLTR HOOD BABA BAC F NOK PFE SPY QQQ IWM GLD XLF".split()
kal=open('kalshi.txt').read().split()
ssf=set(micro+std); O=set(opts); K=set(kal)
def chip(t):
    g='GOOGL' if t=='GOOG' else t
    n=(g in ssf)+(t in O or g in O)+(t in K or g in K)
    cls={3:'c3',2:'c2'}.get(n,'c1')
    return f'<span class="chip {cls}">{t}</span>'
def panel(title,sub,names,col):
    return f'<div class="pn" style="--c:{col}"><div class="pt">{title}</div><div class="ps">{sub}</div><div class="chips">{"".join(chip(t) for t in names)}</div></div>'
all3=sorted(t for t in ssf if t in O and t in K)
html=open('rosters.tpl.html').read()
body=(panel(f'CME stock futures · {len(ssf)}',f'{len(micro)} with micros (first block)',micro+std,'#2FD18B')+
      panel(f'Pre-market + late options · {len(opts)}','7:30-9:25 a.m. and 4:00-4:15 p.m. ET',opts,'#6FA8FF')+
      panel(f'Kalshi stock perps · seen live','partial list from Kalshi site',kal,'#FF5D6C'))
html=html.replace('{{BODY}}',body).replace('{{ALL3}}',' · '.join(all3)).replace('{{N3}}',str(len(all3)))
open('rosters.html','w').write(html); print(all3)
