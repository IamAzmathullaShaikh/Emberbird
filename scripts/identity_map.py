#!/usr/bin/env python3
"""identity_map.py — Emberbird Metamorphosis Programme (Phase E1).

Scans every tracked text file for identity tokens (WSABuilds, MagiskOnWSA,
MagiskOnWSALocal) and produces a CLASSIFIED inventory:

    docs/identity-inventory.json

Every occurrence is marked with one of the classes used by the programme's
brand policy (docs/BRAND.md):

    upstream-attribution  protected forever (S1 — attribution/licensing/provenance)
    historical-doc        protected historical documentation (S1)
    package-name          npm/winget package identity (E5 changes via new packages)
    workflow-name         GitHub Actions workflow identities
    url                   repository URLs (E4 rewrites)
    path-reference        filesystem paths (E2 remaps)
    user-facing           display names / UI copy / README headings (E3A rebrand)
    doc-prose             markdown body text (E3A rebrand, S1-reviewed)
    identifier            code identifiers / config values (case-by-case)

The inventory is the auditable basis for every later metamorphosis step:
nothing is renamed, moved, or rewritten without a record here.

Usage:
    python scripts/identity_map.py                 # regenerate the inventory
    python scripts/identity_map.py --summary       # print per-class summary
    python scripts/identity_map.py --check         # exit 1 if inventory is stale

stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "identity-inventory.json"

TOKENS = ("WSABuilds", "MagiskOnWSALocal", "MagiskOnWSA")  # longest-first matching
TOKEN_RE = re.compile("|".join(re.escape(t) for t in TOKENS))
URL_RE = re.compile(r"https?://[^\s)\"'<>]*")
PATHISH_RE = re.compile(r"[A-Za-z0-9_.\-/\\]*%s[A-Za-z0-9_.\-/\\]*" % "|".join(re.escape(t) for t in TOKENS))

TEXT_SUFFIXES = {
    ".md", ".json", ".yml", ".yaml", ".ts", ".tsx", ".js", ".mjs", ".cjs",
    ".py", ".html", ".css", ".scss", ".sh", ".toml", ".txt", ".xml", ".svg",
}

ATTRIBUTION_FILES = {"docs/ATTRIBUTION.md", "docs/LICENSE_AUDIT.md"}
LICENSE_FILES = {"LICENSE", "LICENSE-CC-BY-NC-ND"}
ATTRIBUTION_TOKENS = ("MustardChef", "MagiskOnWSALocal", "GNU AFFERO", "upstream")

HISTORICAL_DOC_ROOTS = ("Documentation/",)
PACKAGE_CONTEXT_FILES = ("package.json", "package-lock.json")
WORKFLOW_ROOT = ".github/workflows/"


def tracked_files() -> list[str]:
    """Tracked text files (git ls-files; falls back to a filtered walk)."""
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True,
            check=True, timeout=30,
        ).stdout.splitlines()
        files = [REPO_ROOT / f for f in out]
    except (OSError, subprocess.SubprocessError):
        files = []
        skip = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".astro", "coverage"}
        for root, dirs, names in os.walk(REPO_ROOT):
            dirs[:] = [d for d in dirs if d not in skip]
            for n in names:
                files.append(Path(root) / n)
    return sorted(
        p for p in files
        if p.suffix.lower() in TEXT_SUFFIXES
        and p.is_file()
        and rel(p) != rel(DEFAULT_OUTPUT)  # never scan our own output (self-scan ratchet)
    )


def read_content(path: Path) -> str:
    """Read file content from the git INDEX (staged tree) when available.

    The inventory documents COMMITTED-boundary reality: content comes from
    the index (`git show :<path>`), which equals HEAD in a clean CI checkout.
    This makes the inventory immune to uncommitted working-tree changes
    (e.g. preserved ARM64 WIP) — the defect that broke CI at e22f6d1.
    Run `git add` before regenerating so staged content is what is measured.
    """
    try:
        out = subprocess.run(
            ["git", "show", f":{rel(path)}"],
            cwd=REPO_ROOT, capture_output=True, check=True, timeout=30,
        )
        # decode manually: text=True would use the OS codepage (cp1252 on
        # Windows) and crash on UTF-8 content beyond it
        return out.stdout.decode("utf-8", errors="ignore")
    except (OSError, subprocess.SubprocessError):
        return path.read_text(encoding="utf-8", errors="ignore")


def rel(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix().replace("\\", "/")


def classify(path: str, line: str, match: re.Match) -> str:
    """Ordered classification rules (first match wins)."""
    if path in LICENSE_FILES or path in ATTRIBUTION_FILES:
        return "upstream-attribution"
    if path.startswith(HISTORICAL_DOC_ROOTS):
        return "historical-doc"
    if any(tok in line for tok in ATTRIBUTION_TOKENS) and path.endswith(".md"):
        return "upstream-attribution"
    if path.startswith(WORKFLOW_ROOT):
        return "workflow-name"
    if path.endswith(tuple(PACKAGE_CONTEXT_FILES)) or path.startswith("manifests/"):
        return "package-name"
    for url in URL_RE.findall(line):
        if match.group(0) in url:
            return "url"
    span = PATHISH_RE.match(line, match.start())
    if span and ("www" in span.group(0).lower() or match.group(0) in span.group(0)):
        # the occurrence sits inside a longer path-like string
        if "/" in span.group(0) or "\\" in span.group(0) or span.group(0) != match.group(0):
            return "path-reference"
    if path == "README.md" or path.startswith("website/src/content/"):
        return "user-facing"
    if path.endswith(".md"):
        return "doc-prose"
    return "identifier"


def build_inventory() -> dict:
    files_out = []
    token_counts: dict[str, int] = {}
    class_counts: dict[str, int] = {}

    for path in tracked_files():
        rp = rel(path)
        try:
            text = read_content(path)
        except OSError:
            continue
        occurrences = []
        # NOTE: no line numbers by design. A file generated from the index can
        # never be line-fresh against a commit that contains itself plus any
        # line-shifting edit (the line-drift ratchet that broke CI). Token,
        # class, and context are content-derived and shift-immune.
        for line in text.splitlines():
            for match in TOKEN_RE.finditer(line):
                token = match.group(0)
                cls = classify(rp, line, match)
                occurrences.append({
                    "token": token,
                    "class": cls,
                    "context": line.strip()[:180],
                })
                token_counts[token] = token_counts.get(token, 0) + 1
                class_counts[cls] = class_counts.get(cls, 0) + 1
        if occurrences:
            # canonical order: the artifact must be byte-identical regardless of
            # platform scan order (Windows vs Linux walk order was observed to
            # differ, which alone re-staled the committed inventory)
            occurrences.sort(key=lambda o: (o["token"], o["class"], o["context"]))
            files_out.append({"path": rp, "count": len(occurrences), "occurrences": occurrences})

    # canonical dicts: totals must not carry platform insertion order
    token_counts = dict(sorted(token_counts.items()))
    class_counts = dict(sorted(class_counts.items()))
    # canonical file order: sort by the rel-path STRING. Sorting Path objects
    # is case-insensitive on Windows and case-sensitive on POSIX, which made
    # the committed inventory's file-list order platform-dependent (the last
    # hidden divergence; list order survives json.dumps sort_keys).
    files_out.sort(key=lambda f: f["path"])
    protected = class_counts.get("upstream-attribution", 0) + class_counts.get("historical-doc", 0)
    return {
        "tool": "scripts/identity_map.py",
        "programme": "Project Emberbird — Metamorphosis Programme v3 (Phase E1)",
        "rules": {
            "m4": "Release History Is Immutable",
            "s1": "Historical Identity Preservation — Emberbird may replace branding; it may not erase history",
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": {
            "files": len(files_out),
            "occurrences": sum(token_counts.values()),
            "by_token": token_counts,
            "by_class": class_counts,
            "protected_occurrences": protected,
        },
        "files": files_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Classified identity inventory for the Emberbird metamorphosis")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--summary", action="store_true", help="print the per-class summary")
    ap.add_argument("--check", action="store_true", help="exit 1 if the committed inventory differs from a fresh scan")
    args = ap.parse_args()

    inventory = build_inventory()
    payload = json.dumps(inventory, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        # timestamps differ by design; compare everything else
        def without_ts(s: str) -> str:
            d = json.loads(s)
            d.pop("generated_at", None)
            return json.dumps(d, sort_keys=True, ensure_ascii=False)
        if without_ts(current) != without_ts(payload):
            print("STALE: docs/identity-inventory.json does not match the current tree — regenerate it.", file=sys.stderr)
            # precision diagnostics: where exactly do committed vs fresh scans differ?
            try:
                committed = json.loads(current)
                fresh = json.loads(payload)
                cfiles = {f["path"]: f["count"] for f in committed.get("files", [])}
                ffiles = {f["path"]: f["count"] for f in fresh.get("files", [])}
                for path in sorted(set(cfiles) | set(ffiles)):
                    c, n = cfiles.get(path), ffiles.get(path)
                    if c != n:
                        print(f"DIFF file: {path}: committed={c} fresh={n}", file=sys.stderr)
                ct, ft = committed.get("totals", {}), fresh.get("totals", {})
                print(f"DIFF totals: committed={ct.get('occurrences')} fresh={ft.get('occurrences')}", file=sys.stderr)
                print(f"DIFF classes: committed={ct.get('by_class')} fresh={ft.get('by_class')}", file=sys.stderr)
                cocc = {f["path"]: f.get("occurrences", []) for f in committed.get("files", [])}
                focc = {f["path"]: f.get("occurrences", []) for f in fresh.get("files", [])}
                shown = 0
                for path in sorted(set(cocc) | set(focc)):
                    if shown >= 5:
                        print("DIFF occurrences: ...more suppressed", file=sys.stderr)
                        break
                    a, b = cocc.get(path), focc.get(path)
                    if a != b:
                        print(f"DIFF occurrences in {path}: committed={len(a or [])} fresh={len(b or [])}", file=sys.stderr)
                        for i in range(max(len(a or []), len(b or []))):
                            ea = (a or [])[i] if i < len(a or []) else None
                            eb = (b or [])[i] if i < len(b or []) else None
                            if ea != eb:
                                print(f"  first diff at [{i}]:", file=sys.stderr)
                                print(f"    committed: {json.dumps(ea, ensure_ascii=False)[:200]}", file=sys.stderr)
                                print(f"    fresh:     {json.dumps(eb, ensure_ascii=False)[:200]}", file=sys.stderr)
                                break
                        shown += 1
            except Exception as diag_exc:  # diagnostics must never mask the primary failure
                print(f"DIFF diagnostics unavailable: {diag_exc}", file=sys.stderr)
            return 1
        print(f"INVENTORY OK: {inventory['totals']['occurrences']} occurrences, "
              f"{inventory['totals']['files']} files, "
              f"{inventory['totals']['protected_occurrences']} protected")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8", newline="\n")
    if args.summary:
        for cls, n in sorted(inventory["totals"]["by_class"].items()):
            print(f"{cls:22} {n}")
        print("-" * 30)
        print(f"{'TOTAL':22} {inventory['totals']['occurrences']}")
    else:
        print(f"inventory written: {args.output.relative_to(REPO_ROOT)} "
              f"({inventory['totals']['occurrences']} occurrences in {inventory['totals']['files']} files, "
              f"{inventory['totals']['protected_occurrences']} protected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
