# Consumer Purity Matrix (S4)

**Programme:** Project Emberbird — Metamorphosis Programme v3
**Purpose:** the running audit of release-facing consumers. The E7 Registry
Purity Audit reads this matrix; `tests/test_consumer_compliance.py` keeps it
honest against the code on every commit.

**Columns:** does the consumer resolve release truth from the Registry? Does it
enforce contracts? Does it perform **direct GitHub release discovery** (the
forbidden pattern)? What is its migration status?

| Consumer | Registry | Contracts | GitHub Discovery | Status |
|---|---|---|---|---|
| Release Engine (CLI) | ✅ `data/releases/releases.json` only | ✅ `validate --schema`, integrity guards | ❌ none (core is offline-pure) | **Migrated** |
| Registry generator | ✅ writes the registry from reality | ✅ schema-evolution rules | ✅ by design (reality-sync is its job) | **Source of truth** |
| Website — downloads portal | ✅ `RegistryReleaseProvider` (build-time registry import, offline) | ✅ registry schema-validated by CI Reality Gate before every build | ❌ none since E3B.4 (legacy provider kept ONLY as the test-tree parity oracle) | **Migrated** (E3B) |
| Website — compatibility hub | ❌ static compatibility data | partial | ❌ none | **E3B pending** (data-only; no discovery path) |
| Website — docs mirror | n/a (content, not release truth) | ✅ mirror guard | ❌ none | **Migrated** (S1) |
| Manager | ✅ `src/lib/registry.ts` (bundled registry import, offline) | ✅ registry-mapped `ReleaseInfo`; flavors follow the documented WSA naming convention | ⚠️ URL-derivation is repo-config plumbing only (`env.ts`, `ipc.ts`, `types.ts`) — derives no release truth; dead `get_latest_releases` stub removed at E3C.4 | **Migrated** (E3C; Rust side inert — no discovery code exists) |
| Winget workflow | ✅ manifest paths produced from the pipeline | ✅ identity checks | ❌ no release-catalog API | **Migrated** |
| CI (build.yml) | ✅ registry reality gate | ✅ contract suite | ❌ none | **Migrated** (S2) |

**Rules pinned by `tests/test_consumer_compliance.py`:**

1. The engine **core** module must remain offline-pure (zero network tokens);
   only the CLI `__main__` may import a network fetcher, for `verify`.
2. Website production code performs **zero** GitHub release discovery
   (E3B.4): releases resolve exclusively from the Ember Registry. The legacy
   discovery provider survives only as `website/tests/lib/
   github-release-oracle.ts` — the S2 parity oracle — and must never be
   imported by `website/src`.
3. Manager release truth resolves from the bundled registry
   (`src/lib/registry.ts`, E3C): the derivation modules are repo-config
   plumbing that derives no release truth, and no Manager module may gain a
   release-discovery path.
4. No consumer may gain a *new* GitHub-discovery path: the inventoried set is
   closed.

> Matrix updates are part of the phase that changes a consumer's status —
> never after.
