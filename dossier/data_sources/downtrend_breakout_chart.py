"""Render a downtrend-breakout chart with the fitted falling line drawn.

Michael vetoes by eye, so the resistance line MUST be visible: 190d candles +
EMA20/50 + volume + RSI + the red descending trendline (clipped to start at the
OLDER anchor — no misleading left extrapolation) + anchor markers + a break
marker. Reuses the detector's own line-fit so the drawn line is exactly what
fired. Never raises (returns None on any failure).
"""
from __future__ import annotations

from typing import Any

try:
    import numpy as np
    import pandas as pd
    import mplfinance as mpf
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - degrade if deps missing
    np = None  # type: ignore[assignment]

try:
    from . import downtrend_breakout as d
except Exception:  # pragma: no cover - allow running as a loose script
    import downtrend_breakout as d  # type: ignore


def render(sym: str, asof: str | None = None, out: str | None = None) -> str | None:
    if np is None:
        return None
    try:
        hist = d._fetch(sym, asof=asof)
        if hist is None:
            return None
        res = d.scan_downtrend_break(sym, asof=asof, hist=hist)
        sub = hist.tail(d.LINE_WINDOW_BARS).reset_index(drop=True)
        n = len(sub)

        highs = sub["high"].astype(float).reset_index(drop=True)
        closes = sub["close"].astype(float).reset_index(drop=True)
        # Recover the line geometry even when rejected, so negatives are eyeball-able.
        geom = d.fit_descending_line(sub)
        if geom is None:
            f = d._forming_candidate(sub, highs, closes)
            geom = f[1] if f else None

        df = sub.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                                "close": "Close", "volume": "Volume"})
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        delta = df["Close"].diff()
        up = delta.clip(lower=0).ewm(alpha=1 / 14, min_periods=14).mean()
        dn = (-delta.clip(upper=0)).ewm(alpha=1 / 14, min_periods=14).mean()
        df["RSI"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))

        addplots = [
            mpf.make_addplot(df["EMA20"], color="#1f77b4", width=1.0),
            mpf.make_addplot(df["EMA50"], color="#ff7f0e", width=1.0),
            mpf.make_addplot(df["RSI"], panel=2, color="purple", width=1.0, ylabel="RSI"),
        ]

        alines = None
        vlines_dates: list = []
        title_extra = ""
        if geom is not None:
            oi, ni = geom["older_idx"], geom["newer_idx"]
            op, npr = geom["older_price"], geom["newer_price"]
            slope = geom["slope"]
            # CLIP the line to [older_anchor, last_bar] — do NOT extrapolate left
            # of the older anchor (that left-side line is never used by any gate and
            # is geometrically meaningless on the negatives).
            x0, x1 = oi, n - 1
            y0 = op + slope * (x0 - oi)
            y1 = op + slope * (x1 - oi)
            d0, d1 = df.index[x0], df.index[x1]
            alines = dict(alines=[[(d0, y0), (d1, y1)]], colors=["red"],
                          linewidths=[1.8], linestyle="--")
            anchor_y = np.full(n, np.nan)
            anchor_y[oi] = op; anchor_y[ni] = npr
            addplots.append(mpf.make_addplot(anchor_y, type="scatter", markersize=140,
                                             marker="o", color="red", panel=0))
            title_extra = (f"  line {df.index[oi].date()} ${op:.2f} -> "
                           f"{df.index[ni].date()} ${npr:.2f}  slope {geom['slope_pct_per_bar']:.2f}%/bar")
            bk = geom.get("break_idx")
            if bk is not None:
                vlines_dates.append(df.index[bk])

        pat = res["pattern"] if res else "REJECTED"
        title = f"{sym}  [{pat}]" + (f"  asof {asof}" if asof else "") + title_extra

        vlines = (dict(vlines=vlines_dates, colors=["green"], linewidths=[1.2], alpha=0.6)
                  if vlines_dates else None)
        kwargs: dict[str, Any] = dict(type="candle", style="yahoo", addplot=addplots,
                                      volume=True, volume_panel=1, panel_ratios=(6, 2, 2),
                                      figscale=1.6, figratio=(16, 10), title=title,
                                      returnfig=True)
        if alines:
            kwargs["alines"] = alines
        if vlines:
            kwargs["vlines"] = vlines
        fig, _ = mpf.plot(df, **kwargs)
        out = out or f"/tmp/chart_{sym}{'_' + asof if asof else ''}.png"
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        return out
    except Exception:
        return None


if __name__ == "__main__":
    print(render("NKE"))
    print(render("NKE", asof="2026-05-20"))
