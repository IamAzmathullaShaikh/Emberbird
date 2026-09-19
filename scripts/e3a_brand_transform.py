#!/usr/bin/env python3
"""E3A — Brand metamorphosis transform (platform identity only).

Scope: platform-identity prose only (Cycle E3A S1 review):
  REBRAND   : platform-identity prose (WSABuilds -> Emberbird) in living docs
  PATH-FIX  : stale pre-E2 paths in living build guides (E2 residue)
  KEEP      : product name "WSABuilds Manager" (E5), repo URLs & clone paths (E4),
              winget manifest paths (E5), upstream refs (S1), audit reports &
              migration prose (S1), preserved-WIP files (deferred to post-E5)

Usage:
  python scripts/e3a_brand_transform.py --dry-run   # plan + leftover scan
  python scripts/e3a_brand_transform.py --apply     # perform + verify

stdlib-only; auditable counterpart of scripts/identity_map.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Protected substrings, longest first — never rebranded at E3A.
KEEP = [
    "IamAzmathullaShaikh/WSABuilds",   # E4: repository URL (badges, clone, env)
    "MustardChef/WSABuilds",           # S1: upstream identity
    "manifests/w/WSABuilds",           # E5: published winget manifest tree
    "WSABuilds.WSABuildsManager",      # E5: winget package identity
    "WSABuildsManager",                # E5: published artifact/product filenames
    "WSABuilds Manager",               # E5: product name (kept until E5)
    "cd WSABuilds",                    # E4: clone dir name (real until E4)
    "WSABuilds/",                      # E4: repo dir in structure trees
]

# E2 residue path fixes (living build guides reference pre-restructure paths).
PATH_FIX = [
    # Live HTTP identity (E3A: identity-only phase — UA strings are ours)
    ("User-Agent': 'WSABuilds-WebClient'", "User-Agent': 'Emberbird-WebClient'"),
    ("User-Agent': 'WSABuilds-ReleaseService'", "User-Agent': 'Emberbird-ReleaseService'"),
    # License-truth fix: website footer claimed Apache-2.0; repo is AGPL-3.0
    ("Licensed under Apache-2.0. Upstream tracking: MustardChef/WSABuilds.",
     "Licensed under AGPL-3.0. Upstream tracking: MustardChef/WSABuilds."),
    ("MagiskOnWSA\\scripts\\test_runtime.py", "tools\\core\\test_runtime.py"),
    ("MagiskOnWSA/scripts/test_runtime.py", "tools/core/test_runtime.py"),
    ("MagiskOnWSA/scripts/build_local.py", "tools/build_local.py"),
    ("MagiskOnWSA/scripts/build.sh", "tools/build.sh"),
    ("MagiskOnWSA/Update Check/env_helpers", "tools/update-check/env_helpers"),
    ("Navigate to `MagiskOnWSA`", "Navigate to `tools`"),
    ("cd MagiskOnWSA", "cd tools"),
    ("MagiskOnWSA/download", "download"),
    ("MagiskOnWSA\\output", "output"),
    ("MagiskOnWSA/output", "output"),
    ("MagiskOnWSA/scripts", "tools"),  # generic fallback, after specifics
]

# Living platform surfaces whose prose is Emberbird identity from E3A on
# (website mirrors edited in lockstep with their docs/ sources — mirror guard).
REBRAND = [
    ".github/WORKFLOWS.md",
    ".github/workflows/update.yml",
    "CONTRIBUTING.md",
    "README.md",
    "compatibility/README.md",
    "scripts/README.md",
    "services/README.md",
    "website/README.md",
    "website/docs/SEARCH_INTEGRATION.md",
    "docs/README.md",
    "docs/UPGRADE_VALIDATION.md",
    "docs/WINDOWS_VALIDATION_LAB.md",
    "docs/community/compatibility-moderation.md",
    "docs/community/privacy-and-analytics.md",
    "docs/getting-started/quick-start.md",
    "website/src/content/docs/getting-started/UPGRADE_VALIDATION.md",
    "website/src/content/docs/getting-started/WINDOWS_VALIDATION_LAB.md",
    "website/src/content/docs/community/compatibility-moderation.md",
    "website/src/content/docs/community/privacy-and-analytics.md",
    "website/src/content/docs/getting-started/quick-start.md",
    # Website chrome & live HTTP identity (E3A = identity-only phase)
    "website/src/layouts/Layout.astro",
    "website/src/components/SearchModal.astro",
    "website/src/pages/downloads.astro",
    "website/src/pages/analytics.astro",
    "website/src/pages/compatibility/index.astro",
    "website/src/pages/docs/index.astro",
    "website/src/pages/docs/[...slug].astro",
    "website/src/lib/github.ts",
    "website/src/lib/release-service.ts",
    "website/src/content/compatibility/GooglePlayServices.json",
    "website/src/content/compatibility/GooglePlayStore.json",
]

# All-keep files: every occurrence is E5 product/artifact identity or S1
# upstream prose — verified no-op at E3A (revisited at E5).
NO_OP = [
    "apps/manager/README.md",
    "deployment/SPECIFICATION.md",
    ".github/workflows/manager-build.yml",
    ".github/workflows/upstream-sync.yml",
    ".github/workflows/winget-release.yml",
]

# Deferred: preserved ARM64 WIP (protected area — editing would mix the rebrand
# into unstaged work). Rebrand lands after the WIP is committed (pre-E7).
DEFERRED = [
    "docs/ARCHITECTURE.md",
    "website/src/content/docs/getting-started/ARCHITECTURE.md",
]

# Historical records & migration prose — S1: brand tokens are the history.
SKIP = [
    "REPOSITORY_AUDIT.md",
    "CLEANUP_REPORT.md",
    "REMOVED_ROOT_SOLUTIONS.md",
    "TODO.md",
    "docs/ATTRIBUTION.md",
]


def transform(text: str) -> tuple[str, dict]:
    stats = {"pathfix": 0, "rebrand": 0, "keep": 0}
    for old, new in PATH_FIX:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            stats["pathfix"] += n
    for i, keep in enumerate(KEEP):
        n = text.count(keep)
        stats["keep"] += n
        text = text.replace(keep, f"\x00KEEP{i}\x00")
    stats["rebrand"] = text.count("WSABuilds")
    text = text.replace("WSABuilds", "Emberbird")
    for i, keep in enumerate(KEEP):
        text = text.replace(f"\x00KEEP{i}\x00", keep)
    return text, stats


def leftovers(text: str) -> list[str]:
    """Report any brand token not inside a protected keep substring."""
    out = []
    for token in ("WSABuilds", "MagiskOnWSA"):
        work = text
        for keep in KEEP:
            work = work.replace(keep, "\x00")
        for old, _ in PATH_FIX:
            work = work.replace(old, "\x00")
        if token in work:
            for line in work.splitlines():
                if token in line:
                    out.append(f"{token}: {line.strip()[:120]}")
    return out


def read_raw(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_raw(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.apply == args.dry_run:
        ap.error("choose exactly one of --dry-run / --apply")

    failures = []
    for rel in REBRAND:
        path = REPO / rel
        if not path.is_file():
            failures.append(f"missing rebrand target: {rel}")
            continue
        original = read_raw(path)
        new_text, stats = transform(original)
        remain = leftovers(new_text)
        status = "OK" if not remain else "LEFTOVER"
        print(f"[{status}] {rel}: pathfix={stats['pathfix']} "
              f"rebrand={stats['rebrand']} keep={stats['keep']}")
        for line in remain:
            print(f"    ! {line}")
        if remain:
            failures.append(f"{rel}: unprotected leftovers (review above)")
        if args.apply and stats != {"pathfix": 0, "rebrand": 0, "keep": 0}:
            write_raw(path, new_text)

    for rel in NO_OP + DEFERRED + SKIP:
        path = REPO / rel
        note = "no-op (E5/S1 keeps)" if rel in NO_OP else (
            "DEFERRED (preserved WIP)" if rel in DEFERRED else "skip (S1)")
        if not path.is_file():
            failures.append(f"missing expected file: {rel}")
        print(f"[{note}] {rel}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nE3A transform " + ("applied." if args.apply else "planned (dry run)."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
