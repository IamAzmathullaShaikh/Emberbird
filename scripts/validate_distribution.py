#!/usr/bin/env python3
"""
Emberbird Distribution and Winget Manifest Validator
Validates version consistency, packaging specifications, and Winget manifest structure.

Identity (E5.3): the active package identity derives from deployment/version.json
(single source of truth). Historical packages under manifests/w/WSABuilds/ are
frozen published history (M4) and are never mutated — only sanity-checked.
"""

import json
import re
import sys
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

INSTALLER_NAME_PATTERN = re.compile(
    r"^(?P<prefix>[A-Za-z0-9]+)-Setup-(?P<version>[0-9]+\.[0-9]+\.[0-9]+)-(?P<arch>x64|arm64)\.exe$"
)
PORTABLE_NAME_PATTERN = re.compile(
    r"^(?P<prefix>[A-Za-z0-9]+)-Portable-(?P<version>[0-9]+\.[0-9]+\.[0-9]+)-(?P<arch>x64|arm64)\.zip$"
)
CHECKSUM_NAME_PATTERN = re.compile(
    r"^(?P<prefix>[A-Za-z0-9]+)-(?P<version>[0-9]+\.[0-9]+\.[0-9]+)-checksums\.txt$"
)
SHA256_HEX_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def validate_version_json(version_file: Path) -> dict:
    if not version_file.exists():
        raise FileNotFoundError(f"Missing version file: {version_file}")

    with open(version_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "manager" not in data:
        raise ValueError("Missing 'manager' object in version metadata")

    mgr = data["manager"]
    required_keys = [
        "version",
        "channel",
        "release_date",
        "winget_package_id",
        "min_windows_build",
        "target_architectures",
        "publisher",
        "license",
    ]
    for k in required_keys:
        if k not in mgr:
            raise ValueError(f"Missing required key '{k}' in manager version metadata")

    return data


def validate_version_consistency(repo_root: Path, target_version: str) -> list:
    errors = []

    # 1. apps/manager/package.json
    pkg_json_path = repo_root / "apps" / "manager" / "package.json"
    if pkg_json_path.exists():
        with open(pkg_json_path, "r", encoding="utf-8") as f:
            pkg_data = json.load(f)
            if pkg_data.get("version") != target_version:
                errors.append(
                    f"apps/manager/package.json version ({pkg_data.get('version')}) does not match {target_version}"
                )
    else:
        errors.append(f"Missing file: {pkg_json_path}")

    # 2. apps/manager/src-tauri/Cargo.toml
    cargo_path = repo_root / "apps" / "manager" / "src-tauri" / "Cargo.toml"
    if cargo_path.exists():
        content = cargo_path.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            if match.group(1) != target_version:
                errors.append(
                    f"Cargo.toml package version ({match.group(1)}) does not match {target_version}"
                )
        else:
            errors.append("Could not find package version in Cargo.toml")
    else:
        errors.append(f"Missing file: {cargo_path}")

    # 3. apps/manager/src-tauri/tauri.conf.json
    tauri_conf_path = (
        repo_root / "apps" / "manager" / "src-tauri" / "tauri.conf.json"
    )
    if tauri_conf_path.exists():
        with open(tauri_conf_path, "r", encoding="utf-8") as f:
            tauri_data = json.load(f)
            if tauri_data.get("version") != target_version:
                errors.append(
                    f"tauri.conf.json version ({tauri_data.get('version')}) does not match {target_version}"
                )
    else:
        errors.append(f"Missing file: {tauri_conf_path}")

    return errors


def validate_winget_manifests(
    repo_root: Path, package_id: str, version: str
) -> list:
    errors = []
    first_char = package_id.split(".")[0][0].lower()
    publisher = package_id.split(".")[0]
    package_name = package_id.split(".")[1]

    manifest_dir = (
        repo_root
        / "manifests"
        / first_char
        / publisher
        / package_name
        / version
    )
    if not manifest_dir.exists():
        return [f"Winget manifest directory does not exist: {manifest_dir}"]

    version_yaml = manifest_dir / f"{package_id}.yaml"
    installer_yaml = manifest_dir / f"{package_id}.installer.yaml"
    locale_yaml = manifest_dir / f"{package_id}.locale.en-US.yaml"

    for path, expected_type in [
        (version_yaml, "version"),
        (installer_yaml, "installer"),
        (locale_yaml, "defaultLocale"),
    ]:
        if not path.exists():
            errors.append(f"Missing Winget manifest file: {path.name}")
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"YAML parse error in {path.name}: {e}")
            continue

        if data.get("PackageIdentifier") != package_id:
            errors.append(
                f"{path.name}: PackageIdentifier '{data.get('PackageIdentifier')}' does not match expected '{package_id}'"
            )

        if data.get("PackageVersion") != version:
            errors.append(
                f"{path.name}: PackageVersion '{data.get('PackageVersion')}' does not match expected '{version}'"
            )

        if data.get("ManifestType") != expected_type:
            errors.append(
                f"{path.name}: ManifestType '{data.get('ManifestType')}' does not match expected '{expected_type}'"
            )

        if expected_type == "installer":
            installers = data.get("Installers", [])
            if not installers:
                errors.append(f"{path.name}: No installer entries defined")
            for inst in installers:
                arch = inst.get("Architecture")
                if arch not in ["x64", "arm64", "x86"]:
                    errors.append(
                        f"{path.name}: Invalid installer architecture '{arch}'"
                    )
                sha = str(inst.get("InstallerSha256", ""))
                if not SHA256_HEX_PATTERN.match(sha):
                    errors.append(
                        f"{path.name}: Invalid SHA-256 format for arch '{arch}'"
                    )

    return errors


