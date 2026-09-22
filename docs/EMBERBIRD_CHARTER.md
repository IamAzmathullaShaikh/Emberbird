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

## 7. What Emberbird does not guarantee (non-guarantees)

These are deliberate, permanent boundaries — not pending features. A claim
inside them is a bug in the claim, not a gap in the product.

1. **No "it will work on your PC" guarantee.** WSA depends on Windows
   builds, virtualization stacks and OEM drivers Microsoft controls. The
   Manager reports what it can *measure* (virtualization state, Windows
   build, disk space, developer mode) and never promises an outcome.
2. **No guarantee of running apps' correctness.** Emberbird ships the
   Android runtime, not app compatibility; Play Integrity and app-level
   attestations are outside any edition's promise (see the honest-editions
   pillar, §3).
3. **No uninterrupted-update guarantee.** Updates are verified against
   registry hashes before anything is touched, and a failure is loud — but
   Microsoft endpoints, GitHub availability and upstream WSA deprecation
   are not ours to promise.
4. **No silent self-modification.** Emberbird never changes system
   settings (developer mode, virtualization, Defender exclusions) without
   an explicit, explained user action. Remediations always name the change
   before asking.
5. **No data retention promise beyond the machine.** Backups, snapshots
   and lifecycle records live on the user's disk; there is no cloud copy,
   and none is promised (see the privacy policy, §8).
6. **No support surface for modified upstream binaries.** A WSA package
   whose hash does not match registry truth is refused, not "supported
   with caveats".
7. **No availability guarantee for Microsoft's endpoints.** If Microsoft
   withdraws WSA distribution (as the March 2025 WSA/Amazon Appstore store
   withdrawal showed), published artifacts remain queryable and verifiable
   from the registry, but future upstream fixes are outside our control.

## 8. Policies

### 8.1 Supported configurations (declared truth)

The authoritative numbers are the ones the code enforces; this table restates
them and a test keeps the restatement honest.

| Dimension | Declared value | Enforced by |
|---|---|---|
| Windows build | ≥ 10.0.**19045** (22H2); preflight refuses older builds | `deployment/version.json` (`min_windows_build`), `coordinator.rs` preflight |
| Host CPU architecture | **x64** (ARM64 is a research pillar — `target_architectures` in `deployment/version.json`) | preflight + registry `architectures` |
| Virtualization | Virtual Machine Platform / Hyper-V **enabled** | `coordinator.rs` preflight, `detector.rs` |
| Windows Developer Mode | **Required** for subsystem registration | `detector.rs` (`developer_mode_enabled`) |
| Free disk space | **≥ 25 GB** on the system drive (`REQUIRED_DISK_SPACE_BYTES`) | `coordinator.rs` preflight |
| Subsystem baseline | WSA **2407.40000.4.0** (Android 13) | `deployment/version.json` (`subsystem_baseline`) |
| Manager architecture | x64 only (ARM64 builds do not exist — no false ARM64 promise) | `winget-release.yml`, registry |

Anything outside this table may work; it is simply not promised, not tested,
and not claimed.

### 8.2 Telemetry and privacy policy

- **Emberbird collects nothing.** There is no telemetry pipeline in the
  Manager, the CLI, or the website: no analytics SDK, no crash uploader, no
  usage ping, no unique identifier. This is verifiable in the code and is a
  promise, not an oversight — any future telemetry requires amending this
  section first (PH-28/PH-33 gate it) and shipping an opt-in switch.
- **What leaves the machine:** only what a documented feature must fetch —
  registry files and release artifacts from published endpoints (GitHub),
  and diagnostic *commands the user explicitly runs* (emberbird doctor)
  whose output stays on stdout/the local report. Nothing else is sent,
  anywhere, by anything.
- **What stays on the machine:** backups, lifecycle snapshots
  (`%LOCALAPPDATA%\Emberbird\lifecycle.json`), staged archives, and doctor
  reports. Users can delete all of it; Emberbird re-derives what it needs.
- **Crash reporting:** none today. When PH-33 lands it will be opt-in,
  documented here, and disabled by default.

### 8.3 Security model

1. **Artifact integrity is the root of trust.** Artifact identity is
   `(filename, sha256)`; a hash mismatch deletes the content and refuses to
   stage — there is no override flag. The registry schema *requires* the
   hash and the architecture on every asset, so an unverified row cannot
   even be expressed.
2. **Archive extraction is guarded.** Entries that are absolute, UNC,
   drive-qualified or contain a `..` segment are refused *before* anything
   is written; an archive whose entries cannot be enumerated is refused
   rather than trusted to the extractor.
3. **The user mediates every privileged action.** Elevation is requested
   per action with an explanation; the CLI refuses remediations without an
   elevated shell rather than self-elevating.
4. **Secrets stay out.** CI tokens are stored as GitHub secrets; the code
   base is scanned by Gitleaks on every push; no secret is read from the
   registry or the deployment manifest.
5. **Failure is the safe direction.** When evidence is missing — detection
   cannot read a version, a snapshot is corrupt, a schema is from the
   future — every surface reports failure or `UNKNOWN`, never a guess.

### 8.4 Release governance

- **The registry is the only release fact.** Release identity, artifact
  hashes, editions, channels and provenance live in
  `data/releases/releases.json` under the frozen schema; consumers are
  registry-only by contract (enforced by `tests/test_registry_consumer.py`).
- **Publication is gated.** A release enters the registry only through
  `scripts/publish_release.py`, which validates against the schema, records
  provenance (commit, tool, generation mode) and appends to an immutable
  history; removal is a governance action with a recorded reason.
- **CI ratifies.** A claim of "shipped" requires a green run of the
  corresponding workflow on the release ref; local green is necessary but
  never sufficient.
- **Deprecate loudly, delete never.** Superseded releases stay queryable
  with explicit supersession chains.

### 8.5 Backwards-compatibility policy

- **Data contracts:** `releases.schema.json` and the lifecycle snapshot
  schema are versioned. Readers refuse *future* versions loudly (the
  lifecycle reader and the Rust engine both do) and read past versions
  honestly; schema evolution is additive until a recorded breaking change.
- **Registry rows:** published release rows are immutable; supersession,
  not rewrite. A renumber or rename is legitimate only when a crosswalk
  keeps old identifiers resolvable (the `FB-*`/`FX-*`/`QG-*`/`DX-*`/`UX-*`
  crosswalk in `TODO.md` is the precedent, enforced by a test).
- **Machine-readable output:** the CLI's `--json` payloads are additive —
  existing keys keep their names and meaning; new facts get new keys.
- **File locations:** `%LOCALAPPDATA%\Emberbird\` is the application's
  data home; moving a file there is a breaking change requiring a
  migration note in this charter.

## 9. How success is measured

Phase 0 succeeds when the P0 exit checklist in `TODO.md` is fully checked:
registry schema frozen and tested, registry generated from real published
releases, metadata service validating it, a registry-only consumer proven,
contracts frozen, charter and attribution published — with the GREEN CI
baseline preserved and zero protected-subsystem regressions.
