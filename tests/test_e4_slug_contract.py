#!/usr/bin/env python3
"""E4 slug-contract guard tests.

Pins the repository-identity contract after the E4.2 rewrite:
  1. Living identity surfaces carry the canonical Emberbird slug.
  2. Publication plumbing points at the canonical slug (E4.3 flip executed).
  3. Frozen truth (registry, manifests, archive, oracles) keeps the
     historical slug — GitHub's forward redirect preserves it forever.
  4. The transform tool's exact postconditions remain stable.

stdlib-only; runs in CI unchanged.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OLD = "IamAzmathullaShaikh/WSABuilds"
NEW = "IamAzmathullaShaikh/Emberbird"
FLIP_MARK = "E4.3-FLIP"

# (path, mode) — 'readme' applies the frozen-asset-link line rule.
REWRITE_SURFACES = [
    (".github/ISSUE_TEMPLATE/bug_report.yml", "all"),
    (".github/ISSUE_TEMPLATE/config.yml", "all"),
    ("README.md", "readme"),
    ("apps/manager/.env.example", "all"),
    ("apps/manager/src/lib/env.ts", "all"),
    ("apps/manager/src/lib/ipc.ts", "all"),
    ("scripts/build_registry.py", "all"),
    ("scripts/e2e_clean_room.py", "all"),
    ("scripts/bootstrap_winget.py", "all"),
    ("utilities/Update Script/WSAUpdater.py", "all"),
    ("website/.env.example", "all"),
    ("website/README.md", "all"),
    ("docs/WINDOWS_VALIDATION_LAB.md", "all"),
    ("website/src/content/docs/getting-started/WINDOWS_VALIDATION_LAB.md", "all"),
    ("docs/community/discussions-governance.md", "all"),
    ("website/src/content/docs/community/discussions-governance.md", "all"),
    ("docs/getting-started/quick-start.md", "all"),
    ("website/src/content/docs/getting-started/quick-start.md", "all"),
]

PINNED_SURFACES = [
    ".github/workflows/winget-release.yml",
    "apps/manager/src-tauri/src/env.rs",
]

FROZEN_SURFACES = [
    "data/releases/releases.json",
    "tests/fixture.py",
    "tests/test_release_surfaces.py",
    "apps/manager/tests/registry.test.mjs",
    "website/tests/registry-parity.test.mjs",
    "scripts/e3a_brand_transform.py",
    "docs/archive/Documentation/README.md",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.2/WSABuilds.WSABuildsManager.installer.yaml",
]

README_FROZEN_LINE = re.compile(r"releases/(download|tag)/")


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def readme_line_has_old_slug(line: str) -> bool:
    """Old slug on a README line that is NOT a frozen published-asset link."""
    if OLD not in line:
        return False
    return not README_FROZEN_LINE.search(line)


class TestE4SlugContract(unittest.TestCase):
    def test_02_living_surfaces_use_canonical_slug(self):
        stale = []
        for rel, mode in REWRITE_SURFACES:
            if mode == "readme":
                text = read(rel)
                for i, line in enumerate(text.splitlines(), 1):
                    if readme_line_has_old_slug(line):
                        stale.append(f"{rel}:{i}")
            elif OLD in read(rel):
                stale.append(rel)
        self.assertEqual(stale, [], f"living surfaces still carry the historical slug: {stale}")

    def test_03_publication_plumbing_flipped_to_canonical(self):
        """E4.3 executed: publication plumbing points at the canonical slug and
        the flip markers are removed (BRAND §7 status note)."""
        for rel in PINNED_SURFACES:
            text = read(rel)
            self.assertNotIn(
                FLIP_MARK, text, f"{rel} flip marker must be removed after the executed rename"
            )
            self.assertIn(NEW, text, f"{rel} must carry the canonical slug after the flip")
            self.assertNotIn(OLD, text, f"{rel} must no longer pin the historical slug")

    def test_04_frozen_truth_keeps_historical_slug(self):
        for rel in FROZEN_SURFACES:
            text = read(rel)
            self.assertIn(OLD, text, f"{rel}: frozen truth lost the historical slug")
            self.assertNotIn(NEW, text, f"{rel}: frozen truth must not carry the new slug")

    def test_05_transform_postconditions_stable(self):
        res = subprocess.run(
            [sys.executable, "scripts/e4_slug_transform.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(
            res.returncode,
            0,
            f"transform postconditions drifted:\n{res.stdout}\n{res.stderr}",
        )
        self.assertIn("Postconditions OK", res.stdout)

    def test_06_website_deploy_workflow_self_derives(self):
        """The live website must keep deriving identity from github.repository,
        so the rename heals it automatically (BRAND §7 ordering guarantee)."""
        text = read(".github/workflows/website-deploy.yml")
        self.assertIn("PUBLIC_GITHUB_REPO: ${{ github.repository }}", text)
        self.assertNotIn(OLD, text)


if __name__ == "__main__":
    unittest.main()
