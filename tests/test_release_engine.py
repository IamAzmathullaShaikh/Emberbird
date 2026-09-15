#!/usr/bin/env python3
"""
Emberbird Release Engine unit tests (P0.4) - synthetic registry fixtures,
no file IO, no network. Complements test_registry_consumer.py (real registry)
and test_release_registry.py (schema contract).
"""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "platform" / "release-engine"))

from release_engine import Registry, RegistryError, check_integrity  # noqa: E402


def _asset(name, digest="a" * 64, role="package", arch="x64"):
    return {
        "filename": name,
        "sha256": digest,
        "arch": arch,
        "role": role,
        "source_url": f"https://example.test/{name}",
        "source_type": "generated",
        "hash_source": "computed",
        "verified_at": "2026-09-15T00:00:00Z",
    }


def _synthetic():
    return {
        "schema_version": 1,
        "migration_version": 1,
        "compatibility_level": "backward",
        "policy": {
            "recommended_by": "test-policy-engine",
            "decided_at": "2026-02-01T00:00:00Z",
            "rationale": "fixture policy decision backing the recommended flag",
        },
        "releases": [
            {
                "release_id": "wsa-100-standard",
                "tag": "wsa-v100.00000.1.0",
                "kind": "subsystem",
                "wsa_version": "100.00000.1.0",
                "channel": "retail",
                "edition": "standard",
                "architectures": ["x64"],
                "root_solution": "magisk",
                "gapps_variant": "pico",
                "status": "superseded",
                "superseded_by": "wsa-200-standard",
                "published_at": "2026-01-01T00:00:00Z",
                "assets": [_asset("WSA_100.00000.1.0_x64.7z")],
            },
            {
                "release_id": "wsa-200-standard",
                "tag": "wsa-v200.00000.1.0",
                "kind": "subsystem",
                "wsa_version": "200.00000.1.0",
                "channel": "retail",
                "edition": "standard",
                "architectures": ["x64"],
                "root_solution": "magisk",
                "gapps_variant": "pico",
                "status": "published",
                "recommended": True,
                "published_at": "2026-02-01T00:00:00Z",
                "assets": [_asset("WSA_200.00000.1.0_x64.7z")],
            },
            {
                "release_id": "wsa-200-banking",
                "tag": "wsa-v200.00000.1.0",
                "kind": "subsystem",
                "wsa_version": "200.00000.1.0",
                "channel": "retail",
                "edition": "banking",
                "architectures": ["x64"],
                "root_solution": "none",
                "gapps_variant": "pico",
                "status": "published",
                "published_at": "2026-02-01T00:00:00Z",
                "assets": [_asset("WSA_200.00000.1.0_x64_vanilla.7z")],
            },
            {
                "release_id": "manager-9.9.9",
                "tag": "v9.9.9",
                "kind": "manager",
                "channel": "stable",
                "edition": "manager",
                "architectures": ["x64"],
                "status": "published",
                "published_at": "2026-03-01T00:00:00Z",
                "assets": [_asset("Mgr-Setup-9.9.9-x64.exe"), _asset("Mgr-checksums.txt", role="checksum", arch="universal")],
            },
        ],
        "vault": [
            {"artifact": "WSA_200.00000.1.0_x64.7z",
             "source_url": "https://example.test/x",
             "sha256": "a" * 64,
             "mirror_status": "unverified",
             "last_verified_at": "2026-09-15T00:00:00Z"},
        ],
    }


