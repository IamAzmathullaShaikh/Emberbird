"""Emberbird Release Engine - registry-backed metadata service (P0.4).

Reads data/releases/releases.json from disk ONLY (Registry Independence).
Zero network access. Pure stdlib.
"""
from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "data" / "releases" / "releases.json"
SCHEMA_PATH = REPO_ROOT / "data" / "releases" / "releases.schema.json"

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class RegistryError(RuntimeError):
    """Registry integrity violation."""


class PolicyError(RuntimeError):
    """Policy decision refused (Execution Contract clause 9)."""


def utc_now_iso() -> str:
    """UTC timestamp in the registry's RFC3339 'Z' format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    if not isinstance(data.get("migration_version"), int) or data["migration_version"] < 2:
        problems.append("migration_version must be >= 2 (S2: provenance contract applied)")
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

        # Provenance contract (release-contract.md §4.3): every entry must
        # record how it entered the registry.
        prov = rel.get("provenance")
        if not isinstance(prov, dict):
            problems.append(f"{rid}: missing provenance record (contract-mandated)")
        else:
            if not str(prov.get("tool", "")).strip():
                problems.append(f"{rid}: provenance.tool missing/empty")
            if not str(prov.get("mode", "")).strip():
                problems.append(f"{rid}: provenance.mode missing/empty")
            if not str(prov.get("generated_at", "")).strip():
                problems.append(f"{rid}: provenance.generated_at missing/empty")

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


# ---------------------------------------------------------------------------
# Draft-07 subset schema validator (CI Truth Gate; stdlib-only so CI can
# enforce the schema contract without a jsonschema install)
# ---------------------------------------------------------------------------

class SchemaError(RegistryError):
    """Schema-contract violation (validation, not integrity)."""


def validate_against_schema(data, schema: dict, path: str = "$") -> list:
    """Validate `data` against the registry's Draft-07 schema using a
    stdlib-only subset validator. Returns a list of violations ([] = valid).

    Supports the keywords this contract actually uses: type, enum, const,
    required, properties, additionalProperties, pattern, minLength,
    minimum, maximum, minItems, uniqueItems, items, anyOf, allOf, not,
    $ref (local #/definitions only), if/then/else.
    """
    errors: list = []

    def fail(msg):
        errors.append(f"{path}: {msg}")

    def resolve_ref(ref: str):
        if not ref.startswith("#/"):
            raise SchemaError(f"unsupported $ref (not local): {ref}")
        node = schema
        for part in ref[2:].split("/"):
            node = node[part]
        return node

    def is_type(value, expected) -> bool:
        if expected == "object":
            return isinstance(value, dict)
        if expected == "array":
            return isinstance(value, list)
        if expected == "string":
            return isinstance(value, str)
        if expected == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if expected == "boolean":
            return isinstance(value, bool)
        if expected == "null":
            return value is None
        raise SchemaError(f"unsupported type keyword: {expected}")

    def matches(value, sch, path) -> bool:
        return not _check(value, sch, path)

    def _check(value, sch, path):
        local_errors = []
        if "$ref" in sch:
            sch = resolve_ref(sch["$ref"])

        if "type" in sch:
            expected = sch["type"]
            if isinstance(expected, str):
                if not is_type(value, expected):
                    local_errors.append(f"{path}: expected type {expected}")
                    return local_errors
            else:
                if not any(is_type(value, t) for t in expected):
                    local_errors.append(f"{path}: expected one of types {expected}")
                    return local_errors

        if "const" in sch and value != sch["const"]:
            local_errors.append(f"{path}: must equal {sch['const']!r}")
        if "enum" in sch and value not in sch["enum"]:
            local_errors.append(f"{path}: {value!r} not in enum {sch['enum']}")

        if isinstance(value, str):
            if "pattern" in sch:
                try:
                    if not re.search(sch["pattern"], value):
                        local_errors.append(f"{path}: does not match pattern {sch['pattern']}")
                except re.error as exc:
                    raise SchemaError(f"schema pattern invalid ({exc}); CI validator must not silently pass")
            if "minLength" in sch and len(value) < sch["minLength"]:
                local_errors.append(f"{path}: shorter than minLength {sch['minLength']}")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in sch and value < sch["minimum"]:
                local_errors.append(f"{path}: below minimum {sch['minimum']}")
            if "maximum" in sch and value > sch["maximum"]:
                local_errors.append(f"{path}: above maximum {sch['maximum']}")

        if isinstance(value, list):
            if "minItems" in sch and len(value) < sch["minItems"]:
                local_errors.append(f"{path}: fewer than minItems {sch['minItems']}")
            if sch.get("uniqueItems"):
                seen = [json.dumps(item, sort_keys=True) for item in value]
                if len(set(seen)) != len(seen):
                    local_errors.append(f"{path}: array items are not unique")
            if "items" in sch:
                for i, item in enumerate(value):
                    local_errors.extend(_check(item, sch["items"], f"{path}[{i}]"))

        if isinstance(value, dict):
            for req in sch.get("required", []):
                if req not in value:
                    local_errors.append(f"{path}: missing required property {req!r}")
            props = sch.get("properties", {})
            for key, sub in props.items():
                if key in value:
                    local_errors.extend(_check(value[key], sub, f"{path}.{key}"))
            ap = sch.get("additionalProperties", True)
            if ap is False:
                extra = set(value) - set(props)
                if extra:
                    local_errors.append(f"{path}: unexpected properties {sorted(extra)}")
            elif isinstance(ap, dict):
                for key in set(value) - set(props):
                    local_errors.extend(_check(value[key], ap, f"{path}.{key}"))

        if "allOf" in sch:
            for sub in sch["allOf"]:
                local_errors.extend(_check(value, sub, path))
        if "anyOf" in sch:
            if not any(matches(value, sub, path) for sub in sch["anyOf"]):
                local_errors.append(f"{path}: does not match any of the anyOf branches")
        if "not" in sch and matches(value, sch["not"], path):
            local_errors.append(f"{path}: matches a forbidden (not) schema")
        if "if" in sch:
            if matches(value, sch["if"], path):
                if "then" in sch:
                    local_errors.extend(_check(value, sch["then"], path))
            elif "else" in sch:
                local_errors.extend(_check(value, sch["else"], path))

        return local_errors

    try:
        errors.extend(_check(data, schema, path))
    except SchemaError:
        # Validator defects (unsupported constructs) must never masquerade
        # as "valid" - propagate to the caller.
        raise
    except (KeyError, TypeError, re.error) as exc:
        errors.append(f"{path}: validator could not process schema: {exc}")
    return errors


def validate_schema_file(path: Optional[Path] = None) -> int:
    """Schema-contract gate: 0 = registry conforms to releases.schema.json."""
    p = path or REGISTRY_PATH
    try:
        if not p.is_file():
            raise RegistryError(f"registry not found: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (RegistryError, json.JSONDecodeError, OSError) as err:
        print(f"SCHEMA INVALID: {err}")
        return 1
    violations = validate_against_schema(data, schema)
    if violations:
        print(f"SCHEMA INVALID: {len(violations)} violation(s):")
        for v in violations[:20]:
            print(f"  - {v}")
        return 1
    print("SCHEMA OK: registry conforms to releases.schema.json (draft-07 subset validator)")
    return 0


# ---------------------------------------------------------------------------
# Registry drift detection (S2 / Priority 2)
# ---------------------------------------------------------------------------

def diff_registries(previous: dict, current: dict) -> dict:
    """Detect semantic drift between two registry states.

    Categories: added_releases, removed_releases, hash_changes,
    asset_changes (added/removed/size_changed per (filename, sha256) cut),
    status_changes. Drift in hashes/status is contract-relevant;
    provenance.generated_at differences are NOT drift.
    """
    prev_rels = {r.get("release_id"): r for r in previous.get("releases", [])}
    curr_rels = {r.get("release_id"): r for r in current.get("releases", [])}

    added = sorted(set(curr_rels) - set(prev_rels))
    removed = sorted(set(prev_rels) - set(curr_rels))

    hash_changes, status_changes = [], []
    prev_assets, curr_assets = {}, {}
    for rid, rel in curr_rels.items():
        if rid not in prev_rels:
            continue
        old = prev_rels[rid]
        if rel.get("status") != old.get("status"):
            status_changes.append({"release_id": rid, "from": old.get("status"), "to": rel.get("status")})
        for a in rel.get("assets", []):
            key = (rid, a.get("filename"))
            curr_assets.setdefault(key, []).append(a)
        for a in old.get("assets", []):
            key = (rid, a.get("filename"))
            prev_assets.setdefault(key, []).append(a)

    seen_cuts = set()
    for (rid, fname), curr_list in curr_assets.items():
        prev_list = prev_assets.get((rid, fname), [])
        prev_hashes = {a.get("sha256") for a in prev_list}
        for a in curr_list:
            cut = (rid, fname, a.get("sha256"))
            if cut in seen_cuts:
                continue
            seen_cuts.add(cut)
            if a.get("sha256") not in prev_hashes:
                hash_changes.append({"release_id": rid, "filename": fname, "new_sha256": a.get("sha256")})
            elif a.get("size_bytes") != next(
                (p.get("size_bytes") for p in prev_list if p.get("sha256") == a.get("sha256")), None
            ):
                hash_changes.append({"release_id": rid, "filename": fname, "size_changed": True})
    for (rid, fname), prev_list in prev_assets.items():
        if (rid, fname) not in curr_assets:
            for a in prev_list:
                removed_cut = {"release_id": rid, "filename": fname, "sha256": a.get("sha256")}
                if removed_cut not in hash_changes:
                    hash_changes.append(removed_cut)

    return {
        "added_releases": added,
        "removed_releases": removed,
        "hash_changes": hash_changes,
        "asset_changes": [
            c for c in hash_changes if c.get("sha256") or c.get("size_changed")
        ],
        "status_changes": status_changes,
    }


def has_drift(diff: dict) -> bool:
    return bool(
        diff.get("added_releases")
        or diff.get("removed_releases")
        or diff.get("hash_changes")
        or diff.get("asset_changes")
        or diff.get("status_changes")
    )


# --------------- P1.2: vault mirror verification (injected fetcher) -------


def verify_vault(registry: dict, fetcher: Callable[[dict], str], now: Optional[str] = None) -> dict:
    """Verify every vault entry's published hash through an injected fetcher.

    fetcher(vault_entry) must return the artifact's current published sha256
    hex digest, or raise on unavailability. The engine core itself performs
    ZERO network access; the CLI (or a test) supplies the real fetcher.

    Status transitions (schema enum: available / unverified / missing):
    - hash matches    -> "available"   (reality confirmed artifact+hash)
    - hash mismatches -> "unverified"  (registry claim contradicted; needs reconciliation)
    - fetcher raises  -> status unchanged (cannot observe != artifact missing)

    last_verified_at is refreshed on every successful observation (match or
    mismatch), never on fetch errors. Returns a report; mutates `registry`
    in place so callers can choose to persist it.
    """
    vault = registry.get("vault", [])
    mismatches, errors = [], []
    verified = 0
    observed_at = now or utc_now_iso()
    for entry in vault:
        name = entry.get("artifact", "<unknown>")
        try:
            actual = fetcher(entry)
        except Exception as err:  # noqa: BLE001 — reported, never fatal
            errors.append({"artifact": name, "error": str(err)})
            continue
        if not isinstance(actual, str) or not SHA256_RE.match(actual):
            errors.append({"artifact": name, "error": f"fetcher returned invalid sha256: {actual!r}"})
            continue
        if actual == entry.get("sha256"):
            entry["mirror_status"] = "available"
            verified += 1
        else:
            entry["mirror_status"] = "unverified"
            mismatches.append({"artifact": name, "expected": entry.get("sha256"), "actual": actual})
        entry["last_verified_at"] = observed_at
    return {"checked": len(vault), "verified": verified, "mismatches": mismatches, "errors": errors}


# --------------- P1.3: recommended policy write path (clause 9) -----------


def apply_policy(registry: dict, decision: dict) -> dict:
    """Set the registry's recommended release from a policy decision.

    `latest` is a chronological fact; `recommended` is a policy decision
    (Execution Contract clause 9 — the two must never be conflated). This is
    the ONLY sanctioned write path for `recommended`: it requires
    `recommended_by` provenance, a dated decision, and a rationale, it never
    touches chronology, and it keeps the recommendation unique across the
    registry. Returns a new registry dict; the input is not mutated.
    """
    if not isinstance(registry, dict) or "releases" not in registry:
        raise PolicyError("apply_policy requires a registry dict with a 'releases' list")
    by = (decision.get("recommended_by") or "").strip()
    if not by:
        raise PolicyError("policy decision refused: recommended_by provenance is required (clause 9)")
    rationale = (decision.get("rationale") or "").strip()
    if not rationale:
        raise PolicyError("policy decision refused: a rationale is required (clause 9)")
    decided_at = (decision.get("decided_at") or "").strip()
    if not decided_at:
        raise PolicyError("policy decision refused: decided_at is required (clause 9)")
    release_id = (decision.get("release_id") or "").strip()
    if not any(r.get("release_id") == release_id for r in registry["releases"]):
        raise PolicyError(f"policy decision refused: unknown release_id '{release_id}'")

    updated = copy.deepcopy(registry)
    for rel in updated["releases"]:
        rel.pop("recommended", None)
    target = next(r for r in updated["releases"] if r["release_id"] == release_id)
    target["recommended"] = True
    updated["policy"] = {
        "recommended_by": by,
        "decided_at": decided_at,
        "rationale": rationale,
    }
    return updated


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
