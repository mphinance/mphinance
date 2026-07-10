"""Tests for dossier.screener_overlap — multi-screen agreement (TAO/VCP/PEAD)."""

from dossier.screener_overlap import compute_screener_overlap


def _hit(ticker="AAPL", score=80, grade="A"):
    return {"ticker": ticker, "score": score, "grade": grade}


class TestComputeScreenerOverlap:
    def test_empty_inputs_return_no_overlap(self):
        result = compute_screener_overlap([], [], [])
        assert result["overlap_count"] == 0
        assert result["tickers"] == []
        assert "generated_at" in result

    def test_single_screen_hit_is_not_overlap(self):
        result = compute_screener_overlap([_hit("AAPL")], [], [])
        assert result["overlap_count"] == 0

    def test_two_screen_hit_counts_as_overlap(self):
        result = compute_screener_overlap([_hit("AAPL", grade="A+")], [_hit("AAPL", grade="A")], [])
        assert result["overlap_count"] == 1
        entry = result["tickers"][0]
        assert entry["ticker"] == "AAPL"
        assert entry["screen_count"] == 2
        assert entry["screens"] == ["tao", "vcp"]
        assert entry["details"]["tao"]["grade"] == "A+"
        assert entry["details"]["vcp"]["grade"] == "A"

    def test_three_screen_hit(self):
        result = compute_screener_overlap(
            [_hit("MSFT", grade="A+")], [_hit("MSFT", grade="A")], [_hit("MSFT", grade="B")]
        )
        assert result["overlap_count"] == 1
        assert result["tickers"][0]["screen_count"] == 3
        assert result["tickers"][0]["screens"] == ["pead", "tao", "vcp"]

    def test_ranks_more_screens_before_fewer(self):
        result = compute_screener_overlap(
            [_hit("TWO", grade="A"), _hit("THREE", grade="B")],
            [_hit("TWO", grade="A"), _hit("THREE", grade="B")],
            [_hit("THREE", grade="B")],
        )
        tickers = [e["ticker"] for e in result["tickers"]]
        assert tickers == ["THREE", "TWO"]

    def test_higher_combined_grade_breaks_ties(self):
        result = compute_screener_overlap(
            [_hit("STRONG", grade="A+"), _hit("WEAK", grade="B")],
            [_hit("STRONG", grade="A+"), _hit("WEAK", grade="B")],
            [],
        )
        tickers = [e["ticker"] for e in result["tickers"]]
        assert tickers == ["STRONG", "WEAK"]

    def test_missing_grade_is_ignored(self):
        result = compute_screener_overlap([{"ticker": "NOPE", "score": 10}], [_hit("NOPE")], [])
        assert result["overlap_count"] == 0

    def test_non_list_leg_is_treated_as_empty(self):
        result = compute_screener_overlap(None, [_hit("AAPL")], "not-a-list")
        assert result["overlap_count"] == 0

    def test_non_dict_row_is_skipped(self):
        result = compute_screener_overlap(["garbage"], [_hit("AAPL")], [])
        assert result["overlap_count"] == 0

    def test_never_raises_on_malformed_input(self):
        result = compute_screener_overlap([{"ticker": None, "grade": "A"}], [{}], [])
        assert result["overlap_count"] == 0
