"""CLI runner for the canonical stock_analyzer module — single-ticker audit."""
import os
import sys

import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stock_analyzer import StockAnalyzer, generate_market_analysis  # noqa: E402


def main(ticker):
    df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)
    if df.empty:
        print(f"No data for {ticker}")
        return
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    a = StockAnalyzer()
    d = a.calculate_technical_indicators(df)
    cp = float(d["Close"].iloc[-1])
    print(f"=== {ticker} — Single Ticker Audit ({d.index[-1].date()}) ===")
    print(f"Bars: {len(df)}   Current: ${cp:.2f}\n")

    info = a.train_prediction_model(d, horizon=5)
    if info:
        p = a.predict_price_range(info, cp)
        if info.get("reliable"):
            print("🔮 5-Day Price Target Range")
            print(f"  Low      ${p['low']:.2f}   ({p['low_change_pct']:+.2f}%)")
            print(f"  Expected ${p['expected']:.2f}   ({p['expected_change_pct']:+.2f}%)")
            print(f"  High     ${p['high']:.2f}   ({p['high_change_pct']:+.2f}%)")
            print(f"  Tree agreement: {p['confidence']*100:.0f}%   Out-of-sample R²: {info['test_score']:.3f}")
            top = list(info["feature_importance"].items())[:6]
            print("  Top drivers: " + ", ".join(f"{k} {v*100:.0f}%" for k, v in top))
        else:
            print("🔮 5-Day Price Target Range — HIDDEN (model unreliable)")
            print(f"  {info['unreliable_reason']}")
    else:
        print("Not enough data to train model.")

    print("\n💡 Technical Insights")
    for line in generate_market_analysis(d, ticker):
        print(f"  {line}")

    L = d.iloc[-1]
    print("\n📊 Indicator Snapshot")
    print(f"  RSI(14): {L['RSI']:.1f}   Stoch %K/%D: {L['Stoch_K']:.0f}/{L['Stoch_D']:.0f}")
    print(f"  SMA20 ${L['SMA20']:.2f}   SMA50 ${L['SMA50']:.2f}")
    print(f"  MACD {L['MACD']:.2f} / signal {L['MACD_Signal']:.2f} (hist {L['MACD_Hist']:+.2f})")
    print(f"  BB ${L['BB_Lower']:.2f} – ${L['BB_Upper']:.2f}   ATR ${L['ATR']:.2f}")
    print(f"  Vol ratio: {L['Vol_Ratio']:.2f}× 20d avg")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "HPE")
