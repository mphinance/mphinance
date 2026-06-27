"""Render a sexy KLineChart candlestick PNG for the article — same lib/style as
the Gamma Map (klinecharts 9.8.10), screenshotted headless via Playwright.

Levels + an optional trendline segment are passed as JSON so each article chart
(DIS reversal-coil, RSI continuation, RKLB pullback) is one config.

  .venv/bin/python tools/kline_chart.py RKLB --config tools/chart_cfgs/RKLB.json --out /tmp
"""
import argparse
import json
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TD_BASE = "https://traderdaddy-pro-whop-production.up.railway.app"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def load_agent_key():
    f = REPO / ".env_agent_api"
    if not f.exists():
        return None
    raw = f.read_text().strip()
    return raw.split("=", 1)[1].strip() if "=" in raw and raw.split("=", 1)[0].isupper() else raw


def fetch_chart_data(symbol, key):
    req = urllib.request.Request(
        f"{TD_BASE}/api/agent/ticker/{symbol}/chart-data",
        headers={"User-Agent": UA, "Accept": "application/json",
                 **({"Authorization": f"Bearer {key}"} if key else {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
<script src="https://unpkg.com/klinecharts@9.8.10/dist/umd/klinecharts.min.js"></script>
<style>
  html,body{margin:0;background:#0a0a0e;color:#e6e6ee;font-family:'JetBrains Mono',monospace}
  .wrap{width:1200px;padding:18px}
  .symrow{display:flex;align-items:baseline;gap:12px;margin-bottom:4px}
  .sym{font-family:'Share Tech Mono',monospace;font-size:30px;letter-spacing:1px}
  .spot{font-size:22px} .spot small{color:#8a8aa0;font-size:12px}
  .chg.pos{color:#00ff88} .chg.neg{color:#ff5c6c} .chg{font-size:18px}
  .read{color:#cfcfe0;font-size:13.5px;margin:6px 2px 12px;line-height:1.5}
  .read b{color:#fff}
  #chart{width:1164px;height:560px;background:#101018;border:1px solid #1c1c28;border-radius:10px}
  .tag{font-family:'Share Tech Mono',monospace;color:#00ff88;font-size:12px;margin-top:8px;letter-spacing:1px}
</style></head><body><div class="wrap">
  <div class="symrow">
    <div class="sym" id="sym"></div><div class="spot" id="spot"></div>
    <div class="chg" id="chg"></div>
  </div>
  <div class="read" id="read"></div>
  <div id="chart"></div>
  <div class="tag">TRADERDADDY PRO · Sam reads the tape</div>
</div>
<script>
const CFG = __CFG__;
const candles = CFG.candles.map(r=>({timestamp:Date.parse(r[0]+'T16:00:00Z'),
  open:r[1],high:r[2],low:r[3],close:r[4],volume:r[5]}));
document.getElementById('sym').textContent = CFG.sym;
document.getElementById('spot').innerHTML = '$'+CFG.spot.toFixed(2)+' <small>spot</small>';
const ce=document.getElementById('chg'); ce.textContent=(CFG.chg>=0?'+':'')+CFG.chg.toFixed(2)+'%';
ce.className='chg '+(CFG.chg>=0?'pos':'neg');
document.getElementById('read').innerHTML = CFG.read || '';

const chart = klinecharts.init('chart',{styles:{
  grid:{horizontal:{color:'#16161f'},vertical:{color:'#16161f'}},
  candle:{type:'candle_solid',
    bar:{upColor:'#00d68f',downColor:'#ff4d6d',upBorderColor:'#00d68f',downBorderColor:'#ff4d6d',upWickColor:'#00d68f',downWickColor:'#ff4d6d'},
    priceMark:{last:{text:{color:'#04130c'}},high:{color:'#8a8aa0'},low:{color:'#8a8aa0'}}},
  xAxis:{axisLine:{color:'#1c1c28'},tickLine:{color:'#1c1c28'},tickText:{color:'#8a8aa0'}},
  yAxis:{axisLine:{color:'#1c1c28'},tickLine:{color:'#1c1c28'},tickText:{color:'#8a8aa0'}},
  indicator:{lastValueMark:{show:false},tooltip:{showRule:'none'}}
}});
chart.applyNewData(candles);
chart.createIndicator({name:'EMA',calcParams:[8,21,55]},true,{id:'candle_pane'});
chart.createIndicator('VOL');

// horizontal labeled level
klinecharts.registerOverlay({name:'lvl',totalStep:1,lock:true,needDefaultPointFigure:false,
  needDefaultXAxisFigure:false,needDefaultYAxisFigure:true,
  createPointFigures:({overlay,coordinates,bounding})=>{
    if(!coordinates[0])return[]; const d=overlay.extendData,y=coordinates[0].y;
    return [
     {type:'line',ignoreEvent:true,attrs:{coordinates:[{x:0,y},{x:bounding.width,y}]},
      styles:{color:d.color,size:d.major?1.6:1,style:d.dash?'dashed':'solid',dashedValue:[6,5]}},
     {type:'text',ignoreEvent:true,attrs:{x:8,y:y-15,text:d.label},
      styles:{color:d.color,size:11.5,family:"'JetBrains Mono',monospace",
        backgroundColor:'#0a0a0ee6',paddingLeft:5,paddingRight:5,paddingTop:2,paddingBottom:2}}];
  }});
// two-point trendline
klinecharts.registerOverlay({name:'trend',totalStep:1,lock:true,needDefaultPointFigure:false,
  needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{
    if(coordinates.length<2)return[]; const d=overlay.extendData;
    const figs=[{type:'line',ignoreEvent:true,attrs:{coordinates:[coordinates[0],coordinates[1]]},
      styles:{color:d.color,size:1.8,style:d.dash?'dashed':'solid',dashedValue:[7,5]}}];
    if(d.label)figs.push({type:'text',ignoreEvent:true,
      attrs:{x:coordinates[1].x-d.label.length*7-6,y:coordinates[1].y-18,text:d.label},
      styles:{color:d.color,size:11.5,family:"'JetBrains Mono',monospace",
        backgroundColor:'#0a0a0ee6',paddingLeft:5,paddingRight:5,paddingTop:2,paddingBottom:2}});
    return figs;
  }});
(CFG.levels||[]).forEach(l=>chart.createOverlay({name:'lvl',points:[{value:l.price}],extendData:l}));
(CFG.segments||[]).forEach(s=>chart.createOverlay({name:'trend',
  points:[{timestamp:Date.parse(s.p0[0]+'T16:00:00Z'),value:s.p0[1]},
          {timestamp:Date.parse(s.p1[0]+'T16:00:00Z'),value:s.p1[1]}],extendData:s}));
window.__ready=true;
</script></body></html>"""


def build(sym, cfg_path, out_dir):
    key = load_agent_key()
    d = fetch_chart_data(sym, key)
    rows = d.get("chartData") or []
    candles = [[r["date"][:10], float(r["open"]), float(r["high"]), float(r["low"]),
                float(r["close"]), float(r["volume"])] for r in rows]
    cfg = {"sym": sym, "spot": float(d.get("currentPrice")), "chg": float(d.get("changePercent") or 0),
           "candles": candles, "read": "", "levels": [], "segments": []}
    if cfg_path and Path(cfg_path).exists():
        cfg.update(json.loads(Path(cfg_path).read_text()))
        cfg["candles"] = candles  # always live candles
        cfg["spot"] = float(d.get("currentPrice")); cfg["chg"] = float(d.get("changePercent") or 0)
    html = HTML.replace("__CFG__", json.dumps(cfg))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    htmlp = out / f"{sym}_kline.html"
    htmlp.write_text(html)
    return htmlp


def shoot(htmlp, out_dir, sym):
    from playwright.sync_api import sync_playwright
    png = Path(out_dir) / f"{sym}_kline.png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1240, "height": 720}, device_scale_factor=2)
        pg.goto(f"file://{htmlp}")
        pg.wait_for_function("window.__ready===true", timeout=15000)
        pg.wait_for_timeout(1200)
        pg.locator(".wrap").screenshot(path=str(png))
        b.close()
    return png


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--config", default=None)
    ap.add_argument("--out", default="/tmp/kline")
    a = ap.parse_args()
    hp = build(a.symbol.upper(), a.config, a.out)
    pngp = shoot(hp, a.out, a.symbol.upper())
    print(f"{a.symbol.upper()}\t{pngp}")
