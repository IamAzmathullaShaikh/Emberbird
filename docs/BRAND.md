# Emberbird Brand & Identity Policy

**Programme:** Project Emberbird — Metamorphosis Programme v3 (Phase E1)
**Inventory of record:** `docs/identity-inventory.json` (regenerate with `python scripts/identity_map.py --check`)
**Related:** `docs/METAMORPHOSIS.md` (charter) · `docs/PATH_MAP.md` (directory mapping) · clauses 13–14 of the Execution Contract

---

## 1. Canonical identity

| Layer | Value |
|---|---|
| Project name | **Emberbird** |
| Registry | the **Ember Registry** (`data/releases/releases.json`) |
| Observability decision system | **Ember Observatory** (P5; the only sanctioned `recommended` writer via `apply-policy`) |
| Engine package | `release_engine` (`platform/release-engine/`) |
| Governance charters | `docs/PHOENIX_CHARTER.md` (supreme) → `docs/EMBERBIRD_CHARTER.md` → this document |

## 2. The never-touch list (S1 — Emberbird may replace branding; it may not erase history)

1. **Upstream attribution** — MustardChef, the MagiskOnWSA/MagiskOnWSALocal
   lineage, and Microsoft WSA remain visible in `docs/ATTRIBUTION.md`,
   `docs/LICENSE_AUDIT.md`, and wherever provenance requires them.
2. **License texts** — `LICENSE` (AGPL-3.0) and `LICENSE-CC-BY-NC-ND` are
   verbatim-immutable; only upstream or law can change them.
3. **Historical release truth** — tags (`wsa-v2311.40000.5.0`, `v0.2.x`),
   release IDs, checksums, assets, and release notes are immutable (M4).
4. **Published winget manifests** — `manifests/w/WSABuilds/**` are frozen
   history; the Emberbird distribution identity ships as a **new package**,
   never as a mutation of published manifests.
5. **Historical documentation** — `Documentation/**` (soon `docs/archive/**`)
   is preserved as historical record; brand tokens inside it are part of the
   history it records.
6. **Legal names of third parties** — Microsoft, Google, Magisk (topjohnwu),
   OpenGApps are referenced factually, never rebranded.

## 3. Identity classes and their policy

Every identity occurrence in the repository belongs to exactly one class
(`scripts/identity_map.py`). Policy per class:

| Class | Count (E1 baseline) | Policy |
|---|---|---|
| `upstream-attribution` | 30 | **PROTECTED** — never renamed |
| `historical-doc` | 345 | **PROTECTED** — never renamed (history) |
| `package-name` | 48 | New packages at E5; published package names are history |
| `workflow-name` | 82 | Rebranded in place at E3A (workflow `name:` and display text) |
| `url` | 70 | Rewritten at E4 (repository rename) |
| `path-reference` | 112 | Remapped at E2 per PATH_MAP |
| `user-facing` | 35 | Rebranded at E3A |
| `doc-prose` | 115 | Rebranded at E3A (S1-reviewed; attribution prose stays) |
| `identifier` | 192 | Case-by-case review; many are upstream code (protected by classification review at E2) |

## 4. Naming rules

- **Use:** Emberbird (prose), `emberbird` (package/component identifiers),
  `Emberbird` (product/UI).
- **Avoid:** mixing identities in one artifact (a file is Emberbird or it is
  historical record — not both, except for attribution/migration prose, which
  must name both).
- **Migration prose:** documents that describe the metamorphosis itself may
  (and should) name the historical identity — that is S1 preservation, not
  brand leakage.
- **No fabricated history:** never re-date, re-attribute, or re-license
  historical artifacts to match the new brand.

## 5. Rename mechanics (for E3A/E4)

1. Regenerate `docs/identity-inventory.json`.
2. Apply renames **only** to the classes cleared for that phase.
3. Update the pinning tests in the same commit (suite must stay green).
4. Run `python scripts/identity_map.py --check` — the inventory must match the
   tree, proving the rename was exactly as large as recorded and no larger.

## 6. Legal safety statement

Emberbird is an **independent distribution platform** for Windows Subsystem
for Android builds. It distributes independent build tooling and patched
artifacts under AGPL-3.0 with full attribution to upstream
(MustardChef/MagiskOnWSA) and to Microsoft for WSA itself. Emberbird claims no
affiliation with Microsoft; WSA and Windows are trademarks of Microsoft
Corporation; all third-party marks belong to their owners. The AGPL-3.0
obligations (source availability, license text preservation, attribution) are
preserved in full through the metamorphosis — verified by
`tests/test_governance_guards.py` and the attribution tests (E1.5).
