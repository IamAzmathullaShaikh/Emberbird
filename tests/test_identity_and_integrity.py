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

from validate_package_identity import extract_manifest_identity, validate_identity
from validate_package_integrity import check_package_integrity
from generate_release_metadata import compute_hashes, generate_metadata_and_checksums


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


if __name__ == "__main__":
    unittest.main()
