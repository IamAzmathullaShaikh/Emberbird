#!/usr/bin/env python3
"""S2 tests: schema-contract validator, drift detection, CI Truth Gate wiring.

- validate_against_schema: stdlib Draft-07 subset validator must agree with
  the jsonschema reference validator on every fixture case (CI runs the
  subset; local dev cross-checks with the reference implementation).
- diff_registries: added/removed releases, hash changes, asset changes,
  status changes — and NOT provenance/generated_at churn.
- CI Truth Gate: build.yml must gate on validate --schema and compile the
  platform package.
"""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "platform" / "release-engine"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from release_engine import (  # noqa: E402
    SchemaError,
    diff_registries,
    has_drift,
    validate_against_schema,
)

from fixture import FIXTURE  # noqa: E402

SCHEMA = json.loads((REPO_ROOT / "data" / "releases" / "releases.schema.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((REPO_ROOT / "data" / "releases" / "releases.json").read_text(encoding="utf-8"))


class TestSubsetValidator(unittest.TestCase):
    def test_real_registry_is_valid(self):
        self.assertEqual(validate_against_schema(REGISTRY, SCHEMA), [])

    def test_fixture_is_valid(self):
        self.assertEqual(validate_against_schema(FIXTURE, SCHEMA), [])

    def test_missing_required_provenance_detected(self):
        data = copy.deepcopy(FIXTURE)
        del data["releases"][0]["provenance"]
        problems = validate_against_schema(data, SCHEMA)
        self.assertTrue(any("provenance" in p for p in problems))

    def test_bad_channel_detected(self):
        data = copy.deepcopy(FIXTURE)
        data["releases"][0]["channel"] = "beta"
        problems = validate_against_schema(data, SCHEMA)
        self.assertTrue(any("enum" in p for p in problems))

    def test_migration_version_pinned_to_2(self):
        data = copy.deepcopy(FIXTURE)
        data["migration_version"] = 1
        problems = validate_against_schema(data, SCHEMA)
        self.assertTrue(any("migration_version" in p for p in problems))

    def test_placeholder_hash_detected_via_pattern(self):
        data = copy.deepcopy(FIXTURE)
        data["releases"][0]["assets"][0]["sha256"] = "0" * 64
        problems = validate_against_schema(data, SCHEMA)
        self.assertTrue(
            any("pattern" in p or "forbidden" in p for p in problems),
            f"all-zero hash must be rejected, got: {problems}",
        )

    def test_unexpected_property_detected(self):
        data = copy.deepcopy(FIXTURE)
        data["releases"][0]["hardcoded_truth"] = "forbidden"
        problems = validate_against_schema(data, SCHEMA)
        self.assertTrue(any("hardcoded_truth" in p for p in problems))

    def test_reference_validator_agreement(self):
        try:
            import jsonschema  # noqa: F401
        except ImportError:
            self.skipTest("jsonschema not installed (CI); subset validator covered structurally")
        schema = SCHEMA
        jsonschema.Draft7Validator.check_schema(schema)
        # valid docs pass the reference validator
        jsonschema.validate(REGISTRY, schema)
        jsonschema.validate(FIXTURE, schema)
        # invalid docs fail the reference validator iff they fail the subset
        for mutate in ("del_provenance", "bad_channel"):
            data = copy.deepcopy(FIXTURE)
            if mutate == "del_provenance":
                del data["releases"][0]["provenance"]
            else:
                data["releases"][0]["channel"] = "beta"
            subset_rejects = bool(validate_against_schema(data, schema))
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(data, schema)
            self.assertTrue(subset_rejects, f"subset validator must reject {mutate} too")

    def test_non_local_ref_raises_instead_of_passing(self):
        with self.assertRaises(SchemaError):
            validate_against_schema({}, {"$ref": "http://evil.example/x"})


def _mutated():
    return copy.deepcopy(FIXTURE)


class TestDriftDetection(unittest.TestCase):
    def setUp(self):
        self.prev = _mutated()
        self.curr = _mutated()

    def test_identical_registries_no_drift(self):
        diff = diff_registries(self.prev, self.curr)
        self.assertFalse(has_drift(diff), diff)

    def test_generation_timestamp_churn_is_not_drift(self):
        self.curr["generation"]["generated_at"] = "2099-01-01T00:00:00Z"
        self.curr["releases"][0]["provenance"]["generated_at"] = "2099-01-01T00:00:00Z"
        diff = diff_registries(self.prev, self.curr)
        self.assertFalse(has_drift(diff), diff)

    def test_added_release_detected(self):
        clone = copy.deepcopy(self.curr["releases"][0])
        clone["release_id"] = "wsa-9999-new"
        self.curr["releases"].append(clone)
        diff = diff_registries(self.prev, self.curr)
        self.assertEqual(diff["added_releases"], ["wsa-9999-new"])

    def test_removed_release_detected(self):
        self.curr["releases"].pop(0)
        diff = diff_registries(self.prev, self.curr)
        self.assertEqual(diff["removed_releases"], [self.prev["releases"][0]["release_id"]])

    def test_hash_change_detected(self):
        self.curr["releases"][0]["assets"][0]["sha256"] = "b" * 64
        diff = diff_registries(self.prev, self.curr)
        self.assertEqual(len(diff["hash_changes"]), 1)
        self.assertEqual(diff["hash_changes"][0]["filename"], self.prev["releases"][0]["assets"][0]["filename"])

    def test_asset_removed_detected(self):
        self.curr["releases"][0]["assets"] = []
        diff = diff_registries(self.prev, self.curr)
        self.assertTrue(any(c.get("sha256") for c in diff["hash_changes"]))

    def test_status_change_detected(self):
        rid = self.curr["releases"][0]["release_id"]
        self.curr["releases"][0]["status"] = "superseded"
        diff = diff_registries(self.prev, self.curr)
        self.assertEqual(diff["status_changes"], [{"release_id": rid, "from": "published", "to": "superseded"}])

    def test_provenance_commit_change_is_not_drift(self):
        self.curr["releases"][0]["provenance"]["commit"] = "f" * 40
        diff = diff_registries(self.prev, self.curr)
        self.assertFalse(has_drift(diff), diff)


class TestCITruthGate(unittest.TestCase):
    """build.yml must gate on the registry contract and compile the engine."""

    @classmethod
    def setUpClass(cls):
        cls.workflow = (REPO_ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")

    def test_compileall_covers_platform_package(self):
        m = re.search(r"python3 -m compileall.*?services", self.workflow, re.DOTALL)
        self.assertIsNotNone(m, "compileall step not found in build.yml")
        self.assertIn("platform", m.group(0), "compileall must include the platform package")

    def test_schema_gate_invoked(self):
        self.assertRegex(self.workflow, r"validate\s+--schema")

    def test_integrity_gate_invoked(self):
        self.assertIn("validate", self.workflow)


if __name__ == "__main__":
    unittest.main()
