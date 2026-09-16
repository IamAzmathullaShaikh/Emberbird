#!/usr/bin/env python3
"""Governance guard tests — Execution Contract clauses 13 (M4) and 14 (S1).

M4: Release History Is Immutable. S1: Historical Identity Preservation.
These guards pin the invariants that the Emberbird Metamorphosis Programme
must never break, regardless of branding or restructuring.

stdlib-only; runs in CI unchanged.
"""
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8", errors="ignore")


class TestReleaseHistoryImmutability(unittest.TestCase):
    """M4 — clause 13: everything historical remains historical."""

    def test_historical_winget_manifests_present(self):
        base = REPO_ROOT / "manifests" / "w" / "WSABuilds" / "WSABuildsManager"
        self.assertTrue(base.exists(), "published winget manifest tree must exist")
        versions = sorted(d.name for d in base.iterdir() if d.is_dir())
        for historical in ("0.2.0", "0.2.1", "0.2.2"):
            self.assertIn(
                historical, versions,
                f"historical winget manifest {historical} must never be removed",
            )

    def test_historical_winget_package_identifier_untouched(self):
        manifest = read("manifests/w/WSABuilds/WSABuildsManager/0.2.0/WSABuilds.WSABuildsManager.yaml")
        self.assertIn(
            "PackageIdentifier: WSABuilds.WSABuildsManager", manifest,
            "published manifest identity is history — it must never be rewritten",
        )

    def test_historical_registry_releases_present(self):
        import json
        registry = json.loads(read("data/releases/releases.json"))
        ids = {r["release_id"] for r in registry["releases"]}
        for historical in (
            "manager-0.2.0", "manager-0.2.1", "manager-0.2.2",
            "wsa-2311-standard", "wsa-2311-banking",
        ):
            self.assertIn(historical, ids, f"historical release {historical} must never be removed")


class TestHistoricalIdentityPreservation(unittest.TestCase):
    """S1 — clause 14: Emberbird may replace branding; it may not erase history."""

    def test_upstream_attribution_survives(self):
        attribution = read("docs/ATTRIBUTION.md")
        for anchor in ("MustardChef", "MagiskOnWSA"):
            self.assertIn(anchor, attribution, f"upstream attribution anchor {anchor!r} must survive the metamorphosis")

    def test_license_is_verbatim_agpl(self):
        license_text = read("LICENSE")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", license_text)

    def test_upstream_repo_name_lineage_visible(self):
        """The upstream MagiskOnWSALocal lineage must stay visible somewhere in
        tracked documentation or provenance — renaming may not erase it."""
        hits = 0
        for rel in ("docs/ATTRIBUTION.md", "CLEANUP_REPORT.md", "docs/UPGRADE_VALIDATION.md", "docs/README.md"):
            p = REPO_ROOT / rel
            if p.exists() and "MagiskOnWSALocal" in p.read_text(encoding="utf-8", errors="ignore"):
                hits += 1
        self.assertGreaterEqual(hits, 1, "MagiskOnWSALocal lineage must remain visible in tracked docs")

    def test_historical_release_provenance_in_registry(self):
        import json
        registry = json.loads(read("data/releases/releases.json"))
        wsa = [r for r in registry["releases"] if r["release_id"].startswith("wsa-")]
        self.assertTrue(wsa, "historical WSA release provenance must remain in the registry")
        # Every release must keep provenance of how it entered the registry.
        for rel in registry["releases"]:
            self.assertIn("provenance", rel, f"release {rel['release_id']} lost its provenance record")

    def test_microsoft_wsa_lineage_documented(self):
        attribution = read("docs/ATTRIBUTION.md")
        self.assertIn(
            "Microsoft", attribution,
            "the Microsoft WSA lineage must stay documented for provenance",
        )


if __name__ == "__main__":
    unittest.main()
