import sys
from unittest.mock import MagicMock

# Mock dependencies that might be missing in the test environment
sys.modules['yfinance'] = MagicMock()
sys.modules['tradingview_screener'] = MagicMock()

import unittest
from scanner_logic import get_recommended_multiplier

class TestMultiplier(unittest.TestCase):
    def test_high_beta(self):
        high_beta = ['NVDA', 'TSLA', 'COIN', 'AMD', 'PLTR', 'MSTR']
        for ticker in high_beta:
            self.assertEqual(get_recommended_multiplier(ticker), 2.0, f"Failed for {ticker}")

    def test_stable_etf(self):
        stable_etf = ['GLD', 'SPY', 'QQQ', 'DIA']
        for ticker in stable_etf:
            self.assertEqual(get_recommended_multiplier(ticker), 1.5, f"Failed for {ticker}")

    def test_standard(self):
        standard = ['AAPL', 'MSFT', 'UNKNOWN', 'F']
        for ticker in standard:
            self.assertEqual(get_recommended_multiplier(ticker), 1.75, f"Failed for {ticker}")

if __name__ == '__main__':
    unittest.main()
