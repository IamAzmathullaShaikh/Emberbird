# Privacy Charter & Community Analytics Specification

## 1. Executive Privacy Charter

WSABuilds is committed to user privacy and software transparency. The platform operates under a strict Zero-Telemetry, Zero-PII (Personally Identifiable Information) mandate:

- **No Remote Telemetry**: Neither the WSABuilds Manager desktop client nor the WSABuilds web portal transmits device identifiers, machine names, or user activities.
- **No IP Address Logging**: Server logs, visitor IP addresses, and geolocation data are neither collected nor retained.
- **No Browser Fingerprinting or Cookies**: The web portal operates without tracking cookies, Google Analytics, third-party advertising SDKs, or session beacons.
- **100% Public Aggregations**: All telemetry and transparency metrics published on our Transparency Dashboard are derived entirely from public open-source data streams.

---

## 2. Public Data Sources

All analytics presented on the Transparency Platform originate from three public, auditable repositories:

### A. Public GitHub Releases Metrics
- Total download counts are aggregated across production releases using public release asset metadata.
- Metrics track download volume per package variant (e.g. x64 vs arm64, Magisk vs KernelSU vs NoRoot).
- Individual downloader identities, user accounts, and network addresses are inaccessible and unrecorded.

### B. Open-Source Compatibility Submissions
- Application compatibility records are contributed publicly via Git pull requests in the `compatibility/data/` directory.
- Metrics summarize total applications tested, compatibility status distributions (Working, Workaround Required, Broken), and Play Integrity enforcement rates.

### C. Build Variant Synthesis Matrices
- Distribution percentages for root solutions (Magisk, KernelSU, Vanilla) and architectures (x64, arm64) reflect build synthesis recipes maintained in the open-source repository.

---

## 3. Data Model and Schema Specification

All aggregated metrics conform to the formal JSON Schema defined at `services/analytics/schema.json`.

Key schema sections include:
- `transparency_principles`: Enforces boolean constraints (`zero_pii: true`, `no_ip_logging: true`, `no_cookies: true`, `public_aggregates_only: true`).
- `release_metrics`: Summarizes aggregate downloads, total releases, and active package flavors.
- `compatibility_metrics`: Summarizes community-verified application testing results.
- `root_flavor_distribution`: Percentage distribution of root management frameworks.
- `architecture_distribution`: Processor architecture download proportions (x64 vs arm64).
- `version_adoption`: Distribution of community adoption across WSA build baselines.

---

## 4. Pipeline and Governance Verification

The analytics lifecycle is governed by automated verification tools:

1. **Aggregation Engine (`services/analytics/aggregate.py`)**:
   - Parses community compatibility records and release metadata.
   - Computes percentage distributions.
   - Recursively asserts that zero forbidden PII keys exist before writing `services/analytics/metrics.json`.
2. **Validation Engine (`scripts/validate_analytics.py`)**:
   - Validates JSON Schema conformance.
   - Verifies arithmetic sum integrity (e.g. percentage fields summing to 100%).
   - Confirms that recorded compatibility counts match physical files on disk.
3. **Import Layer (`website/scripts/import-analytics.mjs`)**:
   - Synchronizes validated metrics into the website content directory during the site build pipeline (`prebuild`).
   - Ensures zero metric drift between repository storage and public presentation.

---

## 5. Community Auditability

Any community member can verify our zero-PII commitment by inspecting:
- The aggregation script: `services/analytics/aggregate.py`
- The validation engine: `scripts/validate_analytics.py`
- The raw public metrics file: `services/analytics/metrics.json`
- The transparency dashboard implementation: `website/src/pages/analytics.astro`
