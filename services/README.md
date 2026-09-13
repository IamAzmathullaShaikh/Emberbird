# WSABuilds Backend Services & Telemetry Platform

The `services/` directory contains background processing, data aggregation, and telemetry pipelines for the **WSABuilds** platform.

---

## 1. Services Architecture

```text
services/
└── analytics/
    ├── aggregate.py      # Deterministic metrics calculation engine
    ├── metrics.json      # Precomputed aggregated platform metrics
    └── schema.json       # JSON schema enforcing structure and Zero-PII boundaries
```

---

## 2. Privacy Charter & Zero-PII Guarantee

WSABuilds strictly adheres to a **Privacy-First, Zero-PII** standard:

- **No Personal Identifiers**: Zero collection of IP addresses, MAC addresses, machine GUIDs, usernames, or device hostnames.
- **No Client Tracking**: Zero tracking cookies, tracking pixels, or third-party telemetry beacons.
- **Public & Deterministic**: All metrics displayed on `/analytics` are calculated strictly from public GitHub release downloads, issue reports, and open compatibility submissions.

---

## 3. Data Schema & Forbidden Keys

`services/analytics/schema.json` strictly forbids the following keys anywhere in the telemetry payload:
- `ip`, `ip_address`, `client_ip`
- `email`, `user_id`, `username`
- `device_id`, `machine_guid`, `mac_address`, `hostname`
- `latitude`, `longitude`, `location`

---

## 4. Execution & Validation Commands

```powershell
# Run aggregation engine to recompute metrics
python services/analytics/aggregate.py

# Validate schema conformance and assert Zero-PII compliance
python scripts/validate_analytics.py

# Run analytics unit tests
python -m unittest tests/test_analytics.py -v
```
