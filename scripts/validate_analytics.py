#!/usr/bin/env python3
"""
Privacy-First Analytics Validation Engine
Validates schema compliance, aggregation integrity, and Zero-PII adherence for WSABuilds metrics.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = REPO_ROOT / "services" / "analytics" / "schema.json"
METRICS_FILE = REPO_ROOT / "services" / "analytics" / "metrics.json"
COMPAT_DATA_DIR = REPO_ROOT / "compatibility" / "data"
WEBSITE_METRICS_FILE = REPO_ROOT / "website" / "src" / "content" / "analytics" / "metrics.json"

PII_FORBIDDEN_KEYS = {
    "ip",
    "ip_address",
    "client_ip",
    "user_id",
    "username",
    "email",
    "device_id",
    "mac_address",
    "telemetry_id",
    "cookie",
    "session_id",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_no_pii_keys(data, path: str = "") -> list:
    violations = []
    if isinstance(data, dict):
        for k, v in data.items():
            curr = f"{path}.{k}" if path else k
            if k.lower() in PII_FORBIDDEN_KEYS:
                violations.append(f"Forbidden PII key detected: '{curr}'")
            violations.extend(assert_no_pii_keys(v, curr))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            violations.extend(assert_no_pii_keys(item, f"{path}[{i}]"))
    return violations


def validate_analytics_schema(data: dict, schema: dict) -> list:
    errors = []
    required_sections = schema.get("required", [])
    for sec in required_sections:
        if sec not in data:
            errors.append(f"Missing required top-level section: '{sec}'")

    if "transparency_principles" in data:
        tp = data["transparency_principles"]
        if not tp.get("zero_pii"):
            errors.append("transparency_principles.zero_pii must be True")
        if not tp.get("no_ip_logging"):
            errors.append("transparency_principles.no_ip_logging must be True")

    return errors


def validate_aggregation_integrity(data: dict) -> list:
    errors = []

    # 1. Compatibility totals validation
    if "compatibility_metrics" in data:
        cm = data["compatibility_metrics"]
        total = cm.get("total_apps_tested", 0)
        c = cm.get("compatible_count", 0)
        w = cm.get("working_with_issues_count", 0)
        u = cm.get("unsupported_count", 0)

        if total != (c + w + u):
            errors.append(
                f"Compatibility total mismatch: total_apps_tested={total} != ({c} + {w} + {u})"
            )

        # Check against physical files
        if COMPAT_DATA_DIR.exists():
            physical_files = list(COMPAT_DATA_DIR.glob("*.json"))
            if total != len(physical_files):
                errors.append(
                    f"Compatibility count drift: metrics report {total} apps, but {len(physical_files)} exist in compatibility/data/"
                )

    # 2. Root flavor distribution sum check
    if "root_flavor_distribution" in data:
        rd = data["root_flavor_distribution"]
        r_sum = rd.get("magisk", 0) + rd.get("kernelsu", 0) + rd.get("none", 0)
        if r_sum != 100:
            errors.append(f"Root flavor distribution sum must equal 100% (found {r_sum}%)")

    # 3. Architecture distribution sum check
    if "architecture_distribution" in data:
        ad = data["architecture_distribution"]
        a_sum = ad.get("x64", 0) + ad.get("arm64", 0)
        if a_sum != 100:
            errors.append(f"Architecture distribution sum must equal 100% (found {a_sum}%)")

    # 4. Version adoption sum check
    if "version_adoption" in data:
        va = data["version_adoption"]
        v_sum = sum(item.get("adoption_percentage", 0) for item in va)
        if not (99.0 <= v_sum <= 101.0):
            errors.append(f"Version adoption sum must be ~100% (found {v_sum:.1f}%)")

    return errors


def main():
    print("[*] WSABuilds Privacy-First Analytics Validator")

    try:
        schema = load_json(SCHEMA_FILE)
        metrics = load_json(METRICS_FILE)
    except Exception as e:
        print(f"[-] ERROR loading JSON files: {e}")
        sys.exit(1)

    all_errors = []

    # 1. PII Scan
    pii_violations = assert_no_pii_keys(metrics)
    if pii_violations:
        all_errors.extend(pii_violations)

    # 2. Schema structure validation
    schema_errors = validate_analytics_schema(metrics, schema)
    if schema_errors:
        all_errors.extend(schema_errors)

    # 3. Aggregation integrity validation
    integrity_errors = validate_aggregation_integrity(metrics)
    if integrity_errors:
        all_errors.extend(integrity_errors)

    # 4. Website content sync check (if imported file exists)
    if WEBSITE_METRICS_FILE.exists():
        website_metrics = load_json(WEBSITE_METRICS_FILE)
        if website_metrics.get("schema_version") != metrics.get("schema_version"):
            all_errors.append("Website imported metrics schema_version out of sync with services/analytics")

    if all_errors:
        print("[-] Analytics validation FAILED with errors:")
        for err in all_errors:
            print(f"    - {err}")
        sys.exit(1)

    print("[+] Validated schema structure.")
    print("[+] Validated aggregation integrity and percentage sums.")
    print("[+] Validated Zero-PII adherence (0 forbidden keys detected).")
    print("[+] SUCCESS: Privacy-First Analytics Platform is valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
