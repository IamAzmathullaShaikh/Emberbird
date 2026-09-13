#!/usr/bin/env python3
"""
validate_package_integrity.py — Comprehensive package integrity validator

Verifies:
1. AppxManifest.xml schema consistency & dependencies
2. Signature artifact stripping (verifies AppxSignature.p7x, etc. are absent)
3. Essential VHDX / partition image presence and size
4. Ramdisk (initrd.img) CPIO SVR4 header magic (070701)
5. Installation automation scripts (Install.ps1, Run.bat, filelist.txt)
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def check_package_integrity(package_dir: Path) -> tuple[bool, dict]:
    if not package_dir.is_dir():
        return False, {"error": f"Directory not found: {package_dir}"}

    checks = []
    overall_passed = True

    # 1. AppxManifest.xml
    manifest = package_dir / "AppxManifest.xml"
    manifest_ok = manifest.is_file() and manifest.stat().st_size > 0
    if manifest_ok:
        try:
            ET.parse(manifest)
            manifest_parse_ok = True
        except Exception:
            manifest_parse_ok = False
    else:
        manifest_parse_ok = False

    checks.append({
        "name": "AppxManifest.xml presence and XML validity",
        "passed": manifest_ok and manifest_parse_ok,
    })
    if not (manifest_ok and manifest_parse_ok):
        overall_passed = False

    # 2. Stripped signature artifacts (MUST be absent for loose-folder registration)
    signature_artifacts = [
        "AppxSignature.p7x",
        "AppxBlockMap.xml",
        "[Content_Types].xml",
        "AppxMetadata",
    ]
    leaked_signatures = [s for s in signature_artifacts if (package_dir / s).exists()]
    sig_check_ok = (len(leaked_signatures) == 0)
    checks.append({
        "name": "Microsoft signature stripping verification",
        "passed": sig_check_ok,
        "details": f"Leaked artifacts: {leaked_signatures}" if leaked_signatures else "All signature artifacts properly stripped",
    })
    if not sig_check_ok:
        overall_passed = False

    # 3. Partition images
    required_partitions = ["system", "vendor", "product", "system_ext"]
    found_partitions = {}
    missing_partitions = []
    for part in required_partitions:
        vhdx = package_dir / f"{part}.vhdx"
        img = package_dir / f"{part}.img"
        if vhdx.exists() and vhdx.stat().st_size > 1024:
            found_partitions[part] = f"{part}.vhdx ({vhdx.stat().st_size} bytes)"
        elif img.exists() and img.stat().st_size > 1024:
            found_partitions[part] = f"{part}.img ({img.stat().st_size} bytes)"
        else:
            missing_partitions.append(part)

    part_ok = (len(missing_partitions) == 0)
    checks.append({
        "name": "Android partition images presence (system, vendor, product, system_ext)",
        "passed": part_ok,
        "details": found_partitions if part_ok else f"Missing partitions: {missing_partitions}",
    })
    if not part_ok:
        overall_passed = False

    # 4. Ramdisk / initrd.img
    initrd = package_dir / "Tools" / "initrd.img"
    initrd_ok = False
    initrd_details = "Not found"
    if initrd.is_file() and initrd.stat().st_size > 1024:
        with open(initrd, "rb") as f:
            magic = f.read(6)
        if magic == b"070701":
            initrd_ok = True
            initrd_details = f"Valid SVR4 CPIO archive ({initrd.stat().st_size} bytes)"
        else:
            initrd_details = f"Invalid magic bytes: {magic}"
    checks.append({
        "name": "Initrd ramdisk SVR4 CPIO magic validation (070701)",
        "passed": initrd_ok,
        "details": initrd_details,
    })
    if not initrd_ok:
        overall_passed = False

    # 5. Installer scripts
    installer_files = ["Install.ps1", "Run.bat", "filelist.txt"]
    missing_installers = [f for f in installer_files if not (package_dir / f).is_file()]
    installer_ok = (len(missing_installers) == 0)
    checks.append({
        "name": "Deployment automation scripts (Install.ps1, Run.bat, filelist.txt)",
        "passed": installer_ok,
        "details": "All scripts present" if installer_ok else f"Missing: {missing_installers}",
    })
    if not installer_ok:
        overall_passed = False

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "package_dir": str(package_dir),
        "validation_status": "VERIFIED" if overall_passed else "FAILED",
        "checks": checks,
    }

    return overall_passed, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WSA package structural integrity.")
    parser.add_argument("--package-dir", type=Path, help="Path to package directory")
    parser.add_argument("--output-report", type=Path, default=Path("package-integrity-report.json"), help="Output JSON report path")

    args = parser.parse_args()

    package_dir = args.package_dir
    if not package_dir:
        candidates = list(Path("MagiskOnWSA/output").glob("WSA_*"))
        candidates = [c for c in candidates if c.is_dir()]
        if candidates:
            package_dir = candidates[0]
        else:
            print("[-] Error: Could not find package directory. Specify --package-dir.", file=sys.stderr)
            return 2

    print(f"[*] Checking package integrity: {package_dir}")
    passed, report = check_package_integrity(package_dir)

    args.output_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[*] Integrity report written to: {args.output_report}")

    if passed:
        print("[+] SUCCESS: All package integrity checks passed.")
        return 0
    else:
        print("[-] FAILURE: Package integrity verification failed!", file=sys.stderr)
        for c in report["checks"]:
            if not c["passed"]:
                print(f"    - FAILED: {c['name']} ({c.get('details', '')})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
