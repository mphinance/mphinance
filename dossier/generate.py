#!/usr/bin/env python3
"""
Ghost Alpha Dossier — Daily Report Generator

Main orchestrator that runs the full pipeline using mphinance's existing
scanning strategies. Outputs HTML reports to docs/reports/ for GitHub Pages.

Pipeline stages:
  1. Market Pulse (SPY, QQQ, BTC, ETH, Gold, Treasuries)
  2. Run mphinance Strategies (Momentum, Squeeze, EMA Cross, Gamma)
  3. Fetch institutional data (TickerTrace API)
  4. Detect market regime (VIX + sector rotation)
  5. Track signal persistence (21-day rolling)
  6. Enrich top tickers (fundamentals, technicals, valuation)
  7. Generate AI narrative (Gemini)
  8. Render HTML report
  9. Update docs/index.html archive
 10. Git commit & push (optional)

Usage:
    python -m dossier.generate                     # Full pipeline
    python -m dossier.generate --dry-run           # No git push
    python -m dossier.generate --date 2026-03-03   # Specific date
    python -m dossier.generate --no-pdf            # Skip PDF
"""

import sys
import os
import argparse
import subprocess
import time
import random
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root (mphinance/) is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.utils.retry import retry  # noqa: E402


@retry(max_retries=2, initial_delay=2.0, exceptions=(Exception,))
def _safe_enrich_ticker(ticker: str):
    """Parallel-safe enrichment with jitter."""
    from dossier.data_sources.ticker_enrichment import enrich_ticker
    # Random jitter to desynchronize threads
    time.sleep(random.uniform(0.1, 0.8))
    return enrich_ticker(ticker)


# ── Pipeline Instrumentation ──
class PipelineTimer:
    """Track per-stage timing and errors for status dashboard."""

    def __init__(self):
        self.stages: dict[str, dict] = {}
        self.errors: list[dict] = []
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._start_time = time.time()

    @contextmanager
    def stage(self, name: str):
        """Context manager for timing a pipeline stage."""
        t0 = time.time()
        try:
            yield
            self.stages[name] = {
                "duration": round(time.time() - t0, 2),
                "status": "ok",
            }
        except Exception as e:
            self.stages[name] = {
                "duration": round(time.time() - t0, 2),
                "status": "error",
                "error": str(e)[:200],
            }
            self.errors.append({"stage": name, "message": str(e)[:200]})
            print(f"  [ERROR] {name}: {e}")

    def skip(self, name: str):
        """Mark a stage as skipped."""
        self.stages[name] = {"duration": 0, "status": "skipped"}

    def to_dict(self, date: str, dry_run: bool, summary: dict) -> dict:
        """Build the full stats dict for the status page."""
        return {
            "date": date,
            "started_at": self.started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "total_duration": round(time.time() - self._start_time, 1),
            "dry_run": dry_run,
            "stages": self.stages,
            "errors": self.errors,
            "summary": summary,
        }

from dossier.config import CORE_WATCHLIST, MAX_DOSSIER_TICKERS, OUTPUT_DIR, SCANNER_STRATEGIES
from dossier.data_sources.tickertrace import _is_junk


def _run_mphinance_strategies() -> list[dict]:
    """
    Run mphinance's Ghost Alpha V2 scanner and normalise results
    into a list of scanner signal dicts for the dossier.
    """
    print("  Running Ghost Alpha whole-market scanner...")

    try:
        from dossier.ghost_alpha_screener import _tv_fetch_all_stocks, funnel_filter, deep_scan_ticker
    except Exception as e:
        print(f"  [ERR] Could not load ghost alpha screener: {e}")
        return []

    all_signals = []
    try:
        print("    ⚡ Stage 1: TradingView bulk API...")
        raw_stocks = _tv_fetch_all_stocks()
        
        print("    🔍 Stage 2: Progressive elimination funnel...")
        survivors = funnel_filter(raw_stocks, verbose=False)
        
        # Sort survivors by market cap to prioritize deep scanning bigger/more liquid names if we cap
        survivors.sort(key=lambda s: s.get("market_cap") or 0, reverse=True)
        # Cap to 200 to prevent excessive YF api calls in cron
        survivors = survivors[:200]
        
        print(f"    🧪 Stage 3: Deep scanning {len(survivors)} survivors...")
        for i, s in enumerate(survivors):
            ticker = s["ticker"]
            res = deep_scan_ticker(ticker, s)
            if not res: continue
            
            d = res.get("daily", {})
            w = res.get("weekly", {})
            d_score = d.get("score", 0) / 5.0
            
            # Require at least B grade (3.0/5.0) on daily to consider it a signal
            if d.get("score", 0) < 3.0: 
                continue
                
            direction = "BULLISH" if d.get("hull_bull") else "BEARISH"
            rationale = []
            if d.get("sqz_fire"): rationale.append("SQZ FIRE")
            elif d.get("sqz_coiled"): rationale.append("SQZ COIL")
            rationale.append(f"Regime {d.get('regime', '?')}")
            
            all_signals.append({
                "symbol": ticker,
                "direction": direction,
                "score": min(1.0, d_score),
                "rationale": rationale,
                "strategy": "Ghost Alpha V2",
                "price": round(float(d.get("price", 0)), 2) if d.get("price") else 0,
            })
            
    except Exception as e:
        print(f"  [ERR] Scanner failed: {e}")

    # Sort by score descending
    all_signals.sort(key=lambda x: x["score"], reverse=True)
    return all_signals


