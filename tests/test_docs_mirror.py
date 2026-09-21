#!/usr/bin/env python3
"""Docs-mirror sync guard (WO-4a / legacy Task 5.3, Cycle S1).

website/src/content/docs/** is an enriched mirror of docs/** (Astro
frontmatter added for the docs collection schema). A docs/** edit that is
not reflected in the mirror lets the repository documentation and the live
portal silently diverge.

This guard is mapping-aware:
- Some files live at different paths on each side (explicit map).
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

# Docs that intentionally have no website mirror.
ALLOWLIST_UNMIRRORED = {
    "README.md",  # docs/ index; the website has its own portal navigation
    "LICENSE_AUDIT.md",
    "ATTRIBUTION.md",
    "ADR.md",  # Architecture Decision Records register
    "CONSUMER_MATRIX.md",  # S4 consumer purity matrix (E1.5)
    "HISTORICAL_PRESERVATION.md",  # G3 historical preservation manifest (E5.5)
    "LEARNING_PATH.md",  # Role-based learning guides
    "research/ANDROID14_FEASIBILITY.md",  # Phase R1 research report (Project Genesis)
    # Generated outputs written into docs/ by scripts (release_pipeline.py,
    # validate_live_installation.py, generate_compatibility_report.py);
    # gitignored — never committed, never mirrored.
    "COMPATIBILITY_REPORT.md",
    "LIVE_INSTALLATION_REPORT.md",
    "RELEASE_HEALTH_REPORT.md",
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


def read_doc_source(path: Path) -> str:
    """Read docs/ source content. If the file has UNCOMMITTED, UNSTAGED local
    modifications (e.g., protected WIP such as ARM64 enablement), use the
    committed HEAD version if git is available, upholding the L4 Truth
    Hierarchy (committed source).

    Staged-but-uncommitted changes are NOT a fallback trigger: during a
    structural commit (e.g., E2 restructure) the staged content is the
    incoming committed truth, and comparing it against HEAD would produce a
    false divergence against mirrors carrying the same staged repair.
    """
    try:
        import subprocess

        # Unstaged diff only (no HEAD): staged repairs must not trigger the
        # HEAD fallback.
        res = subprocess.run(
            ["git", "diff", "--name-only", "--", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
            cwd=str(REPO_ROOT),
        )
        if res.returncode == 0 and res.stdout.strip():
            rel_path = path.relative_to(REPO_ROOT).as_posix()
            show = subprocess.run(
                ["git", "show", f"HEAD:{rel_path}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                cwd=str(REPO_ROOT),
            )
            if show.returncode == 0:
                return show.stdout
    except Exception:
        pass
    return path.read_text(encoding="utf-8")


def read_mirror_source(path: Path) -> str:
    """Mirror-side counterpart of read_doc_source: a mirror carrying UNSTAGED
    WIP must be compared at HEAD, so source WIP (compared at HEAD) and mirror
    WIP (compared at HEAD) remain comparable. Staged mirror content is the
    incoming truth and never triggers the fallback."""
    return read_doc_source(path)


def doc_files():
    # docs/archive/** is the frozen historical record (Documentation/ moved at
    # E2): archived docs are historical originals, not living site content -
    # they get no website mirror.
    return sorted(
        p for p in DOCS.rglob("*.md")
        if p.is_file() and "archive" not in p.parts
    )


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
            if normalize(read_doc_source(p)) != normalize(read_mirror_source(m)):
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
