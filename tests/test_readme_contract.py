#!/usr/bin/env python3
"""README contract tests (WO-4c Cycle S1; evolved by E6, Metamorphosis).

README.md is documentation of reality and must carry the mandated section
structure — the metamorphosis-era contract (E6) adds Project Story, Learning
Path, Getting Started, Consumers, Roadmap, Credits/Attribution/Lineage, and
Security & Support — reference the registry as the source of truth, never
describe planned features as active, and contain no broken relative links.

stdlib-only; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"

MANDATED_SECTIONS = [
    "Hero & Project Introduction",
    "Mission",
    "Why Emberbird Exists",
    "Project Story",
    "Architecture Diagram",
    "Registry Overview",
    "Release Lifecycle",
    "Features & Supported Editions",
    "Installation Guide",
    "Quick Start",
    "Learning Path",
    "Developer Guide",
    "Contributor Guide",
    "Registry Consumers",
    "Distribution & Package Managers",
    "Security & Integrity Posture",
    "Attribution & Ancestry",
    "Historical Lineage & Preservation",
    "Support Channels & Diagnostics",
    "License & Third-Party Notices",
]

SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


class TestMandatedSections(unittest.TestCase):
    def test_exactly_20_top_level_sections(self):
        titles = SECTION_RE.findall(readme_text())
        self.assertEqual(len(titles), 20, f"expected 20 sections, found {len(titles)}: {titles}")

    def test_sections_match_mandated_order(self):
        titles = SECTION_RE.findall(readme_text())
        for i, mandated in enumerate(MANDATED_SECTIONS):
            self.assertIn(
                mandated, titles[i],
                f"section {i + 1} must be '{mandated}', found '{titles[i]}'",
            )

    def test_registry_is_declared_source_of_truth(self):
        text = readme_text()
        self.assertIn("data/releases/releases.json", text, "README must reference the registry")
        self.assertIn("Registry Independence", text)
        self.assertIn("Published Artifacts Are Truth", text)

    def test_planned_features_not_documented_as_active(self):
        text = readme_text()
        # ARM64 is planned, not shipped — this honesty must be explicit.
        self.assertTrue(
            "NOT YET AVAILABLE" in text or "not currently pre-built" in text,
            "ARM64 status must be documented as not-yet-shipped",
        )
        # The registry validate command must be documented as runnable reality.
        self.assertIn("validate", text)

    def test_sha256_verification_documented(self):
        text = readme_text()
        self.assertIn("Get-FileHash", text, "users must be shown how to verify hashes")


class TestRelativeLinks(unittest.TestCase):
    def test_all_relative_markdown_links_resolve(self):
        text = readme_text()
        broken = []
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#")[0]
            if not path_part:
                continue
            if not (REPO_ROOT / path_part).exists():
                broken.append(target)
        self.assertEqual(broken, [], f"broken relative links in README.md: {broken}")


if __name__ == "__main__":
    unittest.main()
