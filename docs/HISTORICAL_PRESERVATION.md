# Emberbird Historical Preservation Manifest (G3)

**Charter clause:** `docs/METAMORPHOSIS.md` G3 — historical tags, releases,
checksums, winget IDs, download URLs, and documentation references remain
traceable forever. **M4:** release history is immutable.

**Rule:** this manifest records history; it never replaces it. Every row below
points at truth that still exists (or remains resolvable through GitHub's
forward redirect after the E4.3 rename). Nothing here is editable history —
amendments append, they never rewrite.

## Historical winget package identity

| Field | Historical value | Status |
|---|---|---|
| Package identifier | `WSABuilds.WSABuildsManager` | Frozen — manifests preserved under `manifests/w/WSABuilds/WSABuildsManager/` |
| Publisher | `WSABuilds` | Frozen |
| Product name | `WSABuilds Manager` | Frozen |
| Artifact prefix | `WSABuildsManager-` (Setup / Portable / checksums) | Frozen — published asset filenames are immutable |

## Historical published releases (Manager)

| Version | Tag | Artifacts (published names) | Installer SHA-256 |
|---|---|---|---|
| 0.2.0 | `v0.2.0` | `WSABuildsManager-Setup-0.2.0-x64.exe`, portable + checksums sidecars | see `manifests/w/WSABuilds/WSABuildsManager/0.2.0/` |
| 0.2.1 | `v0.2.1` | `WSABuildsManager-Setup-0.2.1-x64.exe`, portable + checksums sidecars | see `manifests/w/WSABuilds/WSABuildsManager/0.2.1/` |
| 0.2.2 | `v0.2.2` | `WSABuildsManager-Setup-0.2.2-x64.exe`, `WSABuildsManager-Portable-0.2.2-x64.zip`, `WSABuildsManager-0.2.2-checksums.txt` | `887443bad0aeb3eec04ff367b4768edad2cc0e1b2fcd6b9b255f5bfd3181466a` (Setup x64) |

Release URLs (redirect-safe): `https://github.com/IamAzmathullaShaikh/WSABuilds/releases/tag/v<version>`.

## Historical WSA releases

The authoritative historical record for WSA builds is the **Ember Registry**
(`data/releases/releases.json`) — registry `source_url`s keep the historical
repository slug and resolve through the rename redirect. This manifest does
not duplicate registry truth; it links to it.

## Known historical inaccuracies (recorded, not corrected)

| Surface | Inaccuracy | Disposition |
|---|---|---|
| `manifests/w/WSABuilds/WSABuildsManager/*/…locale.en-US.yaml` | `License: Apache-2.0` (the repository was and is AGPL-3.0) | Frozen verbatim — what was published is what was published. The active package (`Emberbird.Manager`) carries the truthful `AGPL-3.0` claim. |
| Website footer (pre-E3A) | Claimed Apache-2.0 | Corrected at E3A (living surface). |

## Historical binary lineage

The Manager binary published before E5 was built from this repository's
historical identity. It is a **modified Windows Subsystem for Android
lifecycle manager**, distributed under AGPL-3.0 with full attribution to the
MagiskOnWSA / WSABuilds lineage (see `docs/archive/` and `docs/BRAND.md` §6).
It was never a Microsoft-published binary, and Microsoft trademarks are
described, never claimed (BRAND §8 rule 4).

## Governance

- Historical manifests are sanity-checked by
  `scripts/validate_distribution.py` (`_validate_historic_manifests`) but are
  **never mutated**.
- Boundary guards: `tests/test_e5_distribution_identity.py`,
  `tests/test_e4_slug_contract.py` (frozen-truth class),
  `tests/test_governance_guards.py` (M4/S1 clauses).