def _update_index_page():
    """Scan docs/reports/ and docs/ticker/ and regenerate the docs/index.html archive page.
    Also copies the latest report to docs/reports/latest.html for a stable permalink."""
    import shutil
    import json as _json
    from datetime import datetime as _dt
    from collections import defaultdict

    docs_dir = OUTPUT_DIR.parent  # docs/
    reports_dir = OUTPUT_DIR       # docs/reports/
    watchlist_dir = docs_dir / "ticker"

    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.iterdir(), reverse=True):
            if f.suffix == ".html" and f.stem != "latest" and ".sync-conflict" not in f.name:
                reports.append({
                    "filename": f.name,
                    "date": f.stem.replace("_alpha_dossier", ""),
                    "path": f"reports/{f.name}",
                })

    # ── Copy latest report to docs/reports/latest.html ──
    if reports:
        latest_src = reports_dir / reports[0]["filename"]
        latest_dst = reports_dir / "latest.html"
        shutil.copy2(latest_src, latest_dst)
        print(f"  ✓ Latest report copied → {latest_dst}")

    # ── Gather watchlist with sector data from JSON ──
    watchlist = []
    if watchlist_dir.exists():
        for ticker_folder in sorted(watchlist_dir.iterdir()):
            if ticker_folder.is_dir():
                dd_json = ticker_folder / "deep_dive.json"
                dd_md = ticker_folder / "deep_dive.md"
                if dd_md.exists():
                    ticker = ticker_folder.name
                    mtime = _dt.fromtimestamp(dd_md.stat().st_mtime).strftime("%Y-%m-%d")

                    # Read sector from JSON if available
                    sector = "Other"
                    industry = ""
                    price = ""
                    if dd_json.exists():
                        try:
                            with open(dd_json, "r") as jf:
                                jdata = _json.load(jf)
                                sector = jdata.get("sector", "Other") or "Other"
                                industry = jdata.get("industry", "")
                                p = jdata.get("price", "")
                                price = f"${p:.2f}" if isinstance(p, (int, float)) else ""
                        except Exception:
                            pass

                    watchlist.append({
                        "ticker": ticker,
                        "html_path": f"ticker/{ticker}/deep_dive.html",
                        "md_path": f"ticker/{ticker}/deep_dive.md",
                        "json_path": f"ticker/{ticker}/deep_dive.json",
                        "date": mtime,
                        "sector": sector,
                        "industry": industry,
                        "price": price,
                    })

    # ── Group by sector ──
    sectors = defaultdict(list)
    for w in watchlist:
        sectors[w["sector"]].append(w)

    # Sort sectors by count descending, "Other" at the end
    sorted_sectors = sorted(
        sectors.items(),
        key=lambda x: (x[0] == "Other", -len(x[1]), x[0])
    )

    # Sector emoji/color mapping
    sector_styles = {
        "Technology": ("#00f3ff", "💻"),
        "Healthcare": ("#00ff88", "🏥"),
        "Financial Services": ("#ffb000", "🏦"),
        "Consumer Cyclical": ("#ff6b6b", "🛍️"),
        "Consumer Defensive": ("#a855f7", "🛒"),
        "Energy": ("#ff8c00", "⚡"),
        "Industrials": ("#888", "🏭"),
        "Basic Materials": ("#cd7f32", "⛏️"),
        "Communication Services": ("#00d4ff", "📡"),
        "Real Estate": ("#4caf50", "🏠"),
        "Utilities": ("#6b6bff", "💡"),
    }

    # ── Build latest report date for hero section ──
    latest_date = reports[0]["date"] if reports else "—"

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KTHVTFX699"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KTHVTFX699');</script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALPHA.DOSSIER // Archive</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        'mono': ['"JetBrains Mono"', 'monospace'],
                        'tech': ['"Share Tech Mono"', 'monospace'],
                    }},
                    colors: {{
                        'neon-green': '#00ff41',
                        'neon-red': '#ff3e3e',
                        'neon-blue': '#00f3ff',
                        'neon-amber': '#ffb000',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #050505;
            color: #e0e0e0;
            font-family: 'JetBrains Mono', monospace;
            background-image:
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 2px, 3px 100%;
        }}
        .hud-panel {{
            background: rgba(10, 10, 10, 0.8);
            border: 1px solid #333;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
        }}
        .report-link {{ transition: all 0.2s; }}
        .report-link:hover {{ transform: translateX(4px); border-color: #00f3ff; }}
        .archive-link {{ transition: all 0.15s; display: flex; padding: 6px 10px; border-radius: 3px; text-decoration: none; }}
        .archive-link:hover {{ background: rgba(0, 243, 255, 0.06); }}
        .latest-cta {{
            display: block;
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.08), rgba(0, 243, 255, 0.05));
            border: 1px solid #00ff41;
            border-radius: 4px;
            padding: 32px 28px;
            text-decoration: none;
            transition: all 0.3s;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}
        .latest-cta:hover {{
            border-color: #00f3ff;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.15), 0 0 60px rgba(0, 243, 255, 0.08);
            transform: translateY(-2px);
        }}
        .latest-cta::before {{
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.05), transparent);
            animation: shimmer 3s infinite;
        }}
        @keyframes shimmer {{ 100% {{ left: 100%; }} }}
        .pulse-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            background: #00ff41;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 4px #00ff41; }}
            50% {{ opacity: 0.4; box-shadow: 0 0 12px #00ff41; }}
        }}
        .sector-header {{
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
        }}
        .sector-header:hover {{
            border-color: #00f3ff !important;
        }}
        .sector-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .sector-content.open {{
            max-height: 2000px;
            transition: max-height 0.5s ease-in;
        }}
        .view-badge {{
            font-size: 8px;
            color: #555;
            background: rgba(255,255,255,0.03);
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #222;
        }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-5xl mx-auto space-y-5">
        <div style="background:linear-gradient(90deg,#1a1a2e,#16213e);border:1px solid #0f3460;padding:8px 16px;text-align:center;font-size:10px;font-family:'JetBrains Mono',monospace;border-radius:2px">
            <a href="https://www.traderdaddy.pro/register?ref=8DUEMWAJ" target="_blank" style="color:#00f3ff;letter-spacing:0.1em;text-transform:uppercase;text-decoration:none">🚀 Try TraderDaddy Pro — AI-Powered Trading Dashboard</a>
        </div>
        <div class="hud-panel p-6 rounded-sm border-l-4 border-neon-blue">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl md:text-3xl font-black font-tech tracking-widest text-white uppercase italic">
                        ALPHA.DOSSIER <span class="text-neon-blue">●</span> ARCHIVE
                    </h1>
                    <p class="text-[10px] text-gray-500 uppercase tracking-[0.3em] mt-1">
                        Daily Intelligence Reports // Ghost Alpha Pipeline
                    </p>
                </div>
                <div class="text-right">
                    <div class="text-[9px] text-gray-600 uppercase">Page Views</div>
                    <div class="text-sm text-neon-blue font-bold font-mono" id="index-views">—</div>
                </div>
            </div>
        </div>
"""

    # ── Two-column: Hero CTA (left) + Archive sidebar (right) ──
    if reports:
        index_html += f"""
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="md:col-span-2">
                <a href="reports/latest.html" class="latest-cta">
                    <div class="flex items-center gap-3 mb-3">
                        <span class="pulse-dot"></span>
                        <span class="text-[10px] text-neon-green uppercase tracking-[0.3em] font-bold">Latest Report</span>
                    </div>
                    <div class="text-2xl md:text-3xl font-bold text-white font-tech tracking-wider mb-2">
                        Alpha Dossier
                    </div>
                    <div class="text-lg text-neon-blue font-tech">{latest_date}</div>
                    <div class="text-[10px] text-gray-500 mt-4 uppercase tracking-widest">
                        Click to read the full intelligence report →
                    </div>
                    <div class="text-[9px] text-gray-700 mt-2">
                        Permalink: /reports/latest.html
                    </div>
                </a>
            </div>
            <div class="md:col-span-1">
                <div class="hud-panel p-4 rounded-sm h-full">
                    <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                        📁 Archive <span class="text-neon-blue">// {len(reports)}</span>
                    </div>
                    <div class="space-y-1 max-h-64 overflow-y-auto pr-1" style="scrollbar-width:thin;scrollbar-color:#333 transparent">
"""
        for i, r in enumerate(reports):
            dot_color = "text-neon-green" if i == 0 else "text-gray-700"
            index_html += f"""                        <a href="{r['path']}" class="archive-link flex items-center gap-2">
                            <span class="{dot_color} text-[6px]">●</span>
                            <span class="text-neon-blue text-xs">{r['date']}</span>
                        </a>
"""
        index_html += """                    </div>
                </div>
            </div>
        </div>
"""
    else:
        index_html += '        <div class="hud-panel p-6 rounded-sm text-gray-600 text-sm italic">No reports generated yet. Run the pipeline first.</div>\n'

    # ── Watchlist Deep Dives — Grouped by Sector ──
    if watchlist:
        index_html += f"""
        <div class="hud-panel p-4 rounded-sm border-l-4 border-neon-amber">
            <div class="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                <div class="text-[10px] text-gray-500 uppercase tracking-widest">
                    🔍 WATCHLIST.DEEP.DIVES <span class="text-neon-amber">// {len(watchlist)} TICKERS · {len(sorted_sectors)} SECTORS</span>
                </div>
                <button onclick="toggleAll()" class="text-[9px] text-gray-600 border border-gray-700 px-2 py-0.5 rounded hover:text-neon-blue hover:border-neon-blue/30 transition-colors" id="toggle-btn">
                    Expand All
                </button>
            </div>
"""
        for sector_name, tickers in sorted_sectors:
            color, emoji = sector_styles.get(sector_name, ("#888", "📦"))
            index_html += f"""
            <div class="mb-2">
                <div class="sector-header flex items-center justify-between bg-black/30 border border-gray-800 rounded px-4 py-2"
                     onclick="toggleSector(this)" style="border-left: 3px solid {color}">
                    <div class="flex items-center gap-2">
                        <span>{emoji}</span>
                        <span class="text-xs font-bold text-white">{sector_name}</span>
                        <span class="text-[9px] text-gray-600">{len(tickers)} ticker{"s" if len(tickers) != 1 else ""}</span>
                    </div>
                    <span class="text-[10px] text-gray-600 sector-arrow">▸</span>
                </div>
                <div class="sector-content">
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2 pt-2 pb-3">
"""
            for w in sorted(tickers, key=lambda x: x["ticker"]):
                index_html += f"""                        <div class="report-link bg-black/40 border border-gray-800 rounded px-4 py-3 flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <a href="{w['html_path']}" class="text-neon-amber font-bold text-sm hover:text-white transition-colors">{w['ticker']}</a>
                                <span class="text-[8px] text-gray-700">{w['price']}</span>
                                <span class="view-badge" data-ticker="{w['ticker']}">—</span>
                            </div>
                            <div class="flex gap-2">
                                <a href="https://www.tradingview.com/symbols/{w['ticker']}/chart/" target="_blank" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-neon-blue hover:border-neon-blue/30 transition-colors">TV</a>
                                <a href="{w['md_path']}" download class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">MD</a>
                                <a href="{w['json_path']}" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">JSON</a>
                            </div>
                        </div>
"""
            index_html += """                    </div>
                </div>
            </div>
"""
        index_html += """        </div>
"""

    # ── Page View Analytics Summary ──
    index_html += """
        <div class="hud-panel p-4 rounded-sm">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                📊 ANALYTICS.PULSE <span class="text-neon-blue">// LOCAL TRACKING</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Index Views</div>
                    <div class="text-lg font-bold text-neon-blue font-mono" id="stat-index">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Report Views</div>
                    <div class="text-lg font-bold text-neon-green font-mono" id="stat-reports">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Ticker Pages</div>
                    <div class="text-lg font-bold text-neon-amber font-mono" id="stat-tickers">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Top Ticker</div>
                    <div class="text-lg font-bold text-white font-mono" id="stat-top">—</div>
                </div>
            </div>
        </div>
"""

    index_html += """
        <div class="text-center py-4">
            <div class="text-[9px] text-gray-700 font-mono uppercase tracking-widest">
                Ghost Alpha Dossier Pipeline // mphinance
            </div>
        </div>
    </div>

    <script>
    // ── Page View Tracking (localStorage) ──
    (function() {
        const STORAGE_KEY = 'ghost_dossier_analytics';
        let analytics = {};
        try { analytics = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch(e) {}

        // Track this page
        const page = 'index';
        analytics[page] = (analytics[page] || 0) + 1;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(analytics));

        // Display index views
        const el = document.getElementById('index-views');
        if (el) el.textContent = analytics[page];
        const statEl = document.getElementById('stat-index');
        if (statEl) statEl.textContent = analytics[page];

        // Aggregate stats
        let reportViews = 0, tickerViews = 0, topTicker = '', topCount = 0;
        for (const [k, v] of Object.entries(analytics)) {
            if (k.startsWith('report:')) reportViews += v;
            if (k.startsWith('ticker:')) {
                tickerViews += v;
                if (v > topCount) { topCount = v; topTicker = k.replace('ticker:', ''); }
            }
        }
        const rEl = document.getElementById('stat-reports');
        if (rEl) rEl.textContent = reportViews || '—';
        const tEl = document.getElementById('stat-tickers');
        if (tEl) tEl.textContent = tickerViews || '—';
        const topEl = document.getElementById('stat-top');
        if (topEl) topEl.textContent = topTicker || '—';

        // Show per-ticker view counts
        document.querySelectorAll('.view-badge[data-ticker]').forEach(badge => {
            const t = badge.dataset.ticker;
            const views = analytics['ticker:' + t] || 0;
            badge.textContent = views ? views + '👁' : '';
        });
    })();

    // ── Sector Toggle ──
    function toggleSector(header) {
        const content = header.nextElementSibling;
        const arrow = header.querySelector('.sector-arrow');
        content.classList.toggle('open');
        arrow.textContent = content.classList.contains('open') ? '▾' : '▸';
    }

    function toggleAll() {
        const sections = document.querySelectorAll('.sector-content');
        const btn = document.getElementById('toggle-btn');
        const allOpen = Array.from(sections).every(s => s.classList.contains('open'));
        sections.forEach(s => {
            if (allOpen) s.classList.remove('open');
            else s.classList.add('open');
        });
        document.querySelectorAll('.sector-arrow').forEach(a => a.textContent = allOpen ? '▸' : '▾');
        btn.textContent = allOpen ? 'Expand All' : 'Collapse All';
    }

    // Auto-expand first sector
    const firstContent = document.querySelector('.sector-content');
    if (firstContent) {
        firstContent.classList.add('open');
        firstContent.previousElementSibling.querySelector('.sector-arrow').textContent = '▾';
    }
    </script>
</body>
</html>
"""

    index_path = docs_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)
    print(f"  ✓ Index updated: {index_path} ({len(reports)} reports, {len(watchlist)} watchlist, {len(sorted_sectors)} sectors)")


def run_pipeline(date: str, dry_run: bool = False, generate_pdf: bool = True):
    """Execute the full Alpha Dossier pipeline."""
    timer = PipelineTimer()

    print("=" * 72)
    print(f"  🔮 GHOST ALPHA DOSSIER — PIPELINE START")
    print(f"  Date: {date}")
    print(f"  Mode: {'DRY RUN' if dry_run else 'FULL'}")
    print("=" * 72)

    # ── Stage 1: Market Pulse ──
    print("\n[1/16] MARKET PULSE")
    with timer.stage("Market Pulse"):
        from dossier.data_sources.market_pulse import fetch_market_pulse
        market_pulse = fetch_market_pulse()
        print(f"  {len(market_pulse)} benchmarks fetched")

    # ── Stage 1b: Sector Relative Strength ──
    print("\n[1b/16] SECTOR RELATIVE STRENGTH")
    sector_rs: dict = {}
    with timer.stage("Sector RS"):
        try:
            from dossier.data_sources.sector_rs import fetch_sector_rs
            sector_rs = fetch_sector_rs()
            if sector_rs.get("ranked"):
                leaders = sector_rs.get("leaders", [])
                laggards = sector_rs.get("laggards", [])
                lead_str = ", ".join(
                    f"{r['name']} ({r['composite_rs']:+.1f})" for r in leaders[:2]
                )
                lag_str = ", ".join(
                    f"{r['name']} ({r['composite_rs']:+.1f})" for r in laggards[:2]
                )
                print(f"  Leaders: {lead_str}")
                print(f"  Laggards: {lag_str}")
        except Exception as e:
            print(f"  [WARN] Sector RS failed: {e}")

    # ── Stage 2: Strategy Scanner ──
    print("\n[2/16] STRATEGY SCANNER")
    try:
        scanner_signals = _run_mphinance_strategies()
    except Exception as e:
        print(f"  [WARN] Strategy scanner failed: {e}")
        scanner_signals = []

    # Also scan core watchlist with a simple technical check
    from dossier.data_sources.ticker_enrichment import _sma, _rsi, _ema
    import yfinance as yf

    for ticker in CORE_WATCHLIST:
        if ticker in [s["symbol"] for s in scanner_signals]:
            continue
        try:
            hist = yf.Ticker(ticker).history(period="3mo")
            if hist.empty:
                continue
            close = hist["Close"]
            sma50 = _sma(close, 50).iloc[-1]
            sma200 = _sma(close, 200).iloc[-1] if len(close) >= 200 else sma50
            rsi_val = _rsi(close).iloc[-1]
            price = float(close.iloc[-1])

            rationale = []
            score = 0.4
            direction = "NEUTRAL"

            if price > sma200:
                rationale.append("Above SMA200")
                score += 0.1
            if rsi_val and 30 < rsi_val < 50:
                rationale.append(f"RSI {int(rsi_val)}")
                score += 0.1
                direction = "BULLISH"
            elif rsi_val:
                rationale.append(f"RSI {int(rsi_val)}")

            ema21 = _ema(close, 21).iloc[-1]
            if abs(price - ema21) / price < 0.02:
                rationale.append("Near EMA21 support")
                score += 0.05

            scanner_signals.append({
                "symbol": ticker,
                "direction": direction,
                "score": min(1.0, round(score, 2)),
                "rationale": rationale,
                "strategy": "Core Watchlist",
                "price": round(price, 2),
            })
        except Exception:
            continue

    scanner_signals.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Total signals: {len(scanner_signals)}")

    scanned_tickers = [s["symbol"] for s in scanner_signals]

    # ── Stage 2b: Broad Universe Scan (scanline union) ──
    # Size-agnostic candidate pool (momentum ∪ unusual-volume ∪ oversold-bounce)
    # so the new deep-screener legs (triangle, flow) see small/mid-cap movers the
    # native top-200-by-mcap funnel misses. Never raises → [] on failure.
    print("\n[2b/16] BROAD UNIVERSE SCAN (scanline)")
    universe_rows: list[dict] = []
    universe_mcap: dict[str, float] = {}
    with timer.stage("Universe Scan"):
        try:
            from dossier.data_sources.universe_scan import scan_universe_union
            universe_rows = scan_universe_union(limit_per=120)
            universe_mcap = {
                r["ticker"]: r["market_cap"]
                for r in universe_rows
                if r.get("ticker") and r.get("market_cap") is not None
            }
            multi = [r for r in universe_rows if len(r.get("sources", [])) >= 2]
            print(f"  {len(universe_rows)} candidates ({len(multi)} multi-source)")
        except Exception as e:
            print(f"  [WARN] Universe scan failed: {e}")
    # Candidate pool for the new legs: union tickers first (broad), then the
    # existing strategy survivors. De-duped, junk-filtered, order-preserving.
    universe_syms = [r["ticker"] for r in universe_rows if r.get("ticker")]
    candidate_pool = [
        t for t in dict.fromkeys(universe_syms + scanned_tickers) if not _is_junk(t)
    ]

    # ── Stage 3: Institutional Data ──
    print("\n[3/16] TICKERTRACE INSTITUTIONAL DATA")
    from dossier.data_sources.tickertrace import fetch_institutional_data
    institutional = fetch_institutional_data()

    # ── Stage 4: Market Regime ──
    print("\n[4/16] MARKET REGIME DETECTION")
    market = {}
    market_regime = {}
    with timer.stage("Market Regime"):
        from dossier.market_regime import detect_regime
        market_regime = detect_regime()
        market = market_regime # Compatibility
        regime = market_regime.get("regime", "UNKNOWN")
        vix_data = market_regime.get("vix", {})
        vix_level = vix_data.get("vix_level", 0)
        print(f"  Regime: {regime} (VIX {vix_level:.1f})")
        print(f"  {market_regime.get('market_context', '')}")

    # ── Stage 4c: Market Weather (StrikeForge VIX term-structure) ──
    # Upgrades the level-only regime read with VIX/VIX3M term structure
    # (contango/backwardation) + a "should I trade today" verdict. Fail-open.
    print("\n[4c/16] MARKET WEATHER (VIX term structure)")
    market_weather_data: dict = {}
    with timer.stage("Market Weather"):
        try:
            from dossier.data_sources.sf_market_weather import market_weather
            market_weather_data = market_weather()
            if market_weather_data.get("available"):
                print(f"  {market_weather_data.get('headline', '')}")
            else:
                print("  ⏭️ Market weather unavailable (VIX fetch failed)")
        except Exception as e:
            print(f"  [WARN] Market weather failed: {e}")

    # ── Stage 4a: Mood Ring history (persist today's regime; never fails pipeline) ──
    # Pure surfacing on top of detect_regime() — append a deduped, date-keyed entry
    # so the dossier header can render the mood-ring strip of the last ~10 days.
    try:
        from dossier.mood_ring import record_regime
        regime_entry = {
            "date": date,
            "regime": market_regime.get("regime", "UNKNOWN"),
            "regime_name": market_regime.get("vix", {}).get("regime_name", "UNKNOWN"),
            "vix_level": market_regime.get("vix", {}).get("vix_level", 0),
            "spy_change": market_pulse[0].get("change_pct", 0) if market_pulse else 0,
        }
        rh_path = PROJECT_ROOT / "landing" / "data" / "regime_history.json"
        record_regime(rh_path, regime_entry)
        print(f"  ✓ Mood ring history updated → {rh_path}")
    except Exception as e:
        print(f"  [WARN] Mood ring history failed: {e}")

    # ── Stage 4a2: Volatility Risk Premium (VIX vs. realized SPY vol) ──
    # market_regime.py and sf_market_weather.py both classify off VIX's
    # absolute level/term structure; this asks a different question — is
    # implied vol actually pricing MORE movement than SPY has realized
    # lately, or less. Feeds options-selling (CSP/covered-call) conviction
    # directly. Reuses today's VIX read to avoid a duplicate fetch.
    try:
        from dossier.vol_risk_premium import fetch_and_compute_vrp, format_vrp_text, record_vrp
        vrp_data = fetch_and_compute_vrp(vix_level=market_regime.get("vix", {}).get("vix_level"))
        vrp_data["date"] = date
        vrp_path = PROJECT_ROOT / "landing" / "data" / "vrp_history.json"
        if vrp_data.get("available"):
            record_vrp(vrp_path, vrp_data)
        print(f"  {format_vrp_text(vrp_data)}")
    except Exception as e:
        print(f"  [WARN] Volatility risk premium failed: {e}")

    # ── Stage 4b: ROIC Fortress Filter ──
    print("\n[4b/16] ROIC FORTRESS QUALITY FILTER")
    fortress_results = {}
    with timer.stage("Fortress Filter"):
        from dossier.roic_fortress_screener import deep_scan_fundamentals
        # Scan top 40 strategy survivors for quality
        fortress_candidates = scanned_tickers[:40]
        print(f"  Deep scanning {len(fortress_candidates)} candidates for quality...")
        for ticker in fortress_candidates:
            res = deep_scan_fundamentals(ticker)
            if res:
                fortress_results[ticker] = res
        print(f"  ✓ {len([t for t, r in fortress_results.items() if r['fortress_score'] >= 65])} Castles/Fortresses found")

    # ── Stage 5: Persistence ──
    print("\n[5/16] SIGNAL PERSISTENCE")
    from dossier.persistence.tracker import update_persistence
    persistence = update_persistence(scanned_tickers, date)
    print(f"  Lifers: {persistence['summary']['lifers']}")
    print(f"  High Conviction: {persistence['summary']['high_conviction']}")
    print(f"  New Signals: {persistence['summary']['new_signals']}")

    # ── Stage 6: Technical Setups ──
    print("\n[6/16] TECHNICAL SETUPS (Tao of Trading)")
    from dossier.data_sources.technical_setups import generate_setups
    # Analyze top strategy picks for setup quality
    setup_tickers = [s["symbol"] for s in scanner_signals if s["strategy"] != "Core Watchlist"][:8]
    # Fill with institutional buying tickers
    inst_buy_tickers = [s["ticker"] for s in institutional.get("top_buying", [])[:4]]
    setup_tickers = [t for t in dict.fromkeys(setup_tickers + inst_buy_tickers) if not _is_junk(t)][:10]
    # Fallback to core watchlist if no strategy/institutional tickers
    if not setup_tickers:
        setup_tickers = CORE_WATCHLIST[:6]
        print("  (falling back to Core Watchlist for setups)")
    technical_setups = generate_setups(setup_tickers, max_setups=6)
    print(f"  {len(technical_setups)} setups analyzed")

    # ── Stage 6b: Triangle Breakout (TD Pro engine, OHLCV-only) ──
    # Scans the broad candidate pool's top names for confirmed/forming triangles.
    # Each scan fetches 2y daily bars (yfinance), so cap the universe to keep the
    # static-IP yfinance load bounded. Never raises → [].
    print("\n[6b/16] TRIANGLE BREAKOUT")
    triangle_signals: list[dict] = []
    with timer.stage("Triangle Breakout"):
        try:
            from dossier.data_sources.triangle_screener import generate_triangles
            # Blend liquid strategy survivors / core (which pass the engine's
            # liquidity + 300-bar gates and actually form clean triangles) with
            # the broad universe movers. Survivors first so the liquid names are
            # guaranteed in-scope; universe adds small/mid-cap breakout candidates
            # (illiquid ones simply fail the gate — no harm). De-duped, junk-filtered.
            triangle_universe = [
                t for t in dict.fromkeys(scanned_tickers[:30] + candidate_pool[:30])
                if not _is_junk(t)
            ][:50] or scanned_tickers[:40]
            triangle_signals = generate_triangles(triangle_universe, max_results=10)
            confirmed = [t for t in triangle_signals if t.get("pattern") == "confirmed"]
            print(f"  {len(triangle_signals)} triangles ({len(confirmed)} confirmed) "
                  f"from {len(triangle_universe)} scanned")
        except Exception as e:
            print(f"  [WARN] Triangle breakout failed: {e}")

    # ── Stage 6c: Downtrend Breakout (falling-trendline reversal — Michael's edge) ──
    # His #1 setup: a break of a MULTI-MONTH falling resistance line (lower highs
    # from a major peak), out of a real downtrend — not a triangle, not an uptrend
    # pullback, not a falling knife. Reuses the triangle engine's pivot/liquidity
    # machinery but fits its own long (~9mo) line. Each scan is a 2y yfinance fetch,
    # so cap the universe. Never raises → [].
    print("\n[6c/16] DOWNTREND BREAKOUT")
    downtrend_break_signals: list[dict] = []
    with timer.stage("Downtrend Breakout"):
        try:
            from dossier.data_sources.downtrend_breakout import generate_downtrend_breaks
            # Same liquid-blended pool as triangle: survivors first (they pass the
            # liquidity gate), then broad-universe movers (illiquid ones fail the
            # gate harmlessly). De-duped, junk-filtered, capped for yfinance load.
            dtb_universe = [
                t for t in dict.fromkeys(scanned_tickers[:30] + candidate_pool[:30])
                if not _is_junk(t)
            ][:40] or scanned_tickers[:30]
            downtrend_break_signals = generate_downtrend_breaks(dtb_universe, max_results=10)
            actionable = [s for s in downtrend_break_signals
                          if s.get("pattern") in ("confirmed", "forming")]
            print(f"  {len(downtrend_break_signals)} downtrend breaks "
                  f"({len(actionable)} actionable confirmed/forming) from {len(dtb_universe)} scanned")
        except Exception as e:
            print(f"  [WARN] Downtrend breakout failed: {e}")

    # ── Stage 7: CSP Setups ──
    print("\n[7/16] CSP SETUPS")
    from dossier.data_sources.csp_setups import fetch_csp_setups
    csp_setups = fetch_csp_setups(max_results=8)
    print(f"  {len(csp_setups)} CSP candidates")

    # ── Stage 7b: Options Flow (daily Tradier snapshot) ──
    # Once-daily Vol/OI + premium-skew snapshot, static scoring. Tradier-backed
    # (no yfinance), market-cap-aware tier floors via the universe scan. Never raises.
    print("\n[7b/16] OPTIONS FLOW (Tradier daily)")
    options_flow_signals: list[dict] = []
    with timer.stage("Options Flow"):
        try:
            from dossier.data_sources.options_flow import fetch_options_flow
            flow_universe = candidate_pool[:15] or scanned_tickers[:15]
            options_flow_signals = fetch_options_flow(
                flow_universe, max_results=10, market_caps=universe_mcap
            )
            bull = [f for f in options_flow_signals if f.get("skew") == "bullish"]
            print(f"  {len(options_flow_signals)} tickers with flow ({len(bull)} bullish skew)")
        except Exception as e:
            print(f"  [WARN] Options flow failed: {e}")

    # Build a per-ticker signal-source map from the new directional legs — feeds
    # both the IBKR book overlay and the analyst-watchlist cross-reference.
    signals_by_ticker: dict[str, list[str]] = {}
    for t in triangle_signals:
        sym = (t.get("ticker") or "").upper()
        if sym:
            signals_by_ticker.setdefault(sym, []).append(f"triangle_{t.get('pattern', '')}")
    for f in options_flow_signals:
        sym = (f.get("ticker") or "").upper()
        if sym:
            skew = f.get("skew", "balanced")
            signals_by_ticker.setdefault(sym, []).append(f"flow_{skew}")

    # ── Stage 7c: IBKR Book ("Your Book") ──
    # Live holdings from the local bridge (degrades to empty if the gateway is
    # asleep), each tagged HOLD/ADD/TRIM/WATCH against today's signal overlaps.
    print("\n[7c/16] IBKR BOOK (Your Book)")
    book_data: dict = {"positions": [], "account": {}, "ok": False}
    book_overlay: list[dict] = []
    with timer.stage("IBKR Book"):
        try:
            from dossier.data_sources.ibkr_book import get_book, overlay_book, enrich_with_quotes
            book_data = get_book()
            if book_data.get("ok"):
                positions = enrich_with_quotes(book_data.get("positions", []))
                book_data["positions"] = positions
                book_overlay = overlay_book(positions, signals_by_ticker)
                actions = [p.get("action") for p in book_overlay]
                print(f"  {len(book_overlay)} positions "
                      f"(ADD {actions.count('ADD')}, TRIM {actions.count('TRIM')}, "
                      f"WATCH {actions.count('WATCH')})")
            else:
                print(f"  ⏭️ IBKR bridge unavailable ({book_data.get('error', 'no data')})")
        except Exception as e:
            print(f"  [WARN] IBKR book failed: {e}")

    # Assemble the private "Your Book" payload for the push (never published).
    _acct = book_data.get("account", {}) if isinstance(book_data, dict) else {}
    your_book = {
        "ok": bool(book_data.get("ok")),
        "positions": book_overlay,
        "net_liq": _acct.get("NetLiquidation_num") or _acct.get("NetLiquidation"),
        "daily_pnl": _acct.get("dailyPnL"),
    }

    # ── Stage 8: Ticker Enrichment ──
    print(f"\n[8/16] TICKER ENRICHMENT (top {MAX_DOSSIER_TICKERS})")
    
    # Prioritize: Fortress-grade survivors > Strategy survivors > Institutional buying
    fortress_picks = [t for t, r in fortress_results.items() if r["fortress_score"] >= 60]
    strategy_tickers = [s["symbol"] for s in scanner_signals if s["strategy"] != "Core Watchlist"][:5]
    inst_tickers = [s["ticker"] for s in institutional.get("top_buying", [])[:3]]
    
    enrichment_order = [t for t in dict.fromkeys(
        fortress_picks + strategy_tickers + inst_tickers + scanned_tickers[:MAX_DOSSIER_TICKERS]
    ) if not _is_junk(t)][:MAX_DOSSIER_TICKERS]

    dossiers = []
    with timer.stage("Ticker Enrichment"):
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_ticker = {executor.submit(_safe_enrich_ticker, t): t for t in enrichment_order}
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result()
                    if data:
                        # Inject fortress data if we have it
                        if ticker in fortress_results:
                            f = fortress_results[ticker]
                            data["fortress_score"] = f["fortress_score"]
                            data["fortress_tier"] = f["tier"]
                            data["fortress_emoji"] = f["tier_emoji"]
                        dossiers.append(data)
                except Exception as e:
                    print(f"    [ERR] {ticker} enrichment failed: {e}")
    
    # Sort dossiers back into enrichment_order
    dossiers.sort(key=lambda x: enrichment_order.index(x["ticker"]) if x["ticker"] in enrichment_order else 999)
    print(f"  {len(dossiers)} dossiers enriched")

    # ── Stage 8b: Momentum Picks ──
    print("\n[10/16] DAILY MOMENTUM PICKS")
    momentum_picks = {}
    try:
        from dossier.momentum_picks import pick_daily_momentum, format_picks_text
        # Build payloads from dossier data for scoring
        # We need ticker pages' JSON format — use what we have
        from dossier.pages.ticker_page import TICKER_OUTPUT_DIR
        import json as _picks_json
        
        payloads_for_scoring = []
        for d in dossiers:
            ticker = d.get("ticker", "")
            latest_json = TICKER_OUTPUT_DIR / ticker / "latest.json"
            if latest_json.exists():
                try:
                    with open(latest_json) as pf:
                        payloads_for_scoring.append(_picks_json.load(pf))
                except Exception:
                    pass
        
        # If no existing JSONs (first run), score from enriched data directly
        if not payloads_for_scoring:
            for d in dossiers:
                tech = d.get("technicals", {})
                scores = d.get("scores", {})
                payloads_for_scoring.append({
                    "ticker": d.get("ticker", ""),
                    "currentPrice": d.get("price", 0),
                    "priceChangePct": d.get("change_pct", 0),
                    "trendOverall": "Bullish" if tech.get("ema_stack", "").startswith("FULL BULL") else "Bearish",
                    "technical_analysis": {
                        "ema_stack": tech.get("ema_stack", "UNKNOWN"),
                        "ema": {"21": tech.get("ema_21")},
                        "oscillators": {"rsi_14": tech.get("rsi_14"), "adx_14": tech.get("adx")},
                        "volume": {"rel_vol": tech.get("rel_vol", 1.0)},
                    },
                    "scores": scores,
                    "tickertrace": d.get("tickertrace", {}),
                })
        
        momentum_picks = pick_daily_momentum(payloads_for_scoring, date)
        picks_text = format_picks_text(momentum_picks)
        print(f"  {picks_text}")
    except Exception as e:
        print(f"  [WARN] Momentum picks failed: {e}")

    # ── Stage 10a: Momentum Breadth Index ──
    # Pure surfacing on top of momentum_picks' `all_ranked` scan universe —
    # checks whether the podium picks are backed by a broad move or a thin one.
    try:
        from dossier.breadth_index import compute_breadth, format_breadth_text, record_breadth
        breadth = compute_breadth(momentum_picks.get("all_ranked", []))
        breadth["date"] = date
        bh_path = PROJECT_ROOT / "landing" / "data" / "breadth_history.json"
        record_breadth(bh_path, breadth)
        print(f"  {format_breadth_text(breadth)}")
    except Exception as e:
        print(f"  [WARN] Breadth index failed: {e}")

    # ── Stage 10a2: Factor Leaderboard ──
    # Same `all_ranked` scan universe as breadth, but asks a different
    # question: not "how broad is the move" but "which of the 10 scoring
    # factors is actually driving today's picks."
    try:
        from dossier.factor_leaderboard import compute_leaderboard, format_leaderboard_text, record_leaderboard
        leaderboard = compute_leaderboard(momentum_picks.get("all_ranked", []))
        leaderboard["date"] = date
        fl_path = PROJECT_ROOT / "landing" / "data" / "factor_leaderboard_history.json"
        record_leaderboard(fl_path, leaderboard)
        print(f"  {format_leaderboard_text(leaderboard)}")
    except Exception as e:
        print(f"  [WARN] Factor leaderboard failed: {e}")

    # ── Stage 10a3: Score Dispersion Index ──
    # Same `all_ranked` scan universe again, but asks a third question: not
    # "how broad" or "which factor" but "is today's leadership a lone
    # standout pulling away from the pack, or a broad, evenly-strong tape."
    try:
        from dossier.score_dispersion import compute_dispersion, format_dispersion_text, record_dispersion
        dispersion = compute_dispersion(momentum_picks.get("all_ranked", []))
        dispersion["date"] = date
        sd_path = PROJECT_ROOT / "landing" / "data" / "score_dispersion_history.json"
        record_dispersion(sd_path, dispersion)
        print(f"  {format_dispersion_text(dispersion)}")
    except Exception as e:
        print(f"  [WARN] Score dispersion failed: {e}")

    # ── Stage 10a4: Sector Leadership Concentration ──
    # Same `all_ranked` scan universe again, but asks a fourth question: not
    # "how broad," "which factor," or "what shape," but "which sector is the
    # top-scored group actually made of" — one melt-up sector or a genuine
    # rotation across many.
    try:
        from dossier.sector_leadership import compute_sector_leadership, format_leadership_text, record_leadership
        leadership = compute_sector_leadership(momentum_picks.get("all_ranked", []))
        leadership["date"] = date
        sl_path = PROJECT_ROOT / "landing" / "data" / "sector_leadership_history.json"
        record_leadership(sl_path, leadership)
        print(f"  {format_leadership_text(leadership)}")
    except Exception as e:
        print(f"  [WARN] Sector leadership failed: {e}")

    # ── Stage 10a5: Junk Rally Index ──
    # Same `all_ranked` scan universe one more time, but asks a fifth
    # question: not breadth/factor/shape/sector, but "is the leadership
    # actually clean?" — aggregates quality_filter.py's per-ticker
    # SPAC/penny/junk-bio/shell/ADR/recent-IPO flags across today's top
    # scorers so a thin, junk-driven "rally" doesn't get mistaken for a
    # healthy one.
    try:
        from dossier.quality_breadth import compute_quality_index, format_quality_text, record_quality
        quality = compute_quality_index(momentum_picks.get("all_ranked", []))
        quality["date"] = date
        qb_path = PROJECT_ROOT / "landing" / "data" / "quality_breadth_history.json"
        record_quality(qb_path, quality)
        print(f"  {format_quality_text(quality)}")
    except Exception as e:
        print(f"  [WARN] Junk rally index failed: {e}")

    # ── Stage 10b: Confluence + Day-over-Day Migration (the synthesis) ──
    # Rank tickers by how many INDEPENDENT, directionally-agreeing legs fire
    # (trend ∪ triangle ∪ flow ∪ 13F), then detect what MATURED since yesterday.
    # Both pure + never-raise. Migration needs per-leg namespaced persistence, so
    # we record each new leg into its OWN namespace first (the default-namespace
    # scanner call already happened at Stage 5 — do NOT duplicate it).
    print("\n[10b/16] CONFLUENCE + MIGRATION")
    confluence = {"watchlist": [], "generated": 0}
    migration = {"migrations": [], "migration_of_the_day": None}
    with timer.stage("Confluence + Migration"):
        try:
            from dossier.confluence import compute_confluence, compute_migration
            from dossier.persistence.tracker import update_persistence, load_persistence

            confluence = compute_confluence(
                scanner_signals=scanner_signals,
                triangle_signals=triangle_signals,
                downtrend_break_signals=downtrend_break_signals,
                options_flow_signals=options_flow_signals,
                institutional=institutional,
                momentum_picks=momentum_picks,
                universe_rows=universe_rows,
                market_regime=market_regime,
            )
            print(f"  Confluence: {confluence['generated']} multi-leg names "
                  f"(of {len(confluence['watchlist'])} ranked)")
            top = confluence["watchlist"][0] if confluence["watchlist"] else None
            if top:
                print(f"    Top: {top['ticker']} — {top['n_legs']} legs (score {top['score']})")

            # Namespaced persistence for the new legs (migration anchors).
            mom_tickers = [p.get("ticker") for p in momentum_picks.get("picks", [])] if momentum_picks else []
            update_persistence([t["ticker"] for t in triangle_signals], date, namespace="triangle")
            update_persistence([s["ticker"] for s in downtrend_break_signals], date, namespace="downtrend_breakout")
            update_persistence([f["ticker"] for f in options_flow_signals], date, namespace="flow")
            update_persistence([t for t in mom_tickers if t], date, namespace="momentum")
            update_persistence([b.get("ticker") for b in institutional.get("top_buying", []) if b.get("ticker")], date, namespace="institutional")
            update_persistence(universe_syms, date, namespace="universe")

            namespaces_today = {
                "scanner": scanned_tickers,
                "triangle": [t["ticker"] for t in triangle_signals],
                "flow": [f["ticker"] for f in options_flow_signals],
                "momentum": [t for t in mom_tickers if t],
                "institutional": [b.get("ticker") for b in institutional.get("top_buying", []) if b.get("ticker")],
                "universe": universe_syms,
            }
            namespaces_persistence = {ns: load_persistence(ns) for ns in namespaces_today}
            migration = compute_migration(
                namespaces_today=namespaces_today,
                namespaces_persistence=namespaces_persistence,
                market_caps=universe_mcap,
                date=date,
            )
            motd = migration.get("migration_of_the_day")
            print(f"  Migration: {len(migration['migrations'])} maturation events"
                  + (f" — MOTD {motd['ticker']} {motd['note']}" if motd else ""))
        except Exception as e:
            print(f"  [WARN] Confluence/migration failed: {e}")

    # ── Stage 10c: TAO Pullback Screen ──
    # Scan the top strategy picks + momentum names + core watchlist for EMA-stack
    # pullbacks. Reuses the already-assembled candidate list so there is no extra
    # TradingView call — just the yfinance deep scan for confirmed setups.
    print("\n[10c/16] TAO PULLBACK SCREEN (EMA stack + pullback quality)")
    tao_results: list[dict] = []
    with timer.stage("TAO Screen"):
        try:
            import time as _tao_time
            from dossier.tao_screener import score_tao, _save_api_output as _tao_save
            _mom_tickers = [p.get("ticker", "") for p in (momentum_picks.get("picks", []) if momentum_picks else [])]
            _tao_pool = [t for t in dict.fromkeys(
                scanned_tickers[:25] + _mom_tickers + list(CORE_WATCHLIST)
            ) if not _is_junk(t)][:45]
            for _t in _tao_pool:
                _r = score_tao(_t)
                if _r:
                    tao_results.append(_r)
                _tao_time.sleep(0.05)
            tao_results.sort(key=lambda r: r["score"], reverse=True)
            if not dry_run:
                _tao_save(tao_results)
            _top_tao = [r for r in tao_results if r["grade"] in ("A+", "A")]
            print(f"  🌊 {len(tao_results)} TAO setups — {len(_top_tao)} A+/A: "
                  + (", ".join(f"{r['ticker']} {r['grade']} ({r['score']})" for r in _top_tao[:3]) or "none today"))
        except Exception as e:
            print(f"  [WARN] TAO screen failed: {e}")

    # ── Stage 10d: VCP (Volatility Contraction Pattern) Screen ──
    print("\n[10d/16] VCP SCREEN (coiling-spring setups)")
    vcp_results: list[dict] = []
    with timer.stage("VCP Screen"):
        try:
            import time as _vcp_time
            from dossier.vcp_screener import score_vcp, _save_api_output as _vcp_save
            _vcp_pool = [t for t in dict.fromkeys(
                scanned_tickers[:30] + list(CORE_WATCHLIST)
            ) if not _is_junk(t)][:50]
            for _t in _vcp_pool:
                _r = score_vcp(_t)
                if _r:
                    vcp_results.append(_r)
                _vcp_time.sleep(0.05)
            vcp_results.sort(key=lambda r: r["score"], reverse=True)
            if not dry_run:
                _vcp_save(vcp_results)
            _top_vcp = [r for r in vcp_results if r["grade"] in ("A+", "A")]
            print(f"  🌀 {len(vcp_results)} VCP setups — {len(_top_vcp)} A+/A: "
                  + (", ".join(f"{r['ticker']} {r['grade']} ({r['score']})" for r in _top_vcp[:3]) or "none today"))
        except Exception as e:
            print(f"  [WARN] VCP screen failed: {e}")

    # ── Stage 10e: PEAD (Post-Earnings Drift) Screen ──
    print("\n[10e/16] PEAD SCREEN (post-earnings drift)")
    pead_results: list[dict] = []
    with timer.stage("PEAD Screen"):
        try:
            import time as _pead_time
            from dossier.pead_screener import score_pead, _save_api_output as _pead_save
            _pead_pool = [t for t in dict.fromkeys(
                scanned_tickers[:30] + list(CORE_WATCHLIST)
            ) if not _is_junk(t)][:50]
            for _t in _pead_pool:
                _r = score_pead(_t)
                if _r:
                    pead_results.append(_r)
                _pead_time.sleep(0.05)
            pead_results.sort(key=lambda r: r["score"], reverse=True)
            if not dry_run:
                _pead_save(pead_results)
            _top_pead = [r for r in pead_results if r["grade"] in ("A+", "A")]
            print(f"  🌊 {len(pead_results)} PEAD setups — {len(_top_pead)} A+/A: "
                  + (", ".join(f"{r['ticker']} {r['grade']} ({r['score']})" for r in _top_pead[:3]) or "none today"))
        except Exception as e:
            print(f"  [WARN] PEAD screen failed: {e}")

    # ── Stage 10f: Screener Overlap (TAO/VCP/PEAD agreement) ──
    # Pure post-processing over the three result lists just computed above —
    # no extra API calls. Surfaces names that clear the bar on 2+ independent
    # setup screens the same day, which is the highest-signal subset of any
    # single screen's output.
    print("\n[10f/16] SCREENER OVERLAP (TAO/VCP/PEAD agreement)")
    with timer.stage("Screener Overlap"):
        try:
            from dossier.screener_overlap import compute_screener_overlap, _save_api_output as _overlap_save
            overlap = compute_screener_overlap(tao_results, vcp_results, pead_results)
            if not dry_run:
                _overlap_save(overlap)
            _top_overlap = overlap["tickers"][:3]
            print(f"  🎯 {overlap['overlap_count']} tickers in 2+ screens: "
                  + (", ".join(f"{e['ticker']} ({'+'.join(e['screens'])})" for e in _top_overlap) or "none today"))
        except Exception as e:
            print(f"  [WARN] Screener overlap failed: {e}")

    # ── Stage 8d: Daily Trading Setups (3-Style) ──
    print("\n[11/16] DAILY TRADING SETUPS (Day Trade / Swing / CSP)")
    daily_setups_data = {}
    try:
        from dossier.daily_setups import build_daily_setups, format_setups_text
        # Reuse payloads from momentum scoring
        daily_setups_data = build_daily_setups(
            payloads_for_scoring if 'payloads_for_scoring' in dir() else [],
            date,
            csp_data=csp_setups,
        )
        setups_text = format_setups_text(daily_setups_data)
        print(f"  {setups_text}")
    except Exception as e:
        print(f"  [WARN] Daily setups failed: {e}")

    # ── Stage 8e: Leveraged ETF Daily Screener ──
    print("\n[11b/16] LEVERAGED ETF SCREENER")
    leveraged_top_pick = None
    try:
        from dossier.data_sources.leveraged_daily_screener import generate_daily_screener
        lev_result = generate_daily_screener(date_str=date)
        if lev_result.get("top_picks"):
            leveraged_top_pick = lev_result["top_picks"][0]
            print(f"  ☢️ Top pick: {leveraged_top_pick['underlying']} → {leveraged_top_pick['etf']} (Grade {leveraged_top_pick['grade']}, ADX {leveraged_top_pick['adx']})")
        elif not lev_result.get("is_trade_day"):
            print(f"  ⚠️ No trade day (SPY ADX {lev_result['spy_adx']:.1f} < 20)")
        else:
            print(f"  No A/B grade picks today")
    except Exception as e:
        print(f"  [WARN] Leveraged screener failed: {e}")

    # ── Stage 8f: Daily Cuts (Substack/Report streamlined cuts) ──
    print("\n[11c/16] DAILY CUTS (Prime/Choice/Select)")
    daily_cuts = {}
    try:
        from dossier.daily_cuts import build_daily_cuts
        daily_cuts = build_daily_cuts(daily_setups_data, leveraged_top_pick)
        print(f"  ✓ Daily Cuts generated ({len(daily_cuts)} setups)")
    except Exception as e:
        print(f"  [WARN] Daily Cuts failed: {e}")

    # ── Stage 11d: Analyst Watchlist Overlay ──
    # Ingest the nightly analyst watchlist (email when available, else the
    # ANALYST_WATCHLIST env var) and cross-reference it against today's signals
    # to surface confirmed overlaps vs off-radar (narrow-universe-gap) names.
    print("\n[11d/16] ANALYST WATCHLIST OVERLAY")
    analyst_overlay: dict = {}
    try:
        from dossier.data_sources.watchlist_ingest import (
            parse_watchlist, cross_reference, fetch_latest_watchlist_email,
        )
        raw_watch = fetch_latest_watchlist_email() or os.environ.get("ANALYST_WATCHLIST", "")
        watch = parse_watchlist(raw_watch) if raw_watch else []
        if watch:
            signals_by_source = {
                "universe": universe_syms,
                "triangle": [t.get("ticker") for t in triangle_signals],
                "flow": [f.get("ticker") for f in options_flow_signals],
                "institutional": [s.get("ticker") for s in institutional.get("top_buying", [])],
                "momentum": [p.get("ticker") for p in (momentum_picks.get("picks", []) if momentum_picks else [])],
            }
            analyst_overlay = cross_reference(watch, signals_by_source)
            summ = analyst_overlay.get("summary", {})
            print(f"  {len(watch)} analyst names — {summ.get('overlap_count', 0)} confirmed, "
                  f"{len(summ.get('off_radar', []))} off-radar")
        else:
            print("  ⏭️ No analyst watchlist available (set ANALYST_WATCHLIST or wire email)")
    except Exception as e:
        print(f"  [WARN] Analyst watchlist overlay failed: {e}")

    # ── Stage 8c: Chart Generation ──
    print("\n[12/16] CHART GENERATION")
    try:
        from dossier.charts import generate_charts_for_dossier
        chart_tickers = [d["ticker"] for d in dossiers[:5]]
        charts = generate_charts_for_dossier(chart_tickers, output_dir=str(OUTPUT_DIR.parent / "charts"), max_charts=5)
        # Attach chart paths to dossier data
        chart_map = {c["ticker"]: c["path"] for c in charts}
        for d in dossiers:
            d["chart_path"] = chart_map.get(d["ticker"], "")
        print(f"  {len(charts)} charts generated")
    except Exception as e:
        print(f"  [WARN] Chart generation failed: {e}")
        charts = []

    # ── Stage 9: AI Narrative ──
    print("\n[13/16] AI NARRATIVE")
    from dossier.report.ai_narrative import generate_narrative
    ai_narrative = generate_narrative(market, institutional, scanner_signals, persistence, dossiers, leveraged_top_pick=leveraged_top_pick)

    # ── Stage 9a: Gamma Pin Gravity Watch ──
    # Check if OpEx week (approximate: date between 15th and 21st)
    day = int(date.split("-")[-1])
    is_opex_week = 14 <= day <= 22
    gamma_warnings = []
    if is_opex_week:
        print("\n[13a/16] GAMMA PIN GRAVITY WATCH (OpEx Week)")
        try:
            from dossier.gamma_pin_screener import scan_ticker, _next_monthly_opex
            # Scan top 5 momentum picks
            watch_tickers = [d["ticker"] for d in dossiers[:5]]
            # Dynamic monthly OpEx calculation
            target_expiry = _next_monthly_opex()
            # Market regime context for filtering
            vix_level = market_regime.get("vix", {}).get("vix_level", 20)
            regime = market_regime.get("regime", "NORMAL")
            is_risk_off = regime in ("FEAR", "PANIC")
            if is_risk_off:
                print(f"  ⚠️ REGIME: {regime} (VIX {vix_level:.1f}) — suppressing BELOW (long) signals")
            for ticker in watch_tickers:
                d_data = next((d for d in dossiers if d["ticker"] == ticker), {})
                res = scan_ticker(ticker, d_data.get("price", 0), target_expiry)
                if res and res["snap_score"] > 40:
                    # Regime gate: skip BELOW (long bias) in FEAR/PANIC
                    if is_risk_off and res["overext_dir"] == "BELOW":
                        print(f"  🚫 {ticker}: SKIPPED (BELOW in {regime} regime)")
                        continue
                    # Quality gate: skip GARBAGE gravity centroids
                    if res.get("grav_quality") == "GARBAGE":
                        print(f"  🗑️ {ticker}: SKIPPED (gravity centroid too far from price)")
                        continue
                    gamma_warnings.append(res)
                    gq = res.get("grav_quality", "?")
                    print(f"  ⚠️ {ticker}: SNAP {res['snap_score']} "
                          f"(OE {res['overext_pct']}% {res['overext_dir']}) "
                          f"[Grav:{gq}]")
        except Exception as e:
            print(f"  [WARN] Gamma watch failed: {e}")

    # ── Stage 9d: GEX (StrikeForge dealer positioning) ──
    # Gamma-exposure read on the top dossier picks: gamma flip, call/put walls,
    # dealer regime. Tradier-backed, capped to the top names. Never raises.
    print("\n[13d/16] GEX DEALER POSITIONING")
    gex_reads: list[dict] = []
    with timer.stage("GEX"):
        try:
            from dossier.data_sources.sf_gex import gex_read
            gex_tickers = [d["ticker"] for d in dossiers[:5]]
            for tkr in gex_tickers:
                r = gex_read(tkr)
                if r:
                    gex_reads.append(r)
                    print(f"  {tkr}: {r.get('regime', '?')} "
                          f"(flip {r.get('gamma_flip')}, net GEX {r.get('net_gex')})")
            if not gex_reads:
                print("  ⏭️ No GEX reads (no key / no chains)")
        except Exception as e:
            print(f"  [WARN] GEX failed: {e}")

    # ── Stage 9b: Ghost Dev Log ──
    print("\n[13b/16] GHOST DEV LOG")
    try:
        from dossier.report.ghost_log import generate_ghost_log
        ghost_log = generate_ghost_log(date)
        preview = ghost_log[:80].replace('<br>', ' ').replace('<em>', '').replace('</em>', '')
        print(f"  👻 {preview}...")
    except Exception as e:
        print(f"  [WARN] Ghost log failed: {e}")
        ghost_log = ""

    # ── Stage 9c: Ghost Suggestions ──
    print("\n[13c/16] GHOST SUGGESTIONS")
    try:
        from dossier.report.ghost_suggestions import generate_suggestions
        ghost_suggestions = generate_suggestions(date)
        preview = ghost_suggestions[:80].replace('<br>', ' ').replace('<b>', '').replace('</b>', '')
        print(f"  🗺️ {preview}...")
    except Exception as e:
        print(f"  [WARN] Ghost suggestions failed: {e}")
        ghost_suggestions = ""

    # ── Stage 10: Report Generation ──
    print("\n[14/16] REPORT GENERATION")
    from dossier.report.builder import build_report, build_pdf

    report_path = build_report(
        date=date,
        market=market,
        market_pulse=market_pulse,
        institutional=institutional,
        scanner_signals=scanner_signals,
        persistence=persistence,
        dossiers=dossiers,
        ai_narrative=ai_narrative,
        technical_setups=technical_setups,
        csp_setups=csp_setups,
        ghost_log=ghost_log,
        ghost_suggestions=ghost_suggestions,
        momentum_picks=momentum_picks,
        market_regime=market_regime,
        leveraged_top_pick=leveraged_top_pick,
        gamma_warnings=gamma_warnings,
        daily_cuts=daily_cuts,
        confluence=confluence,
        migration=migration,
        market_weather=market_weather_data,
    )

    pdf_path = None
    if generate_pdf:
        pdf_path = build_pdf(report_path)

    # ── Stage 11: Ticker Deep-Dive Pages ──
    print("\n[14b/16] TICKER PAGES")
    try:
        from dossier.pages.ticker_page import generate_all_ticker_pages
        ticker_pages = generate_all_ticker_pages(dossiers, date, institutional)
        print(f"  ✓ Generated {len(ticker_pages)} ticker pages")
    except Exception as e:
        print(f"  [WARN] Ticker pages failed: {e}")
        ticker_pages = []

    # ── Stage 11b: Auto-Watchlist Discovery ──
    print("\n[14c/16] AUTO-WATCHLIST (A-grade only)")
    try:
        watchlist_path = PROJECT_ROOT / "watchlist.txt"
        existing = set()
        if watchlist_path.exists():
            existing = set(l.strip().upper() for l in watchlist_path.read_text().splitlines() if l.strip())

        ticker_dir = PROJECT_ROOT / "docs" / "ticker"
        has_page = set()
        if ticker_dir.exists():
            has_page = set(d.name for d in ticker_dir.iterdir() if d.is_dir())

        new_adds = []
        for d in dossiers:
            ticker = d.get("ticker", "").upper()
            grade = d.get("scores", {}).get("grade", "")
            if grade == "A" and ticker and ticker not in existing and ticker not in has_page:
                new_adds.append(ticker)

        if new_adds:
            with open(watchlist_path, "a") as f:
                for t in new_adds:
                    f.write(f"{t}\n")
            print(f"  🆕 Auto-added {len(new_adds)} A-grade tickers: {', '.join(new_adds)}")
        else:
            print(f"  ✓ No new A-grade discoveries (checked {len(dossiers)} dossiers)")
    except Exception as e:
        print(f"  [WARN] Auto-watchlist failed: {e}")

    # ── Stage 11c: Watchlist Auto-Cleanup ──
    print("\n[14d/16] WATCHLIST CLEANUP")
    try:
        watchlist_path = PROJECT_ROOT / "watchlist.txt"
        if watchlist_path.exists():
            lines = watchlist_path.read_text().splitlines()
            cleaned = []
            removed = []
            ticker_dir = PROJECT_ROOT / "docs" / "ticker"
            for line in lines:
                stripped = line.strip().upper()
                if not stripped or stripped.startswith("#"):
                    cleaned.append(line)  # Keep comments and blanks
                    continue
                # If deep dive already exists, remove from watchlist
                dd_html = ticker_dir / stripped / "deep_dive.html"
                dd_md = ticker_dir / stripped / "deep_dive.md"
                if dd_html.exists() or dd_md.exists():
                    removed.append(stripped)
                else:
                    cleaned.append(line)
            if removed:
                watchlist_path.write_text("\n".join(cleaned) + "\n")
                print(f"  🧹 Removed {len(removed)} tickers with existing deep dives: {', '.join(removed)}")
            else:
                print(f"  ✓ No tickers to clean up")
    except Exception as e:
        print(f"  [WARN] Watchlist cleanup failed: {e}")

    # ── Stage 15: Update Index + Summary API ──
    print("\n[15/16] INDEX + STATUS + SUMMARY API")
    _update_index_page()

    # Generate Dossier Summary API (the atomic content unit)
    try:
        from dossier.report.summary_api import generate_summary_api
        summary = generate_summary_api(
            date=date,
            market_pulse=market_pulse,
            scanner_signals=scanner_signals,
            dossiers=dossiers,
            momentum_picks=momentum_picks,
            market=market,
            ai_narrative=ai_narrative,
            technical_setups=technical_setups,
            daily_setups=daily_setups_data,
            ghost_log=ghost_log,
            confluence=confluence,
            migration=migration,
            market_weather=market_weather_data,
            sector_rs=sector_rs,
        )
        # Auto-generate Substack teaser from the summary
        try:
            from dossier.report.substack_teaser import generate_teaser
            generate_teaser(summary)
        except Exception as te:
            print(f"  [WARN] Substack teaser failed: {te}")
        # Auto-post to Discord (PUBLIC teaser)
        try:
            from dossier.report.discord_notify import post_dossier_to_discord
            post_dossier_to_discord(summary)
        except Exception as de:
            print(f"  [WARN] Discord notification failed: {de}")
        # Private "Daily Review" push (Your Book + analyst overlay) — writes a
        # private payload for the Claude task to deliver; posts now if a private
        # webhook is configured. Never published.
        try:
            from dossier.report.daily_review_push import emit_push
            push = emit_push(summary, your_book=your_book, analyst_overlay=analyst_overlay)
            print(f"  ✓ Daily-review push staged ({len(push.get('phone_lines', []))} lines"
                  + (", webhook sent" if push.get("_webhook_sent") else ", file only") + ")")
        except Exception as pe:
            print(f"  [WARN] Daily-review push failed: {pe}")
    except Exception as e:
        print(f"  [WARN] Summary API failed: {e}")

    # RSS Feed generation
    try:
        from dossier.report.rss_feed import generate_rss_feed
        generate_rss_feed()
    except Exception as e:
        print(f"  [WARN] RSS feed failed: {e}")

    # ── Stage 12b: Blog Entry ──
    print("\n[15b/16] GHOST BLOG UPDATE")
    try:
        import json as _json
        blog_path = PROJECT_ROOT / "docs" / "blog" / "blog_entries.json"
        entries = []
        if blog_path.exists():
            with open(blog_path) as bf:
                entries = _json.load(bf)

        # Determine period based on current hour (UTC)
        from datetime import datetime as _dtm
        _h = _dtm.utcnow().hour
        _period = "morning" if _h < 14 else ("midday" if _h < 20 else "evening")
        _entry_key = f"{date}-{_period}"

        # Don't duplicate entries for the same period
        if not any(e.get("entry_key") == _entry_key for e in entries):
            # Pick a chart ticker — prefer gold pick if available
            chart_ticker = ""
            if momentum_picks and momentum_picks.get("picks"):
                chart_ticker = momentum_picks["picks"][0]["ticker"]
            elif scanner_signals:
                chart_ticker = scanner_signals[0]["symbol"]

            entries.append({
                "date": date,
                "entry_key": _entry_key,
                "period": _period,
                "ghost_log": ghost_log,
                "suggestions": ghost_suggestions,
                "commits": len([l for l in subprocess.run(
                    ["git", "log", "--since=7 days ago", "--oneline"],
                    cwd=str(PROJECT_ROOT), capture_output=True, text=True
                ).stdout.strip().split("\n") if l.strip()]),
                "files_changed": len(set(l.strip() for l in subprocess.run(
                    ["git", "log", "--since=7 days ago", "--name-only", "--pretty=format:"],
                    cwd=str(PROJECT_ROOT), capture_output=True, text=True
                ).stdout.strip().split("\n") if l.strip())),
                "chart_ticker": chart_ticker,
            })

            with open(blog_path, "w") as bf:
                _json.dump(entries, bf, indent=2)
            print(f"  ✓ Blog entry added for {_entry_key} (chart: {chart_ticker})")
        else:
            print(f"  ✓ Blog entry already exists for {_entry_key}")
    except Exception as e:
        print(f"  [WARN] Blog update failed: {e}")

    # ── Stage 13: Git Push ──
    if not dry_run:
        # ── Stage 12c: Revenue Stats Auto-Refresh ──
        print("\n[15c/16] REVENUE + GA4 STATS")
        try:
            from dossier.fetch_revenue import fetch_stripe_revenue
            import json as _rev_json
            rev_stats = fetch_stripe_revenue()
            if rev_stats:
                rev_out = PROJECT_ROOT / "landing" / "data" / "revenue_stats.json"
                rev_out.parent.mkdir(parents=True, exist_ok=True)
                with open(rev_out, "w") as rf:
                    _rev_json.dump(rev_stats, rf, indent=2)
                print(f"  ✓ Revenue stats updated → {rev_out}")
            else:
                print("  ⏭️ Skipped (no Stripe key available)")
        except Exception as e:
            print(f"  [WARN] Revenue refresh failed: {e}")

        # GA4 Analytics Refresh (only locally — needs OAuth)
        if not os.environ.get("GITHUB_ACTIONS"):
            try:
                from dossier.fetch_ga4_stats import fetch_ga4_stats
                ga4_result = fetch_ga4_stats()
                if ga4_result:
                    print(f"  ✓ GA4 stats refreshed")
            except Exception as e:
                print(f"  [WARN] GA4 refresh failed: {e}")

        # Landing stats auto-refresh (scanner strategies count, ETFs, watchlist size)
        try:
            import json as _lstats_json
            landing_stats = {
                "scanner_strategies": len(SCANNER_STRATEGIES),
                "etf_count": len(__import__('dossier.config', fromlist=['SECTOR_ETFS']).SECTOR_ETFS),
                "watchlist_size": len(CORE_WATCHLIST),
                "signals_today": len(scanner_signals),
                "dossiers_today": len(dossiers),
                "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "market_regime": {
                    "vix_level": market.get("vix", {}).get("vix_level", 0),
                    "regime_name": market.get("vix", {}).get("regime_name", "UNKNOWN"),
                    "spy_change": market_pulse[0].get("change_pct", 0) if market_pulse else 0,
                    "date": date,
                },
            }
            ls_path = PROJECT_ROOT / "landing" / "data" / "pipeline_stats.json"
            ls_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ls_path, "w") as lf:
                _lstats_json.dump(landing_stats, lf, indent=2)
            print(f"  ✓ Landing stats updated → {ls_path}")
        except Exception as e:
            print(f"  [WARN] Landing stats failed: {e}")

        # ── Stage 15d: Auto-Backtest ──
        print("\n[15d/16] AUTO-BACKTEST")
        with timer.stage("Auto-Backtest"):
            from dossier.backtesting.auto_backtest import main as run_backtest
            run_backtest()
            print(f"  ✓ Backtest complete")

        # ── Stage 15e: Track Record ──
        print("\n[15e/16] TRACK RECORD UPDATE")
        try:
            from dossier.backtesting.track_record_generator import generate_track_record
            generate_track_record()
        except Exception as e:
            print(f"  [WARN] Track record update failed: {e}")

        # ── Stage 15f: Scan Archive Logging ──
        # Appends today's picks + full technical snapshot to the JSONL archive
        # that dossier/backtesting/screen_health.py and pattern_matcher.py read
        # (both already built, but sat dormant since nothing populated the archive).
        print("\n[15f/16] SCAN ARCHIVE")
        with timer.stage("Scan Archive"):
            from dossier.backtesting.scan_logger import log_todays_picks, update_forward_returns
            log_todays_picks()
            update_forward_returns()
            print(f"  ✓ Scan archive updated")

        # ── Stage 15g: Screen Health Monitor ──
        # Rolling win-rate per screen/grade/regime, now that Stage 15f is
        # actually populating the scan archive it reads from. Writes
        # docs/api/screen-health.json for the screen-health dashboard page.
        print("\n[15g/16] SCREEN HEALTH")
        try:
            from dossier.backtesting.screen_health import write_health_json
            health = write_health_json()
            print(f"  ✓ Screen health updated ({health['total_validated']} validated entries)")
        except Exception as e:
            print(f"  [WARN] Screen health update failed: {e}")

        # ── Sync regime history to docs/ for the Mood Ring widget (GH Pages) ──
        import shutil as _shutil
        _rh_landing = PROJECT_ROOT / "landing" / "data" / "regime_history.json"
        _rh_docs = PROJECT_ROOT / "docs" / "data" / "regime_history.json"
        try:
            if _rh_landing.exists():
                _rh_docs.parent.mkdir(parents=True, exist_ok=True)
                _shutil.copy2(_rh_landing, _rh_docs)
                print(f"  ✓ Regime history synced → docs/data/")
        except Exception as _sync_e:
            print(f"  [WARN] Regime history sync failed: {_sync_e}")

        # ── Sync breadth history to docs/ for the dashboard (GH Pages) ──
        _bh_landing = PROJECT_ROOT / "landing" / "data" / "breadth_history.json"
        _bh_docs = PROJECT_ROOT / "docs" / "data" / "breadth_history.json"
        try:
            if _bh_landing.exists():
                _bh_docs.parent.mkdir(parents=True, exist_ok=True)
                _shutil.copy2(_bh_landing, _bh_docs)
                print(f"  ✓ Breadth history synced → docs/data/")
        except Exception as _sync_e:
            print(f"  [WARN] Breadth history sync failed: {_sync_e}")

        # ── Sync quality breadth history to docs/ for the dashboard (GH Pages) ──
        _qb_landing = PROJECT_ROOT / "landing" / "data" / "quality_breadth_history.json"
        _qb_docs = PROJECT_ROOT / "docs" / "data" / "quality_breadth_history.json"
        try:
            if _qb_landing.exists():
                _qb_docs.parent.mkdir(parents=True, exist_ok=True)
                _shutil.copy2(_qb_landing, _qb_docs)
                print(f"  ✓ Quality breadth history synced → docs/data/")
        except Exception as _sync_e:
            print(f"  [WARN] Quality breadth history sync failed: {_sync_e}")

        # ── Sync VRP history to docs/ for the dashboard (GH Pages) ──
        _vrp_landing = PROJECT_ROOT / "landing" / "data" / "vrp_history.json"
        _vrp_docs = PROJECT_ROOT / "docs" / "data" / "vrp_history.json"
        try:
            if _vrp_landing.exists():
                _vrp_docs.parent.mkdir(parents=True, exist_ok=True)
                _shutil.copy2(_vrp_landing, _vrp_docs)
                print(f"  ✓ VRP history synced → docs/data/")
        except Exception as _sync_e:
            print(f"  [WARN] VRP history sync failed: {_sync_e}")

        print("\n[16/16] GIT PUSH")
        print("  Committing to Git...")
        try:
            subprocess.run(["git", "add", "docs/", "dossier/persistence/", "landing/blog/", "landing/data/", "watchlist.txt"],
                           cwd=str(PROJECT_ROOT), check=True)
            subprocess.run(
                ["git", "commit", "-m", f"📊 Alpha Dossier {date}"],
                cwd=str(PROJECT_ROOT), check=True
            )
            subprocess.run(["git", "push"], cwd=str(PROJECT_ROOT), check=True)
            print("  ✓ Pushed to GitHub")
        except subprocess.CalledProcessError as e:
            print(f"  [WARN] Git push failed: {e}")
    else:
        print("\n[SKIP] Dry run — skipping git push")

    # ── Substack Draft (post-push) ──
    if not dry_run:
        print("\n[POST] SUBSTACK DRAFT")
        try:
            from substack_dossier import build_dossier_doc, SubstackClient
            client = SubstackClient()
            if client.authenticate():
                title, subtitle, doc = build_dossier_doc(date, client=client)
                result = client.create_draft(title, subtitle, doc)
                if result:
                    draft_id = result.get("id")
                    print(f"  ✓ Substack draft created! Edit: https://{client.pub}/publish/post/{draft_id}")
                else:
                    print("  [WARN] Substack draft creation failed")
            else:
                print("  [WARN] Substack auth failed — refresh SID")
        except Exception as e:
            print(f"  [WARN] Substack draft failed: {e}")

    # ── Summary + Status Dashboard ──
    pipeline_summary = {
        "market_pulse": len(market_pulse),
        "signals_count": len(scanner_signals),
        "dossiers_enriched": len(dossiers),
        "ticker_pages": len(ticker_pages),
        "technical_setups": len(technical_setups) if technical_setups else 0,
        "csp_setups": len(csp_setups) if csp_setups else 0,
        "charts_generated": len(charts) if charts else 0,
    }

    # Generate Pipeline Status Dashboard
    try:
        from dossier.report.status_page import generate_status_page
        stats = timer.to_dict(date, dry_run, pipeline_summary)
        generate_status_page(stats)
        print("  ✓ Pipeline Status Dashboard generated")
    except Exception as e:
        print(f"  [WARN] Status dashboard failed: {e}")

    print("\n" + "=" * 72)
    print("  ✅ PIPELINE COMPLETE")
    total_time = time.time() - timer._start_time
    print(f"  ⏱️  Total: {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"  Report: {report_path}")
    if pdf_path:
        print(f"  PDF:    {pdf_path}")
    print(f"  Pulse:  {len(market_pulse)} benchmarks")
    print(f"  Signals: {len(scanner_signals)}")
    print(f"  Dossiers: {len(dossiers)}")
    print(f"  Ticker Pages: {len(ticker_pages)}")
    print(f"  VIX: {market['vix']['vix_level']} ({market['vix']['regime_name']})")
    if momentum_picks and momentum_picks.get("picks"):
        gold = momentum_picks["picks"][0]
        print(f"  🥇 GOLD PICK: {gold['ticker']} (Score: {gold['score']}/100)")
    if timer.errors:
        print(f"  ⚠️  Errors: {len(timer.errors)}")
        for err in timer.errors:
            print(f"     └─ {err['stage']}: {err['message'][:80]}")
    print("=" * 72)

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Ghost Alpha Dossier — Daily Report Generator")
    parser.add_argument("--date", type=str, default=None, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Skip git push")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    args = parser.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_pipeline(date=date, dry_run=args.dry_run, generate_pdf=not args.no_pdf)


if __name__ == "__main__":
    main()
