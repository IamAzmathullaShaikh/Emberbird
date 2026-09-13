import json
import unittest
from pathlib import Path

from scripts.validate_analytics import (
    REPO_ROOT,
    SCHEMA_FILE,
    METRICS_FILE,
    assert_no_pii_keys,
    validate_analytics_schema,
    validate_aggregation_integrity,
)


class TestAnalyticsSubsystem(unittest.TestCase):
    def setUp(self):
        self.schema_file = SCHEMA_FILE
        self.metrics_file = METRICS_FILE

    def test_schema_and_metrics_files_exist(self):
        """Verify schema and metrics files exist on disk."""
        self.assertTrue(self.schema_file.exists(), "schema.json must exist")
        self.assertTrue(self.metrics_file.exists(), "metrics.json must exist")

    def test_zero_pii_enforcement(self):
        """Verify metrics.json contains zero forbidden PII keys."""
        data = json.loads(self.metrics_file.read_text(encoding="utf-8"))
        violations = assert_no_pii_keys(data)
        self.assertEqual(violations, [], f"PII violations detected: {violations}")

    def test_pii_detector_flags_forbidden_keys(self):
        """Verify that PII detector correctly flags injected forbidden keys."""
        bad_payload = {
            "public_metric": 100,
            "user_data": {"client_ip": "192.168.1.1", "device_id": "ABC-123"},
        }
        violations = assert_no_pii_keys(bad_payload)
        self.assertEqual(len(violations), 2)
        self.assertTrue(any("client_ip" in v for v in violations))
        self.assertTrue(any("device_id" in v for v in violations))

    def test_schema_validation(self):
        """Verify metrics payload matches schema requirements."""
        schema = json.loads(self.schema_file.read_text(encoding="utf-8"))
        metrics = json.loads(self.metrics_file.read_text(encoding="utf-8"))

        errors = validate_analytics_schema(metrics, schema)
        self.assertEqual(errors, [], f"Schema errors detected: {errors}")

    def test_aggregation_arithmetic_integrity(self):
        """Verify arithmetic sums for root flavor and architecture distributions."""
        metrics = json.loads(self.metrics_file.read_text(encoding="utf-8"))
        errors = validate_aggregation_integrity(metrics)
        self.assertEqual(errors, [], f"Integrity errors detected: {errors}")


if __name__ == "__main__":
    unittest.main()
