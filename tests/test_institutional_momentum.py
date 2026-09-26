"""Tests for dossier.institutional_momentum — nets TickerTrace's recent_changes."""

from dossier.institutional_momentum import compute_fund_flow_clusters


def _change(ticker="AAPL", fund="ULTI", weight_delta=1.0, change_type="CHANGED", **kw):
    return {
        "fund": fund, "ticker": ticker, "name": kw.get("name", ticker),
        "sector": kw.get("sector", "TECHNOLOGY"), "weightDelta": weight_delta,
        "activeWeightDelta": weight_delta, "sharesDelta": kw.get("sharesDelta", 100.0),
        "currentWeight": kw.get("currentWeight", 5.0), "previousWeight": kw.get("previousWeight", 4.0),
        "type": change_type, "isOption": kw.get("isOption", False),
        "fundCategory": kw.get("fundCategory", "active-equity"),
    }


class TestComputeFundFlowClusters:
    def test_empty_input_returns_nothing(self):
        result = compute_fund_flow_clusters([])
        assert result["total_changes"] == 0
        assert result["counts"] == {"accumulating": 0, "distributing": 0}
        assert result["accumulating"] == result["distributing"] == []
        assert "generated_at" in result

    def test_non_list_input_does_not_raise(self):
        for bad in (None, "oops", 42, {"not": "a list"}):
            result = compute_fund_flow_clusters(bad)
            assert result["total_changes"] == 0
            assert result["accumulating"] == result["distributing"] == []

    def test_malformed_rows_are_skipped(self):
        rows = [
            "not-a-dict",
            {"fund": "ULTI"},  # missing ticker
            {"ticker": "AAPL"},  # missing fund
            _change("AAPL", "ULTI"),
            _change("AAPL", "TSLW"),
        ]
        result = compute_fund_flow_clusters(rows)
        assert result["total_changes"] == 2
        assert [e["ticker"] for e in result["accumulating"]] == ["AAPL"]

    def test_single_fund_routine_trim_is_not_notable_enough_to_surface(self):
        """One fund nudging a position (type CHANGED) below the cluster
        threshold is noise — it shouldn't show up in either list."""
        result = compute_fund_flow_clusters([_change("AAPL", "ULTI", weight_delta=0.5)])
        assert result["accumulating"] == result["distributing"] == []
        assert result["total_changes"] == 1

    def test_single_fund_new_position_is_notable_even_alone(self):
        result = compute_fund_flow_clusters([
            _change("HOS", "AVUV", weight_delta=2.0, change_type="NEW")
        ])
        assert len(result["accumulating"]) == 1
        entry = result["accumulating"][0]
        assert entry["ticker"] == "HOS"
        assert entry["fund_count"] == 1
        assert entry["notable"] is True
        assert entry["new_count"] == 1

    def test_single_fund_full_exit_is_notable_and_distributing(self):
        result = compute_fund_flow_clusters([
            _change("ASST", "ULTI", weight_delta=-5.6, change_type="REMOVED")
        ])
        assert len(result["distributing"]) == 1
        entry = result["distributing"][0]
        assert entry["ticker"] == "ASST"
        assert entry["notable"] is True
        assert entry["removed_count"] == 1

    def test_two_funds_same_direction_cluster_into_accumulating(self):
        result = compute_fund_flow_clusters([
            _change("TSLA", "TSLW", weight_delta=0.78),
            _change("TSLA", "TSLQ", weight_delta=1.2),
        ])
        assert len(result["accumulating"]) == 1
        entry = result["accumulating"][0]
        assert entry["fund_count"] == 2
        assert entry["net_weight_delta"] == round(0.78 + 1.2, 4)
        assert {f["fund"] for f in entry["funds"]} == {"TSLW", "TSLQ"}
        assert entry["notable"] is False

    def test_opposing_funds_net_to_correct_direction(self):
        """Two funds moving in opposite directions still cluster (2+ funds
        touched the name), netted to whichever side wins."""
        result = compute_fund_flow_clusters([
            _change("NVDA", "FundA", weight_delta=3.0),
            _change("NVDA", "FundB", weight_delta=-1.0),
        ])
        assert len(result["accumulating"]) == 1
        assert result["accumulating"][0]["net_weight_delta"] == 2.0

    def test_exact_cancel_out_produces_no_net_signal(self):
        result = compute_fund_flow_clusters([
            _change("SPY", "FundA", weight_delta=1.0),
            _change("SPY", "FundB", weight_delta=-1.0),
        ])
        assert result["accumulating"] == result["distributing"] == []

    def test_accumulating_sorted_strongest_first(self):
        rows = [
            _change("A", "F1", weight_delta=0.5), _change("A", "F2", weight_delta=0.5),
            _change("B", "F1", weight_delta=5.0), _change("B", "F2", weight_delta=5.0),
        ]
        result = compute_fund_flow_clusters(rows)
        assert [e["ticker"] for e in result["accumulating"]] == ["B", "A"]

    def test_distributing_sorted_strongest_first(self):
        rows = [
            _change("A", "F1", weight_delta=-0.5), _change("A", "F2", weight_delta=-0.5),
            _change("B", "F1", weight_delta=-5.0), _change("B", "F2", weight_delta=-5.0),
        ]
        result = compute_fund_flow_clusters(rows)
        assert [e["ticker"] for e in result["distributing"]] == ["B", "A"]

    def test_custom_min_cluster_funds_threshold(self):
        rows = [_change("A", "F1", weight_delta=1.0), _change("A", "F2", weight_delta=1.0),
                _change("A", "F3", weight_delta=1.0)]
        assert compute_fund_flow_clusters(rows, min_cluster_funds=2)["accumulating"] != []
        assert compute_fund_flow_clusters(rows, min_cluster_funds=4)["accumulating"] == []
