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

## 7. Repository identity (E4.1 slug contract)

**Canonical repository identity: `IamAzmathullaShaikh/Emberbird`.**

**Slug boundary — what may and may not be rewritten:**

| Class | Rule |
|---|---|
| **Rewrite (living identity pointers)** | Badges, canonical clone URLs, issue/discussion links in living docs, `.env.example` identity values, website README env examples, and the fork-parent reference in this document (§1). |
| **Pin with E4.3 flip marker (publication plumbing)** | Anything that could poison a real publication before `IamAzmathullaShaikh/Emberbird` exists: `winget-release.yml` slug env, `apps/manager/src/lib/env.ts` embedded default. These carry an `<!-- E4.3-FLIP: ... -->` (or `# E4.3-FLIP:`) marker and a documented flip command. |
| **Keep (frozen truth, S1)** | Registry `source_url` values, registry-sidecar URL strings, published winget manifests, `docs/archive/**`, all cycle/audit records (CLEANUP_REPORT, REMOVED_ROOT_SOLUTIONS, TODO cycle records), upstream sync target, attribution anchors. GitHub's forward redirect keeps every historical URL resolvable. |

**Ordering guarantee:** the owner's rename (E4.3) happens via GitHub → Settings → General →
"Rename repository". Git history, tags, releases, stars, issues, and web traffic follow the
rename; GitHub 301-redirects all old URLs. Nothing in this contract requires breaking
historical URL truth — frozen URLs keep working forever through the redirect.

**E4.3 flip (owner action, single command):**
`grep -rl "E4.3-FLIP" --include="*.yml" --include="*.ts" . | xargs sed -i 's/IamAzmathullaShaikh\/WSABuilds/IamAzmathullaShaikh\/Emberbird/g'`
(then remove the markers, commit, push). Publication systems then build from the new slug.

**Guard:** `tests/test_e4_slug_contract.py` pins this table: rewritten surfaces stay
rewritten, pinned surfaces carry flip markers, frozen truth keeps the historical slug.

**Status (2026-09-17): E4.3 EXECUTED.** The GitHub rename was performed and the
flip applied: publication plumbing now points at the canonical slug, flip markers
are removed, and `IamAzmathullaShaikh/WSABuilds` resolves through GitHub's
forward redirect. Frozen truth keeps the historical slug permanently.

## 8. Distribution identity (E5)

**Active distribution identity (from `deployment/version.json` — the seam):**

| Field | Value |
|---|---|
| Winget package | `Emberbird.Manager` |
| Publisher | `Emberbird` |
| Product name | `Emberbird Manager` |
| Artifact prefix | `EmberbirdManager-` (Setup / Portable / checksums) |
| License claim | `AGPL-3.0` (truthful — Legal Compliance Gate) |

**Rules:**

1. **New identity ships as a new package.** `WSABuilds.WSABuildsManager` and its
   manifests under `manifests/w/WSABuilds/` are frozen history (M4) — never mutated,
   never re-licensed, never re-pointed. Guard: `tests/test_e5_distribution_identity.py`.
2. **Published artifact filenames are observed reality.** The new package's manifests
   reference the artifacts that were actually published (e.g. `WSABuildsManager-Setup-0.2.2-x64.exe`)
   with the exact published hashes. Future releases built by this repository publish
   `EmberbirdManager-*` artifacts and manifests derive from `version.json`.
3. **License claims must be truthful.** The repository is AGPL-3.0; any Apache-2.0 claim
   in *living* metadata is a fabrication defect. Historical manifests keep their original
   (erroneous) claims verbatim — that is what was published, and history is not rewritten.
4. **Trademark hygiene** in all new identity surfaces: describe the product as a
   lifecycle platform for Android on Windows / a modified Windows Subsystem for Android
   distribution; never imply Microsoft affiliation.
5. **Data-directory continuity:** the Manager's real backup directory
   (`%LOCALAPPDATA%\WSABuilds\backups`) keeps its name until a real migration path
   exists — renaming it would orphan existing users' verified backups.
