#!/usr/bin/env python3
"""
Analytics validation cycle tests.

Derived from the v0.2.2 hardening audit (Phase 8). These tests pin the
privacy-first analytics guarantees so regressions fail loudly in CI:

  1. metrics.json validates against services/analytics/schema.json
  2. zero-PII enforcement: forbidden keys must raise (validator failure test)
  3. privacy schema enforcement: zero_pii=false must fail schema (const)
  4. aggregation integrity: independent recount matches metrics.json
  5. dashboard readiness: aggregate.py regenerates identical metrics
     (modulo the last_updated timestamp)

Run: python3 -m unittest tests.test_analytics -v
"""

import copy
import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "services" / "analytics" / "schema.json"
METRICS = REPO_ROOT / "services" / "analytics" / "metrics.json"
AGGREGATE = REPO_ROOT / "services" / "analytics" / "aggregate.py"
COMPAT_DATA = REPO_ROOT / "compatibility" / "data"

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def _load_aggregate_module():
    spec = importlib.util.spec_from_file_location("aggregate", AGGREGATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(jsonschema is not None, "jsonschema not installed")
class TestAnalyticsSchema(unittest.TestCase):
    def test_metrics_validate_against_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        metrics = json.loads(METRICS.read_text(encoding="utf-8"))
        jsonschema.validate(metrics, schema)

    def test_zero_pii_false_rejected_by_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        metrics = json.loads(METRICS.read_text(encoding="utf-8"))
        bad = copy.deepcopy(metrics)
        bad["transparency_principles"]["zero_pii"] = False
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(bad, schema)


class TestZeroPIIEnforcement(unittest.TestCase):
    def test_forbidden_key_raises(self):
        agg = _load_aggregate_module()
        with self.assertRaises(ValueError):
            agg.assert_zero_pii({"release_metrics": {"user_id": "u123"}})

    def test_nested_pii_in_list_raises(self):
        agg = _load_aggregate_module()
        with self.assertRaises(ValueError):
            agg.assert_zero_pii({"items": [{"email": "x@y.z"}]})

    def test_clean_payload_accepted(self):
        agg = _load_aggregate_module()
        agg.assert_zero_pii(
            {"release_metrics": {"total_releases": 48}, "items": [{"app": "a"}]}
        )


class TestAggregationIntegrity(unittest.TestCase):
    def test_independent_recount_matches_metrics(self):
        metrics = json.loads(METRICS.read_text(encoding="utf-8"))
        counts = {"Working": 0, "Workaround Required": 0, "Broken": 0}
        categories, play_integrity = set(), 0
        files = [f for f in COMPAT_DATA.glob("*.json")]
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            counts[d.get("compatibility_status")] = (
                counts.get(d.get("compatibility_status"), 0) + 1
            )
            categories.add(d.get("category"))
            play_integrity += bool(d.get("play_integrity_required"))
        cm = metrics["compatibility_metrics"]
        self.assertEqual(cm["total_apps_tested"], len(files))
        self.assertEqual(cm["compatible_count"], counts["Working"])
        self.assertEqual(
            cm["working_with_issues_count"], counts["Workaround Required"]
        )
        self.assertEqual(cm["unsupported_count"], counts["Broken"])
        self.assertEqual(cm["play_integrity_required_count"], play_integrity)
        self.assertEqual(cm["categories_count"], len(categories))


class TestDashboardGeneration(unittest.TestCase):
    def test_aggregate_regenerates_identical_metrics(self):
        agg = _load_aggregate_module()
        before = json.loads(METRICS.read_text(encoding="utf-8"))
        payload = agg.generate_analytics_payload()
        # Timestamp is expected to move; everything else must be identical.
        before.pop("last_updated")
        after = copy.deepcopy(payload)
        after.pop("last_updated")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
