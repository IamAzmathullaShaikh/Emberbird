#!/usr/bin/env python3
"""test_distribution_manifests.py — Unit tests for Multi-Target Manifest Generator (Phase P7)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "scripts"
sys.path.insert(0, str(sys_path))

import generate_package_manifests as gpm  # noqa: E402


class TestPackageManifestGenerator(unittest.TestCase):
    def test_load_manager_release_assets_valid_version(self):
        assets = gpm.load_manager_release_assets("0.2.2")
        self.assertEqual(assets["version"], "0.2.2")
        self.assertTrue(assets["exe"]["filename"].endswith(".exe"))
        self.assertTrue(assets["zip"]["filename"].endswith(".zip"))
        self.assertEqual(len(assets["exe"]["sha256"]), 64)
        self.assertEqual(len(assets["zip"]["sha256"]), 64)

    def test_generate_scoop_manifest_structure(self):
        assets = gpm.load_manager_release_assets("0.2.2")
        scoop_manifest = gpm.generate_scoop_manifest(assets)
        self.assertEqual(scoop_manifest["version"], "0.2.2")
        self.assertEqual(scoop_manifest["license"], "AGPL-3.0")
        self.assertEqual(scoop_manifest["bin"], "EmberbirdManager.exe")
        self.assertEqual(scoop_manifest["hash"], assets["zip"]["sha256"])

    def test_generate_chocolatey_nuspec_structure(self):
        assets = gpm.load_manager_release_assets("0.2.2")
        nuspec = gpm.generate_chocolatey_nuspec(assets)
        self.assertIn("<id>emberbird-manager</id>", nuspec)
        self.assertIn("<version>0.2.2</version>", nuspec)
        self.assertIn("https://www.gnu.org/licenses/agpl-3.0.html", nuspec)

    def test_generate_winget_manifests(self):
        assets = gpm.load_manager_release_assets("0.2.2")
        version_yaml = gpm.generate_winget_root_manifest("Emberbird.Manager", "0.2.2")
        self.assertIn("PackageIdentifier: Emberbird.Manager", version_yaml)
        self.assertIn("PackageVersion: 0.2.2", version_yaml)

        installer_yaml = gpm.generate_winget_installer_manifest("Emberbird.Manager", "0.2.2", assets)
        self.assertIn("PackageIdentifier: Emberbird.Manager", installer_yaml)
        self.assertIn(assets["exe"]["sha256"].upper(), installer_yaml)
        self.assertIn(assets["zip"]["sha256"].upper(), installer_yaml)

    def test_generate_winget_default_locale_manifest(self):
        locale_yaml = gpm.generate_winget_default_locale_manifest("Emberbird.Manager", "0.2.2")
        self.assertIn("PackageIdentifier: Emberbird.Manager", locale_yaml)
        self.assertIn("PackageVersion: 0.2.2", locale_yaml)
        self.assertIn("PackageLocale: en-US", locale_yaml)
        self.assertIn("ManifestType: defaultLocale", locale_yaml)
        self.assertIn("License: AGPL-3.0", locale_yaml)

    def test_generate_portable_manifest(self):
        assets = gpm.load_manager_release_assets("0.2.2")
        portable = gpm.generate_portable_manifest(assets)
        self.assertEqual(portable["package_id"], "Emberbird.Manager.Portable")
        self.assertEqual(portable["version"], "0.2.2")
        self.assertEqual(portable["entrypoint"], "EmberbirdManager.exe")
        self.assertEqual(portable["sha256"], assets["zip"]["sha256"])
        self.assertEqual(portable["download_url"], assets["zip"]["source_url"])
        self.assertEqual(portable["license"], "AGPL-3.0")

    def test_cli_write_all_targets_to_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir)
            cmd = [
                sys.executable,
                str(REPO_ROOT / "scripts" / "generate_package_manifests.py"),
                "--version", "0.2.2",
                "--output-dir", str(out_path),
                "--target", "all",
                "--write",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")

            # Check all generated files
            self.assertTrue((out_path / "emberbird-manager.json").is_file())
            self.assertTrue((out_path / "emberbird-manager.nuspec").is_file())
            self.assertTrue((out_path / "emberbird-manager-portable.json").is_file())

            w_dir = out_path / "winget" / "0.2.2"
            self.assertTrue((w_dir / "Emberbird.Manager.yaml").is_file())
            self.assertTrue((w_dir / "Emberbird.Manager.installer.yaml").is_file())
            self.assertTrue((w_dir / "Emberbird.Manager.locale.en-US.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
