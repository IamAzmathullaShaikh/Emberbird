#!/usr/bin/env python3
"""
Emberbird Release Registry contract tests (P0.2).

Layers:
  1. Structural tests - always run (CI has no jsonschema): schema parses,
     required definitions/enums present, no-placeholder-hash rule encoded.
  2. Contract tests   - jsonschema-gated: valid fixtures pass, invalid
     mutations raise ValidationError.
  3. Reality pins     - fixture anchors to deployment/version.json.

Run: python3 -m unittest tests.test_release_registry -v
"""
import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "data" / "releases" / "releases.schema.json"
VERSION_FILE = REPO_ROOT / "deployment" / "version.json"

try:
    import jsonschema
except ImportError:
    jsonschema = None


sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture import FIXTURE


def _load_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _version_file():
    return json.loads(VERSION_FILE.read_text(encoding="utf-8"))


class TestSchemaStructural(unittest.TestCase):
    """CI-safe: no third-party dependency required."""

    def setUp(self):
        self.schema = _load_schema()

    def test_schema_is_draft07_with_correct_id(self):
        self.assertEqual(self.schema["$schema"], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(
            self.schema["$id"],
            "https://wsabuilds.azmathulla.dev/schemas/releases.schema.json",
        )

    def test_required_definitions_present(self):
        defs = self.schema["definitions"]
        for name in ("release", "asset", "vault_entry", "validation_report", "sha256", "release_id"):
            self.assertIn(name, defs)

    def test_channel_enum_tokens(self):
        self.assertEqual(
            self.schema["definitions"]["channel"]["enum"],
            ["stable", "retail", "RP", "WIS", "WIF"],
        )

    def test_edition_enum_tokens(self):
        self.assertEqual(
            self.schema["definitions"]["edition"]["enum"],
            ["standard", "banking", "manager"],
        )

    def test_status_enum_tokens(self):
        self.assertEqual(
            self.schema["definitions"]["status"]["enum"],
            ["draft", "published", "superseded", "yanked"],
        )

    def test_architecture_enum_tokens(self):
        self.assertEqual(self.schema["definitions"]["architecture"]["enum"], ["x64", "arm64"])
        self.assertEqual(
            self.schema["definitions"]["asset_arch"]["enum"],
            ["x64", "arm64", "universal"],
        )

    def test_registry_versioning_fields_required(self):
        for field in ("schema_version", "migration_version", "compatibility_level", "releases"):
            self.assertIn(field, self.schema["required"])

    def test_placeholder_hash_is_schema_invalid_by_construction(self):
        sha = self.schema["definitions"]["sha256"]
        self.assertEqual(sha["pattern"], "^[a-f0-9]{64}$")
        self.assertEqual(sha["not"]["pattern"], "^0{64}$")

    def test_reserved_future_fields_exist(self):
        props = self.schema["definitions"]["release"]["properties"]
        for field in ("health_score", "registry_signature", "recommended"):
            self.assertIn(field, props)

    def test_six_conditional_rules_present(self):
        self.assertEqual(len(self.schema["definitions"]["release"]["allOf"]), 6)


def _validate(instance):
    import jsonschema
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance, schema)


@unittest.skipUnless(jsonschema is not None, "jsonschema not installed")
class TestRegistryContract(unittest.TestCase):
    def setUp(self):
        self.registry = copy.deepcopy(FIXTURE)

    def test_valid_registry_passes(self):
        _validate(self.registry)

    def test_bad_channel_rejected(self):
        self.registry["releases"][0]["channel"] = "beta"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_bad_architecture_rejected(self):
        self.registry["releases"][0]["architectures"] = ["arm"]
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_placeholder_hash_rejected(self):
        self.registry["releases"][0]["assets"][0]["sha256"] = "0" * 64
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_short_hash_rejected(self):
        self.registry["releases"][0]["assets"][0]["sha256"] = "abc123"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_superseded_without_successor_rejected(self):
        rel = self.registry["releases"][2]
        rel["status"] = "superseded"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_standard_with_vanilla_root_rejected(self):
        self.registry["releases"][0]["root_solution"] = "none"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_banking_without_vanilla_asset_rejected(self):
        self.registry["releases"][1]["assets"][0]["filename"] = "WSA_2407.40000.4.0_x64.7z"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_manager_claiming_arm64_rejected(self):
        self.registry["releases"][2]["architectures"] = ["x64", "arm64"]
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_manager_carrying_subsystem_fields_rejected(self):
        self.registry["releases"][2]["wsa_version"] = "2407.40000.4.0"
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_wrong_schema_version_rejected(self):
        self.registry["schema_version"] = 2
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_recommended_superseded_rejected(self):
        rel = self.registry["releases"][2]
        rel["status"] = "superseded"
        rel["superseded_by"] = "manager-0.3.0"
        rel["recommended"] = True
        with self.assertRaises(Exception):
            _validate(self.registry)

    def test_unknown_top_level_field_rejected(self):
        self.registry["extraneous"] = True
        with self.assertRaises(Exception):
            _validate(self.registry)


class TestRealityPins(unittest.TestCase):
    """Fixture must stay anchored to published reality (L4 repository metadata)."""

    def test_wsa_version_matches_deployment(self):
        vf = _version_file()
        fixture_rel = FIXTURE["releases"][0]
        self.assertEqual(fixture_rel["wsa_version"], vf["subsystem_baseline"]["wsa_version"])

    def test_current_release_tag_matches_deployment(self):
        vf = _version_file()
        fixture_rel = FIXTURE["releases"][1]
        self.assertEqual(fixture_rel["tag"], vf["subsystem_baseline"]["release_tag"])

    def test_wsa_version_matches_deployment_bank(self):
        vf = _version_file()
        self.assertEqual(FIXTURE["releases"][1]["wsa_version"], vf["subsystem_baseline"]["wsa_version"])

    def test_manager_version_matches_deployment(self):
        vf = _version_file()
        self.assertTrue(
            FIXTURE["releases"][2]["tag"].endswith(vf["manager"]["version"]),
            "manager fixture tag must track deployment/version.json manager.version",
        )
