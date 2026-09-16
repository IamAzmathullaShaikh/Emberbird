# Repository Path Map (v2)

**Programme:** Project Emberbird — Metamorphosis Programme v3
**Status key:** `ACTIVE` (live layout, executed by E2) · `MAPPED` (existing mirror mapping, unchanged)

This document is the **authoritative** old→new mapping for the metamorphosis.
The E2 restructure executes it as a single surgical `git mv` commit; history
is preserved because moves are renames, not delete/create. After E2, this file
doubles as the **legacy redirect map**: old paths remain traceable forever
(S1/G3).

---

## 1. Root taxonomy (E2 — EXECUTED)

| Legacy path | New path | Contents | Status |
|---|---|---|---|
| `Documentation/**` | `docs/archive/**` | 49 upstream-era user docs (historical record) | ACTIVE |
| `WSABuilds Utilities/` | `utilities/` | 4 utility scripts (space-separated name, tracked) | ACTIVE |
| `MagiskOnWSA/scripts/` toolchain | `tools/` | build.sh, build_local.py, config.sh, update-check/, core/ + helpers | ACTIVE |
| `MagiskOnWSA/` (remainder, unmodified-from-upstream) | `upstream/` | vendored upstream files with provenance | ACTIVE |
| `releases/` (stray tracked file) | — | verified absent from HEAD when E2 executed; map row was speculative | VERIFIED ABSENT |

Untracked local residue (`MagiskOnWSAOld/`, `dist_clean/`, `dist_winget_submission/`, root report JSONs) is **not** part of the map — it never enters git (`.gitignore` since E2).

## 2. Paths that do NOT move (stability anchors)

| Path | Reason |
|---|---|
| `data/releases/**` | the Ember Registry — consumers and CI depend on its location |
| `data/contracts/**` | frozen contracts |
| `platform/release-engine/**` | engine package + CI compile target |
| `tests/**` | CI discovery path (`unittest discover -s tests`) |
| `scripts/**` | operational scripts (identity_map, build_registry, validators) |
| `.github/**` | workflows (CI truth) |
| `website/**`, `apps/**` | consumer surfaces (E3B/E3C migrate their *content*, not their location) |
| `docs/**` | living documentation (absorbs `Documentation/` as `docs/archive/`) |

## 3. Docs mirror mapping (ACTIVE — pre-existing, unchanged by E2)

`tests/test_docs_mirror.py::PATH_MAP` pins `docs/**` ↔ `website/src/content/docs/**`:

| docs/ | website mirror |
|---|---|
| `ARCHITECTURE.md` | `getting-started/ARCHITECTURE.md` |
| `UPGRADE_VALIDATION.md` | `getting-started/UPGRADE_VALIDATION.md` |
| `WINDOWS_VALIDATION_LAB.md` | `getting-started/WINDOWS_VALIDATION_LAB.md` |
| `*(everything else)*` | same relative path |

## 4. Redirect policy

- Moves are executed with `git mv` — file history follows the file.
- After E2 (executed), any functional reference to a legacy path is a defect:
  the E1.5 contract tests, CI compile targets and the doc-link validator
  enforce the new taxonomy. Attribution and historical docs intentionally keep
  the legacy names (S1).
- This file is the single source for what moved where; `git log --follow` is
  the single source for how a file got there.
