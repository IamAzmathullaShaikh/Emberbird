#!/usr/bin/env python3
"""PH-24 — Generate the SPDX 2.3 SBOM for an Emberbird release.

Sources of truth (no invented packages):

- ``apps/manager/src-tauri/Cargo.lock`` — every resolved Rust crate (the lock
  file is the pinned resolution, so this is complete, not "direct-only").
- ``apps/manager/package.json`` + ``website/package.json`` — *declared direct*
  npm dependencies. No committed lockfile exists for these, so transitive npm
  resolution is deliberately NOT invented here; the document comment states it.
- The running Python environment (``importlib.metadata``) — the toolchain the
  pipeline itself executes with, labeled as such.

Honesty rules mirror the zero-mock law: licenses are ``NOASSERTION`` (we do
not scrape LICENSE files here), packages without a registry source (the
workspace crate) get ``NOASSERTION`` download locations, and the document is
byte-deterministic when ``SOURCE_DATE_EPOCH`` is set (reproducible-build
convention, PH-24's next item).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CARGO_LOCK = REPO / "apps" / "manager" / "src-tauri" / "Cargo.lock"
MANAGER_PKG = REPO / "apps" / "manager" / "package.json"
WEBSITE_PKG = REPO / "website" / "package.json"

SPDX_VERSION = "SPDX-2.3"
DATA_LICENSE = "CC0-1.0"
TOOL_ID = "emberbird-sbom-generator-0.1.0"
DOC_SPDX_ID = "SPDXRef-DOCUMENT"


def _person_or_org(name: str) -> str:
    return f"Organization: {name}"


def parse_cargo_lock(path: Path) -> list[dict]:
    """Extract (name, version, source) for every [[package]] in a lock file."""
    if not path.is_file():
        raise FileNotFoundError(f"missing manifest: {path}")
    text = path.read_text(encoding="utf-8")
    packages: list[dict] = []
    for block in text.split("[[package]]")[1:]:
        name_m = re.search(r'^name = "(.+?)"', block, re.M)
        ver_m = re.search(r'^version = "(.+?)"', block, re.M)
        src_m = re.search(r'^source = "(.+?)"', block, re.M)
        if not (name_m and ver_m):
            continue
        source = src_m.group(1) if src_m else None
        packages.append({"name": name_m.group(1), "version": ver_m.group(1), "source": source})
    if not packages:
        raise ValueError(f"parsed zero packages from {path} — format drift?")
    return packages


def _purl_for_crate(pkg: dict) -> str | None:
    """crates.io source registry → purl; workspace member → None.

    The index name lives in the URL path (``.../crates.io-index``) for git
    registries or the host (``index.crates.io``) for sparse — check the whole
    registry URL, not just the host.
    """
    source = pkg.get("source") or ""
    m = re.match(r"(?:registry|sparse)\+(https://.+)", source)
    if m and "crates.io" in m.group(1):
        return f"pkg:cargo/{pkg['name']}@{pkg['version']}"
    return None


def parse_npm_manifests() -> list[dict]:
    """Declared direct dependencies from the two committed package.json files."""
    out: list[dict] = []
    for label, path in (("manager", MANAGER_PKG), ("website", WEBSITE_PKG)):
        if not path.is_file():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        deps = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
        for name, version in sorted(deps.items()):
            out.append({"name": name, "version": version, "surface": label})
    return out


def collect_python_env() -> list[dict]:
    """The executing interpreter's environment (the pipeline toolchain)."""
    out: list[dict] = []
    for dist in distributions():
        name = dist.metadata.get("Name")
        version = dist.metadata.get("Version")
        if not (name and version):
            continue
        out.append({"name": name, "version": version})
    return sorted(out, key=lambda p: (p["name"].lower(), p["version"]))


def _pypi_purl(name: str, version: str) -> str:
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    return f"pkg:pypi/{normalized}@{version}"


