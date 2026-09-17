import json
import re
import unittest
from pathlib import Path
import yaml

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
        # E5: the active distribution identity is the NEW Emberbird package;
        # the historical WSABuilds.WSABuildsManager manifests stay frozen (M4).
        self.assertEqual(mgr["winget_package_id"], "Emberbird.Manager")
        self.assertEqual(mgr["publisher"], "Emberbird")
        self.assertEqual(mgr["product_name"], "Emberbird Manager")
        # License claims must be truthful: the repository is AGPL-3.0
        # (Legal Compliance Gate — no fabricated Apache-2.0 claims).
        self.assertEqual(mgr["license"], "AGPL-3.0")
        self.assertIn(mgr["channel"], ["stable", "beta", "nightly"])
        # Declared architectures must be real build targets, never aspirational:
        # every architecture here must have an installer manifest with a
        # non-placeholder InstallerSha256 (see test_winget_manifest_structure).
        self.assertGreaterEqual(len(mgr["target_architectures"]), 1)
        self.assertIn("x64", mgr["target_architectures"])
        for arch in mgr["target_architectures"]:
            self.assertIn(arch, ["x64", "arm64", "x86"])

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

    def test_winget_release_prevents_latest_hijacking(self):
        """Verify that winget-release.yml explicitly sets make_latest: false to prevent displacing WSA releases."""
        wf_path = self.repo_root / ".github" / "workflows" / "winget-release.yml"
        self.assertTrue(wf_path.exists(), "winget-release.yml must exist")
        wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))

        jobs = wf.get("jobs", {})
        self.assertIn("publish-manager-release", jobs, "publish-manager-release job must exist")
        steps = jobs["publish-manager-release"].get("steps", [])
        gh_steps = [s for s in steps if "softprops/action-gh-release" in s.get("uses", "")]
        self.assertTrue(len(gh_steps) > 0, "softprops/action-gh-release step must exist")

        with_block = gh_steps[0].get("with", {})
        self.assertIn("make_latest", with_block, "make_latest parameter must be explicitly configured")
        self.assertFalse(with_block["make_latest"], "make_latest must be false to preserve WSA latest pointer")

    def test_release_workflow_segregates_validation_reports(self):
        """Verify that release.yml parameterizes validation reports per edition and enforces make_latest: true."""
        wf_path = self.repo_root / ".github" / "workflows" / "release.yml"
        self.assertTrue(wf_path.exists(), "release.yml must exist")
        wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))

        jobs = wf.get("jobs", {})
        self.assertIn("validate-and-publish", jobs, "validate-and-publish job must exist")
        steps = jobs["validate-and-publish"].get("steps", [])

        # Verify validation report parameterization
        val_magisk = [s for s in steps if "Validate Magisk" in s.get("name", "")]
        self.assertTrue(len(val_magisk) > 0, "Validate Magisk step must exist")
        self.assertIn("magisk-validation-report-${EDITION}.json", val_magisk[0].get("run", ""))

        val_integrity = [s for s in steps if "Validate Package Structural Integrity" in s.get("name", "")]
        self.assertTrue(len(val_integrity) > 0, "Validate Package Structural Integrity step must exist")
        self.assertIn("package-integrity-report-${EDITION}.json", val_integrity[0].get("run", ""))

        # Verify GitHub release step configuration
        gh_steps = [s for s in steps if "softprops/action-gh-release" in s.get("uses", "")]
        self.assertTrue(len(gh_steps) > 0, "softprops/action-gh-release step must exist")
        with_block = gh_steps[0].get("with", {})
        self.assertTrue(with_block.get("make_latest"), "release.yml must explicitly set make_latest: true")
        files = with_block.get("files", "")
        self.assertIn("package-integrity-report*.json", files)
        self.assertIn("magisk-validation-report*.json", files)

    def test_release_workflow_aggregates_multi_package_metadata(self):
        """Verify release.yml does not restrict to a single package via head -n 1 and passes multi-package flags."""
        wf_path = self.repo_root / ".github" / "workflows" / "release.yml"
        self.assertTrue(wf_path.exists(), "release.yml must exist")
        wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))

        steps = wf.get("jobs", {}).get("validate-and-publish", {}).get("steps", [])
        meta_steps = [s for s in steps if "Generate Checksums and Release Metadata" in s.get("name", "")]
        self.assertTrue(len(meta_steps) > 0, "Generate Checksums and Release Metadata step must exist")

        run_script = meta_steps[0].get("run", "")
        self.assertNotIn("head -n 1", run_script, "Step must not truncate package discovery to head -n 1")
        self.assertIn("generate_release_metadata.py", run_script)
        self.assertIn("--packages-dir output", run_script)
        self.assertIn("--output-dir output", run_script)


if __name__ == "__main__":
    unittest.main()
