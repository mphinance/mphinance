import { chromium } from 'playwright';
const [,, inp, out] = process.argv;
const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1200,height:800},deviceScaleFactor:2});
await p.goto('file://'+inp); await p.waitForTimeout(1200);
const el = await p.$('.card'); await el.screenshot({path:out}); await b.close();
