#!/usr/bin/env python3
"""E5 distribution-identity guards.

Pins the distribution-identity boundary:
  - The ACTIVE distribution identity is the new Emberbird package, derived
    from deployment/version.json (single seam).
  - The HISTORICAL package (WSABuilds.WSABuildsManager) is frozen history:
    its manifests are never mutated, never re-licensed, never re-pointed.
  - License claims in living metadata are truthful (AGPL-3.0).
  - The artifact chain (workflow names, artifact prefix, manifest paths)
    derives from the identity seam, not from hardcoded strings.

stdlib-only; runs in CI unchanged.
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_JSON = REPO_ROOT / "deployment" / "version.json"
OLD_PKG = "WSABuilds.WSABuildsManager"
OLD_MANIFEST_DIR = REPO_ROOT / "manifests" / "w" / "WSABuilds" / "WSABuildsManager"


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def identity() -> dict:
    return json.loads(VERSION_JSON.read_text(encoding="utf-8"))["manager"]


class TestE5DistributionIdentity(unittest.TestCase):
    def test_01_active_identity_is_emberbird_package(self):
        mgr = identity()
        self.assertEqual(mgr["winget_package_id"], "Emberbird.Manager")
        self.assertEqual(mgr["publisher"], "Emberbird")
        self.assertEqual(mgr["product_name"], "Emberbird Manager")

    def test_02_license_claims_are_truthful_in_living_metadata(self):
        self.assertEqual(identity()["license"], "AGPL-3.0")
        cargo = read("apps/manager/src-tauri/Cargo.toml")
        self.assertIn('license = "AGPL-3.0"', cargo)
        self.assertNotIn("Apache-2.0", cargo)
        locale = read("manifests/e/Emberbird/Manager/0.2.2/Emberbird.Manager.locale.en-US.yaml")
        self.assertIn("License: AGPL-3.0", locale)

    def test_03_new_manifests_reference_published_reality(self):
        """The new package's first authored version must point at the artifact
        that was actually published (bytes + hash are immutable reality)."""
        installer = read("manifests/e/Emberbird/Manager/0.2.2/Emberbird.Manager.installer.yaml")
        self.assertIn(
            "https://github.com/IamAzmathullaShaikh/WSABuilds/releases/download/v0.2.2/WSABuildsManager-Setup-0.2.2-x64.exe",
            installer,
        )
        self.assertIn("887443bad0aeb3eec04ff367b4768edad2cc0e1b2fcd6b9b255f5bfd3181466a", installer)

    def test_04_historical_manifests_remain_frozen(self):
        for version in ("0.2.0", "0.2.1", "0.2.2"):
            base = OLD_MANIFEST_DIR / version
            locale = base / f"{OLD_PKG}.locale.en-US.yaml"
            self.assertTrue(locale.exists(), f"frozen manifest missing: {locale}")
            text = locale.read_text(encoding="utf-8")
            self.assertIn(f"PackageIdentifier: {OLD_PKG}", text)
            # M4: history keeps what was published, including the wrong license claim.
            self.assertIn("License: Apache-2.0", text)

    def test_05_historical_manifests_not_repointed_to_new_slug(self):
        for version in ("0.2.0", "0.2.1", "0.2.2"):
            locale = (OLD_MANIFEST_DIR / version / f"{OLD_PKG}.locale.en-US.yaml").read_text(encoding="utf-8")
            installer = (OLD_MANIFEST_DIR / version / f"{OLD_PKG}.installer.yaml").read_text(encoding="utf-8")
            self.assertNotIn("IamAzmathullaShaikh/Emberbird", locale + installer)
            self.assertIn("IamAzmathullaShaikh/WSABuilds", locale + installer)

    def test_06_artifact_chain_derives_from_seam(self):
        """Workflow artifact names and prepare-winget must not hardcode the old
        identity; they derive from version.json."""
        wf = read(".github/workflows/winget-release.yml")
        self.assertNotIn("WSABuildsManager-", wf)
        self.assertIn("EmberbirdManager-", wf)
        self.assertIn("$mgr.winget_package_id.Split", wf)
        self.assertIn("emberbird-manager.exe", wf)

    def test_09_registry_untouched_by_distribution_rebrand(self):
        """Registry truth is observed reality; the E5 identity change must not
        have drifted it."""
        registry = json.loads(read("data/releases/releases.json"))
        # E5 must not fabricate registry rows for the new package identity.
        ids = [r.get("release_id", "") for r in registry.get("releases", [])]
        self.assertFalse([i for i in ids if i.startswith("emberbird")],
                         "registry must not gain unobserved emberbird rows")


if __name__ == "__main__":
    unittest.main()
