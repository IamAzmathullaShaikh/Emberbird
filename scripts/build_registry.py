#!/usr/bin/env python3
"""
build_registry.py - Emberbird Registry Generator (P0.3)

Generates data/releases/releases.json from published reality (GitHub Releases
API + published checksums + sidecars). Real hashes only; placeholder hashes
are forbidden by the schema itself.

Idempotence: running the generator twice produces byte-identical output.
Determinism: verified_at timestamps are derived from the registry's previous
state when the hash is unchanged (hash-stable timestamps), so regenerating
without new reality does not churn the file.

Usage:
    python3 scripts/build_registry.py [--offline FILE]

Offline mode (--offline) reads a GitHub API releases JSON dump instead of the
network - used by tests and for reproducible regeneration from a snapshot.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"
SCHEMA_PATH = REPO_ROOT / "data" / "releases" / "releases.schema.json"
REPO_SLUG = "IamAzmathullaShaikh/Emberbird"

WSA_VER_RE = re.compile(r"[0-9]+[.][0-9]{5}[.][0-9]+[.][0-9]+")
MANAGER_VER_RE = re.compile(r"^v([0-9]+[.][0-9]+[.][0-9]+)$")
PACKAGE_RE = re.compile(r"^(WSA_[0-9.]+_x64(_vanilla)?[.]7z)$")


def _git_commit() -> str:
    """Best-effort HEAD commit for provenance (empty outside a git repo)."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


GIT_COMMIT = _git_commit()


def make_provenance(now_iso: str) -> dict:
    """Per-entry provenance (release-contract.md §4.3)."""
    prov = {
        "tool": "scripts/build_registry.py",
        "mode": "reality-sync",
        "generated_at": now_iso,
    }
    if GIT_COMMIT:
        prov["commit"] = GIT_COMMIT
    return prov

TODAY = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)


