// stock-recap / detectors/downtrend.mjs
// Merged downtrend-breakout + failed-breakdown-spring detectors.
//
// "Convex-hull anchor + robust upper-envelope fit + backward-streak freshness."
//   - Convex-hull peak/lower-high geometry (the ceiling the eye draws), O(pivots).
//   - Theil-Sen robust line fit + multi-anchor fallback (outlier-resistant, no dead lines).
//   - 2-of-3 confirmation (vol / RSI / EMA) — forgiving, realistic.
//   - Backward-streak freshness + line-at-now clearance (fixes the two named bugs).
//
// PURE functions over one OHLC array of {date,open,high,low,close,volume,ema8,ema21,
// ema55,sma200,rsi,atr,...}. NEVER throws — every failure path returns null. Every
// indicator read is null-guarded (ema/sma200/rsi/adx can be null early in a 300-bar
// fetch). ATR is self-computed so it is always present.

// ---- tunables --------------------------------------------------------------
const N = 300;
const K_PIVOT = 3;
const MIN_SPAN = 40;
const MIN_AGE = 40;
const MIN_TOUCHES = 3;
const SLOPE_LO = 0.12, SLOPE_HI = 3.0;     // %/bar
const DECLINE_LO = 0.12, DECLINE_HI = 0.55;
const FRESH_MAX = 3;
const CHASE_MAX = 8;                        // clearance % beyond which -> extended
const EXT_MAX = 45;                         // clearance % beyond which -> drop
const VOL_CONFIRM = 1.3;
const MAX_ANCHORS = 2;

