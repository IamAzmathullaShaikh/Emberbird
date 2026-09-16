#!/usr/bin/env python3
"""E1.5 — M1: Metamorphosis contract tests.

Pins the metamorphosis structure against the authoritative contracts:
  - PATH_MAP v2 (docs/PATH_MAP.md) — the restructure targets exist exactly as
    documented (or, after E2, that the mapping executed); fail-first protects
    every later migration step
  - BRAND (docs/BRAND.md) — canonical identity layers exist
  - programme charter present; freeze rules documented

stdlib-only; runs in CI unchanged.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestPathMapContract(unittest.TestCase):
    def test_path_map_document_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "PATH_MAP.md").is_file())

    def test_legacy_paths_exist_pre_e2(self):
        """Before E2 executes, the legacy paths must still exist — the map
        documents reality, not fiction. (After E2, this test is updated in the
        same commit to pin the NEW paths.)"""
        legacy = [
            "Documentation",
            "WSABuilds Utilities",
            "MagiskOnWSA/scripts",
        ]
        missing = [p for p in legacy if not (REPO_ROOT / p).exists()]
        self.assertEqual(missing, [], f"legacy paths vanished without an E2 mapping execution: {missing}")

    def test_mapped_target_names_not_occupied_pre_e2(self):
        """E2 target directories must not already exist (no partial restructure)."""
        targets = ["docs/archive", "utilities", "tools", "upstream"]
        occupied = [p for p in targets if (REPO_ROOT / p).exists()]
        self.assertEqual(
            occupied, [],
            f"E2 target paths already exist — restructure started without the map being executed: {occupied}",
        )


class TestBrandContract(unittest.TestCase):
    def test_brand_document_exists(self):
        self.assertTrue((REPO_ROOT / "docs" / "BRAND.md").is_file())

    def test_canonical_identity_layers_present(self):
        self.assertTrue((REPO_ROOT / "data" / "releases" / "releases.json").is_file())
        self.assertTrue((REPO_ROOT / "docs" / "PHOENIX_CHARTER.md").is_file())
        self.assertTrue((REPO_ROOT / "docs" / "EMBERBIRD_CHARTER.md").is_file())


class TestProgrammeCharter(unittest.TestCase):
    def test_charter_exists_with_governing_rules(self):
        charter = (REPO_ROOT / "docs" / "METAMORPHOSIS.md").read_text(encoding="utf-8")
        for rule in ("M4", "S1", "G1", "G2", "S2", "S3", "G3", "G4"):
            self.assertIn(rule, charter, f"charter must document rule {rule}")

    def test_freeze_window_rules_documented(self):
        charter = (REPO_ROOT / "docs" / "METAMORPHOSIS.md").read_text(encoding="utf-8")
        self.assertIn("E2", charter)
        self.assertIn("E5", charter)


if __name__ == "__main__":
    unittest.main()
