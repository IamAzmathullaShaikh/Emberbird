# Project Phoenix — The Emberbird Charter

**Project Codename**: Phoenix  
**Platform Name**: Emberbird  
**Repository**: https://github.com/IamAzmathullaShaikh/WSABuilds  
**Charter Version**: 1.0 (Phase P0 Foundation)

---

## 0. Foundational Principles & The Bold Rule

> **Published Artifacts Are Truth.**  
> **Registry reflects Reality.**  
> **Contracts define Reality.**  
> **Consumers trust Contracts.**  
> **Nothing trusts assumptions.**

Before any other consideration, any claim this project makes — a download link, a hash, a compatibility note, a "works on your device" promise — must be backed by published, hash-verified artifacts. If documentation, intuition, or commentary disagree with published reality: **published reality wins** and documentation is updated.

---

## 1. Mission

Build Emberbird: a lifecycle platform for Android on Windows.

### Emberbird IS:
- A **release intelligence** platform
- A **lifecycle** platform
- A **validation** platform
- A **compatibility** platform
- A **distribution** platform
- A **sustainability** platform

### Emberbird is NOT:
- A simple WSA fork
- A build script collection
- A GitHub release repository
- An app store or third-party APK broker
- A rebrand of Microsoft's proprietary product

---

## 2. Architectural Independence

1. **Repository Independence Rule**:
   The release registry remains valid even if GitHub Releases disappear, GitHub API becomes unavailable, builders change, workflows change, or distribution providers change. Consumers depend only on the Registry (`data/releases/releases.json`) and frozen Contracts (`data/contracts/`).
2. **Builder Independence Rule**:
   Builders create releases; the Registry describes releases; consumers consume releases. Consumers never consume builders or builder internals.
3. **Distribution Independence Rule**:
   Winget, Chocolatey, Scoop, Web Portals, Desktop Managers, and CLIs consume the Registry. No distributor owns release metadata.

---

## 3. Truth Hierarchy

When sources disagree, the higher layer strictly overrides the lower:

| Level | Source | Description |
|---|---|---|
| **Level 1** | **Published Artifacts** | Real package bytes (`.7z`, `.exe`, `.zip`) |
| **Level 2** | **Published Checksums** | SHA-256 manifests and sidecars computed from bytes |
| **Level 3** | **Published Metadata** | Validated release metadata files (`release-metadata.json`) |
| **Level 4** | **Repository Metadata** | Authoritative registry (`releases.json`, `version.json`) |
| **Level 5** | **Documentation** | README, charters, contracts, and guides |

---

## 4. Protected Subsystems

Nothing in these systems may regress during any execution phase:
- WSA Release Pipeline
- Standard Edition (Magisk-rooted)
- Banking Edition (vanilla / non-rooted)
- Manager Desktop Client
- Downloads Portal & Web Experience
- Compatibility Hub & Validation Harness
- Analytics Aggregation Engine
- Release Automation & GitHub Releases
- Winget Manifests & Packaging
- CI/CD Pipelines (`build.yml`, `security.yml`, `docs-validation.yml`, etc.)
- Clean Room E2E Harness

---

## 5. Governance & Guardrails

### Legal Guardrails
- Repository code, scripts, contracts, and docs are governed under **AGPL-3.0**.
- Microsoft's Windows Subsystem for Android binaries are redistributed as published (with documented patches) without claiming Microsoft trademarks, kernels, or proprietary payloads. Shipped packages are designated as *Modified Windows Subsystem for Android distribution*.
- Third-party components (Magisk under GPL-3.0, MindTheGapps under Apache-2.0) maintain upstream license obligations and provenance records.

### Privacy Guardrails (Zero PII Doctrine)
- Telemetry is opt-in and disabled by default.
- The registry and metadata services must **never** contain emails, usernames, device IDs, IP addresses, tokens, fingerprints, or installation identifiers.

### Responsible AI Guardrails
- AI assistance must be transparent, auditable, reviewable, and human-overridable.
- AI must not auto-publish releases, modify host systems silently, or invent compatibility statuses without empirical evidence.

---

## 6. Phase Roadmap Summary

- **P0 — Foundation** (ACTIVE): Registry, Schema, Governance, Contracts, Engine, Charter
- **P1 — Registry Consumers**: Transition consumers to registry-derived lookups
- **P1.5 — Vault Auditor**: Automated mirror verification & availability scoring
- **P1.6 — Archive Index**: Cold-storage indexing
- **P2 — CLI**: Command-line developer interface
- **P3 — ARM64 Completion**: Cross-compilation & multi-arch packaging
- **P4 — Control**: Enhanced desktop orchestration
- **P5 — Portal & Observatory**: Telemetry-informed policy & web experience
- **P6 — Distribution Expansion**: Additional package managers
- **P7 — Trusted Signing**: Cryptographic attestation
- **P8+ — Research**: Future Android/Windows subsystem compatibility
