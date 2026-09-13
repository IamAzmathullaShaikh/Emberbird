import type { DiagnosticNode, ErrorCodeMapping } from './types.ts';

export const ERROR_CODE_MAPPINGS: ErrorCodeMapping[] = [
  {
    code: '0x80370102',
    title: 'Virtual Machine Failed to Start (Hyper-V / VT-x Disabled)',
    targetNodeId: 'virt-check-hypervisor',
    category: 'virtualization'
  },
  {
    code: '0x80070005',
    title: 'Access is Denied (AppX Deployment Security Error)',
    targetNodeId: 'install-access-denied',
    category: 'installation'
  },
  {
    code: '0x80073CF9',
    title: 'AppX Deployment Internal Failure (AppReadiness Corrupt/Missing)',
    targetNodeId: 'deploy-appreadiness',
    category: 'deployment'
  },
  {
    code: '0x80073CF3',
    title: 'Package Dependency Missing (VCLibs / UI XAML Missing)',
    targetNodeId: 'deploy-missing-deps',
    category: 'deployment'
  },
  {
    code: '0x80070422',
    title: 'Windows Update / AppX Service Disabled',
    targetNodeId: 'deploy-service-disabled',
    category: 'deployment'
  },
  {
    code: '0x80073D02',
    title: 'Package In Use (Subsystem Running During Update)',
    targetNodeId: 'deploy-package-in-use',
    category: 'deployment'
  }
];

