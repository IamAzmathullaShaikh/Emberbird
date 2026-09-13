#!/usr/bin/env python3
"""
validate_package_identity.py — Enforce package identity regression protection

Extracts package identity parameters from AppxManifest.xml and compares them
against the verified baseline (config/baseline-identity.json) to detect and
prevent accidental identity drift, publisher alteration, or breaking changes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASELINE_DEFAULT = Path(__file__).resolve().parent.parent / "config" / "baseline-identity.json"


def extract_manifest_identity(manifest_path: Path) -> dict:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    tree = ET.parse(manifest_path)
    root = tree.getroot()

    # AppX XML namespace map
    ns = {"appx": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}

    identity_elem = root.find("appx:Identity", ns)
    if identity_elem is None:
        identity_elem = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")
    if identity_elem is None:
        raise ValueError("Could not find <Identity> tag in manifest")

    name = identity_elem.get("Name", "")
    publisher = identity_elem.get("Publisher", "")
    version = identity_elem.get("Version", "")
    arch = identity_elem.get("ProcessorArchitecture", "")

    # Dependencies
    dependencies = []
    for dep in root.iter():
        if dep.tag.endswith("PackageDependency"):
            dep_name = dep.get("Name")
            if dep_name and dep_name not in dependencies:
                dependencies.append(dep_name)

    # Standard Microsoft publisher ID hash for CN=Microsoft Corporation...
    publisher_id = "8wekyb3d8bbwe" if "CN=Microsoft Corporation" in publisher else "UNKNOWN"
    package_family_name = f"{name}_{publisher_id}"

    return {
        "package_name": name,
        "publisher": publisher,
        "publisher_id": publisher_id,
        "package_family_name": package_family_name,
        "version": version,
        "processor_architecture": arch,
        "dependencies": dependencies,
    }


def validate_identity(manifest_path: Path, baseline_path: Path) -> tuple[bool, dict]:
    identity = extract_manifest_identity(manifest_path)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    checks = []
    passed = True

    # 1. Package Name
    name_ok = (identity["package_name"] == baseline["package_name"])
    checks.append({
        "check": "package_name_match",
        "expected": baseline["package_name"],
        "actual": identity["package_name"],
        "passed": name_ok,
    })
    if not name_ok:
        passed = False

    # 2. Publisher
    pub_ok = (identity["publisher"] == baseline["publisher"])
    checks.append({
        "check": "publisher_match",
        "expected": baseline["publisher"],
        "actual": identity["publisher"],
        "passed": pub_ok,
    })
    if not pub_ok:
        passed = False

    # 3. Publisher ID
    pub_id_ok = (identity["publisher_id"] == baseline["publisher_id"])
    checks.append({
        "check": "publisher_id_match",
        "expected": baseline["publisher_id"],
        "actual": identity["publisher_id"],
        "passed": pub_id_ok,
    })
    if not pub_id_ok:
        passed = False

    # 4. Package Family Name
    pfn_ok = (identity["package_family_name"] == baseline["package_family_name"])
    checks.append({
        "check": "package_family_name_match",
        "expected": baseline["package_family_name"],
        "actual": identity["package_family_name"],
        "passed": pfn_ok,
    })
    if not pfn_ok:
        passed = False

    # 5. Version format (four quad integers)
    ver_ok = bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", identity["version"]))
    checks.append({
        "check": "version_quad_format",
        "actual": identity["version"],
        "passed": ver_ok,
    })
    if not ver_ok:
        passed = False

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path),
        "validation_passed": passed,
        "identity_extracted": identity,
        "baseline_identity": baseline,
        "checks": checks,
    }

    return passed, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WSA package identity against baseline.")
    parser.add_argument("--manifest", type=Path, help="Path to AppxManifest.xml")
    parser.add_argument("--package-dir", type=Path, help="Path to unpacked package directory")
    parser.add_argument("--baseline", type=Path, default=BASELINE_DEFAULT, help="Path to baseline identity JSON")
    parser.add_argument("--output-report", type=Path, default=Path("package-identity-report.json"), help="Output JSON report path")

    args = parser.parse_args()

    manifest_path = args.manifest
    if not manifest_path:
        if args.package_dir:
            manifest_path = args.package_dir / "AppxManifest.xml"
        else:
            # Look in MagiskOnWSA/output
            candidates = list(Path("MagiskOnWSA/output").glob("WSA_*/AppxManifest.xml"))
            if candidates:
                manifest_path = candidates[0]
            else:
                print("[-] Error: Could not locate AppxManifest.xml. Specify --manifest or --package-dir.", file=sys.stderr)
                return 2

    print(f"[*] Validating package identity: {manifest_path}")
    passed, report = validate_identity(manifest_path, args.baseline)

    args.output_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[*] Identity report generated at: {args.output_report}")

    if passed:
        print("[+] SUCCESS: Package identity matches baseline exactly. No drift detected.")
        return 0
    else:
        print("[-] FAILURE: Package identity drift detected! Release aborted.", file=sys.stderr)
        for c in report["checks"]:
            if not c["passed"]:
                print(f"    - FAILED: {c['check']} (expected '{c.get('expected')}', got '{c.get('actual')}')", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
