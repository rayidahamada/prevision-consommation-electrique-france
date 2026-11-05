"""Tests synthétiques des hypothèses, sans accès réseau."""

from contextlib import redirect_stdout
import copy
from datetime import timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest

from src.odre_data import parse_time
from src.preparer_electricite import prepare_grid, sha256
from src.preparer_horaire_experimental import common_bounds, make_hour, run
from test_preparer_electricite import source


class HourlyTests(unittest.TestCase):
    def grid(self):
        return list(prepare_grid([source("2024-01-01T00:00:00Z", 100),
                                  source("2024-01-01T00:30:00Z", 200),
                                  source("2024-01-01T01:00:00Z", 400)]))

    def test_start_formula(self):
        result = make_hour(parse_time("2024-01-01T00:00:00Z"), self.grid()[:2], "experimental_start_label")
        self.assertEqual(result["electricity_mw"], 150)
        self.assertTrue(result["target_eligible_strict"] is False)  # statut synthétique inconnu

    def test_end_formula_and_alignment_difference(self):
        grid = self.grid()
        stamp = parse_time(grid[0]["timestamp_utc"])
        a = make_hour(stamp, grid[:2], "experimental_start_label")
        b = make_hour(stamp, grid[1:], "experimental_end_label")
        self.assertEqual(b["electricity_mw"], 300)
        self.assertNotEqual(a["electricity_mw"], b["electricity_mw"])
        self.assertEqual(a["hour_start_utc"], b["hour_start_utc"])
        with self.assertRaises(ValueError):
            make_hour(stamp, grid[:2], "experimental_end_label")

    def test_absent_halfhour_null(self):
        grid = list(prepare_grid([source("2024-01-01T00:00:00Z"), source("2024-01-01T01:00:00Z")]))
        result = make_hour(parse_time(grid[0]["timestamp_utc"]), grid[:2], "experimental_start_label")
        self.assertIsNone(result["electricity_mw"])
        self.assertFalse(result["power_computable"])
        self.assertEqual(result["source_positions"][1], [])

    def test_ambiguous_halfhour_never_averaged(self):
        grid = list(prepare_grid([source("2024-01-01T00:00:00Z", 100),
                                 source("2024-01-01T00:00:00Z", 500),
                                 source("2024-01-01T00:30:00Z", 200)]))
        result = make_hour(parse_time(grid[0]["timestamp_utc"]), grid, "experimental_start_label")
        self.assertIsNone(result["electricity_mw"])
        self.assertEqual(result["source_positions"], [[1, 2], [3]])

    def test_same_power_provenance_and_known_status_strict(self):
        records = [source("2024-01-01T00:00:00Z", 100, "Définitif", "autre"),
                   source("2024-01-01T00:00:00Z", 100, "Définitif", "non"),
                   source("2024-01-01T00:30:00Z", 200, "Définitif", "non")]
        grid = list(prepare_grid(records))
        before = copy.deepcopy(grid)
        result = make_hour(parse_time(grid[0]["timestamp_utc"]), grid, "experimental_start_label")
        self.assertEqual(result["electricity_mw"], 150)
        self.assertTrue(result["target_eligible_strict"])
        self.assertEqual(result["source_positions"], [[1, 2], [3]])
        self.assertEqual(result["source_flags"], [["autre", "non"], ["non"]])
        self.assertEqual(grid, before)

    def test_missing_unknown_and_mixed_statuses(self):
        for first, second in [(None, "Définitif"), ("inconnu", "inconnu"), ("Définitif", "Consolidé")]:
            with self.subTest(first=first, second=second):
                grid = list(prepare_grid([source("2024-01-01T00:00:00Z", status=first),
                                          source("2024-01-01T00:30:00Z", status=second)]))
                result = make_hour(parse_time(grid[0]["timestamp_utc"]), grid, "experimental_start_label")
                self.assertTrue(result["power_computable"])
                self.assertFalse(result["target_eligible_strict"])
                self.assertIsNone(result["strict_electricity_mw"])
                self.assertEqual(result["source_statuses"], [[first], [second]])

    def test_calendar_mismatch_excludes_strict_only(self):
        records = [source("2024-01-01T00:00:00Z", status="Définitif"),
                   source("2024-01-01T00:30:00Z", status="Définitif")]
        records[0]["heure"] = "00:00"
        grid = list(prepare_grid(records))
        result = make_hour(parse_time(grid[0]["timestamp_utc"]), grid, "experimental_start_label")
        self.assertTrue(result["power_computable"])
        self.assertFalse(result["target_eligible_strict"])
        self.assertEqual(result["source_quality"][0]["source_calendar_mismatch_count"], 1)

    def test_spring_and_autumn_local_offsets(self):
        for start in ("2024-03-31T00:00:00Z", "2024-10-27T00:00:00Z"):
            stamp = parse_time(start)
            grid = list(prepare_grid([source((stamp + timedelta(minutes=30*i)).isoformat()) for i in range(4)]))
            a = make_hour(stamp, grid[:2], "experimental_start_label")
            b = make_hour(stamp + timedelta(hours=1), grid[2:], "experimental_start_label")
            self.assertNotEqual(a["hour_start_local"][-6:], b["hour_start_local"][-6:])
            if stamp.month == 10:
                self.assertEqual(a["hour_start_local"][11:16], b["hour_start_local"][11:16])

    def test_common_bounds_do_not_invent_boundary_labels(self):
        first, last = parse_time("2024-01-01T00:30:00Z"), parse_time("2024-01-01T03:30:00Z")
        start, end = common_bounds(first, last)
        self.assertEqual(start.hour, 1)
        self.assertEqual(end.hour, 3)
        with self.assertRaises(ValueError):
            common_bounds(first, first + timedelta(minutes=30))

    def test_end_to_end_csv_integrity_and_no_overwrite(self):
        import csv
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            input_file = base / "grid.jsonl"
            input_file.write_text("".join(json.dumps(r) + "\n" for r in self.grid()), encoding="utf-8")
            digest = sha256(input_file)
            a, b, report = base / "a.csv", base / "b.csv", base / "report.md"
            with redirect_stdout(io.StringIO()):
                info = run(input_file, digest, a, b, report)
            self.assertEqual([r["hours"] for r in info["outputs"]], [1, 1])
            with a.open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(json.loads(row["source_positions"]), [[1], [2]])
            self.assertEqual(sha256(input_file), digest)
            previous = a.read_bytes()
            with self.assertRaises(FileExistsError):
                run(input_file, digest, a, b, report)
            self.assertEqual(a.read_bytes(), previous)
            with self.assertRaises(ValueError):
                run(input_file, "0"*64, base/"new_a.csv", base/"new_b.csv", base/"new.md")
            self.assertFalse((base/"new_a.csv").exists())

    def test_irregular_grid_rejected_before_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            path = base / "input.jsonl"
            rows = self.grid()[::2]
            path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
            with self.assertRaises(ValueError):
                run(path, sha256(path), base/"a.csv", base/"b.csv", base/"report.md")
            self.assertFalse((base/"a.csv").exists())


if __name__ == "__main__":
    unittest.main()
