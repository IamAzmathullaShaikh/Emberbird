#!/usr/bin/env python3
"""test_live_release_validation.py — Unit tests for Live Release Validation (Epic PR2)."""

import copy
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

import validate_live_release as vlr  # noqa: E402


class TestLiveReleaseValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        cls.registry_data = json.loads(cls.registry_path.read_text(encoding="utf-8"))

    def test_pr21_validate_release_assets_real_registry(self):
        res = vlr.validate_release_assets(self.registry_data)
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)
        self.assertGreaterEqual(res.findings["total_assets"], 9)

    def test_pr21_validate_release_assets_detects_bad_hash(self):
        corrupt = copy.deepcopy(self.registry_data)
        corrupt["releases"][0]["assets"][0]["sha256"] = "0" * 64
        res = vlr.validate_release_assets(corrupt)
        self.assertEqual(res.status, "FAIL")
        self.assertTrue(any("Invalid SHA-256" in e for e in res.errors))

    def test_pr22_validate_downloads_real_registry(self):
        res = vlr.validate_downloads(self.registry_data)
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)
        self.assertGreaterEqual(res.findings["total_download_vectors"], 9)

    def test_pr22_validate_downloads_detects_insecure_url(self):
        corrupt = copy.deepcopy(self.registry_data)
        corrupt["releases"][0]["assets"][0]["source_url"] = "http://insecure.url/file.zip"
        res = vlr.validate_downloads(corrupt)
        self.assertEqual(res.status, "FAIL")
        self.assertTrue(any("Non-HTTPS" in e for e in res.errors))

    def test_pr23_validate_distribution_manifests(self):
        res = vlr.validate_distribution_manifests(self.registry_data)
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(res.findings["manager_version"], "0.2.2")

    def test_pr24_validate_registry_consistency_real_registry(self):
        res = vlr.validate_registry_consistency(self.registry_data)
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)
        self.assertEqual(len(res.findings["orphan_assets"]), 0)
        self.assertEqual(len(res.findings["orphan_vault"]), 0)

    def test_pr24_validate_registry_consistency_detects_orphans(self):
        corrupt = copy.deepcopy(self.registry_data)
        # Add an asset without corresponding vault entry
        corrupt["releases"][0]["assets"].append({
            "filename": "WSA_Orphan_Package.7z",
            "sha256": "a" * 64,
            "arch": "x64",
            "role": "package",
            "source_url": "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v1.0.0/WSA_Orphan_Package.7z",
            "source_type": "derived",
            "hash_source": "published-manifest",
            "verified_at": "2026-09-17T12:00:00Z",
            "size_bytes": 12345,
        })
        res = vlr.validate_registry_consistency(corrupt)
        self.assertEqual(res.status, "FAIL")
        self.assertTrue(any("orphan release assets" in e for e in res.errors))

    def test_pr25_compute_release_health_score(self):
        r_asset = vlr.validate_release_assets(self.registry_data)
        r_download = vlr.validate_downloads(self.registry_data)
        r_dist = vlr.validate_distribution_manifests(self.registry_data)
        r_reg = vlr.validate_registry_consistency(self.registry_data)

        report = vlr.compute_release_health(r_asset, r_download, r_dist, r_reg, [])
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.overall_health_score, 100.0)
        self.assertEqual(report.registry_health_score, 100.0)
        self.assertEqual(report.asset_integrity_score, 100.0)
        self.assertEqual(report.download_health_score, 100.0)
        self.assertEqual(report.distribution_health_score, 100.0)

        md = vlr.format_markdown_health_report(report)
        self.assertIn("# Emberbird Release Health Report", md)
        self.assertIn("100.0 / 100.0", md)

    def test_pr26_validate_website_visibility(self):
        res = vlr.validate_website_visibility()
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)

    def test_pr27_validate_manager_discovery(self):
        res = vlr.validate_manager_discovery()
        self.assertEqual(res.status, "PASS")
        self.assertEqual(res.score, 100.0)
        self.assertEqual(len(res.errors), 0)

    def test_cli_execution_all_checks_pass(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_live_release.py"),
            "--check",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["overall_health_score"], 100.0)


if __name__ == "__main__":
    unittest.main()
