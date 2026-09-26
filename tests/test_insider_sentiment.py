"""Tests for dossier.insider_sentiment — net read across buy/sell cluster screens."""

from dossier.insider_sentiment import compute_insider_sentiment


def _buy(ticker="AAPL", grade="A", score=80, distinct_buyers=2, total_value=1_000_000):
    return {
        "ticker": ticker, "name": ticker, "price": 100.0, "change_pct": 1.5,
        "market_cap": 5e9, "grade": grade, "score": score,
        "distinct_buyers": distinct_buyers, "total_value": total_value,
    }


def _sell(ticker="AAPL", grade="A", score=80, distinct_sellers=2, total_value=1_000_000):
    return {
        "ticker": ticker, "name": ticker, "price": 100.0, "change_pct": -1.5,
        "market_cap": 5e9, "grade": grade, "score": score,
        "distinct_sellers": distinct_sellers, "total_value": total_value,
    }


class TestComputeInsiderSentiment:
    def test_empty_inputs_return_nothing(self):
        result = compute_insider_sentiment([], [])
        assert result["counts"] == {"bullish": 0, "bearish": 0, "conflicted": 0}
        assert result["bullish"] == result["bearish"] == result["conflicted"] == []
        assert result["buy_loaded"] is False
        assert result["sell_loaded"] is False
        assert "generated_at" in result

    def test_buy_only_is_clean_bullish(self):
        result = compute_insider_sentiment([_buy("AAPL", grade="A+")], [])
        assert result["counts"]["bullish"] == 1
        entry = result["bullish"][0]
        assert entry["ticker"] == "AAPL"
        assert entry["buy"]["grade"] == "A+"
        assert entry["sell"] is None
        assert entry["net_score"] == 5
        assert result["buy_loaded"] is True
        assert result["sell_loaded"] is False

    def test_sell_only_is_clean_bearish(self):
        result = compute_insider_sentiment([], [_sell("XYZ", grade="B")])
        assert result["counts"]["bearish"] == 1
        entry = result["bearish"][0]
        assert entry["ticker"] == "XYZ"
        assert entry["sell"]["grade"] == "B"
        assert entry["buy"] is None
        assert entry["net_score"] == -3

    def test_ticker_in_both_lists_is_conflicted_not_bullish_or_bearish(self):
        result = compute_insider_sentiment(
            [_buy("MSFT", grade="A")], [_sell("MSFT", grade="C")]
        )
        assert result["counts"] == {"bullish": 0, "bearish": 0, "conflicted": 1}
        entry = result["conflicted"][0]
        assert entry["ticker"] == "MSFT"
        assert entry["buy"]["grade"] == "A"
        assert entry["sell"]["grade"] == "C"
        assert entry["net_score"] == 4 - 2

    def test_conflicted_net_score_can_be_negative_when_sellers_dominate(self):
        result = compute_insider_sentiment(
            [_buy("CONF", grade="C")], [_sell("CONF", grade="A+")]
        )
        entry = result["conflicted"][0]
        assert entry["net_score"] == 2 - 5

    def test_bullish_sorted_strongest_first(self):
        result = compute_insider_sentiment(
            [_buy("WEAK", grade="B"), _buy("STRONG", grade="A+")], []
        )
        tickers = [e["ticker"] for e in result["bullish"]]
        assert tickers == ["STRONG", "WEAK"]

    def test_bearish_sorted_strongest_first(self):
        result = compute_insider_sentiment(
            [], [_sell("WEAK", grade="B"), _sell("STRONG", grade="A+")]
        )
        tickers = [e["ticker"] for e in result["bearish"]]
        assert tickers == ["STRONG", "WEAK"]

    def test_conflicted_sorted_by_combined_activity(self):
        result = compute_insider_sentiment(
            [_buy("LOUD", grade="A+"), _buy("QUIET", grade="B")],
            [_sell("LOUD", grade="A"), _sell("QUIET", grade="C")],
        )
        tickers = [e["ticker"] for e in result["conflicted"]]
        assert tickers == ["LOUD", "QUIET"]

    def test_missing_grade_is_ignored(self):
        result = compute_insider_sentiment([{"ticker": "NOPE", "score": 10}], [])
        assert result["counts"] == {"bullish": 0, "bearish": 0, "conflicted": 0}

    def test_missing_ticker_is_ignored(self):
        result = compute_insider_sentiment([{"ticker": None, "grade": "A"}], [])
        assert result["counts"]["bullish"] == 0

    def test_non_list_input_is_treated_as_empty(self):
        result = compute_insider_sentiment(None, "not-a-list")
        assert result["counts"] == {"bullish": 0, "bearish": 0, "conflicted": 0}
        assert result["buy_loaded"] is False
        assert result["sell_loaded"] is False

    def test_non_dict_row_is_skipped(self):
        result = compute_insider_sentiment(["garbage"], [_sell("AAPL")])
        assert result["counts"]["bearish"] == 1

    def test_never_raises_on_malformed_input(self):
        result = compute_insider_sentiment([{}], [{"ticker": "X"}])
        assert result["counts"] == {"bullish": 0, "bearish": 0, "conflicted": 0}

    def test_loaded_flags_reflect_at_least_one_valid_row(self):
        result = compute_insider_sentiment([{"ticker": "OK", "grade": "A"}], [{"ticker": None}])
        assert result["buy_loaded"] is True
        assert result["sell_loaded"] is False

    def test_carries_through_display_fields(self):
        result = compute_insider_sentiment([_buy("AAPL", grade="A")], [])
        entry = result["bullish"][0]
        assert entry["name"] == "AAPL"
        assert entry["price"] == 100.0
        assert entry["change_pct"] == 1.5
        assert entry["market_cap"] == 5e9
