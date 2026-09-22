"""PH-24 contract tests for the SPDX 2.3 SBOM generator.

The generator must derive every package from a real manifest — the zero-mock
law applies to dependency data as much as to runtime probes. These tests pin
the parsing rules to the committed ``Cargo.lock`` bytes and the declared npm
manifests, and verify the structural self-check rejects malformed documents.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SBOM_SCRIPT = ROOT / "scripts" / "generate_sbom.py"
CARGO_LOCK = ROOT / "apps" / "manager" / "src-tauri" / "Cargo.lock"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_sbom", SBOM_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_sbom"] = module
    spec.loader.exec_module(module)
    return module


class TestCargoLockParsing(unittest.TestCase):
    """The Rust inventory comes from the committed lock file — pin the parser."""

    def setUp(self):
        self.mod = _load_module()
        self.packages = self.mod.parse_cargo_lock(CARGO_LOCK)

    def test_parses_a_substantial_resolution(self):
        self.assertGreater(
            len(self.packages), 100,
            f"only {len(self.packages)} crates parsed from the real Cargo.lock",
        )

    def test_known_crates_present_with_versions(self):
        names = {p["name"] for p in self.packages}
        for expected in ("tauri", "serde", "sha2"):
            self.assertIn(expected, names, f"crate '{expected}' missing from parse")

    def test_sha2_version_matches_lock_bytes(self):
        lock = CARGO_LOCK.read_text(encoding="utf-8")
        self.assertIn('name = "sha2"', lock)
        block = lock.split('name = "sha2"')[1]
        version = block.split('version = "')[1].split('"')[0]
        parsed = next(p for p in self.packages if p["name"] == "sha2")
        self.assertEqual(parsed["version"], version)

    def test_every_package_has_name_and_version(self):
        for pkg in self.packages:
            self.assertTrue(pkg["name"])
            self.assertTrue(pkg["version"])

    def test_workspace_member_detected_by_missing_source(self):
        """The app crate has no registry source — purl must be absent for it."""
        root = next(p for p in self.packages if p["name"] == "emberbird-manager")
        self.assertIsNone(root["source"])
        self.assertIsNone(self.mod._purl_for_crate(root))

    def test_registry_crate_gets_a_purl(self):
        sha2 = next(p for p in self.packages if p["name"] == "sha2")
        self.assertEqual(
            self.mod._purl_for_crate(sha2),
            f"pkg:cargo/sha2@{sha2['version']}",
        )

    def test_parse_rejects_empty_lock(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".lock", delete=False) as fh:
            fh.write("# empty\n")
            bad = Path(fh.name)
        with self.assertRaises(ValueError):
            self.mod.parse_cargo_lock(bad)
        bad.unlink()


class TestNpmManifestParsing(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()

    def test_manifests_yield_declared_direct_deps_only(self):
        packages = self.mod.parse_npm_manifests()
        self.assertGreater(len(packages), 10)
        manager = json.loads((ROOT / "apps/manager/package.json").read_text(encoding="utf-8"))
        declared = {**manager.get("dependencies", {}), **manager.get("devDependencies", {})}
        parsed_names = {p["name"] for p in packages if p["surface"] == "manager"}
        self.assertEqual(parsed_names, set(declared), "npm inventory must equal the declared manifest set")

    def test_no_transitive_npm_invention(self):
        """With no committed npm lockfile, the inventory equals the declared set.

        ``@types/node`` is a legitimately *declared* dev dependency, not a
        transitive marker — the real invariant is manifest-set equality,
        which ``test_manifests_yield_declared_direct_deps_only`` pins for the
        manager surface. Here we pin the website surface the same way.
        """
        website = json.loads((ROOT / "website/package.json").read_text(encoding="utf-8"))
        declared = {**website.get("dependencies", {}), **website.get("devDependencies", {})}
        parsed_names = {p["name"] for p in self.mod.parse_npm_manifests() if p["surface"] == "website"}
        self.assertEqual(parsed_names, set(declared))

    def test_website_surface_present(self):
        packages = self.mod.parse_npm_manifests()
        surfaces = {p["surface"] for p in packages}
        self.assertEqual(surfaces, {"manager", "website"})


class TestDocumentAssembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.doc = cls.mod.build_sbom("Windows_11_2407.40000.4.0_v4", "0.2.2", "2407.40000.4.0")

    def test_document_validates_clean(self):
        self.assertEqual(self.mod.validate_sbom(self.doc), [])

    def test_document_carries_spdx_23_required_fields(self):
        self.assertEqual(self.doc["spdxVersion"], "SPDX-2.3")
        self.assertEqual(self.doc["dataLicense"], "CC0-1.0")
        self.assertTrue(self.doc["documentNamespace"].startswith("https://emberbird.dev/spdx/"))
        self.assertIn("SPDXRef-Package-EMBERBIRD-RELEASE", self.doc["documentDescribes"])

    def test_root_package_describes_the_release(self):
        root = next(p for p in self.doc["packages"] if p["SPDXID"] == "SPDXRef-Package-EMBERBIRD-RELEASE")
        self.assertEqual(root["licenseConcluded"], "AGPL-3.0-only")
        self.assertEqual(root["versionInfo"], "0.2.2")

    def test_every_component_has_unique_spdxid(self):
        ids = [p["SPDXID"] for p in self.doc["packages"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_component_count_matches_parsed_sources(self):
        crates = self.mod.parse_cargo_lock(CARGO_LOCK)
        npm = self.mod.parse_npm_manifests()
        pyenv = self.mod.collect_python_env()
        root = 1
        self.assertEqual(
            len(self.doc["packages"]),
            len(crates) + len(npm) + len(pyenv) + root,
            "document must not invent or drop packages",
        )

    def test_namespace_is_deterministic_for_identical_inputs(self):
        doc2 = self.mod.build_sbom("Windows_11_2407.40000.4.0_v4", "0.2.2", "2407.40000.4.0")
        self.assertEqual(self.doc["documentNamespace"], doc2["documentNamespace"])

    def test_source_date_epoch_pins_created_timestamp(self):
        import os
        from datetime import datetime, timezone
        from unittest import mock
        epoch = 1758500000
        with mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": str(epoch)}):
            doc = self.mod.build_sbom("T", "0.2.2", "2407.40000.4.0")
        expected = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(doc["creationInfo"]["created"], expected)


class TestValidatorRejectsBrokenDocuments(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()

    def test_rejects_missing_document_fields(self):
        errors = self.mod.validate_sbom({"packages": []})
        self.assertTrue(any("missing document field" in e for e in errors))

    def test_rejects_duplicate_spdxids(self):
        doc = {
            "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
            "name": "x", "documentNamespace": "https://x", "creationInfo": {"created": "2026-01-01T00:00:00Z"},
            "documentDescribes": ["A"],
            "packages": [
                {"name": "a", "SPDXID": "SPDXRef-A", "downloadLocation": "NOASSERTION",
                 "filesAnalyzed": False, "licenseConcluded": "NOASSERTION",
                 "licenseDeclared": "NOASSERTION", "copyrightText": "NOASSERTION"},
                {"name": "b", "SPDXID": "SPDXRef-A", "downloadLocation": "NOASSERTION",
                 "filesAnalyzed": False, "licenseConcluded": "NOASSERTION",
                 "licenseDeclared": "NOASSERTION", "copyrightText": "NOASSERTION"},
            ],
        }
        errors = self.mod.validate_sbom(doc)
        self.assertTrue(any("duplicate SPDXID" in e for e in errors))

    def test_rejects_package_missing_required_fields(self):
        doc = {
            "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0", "SPDXID": "SPDXRef-DOCUMENT",
            "name": "x", "documentNamespace": "https://x", "creationInfo": {"created": "2026-01-01T00:00:00Z"},
            "documentDescribes": ["A"],
            "packages": [{"name": "a", "SPDXID": "SPDXRef-A"}],
        }
        errors = self.mod.validate_sbom(doc)
        self.assertTrue(any("missing:" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
