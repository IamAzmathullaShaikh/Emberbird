#!/usr/bin/env python3
"""Docs-mirror sync guard (WO-4a / legacy Task 5.3, Cycle S1).

website/src/content/docs/** is an enriched mirror of docs/** (Astro
frontmatter added for the docs collection schema). A docs/** edit that is
not reflected in the mirror lets the repository documentation and the live
portal silently diverge.

This guard is mapping-aware:
- Some files live at different paths on each side (PATH_MAP).
- Governance docs (charter, license audit, attribution, docs index) are
  intentionally unmirrored (ALLOWLIST_UNMIRRORED).

stdlib-only: jsonschema is NOT required; runs in CI unchanged.
"""
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
MIRROR = REPO_ROOT / "website" / "src" / "content" / "docs"

# Explicit path mapping: docs/ path -> mirror path (relative to docs root).
PATH_MAP = {
    "ARCHITECTURE.md": "getting-started/ARCHITECTURE.md",
    "UPGRADE_VALIDATION.md": "getting-started/UPGRADE_VALIDATION.md",
    "WINDOWS_VALIDATION_LAB.md": "getting-started/WINDOWS_VALIDATION_LAB.md",
}

# Governance/platform docs that intentionally have no website mirror.
ALLOWLIST_UNMIRRORED = {
    "README.md",  # docs/ index; the website has its own portal navigation
    "EMBERBIRD_CHARTER.md",
    "PHOENIX_CHARTER.md",
    "LICENSE_AUDIT.md",
    "ATTRIBUTION.md",
    "CLEANUP_REGISTER.md",  # platform governance evidence log
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def normalize(text: str) -> str:
    """Normalize for comparison: strip frontmatter, unify line endings,
    drop the leading H1 title line (the mirror convention moves the title
    into frontmatter `title:`), and collapse trailing whitespace so cosmetic
    diffs never fail the guard."""
    text = strip_frontmatter(text)
    text = text.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    # Mirror convention: title lives in frontmatter, H1 removed.
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip() + "\n"


def doc_files():
    return sorted(p for p in DOCS.rglob("*.md") if p.is_file())


def rel(path: Path) -> str:
    return path.relative_to(DOCS).as_posix()


def mirror_path_for(doc_rel: str) -> Path:
    mapped = PATH_MAP.get(doc_rel, doc_rel)
    return MIRROR / mapped


class TestDocsMirrorSync(unittest.TestCase):
    """Every mirrored docs/** file must match its website copy (content
    equality ignoring frontmatter and line-ending noise)."""

    def test_every_doc_is_mapped_allowlisted_or_mirrored(self):
        missing = []
        for p in doc_files():
            r = rel(p)
            if r in ALLOWLIST_UNMIRRORED:
                continue
            m = mirror_path_for(r)
            if not m.is_file():
                missing.append(r)
        self.assertEqual(
            missing, [], f"docs files with no mirror copy (add to PATH_MAP or ALLOWLIST): {missing}"
        )

    def test_mirrored_content_matches_source(self):
        stale = []
        for p in doc_files():
            r = rel(p)
            if r in ALLOWLIST_UNMIRRORED:
                continue
            m = mirror_path_for(r)
            if not m.is_file():
                continue  # reported by the structural test above
            if normalize(p.read_text(encoding="utf-8")) != normalize(m.read_text(encoding="utf-8")):
                stale.append(r)
        self.assertEqual(
            stale, [], f"mirror copies diverged from docs/ source (update website/src/content/docs/): {stale}"
        )

    def test_path_map_entries_exist_on_both_sides(self):
        for src, dst in PATH_MAP.items():
            self.assertTrue((DOCS / src).is_file(), f"PATH_MAP source missing: {src}")
            self.assertTrue((MIRROR / dst).is_file(), f"PATH_MAP target missing: {dst}")

    def test_allowlist_entries_exist(self):
        for name in ALLOWLIST_UNMIRRORED:
            self.assertTrue((DOCS / name).is_file(), f"allowlisted doc missing: {name}")

    def test_mirror_has_no_orphan_files(self):
        """Mirror files whose source was deleted must be caught too."""
        mirrored = {mirror_path_for(rel(p)).as_posix() for p in doc_files()} | {
            (MIRROR / d).as_posix() for d in PATH_MAP.values()
        }
        actual = {p.as_posix() for p in MIRROR.rglob("*.md") if p.is_file()}
        orphans = actual - mirrored
        self.assertEqual(sorted(orphans), [], f"mirror files with no docs/ source: {orphans}")


if __name__ == "__main__":
    unittest.main()
