#!/usr/bin/env python3
"""test_package_release.py — Unit tests for Release Packager Pipeline (Epic PR1, Task PR1.2)."""

import hashlib
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

import build_release_candidates as brc  # noqa: E402
import package_release as pr  # noqa: E402


class TestPackageRelease(unittest.TestCase):
    def test_package_release_candidates_end_to_end(self):
        with tempfile.TemporaryDirectory() as staging_tmp, tempfile.TemporaryDirectory() as dist_tmp:
            staging_dir = Path(staging_tmp)
            dist_dir = Path(dist_tmp)

            # 1. Build candidates
            candidates = brc.build_all_candidates(
                targets=["standard", "manager"],
                output_base=staging_dir,
                wsa_version="2407.40000.4.0",
                manager_version="0.2.2",
                force_mock=True,
            )
            self.assertEqual(len(candidates), 2)

            # 2. Package candidates (use zip format for universal test environment)
            artifacts, meta = pr.package_release_candidates(
                input_dir=staging_dir,
                output_dir=dist_dir,
                format_choice="zip",
                version="2407.40000.4.0",
                release_id="wsa-2311-standard",
            )

            self.assertGreaterEqual(len(artifacts), 2)
            self.assertEqual(meta["version"], "2407.40000.4.0")
            self.assertEqual(meta["validation_status"], "VERIFIED")

            # Check files created in dist_dir
            self.assertTrue((dist_dir / "checksums.sha256").is_file())
            self.assertTrue((dist_dir / "checksums.sha512").is_file())
            self.assertTrue((dist_dir / "checksums.txt").is_file())
            self.assertTrue((dist_dir / "release-metadata.json").is_file())

            # Verify sha256 checksums file content matches actual artifact hashes
            sha256_lines = (dist_dir / "checksums.sha256").read_text(encoding="utf-8").strip().splitlines()
            for line in sha256_lines:
                expected_hash, filename = line.split("  ")
                file_path = dist_dir / filename
                self.assertTrue(file_path.is_file(), f"Packaged file {filename} should exist")
                computed_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                self.assertEqual(expected_hash, computed_hash)

            # Verify metadata JSON parses and matches artifacts
            meta_json = json.loads((dist_dir / "release-metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(meta_json["total_artifacts"], len(artifacts))
            filenames = [a["filename"] for a in meta_json["artifacts"]]
            self.assertTrue(any(f.startswith("WSA_") and f.endswith(".zip") for f in filenames))
            editions = [a["edition"] for a in meta_json["artifacts"]]
            self.assertIn("standard", editions)

    def test_package_existing_archives(self):
        """Test packager handling when archives already exist in input_dir."""
        with tempfile.TemporaryDirectory() as in_tmp, tempfile.TemporaryDirectory() as out_tmp:
            in_dir = Path(in_tmp)
            out_dir = Path(out_tmp)

            dummy_zip = in_dir / "WSA_2407.40000.4.0_x64_Release-Nightly-GApps-Pico.zip"
            dummy_zip.write_bytes(b"PK\x03\x04testpayloadcontent")

            artifacts, meta = pr.package_release_candidates(
                input_dir=in_dir,
                output_dir=out_dir,
                format_choice="zip",
            )

            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0].filename, dummy_zip.name)
            self.assertEqual(artifacts[0].sha256, hashlib.sha256(b"PK\x03\x04testpayloadcontent").hexdigest())

    def test_cli_package_release(self):
        with tempfile.TemporaryDirectory() as staging_tmp, tempfile.TemporaryDirectory() as dist_tmp:
            staging_dir = Path(staging_tmp)
            dist_dir = Path(dist_tmp)

            brc.build_all_candidates(
                targets=["banking"],
                output_base=staging_dir,
                wsa_version="2407.40000.4.0",
                force_mock=True,
            )

            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "package_release.py"),
                "--input-dir", str(staging_dir),
                "--output-dir", str(dist_dir),
                "--format", "zip",
                "--version", "2407.40000.4.0",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

            meta_file = dist_dir / "release-metadata.json"
            self.assertTrue(meta_file.is_file())
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            self.assertEqual(meta["total_artifacts"], 1)
            self.assertIn("vanilla", meta["artifacts"][0]["filename"].lower())


if __name__ == "__main__":
    unittest.main()
