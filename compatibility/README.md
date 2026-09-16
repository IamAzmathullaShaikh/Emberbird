# Compatibility Hub Data & Moderation Architecture

This directory contains verified and community-submitted application compatibility records for Windows Subsystem for Android (WSA). It serves as the single source of truth for the Emberbird compatibility portal.

## Directory Structure
- `schema.json`: Strict JSON Schema (Draft-07) defining valid fields, package ID formatting, and category enums.
- `data/`: Canonical, verified JSON records for Android applications (e.g. `PhonePe.json`, `Paytm.json`).
- `submissions/`: Staged community test reports awaiting verification or lab reproduction.
- `templates/`: Example template (`template.json`) conforming to `schema.json`.

## Moderation Architecture & Lifecycle

All compatibility data undergoes strict verification to prevent fraudulent reports or invalid configurations:

```text
[Community Report via Issue Form]
                 │
                 ▼
[PR Opened with compatibility/data/<App>.json]
                 │
                 ▼
[CI Automated Validation: compatibility-validation.yml]
  ├── Validates JSON syntax & schema constraints
  ├── Verifies package_id reverse-DNS format
  ├── Enforces valid category & status enums
  └── Executes compatibility test suite
                 │
                 ▼
[Maintainer Review & Lab Reproduction]
                 │
                 ▼
[Merged to master -> Auto-Synced to Website Portal]
```

## Verification Status Progression

- `community_submitted`: Initial report submitted by community member; pending maintainer triage.
- `unverified`: Staged record with documented workaround; awaiting automated or physical lab reproduction.
- `verified`: Thoroughly validated by maintainers on physical Windows 11/10 hardware with live root/GApps runtime checks.

## Security & Submission Guidelines

1. **No External URLs**: Compatibility records must never contain arbitrary external download URLs or APK links.
2. **Standardized Workarounds**: Workaround steps must reference standard tools (e.g. Magisk DenyList, Shamiko, PlayIntegrityFix) without custom proprietary payloads.
3. **Reproducibility**: Issues and workaround steps must be clearly described and reproducible on standard retail WSA builds.
