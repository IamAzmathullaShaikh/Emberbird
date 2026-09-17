#!/usr/bin/env python3
"""test_release_pipeline_audit.py — Unit tests for Release Pipeline Auditor (Epic RO1, Task RO1.1)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import audit_release_pipeline as arpa  # noqa: E402


class TestReleasePipelineAudit(unittest.TestCase):
    def test_all_six_pathways_audited(self):
        report = arpa.run_pipeline_audit()
        self.assertEqual(report.total_pathways, 6)
        pathway_ids = [p.pathway_id for p in report.pathways]
        expected = ["standard", "banking", "arm64", "manager", "website", "distribution"]
        self.assertEqual(pathway_ids, expected)

    def test_no_pathways_are_blocked(self):
        report = arpa.run_pipeline_audit()
        self.assertEqual(report.blocked_count, 0, f"Blocked pathways found: {[p.name for p in report.pathways if p.status == arpa.PipelineStatus.BLOCKED]}")
        self.assertIn(report.overall_status, (arpa.PipelineStatus.BUILDABLE, arpa.PipelineStatus.PARTIAL))

    def test_report_dict_schema(self):
        report = arpa.run_pipeline_audit()
        d = report.to_dict()
        self.assertIn("generated_at", d)
        self.assertIn("host_os", d)
        self.assertIn("total_pathways", d)
        self.assertEqual(len(d["pathways"]), 6)
        for p in d["pathways"]:
            self.assertIn("pathway_id", p)
            self.assertIn("name", p)
            self.assertIn("target_arch", p)
            self.assertIn("status", p)
            self.assertIn(p["status"], ["BUILDABLE", "PARTIAL", "BLOCKED"])
            self.assertIn("primary_tool", p)
            self.assertIsInstance(p["inputs_required"], list)
            self.assertIsInstance(p["outputs_expected"], list)
            self.assertTrue(len(p["readiness_notes"]) > 0)

    def test_markdown_formatting(self):
        report = arpa.run_pipeline_audit()
        md = arpa.format_markdown_report(report)
        self.assertIn("# Emberbird Release Pipeline Audit Report", md)
        self.assertIn("Standard Edition", md)
        self.assertIn("Banking Edition", md)
        self.assertIn("ARM64 Edition", md)
        self.assertIn("Emberbird Manager", md)
        self.assertIn("Emberbird Web Portal", md)
        self.assertIn("Package Manifests", md)

    def test_cli_execution_json(self):
        cmd = [sys.executable, str(REPO_ROOT / "scripts" / "audit_release_pipeline.py"), "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertEqual(data["total_pathways"], 6)


if __name__ == "__main__":
    unittest.main()
