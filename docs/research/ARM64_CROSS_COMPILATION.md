# ARM64 Cross-Compilation Investigation (Task 4.2)

**Status:** Research-only · **Classification:** Task 4.2 — completed as research (no build-system changes) · **Date:** 2026-09-16
**Programme:** Project Emberbird Metamorphosis Programme v3, Phase E0
**Preserved work:** uncommitted diffs across the build toolchain — `build.sh`, `build_local.py`, `config.sh`, `generateGappsLink.py` (94 insertions) — are the starting point; nothing in this document modifies the build system.

---

## 1. Scope and constraint

Task 4.2 asks: what would it take for the pipeline to build for **ARM64**?
Per the Execution Contract and the G1 freeze (once E2 starts), this document is
**research-only**: no build flag, script, workflow, or release behavior changes
as a result of writing it. The preserved diffs remain preserved and uncommitted,
exactly as the owner's protection rule requires.

## 2. Current state (reality)

- The pipeline builds **x64** targets on the locked retail channel.
- The **preserved diffs** (uncommitted) already sketch the ARM64 shape:
  `--arch x64|arm64` on `build.sh` / `build_local.py` (Magisk ABI mapping
  `arm64-v8a` vs `x86_64`, GApps machine names `arm64` vs `x86_64`), a
  `TARGET_ARCH_NATIVE` derivation in `config.sh`, and a fourth argument
  (native arch) passed to `generateGappsLink.py`.
- Upstream WSA does not publish ARM64 builds — "WSA on ARM" is the operating
  system shipping an x64 emulation layer on ARM hosts. A WSA **ARM64 MSIX** was
  never published by Microsoft; there is no official ARM64 WSA msixbundle to
  package or patch.

## 3. WSA ARM64 feasibility (the hard wall)

- WSA's Android framework (Android 13, API 33) in the wild is x64-only. A
  credible ARM64 distribution would need either Microsoft to publish an ARM64
  WSA msix (never happened) or an ARM64 Android system image substituted into
  the WSA shell — a fundamental re-engineering with unknown Windows-host
  compatibility, outside this project's charter and risk tolerance.
- **Conclusion:** WSA ARM64 is a **dead end for packaging** — the artifact that
  would carry the build does not exist. Any effort here competes with reality:
  Published Artifacts Are Truth (L1) has no ARM64 WSA asset to be truth about.

## 4. Cross-compilation targets that ARE viable (research findings)

The pipeline's actual cross-compilation build surface is **Magisk + GApps**, not WSA:

| Component | ARM64 feasibility | Mechanism | Risk |
|---|---|---|---|
| Magisk ARM64 | **Viable** | Magisk publishes `lib/arm64-v8a/*.so` inside the same APK; the preserved diffs already extract the correct ABI directory (`magisk_abi = "arm64-v8a" if arch == "arm64"`). | Low |
| GApps (OpenGApps) ARM64 | **Viable in principle** | OpenGApps publishes `arm64` Android 13 images; the preserved diffs already route `arm64` machine-name images (`TARGET_ARCH_NATIVE`). | Medium — availability of exact API 33 arm64 pico builds varies |
| WSA msix ARM64 | **Not viable** | No upstream ARM64 msix exists to package (L1: no such published artifact). | — |

- **Deployment reality:** ARM64 Windows hosts run the x64 WSA through
  Windows on ARM x64 emulation. An Emberbird distribution for ARM64 hosts would
  ship the **x64 WSA package** with explicit user guidance — not an ARM64
  artifact.
- **Research conclusion:** keep the preserved diffs preserved; when P8 unlocks
  after the x64 pipeline is fully registry-driven, the correct decision to make
  is **distribution packaging for ARM64 hosts (ship x64 + guidance)** rather
  than ARM64 artifact production.

## 5. CI implications (research-only)

- If P8 ever activates: matrix builds would need `x64` and an explicitly
  experimental `arm64` leg; the drift workflow and registry schema already
  carry `architecture` as a first-class field, so the registry is ready; CI
  validation of an ARM64 leg would be new workflow work under G1 discipline.
- Registry readiness confirmed: `releases.schema.json` already models
  `architecture` as a first-class release field — the metadata layer needs no
  change for a future ARM64 decision; only build and distribution layers would.

## 6. Decision record (for the Programme Control Board, G4)

| # | Decision | Status |
|---|---|---|
| D1 | WSA ARM64 artifact production | **Rejected** — no upstream artifact exists (L1 reality) |
| D2 | Magisk/GApps ARM64 enablement | **Deferred** to P8, preserved diffs are the starting point |
| D3 | ARM64 host distribution strategy | **Deferred** to P8: ship x64 WSA + guidance for ARM64 hosts |

**Maintainer guidance:** the preserved diffs should ride along through the
metamorphosis untouched (per the ARM64 Protection Rule) and remain the P8
starting point. This document is their only sanctioned activator until P8.

---

*Task 4.2 is complete as research. Zero build-system changes were made.*
