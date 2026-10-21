import csv
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tools.compare_runs import ComparisonError, compare_runs

DEMO = Path(__file__).resolve().parents[1] / "examples" / "runs_demo.csv"


class CompareRunsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        with DEMO.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            self.fields = reader.fieldnames
            self.rows = list(reader)

    def write(self):
        path = Path(self.temp.name) / "runs.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(self.rows)
        return path

    def assert_error(self, code, **kwargs):
        with self.assertRaises(ComparisonError) as raised:
            compare_runs(self.write(), kwargs.get("project", "P001"),
                         kwargs.get("baseline", "R001"), kwargs.get("candidate", "R002"))
        self.assertEqual(raised.exception.code, code)
        return raised.exception

    def test_min_metric_calculation_and_provenance(self):
        result = compare_runs(DEMO, "P001", "R001", "R002")
        self.assertEqual(Decimal(result["comparison"]["improvement_pct"]), Decimal("10"))
        self.assertEqual(Decimal(result["comparison"]["candidate_minus_baseline"]), Decimal("-0.05"))
        self.assertEqual(result["comparison"]["better_run_id"], "R002")
        self.assertEqual((result["baseline"]["source_line"], result["candidate"]["source_line"]), (2, 3))
        self.assertEqual(len(result["provenance"]["sha256"]), 64)

    def test_protocol_mismatch_is_reported(self):
        error = self.assert_error("INCOMPARABLE_RUNS", candidate="R003")
        self.assertEqual(set(error.details), {"split_id", "protocol_version"})

    def test_other_project_is_rejected(self):
        self.assert_error("PROJECT_MISMATCH", project="P002")

    def test_missing_run_is_rejected(self):
        self.assert_error("RUN_NOT_FOUND", candidate="unknown")

    def test_duplicate_run_is_rejected(self):
        self.rows.append(dict(self.rows[0]))
        self.assert_error("DUPLICATE_RUN")

    def test_nonfinite_metrics_are_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity", "1e9999", "1e-9999", "not-a-number"):
            with self.subTest(value=value):
                self.rows[1]["metric_value"] = value
                self.assert_error("INVALID_METRIC")

    def test_max_metric_and_regression(self):
        for row in self.rows:
            row["optimization"] = "max"
        result = compare_runs(self.write(), "P001", "R001", "R002")
        self.assertEqual(result["comparison"]["outcome"], "regressed")
        self.assertEqual(result["comparison"]["better_run_id"], "R001")
        self.assertEqual(Decimal(result["comparison"]["improvement_pct"]), Decimal("-10"))

    def test_zero_baseline_has_no_relative_percentage(self):
        self.rows[0]["metric_value"] = "0"
        result = compare_runs(self.write(), "P001", "R001", "R002")
        self.assertIsNone(result["comparison"]["improvement_pct"])
        self.assertEqual(result["comparison"]["outcome"], "regressed")

    def test_tie_has_no_better_run(self):
        self.rows[1]["metric_value"] = "0.50"
        result = compare_runs(self.write(), "P001", "R001", "R002")
        self.assertEqual(result["comparison"]["outcome"], "tied")
        self.assertIsNone(result["comparison"]["better_run_id"])

    def test_missing_required_column_is_rejected(self):
        self.fields = [field for field in self.fields if field != "metric_unit"]
        for row in self.rows:
            del row["metric_unit"]
        self.assert_error("INVALID_SCHEMA")

    def test_different_seed_is_not_silently_compared(self):
        self.rows[1]["seed"] = "123"
        self.assert_error("INCOMPARABLE_RUNS")

    def test_same_run_is_rejected(self):
        self.assert_error("SAME_RUN", candidate="R001")

    def test_cli_success_outputs_utf8_json(self):
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "tools.compare_runs", "--csv", str(DEMO),
             "--project", "P001", "--baseline", "R001", "--candidate", "R002"],
            cwd=DEMO.parents[1], capture_output=True, text=True, encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "succeeded")
        self.assertIn("不推断", payload["comparison"]["scope"])

    def test_cli_rejection_returns_exit_code_two(self):
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "tools.compare_runs", "--csv", str(DEMO),
             "--project", "P001", "--baseline", "R001", "--candidate", "R003"],
            cwd=DEMO.parents[1], capture_output=True, text=True, encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["error"]["code"], "INCOMPARABLE_RUNS")


if __name__ == "__main__":
    unittest.main()