def _artifact_prefix(product_name: str) -> str:
    """Emberbird Manager -> EmberbirdManager (published-artifact naming rule)."""
    return "".join(part for part in product_name.split() if part)


def _validate_historic_manifests(repo_root: Path) -> list:
    """Frozen-history sanity (M4): every historic package keeps its three
    manifests with a real-format hash. Historic manifests are never mutated."""
    errors = []
    base = repo_root / "manifests"
    # Layout: manifests/<first-char>/<Publisher>/<Package>/<version>/ (winget convention).
    for bucket in sorted(p for p in base.iterdir() if p.is_dir()):
        for publisher_dir in sorted(p for p in bucket.iterdir() if p.is_dir()):
            for pkg_dir in sorted(p for p in publisher_dir.iterdir() if p.is_dir()):
                for ver_dir in sorted(p for p in pkg_dir.iterdir() if p.is_dir()):
                    pkg_id = f"{publisher_dir.name}.{pkg_dir.name}"
                    for suffix in (".yaml", ".installer.yaml", ".locale.en-US.yaml"):
                        if not (ver_dir / f"{pkg_id}{suffix}").exists():
                            errors.append(f"historic manifest missing: {pkg_id}{suffix} under {ver_dir.name}")
                    inst = ver_dir / f"{pkg_id}.installer.yaml"
                    if inst.exists():
                        try:
                            data = yaml.safe_load(inst.read_text(encoding="utf-8"))
                            for entry in data.get("Installers", []):
                                if not SHA256_HEX_PATTERN.match(str(entry.get("InstallerSha256", ""))):
                                    errors.append(f"historic hash format invalid: {inst}")
                        except Exception as e:
                            errors.append(f"historic manifest parse error: {inst}: {e}")
    return errors


def is_valid_installer_name(
    filename: str, expected_version: str = None, expected_arch: str = None
) -> bool:
    match = INSTALLER_NAME_PATTERN.match(filename)
    if not match:
        return False
    if expected_version and match.group("version") != expected_version:
        return False
    if expected_arch and match.group("arch") != expected_arch:
        return False
    return True


def is_valid_portable_name(
    filename: str, expected_version: str = None, expected_arch: str = None
) -> bool:
    match = PORTABLE_NAME_PATTERN.match(filename)
    if not match:
        return False
    if expected_version and match.group("version") != expected_version:
        return False
    if expected_arch and match.group("arch") != expected_arch:
        return False
    return True


def is_valid_checksum_name(
    filename: str, expected_version: str = None
) -> bool:
    match = CHECKSUM_NAME_PATTERN.match(filename)
    if not match:
        return False
    if expected_version and match.group("version") != expected_version:
        return False
    return True


def main():
    print("[*] Emberbird Distribution & Winget Manifest Validator")
    version_file = REPO_ROOT / "deployment" / "version.json"

    try:
        data = validate_version_json(version_file)
    except Exception as e:
        print(f"[-] ERROR: Failed to parse {version_file}: {e}")
        sys.exit(1)

    target_version = data["manager"]["version"]
    package_id = data["manager"]["winget_package_id"]
    print(
        f"[+] Validated version.json: Package={package_id}, Version={target_version}"
    )

    # Validate version consistency across codebase
    consistency_errors = validate_version_consistency(
        REPO_ROOT, target_version
    )
    if consistency_errors:
        print("[-] Version consistency check failed:")
        for err in consistency_errors:
            print(f"    - {err}")
        sys.exit(1)
    print("[+] All project manifest versions are synchronized.")

    # Validate Winget manifests
    manifest_errors = validate_winget_manifests(
        REPO_ROOT, package_id, target_version
    )
    if manifest_errors:
        print("[-] Winget manifest check failed:")
        for err in manifest_errors:
            print(f"    - {err}")
        sys.exit(1)
    print("[+] All Winget manifest YAML files validated successfully.")

    # Validate sample artifact names (prefix derives from the active identity)
    artifact_prefix = _artifact_prefix(data["manager"]["product_name"])
    sample_installer = f"{artifact_prefix}-Setup-{target_version}-x64.exe"
    sample_portable = f"{artifact_prefix}-Portable-{target_version}-x64.zip"
    sample_checksums = f"{artifact_prefix}-{target_version}-checksums.txt"

    assert is_valid_installer_name(sample_installer, target_version, "x64")
    assert is_valid_portable_name(sample_portable, target_version, "x64")
    assert is_valid_checksum_name(sample_checksums, target_version)
    print("[+] Release packaging naming conventions verified.")

    # Frozen-history sanity: never mutated, only checked (M4)
    historic_errors = _validate_historic_manifests(REPO_ROOT)
    if historic_errors:
        print("[-] Historic manifest sanity check failed:")
        for err in historic_errors:
            print(f"    - {err}")
        sys.exit(1)
    print("[+] Historic winget manifests intact (frozen history, M4).")

    print(
        "[+] SUCCESS: Distribution metadata and Winget manifests are fully valid."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
