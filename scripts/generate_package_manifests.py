#!/usr/bin/env python3
"""generate_package_manifests.py — Multi-Target Package Manifest Generator (Phase P7).

Generates Winget, Scoop, and Chocolatey manifests directly from the Release Registry
vault and deployment metadata, enforcing Registry Independence and Truth Hierarchy L1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"
VERSION_JSON = REPO_ROOT / "deployment" / "version.json"


def load_manager_release_assets(version: str, registry_path: Path = REGISTRY_PATH, registry_dict: Optional[dict] = None) -> dict:
    """Retrieve published manager assets and hashes for a given version from registry."""
    if registry_dict is not None:
        registry = registry_dict
    else:
        if not registry_path.is_file():
            raise FileNotFoundError(f"Registry not found: {registry_path}")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manager_releases = [
        r for r in registry.get("releases", [])
        if r.get("kind") == "manager" and (r.get("tag") == f"v{version}" or r.get("release_id") == f"manager-{version}")
    ]

    if not manager_releases:
        raise ValueError(f"Manager release v{version} not found in registry")

    rel = manager_releases[0]
    assets = rel.get("assets", [])

    exe_asset = next((a for a in assets if a["filename"].endswith(".exe")), None)
    zip_asset = next((a for a in assets if a["filename"].endswith(".zip")), None)

    if not exe_asset and not zip_asset:
        raise ValueError(f"No executable or zip assets found for manager v{version}")

    return {
        "version": version,
        "tag": rel.get("tag", f"v{version}"),
        "published_at": rel.get("published_at", ""),
        "exe": exe_asset,
        "zip": zip_asset,
    }


def generate_scoop_manifest(assets_info: dict) -> dict:
    """Generate Scoop package manifest structure."""
    zip_asset = assets_info.get("zip") or assets_info.get("exe")
    return {
        "version": assets_info["version"],
        "description": "Desktop Subsystem Lifecycle Manager for Emberbird",
        "homepage": "https://emberbird.azmathulla.dev",
        "license": "AGPL-3.0",
        "url": zip_asset["source_url"],
        "hash": zip_asset["sha256"],
        "bin": "EmberbirdManager.exe",
        "shortcuts": [
            ["EmberbirdManager.exe", "Emberbird Manager"]
        ],
        "checkver": {
            "github": "https://github.com/IamAzmathullaShaikh/Emberbird"
        },
        "autoupdate": {
            "url": "https://github.com/IamAzmathullaShaikh/Emberbird/releases/download/v$version/WSABuildsManager-$version-portable.zip"
        }
    }


def generate_chocolatey_nuspec(assets_info: dict) -> str:
    """Generate Chocolatey .nuspec XML structure."""
    ver = assets_info["version"]
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>emberbird-manager</id>
    <version>{ver}</version>
    <title>Emberbird Manager</title>
    <authors>Emberbird Contributors, MustardChef</authors>
    <projectUrl>https://emberbird.azmathulla.dev</projectUrl>
    <licenseUrl>https://www.gnu.org/licenses/agpl-3.0.html</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <description>Desktop Subsystem Lifecycle Manager for Windows Subsystem for Android.</description>
    <tags>wsa android windows subsystem magisk root manager</tags>
  </metadata>
</package>
"""


def generate_winget_root_manifest(package_id: str, version: str) -> str:
    return f"""# Created using scripts/generate_package_manifests.py
PackageIdentifier: {package_id}
PackageVersion: {version}
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.6.0
"""


def generate_winget_default_locale_manifest(package_id: str, version: str) -> str:
    return f"""# Created using scripts/generate_package_manifests.py
PackageIdentifier: {package_id}
PackageVersion: {version}
PackageLocale: en-US
Publisher: Emberbird
PublisherUrl: https://emberbird.azmathulla.dev
PackageName: Emberbird Manager
PackageUrl: https://emberbird.azmathulla.dev
License: AGPL-3.0
LicenseUrl: https://www.gnu.org/licenses/agpl-3.0.html
ShortDescription: Desktop Subsystem Lifecycle Manager for Windows Subsystem for Android.
Description: Native lifecycle manager for Windows Subsystem for Android with verified cold VHDX snapshots, container restoration with rollback safety, and automated upgrade coordination.
Tags:
  - wsa
  - android
  - windows
  - subsystem
  - magisk
  - manager
ManifestType: defaultLocale
ManifestVersion: 1.6.0
"""


def generate_portable_manifest(assets_info: dict) -> dict:
    """Generate portable standalone package descriptor JSON."""
    zip_asset = assets_info.get("zip") or assets_info.get("exe")
    return {
        "package_id": "Emberbird.Manager.Portable",
        "version": assets_info["version"],
        "name": "Emberbird Manager Portable",
        "description": "Standalone portable deployment descriptor for Emberbird Manager",
        "architecture": "x64",
        "filename": zip_asset["filename"],
        "download_url": zip_asset["source_url"],
        "sha256": zip_asset["sha256"],
        "size_bytes": zip_asset.get("size_bytes", 0),
        "entrypoint": "EmberbirdManager.exe",
        "license": "AGPL-3.0",
        "homepage": "https://emberbird.azmathulla.dev",
    }


