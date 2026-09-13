# Forensic Report: Complete Removal of KernelSU and SuperSU Root Solutions

**Date:** September 13, 2026  
**Auditor:** Principal CI/CD & Reliability Engineering Team  
**Scope:** Elimination of all non-Magisk root solutions (KernelSU, SuperSU, KSU) across the entire WSABuilds repository.  
**Repository State:** Zero active KernelSU / SuperSU build pipelines or dormant branches.

---

## Executive Summary

WSABuilds previously contained historical, dormant, and unmaintained references to **KernelSU** and **SuperSU**. Modern Windows Subsystem for Android (Android 13 / API 33) requires dynamic linker and initrd ramdisk trampolining (`lspinit`, `magiskboot`, `overlay.d/sbin/init-ld.xz`) which is natively and stably supported exclusively by **Magisk Stable (≥ 26.0, currently v30.6+)**. 

SuperSU has been obsolete since Android 9 (Pie) and cannot run on Android 13. KernelSU requires compiling custom Linux kernels (`bzImage`) into WSA's `Tools/` directory, which is outside the scope of stock WSA retail packaging and breaks upgrade compatibility and automated update delivery.

To reduce technical debt, eliminate dead code, and prevent user confusion, all KernelSU and SuperSU scripts, update checkers, documentation, badges, and build options have been completely expunged.

---

## 1. Search Query Audit

A repository-wide case-insensitive regex search was executed across all tracked files for:
```regex
(kernelsu|supersu|\bksu\b)
```

### Search Scope Audited:
- Workflows (`.github/workflows/*.yml`)
- Build scripts (`MagiskOnWSA/scripts/*`, `build_local.py`)
- Update checkers (`MagiskOnWSA/Update Check/*`)
- Documentation (`Documentation/**`, `docs/**`, `*.md`)
- Templates (`templates/**`)
- Test suites (`tests/**`)
- Configurations (`config/**`)

### Result:
All occurrences were either permanently deleted (files removed from Git) or replaced with accurate descriptions documenting that only Magisk Stable is built.

---

## 2. Inventory of Removed Files

The following 9 files and directories dedicated to KernelSU and SuperSU were removed:

| # | File / Directory Path | Purpose | Removal Evidence & Rationale |
|---|---|---|---|
| 1 | `MagiskOnWSA/scripts/generateKernelSULink.py` | Download generator script for KernelSU | Never called by `build.sh` (locked to Magisk). Deleted in commit `c073ff9`. |
| 2 | `MagiskOnWSA/Update Check/KernelSUUpdateCheck.py` | Automated update checker for KernelSU GitHub releases | Never invoked by `.github/workflows/update.yml`. Deleted in commit `c073ff9`. |
| 3 | `MagiskOnWSA/docs/KernelSU.md` | Installation tutorial for KernelSU manager and kernel replacement | Obsolete guide for unsupported root base. Deleted in commit `c073ff9`. |
| 4 | `MagiskOnWSA/docs/Guides/KernelSU.md` | Guide for ADB sideloading `ksuinstall` | Broken / orphaned guide. Deleted in commit `c073ff9`. |
| 5 | `Documentation/Usage Guides/General Usage Guides/KernelSU.md` | Guide for sideloading KernelSU Manager | Outdated guide for deprecated root method. Deleted in commit `c073ff9`. |
| 6 | `Documentation/Usage Guides/Post-Installation Guides/KernelSU/MindTheGapps and AMZ/` | Post-installation guide | Orphaned, unreferenced guide. Deleted in commit `c073ff9`. |
| 7 | `Documentation/Usage Guides/Post-Installation Guides/KernelSU/MindTheGapps and Removed AMZ/` | Post-installation guide | Orphaned, unreferenced guide. Deleted in commit `c073ff9`. |
| 8 | `Documentation/Usage Guides/Post-Installation Guides/KernelSU/No Gapps and AMZ/` | Post-installation guide | Orphaned, unreferenced guide. Deleted in commit `c073ff9`. |
| 9 | `Documentation/Usage Guides/Post-Installation Guides/KernelSU/No Gapps and Removed AMZ/` | Post-installation guide | Orphaned, unreferenced guide. Deleted in commit `c073ff9`. |

---

## 3. Build Logic & Script Simplifications

### 3.1 `MagiskOnWSA/scripts/run.sh`
* **Previous Implementation:**
  Presented an interactive Whiptail radio list prompting the user to choose between `magisk` and `kernelsu`:
  ```bash
  if (YesNoBox '([title]="Root" [text]="Do you want to Root WSA?")'); then
      ROOT_SOL=$(
          Radiolist '([title]="Root solution"
                      [default]="magisk")' \
              'magisk' "Magisk" 'on' \
              'kernelsu' "KernelSU" 'off'
      )
      COMMAND_LINE+=(--root-sol "$ROOT_SOL")
  fi
  ```
* **Refactored Implementation:**
  Eliminated the dormant `kernelsu` branch and simplified logic to default directly to `magisk`:
  ```bash
  if (YesNoBox '([title]="Root" [text]="Do you want to Root WSA?")'); then
      ROOT_SOL="magisk"
      COMMAND_LINE+=(--root-sol "$ROOT_SOL")
  fi
  ```

### 3.2 `MagiskOnWSA/scripts/build.sh`
* Verified that `build.sh` contains zero references or branches for `kernelsu` or `supersu`.
* Target is locked strictly to `Root solution: Magisk Stable (≥ 26.0)`.

---

## 4. Documentation Cleanups & Link Remediations

To ensure zero broken links across the documentation suite, all inbound references and badges pointing to KernelSU were removed:

| Document | Location | Change Description |
|---|---|---|
| `Documentation/WSABuilds/Usage Guide.md` | Lines 16–18 | Removed `### Installing KernelSU:` heading and badge link to `KernelSU.md`. |
| `MagiskOnWSA/docs/README.md` | Lines 162–165 | Removed KernelSU FAQ entry and reference to KernelSU.md. |
| `Documentation/WSABuilds/Custom Builds.md` | Line 12 | Changed `State the Root Solution (Magisk, KernelSU or none)?` to `State the Root Solution (Magisk or none)?`. |
| `Documentation/WSABuilds/Credits.md` | Line 96 | Removed `- [KernelSU](https://github.com/tiann/KernelSU)` upstream credit entry. |
| `Documentation/WSABuilds/App Compatibility.md` | Lines 129, 213 | Removed KernelSU manager compatibility row and cleaned up eGovPH testing notes. |
| `README.md` | Header & LTS | Removed KernelSU from project subtitle, LTS guarantee, and variant matrix. |

---

## 5. Verification & Validation

1. **Static Grep:** Confirmed zero remaining occurrences of `kernelsu`, `supersu`, or `ksu` across all active scripts, workflows, and configs.
2. **Markdown Integrity:** `python scripts/check_doc_links.py` audited all repository Markdown files and reported **0 broken links**.
3. **Unit Tests:** `python -m unittest discover -s tests -v` ran 24/24 tests with **100% pass rate**.
4. **Security Scan:** `python scripts/security_scan.py` reported **0 detected credentials or machine paths**.

---

## 6. Conclusion

KernelSU and SuperSU have been completely removed from WSABuilds. The repository's root management pipeline is now 100% focused on **Magisk Stable (v30.6+)**, resulting in a leaner, more maintainable, and reliable build platform.
