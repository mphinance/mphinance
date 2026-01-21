from nicegui import ui, app
import scanner_logic
import strategies
import asbury_metrics
import fundamental_metrics
import options_flow
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- STYLING (Dark Navy Theme matching screenshot) ---
ui.add_head_html('''
<style>
    body { 
        background-color: #0a0e17; 
        color: #e5e5e5; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .nicegui-content { padding: 0; }
    .q-drawer { background-color: #0d1320 !important; border-right: 1px solid #1a2332; }
    
    /* Metric Cards */
    .metric-card { 
        background: linear-gradient(145deg, #111827, #0d1320);
        padding: 1.25rem; 
        border-radius: 12px; 
        border: 1px solid #1f2937;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .metric-label { 
        font-size: 0.75rem; 
        color: #6b7280; 
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .metric-value { 
        font-size: 2rem; 
        font-weight: 700; 
        color: #00d4aa; 
    }
    
    /* Status Indicators */
    .st-bullish { color: #10b981; }
    .st-bearish { color: #ef4444; }
    .st-neutral { color: #6b7280; }
    
    /* Table Styling */
    .q-table { background-color: #0d1320 !important; }
    .q-table thead tr th { 
        background-color: #111827 !important; 
        color: #9ca3af !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.05em;
    }
    .q-table tbody tr { background-color: #0d1320 !important; }
    .q-table tbody tr:hover { background-color: #1a2332 !important; }
    .q-table tbody tr td { color: #e5e5e5 !important; border-color: #1f2937 !important; }
    
    /* Sidebar Styling */
    .sidebar-title { 
        font-size: 1.25rem; 
        font-weight: bold; 
        color: #fff;
        text-align: center;
        padding: 1rem 0;
    }
    .sidebar-section { 
        background-color: #111827;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .section-label {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    /* Card styling */
    .nicegui-card {
        background-color: #111827 !important;
        border: 1px solid #1f2937;
    }
    
    /* Button styling */
    .q-btn--outline { border-color: #00d4aa !important; color: #00d4aa !important; }
</style>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
''')

# --- STATE ---
class AppState:
    def __init__(self):
        self.mode = 'Market Screens'
        self.scanner_results = pd.DataFrame()
        self.target_ticker = ''
        self.selected_strategy = 'Momentum with Pullback'
        self.strategy_params = {}
        self.selected_webhooks = []

state = AppState()

# --- WEBHOOK HELPERS ---

def get_configured_webhooks():
    """Load webhooks from environment variables (WEBHOOK_*)."""
    webhooks = {}
    for key, value in os.environ.items():
        if key.startswith("WEBHOOK_"):
            name = key.replace("WEBHOOK_", "").replace("_", " ").title()
            webhooks[name] = value
    return webhooks

def get_google_sheets_webhook():
    """Get Google Sheets webhook URL from environment."""
    return os.getenv("GOOGLE_SHEETS_WEBHOOK", "")

# --- HELPER FUNCTIONS ---

def format_market_cap(value):
    """Format market cap with B/M suffix."""
    if pd.isna(value) or value == 0:
        return '-'
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    else:
        return f"${value:,.0f}"

def format_number(value, decimals=2, prefix='', suffix=''):
    """Format a number with optional prefix/suffix."""
    if pd.isna(value):
        return '-'
    return f"{prefix}{value:.{decimals}f}{suffix}"

def format_premium(value):
    """Format premium values for display."""
    if value is None:
        return '-'
    if abs(value) >= 1e9:
        return f"${value/1e9:.1f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:,.0f}"

# --- UI LOGIC ---

def update_ui():
    content_container.clear()
    with content_container:
        if state.mode == 'Market Screens':
            render_scanner_view()
        elif state.mode == 'Single Ticker Audit':
            render_audit_view()

def render_market_header():
    """Render a compact Asbury 6 Market Health Header."""
    with ui.card().classes('w-full bg-gray-900/50 border border-gray-800 p-4 mb-4 backdrop-blur-md'):
        with ui.row().classes('w-full items-center justify-between'):
            # Header Title & Signal
            with ui.row().classes('items-center gap-4'):
                ui.label('📊 Market Health').classes('text-lg font-bold text-gray-300')
                
                # Signal placeholder - updated async
                signal_container = ui.row().classes('items-center gap-2')
                with signal_container:
                    ui.spinner('dots', size='sm').classes('text-gray-500')
                    
            # Expansion for detailed grid
            details = ui.expansion('Show Details', icon='analytics').props('dense flat color=cyan')
            details.classes('text-sm text-gray-400')

    async def load_weather():
        result = await asyncio.to_thread(asbury_metrics.get_asbury_6_signals)
        
        signal_container.clear()
        with signal_container:
            if result.get('error'):
                ui.icon('cloud_off', color='gray')
                ui.label('Data Unavailable').classes('text-xs text-gray-500')
                return

            signal = result['signal']
            count = result['positive_count']
            
            # Signal visual
            color = 'green-400' if signal == 'BUY' else 'red-400' if signal == 'CASH' else 'yellow-400'
            bg_color = 'bg-green-900/30' if signal == 'BUY' else 'bg-red-900/30' if signal == 'CASH' else 'bg-yellow-900/30'
            
            with ui.row().classes(f'{bg_color} px-3 py-1 rounded-full items-center gap-2 border border-{color}'):
                ui.icon('circle', color=color.split('-')[0]).classes('text-xs')
                ui.label(signal).classes(f'text-sm font-bold text-{color}')
                ui.label(f'({count}/6)').classes('text-xs text-gray-400')

        # Populate Details Grid
        details.clear()
        with details:
            if result.get('error'):
                # Fun error messages for when market data isn't available
                import random
                fun_messages = [
                    "🏖️ The market is on vacation! Even Wall Street needs a break sometimes.",
                    "😴 Markets are sleeping... probably dreaming of green candles.",
                    "🎉 It's a holiday! The bulls and bears are at a party together.",
                    "📺 Nothing to see here... the market data is binge-watching Netflix.",
                    "🌙 After hours vibes... the stock market has gone to bed.",
                    "☕ Coffee break! Even algorithms need their caffeine fix.",
                    "🎮 The trading floor is playing video games right now.",
                    "🧘 Market is meditating. Ommmm... no volatility here.",
                ]
                with ui.column().classes('w-full items-center justify-center py-8'):
                    ui.label('🔌').classes('text-4xl mb-4')
                    ui.label(random.choice(fun_messages)).classes('text-sm text-cyan-400 text-center mb-2')
                    ui.label(f"Technical details: {result['error']}").classes('text-xs text-gray-500')
            else:
                ui.separator().classes('bg-gray-800 my-2')
                # 3x2 Grid
                with ui.grid(columns=3).classes('w-full gap-4'):
                    metrics = result['metrics']
                    for metric in metrics:
                        is_pos = metric['status'] == 'Positive'
                        color = 'text-green-400' if is_pos else 'text-red-400'
                        icon = 'trending_up' if is_pos else 'trending_down'
                        
                        with ui.column().classes('bg-gray-900 p-3 rounded border border-gray-800'):
                            with ui.row().classes('w-full justify-between items-center'):
                                ui.label(metric['name']).classes('text-xs font-bold text-gray-400')
                                ui.icon(icon).classes(f'text-xs {color}')
                            ui.label(metric['value']).classes(f'text-sm font-bold {color} mt-1')
                            ui.label(metric['description']).classes('text-xs text-gray-500')

    ui.timer(0.1, load_weather, once=True)



def render_audit_view():
    # Back to Scanner Button - Prominent
    def go_back():
        state.mode = 'Market Screens'
        update_ui()
    
    with ui.row().classes('w-full items-center justify-between mb-4'):
        ui.button('← Back to Scanner', on_click=go_back).props('flat color=cyan no-caps').classes('text-lg')
        ui.label('Single Ticker Audit').classes('text-2xl font-bold text-white')
        ui.element('div')  # Spacer for centering
    
    with ui.row().classes('items-center gap-4 mb-4'):
        ticker_input = ui.input('Ticker').props('outlined dense dark').bind_value(state, 'target_ticker')
        
        async def on_analyze():
            await run_audit_async(state.target_ticker)
        
        ui.button('Analyze', on_click=on_analyze).props('color=primary')
    
    if state.target_ticker:
        audit_results_container = ui.column().classes('w-full')
        
        async def load_audit():
            await run_audit_async(state.target_ticker, audit_results_container)
        
        ui.timer(0.1, load_audit, once=True)

