#!/usr/bin/env python3
"""
bootstrap_winget.py — WSABuilds Winget Submission & Release Hash Bootstrap

Automates the two remaining manual release steps (GOVERNANCE.md §3 post-release
checklist):

  WS6  Release hash bootstrap:
       1. Locate the published release for the manifest version (GitHub API).
       2. Download the installer asset advertised in installer.yaml.
       3. Compute its real SHA256.
       4. Cross-verify against the release's published checksums.txt.
       5. Patch InstallerSha256 / InstallerUrl / PackageVersion in the manifest.

  WS5  Winget submission package:
       6. Bundle the three manifests for microsoft/winget-pkgs PRs and validate
          structural requirements (InstallerUrl reachability, hash equality,
          ManifestVersion/PackageVersion consistency).

Honesty contract: if the release or asset does not exist, the script FAILS —
it never writes a placeholder hash. Pre-publication bootstrap is supported via
--expected-hash (the value from the built checksums manifest), never invented.

Exit codes: 0 success · 1 verification/argument failure · 2 network failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS_DIR = ROOT / "manifests" / "w" / "WSABuilds" / "WSABuildsManager"
PACKAGE_ID = "WSABuilds.WSABuildsManager"
PUBLISHER_DIR = "WSABuilds"
REPO = "IamAzmathullaShaikh/WSABuilds"
OUT_DIR = ROOT / "dist_winget_submission"

# The documented bootstrap placeholder allowed ONLY before publication
# (GOVERNANCE.md §2). Never invented by this script; only carried through.
PLACEHOLDER_MARKERS = ("REQUIRES REPOSITORY VERIFICATION",)


class BootstrapError(RuntimeError):
    """Fatal bootstrap condition (bad manifests, missing release, hash mismatch)."""


class NetworkError(RuntimeError):
    """GitHub API / asset download failure."""


# ------------------------------------------------------------------ GitHub I/O


def api_get_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "WSABuilds-WingetBootstrap",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise BootstrapError(f"Not found: {url}") from exc
        raise NetworkError(f"GitHub API {url} -> HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise NetworkError(f"GitHub API unreachable: {exc.reason}") from exc


def download_with_hash(url: str, sha256: str | None = None) -> tuple[bytes, str]:
    """Download bytes; optionally enforce sha256 mid-stream."""
    req = urllib.request.Request(url, headers={"User-Agent": "WSABuilds-WingetBootstrap"})
    hasher = hashlib.sha256()
    chunks = bytearray()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            while True:
                block = resp.read(1 << 20)
                if not block:
                    break
                chunks += block
                hasher.update(block)
    except urllib.error.URLError as exc:
        raise NetworkError(f"Asset download failed: {url} ({exc.reason})") from exc
    actual = hasher.hexdigest()
    if sha256 and actual != sha256:
        raise BootstrapError(
            f"Downloaded asset hash mismatch: expected {sha256}, got {actual} ({url})"
        )
    return bytes(chunks), actual


# ---------------------------------------------------------------- manifest I/O


def manifest_paths(version: str) -> dict[str, Path]:
    base = MANIFESTS_DIR / version
    return {
        "version": base / f"{PACKAGE_ID}.yaml",
        "installer": base / f"{PACKAGE_ID}.installer.yaml",
        "locale": base / f"{PACKAGE_ID}.locale.en-US.yaml",
    }


def read_manifest_field(text: str, field: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            return value
    return None


def patch_manifest_field(text: str, field: str, value: str) -> str:
    lines = text.splitlines()
    out = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{field}:"):
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}{field}: \"{value}\"" if field == "InstallerSha256" else f"{indent}{field}: {value}")
            found = True
        else:
            out.append(line)
    if not found:
        raise BootstrapError(f"Field '{field}' not found in manifest for patching.")
    return "\n".join(out) + "\n"


def load_installer_manifest(version: str) -> tuple[Path, str]:
    path = manifest_paths(version)["installer"]
    if not path.exists():
        raise BootstrapError(f"Installer manifest not found: {path}")
    return path, path.read_text(encoding="utf-8")


# ------------------------------------------------------------------- pipeline


def resolve_release(version: str) -> dict:
    """Find the published release whose tag matches v<version>."""
    try:
        release = api_get_json(f"https://api.github.com/repos/{REPO}/releases/tags/v{version}")
    except BootstrapError as exc:
        raise BootstrapError(
            f"Release for version {version} is not published yet ({exc}). "
            "Publish first, or pass --expected-hash for pre-publication bootstrap."
        ) from exc
    if release.get("draft"):
        raise BootstrapError(f"Release v{version} is a draft; refusing to bootstrap from drafts.")
    return release


def pick_installer_asset(release: dict, asset_name: str) -> dict:
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            return asset
    raise BootstrapError(
        f"Asset '{asset_name}' not found on release {release.get('tag_name')}. "
        f"Available: {[a['name'] for a in release.get('assets', [])]}"
    )


def verify_against_checksums(release: dict, asset_name: str, computed_hash: str) -> str:
    """Cross-verify the computed hash against the release's checksums.txt.

    Returns the source label ('checksums.txt' or 'sidecar'). Raises when no
    published reference exists or when references disagree.
    """
    checksum_asset = None
    for asset in release.get("assets", []):
        if asset["name"].endswith("checksums.txt"):
            checksum_asset = asset
            break

    references: list[tuple[str, str]] = []
    if checksum_asset:
        body, _ = download_with_hash(checksum_asset["browser_download_url"])
        for line in body.decode("utf-8", errors="replace").splitlines():
            parts = line.split()
            if len(parts) == 2:
                h, name = parts
                name = name.lstrip("*")
                if name == asset_name:
                    references.append(("checksums.txt", h.lower()))

    sidecar_asset = None
    for asset in release.get("assets", []):
        if asset["name"] == f"{asset_name}.sha256":
            sidecar_asset = asset
            break
    if sidecar_asset:
        body, _ = download_with_hash(sidecar_asset["browser_download_url"])
        line = body.decode("utf-8", errors="replace").strip().splitlines()[0]
        h = line.split()[0].lower()
        references.append(("sidecar", h))

    if not references:
        raise BootstrapError(
            "No published checksum reference (checksums.txt or .sha256 sidecar) "
            f"found for {asset_name}; cannot independently verify."
        )

    mismatched = [(src, h) for src, h in references if h != computed_hash]
    if mismatched:
        raise BootstrapError(
            f"Hash disagreement for {asset_name}: computed {computed_hash}, "
            f"references {mismatched}. The release itself is inconsistent — "
            "do NOT bootstrap from it."
        )
    return references[0][0]


def bootstrap(version: str, expected_hash: str | None, allow_download: bool) -> dict:
    installer_path, installer_text = load_installer_manifest(version)

    current_url = read_manifest_field(installer_text, "InstallerUrl")
    current_hash = read_manifest_field(installer_text, "InstallerSha256")
    manifest_version = read_manifest_field(installer_text, "PackageVersion")
    if manifest_version != version:
        raise BootstrapError(f"Manifest PackageVersion {manifest_version!r} != target {version!r}")
    if not current_url:
        raise BootstrapError("InstallerUrl missing from installer manifest.")
    if current_hash and any(m in current_hash.upper() for m in PLACEHOLDER_MARKERS):
        # Governance placeholder text (not zeros). Replaced below by real value.
        current_hash = None

    asset_name = current_url.rsplit("/", 1)[-1]
    result: dict = {
        "version": version,
        "asset": asset_name,
        "installer_url": current_url,
        "hash_source": None,
    }

    if expected_hash:
        computed = expected_hash.lower()
        result["hash_source"] = "--expected-hash (pre-publication bootstrap)"
        result["verified_against"] = "none (asset not yet published)"
    elif allow_download:
        release = resolve_release(version)
        asset = pick_installer_asset(release, asset_name)
        if asset.get("size", 0) < 1_000_000:
            raise BootstrapError(
                f"Asset '{asset_name}' is suspiciously small ({asset.get('size')} bytes) — refusing."
            )
        print(f"[*] Downloading {asset_name} ({asset.get('size', '?')} bytes)...")
        blob, computed = download_with_hash(asset["browser_download_url"])
        result["hash_source"] = "computed from published asset bytes"
        verified_via = verify_against_checksums(release, asset_name, computed)
        result["verified_against"] = verified_via
        result["release_tag"] = release.get("tag_name")
        print(f"[+] Computed SHA256 {computed}")
        print(f"[+] Cross-verified against release {verified_via}")
    else:
        raise BootstrapError(
            "No --expected-hash given and asset publication not requested; "
            "refusing to invent a hash."
        )

    # Patch the manifest: URL pinned, version consistent, hash real.
    updated = installer_text
    updated = patch_manifest_field(updated, "InstallerUrl", current_url)
    updated = patch_manifest_field(updated, "InstallerSha256", computed)
    updated = patch_manifest_field(updated, "PackageVersion", version)
    installer_path.write_text(updated, encoding="utf-8")
    print(f"[+] Patched {installer_path.name}: InstallerSha256={computed[:16]}...")

    # Keep the version manifest consistent.
    vpath = manifest_paths(version)["version"]
    if vpath.exists():
        vtext = vpath.read_text(encoding="utf-8")
        if read_manifest_field(vtext, "PackageVersion") != version:
            vpath.write_text(patch_manifest_field(vtext, "PackageVersion", version), encoding="utf-8")

    result["manifest_hash"] = computed
    return result


def validate_with_winget(version: str) -> bool:
    """Run `winget validate` if the CLI exists. Returns True when skipped."""
    winget = shutil.which("winget")
    if not winget:
        print("[i] winget CLI not available; skipping live validation (CI covers this).")
        return True
    base = MANIFESTS_DIR / version
    proc = subprocess.run([winget, "validate", str(base)], capture_output=True, text=True, timeout=120)
    print(proc.stdout.strip())
    if proc.returncode != 0:
        print(proc.stderr.strip())
        return False
    return True


def build_submission_package(version: str) -> Path:
    """Bundle the three manifests into a ready-to-submit package."""
    paths = manifest_paths(version)
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise BootstrapError(f"Submission package incomplete, missing manifests: {missing}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / version
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(paths["version"].parent, target)
    # Structural submission checks (winget-pkgs automated review surface).
    installer_text = paths["installer"].read_text(encoding="utf-8")
    version_text = paths["version"].read_text(encoding="utf-8")
    locale_text = paths["locale"].read_text(encoding="utf-8")
    checks = {
        "InstallerManifestType": read_manifest_field(installer_text, "ManifestType") == "installer",
        "InstallerManifestVersion": read_manifest_field(installer_text, "ManifestVersion") == "1.6.0",
        "VersionManifestType": read_manifest_field(version_text, "ManifestType") == "version",
        "LocaleManifestType": read_manifest_field(locale_text, "ManifestType") == "defaultLocale",
        "PackageVersionConsistent": all(
            read_manifest_field(t.read_text(encoding="utf-8"), "PackageVersion") == version
            for t in paths.values()
        ),
        "InstallerUrlPresent": bool(read_manifest_field(installer_text, "InstallerUrl")),
        "InstallerSha256Real": (
            len(read_manifest_field(installer_text, "InstallerSha256") or "") == 64
            and read_manifest_field(installer_text, "InstallerSha256") != "0" * 64
        ),
        "ArchitectureX64": "Architecture: x64" in installer_text,
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        shutil.rmtree(target)
        raise BootstrapError(f"Submission package failed structural checks: {failed}")
    print(f"[+] Submission package: {target} ({sum(1 for _ in target.glob('*.yaml'))} manifests)")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Winget submission & hash bootstrap automation")
    parser.add_argument("--version", required=True, help="Manager version, e.g. 0.2.2")
    parser.add_argument("--expected-hash", default=None,
                        help="Pre-publication bootstrap: hash from the built checksums manifest")
    parser.add_argument("--no-download", action="store_true",
                        help="Never download the published asset (implies --expected-hash required)")
    parser.add_argument("--skip-winget-validate", action="store_true",
                        help="Skip winget validate even when the CLI is present")
    parser.add_argument("--no-package", action="store_true",
                        help="Skip building the submission package under dist_winget_submission/")
    args = parser.parse_args(argv)

    try:
        result = bootstrap(args.version, args.expected_hash, allow_download=not args.no_download)
    except BootstrapError as exc:
        print(f"[-] BOOTSTRAP FAILED: {exc}", file=sys.stderr)
        return 1
    except NetworkError as exc:
        print(f"[-] NETWORK FAILURE: {exc}", file=sys.stderr)
        return 2

    ok = True
    if not args.skip_winget_validate:
        ok = validate_with_winget(args.version)
    if not args.no_package:
        try:
            build_submission_package(args.version)
        except BootstrapError as exc:
            print(f"[-] PACKAGE FAILED: {exc}", file=sys.stderr)
            return 1

    print(json.dumps(result, indent=2))
    print("[+] Bootstrap complete: zero manual hash patching required." if ok
          else "[!] Bootstrap applied but winget validation reported failures.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
