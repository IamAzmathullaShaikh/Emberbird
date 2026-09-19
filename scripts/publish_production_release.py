#!/usr/bin/env python3
"""Publish the assembled Emberbird production release to GitHub Releases.

Creates a fresh tag + draft release, uploads every dist asset with curl
streaming, then publishes the release. Reuses the credential and upload
machinery from scripts/upload_github_release_assets.py.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_github_release_assets import get_api_headers, get_github_auth  # noqa: E402

REPO_SLUG = "IamAzmathullaShaikh/Emberbird"
TAG = "Windows_11_2407.40000.4.0_v4"
TITLE = "Emberbird 2407.40000.4.0 — Standard & Banking Editions (x64 + ARM64) with Manager 0.2.2"
DIST = Path(__file__).resolve().parent.parent / "dist" / "Emberbird-WSA-2407.40000.4.0"

ASSETS = [
    "Emberbird_WSA_2407.40000.4.0_x64.7z",
    "Emberbird_WSA_2407.40000.4.0_x64_Banking.7z",
    "Emberbird_WSA_2407.40000.4.0_arm64.7z",
    "Emberbird_WSA_2407.40000.4.0_arm64_Banking.7z",
    "EmberbirdManagerSetup_0.2.2.exe",
    "EmberbirdManagerPortable_0.2.2.zip",
    "checksums.sha256",
    "checksums.sha512",
    "release-metadata.json",
    "RELEASE_NOTES.md",
]


def api(method: str, url: str, headers: dict, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else {}


def upload_curl(url: str, path: Path, headers: dict) -> dict:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    cmd = [
        "curl", "-s", "-S", "-X", "POST",
        "-H", f"Authorization: {headers['Authorization']}",
        "-H", f"Content-Type: {mime}",
        "-H", "Accept: application/vnd.github.v3+json",
        "--data-binary", f"@{path}",
        url,
    ]
    for attempt in range(3):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                data = json.loads(res.stdout)
                if "browser_download_url" in data:
                    return data
            except json.JSONDecodeError:
                pass
        print(f"    retry {attempt + 1}: {res.stdout[:200]} {res.stderr[:200]}", flush=True)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"upload failed after retries: {path.name}")


def main() -> int:
    if not DIST.is_dir():
        print(f"FATAL: dist missing: {DIST}")
        return 1
    missing = [a for a in ASSETS if not (DIST / a).is_file()]
    if missing:
        print(f"FATAL: missing assets: {missing}")
        return 1

    username, token = get_github_auth()
    headers = get_api_headers(username, token)
    owner, repo = REPO_SLUG.split("/")

    notes = (DIST / "RELEASE_NOTES.md").read_text(encoding="utf-8")

    # 1. Create the tag by pushing a release that references a new tag.
    print(f"[*] Creating draft release {TAG} ...", flush=True)
    rel = api("POST", f"https://api.github.com/repos/{owner}/{repo}/releases", headers, {
        "tag_name": TAG,
        "target_commitish": "main",
        "name": TITLE,
        "body": notes,
        "draft": True,
        "prerelease": False,
        "make_latest": "true",
    })
    print(f"    release id={rel['id']} upload_url acquired", flush=True)

    # 2. Upload all assets (skip anything already present).
    upload_base = rel["upload_url"].split("{")[0]
    existing = {a["name"] for a in rel.get("assets", [])}
    for name in ASSETS:
        if name in existing:
            print(f"    [=] {name} already present, skipping", flush=True)
            continue
        path = DIST / name
        print(f"    [+] uploading {name} ({path.stat().st_size:,} bytes)", flush=True)
        result = upload_curl(f"{upload_base}?name={urllib.parse.quote(name)}", path, headers)
        print(f"        -> {result['browser_download_url']}", flush=True)

    # 3. Publish the release.
    print("[*] Publishing release ...", flush=True)
    published = api("PATCH", f"https://api.github.com/repos/{owner}/{repo}/releases/{rel['id']}", headers, {"draft": False})

    # 4. Evidence: final asset inventory from GitHub.
    final = api("GET", f"https://api.github.com/repos/{owner}/{repo}/releases/{rel['id']}", headers)
    print(f"\n=== PUBLISHED: {final['html_url']} ===")
    print(f"draft={final['draft']} assets={len(final['assets'])}")
    total = 0
    for a in final["assets"]:
        total += a["size"]
        print(f"  {a['name']:58s} {a['size']:>12,}  state={a['state']}")
    print(f"  {'TOTAL':58s} {total:>12,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