def generate_winget_installer_manifest(package_id: str, version: str, assets_info: dict) -> str:
    exe_asset = assets_info.get("exe")
    zip_asset = assets_info.get("zip")
    installers_yaml = ""

    if exe_asset:
        installers_yaml += f"""  - Architecture: x64
    InstallerType: nullsoft
    InstallerUrl: {exe_asset["source_url"]}
    InstallerSha256: {exe_asset["sha256"].upper()}
"""
    if zip_asset:
        installers_yaml += f"""  - Architecture: x64
    InstallerType: zip
    NestedInstallerType: portable
    NestedInstallerFiles:
      - RelativeFilePath: EmberbirdManager.exe
        PortableCommandAlias: emberbird-manager
    InstallerUrl: {zip_asset["source_url"]}
    InstallerSha256: {zip_asset["sha256"].upper()}
"""

    return f"""# Created using scripts/generate_package_manifests.py
PackageIdentifier: {package_id}
PackageVersion: {version}
Installers:
{installers_yaml}ManifestType: installer
ManifestVersion: 1.6.0
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Target Package Manifest Generator (Phase P7)")
    parser.add_argument("--version", type=str, default=None, help="Manager semver version (e.g. 0.2.2)")
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH, help="Path to releases.json")
    parser.add_argument("--target", choices=["all", "winget", "scoop", "choco", "portable"], default="all", help="Target format")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "dist" / "manifests", help="Output directory")
    parser.add_argument("--write", action="store_true", help="Write generated files to disk")

    args = parser.parse_args()

    # Resolve version
    ver = args.version
    if not ver and VERSION_JSON.is_file():
        vdata = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
        ver = vdata.get("manager_version", "0.2.2")
    if not ver:
        ver = "0.2.2"

    try:
        assets_info = load_manager_release_assets(ver, registry_path=args.registry)
    except Exception as err:
        print(f"ERROR: Failed to load manager release assets: {err}", file=sys.stderr)
        return 1

    package_id = "Emberbird.Manager"

    outputs = {}
    if args.target in ("all", "scoop"):
        outputs["scoop"] = json.dumps(generate_scoop_manifest(assets_info), indent=2)
    if args.target in ("all", "choco"):
        outputs["choco"] = generate_chocolatey_nuspec(assets_info)
    if args.target in ("all", "portable"):
        outputs["portable"] = json.dumps(generate_portable_manifest(assets_info), indent=2)
    if args.target in ("all", "winget"):
        outputs["winget_version"] = generate_winget_root_manifest(package_id, ver)
        outputs["winget_installer"] = generate_winget_installer_manifest(package_id, ver, assets_info)
        outputs["winget_locale"] = generate_winget_default_locale_manifest(package_id, ver)

    if not args.write:
        print("================================================================================")
        print(f" Package Manifest Preview for {package_id} v{ver}")
        print("================================================================================")
        for target, content in outputs.items():
            print(f"\n--- [{target.upper()}] ---")
            print(content[:500] + ("..." if len(content) > 500 else ""))
        print("================================================================================")
        print("Run with --write to persist manifests to disk.")
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if "scoop" in outputs:
        (args.output_dir / "emberbird-manager.json").write_text(outputs["scoop"], encoding="utf-8")
        print(f"[+] Wrote Scoop manifest: {args.output_dir / 'emberbird-manager.json'}")
    if "choco" in outputs:
        (args.output_dir / "emberbird-manager.nuspec").write_text(outputs["choco"], encoding="utf-8")
        print(f"[+] Wrote Chocolatey manifest: {args.output_dir / 'emberbird-manager.nuspec'}")
    if "portable" in outputs:
        (args.output_dir / "emberbird-manager-portable.json").write_text(outputs["portable"], encoding="utf-8")
        print(f"[+] Wrote Portable package descriptor: {args.output_dir / 'emberbird-manager-portable.json'}")
    if "winget_version" in outputs:
        w_dir = args.output_dir / "winget" / ver
        w_dir.mkdir(parents=True, exist_ok=True)
        (w_dir / f"{package_id}.yaml").write_text(outputs["winget_version"], encoding="utf-8")
        (w_dir / f"{package_id}.installer.yaml").write_text(outputs["winget_installer"], encoding="utf-8")
        (w_dir / f"{package_id}.locale.en-US.yaml").write_text(outputs["winget_locale"], encoding="utf-8")
        print(f"[+] Wrote Winget manifests: {w_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
