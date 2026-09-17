#!/usr/bin/env python3
"""test_release_pipeline.py — Unit tests for Continuous Release Pipeline (Epic PR3).

Contract: the continuous release pipeline may not report PASS for a release it
cannot actually make. When candidate staging produces scaffold artifacts (no
build toolchain present), step 3 — registry publication — must refuse, the run
must report FAIL, and no GitHub publish payload may be generated.

stdlib-only; runs in CI unchanged.
"""

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
sys.path.insert(0, str(REPO_ROOT / "tests"))

import release_pipeline as rp  # noqa: E402


class TestReleasePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        cls.schema_path = REPO_ROOT / "data" / "releases" / "releases.schema.json"

    # -- shared assertions ---------------------------------------------------

    def assert_pipeline_refused_fabricated_artifacts(self, summary, dist_path):
        """The pipeline ran, packaged, and then refused to publish stubs."""
        self.assertEqual(summary.status, "FAIL")
        self.assertLess(summary.passed_steps, summary.total_steps)

        step3 = next(s for s in summary.steps if s.step_num == 3)
        self.assertEqual(step3.status, "FAIL")
        self.assertIn("Publication Integrity Gate", step3.error or "")

        # No publish payload may exist for artifacts that are not real builds.
        self.assertFalse((Path(dist_path) / "publish-github.sh").is_file())
        self.assertFalse((Path(dist_path) / "publish-github.bat").is_file())

    def assert_packaging_still_produced_evidence(self, dist_path):
        dist_path = Path(dist_path)
        self.assertTrue((dist_path / "checksums.sha256").is_file())
        self.assertTrue((dist_path / "checksums.txt").is_file())
        metadata = json.loads((dist_path / "release-metadata.json").read_text(encoding="utf-8"))
        self.assertNotEqual(metadata["validation_status"], "VERIFIED")
        return metadata

    # -- tests ---------------------------------------------------------------

    def test_pipeline_refuses_to_publish_scaffold_manager_build(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="manager",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            dist_path = Path(tmp_dist)
            self.assert_packaging_still_produced_evidence(dist_path)
            self.assert_pipeline_refused_fabricated_artifacts(summary, dist_path)

    def test_pipeline_refuses_to_publish_scaffold_banking_build(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="banking",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            self.assert_pipeline_refused_fabricated_artifacts(summary, Path(tmp_dist))

    def test_pipeline_never_commits_scaffold_artifacts_to_the_registry(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist, tempfile.TemporaryDirectory() as tmp_reg:
            temp_reg_file = Path(tmp_reg) / "releases.json"
            shutil.copy2(self.registry_path, temp_reg_file)
            before = temp_reg_file.read_text(encoding="utf-8")

            summary = rp.execute_release_pipeline(
                target="standard",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                registry_path=temp_reg_file,
                schema_path=self.schema_path,
                dry_run=False,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "FAIL")
            # The isolated registry must be byte-identical: nothing was registered.
            self.assertEqual(temp_reg_file.read_text(encoding="utf-8"), before)

    def test_pipeline_target_all_refuses_and_creates_no_publish_payloads(self):
        with tempfile.TemporaryDirectory() as tmp_stg, tempfile.TemporaryDirectory() as tmp_dist:
            summary = rp.execute_release_pipeline(
                target="all",
                staging_dir=Path(tmp_stg),
                dist_dir=Path(tmp_dist),
                dry_run=True,
                skip_website_build=True,
            )

            self.assertEqual(summary.status, "FAIL")
            for sub_t in ["standard", "banking", "arm64", "manager"]:
                sub_dir = Path(tmp_dist) / sub_t
                self.assertTrue((sub_dir / "checksums.sha256").is_file(), f"Missing checksums in {sub_dir}")
                self.assertFalse((sub_dir / "github-release.json").is_file(), f"Unexpected publish payload in {sub_dir}")

    def test_cli_reports_failure_and_nonzero_exit_for_scaffold_build(self):
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "release_pipeline.py"),
            "--target", "manager",
            "--dry-run",
            "--skip-website-build",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)

        # A run that cannot produce publishable artifacts must not exit 0.
        self.assertNotEqual(res.returncode, 0, "pipeline CLI must fail when it cannot publish")

        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "FAIL")
        self.assertLess(data["passed_steps"], data["total_steps"])
        self.assertLess(data["health_score"], 100.0)

        step3 = next(s for s in data["steps"] if s["step_num"] == 3)
        self.assertIn("Publication Integrity Gate", step3["error"])


if __name__ == "__main__":
    unittest.main()
