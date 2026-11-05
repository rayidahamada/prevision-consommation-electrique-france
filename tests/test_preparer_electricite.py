"""Données synthétiques ; aucun accès réseau."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from src.odre_data import ELECTRICITY, audit, parse_time
from src.preparer_electricite import prepare_grid, run, sha256


def source(stamp, power=100, status="Synthétique", flag="non"):
    from zoneinfo import ZoneInfo
    local = parse_time(stamp).astimezone(ZoneInfo("Europe/Paris"))
    return {"date_heure": stamp, "date": local.strftime("%d/%m/%Y"),
            "heure": local.strftime("%H:%M"), ELECTRICITY: power,
            "statut_rte": status, "flag_ignore": flag}


class PreparationTests(unittest.TestCase):
    def test_unique_sorted_with_original_positions(self):
        records = [source("2024-01-01T00:30:00Z", 120), source("2024-01-01T00:00:00Z", 100)]
        before = copy.deepcopy(records)
        result = list(prepare_grid(records))
        self.assertEqual([r["electricity_mw"] for r in result], [100, 120])
        self.assertEqual([r["source_positions"] for r in result], [[2], [1]])
        self.assertTrue(all(r["quality_state"] == "unique" for r in result))
        self.assertEqual(records, before)

    def test_same_power_preserves_different_statuses_and_flags(self):
        records = [source("2024-01-01T00:00:00Z", 100, None, "non"),
                   source("2024-01-01T01:00:00+01:00", 100, "Autre", "inconnu")]
        result = list(prepare_grid(records))[0]
        self.assertEqual(result["electricity_mw"], 100)
        self.assertEqual(result["quality_state"], "duplicate_same_power")
        self.assertEqual(result["source_positions"], [1, 2])
        self.assertEqual(result["statut_rte_sources"], [None, "Autre"])
        self.assertEqual(result["flag_ignore_sources"], ["non", "inconnu"])
        self.assertTrue(result["has_missing_source_status"])

    def test_conflicting_power_never_averaged_or_selected(self):
        result = list(prepare_grid([source("2024-01-01T00:00:00Z", 100),
                                    source("2024-01-01T00:00:00Z", 200)]))[0]
        self.assertIsNone(result["electricity_mw"])
        self.assertEqual(result["quality_state"], "ambiguous")
        self.assertEqual([r[ELECTRICITY] for r in result["source_observations"]], [100, 200])

    def test_missing_slot_has_explicit_null_and_empty_provenance(self):
        result = list(prepare_grid([source("2024-01-01T00:00:00Z"), source("2024-01-01T01:00:00Z")]))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]["quality_state"], "absent")
        self.assertIsNone(result[1]["electricity_mw"])
        self.assertEqual(result[1]["source_positions"], [])
        self.assertEqual(result[1]["statut_rte_sources"], [])
        self.assertFalse(result[1]["has_missing_source_status"])

    def test_spring_dst_local_hour_skipped_without_utc_gap(self):
        result = list(prepare_grid([source("2024-03-31T00:30:00Z"), source("2024-03-31T01:00:00Z")]))
        self.assertEqual([r["local_time"] for r in result], ["01:30", "03:00"])
        self.assertEqual([r["utc_offset_minutes"] for r in result], [60, 120])
        self.assertEqual(len(result), 2)

    def test_autumn_dst_same_local_clock_two_distinct_instants(self):
        result = list(prepare_grid([source("2024-10-27T00:00:00Z"), source("2024-10-27T01:00:00Z")]))
        self.assertEqual(result[0]["local_time"], result[2]["local_time"])
        self.assertEqual([result[i]["local_fold"] for i in (0, 2)], [0, 1])
        self.assertEqual([result[i]["utc_offset_minutes"] for i in (0, 2)], [120, 60])
        self.assertFalse(result[0]["is_duplicate"])

    def test_missing_status_keeps_power_and_null(self):
        result = list(prepare_grid([source("2024-01-01T00:00:00Z", status=None)]))[0]
        self.assertEqual(result["electricity_mw"], 100)
        self.assertEqual(result["statut_rte_sources"], [None])
        self.assertTrue(result["has_missing_source_status"])

    def test_calendar_mismatch_preserves_original(self):
        record = source("2024-03-31T01:00:00Z")
        record["heure"] = "02:00"
        result = list(prepare_grid([record]))[0]
        self.assertEqual(result["source_calendar_mismatch_count"], 1)
        self.assertEqual(result["source_observations"][0]["heure"], "02:00")
        self.assertEqual(result["local_time"], "03:00")

    def test_invalid_inputs_fail_without_implicit_correction(self):
        for records in ([], [source("2024-01-01T00:01:00Z")],
                        [source("2024-01-01T00:00:00Z", True)],
                        [source("2024-01-01T00:00:00Z", float("nan"))]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                list(prepare_grid(records))

    def test_end_to_end_integrity_provenance_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            raw = base / "raw"
            raw.mkdir()
            source_file, manifest, reference = [raw / name for name in ("obs.json", "manifest.json", "audit.json")]
            records = [source("2024-01-01T00:00:00Z"), source("2024-01-01T01:00:00Z")]
            source_file.write_text(json.dumps(records), encoding="utf-8")
            digest = sha256(source_file)
            manifest.write_text(json.dumps({"status": "complete", "sha256": digest, "rows": 2}), encoding="utf-8")
            reference.write_text(json.dumps(dict(audit(records), input_sha256=digest)), encoding="utf-8")
            output, report = base / "processed/table.jsonl", base / "reports/test.md"
            summary = run(source_file, manifest, reference, output, report)
            self.assertEqual(summary["counts"]["expected"], 3)
            self.assertEqual(summary["counts"]["absent"], 1)
            self.assertEqual(sha256(source_file), digest)
            written = output.read_bytes()
            with self.assertRaises(FileExistsError):
                run(source_file, manifest, reference, output, report)
            self.assertEqual(output.read_bytes(), written)
            with self.assertRaises(ValueError):
                run(source_file, manifest, reference, raw / "new.jsonl", base / "new.md")
            source_file.write_text(json.dumps(records + records), encoding="utf-8")
            with self.assertRaises(ValueError):
                run(source_file, manifest, reference, base / "other.jsonl", base / "other.md")
            self.assertFalse((base / "other.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
