# Building WSABuilds

This guide documents the procedures for compiling and assembling customized Windows Subsystem for Android (WSA) packages.

---

## Build System Architecture

WSABuilds supports two distinct build pipelines:
1. **Linux / WSL2 Pipeline (`MagiskOnWSA/scripts/build.sh`)**: Modular Bash build system that downloads upstream dependencies, converts and resizes VHDX images, injects Magisk/GApps via `magiskboot`, and applies Houdini ARM translation.
2. **Native Windows Standalone Builder (`MagiskOnWSA/scripts/build_local.py`)**: Pure-Python Windows builder that directly parses and synthesizes SVR4 CPIO `initrd.img` archives and XZ compression without requiring WSL, Hyper-V, or root privileges.

---

## Method 1: Linux / WSL2 Build Pipeline

### Prerequisites (Ubuntu / Debian)
```bash
sudo apt-get update && sudo apt-get install -y \
  e2fsprogs attr unzip qemu-utils python3-venv aria2 p7zip-full curl xmlstarlet
```

### Build Execution
Navigate to `MagiskOnWSA` and execute `build.sh`:
```bash
cd MagiskOnWSA

# Standard build: Retail release, Magisk Stable, OpenGApps Pico, Redfin device model
./scripts/build.sh --compress-format 7z
```

### Command-Line Arguments
| Argument | Description | Default |
|---|---|---|
| `--arch <arch>` | Target CPU architecture (`x64` or `arm64`) | `x64` |
| `--release-type <type>` | WSA channel (`retail`, `RP`, `WIS`, `WIF`) | `retail` |
| `--magisk-ver <ver>` | Magisk release channel (`stable`, `beta`, `canary`) | `stable` |
| `--gapps-brand <brand>` | GApps variant (`MindTheGapps`, `OpenGApps`, `none`) | `OpenGApps` |
| `--compress-format <fmt>` | Output archive format (`7z`, `zip`, `none`) | `7z` |
| `--offline` | Skip downloading if archives already exist in `download/` | Disabled |

---

## Method 2: Native Windows Standalone Builder

The standalone builder operates directly on Windows using standard Python 3.10+.

### Prerequisites
- Windows 10 (Build 19041+) or Windows 11
- Python 3.10+ installed and on `PATH`
- 7-Zip installed (at `C:\Program Files\7-Zip\7z.exe` or on `PATH`)

### Required Downloads in `MagiskOnWSA/download/`:
- `wsa-retail.zip`: Official stock WSA MSIX bundle
- `magisk-stable.zip`: Official Magisk APK / ZIP release
- `gapps-13.0-x86_64.img`: Minimal OpenGApps ext4 image
- `gapps-13.0.rc`: Init RC configuration for GMS
- `cust.img`: Boot overlay image

### Execution:
```cmd
cd MagiskOnWSA\scripts
python build_local.py
```

The output package will be generated under `MagiskOnWSA\output\WSA_<version>_<arch>\`.

---

## Output Structure & Artifacts

The final assembled package directory contains:
- `system.vhdx`, `vendor.vhdx`, `product.vhdx`, `system_ext.vhdx`
- `Tools/initrd.img` (patched with Magisk trampoline and GApps overlay)
- `AppxManifest.xml` (Microsoft manifest configured for sideloading)
- `Install.ps1`, `Run.bat` (Elevation launcher and installation automation)
- `filelist.txt` (Integrity manifest)
