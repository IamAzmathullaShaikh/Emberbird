# Project Emberbird — Metamorphosis Programme (Charter)

**Objective:** Transform the repository from a WSABuilds-based implementation
into the **Emberbird lifecycle platform** using:
Inventory → Contracts → Registry → Consumers → Identity → Distribution —
while preserving legal attribution, historical releases, published artifacts,
reproducibility, and rollback capability.

**Frozen roadmap:** Metamorphosis Programme v3. Architecture freeze is in
effect: no new phases, no new architecture, no redesign. Only the currently
unlocked phase may receive implementation work.

---

## Governing rules

| Rule | Statement |
|---|---|
| **M4 — Release History Is Immutable** | Never delete tags, rewrite published release metadata, rename historical assets, or mutate published winget manifests. Everything historical remains historical; new identity ships as *new* packages. (Contract clause 13.) |
| **S1 — Historical Identity Preservation** | Historical project names (WSABuilds, MagiskOnWSA lineage, MustardChef, Microsoft WSA) remain visible wherever attribution, licensing, migration documentation, historical release records, or provenance require them. Emberbird may replace branding; Emberbird may not erase history. (Contract clause 14.) |
| **G1 — Metamorphosis Freeze** | From E2 until E5 completes: no new features, no new architecture, no new roadmap phases, no ARM64 implementation, no distribution expansion. Only metamorphosis-programme tasks may merge. |
| **G2 — Consumer Migration Contract** | Before migrating a consumer: inventory its metadata inputs and release-discovery logic; provide a migration diff and rollback path; the consumer must support Registry, Contract, and the Reality Gate before legacy discovery is removed. |
| **S2 — Migration Success Rule** | A consumer migration is complete only when registry output and legacy output produce **equivalent results for the same release set**. Parity is demonstrated before legacy discovery is removed. |
| **S3 — Phase Abort Rule** | If CI, Reality Gates, attribution tests, contract tests, or registry purity tests fail, the current phase aborts, the latest rollback tag becomes authoritative, and the next phase stays locked. |
| **G3 — Historical Preservation Manifest** | `docs/HISTORICAL_PRESERVATION.md` (lands at E5.5) keeps historical tags, releases, checksums, winget IDs, download URLs, and documentation references traceable forever. |
| **G4 — Programme Control Board** | `docs/programme-board.md` tracks Open / Deferred / Rejected / Adopted programme decisions, separate from architecture ADRs. |

## Master mapping (summary)

The authoritative mapping is `docs/PATH_MAP.md` (E1). Summary of the taxonomy:

| Legacy | New |
|---|---|
| `Documentation/` | `docs/archive/` |
| `WSABuilds Utilities/` | `utilities/` |
| `MagiskOnWSA/scripts/` toolchain | `tools/` |
| Unmodified-from-upstream files | `upstream/` (inventory-classified) |

## Execution model

Every phase: declare in TODO.md → implement → full validation battery →
scoped commit → push → CI ratification → cycle record → rollback tag.
No phase opens before its predecessor is CI-ratified. The safety net is
`tests/test_metamorphosis_contract.py` (M1), the attribution tests (M2), and
`tests/test_consumer_compliance.py` (M3).

## Success criteria (M5)

1. Registry drives all consumers · 2. No GitHub release discovery in any
consumer · 3. All consumers migrated · 4. No AGPL regressions · 5. No
attribution regressions · 6. All phases CI-ratified · 7. Zero TODO items
(except formally environment-gated Task 5.1). The Repository Health Score is
an **output** of these criteria, never a goal.
