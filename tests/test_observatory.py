#!/usr/bin/env python3
"""test_observatory.py — Unit tests for Ember Observatory Decision Engine (Phase P5)."""
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys_path = REPO_ROOT / "services" / "analytics"
import sys
sys.path.insert(0, str(sys_path))

import observatory  # noqa: E402
from release_engine import apply_policy  # noqa: E402


class TestObservatoryEngine(unittest.TestCase):
    def test_evaluate_telemetry_decision_shape(self):
        decision = observatory.evaluate_telemetry_for_recommendation()
        self.assertEqual(decision["recommended_by"], "Ember Observatory")
        self.assertTrue(decision["decided_at"].endswith("Z"))
        self.assertIn("rationale", decision)
        self.assertTrue(decision["release_id"].startswith("wsa-"))

    def test_decision_is_applicable_by_release_engine(self):
        registry_path = REPO_ROOT / "data" / "releases" / "releases.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        decision = observatory.evaluate_telemetry_for_recommendation()

        updated = apply_policy(registry, decision)
        self.assertIn("policy", updated)
        self.assertEqual(updated["policy"]["recommended_by"], "Ember Observatory")
        self.assertEqual(updated["policy"]["rationale"], decision["rationale"])

        # Exactly one release marked recommended
        rec_releases = [r for r in updated["releases"] if r.get("recommended") is True]
        self.assertEqual(len(rec_releases), 1)
        self.assertEqual(rec_releases[0]["release_id"], decision["release_id"])


if __name__ == "__main__":
    unittest.main()
