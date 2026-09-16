#!/usr/bin/env python3
"""
check_doc_links.py — Markdown link integrity validator for WSABuilds

Scans all Markdown files in the repository, extracts relative local file links
(e.g., [Title](path/to/file.md) and href="path/to/file.md"), and verifies that
the target files exist on disk.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

# Matches standard markdown links [text](url)
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
# Matches HTML href="url" links
HREF_LINK_RE = re.compile(r'href=["\']([^"\']+)["\']')


def check_links_in_file(file_path: Path, repo_root: Path) -> list[dict]:
    errors = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")

    raw_links = []
    for match in MD_LINK_RE.finditer(text):
        raw_links.append(match.group(2))
    for match in HREF_LINK_RE.finditer(text):
        raw_links.append(match.group(1))

    for target in raw_links:
        # Strip anchor and query string
        target_clean = target.split("#")[0].split("?")[0].strip()
        if not target_clean:
            continue

        # Skip web URLs, mailto, protocol schemes
        if target_clean.startswith(("http://", "https://", "mailto:", "wsa:", "wsa-client:")):
            continue

        # URL decode path (e.g. %20 -> space)
        decoded_path = urllib.parse.unquote(target_clean)

        # Check relative to file's directory first, then repo root
        rel_to_file = file_path.parent / decoded_path
        clean_root_rel = decoded_path.lstrip("/\\")
        rel_to_root = repo_root / clean_root_rel

        # Support website portal routes (e.g. /troubleshoot/wizard, /compatibility)
        portal_page = repo_root / "website" / "src" / "pages" / f"{clean_root_rel}.astro"
        portal_index = repo_root / "website" / "src" / "pages" / clean_root_rel / "index.astro"
        portal_doc = repo_root / "docs" / f"{clean_root_rel}.md"

        exists = (
            rel_to_file.exists() or
            rel_to_root.exists() or
            portal_page.exists() or
            portal_index.exists() or
            portal_doc.exists()
        )

        if not exists:
            errors.append({
                "source_file": str(file_path.relative_to(repo_root)),
                "target_link": target,
                "resolved_attempt": str(rel_to_file),
            })

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check integrity of local links across Markdown files.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root path")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    print(f"[*] Scanning markdown files for broken local links in: {repo_root}")

    md_files = list(repo_root.glob("*.md")) + list(repo_root.glob("docs/**/*.md"))
    # Filter out temp directories
    md_files = [f for f in md_files if not any(p in f.parts for p in [".git", "download", "output", "python3-env", ".venv", "venv"])]

    all_errors = []
    checked_count = 0
    for md_file in md_files:
        checked_count += 1
        errs = check_links_in_file(md_file, repo_root)
        if errs:
            all_errors.extend(errs)

    print(f"[*] Audited {checked_count} Markdown files.")
    if all_errors:
        print(f"[-] Found {len(all_errors)} broken local link(s):", file=sys.stderr)
        for err in all_errors:
            print(f"    - {err['source_file']}: '{err['target_link']}' -> not found", file=sys.stderr)
        return 1

    print("[+] All local Markdown links verified successfully! No broken links found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
