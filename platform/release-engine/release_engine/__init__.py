"""Emberbird Release Engine - registry-backed metadata service (P0.4).

Reads data/releases/releases.json from disk ONLY (Registry Independence).
Zero network access. Pure stdlib.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"
SCHEMA_PATH = REPO_ROOT / "data" / "releases" / "releases.schema.json"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class RegistryError(RuntimeError):
    """Registry integrity violation."""


class Release:
    """Read-only view over one registry release entry."""

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        self._data = data

    @property
    def release_id(self) -> str:
        return self._data["release_id"]

    @property
    def tag(self) -> str:
        return self._data["tag"]

    @property
    def kind(self) -> str:
        return self._data["kind"]

    @property
    def edition(self) -> str:
        return self._data["edition"]

    @property
    def channel(self) -> str:
        return self._data["channel"]

    @property
    def status(self) -> str:
        return self._data["status"]

    @property
    def wsa_version(self) -> Optional[str]:
        return self._data.get("wsa_version")

    @property
    def recommended(self) -> bool:
        return bool(self._data.get("recommended", False))

    @property
    def published_at(self) -> str:
        return self._data["published_at"]

    @property
    def raw(self) -> dict:
        return dict(self._data)

    @property
    def package_assets(self) -> list:
        return [a for a in self._data.get("assets", []) if a.get("role") == "package"]

    def report_result(self, report_type: str) -> Optional[str]:
        for r in self._data.get("validation_reports", []):
            if r["report_type"] == report_type:
                return r["result"]
        return None

    def __repr__(self) -> str:
        return f"<Release {self.release_id} [{self.status}]>"


class Registry:
    """Loaded registry with integrity checks and lookup helpers."""

    def __init__(self, data: dict, path: Optional[Path] = None):
        self._data = data
        self.path = path
        self._releases = [Release(r) for r in data.get("releases", [])]

    # -- metadata ----------------------------------------------------------
    @property
    def schema_version(self) -> int:
        return self._data["schema_version"]

    @property
    def migration_version(self) -> int:
        return self._data["migration_version"]

    @property
    def compatibility_level(self) -> str:
        return self._data["compatibility_level"]

    @property
    def releases(self) -> list:
        return list(self._releases)

    @property
    def vault(self) -> list:
        return list(self._data.get("vault", []))

    @property
    def raw(self) -> dict:
        return self._data

    # -- lookups (P0.4 capability list) ------------------------------------
    def all(self) -> list:
        return self.releases

    def published(self) -> list:
        return [r for r in self._releases if r.status == "published"]

    def latest_wsa(self) -> Optional[Release]:
        """Newest published subsystem release by published_at."""
        pool = [r for r in self.published() if r.kind == "subsystem"]
        return max(pool, key=lambda r: (r.published_at, r.release_id), default=None)

    def latest_manager(self) -> Optional[Release]:
        pool = [r for r in self.published() if r.kind == "manager"]
        return max(pool, key=lambda r: (r.published_at, r.release_id), default=None)

    def recommended_wsa(self, edition: Optional[str] = None) -> Optional[Release]:
        pool = [r for r in self.published() if r.kind == "subsystem" and r.recommended]
        if edition:
            pool = [r for r in pool if r.edition == edition]
        return pool[0] if pool else None

    def by_channel(self, channel: str) -> list:
        return [r for r in self._releases if r.channel == channel]

    def by_edition(self, edition: str) -> list:
        return [r for r in self._releases if r.edition == edition]

    def by_kind(self, kind: str) -> list:
        return [r for r in self._releases if r.kind == kind]

    def by_tag(self, tag: str) -> list:
        return [r for r in self._releases if r.tag == tag]

    def by_id(self, release_id: str) -> Optional[Release]:
        for r in self._releases:
            if r.release_id == release_id:
                return r
        return None

    def hash_for(self, filename: str, cut_sha256: Optional[str] = None) -> Optional[str]:
        """Asset hash by filename; pass cut_sha256 when the same filename
        exists as multiple published cuts."""
        matches = []
        for rel in self._releases:
            for a in rel._data.get("assets", []):
                if a.get("filename") == filename:
                    matches.append(a["sha256"])
        if not matches:
            return None
        if cut_sha256 and cut_sha256 in matches:
            return cut_sha256
        unique = sorted(set(matches))
        if len(unique) == 1:
            return unique[0]
        raise RegistryError(
            f"ambiguous asset {filename}: {len(unique)} distinct published cuts; "
            "pass cut_sha256 to disambiguate"
        )

    def vault_entry(self, artifact: str, sha256: Optional[str] = None) -> Optional[dict]:
        for v in self._data.get("vault", []):
            if v["artifact"] == artifact and (sha256 is None or v["sha256"] == sha256):
                return v
        return None


# ---------------------------------------------------------------------------
# Integrity checks (P0.4.1 validate)
# ---------------------------------------------------------------------------

def check_integrity(data: dict) -> list:
    """Return a list of integrity problems ([] means healthy)."""
    problems = []
    known_ids = {r.get("release_id") for r in data.get("releases", [])}

    if data.get("schema_version") != 1:
        problems.append(f"unsupported schema_version: {data.get('schema_version')}")
    if not isinstance(data.get("migration_version"), int) or data["migration_version"] < 1:
        problems.append("migration_version must be a positive integer")
    if data.get("compatibility_level") not in ("backward", "forward", "breaking"):
        problems.append(f"bad compatibility_level: {data.get('compatibility_level')}")

    seen_ids = set()
    recommended_counter = {}
    for rel in data.get("releases", []):
        rid = rel.get("release_id", "<missing>")
        if rid in seen_ids:
            problems.append(f"duplicate release_id: {rid}")
        seen_ids.add(rid)

        if rel.get("status") == "superseded":
            target = rel.get("superseded_by")
            if not target:
                problems.append(f"{rid}: superseded without superseded_by")
            elif target not in known_ids:
                problems.append(f"{rid}: superseded_by points to unknown release {target}")

        if rel.get("recommended"):
            if rel.get("status") in ("superseded", "yanked"):
                problems.append(f"{rid}: a superseded/yanked release cannot be recommended")
            key = (rel.get("channel"), rel.get("edition"))
            recommended_counter[key] = recommended_counter.get(key, 0) + 1

        if rel.get("kind") == "subsystem":
            if rel.get("edition") == "standard" and rel.get("root_solution") != "magisk":
                problems.append(f"{rid}: standard release must be magisk-rooted")
            if rel.get("edition") == "banking" and rel.get("root_solution") != "none":
                problems.append(f"{rid}: banking release must be vanilla")
            files = {a.get("filename") for a in rel.get("assets", [])}
            if rel.get("edition") == "standard" and not any(f and f.endswith("_x64.7z") for f in files):
                problems.append(f"{rid}: standard release lacks WSA_*_x64.7z package asset")
            if rel.get("edition") == "banking" and not any(f and f.endswith("_x64_vanilla.7z") for f in files):
                problems.append(f"{rid}: banking release lacks WSA_*_x64_vanilla.7z package asset")

        for asset in rel.get("assets", []):
            digest = asset.get("sha256", "")
            if not SHA256_RE.match(digest):
                problems.append(f"{rid}/{asset.get('filename')}: malformed sha256")
            elif set(digest) == {"0"}:
                problems.append(f"{rid}/{asset.get('filename')}: placeholder (all-zero) hash")
            if asset.get("arch", "x64") not in rel.get("architectures", []) and asset.get("arch") != "universal":
                problems.append(f"{rid}/{asset.get('filename')}: asset arch not in release architectures")

    for (channel, edition), count in recommended_counter.items():
        if count > 1:
            problems.append(f"channel={channel} edition={edition}: {count} recommended releases (max 1)")

    # Policy guard: `recommended` is a POLICY decision, never a chronological
    # or generator default. Any recommendation must be backed by an explicit
    # policy provenance record (who decided it and when).
    if recommended_counter:
        policy = data.get("policy") or {}
        if not policy.get("recommended_by"):
            problems.append(
                "recommended release(s) present but policy.recommended_by is "
                "missing - recommendations require policy provenance"
            )
        elif not policy.get("decided_at"):
            problems.append("policy.recommended_by present but policy.decided_at is missing")

    # Artifact identity guard: identity is (package_name + sha256), never
    # filename alone. Exact (filename, sha256) duplicates are redundant;
    # distinct cuts sharing a filename are expected and must stay distinct.
    seen_assets = set()
    for rel in data.get("releases", []):
        for a in rel.get("assets", []):
            key = (a.get("filename"), a.get("sha256"))
            if key in seen_assets:
                problems.append(
                    f"duplicate artifact identity {key[0]} sha256:{key[1][:12]}... "
                    "- (filename, sha256) pairs must be unique"
                )
            seen_assets.add(key)

    seen_vault = set()
    for v in data.get("vault", []):
        key = (v.get("artifact"), v.get("sha256"))
        if key in seen_vault:
            problems.append(f"duplicate vault identity {key[0]} sha256:{key[1][:12]}...")
        seen_vault.add(key)

    # vault agreement: every vault hash must exist on some asset with same name
    asset_hashes = {}
    for rel in data.get("releases", []):
        for a in rel.get("assets", []):
            asset_hashes.setdefault((a.get("filename"), a.get("sha256")), True)
    for v in data.get("vault", []):
        if (v.get("artifact"), v.get("sha256")) not in asset_hashes:
            problems.append(f"vault entry {v.get('artifact')} hash does not match any release asset")

    return problems


def load(path: Optional[Path] = None) -> Registry:
    """Load the registry from disk (no network) with integrity checks."""
    p = path or REGISTRY_PATH
    if not p.is_file():
        raise RegistryError(f"registry not found: {p} - run scripts/build_registry.py")
    data = json.loads(p.read_text(encoding="utf-8"))
    problems = check_integrity(data)
    if problems:
        raise RegistryError("registry integrity check failed:\n  - " + "\n  - ".join(problems))
    return Registry(data, path=p)


def validate_file(path: Optional[Path] = None) -> int:
    """P0.4.1 CLI entry: 0 = healthy, 1 = problems found."""
    p = path or REGISTRY_PATH
    try:
        registry = load(p)
    except RegistryError as err:
        print(f"REGISTRY INVALID: {err}")
        return 1
    print(
        f"REGISTRY OK: {len(registry.releases)} releases, {len(registry.vault)} vault entries "
        f"(schema_version={registry.schema_version}, migration={registry.migration_version}, "
        f"compatibility={registry.compatibility_level})"
    )
    return 0
