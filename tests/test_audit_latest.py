"""Cas synthétiques pour le contrôle minimal du dernier timestamp ; sans réseau."""

from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.faisabilite_application import audit_latest as audit


def responses(stamp="2026-11-06T12:00:00Z", maximum=None, count=4):
    row = {"date_heure": stamp, "date": "2026-11-06", "heure": "13:00",
           "consommation": 50000, "nature": "Synthétique", "perimetre": "France"}
    return ({"total_count": 4, "results": [row]},
            {"total_count": 1, "results": [{"last_timestamp": maximum or stamp, "eligible_count": count}]})


class LatestAuditTests(unittest.TestCase):
    def compare(self, pair):
        return audit.compare_responses(*pair, "2026-11-06T13:00:01Z", "2026-11-06T13:00:00Z")

    def test_queries_same_filter_no_offset_and_limit_one(self):
        first, second = audit.build_queries("2026-11-06T14:00:00+01:00")
        self.assertEqual(first["where"], second["where"])
        self.assertIn("consommation is not null", first["where"])
        self.assertIn("2026-11-06T13:00:00+00:00", first["where"])
        self.assertEqual(first["order_by"], "date_heure desc")
        self.assertIn("max(date_heure)", second["select"])
        for query in (first, second):
            self.assertEqual(query["limit"], 1)
            self.assertNotIn("offset", query)

    def test_matching_time_count_and_age(self):
        result = self.compare(responses())
        self.assertEqual(result["status"], "consistent_evidence")
        self.assertEqual(result["observation_age_seconds"], 3601)
        self.assertFalse(result["publication_delay_proven"])

    def test_time_mismatch(self):
        self.assertEqual(self.compare(responses(maximum="2026-11-06T12:15:00Z"))["status"], "inconsistent")

    def test_count_mismatch(self):
        self.assertEqual(self.compare(responses(count=5))["status"], "inconsistent")

    def test_future_or_naive_timestamp_rejected(self):
        for stamp in ("2026-11-06T13:15:00Z", "2026-11-06T12:00:00"):
            with self.assertRaises(ValueError):
                self.compare(responses(stamp))

    def test_invalid_or_null_power_rejected(self):
        for value in (None, True, 0, -1, float("nan")):
            first, second = responses()
            first["results"][0]["consommation"] = value
            with self.assertRaises(ValueError):
                self.compare((first, second))

    def test_control_schema_rejected(self):
        first, _ = responses()
        for second in ({}, {"total_count": 1, "results": [{}]}):
            with self.assertRaises(ValueError):
                self.compare((first, second))

    def test_empty_consistent(self):
        first = {"total_count": 0, "results": []}
        control = {"total_count": 1, "results": [{"last_timestamp": None, "eligible_count": 0}]}
        self.assertEqual(self.compare((first, control))["status"], "empty")

    def test_plan_does_not_write_or_request(self):
        with patch.object(audit, "request_json") as request, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(audit.main([]), 0)
        request.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["mode"], "plan_only")

    def test_execution_bounded_and_exclusive(self):
        first, second = responses()
        event = {"received_at_utc": "2026-11-06T13:00:01Z", "error": None}
        with tempfile.TemporaryDirectory() as folder, patch.object(audit, "request_json", side_effect=[(first, event), (second, event)]) as request, patch.object(audit, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 11, 6, 13, tzinfo=timezone.utc)
            path, result = audit.execute(folder)
            self.assertEqual(request.call_count, 2)
            self.assertEqual(result["status"], "consistent_evidence")
            original = path.read_bytes()
            with patch.object(audit, "request_json", return_value=(None, {"error": "synthetic"})):
                other, failed = audit.execute(folder)
            self.assertNotEqual(path.parent, other.parent)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(failed["status"], "incomplete")
            self.assertEqual(len(failed["requests"]), 1)


if __name__ == "__main__":
    unittest.main()
