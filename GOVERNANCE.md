# WSABuilds Master Governance — Release & Security Policy

**Framework:** WSABuilds Master Governance Framework v5.1 · **Status:** ACTIVE · **Applies to:** every release, workflow, and credential in this repository.

**Core doctrine:** every claim must match reality. No artifact is advertised that does not exist, no hash is published that was not computed from the published bytes, and no workflow step may substitute a placeholder for a real build product.

---

## 1. Release Principles

1. **Reality over claims.** CI is the only source of truth. A locally-passing build proves nothing until the pinned CI pipeline reproduces it.
2. **No placeholders ever.** Stub binaries, `000…0` hashes, and "temporary" placeholder releases are forbidden. Format validation ≠ value validation.
3. **Gates over goodwill.** Automated reality gates (below) decide; humans verify outcomes, they do not bypass gates.
4. **One version, everywhere.** `deployment/version.json` is authoritative. All other version declarations derive from it.
5. **Privacy is structural.** Analytics must remain zero-PII by schema and by code enforcement, not by convention.
6. **Least privilege always.** Tokens, workflow permissions, and third-party actions get the minimum scope that works.

## 2. Pre-Tag Checklist (run before every `git tag vX.Y.Z`)

- [ ] `deployment/version.json` `manager.version` = new version
- [ ] `apps/manager/package.json`, `src-tauri/Cargo.toml`, `src-tauri/tauri.conf.json`, `src-tauri/Cargo.lock` all bumped to the same version
- [ ] `manifests/w/WSABuilds/WSABuildsManager/<new-version>/` exists with all three manifests; installer manifest references the new release URL; SHA256 carries the **documented bootstrap placeholder** (previous hash) if the real hash does not exist yet — never zeros
- [ ] `python3 scripts/validate_distribution.py` → SUCCESS
- [ ] `python3 -m unittest discover -s tests` → OK
- [ ] `winget validate manifests/w/WSABuilds/WSABuildsManager/<new-version>` (local winget CLI) → succeeded
- [ ] Target tag does not exist locally or on remote (`git tag -l`, `git ls-remote --tags`)
- [ ] Working tree clean; all hardening commits pushed to `main`
- [ ] **WSA cuts only:** `deployment/version.json` `subsystem_baseline.wsa_version` + `subsystem_baseline.release_tag` updated together; tag named `wsa-v<shipped-version>` per §3.1

## 3. Release Checklist (the automated pipeline — verify, never hand-execute)

Tag push (`v*`) triggers `winget-release.yml`:
1. `validate-metadata` — distribution + winget manifest validation
2. `package-manager` — tag↔version gate → `npm ci` → `tsc --noEmit` → `npx tauri build --bundles nsis` → MZ-header + size Reality Gate → SHA256 checksums + sidecars
3. `publish-manager-release` — independent re-hash of every asset against the checksums manifest → `softprops/action-gh-release` publishes assets (`overwrite_files: true`)
4. `prepare-winget` — archives manifests for the release version

**Post-release (automated where possible, otherwise manual):**
- [ ] All four jobs green on the tag run
- [ ] Assets present: Setup EXE, Portable ZIP, checksums.txt, 2 × `.sha256` sidecars — and **nothing else** (publish glob is `WSABuildsManager-*`; staging binaries must never leak)
- [ ] Public download of Setup EXE re-hashes to the manifest value
- [ ] Installer manifest hash patched from bootstrap placeholder to the real published hash (commit to `main`; see §9 rule 6)
- [ ] `winget validate` re-run on the finalized manifest

### 3.1 WSA Release Tag Convention & Notes Template

**Tag naming:** WSA releases are tagged `wsa-v<shipped-version>` where `<shipped-version>` is the version **inside the produced archives** (the `WSA_*` MSIX package version), not an external counter. The tag and the asset filenames must agree — a tag quoting a different version than the assets ship is a documentation defect (this exact mismatch, `wsa-v2311.40000.5.0` shipping `2407.40000.4.0` assets, is why the convention exists). `deployment/version.json` → `subsystem_baseline.release_tag` is the authoritative pointer consumed by the website downloads page.

**Release notes template (enrich, never ship bare changelogs):**

