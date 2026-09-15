#!/usr/bin/env python3
"""README contract tests (WO-4c, Cycle S1).

README.md is documentation of reality and must carry the 14 mandated
sections in order, reference the registry as the source of truth, never
describe planned features as active, and contain no broken relative links.

stdlib-only; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"

MANDATED_SECTIONS = [
    "Current Project Overview",
    "Supported Build Types",
    "Release Architecture",
    "Registry Architecture",
    "Repository Structure",
    "Windows 11 Build Guide",
    "Dependency Installation",
    "Developer Setup",
    "Build Instructions",
    "Validation Instructions",
    "Troubleshooting",
    "Contributing",
    "License",
    "Release Workflow",
]

SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


class TestMandatedSections(unittest.TestCase):
    def test_exactly_14_top_level_sections(self):
        titles = SECTION_RE.findall(readme_text())
        self.assertEqual(len(titles), 14, f"expected 14 sections, found {len(titles)}: {titles}")

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