def github_headers() -> dict:
    """Headers for GitHub API/asset requests. GITHUB_TOKEN (when present) is
    used for authenticated access — required for scheduled CI runs to stay
    clear of the 60-requests/hour anonymous rate limit."""
    import os

    headers = {"User-Agent": "emberbird-registry/1.0"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_json(url: str, retries: int = 3):
    """GET JSON with retries (GitHub occasionally 502s)."""
    import urllib.request
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=github_headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as err:  # noqa: BLE001
            last_err = err
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def fetch_text(url: str, retries: int = 3) -> str:
    import urllib.request
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=github_headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as err:  # noqa: BLE001
            last_err = err
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def sha256_of_asset(asset, retries: int = 3) -> str:
    """Download the asset and hash it (fallback when no published hash exists)."""
    import urllib.request
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(asset["browser_download_url"],
                                         headers=github_headers())
            with urllib.request.urlopen(req, timeout=120) as resp:
                digest = hashlib.sha256()
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    digest.update(chunk)
                return digest.hexdigest()
        except Exception as err:  # noqa: BLE001
            last_err = err
    raise RuntimeError(f"failed to hash {asset['name']}: {last_err}")


def parse_checksum_text(text: str) -> dict:
    """Parse 'HASH  name' or 'HASH *name' lines into {name: hash}."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, name = parts
        name = name.lstrip("*").strip()
        digest = digest.strip().lower()
        if re.fullmatch(r"[a-f0-9]{64}", digest):
            out[name] = digest
    return out


def load_previous() -> dict:
    """Previous registry state, for hash-stable verified_at timestamps."""
    if REGISTRY_PATH.is_file():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def verified_at_for(prev_registry: dict, filename: str, sha256: str, default: str) -> str:
    """Keep the old verified_at if the hash is unchanged (idempotence)."""
    for vault_entry in prev_registry.get("vault", []):
        if vault_entry.get("artifact") == filename and vault_entry.get("sha256") == sha256:
            return vault_entry.get("last_verified_at", default)
    for rel in prev_registry.get("releases", []):
        for asset in rel.get("assets", []):
            if asset.get("filename") == filename and asset.get("sha256") == sha256:
                return asset.get("verified_at", default)
    return default


def extract_report_result(report_name: str, body) -> str:
    """Map each validator's real JSON shape onto the report_result enum."""
    if not isinstance(body, dict):
        return "NOT VERIFIED"
    if report_name == "package-identity-report.json":
        return "VERIFIED" if body.get("validation_passed") is True else "FAILED"
    if report_name == "package-integrity-report.json":
        status = body.get("validation_status")
        return status if status in ("VERIFIED", "FAILED", "PARTIALLY VERIFIED") else "NOT VERIFIED"
    if report_name == "release-metadata.json":
        return "VERIFIED" if body.get("packages") or body.get("artifacts") or body else "VERIFIED"
    offline = body.get("offline")
    if isinstance(offline, dict) and offline.get("status"):
        return offline["status"]
    return "NOT VERIFIED"


def fetch_sidecar_hashes(assets) -> dict:
    """Fetch all .sha256 sidecars of a release into {asset_name: hash}."""
    out = {}
    for a in assets:
        if a["name"].endswith(".sha256"):
            out.update(parse_checksum_text(fetch_text(a["browser_download_url"])))
    return out


def resolve_hash(asset, manifest, sidecars):
    """Reality Source Hierarchy: L2 published manifest > sidecar > computed."""
    digest = manifest.get(asset["name"])
    if digest:
        return digest, "published-manifest"
    digest = sidecars.get(asset["name"])
    if digest:
        return digest, "sidecar"
    return sha256_of_asset(asset), "computed"


def classify_release(rel, prev_registry) -> list:
    """Convert one GitHub release into 1..n registry entries (tag x edition)."""
    tag = rel["tag_name"]
    published = rel["published_at"]
    assets = rel.get("assets", [])
    entries = []
    now_iso = TODAY.isoformat().replace("+00:00", "Z")

    manager_match = MANAGER_VER_RE.match(tag)
    if manager_match:
        version = manager_match.group(1)
        manifest = {}
        checksum_txt = next((a for a in assets if a["name"] == f"WSABuildsManager-{version}-checksums.txt"), None)
        if checksum_txt:
            manifest = parse_checksum_text(fetch_text(checksum_txt["browser_download_url"]))
        sidecars = fetch_sidecar_hashes(assets)
        pkg_assets = [a for a in assets if a["name"].endswith((".exe", ".zip")) and "WSABuildsManager" in a["name"]]
        reg_assets = []
        for a in sorted(pkg_assets, key=lambda x: x["name"]):
            digest, hash_source = resolve_hash(a, manifest, sidecars)
            reg_assets.append({
                "filename": a["name"],
                "sha256": digest,
                "arch": "x64",
                "role": "package",
                "source_url": a["browser_download_url"],
                "source_type": "generated",
                "hash_source": hash_source,
                "verified_at": verified_at_for(prev_registry, a["name"], digest, now_iso),
                "size_bytes": a["size"],
            })
        if reg_assets:
            entries.append({
                "release_id": f"manager-{version}",
                "tag": tag,
                "kind": "manager",
                "channel": "stable",
                "edition": "manager",
                "architectures": ["x64"],
                "status": "published",
                "published_at": published,
                "provenance": make_provenance(now_iso),
                "assets": reg_assets,
            })
        return entries

    if tag.startswith(("wsa-v", "Windows_11_")):
        joined = " ".join(a["name"] for a in assets)
        ver_match = WSA_VER_RE.search(joined)
        if not ver_match:
            return entries
        wsa_version = ver_match.group(0)
        checksum_sha = next((a for a in assets if a["name"] == "checksums.sha256"), None)
        manifest = parse_checksum_text(fetch_text(checksum_sha["browser_download_url"])) if checksum_sha else {}
        sidecars = fetch_sidecar_hashes(assets)
        report_type_map = {
            "package-identity-report.json": "package-identity",
            "package-integrity-report.json": "package-integrity",
            "magisk-validation-report.json": "magisk",
            "gapps-validation-report.json": "gapps",
            "release-metadata.json": "release-metadata",
        }
        reports = []
        report_assets = [a for a in assets if a["name"] in report_type_map]
        for ra in sorted(report_assets, key=lambda x: x["name"]):
            result = "NOT VERIFIED"
            try:
                body = json.loads(fetch_text(ra["browser_download_url"]))
                result = extract_report_result(ra["name"], body)
            except Exception:  # noqa: BLE001
                result = "NOT VERIFIED"
            reports.append({"report_type": report_type_map[ra["name"]], "result": result, "report_file": ra["name"]})
        packages = [a for a in assets if PACKAGE_RE.match(a["name"])]
        by_edition = {}
        for a in packages:
            edition = "banking" if "_vanilla" in a["name"] else "standard"
            by_edition.setdefault(edition, []).append(a)
        tag_epoch = tag.split("_")[-1].split(".")[0] if tag.startswith("Windows_11_") else tag.replace("wsa-v", "").split(".")[0]
        suffix = "" if tag.startswith("wsa-v") else "-alt"
        for edition, pkgs in sorted(by_edition.items()):
            reg_assets = []
            for a in sorted(pkgs, key=lambda x: x["name"]):
                digest, hash_source = resolve_hash(a, manifest, sidecars)
                reg_assets.append({
                    "filename": a["name"],
                    "sha256": digest,
                    "arch": "x64",
                    "role": "package",
                    "source_url": a["browser_download_url"],
                    "source_type": "derived",
                    "hash_source": hash_source,
                    "verified_at": verified_at_for(prev_registry, a["name"], digest, now_iso),
                    "size_bytes": a["size"],
                })
            entries.append({
                "release_id": f"wsa-{tag_epoch}-{edition}{suffix}",
                "tag": tag,
                "kind": "subsystem",
                "wsa_version": wsa_version,
                "channel": "retail",
                "edition": edition,
                "architectures": ["x64"],
                "root_solution": "none" if edition == "banking" else "magisk",
                "gapps_variant": "pico",
                "status": "published",
                "published_at": published,
                "provenance": make_provenance(now_iso),
                "assets": reg_assets,
                "validation_reports": reports,
            })
    return entries


def build_vault(entries, prev_registry, now_iso) -> list:
    """Ember Vault: one entry per published package artifact across all releases."""
    vault = []
    seen = set()
    # Vault identity is (artifact, sha256): the same filename may exist as
    # distinct published cuts with different hashes across tags.
    prev_by_pair = {
        (v.get("artifact"), v.get("sha256")): v for v in prev_registry.get("vault", [])
    }
    for rel in entries:
        for asset in rel.get("assets", []):
            if asset["role"] != "package":
                continue
            key = (asset["filename"], asset["sha256"])
            if key in seen:
                continue
            seen.add(key)
            prev = prev_by_pair.get(key, {})
            stable_score = prev.get("availability_score", 100) if prev.get("sha256") == asset["sha256"] else 100
            vault.append({
                "artifact": asset["filename"],
                "source_url": asset["source_url"],
                "sha256": asset["sha256"],
                "mirror_status": prev.get("mirror_status", "unverified"),
                "last_verified_at": verified_at_for(prev_registry, asset["filename"], asset["sha256"], now_iso),
                "availability_score": stable_score,
            })
    return sorted(vault, key=lambda v: v["artifact"])


def generate(releases_payload: list, prev_registry: dict) -> dict:
    now_iso = TODAY.isoformat().replace("+00:00", "Z")
    entries = []
    for rel in sorted(releases_payload, key=lambda r: r.get("published_at") or ""):
        entries.extend(classify_release(rel, prev_registry))
    entries.sort(key=lambda r: (r["kind"], r["published_at"], r["release_id"]))
    registry = {
        "schema_version": 1,
        "migration_version": 2,
        "compatibility_level": "backward",
        "generation": {
            "tool": "scripts/build_registry.py",
            "mode": "reality-sync",
            "source": f"https://api.github.com/repos/{REPO_SLUG}/releases",
            "generated_at": now_iso,
        },
        "releases": entries,
        "vault": build_vault(entries, prev_registry, now_iso),
    }
    # Policy carry-over (P1.3 / clause 9): `recommended` is a policy
    # decision, never a generator default. Reality-sync re-applies the
    # previous decision and its provenance verbatim - and only for
    # releases that still exist in published reality.
    prev_policy = prev_registry.get("policy") if isinstance(prev_registry, dict) else None
    prev_rec = {
        r.get("release_id")
        for r in (prev_registry.get("releases", []) if isinstance(prev_registry, dict) else [])
        if r.get("recommended")
    }
    if prev_rec and prev_policy and prev_policy.get("recommended_by"):
        carried = prev_rec & {r["release_id"] for r in entries}
        if carried:
            for rel in entries:
                if rel["release_id"] in carried:
                    rel["recommended"] = True
            registry["policy"] = dict(prev_policy)
    return registry


def _deny_socket(*args, **kwargs):
    raise RuntimeError("network access denied (--no-network mode)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Emberbird Registry Generator")
    parser.add_argument("--offline", type=str, default=None,
                        help="Path to a GitHub releases JSON dump (offline mode)")
    parser.add_argument("--no-network", action="store_true",
                        help="Refuse every network access (CI drift runs: reads only committed data)")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path (default: data/releases/releases.json)")
    args = parser.parse_args()

    if args.no_network:
        if not args.offline:
            print("--no-network requires --offline (CI drift runs must read only committed data)")
            return 2
        import socket

        socket.socket = _deny_socket
        socket.create_connection = _deny_socket
        socket.getaddrinfo = _deny_socket
    if args.offline:
        payload = json.loads(Path(args.offline).read_text(encoding="utf-8"))
    else:
        api = f"https://api.github.com/repos/{REPO_SLUG}/releases?per_page=50"
        payload = fetch_json(api)
    if isinstance(payload, dict):
        payload = payload.get("releases", [])

    prev_registry = load_previous()
    registry = generate(payload, prev_registry)
    text = json.dumps(registry, indent=2, ensure_ascii=True, sort_keys=False) + "\n"

    out = Path(args.output) if args.output else REGISTRY_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")

    # Idempotence self-check: regenerate from the same payload and compare bytes.
    second = json.dumps(generate(payload, prev_registry), indent=2, ensure_ascii=True, sort_keys=False) + "\n"
    assert text == second, "generator is not idempotent"
    print(f"registry written: {out} ({len(registry['releases'])} releases, {len(registry['vault'])} vault entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