class TestLookups(unittest.TestCase):
    def setUp(self):
        self.reg = Registry(_synthetic())

    def test_latest_wsa_picks_newest_published(self):
        self.assertEqual(self.reg.latest_wsa().release_id, "wsa-200-standard")

    def test_latest_wsa_ignores_superseded(self):
        ids = [r.release_id for r in self.reg.published()]
        self.assertNotIn("wsa-100-standard", ids)

    def test_latest_manager(self):
        self.assertEqual(self.reg.latest_manager().release_id, "manager-9.9.9")

    def test_recommended_wsa(self):
        self.assertEqual(self.reg.recommended_wsa().release_id, "wsa-200-standard")

    def test_recommended_wsa_by_edition(self):
        self.assertIsNone(self.reg.recommended_wsa(edition="banking"))

    def test_by_channel_edition_tag_id(self):
        self.assertEqual(len(self.reg.by_channel("retail")), 3)
        self.assertEqual(len(self.reg.by_edition("banking")), 1)
        self.assertEqual(len(self.reg.by_tag("wsa-v200.00000.1.0")), 2)
        self.assertIsNone(self.reg.by_id("ghost"))

    def test_hash_for_unique(self):
        self.assertEqual(self.reg.hash_for("Mgr-Setup-9.9.9-x64.exe"), "a" * 64)

    def test_hash_for_missing_returns_none(self):
        self.assertIsNone(self.reg.hash_for("nope.bin"))

    def test_vault_entry_lookup(self):
        entry = self.reg.vault_entry("WSA_200.00000.1.0_x64.7z")
        self.assertIsNotNone(entry)
        self.assertIsNone(self.reg.vault_entry("ghost"))


class TestIntegritySynthetic(unittest.TestCase):
    def test_synthetic_healthy(self):
        self.assertEqual(check_integrity(_synthetic()), [])

    def test_superseded_chain_valid(self):
        data = _synthetic()
        problems = check_integrity(data)
        self.assertEqual(problems, [], "superseded_by -> existing id must be valid")

    def test_breaking_chain_detected(self):
        data = _synthetic()
        data["releases"][0]["superseded_by"] = "wsa-ghost"
        self.assertTrue(any("unknown release" in p for p in check_integrity(data)))

    def test_universal_assets_exempt_from_arch_rule(self):
        data = _synthetic()
        problems = check_integrity(data)
        self.assertEqual(problems, [], "checksum assets are universal; arch rule must not fire")


class TestPolicyGuards(unittest.TestCase):
    """WO-7 registry policy guards (S1).

    Rule 1: recommended = policy decision; requires policy provenance.
    Rule 2: artifact identity = (filename, sha256); duplicates are defects.
    """

    def setUp(self):
        self.data = _synthetic()

    def test_recommended_without_policy_provenance_flagged(self):
        del self.data["policy"]
        problems = check_integrity(self.data)
        self.assertTrue(
            any("policy.recommended_by" in p for p in problems),
            f"expected missing-policy-provenance problem, got: {problems}",
        )

    def test_recommended_with_policy_provenance_clean(self):
        self.assertEqual(check_integrity(self.data), [])

    def test_policy_without_decided_at_flagged(self):
        del self.data["policy"]["decided_at"]
        problems = check_integrity(self.data)
        self.assertTrue(any("decided_at" in p for p in problems))

    def test_no_recommendation_needs_no_policy(self):
        for rel in self.data["releases"]:
            rel.pop("recommended", None)
        self.data.pop("policy", None)
        self.assertEqual(check_integrity(self.data), [])

    def test_duplicate_asset_identity_flagged(self):
        dup = dict(self.data["releases"][1]["assets"][0])
        self.data["releases"][1]["assets"].append(dup)
        problems = check_integrity(self.data)
        self.assertTrue(any("duplicate artifact identity" in p for p in problems))

    def test_same_filename_different_hash_stays_distinct(self):
        # The P0 reality case: identical filename, different cut.
        cut2 = dict(self.data["releases"][1]["assets"][0])
        cut2["sha256"] = "b" * 64
        self.data["releases"][1]["assets"].append(cut2)
        problems = [p for p in check_integrity(self.data) if "duplicate artifact identity" in p]
        self.assertEqual(problems, [], "distinct cuts must never be flagged as duplicates")

    def test_duplicate_vault_identity_flagged(self):
        self.data["vault"].append(dict(self.data["vault"][0]))
        problems = check_integrity(self.data)
        self.assertTrue(any("duplicate vault identity" in p for p in problems))

    def test_real_registry_satisfies_policy_guards(self):
        from pathlib import Path

        registry_path = Path(__file__).resolve().parent.parent / "data" / "releases" / "releases.json"
        if not registry_path.is_file():
            self.skipTest("registry not generated in this environment")
        import json

        data = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(check_integrity(data), [])


if __name__ == "__main__":
    unittest.main()