```markdown
## WSABuilds <shipped-version> — <Standard/Banking> Edition

### Downloads
| Edition | Root | GApps | Asset | Size |
|---|---|---|---|---|
| Standard | Magisk Stable | OpenGApps Pico | `WSA_<ver>_x64.7z` | <size> |
| Banking (Enterprise) | None (vanilla ramdisk) | OpenGApps Pico | `WSA_<ver>_x64_vanilla.7z` | <size> |

### Verify before install (PowerShell)
`Get-FileHash -Algorithm SHA256 .\WSA_<ver>_x64.7z` — must match `checksums.txt` in this release.

### Install
Extract the `.7z`, then run `Install.ps1` as administrator. Full guide: https://wsabuilds-website.pages.dev/docs/getting-started/quick-start

### Reports shipped with this release
package-identity-report.json · package-integrity-report.json · magisk-validation-report.json · gapps-validation-report.json · release-metadata.json
```

**Editions table rule:** both Tier 1 editions build with Pico GApps (`release.yml` matrix). Standard = Magisk-rooted ramdisk; Banking = vanilla (unrooted) ramdisk. The website downloads page classifies on this basis — asset names without a root token are Standard (rooted), `_vanilla` assets are Banking.

## 4. Hash Verification Checklist

- [ ] `sha256sum <downloaded asset>` matches the `.sha256` sidecar byte-for-byte
- [ ] Both hashes appear in `WSABuildsManager-<version>-checksums.txt`
- [ ] `manifests/.../installer.yaml` `InstallerSha256` equals the Setup EXE hash
- [ ] Verification performed on a **fresh public download**, not the local staging copy
- [ ] Any mismatch → treat as security incident (§6), remove the asset, re-cut the release

## 5. Winget Checklist

- [ ] Three manifests present: version / installer / defaultLocale, schema 1.6.0
- [ ] `PackageVersion` consistent across all three; directory name matches
- [ ] `InstallerUrl` resolves (HTTP 200/206) against the published release
- [ ] `InstallerSha256` is a real hash of a published asset — placeholders forbidden outside the bootstrap window (tag → publish + hash patch, ideally < 24h)
- [ ] `winget validate` passes on the manifest directory
- [ ] No architectures advertised that lack a real installer

## 6. Incident Response Checklist (security)

1. **Revoke** the exposed credential immediately (GitHub → Settings → Developer settings → PATs). Do not investigate first; revoke first.
2. **Verify revocation:** `curl -H "Authorization: Bearer <token>" https://api.github.com/user` must return **401**.
3. **Audit for misuse:** Security log (last 7 days) for `repo.*`, `workflow.*`, `org.*` events; check deploy keys, webhooks, collaborators, OAuth app grants, new PATs.
4. **Check persistence vectors:** unknown deploy keys, webhooks, collaborators, or installed GitHub Apps → remove immediately.
5. **Scope review:** if the token was classic/full-scope, audit org and enterprise surfaces (members, hooks, apps) — admin scopes were granted.
6. **Replace only if needed:** CI uses the built-in `GITHUB_TOKEN`; no PAT is required for releases. Manual API work → fine-grained PAT, single repo, Contents: R/W, ≤ 90-day expiry, password manager.
7. **Post-incident:** record the incident in a private security log; never paste credentials into chat, tickets, or agent contexts.

## 7. Supply Chain Policy

- Every third-party action is pinned to a **full 40-character commit SHA** — never `@v4`-style tags. Rationale: tags are mutable; SHAs are not.
- Pin comments may note the resolved tag (`# v4.6.2`) for human readability.
- Quarterly cadence: re-resolve each pinned action's latest release, review its changelog, bump the SHA deliberately.
- `Cargo.lock` and `package-lock.json` are committed; `npm ci` is mandatory in CI (`npm install` forbidden).
- Rust toolchain is pinned (`dtolnay/rust-toolchain` + explicit `toolchain: '1.98.1'`); bump deliberately, not silently.
- New dependencies require: license check, maintenance signal, and no known critical advisories (`npm audit --audit-level=critical` in CI for the website).
- Runtime secrets come from GitHub secrets only — never committed, never pasted into agent/chat contexts, never echoed in logs.

## 8. Release Gates Registry

