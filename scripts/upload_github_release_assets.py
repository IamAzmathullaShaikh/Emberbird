#!/usr/bin/env python3
"""upload_github_release_assets.py — Upload packaged release artifacts to GitHub Releases.

Utilizes authenticated GitHub REST API (using credentials from git credential helper).
Uploads WSA artifacts (Standard, Banking, ARM64, and reports) to the target GitHub release.

Publication Integrity Gate (see scripts/release_integrity.py): every candidate
is classified REAL / PLACEHOLDER / UNVERIFIABLE before any network call. Only
REAL artifacts may be published, so scaffold or stub bytes can never reach the
public Releases section. Already-published assets are never overwritten unless
--replace-existing is passed explicitly.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_integrity import (  # noqa: E402
    audit_artifacts,
    collect_directory_artifacts,
    format_report,
    gate_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_github_auth() -> tuple[str, str]:
    """Retrieve GitHub username and token/password from git credential helper."""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        check=True,
    )
    lines = dict(l.split("=", 1) for l in p.stdout.splitlines() if "=" in l)
    username = lines.get("username", "")
    password = lines.get("password", "")
    if not username or not password:
        raise RuntimeError("Failed to retrieve GitHub credentials from git credential helper")
    return username, password


def get_api_headers(username: str, token: str) -> dict[str, str]:
    auth_str = base64.b64encode(f"{username}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {auth_str}",
        "User-Agent": "Emberbird-Release-Engine",
        "Accept": "application/vnd.github.v3+json",
    }


def get_release_by_tag(owner: str, repo: str, tag: str, headers: dict[str, str]) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        if err.code == 404:
            raise RuntimeError(f"Release with tag '{tag}' not found in {owner}/{repo}")
        raise RuntimeError(f"HTTP error fetching release {tag}: {err}")


def upload_asset(
    upload_url_template: str,
    file_path: Path,
    headers: dict[str, str],
    existing_assets: list[dict[str, Any]],
    owner: str,
    repo: str,
    replace_existing: bool = True,
) -> dict[str, Any]:
    """Upload a file as a release asset."""
    filename = file_path.name
    size_bytes = file_path.stat().st_size

    # Check for existing asset with identical name
    for existing in existing_assets:
        if existing["name"] == filename:
            if not replace_existing:
                print(f"  [=] Asset '{filename}' already exists, skipping upload.")
                return existing
            print(f"  [-] Asset '{filename}' exists (ID: {existing['id']}), removing to replace...")
            del_url = f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{existing['id']}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            with urllib.request.urlopen(del_req) as del_resp:
                pass
            break

    # Strip URI template parameters: {?name,label} -> ?name=...
    base_upload_url = upload_url_template.split("{")[0]
    upload_url = f"{base_upload_url}?name={urllib.parse.quote(filename)}"

    mime_type, _ = mimetypes.guess_type(str(file_path))
    content_type = mime_type or "application/octet-stream"

    upload_headers = dict(headers)
    upload_headers["Content-Type"] = content_type
    upload_headers["Content-Length"] = str(size_bytes)

    print(f"  [*] Uploading '{filename}' ({size_bytes} bytes, {content_type})...", flush=True)

    # Use curl.exe for streaming large binary files (>10MB) to prevent OpenSSL socket buffer saturation
    curl_bin = shutil.which("curl")
    if size_bytes > 10 * 1024 * 1024 and curl_bin:
        print(f"  [*] Using {curl_bin} for high-performance streaming upload...", flush=True)
        curl_cmd = [
            curl_bin,
            "-s", "-S",
            "-X", "POST",
            "-H", f"Authorization: {headers['Authorization']}",
            "-H", f"Content-Type: {content_type}",
            "-H", f"Accept: application/vnd.github.v3+json",
            "--data-binary", f"@{file_path}",
            upload_url,
        ]
        res = subprocess.run(curl_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"curl upload failed: {res.stderr}")
        try:
            data = json.loads(res.stdout)
            if "browser_download_url" in data:
                print(f"  [+] Uploaded '{filename}' successfully -> {data.get('browser_download_url', '')}", flush=True)
                return data
            raise RuntimeError(f"GitHub upload failed response: {res.stdout[:300]}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse GitHub response: {res.stdout[:300]}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    req = urllib.request.Request(upload_url, data=file_bytes, headers=upload_headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"  [+] Uploaded '{filename}' successfully -> {data.get('browser_download_url', '')}", flush=True)
            return data
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode() if err.fp else str(err)
        raise RuntimeError(f"Failed to upload '{filename}': HTTP {err.code} — {err_msg}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Upload release artifacts to GitHub Releases")
    parser.add_argument("--repo-slug", default="IamAzmathullaShaikh/Emberbird", help="Target GitHub repo (owner/repo)")
    parser.add_argument("--tag", default="Windows_11_2407.40000.4.0", help="Release tag to upload to")
    parser.add_argument("--files", nargs="+", help="Paths to files to upload")
    parser.add_argument("--all-dist", action="store_true", help="Automatically upload all built packages from dist/")
    parser.add_argument(
        "--dist-dir",
        action="append",
        type=Path,
        default=[],
        help="Upload every artifact in a packaged release directory (repeatable)",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Overwrite a published asset with the same name (OFF by default: "
        "published release history is immutable)",
    )
    parser.add_argument(
        "--force-placeholder",
        action="store_true",
        help="Bypass the Publication Integrity Gate (publishes unverified bytes; "
        "audited as a governance violation)",
    )
    parser.add_argument(
        "--gate-only",
        action="store_true",
        help="Run the Publication Integrity Gate and exit without uploading",
    )

    args = parser.parse_args(argv)

    # Integrity is checked BEFORE authentication: refusing to publish fabricated
    # bytes must never depend on having credentials.
    files_to_upload: list[Path] = []
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.is_file():
                files_to_upload.append(p)
            else:
                print(f"[!] Warning: file not found: {f}", file=sys.stderr)
    elif args.dist_dir:
        for d in args.dist_dir:
            files_to_upload.extend(collect_directory_artifacts(d))
    elif args.all_dist:
        candidates = [
            REPO_ROOT / "dist" / "release-all" / "WSA_2407.40000.4.0_x64.zip",
            REPO_ROOT / "dist" / "release-all" / "WSA_2407.40000.4.0_x64_vanilla.zip",
            REPO_ROOT / "dist" / "release-all" / "WSA_2407.40000.4.0_arm64.zip",
            REPO_ROOT / "dist" / "release-all" / "checksums.sha256",
            REPO_ROOT / "dist" / "release-all" / "checksums.sha512",
            REPO_ROOT / "dist" / "release-all" / "checksums.txt",
            REPO_ROOT / "dist" / "reports" / "live-installation-validation-report.json",
            REPO_ROOT / "dist" / "reports" / "compatibility-report.json",
            REPO_ROOT / "dist" / "reports" / "release-health-report.json",
            REPO_ROOT / "dist" / "reports" / "observatory-report.json",
        ]
        files_to_upload = [p for p in candidates if p.is_file()]

    if not files_to_upload:
        print("[-] No files to upload.", file=sys.stderr)
        return 1

    # Publication Integrity Gate — the Releases section never receives
    # fabricated or unverifiable bytes.
    verdicts = audit_artifacts(files_to_upload)
    print(format_report(verdicts))
    if not gate_report(verdicts)["passed"]:
        if not args.force_placeholder:
            print(
                "[-] REFUSING TO PUBLISH: one or more artifacts are not genuine "
                "build outputs. Build them through the CI release pipeline "
                "(.github/workflows/release.yml) instead of staging scaffolds.",
                file=sys.stderr,
            )
            return 1
        print(
            "[!] WARNING: --force-placeholder supplied. Publishing non-verified "
            "artifacts to a public release. This is recorded as a governance "
            "violation.",
            file=sys.stderr,
        )

    if args.gate_only:
        print("[+] Gate-only run complete; nothing uploaded.")
        return 0

    owner, repo = args.repo_slug.split("/", 1)
    username, password = get_github_auth()
    headers = get_api_headers(username, password)

    print(f"[*] Authenticated as GitHub user: {username}")
    print(f"[*] Resolving release for {owner}/{repo} (tag: {args.tag})...")

    rel_info = get_release_by_tag(owner, repo, args.tag, headers)
    upload_url = rel_info["upload_url"]
    existing_assets = rel_info.get("assets", [])
    print(f"[+] Found release: {rel_info.get('name')} (ID: {rel_info['id']}, existing assets: {len(existing_assets)})")

    print(f"[*] Uploading {len(files_to_upload)} artifacts to release '{args.tag}'...")
    uploaded = 0
    for fpath in files_to_upload:
        try:
            upload_asset(
                upload_url_template=upload_url,
                file_path=fpath,
                headers=headers,
                existing_assets=existing_assets,
                owner=owner,
                repo=repo,
                replace_existing=args.replace_existing,
            )
            uploaded += 1
        except Exception as err:
            print(f"[-] Error uploading {fpath.name}: {err}", file=sys.stderr)

    print(f"[+] Successfully processed {uploaded}/{len(files_to_upload)} release artifacts.")
    return 0 if uploaded == len(files_to_upload) else 1


if __name__ == "__main__":
    sys.exit(main())
