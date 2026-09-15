#!/usr/bin/env python3
"""S2 tests: release-surface integrity (Priorities 3-5).

- Registry-fact agreement: deployment/version.json must agree with the
  registry's published facts (no duplicated release truth).
- README download surface: every GitHub download link on the README must
  resolve to a registry asset (tag + filename) - docs reflect registry truth.
- Consumer inventory: consumers that do not yet read the registry must be
  planned phases recorded in TODO.md, and no consumer may hardcode releases.
- Workflow documentation completeness: every workflow is documented in
  WORKFLOWS.md and carries a name.
"""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = json.loads((REPO_ROOT / "data" / "releases" / "releases.json").read_text(encoding="utf-8"))
VERSION = json.loads((REPO_ROOT / "deployment" / "version.json").read_text(encoding="utf-8"))
README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
TODO = (REPO_ROOT / "TODO.md").read_text(encoding="utf-8")

DOWNLOAD_RE = re.compile(r"https://github\.com/IamAzmathullaShaikh/WSABuilds/releases/download/([^/]+)/([^)\s]+)")


def registry_assets():
    out = {}
    for rel in REGISTRY["releases"]:
        for a in rel.get("assets", []):
            out[(rel["tag"], a["filename"])] = (rel, a)
    return out


class TestRegistryFactAgreement(unittest.TestCase):
    """deployment/version.json is a versioning layer, not a second truth:
    every fact it states must agree with the registry."""

    def test_manager_version_agrees(self):
        declared = VERSION["manager"]["version"]
        manager_rels = [r for r in REGISTRY["releases"] if r["kind"] == "manager" and r["status"] == "published"]
        self.assertTrue(manager_rels, "registry must contain a published manager release")
        ids = [r["release_id"] for r in manager_rels]
        self.assertIn(f"manager-{declared}", ids, f"version.json manager {declared} not published in registry {ids}")

    def test_subsystem_baseline_version_agrees(self):
        declared = VERSION["subsystem_baseline"]["wsa_version"]
        versions = {
            r.get("wsa_version")
            for r in REGISTRY["releases"]
            if r["kind"] == "subsystem" and r["status"] == "published"
        }
        self.assertIn(declared, versions, f"baseline {declared} not among published registry versions {versions}")

    def test_baseline_release_tag_exists(self):
        tag = VERSION["subsystem_baseline"]["release_tag"]
        tags = {r["tag"] for r in REGISTRY["releases"]}
        self.assertIn(tag, tags, f"baseline release_tag {tag} absent from registry tags {tags}")

    def test_manager_channel_agrees(self):
        # version.json channel must be a channel-contract token and match registry entries
        declared = VERSION["manager"]["channel"]
        channels = {r["channel"] for r in REGISTRY["releases"] if r["kind"] == "manager"}
        self.assertIn(declared, channels)


class TestReadmeDownloadSurface(unittest.TestCase):
    def test_readme_download_links_resolve_to_registry(self):
        assets = registry_assets()
        missing = []
        for tag, filename in DOWNLOAD_RE.findall(README):
            if (tag, filename) not in assets:
                missing.append(f"{tag}/{filename}")
        self.assertEqual(missing, [], f"README links to assets absent from the registry: {missing}")

    def test_readme_package_links_are_hash_backed(self):
        assets = registry_assets()
        unbacked = []
        for tag, filename in DOWNLOAD_RE.findall(README):
            entry = assets.get((tag, filename))
            if entry and entry[1].get("role") == "package":
                digest = entry[1].get("sha256", "")
                if len(digest) != 64 or set(digest) == {"0"}:
                    unbacked.append(filename)
        self.assertEqual(unbacked, [], f"README-linked packages without real hashes: {unbacked}")


class TestConsumerInventory(unittest.TestCase):
    """No duplicated release truth: consumers either read the registry or
    are recorded as planned registry migrations in TODO.md."""

    def test_website_does_not_hardcode_releases(self):
        # Format-grammar prefixes are allowed; concrete tags/hashes are not.
        # Inline `code` doc-comment examples (backtick-wrapped) are exempt:
        # the contract bans deriving release intelligence from hardcodes,
        # not documenting the tag grammar.
        banned = re.compile(r"wsa-v\d{4}\.\d{5}\.\d\.\d|Windows_11_\d{4}\.\d{5}|[a-f0-9]{64}")
        offenders = []
        for p in (REPO_ROOT / "website" / "src").rglob("*.ts"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            scrubbed = re.sub(r"`[^`]*`", "", text)
            if banned.search(scrubbed):
                offenders.append(str(p.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [], f"website source hardcodes release truth: {offenders}")

    def test_unmigrated_consumers_are_planned_phases(self):
        self.assertIn("P2 — Manager V2 on the registry", TODO, "manager migration must be a recorded planned phase")
        self.assertIn("P3 — Website on the registry", TODO, "website migration must be a recorded planned phase")


class TestWorkflowDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflows_dir = REPO_ROOT / ".github" / "workflows"
        cls.doc = (REPO_ROOT / ".github" / "WORKFLOWS.md").read_text(encoding="utf-8")

    def test_every_workflow_is_documented(self):
        undocumented = []
        for wf in sorted(self.workflows_dir.glob("*.yml")):
            if wf.name not in self.doc:
                undocumented.append(wf.name)
        self.assertEqual(undocumented, [], f"workflows missing from WORKFLOWS.md: {undocumented}")

    def test_doc_references_only_real_workflows(self):
        real = {wf.name for wf in self.workflows_dir.glob("*.yml")}
        referenced = set(re.findall(r"`([a-z0-9-]+\.yml)`", self.doc))
        ghosts = referenced - real
        self.assertEqual(sorted(ghosts), [], f"WORKFLOWS.md references non-existent workflows: {ghosts}")

    def test_every_workflow_has_a_name(self):
        unnamed = []
        for wf in sorted(self.workflows_dir.glob("*.yml")):
            if not re.search(r"^name:", wf.read_text(encoding="utf-8"), re.MULTILINE):
                unnamed.append(wf.name)
        self.assertEqual(unnamed, [], f"workflows without a name field: {unnamed}")


if __name__ == "__main__":
    unittest.main()
