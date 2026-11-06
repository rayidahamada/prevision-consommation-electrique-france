"""Tests synthétiques de l'audit exploratoire ; aucun appel réseau réel."""

from datetime import datetime, timezone
from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

from experiments.faisabilite_application import inspect_eco2mix_api as api


def row(stamp="2026-01-01T00:00:00Z", value=50000):
    local = api.parse_utc(stamp).astimezone(ZoneInfo("Europe/Paris"))
    return {"date_heure": stamp, "consommation": value, "nature": "Synthétique",
            "perimetre": "France", "date": local.date().isoformat(), "heure": local.strftime("%H:%M")}


def metadata():
    return {"dataset_id": "eco2mix-national-tr", "fields": [{"name": name} for name in api.FIELDS]}


class Response(io.BytesIO):
    def __init__(self, value, content_type="application/json"):
        super().__init__(value)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = content_type


class ApiInspectionTests(unittest.TestCase):
    def test_parse_offsets_and_naive_rejection(self):
        self.assertEqual(api.parse_utc("2026-01-01T01:00:00+01:00"), api.parse_utc("2026-01-01T00:00:00Z"))
        with self.assertRaises(ValueError):
            api.parse_utc("2026-01-01T00:00:00")

    def test_age_and_future_sign(self):
        self.assertEqual(api.observation_age("2026-01-01T23:45:00Z", "2026-01-02T00:00:00Z"), 900)
        self.assertEqual(api.observation_age("2026-01-02T00:15:00Z", "2026-01-02T00:00:00Z"), -900)

    def test_spring_23_hours_no_utc_gap(self):
        stamps = api.local_day_hours("2026-03-29")
        self.assertEqual(len(stamps), 23)
        self.assertEqual(set((b-a).total_seconds() for a,b in zip(stamps, stamps[1:])), {3600})
        self.assertNotIn(2, [v.astimezone(ZoneInfo("Europe/Paris")).hour for v in stamps])

    def test_autumn_25_hours_distinct_repeated_hour(self):
        stamps = api.local_day_hours("2026-10-25")
        repeated = [s.astimezone(ZoneInfo("Europe/Paris")) for s in stamps if s.astimezone(ZoneInfo("Europe/Paris")).hour == 2]
        self.assertEqual(len(stamps), 25)
        self.assertEqual([s.fold for s in repeated], [0, 1])
        self.assertNotEqual(repeated[0].utcoffset(), repeated[1].utcoffset())

    def test_utc_day_boundary(self):
        stamp = api.parse_utc("2026-07-01T00:00:00+02:00")
        self.assertEqual(stamp.isoformat(), "2026-06-30T22:00:00+00:00")
        self.assertEqual(len(api.local_day_hours("2026-01-01")), 24)

    def test_metadata_changed_schema(self):
        self.assertEqual(api.metadata_summary(metadata())["dataset_id"], "eco2mix-national-tr")
        for value in ({}, {"dataset_id": "eco2mix-national-tr", "fields": []}, []):
            with self.assertRaises(ValueError):
                api.metadata_summary(value)

    def test_empty_and_null_records_are_distinct(self):
        self.assertEqual(api.parse_records({"total_count": 0, "results": []}, 1), [])
        record = row(value=None)
        parsed = api.parse_records({"total_count": 1, "results": [record]}, 1)
        audit = api.analyse_records(parsed, "2026-01-01T02:00:00Z")
        self.assertEqual(audit["null_consumption"], 1)
        self.assertIsNone(audit["latest_usable"])
        self.assertFalse(audit["publication_delay_proven"])

    def test_record_schema_count_and_limit(self):
        for payload in ({"total_count": 1, "results": [{}]}, {"total_count": True, "results": []},
                        {"total_count": 0, "results": [row()]}, {"total_count": 2, "results": [row(), row()]}):
            with self.assertRaises(ValueError):
                api.parse_records(payload, 1)

    def test_latest_finite_positive_past_and_age(self):
        rows = [row(), row("2026-01-01T00:15:00Z", None), row("2026-01-01T03:00:00Z")]
        audit = api.analyse_records(rows, "2026-01-01T02:00:00Z")
        self.assertEqual(audit["latest_usable_age_seconds"], 7200)
        self.assertEqual(audit["future_timestamps"], 1)

    def test_invalid_power_and_timestamp(self):
        rows = [row(value=value) for value in [True, "100", float("nan"), -1, 0]]
        rows.append({**row(), "date_heure": "invalide"})
        audit = api.analyse_records(rows, "2026-01-01T01:00:00Z")
        self.assertEqual(audit["invalid_consumption"], 3)
        self.assertEqual(audit["negative_consumption"], 1)
        self.assertEqual(audit["zero_consumption"], 1)
        self.assertEqual(audit["invalid_timestamps"], 1)

    def test_duplicates_not_selected_and_missing_steps(self):
        rows = [row(value=1), row(value=2), row("2026-01-01T00:30:00Z")]
        audit = api.analyse_records(rows, "2026-01-01T02:00:00Z")
        self.assertEqual(audit["duplicate_timestamp_excess"], 1)
        self.assertEqual(audit["missing_quarterhours_between_sample_bounds"], 1)
        audit = api.analyse_records(rows[:2], "2026-01-01T02:00:00Z")
        self.assertIsNone(audit["latest_usable"])

    def test_calendar_mismatch_and_off_grid(self):
        record = {**row("2026-01-01T00:07:00Z"), "heure": "00:07"}
        audit = api.analyse_records([record], "2026-01-01T02:00:00Z")
        self.assertEqual(audit["off_quarterhour_grid"], 1)
        self.assertEqual(audit["source_calendar_mismatch_iso"], 1)
        self.assertIsNone(audit["missing_quarterhours_between_sample_bounds"])

    def test_http_request_success_and_timeout_argument(self):
        opener = unittest.mock.Mock()
        opener.open.return_value = Response(b'{"total_count":0,"results":[]}')
        payload, event = api.request_json(api.API + "/records", {"limit": 1}, 3, opener)
        self.assertEqual(payload["results"], [])
        self.assertEqual(event["http_status"], 200)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 3)
        self.assertIsNone(opener.open.call_args.args[0].get_header("Authorization"))

    def test_http_network_timeout_errors(self):
        for error, expected in [(HTTPError(api.API, 429, "limited", {}, None), "HTTPError: HTTP 429"),
                                (URLError("synthetic-network"), "URLError: synthetic-network"),
                                (TimeoutError("synthetic-timeout"), "TimeoutError: synthetic-timeout")]:
            opener = unittest.mock.Mock()
            opener.open.side_effect = error
            payload, event = api.request_json(api.API, {}, opener=opener)
            self.assertIsNone(payload)
            self.assertEqual(event["error"], expected)

    def test_invalid_json_content_and_response_size(self):
        for body, kind in [(b"not json", "application/json"), (b"{}", "text/html"),
                           (b'{"bad":NaN}', "application/json"), (b"x" * (api.MAX_BYTES + 1), "application/json")]:
            opener = unittest.mock.Mock()
            opener.open.return_value = Response(body, kind)
            payload, event = api.request_json(api.API, {}, opener=opener)
            self.assertIsNone(payload)
            self.assertIsNotNone(event["error"])

    def test_redirects_are_not_followed(self):
        self.assertIsNone(api.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.org"))

    def test_run_bounded_pagination_and_no_overwrite(self):
        calls = []

        def request(url, params, timeout):
            calls.append((url, params))
            event = {"requested_at_utc": datetime.now(timezone.utc).isoformat(),
                     "received_at_utc": datetime.now(timezone.utc).isoformat(), "error": None}
            if url == api.API:
                return metadata(), event
            stamp = "2026-01-01T00:15:00Z" if params.get("offset", 0) == 0 else "2026-01-01T00:00:00Z"
            return {"total_count": 2, "results": [row(stamp)]}, event

        with tempfile.TemporaryDirectory() as directory, patch.object(api, "request_json", side_effect=request):
            first, result = api.run(directory, pages=2, page_size=1)
            original = first.read_bytes()
            second, _ = api.run(directory, pages=1, page_size=1)
            self.assertNotEqual(first.parent, second.parent)
            self.assertEqual(first.read_bytes(), original)
            self.assertEqual(result["status"], "complete_sample")
            self.assertEqual(len(result["requests"]), 4)
            self.assertEqual([calls[i][1]["offset"] for i in (1, 2)], [0, 1])
            self.assertIn("where", calls[1][1])

    def test_network_failure_saved_and_no_further_request(self):
        event = {"error": "synthetic-network", "received_at_utc": "2026-01-01T00:00:00Z"}
        with tempfile.TemporaryDirectory() as directory, patch.object(api, "request_json", return_value=(None, event)) as request:
            path, result = api.run(directory)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["pages"], [])

    def test_limits_and_project_data_output_forbidden(self):
        with tempfile.TemporaryDirectory() as directory:
            for kwargs in ({"pages": 3}, {"page_size": 101}, {"timeout": 0}):
                with self.assertRaises(ValueError):
                    api.run(directory, **kwargs)
        with self.assertRaises(ValueError):
            api.run(Path(api.__file__).resolve().parents[2] / "data/raw/exploratory")

    def test_empty_sample_is_not_success(self):
        def request(url, params, timeout):
            event = {"error": None, "received_at_utc": "2026-01-01T00:00:00Z"}
            return (metadata() if url == api.API else {"total_count": 0, "results": []}), event

        with tempfile.TemporaryDirectory() as directory, patch.object(api, "request_json", side_effect=request):
            _, result = api.run(directory)
            self.assertEqual(result["status"], "empty_sample")
            self.assertNotIn("combined_sample_audit", result)


if __name__ == "__main__":
    unittest.main()
