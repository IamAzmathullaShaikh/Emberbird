#!/usr/bin/env python3
"""test_live_installation_validation.py — Unit tests for Live Installation Validation Engine (Epic PR4, Task PR4.2)."""

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

import validate_live_installation as vli  # noqa: E402


class TestLiveInstallationValidation(unittest.TestCase):
    def test_run_live_installation_validation_structure(self):
        report = vli.run_live_installation_validation()
        self.assertIsInstance(report, vli.LiveInstallationReport)
        self.assertIn(report.overall_status, [vli.STATUS_PASS, vli.STATUS_WARN, vli.STATUS_FAIL, vli.STATUS_REQUIRES_VALIDATION])
        self.assertEqual(len(report.components), 9)

        component_names = [c.component for c in report.components]
        expected = ["installation", "launch", "google_signin", "play_store", "adb", "updates", "recovery", "storage_migration", "uninstall"]
        self.assertEqual(component_names, expected)

    def test_honesty_contract_dormant_adb(self):
        """ADB loopback on 58526 must report REQUIRES TARGET ENVIRONMENT VALIDATION when dormant."""
        report = vli.run_live_installation_validation()
        adb_comp = next(c for c in report.components if c.component == "adb")
        # In headless / test runners where adb port 58526 is not connected:
        if not vli.check_port_open("127.0.0.1", 58526):
            self.assertEqual(adb_comp.status, vli.STATUS_REQUIRES_VALIDATION)
            self.assertTrue(any("Honesty contract enforced" in ev for ev in adb_comp.evidence))
            self.assertIsNotNone(adb_comp.remediation)

    def test_markdown_report_formatting(self):
        report = vli.run_live_installation_validation()
        md = vli.format_markdown_report(report)
        self.assertIn("# Emberbird Live Installation Validation Report", md)
        self.assertIn("| Component | Title | Status | Details | Remediation |", md)
        self.assertIn("Standard Edition", md)
        self.assertIn("Banking Edition", md)

    def test_cli_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "validate_live_installation.py"),
                "--output-dir", str(out_dir),
                "--json",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI execution error: {res.stderr}")

            data = json.loads(res.stdout)
            self.assertEqual(len(data["components"]), 9)
            self.assertTrue((out_dir / "live-installation-validation-report.json").is_file())


if __name__ == "__main__":
    unittest.main()
