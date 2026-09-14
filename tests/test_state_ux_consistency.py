#!/usr/bin/env python3
"""
test_state_ux_consistency.py — Cross-surface State & UX consistency tests (WS7).

Detects contradictions ACROSS surfaces, not just inside one app:

  1. State model contract: every state that appears in the Manager frontend
     has a backend counterpart and a UI presentation — no surface can invent
     a state the others don't know (prevents "Installed but Not Installed").
  2. Compatibility Hub: every record in compatibility/data/ has a website
     content copy and its status label is one of the three schema values —
     prevents "Banking Edition but Standard Label"-style drift.
  3. Release classification: version.json's pinned release tags classify to
     the right channel, so downloads can never render WSA assets under the
     Manager header or vice versa.
  4. Winget manifest honesty: the manifest's InstallerSha256 equals the
     checksums published on the referenced release (fetches the small
     checksums.txt only; skipped gracefully offline).
"""

import json
import re
import sys
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_STATUSES = {"Working", "Workaround Required", "Broken"}
VALID_STATES = {"NOT_INSTALLED", "INSTALLED", "INSTALLED_OUTDATED", "PARTIALLY_INSTALLED", "UNKNOWN"}


class TestStateModelContract(unittest.TestCase):
    """The five-state vocabulary must be identical across backend and frontend."""

    BACKEND_STATE_RS = ROOT / "apps" / "manager" / "src-tauri" / "src" / "state.rs"
    FRONTEND_STATE_TS = ROOT / "apps" / "manager" / "src" / "lib" / "types.ts"
    PRESENTATION_TS = ROOT / "apps" / "manager" / "src" / "lib" / "state.ts"

    def test_backend_defines_exactly_the_five_states(self):
        src = self.BACKEND_STATE_RS.read_text(encoding="utf-8")
        enum_body = src.split("pub enum SubsystemState", 1)[1].split("}", 1)[0]
        defined = set(re.findall(r"^\s*([A-Z][A-Za-z]+),", enum_body, re.M))
        expected = {"NotInstalled", "Installed", "InstalledOutdated", "PartiallyInstalled", "Unknown"}
        self.assertEqual(defined, expected)

    def test_frontend_mirrors_backend_states(self):
        src = self.FRONTEND_STATE_TS.read_text(encoding="utf-8")
        block = src.split("export type SubsystemState", 1)[1].split(";", 1)[0]
        defined = set(re.findall(r"'([A-Z_]+)'", block))
        self.assertEqual(defined, VALID_STATES)

    def test_frontend_presentation_covers_every_state(self):
        src = self.PRESENTATION_TS.read_text(encoding="utf-8")
        for state in VALID_STATES:
            self.assertIn(f"{state}:", src, f"state.ts must define a presentation for {state}")

    def test_ui_components_use_state_projection_not_raw_installed_flag(self):
        """Regression guard: components must not branch on `status.installed`
        for install-state wording (the original contradiction source)."""
        components = ROOT / "apps" / "manager" / "src" / "components"
        offenders = []
        for tsx in components.glob("*.tsx"):
            src = tsx.read_text(encoding="utf-8")
            if "projectSubsystemStatus" in src:
                continue  # correctly uses the single projection
            if re.search(r"status\.installed|status\?\.installed", src):
                offenders.append(tsx.name)
        self.assertEqual(offenders, [], f"components bypassing the state model: {offenders}")

    def test_detector_writes_state_field(self):
        src = (ROOT / "apps" / "manager" / "src-tauri" / "src" / "detector.rs").read_text(encoding="utf-8")
        self.assertIn("state: derived.state", src)
        self.assertIn("state_evidence: derived.evidence", src)


