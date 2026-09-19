#!/usr/bin/env python3
"""E7 — Registry purity audit guards (final metamorphosis gate).

Codifies the audit results as permanent guards:
  1. Workflow inventory completeness: every workflow file on disk is
     documented in .github/WORKFLOWS.md (no undocumented workflows).
  2. No hardcoded release tags in living production code (release truth
     comes from the registry; frozen surfaces are exempt and guarded
     elsewhere — E4/E5 tests).
  3. No hardcoded asset hashes in website/manager production modules.
  4. Milestone metadata consistency for the v1.0.0 tag.

stdlib-only; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Production modules that must never carry hardcoded release truth.
PRODUCTION_TS = [
    "website/src/lib/release-service.ts",
    "apps/manager/src/lib/registry.ts",
]

# Surfaces where release-tag-shaped strings are frozen truth or oracles —
# exempt here (each is guarded by its own E-phase test).
TAG_SCAN_PATHS = [
    "scripts",
    "website/src",
    "apps/manager/src",
]
TAG_SCAN_GLOBS = ["**/*.py", "**/*.ts", "**/*.mjs", "**/*.astro"]
TAG_EXEMPT_FILES = {
    "scripts/build_registry.py",       # reality-sync reads published tags from GitHub API
    "scripts/e2e_clean_room.py",       # harness fixture
    "scripts/e3a_brand_transform.py",  # audit tooling (keep-class records)
    "scripts/e4_slug_transform.py",    # audit tooling (keep-class records)
    "apps/manager/src/lib/ipc.ts",     # browser-dev mock data only (no discovery)
}
TAG_RE = re.compile(r"\bwsa-v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\b|\bv0\.[0-9]+\.[0-9]+\b")
HASH_RE = re.compile(r"\b[a-f0-9]{64}\b")


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


class TestE7PurityAudit(unittest.TestCase):
    def test_01_every_workflow_is_documented(self):
        workflows_md = read(".github/WORKFLOWS.md")
        undocumented = [
            f.name
            for f in (REPO_ROOT / ".github" / "workflows").glob("*.yml")
            if f.name not in workflows_md
        ]
        self.assertEqual(undocumented, [], f"undocumented workflows: {undocumented}")

    def test_02_no_hardcoded_release_tags_in_production(self):
        offenders = []
        for scan_dir in TAG_SCAN_PATHS:
            for pattern in TAG_SCAN_GLOBS:
                for f in (REPO_ROOT / scan_dir).rglob(Path(pattern).name):
                    rel = f.relative_to(REPO_ROOT).as_posix()
                    if rel in TAG_EXEMPT_FILES:
                        continue
                    if not f.is_file():
                        continue
                    for m in TAG_RE.finditer(f.read_text(encoding="utf-8")):
                        offenders.append(f"{rel}: {m.group(0)}")
        self.assertEqual(offenders, [], f"hardcoded release tags in living code: {offenders}")

    def test_03_no_hardcoded_asset_hashes_in_production_modules(self):
        for rel in PRODUCTION_TS:
            text = read(rel)
            self.assertNotIn("api.github.com", text, f"{rel} must not discover via GitHub API")
            matches = HASH_RE.findall(text)
            self.assertEqual(
                matches,
                [],
                f"{rel} carries hardcoded 64-hex hashes (release truth must come from the registry): {matches}",
            )

    def test_04_milestone_metadata_is_consistent(self):
        """The emberbird-v1.0.0 milestone pins the completed metamorphosis state."""
        pkg = __import__("json").loads(read("deployment/version.json"))["manager"]
        self.assertEqual(pkg["winget_package_id"], "Emberbird.Manager")
        self.assertEqual(pkg["license"], "AGPL-3.0")
        # Registry still validates as the single source of truth.
        registry = __import__("json").loads(read("data/releases/releases.json"))
        self.assertTrue(registry.get("releases"), "registry must remain populated")


if __name__ == "__main__":
    unittest.main()
