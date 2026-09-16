---
title: "WSABuilds Technical Architecture Specification"
description: "This document provides an in-depth architectural breakdown of the modifications, boot interception, and packaging models utilized in WSABuilds."
category: "getting-started"
order: 1
---

This document provides an in-depth architectural breakdown of the modifications, boot interception, and packaging models utilized in WSABuilds.

---

## 1. Overview of Android Container on Windows

Windows Subsystem for Android runs Android within a lightweight Hyper-V virtual machine utilizing Microsoft's customized Linux kernel. The subsystem boots Android user-space directly from virtual hard disks (VHDX):
- `system.vhdx`: Android system partition (read-only ext4 or EROFS)
- `vendor.vhdx`: Hardware abstraction layer and graphics drivers
- `product.vhdx`: Product-specific applications and overlays
- `system_ext.vhdx`: System extensions
- `userdata.vhdx`: User applications, data, and settings
- `Tools/initrd.img`: SVR4 CPIO ramdisk containing the boot environment

---

## 2. Initrd Interception & Trampoline Architecture

In stock WSA, the kernel executes `/init` inside `initrd.img` to configure early mountpoints and start `init.rc`. 

WSABuilds intercepts the boot process via the **LSPosed Trampoline Architecture**:

```text
[Linux Kernel Boot]
        │
        ▼
[/init (Symlink -> /lspinit)]
        │
        ▼
[/lspinit (Mode 0750)]
        │
  Mounts /overlay.d and executes
        ▼
[/magiskinit (Mode 0750)]
        │
  Injects SELinux policy, overlays /sbin
        ▼
[/wsainit (Original Stock Android Init)]
        │
        ▼
[Android Userspace Init]
        │
  Trigger: post-fs-data
        ▼
[/sbin/post-fs-data.sh]
  ├── Grants ADB shell (UID 2000) Magisk root in SQLite DB
  ├── Loops and mounts lsp_*.img overlays
  └── Injects host adbkey.pub if present
```

### SVR4 CPIO Archive Structure
The patched `initrd.img` conforms to the SVR4 portable format (magic `070701`):

| Entry Name | Mode | Purpose |
|---|---|---|
| `.backup` | `040000` | Magisk backup directory marker |
| `init` | `120000` | Symbolic link pointing to `lspinit` |
| `lspinit` | `100750` | LSPosed trampoline executable |
| `magiskinit` | `100750` | Magisk initialization and policy daemon |
| `wsainit` | `100777` | Original stock WSA init binary |
| `overlay.d` | `040750` | Overlay directory structure |
| `overlay.d/init.lsp.magisk.rc` | `100000` | Init trigger launching `post-fs-data.sh` |
| `overlay.d/gapps.rc` | `100000` | GMS runtime property configuration |
| `overlay.d/sbin` | `040750` | Injected binaries folder |
| `overlay.d/sbin/magisk.xz` | `100644` | CRC32 XZ-compressed Magisk 64-bit binary |
| `overlay.d/sbin/init-ld.xz` | `100644` | Dynamic linker for Magisk |
| `overlay.d/sbin/stub.xz` | `100644` | Magisk Manager APK stub |
| `overlay.d/sbin/lsp_cust.img` | `100000` | Custom overlay filesystem |
| `overlay.d/sbin/lsp_gapps.img` | `100000` | OpenGApps ext4 image overlay |
| `overlay.d/sbin/post-fs-data.sh` | `100000` | Early boot shell script |

---

## 3. Packaging & Code Signing Model

### Loose-Folder Developer Mode Deployment
Modified WSA packages cannot retain Microsoft's official cryptographic signature (`AppxSignature.p7x`). Rather than requiring users to install an untrusted private root CA certificate into the Windows Certificate Store, WSABuilds deploys packages using **Windows Developer Mode Loose-Folder Registration**:

1. **Signature Stripping**: During build, `[Content_Types].xml`, `AppxBlockMap.xml`, `AppxSignature.p7x`, and `AppxMetadata` are removed.
2. **Policy Configuration**:
   ```powershell
   reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"
   ```
3. **Registration**:
   ```powershell
   Add-AppxPackage -ForceApplicationShutdown -ForceUpdateFromAnyVersion -Register .\AppxManifest.xml
   ```

---

## 4. Play Integrity & CTS Device Spoofing

To satisfy Google Play Services CTS and Play Integrity verification on WSA, `fixGappsProp.py` modifies Android system properties to spoof a certified Google Pixel 5 (`redfin`):

```properties
ro.product.model=Pixel 5
ro.product.brand=google
ro.product.name=redfin
ro.product.device=redfin
ro.product.manufacturer=Google
ro.build.fingerprint=google/redfin/redfin:13/TQ3A.230901.001/10750766:user/release-keys
ro.build.version.release=13
ro.build.version.sdk=33
```
