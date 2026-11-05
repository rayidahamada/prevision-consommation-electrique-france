"""Tests sur observations synthétiques uniquement ; aucune donnée ODRÉ réelle."""

import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.odre_data import ELECTRICITY, audit, download, parse_time, read_records, write_json


def row(stamp, value=100):
    return {"date_heure": stamp, ELECTRICITY: value, "statut_rte": "Synthétique"}


class QualityTests(unittest.TestCase):
    def test_offsets_normalize_same_instant(self):
        self.assertEqual(parse_time("2024-10-27T02:00:00+02:00"),
                         parse_time("2024-10-27T00:00:00Z"))
        self.assertNotEqual(parse_time("2024-10-27T02:00:00+02:00"),
                            parse_time("2024-10-27T02:00:00+01:00"))

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_time("2024-01-01T00:00:00")

    def test_gaps_duplicates_and_missing_electricity(self):
        result = audit([row("2024-01-01T00:00:00Z"), row("2024-01-01T00:00:00Z"),
                        row("2024-01-01T00:30:00Z", None), row("2024-01-01T01:30:00Z")])
        self.assertEqual(result["all_rows_time"]["duplicate_timestamp_excess"], 1)
        self.assertEqual(result["all_rows_time"]["missing_halfhour_slots_between_grid_bounds"], 1)
        self.assertEqual(result["finite_electricity_time"]["missing_halfhour_slots_between_grid_bounds"], 2)
        self.assertEqual(result["missing_by_column"][ELECTRICITY], 1)

    def test_numeric_anomalies_and_no_gas_as_target(self):
        rows = [row("2024-01-01T00:00:00Z", value) for value in (-1, 0, "bad", "NaN", True)]
        rows[0]["consommation_brute_gaz_totale"] = 999999
        result = audit(rows)
        self.assertEqual(result["electricity"]["negative_count"], 1)
        self.assertEqual(result["electricity"]["zero_count"], 1)
        self.assertEqual(result["electricity"]["invalid_numeric_count"], 2)
        self.assertEqual(result["electricity"]["nonfinite_count"], 1)
        self.assertEqual(result["electricity"]["max"], 0)

    def test_invalid_time_offgrid_order_and_empty(self):
        result = audit([row("2024-01-01T01:15:00Z"), row("bad"), row("2024-01-01T00:00:00Z")])
        self.assertEqual(result["invalid_timestamps"], 1)
        self.assertEqual(result["timestamps_off_utc_halfhour_grid"], 1)
        self.assertTrue(result["timestamps_descend_in_file"])
        with self.assertRaises(ValueError):
            audit([])

    def test_json_schema_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.json"
            write_json(path, [row("2024-01-01T00:00:00Z")])
            self.assertEqual(len(read_records(path)), 1)
            with self.assertRaises(FileExistsError):
                write_json(path, [])
            bad = Path(folder) / "bad.json"
            write_json(bad, {"error": "not an export"})
            with self.assertRaises(ValueError):
                read_records(bad)

    def test_network_failure_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / "existing.json"
            old.write_text("unchanged", encoding="utf-8")
            with patch("src.odre_data.urlopen", side_effect=URLError("synthetic failure")):
                with self.assertRaises(RuntimeError):
                    download(folder)
            self.assertEqual(old.read_text(encoding="utf-8"), "unchanged")
            manifests = list(Path(folder).glob("odre_*/manifest.json"))
            self.assertEqual(len(manifests), 1)
            self.assertEqual(json.loads(manifests[0].read_text(encoding="utf-8"))["status"], "incomplete")
            self.assertFalse(list(Path(folder).glob("odre_*/observations.json")))

    def test_successful_acquisition_and_distinct_snapshots(self):
        from src.odre_data import REQUIRED
        metadata = {"fields": [{"name": key} for key in REQUIRED],
                    "metas": {"default": {"license": "Licence Ouverte v2.0 (Etalab)",
                                           "modified": "2024-01-01"}}}

        def response(value):
            stream = io.BytesIO(json.dumps(value).encode())
            stream.headers = {}
            return stream

        with tempfile.TemporaryDirectory() as folder:
            snapshots = []
            for _ in range(2):
                with patch("src.odre_data.urlopen", side_effect=[response(metadata),
                           response([row("2024-01-01T00:00:00Z")])]):
                    snapshots.append(download(folder))
            self.assertNotEqual(*snapshots)
            for snapshot in snapshots:
                manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "complete")
                self.assertEqual(manifest["rows"], 1)
                self.assertEqual(len(manifest["sha256"]), 64)
                self.assertFalse((snapshot / "observations.json.part").exists())

    def test_unverified_license_blocks_export(self):
        from src.odre_data import REQUIRED
        metadata = {"fields": [{"name": key} for key in REQUIRED],
                    "metas": {"default": {"license": "inconnue"}}}
        with tempfile.TemporaryDirectory() as folder:
            with patch("src.odre_data.urlopen", return_value=io.BytesIO(json.dumps(metadata).encode())) as request:
                with self.assertRaises(RuntimeError):
                    download(folder)
                self.assertEqual(request.call_count, 1)
            self.assertFalse(list(Path(folder).glob("odre_*/observations.json")))


if __name__ == "__main__":
    unittest.main()
