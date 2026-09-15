# Emberbird Release Contract (P0.5)

Status: **FROZEN for P0** · Governs: every consumer of the release registry
Owner: Emberbird governance (see `data/releases/GOVERNANCE.md`)

This contract is the promise the registry makes to everything that reads it —
Website, Manager, Compatibility Hub, Analytics, Winget automation, CI.
A change to the registry that violates this contract is a **breaking change**
and must follow the compatibility-level policy in `data/releases/GOVERNANCE.md`.

---

## 1. Registry Independence Rule (P0.4.2 exit criterion)

> **No consumer may derive release intelligence from anything other than
> `data/releases/releases.json`.**

Concretely:

1. Consumers MUST NOT hardcode release tags, versions, hashes, or URLs.
2. Consumers MUST NOT scrape GitHub releases pages, HTML, or the GitHub API
   to decide *which* release to offer a user.
3. Consumers MUST NOT read ad-hoc docs/markdown files to find download links.
4. Consumers MAY verify what the registry asserts (hash checks, URL liveness)
   — verification is not derivation.
5. The only permitted sources of truth are, in order:
   - `data/releases/releases.json` (the authoritative registry)
   - The schema `data/releases/releases.schema.json` (for validation only)

**Proof**: `tests/test_registry_consumer.py` imports the registry and performs
every consumer-style lookup (latest, recommended, hash-for-artifact, mirror
status) with zero network calls and zero hardcodes. CI runs it on every push.

---

## 2. Published Artifacts Are Truth (banner principle)

1. A release exists in the registry **only if** its artifacts are published
   and their hashes were computed from the published bytes.
2. No hash may be entered that was not computed from real bytes (GOVERNANCE
   of the parent repo, carried forward). The schema enforces this structurally
   (`sha256` cannot be all zeros; `hash_source` is a required enum).
3. `mirror_status: "verified"` requires a fresh byte-hash match, not a
   sidecar read. Sidecar hashes are recorded with `hash_source: "sidecar"`
   and flagged for verification.
4. If reality and docs disagree, reality wins and the registry records
   reality (the registry generator proves this: tag `wsa-v2311.40000.5.0`
   is published with real assets even where older docs said otherwise).

---

## 3. Release identity rules

1. **Identity is `release_id`**, stable across edits. Format:
   `<kind>-<qualifier>-<edition>` for subsystem releases
   (e.g. `wsa-v2311-40000-5-0-standard`), `manager-<version>` for manager.
2. **One GitHub tag may carry multiple editions** — the registry splits
   editions into separate Release entries sharing a `tag`
   (observed reality: `wsa-v2311.40000.5.0` ships standard *and* vanilla).
3. **Same filename, different bytes = different artifacts.** The vault keys
   on `(artifact, sha256)` pairs, not filenames — observed when two tags
   both shipped `WSA_2407.40000.4.0_x64.7z` with different cuts.
4. `recommended` is **policy, not data**: it is set by Ember Observatory
   policy (Phase 5.5), never by the generator. P0 ships with no
   recommendation; consumers fall back to `latest_wsa()`.

---

## 4. Builder Independence Rule

> **The registry MUST NOT depend on any single build pathway.**

1. Registry entries record *what was published*, never *which script built it*.
   A future Builder V2 must produce registry-identical entries.
2. Builder V1 (the legacy WSA build pipeline) is **not retired** until a
   Builder V2 build can be generated, validated, and registered with
   byte-identical artifact semantics. Evolution over replacement.
3. Generator provenance: every registry entry carries `provenance` describing
   how it entered the registry (`tool`, `mode`, `commit`). Regeneration is
   idempotent — byte-stable output for byte-stable inputs, except for
   timestamps recorded under `provenance.generated_at`.

---

## 5. Distribution Policy

1. **Registry-first distribution.** Every distribution surface (Website
   downloads portal, Manager, Winget manifests, future package managers)
   resolves artifacts via the registry, not via hardcoded manifests.
2. **Mirror discipline.** Third-party mirrors are recorded in the vault with
   `mirror_status` (`verified` / `unverified` / `revoked` / `removed`).
   Consumers MUST NOT offer unverified mirrors as primary links.
3. **No fabricated availability.** A download link must not be surfaced for
   an artifact whose bytes cannot be confirmed (hash-verified now, or
   hash-verified at registration plus liveness check since).
4. **Edition clarity.** Standard and Banking editions are distinct products
   with distinct security properties; no surface may present them
   interchangeably or merge their metadata.
5. **Deprecation, not deletion.** Superseded releases stay queryable
   (status `superseded` + `superseded_by` chain) for audit and rollback.
   Registry entries are never silently deleted.

## 6. Validation hooks

1. `python3 platform/release-engine/release_engine/__main__.py validate`
   must exit 0 on every commit that touches `data/releases/`.
2. CI runs the full unit suite, including schema contract tests and the
   registry-only consumer proof, on every push.
3. A registry change that fails `validate` or breaks any test MUST NOT be
   merged. There is no override flag.

## 7. Freeze and evolution

1. This contract is **frozen for P0**. Changes require a new registry
   compatibility level and a migration entry
   (`migration_version` bump in `data/releases/releases.json`).
2. Additive changes (new optional fields, new enum values) may land without
   a freeze break, provided every existing test still passes unchanged.
3. The first registry consumer migration (Website, Manager, or otherwise)
   must cite this contract in its PR description.