def build_sbom(tag: str, manager_version: str, wsa_version: str) -> dict:
    crates = parse_cargo_lock(CARGO_LOCK)
    npm = parse_npm_manifests()
    pyenv = collect_python_env()

    def content_id() -> str:
        h = hashlib.sha256()
        for p in sorted(crates, key=lambda c: (c["name"], c["version"])):
            h.update(f"cargo:{p['name']}@{p['version']}\n".encode())
        for p in npm:
            h.update(f"npm:{p['surface']}:{p['name']}@{p['version']}\n".encode())
        for p in pyenv:
            h.update(f"pypi:{_pypi_purl(p['name'], p['version'])}\n".encode())
        h.update(f"tag:{tag};manager:{manager_version};wsa:{wsa_version}\n".encode())
        return h.hexdigest()

    namespace = f"https://emberbird.dev/spdx/{tag}/{uuid.uuid5(uuid.NAMESPACE_URL, content_id())}"

    # Reproducible-build convention: SOURCE_DATE_EPOCH pins the timestamp.
    epoch = None
    if epoch_raw := __import__("os").environ.get("SOURCE_DATE_EPOCH"):
        epoch = int(epoch_raw)
    created = (
        datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if epoch is not None
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    packages: list[dict] = []
    root_id = "SPDXRef-Package-EMBERBIRD-RELEASE"
    packages.append({
        "name": f"Emberbird Release {tag}",
        "SPDXID": root_id,
        "versionInfo": manager_version,
        "downloadLocation": "https://github.com/Emberbird-WSA/Emberbird",
        "filesAnalyzed": False,
        "licenseConcluded": "AGPL-3.0-only",
        "licenseDeclared": "AGPL-3.0-only",
        "copyrightText": "NOASSERTION",
        "supplier": _person_or_org("Emberbird"),
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:generic/emberbird@{manager_version}",
            }
        ],
    })

    for pkg in crates:
        purl = _purl_for_crate(pkg)
        packages.append({
            "name": pkg["name"],
            "SPDXID": f"SPDXRef-Package-cargo-{pkg['name']}-{pkg['version']}",
            "versionInfo": pkg["version"],
            "downloadLocation": "NOASSERTION" if purl is None else "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            **({"externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": purl,
            }]} if purl else {"comment": "workspace member — built from this repository"}),
        })

    for pkg in npm:
        escaped = re.sub(r"[^A-Za-z0-9._-]", "-", pkg["name"])
        packages.append({
            "name": pkg["name"],
            "SPDXID": f"SPDXRef-Package-npm-{pkg['surface']}-{escaped}-{pkg['version']}",
            "versionInfo": pkg["version"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "comment": f"declared direct dependency of the {pkg['surface']} surface (no committed npm lockfile; transitive resolution not represented)",
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:npm/{pkg['name']}@{pkg['version']}",
            }],
        })

    for pkg in pyenv:
        escaped = re.sub(r"[^A-Za-z0-9._-]", "-", pkg["name"])
        packages.append({
            "name": pkg["name"],
            "SPDXID": f"SPDXRef-Package-pypi-{escaped}-{pkg['version']}",
            "versionInfo": pkg["version"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "comment": "toolchain environment of the release pipeline (importlib.metadata of the executing interpreter)",
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": _pypi_purl(pkg["name"], pkg["version"]),
            }],
        })

    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": DATA_LICENSE,
        "SPDXID": DOC_SPDX_ID,
        "name": f"Emberbird-{tag}-SBOM",
        "documentNamespace": namespace,
        "creationInfo": {
            "created": created,
            "creators": [_person_or_org("Emberbird"), f"Tool: {TOOL_ID}"],
            "licenseListVersion": "3.25",
            "comment": (
                "Rust crates derive from the committed Cargo.lock (complete pinned "
                "resolution). npm entries are declared direct dependencies only. "
                "Python entries describe the pipeline toolchain environment. "
                "Licenses are NOASSERTION pending per-package license review."
            ),
        },
        "documentDescribes": [root_id],
        "packages": packages,
    }


def validate_sbom(doc: dict) -> list[str]:
    """Minimal structural self-check of the SPDX 2.3 required fields."""
    errors: list[str] = []
    for field in ("spdxVersion", "dataLicense", "SPDXID", "name", "documentNamespace", "creationInfo", "documentDescribes"):
        if field not in doc:
            errors.append(f"missing document field: {field}")
    if doc.get("spdxVersion") != SPDX_VERSION:
        errors.append(f"bad spdxVersion: {doc.get('spdxVersion')}")
    if doc.get("dataLicense") != DATA_LICENSE:
        errors.append(f"bad dataLicense: {doc.get('dataLicense')}")
    seen_ids: set[str] = set()
    required_pkg = {"name", "SPDXID", "downloadLocation", "filesAnalyzed", "licenseConcluded", "licenseDeclared", "copyrightText"}
    for pkg in doc.get("packages", []):
        missing = required_pkg - set(pkg)
        if missing:
            errors.append(f"package {pkg.get('SPDXID', '?')} missing: {sorted(missing)}")
        spdx_id = pkg.get("SPDXID")
        if spdx_id in seen_ids:
            errors.append(f"duplicate SPDXID: {spdx_id}")
        seen_ids.add(spdx_id or "")
    if len(doc.get("packages", [])) < 2:
        errors.append("SBOM must contain the root package plus at least one component")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="Windows_11_2407.40000.4.0_v4")
    parser.add_argument("--manager-version", default=None)
    parser.add_argument("--wsa-version", default="2407.40000.4.0")
    parser.add_argument("--out", type=Path, default=None, help="output path (default: dist/<tag>/sbom.spdx.json)")
    args = parser.parse_args(argv)

    if args.manager_version is None:
        version_json = REPO / "deployment" / "version.json"
        args.manager_version = json.loads(version_json.read_text(encoding="utf-8"))["manager"]["version"]

    doc = build_sbom(args.tag, args.manager_version, args.wsa_version)
    errors = validate_sbom(doc)
    if errors:
        for err in errors:
            print(f"SBOM INVALID: {err}", file=sys.stderr)
        return 2

    out = args.out or (REPO / "dist" / args.tag / "sbom.spdx.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    by_origin = {"cargo": 0, "npm": 0, "pypi": 0, "root": 0}
    for pkg in doc["packages"]:
        if pkg["SPDXID"] == "SPDXRef-Package-EMBERBIRD-RELEASE":
            by_origin["root"] += 1
        elif pkg["SPDXID"].startswith("SPDXRef-Package-cargo-"):
            by_origin["cargo"] += 1
        elif pkg["SPDXID"].startswith("SPDXRef-Package-npm-"):
            by_origin["npm"] += 1
        else:
            by_origin["pypi"] += 1
    print(f"SBOM written: {out}")
    print(f"  packages: {len(doc['packages'])} (root {by_origin['root']}, cargo {by_origin['cargo']}, npm {by_origin['npm']}, pypi {by_origin['pypi']})")
    print(f"  namespace: {doc['documentNamespace']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
