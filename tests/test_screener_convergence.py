"""Tests for dossier.screener_convergence — multi-screen agreement across all screens."""

from dossier.screener_convergence import compute_convergence


def _hit(ticker="AAPL", score=80, grade="A"):
    return {"ticker": ticker, "score": score, "grade": grade}


class TestComputeConvergence:
    def test_empty_inputs_return_no_convergence(self):
        result = compute_convergence({})
        assert result["convergence_count"] == 0
        assert result["tickers"] == []
        assert result["screens_loaded"] == []
        assert "generated_at" in result

    def test_single_screen_hit_is_not_convergence(self):
        result = compute_convergence({"tao": [_hit("AAPL")]})
        assert result["convergence_count"] == 0
        assert result["screens_loaded"] == ["tao"]

    def test_two_screen_hit_counts_as_convergence(self):
        result = compute_convergence({
            "tao": [_hit("AAPL", grade="A+")],
            "vcp": [_hit("AAPL", grade="A")],
        })
        assert result["convergence_count"] == 1
        entry = result["tickers"][0]
        assert entry["ticker"] == "AAPL"
        assert entry["screen_count"] == 2
        assert entry["screens"] == ["tao", "vcp"]
        assert entry["details"]["tao"]["grade"] == "A+"
        assert entry["details"]["vcp"]["grade"] == "A"

    def test_five_screen_hit_across_new_screens(self):
        result = compute_convergence({
            "tao": [_hit("MSFT", grade="A+")],
            "capitulation": [_hit("MSFT", grade="A")],
            "golden_cross": [_hit("MSFT", grade="B")],
            "rvol": [_hit("MSFT", grade="A")],
            "nr7": [_hit("MSFT", grade="C")],
        })
        assert result["convergence_count"] == 1
        entry = result["tickers"][0]
        assert entry["screen_count"] == 5
        assert entry["screens"] == ["capitulation", "golden_cross", "nr7", "rvol", "tao"]

    def test_ranks_more_screens_before_fewer(self):
        result = compute_convergence({
            "tao": [_hit("TWO", grade="A"), _hit("THREE", grade="B")],
            "vcp": [_hit("TWO", grade="A"), _hit("THREE", grade="B")],
            "pead": [_hit("THREE", grade="B")],
        })
        tickers = [e["ticker"] for e in result["tickers"]]
        assert tickers == ["THREE", "TWO"]

    def test_higher_combined_grade_breaks_ties(self):
        result = compute_convergence({
            "tao": [_hit("STRONG", grade="A+"), _hit("WEAK", grade="B")],
            "vcp": [_hit("STRONG", grade="A+"), _hit("WEAK", grade="B")],
        })
        tickers = [e["ticker"] for e in result["tickers"]]
        assert tickers == ["STRONG", "WEAK"]

    def test_missing_grade_is_ignored(self):
        result = compute_convergence({
            "tao": [{"ticker": "NOPE", "score": 10}],
            "vcp": [_hit("NOPE")],
        })
        assert result["convergence_count"] == 0

    def test_non_list_leg_is_treated_as_empty(self):
        result = compute_convergence({"tao": None, "vcp": [_hit("AAPL")], "pead": "not-a-list"})
        assert result["convergence_count"] == 0
        assert result["screens_loaded"] == ["vcp"]

    def test_non_dict_row_is_skipped(self):
        result = compute_convergence({"tao": ["garbage"], "vcp": [_hit("AAPL")]})
        assert result["convergence_count"] == 0

    def test_never_raises_on_malformed_input(self):
        result = compute_convergence({"tao": [{"ticker": None, "grade": "A"}], "vcp": [{}]})
        assert result["convergence_count"] == 0

    def test_min_screens_can_be_tightened(self):
        results_by_screen = {
            "tao": [_hit("AAPL", grade="A")],
            "vcp": [_hit("AAPL", grade="A")],
        }
        assert compute_convergence(results_by_screen, min_screens=2)["convergence_count"] == 1
        assert compute_convergence(results_by_screen, min_screens=3)["convergence_count"] == 0

    def test_screens_loaded_excludes_empty_screens(self):
        result = compute_convergence({"tao": [_hit("AAPL")], "vcp": [], "pead": []})
        assert result["screens_loaded"] == ["tao"]
