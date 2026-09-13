# Windows Validation Lab Design Specification

This document details the architectural design, security requirements, and automated deployment of dedicated, self-hosted Windows validation runners for WSABuilds.

---

## 1. System Topology & Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                      │
│                (IamAzmathullaShaikh/WSABuilds)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ GitHub Actions Runner Agent
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Self-Hosted Windows Validation Host             │
│            (Windows 11 Pro / Enterprise 23H2+)              │
├─────────────────────────────────────────────────────────────┤
│  Host OS Services:                                          │
│  ├── Hyper-V & VirtualMachinePlatform (Nested Virtualization)│
│  ├── Windows AppModelUnlock (Developer Mode Enabled)        │
│  ├── GitHub Actions Runner Service                          │
│  └── ADB Server Daemon (127.0.0.1:58526)                    │
├─────────────────────────────────────────────────────────────┤
│  WSA Execution Sandbox:                                     │
│  ├── MicrosoftCorporationII.WindowsSubsystemForAndroid       │
│  ├── Magisk Root Daemon (su, zygisk)                        │
│  └── OpenGApps Services (Phonesky, GMSCore, GSF)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware & Host Prerequisites

| Component | Minimum Specification | Recommended Specification |
|---|---|---|
| **Operating System** | Windows 11 64-bit (Build 22000.526+) | Windows 11 Enterprise 23H2 / 24H2 |
| **CPU** | 4 Cores with Intel VT-x / AMD-V | 8+ Cores with Nested Virtualization |
| **RAM** | 16 GB | 32 GB DDR4 / DDR5 |
| **Storage** | 100 GB Free NVMe SSD | 250 GB Free NVMe SSD |
| **Networking** | 100 Mbps broadband | 1 Gbps broadband |

---

## 3. Host Hardening & Security Standards

### RDP Security Policy:
- **No Plaintext Passwords**: Never embed RDP credentials or administrative tokens into scripts, markdown files, or workflow manifests.
- **Credential Storage**: Store all runner deployment tokens and administrative credentials in encrypted **GitHub Environment Secrets**.
- **Network Isolation**: Restrict RDP access to VPN or specific administrative IP addresses; disable default RDP port (3389).

---

## 4. Automated Provisioning Script

Run the automated provisioning script from an elevated PowerShell terminal:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts/setup_validation_runner.ps1
```

The script automates:
1. Enabling `VirtualMachinePlatform` and `Hyper-V`.
2. Enabling Windows Developer Mode (`AllowDevelopmentWithoutDevLicense = 1`).
3. Installing platform dependencies (`7-Zip`, `Git`, `Python 3.11`, `ADB`).
4. Configuring ADB loopback firewall exceptions for port `58526`.
