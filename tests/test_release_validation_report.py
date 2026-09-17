#!/usr/bin/env python3
"""test_release_validation_report.py — Unit tests for Release Validation Report Generator (Epic RO1, Task RO1.2)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import generate_release_validation_report as grvr  # noqa: E402


class TestReleaseValidationReport(unittest.TestCase):
    def test_generate_standard_edition_report(self):
        report = grvr.generate_validation_report("wsa-2311-standard")
        self.assertEqual(report.release_id, "wsa-2311-standard")
        self.assertEqual(report.overall_readiness, grvr.ReadinessStatus.READY)
        self.assertEqual(len(report.gates), 5)
        self.assertTrue(all(g.result == grvr.GateResult.PASS for g in report.gates))
        self.assertTrue(any(k.category == "Root Detection" for k in report.known_issues))
        self.assertTrue(any(k.category == "Disk Space Requirement" for k in report.known_issues))

    def test_generate_banking_edition_report(self):
        report = grvr.generate_validation_report("wsa-2311-banking")
        self.assertEqual(report.release_id, "wsa-2311-banking")
        self.assertEqual(report.edition, "banking")
        self.assertEqual(report.overall_readiness, grvr.ReadinessStatus.READY)
        # Banking edition should NOT flag root detection issue
        self.assertFalse(any(k.category == "Root Detection" for k in report.known_issues))

    def test_generate_manager_report(self):
        report = grvr.generate_validation_report("manager-0.2.2")
        self.assertEqual(report.kind, "manager")
        self.assertEqual(report.overall_readiness, grvr.ReadinessStatus.READY)
        self.assertTrue(len(report.assets) >= 2)

    def test_report_dict_schema(self):
        report = grvr.generate_validation_report("wsa-2311-standard")
        d = report.to_dict()
        self.assertIn("report_id", d)
        self.assertIn("generated_at", d)
        self.assertIn("release_id", d)
        self.assertIn("overall_readiness", d)
        self.assertIn("gates", d)
        self.assertEqual(len(d["gates"]), 5)
        for g in d["gates"]:
            self.assertIn("gate_id", g)
            self.assertIn("name", g)
            self.assertIn("result", g)
            self.assertIn(g["result"], ["PASS", "WARN", "FAIL"])
            self.assertIn("details", g)

    def test_markdown_formatting(self):
        report = grvr.generate_validation_report("wsa-2311-standard")
        md = grvr.format_markdown_validation_report(report)
        self.assertIn("# Release Validation Report", md)
        self.assertIn("wsa-2311-standard", md)
        self.assertIn("Release Readiness Gates", md)
        self.assertIn("Cryptographic Asset Manifest", md)
        self.assertIn("Known Issues", md)

    def test_cli_execution_json(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_release_validation_report.py"),
            "--release-id", "wsa-2311-standard",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["release_id"], "wsa-2311-standard")
        self.assertEqual(data["overall_readiness"], "READY")


if __name__ == "__main__":
    unittest.main()
