#!/usr/bin/env python3
"""test_release_pipeline.py — Unit tests for Continuous Release Pipeline (Epic PR3)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import release_pipeline as rp  # noqa: E402


class TestReleasePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        cls.schema_path = REPO_ROOT / "data" / "releases" / "releases.schema.json"

    def test_pipeline_execution_manager_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="manager",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "PASS")
            self.assertEqual(summary.passed_steps, 7)
            self.assertEqual(summary.total_steps, 7)
            self.assertEqual(summary.health_score, 100.0)

            # Check that artifacts were created
            dist_path = Path(tmp_dist)
            self.assertTrue((dist_path / "checksums.sha256").is_file())
            self.assertTrue((dist_path / "checksums.txt").is_file())
            self.assertTrue((dist_path / "release-metadata.json").is_file())
            self.assertTrue((dist_path / "github-release.json").is_file())

            gh_meta = json.loads((dist_path / "github-release.json").read_text(encoding="utf-8"))
            self.assertIn("v0.2.", gh_meta["tag_name"])

    def test_pipeline_execution_banking_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="banking",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "PASS")
            self.assertEqual(summary.passed_steps, 7)
            self.assertEqual(summary.health_score, 100.0)

            dist_path = Path(tmp_dist)
            gh_meta = json.loads((dist_path / "github-release.json").read_text(encoding="utf-8"))
            self.assertIn("Windows_11_2407", gh_meta["tag_name"])

    def test_pipeline_commit_to_isolated_registry(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist, tempfile.TemporaryDirectory() as tmp_reg:
            temp_reg_file = Path(tmp_reg) / "releases.json"
            shutil.copy2(self.registry_path, temp_reg_file)

            summary = rp.execute_release_pipeline(
                target="standard",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                registry_path=temp_reg_file,
                schema_path=self.schema_path,
                dry_run=False,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "PASS")
            self.assertEqual(summary.passed_steps, 7)

            # Verify saved registry file
            saved_reg = json.loads(temp_reg_file.read_text(encoding="utf-8"))
            saved_ids = [r["release_id"] for r in saved_reg["releases"]]
            self.assertIn("wsa-2407-standard", saved_ids)

    def test_cli_execution_json_flag(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "release_pipeline.py"),
            "--target", "manager",
            "--dry-run",
            "--skip-website-build",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["passed_steps"], 7)
        self.assertEqual(data["total_steps"], 7)
        self.assertEqual(data["health_score"], 100.0)


    def test_pipeline_execution_target_all_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="all",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "PASS")
            self.assertEqual(summary.passed_steps, 7)
            self.assertEqual(summary.total_steps, 7)
            self.assertEqual(summary.health_score, 100.0)

            # Check that target subdirectories exist in dist
            dist_path = Path(tmp_dist)
            for sub_t in ["standard", "banking", "arm64", "manager"]:
                sub_dir = dist_path / sub_t
                self.assertTrue((sub_dir / "checksums.sha256").is_file(), f"Missing checksums in {sub_dir}")
                self.assertTrue((sub_dir / "github-release.json").is_file(), f"Missing gh release in {sub_dir}")


if __name__ == "__main__":
    unittest.main()
