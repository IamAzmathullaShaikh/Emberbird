# Emberbird License Audit (P0.1)

Status: living document · Last full audit: P0 (September 2026)
Scope: all code and content distributed by this repository.

## 1. Repository license

| Item | License | Notes |
|---|---|---|
| This repository (code, scripts, contracts, docs) | **AGPL-3.0** (`/LICENSE`) | Inherited from the WSABuilds ancestry. Applies to all Emberbird-authored files. |

Implications for Emberbird work:

1. Any network service built from this code (e.g. a future metadata service
   exposed over HTTP) must offer its source to its users — the registry
   generator and engine are fine as build-time CLI tools, but a hosted
   deployment of them would trigger the network-use clause.
2. Vendored or copied code from other projects must preserve its upstream
   license headers and be listed below.

## 2. Third-party components consumed at build time

| Component | License | How used | Provenance recorded |
|---|---|---|---|
| Windows Subsystem for Android (MSIX) | **Proprietary (Microsoft)** | Downloaded from Microsoft's endpoints; patched per documented patch set; redistributed as part of builds | Registry asset `source_url` per release |
| Magisk (topjohnwu) | **GPL-3.0** | Downloaded at build time from `topjohnwu/magisk-files`; embedded into the patched subsystem as the root solution | `generateMagiskLink.py`; registry provenance |
| MindTheGapps | **Apache-2.0** | Optional GApps image embedded when the user selects GApps variants | `generateGappsLink.py`; registry provenance |
| WSA-Addon / community sidecars | Per-upstream (audited per asset) | Hash sidecars and supplementary assets | Vault `hash_source: sidecar` records |

**GPL-3.0 note (Magisk):** embedding Magisk inside distributed WSA builds
obligates the distributor to provide the corresponding source for the
combined work. Magisk's source is public at
`https://github.com/topjohnwu/Magisk`; the pinned version per release is
recorded in registry provenance. This is the same posture upstream
WSABuilds takes; Emberbird documents it explicitly here.

**Proprietary note (WSA MSIX):** Microsoft's binaries are redistributed as
Microsoft published them (plus documented patches), without any claim of
ownership or endorsement. Emberbird's *own* claim is limited to the
patch set and the surrounding platform. If Microsoft requests
redistribution changes, the registry's supersession machinery is the
compliance mechanism: affected builds are marked `superseded`/`removed`,
never silently deleted.

## 3. Attribution obligations

- The charter (`docs/EMBERBIRD_CHARTER.md`) disclaims ownership of
  Microsoft's product; the shipped subsystem remains "Windows Subsystem
  for Android (modified)".
- Per-component credits live in `docs/ATTRIBUTION.md`.
- Registry provenance records (`provenance.tool`, `provenance.commit`)
  tie every generated entry to the exact tooling that produced it.

## 4. Gaps and follow-ups

1. The upstream WSA EULA is presented to users at install time by the
   installer itself; Emberbird does not re-display it. A future Manager
   release should surface a "licenses" screen (tracked for Phase 2).
2. If Emberbird ever ships its own signed binaries, signing-key policy
   (Phase 6, Trusted Signing) must add a key-governance addendum to this
   audit.
