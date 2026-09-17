#!/usr/bin/env python3
"""test_programme_intelligence.py — Contract tests for AntiGravity Programme Intelligence System.

Guards the system operating model, 10 drift dimensions, the 4 future success tests,
and sequenced programme charters.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestProgrammeIntelligenceContract(unittest.TestCase):
    """Guards the Programme Intelligence System specification and audit tool."""

    def test_spec_exists_and_covers_mandate(self):
        spec_path = REPO_ROOT / "docs" / "PROGRAMME_INTELLIGENCE.md"
        self.assertTrue(spec_path.is_file(), "docs/PROGRAMME_INTELLIGENCE.md missing")
        content = spec_path.read_text(encoding="utf-8")

        required_phrases = [
            "AntiGravity",
            "Programme Intelligence System",
            "Published Artifacts Are Truth",
            "Registry Reflects Reality",
            "Contracts Define Reality",
            "Consumers Trust Contracts",
            "Nothing Trusts Assumptions",
            "Ten Invariants of Architectural Integrity",
            "Phase D1 — Project Doctor",
            "Phase A1 — Project Snapdragon",
            "Phase R1 — Project Genesis",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, content, f"Missing required specification phrase: '{phrase}'")

    def test_four_future_success_tests_codified(self):
        """Verifies the four durability guarantees that ensure project longevity."""
        spec_path = REPO_ROOT / "docs" / "PROGRAMME_INTELLIGENCE.md"
        content = spec_path.read_text(encoding="utf-8")

        durability_clauses = [
            "If GitHub changes, Emberbird continues",
            "If builders change, Emberbird continues",
            "If maintainers change, Emberbird continues",
            "If distribution channels change, Emberbird continues",
        ]
        for clause in durability_clauses:
            self.assertIn(clause, content, f"Missing durability guarantee: '{clause}'")

    def test_programme_board_integrates_chartered_phases(self):
        """Verifies that the G4 Programme Control Board tracks the chartered programmes."""
        board_path = REPO_ROOT / "docs" / "programme-board.md"
        self.assertTrue(board_path.is_file(), "docs/programme-board.md missing")
        content = board_path.read_text(encoding="utf-8")

        self.assertIn("Phase D1 (Project Doctor)", content)
        self.assertIn("Phase A1 (Project Snapdragon)", content)
        self.assertIn("Phase R1 (Project Genesis)", content)

    def test_audit_cli_passes_ten_of_ten(self):
        """Executes the Programme Intelligence Auditor and asserts 10.0 / 10 score."""
        audit_script = REPO_ROOT / "scripts" / "programme_intelligence.py"
        self.assertTrue(audit_script.is_file(), "scripts/programme_intelligence.py missing")

        res = subprocess.run(
            [sys.executable, str(audit_script), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(res.returncode, 0, f"Programme Intelligence Auditor failed:\n{res.stderr or res.stdout}")

        report = json.loads(res.stdout)
        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["health_score"], 10.0)
        self.assertEqual(report["dimensions_passed"], 10)
        self.assertEqual(report["dimensions_total"], 10)
        self.assertEqual(len(report["dimensions"]), 10)

        for dim in report["dimensions"]:
            self.assertEqual(dim["status"], "PASS", f"Dimension {dim['name']} did not PASS: {dim['details']}")
            self.assertEqual(dim["score"], 10.0, f"Dimension {dim['name']} score < 10.0")


if __name__ == "__main__":
    unittest.main()
