#!/usr/bin/env python3
"""E1.5 — M2: Attribution preservation tests.

Before and after every rename/migration phase, the attribution anchors must
survive. These tests are the S1 guarantee in executable form: Emberbird may
replace branding; it may not erase history.

stdlib-only; runs in CI unchanged.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    p = REPO_ROOT / rel
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


class TestAttributionAnchors(unittest.TestCase):
    """These must hold at EVERY phase boundary — the whole programme may not
    proceed while any of them fails (S3 abort condition)."""

    def test_mustardchef_credit_survives(self):
        self.assertIn("MustardChef", read("docs/ATTRIBUTION.md"))

    def test_wsabuilds_lineage_documented(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn("WSABuilds", attribution)

    def test_magiskonwsa_lineage_documented(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn("MagiskOnWSA", attribution)

    def test_magiskonwsalocal_prior_name_visible(self):
        """The prior project name must remain visible somewhere in tracked
        documentation — renaming may not erase the lineage (S1)."""
        candidates = [
            "docs/ATTRIBUTION.md",
            "docs/LICENSE_AUDIT.md",
            "docs/UPGRADE_VALIDATION.md",
            "CLEANUP_REPORT.md",
        ]
        visible = any("MagiskOnWSALocal" in read(c) for c in candidates)
        self.assertTrue(visible, "MagiskOnWSALocal lineage lost from tracked documentation")

    def test_microsoft_provenance_documented(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn("Microsoft", attribution)

    def test_agpl_license_verbatim(self):
        license_text = read("LICENSE")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("Version 3", license_text)

    def test_secondary_license_present(self):
        self.assertTrue((REPO_ROOT / "LICENSE-CC-BY-NC-ND").is_file())

    def test_legal_statement_present(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn("independent distribution platform", attribution)


class TestAttributionInCode(unittest.TestCase):
    def test_generator_carries_upstream_reference(self):
        """The generator remains the provenance tool of record; it must keep
        referencing the upstream source it syncs reality from."""
        gen = read("scripts/build_registry.py")
        self.assertIn("github.com", gen.lower())

    def test_chart_preserved_in_docs(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn("topjohnwu", attribution)
        self.assertIn("Magisk", attribution)


if __name__ == "__main__":
    unittest.main()
