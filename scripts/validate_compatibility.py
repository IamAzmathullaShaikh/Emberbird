#!/usr/bin/env python3
"""
validate_compatibility.py — WSA Application Compatibility Record Validator

Validates JSON records against compatibility/schema.json schema constraints.
Supports standalone validation using Python standard library with optional
jsonschema acceleration.
"""

import sys
import os
import json
import re
from pathlib import Path

PACKAGE_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$')

ALLOWED_CATEGORIES = {
    "Banking & UPI",
    "Social & Communication",
    "Communication",
    "Productivity & Office",
    "Productivity",
    "Streaming & Media",
    "Gaming",
    "Utilities & Tools"
}

ALLOWED_STATUSES = {
    "Working",
    "Workaround Required",
    "Broken"
}

ALLOWED_VERIFICATION = {
    "verified",
    "unverified",
    "community_submitted"
}

ALLOWED_CHANNELS = {
    "retail",
    "stable",
    "RP",
    "WIS",
    "WIF"
}

REQUIRED_FIELDS = [
    "app_name",
    "package_id",
    "category",
    "compatibility_status",
    "play_integrity_required",
    "tested_wsa_version",
    "tested_root_flavor",
    "verification_status"
]

ALLOWED_FIELDS = set(REQUIRED_FIELDS) | {
    "$schema",
    "tested_channel",
    "last_tested_date",
    "workaround_steps",
    "known_issues"
}


def validate_record_data(data, filepath):
    errors = []
    
    if not isinstance(data, dict):
        return [f"{filepath}: Root element must be a JSON object."]

    # Check unknown fields
    for k in data.keys():
        if k not in ALLOWED_FIELDS:
            errors.append(f"{filepath}: Unrecognized field '{k}' not permitted by schema.")

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"{filepath}: Missing required field '{field}'.")

    if errors:
        return errors

    # Field-specific validations
    app_name = data.get("app_name")
    if not isinstance(app_name, str) or len(app_name.strip()) == 0 or len(app_name) > 100:
        errors.append(f"{filepath}: 'app_name' must be a non-empty string <= 100 characters.")

    package_id = data.get("package_id")
    if not isinstance(package_id, str) or not PACKAGE_REGEX.match(package_id):
        errors.append(f"{filepath}: 'package_id' ('{package_id}') is invalid. Must be valid reverse-DNS format.")

    category = data.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(f"{filepath}: 'category' ('{category}') is invalid. Allowed: {sorted(list(ALLOWED_CATEGORIES))}")

    status = data.get("compatibility_status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"{filepath}: 'compatibility_status' ('{status}') is invalid. Allowed: {sorted(list(ALLOWED_STATUSES))}")

    play_integrity = data.get("play_integrity_required")
    if not isinstance(play_integrity, bool):
        errors.append(f"{filepath}: 'play_integrity_required' must be a boolean.")

    wsa_version = data.get("tested_wsa_version")
    if not isinstance(wsa_version, str) or len(wsa_version.strip()) == 0:
        errors.append(f"{filepath}: 'tested_wsa_version' must be a non-empty string.")

    root_flavor = data.get("tested_root_flavor")
    if not isinstance(root_flavor, str) or len(root_flavor.strip()) == 0:
        errors.append(f"{filepath}: 'tested_root_flavor' must be a non-empty string.")

    verification = data.get("verification_status")
    if verification not in ALLOWED_VERIFICATION:
        errors.append(f"{filepath}: 'verification_status' ('{verification}') is invalid. Allowed: {sorted(list(ALLOWED_VERIFICATION))}")

    if "workaround_steps" in data:
        steps = data["workaround_steps"]
        if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
            errors.append(f"{filepath}: 'workaround_steps' must be an array of strings.")

    if "known_issues" in data and not isinstance(data["known_issues"], str):
        errors.append(f"{filepath}: 'known_issues' must be a string.")

    if "last_tested_date" in data and not isinstance(data["last_tested_date"], str):
        errors.append(f"{filepath}: 'last_tested_date' must be a string.")

    if "tested_channel" in data:
        channel = data["tested_channel"]
        if channel not in ALLOWED_CHANNELS:
            errors.append(f"{filepath}: 'tested_channel' ('{channel}') is invalid. Allowed: {sorted(list(ALLOWED_CHANNELS))}")

    return errors


def validate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        return [f"{filepath}: Invalid JSON syntax: {err}"]
    except Exception as ex:
        return [f"{filepath}: Failed to read file: {ex}"]

    return validate_record_data(data, str(filepath))


def main():
    root_dir = Path(__file__).resolve().parent.parent
    targets = []

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            targets.append(Path(arg))
    else:
        compat_dir = root_dir / 'compatibility'
        for sub in ['data', 'templates', 'submissions']:
            sub_dir = compat_dir / sub
            if sub_dir.exists():
                for p in sub_dir.glob('*.json'):
                    targets.append(p)

    if not targets:
        print("[*] No compatibility JSON records found to validate.")
        return 0

    print(f"[*] Validating {len(targets)} compatibility record(s)...")
    total_errors = []

    for t in sorted(targets):
        file_errors = validate_file(t)
        if file_errors:
            total_errors.extend(file_errors)
            print(f"[-] FAILED: {t.name}")
            for err in file_errors:
                print(f"    - {err}")
        else:
            print(f"[+] VALID:  {t.name}")

    if total_errors:
        print(f"\n[-] Validation failed with {len(total_errors)} error(s).")
        return 1

    print(f"\n[+] All {len(targets)} compatibility record(s) passed validation successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
