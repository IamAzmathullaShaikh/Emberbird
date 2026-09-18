#!/usr/bin/env python3
"""test_compatibility_report.py — Unit tests for Compatibility Operations & Scoring (Epic PR4, Task PR4.3)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import generate_compatibility_report as gcr  # noqa: E402


class TestCompatibilityReport(unittest.TestCase):
    def test_generate_compatibility_report_structure(self):
        report = gcr.generate_compatibility_report()
        self.assertIsInstance(report, gcr.CompatibilityReport)
        self.assertEqual(report.total_apps_tested, 11)
        self.assertGreater(report.overall_compatibility_score, 80.0)
        self.assertGreater(report.play_integrity_rate, 50.0)

        # Ensure categories exist
        cats = [cs.category for cs in report.category_scores]
        self.assertIn("Banking & UPI", cats)
        self.assertIn("Communication", cats)
        self.assertIn("Streaming & Media", cats)
        self.assertIn("Utilities & Tools", cats)

        # Ensure edition recommendations exist
        self.assertIn("standard_edition", report.edition_recommendations)
        self.assertIn("banking_edition", report.edition_recommendations)
        self.assertIn("arm64_guidance", report.edition_recommendations)

    def test_markdown_formatting(self):
        report = gcr.generate_compatibility_report()
        md = gcr.format_markdown_report(report)
        self.assertIn("# Emberbird Application Compatibility Operations Report", md)
        self.assertIn("| Category | Apps Tested | Working | Workaround | Broken | Compatibility Score |", md)
        self.assertIn("Standard Edition", md)
        self.assertIn("Banking Edition", md)

    def test_cli_execution_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "generate_compatibility_report.py"),
                "--output-dir", str(out_dir),
                "--json",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

            data = json.loads(res.stdout)
            self.assertEqual(data["total_apps_tested"], 11)
            self.assertTrue((out_dir / "compatibility-report.json").is_file())


if __name__ == "__main__":
    unittest.main()
