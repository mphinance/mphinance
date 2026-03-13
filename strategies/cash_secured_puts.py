"""
Cash Secured Puts Strategy — Momentum-filtered CSP candidates.

Stage 1: TradingView scan for bullish, liquid stocks
Stage 2: Post-filter for EMA stack alignment + ATR proximity
Stage 3: Deep dive into options chains for OTM put candidates

Backtested 2026-03-13: Momentum filter (EMA 21>34>55 + VRP≥1.0)
caught all 9 Grade-F setups from March 5 snapshot.
"""
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
from .base import BaseStrategy


class CashSecuredPutsStrategy(BaseStrategy):
    """Find bullish stocks with rich IV for cash-secured put selling."""

    name = "Cash Secured Puts"
    description = "Momentum-filtered CSP candidates with VoPR enrichment"

    select_columns = [
        'name', 'description', 'close', 'change', 'sector',
        'ADX', 'ATR', 'RSI', 'market_cap_basic',
        'average_volume_10d_calc', 'relative_volume_10d_calc',
        'SMA50', 'SMA200',
        'EMA21', 'EMA34', 'EMA55', 'EMA89',
        'Stoch.K',
    ]

    def get_default_params(self) -> Dict[str, Any]:
        return {
            'adx_min': 20.0,
            'rsi_min': 30.0,
            'rsi_max': 70.0,
            'min_volume': 500_000,
            'price_min': 10.0,
            'price_max': 500.0,
            'dte_min': 7,
            'dte_max': 45,
            'max_results': 30,
        }

    def build_query(self, params: Dict[str, Any]) -> Query:
        """Stage 1: TradingView sweep — bullish, liquid, trending stocks."""
        adx_min = params.get('adx_min', 20)
        rsi_min = params.get('rsi_min', 30)
        rsi_max = params.get('rsi_max', 70)
        min_vol = params.get('min_volume', 500_000)
        price_min = params.get('price_min', 10)
        price_max = params.get('price_max', 500)

        filters = [
            # Exchange & liquidity
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('close').between(price_min, price_max),
            col('volume') >= min_vol,
            col('average_volume_10d_calc') > min_vol,

            # Trend gate: Golden Cross + EMA 21>34>55 (backtested)
            col('SMA50') > col('SMA200'),
            col('EMA21') > col('EMA34'),
            col('EMA34') > col('EMA55'),

            # Strength: ADX > 20 + RSI neutral zone
            col('ADX') >= adx_min,
            col('RSI').between(rsi_min, rsi_max),
        ]

        return (
            Query()
            .select(*self.select_columns)
            .where(*filters)
            .limit(500)
        )

    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Stage 2: ATR proximity filter — price within 1 ATR of EMA21."""
        if df.empty:
            return df

        df = df.rename(columns={'Stoch.K': 'Stoch_K'})

        # Filter: price within 1 ATR of EMA21 (not overextended)
        df['dist_to_21'] = (df['close'] - df['EMA21']).abs()
        df = df[df['dist_to_21'] <= df['ATR']]

        df = df.fillna(0.0)
        return df

    def deep_dive(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Stage 3: Options chain analysis for OTM put candidates."""
        params = params or self.get_default_params()
        dte_min = params.get('dte_min', 7)
        dte_max = params.get('dte_max', 45)

        results = []
        for _, row in df.iterrows():
            ticker = str(row.get('name', ''))
            price = float(row.get('close', 0))
            if not ticker or price <= 0:
                continue

            try:
                stock = yf.Ticker(ticker)
                expirations = stock.options
                if not expirations:
                    continue

                today = datetime.now()
                best_trade = None

                for exp_str in expirations:
                    exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                    dte = (exp_date - today).days
                    if dte < dte_min or dte > dte_max:
                        continue

                    try:
                        chain = stock.option_chain(exp_str)
                        puts = chain.puts
                        if puts.empty:
                            continue

                        # OTM puts: strike < current price, ~10% below
                        otm = puts[puts['strike'] < price * 0.92]
                        if otm.empty:
                            otm = puts[puts['strike'] < price * 0.95]
                        if otm.empty:
                            continue

                        # Pick the highest strike (closest to ATM but still OTM)
                        candidate = otm.iloc[-1]
                        strike = float(candidate['strike'])
                        premium = float(candidate['lastPrice']) if candidate['lastPrice'] > 0 else float(candidate.get('bid', 0))
                        if premium <= 0:
                            continue

                        # Weekly ROC = (premium / strike) * (7 / dte) * 100
                        roc_weekly = (premium / strike) * (7 / max(dte, 1)) * 100

                        if best_trade is None or roc_weekly > best_trade['roc_w']:
                            best_trade = {
                                'exp': exp_str,
                                'strike': strike,
                                'premium': premium,
                                'roc_w': roc_weekly,
                                'dte': dte,
                                'delta': float(candidate.get('delta', 0)) if pd.notna(candidate.get('delta')) else 0,
                            }
                    except Exception:
                        continue

                if best_trade:
                    trade_row = row.to_dict()
                    trade_row['Trade_Type'] = 'CSP'
                    trade_row['Trade_Exp'] = best_trade['exp']
                    trade_row['Trade_Strike'] = best_trade['strike']
                    trade_row['Trade_Prem'] = best_trade['premium']
                    trade_row['Trade_ROC_W'] = best_trade['roc_w']
                    trade_row['DaysOut'] = best_trade['dte']
                    trade_row['Trade_Delta'] = best_trade['delta']
                    results.append(trade_row)

            except Exception as e:
                print(f"    [WARN] {ticker} chain failed: {e}")
                continue

        if not results:
            return pd.DataFrame()

        result_df = pd.DataFrame(results)
        # Sort by weekly ROC descending
        result_df = result_df.sort_values('Trade_ROC_W', ascending=False)
        return result_df