async def run_audit_async(ticker, container=None):
    """Async audit that loads the text box first, then other sections progressively."""
    if container is None:
        update_ui()
        return

    container.clear()
    with container:
        if not ticker:
            return

        ui.notify(f'Analyzing {ticker}...', type='info')
        
        # Show loading spinner while fetching basic data
        loading_row = ui.row().classes('w-full justify-center py-4')
        with loading_row:
            ui.spinner('dots', size='lg')
            ui.label(f'Fetching price data for {ticker}...').classes('text-gray-400 ml-4')
        
        # Fetch basic price data in background
        data = await asyncio.to_thread(scanner_logic.get_live_data, ticker)
        loading_row.delete()
        
        if data is None:
            ui.label("Ticker not found or insufficient data (200+ days required).").classes('text-red-500 font-bold')
            return

        last = data.iloc[-1]
        price = float(last['Close'])
        sma200 = float(last['SMA200'])
        ema21 = float(last['EMA21'])
        atr = float(last['ATR'])
        atr55 = float(last['ATR55'])
        stoch = float(last['Stoch'])
        
        # Calculate squeeze ratio (lower = more compressed)
        squeeze_ratio = atr / atr55 if atr55 > 0 else 1.0
        is_squeezed = squeeze_ratio < 0.85  # ATR14 less than 85% of ATR55 indicates squeeze

        # Metrics
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.column().classes('metric-card flex-1'):
                ui.label('Current Price').classes('metric-label')
                ui.label(f"${price:.2f}").classes('metric-value')
            with ui.column().classes('metric-card flex-1'):
                ui.label('200 SMA').classes('metric-label')
                ui.label(f"${sma200:.2f}").classes('metric-value')
            with ui.column().classes('metric-card flex-1'):
                ui.label('ATR (14)').classes('metric-label')
                ui.label(f"${atr:.2f}").classes('metric-value')
            with ui.column().classes('metric-card flex-1'):
                ui.label('ATR (55)').classes('metric-label')
                ui.label(f"${atr55:.2f}").classes('metric-value')
            with ui.column().classes('metric-card flex-1'):
                ui.label('EMA 21').classes('metric-label')
                ui.label(f"${ema21:.2f}").classes('metric-value')
            with ui.column().classes('metric-card flex-1'):
                ui.label('Stoch (8,3,3)').classes('metric-label')
                ui.label(f"{stoch:.1f}").classes('metric-value')
        
        # Squeeze indicator row
        with ui.row().classes('w-full gap-4 mb-4'):
            squeeze_bg = 'bg-green-900' if is_squeezed else 'bg-gray-800'
            squeeze_text = '🔋 SQUEEZED' if is_squeezed else 'Normal Volatility'
            with ui.column().classes(f'metric-card {squeeze_bg}'):
                ui.label('Volatility Squeeze').classes('metric-label')
                ui.label(squeeze_text).classes('text-lg font-bold text-white')
                ui.label(f"ATR14/ATR55 Ratio: {squeeze_ratio:.2f}").classes('text-sm text-gray-400')

        ui.separator().classes('bg-gray-700 my-4')

        with ui.row().classes('w-full gap-4'):
            # Chart - Zoomed to last 30 days by default
            with ui.card().classes('w-2/3 bg-gray-900'):
                # Get last 30 days of data
                recent_data = data.tail(30)
                
                fig = go.Figure(data=[go.Candlestick(
                    x=recent_data.index, 
                    open=recent_data['Open'], 
                    high=recent_data['High'], 
                    low=recent_data['Low'], 
                    close=recent_data['Close'], 
                    name="Price"
                )])
                colors = ['#00d4aa', '#00b4d8', '#3a86ff', '#8338ec', '#ff006e']
                for i, p in enumerate([8, 21, 34, 55, 89]):
                    fig.add_trace(go.Scatter(
                        x=recent_data.index, 
                        y=recent_data[f'EMA{p}'], 
                        name=f'EMA {p}', 
                        line=dict(color=colors[i], width=1.5)
                    ))
                fig.add_trace(go.Scatter(
                    x=recent_data.index, 
                    y=recent_data['SMA200'], 
                    name='200 SMA', 
                    line=dict(color='white', width=2, dash='dash')
                ))
                fig.update_layout(
                    template="plotly_dark", 
                    height=500, 
                    margin=dict(l=0, r=0, t=30, b=0), 
                    xaxis_rangeslider_visible=False, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(13,19,32,1)',
                    title=dict(text=f'{ticker} - Last 30 Days', font=dict(size=14, color='#9ca3af')),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=10)
                    )
                )
                ui.plotly(fig).classes('w-full h-full')

            # Analysis
            with ui.card().classes('w-1/3 bg-gray-900 p-4'):
                ui.label("⚙️ Mechanics Check").classes('text-xl font-bold mb-4 text-white')
                
                if price > sma200:
                    ui.label("✅ SAILING WITH THE WIND").classes('text-green-400 font-bold')
                else:
                    ui.label("❌ STAGNANT WATER: Below 200 SMA").classes('text-red-400 font-bold')

                ui.label("📊 EMA Stack Values").classes('text-lg font-bold mt-4 mb-2 text-white')
                e8, e21, e34, e55, e89 = (float(last['EMA8']), float(last['EMA21']), 
                                          float(last['EMA34']), float(last['EMA55']), float(last['EMA89']))
                
                with ui.column().classes('gap-1'):
                    ui.label(f"EMA 8: ${e8:.2f}")
                    ui.label(f"EMA 21: ${e21:.2f}")
                    ui.label(f"EMA 34: ${e34:.2f}")
                    ui.label(f"EMA 55: ${e55:.2f}")
                    ui.label(f"EMA 89: ${e89:.2f}")

                is_stacked = (e8 > e21 > e34 > e55 > e89)
                if is_stacked:
                    ui.label("✅ BULLISH STACK CONFIRMED").classes('text-green-400 font-bold mt-2')
                else:
                    ui.label("⚠️ STACK DISORDERED").classes('text-yellow-400 font-bold mt-2')

                dist_to_21 = abs(price - e21)
                if dist_to_21 <= atr:
                    ui.label("🎯 IN THE BUY ZONE (Within 1 ATR)").classes('text-blue-400 font-bold mt-2')
                else:
                    ui.label("⌛ OVEREXTENDED: Wait for Pullback").classes('text-yellow-400 font-bold mt-2')

                ui.separator().classes('bg-gray-700 my-4')
                
                ui.label("📝 Tactical Execution").classes('text-xl font-bold mb-2 text-white')
                stop_loss = price - (atr * 1.5)
                tp1 = price + (atr * 1.2)
                tp2 = price + (atr * 2.5)
                
                ui.label(f"Stop Loss: ${stop_loss:.2f}").classes('text-red-400')
                ui.label(f"Take Profit 1: ${tp1:.2f}").classes('text-green-400')
                ui.label(f"Take Profit 2: ${tp2:.2f}").classes('text-green-400')

        # === QUICK COPY SECTION - Available immediately ===
        ui.separator().classes('bg-gray-700 my-4')
        ui.label('📋 Quick Copy (Basic Technicals)').classes('text-xl font-bold text-white mb-2')
        ui.label('Copy this data now while detailed analysis loads below:').classes('text-gray-400 text-sm mb-2')
        
        # Build quick export with just the basic data we have
        quick_lines = [
            f"# {ticker} Quick Technical Summary",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Price",
            f"Close: ${price:.2f}",
            "",
            "## Moving Averages",
            f"SMA 200: ${sma200:.2f}",
            f"EMA 8: ${e8:.2f}",
            f"EMA 21: ${e21:.2f}",
            f"EMA 34: ${e34:.2f}",
            f"EMA 55: ${e55:.2f}",
            f"EMA 89: ${e89:.2f}",
            f"EMA Stack: {'Bullish' if is_stacked else 'Disordered'}",
            f"Above SMA 200: {'Yes' if price > sma200 else 'No'}",
            "",
            "## Momentum",
            f"Stochastic K (8,3,3): {stoch:.1f}",
            "",
            "## Volatility",
            f"ATR (14): ${atr:.2f}",
            f"ATR (55): ${atr55:.2f}",
            f"ATR14/ATR55 Ratio: {squeeze_ratio:.2f}",
            f"Squeeze Status: {'SQUEEZED' if is_squeezed else 'Normal'}",
            "",
            "## Calculated Levels",
            f"Stop Loss (1.5 ATR): ${stop_loss:.2f}",
            f"Target 1 (1.2 ATR): ${tp1:.2f}",
            f"Target 2 (2.5 ATR): ${tp2:.2f}",
        ]
        quick_export = '\n'.join(quick_lines)
        ui.textarea(value=quick_export).props('dark outlined readonly').classes('w-full').style('height: 180px; font-family: monospace;')
        
        # === SEND TO DISCORD ===
        webhooks = get_configured_webhooks()
        if webhooks:
            with ui.row().classes('w-full gap-2 mt-2'):
                async def send_audit_to_discord():
                    selected = state.selected_webhooks
                    if not selected:
                        ui.notify('⚠️ No webhooks selected (check Export Settings in sidebar)', type='warning')
                        return
                    
                    # Build single ticker embed
                    embed = {
                        "title": f"📊 {ticker} Technical Analysis",
                        "description": f"**${price:.2f}** | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        "color": 0x00d4aa if price > sma200 else 0xef4444,
                        "fields": [
                            {
                                "name": "📈 Price Status",
                                "value": f"{'✅ Above 200 SMA' if price > sma200 else '❌ Below 200 SMA'}",
                                "inline": True
                            },
                            {
                                "name": "📊 EMA Stack",
                                "value": f"{'✅ Bullish' if is_stacked else '⚠️ Disordered'}",
                                "inline": True
                            },
                            {
                                "name": "🎯 Buy Zone",
                                "value": f"{'✅ Within 1 ATR' if dist_to_21 <= atr else '⌛ Overextended'}",
                                "inline": True
                            },
                            {
                                "name": "🔋 Volatility",
                                "value": f"ATR: ${atr:.2f} | {'🔋 SQUEEZED' if is_squeezed else 'Normal'}",
                                "inline": False
                            },
                            {
                                "name": "📉 EMAs",
                                "value": f"8: ${e8:.2f} | 21: ${e21:.2f} | 34: ${e34:.2f} | 55: ${e55:.2f} | 89: ${e89:.2f}",
                                "inline": False
                            },
                            {
                                "name": "🎯 Levels",
                                "value": f"SL: ${stop_loss:.2f} | TP1: ${tp1:.2f} | TP2: ${tp2:.2f}",
                                "inline": False
                            }
                        ],
                        "footer": {"text": "Momentum Phinance Audit"},
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    discord_payload = {"embeds": [embed]}
                    
                    success_count = 0
                    for name in selected:
                        url = webhooks.get(name)
                        if not url:
                            continue
                        try:
                            response = await asyncio.to_thread(requests.post, url, json=discord_payload)
                            if response.status_code in (200, 204):
                                success_count += 1
                            else:
                                ui.notify(f'❌ {name}: {response.status_code}', type='negative')
                        except Exception as e:
                            ui.notify(f'❌ {name}: {e}', type='negative')
                    
                    if success_count > 0:
                        ui.notify(f'✅ Sent {ticker} audit to {success_count} webhook(s)!', type='positive')
                
                ui.button(f'🚀 Send to Discord ({len(state.selected_webhooks)})', on_click=send_audit_to_discord).props('color=purple')
        
        # === ML PRICE PREDICTION SECTION ===
        ui.separator().classes('bg-gray-700 my-6')
        ui.label('🔮 AI Price Prediction').classes('text-xl font-bold text-white mb-4')
        
        # Calculate technical indicators and train model
        analyzer = stock_analyzer.StockAnalyzer()
        data_with_indicators = analyzer.calculate_technical_indicators(data)
        model_info = analyzer.train_prediction_model(data_with_indicators)
        
        if model_info:
            current_price = float(data['Close'].iloc[-1])
            prediction = analyzer.predict_price_range(model_info, current_price)
            
            if prediction:
                horizon = prediction['horizon']
                confidence = model_info['test_score']
                
                # Header with horizon
                ui.label(f"📆 {horizon}-Day Price Target Range").classes('text-lg text-cyan-400 mb-2')
                
                with ui.row().classes('w-full gap-4 mb-4'):
                    # Low target card
                    low_color = 'text-red-400' if prediction['low_change_pct'] < 0 else 'text-green-400'
                    with ui.column().classes('metric-card flex-1 bg-red-900/30 border border-red-800'):
                        ui.label('Low Target').classes('metric-label')
                        ui.label(f"${prediction['low']:.2f}").classes('text-2xl font-bold text-white')
                        ui.label(f"{prediction['low_change_pct']:+.2f}%").classes(f'{low_color} font-bold')
                    
                    # Expected target card (center, larger)
                    exp_color = 'bg-green-900' if prediction['expected_change_pct'] > 0 else 'bg-red-900'
                    with ui.column().classes(f'metric-card flex-1 {exp_color} border-2 border-cyan-500'):
                        ui.label('Expected').classes('metric-label')
                        ui.label(f"${prediction['expected']:.2f}").classes('text-3xl font-bold text-white')
                        change_color = 'text-green-400' if prediction['expected_change_pct'] > 0 else 'text-red-400'
                        ui.label(f"{prediction['expected_change_pct']:+.2f}%").classes(f'{change_color} font-bold text-lg')
                    
                    # High target card 
                    high_color = 'text-green-400' if prediction['high_change_pct'] > 0 else 'text-red-400'
                    with ui.column().classes('metric-card flex-1 bg-green-900/30 border border-green-800'):
                        ui.label('High Target').classes('metric-label')
                        ui.label(f"${prediction['high']:.2f}").classes('text-2xl font-bold text-white')
                        ui.label(f"{prediction['high_change_pct']:+.2f}%").classes(f'{high_color} font-bold')
                
                # Model metrics row
                with ui.row().classes('w-full gap-4 mb-4'):
                    # Confidence bar
                    conf_level = "High" if confidence > 0.8 else ("Medium" if confidence > 0.6 else "Low")
                    conf_bg = 'bg-green-900' if confidence > 0.8 else ('bg-yellow-900' if confidence > 0.6 else 'bg-red-900')
                    with ui.column().classes(f'metric-card flex-1 {conf_bg}'):
                        ui.label('Model Confidence').classes('metric-label')
                        ui.label(f"{confidence:.1%}").classes('text-xl font-bold text-white')
                        ui.label(conf_level).classes('text-gray-300 text-sm')
                    
                    # Range confidence
                    range_conf = prediction['confidence']
                    range_bg = 'bg-green-900' if range_conf > 0.7 else ('bg-yellow-900' if range_conf > 0.4 else 'bg-red-900')
                    with ui.column().classes(f'metric-card flex-1 {range_bg}'):
                        ui.label('Range Confidence').classes('metric-label')
                        ui.label(f"{range_conf:.1%}").classes('text-xl font-bold text-white')
                        ui.label('Tree agreement').classes('text-gray-300 text-sm')
                    
                    # Training info
                    with ui.column().classes('metric-card flex-1'):
                        ui.label('Model Performance').classes('metric-label')
                        ui.label(f"Train: {model_info['train_score']:.1%}").classes('text-cyan-400')
                        ui.label(f"Test: {model_info['test_score']:.1%}").classes('text-cyan-400')
                
                # Top features driving prediction
                with ui.expansion('📊 Top Prediction Factors', icon='analytics').classes('w-full'):
                    with ui.row().classes('gap-2 flex-wrap'):
                        for feature, importance in model_info['feature_importance'].items():
                            # Clean up feature name for display
                            display_name = feature.replace('_', ' ').replace('lag', 'Lag ').title()
                            ui.label(f"{display_name}: {importance:.1%}").classes('bg-gray-800 px-3 py-1 rounded text-sm text-gray-300')
            else:
                ui.label("⚠️ Could not generate prediction range").classes('text-yellow-400')
        else:
            with ui.row().classes('w-full'):
                ui.label("⚠️ Insufficient historical data for reliable ML prediction").classes('text-yellow-400')
                ui.label("Requires 50+ trading days with valid technical indicators").classes('text-gray-400 text-sm ml-4')
        
        # === AI MARKET ANALYSIS SECTION ===
        ui.separator().classes('bg-gray-700 my-6')
        ui.label('🧠 AI Market Analysis').classes('text-xl font-bold text-white mb-4')
        
        analysis_insights = stock_analyzer.generate_market_analysis(data_with_indicators, ticker)
        
        for i, insight in enumerate(analysis_insights):
            # Color-code based on sentiment indicators
            if any(x in insight for x in ['🚀', '🟢', '✅', '📈', '🛒', '💡']):
                ui.label(insight).classes('text-green-400 mb-2')
            elif any(x in insight for x in ['🔴', '🔻', '📉', '🚨']):
                ui.label(insight).classes('text-red-400 mb-2')
            elif any(x in insight for x in ['⚠️', '🟡', '⌛']):
                ui.label(insight).classes('text-yellow-400 mb-2')
            else:
                ui.label(insight).classes('text-gray-300 mb-2')

        # === KEY TECHNICALS SECTION (Replaces Fundamentals) ===
        ui.separator().classes('bg-gray-700 my-6')
        ui.label('📊 Key Technicals').classes('text-xl font-bold text-white mb-4')
        
        # Get values from the last row of data
        e8, e21, e34 = float(last['EMA8']), float(last['EMA21']), float(last['EMA34'])
        e55, e89 = float(last['EMA55']), float(last['EMA89'])
        adx_val = float(last.get('ADX', 0))
        stoch_val = float(last.get('Stoch', 0))
        
        tech_cards = [
            {'label': 'EMA 8', 'value': f"${e8:.2f}", 'color': 'text-cyan-400'},
            {'label': 'EMA 21', 'value': f"${e21:.2f}", 'color': 'text-cyan-400'},
            {'label': 'EMA 34', 'value': f"${e34:.2f}", 'color': 'text-cyan-400'},
            {'label': 'EMA 55', 'value': f"${e55:.2f}", 'color': 'text-cyan-400'},
            {'label': 'EMA 89', 'value': f"${e89:.2f}", 'color': 'text-cyan-400'},
            {'label': 'ADX (14)', 'value': f"{adx_val:.1f}", 'color': 'text-yellow-400' if adx_val > 25 else 'text-gray-400'},
            {'label': 'Stoch (8,3,3)', 'value': f"{stoch_val:.1f}", 'color': 'text-purple-400'},
            {'label': 'ATR (14)', 'value': f"${atr:.2f}", 'color': 'text-gray-300'},
        ]
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            for card in tech_cards:
                with ui.column().classes('metric-card flex-1 min-w-[140px]'):
                    ui.label(card['label']).classes('metric-label')
                    ui.label(card['value']).classes(f"text-xl font-bold {card.get('color', 'text-white')}")
        
        # === OPTIONS FLOW SECTION ===
        ui.separator().classes('bg-gray-700 my-6')
        ui.label('📊 Options Flow').classes('text-xl font-bold text-white mb-4')
        
        flow = options_flow.get_options_flow(ticker)
        
        if flow.get('error'):
            ui.label(f"Could not load options flow: {flow['error']}").classes('text-yellow-400')
        else:
            # === TOP ROW: IV and Max Pain ===
            with ui.row().classes('w-full gap-4 mb-4'):
                with ui.column().classes('metric-card flex-1'):
                    ui.label('Implied Volatility (ATM)').classes('metric-label')
                    iv = flow.get('iv')
                    ui.label(f"{iv:.1f}%" if iv else '-').classes('text-2xl font-bold text-cyan-400')
                    exp = flow.get('nearest_expiration', '')
                    ui.label(f"Nearest Exp: {exp}").classes('text-xs text-gray-400')
                
                with ui.column().classes('metric-card flex-1'):
                    ui.label('Maximum Pain').classes('metric-label')
                    max_pain = flow.get('max_pain')
                    ui.label(f"${max_pain:.2f}" if max_pain else '-').classes('text-2xl font-bold text-purple-400')
                    mp_exp = flow.get('nearest_expiration', '')
                    ui.label(f"For: {mp_exp}").classes('text-xs text-gray-400')
                
                with ui.column().classes('metric-card flex-1'):
                    ui.label('Current Price').classes('metric-label')
                    flow_price = flow.get('current_price', 0)
                    ui.label(f"${flow_price:.2f}" if flow_price else '-').classes('text-2xl font-bold text-white')
            
            # Max Pain Analysis Row
            max_pain = flow.get('max_pain')
            flow_price = flow.get('current_price', 0)
            if max_pain and flow_price:
                mp_diff = flow_price - max_pain
                mp_diff_pct = (mp_diff / max_pain) * 100
                mp_distance = abs(mp_diff)
                mp_distance_pct = abs(mp_diff_pct)
                
                # Determine direction and color
                if mp_diff > 0:
                    mp_direction = "⬇️ BELOW"
                    mp_dir_color = 'text-red-400'
                    mp_action = f"Price likely to pull DOWN toward ${max_pain:.2f}"
                    mp_bg = 'bg-red-900/30 border border-red-800'
                else:
                    mp_direction = "⬆️ ABOVE"
                    mp_dir_color = 'text-green-400'
                    mp_action = f"Price likely to pull UP toward ${max_pain:.2f}"
                    mp_bg = 'bg-green-900/30 border border-green-800'
                
                # Determine strength of gravitational pull
                if mp_distance_pct < 2:
                    mp_strength = "🎯 AT MAX PAIN"
                    mp_strength_desc = "Price near max pain - expiration pressure is neutral"
                    mp_bg = 'bg-gray-800 border border-gray-600'
                elif mp_distance_pct < 5:
                    mp_strength = "💪 STRONG PULL"
                    mp_strength_desc = "Close to max pain - high probability of convergence"
                elif mp_distance_pct < 10:
                    mp_strength = "📊 MODERATE PULL"
                    mp_strength_desc = "Watch for movement toward max pain into expiration"
                else:
                    mp_strength = "⚠️ EXTENDED"
                    mp_strength_desc = "Far from max pain - may not converge this expiration"
                
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.column().classes(f'metric-card flex-1 {mp_bg}'):
                        ui.label('Max Pain Gravity').classes('metric-label')
                        ui.label(mp_strength).classes('text-lg font-bold text-white')
                        ui.label(mp_strength_desc).classes('text-xs text-gray-300')
                    
                    with ui.column().classes('metric-card flex-1'):
                        ui.label('Direction to Max Pain').classes('metric-label')
                        ui.label(f"{mp_direction} ${max_pain:.2f}").classes(f'text-lg font-bold {mp_dir_color}')
                        ui.label(f"Distance: ${mp_distance:.2f} ({mp_distance_pct:.1f}%)").classes('text-xs text-gray-400')
                    
                    with ui.column().classes('metric-card flex-1'):
                        ui.label('Expiration Outlook').classes('metric-label')
                        ui.label(mp_action).classes('text-sm text-white')
            
            # Sentiment Badge
            sentiment = flow['sentiment']
            sentiment_colors = {
                'STRONGLY BULLISH': 'bg-green-900 text-green-400',
                'BULLISH': 'bg-green-800 text-green-300',
                'BEARISH': 'bg-red-800 text-red-300',
                'STRONGLY BEARISH': 'bg-red-900 text-red-400'
            }
            
            with ui.row().classes('w-full gap-4 mb-4'):
                with ui.column().classes(f'metric-card flex-1 text-center {sentiment_colors.get(sentiment, "")}'):
                    ui.label('FLOW SENTIMENT').classes('metric-label')
                    ui.label(sentiment).classes('text-2xl font-bold')
                    ui.label(flow['sentiment_description']).classes('text-xs text-gray-300 mt-1')
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('metric-card flex-1'):
                    ui.label('Net Premium').classes('metric-label')
                    net_prem = flow['net_premium']
                    prem_color = 'text-green-400' if net_prem > 0 else 'text-red-400'
                    ui.label(format_premium(net_prem)).classes(f'text-xl font-bold {prem_color}')
                    ui.label('Call $ - Put $').classes('text-xs text-gray-400')
                
                with ui.column().classes('metric-card flex-1'):
                    ui.label('P/C Volume Ratio').classes('metric-label')
                    ui.label(f"{flow['pc_volume_ratio']:.2f}").classes('text-xl font-bold text-cyan-400')
                    ui.label(flow['volume_bias']).classes('text-xs text-gray-400')
                
                with ui.column().classes('metric-card flex-1'):
                    ui.label('P/C Premium Ratio').classes('metric-label')
                    ui.label(f"{flow['pc_premium_ratio']:.2f}").classes('text-xl font-bold text-cyan-400')
                    ui.label(flow['premium_bias']).classes('text-xs text-gray-400')
                
                with ui.column().classes('metric-card flex-1'):
                    ui.label('Unusual Activity').classes('metric-label')
                    unusual_total = flow['unusual_calls'] + flow['unusual_puts']
                    ui.label(f"{unusual_total}").classes('text-xl font-bold text-yellow-400' if unusual_total > 0 else 'text-xl font-bold text-gray-400')
                    ui.label(f"{flow['unusual_calls']} calls, {flow['unusual_puts']} puts").classes('text-xs text-gray-400')

        # === EXPORT / COPY SECTION ===
        ui.separator().classes('bg-gray-700 my-6')
        ui.label('📋 Export Technical Data').classes('text-xl font-bold text-white mb-4')
        
        # Build raw technical data export
        export_lines = []
        export_lines.append(f"# {ticker} Technical Data")
        export_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        export_lines.append("")
        
        # Price Data
        export_lines.append("## Price")
        export_lines.append(f"Close: {price:.2f}")
        export_lines.append("")
        
        # Moving Averages
        export_lines.append("## Moving Averages")
        export_lines.append(f"SMA 200: {sma200:.2f}")
        export_lines.append(f"EMA 8: {e8:.2f}")
        export_lines.append(f"EMA 21: {e21:.2f}")
        export_lines.append(f"EMA 34: {e34:.2f}")
        export_lines.append(f"EMA 55: {e55:.2f}")
        export_lines.append(f"EMA 89: {e89:.2f}")
        
        # Additional MAs from data_with_indicators
        if 'SMA_20' in data_with_indicators.columns:
            sma20 = float(data_with_indicators['SMA_20'].iloc[-1])
            export_lines.append(f"SMA 20: {sma20:.2f}")
        if 'SMA_50' in data_with_indicators.columns:
            sma50 = float(data_with_indicators['SMA_50'].iloc[-1])
            export_lines.append(f"SMA 50: {sma50:.2f}")
        export_lines.append("")
        
        # RSI & Momentum Indicators
        export_lines.append("## Momentum Indicators")
        if 'RSI' in data_with_indicators.columns:
            rsi = float(data_with_indicators['RSI'].iloc[-1])
            export_lines.append(f"RSI (14): {rsi:.1f}")
        export_lines.append(f"Stochastic K (8,3,3): {stoch:.1f}")
        if 'Stoch_D' in data_with_indicators.columns:
            stoch_d = float(data_with_indicators['Stoch_D'].iloc[-1])
            export_lines.append(f"Stochastic D: {stoch_d:.1f}")
        export_lines.append("")
        
        # MACD
        export_lines.append("## MACD")
        if 'MACD' in data_with_indicators.columns:
            macd = float(data_with_indicators['MACD'].iloc[-1])
            export_lines.append(f"MACD: {macd:.4f}")
        if 'MACD_signal' in data_with_indicators.columns:
            macd_signal = float(data_with_indicators['MACD_signal'].iloc[-1])
            export_lines.append(f"MACD Signal: {macd_signal:.4f}")
        if 'MACD_histogram' in data_with_indicators.columns:
            macd_hist = float(data_with_indicators['MACD_histogram'].iloc[-1])
            export_lines.append(f"MACD Histogram: {macd_hist:.4f}")
        export_lines.append("")
        
        # Bollinger Bands
        export_lines.append("## Bollinger Bands (20,2)")
        if 'BB_upper' in data_with_indicators.columns:
            bb_upper = float(data_with_indicators['BB_upper'].iloc[-1])
            bb_middle = float(data_with_indicators['BB_middle'].iloc[-1])
            bb_lower = float(data_with_indicators['BB_lower'].iloc[-1])
            export_lines.append(f"Upper Band: {bb_upper:.2f}")
            export_lines.append(f"Middle Band: {bb_middle:.2f}")
            export_lines.append(f"Lower Band: {bb_lower:.2f}")
            bb_width = (bb_upper - bb_lower) / bb_middle * 100
            export_lines.append(f"Band Width: {bb_width:.2f}%")
        export_lines.append("")
        
        # Volatility & ATR
        export_lines.append("## Volatility")
        export_lines.append(f"ATR (14): {atr:.2f}")
        export_lines.append(f"ATR (55): {atr55:.2f}")
        export_lines.append(f"ATR14/ATR55 Ratio: {squeeze_ratio:.2f}")
        export_lines.append(f"Squeeze Status: {'SQUEEZED' if is_squeezed else 'Normal'}")
        if 'High_Low_Pct' in data_with_indicators.columns:
            hl_pct = float(data_with_indicators['High_Low_Pct'].iloc[-1])
            export_lines.append(f"Daily Range %: {hl_pct:.2f}%")
        export_lines.append("")
        
        # Volume
        export_lines.append("## Volume")
        vol = float(data['Volume'].iloc[-1])
        vol_avg = float(data['Volume'].rolling(20).mean().iloc[-1])
        vol_ratio = vol / vol_avg if vol_avg > 0 else 1
        export_lines.append(f"Today Volume: {vol:,.0f}")
        export_lines.append(f"20-Day Avg Volume: {vol_avg:,.0f}")
        export_lines.append(f"Volume Ratio: {vol_ratio:.2f}")
        export_lines.append("")
        
        # Price Position
        export_lines.append("## Price Position")
        fifty_two_high = float(data['High'].rolling(252).max().iloc[-1])
        fifty_two_low = float(data['Low'].rolling(252).min().iloc[-1])
        pct_from_high = ((price - fifty_two_high) / fifty_two_high) * 100
        pct_from_low = ((price - fifty_two_low) / fifty_two_low) * 100
        export_lines.append(f"52-Week High: {fifty_two_high:.2f}")
        export_lines.append(f"52-Week Low: {fifty_two_low:.2f}")
        export_lines.append(f"% From 52W High: {pct_from_high:.1f}%")
        export_lines.append(f"% From 52W Low: {pct_from_low:.1f}%")
        export_lines.append(f"EMA Stack: {'Bullish' if is_stacked else 'Disordered'}")
        export_lines.append(f"Above SMA 200: {'Yes' if price > sma200 else 'No'}")
        export_lines.append("")
        
        # Calculated Levels
        export_lines.append("## Calculated Levels")
        export_lines.append(f"Stop Loss (1.5 ATR): {stop_loss:.2f}")
        export_lines.append(f"Target 1 (1.2 ATR): {tp1:.2f}")
        export_lines.append(f"Target 2 (2.5 ATR): {tp2:.2f}")
        export_lines.append("")
        
        # Comprehensive Fundamentals
        full_fundamentals = fundamental_metrics.get_fundamental_metrics(ticker)
        if not full_fundamentals.get('error'):
            export_lines.append("## Company Info")
            export_lines.append(f"Name: {full_fundamentals.get('company_name', ticker)}")
            export_lines.append(f"Sector: {full_fundamentals.get('sector', '-')}")
            export_lines.append(f"Industry: {full_fundamentals.get('industry', '-')}")
            export_lines.append("")
            
            export_lines.append("## Valuation")
            export_lines.append(f"Market Cap: {full_fundamentals.get('market_cap', '-')}")
            export_lines.append(f"P/E Ratio (TTM): {full_fundamentals.get('pe_ratio', '-')}")
            export_lines.append(f"Forward P/E: {full_fundamentals.get('forward_pe', '-')}")
            export_lines.append(f"P/S Ratio: {full_fundamentals.get('ps_ratio', '-')}")
            export_lines.append(f"P/B Ratio: {full_fundamentals.get('pb_ratio', '-')}")
            export_lines.append(f"EV/EBITDA: {full_fundamentals.get('ev_ebitda', '-')}")
            export_lines.append(f"PEG Ratio: {full_fundamentals.get('peg_ratio', '-')}")
            export_lines.append("")
            
            export_lines.append("## Profitability")
            export_lines.append(f"Gross Margin: {full_fundamentals.get('gross_margin', '-')}")
            export_lines.append(f"Operating Margin: {full_fundamentals.get('operating_margin', '-')}")
            export_lines.append(f"Profit Margin: {full_fundamentals.get('profit_margin', '-')}")
            export_lines.append(f"ROE: {full_fundamentals.get('roe', '-')}")
            export_lines.append(f"ROA: {full_fundamentals.get('roa', '-')}")
            export_lines.append("")
            
            export_lines.append("## Financial Health")
            export_lines.append(f"Current Ratio: {full_fundamentals.get('current_ratio', '-')}")
            export_lines.append(f"Debt/Equity: {full_fundamentals.get('debt_to_equity', '-')}")
            export_lines.append(f"Total Debt: {full_fundamentals.get('total_debt', '-')}")
            export_lines.append(f"Total Cash: {full_fundamentals.get('total_cash', '-')}")
            export_lines.append(f"Free Cash Flow: {full_fundamentals.get('free_cash_flow', '-')}")
            export_lines.append(f"Operating Cash Flow: {full_fundamentals.get('operating_cash_flow', '-')}")
            export_lines.append("")
            
            export_lines.append("## Growth")
            export_lines.append(f"Revenue Growth: {full_fundamentals.get('revenue_growth', '-')}")
            export_lines.append(f"Earnings Growth: {full_fundamentals.get('earnings_growth', '-')}")
            export_lines.append(f"Revenue Per Share: {full_fundamentals.get('revenue_per_share', '-')}")
            export_lines.append("")
            
            export_lines.append("## Analyst Consensus")
            export_lines.append(f"Target Price: ${full_fundamentals.get('target_price', 0):.2f}" if full_fundamentals.get('target_price') else "Target Price: -")
            export_lines.append(f"Recommendation: {full_fundamentals.get('recommendation', '-')}")
            export_lines.append(f"Number of Analysts: {full_fundamentals.get('num_analysts', 0)}")
            export_lines.append("")
        
        # Recent Performance
        export_lines.append("## Recent Performance")
        if len(data) >= 5:
            change_1d = ((price - float(data['Close'].iloc[-2])) / float(data['Close'].iloc[-2])) * 100
            change_5d = ((price - float(data['Close'].iloc[-5])) / float(data['Close'].iloc[-5])) * 100
            export_lines.append(f"1-Day Change: {change_1d:+.2f}%")
            export_lines.append(f"5-Day Change: {change_5d:+.2f}%")
        if len(data) >= 21:
            change_1mo = ((price - float(data['Close'].iloc[-21])) / float(data['Close'].iloc[-21])) * 100
            export_lines.append(f"1-Month Change: {change_1mo:+.2f}%")
        if len(data) >= 63:
            change_3mo = ((price - float(data['Close'].iloc[-63])) / float(data['Close'].iloc[-63])) * 100
            export_lines.append(f"3-Month Change: {change_3mo:+.2f}%")
        export_lines.append("")
        
        # Options Data (if available)
        if not flow.get('error'):
            export_lines.append("## Options Data")
            export_lines.append(f"IV (ATM): {flow.get('iv', 0):.1f}%")
            export_lines.append(f"Max Pain: {flow.get('max_pain', 0):.2f}")
            export_lines.append(f"Current vs Max Pain: {((flow.get('current_price', 0) - flow.get('max_pain', 0)) / flow.get('max_pain', 1) * 100):.1f}%")
            export_lines.append(f"P/C Volume Ratio: {flow['pc_volume_ratio']:.2f}")
            export_lines.append(f"P/C Premium Ratio: {flow['pc_premium_ratio']:.2f}")
            export_lines.append(f"Call Volume: {flow['total_call_volume']:,}")
            export_lines.append(f"Put Volume: {flow['total_put_volume']:,}")
            export_lines.append(f"Net Premium: ${flow['net_premium']:,.0f}")
            export_lines.append(f"Unusual Calls: {flow['unusual_calls']}")
            export_lines.append(f"Unusual Puts: {flow['unusual_puts']}")
            export_lines.append(f"Sentiment: {flow['sentiment']}")
            export_lines.append("")
        
        export_text = '\n'.join(export_lines)
        
        # Copy/paste text area
        ui.label('Copy this analysis to use with NotebookLM or other tools:').classes('text-gray-400 text-sm mb-2')
        ui.textarea(value=export_text).props('dark outlined readonly').classes('w-full').style('height: 250px; font-family: monospace;')
        
        # Download button
        def download_analysis():
            filename = f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            ui.download(export_text.encode('utf-8'), filename)
        
        ui.button('📥 Download as Markdown', on_click=download_analysis).props('outline color=cyan').classes('mt-2')

# --- LAYOUT ---

def render_scanner_view():
    render_market_header()
    
    strategy = strategies.get_strategy_by_display_name(state.selected_strategy)
    
    # Scanner Results Card
    with ui.card().classes('w-full bg-gray-900/50 border border-gray-800 p-6 backdrop-blur-md'):
        with ui.row().classes('w-full items-center justify-between mb-4'):
            with ui.column().classes('gap-0'):
                ui.label(f'🔍 {strategy.name}').classes('text-xl font-bold text-white')
                if not state.scanner_results.empty:
                    ui.label(f"Showing {len(state.scanner_results)} matches").classes('text-xs text-green-400')
            
            # Toolbar for Actions (if results exist)
            if not state.scanner_results.empty:
                with ui.row().classes('items-center gap-2'):
                    # Search filter placeholder
                    ui.input(placeholder='Filter ticker...').props('dark dense outlined rounded item-aligned input-class="text-xs"').classes('w-40')
                    
                    ui.separator().props('vertical').classes('mx-2 h-6 bg-gray-700')
                    
                    # Download Menu
                    with ui.button(icon='download', color='blue').props('outline round size=sm').tooltip('Download'):
                        with ui.menu().props('dark auto-close'):
                            def download_csv():
                                csv_data = state.scanner_results[['name', 'description', 'close', 'change', 'market_cap_basic', 'ADX', 'Stoch_K']].to_csv(index=False)
                                filename = f"screen_{state.selected_strategy.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                                ui.download(csv_data.encode('utf-8'), filename)
                            ui.menu_item('CSV File', on_click=download_csv)
                            
                            def download_txt():
                                txt_data = scanner_logic.convert_df_to_txt(state.scanner_results)
                                filename = f"screen_{state.selected_strategy.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                                ui.download(txt_data, filename)
                            ui.menu_item('TXT File', on_click=download_txt)

                            def download_tv():
                                tv_text = ",".join(state.scanner_results['name'].unique())
                                filename = f"tv_watchlist_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                                ui.download(tv_text.encode('utf-8'), filename)
                            ui.menu_item('TradingView Watchlist', on_click=download_tv)

                    # Discord Menu
                    webhooks = get_configured_webhooks()
                    if webhooks:
                        async def on_send_discord():
                            selected = state.selected_webhooks
                            if not selected:
                                ui.notify('⚠️ No webhooks selected in sidebar', type='warning')
                                return
                            
                            strategy = strategies.get_strategy_by_display_name(state.selected_strategy)
                            results = state.scanner_results
                            
                            header_embed = {
                                "title": f"📊 {strategy.name} Results",
                                "description": f"Found **{len(results)}** matches",
                                "color": 0x00d4aa,
                                "fields": [
                                    {"name": "⚙️ Strategy", "value": strategy.name, "inline": True},
                                    {"name": "🕐 Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M'), "inline": True}
                                ],
                                "footer": {"text": "Momentum Phinance Scanner"},
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            # Build clean results table with SL/TP1
                            all_rows = []
                            for _, row in results.iterrows():
                                sym = str(row['name'])[:6]
                                close_val = float(row['close'])
                                atr14 = float(row.get('ATR', 0))
                                atr55 = float(row.get('ATR_1W', atr14))
                                
                                squeeze_ratio = atr14 / (atr55 / 2.0) if atr55 > 0 else 1.0
                                is_squeezed = squeeze_ratio < 0.85
                                atr_for_levels = atr55 if is_squeezed else atr14
                                
                                sl = close_val - (atr_for_levels * 1.5) if atr_for_levels > 0 else close_val * 0.95
                                tp1 = close_val + (atr_for_levels * 1.2) if atr_for_levels > 0 else close_val * 1.05
                                
                                price_str = f"${close_val:.0f}" if close_val >= 100 else f"${close_val:.2f}"
                                sl_str = f"${sl:.0f}" if sl >= 100 else f"${sl:.2f}"
                                tp1_str = f"${tp1:.0f}" if tp1 >= 100 else f"${tp1:.2f}"
                                
                                squeeze_flag = "🔋" if is_squeezed else ""
                                all_rows.append(f"{sym:<5}{squeeze_flag:1} {price_str:>7} {sl_str:>7} {tp1_str:>7}")
                            
                            # Add table to embed (chunked for Discord limits)
                            header_line = f"{'SYM':<6} {'PRICE':>7} {'SL':>7} {'TP1':>7}"
                            separator = "-" * 30
                            
                            chunk_size = 20
                            for i in range(0, len(all_rows), chunk_size):
                                chunk = all_rows[i:i+chunk_size]
                                table_text = "```\n" + header_line + "\n" + separator + "\n" + "\n".join(chunk) + "\n```"
                                field_name = f"📈 Results ({i+1}-{min(i+chunk_size, len(all_rows))})"
                                header_embed["fields"].append({"name": field_name, "value": table_text, "inline": False})
                            
                            # Build COMPREHENSIVE CSV with ALL technicals for NotebookLM (raw data only)
                            # Build COMPREHENSIVE CSV with ALL technicals for NotebookLM (raw data only)
                            csv_header = "Symbol,Company,Sector,Price,Change%,MktCap,RelVol,IV,EMA8,EMA21,EMA34,EMA55,EMA89,SMA50,SMA200,ADX,Stoch_K,Stoch_D,RSI,ATR14,ATR55,SqueezeRatio,Squeezed"
                            csv_lines = [csv_header]
                            for _, row in results.iterrows():
                                close_val = float(row['close'])
                                atr14 = float(row.get('ATR', 0))
                                atr55 = float(row.get('ATR_1W', atr14))
                                squeeze_ratio = atr14 / (atr55 / 2.0) if atr55 > 0 else 1.0
                                is_squeezed = squeeze_ratio < 0.85
                                
                                line_items = [
                                    str(row['name']),
                                    str(row.get('description', ''))[:30].replace(',', ' '),
                                    str(row.get('sector', '')).replace(',', ' '),
                                    f"{close_val:.2f}",
                                    f"{row['change']:.2f}",
                                    f"{row.get('market_cap_basic', 0):.0f}",
                                    f"{row.get('relative_volume_10d_calc', 0):.2f}",
                                    str(row.get('IV', '')),
                                    f"{row.get('EMA8', 0):.2f}",
                                    f"{row.get('EMA21', 0):.2f}",
                                    f"{row.get('EMA34', 0):.2f}",
                                    f"{row.get('EMA55', 0):.2f}",
                                    f"{row.get('EMA89', 0):.2f}",
                                    f"{row.get('SMA50', 0):.2f}",
                                    f"{row.get('SMA200', 0):.2f}",
                                    f"{row.get('ADX', 0):.1f}",
                                    f"{row.get('Stoch_K', 0):.1f}",
                                    f"{row.get('Stoch_D', 0):.1f}",
                                    f"{row.get('RSI', 0):.1f}",
                                    f"{atr14:.2f}",
                                    f"{atr55:.2f}",
                                    f"{squeeze_ratio:.2f}",
                                    "Yes" if is_squeezed else "No"
                                ]
                                csv_lines.append(",".join(line_items))
                            
                            csv_content = "\n".join(csv_lines)
                            
                            # Add note about CSV
                            header_embed["fields"].append({
                                "name": "📎 Attached",
                                "value": "Full CSV with all technicals for NotebookLM",
                                "inline": False
                            })
                            
                            # Send with file attachment
                            success = 0
                            for name in selected:
                                url = webhooks.get(name)
                                if url:
                                    try:
                                        files = {
                                            'file': (f'momentum_scan_{datetime.now().strftime("%Y%m%d_%H%M")}.csv', csv_content.encode('utf-8'), 'text/csv')
                                        }
                                        data = {
                                            'payload_json': json.dumps({"embeds": [header_embed]})
                                        }
                                        resp = requests.post(url, files=files, data=data)
                                        if resp.status_code in (200, 204):
                                            success += 1
                                    except Exception as e:
                                        print(f"Discord error: {e}")
                            
                            if success > 0:
                                ui.notify(f'✅ Sent to {success} webhook(s) with CSV!', type='positive')
                            else:
                                ui.notify('❌ Failed to send', type='negative')
                        
                        ui.button(icon='send', color='purple', on_click=on_send_discord).props('outline round size=sm').tooltip('Send to Discord with CSV')

                    # Google Sheets Button
                    sheets_url = get_google_sheets_webhook()
                    if sheets_url:
                        async def send_sheets():
                            try:
                                # Prepare comprehensive data for Sheets (matching CSV structure)
                                sheets_data = []
                                for _, row in state.scanner_results.iterrows():
                                    close_val = float(row['close'])
                                    atr14 = float(row.get('ATR', 0))
                                    atr55 = float(row.get('ATR_1W', atr14))
                                    squeeze_ratio = atr14 / (atr55 / 2.0) if atr55 > 0 else 1.0
                                    is_squeezed = squeeze_ratio < 0.85
                                    
                                    # Calculate week ending (Sunday) for filtering
                                    from datetime import timedelta
                                    today = datetime.now()
                                    days_until_sunday = (6 - today.weekday()) % 7
                                    if days_until_sunday == 0:  # If today is Sunday, use today
                                        week_ending = today
                                    else:
                                        week_ending = today + timedelta(days=days_until_sunday)
                                    week_ending_str = week_ending.strftime('%Y-%m-%d')
                                    
                                    sheets_data.append({
                                        'Symbol': row['name'],
                                        'Company': str(row.get('description', ''))[:50],
                                        'Sector': str(row.get('sector', '')),
                                        'WeekEnding': week_ending_str,
                                        'PriceWhenScanned': close_val,
                                        'Change%': float(row['change']),
                                        'MktCap': float(row.get('market_cap_basic', 0)),
                                        'RelVol': float(row.get('relative_volume_10d_calc', 0)),
                                        
                                        # Trend Exhaustion Specific
                                        'Signal': row.get('Signal', ''),
                                        'SignalDate': row.get('SignalDate', ''),
                                        'WR21': float(row.get('WR21', 0)),
                                        'WR112': float(row.get('WR112', 0)),
                                        'HMA55': float(row.get('HMA55', 0)),
                                        'PriceVsHMA': row.get('PriceVsHMA', ''),

                                        # Momentum
                                        'ADX': float(row.get('ADX', 0)),
                                        'Stoch_K': float(row.get('Stoch_K', 0)),
                                        'Stoch_D': float(row.get('Stoch_D', 0)),
                                        'RSI': float(row.get('RSI', 0)),
                                        
                                        # Volatility
                                        'ATR14': atr14,
                                        'ATR55': atr55,
                                        'SqueezeRatio': float(f"{squeeze_ratio:.2f}"),
                                        'Squeezed': "Yes" if is_squeezed else "No",

                                        # Moving Averages (Daily)
                                        'EMA8': float(row.get('EMA8', 0)),
                                        'EMA21': float(row.get('EMA21', 0)),
                                        'EMA34': float(row.get('EMA34', 0)),
                                        'EMA55': float(row.get('EMA55', 0)),
                                        'EMA89': float(row.get('EMA89', 0)),
                                        'SMA50': float(row.get('SMA50', 0)),
                                        'SMA200': float(row.get('SMA200', 0)),

                                        # Moving Averages (Weekly)
                                        'EMA8_W': float(row.get('EMA8|1W', 0)),
                                        'EMA21_W': float(row.get('EMA21|1W', 0)),
                                        'EMA34_W': float(row.get('EMA34|1W', 0)),
                                        'EMA55_W': float(row.get('EMA55|1W', 0)),
                                        'EMA89_W': float(row.get('EMA89|1W', 0)),
                                        
                                        # Moving Averages (Monthly)
                                        'EMA8_M': float(row.get('EMA8|1M', 0)),
                                        'EMA21_M': float(row.get('EMA21|1M', 0)),
                                        'EMA34_M': float(row.get('EMA34|1M', 0)),
                                        'EMA55_M': float(row.get('EMA55|1M', 0)),
                                        'EMA89_M': float(row.get('EMA8|1M', 0)),

                                        # Strategy Specific
                                        'IV': row.get('IV', ''),
                                    })
                                
                                # Send strategy name to route to correct tab
                                payload = {
                                    "data": sheets_data, 
                                    "timestamp": datetime.now().isoformat(),
                                    "strategy": state.selected_strategy
                                }
                                print(f"Sending to Sheets URL: {sheets_url}")
                                
                                resp = requests.post(sheets_url, json=payload)
                                print(f"Sheets Response: {resp.status_code} - {resp.text}")
                                
                                if resp.status_code == 200:
                                    ui.notify(f'✅ Sent to Sheets ({state.selected_strategy})', type='positive')
                                elif resp.status_code == 302:
                                    ui.notify('⚠️ Sheets Redirect (Check Permissions)', type='warning')
                                else:
                                    ui.notify(f'❌ Sheets Error {resp.status_code}', type='negative')
                                    
                            except Exception as e:
                                print(f"Sheets Exception: {e}")
                                ui.notify(f'❌ Sheets Exception: {str(e)}', type='negative')
                        ui.button(icon='table_view', color='green', on_click=send_sheets).props('outline round size=sm').tooltip('Send to Sheets')
        
        # Table Logic (Compact)
        if not state.scanner_results.empty:
            columns = [
                {'name': 'name', 'label': 'Ticker', 'field': 'name', 'sortable': True, 'align': 'left'},
                {'name': 'description', 'label': 'Company', 'field': 'description', 'sortable': True, 'align': 'left'},
                {'name': 'close', 'label': 'Price', 'field': 'close', 'sortable': True, 'align': 'right'},
                {'name': 'change', 'label': 'Chg %', 'field': 'change', 'sortable': True, 'align': 'right'},
                {'name': 'market_cap', 'label': 'Mkt Cap', 'field': 'market_cap', 'sortable': True, 'align': 'right'},
            ]
            
            # Add strategy-specific columns
            # Add strategy-specific columns
            if state.selected_strategy == 'Momentum with Pullback':
                columns.extend([
                    {'name': 'ADX', 'label': 'ADX', 'field': 'ADX', 'sortable': True, 'align': 'right'},
                    {'name': 'Stoch_K', 'label': 'Stoch K', 'field': 'Stoch_K', 'sortable': True, 'align': 'right'},
                    {'name': 'SqueezeRatio', 'label': 'Squeeze', 'field': 'SqueezeRatio', 'sortable': True, 'align': 'right'},
                ])
            elif state.selected_strategy == 'Volatility Squeeze':
                columns.extend([
                    {'name': 'SqueezeRatio', 'label': 'Squeeze', 'field': 'SqueezeRatio', 'sortable': True, 'align': 'right'},
                    {'name': 'ADX', 'label': 'ADX', 'field': 'ADX', 'sortable': True, 'align': 'right'},
                    {'name': 'RSI', 'label': 'RSI', 'field': 'RSI', 'sortable': True, 'align': 'right'},
                    {'name': 'RelVol', 'label': 'RelVol', 'field': 'RelVol', 'sortable': True, 'align': 'right'},
                    {'name': 'Signals', 'label': 'Signals', 'field': 'Signals', 'sortable': True, 'align': 'left'},
                ])
            elif state.selected_strategy == 'Trend Exhaustion Reversals':
                columns.extend([
                    {'name': 'Signal', 'label': 'Signal', 'field': 'Signal', 'sortable': True, 'align': 'left'},
                    {'name': 'SignalDate', 'label': 'Date', 'field': 'SignalDate', 'sortable': True, 'align': 'center'},
                    {'name': 'WR21', 'label': '%R (21)', 'field': 'WR21', 'sortable': True, 'align': 'right'},
                    {'name': 'WR112', 'label': '%R (112)', 'field': 'WR112', 'sortable': True, 'align': 'right'},
                    {'name': 'PriceVsHMA', 'label': 'vs HMA(55)', 'field': 'PriceVsHMA', 'sortable': True, 'align': 'center'},
                ])
            elif state.selected_strategy == 'MEME Screen':
                columns.extend([
                    {'name': 'IV', 'label': 'Implied Volatility', 'field': 'IV', 'sortable': True, 'align': 'right'},
                    {'name': 'volume', 'label': 'Volume', 'field': 'volume', 'sortable': True, 'align': 'right'},
                    {'name': 'sector', 'label': 'Sector', 'field': 'sector', 'sortable': True, 'align': 'left'},
                ])
            else:  # Small Cap Multibaggers
                columns.extend([
                    {'name': 'gross_margin', 'label': 'Gross Margin', 'field': 'gross_margin', 'sortable': True, 'align': 'right'},
                    {'name': 'revenue_growth', 'label': 'Rev Growth 3Y', 'field': 'revenue_growth', 'sortable': True, 'align': 'right'},
                ])
            
            def custom_on_row_click(e):
                 # Go to Audit view
                 state.target_ticker = e.args[1]['name']
                 state.mode = 'Single Ticker Audit'
                 update_ui()

            # Format data for display
            formatted_rows = []
            for _, row in state.scanner_results.iterrows():
                formatted_row = {
                    'name': row['name'],
                    'description': str(row.get('description', ''))[:35],
                    'close': f"${row['close']:.2f}",
                    'change': f"{row['change']:+.1f}%",
                    'market_cap': format_market_cap(row.get('market_cap_basic', 0)),
                }
                
                if state.selected_strategy == 'Momentum with Pullback':
                    formatted_row['ADX'] = f"{row.get('ADX', 0):.1f}"
                    formatted_row['Stoch_K'] = f"{row.get('Stoch_K', 0):.1f}"
                    squeeze = row.get('SqueezeRatio', 1.0)
                    # Add visual indicator: 🔋 for squeezed (<0.85), plain for normal
                    if squeeze < 0.85:
                        formatted_row['SqueezeRatio'] = f"🔋 {squeeze:.2f}"
                    else:
                        formatted_row['SqueezeRatio'] = f"{squeeze:.2f}"
                elif state.selected_strategy == 'Volatility Squeeze':
                    squeeze = row.get('SqueezeRatio', 1.0)
                    # Visual indicator for squeeze intensity
                    if squeeze < 0.7:
                        formatted_row['SqueezeRatio'] = f"🔋 {squeeze:.2f}"
                    elif squeeze < 0.85:
                        formatted_row['SqueezeRatio'] = f"⚡ {squeeze:.2f}"
                    else:
                        formatted_row['SqueezeRatio'] = f"{squeeze:.2f}"
                    formatted_row['ADX'] = f"{row.get('ADX', 0):.1f}"
                    formatted_row['RSI'] = f"{row.get('RSI', 0):.1f}"
                    rel_vol = row.get('relative_volume_10d_calc', 0)
                    formatted_row['RelVol'] = f"{rel_vol:.1f}x" if rel_vol else "—"
                    formatted_row['Signals'] = row.get('Signals', '—')
                elif state.selected_strategy == 'Trend Exhaustion Reversals':
                    formatted_row['Signal'] = row.get('Signal', '-')
                    formatted_row['SignalDate'] = row.get('SignalDate', '-')
                    formatted_row['WR21'] = f"{row.get('WR21', 0):.1f}"
                    formatted_row['WR112'] = f"{row.get('WR112', 0):.1f}"
                    formatted_row['PriceVsHMA'] = row.get('PriceVsHMA', '-')
                elif state.selected_strategy == 'MEME Screen':
                    formatted_row['IV'] = str(row.get('IV', '-'))
                    formatted_row['volume'] = f"{row.get('volume', 0):,.0f}"
                    formatted_row['sector'] = str(row.get('sector', '-'))
                else:
                    formatted_row['gross_margin'] = f"{row.get('gross_margin', 0):.1f}%"
                    formatted_row['revenue_growth'] = f"{row.get('revenue_growth_3y', 0):.1f}%"
                
                formatted_rows.append(formatted_row)

            table = ui.table(
                columns=columns, 
                rows=formatted_rows,
                pagination={'rowsPerPage': 15}
            ).classes('w-full scanner-table text-gray-300').props('flat dense square')
            
            table.on('rowClick', custom_on_row_click)
            
            # Add custom CSS for row hover pointer
            ui.add_head_html('<style>.scanner-table .q-table tbody tr:hover { cursor: pointer; background: rgba(255,255,255,0.05) !important; }</style>')
            
            # CSV Copy Section
            with ui.expansion('📋 Copy CSV Data', icon='content_copy').props('dense header-class="text-cyan-400"').classes('mt-4'):
                # Generate comprehensive CSV (Raw Data)
                csv_header = "Symbol,Company,Sector,Price,Change%,MktCap,RelVol,IV,EMA8,EMA21,EMA34,EMA55,EMA89,SMA50,SMA200,ADX,Stoch_K,Stoch_D,RSI,ATR14,ATR55,SqueezeRatio,Squeezed"
                csv_lines = [csv_header]
                for _, row in state.scanner_results.iterrows():
                    close_val = float(row['close'])
                    atr14 = float(row.get('ATR', 0))
                    atr55 = float(row.get('ATR_1W', atr14))
                    squeeze_ratio = atr14 / (atr55 / 2.0) if atr55 > 0 else 1.0
                    is_squeezed = squeeze_ratio < 0.85
                    
                    line_items = [
                        str(row['name']),
                        str(row.get('description', ''))[:30].replace(',', ' '),
                        str(row.get('sector', '')).replace(',', ' '),
                        f"{close_val:.2f}",
                        f"{row['change']:.2f}",
                        f"{row.get('market_cap_basic', 0):.0f}",
                        f"{row.get('relative_volume_10d_calc', 0):.2f}",
                        str(row.get('IV', '')),
                        f"{row.get('EMA8', 0):.2f}",
                        f"{row.get('EMA21', 0):.2f}",
                        f"{row.get('EMA34', 0):.2f}",
                        f"{row.get('EMA55', 0):.2f}",
                        f"{row.get('EMA89', 0):.2f}",
                        f"{row.get('SMA50', 0):.2f}",
                        f"{row.get('SMA200', 0):.2f}",
                        f"{row.get('ADX', 0):.1f}",
                        f"{row.get('Stoch_K', 0):.1f}",
                        f"{row.get('Stoch_D', 0):.1f}",
                        f"{row.get('RSI', 0):.1f}",
                        f"{atr14:.2f}",
                        f"{atr55:.2f}",
                        f"{squeeze_ratio:.2f}",
                        "Yes" if is_squeezed else "No"
                    ]
                    csv_lines.append(",".join(line_items))
                
                csv_text = "\n".join(csv_lines)
                ui.textarea(value=csv_text).props('dark outlined readonly').classes('w-full font-mono text-xs').style('height: 200px;')

        else:
            with ui.column().classes('w-full items-center justify-center py-12'):
                ui.icon('search_off', size='4rem', color='gray').classes('opacity-50')
                ui.label('No results found. Adjust filters and run screen.').classes('text-gray-500 mt-4')


# --- UPDATED LAYOUT & SIDEBAR ---

with ui.left_drawer(value=True).classes('bg-gray-900/90 backdrop-blur-md q-pa-md border-r border-gray-800'):
    ui.label("⚡ Momentum Phinance").classes('text-xl font-bold text-white tracking-wider mb-1')
    ui.label("INTEGRATED TERMINAL").classes('text-[10px] text-cyan-400 font-bold tracking-[0.2em] mb-4')
    
    ui.separator().classes('bg-gray-800 my-4')

    # QUICK SEARCH NAV
    def search_ticker(e):
        if e.value:
            state.target_ticker = e.value.upper()
            state.mode = 'Single Ticker Audit'
            update_ui()
    
    ui.input(placeholder='Search Ticker...', on_change=search_ticker).props('dark dense outlined rounded prepend-icon=search').classes('w-full mb-4')

    # Navigation (Simple)
    if state.mode == 'Single Ticker Audit':
         def go_home():
             state.mode = 'Market Screens'
             update_ui()
         ui.button('← Back to Scanner', on_click=go_home).props('flat dense color=cyan no-caps').classes('w-full mb-4')

    ui.separator().classes('bg-gray-800 mb-4')
    
    # Strategy Controls (Only show in Scanner mode)
    with ui.column().bind_visibility_from(state, 'mode', lambda m: m == 'Market Screens'):
        ui.label("STRATEGY CONTROLS").classes('text-[10px] font-bold text-gray-500 tracking-wider mb-2')
        
        # Strategy Select
        ui.select(
            strategies.get_strategy_names(),
            value=state.selected_strategy,
            on_change=lambda e: setattr(state, 'selected_strategy', e.value)
        ).props('dark outlined dense options-dense').classes('w-full mb-4')
        
        # Dynamic Params
        with ui.column().classes('gap-3'):
             
             # Momentum with Pullback Strategy Params
            with ui.column().bind_visibility_from(state, 'selected_strategy', lambda s: s == 'Momentum with Pullback'):
                ui.label("ADX Range").classes('text-white text-xs font-bold mb-1')
                with ui.row().classes('w-full gap-2'):
                    min_adx = ui.number('Min', value=20.0).props('dark dense outlined step=1.0').classes('flex-1')
                    max_adx = ui.number('Max', value=100.0).props('dark dense outlined step=1.0').classes('flex-1')

                ui.label("Market Cap ($B)").classes('text-white text-xs font-bold mt-2 mb-1')
                mega_cap = ui.switch('Include Mega Caps ($2T+)', value=True).props('dark dense size=sm')
                
                with ui.row().classes('w-full gap-2'):
                    min_mcap_b = ui.number('Min', value=0.0).props('dark dense outlined step=0.1').classes('flex-1')
                    max_mcap_b = ui.number('Max', value=5000.0).props('dark dense outlined step=0.1').classes('flex-1')
                    
                    def update_mega_cap(e):
                        if e.value:
                            max_mcap_b.value = 5000.0
                        else:
                            max_mcap_b.value = 2.0
                    mega_cap.on_value_change(update_mega_cap)

                ui.label("Stochastic (8,3,3)").classes('text-white text-xs font-bold mt-2 mb-1')
                with ui.row().classes('w-full gap-2'):
                    min_stoch = ui.number('Min', value=0.0).props('dark dense outlined step=1.0').classes('flex-1')
                    max_stoch = ui.number('Max', value=40.0).props('dark dense outlined step=1.0').classes('flex-1')
                
                # Toggle Filters
                ui.separator().classes('bg-gray-700 my-3')
                ui.label("Filter Toggles").classes('text-cyan-400 text-xs font-bold mb-2')
                

                
                require_within_1_atr = ui.switch('Require Within 1 ATR', value=True).props('dark dense size=sm')
                ui.label('Only show stocks within 1 ATR of EMA21. Turn OFF to include extended stocks.').classes('text-gray-500 text-xs')
            
            # Volatility Squeeze Params
            with ui.column().bind_visibility_from(state, 'selected_strategy', lambda s: s == 'Volatility Squeeze'):
                ui.label("Coil Strength (Max ADX)").classes('text-white text-xs font-bold mb-1')
                max_adx_sq = ui.number('Max ADX', value=30.0).props('dark dense outlined step=1.0').classes('w-full')
                
                ui.label("Market Cap ($B)").classes('text-white text-xs font-bold mt-2 mb-1')
                mega_cap_sq = ui.switch('Include Mega Caps', value=True).props('dark dense size=sm')
                
                with ui.row().classes('w-full gap-2'):
                    min_mcap_sq = ui.number('Min', value=0.0).props('dark dense outlined step=0.1').classes('flex-1')
                    max_mcap_sq = ui.number('Max', value=1000.0).props('dark dense outlined step=0.1').classes('flex-1')
                    
                    def update_mega_cap_sq(e):
                        if e.value:
                            max_mcap_sq.value = 5000.0
                        else:
                            max_mcap_sq.value = 1000.0
                    mega_cap_sq.on_value_change(update_mega_cap_sq)
            
            # Small Cap Multibaggers Params
            with ui.column().bind_visibility_from(state, 'selected_strategy', lambda s: s == 'Small Cap Multibaggers'):
                ui.label("Market Cap ($M)").classes('text-white text-xs font-bold mb-1')
                with ui.row().classes('w-full gap-2'):
                    min_mcap_m = ui.number('Min', value=10.0).props('dark dense outlined step=1.0').classes('flex-1')
                    max_mcap_m = ui.number('Max', value=1000.0).props('dark dense outlined step=10.0').classes('flex-1')

                ui.label("Gross Margin (%)").classes('text-white text-xs font-bold mt-2 mb-1')
                with ui.row().classes('w-full gap-2'):
                    min_gm = ui.number('Min', value=30.0).props('dark dense outlined step=5.0').classes('flex-1')
                    max_gm = ui.number('Max', value=100.0).props('dark dense outlined step=5.0').classes('flex-1')

                ui.label("Revenue Growth 3Y (%)").classes('text-white text-xs font-bold mt-2 mb-1')
                min_rev_growth = ui.number('Min', value=15.0).props('dark dense outlined step=1.0').classes('w-full')

            # Trend Exhaustion Params
            with ui.column().bind_visibility_from(state, 'selected_strategy', lambda s: s == 'Trend Exhaustion Reversals'):
                ui.label("Min Relative Volume").classes('text-white text-xs font-bold mb-1')
                te_min_vol = ui.number('Min', value=0.5).props('dark dense outlined step=0.1').classes('w-full')
                
                ui.label("Signal Mode").classes('text-white text-xs font-bold mb-1')
                with ui.row().classes('w-full gap-2'):
                    te_mode = ui.select(['Potential Setups', 'Trend Start', 'Reversal'], value='Potential Setups', label='Mode').props('dark dense outlined options-dense').classes('flex-1')
                    te_type = ui.select(['All', 'Long', 'Short'], value='All', label='Type').props('dark dense outlined options-dense').classes('flex-1')

                ui.label("Exhaustion Threshold").classes('text-white text-xs font-bold mt-2 mb-1')
                te_threshold = ui.number('Value', value=20).props('dark dense outlined step=1 min=1 max=50').classes('w-full')
                
                ui.label("Timeframe & MA Source").classes('text-white text-xs font-bold mt-2 mb-1')
                with ui.row().classes('w-full gap-2'):
                    te_timeframe = ui.select(['1d', '1wk', '1mo'], value='1d', label='TF').props('dark dense outlined options-dense').classes('flex-1')
                    te_source = ui.select(['close', 'hlc3'], value='hlc3', label='Src').props('dark dense outlined options-dense').classes('flex-1')

                ui.label("Confirmation").classes('text-white text-xs font-bold mt-2 mb-1')
                te_hull = ui.switch('Require Hull MA Trend', value=True).props('dark dense size=sm')

        
        # Run Button Logic (Re-implementing simplified logic)
        async def run_scanner():
            strategy = strategies.get_strategy_by_display_name(state.selected_strategy)
            ui.notify(f'Running {strategy.name} screen...', type='info')
            
            # Build params based on selected strategy
            if state.selected_strategy == 'Momentum with Pullback':
                params = {
                    'adx_min': min_adx.value,
                    'adx_max': max_adx.value,
                    'mcap_min_b': min_mcap_b.value,
                    'mcap_max_b': max_mcap_b.value,
                    'stoch_min': min_stoch.value,
                    'stoch_max': max_stoch.value,
                    'include_mega_caps': mega_cap.value,


                    'require_within_1_atr': require_within_1_atr.value
                }
            elif state.selected_strategy == 'Volatility Squeeze':
                params = {
                    'adx_max': max_adx_sq.value,
                    'mcap_min_b': min_mcap_sq.value,
                    'mcap_max_b': max_mcap_sq.value,
                    'include_mega_caps': mega_cap_sq.value
                }
            elif state.selected_strategy == 'Trend Exhaustion Reversals':
                params = {
                    'min_rel_vol': te_min_vol.value,
                    'threshold': te_threshold.value,
                    'require_hull_trend': te_hull.value,
                    'timeframe': te_timeframe.value,
                    'hull_source': te_source.value,
                    'signal_mode': te_mode.value,
                    'signal_type': te_type.value
                }
            else:
                params = {
                    'mcap_min_m': min_mcap_m.value,
                    'mcap_max_m': max_mcap_m.value,
                    'gross_margin_min': min_gm.value,
                    'gross_margin_max': max_gm.value,
                    'revenue_growth_min': min_rev_growth.value
                }
            
            try:
                query = strategy.build_query(params)
                count, df = await asyncio.to_thread(query.get_scanner_data)
                
                if count > 0:
                    df = strategy.post_process(df, params)
                    state.scanner_results = df
                    ui.notify(f'Found {len(df)} matches.', type='positive')
                else:
                    state.scanner_results = pd.DataFrame()
                    ui.notify('No matches found meeting criteria.', type='warning')
            except Exception as e:
                ui.notify(f"Error running scanner: {e}", type='negative')
                print(f"Scanner Error: {e}")
            
            # Force UI update by refreshing
            update_ui()
            
        ui.button('🚀 Run Screen', on_click=run_scanner).props('color=green').classes('mt-4 w-full shadow-lg shadow-green-500/20') 

    # --- WEBHOOK CONFIGURATION ---
    ui.separator().classes('bg-gray-700 my-4')
    with ui.expansion('📤 Export Settings', icon='send').props('dark dense header-class="text-cyan-400"'):
        webhooks = get_configured_webhooks()
        if webhooks:
            ui.label('Discord Webhooks').classes('text-gray-400 text-xs mb-2')
            webhook_names = list(webhooks.keys())
            if not getattr(state, 'selected_webhooks', None):
                state.selected_webhooks = webhook_names.copy()
            
            with ui.column().classes('gap-1'):
                for name in webhook_names:
                    def make_toggle(webhook_name):
                        def toggle(e):
                            if e.value:
                                if webhook_name not in state.selected_webhooks:
                                    state.selected_webhooks.append(webhook_name)
                            else:
                                if webhook_name in state.selected_webhooks:
                                    state.selected_webhooks.remove(webhook_name)
                        return toggle
                    
                    is_selected = name in state.selected_webhooks
                    with ui.row().classes('items-center'):
                        cb = ui.checkbox(name, value=is_selected).props('dark dense color=purple')
                        cb.on_value_change(make_toggle(name))
                        ui.label('🟣').classes('text-xs')
        else:
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='yellow').classes('text-sm')
                ui.label('No webhooks configured').classes('text-gray-400 text-xs')
            ui.label('Add WEBHOOK_NAME=URL to .env').classes('text-gray-500 text-xs ml-6')
        
        ui.separator().classes('bg-gray-700 my-2')
        
        sheets_url = get_google_sheets_webhook()
        if sheets_url:
            with ui.row().classes('items-center gap-2'):
                ui.icon('check_circle', color='green').classes('text-sm')
                ui.label('Google Sheets connected').classes('text-green-400 text-xs')
        else:
            with ui.row().classes('items-center gap-2'):
                ui.icon('info', color='gray').classes('text-sm')
                ui.label('Add GOOGLE_SHEETS_WEBHOOK to .env').classes('text-gray-500 text-xs')

# Main container update
with ui.column().classes('w-full q-pa-md max-w-7xl mx-auto') as content_container:
    update_ui()


ui.run(title='Tao Integrated Terminal', dark=True, reload=True, port=8080)
