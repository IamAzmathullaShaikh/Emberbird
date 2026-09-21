# The Emberbird Charter

> **Emberbird** — a registry-first lifecycle platform for Android on Windows.
> Continuation, not replacement: the Windows Subsystem for Android is no
> longer developed by Microsoft; Emberbird keeps patched builds alive,
> verifiable, and honestly documented.

---

## 0. The Bold Rule (read first)

**Published Artifacts Are Truth.**

Before any other consideration, any claim this project makes — a download
link, a hash, a compatibility note, a "works on your device" promise — must
be backed by published, hash-verified artifacts. If documentation, intuition,
and published reality disagree, published reality wins and the docs are
corrected. No exceptions for convenience. The release registry exists to
make this rule mechanical rather than aspirational.

## 1. Why Emberbird exists

Microsoft ended support for the Windows Subsystem for Android (WSA) in
March 2025. The upstream community build project (WSABuilds) carries that
torch today, but its intelligence — which release is current, what is safe
to install, which device works — lives scattered across GitHub releases,
wiki pages, and issue threads. Emberbird's founding premise:

1. **One registry.** Every consumer (website, manager, compatibility hub,
   analytics, package managers) derives release intelligence from a single,
   validated, versioned registry: `data/releases/releases.json`.
2. **Continuation.** Upstream WSA is dead; the builds are not. Emberbird
   sustains patched builds, tracks regressions, and researches forward
   paths (ARM64, newer Android) instead of declaring the platform finished.
3. **Evolution over replacement.** Existing working pipelines (Builder V1,
   release CI, website) are wrapped and extended, never ripped out before
   parity is proven (see the Builder Independence Rule in
   `data/contracts/release-contract.md`).
4. **Single-maintainer durability.** Every piece of intelligence must be
   regenerable from published bytes by documented tooling. No tribal
   knowledge, no manual metadata patching, no bus-factor of one person's
   memory.

## 2. What Emberbird is not

- **Not a rebrand of Microsoft's product.** The shipped subsystem remains
  "Windows Subsystem for Android (modified)". Emberbird is the platform
  around it: registry, tooling, manager, docs, policy. Microsoft's binaries
  stay attributed to Microsoft; see `docs/ATTRIBUTION.md` and the license
  audit.
- **Not a fork war.** Upstream WSABuilds is treated as a respected ancestor;
  provenance of inherited assets is recorded, and divergence is documented
  rather than hidden.
- **Not an app store.** Emberbird distributes subsystem builds and a
  manager; it does not broker third-party Android applications.

## 3. Product pillars (from upstream pain)

| Pillar | Upstream problem addressed | Emberbird mechanism |
|---|---|---|
| Verifiability | Hashes and links drift; users install stale or mirrored builds | Registry + vault keyed on `(artifact, sha256)`; schema rejects placeholder hashes |
| Continuity | Project momentum dies with maintainer availability | Everything regenerable from published bytes; documented tooling; contracts frozen and tested |
| Compatibility truth | Canary-channel breakages surprise users after install | Compatibility Hub data feeds the registry; install-time checks validated against it |
| Honest editions | Users conflate rooted (Magisk) and clean (banking) builds | Editions are separate registry entries with distinct security properties |
| Reach | ARM64 / Copilot+ devices unsupported | ARM64 tracked as a first-class roadmap pillar (research-first, no false promises) |

## 4. Governance pillars

1. **Contracts over conventions.** Rules that matter are written as
   contracts (`data/contracts/`, `data/releases/GOVERNANCE.md`) and
   enforced by tests, not memory.
2. **Phases, never sprawl.** Work proceeds through the roadmap in
   `TODO.md`; only the active phase receives implementation. The phase
   guard is absolute: Phase N+1 cannot start until Phase N's exit
   checklist is fully checked.
3. **Reality gates.** Every claim is tested against reality: build gates
   (does it compile?), CI gates (does CI ratify?), runtime gates (does it
   actually run?), and registry gates (is the metadata true?).
4. **No fabricated data.** No hash computed from anything other than
   published bytes. No fixture posing as a release. Test fixtures are
   labeled and quarantined from the registry.

## 5. Principles of conduct

1. **Ship truth or ship nothing.** A half-true status is worse than an
   honest BLOCKED. Every status report states which gate failed.
2. **The user installs with their own hands.** Convenience features must
   never silently escalate privileges, weaken verification, or paper over
   a failed hash check. Any failure at install time is loud, explained,
   and linked to evidence.
3. **Deprecate loudly, delete never.** Old builds remain queryable with
   explicit supersession chains; removal from the registry is a governance
   action with a recorded reason, never a silent rewrite.
4. **Boring over clever.** The tooling is stdlib-first (jsonschema the only
   soft dependency), documented, and testable by a single maintainer on a
   laptop with no secrets installed.
5. **Upstream is family.** Patches and learnings flow back where they can;
   divergence is documented at the point of divergence.

## 6. Licensing position

- Emberbird's own code and contracts: licensed under the repository's
  existing license (see `LICENSE`; details and any gaps in
  `docs/LICENSE_AUDIT.md`).
- Microsoft's WSA binaries: redistributed under the terms that govern
  their public availability, always attributed, never modified beyond the
  documented patch set. Emberbird claims no ownership of them.
- Community tooling (Magisk, MindTheGapps, and friends): attributed with
  provenance in `docs/ATTRIBUTION.md` and version-pinned in registry
  provenance records.

## 7. How success is measured

Phase 0 succeeds when the P0 exit checklist in `TODO.md` is fully checked:
registry schema frozen and tested, registry generated from real published
releases, metadata service validating it, a registry-only consumer proven,
contracts frozen, charter and attribution published — with the GREEN CI
baseline preserved and zero protected-subsystem regressions.
