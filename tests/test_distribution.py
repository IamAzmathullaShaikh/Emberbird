import json
import re
import unittest
from pathlib import Path

from scripts.validate_distribution import (
    REPO_ROOT,
    validate_version_json,
    validate_version_consistency,
    validate_winget_manifests,
    is_valid_installer_name,
    is_valid_portable_name,
    is_valid_checksum_name,
)


class TestDistributionAndWinget(unittest.TestCase):
    def setUp(self):
        self.repo_root = REPO_ROOT
        self.version_file = self.repo_root / "deployment" / "version.json"

    def test_version_metadata_parsing(self):
        """Verify deployment/version.json parses and adheres to schema requirements."""
        self.assertTrue(self.version_file.exists(), "deployment/version.json must exist")
        data = validate_version_json(self.version_file)

        mgr = data["manager"]
        self.assertEqual(mgr["winget_package_id"], "WSABuilds.WSABuildsManager")
        self.assertIn(mgr["channel"], ["stable", "beta", "nightly"])
        self.assertTrue(len(mgr["target_architectures"]) >= 2)
        self.assertIn("x64", mgr["target_architectures"])
        self.assertIn("arm64", mgr["target_architectures"])

    def test_version_synchronization(self):
        """Verify version consistency across version.json, Cargo.toml, package.json, and tauri.conf.json."""
        data = validate_version_json(self.version_file)
        target_version = data["manager"]["version"]

        errors = validate_version_consistency(self.repo_root, target_version)
        self.assertEqual(
            errors,
            [],
            f"Version synchronization errors detected: {errors}",
        )

    def test_winget_manifests_integrity(self):
        """Verify Winget manifests match schema version 1.6.0 and package ID."""
        data = validate_version_json(self.version_file)
        target_version = data["manager"]["version"]
        package_id = data["manager"]["winget_package_id"]

        errors = validate_winget_manifests(self.repo_root, package_id, target_version)
        self.assertEqual(
            errors,
            [],
            f"Winget manifest validation errors detected: {errors}",
        )

    def test_artifact_naming_regex(self):
        """Verify naming grammar for installers, portable archives, and checksum files."""
        v = "0.2.0"

        # Valid names
        self.assertTrue(is_valid_installer_name(f"WSABuildsManager-Setup-{v}-x64.exe", v, "x64"))
        self.assertTrue(is_valid_installer_name(f"WSABuildsManager-Setup-{v}-arm64.exe", v, "arm64"))
        self.assertTrue(is_valid_portable_name(f"WSABuildsManager-Portable-{v}-x64.zip", v, "x64"))
        self.assertTrue(is_valid_portable_name(f"WSABuildsManager-Portable-{v}-arm64.zip", v, "arm64"))
        self.assertTrue(is_valid_checksum_name(f"WSABuildsManager-{v}-checksums.txt", v))

        # Invalid names
        self.assertFalse(is_valid_installer_name("WSABuildsManager-x64.exe"))
        self.assertFalse(is_valid_installer_name(f"WSABuildsManager-Setup-{v}-mips.exe"))
        self.assertFalse(is_valid_portable_name("Setup.zip"))
        self.assertFalse(is_valid_checksum_name(f"WSABuildsManager-{v}-sha256.txt"))

    def test_wsa_release_artifact_naming_regex(self):
        """Verify naming grammar for both Standard Edition (Magisk) and Banking Edition (Vanilla)."""
        wsa_pattern = re.compile(
            r"^WSA_(?P<version>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)_(?P<arch>x64|arm64)_Release-(with-magisk-[a-f0-9]+-stable|vanilla)-GApps-13\.0-(pico|none)\.7z$"
        )

        standard_sample = "WSA_2311.40000.5.0_x64_Release-with-magisk-26404-stable-GApps-13.0-pico.7z"
        vanilla_sample = "WSA_2311.40000.5.0_x64_Release-vanilla-GApps-13.0-pico.7z"

        self.assertTrue(wsa_pattern.match(standard_sample), f"Standard sample should match: {standard_sample}")
        self.assertTrue(wsa_pattern.match(vanilla_sample), f"Vanilla sample should match: {vanilla_sample}")

        # Invalid variants
        self.assertFalse(wsa_pattern.match("WSA_2311.40000.5.0_x64_Release.7z"))
        self.assertFalse(wsa_pattern.match("WSA_2311.40000.5.0_x64_Release-with-magisk-canary.7z"))


if __name__ == "__main__":
    unittest.main()
