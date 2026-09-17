#!/usr/bin/env python3
"""
test_compatibility_schema.py — Unit Tests for Compatibility Schema and Validator
"""

import unittest
import json
from pathlib import Path

# Add scripts directory to sys.path
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import validate_compatibility as vc


class TestCompatibilitySchema(unittest.TestCase):
    def setUp(self):
        self.root_dir = ROOT_DIR
        self.schema_path = self.root_dir / "compatibility" / "schema.json"
        self.valid_sample = {
            "app_name": "Test Application",
            "package_id": "com.test.app",
            "category": "Banking & UPI",
            "compatibility_status": "Working",
            "play_integrity_required": False,
            "tested_wsa_version": "2311.40000.5.0",
            "tested_root_flavor": "Magisk Stable",
            "verification_status": "unverified",
            "workaround_steps": ["Step 1", "Step 2"],
            "known_issues": "None"
        }

    def test_schema_file_exists_and_is_valid_json(self):
        self.assertTrue(self.schema_path.exists(), "schema.json must exist")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("title"), "WSA Application Compatibility Record")
        self.assertIn("required", data)

    def test_existing_records_pass_validation(self):
        data_dir = self.root_dir / "compatibility" / "data"
        json_files = list(data_dir.glob("*.json"))
        self.assertGreater(len(json_files), 0, "Expected at least 1 seed record")
        for jf in json_files:
            errors = vc.validate_file(jf)
            self.assertEqual(errors, [], f"Record {jf.name} should pass validation")

    def test_coverage_matrix_records_present(self):
        """The advertised coverage matrix must stay complete: every record
        shown on the Compatibility Hub must exist in compatibility/data/."""
        data_dir = self.root_dir / "compatibility" / "data"
        expected = {
            "Paytm.json",
            "PhonePe.json",
            "WhatsApp.json",
            "YONO.json",
            "Telegram.json",
            "Spotify.json",
            "Netflix.json",
            "GooglePlayStore.json",
            "GooglePlayServices.json",
        }
        present = {p.name for p in data_dir.glob("*.json")}
        missing = expected - present
        self.assertEqual(missing, set(), f"Coverage matrix missing records: {sorted(missing)}")

        # Package IDs for the new records must match the real Android packages.
        expected_ids = {
            "Telegram.json": "org.telegram.messenger.web",
            "Spotify.json": "com.spotify.music",
            "Netflix.json": "com.netflix.mediaclient",
            "GooglePlayStore.json": "com.android.vending",
            "GooglePlayServices.json": "com.google.android.gms",
        }
        for name, package_id in expected_ids.items():
            with open(data_dir / name, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["package_id"], package_id)

    def test_new_records_use_honest_verification_status(self):
        """Unexercised runtime claims must be marked unverified with the
        target-environment placeholder, per the Runtime Reality Gate."""
        data_dir = self.root_dir / "compatibility" / "data"
        for name in ["Telegram.json", "Spotify.json", "Netflix.json", "GooglePlayStore.json", "GooglePlayServices.json"]:
            with open(data_dir / name, encoding="utf-8") as f:
                rec = json.load(f)
            self.assertEqual(rec["verification_status"], "unverified", name)
            self.assertIn("REQUIRES TARGET ENVIRONMENT VERIFICATION", rec["tested_wsa_version"], name)

    def test_missing_required_fields_rejected(self):
        for field in vc.REQUIRED_FIELDS:
            invalid_record = dict(self.valid_sample)
            del invalid_record[field]
            errors = vc.validate_record_data(invalid_record, "test_file.json")
            self.assertTrue(any(field in err for err in errors), f"Missing '{field}' must produce error")

    def test_invalid_package_id_rejected(self):
        invalid_ids = ["not_reverse_dns", "123.numeric.first", "trailing.dot.", ".leading.dot", "has space.pkg"]
        for pid in invalid_ids:
            record = dict(self.valid_sample, package_id=pid)
            errors = vc.validate_record_data(record, "test_file.json")
            self.assertTrue(any("package_id" in err for err in errors), f"Invalid package_id '{pid}' must fail")

    def test_invalid_category_rejected(self):
        record = dict(self.valid_sample, category="NonExistentCategory")
        errors = vc.validate_record_data(record, "test_file.json")
        self.assertTrue(any("category" in err for err in errors))

    def test_invalid_status_rejected(self):
        record = dict(self.valid_sample, compatibility_status="PartiallyWorking")
        errors = vc.validate_record_data(record, "test_file.json")
        self.assertTrue(any("compatibility_status" in err for err in errors))

    def test_unrecognized_fields_rejected(self):
        record = dict(self.valid_sample, malicious_injection="rm -rf /")
        errors = vc.validate_record_data(record, "test_file.json")
        self.assertTrue(any("Unrecognized field" in err for err in errors))

    def test_play_integrity_boolean_enforced(self):
        record = dict(self.valid_sample, play_integrity_required="true")
        errors = vc.validate_record_data(record, "test_file.json")
        self.assertTrue(any("play_integrity_required" in err for err in errors))

    def test_malformed_json_syntax(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            tf.write("{ this is not valid json }")
            temp_path = tf.name

        try:
            errors = vc.validate_file(temp_path)
            self.assertTrue(any("Invalid JSON syntax" in err for err in errors))
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_tested_channel_validation(self):
        for ch in ["retail", "stable", "RP", "WIS", "WIF"]:
            record = dict(self.valid_sample, tested_channel=ch)
            errors = vc.validate_record_data(record, "test_file.json")
            self.assertEqual(errors, [], f"Valid channel '{ch}' should pass")

        invalid_record = dict(self.valid_sample, tested_channel="nightly_canary")
        errors = vc.validate_record_data(invalid_record, "test_file.json")
        self.assertTrue(any("tested_channel" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