class TestCompatibilityHubConsistency(unittest.TestCase):
    DATA = ROOT / "compatibility" / "data"
    CONTENT = ROOT / "website" / "src" / "content" / "compatibility"

    def test_every_repo_record_has_website_copy(self):
        for record in sorted(self.DATA.glob("*.json")):
            if record.name == "template.json":
                continue
            copy = self.CONTENT / record.name
            self.assertTrue(copy.exists(), f"{record.name} missing from website content copy")

    def test_website_copies_are_fresh(self):
        stale = []
        for record in sorted(self.DATA.glob("*.json")):
            if record.name == "template.json":
                continue
            src = json.loads(record.read_text(encoding="utf-8"))
            copy_path = self.CONTENT / record.name
            if not copy_path.exists():
                stale.append(record.name)
                continue
            copy = json.loads(copy_path.read_text(encoding="utf-8"))
            if src != copy:
                stale.append(record.name)
        self.assertEqual(stale, [], f"website copies out of date (run import-compatibility): {stale}")

    def test_statuses_are_schema_labels(self):
        for record in sorted(self.DATA.glob("*.json")):
            data = json.loads(record.read_text(encoding="utf-8"))
            status = data.get("compatibility_status")
            self.assertIn(status, VALID_STATUSES, f"{record.name}: bad status {status!r}")

    def test_index_page_labels_match_records(self):
        """The rendered hub must show each record's exact status string — no
        relabeling ('Standard' vs 'Banking' style drift)."""
        page = (ROOT / "website" / "src" / "pages" / "compatibility" / "index.astro").read_text(encoding="utf-8")
        self.assertIn("record.compatibility_status", page,
                      "hub must render the record's status verbatim")


class TestReleaseClassificationConsistency(unittest.TestCase):
    VERSION_JSON = ROOT / "deployment" / "version.json"

    def test_pinned_tags_classify_to_expected_channels(self):
        data = json.loads(self.VERSION_JSON.read_text(encoding="utf-8"))
        wsa_tag = data.get("subsystem_baseline", {}).get("release_tag")
        self.assertTrue(wsa_tag and wsa_tag.startswith("wsa-v"),
                        f"subsystem_baseline.release_tag must be a wsa-v* tag, got {wsa_tag!r}")

        # Mirror of website release-service classification (no JS runtime needed).
        def classify(tag: str) -> str:
            return "wsa" if tag.startswith("wsa-v") else "manager"

        self.assertEqual(classify(wsa_tag), "wsa")
        self.assertEqual(classify(f"v{data['manager']['version']}"), "manager")

    def test_release_service_keeps_pinned_classification(self):
        src = (ROOT / "website" / "src" / "lib" / "release-service.ts").read_text(encoding="utf-8")
        self.assertIn("startsWith('wsa-v')", src)
        self.assertNotIn("releases/latest", src.split("class PinnedReleaseService")[1].split("}")[1]
                         if "class PinnedReleaseService" in src else "",
                         "pinned service must not fall back to releases/latest")


class TestWingetManifestHonesty(unittest.TestCase):
    """Manifest hash must equal the hash published on the referenced release."""

    def test_installer_manifest_hash_matches_published_checksums(self):
        manifests = sorted((ROOT / "manifests" / "w" / "WSABuilds" / "WSABuildsManager").glob("*"))
        self.assertTrue(manifests)
        version_dir = manifests[-1]
        installer = version_dir / "WSABuilds.WSABuildsManager.installer.yaml"
        text = installer.read_text(encoding="utf-8")
        url = re.search(r"InstallerUrl:\s*(\S+)", text).group(1)
        sha = re.search(r"InstallerSha256:\s*\"?([a-f0-9]{64})", text).group(1)

        self.assertNotEqual(sha, "0" * 64, "placeholder zero hash in published manifest")

        # checksums.txt sits next to the installer asset in the release.
        # The tag carries a `v` prefix; the checksums filename does not.
        tag = re.search(r"/download/([^/]+)/", url).group(1)
        version = tag.lstrip("v")
        checksums_url = re.sub(r"/download/[^/]+/.*$",
                               f"/download/{tag}/WSABuildsManager-{version}-checksums.txt", url)
        req = urllib.request.Request(checksums_url, headers={"User-Agent": "WSABuilds-Consistency"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # offline CI environments skip gracefully
            self.skipTest(f"cannot reach {checksums_url}: {exc}")

        asset_name = url.rsplit("/", 1)[-1]
        published = None
        for line in body.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1].lstrip("*") == asset_name:
                published = parts[0].lower()
        self.assertIsNotNone(published, f"{asset_name} not listed in {checksums_url}")
        self.assertEqual(published, sha,
                         "manifest InstallerSha256 must equal the published checksum")


if __name__ == "__main__":
    unittest.main()
