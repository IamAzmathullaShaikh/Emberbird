#!/usr/bin/env python3
"""test_build_release_candidates.py — Unit tests for Release Candidate Builder (Epic PR1, Task PR1.1)."""

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


class TestBuildReleaseCandidates(unittest.TestCase):
    def test_build_all_candidates_generates_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            candidates = brc.build_all_candidates(
                targets=["all"],
                output_base=out_dir,
                wsa_version="2407.40000.4.0",
                manager_version="0.2.2",
                force_mock=True,
            )
            self.assertEqual(len(candidates), 4)
            manifest_file = out_dir / "release-candidate-manifest.json"
            self.assertTrue(manifest_file.is_file())

            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["total_candidates"], 4)
            targets = [c["target"] for c in manifest["candidates"]]
            self.assertEqual(sorted(targets), ["arm64", "banking", "manager", "standard"])

    def test_standard_candidate_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            entry = brc.build_wsa_candidate(
                output_base=out_dir,
                target="standard",
                edition="standard",
                version="2407.40000.4.0",
                arch="x64",
                force_mock=True,
            )
            pkg_dir = out_dir / entry.directory
            self.assertTrue(pkg_dir.is_dir())
            self.assertTrue((pkg_dir / "AppxManifest.xml").is_file())
            self.assertTrue((pkg_dir / "Install.ps1").is_file())
            self.assertTrue((pkg_dir / "Run.bat").is_file())
            self.assertTrue((pkg_dir / "Tools" / "initrd.img").is_file())

    def test_banking_candidate_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            entry = brc.build_wsa_candidate(
                output_base=out_dir,
                target="banking",
                edition="banking",
                version="2407.40000.4.0",
                arch="x64",
                force_mock=True,
            )
            pkg_dir = out_dir / entry.directory
            self.assertTrue(pkg_dir.is_dir())
            self.assertIn("vanilla", pkg_dir.name)
            initrd = (pkg_dir / "Tools" / "initrd.img").read_bytes()
            self.assertIn(b"CLEAN_BOOT_IMG_HEADER", initrd)

    def test_cli_execution_manager_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "build_release_candidates.py"),
                "--target", "manager",
                "--output-dir", tmpdir,
                "--manager-version", "0.2.2",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

            manifest_file = Path(tmpdir) / "release-candidate-manifest.json"
            self.assertTrue(manifest_file.is_file())
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest["total_candidates"], 1)
            self.assertEqual(manifest["candidates"][0]["target"], "manager")


if __name__ == "__main__":
    unittest.main()
