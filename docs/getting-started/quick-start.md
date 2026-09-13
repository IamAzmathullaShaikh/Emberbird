# Quick Start Guide: Windows Subsystem for Android (WSA)

Welcome to **WSABuilds**! This beginner-friendly guide walks you through setting up Windows Subsystem for Android with Google Play Store and Magisk root on Windows 10 or Windows 11 in under 5 minutes.

---

## 1. System Prerequisites

Before beginning installation, ensure your computer meets the minimum hardware and software requirements:

| Requirement | Minimum Specification | Recommended |
|---|---|---|
| **Operating System** | Windows 11 Build 22000+ or Windows 10 22H2 Build 19045+ | Windows 11 23H2 / 24H2 |
| **Architecture** | 64-bit x86 (`x64`) or ARM64 | 64-bit x86 (`x64`) |
| **System Memory (RAM)** | 8 GB | 16 GB or higher |
| **Storage** | 10 GB free space on SSD | 20 GB free space on NVMe SSD |
| **Hardware Virtualization** | Enabled in BIOS/UEFI | Enabled in BIOS/UEFI |

---

## 2. Step 1: Verify Hardware Virtualization

Windows Subsystem for Android runs inside Microsoft's Hyper-V virtualization container. Hardware virtualization must be enabled in your computer's motherboard BIOS/UEFI.

1. Press `Ctrl + Shift + Esc` to open **Task Manager**.
2. Select the **Performance** tab on the left sidebar.
3. Click **CPU**.
4. In the bottom-right information panel, look for **Virtualization**:
   - If it says **Enabled**: Proceed to Step 2.
   - If it says **Disabled**: You must reboot into your computer's BIOS/UEFI settings and enable **Intel Virtualization Technology (Intel VT-x)** or **AMD-V / SVM Mode**.

---

## 3. Step 2: Enable Windows Virtual Machine Platform

WSA requires the Windows **Virtual Machine Platform** feature:

1. Press `Windows Key + S`, type `Turn Windows features on or off`, and press `Enter`.
2. Scroll down and check the box for **Virtual Machine Platform**.
3. *(Optional but recommended for Windows 11 Pro/Enterprise)*: Check **Windows Hypervisor Platform**.
4. Click **OK**. Windows will install the required system components.
5. **Restart your computer** when prompted.

---

## 4. Step 3: Download the Recommended Release

1. Download the recommended release from the WSABuilds Web Portal (`/downloads`) or the official GitHub Releases page: `https://github.com/IamAzmathullaShaikh/WSABuilds/releases`.
2. Download the recommended standard package for your computer:
   - **For Intel/AMD Processors**:  
     `WSA_[version]_x64_[root]_[gapps].7z` (or `.zip` - check repository releases for current build)
   - **For Snapdragon Processors**:  
     `WSA_[version]_arm64_[root]_[gapps].7z` (or `.zip` - check repository releases for current build)
3. Once downloaded, extract the entire archive into a permanent folder on your drive (e.g. `C:\WSA` or `D:\Android\WSA`).
   > **Important**: Do **not** delete or move this folder after installation, as Windows runs the subsystem directly from this location.

---

## 5. Step 4: Execute Installation

1. Open the extracted folder containing the WSA files.
2. Locate the file named `Install.ps1`.
3. Right-click `Install.ps1` and select **Run with PowerShell**.
4. A blue terminal window will open:
   - If prompted with an *Execution Policy* warning, press `Y` and hit `Enter`.
   - If prompted by *User Account Control (UAC)*, click **Yes** to allow administrator privileges.
5. The installer will automatically register the AppX package with Windows.
6. When complete, the **Windows Subsystem for Android Settings** application and the **Google Play Store** will automatically launch.

---

## 6. Step 5: First-Boot Google Play Setup

1. In the WSA Settings window, ensure that **Optional diagnostic data** is toggled according to your preference.
2. The Google Play Store window will appear. Click **Sign In**.
3. Enter your Google Account credentials.
4. You now have complete access to the Google Play Store on your Windows desktop!

---

## Next Steps & Community Tools

- **Interactive Diagnostic Wizard**: Experiencing an installation error, virtualization failure, or ADB connection problem? Use the [Interactive Diagnostic Wizard](/troubleshoot/wizard) for instant, guided decision trees and copyable PowerShell remediation commands.
- **Banking & UPI Apps**: Review the [Play Integrity Guide](../configuration/play-integrity-setup.md) to configure root cloaking for apps like PhonePe, Paytm, and SBI YONO.
- **Application Compatibility**: Check real-world community test results in the [Compatibility Directory](/compatibility).
- **Subsystem Management**: Manage cold VHDX backups, safe restores, and guided updates with the **WSABuilds Manager** desktop client.
- **Error Codes Reference**: Consult the [Error Codes Guide](../troubleshooting/error-codes.md) for root-cause analysis and manual recovery instructions.
