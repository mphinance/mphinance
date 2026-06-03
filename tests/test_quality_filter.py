"""Tests for dossier.quality_filter pure helpers."""
import pytest
from dossier.quality_filter import check_quality, _parse_market_cap, _parse_vol_string


class TestParseMarketCap:
    def test_billion_string(self):
        assert _parse_market_cap("$1.5B") == 1_500_000_000.0

    def test_million_string(self):
        assert _parse_market_cap("$500M") == 500_000_000.0

    def test_trillion_string(self):
        assert _parse_market_cap("$2.5T") == 2_500_000_000_000.0

    def test_thousand_string(self):
        assert _parse_market_cap("$10K") == 10_000.0

    def test_numeric_int(self):
        assert _parse_market_cap(1_234_567_890) == 1_234_567_890.0

    def test_numeric_float(self):
        assert _parse_market_cap(5.5e9) == 5.5e9

    def test_zero_numeric(self):
        assert _parse_market_cap(0) is None

    def test_empty_string(self):
        assert _parse_market_cap("") is None

    def test_none(self):
        assert _parse_market_cap(None) is None

    def test_invalid_string(self):
        assert _parse_market_cap("not-a-number") is None

    def test_bare_numeric_string(self):
        assert _parse_market_cap("1000000") == 1_000_000.0

    def test_comma_stripped(self):
        assert _parse_market_cap("$1,000M") == 1_000_000_000.0


class TestParseVolString:
    def test_comma_separated(self):
        assert _parse_vol_string("1,234,567") == 1_234_567

    def test_million_suffix(self):
        assert _parse_vol_string("1.2M") == 1_200_000

    def test_thousand_suffix(self):
        assert _parse_vol_string("500K") == 500_000

    def test_invalid(self):
        assert _parse_vol_string("abc") == 0

    def test_empty(self):
        assert _parse_vol_string("") == 0

    def test_plain_integer_string(self):
        assert _parse_vol_string("250000") == 250_000


class TestCheckQuality:
    def _minimal_clean_payload(self):
        """A clean, high-quality payload that should score near 100."""
        return {
            "ticker": "MSFT",
            "companyName": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software",
            "currentPrice": 420.0,
            "priceChangePct": 1.2,
            "technical_analysis": {
                "volume": {"avg_vol_20d": 20_000_000, "rel_vol": 1.1},
            },
            "fundamentals": {
                "marketCap": 3_000_000_000_000,
                "trailingEps": 12.5,
                "revenueGrowth": 0.17,
            },
            "scores": {"grade": "A"},
        }

    def test_clean_ticker_high_score(self):
        result = check_quality(self._minimal_clean_payload())
        assert result["quality_score"] == 100
        assert not result["has_issues"]

    def test_etf_penalized(self):
        payload = self._minimal_clean_payload()
        payload["companyName"] = "iShares Core S&P 500 ETF"
        result = check_quality(payload)
        assert result["quality_score"] < 50
        assert result["flags"]["is_etf"]

    def test_penny_stock_penalized(self):
        payload = self._minimal_clean_payload()
        payload["currentPrice"] = 1.50
        result = check_quality(payload)
        assert result["quality_score"] < 100
        assert result["flags"]["is_penny"]

    def test_spac_penalized(self):
        payload = self._minimal_clean_payload()
        payload["companyName"] = "Acme Acquisition Corp"
        result = check_quality(payload)
        assert result["quality_score"] < 60
        assert result["flags"]["is_spac"]

    def test_low_liquidity_penalized(self):
        payload = self._minimal_clean_payload()
        payload["technical_analysis"]["volume"]["avg_vol_20d"] = 50_000
        result = check_quality(payload)
        assert result["quality_score"] < 100
        assert result["flags"]["is_low_liquidity"]

    def test_junk_bio_penalized(self):
        payload = self._minimal_clean_payload()
        payload["sector"] = "Healthcare"
        payload["industry"] = "Biotechnology"
        payload["fundamentals"]["marketCap"] = 200_000_000  # < $500M
        payload["fundamentals"]["trailingEps"] = -0.5       # no profits
        payload["fundamentals"]["revenueGrowth"] = -0.1     # no growth
        result = check_quality(payload)
        assert result["quality_score"] < 100
        assert result["flags"]["is_junk_bio"]

    def test_result_keys_present(self):
        result = check_quality(self._minimal_clean_payload())
        assert "quality_score" in result
        assert "flags" in result
        assert "reasons" in result
        assert "has_issues" in result
        assert "ticker" in result

    def test_score_bounded(self):
        # Even with multiple flags the score can't go below 0
        payload = self._minimal_clean_payload()
        payload["companyName"] = "Ghost Acquisition Blank Check Special Purpose"
        payload["currentPrice"] = 0.50
        result = check_quality(payload)
        assert 0 <= result["quality_score"] <= 100
