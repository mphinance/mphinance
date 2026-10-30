import { chromium } from 'playwright';
import fs from 'fs'; import { execSync } from 'child_process';
const D='/home/mph/mphinance/docs/articles/capex-nvda', OUT=D+'/images', F='/tmp/harvest/frames2';
fs.mkdirSync(F,{recursive:true}); for (const f of fs.readdirSync(F)) fs.unlinkSync(F+'/'+f);
const b=await chromium.launch();
let pg=await b.newPage({viewport:{width:1456,height:900}});
await pg.goto('file://'+D+'/html/stress.html'); await pg.waitForTimeout(300);
await pg.screenshot({path:OUT+'/02-stress-test.png'});
pg=await b.newPage({viewport:{width:1456,height:1000}});
await pg.goto('file://'+D+'/html/flow.html'); await pg.waitForTimeout(300);
await pg.screenshot({path:OUT+'/01-follow-100b.png'});
const N=72; for(let i=0;i<=N;i++){ await pg.evaluate(t=>setT(t), i/N); await pg.screenshot({path:`${F}/f${String(i).padStart(3,'0')}.png`}); }
for(let j=1;j<=30;j++) fs.copyFileSync(`${F}/f${String(N).padStart(3,'0')}.png`,`${F}/f${String(N+j).padStart(3,'0')}.png`);
await b.close();
execSync(`ffmpeg -loglevel error -y -framerate 18 -i ${F}/f%03d.png -vf "scale=1100:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=sierra2_4a" ${OUT}/03-follow-100b.gif`);
console.log(fs.readdirSync(OUT).map(f=>f+' '+fs.statSync(OUT+'/'+f).size).join('\n'));
