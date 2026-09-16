---
title: "Compatibility Moderation & Submission Governance"
description: "This guide outlines the governance standards, verification lifecycles, and moderation criteria for the Emberbird Application Compatibility Directory."
category: "community"
order: 4
---

This guide outlines the governance standards, verification lifecycles, and moderation criteria for the Emberbird Application Compatibility Directory.

## 1. Overview

The Emberbird Compatibility Directory bridges the gap between Windows Subsystem for Android and popular mobile applications that require hardware attestation, root hiding, or Google Mobile Services.

To guarantee that users find accurate, reliable, and actionable information, every compatibility report is subject to automated validation and community moderation.

---

## 2. Submission Lifecycle

### Phase 1: Community Reporting
Users submit compatibility results using the standardized GitHub Issue Form:
- Application Name and Package Identifier (e.g. `com.phonepe.app`)
- Operational Status (`Working`, `Workaround Required`, `Broken`)
- Primary Category (e.g. `Banking & UPI`, `Social & Communication`)
- Tested WSA Version and Root Flavor
- Play Integrity requirement status
- Clear, step-by-step workaround instructions (if applicable)
- Known limitations or hardware constraints

### Phase 2: Automated Schema Validation
Every submission converted into a pull request triggers the `compatibility-validation.yml` workflow:
- Validates the JSON record against `compatibility/schema.json`.
- Confirms package ID regex matches reverse-DNS format.
- Checks that category and status strings belong to approved enums.
- Executes Python and Node compatibility unit tests.

### Phase 3: Verification Progression
Records transition through three distinct trust tiers:
1. `community_submitted`: Newly contributed reports from users.
2. `unverified`: Formally structured records undergoing review.
3. `verified`: Confirmed by maintainers in test environments.

---

## 3. Moderation & Safety Criteria

To preserve portal integrity and user security:
- **No Malicious Packages**: Submissions must correspond to legitimate, publicly identifiable applications from official repositories (e.g. Google Play Store, F-Droid).
- **No Direct APK Links**: Reports must never include external direct file download links or third-party mirror URLs.
- **Reproducible Workarounds**: Workaround steps must use verified open-source tooling (e.g., Magisk Stable, Shamiko, PlayIntegrityFix).
- **Clear Limitations**: Known hardware limitations (such as lack of Bluetooth LE or camera autofocus) must be transparently noted.
