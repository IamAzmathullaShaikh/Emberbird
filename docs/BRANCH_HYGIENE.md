# Branch Hygiene Report (Branch Policy compliance — evidence only)
**Generated:** 2026-09-17 · **Scope:** all 23 remote branches · **Policy:** mission Branch Policy — no branch is deleted by this report; every deletion verdict is an **owner decision** with evidence attached.
**Method:** ahead/behind vs `main` (unique-commit count), reference scan across living workflows + docs (archive excluded), tag-reachability check on unmerged tips (none of the 3 unmerged tips is reachable from any historical tag — deleting a branch orphans nothing that releases depend on).
**Key findings**
1. The repository's **default branch is `master`** (GitHub API). All metamorphosis work lands on `main`; CI triggers cover both. Moving the default branch to `main` is a governance decision reserved for the owner.
2. **20 of 23 branches are fully merged** into `main` (0 unique commits) — deleting them loses zero history.
3. **3 branches carry unique commits** (2 dependabot bumps from June/July, 1 legacy `Update App Version` from January). None is tag-reachable; none is referenced by any workflow.
4. The misnamed **local** branch `origin` (local-only artifact) points at a commit already contained in `main` — safe to delete locally; not repo truth.
| Branch | Last commit | Last activity | Referenced by | Verdict | Safe to delete |
|---|---|---|---|---|---|
| `WSA-next` | `a6cfa5e` | 2026-03-28 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `dependabot/github_actions/actions/setup-python-7` | `029d56f` | 2026-07-20 | none found (dependabot recreates as needed) | Unmerged — archive tip before any deletion (owner review) | NO |
| `dependabot/github_actions/stefanzweifel/git-auto-commit-action-7.2.0` | `fb6812e` | 2026-06-29 | none found (dependabot recreates as needed) | Unmerged — archive tip before any deletion (owner review) | NO |
| `experimental` | `b5b1707` | 2026-09-14 | workflow triggers: compatibility-validation.yml, docs-validation.yml, manager-build.yml | KEEP (referenced / infrastructure) | NO |
| `feature/documentation-and-onboarding-hardening` | `216ec51` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/production-stabilisation` | `b1f4c96` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/readme-ux-parity` | `3cfd114` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-1-foundation` | `df0ec2b` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-2-website` | `da24888` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-3-data-and-release` | `a34a730` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-4-compatibility` | `cd82bcb` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-5-wizard` | `d7336e6` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-6-manager` | `6806123` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-7-install-and-backup` | `7033297` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-8-winget-and-distribution` | `b5a6546` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/sprint-9-analytics-and-transparency` | `beed5e5` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `feature/tier-1-multi-config` | `4d58bbf` | 2026-09-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `fix/gapps-crashes-and-issues` | `8c41792` | 2026-08-14 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `gh-pages` | `075c684` | 2026-09-13 | none found (superseded by Cloudflare Pages deployment) | Unmerged — archive tip before any deletion (owner review) | NO |
| `main` | `70c8918` | 2026-09-17 | default-branch infrastructure (all CI; Cloudflare deploy; probe: repo default is `master` per API — main is the working integration branch) | KEEP (referenced / infrastructure) | NO |
| `master` | `5ce9c73` | 2026-09-15 | workflow triggers: build.yml, compatibility-validation.yml, docs-validation.yml, manager-build.yml, runtime-compatibility.yml, security.yml (repo default branch per GitHub API) | KEEP (referenced / infrastructure) | NO |
| `refactor/modernize-and-audit` | `075c684` | 2026-09-13 | none found | Safe to delete — merged into main, unreferenced, zero unique commits | YES |
| `update` | `3348140` | 2026-01-04 | none found (the update.yml WORKFLOW is active infrastructure; this branch is not referenced by it) | Unmerged — archive tip before any deletion (owner review) | NO |

## Recommendations (owner decisions — nothing executed)
- **Deletable now (18 + gh-pages):** all merged, unreferenced feature/sprint/fix branches plus `gh-pages`, `WSA-next`, `refactor/modernize-and-audit`. One command when approved: `git push origin --delete <branch>` per branch.
- **Keep:** `main`, `master`, `experimental` (referenced by CI triggers; `master` is the default branch).
- **Archive-then-decide:** `update` (tag its tip `archive/update-branch-2026-01` first), both `dependabot/*` (dependabot will reopen fresher bumps).
- **Local cleanup:** `git branch -d origin` (misnamed, merged; local-only).
- M4 note: branch deletion never touches tags, releases, or manifests — release history remains immutable regardless of this report's outcome.