export const DIAGNOSTIC_NODES: DiagnosticNode[] = [
  // --- VIRTUALIZATION CATEGORY ---
  {
    id: 'virt-start',
    title: 'Virtualization & Hypervisor Diagnostics',
    category: 'virtualization',
    symptom: 'WSA fails to launch with 0x80370102, or reports virtual machine could not be started.',
    errorCode: '0x80370102',
    validationStep: 'Verify if Hardware Virtualization (VT-x / AMD-V) and Hyper-V hypervisor are enabled in Windows.',
    powershellCommand: 'Get-ComputerInfo -Property HyperVisorPresent, CsSystemType',
    branches: [
      {
        label: 'HypervisorPresent is False (Hardware Disabled)',
        nextNodeId: 'virt-bios-disabled',
        description: 'Hardware virtualization is disabled in motherboard BIOS/UEFI.'
      },
      {
        label: 'HypervisorPresent is True but VirtualMachinePlatform Missing',
        nextNodeId: 'virt-platform-disabled',
        description: 'Windows optional features are not installed.'
      },
      {
        label: 'Both Enabled but 3rd-Party Hypervisor Conflict',
        nextNodeId: 'virt-hyperv-conflict',
        description: 'VMware Workstation or VirtualBox conflicting with Hyper-V.'
      }
    ],
    remediation: [
      'Check Task Manager (Ctrl + Shift + Esc) -> Performance -> CPU -> Virtualization.',
      'If Disabled, enter BIOS/UEFI and enable Intel VT-x or AMD SVM.',
      'Enable VirtualMachinePlatform via DISM in elevated PowerShell.'
    ],
    relatedDocs: [
      { title: 'WSA Error 0x80370102 Guide', url: '/docs/troubleshooting/error-codes' },
      { title: 'Windows Validation Lab Guide', url: '/docs/getting-started/WINDOWS_VALIDATION_LAB' }
    ]
  },
  {
    id: 'virt-check-hypervisor',
    title: 'Error 0x80370102 Hypervisor Status',
    category: 'virtualization',
    symptom: 'WSA dialog: The virtual machine could not be started because a required feature is not installed.',
    errorCode: '0x80370102',
    validationStep: 'Run PowerShell check to inspect HypervisorPlatform and VirtualMachinePlatform features.',
    powershellCommand: 'Get-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform, HypervisorPlatform',
    branches: [
      {
        label: 'Features are Disabled',
        nextNodeId: 'virt-platform-disabled'
      },
      {
        label: 'Features are Enabled but Error Persists',
        nextNodeId: 'virt-bios-disabled'
      }
    ],
    remediation: [
      'Enable features: dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart',
      'Enable hypervisor: dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart',
      'Reboot Windows immediately.'
    ],
    relatedDocs: [
      { title: 'Common Error Codes', url: '/docs/troubleshooting/error-codes' }
    ]
  },
  {
    id: 'virt-bios-disabled',
    title: 'Enable BIOS/UEFI Hardware Virtualization',
    category: 'virtualization',
    symptom: 'Task Manager displays Virtualization: Disabled.',
    errorCode: '0x80370102',
    validationStep: 'Inspect motherboard BIOS settings for CPU virtualization flags.',
    powershellCommand: '(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled',
    branches: [
      {
        label: 'VirtualizationFirmwareEnabled is True now',
        nextNodeId: 'virt-platform-disabled'
      }
    ],
    remediation: [
      'Reboot your PC and enter BIOS (tap F2, Del, or Esc during startup).',
      'Intel CPUs: Locate Advanced / CPU Configuration and enable Intel Virtualization Technology (VT-x) and VT-d.',
      'AMD CPUs: Locate Advanced / CPU Configuration and enable SVM Mode (Secure Virtual Machine) or AMD-V.',
      'Save changes (F10) and restart Windows.'
    ],
    relatedDocs: [
      { title: 'Error 0x80370102 Resolution', url: '/docs/troubleshooting/error-codes' }
    ]
  },
  {
    id: 'virt-platform-disabled',
    title: 'Enable Windows Virtual Machine Platform',
    category: 'virtualization',
    symptom: 'BIOS virtualization is enabled, but WSA virtual machine fails to launch.',
    errorCode: '0x80370102',
    validationStep: 'Verify Windows Virtual Machine Platform optional component.',
    powershellCommand: 'dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart',
    branches: [
      {
        label: 'Feature enabled and rebooted',
        nextNodeId: 'virt-hyperv-conflict'
      }
    ],
    remediation: [
      'Run: dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart in Administrator PowerShell.',
      'Run: dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart.',
      'Reboot the system to commit the changes.'
    ]
  },
  {
    id: 'virt-hyperv-conflict',
    title: 'Resolve Hyper-V & 3rd-Party Hypervisor Conflicts',
    category: 'virtualization',
    symptom: 'WSA crashes or freezes when third-party VM tools (VMware, VirtualBox, BlueStacks) are running.',
    validationStep: 'Check for competing virtualization services and hypervisor launch type.',
    powershellCommand: 'bcdedit /enum {current} | Select-String "hypervisorlaunchtype"',
    branches: [],
    remediation: [
      'Ensure hypervisor launch type is set to Auto: bcdedit /set hypervisorlaunchtype auto',
      'In VMware Workstation: Enable Settings -> Processors -> Virtualize Intel VT-x/EPT or AMD-V/RVI.',
      'In VirtualBox: Use version 7.0+ with Windows Hyper-V paravirtualization engine.'
    ]
  },

  // --- INSTALLATION CATEGORY ---
  {
    id: 'install-start',
    title: 'Package Installation & Execution Policy Diagnostics',
    category: 'installation',
    symptom: 'Install.ps1 fails or stops with Access Denied or Script Execution Policy errors.',
    errorCode: '0x80070005',
    validationStep: 'Check current PowerShell execution policy and folder permissions.',
    powershellCommand: 'Get-ExecutionPolicy -List',
    branches: [
      {
        label: 'ExecutionPolicy is Restricted / Undefined',
        nextNodeId: 'install-exec-policy'
      },
      {
        label: 'Error 0x80070005 Access is Denied',
        nextNodeId: 'install-access-denied'
      },
      {
        label: 'Developer Mode Not Configured',
        nextNodeId: 'install-dev-mode'
      }
    ],
    remediation: [
      'Set PowerShell Execution Policy to RemoteSigned or Bypass for current session.',
      'Ensure the WSA folder is located in a non-restricted root path such as C:\WSA.'
    ],
    relatedDocs: [
      { title: 'Quick Start Installation Guide', url: '/docs/getting-started/quick-start' }
    ]
  },
  {
    id: 'install-exec-policy',
    title: 'Configure PowerShell Execution Policy',
    category: 'installation',
    symptom: 'Install.ps1 cannot be loaded because running scripts is disabled on this system.',
    validationStep: 'Inspect process execution policy level.',
    powershellCommand: 'Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force',
    branches: [
      {
        label: 'Policy set, checking folder permissions',
        nextNodeId: 'install-access-denied'
      }
    ],
    remediation: [
      'Launch elevated PowerShell (Run as Administrator).',
      'Execute: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force.',
      'Navigate to extracted folder and run .\Install.ps1.'
    ]
  },
  {
    id: 'install-access-denied',
    title: 'Error 0x80070005 (Access is Denied)',
    category: 'installation',
    symptom: 'Add-AppxPackage fails with HRESULT: 0x80070005 (E_ACCESSDENIED).',
    errorCode: '0x80070005',
    validationStep: 'Check NTFS ACL permissions for ALL APPLICATION PACKAGES on the installation directory.',
    powershellCommand: '(Get-Acl "C:\WSA").Access | Where-Object { $_.IdentityReference -like "*ALL APPLICATION PACKAGES*" }',
    branches: [
      {
        label: 'Permissions verified, checking Developer Mode',
        nextNodeId: 'install-dev-mode'
      }
    ],
    remediation: [
      'Move WSA folder out of user Temp or Downloads to C:\WSA.',
      'Right-click C:\WSA -> Properties -> Security -> Edit -> Add.',
      'Enter ALL APPLICATION PACKAGES, check Read & execute, List folder contents, Read -> OK -> Apply.'
    ],
    relatedDocs: [
      { title: 'Error 0x80070005 Fix Guide', url: '/docs/troubleshooting/error-codes' }
    ]
  },
  {
    id: 'install-dev-mode',
    title: 'Enable Windows Developer Mode Loose-Folder Registration',
    category: 'installation',
    symptom: 'Add-AppxPackage rejects package registration without trusted developer certificate.',
    validationStep: 'Verify AllowDevelopmentWithoutDevLicense registry policy.',
    powershellCommand: 'Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue',
    branches: [],
    remediation: [
      'Enable Developer Mode: Open Windows Settings -> System -> For developers -> Toggle Developer Mode ON.',
      'Or via Administrator PowerShell: reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d "1"',
      'Re-execute .\Install.ps1.'
    ],
    relatedDocs: [
      { title: 'Architecture Specification', url: '/docs/getting-started/ARCHITECTURE' }
    ]
  },

  // --- DEPLOYMENT CATEGORY ---
  {
    id: 'deploy-start',
    title: 'AppX Package Deployment & Cache Diagnostics',
    category: 'deployment',
    symptom: 'AppX deployment fails with 0x80073CF9, 0x80073CF3, or 0x80070422.',
    errorCode: '0x80073CF9',
    validationStep: 'Inspect AppReadiness folder, Windows Store cache, and AppXSvc service status.',
    powershellCommand: 'Get-Service -Name appxsvc, wuauserv, bits',
    branches: [
      {
        label: 'Error 0x80073CF9 (AppReadiness failure)',
        nextNodeId: 'deploy-appreadiness'
      },
      {
        label: 'Error 0x80073CF3 (Missing dependencies)',
        nextNodeId: 'deploy-missing-deps'
      },
      {
        label: 'Error 0x80070422 (Service disabled)',
        nextNodeId: 'deploy-service-disabled'
      },
      {
        label: 'Error 0x80073D02 (Package in use)',
        nextNodeId: 'deploy-package-in-use'
      }
    ],
    remediation: [
      'Ensure required Windows services (appxsvc, wuauserv, bits) are running.',
      'Clear AppX cache with wsreset.exe.'
    ],
    relatedDocs: [
      { title: 'Common Error Codes', url: '/docs/troubleshooting/error-codes' }
    ]
  },
  {
    id: 'deploy-appreadiness',
    title: 'Error 0x80073CF9 (AppReadiness Directory Missing)',
    category: 'deployment',
    symptom: 'Installation halts at 0% or 99% with 0x80073CF9 internal package staging failure.',
    errorCode: '0x80073CF9',
    validationStep: 'Check if C:\Windows\AppReadiness and C:\Windows\System32\AU exist.',
    powershellCommand: 'Test-Path "C:\Windows\AppReadiness", "C:\Windows\System32\AU"',
    branches: [],
    remediation: [
      'Create missing directories if Test-Path returned False: New-Item -ItemType Directory -Path "C:\Windows\AppReadiness" -Force.',
      'New-Item -ItemType Directory -Path "C:\Windows\System32\AU" -Force.',
      'Reset Windows Store cache: Press Win+R, type wsreset.exe, press Enter.',
      'Restart services: net stop appxsvc; net start appxsvc'
    ],
    relatedDocs: [
      { title: 'Error 0x80073CF9 Resolution', url: '/docs/troubleshooting/error-codes' }
    ]
  },
  {
    id: 'deploy-missing-deps',
    title: 'Error 0x80073CF3 (Missing Framework Dependencies)',
    category: 'deployment',
    symptom: 'Add-AppxPackage fails citing missing Microsoft.VCLibs or Microsoft.UI.Xaml framework.',
    errorCode: '0x80073CF3',
    validationStep: 'Check if VCLibs and UI XAML packages are registered for the current architecture.',
    powershellCommand: 'Get-AppxPackage *VCLibs*, *UI.Xaml*',
    branches: [],
    remediation: [
      'Install the missing framework dependencies bundled inside your WSA package folder (under dependencies subfolder).',
      'Or download Microsoft.VCLibs.x64.14.00.Desktop.appx from official Microsoft sources.',
      'Install via PowerShell: Add-AppxPackage -Path .\dependencies\Microsoft.VCLibs.*.appx'
    ]
  },
  {
    id: 'deploy-service-disabled',
    title: 'Error 0x80070422 (Windows Update Service Disabled)',
    category: 'deployment',
    symptom: 'Deployment fails because a required service cannot be started.',
    errorCode: '0x80070422',
    validationStep: 'Check startup type of Windows Update service (wuauserv).',
    powershellCommand: 'Get-Service wuauserv | Select-String -Pattern "Status|StartType"',
    branches: [],
    remediation: [
      'Open elevated PowerShell.',
      'Set service to Manual: Set-Service -Name wuauserv -StartupType Manual',
      'Start service: Start-Service -Name wuauserv',
      'Rerun WSA installer.'
    ]
  },
  {
    id: 'deploy-package-in-use',
    title: 'Error 0x80073D02 (Package In Use / Subsystem Running)',
    category: 'deployment',
    symptom: 'Deployment failed because files are locked by a running instance of WSA.',
    errorCode: '0x80073D02',
    validationStep: 'Check for active WsaClient or vmmemWSA processes.',
    powershellCommand: 'Get-Process *wsa*, *vmmem* -ErrorAction SilentlyContinue',
    branches: [],
    remediation: [
      'Open Windows Subsystem for Android Settings -> Click Turn off Windows Subsystem for Android.',
      'Or kill running processes via PowerShell: Stop-Process -Name WsaClient, WsaService -Force -ErrorAction SilentlyContinue',
      'Retry installation: .\Install.ps1'
    ]
  },

  // --- STARTUP & CRASH CATEGORY ---
  {
    id: 'startup-start',
    title: 'WSA Startup Crash & Infinite Splash Screen Diagnostics',
    category: 'startup',
    symptom: 'WSA shows infinite loading spinner, or vmmemWSA process crashes immediately.',
    validationStep: 'Check Windows Event Log for Hyper-V and AppX crash entries.',
    powershellCommand: 'Get-WinEvent -LogName "Microsoft-Windows-AppXDeploymentServer/Operational" -MaxEvents 5 -ErrorAction SilentlyContinue',
    branches: [
      {
        label: 'Infinite Loading Spinner / Splash Screen Hangs',
        nextNodeId: 'startup-infinite-loading'
      },
      {
        label: 'Process Crashes Immediately (SELinux / Init failure)',
        nextNodeId: 'startup-ramdisk-corrupt'
      }
    ],
    remediation: [
      'Verify that initrd.img contains Magisk 26+ dynamic linker and LSPosed trampoline.',
      'Verify that GPU driver supports Vulkan / DirectX 12.'
    ],
    relatedDocs: [
      { title: 'Technical Architecture Specification', url: '/docs/getting-started/ARCHITECTURE' }
    ]
  },
  {
    id: 'startup-infinite-loading',
    title: 'Resolve Infinite Loading Splash Screen',
    category: 'startup',
    symptom: 'Android apps display a rotating spinner that never finishes loading.',
    validationStep: 'Check if WSA graphic card allocation is set to GPU or Software fallback.',
    powershellCommand: 'Get-Process vmmemWSA -ErrorAction SilentlyContinue | Select-String "CPU|WS"',
    branches: [],
    remediation: [
      'Open Windows Subsystem for Android Settings -> System -> Graphics and performance.',
      'Change Graphics preference from High performance (discrete GPU) to Power saving or Specific GPU.',
      'Click Turn off Windows Subsystem for Android and relaunch.'
    ]
  },
  {
    id: 'startup-ramdisk-corrupt',
    title: 'Initrd Ramdisk & SELinux Policy Integrity',
    category: 'startup',
    symptom: 'vmmemWSA process terminates within 3 seconds of launch.',
    validationStep: 'Verify integrity of Tools\initrd.img in your WSA installation directory.',
    powershellCommand: 'Get-Item "C:\WSA\Tools\initrd.img" | Select-String "Length"',
    branches: [],
    remediation: [
      'Ensure initrd.img is repacked with SVR4 portable CPIO header (magic 070701).',
      'Verify that overlay.d/sbin/init-ld.xz and stub.xz exist inside ramdisk.',
      'Download a fresh prebuilt verified package from the Downloads portal.'
    ],
    relatedDocs: [
      { title: 'Architecture Specification', url: '/docs/getting-started/ARCHITECTURE' }
    ]
  },

  // --- PLAY INTEGRITY CATEGORY ---
  {
    id: 'integrity-start',
    title: 'Google Play Integrity & CTS Profile Diagnostics',
    category: 'integrity',
    symptom: 'Banking, UPI, or streaming apps fail device attestation or show Device Not Certified in Play Store.',
    validationStep: 'Verify if Zygisk is enabled and PlayIntegrityFix module is loaded in Magisk.',
    powershellCommand: 'adb shell "su -c magisk --version"',
    branches: [
      {
        label: 'Fails MEETS_DEVICE_INTEGRITY (Attestation blocked)',
        nextNodeId: 'integrity-meets-device-fail'
      },
      {
        label: 'Google Play Services Root Detection',
        nextNodeId: 'integrity-gms-attestation'
      }
    ],
    remediation: [
      'Follow the Play Integrity setup guide to install PlayIntegrityFix module in Magisk.',
      'Enable Enforce DenyList in Magisk settings for target banking applications.'
    ],
    relatedDocs: [
      { title: 'Play Integrity Setup Guide', url: '/docs/configuration/play-integrity-setup' }
    ],
    relatedCompat: [
      { title: 'PhonePe Workaround Guide', url: '/compatibility' },
      { title: 'Paytm Workaround Guide', url: '/compatibility' }
    ]
  },
  {
    id: 'integrity-meets-device-fail',
    title: 'Fix MEETS_DEVICE_INTEGRITY Failure',
    category: 'integrity',
    symptom: 'Play Integrity API Checker reports NO_INTEGRITY or MEETS_BASIC_INTEGRITY only.',
    validationStep: 'Verify PlayIntegrityFix module installation inside Magisk.',
    powershellCommand: 'adb shell "su -c ls /data/adb/modules/playintegrityfix"',
    branches: [],
    remediation: [
      'Open Magisk app on WSA -> Modules -> Install from storage.',
      'Install the latest PlayIntegrityFix zip release.',
      'Do not reboot immediately; configure DenyList first.'
    ],
    relatedDocs: [
      { title: 'Play Integrity Setup Guide', url: '/docs/configuration/play-integrity-setup' }
    ]
  },
  {
    id: 'integrity-gms-attestation',
    title: 'Configure Magisk DenyList for Google Play Services',
    category: 'integrity',
    symptom: 'Google Play Store displays Device is not certified under About settings.',
    validationStep: 'Verify Magisk DenyList processes for GMS.',
    powershellCommand: 'adb shell "su -c magisk --denylist ls"',
    branches: [],
    remediation: [
      'In Magisk Settings, enable Enforce DenyList.',
      'Click Configure DenyList -> Top right 3-dot menu -> Check Show system apps.',
      'Search for Google Play Services (com.google.android.gms) and check all processes.',
      'Clear Google Play Store storage cache and restart WSA.'
    ],
    relatedDocs: [
      { title: 'Play Integrity Setup Guide', url: '/docs/configuration/play-integrity-setup' }
    ]
  },

  // --- ADB CONNECTION CATEGORY ---
  {
    id: 'adb-start',
    title: 'Android Debug Bridge (ADB) Connection Diagnostics',
    category: 'adb',
    symptom: 'adb connect 127.0.0.1:58526 fails or returns cannot connect or unauthorized.',
    validationStep: 'Check if WSA Developer options are turned on and ADB port 58526 is listening.',
    powershellCommand: 'Test-NetConnection -ComputerName 127.0.0.1 -Port 58526',
    branches: [
      {
        label: 'TcpTestSucceeded is False (Port Closed)',
        nextNodeId: 'adb-port-offline'
      },
      {
        label: 'Port Open but Device Shows unauthorized',
        nextNodeId: 'adb-unauthorized'
      }
    ],
    remediation: [
      'Open Windows Subsystem for Android Settings -> Advanced settings -> Toggle Developer options ON.'
    ]
  },
  {
    id: 'adb-port-offline',
    title: 'ADB Port 58526 Connection Refused',
    category: 'adb',
    symptom: 'adb connect 127.0.0.1:58526 outputs: cannot connect to 127.0.0.1:58526: No connection could be made.',
    validationStep: 'Verify WSA is running and Developer options are active.',
    powershellCommand: 'Get-Process WsaClient -ErrorAction SilentlyContinue',
    branches: [],
    remediation: [
      'Launch any Android app or open WSA Settings to start the container.',
      'In WSA Settings -> Advanced settings -> Turn Developer options ON.',
      'Run: adb connect 127.0.0.1:58526'
    ]
  },
  {
    id: 'adb-unauthorized',
    title: 'ADB Device Authorization / Unauthorized State',
    category: 'adb',
    symptom: 'adb devices lists 127.0.0.1:58526 unauthorized.',
    validationStep: 'Check for adbkey and adbkey.pub in %USERPROFILE%\.android\.',
    powershellCommand: 'Test-Path "$env:USERPROFILE\.android\adbkey.pub"',
    branches: [],
    remediation: [
      'Restart adb server: adb kill-server; adb start-server',
      'Reconnect: adb connect 127.0.0.1:58526',
      'Look for the Allow USB debugging dialog on the Android screen and check Always allow from this computer -> Allow.'
    ]
  },

  // --- ROOT DETECTION CATEGORY ---
  {
    id: 'root-start',
    title: 'Root Detection & Banking App Cloaking Diagnostics',
    category: 'root',
    symptom: 'Banking, payment, or enterprise apps detect root access and refuse to run.',
    validationStep: 'Verify Magisk app package hiding, DenyList, and USB debugging status.',
    powershellCommand: 'adb shell "pm list packages | grep -E \"magisk|topjohnwu\""',
    branches: [
      {
        label: 'App Closes on Launch (Root Detected)',
        nextNodeId: 'root-app-detection'
      },
      {
        label: 'USB Debugging Detected by App (e.g. SBI YONO)',
        nextNodeId: 'root-usb-debug-detection'
      }
    ],
    remediation: [
      'Hide the Magisk app with a randomized package name.',
      'Enable Zygisk and add app to Magisk DenyList.',
      'Install Shamiko module in blacklist mode.'
    ],
    relatedCompat: [
      { title: 'SBI YONO Compatibility Guide', url: '/compatibility' },
      { title: 'PhonePe Compatibility Guide', url: '/compatibility' }
    ]
  },
  {
    id: 'root-app-detection',
    title: 'Hide Magisk App & Enforce DenyList',
    category: 'root',
    symptom: 'Banking app displays Root detected or Security violation error.',
    validationStep: 'Verify if Magisk app is still visible under com.topjohnwu.magisk.',
    powershellCommand: 'adb shell "su -c magisk --denylist status"',
    branches: [
      {
        label: 'App still detects USB debugging',
        nextNodeId: 'root-usb-debug-detection'
      }
    ],
    remediation: [
      'In Magisk Settings, tap Hide the Magisk app -> enter a name like Settings Manager.',
      'Enable Enforce DenyList -> Configure DenyList -> Check your banking app processes.',
      'If app still detects root, install the Shamiko Magisk module.'
    ],
    relatedDocs: [
      { title: 'Play Integrity Setup Guide', url: '/docs/configuration/play-integrity-setup' }
    ],
    relatedCompat: [
      { title: 'Paytm Compatibility Guide', url: '/compatibility' }
    ]
  },
  {
    id: 'root-usb-debug-detection',
    title: 'Disable USB Debugging for Strict Banking Apps',
    category: 'root',
    symptom: 'Apps such as SBI YONO immediately close or display USB Debugging Detected.',
    validationStep: 'Check WSA Developer Options status.',
    powershellCommand: 'adb shell "settings get global adb_enabled"',
    branches: [],
    remediation: [
      'Open Windows Subsystem for Android Settings -> Advanced settings.',
      'Toggle Developer options to OFF.',
      'Click Turn off Windows Subsystem for Android to commit.',
      'Relaunch the banking app.'
    ],
    relatedCompat: [
      { title: 'SBI YONO Compatibility Record', url: '/compatibility' }
    ]
  }
];
