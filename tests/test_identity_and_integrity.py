import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
CONFIG_DIR = REPO_ROOT / "config"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_package_identity import extract_manifest_identity, validate_identity, validate_baseline_schema
from validate_package_integrity import check_package_integrity
from generate_release_metadata import compute_hashes, generate_metadata_and_checksums
from security_scan import audit_repository


class TestIdentityAndIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline_path = CONFIG_DIR / "baseline-identity.json"
        cls.sample_manifest = REPO_ROOT / "MagiskOnWSA" / "output" / "WSA_2407.40000.4.0_x64" / "AppxManifest.xml"
        cls.package_dir = REPO_ROOT / "MagiskOnWSA" / "output" / "WSA_2407.40000.4.0_x64"

    def test_baseline_identity_file_exists(self):
        self.assertTrue(self.baseline_path.exists())
        data = json.loads(self.baseline_path.read_text(encoding="utf-8"))
        self.assertEqual(data["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")
        self.assertEqual(data["publisher_id"], "8wekyb3d8bbwe")
        self.assertEqual(data["package_family_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe")

    def test_baseline_schema_validation_mode_b(self):
        passed, report = validate_baseline_schema(self.baseline_path)
        self.assertTrue(passed, "Baseline schema validation must pass for valid baseline JSON")
        self.assertEqual(report["status"], "BASELINE_SCHEMA_VERIFIED")
        self.assertEqual(report["mode"], "MODE_B_BASELINE_SCHEMA_ONLY")

    def test_manifest_identity_extraction(self):
        if not self.sample_manifest.exists():
            self.skipTest("Sample AppxManifest.xml not available in output directory")

        identity = extract_manifest_identity(self.sample_manifest)
        self.assertEqual(identity["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")
        self.assertIn("Microsoft Corporation", identity["publisher"])
        self.assertEqual(identity["publisher_id"], "8wekyb3d8bbwe")
        self.assertEqual(identity["package_family_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe")
        self.assertEqual(identity["version"], "2407.40000.4.0")

    def test_identity_drift_validation(self):
        if not self.sample_manifest.exists():
            self.skipTest("Sample AppxManifest.xml not available in output directory")

        passed, report = validate_identity(self.sample_manifest, self.baseline_path)
        self.assertTrue(passed, "Package identity must match baseline exactly with no drift")
        self.assertEqual(report["validation_passed"], True)

    def test_package_integrity_check(self):
        if not self.package_dir.exists():
            self.skipTest("Sample package directory not available")

        passed, report = check_package_integrity(self.package_dir)
        self.assertTrue(passed, "Package integrity check failed")
        self.assertEqual(report["validation_status"], "VERIFIED")

    def test_checksum_and_metadata_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            sample_file = tmp_path / "test_artifact.7z"
            sample_file.write_bytes(b"Mock 7z compressed payload for WSABuilds testing.")

            out_dir = tmp_path / "release_out"
            generate_metadata_and_checksums(
                package_dir=None,
                archive_paths=[sample_file],
                output_dir=out_dir,
                version="2407.40000.4.0",
                variant="Test_Variant_x64",
            )

            # Checksums verification
            self.assertTrue((out_dir / "checksums.sha256").exists())
            self.assertTrue((out_dir / "checksums.sha512").exists())
            self.assertTrue((out_dir / "checksums.txt").exists())
            self.assertTrue((out_dir / "release-metadata.json").exists())

            meta = json.loads((out_dir / "release-metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")
            self.assertEqual(meta["publisher_id"], "8wekyb3d8bbwe")
            self.assertEqual(meta["version"], "2407.40000.4.0")
            self.assertEqual(meta["variant"], "Test_Variant_x64")
            self.assertEqual(len(meta["artifacts"]), 1)
            self.assertEqual(meta["artifacts"][0]["filename"], "test_artifact.7z")

    def test_multi_package_metadata_aggregation(self):
        """Verify release metadata aggregator discovers multiple packages and generates dual checksum mappings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_dir = tmp_path / "output"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Create mock packages with AppxManifest.xml
            manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10">
  <Identity Name="MicrosoftCorporationII.WindowsSubsystemForAndroid"
            Publisher="CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US"
            Version="2407.40000.4.0"
            ProcessorArchitecture="x64" />
</Package>
"""
            pkg_std = out_dir / "WSA_2407.40000.4.0_x64"
            pkg_std.mkdir()
            (pkg_std / "AppxManifest.xml").write_text(manifest_content, encoding="utf-8")

            pkg_vanilla = out_dir / "WSA_2407.40000.4.0_x64_vanilla"
            pkg_vanilla.mkdir()
            (pkg_vanilla / "AppxManifest.xml").write_text(manifest_content, encoding="utf-8")

            # Create mock archives
            archive_std = out_dir / "WSA_2407.40000.4.0_x64_Release-with-magisk-26404-stable-GApps-13.0-pico.7z"
            archive_std.write_bytes(b"Mock Standard Rooted 7z Payload")

            archive_vanilla = out_dir / "WSA_2407.40000.4.0_x64_Release-vanilla-GApps-13.0-pico.7z"
            archive_vanilla.write_bytes(b"Mock Banking Vanilla 7z Payload")

            # Run aggregation via directory discovery
            generate_metadata_and_checksums(
                packages_dir=out_dir,
                output_dir=out_dir,
                version="2407.40000.4.0",
                variant="Tier1_MultiConfig_Retail_x64",
            )

            # Verify checksum files exist
            self.assertTrue((out_dir / "checksums.sha256").exists())
            self.assertTrue((out_dir / "checksums.sha512").exists())
            self.assertTrue((out_dir / "checksums.txt").exists())
            self.assertTrue((out_dir / "release-metadata.json").exists())

            # Verify sha256 contains both archives
            sha256_content = (out_dir / "checksums.sha256").read_text(encoding="utf-8")
            self.assertIn(archive_std.name, sha256_content)
            self.assertIn(archive_vanilla.name, sha256_content)
            self.assertEqual(len([line for line in sha256_content.strip().splitlines() if line]), 2)

            # Verify sha512 contains both archives
            sha512_content = (out_dir / "checksums.sha512").read_text(encoding="utf-8")
            self.assertIn(archive_std.name, sha512_content)
            self.assertIn(archive_vanilla.name, sha512_content)
            self.assertEqual(len([line for line in sha512_content.strip().splitlines() if line]), 2)

            # Verify checksums.txt contains edition labels
            txt_content = (out_dir / "checksums.txt").read_text(encoding="utf-8")
            self.assertIn("Edition: Standard Edition (Rooted)", txt_content)
            self.assertIn("Edition: Banking & Enterprise Edition (Vanilla)", txt_content)

            # Verify release-metadata.json content
            meta = json.loads((out_dir / "release-metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["version"], "2407.40000.4.0")
            self.assertEqual(meta["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")
            self.assertEqual(meta["publisher_id"], "8wekyb3d8bbwe")

            # Dual artifacts verification
            self.assertEqual(len(meta["artifacts"]), 2)
            editions = {a["edition"] for a in meta["artifacts"]}
            self.assertEqual(editions, {"standard", "vanilla"})

            # Dual checksum dictionary verification
            self.assertIn(archive_std.name, meta["checksums"]["sha256"])
            self.assertIn(archive_vanilla.name, meta["checksums"]["sha256"])
            self.assertIn(archive_std.name, meta["checksums"]["sha512"])
            self.assertIn(archive_vanilla.name, meta["checksums"]["sha512"])

            # Discovered packages verification
            self.assertEqual(len(meta["packages"]), 2)
            pkg_map = {p["edition"]: p for p in meta["packages"]}
            self.assertTrue(pkg_map["standard"]["has_magisk"])
            self.assertFalse(pkg_map["vanilla"]["has_magisk"])
            self.assertEqual(pkg_map["standard"]["directory"], "WSA_2407.40000.4.0_x64")
            self.assertEqual(pkg_map["vanilla"]["directory"], "WSA_2407.40000.4.0_x64_vanilla")
            self.assertEqual(pkg_map["standard"]["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")
            self.assertEqual(pkg_map["vanilla"]["package_name"], "MicrosoftCorporationII.WindowsSubsystemForAndroid")

    def test_security_audit_scanner(self):
        count, findings = audit_repository(REPO_ROOT)
        self.assertEqual(count, 0, f"Repository security audit failed with {count} violation(s): {findings}")


if __name__ == "__main__":
    unittest.main()
