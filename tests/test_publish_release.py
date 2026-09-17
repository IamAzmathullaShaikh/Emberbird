#!/usr/bin/env python3
"""test_publish_release.py — Unit tests for Release Publication Flow (Epic PR1, Task PR1.3).

Fixtures are genuine-shaped artifacts (real PE / ZIP / 7z containers) because the
Publication Integrity Gate refuses fabricated bytes. A separate case pins the
refusal itself, so a scaffold build can never be registered as a release.

stdlib-only; runs in CI unchanged.
"""

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
sys.path.insert(0, str(REPO_ROOT / "tests"))

import publish_release as pub  # noqa: E402
from release_fixtures import (  # noqa: E402
    relaxed_floors,
    write_7z,
    write_pe,
    write_zip,
)


class TestPublishRelease(unittest.TestCase):
    def setUp(self):
        self.registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        self.schema_path = REPO_ROOT / "data" / "releases" / "releases.schema.json"

    def test_build_release_entry_subsystem(self):
        with tempfile.TemporaryDirectory() as tmpdir, relaxed_floors():
            dist_dir = Path(tmpdir)
            archive = write_7z(dist_dir / "WSA_2407.40000.4.0_x64.7z")
            expected_hash = hashlib.sha256(archive.read_bytes()).hexdigest()

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
            self.assertEqual(entry["assets"][0]["sha256"], expected_hash)
            self.assertEqual(entry["assets"][0]["size_bytes"], archive.stat().st_size)
            self.assertEqual(len(entry["validation_reports"]), 5)

    def test_build_release_entry_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir, relaxed_floors():
            dist_dir = Path(tmpdir)
            write_pe(dist_dir / "EmberbirdManager-Setup-0.2.3-x64.exe")
            write_zip(dist_dir / "EmberbirdManager-Portable-0.2.3-x64.zip")

            entry = pub.build_release_entry(dist_dir=dist_dir)

            self.assertEqual(entry["kind"], "manager")
            self.assertEqual(entry["edition"], "manager")
            self.assertEqual(entry["channel"], "stable")
            self.assertEqual(entry["tag"], "v0.2.3")
            self.assertEqual(entry["release_id"], "manager-0.2.3")
            self.assertEqual(entry["architectures"], ["x64"])
            self.assertEqual(len(entry["assets"]), 2)
            filenames = [a["filename"] for a in entry["assets"]]
            self.assertIn("EmberbirdManager-Setup-0.2.3-x64.exe", filenames)
            self.assertIn("EmberbirdManager-Portable-0.2.3-x64.zip", filenames)

    def test_new_publication_uses_the_canonical_repo_slug(self):
        with tempfile.TemporaryDirectory() as tmpdir, relaxed_floors():
            dist_dir = Path(tmpdir)
            write_zip(dist_dir / "EmberbirdManager-Portable-0.2.3-x64.zip")

            entry = pub.build_release_entry(dist_dir=dist_dir)

            for asset in entry["assets"]:
                self.assertIn(
                    "https://github.com/IamAzmathullaShaikh/Emberbird/releases/download/",
                    asset["source_url"],
                )
                self.assertEqual(asset["hash_source"], "computed")

    def test_scaffold_artifacts_are_refused(self):
        with tempfile.TemporaryDirectory() as tmpdir, relaxed_floors():
            dist_dir = Path(tmpdir)
            (dist_dir / "EmberbirdManager-Setup-0.2.3-x64.exe").write_bytes(
                b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.3"
            )
            (dist_dir / "EmberbirdManager-Portable-0.2.3-x64.zip").write_bytes(
                b"PK_EMBERBIRD_MANAGER_DESKTOP_PORTABLE_ZIP_PAYLOAD_V0.2.3"
            )

            with self.assertRaises(ValueError) as ctx:
                pub.build_release_entry(dist_dir=dist_dir)
            message = str(ctx.exception)
            self.assertIn("Publication Integrity Gate FAILED", message)
            self.assertIn("PLACEHOLDER", message)

    def test_prepare_publication_dry_run_preserves_registry(self):
        with tempfile.TemporaryDirectory() as tmpdir, relaxed_floors():
            dist_dir = Path(tmpdir)
            write_7z(dist_dir / "WSA_2407.40000.4.0_x64.7z")

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
        with tempfile.TemporaryDirectory() as dist_tmp, tempfile.TemporaryDirectory() as reg_tmp, relaxed_floors():
            dist_dir = Path(dist_tmp)
            temp_reg_file = Path(reg_tmp) / "releases.json"
            shutil.copy2(self.registry_path, temp_reg_file)

            write_7z(dist_dir / "WSA_2407.40000.4.0_x64_vanilla.7z")

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
        """The CLI end-to-end path runs against a genuine 1 MiB-class artifact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            # Manager artifacts carry the smallest real floor (1 MiB), so the CLI
            # can be exercised end-to-end without relaxing anything.
            write_pe(
                dist_dir / "EmberbirdManager-Setup-0.2.3-x64.exe",
                size=1 << 20,
            )

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

    def test_cli_refuses_scaffold_artifacts(self):
        """The publication CLI must fail loudly rather than register stubs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir)
            (dist_dir / "EmberbirdManager-Setup-0.2.3-x64.exe").write_bytes(
                b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V0.2.3"
            )

            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "publish_release.py"),
                "--dist-dir", str(dist_dir),
                "--registry-path", str(self.registry_path),
                "--schema-path", str(self.schema_path),
                "--dry-run",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("Publication Integrity Gate", res.stdout + res.stderr)

    def test_end_to_end_pr1_pipeline(self):
        """Verify full PR1 pipeline with genuine artifacts: Package -> Publication."""
        import package_release as pr

        with tempfile.TemporaryDirectory() as staging_tmp, tempfile.TemporaryDirectory() as dist_tmp, relaxed_floors():
            staging_dir = Path(staging_tmp)
            dist_dir = Path(dist_tmp)

            # 1. Genuine staged candidate (a real toolchain produces this in CI)
            from release_fixtures import stage_standard_candidate

            stage_standard_candidate(staging_dir)

            # 2. Release Packager (PR1.2)
            artifacts, meta = pr.package_release_candidates(
                input_dir=staging_dir,
                output_dir=dist_dir,
                format_choice="zip",
                version="2407.40000.4.0",
                release_id="wsa-2311-standard",
            )
            self.assertGreaterEqual(len(artifacts), 1)
            self.assertEqual(meta["validation_status"], "VERIFIED")

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
