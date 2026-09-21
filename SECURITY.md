# Security Policy — Project Emberbird

**Platform**: Emberbird (registry-first lifecycle platform for Android on Windows)  
**Governance**: `docs/EMBERBIRD_CHARTER.md` · `data/contracts/release-contract.md`  
**License**: AGPL-3.0 (code/tooling) · CC-BY-NC-ND-4.0 (documentation)

---

## 1. Reporting Security Vulnerabilities

We take the security of Emberbird, its build pipeline, and its distribution mechanisms seriously. If you discover a potential security vulnerability, please do **NOT** disclose it publicly in issues, discussions, or social media.

### Sanctioned Reporting Channel
- **Private Vulnerability Reporting**: Submit through [GitHub Security Advisories](https://github.com/IamAzmathullaShaikh/Emberbird/security/advisories/new).
- **Direct Maintainer Contact**: If GitHub Advisories is unavailable, contact the repository steward directly via the email address on their GitHub profile with `[SECURITY: Emberbird]` in the subject line.

### Response Timelines
- **Initial Acknowledgement**: Within 48 hours of receipt.
- **Triage & Reproduction**: Within 5 business days.
- **Remediation & Advisory Publication**: Coordinated disclosure within 30 to 90 days depending on severity.

---

## 2. Supported Versions

Only the current flagship release series receives security updates and vulnerability triage:

| Component | Active Version | Support Status |
|---|---|---|
| **Windows Subsystem for Android (Modified)** | `2407.40000.4.0` (Android 13) | **Supported** (Active Flagship) |
| **Emberbird Manager** | `0.2.2` | **Supported** (Active Desktop Client) |
| **Release Engine & Tooling** | Main branch (`platform/release-engine`) | **Supported** |
| Historical WSABuilds releases | `< 2407.40000.4.0` | **Unsupported** (Preserved for archive only) |

---

## 3. Security Architecture & Posture

Emberbird enforces an defense-in-depth security model across its registry, pipelines, and runtime tooling:

### 3.1 Microsoft Root Certificate Trust
Network interactions with Microsoft's Windows Update Delivery Network (FE3) are secured via a bundled Microsoft Root CA 2011 / Intermediate CA 2.1 certificate bundle (`upstream/cacerts/`). This guarantees that:
- Update lookups verify against Microsoft's authentic cryptographic roots.
- Local host OS certificate store tampering or proxy interception cannot inject malicious package URLs.

### 3.2 Zero-PII Telemetry Doctrine
The platform aggregates public telemetry only through the opt-in analytics service (`services/analytics/`):
- **Disabled by default**: Telemetry requires explicit user opt-in.
- **Zero personal identifiers**: The registry, metadata services, and analytics endpoints collect **0 IP addresses, 0 device IDs, 0 MAC addresses, 0 usernames, 0 emails, 0 auth tokens, and 0 hardware fingerprints**.
- **Automated enforcement**: CI continuously executes `scripts/validate_analytics.py` to verify that analytical datasets contain zero PII.

### 3.3 Registry Cryptographic Verification
- **Published Artifacts Are Truth**: Every artifact listed in `data/releases/releases.json` is pinned to its SHA-256 cryptographic hash computed directly from published bytes.
- **Rejection of Placeholder Hashes**: The Draft-07 registry schema (`data/releases/releases.schema.json`) structurally forbids all-zero placeholder hashes.
- **Download Verification**: Users and consumers verify package hashes before extraction using `Get-FileHash -Algorithm SHA256`.

### 3.4 Automated Secret & Credential Scanning
Every commit and pull request runs `scripts/security_scan.py` and the Gitleaks secret scanner (`.github/workflows/gitleaks.yml`) to ensure:
- Zero personal access tokens, API keys, private keys, or credentials exist in the tree.
- Zero private host machine paths or developer usernames are committed.

`gitleaks.yml` is the single owner of secret scanning: it runs Gitleaks on every push/PR plus a weekly full-history scan, and additionally executes the hardcoded-machine-path / developer-username gate that Gitleaks cannot perform.

### 3.5 Third-Party Component Provenance
Emberbird redistributes unmodified Microsoft WSA packages alongside patched ramdisks containing:
- **Magisk**: Root solution under GPL-3.0 by topjohnwu (Standard Edition).
- **OpenGApps Pico**: Google Play services under Apache-2.0.
All third-party components are pinned by version, origin URL, and hash in registry provenance metadata.
