import json
from datetime import datetime, timedelta, timezone

from scripts.check_data_freshness import (
    classify,
    extract_timestamp,
    last_expected_run,
    parse_timestamp,
    scan_directory,
)


class TestParseTimestamp:
    def test_iso_with_z(self):
        dt = parse_timestamp("2026-09-11T14:05:03.512434Z")
        assert dt == datetime(2026, 9, 11, 14, 5, 3, 512434, tzinfo=timezone.utc)

    def test_space_separated_no_tz(self):
        dt = parse_timestamp("2026-09-11 14:02:48")
        assert dt == datetime(2026, 9, 11, 14, 2, 48, tzinfo=timezone.utc)

    def test_date_only(self):
        dt = parse_timestamp("2026-09-11")
        assert dt == datetime(2026, 9, 11, tzinfo=timezone.utc)

    def test_naive_iso_gets_utc(self):
        dt = parse_timestamp("2026-09-11T14:05:03.501982")
        assert dt.tzinfo == timezone.utc

    def test_none_input(self):
        assert parse_timestamp(None) is None

    def test_empty_string(self):
        assert parse_timestamp("") is None

    def test_garbage_string(self):
        assert parse_timestamp("not-a-date") is None


class TestExtractTimestamp:
    def test_top_level_generated_at(self):
        assert extract_timestamp({"generated_at": "2026-09-11T14:05:03Z"}) is not None

    def test_nested_meta(self):
        data = {"meta": {"generated_at": "2026-09-11T14:04:38+00:00"}}
        assert extract_timestamp(data) is not None

    def test_no_timestamp_field(self):
        assert extract_timestamp({"window": 20, "breadth": {}}) is None

    def test_non_dict_payload(self):
        assert extract_timestamp([1, 2, 3]) is None

    def test_prefers_top_level_over_meta(self):
        data = {
            "generated_at": "2026-09-11T14:00:00Z",
            "meta": {"generated_at": "2020-01-01T00:00:00Z"},
        }
        assert extract_timestamp(data) == parse_timestamp("2026-09-11T14:00:00Z")


class TestLastExpectedRun:
    def test_weekday_after_run_hour(self):
        # Friday 2026-09-11 is a Friday, 16:00 UTC is after the 14:00 run hour.
        now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
        expected = last_expected_run(now, run_hour_utc=14)
        assert expected == datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)

    def test_weekday_before_run_hour_rolls_back(self):
        now = datetime(2026, 9, 11, 8, 0, tzinfo=timezone.utc)
        expected = last_expected_run(now, run_hour_utc=14)
        assert expected == datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)

    def test_saturday_rolls_back_to_friday(self):
        now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)  # Saturday
        expected = last_expected_run(now, run_hour_utc=14)
        assert expected == datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)

    def test_sunday_rolls_back_to_friday(self):
        now = datetime(2026, 9, 13, 23, 0, tzinfo=timezone.utc)  # Sunday
        expected = last_expected_run(now, run_hour_utc=14)
        assert expected == datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)

    def test_monday_before_run_hour_rolls_back_to_friday(self):
        now = datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc)  # Monday morning
        expected = last_expected_run(now, run_hour_utc=14)
        assert expected == datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)


class TestClassify:
    def test_no_timestamp(self):
        now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
        assert classify(None, now, grace_hours=6, run_hour_utc=14) == "NO_TIMESTAMP"

    def test_fresh_is_ok(self):
        now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
        ts = datetime(2026, 9, 11, 14, 5, tzinfo=timezone.utc)
        assert classify(ts, now, grace_hours=6, run_hour_utc=14) == "OK"

    def test_within_grace_is_ok(self):
        now = datetime(2026, 9, 11, 19, 0, tzinfo=timezone.utc)
        ts = datetime(2026, 9, 11, 14, 0, tzinfo=timezone.utc)
        assert classify(ts, now, grace_hours=6, run_hour_utc=14) == "OK"

    def test_older_than_grace_is_stale(self):
        now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)  # Saturday
        ts = datetime(2026, 9, 10, 14, 0, tzinfo=timezone.utc)  # Thursday's run
        assert classify(ts, now, grace_hours=6, run_hour_utc=14) == "STALE"

    def test_weekend_does_not_flag_fridays_run(self):
        now = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)  # Saturday
        ts = datetime(2026, 9, 11, 14, 5, tzinfo=timezone.utc)  # Friday's run
        assert classify(ts, now, grace_hours=6, run_hour_utc=14) == "OK"


class TestScanDirectory:
    def test_classifies_mixed_files(self, tmp_path):
        now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)

        (tmp_path / "fresh.json").write_text(
            json.dumps({"generated_at": "2026-09-11T14:05:03Z"}))
        (tmp_path / "stale.json").write_text(
            json.dumps({"generated_at": "2026-03-05T18:27:47Z"}))
        (tmp_path / "no-ts.json").write_text(json.dumps({"window": 20}))
        (tmp_path / "dossier-2026-04-07.json").write_text(
            json.dumps({"generated_at": "2020-01-01T00:00:00Z"}))
        (tmp_path / "broken.json").write_text("{not valid json")

        results = {r["file"]: r for r in scan_directory(tmp_path, now, 6.0, 14)}

        assert results["fresh.json"]["status"] == "OK"
        assert results["stale.json"]["status"] == "STALE"
        assert results["no-ts.json"]["status"] == "NO_TIMESTAMP"
        assert results["dossier-2026-04-07.json"]["status"] == "ARCHIVE"
        assert results["broken.json"]["status"] == "PARSE_ERROR"

    def test_empty_directory(self, tmp_path):
        now = datetime(2026, 9, 11, 16, 0, tzinfo=timezone.utc)
        assert scan_directory(tmp_path, now, 6.0, 14) == []
