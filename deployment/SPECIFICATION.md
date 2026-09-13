# WSABuilds Manager Release Packaging Specification

## 1. Overview and Architecture

This document defines the release packaging, artifact naming conventions, checksum validation standards, and Windows Package Manager (Winget) distribution specifications for the WSABuilds Manager desktop application.

WSABuilds Manager is distributed across two primary packaging formats:
1. Setup Installer (NSIS-based executable)
2. Portable Archive (Standalone ZIP container)

Both distribution formats target Windows 10 (Build 19045+) and Windows 11 (Build 22000+) across 64-bit architectures (x64 and arm64).

---

## 2. Release Packaging Targets

### Target 1: Setup Installer (.exe)
- **Engine**: Nullsoft Scriptable Install System (NSIS) generated via Tauri bundle target.
- **Target File Naming Convention**: `WSABuildsManager-Setup-<version>-<arch>.exe`
  - Example (x64): `WSABuildsManager-Setup-0.2.0-x64.exe`
  - Example (arm64): `WSABuildsManager-Setup-0.2.0-arm64.exe`
- **Installation Scope**: User-mode (`Scope: user`).
- **Default Installation Path**: `%LOCALAPPDATA%\Programs\WSABuildsManager`
- **Elevation Requirement**: Non-elevated execution for standard installation. Elevation is prompted dynamically only when modifying system-wide registry policies.
- **Silent Installation Switches**:
  - Silent Mode: `/S`
  - Target Directory Override: `/D=<path>`
- **Registry Registration**: Writes to `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\WSABuildsManager` for integration with Windows Settings > Apps & Features and Winget uninstallation.

### Target 2: Portable Archive (.zip)
- **Engine**: Standard DEFLATE zip archive.
- **Target File Naming Convention**: `WSABuildsManager-Portable-<version>-<arch>.zip`
  - Example (x64): `WSABuildsManager-Portable-0.2.0-x64.zip`
  - Example (arm64): `WSABuildsManager-Portable-0.2.0-arm64.zip`
- **Internal Archive Layout**:
  - Root: `wsabuilds-manager.exe` (Executable binary)
  - Resources: `resources/` (Icons, web assets)
  - Documentation: `LICENSE`, `README.txt`
- **Portability Contract**: Application stores caches and configuration under `%LOCALAPPDATA%\WSABuilds\manager`, leaving the execution directory clean.

---

## 3. Cryptographic Checksum Specification

Every build release produces cryptographic digests using standard SHA-256 hashing.

### Combined Checksum Digest File
- **Filename Convention**: `WSABuildsManager-<version>-checksums.txt`
  - Example: `WSABuildsManager-0.2.0-checksums.txt`
- **Format**: Standard GNU coreutils sha256sum format:
  `<64-character lowercase hex sha256> *<filename>`
- **Sample Representation**:
  ```
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 *WSABuildsManager-Setup-0.2.0-x64.exe
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 *WSABuildsManager-Setup-0.2.0-arm64.exe
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 *WSABuildsManager-Portable-0.2.0-x64.zip
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 *WSABuildsManager-Portable-0.2.0-arm64.zip
  ```

### Sidecar Checksum Files
- In addition to the aggregate manifest, each individual distribution binary includes an explicit `.sha256` sidecar file containing the isolated hash.

---

## 4. Winget Manifest Specification

### Package Identity
- **PackageIdentifier**: `WSABuilds.WSABuildsManager`
- **Publisher**: `WSABuilds`
- **PackageName**: `WSABuilds Manager`
- **Manifest Schema Version**: `1.6.0`

### Directory Layout
Winget manifests reside within the repository at:
`manifests/w/WSABuilds/WSABuildsManager/<PackageVersion>/`

Comprising three atomic YAML manifests:
1. `WSABuilds.WSABuildsManager.yaml`: Version declaration manifest.
2. `WSABuilds.WSABuildsManager.installer.yaml`: Architecture, installer type, download URL, and SHA-256 definitions.
3. `WSABuilds.WSABuildsManager.locale.en-US.yaml`: Metadata, localized descriptions, license, and tag definitions.

---

## 5. Artifact Naming Grammar

The distribution automation strictly validates all output filenames using regular expressions:

- **Installer Binary**: `^WSABuildsManager-Setup-[0-9]+\.[0-9]+\.[0-9]+-(x64|arm64)\.exe$`
- **Portable Container**: `^WSABuildsManager-Portable-[0-9]+\.[0-9]+\.[0-9]+-(x64|arm64)\.zip$`
- **Combined Checksums**: `^WSABuildsManager-[0-9]+\.[0-9]+\.[0-9]+-checksums\.txt$`

Any artifact deviating from this grammar is rejected by the pre-release validation suite.
