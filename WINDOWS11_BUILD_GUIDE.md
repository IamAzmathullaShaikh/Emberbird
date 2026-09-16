# Windows 11 Build Guide for Emberbird

A complete, copy-paste-ready technical guide for compiling, packaging, and verifying customized Windows Subsystem for Android (WSA) packages featuring **Magisk Stable root** and **OpenGApps Pico** directly on Windows 11.

---

## 1. Prerequisites

Before building Emberbird, verify that your host system meets the following specifications:

* **Operating System:** Windows 11 (Build 22000.526 or higher, 64-bit x86_64).
* **Processor:** Intel Core 8th Gen+ / AMD Ryzen 3000+ / Qualcomm Snapdragon 8c+ with Hardware Virtualization support.
* **RAM:** Minimum 8 GB (16 GB recommended).
* **Storage:** Minimum 20 GB free space on an **NTFS** partition (build scripts and intermediate VHDX files will fail on exFAT/FAT32).
* **Virtualization:** Enabled in BIOS/UEFI (Intel VT-x / AMD-V / SVM).

---

## 2. Required Software

Install the following software on Windows 11:

1. **Windows Subsystem for Linux (WSL2):** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS.
2. **Git for Windows:** Version ≥ 2.40 ([git-scm.com](https://git-scm.com/)).
3. **Python:** Version ≥ 3.10 ([python.org](https://www.python.org/downloads/windows/)). Ensure *"Add Python to PATH"* is checked during setup.
4. **7-Zip:** 64-bit version ≥ 23.01 ([7-zip.org](https://www.7-zip.org/)). Default location: `C:\Program Files\7-Zip\7z.exe`.
5. **Windows Terminal & PowerShell 7+ (Recommended):** Pre-installed on Windows 11 or available via Microsoft Store.

---

## 3. Environment Setup

### 3.1 Enable Required Windows Optional Features
Open **PowerShell as Administrator** and execute:

```powershell
# Enable Virtual Machine Platform and Windows Hypervisor Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart

# Enable WSL optional component
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

> [!NOTE]
> Restart your computer after executing the above commands if prompted.

---

## 4. Git Configuration

Ensure long path support and line ending normalization are active in Git:

```powershell
# Enable Windows Long Paths in Git and system registry
git config --global core.longpaths true
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'LongPathsEnabled' -Value 1

# Configure proper checkout line endings
git config --global core.autocrlf input
```

---

## 5. Python Setup

Verify Python 3.10+ is accessible in your PowerShell environment:

```powershell
python --version
python -m pip install --upgrade pip
```

---

## 6. WSL Setup

Install and initialize Ubuntu on WSL2:

```powershell
# Install Ubuntu on WSL2
wsl --install -d Ubuntu

# Set default WSL version to 2
wsl --set-default-version 2
```

Launch Ubuntu from your Start Menu, complete initial user account setup, and confirm WSL2 operation:

```powershell
wsl -l -v
# Output should indicate Ubuntu running Version 2
```

---

## 7. Dependency Installation (Inside WSL2)

Open your WSL2 Ubuntu terminal and execute:

```bash
# Update package repositories
sudo apt-get update && sudo apt-get upgrade -y

# Install required build tools and libraries
sudo apt-get install -y \
  bash \
  curl \
  wget \
  aria2 \
  unzip \
  p7zip-full \
  python3 \
  python3-pip \
  python3-venv \
  e2fsprogs \
  attr \
  qemu-utils \
  xmlstarlet \
  libxml2-utils \
  sed \
  tar

# Verify tool availability
which aria2c 7z qemu-img python3
```

---

## 8. Repository Clone

### In WSL2 (Recommended for `./scripts/build.sh`):
```bash
# Navigate to home directory or workspace
cd ~

# Clone the repository
git clone https://github.com/IamAzmathullaShaikh/WSABuilds.git
cd WSABuilds
```

### In Native Windows PowerShell (For `build_local.py`):
```powershell
cd C:\Projects
git clone https://github.com/IamAzmathullaShaikh/WSABuilds.git
cd WSABuilds
```

---

## 9. Configuration

Emberbird defaults to a locked, battle-tested production target:
* **Architecture:** `x64`
* **WSA Release Channel:** `retail` (stable)
* **Root Solution:** `Magisk Stable` (v30.6+)
* **GApps Distribution:** `OpenGApps Pico` (Android 13 / API 33)
* **Device Fingerprint Spoofing:** Google Pixel 5 (`redfin`)

If you have a GitHub Personal Access Token (PAT), export it to avoid GitHub API rate-limiting when downloading releases:

```bash
export GITHUB_TOKEN="ghp_yourPersonalAccessTokenHere"
```

---

## 10. Build Commands

### Method A: Building via Linux / WSL2 Pipeline (Standard)

The Linux pipeline orchestrates upstream MSIX downloads, extracts VHDX images, injects Magisk/GApps payloads using `magiskboot`, spoofs Pixel 5 build properties, and compresses the final release into `.7z`.

```bash
# Enter the build directory
cd tools

# Install Python script dependencies into local venv
python3 -m venv python3-env
source python3-env/bin/activate
pip install -r scripts/requirements.txt

# Run the build script
./scripts/build.sh --compress-format 7z
```

#### Available CLI Flags for `build.sh`:
* `--compress-format <7z|zip|none>`: Output archive format (default: `7z`).
* `--offline`: Skip all downloads and use pre-cached archives located in `download/`.
* `--skip-download-wsa`: Skip WSA download and reuse an existing package in `download/`.
* `--debug`: Enable verbose bash tracing (`set -x`).

---

### Method B: Building via Native Windows Standalone Builder

Emberbird includes a pure-Python Windows builder (`tools/build_local.py`) that constructs the SVR4 CPIO `initrd.img` archive and XZ compression natively without requiring a Linux kernel or WSL VM.

```powershell
# In PowerShell (Run as Administrator)
cd tools\scripts

# Install Python dependencies
pip install -r requirements.txt

# Run the local builder
python build_local.py
```

The script will:
1. Verify presence of cached WSA, Magisk, and GApps payloads in `../download`.
2. Extract the MSIX bundle.
3. Repack `initrd.img` with Magisk trampolines and the WSA-Addon loopback mount service.
4. Stage runtime dependencies and generate an uncompressed or compressed package in `../output`.

---

## 11. Verification

After the build completes, verify package integrity and compliance:

```powershell
# 1. Run offline identity validation
python scripts/validate_package_identity.py --baseline config/baseline-identity.json

# 2. Run offline subsystem structure validation
python scripts/validate_package_integrity.py --package-dir output/WSA_2407.40000.4.0_x64

# 3. Verify Magisk trampoline structure
python scripts/validate_magisk.py --package-dir output/WSA_2407.40000.4.0_x64

# 4. Verify OpenGApps Pico components
python scripts/validate_gapps.py --package-dir output/WSA_2407.40000.4.0_x64

# 5. Run repository unit test suite
python -m unittest discover -s tests -v
```

---

## 12. Output Artifacts

The final output is saved to `output/`:

* **Release Archive:**  
  `WSA_<version>_x64_Release-Nightly-with-magisk-<magisk_ver>-stable-GApps-13.0-pico.7z`
* **Uncompressed Installation Directory:**  
  `WSA_<version>_x64/`
  - `AppxManifest.xml`: MSIX package manifest with preserved Microsoft package identity.
  - `Install.ps1`: Automated installation script.
  - `Run.bat`: One-click execution launcher.
  - `system.img` / `system.vhdx`: Android system partition with Magisk and GApps overlay hooks.
  - `initrd.img`: Patched SVR4 CPIO ramdisk with `lspinit`, `magiskboot`, and `overlay.d/sbin/init-ld.xz`.

### Installation:
1. Extract the `.7z` archive to a permanent folder on an NTFS drive (e.g. `C:\WSA`).
2. Right-click `Install.ps1` and select **Run with PowerShell** (or run `Run.bat`).
3. If prompted by User Account Control (UAC), click **Yes**.
4. Once installation completes, Windows Subsystem for Android, Google Play Store, and Magisk will launch automatically.

---

## 13. Troubleshooting

### Issue 1: `SSLCertVerificationError: self-signed certificate in certificate chain`
* **Cause:** Linux/WSL environment lacks Microsoft Root CA certificates when downloading from `fe3.delivery.mp.microsoft.com`.
* **Solution:** Emberbird bundles Microsoft Root CA 2011 and Intermediate CA 2.1 in `tools/update-check/env_helpers.py`. Ensure you are running the latest repository code.

### Issue 2: `Path Too Long (MAX_PATH)`
* **Cause:** Windows 260-character path limit during extraction.
* **Solution:** Extract to a short root directory such as `C:\WSA` and ensure LongPathsEnabled is active in the Windows Registry (`HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 1`).

### Issue 3: `Install.ps1 cannot be loaded because running scripts is disabled`
* **Cause:** Windows PowerShell Execution Policy restriction.
* **Solution:** Run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\Install.ps1
  ```

### Issue 4: `Virtualization Error / Hyper-V not enabled`
* **Cause:** Hardware virtualization disabled in BIOS/UEFI or Windows Hypervisor Platform features missing.
* **Solution:** Confirm virtualization is enabled in BIOS/UEFI. Enable `VirtualMachinePlatform` and `HypervisorPlatform` via DISM as shown in Step 3.
