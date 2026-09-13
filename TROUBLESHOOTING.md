# Troubleshooting & Known Issues

This document serves as the master index for resolving common installation, update, and runtime issues in WSABuilds.

For detailed, step-by-step resolution guides, refer to the [Documentation/Fix Guides/](Documentation/Fix%20Guides/) directory.

---

## Pre-Installation Issues

| Error Code / Symptom | Root Cause | Solution Guide |
|---|---|---|
| **0x80073CF0** | Package extraction corruption or pending Windows updates | [Fix Error 0x80073CF0](Documentation/Fix%20Guides/Pre-Install%20Issues/Fix%20Error%200x80073CF0.md) |
| **0x80073CF6** | Package registration conflict with existing WSA installation | [Fix Error 0x80073CF6](Documentation/Fix%20Guides/Pre-Install%20Issues/Fix%20Error%200x80073CF6.md) |
| **0x80073CF9** | Storage service failure or missing AppData permissions | [Fix Error 0x80073CF9](Documentation/Fix%20Guides/Pre-Install%20Issues/Fix%20Error%200x80073CF9.md) |
| **0x80073CFD** | Hardware or OS minimum requirements not met | [Fix Error 0x80073CFD](Documentation/Fix%20Guides/Pre-Install%20Issues/Fix%20Error%200x80073CFD.md) |
| **0x80073D10** | Volume does not support NTFS or virtualization features | [Fix Error 0x80073D10](Documentation/Fix%20Guides/Pre-Install%20Issues/Fix%20Error%200x80073D10.md) |
| **0x80073B17** | `NamedResource Not Found` — corrupted or unmerged `resources.pri` | [Fix Error 0x80073B17](Documentation/Fix%20Guides/Pre-Install%20Issues/NamedResource%20Not%20Found%20-%20Fix%20Error%200x80073B17.md) |
| **Path Too Long** | Windows 260-character MAX_PATH limitation | [Fix Path Too Long](Documentation/Fix%20Guides/Pre-Install%20Issues/FixPathTooLong.md) |
| **Execution Policy Block** | PowerShell script execution restricted | [Fix Install.ps1](Documentation/Fix%20Guides/Pre-Install%20Issues/FixInstallps1.md) |

---

## Post-Installation & Runtime Issues

| Symptom | Root Cause | Solution Guide |
|---|---|---|
| **WSA Does Not Load / No Splashscreen** | Virtual Machine Platform disabled or Hyper-V misconfiguration | [Fix WSA Does Not Load](Documentation/Fix%20Guides/Post-Install%20Issues/WSA%20Does%20Not%20Load%20After%20Install%20+%20No%20Splashscreen.md) |
| **Settings App Crashes on Launch** | Resource index mismatch or GPU compatibility quirk | [Fix Settings App Crashes](Documentation/Fix%20Guides/Post-Install%20Issues/WSA%20Settings%20App%20Crashes%20+%20Android%20Apps%20Do%20Not%20Load%20After%20Installation.md) |
| **Google Play Sign-in Crash** | SELinux denials or initrd CPIO relative path mismatch | [Google Play Issues](Documentation/Fix%20Guides/Post-Install%20Issues/Google%20Play%20Issues.md) |
| **No Internet in Android Apps** | Windows firewall or VPN virtual adapter binding conflict | [Fix Internet](Documentation/Fix%20Guides/Post-Install%20Issues/FixInternet.md) |
| **Virtualization Error on Boot** | Hardware virtualization disabled in BIOS/UEFI | [Fix Virtualization Error](Documentation/Fix%20Guides/Post-Install%20Issues/FixVirtError.md) |
| **Missing Android App Icons** | AppX loose-folder registration cache desynchronization | [Missing Icons](Documentation/Fix%20Guides/Post-Install%20Issues/MissingIcons.md) |

---

## Diagnostic Tools

To diagnose live runtime issues:
1. Ensure **Developer Mode** is enabled in WSA Settings.
2. Run the diagnostic monitor:
   ```cmd
   python MagiskOnWSA\scripts\test_runtime.py
   ```
   This script validates:
   - WSA AppX package registration
   - ADB connectivity over `127.0.0.1:58526`
   - Magisk root status (`su -c id`)
   - Google Play, GMS, and GSF package installation
   - Real-time logcat fatal crash and SELinux denial analysis
