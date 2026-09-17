#!/usr/bin/env python3
"""build_release_candidates.py — Release Candidate Builder (Epic PR1, Task PR1.1).

Orchestrates building and staging release candidates across all target editions:
  1. Standard Edition (x64 Magisk Stable + OpenGApps Pico)
  2. Banking Edition (x64 Vanilla clean ramdisk + OpenGApps Pico)
  3. Manager (Desktop Subsystem Lifecycle Manager)
  4. ARM64 Edition (Qualcomm Snapdragon X Elite / Copilot+ PC)

Produces staged directory structures ready for archive packaging and verification,
recording all build metadata into release-candidate-manifest.json.

Pure Python stdlib. Safe and deterministic.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_integrity import audit_artifacts  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_JSON = REPO_ROOT / "deployment" / "version.json"


@dataclass
class CandidateEntry:
    target: str
    edition: str
    version: str
    architecture: str
    directory: str
    file_count: int
    total_size_bytes: int
    is_mock: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "edition": self.edition,
            "version": self.version,
            "architecture": self.architecture,
            "directory": self.directory,
            "file_count": self.file_count,
            "total_size_bytes": self.total_size_bytes,
            "is_mock": self.is_mock,
            "status": self.status,
        }


def artifact_prefix() -> str:
    """Published Manager artifact prefix, derived from the identity seam
    (deployment/version.json ``manager.product_name``) — never hardcoded.

    "Emberbird Manager" -> "EmberbirdManager".
    """
    product_name = "Emberbird Manager"
    if VERSION_JSON.is_file():
        try:
            data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
            product_name = data.get("manager", {}).get("product_name", product_name)
        except Exception:
            pass
    return "".join(part for part in product_name.split() if part)


def get_default_versions() -> tuple[str, str]:
    wsa_ver = "2407.40000.4.0"
    manager_ver = "0.2.2"
    if VERSION_JSON.is_file():
        try:
            data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
            wsa_ver = data.get("subsystem_baseline", {}).get("wsa_version", wsa_ver)
            manager_ver = data.get("manager", {}).get("version", manager_ver)
        except Exception:
            pass
    return wsa_ver, manager_ver


def dir_stats(path: Path) -> tuple[int, int]:
    """Return (file_count, total_size_bytes) for directory."""
    count = 0
    size = 0
    for root, _, files in os.walk(path):
        for f in files:
            count += 1
            fp = Path(root) / f
            try:
                size += fp.stat().st_size
            except OSError:
                pass
    return count, size


def stage_mock_wsa_package(target_dir: Path, version: str, arch: str, edition: str) -> None:
    """Stage a valid unpackaged WSA directory with stripped signatures and valid AppxManifest."""
    target_dir.mkdir(parents=True, exist_ok=True)
    tools_dir = target_dir / "Tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    manifest_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         IgnorableNamespaces="uap">
  <Identity Name="MicrosoftCorporationII.WindowsSubsystemForAndroid"
            Publisher="CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US"
            Version="{version}"
            ProcessorArchitecture="{arch}" />
  <Properties>
    <DisplayName>Windows Subsystem for Android ({edition})</DisplayName>
    <PublisherDisplayName>Microsoft Corporation</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.19041.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>
</Package>
"""
    (target_dir / "AppxManifest.xml").write_text(manifest_xml, encoding="utf-8")

    install_ps1 = """# Emberbird WSA Sideload Installer
param([switch]$DryRun)
if ($DryRun) { Write-Host "Preflight check PASS"; exit 0 }
Add-AppxPackage -Register .\\AppxManifest.xml
"""
    (target_dir / "Install.ps1").write_text(install_ps1, encoding="utf-8")

    run_bat = """@echo off
powershell.exe -ExecutionPolicy Bypass -File .\\Install.ps1
pause
"""
    (target_dir / "Run.bat").write_text(run_bat, encoding="utf-8")

    # Staging initrd.img
    initrd_content = b"MAGISK_BOOT_IMG_HEADER\nROOT_STAGE=2\n" if edition == "standard" else b"CLEAN_BOOT_IMG_HEADER\nROOT_STAGE=0\n"
    (tools_dir / "initrd.img").write_bytes(initrd_content)

    # Empty placeholder files for runtime validation
    (target_dir / "filelist.txt").write_text("AppxManifest.xml\nInstall.ps1\nRun.bat\nTools/initrd.img\n", encoding="utf-8")


def build_manager_candidate(output_base: Path, version: str) -> CandidateEntry:
    """Build or stage Manager desktop candidate."""
    manager_dir = output_base / f"manager-{version}"
    manager_dir.mkdir(parents=True, exist_ok=True)

    manager_src = REPO_ROOT / "apps" / "manager"
    dist_dir = manager_src / "dist"

    # If dist doesn't exist, try npm run build
    if not dist_dir.is_dir() and shutil.which("npm"):
        try:
            subprocess.run(["npm", "--prefix", str(manager_src), "run", "build"], capture_output=True, check=True)
        except Exception:
            pass

    # Stage mock/real desktop binaries under the active published identity
    prefix = artifact_prefix()
    exe_name = f"{prefix}-Setup-{version}-x64.exe"
    zip_name = f"{prefix}-Portable-{version}-x64.zip"
    real_binaries = False

    exe_file = manager_dir / exe_name
    zip_file = manager_dir / zip_name

    if not exe_file.exists():
        exe_file.write_bytes(b"MZ_EMBERBIRD_MANAGER_DESKTOP_SETUP_BINARY_PAYLOAD_V" + version.encode())
    if not zip_file.exists():
        zip_file.write_bytes(b"PK_EMBERBIRD_MANAGER_DESKTOP_PORTABLE_ZIP_PAYLOAD_V" + version.encode())

    # Truth is decided by the Publication Integrity Gate, not by the fact that a
    # file happens to exist on disk.
    real_binaries = all(
        v.publishable for v in audit_artifacts([exe_file, zip_file])
    )

    count, size = dir_stats(manager_dir)
    return CandidateEntry(
        target="manager",
        edition="manager",
        version=version,
        architecture="x64",
        directory=str(manager_dir.relative_to(output_base)),
        file_count=count,
        total_size_bytes=size,
        is_mock=not real_binaries,
        status="BUILT" if real_binaries else "PLACEHOLDER",
    )


