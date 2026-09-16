# Emberbird Engineering & Validation Tooling

The `scripts/` directory contains standalone automation, security, validation, and release engineering tools for the **Emberbird** platform. All tools are designed to operate deterministically across Linux, macOS, and Windows.

---

## 1. Catalog of Tools & Validators

| Script | Purpose / Scope | Execution Environment |
|---|---|---|
| **`check_doc_links.py`** | Markdown Local Link Validator. Recursively scans all `.md` files to detect broken relative links, missing files, and invalid heading anchors. | Python 3.10+ |
| **`security_scan.py`** | Security & Secret Scanner. Audits the entire repository for personal access tokens, credentials, private keys, and hardcoded machine paths (`C:\Users\...`). | Python 3.10+ |
| **`validate_distribution.py`** | Distribution & Winget Validator. Asserts semver consistency between `deployment/version.json`, `package.json`, `Cargo.toml`, and validates Winget v1.6.0 manifests. | Python 3.10+ (`pyyaml`) |
| **`validate_analytics.py`** | Privacy-First Analytics Validator. Validates telemetry payload against `services/analytics/schema.json` and asserts strict Zero-PII compliance. | Python 3.10+ |
| **`validate_compatibility.py`** | Compatibility Database Validator. Validates community application records in `compatibility/data/` against `compatibility/schema.json`. | Python 3.10+ |
| **`validate_package_identity.py`** | AppX Identity Baseline Comparator. Compares `AppxManifest.xml` against `config/baseline-identity.json` to prevent package family name drift. | Python 3.10+ |
| **`validate_package_integrity.py`** | Structural Package Validator. Verifies required loose-folder registration files, PowerShell scripts, and binary tools in extracted release packages. | Python 3.10+ |
| **`validate_magisk.py`** | Magisk Trampoline Validator. Inspects `initrd.img` SVR4 CPIO structure, verifying `.backup`, `lspinit`, `magiskboot`, and `overlay.d/sbin/init-ld.xz`. | Python 3.10+ |
| **`validate_gapps.py`** | Google Play Overlay Validator. Inspects `gapps-13.0-x86_64.img` ext4 loopback mount points, verifying Play Store, Play Services, and GSF. | Python 3.10+ |
| **`generate_release_metadata.py`** | Release Metadata & Digest Generator. Calculates GNU SHA-256 digests and emits machine-readable `release-metadata.json`. | Python 3.10+ |

---

## 2. CLI Usage Examples

```powershell
# Verify local Markdown links across entire repository
python scripts/check_doc_links.py

# Perform security, secret, and path hygiene audit
python scripts/security_scan.py

# Validate distribution version metadata and Winget manifests
python scripts/validate_distribution.py

# Validate privacy-first analytics and Zero-PII adherence
python scripts/validate_analytics.py

# Validate all community compatibility records
python scripts/validate_compatibility.py

# Validate AppX package identity against baseline
python scripts/validate_package_identity.py --baseline config/baseline-identity.json
```

---

## 3. Exit Code Conventions

All validation scripts adhere to standard POSIX exit codes:
- **`0`**: Validation passed successfully with zero defects.
- **`1`**: Validation failed (defect or violation detected).
- **`2`**: Operational error (invalid arguments or missing required files).