| Gate | Location | Enforces | Failure mode |
|---|---|---|---|
| Distribution Validator | `validate-metadata` job | version sync across 4 files + manifests | hard fail before build |
| Tag↔Version Gate | `package-manager` job | tag name equals declared version | hard fail at build start |
| TypeScript Gate | `package-manager` job | `tsc --noEmit` clean | hard fail before bundling |
| Build Reality Gate | `package-manager` job | MZ/PE header + ≥1 MB installer size | hard fail; stubs impossible |
| Publish Reality Gate | `publish-manager-release` job | independent re-hash of all assets vs checksums manifest | hard fail before publication |
| Publish Glob | `publish-manager-release` job | only `WSABuildsManager-*` assets may publish | staging binaries filtered out |
| Analytics Privacy Gate | `tests/test_analytics.py` | zero-PII enforcement + schema const | CI failure on regression |
| Compatibility Schema Gate | `compatibility-validation.yml` + website tests | record schema validity | CI failure on bad records |

## 9. Security Rules

1. Never commit credentials; the exposed-PAT incident (2026-09) is the standing example.
2. Classic PATs with full scope are forbidden going forward; fine-grained, scoped, expiring tokens only.
3. Workflow permissions are minimal per job (`contents: read` unless the job writes).
4. Third-party actions pinned to SHAs (§7).
5. `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` must exist as repository secrets before any deploy step can run; the deploy step fails by design when they are absent.
6. Winget bootstrap window: a manifest may carry a **documented** placeholder hash only between tag push and publish+patch; it must never reach a public submission.
7. Any artifact whose hash chain fails verification is removed and re-cut — never "fixed in place".

## 10. Token Handling Rules

- **Storage:** password manager or OS keychain. Never in chat/agent contexts, never in shell history (`HISTFILE` hygiene), never in code, never in issue text.
- **Least privilege:** fine-grained PAT, single repository, Contents: R/W, ≤ 90-day expiry. No org/enterprise/admin scopes for routine work.
- **Rotation:** immediate on suspicion; scheduled every 90 days for any standing manual-use token.
- **Revocation drill:** after any exposure, run §6 steps 1–4 and record the verification output (401) as evidence.
- **No PAT in CI:** release automation uses the built-in `GITHUB_TOKEN` with job-scoped permissions.

---

## Appendix A: Runtime Compatibility Validation Procedure (Phase 7 executable)

**Prerequisite:** Windows 11 host with WSA installed (`Get-AppxPackage *WindowsSubsystemForAndroid*`), adb on PATH.

1. `explorer.exe "wsa://com.android.settings"` — boots the WSA VM
2. `adb connect 127.0.0.1:58526` — first connection triggers an **interactive RSA prompt inside the WSA window**; a human must click **Allow**. Automation cannot pass this step by design.
3. Once `adb devices` shows `device`:
   - `adb shell getprop ro.build.version.release` → Android version
   - Root flavor: `adb shell "su -c id"` (Magisk/KernelSU) → `uid=0` proves root; absence = No Root
   - GApps: `adb shell pm list packages com.google.android.gms` → presence/absence
4. Per app: install the target APK from an approved source, launch, record launch + login + core-function status in `compatibility/data/<App>.json` per `compatibility/schema.json`; set `verification_status: verified` only after maintainer reproduction.
5. Commit records; CI validates schema; website auto-syncs.

**Known limitation:** without the interactive RSA approval, runtime app statuses cannot be produced by automation. Records must never claim statuses without this evidence.

## Appendix B: Code Signing Adoption Plan (Phase 6)

**Recommended path: Azure Trusted Signing (Microsoft) — 90-day milestone.**

| Criterion | Azure Trusted Signing | SignPath Foundation |
|---|---|---|
| Cost | Free tier; then usage-based (modest) | Free for OSS (foundation approval required) |
| Effort | Lowest — native Azure + GitHub Action (`azure/trusted-signing-action`), Authenticode signing as a service | Moderate — org onboarding + signing policy config |
| Hurdle | Identity validation for individual accounts can take days–weeks; regional availability check required | OSS review/approval lead time |
| Outcome | Signed installer + portable binary; SmartScreen reputation accrues over time | Same, plus cross-signing ecosystem |

