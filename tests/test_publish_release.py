#!/usr/bin/env python3
"""test_publish_release.py — Unit tests for Release Publication Flow (Epic PR1, Task PR1.3)."""

import hashlib
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

import publish_release as pub  # noqa: E402


class TestPublishRelease(unittest.TestCase):
    def setUp(self):
        self.registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        self.schema_path = REPO_ROOT / "data" / "releases" / "releases.schema.json"

    def test_build_release_entry_subsystem(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            archive = dist_dir / "WSA_2407.40000.4.0_x64.7z"
            dummy_data = b"DUMMY_WSA_7Z_PAYLOAD_FOR_TESTING"
            archive.write_bytes(dummy_data)

            entry = pub.build_release_entry(dist_dir=dist_dir)

            self.assertEqual(entry["kind"], "subsystem")
            self.assertEqual(entry["edition"], "standard")
            self.assertEqual(entry["channel"], "retail")
            self.assertEqual(entry["wsa_version"], "2407.40000.4.0")
            self.assertEqual(entry["tag"], "Windows_11_2407.40000.4.0")
            self.assertEqual(entry["release_id"], "wsa-2407-standard")
            self.assertEqual(entry["architectures"], ["x64"])
            self.assertEqual(len(entry["assets"]), 1)
            self.assertEqual(entry["assets"][0]["filename"], "WSA_2407.40000.4.0_x64.7z")
            self.assertEqual(entry["assets"][0]["sha256"], hashlib.sha256(dummy_data).hexdigest())
            self.assertEqual(entry["assets"][0]["size_bytes"], len(dummy_data))
            self.assertEqual(len(entry["validation_reports"]), 5)

    def test_build_release_entry_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            setup_exe = dist_dir / "WSABuildsManager-Setup-0.2.3-x64.exe"
            portable_zip = dist_dir / "WSABuildsManager-Portable-0.2.3-x64.zip"
            setup_exe.write_bytes(b"SETUP_EXE_DATA")
            portable_zip.write_bytes(b"PORTABLE_ZIP_DATA")

            entry = pub.build_release_entry(dist_dir=dist_dir)

            self.assertEqual(entry["kind"], "manager")
            self.assertEqual(entry["edition"], "manager")
            self.assertEqual(entry["channel"], "stable")
            self.assertEqual(entry["tag"], "v0.2.3")
            self.assertEqual(entry["release_id"], "manager-0.2.3")
            self.assertEqual(entry["architectures"], ["x64"])
            self.assertEqual(len(entry["assets"]), 2)
            filenames = [a["filename"] for a in entry["assets"]]
            self.assertIn("WSABuildsManager-Setup-0.2.3-x64.exe", filenames)
            self.assertIn("WSABuildsManager-Portable-0.2.3-x64.zip", filenames)

    def test_prepare_publication_dry_run_preserves_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            archive = dist_dir / "WSA_2407.40000.4.0_x64.7z"
            archive.write_bytes(b"DUMMY_ARCHIVE_DATA")

            orig_registry_text = self.registry_path.read_text(encoding="utf-8")

            entry, registry, pub_manifest = pub.prepare_publication(
                dist_dir=dist_dir,
                registry_path=self.registry_path,
                schema_path=self.schema_path,
                dry_run=True,
            )

            # Registry file on disk must remain strictly untouched during dry-run
            self.assertEqual(self.registry_path.read_text(encoding="utf-8"), orig_registry_text)

            self.assertEqual(pub_manifest["publication_status"], "DRY_RUN_VERIFIED")
            self.assertEqual(pub_manifest["schema_validation"], "PASSED")
            self.assertTrue((dist_dir / "github-release.json").is_file())
            self.assertTrue((dist_dir / "release-publication-manifest.json").is_file())

            gh_meta = json.loads((dist_dir / "github-release.json").read_text(encoding="utf-8"))
            self.assertEqual(gh_meta["tag_name"], "Windows_11_2407.40000.4.0")
            self.assertIn("Emberbird WSA 2407.40000.4.0", gh_meta["name"])

    def test_prepare_publication_commit_to_isolated_registry(self):
        with tempfile.TemporaryDirectory() as dist_tmp, tempfile.TemporaryDirectory() as reg_tmp:
            dist_dir = Path(dist_tmp)
            temp_reg_file = Path(reg_tmp) / "releases.json"
            shutil.copy2(self.registry_path, temp_reg_file)

            archive = dist_dir / "WSA_2407.40000.4.0_x64_vanilla.7z"
            archive.write_bytes(b"DUMMY_VANILLA_ARCHIVE_DATA")

            entry, registry, pub_manifest = pub.prepare_publication(
                dist_dir=dist_dir,
                registry_path=temp_reg_file,
                schema_path=self.schema_path,
                dry_run=False,
            )

            self.assertEqual(pub_manifest["publication_status"], "PUBLISHED")

            # Check that isolated releases.json was actually updated
            saved_reg = json.loads(temp_reg_file.read_text(encoding="utf-8"))
            saved_ids = [r["release_id"] for r in saved_reg["releases"]]
            self.assertIn("wsa-2407-banking", saved_ids)

            # Verify saved registry against schema directly
            sys_release_engine = REPO_ROOT / "platform" / "release-engine"
            if str(sys_release_engine) not in sys.path:
                sys.path.insert(0, str(sys_release_engine))
            from release_engine import validate_against_schema

            schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
            violations = validate_against_schema(saved_reg, schema)
            self.assertEqual(violations, [])

    def test_cli_execution_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            (dist_dir / "WSA_2407.40000.4.0_x64.7z").write_bytes(b"DATA")

            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "publish_release.py"),
                "--dist-dir", str(dist_dir),
                "--registry-path", str(self.registry_path),
                "--schema-path", str(self.schema_path),
                "--dry-run",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
            self.assertIn("Emberbird Release Publication Flow", res.stdout)
            self.assertIn("VALIDATED (0 violations)", res.stdout)

    def test_end_to_end_pr1_pipeline(self):
        """Verify full PR1 pipeline: Candidate Build -> Packaging -> Publication Flow."""
        import build_release_candidates as brc
        import package_release as pr

        with tempfile.TemporaryDirectory() as staging_tmp, tempfile.TemporaryDirectory() as dist_tmp:
            staging_dir = Path(staging_tmp)
            dist_dir = Path(dist_tmp)

            # 1. Candidate Builder (PR1.1)
            candidates = brc.build_all_candidates(
                targets=["standard"],
                output_base=staging_dir,
                wsa_version="2407.40000.4.0",
                force_mock=True,
            )
            self.assertEqual(len(candidates), 1)

            # 2. Release Packager (PR1.2)
            artifacts, meta = pr.package_release_candidates(
                input_dir=staging_dir,
                output_dir=dist_dir,
                format_choice="zip",
                version="2407.40000.4.0",
                release_id="wsa-2311-standard",
            )
            self.assertGreaterEqual(len(artifacts), 1)

            # 3. Release Publication (PR1.3)
            entry, registry, pub_manifest = pub.prepare_publication(
                dist_dir=dist_dir,
                registry_path=self.registry_path,
                schema_path=self.schema_path,
                dry_run=True,
            )

            self.assertEqual(pub_manifest["publication_status"], "DRY_RUN_VERIFIED")
            self.assertEqual(pub_manifest["schema_validation"], "PASSED")
            self.assertEqual(entry["kind"], "subsystem")
            self.assertEqual(entry["edition"], "standard")
            self.assertEqual(len(entry["assets"]), 1)
            self.assertEqual(entry["assets"][0]["sha256"], artifacts[0].sha256)


if __name__ == "__main__":
    unittest.main()
