"""PH-00 contract: the charter's declared policies must match code truth.

``docs/EMBERBIRD_CHARTER.md`` restates a support matrix, a privacy policy and
integrity promises. A restatement that drifts from the code is worse than no
restatement — it is a lie with a citation. These guards pin every declared
number and every "nothing" claim to its source, so the charter can only be
amended together with the truth it restates.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARTER = ROOT / "docs" / "EMBERBIRD_CHARTER.md"
VERSION_JSON = ROOT / "deployment" / "version.json"
COORDINATOR = ROOT / "apps/manager/src-tauri/src/coordinator.rs"
MANAGER_SRC = ROOT / "apps/manager/src"
RUST_SRC = ROOT / "apps/manager/src-tauri/src"
WEBSITE_SRC = ROOT / "website/src"
CLI_SRC = ROOT / "platform/cli"


def charter_text() -> str:
    return CHARTER.read_text(encoding="utf-8")


class TestSupportMatrix(unittest.TestCase):
    """Every declared configuration number must equal its code truth."""

    def setUp(self):
        self.version = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
        self.charter = charter_text()

    def test_min_windows_build_matches_deployment_manifest(self):
        declared = self.version["manager"]["min_windows_build"]
        build = declared.split(".")[2]
        self.assertIn(
            f"**{build}**",
            self.charter,
            f"charter does not declare the enforced min build {build}",
        )

    def test_architecture_row_matches_target_architectures(self):
        targets = self.version["manager"]["target_architectures"]
        self.assertEqual(targets, ["x64"], "precondition: x64-only until ARM64 lands")
        self.assertIn("**x64**", self.charter, "charter must declare x64 host arch")

    def test_disk_row_matches_required_disk_space_constant(self):
        rust = COORDINATOR.read_text(encoding="utf-8")
        match = re.search(
            r"REQUIRED_DISK_SPACE_BYTES:\s*u64\s*=\s*([\d\s*]+);", rust
        )
        self.assertIsNotNone(match, "failed to parse REQUIRED_DISK_SPACE_BYTES")
        # The constant may be written as an expression (``25 * 1024 * ...``);
        # evaluate it restricted to the integer-multiplication grammar above.
        bytes_ = 1
        for factor in match.group(1).split("*"):
            bytes_ *= int(factor.strip())
        gb = bytes_ // (1024**3)
        self.assertEqual(gb, 25, "precondition: 25 GB baseline")
        self.assertIn(f"**≥ {gb} GB**", self.charter, "charter disk row must match the constant")

    def test_subsystem_baseline_row_matches_deployment_manifest(self):
        baseline = self.version["subsystem_baseline"]
        needle = f"WSA **{baseline['wsa_version']}**"
        self.assertIn(needle, self.charter, f"charter must declare the baseline {baseline['wsa_version']}")
        self.assertIn(baseline["android_version"], self.charter)

    def test_charter_mentions_every_enforced_dimension(self):
        for dimension in ("Virtualization", "Developer Mode", "disk", "Windows build"):
            self.assertIn(dimension, self.charter, f"support matrix missing: {dimension}")


class TestPrivacyClaims(unittest.TestCase):
    """The 'Emberbird collects nothing' policy is a code claim — verify it."""

    def setUp(self):
        self.charter = charter_text()

    def test_charter_makes_the_no_collection_claim(self):
        self.assertIn("collects nothing", self.charter)

    def test_no_analytics_sdk_in_any_surface(self):
        """No analytics/crash/telemetry SDK in manager, website or CLI code.

        Tokens match on word boundaries so identifiers like ``setStagingTag``
        (which lowercases to contain ``gtag(``) cannot false-positive.
        """
        forbidden = ["posthog", "amplitude", "mixpanel", "segment", "sentry", "gtag", "googletagmanager", "matomo"]
        # Generic word boundaries catch identifiers, but ``segment`` is also an
        # English word ("URL segment"), so anchor it to SDK-shaped contexts:
        # an import path, a require call, or the segment.io hostname.
        overrides = {
            "segment": re.compile(r"(['\"]segment[/'\"]|require\(\s*['\"]segment|segment\.io|segment\.analytics)"),
        }
        patterns = {
            tok: overrides.get(tok, re.compile(rf"(?<![a-z0-9_]){re.escape(tok)}(?![a-z0-9_])"))
            for tok in forbidden
        }
        for base in (MANAGER_SRC, WEBSITE_SRC, CLI_SRC):
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".mjs", ".py"}:
                    continue
                blob = path.read_text(encoding="utf-8", errors="replace").lower()
                for tok, pat in patterns.items():
                    self.assertIsNone(
                        pat.search(blob),
                        f"{path.relative_to(ROOT)} references analytics SDK '{tok}' — update charter §8.2 or remove it",
                    )

    def test_package_json_declares_no_telemetry_dependency(self):
        pkg = json.loads((ROOT / "apps/manager/package.json").read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for name in deps:
            self.assertNotIn("analytics", name.lower(), f"unexpected analytics dependency: {name}")
            self.assertNotIn("telemetry", name.lower(), f"unexpected telemetry dependency: {name}")

    def test_lifecycle_snapshot_stays_in_the_documented_home(self):
        """The privacy policy names the data home; the code must agree."""
        rust = (RUST_SRC / "runtime_state.rs").read_text(encoding="utf-8")
        self.assertIn('"Emberbird"', rust)
        self.assertIn("lifecycle.json", rust)
        self.assertIn("LOCALAPPDATA", self.charter, "charter must document the data home")


class TestIntegrityPromises(unittest.TestCase):
    """The security model's promises must hold in the code it describes."""

    def setUp(self):
        self.charter = charter_text()
        self.downloader = (RUST_SRC / "downloader.rs").read_text(encoding="utf-8")

    def test_charter_promises_no_override_for_hash_mismatch(self):
        self.assertIn("no override flag", self.charter)
        # The refusal path must exist and must not be bypassable by a flag.
        self.assertIn("SHA-256 verification failed", self.downloader)
        self.assertNotIn(
            "allow_unverified", self.downloader,
            "a bypass flag appeared — update charter §8.3 or remove the flag",
        )

    def test_charter_documents_path_traversal_guard(self):
        self.assertIn("`..` segment", self.charter)
        self.assertIn("is_safe_archive_entry", self.downloader, "the named guard must exist")

    def test_registry_only_claim_has_a_test_guard(self):
        self.assertIn("registry-only", self.charter)
        guard = (ROOT / "tests" / "test_registry_consumer.py").read_text(encoding="utf-8")
        self.assertIn("NETWORK ACCESS DENIED", guard, "the network-isolation guard must exist")


class TestCharterStructure(unittest.TestCase):
    def test_charter_is_valid_markdown_with_expected_sections(self):
        text = charter_text()
        for section in (
            "## 7. What Emberbird does not guarantee",
            "## 8. Policies",
            "### 8.1 Supported configurations",
            "### 8.2 Telemetry and privacy policy",
            "### 8.3 Security model",
            "### 8.4 Release governance",
            "### 8.5 Backwards-compatibility policy",
        ):
            self.assertIn(section, text, f"charter section missing: {section}")


if __name__ == "__main__":
    unittest.main()
