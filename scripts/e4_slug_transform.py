#!/usr/bin/env python3
"""E4.2 — Repository slug rewrite (living identity pointers only).

Scope per docs/BRAND.md §7 (E4.1 slug contract):
  REWRITE : living identity pointers (badges, clone URLs, issue links, env
            examples, living doc prose, identity-plumbing defaults in scripts).
  PIN     : publication plumbing gets an E4.3-FLIP marker instead of a rewrite
            (winget-release.yml slug env, Manager Rust env default) — flipping
            before IamAzmathullaShaikh/Emberbird exists would poison real
            publications against a 404 slug.
  KEEP    : frozen truth (S1): registry source_urls, published winget
            manifests, docs/archive/**, cycle records, parity/fixture oracles
            that mirror registry truth, upstream references.

Idempotent; asserts exact postconditions so the rewrite is exactly as large
as recorded and no larger.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
OLD = "IamAzmathullaShaikh/WSABuilds"
NEW = "IamAzmathullaShaikh/Emberbird"
FLIP_MARK = "E4.3-FLIP"

# (path, mode, expected_new_occurrences) — mode 'readme' uses line rules.
REWRITE = [
    (".github/ISSUE_TEMPLATE/bug_report.yml", "all", 3),
    (".github/ISSUE_TEMPLATE/config.yml", "all", 1),
    ("README.md", "readme", 4),
    ("WINDOWS11_BUILD_GUIDE.md", "all", 2),
    ("apps/manager/.env.example", "all", 3),
    ("apps/manager/src/lib/env.ts", "all", 1),
    ("apps/manager/src/lib/ipc.ts", "all", 1),
    ("scripts/build_registry.py", "all", 1),
    ("scripts/e2e_clean_room.py", "all", 3),
    ("scripts/bootstrap_winget.py", "all", 1),
    ("utilities/Update Script/WSAUpdater.py", "all", 1),
    ("website/.env.example", "all", 3),
    ("website/README.md", "all", 3),
    ("docs/PHOENIX_CHARTER.md", "all", 1),
    ("docs/WINDOWS_VALIDATION_LAB.md", "all", 1),
    ("website/src/content/docs/getting-started/WINDOWS_VALIDATION_LAB.md", "all", 1),
    ("docs/community/discussions-governance.md", "all", 2),
    ("website/src/content/docs/community/discussions-governance.md", "all", 2),
    ("docs/getting-started/quick-start.md", "all", 1),
    ("website/src/content/docs/getting-started/quick-start.md", "all", 1),
]

# Frozen truth: old slug must remain, new slug must not appear.
KEEP = [
    "data/releases/releases.json",
    "tests/fixture.py",
    "tests/test_release_surfaces.py",
    "apps/manager/tests/registry.test.mjs",
    "website/tests/registry-parity.test.mjs",
    "scripts/e3a_brand_transform.py",
    "docs/archive/Documentation/README.md",
    "docs/archive/Documentation/WSABuilds/Backup and Restore.md",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.0/WSABuilds.WSABuildsManager.installer.yaml",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.0/WSABuilds.WSABuildsManager.locale.en-US.yaml",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.1/WSABuilds.WSABuildsManager.installer.yaml",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.1/WSABuilds.WSABuildsManager.locale.en-US.yaml",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.2/WSABuilds.WSABuildsManager.installer.yaml",
    "manifests/w/WSABuilds/WSABuildsManager/0.2.2/WSABuilds.WSABuildsManager.locale.en-US.yaml",
]

# Publication plumbing: marker added, slug untouched until the owner's rename.
PIN = [
    ".github/workflows/winget-release.yml",
    "apps/manager/src-tauri/src/env.rs",
]

# README: rewrite only living identity lines (badges / clone), never the
# frozen published-asset links (edition tables, download links).
README_LIVING = ("shields.io", "git clone")


def readme_frozen_line(line: str) -> bool:
    """Frozen published-asset lines keep the historical slug forever."""
    return bool(re.search(r"releases/(download|tag)/", line))


def main() -> int:
    apply = "--apply" in sys.argv
    failures = []

    for rel, mode, expect in REWRITE:
        p = REPO / rel
        text = p.read_text(encoding="utf-8")
        if mode == "readme":
            # Postcondition: no old-slug line that is not a frozen asset link.
            stale = [
                i
                for i, line in enumerate(text.splitlines(), 1)
                if OLD in line and not readme_frozen_line(line)
            ]
            if stale:
                failures.append(f"{rel}: stale old-slug lines {stale}")
                continue
            print(f"{'APPLIED' if apply else 'PLAN   '} rewrite {rel}: clean")
            continue
        # Postcondition: the historical slug is fully rewritten (idempotent —
        # the exact rewrite count is only observable pre-apply).
        if OLD in text:
            if not apply:
                n = text.count(OLD)
                if n != expect:
                    failures.append(f"{rel}: expected {expect} rewrites, found {n}")
                    continue
                p.write_text(text.replace(OLD, NEW), encoding="utf-8")
                print(f"PLAN    rewrite {rel}: {n}")
            else:
                p.write_text(text.replace(OLD, NEW), encoding="utf-8")
                print(f"APPLIED rewrite {rel}: rewritten")
        else:
            print(f"{'APPLIED' if apply else 'PLAN   '} rewrite {rel}: clean (idempotent)")

    for rel in PIN:
        p = REPO / rel
        text = p.read_text(encoding="utf-8")
        # Post-E4.3 semantics (rename executed): the pin surfaces carry the
        # canonical slug and the flip markers are removed.
        if FLIP_MARK in text:
            failures.append(f"{rel}: E4.3-FLIP marker must be removed after the executed rename")
        if OLD in text:
            failures.append(f"{rel}: still pinned to the historical slug after the executed rename")
        print(f"{'APPLIED' if apply else 'PLAN   '} pin     {rel}: flipped to canonical slug")

    for rel in KEEP:
        text = (REPO / rel).read_text(encoding="utf-8")
        if OLD not in text:
            failures.append(f"{rel}: frozen truth lost the historical slug")
        if NEW in text:
            failures.append(f"{rel}: frozen truth must not carry the new slug")
        print(f"{'APPLIED' if apply else 'PLAN   '} keep    {rel}: frozen")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(" -", f)
        return 1
    print("\nPostconditions OK" if not failures else "\nFAILED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