def build_wsa_candidate(
    output_base: Path,
    target: str,
    edition: str,
    version: str,
    arch: str,
    wsa_bundle: Optional[Path] = None,
    force_mock: bool = False,
) -> CandidateEntry:
    """Build or stage a WSA package candidate (Standard, Banking, or ARM64)."""
    dir_name = f"WSA_{version}_{arch}" + ("_vanilla" if edition == "banking" else "")
    target_dir = output_base / dir_name

    # If real bundle exists and not forced mock, try build_local.py
    built_real = False
    if wsa_bundle and wsa_bundle.is_file() and not force_mock:
        build_script = REPO_ROOT / "tools" / "build_local.py"
        cmd = [sys.executable, str(build_script), "--arch", arch, "--wsa-file", str(wsa_bundle)]
        if edition == "banking":
            cmd.extend(["--root-sol", "none"])
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and target_dir.is_dir():
            built_real = True

    if not built_real:
        stage_mock_wsa_package(target_dir, version, arch, edition)

    count, size = dir_stats(target_dir)
    return CandidateEntry(
        target=target,
        edition=edition,
        version=version,
        architecture=arch,
        directory=str(target_dir.relative_to(output_base)),
        file_count=count,
        total_size_bytes=size,
        is_mock=not built_real,
        # Truthful staging status: a scaffold candidate is never "READY" to
        # publish, and the Publication Integrity Gate refuses it downstream.
        status="BUILT" if built_real else "PLACEHOLDER",
    )


def build_all_candidates(
    targets: list[str],
    output_base: Path,
    wsa_version: Optional[str] = None,
    manager_version: Optional[str] = None,
    wsa_bundle: Optional[Path] = None,
    force_mock: bool = False,
) -> list[CandidateEntry]:
    default_wsa, default_mgr = get_default_versions()
    w_ver = wsa_version or default_wsa
    m_ver = manager_version or default_mgr

    output_base.mkdir(parents=True, exist_ok=True)
    results: list[CandidateEntry] = []

    if "standard" in targets or "all" in targets:
        results.append(build_wsa_candidate(output_base, "standard", "standard", w_ver, "x64", wsa_bundle, force_mock))

    if "banking" in targets or "all" in targets:
        results.append(build_wsa_candidate(output_base, "banking", "banking", w_ver, "x64", wsa_bundle, force_mock))

    if "arm64" in targets or "all" in targets:
        results.append(build_wsa_candidate(output_base, "arm64", "standard", w_ver, "arm64", wsa_bundle, force_mock))

    if "manager" in targets or "all" in targets:
        results.append(build_manager_candidate(output_base, m_ver))

    # Write manifest
    now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest = {
        "generated_at": now_iso,
        "output_directory": str(output_base.resolve()),
        "total_candidates": len(results),
        "candidates": [r.to_dict() for r in results],
    }
    manifest_path = output_base / "release-candidate-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Emberbird Release Candidate Builder (Epic PR1, Task PR1.1)")
    parser.add_argument("--target", choices=["all", "standard", "banking", "arm64", "manager"], default="all", help="Target edition to build")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "output", help="Output directory for staged candidates")
    parser.add_argument("--wsa-version", type=str, default=None, help="WSA version (e.g. 2407.40000.4.0)")
    parser.add_argument("--manager-version", type=str, default=None, help="Manager version (e.g. 0.2.2)")
    parser.add_argument("--wsa-bundle", type=Path, default=None, help="Path to input stock WSA MSIX/msixbundle")
    parser.add_argument("--mock", action="store_true", help="Force staged mock packages for test/CI verification")

    args = parser.parse_args(argv)

    print("================================================================================")
    print(" Emberbird Release Candidate Builder (Task PR1.1)")
    print(f" Target: {args.target} | Output: {args.output_dir}")
    print("================================================================================")

    targets = [args.target] if args.target != "all" else ["standard", "banking", "arm64", "manager"]
    candidates = build_all_candidates(
        targets=targets,
        output_base=args.output_dir,
        wsa_version=args.wsa_version,
        manager_version=args.manager_version,
        wsa_bundle=args.wsa_bundle,
        force_mock=args.mock,
    )

    for c in candidates:
        status_tag = f"[{c.status}]"
        mock_tag = "(MOCK/STAGED)" if c.is_mock else "(BUILT REAL)"
        print(f" [+] {c.target.upper():<10} -> {c.directory:<32} {status_tag} {mock_tag} ({c.file_count} files, {c.total_size_bytes} bytes)")

    print(f"\n[+] Release candidate manifest written to: {args.output_dir / 'release-candidate-manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
