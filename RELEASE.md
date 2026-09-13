# Release Engineering Specification

This document defines the release lifecycle, versioning convention, tagging format, and asset generation standards for WSABuilds.

---

## Release Channels & Tagging Conventions

Release tags in WSABuilds follow the format:

```text
<OS>_<WSA_Version>[_<Modifier>]
```

### Examples:
- **Windows 11 Stable**: `Windows_11_2407.40000.4.0`
- **Windows 11 LTS Release**: `Windows_11_2407.40000.4.0_LTS_7_HOTFIX_1`
- **Windows 10 Compatibility Release**: `Windows_10_2407.40000.4.0`
- **ARM64 Architecture**: `Windows_11_2407.40000.4.0_arm64`

---

## Release Artifacts Specification

Each production release publishes the following assets:
1. **Compressed Package (`.7z`)**:
   - Format: 7-Zip archive compressed with LZMA2 solid compression (`-mx=6 -m0=LZMA2 -ms=on -mmt=8`).
   - Naming convention: `WSA_<version>_<arch>_<variant>.7z`.
2. **Checksum Verification (`sha256-checksum.txt`)**:
   - Format: Standard GNU coreutils SHA-256 digest format: `<hash>  <filename>`.

---

## Automated CI/CD Release Pipeline

Production releases are coordinated by `.github/workflows/build.yml` and `.github/workflows/update.yml`:

```text
[Cron: Daily at 03:00 UTC]
        │
        ▼
[Check Updates: FE3, Magisk, OpenGApps]
        │
        ▼
[Create GitHub Release Draft Tag]
        │
        ▼
[Job 1: Ubuntu Runner (build.sh)]
  ├── Patch initrd.img with Magisk & GApps
  ├── Apply Houdini ARM translation
  └── Spoof device model to Pixel 5 (redfin)
        │
        ▼
[Job 2: Windows Runner (MakePri & VHDX Compaction)]
  ├── Merge PRI resources with makepri.exe
  ├── Compact system, vendor, product VHDx with diskpart.exe
  ├── Compress with 7z (LZMA2)
  └── Publish assets to GitHub Release via softprops/action-gh-release@v2
```

---

## Integrity & Verification

Before publishing any release:
- SHA-256 checksums must match the computed artifact hash.
- Package filelist (`filelist.txt`) must verify all constituent VHDX and tool files.
- Real-time diagnostic verification can be executed via `test_runtime.py` against a running WSA instance.