**Decision:** pursue Trusted Signing first; fall back to SignPath Foundation if identity validation stalls. Intermediate mitigation until certificates live: publish SHA256 checksums + sidecars (already automated) and document verification steps in release notes.

**Implementation steps (when initiated):** ① validate regional availability + identity for the account owner; ② provision a Trusted Signing account + certificate profile; ③ add `azure/trusted-signing-action` (SHA-pinned) between the reality gate and artifact upload in `winget-release.yml`; ④ sign both `WSABuildsManager-Setup-*.exe` and the portable binary; ⑤ add a post-signing hash re-computation step so winget manifests always carry the hash of the **signed** bytes; ⑥ document the trust-chain change in release notes.

**Effort estimate:** ~0.5 day CI work + external approval latency (days–weeks).

**Expected user impact:** pre-signing, Windows SmartScreen shows "Unknown publisher" on first run and users must click "More info → Run anyway" — a measurable adoption friction. Post-signing, SmartScreen reputation accrues over downloads; installers eventually run with the publisher name displayed, and enterprise environments (SmartScreen/WDAC policies) can allowlist by publisher. Unsigned → signed is the single highest-trust-per-effort improvement available to distribution.

---

## Appendix C: v0.2.2 Hardening Status Snapshot (2026-09-14)

| Area | Status |
|---|---|
| PAT incident | **RESOLVED (2026-09-14)** — exposed classic PAT revoked by the owner; API calls with the token now return `Bad credentials` (401). Pre-revocation sweep found zero misuse: 0 deploy keys, 0 webhooks, owner-only collaborator, event actors = owner + Actions bot. |
| Website deploy | **WORKING — PRODUCTION LIVE** at https://wsabuilds-website.pages.dev (2026-09-14). Enablement record: Pages project `wsabuilds-website` created via API (action's 401 on missing project was misleading); `production_branch` aligned to `main`; token IP-filter (error 9109) had to be lifted in the Cloudflare dashboard — CI runners are not fixed-IP. Credentials pasted into chat must be rotated (§10). |
| Reproducibility | **PASS** — Cargo.lock + package-lock committed, `npm ci` enforced, Rust toolchain pinned 1.98.1 |
| Supply chain | **PASS** — all actions SHA-pinned across every workflow; zero `@v` tags |
| Analytics cycle | **PASS** — 7/7 tests (injection, schema const, aggregation recount, dashboard regeneration) |
| Compatibility cycle | **PARTIAL** — records schema-valid; runtime statuses for Google Play/Play Services/YONO/WhatsApp/Telegram/Spotify/Netflix REQUIRES TARGET ENVIRONMENT VERIFICATION (interactive adb RSA approval required) |
| Winget | **VALIDATED** — 0.2.2 manifest set passes `winget validate`; real published hash set post-release |

## Appendix D: Compatibility Runtime Roadmap (next validation cycle)

**Current coverage (schema-verified, runtime `unverified`):** Paytm, PhonePe, WhatsApp, YONO. **No records yet:** Google Play, Play Services, Telegram, Spotify, Netflix.

| Cycle step | Action | Prerequisite | Output |
|---|---|---|---|
| 1 | Human grants adb RSA approval (Appendix A steps 1–3) | Maintainer at the WSA host machine | `adb devices` shows `device` |
| 2 | Capture platform baseline: Android version, root flavor, GApps presence | Step 1 | Platform row in validation matrix |
| 3 | Exercise the 4 existing records in-app (launch, login, core function) | Step 2 | Status + evidence per record; set `verification_status: verified` only after reproduction |
| 4 | Author records for the 5 uncovered targets (start `community_submitted`) | Approved APK sources | `compatibility/data/<App>.json` — schema-validated by CI |
| 5 | Run `aggregate.py`, commit refreshed `metrics.json`, verify analytics tests | Step 3–4 | Portal + analytics reflect real coverage |
| 6 | Re-run website build (auto-triggered) and confirm portal pages render new records | Step 5 | Website sync evidence |

**Evidence requirements per app:** screenshot or screen recording of the core function running; APK source noted in the record; Play Integrity behavior observed (attestation passes/fails); any workaround steps reproduced verbatim before recording.
