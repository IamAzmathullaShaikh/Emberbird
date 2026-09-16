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

    def test_new_taxonomy_paths_exist_post_e2(self):
        """After E2 executed, the NEW taxonomy paths must exist — the map
        documents reality, not fiction. The old paths are preserved only in
        docs/PATH_MAP.md as the permanent legacy redirect map (S1)."""
        required = [
            "docs/archive",
            "utilities",
            "tools",
            "upstream",
            "tools/build.sh",
            "tools/build_local.py",
            "tools/update-check/MagiskStableUpdateCheck.py",
        ]
        missing = [p for p in required if not (REPO_ROOT / p).exists()]
        self.assertEqual(missing, [], f"E2 mapping failed — required new paths missing: {missing}")

    def test_mapped_target_names_occupied_post_e2(self):
        """E2 executed: targets must exist and legacy top-level dirs must be
        gone from the live tree (they survive only in docs/PATH_MAP.md and
        git history)."""
        targets = ["docs/archive", "utilities", "tools", "upstream"]
        missing = [p for p in targets if not (REPO_ROOT / p).exists()]
        self.assertEqual(
            missing, [],
            f"E2 target paths missing — restructure mapping not executed: {missing}",
        )
        # Residual check uses git-tracked truth (L3/L4), not raw disk state:
        # local untracked build residue (MagiskOnWSA/output, download) must
        # never fail the contract, and CI has no such residue — tracked-truth
        # keeps both environments consistent.
        legacy = ["Documentation", "WSABuilds Utilities", "MagiskOnWSA"]
        import subprocess

        ls = subprocess.run(
            ["git", "ls-files", "--", *legacy],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            cwd=str(REPO_ROOT),
        )
        tracked = [l for l in ls.stdout.splitlines() if l.strip()]
        self.assertEqual(
            tracked, [],
            f"legacy top-level directories still tracked after E2: {tracked}",
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