// ---- tiny math helpers -----------------------------------------------------
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const numOr = (v) => (isNum(v) ? v : (v == null ? null : (Number.isFinite(Number(v)) ? Number(v) : null)));
function median(arr) {
  const a = arr.filter(isNum).slice().sort((x, y) => x - y);
  if (!a.length) return null;
  const m = a.length >> 1;
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// ---- ATR (Wilder 14, backfilled) ------------------------------------------
// Use the candles' own .atr if every bar carries a finite value; otherwise
// compute Wilder ATR(14) over the window and backfill the warmup bars so even
// early bars are usable.
function atrSeries(c) {
  const n = c.length;
  const carried = c.map((b) => numOr(b.atr));
  if (carried.every(isNum)) return carried;
  const tr = new Array(n);
  for (let i = 0; i < n; i++) {
    const h = numOr(c[i].high), l = numOr(c[i].low);
    if (!isNum(h) || !isNum(l)) { tr[i] = null; continue; }
    if (i === 0) { tr[i] = h - l; continue; }
    const pc = numOr(c[i - 1].close);
    tr[i] = isNum(pc) ? Math.max(h - l, Math.abs(h - pc), Math.abs(l - pc)) : (h - l);
  }
  const atr = new Array(n).fill(null);
  if (n < 15) { // too short for a proper Wilder seed — fall back to mean TR
    const mt = median(tr) ?? 0;
    return atr.map(() => mt || null);
  }
  let seed = 0, cnt = 0;
  for (let i = 1; i <= 14; i++) if (isNum(tr[i])) { seed += tr[i]; cnt++; }
  seed = cnt ? seed / cnt : (tr[14] ?? 0);
  atr[14] = seed;
  for (let i = 15; i < n; i++) atr[i] = (atr[i - 1] * 13 + (isNum(tr[i]) ? tr[i] : atr[i - 1])) / 14;
  for (let i = 0; i < 14; i++) atr[i] = atr[14];
  return atr;
}

// ---- fractal pivots (plateau-safe) ----------------------------------------
function pivotHighs(c, k) {
  const n = c.length, out = [];
  for (let i = k; i <= n - 1 - k; i++) {
    const hi = numOr(c[i].high);
    if (!isNum(hi)) continue;
    let ok = true, gtLeft = false, gtRight = false;
    for (let j = i - k; j <= i + k && ok; j++) {
      if (j === i) continue;
      const hj = numOr(c[j].high);
      if (!isNum(hj)) { ok = false; break; }
      if (hj > hi) { ok = false; break; }
      if (j < i && hi > hj) gtLeft = true;
      if (j > i && hi > hj) gtRight = true;
    }
    if (ok && gtLeft && gtRight) out.push({ x: i, y: hi });
  }
  return out;
}
function pivotLows(c, k) {
  const n = c.length, out = [];
  for (let i = k; i <= n - 1 - k; i++) {
    const lo = numOr(c[i].low);
    if (!isNum(lo)) continue;
    let ok = true, ltLeft = false, ltRight = false;
    for (let j = i - k; j <= i + k && ok; j++) {
      if (j === i) continue;
      const lj = numOr(c[j].low);
      if (!isNum(lj)) { ok = false; break; }
      if (lj < lo) { ok = false; break; }
      if (j < i && lo < lj) ltLeft = true;
      if (j > i && lo < lj) ltRight = true;
    }
    if (ok && ltLeft && ltRight) out.push({ x: i, y: lo });
  }
  return out;
}

// ---- upper convex hull (Andrew monotone chain, clockwise turns) -----------
const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
function upperHull(points) {
  const pts = points.slice().sort((p, q) => p.x - q.x || p.y - q.y);
  const h = [];
  for (const p of pts) {
    while (h.length >= 2 && cross(h[h.length - 2], h[h.length - 1], p) >= 0) h.pop();
    h.push(p);
  }
  return h;
}

// ---- Theil-Sen robust line fit --------------------------------------------
function theilSen(points) {
  const slopes = [];
  for (let i = 0; i < points.length; i++)
    for (let j = i + 1; j < points.length; j++) {
      const dx = points[j].x - points[i].x;
      if (dx !== 0) slopes.push((points[j].y - points[i].y) / dx);
    }
  const m = median(slopes);
  if (!isNum(m)) return null;
  const b = median(points.map((p) => p.y - m * p.x));
  if (!isNum(b)) return null;
  return { m, b };
}

// ===========================================================================
// detectDowntrendBreakout
// ===========================================================================
export function detectDowntrendBreakout(candles, opts = {}) {
  try {
    if (!Array.isArray(candles) || candles.length < 120) return null;
    const c = candles.slice(-N);
    const last = c.length - 1;
    const px = numOr(c[last].close);
    const atr = atrSeries(c);
    const atrNow = atr[last];
    if (!isNum(atrNow) || !isNum(px) || px <= 0) return null;
    const atrPct = atrNow / px;

    const TOUCH_TOL = 0.6 * atrNow;
    const LIFT_TOL = 0.25 * atrNow;
    const BREAK_BUF = Math.max(0.25 * atrNow, 0.003 * px);

    const pivots = pivotHighs(c, K_PIVOT);
    if (pivots.length < 3) return null;
    const hull = upperHull(pivots);
    const m = hull.length - 1;
    if (m < 1) return null;

    // candidate peak anchors: hull vertices in the older 70%, that leave room to
    // descend and are at least MIN_AGE bars back. Sorted strongest-peak-first.
    const cutoff = Math.floor(N * 0.7);
    const cands = [];
    for (let p = 0; p < m; p++) {
      const v = hull[p];
      if (v.x <= cutoff && (last - v.x) >= MIN_AGE) cands.push(p);
    }
    cands.sort((a, b) => hull[b].y - hull[a].y);
    if (!cands.length) return null;

    let best = null;
    let attempts = 0;
    for (const peakPos of cands) {
      if (attempts >= MAX_ANCHORS) break;
      attempts++;
      const res = evalAnchor({ c, last, px, atr, atrNow, atrPct, hull, m, peakPos, pivots,
        TOUCH_TOL, LIFT_TOL, BREAK_BUF, opts });
      if (!res) continue;
      // prefer a fresh actionable fire; then higher score.
      const freshFire = res.tier === 'confirmed' && res.bars_since_break != null && res.bars_since_break <= FRESH_MAX;
      res._freshFire = freshFire;
      if (!best) { best = res; if (freshFire) break; continue; }
      const bestFresh = best._freshFire;
      if (freshFire && !bestFresh) { best = res; break; }
      if (freshFire === bestFresh && res.dtbScore > best.dtbScore) best = res;
      if (best._freshFire) break;
    }
    if (best) delete best._freshFire;
    return best;
  } catch { return null; }
}

function evalAnchor(ctx) {
  const { c, last, px, atr, atrNow, hull, m, peakPos, pivots, TOUCH_TOL, LIFT_TOL, BREAK_BUF, opts } = ctx;
  const DBG = opts && opts.debug;
  const rej = (r) => { if (DBG) console.error(`  [anchor x=${hull[peakPos].x}] reject: ${r}`); return null; };
  const A = hull[peakPos];
  const active = hull.slice(peakPos + 1, m + 1); // post-peak lower-highs
  if (!active.length) return rej('no active vertices');

  // Step 5 — resistance ray = the convex-hull EDGE from the major peak (the line
  // the eye draws). slope* = max over later pivots of slope_to(p) = the flattest
  // descending line through A that keeps every later swing-high at or below it
  // (no pierce by construction, the binding pivot kisses it). Fitting Theil-Sen
  // over ALL hull vertices + lifting would only touch the concave bulge of an
  // accelerating downtrend, so we anchor on the hull edge first, then optionally
  // refine with Theil-Sen over the points that actually touch.
  const laterP = pivots.filter((p) => p.x > A.x + K_PIVOT);
  if (!laterP.length) return rej('no later pivots');
  let slope = -Infinity, bind = null;
  for (const p of laterP) {
    const s = (p.y - A.y) / (p.x - A.x);
    if (s > slope) { slope = s; bind = p; }
  }
  if (!isNum(slope) || slope >= 0 || !bind) return rej('slope>=0 (peak not dominant)');
  let b = A.y - slope * A.x;          // line through A with slope*
  let line = (x) => slope * x + b;

  const inRange = pivots.filter((p) => p.x >= A.x);
  // robustness refine: Theil-Sen over the primary line's touchers, re-lift, accept
  // only if it pierces nothing and keeps at least as many touches.
  let touchers = inRange.filter((p) => Math.abs(p.y - line(p.x)) <= TOUCH_TOL);
  if (touchers.length >= 3) {
    const fit = theilSen(touchers);
    if (fit && fit.m < 0) {
      let rl = fit.m, rb = fit.b, maxR = -Infinity;
      for (const p of touchers) maxR = Math.max(maxR, p.y - (rl * p.x + rb));
      rb += maxR;
      const rline = (x) => rl * x + rb;
      const pierce = inRange.some((p) => p.y - rline(p.x) > TOUCH_TOL);
      const rTouch = inRange.filter((p) => Math.abs(p.y - rline(p.x)) <= TOUCH_TOL).length;
      if (!pierce && rl < 0 && rTouch >= touchers.length) { slope = rl; b = rb; line = rline; }
    }
  }

  // final touchers + newer anchor B = farthest-right toucher
  const finalTouch = inRange.filter((p) => Math.abs(p.y - line(p.x)) <= TOUCH_TOL);
  if (finalTouch.length < MIN_TOUCHES) return rej('touches ' + finalTouch.length);
  let B = finalTouch.reduce((a, p) => (p.x > a.x ? p : a), A);

  const span = B.x - A.x;
  if (span < MIN_SPAN) return rej('span ' + span + '<40');
  if ((last - A.x) < MIN_AGE) return rej('age');

  const meanPivotPrice = finalTouch.reduce((s, p) => s + p.y, 0) / finalTouch.length;
  const slopePctBar = meanPivotPrice ? slope / meanPivotPrice * 100 : 0;
  if (Math.abs(slopePctBar) < SLOPE_LO || Math.abs(slopePctBar) > SLOPE_HI) return rej('slope ' + slopePctBar.toFixed(3));

  // ceiling integrity over [A.x .. B.x]: no pivot in the trendline region may
  // pierce the line by > TOUCH_TOL. Pivots AFTER B are the breakout itself and
  // are allowed to pierce.
  let touches = 0;
  const residTouch = [];
  for (const p of inRange) {
    if (p.x > B.x) continue;
    const r = p.y - line(p.x);
    if (r > TOUCH_TOL) return rej('ceiling pierce by ' + r.toFixed(2));
    if (Math.abs(r) <= TOUCH_TOL) { touches++; residTouch.push(Math.abs(r)); }
  }
  if (touches < MIN_TOUCHES) return rej('touches(span) ' + touches);
  const fitErr = median(residTouch);
  if (!isNum(fitErr) || fitErr > 0.6 * atrNow) return rej('fitErr ' + (fitErr == null ? 'na' : fitErr.toFixed(2)));

  // decline gate
  let minLow = Infinity;
  for (let i = A.x; i <= last; i++) { const lo = numOr(c[i].low); if (isNum(lo) && lo < minLow) minLow = lo; }
  if (!isNum(minLow) || minLow === Infinity) return rej('minLow');
  const decline = (A.y - minLow) / A.y;
  if (decline < DECLINE_LO || decline > DECLINE_HI) return rej('decline '+decline.toFixed(3));

  // indicator reads (null-guarded)
  const close = (i) => numOr(c[i]?.close);
  const ema8 = (i) => numOr(c[i]?.ema8);
  const ema21 = (i) => numOr(c[i]?.ema21);
  const ema55 = (i) => numOr(c[i]?.ema55);
  const sma200 = numOr(c[last]?.sma200);
  const rsiAt = (i) => numOr(c[i]?.rsi);

  const e21 = ema21(last), e55 = ema55(last), cl = close(last);
  const uptrendStack = isNum(cl) && isNum(e21) && isNum(e55) &&
    cl > e21 && e21 > e55 && (sma200 == null || cl > sma200);

  // Step 7 — fresh break trigger (backward-streak scan, line-at-now clearance).
  const lineToday = line(last);
  // A steep multi-month decline can extrapolate the resistance line to <=0 at "now",
  // which sign-flips clearance_pct and mislabels an extended name as a retest. Bail.
  if (!isNum(lineToday) || lineToday <= 0) return rej('lineToday<=0');
  let breakIdx = null;
  if (cl != null && cl > lineToday + BREAK_BUF) {
    breakIdx = last;
    for (let i = last - 1; i > B.x; i--) {
      const ci = close(i);
      if (ci != null && ci > line(i) + BREAK_BUF) breakIdx = i; else break;
    }
  }
  const bars_since_break = breakIdx != null ? last - breakIdx : null;
  const clearance_pct = (px / lineToday - 1) * 100;
  const aboveLine = cl != null && cl > lineToday + BREAK_BUF;

  // NOT-A-PULLBACK / uptrend-continuation reject (needs break info)
  if (uptrendStack && bars_since_break != null && bars_since_break > FRESH_MAX) return rej('uptrend continuation');

  // Step 8 — 2-of-3 confirmation
  let vol_ratio = null;
  {
    const endIdx = (breakIdx != null ? breakIdx : last) - 1;
    if (endIdx >= 20) {
      let s = 0, n2 = 0;
      for (let i = endIdx - 19; i <= endIdx; i++) { const v = numOr(c[i].volume); if (isNum(v)) { s += v; n2++; } }
      const avg = n2 ? s / n2 : null;
      if (isNum(avg) && avg > 0) {
        let mx = 0;
        for (let i = Math.max(0, last - 2); i <= last; i++) { const v = numOr(c[i].volume); if (isNum(v)) mx = Math.max(mx, v / avg); }
        vol_ratio = mx;
      }
    }
  }
  const volOK = isNum(vol_ratio) && vol_ratio >= VOL_CONFIRM;
  const rsiNow = rsiAt(last), rsi3 = rsiAt(last - 3);
  const rsiOK = isNum(rsiNow) && rsiNow > 50 && isNum(rsi3) && rsiNow > rsi3;
  const e8 = ema8(last);
  const emaOK = isNum(cl) && isNum(e8) && isNum(e21) && cl > e8 && e8 >= e21;
  const confirms = (volOK ? 1 : 0) + (rsiOK ? 1 : 0) + (emaOK ? 1 : 0);

  const notUptrendCont = !(uptrendStack && bars_since_break != null && bars_since_break > FRESH_MAX);
  const lineVsClose = (px / lineToday - 1) * 100;

  // Step 9 — tier
  let tier = null;
  if (aboveLine) {
    if (bars_since_break != null && bars_since_break <= FRESH_MAX &&
        clearance_pct > 0 && clearance_pct <= CHASE_MAX && confirms >= 2 && notUptrendCont) {
      tier = 'confirmed';
    } else if (clearance_pct <= 0.3) {
      tier = 'retest';
    } else if (clearance_pct > CHASE_MAX && clearance_pct <= EXT_MAX) {
      tier = 'extended';
    } else if (bars_since_break != null && bars_since_break > FRESH_MAX && clearance_pct <= EXT_MAX) {
      tier = 'extended';
    } else {
      return rej('clearance>'+EXT_MAX+' = '+clearance_pct.toFixed(1)); // dropped
    }
  } else if (lineVsClose >= -2.5 && lineVsClose <= 0.3 && !uptrendStack) {
    tier = 'forming';
  } else {
    return rej('no tier: aboveLine='+aboveLine+' lineVsClose='+lineVsClose.toFixed(2)+' bars='+bars_since_break+' clr='+clearance_pct.toFixed(2)+' confirms='+confirms);
  }

  const dtbFresh = bars_since_break != null && bars_since_break <= 5;

  // Step 10 — score
  const lineQ = Math.min((touches - 2) * 8, 16) + Math.min(span / 120 * 8, 8) +
    Math.min(Math.abs(slopePctBar) / 1.0 * 6, 6);
  const freshTable = [20, 16, 10, 5];
  const fresh = bars_since_break == null ? 0 :
    (freshTable[Math.min(bars_since_break, 3)] - Math.min(Math.max(clearance_pct, 0), 8) * 0.9);
  const vol = isNum(vol_ratio) ? Math.min(Math.max(vol_ratio - 1, 0) / 0.7, 1) * 20 : 0;
  const e8prev = ema8(last - 3);
  const momo = (rsiOK ? 6 : 0) + (emaOK ? 5 : 0) + ((isNum(e8) && isNum(e8prev) && e8 > e8prev) ? 4 : 0);
  let ctx15 = 0;
  // decline sweet-spot 0.15-0.40 -> up to +8, taper to 0 at 0.12 / 0.55
  if (decline >= 0.15 && decline <= 0.40) ctx15 += 8;
  else if (decline >= 0.12 && decline < 0.15) ctx15 += 8 * (decline - 0.12) / 0.03;
  else if (decline > 0.40 && decline <= 0.55) ctx15 += 8 * (0.55 - decline) / 0.15;
  if (opts.gex?.aboveFlip === true) ctx15 += 4;
  if (opts.earningsDaysAway == null || opts.earningsDaysAway > 5) ctx15 += 3;
  const dtbScore = clamp(Math.round(lineQ + fresh + vol + momo + ctx15), 0, 100);

  return {
    ticker: opts.ticker || null,
    signal_type: 'downtrend_break',
    tier,
    breakout: tier === 'confirmed',
    dtbScore,
    dtbFresh,
    older_anchor: { date: c[A.x]?.date ?? null, price: A.y },
    newer_anchor: { date: c[B.x]?.date ?? null, price: B.y },
    slope_pct_per_bar: Number(slopePctBar.toFixed(4)),
    span_bars: span,
    touches,
    lineToday: Number(lineToday.toFixed(4)),
    clearance_pct: Number(clearance_pct.toFixed(2)),
    bars_since_break,
    break_date: breakIdx != null ? (c[breakIdx]?.date ?? null) : null,
    decline_pct: Number(decline.toFixed(4)),
    vol_ratio: isNum(vol_ratio) ? Number(vol_ratio.toFixed(2)) : null,
    rsi: isNum(rsiNow) ? Number(rsiNow.toFixed(1)) : null,
    rsi_rising: isNum(rsiNow) && isNum(rsi3) ? rsiNow > rsi3 : null,
    confirms,
    sub: {
      lineQ: Number(lineQ.toFixed(1)),
      fresh: Number(fresh.toFixed(1)),
      vol: Number(vol.toFixed(1)),
      momo: Number(momo.toFixed(1)),
      ctx: Number(ctx15.toFixed(1)),
    },
  };
}

// ===========================================================================
// detectSpring — failed breakdown / reclaim (flag, not a standalone leg)
// ===========================================================================
export function detectSpring(candles, opts = {}) {
  try {
    if (!Array.isArray(candles) || candles.length < 120) return null;
    const c = candles.slice(-N);
    const last = c.length - 1;
    const px = numOr(c[last].close);
    const atr = atrSeries(c);
    const atrNow = atr[last];
    if (!isNum(atrNow) || !isNum(px) || px <= 0) return null;

    const lows = pivotLows(c, K_PIVOT);
    // support = most-touched low cluster (within 0.75*ATR), >=3 hits; else recent shelf
    let support = null;
    if (lows.length >= 3) {
      let bestCount = 0, bestLevel = null;
      for (const a of lows) {
        let cnt = 0, sum = 0;
        for (const b of lows) if (Math.abs(b.y - a.y) <= 0.75 * atrNow) { cnt++; sum += b.y; }
        if (cnt > bestCount) { bestCount = cnt; bestLevel = sum / cnt; }
      }
      if (bestCount >= 3) support = bestLevel;
    }
    if (support == null) {
      // recent swing-low shelf: min low over the ~30 bars before the last 3
      let mn = Infinity;
      for (let i = Math.max(0, last - 33); i <= last - 3; i++) { const lo = numOr(c[i].low); if (isNum(lo)) mn = Math.min(mn, lo); }
      if (mn !== Infinity) support = mn;
    }
    if (support == null) return null;

    const buf = Math.max(0.3 * atrNow, 0.004 * px);
    let springIdx = null;
    for (let i = last; i >= Math.max(0, last - 2); i--) {
      const lo = numOr(c[i].low), cl = numOr(c[i].close);
      if (isNum(lo) && isNum(cl) && lo < support - buf && cl > support) { springIdx = i; break; }
    }
    if (springIdx == null) return null;

    // confirm: volume >=1.2x trailing-20 ending springIdx-1, RSI turning up off oversold
    let vol_ratio = null;
    {
      const endIdx = springIdx - 1;
      if (endIdx >= 20) {
        let s = 0, n2 = 0;
        for (let i = endIdx - 19; i <= endIdx; i++) { const v = numOr(c[i].volume); if (isNum(v)) { s += v; n2++; } }
        const avg = n2 ? s / n2 : null;
        const vNow = numOr(c[springIdx].volume);
        if (isNum(avg) && avg > 0 && isNum(vNow)) vol_ratio = vNow / avg;
      }
    }
    const rsiNow = numOr(c[last].rsi);
    const rsiPre = numOr(c[springIdx - 2]?.rsi);
    const rsiTurn = isNum(rsiNow) && isNum(rsiPre) && rsiNow > rsiPre && rsiPre < 40;
    const volOK = isNum(vol_ratio) && vol_ratio >= 1.2;
    if (!volOK && !rsiTurn) return null; // need at least one confirm

    const bars_since = last - springIdx;
    const freshTable = [20, 14, 8, 4];
    const base = freshTable[Math.min(bars_since, 3)];
    const volScore = isNum(vol_ratio) ? Math.min(Math.max(vol_ratio - 1, 0) / 0.7, 1) * 20 : 0;
    const dtbScore = clamp(Math.round(base + volScore + (rsiTurn ? 15 : 0)), 0, 100);

    return {
      ticker: opts.ticker || null,
      signal_type: 'failed_breakdown_spring',
      spring: true,
      support: Number(support.toFixed(2)),
      spring_date: c[springIdx]?.date ?? null,
      bars_since,
      vol_ratio: isNum(vol_ratio) ? Number(vol_ratio.toFixed(2)) : null,
      rsi: isNum(rsiNow) ? Number(rsiNow.toFixed(1)) : null,
      dtbScore,
    };
  } catch { return null; }
}
