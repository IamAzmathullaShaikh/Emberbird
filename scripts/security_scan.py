#!/usr/bin/env python3
"""
security_scan.py — Repository Secret & Machine Path Audit Scanner for WSABuilds

Performs strict forensic security checks across all tracked repository text files:
1. Detects GitHub Personal Access Tokens (classic, OAuth, fine-grained).
2. Detects credentials embedded in URLs (e.g., https://ghp_xxx@github.com).
3. Detects developer machine paths (e.g., C:\\Users\\... or author username).
4. Automatically excludes scanner files, test fixtures, documentation, and binary assets.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Strict token regular expressions
TOKEN_PATTERNS = [
    ("GitHub Classic PAT", re.compile(r"\bghp_[A-Za-z0-9_]{36}\b")),
    ("GitHub OAuth Token", re.compile(r"\bgho_[A-Za-z0-9_]{36}\b")),
    ("GitHub Fine-Grained PAT", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b")),
    ("Embedded URL GitHub Token", re.compile(r"https://[A-Za-z0-9_:]*ghp_[A-Za-z0-9_]{36}@[a-zA-Z0-9.-]+")),
]

# Developer machine path patterns
MACHINE_PATH_PATTERNS = [
    ("Hardcoded User Profile Path", re.compile(r"[A-Za-z]:\\[Uu]sers\\[A-Za-z0-9_-]+\\", re.IGNORECASE)),
    ("Hardcoded Linux Home Path", re.compile(r"/home/[A-Za-z0-9_-]+/(?!runner\b|runneradmin\b)", re.IGNORECASE)),
    ("Developer Username", re.compile(r"\bBangerSoul\b")),
]

# Files/paths always excluded from security scans (to prevent self-triggers)
# The Gitleaks workflow legitimately contains token-format literals and the
# author-username gate, so it is excluded the same way security.yml once was.
EXCLUDED_PATHS = {
    ".github/workflows/gitleaks.yml",
    "scripts/security_scan.py",
}

# Directories excluded from machine path check (where usernames or sample paths may appear in docs/tests)
MACHINE_PATH_EXCLUDED_DIRS = [
    "docs/",
    "tests/",
    ".gemini/",
]

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".7z", ".zip", ".tar", ".gz", ".xz", ".bz2", ".cpio",
    ".exe", ".dll", ".so", ".bin", ".iso", ".img", ".vhdx",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".pyc", ".p7x", ".cer", ".crt", ".key"
}


def get_tracked_files(repo_root: Path) -> list[Path]:
    """Get list of tracked files using git ls-files."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True
        )
        return [repo_root / p.strip() for p in res.stdout.splitlines() if p.strip()]
    except Exception:
        # Fallback to filesystem walk if git is not available
        files = []
        for p in repo_root.rglob("*"):
            if p.is_file() and not any(part in p.parts for part in [".git", "output", "download", "python3-env"]):
                files.append(p)
        return files


def is_binary(file_path: Path) -> bool:
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
    except Exception:
        return True
    return False


def audit_repository(repo_root: Path) -> tuple[int, list[dict]]:
    tracked = get_tracked_files(repo_root)
    findings = []

    for file_path in tracked:
        if not file_path.is_file():
            continue

        try:
            rel_path = file_path.relative_to(repo_root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()

        # Rule 1: Exclude scanner itself and security workflow
        if rel_path in EXCLUDED_PATHS:
            continue

        # Skip binary files
        if is_binary(file_path):
            continue

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        lines = text.splitlines()

        # Check for leaked tokens
        for line_num, line in enumerate(lines, start=1):
            for label, pattern in TOKEN_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append({
                        "type": "SECRET_TOKEN",
                        "label": label,
                        "file": rel_path,
                        "line": line_num,
                        "snippet": line.strip()[:100],
                    })

        # Check for machine-specific paths (excluding docs and tests)
        is_path_exempt = any(rel_path.startswith(d) for d in MACHINE_PATH_EXCLUDED_DIRS)
        if not is_path_exempt:
            for line_num, line in enumerate(lines, start=1):
                for label, pattern in MACHINE_PATH_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        findings.append({
                            "type": "MACHINE_PATH",
                            "label": label,
                            "file": rel_path,
                            "line": line_num,
                            "snippet": line.strip()[:100],
                        })

    return len(findings), findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit repository for leaked tokens and machine paths.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root directory")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    print(f"[*] Starting Security & Secret Audit in: {repo_root}")

    count, findings = audit_repository(repo_root)

    if count == 0:
        print("[+] SUCCESS: No personal access tokens, credentials, or machine paths detected.")
        return 0

    print(f"[-] FAILURE: Found {count} security violation(s):", file=sys.stderr)
    for f in findings:
        print(f"    [{f['type']}] {f['file']}:{f['line']} — {f['label']}: {f['snippet']}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
