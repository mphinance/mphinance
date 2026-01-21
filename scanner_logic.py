import yfinance as yf
import pandas as pd
import numpy as np
from tradingview_screener import Query, col
from datetime import datetime

def convert_df_to_txt(df):
    """Converts the dataframe to a tab-separated text format for easy reading"""
    return df.to_csv(index=False, sep='\t').encode('utf-8')




def get_live_data(ticker):
    # Fetching 2y to stabilize the 200 SMA and 89 EMA
    data = yf.download(ticker, period="2y", interval="1d", progress=False)
    if data.empty or len(data) < 200:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Calculate Live EMA Stack
    for p in [8, 21, 34, 55, 89]:
        data[f'EMA{p}'] = data['Close'].ewm(span=p, adjust=False).mean()
    
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    
    # ATR Calculation - True Range
    h, l, c = data['High'], data['Low'], data['Close']
    tr = np.maximum(h - l, np.maximum(abs(h - c.shift(1)), abs(l - c.shift(1))))
    
    # ATR(14) - Short-term volatility
    data['ATR'] = tr.rolling(window=14).mean()
    
    # ATR(55) - Long-term volatility for squeeze detection
    data['ATR55'] = tr.rolling(window=55).mean()

    # Stochastic (8, 3, 3) Calculation
    low_8 = data['Low'].rolling(window=8).min()
    high_8 = data['High'].rolling(window=8).max()
    data['stoch_k_raw'] = (data['Close'] - low_8) / (high_8 - low_8) * 100
    data['Stoch'] = data['stoch_k_raw'].rolling(window=3).mean()
    
    # ADX Calculation (14 period)
    plus_dm = data['High'].diff()
    minus_dm = data['Low'].diff() * -1
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # +DM should be > -DM for it to be a +DM move, otherwise 0
    # The standard Wilder implementation is slightly different:
    # UpMove = H - H_prev
    # DownMove = L_prev - L
    # if UpMove > DownMove and UpMove > 0: +DM = UpMove, else 0
    # if DownMove > UpMove and DownMove > 0: -DM = DownMove, else 0
    
    up_move = data['High'] - data['High'].shift(1)
    down_move = data['Low'].shift(1) - data['Low']
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    # Smoothing using RMA (Wilder's Smoothing) - effectively ewm(alpha=1/14)
    # Pandas doesn't have a direct RMA, but ewm(adjust=False, alpha=1/N) is equivalent to EMA(alpha=1/N)
    # Wilder's MMA is ewm(alpha=1/N, adjust=False) which is same as span=2N-1
    # For N=14, alpha=1/14. span = 2*14 - 1 = 27.
    
    tr_s = pd.Series(tr).ewm(alpha=1/14, adjust=False).mean()
    plus_di = pd.Series(plus_dm, index=data.index).ewm(alpha=1/14, adjust=False).mean() / tr_s * 100
    minus_di = pd.Series(minus_dm, index=data.index).ewm(alpha=1/14, adjust=False).mean() / tr_s * 100
    
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    data['ADX'] = dx.ewm(alpha=1/14, adjust=False).mean()
    
    return data

def run_tradingview_screen(adx_range, mcap_range, stoch_range):
    """Full screen criteria with range-based number inputs for ADX, MCap, and Stoch"""
    query = (
        Query()
        .select(
            'name', 'description', 'close', 'change', 
            'ADX', 'ATR', 'average_volume_10d_calc', 'market_cap_basic',
            'Stoch.K',
            'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89',
            'EMA8|1W', 'EMA21|1W', 'EMA34|1W', 'EMA55|1W', 'EMA89|1W',
            'EMA8|1M', 'EMA21|1M', 'EMA34|1M', 'EMA55|1M', 'EMA89|1M',
            'SMA50', 'EMA200'
        )
        .where(
            # General Filters
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('close') > 0.01,
            col('volume') >= 500_000,
            col('average_volume_10d_calc') > 500_000,
            
            # User Dynamic Range Filters
            col('ADX').between(adx_range[0], adx_range[1]),
            col('market_cap_basic').between(mcap_range[0], mcap_range[1]),
            col('Stoch.K').between(stoch_range[0], stoch_range[1]),

            # Strategy Constants (Locked)
            col('ATR') < col('ATR|1W'),
            col('SMA50') > col('EMA200'),
            col('SMA50|1W') > col('EMA200|1W'),
            col('SMA50|1M') > col('EMA200|1M'),

            col('EMA8') > col('EMA21'), col('EMA21') > col('EMA34'), 
            col('EMA34') > col('EMA55'), col('EMA55') > col('EMA89'),

            col('EMA8|1W') > col('EMA21|1W'), col('EMA21|1W') > col('EMA34|1W'), 
            col('EMA34|1W') > col('EMA55|1W'), col('EMA55|1W') > col('EMA89|1W'),

            col('EMA8|1M') > col('EMA21|1M'), col('EMA21|1M') > col('EMA34|1M'), 
            col('EMA34|1M') > col('EMA55|1M'), col('EMA55|1M') > col('EMA89|1M')
        )
        .limit(1000)
    )
    count, df = query.get_scanner_data()
    
    if count > 0:
        # CUSTOM FILTER: Only show stocks within 1 ATR of EMA21 (Not Overextended)
        df['dist_to_21'] = (df['close'] - df['EMA21']).abs()
        df = df[df['dist_to_21'] <= df['ATR']]
        df = df[df['dist_to_21'] <= df['ATR']]
        df = df.rename(columns={'Stoch.K': 'Stoch_K'})
        df = df.fillna(0.0) # Ensure no NaNs for JSON serialization
        return df
    return pd.DataFrame()
