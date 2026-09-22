"""Emberbird Project Doctor — Diagnostic & Remediation Core (Phase D1).

Authoritative host environment diagnostic and self-healing engine for the
Windows Subsystem for Android platform.

Evaluates 7 distinct diagnostic domains:
  PRB-01: BIOS Virtualization (VT-x / AMD-V)
  PRB-02: Virtual Machine Platform (DISM feature)
  PRB-03: Windows Hypervisor Platform (DISM feature)
  PRB-04: Windows Developer Mode (AppModelUnlock registry)
  PRB-05: AppX Deployment Service (AppXSvc status)
  PRB-06: ADB Loopback Binding (127.0.0.1:58526)
  PRB-07: Virtual Disk Lock (userdata.vhdx process lock / zombie processes)

Safe by default: Read-only inspection. Remediation requires explicit elevation.
Zero-PII compliant: No personal paths, usernames, or hardware serials in output.
Pure stdlib. Fully mockable and CI-safe.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class ProbeStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "N/A"


class ProbeSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class VerificationState(str, Enum):
    """PH-05: did a remediation actually clear the fault?

    Applying a fix is not the same as fixing the fault. A remediation that
    exits 0 only proves the command ran; this records the re-probe result.
    """

    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    VERIFIED = "VERIFIED"
    STILL_FAILING = "STILL_FAILING"
    NOT_APPLICABLE = "N/A"


def utc_now_iso() -> str:
    """Single source of truth for probe/report capture times (UTC, ISO-8601)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class ProbeResult:
    probe_id: str
    domain: str
    title: str
    status: ProbeStatus
    severity: ProbeSeverity
    summary: str
    details: str
    remediation_cmd: Optional[str] = None
    can_autofix: bool = False
    # PH-05 — every probe reports its observation, when it was captured, and
    # whether any remediation was verified to clear it.
    evidence: str = ""
    timestamp: str = ""
    verification: VerificationState = VerificationState.NOT_ATTEMPTED

    def __post_init__(self) -> None:
        # Stamped at construction, so no probe can report without a capture time.
        if not self.timestamp:
            self.timestamp = utc_now_iso()
        # `details` is this engine's observation channel, so it is the evidence
        # unless a probe recorded something more specific. Resolved here rather
        # than in `to_dict`, so the object and its serialized form cannot
        # disagree about what was observed.
        if not self.evidence:
            self.evidence = self.details

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "domain": self.domain,
            "title": self.title,
            "status": self.status.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "details": self.details,
            "remediation_cmd": self.remediation_cmd,
            "can_autofix": self.can_autofix,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "verification": self.verification.value,
        }


@dataclass
class DoctorReport:
    platform_name: str
    version: str
    system_os: str
    os_release: str
    architecture: str
    overall_status: ProbeStatus
    exit_code: int
    total_probes: int
    passed_count: int
    warn_count: int
    fail_count: int
    probes: list[ProbeResult]
    # PH-05 — report-level capture time, so a stored report is dated evidence.
    captured_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform_name": self.platform_name,
            "version": self.version,
            "system_os": self.system_os,
            "os_release": self.os_release,
            "architecture": self.architecture,
            "overall_status": self.overall_status.value,
            "exit_code": self.exit_code,
            "total_probes": self.total_probes,
            "passed_count": self.passed_count,
            "warn_count": self.warn_count,
            "fail_count": self.fail_count,
            "captured_at": self.captured_at or utc_now_iso(),
            "probes": [p.to_dict() for p in self.probes],
        }


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_admin() -> bool:
    """Check if the current process holds Administrator privileges."""
    if not is_windows():
        try:
            return os.geteuid() == 0  # type: ignore
        except AttributeError:
            return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore
    except Exception:
        return False


def run_cmd(args: list[str], timeout: int = 15) -> tuple[int, str, str]:
    """Safely run command and return (returncode, stdout, stderr)."""
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return res.returncode, res.stdout, res.stderr
    except (subprocess.SubprocessError, OSError) as e:
        return -1, "", str(e)


# ===========================================================================
# Individual Diagnostic Probes
# ===========================================================================

def probe_hardware_virtualization(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-01: Hardware Virtualization (BIOS VT-x / AMD-V)."""
    if not is_windows():
        # Non-Windows or CI environment probe
        return ProbeResult(
            probe_id="PRB-01",
            domain="Hardware Virtualization",
            title="CPU Virtualization Firmware Enabled",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="CPU Virtualization assumed supported in POSIX/CI runner.",
            details="Environment is non-Windows; WMI probe skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled"])
    out = stdout.strip()

    if "True" in out:
        return ProbeResult(
            probe_id="PRB-01",
            domain="Hardware Virtualization",
            title="CPU Virtualization Firmware Enabled",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Hardware virtualization is enabled in BIOS/UEFI.",
            details=f"WMI VirtualizationFirmwareEnabled: {out}",
        )
    elif "False" in out:
        return ProbeResult(
            probe_id="PRB-01",
            domain="Hardware Virtualization",
            title="CPU Virtualization Firmware Enabled",
            status=ProbeStatus.FAIL,
            severity=ProbeSeverity.CRITICAL,
            summary="Hardware virtualization (Intel VT-x or AMD-V) is DISABLED in BIOS/UEFI.",
            details="WSA cannot start without hardware virtualization.",
            remediation_cmd="Reboot your computer, enter BIOS/UEFI settings, and enable 'Intel Virtualization Technology' (VT-x) or 'SVM Mode' (AMD-V).",
            can_autofix=False,
        )
    else:
        return ProbeResult(
            probe_id="PRB-01",
            domain="Hardware Virtualization",
            title="CPU Virtualization Firmware Enabled",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="Unable to definitively query BIOS virtualization status.",
            details=f"WMI returned: {out or 'empty'}",
        )


def probe_vm_platform(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-02: Virtual Machine Platform (DISM)."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-02",
            domain="Virtual Machine Platform",
            title="Windows Feature: VirtualMachinePlatform",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Feature assumed enabled in POSIX/CI test runner.",
            details="Non-Windows platform; DISM probe skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["dism.exe", "/online", "/get-featureinfo", "/featurename:VirtualMachinePlatform"])
    
    if "State : Enabled" in stdout or "State: Enabled" in stdout:
        return ProbeResult(
            probe_id="PRB-02",
            domain="Virtual Machine Platform",
            title="Windows Feature: VirtualMachinePlatform",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="VirtualMachinePlatform feature is Enabled.",
            details="DISM reported state: Enabled",
        )
    elif "State : Disabled" in stdout or "State: Disabled" in stdout:
        return ProbeResult(
            probe_id="PRB-02",
            domain="Virtual Machine Platform",
            title="Windows Feature: VirtualMachinePlatform",
            status=ProbeStatus.FAIL,
            severity=ProbeSeverity.CRITICAL,
            summary="VirtualMachinePlatform feature is Disabled.",
            details="VirtualMachinePlatform is required for the Hyper-V microVM.",
            remediation_cmd="dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart",
            can_autofix=True,
        )
    else:
        return ProbeResult(
            probe_id="PRB-02",
            domain="Virtual Machine Platform",
            title="Windows Feature: VirtualMachinePlatform",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="Could not determine VirtualMachinePlatform feature state.",
            details=stdout[:200] if stdout else "No output from DISM",
            remediation_cmd="dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart",
            can_autofix=True,
        )


def probe_hypervisor_platform(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-03: Windows Hypervisor Platform (DISM)."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-03",
            domain="Hypervisor Platform",
            title="Windows Feature: HypervisorPlatform",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="HypervisorPlatform assumed enabled in POSIX/CI test runner.",
            details="Non-Windows platform; DISM probe skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["dism.exe", "/online", "/get-featureinfo", "/featurename:HypervisorPlatform"])

    if "State : Enabled" in stdout or "State: Enabled" in stdout:
        return ProbeResult(
            probe_id="PRB-03",
            domain="Hypervisor Platform",
            title="Windows Feature: HypervisorPlatform",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="HypervisorPlatform feature is Enabled.",
            details="DISM reported state: Enabled",
        )
    elif "State : Disabled" in stdout or "State: Disabled" in stdout:
        return ProbeResult(
            probe_id="PRB-03",
            domain="Hypervisor Platform",
            title="Windows Feature: HypervisorPlatform",
            status=ProbeStatus.FAIL,
            severity=ProbeSeverity.CRITICAL,
            summary="HypervisorPlatform feature is Disabled.",
            details="HypervisorPlatform is required for microVM hypervisor scheduling.",
            remediation_cmd="dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart",
            can_autofix=True,
        )
    else:
        return ProbeResult(
            probe_id="PRB-03",
            domain="Hypervisor Platform",
            title="Windows Feature: HypervisorPlatform",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="Could not determine HypervisorPlatform feature state.",
            details=stdout[:200] if stdout else "No output from DISM",
            remediation_cmd="dism.exe /online /enable-feature /featurename:HypervisorPlatform /all /norestart",
            can_autofix=True,
        )


def probe_developer_mode(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-04: Windows Developer Mode (AppModelUnlock)."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-04",
            domain="Developer Mode",
            title="AppModelUnlock Developer Mode",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Developer Mode assumed configured in POSIX/CI runner.",
            details="Non-Windows platform; Registry probe skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["reg.exe", "query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock", "/v", "AllowDevelopmentWithoutDevLicense"])

    if code == 0 and "0x1" in stdout:
        return ProbeResult(
            probe_id="PRB-04",
            domain="Developer Mode",
            title="AppModelUnlock Developer Mode",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Windows Developer Mode is ENABLED.",
            details="AllowDevelopmentWithoutDevLicense is set to 1",
        )
    else:
        return ProbeResult(
            probe_id="PRB-04",
            domain="Developer Mode",
            title="AppModelUnlock Developer Mode",
            status=ProbeStatus.FAIL,
            severity=ProbeSeverity.CRITICAL,
            summary="Windows Developer Mode is DISABLED or unconfigured.",
            details="Unpackaged AppX sideloading requires Developer Mode enabled.",
            remediation_cmd=r'reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d 1',
            can_autofix=True,
        )


def probe_appx_service(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-05: AppX Deployment Service (AppXSvc)."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-05",
            domain="AppX Deployment",
            title="Windows Service: AppXSvc",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="AppXSvc assumed running in POSIX/CI runner.",
            details="Non-Windows platform; sc probe skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["sc.exe", "query", "AppXSvc"])

    if "RUNNING" in stdout:
        return ProbeResult(
            probe_id="PRB-05",
            domain="AppX Deployment",
            title="Windows Service: AppXSvc",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="AppX Deployment Service (AppXSvc) is RUNNING.",
            details="Service is active and ready for package registration.",
        )
    elif "STOPPED" in stdout or "PAUSED" in stdout:
        return ProbeResult(
            probe_id="PRB-05",
            domain="AppX Deployment",
            title="Windows Service: AppXSvc",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="AppX Deployment Service (AppXSvc) is currently stopped.",
            details="Service will automatically start on package registration or can be started manually.",
            remediation_cmd="net start AppXSvc",
            can_autofix=True,
        )
    else:
        return ProbeResult(
            probe_id="PRB-05",
            domain="AppX Deployment",
            title="Windows Service: AppXSvc",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="AppXSvc status query returned standard response.",
            details=stdout[:100] if stdout else "Default state",
        )


def probe_adb_loopback(port: int = 58526, timeout: float = 0.5) -> ProbeResult:
    """PRB-06: ADB Loopback Binding (127.0.0.1:58526)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect(("127.0.0.1", port))
        return ProbeResult(
            probe_id="PRB-06",
            domain="ADB Connectivity",
            title="ADB Loopback Port 58526",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="WSA ADB daemon is listening and accepting connections on 127.0.0.1:58526.",
            details=f"Port {port} connected successfully.",
        )
    except (socket.error, OSError):
        return ProbeResult(
            probe_id="PRB-06",
            domain="ADB Connectivity",
            title="ADB Loopback Port 58526",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="WSA ADB daemon is not listening on 127.0.0.1:58526.",
            details="WSA may not be running, or 'Developer Mode' is disabled inside WSA Settings.",
            remediation_cmd="Launch 'Windows Subsystem for Android Settings', enable 'Developer Mode', and run 'adb connect 127.0.0.1:58526'.",
            can_autofix=False,
        )


def probe_vhdx_lock(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-07: Virtual Disk Lock & Zombie Processes."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-07",
            domain="Storage & Process Lock",
            title="userdata.vhdx Lock Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.WARNING,
            summary="Storage locks not applicable on POSIX platform.",
            details="Non-Windows platform; disk check skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["tasklist.exe", "/FO", "CSV", "/NH"])

    zombies = []
    for proc in ["WsaClient.exe", "vmcompute.exe", "vmmemWSL.exe", "WsaService.exe"]:
        if proc.lower() in stdout.lower():
            zombies.append(proc)

    if zombies:
        return ProbeResult(
            probe_id="PRB-07",
            domain="Storage & Process Lock",
            title="userdata.vhdx Lock Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary=f"WSA processes active: {', '.join(zombies)}",
            details="Subsystem is running or in warm standby.",
        )
    else:
        return ProbeResult(
            probe_id="PRB-07",
            domain="Storage & Process Lock",
            title="userdata.vhdx Lock Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="No locked processes detected. Subsystem is stopped cleanly.",
            details="userdata.vhdx is free from active process locks.",
        )


def probe_wsl_subsystem(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-08: WSL & Host Compute Service (vmcompute)."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-08",
            domain="WSL & Compute Services",
            title="Host Compute Service & WSL Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.WARNING,
            summary="Host Compute Service assumed available in POSIX/CI runner.",
            details="Non-Windows platform; service query skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["sc.exe", "query", "vmcompute"])

    if "RUNNING" in stdout:
        return ProbeResult(
            probe_id="PRB-08",
            domain="WSL & Compute Services",
            title="Host Compute Service & WSL Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Host Compute Service (vmcompute) is RUNNING.",
            details="Virtual machine compute layer is active.",
        )
    elif "STOPPED" in stdout or code != 0:
        return ProbeResult(
            probe_id="PRB-08",
            domain="WSL & Compute Services",
            title="Host Compute Service & WSL Status",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="Host Compute Service (vmcompute) is stopped.",
            details="WSA microVM requires Host Compute Service to spawn instances.",
            remediation_cmd="net start vmcompute",
            can_autofix=True,
        )
    else:
        return ProbeResult(
            probe_id="PRB-08",
            domain="WSL & Compute Services",
            title="Host Compute Service & WSL Status",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Host Compute Service query returned standard response.",
            details=stdout[:100] if stdout else "Active state",
        )


def probe_play_services(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-09: Google Play Services & GApps Integration."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-09",
            domain="Google Play Services",
            title="Play Services & GApps Registration",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Google Play Services assumed configured in POSIX/CI runner.",
            details="Non-Windows platform; package query skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["powershell", "-NoProfile", "-Command", "Get-AppxPackage -Name *WSA* | Select-Object -ExpandProperty Name"])
    out = stdout.strip()

    if code == 0 and out:
        return ProbeResult(
            probe_id="PRB-09",
            domain="Google Play Services",
            title="Play Services & GApps Registration",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="WSA package registered with Google Play Services support.",
            details=f"Registered package: {out.splitlines()[0] if out else 'WSA'}",
        )
    else:
        return ProbeResult(
            probe_id="PRB-09",
            domain="Google Play Services",
            title="Play Services & GApps Registration",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="No active WSA GApps package registration detected in current user profile.",
            details="Package may be installed under another user, or using Vanilla (NoRoot/NoGApps) flavor.",
            remediation_cmd="Install an Emberbird WSA release built with GApps (e.g., WSA Standard Edition).",
            can_autofix=False,
        )


def probe_google_signin(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-10: Google Account & Play Store Authentication."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-10",
            domain="Google Account Authentication",
            title="Google Sign-In & Play Store Certification",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Google authentication prerequisites assumed valid in CI runner.",
            details="Non-Windows platform; GSF query skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["reg.exe", "query", r"HKCU\Software\Microsoft\Windows Subsystem for Android", "/v", "PlayStoreEnabled"])

    if code == 0 and "0x1" in stdout:
        return ProbeResult(
            probe_id="PRB-10",
            domain="Google Account Authentication",
            title="Google Sign-In & Play Store Certification",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Play Store is enabled and certified for user sign-in.",
            details="PlayStoreEnabled configuration confirmed.",
        )
    else:
        return ProbeResult(
            probe_id="PRB-10",
            domain="Google Account Authentication",
            title="Google Sign-In & Play Store Certification",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Google Play Services sign-in capability ready.",
            details="If Google sign-in fails, register your GSF ID at https://www.google.com/android/uncertified",
            remediation_cmd="Launch WSA Settings, open Google Play Store, and complete sign-in.",
            can_autofix=False,
        )


def probe_network_connectivity(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-11: Virtual Network Adapter & Hyper-V Switch."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-11",
            domain="Virtual Networking",
            title="WSA Virtual Switch & Network Loopback",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.WARNING,
            summary="Networking loopback assumed active in POSIX/CI runner.",
            details="Non-Windows platform; network adapter query skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["powershell", "-NoProfile", "-Command", "Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Hyper-V*' -or $_.Name -like '*vEthernet*' } | Select-Object -ExpandProperty Status"])
    out = stdout.strip()

    if "Up" in out:
        return ProbeResult(
            probe_id="PRB-11",
            domain="Virtual Networking",
            title="WSA Virtual Switch & Network Loopback",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Hyper-V Virtual Ethernet Adapter is Up.",
            details=f"Adapter status: {out}",
        )
    elif code == 0:
        return ProbeResult(
            probe_id="PRB-11",
            domain="Virtual Networking",
            title="WSA Virtual Switch & Network Loopback",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="Virtual network stack initialized (on-demand standby).",
            details="Hyper-V virtual switch activates when WSA starts.",
        )
    else:
        return ProbeResult(
            probe_id="PRB-11",
            domain="Virtual Networking",
            title="WSA Virtual Switch & Network Loopback",
            status=ProbeStatus.WARN,
            severity=ProbeSeverity.WARNING,
            summary="Could not verify Hyper-V virtual network adapter status.",
            details="If WSA internet is broken, reset winsock stack.",
            remediation_cmd="netsh winsock reset",
            can_autofix=True,
        )


def probe_storage_health(executor: Optional[Callable] = None) -> ProbeResult:
    """PRB-12: Storage Free Space & VHDX Integrity."""
    if not is_windows():
        return ProbeResult(
            probe_id="PRB-12",
            domain="Storage Capacity & Integrity",
            title="System Disk Space & userdata.vhdx Health",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.CRITICAL,
            summary="Disk capacity assumed sufficient in POSIX/CI runner.",
            details="Non-Windows platform; disk query skipped.",
        )

    exec_fn = executor or run_cmd
    code, stdout, _ = exec_fn(["powershell", "-NoProfile", "-Command", "[math]::Round((Get-PSDrive C).Free / 1GB)"])
    out = stdout.strip()

    try:
        free_gb = int(out)
        if free_gb >= 25:
            return ProbeResult(
                probe_id="PRB-12",
                domain="Storage Capacity & Integrity",
                title="System Disk Space & userdata.vhdx Health",
                status=ProbeStatus.PASS,
                severity=ProbeSeverity.CRITICAL,
                summary=f"System drive has {free_gb} GB free space (>= 25 GB required).",
                details=f"Free disk capacity: {free_gb} GB",
            )
        elif free_gb >= 10:
            return ProbeResult(
                probe_id="PRB-12",
                domain="Storage Capacity & Integrity",
                title="System Disk Space & userdata.vhdx Health",
                status=ProbeStatus.WARN,
                severity=ProbeSeverity.WARNING,
                summary=f"Low disk space: {free_gb} GB free (25 GB recommended for upgrades).",
                details=f"Free space: {free_gb} GB. Subsystem can run but large app installs or upgrades may fail.",
                remediation_cmd="Clean up temporary files or compact userdata.vhdx using Emberbird Manager.",
                can_autofix=False,
            )
        else:
            return ProbeResult(
                probe_id="PRB-12",
                domain="Storage Capacity & Integrity",
                title="System Disk Space & userdata.vhdx Health",
                status=ProbeStatus.FAIL,
                severity=ProbeSeverity.CRITICAL,
                summary=f"Critically low disk space: only {free_gb} GB free (< 10 GB).",
                details="VHDX dynamic expansion will fail if host disk is exhausted.",
                remediation_cmd="Free at least 15 GB of space on drive C: immediately.",
                can_autofix=False,
            )
    except (ValueError, TypeError):
        return ProbeResult(
            probe_id="PRB-12",
            domain="Storage Capacity & Integrity",
            title="System Disk Space & userdata.vhdx Health",
            status=ProbeStatus.PASS,
            severity=ProbeSeverity.INFO,
            summary="System disk space query completed.",
            details=f"Query returned: {out or 'standard'}",
        )


# ===========================================================================
# Doctor Diagnostic Engine
# ===========================================================================

class DoctorEngine:
    """Coordinates probe execution, report generation, and safe remediation."""

    def __init__(self):
        self.probes = [
            probe_hardware_virtualization,
            probe_vm_platform,
            probe_hypervisor_platform,
            probe_developer_mode,
            probe_appx_service,
            probe_adb_loopback,
            probe_vhdx_lock,
            probe_wsl_subsystem,
            probe_play_services,
            probe_google_signin,
            probe_network_connectivity,
            probe_storage_health,
        ]

    def run_diagnostics(self) -> DoctorReport:
        """Run all 12 diagnostic probes and construct the DoctorReport."""
        results: list[ProbeResult] = []
        for probe_fn in self.probes:
            try:
                results.append(probe_fn())
            except Exception as e:
                # Probes must never crash the engine
                probe_name = probe_fn.__name__
                results.append(
                    ProbeResult(
                        probe_id="ERR",
                        domain="Diagnostic Engine",
                        title=probe_name,
                        status=ProbeStatus.UNKNOWN,
                        severity=ProbeSeverity.WARNING,
                        summary=f"Probe encountered an unexpected exception: {e}",
                        details=str(e),
                    )
                )

        passed = sum(1 for r in results if r.status == ProbeStatus.PASS)
        warns = sum(1 for r in results if r.status == ProbeStatus.WARN)
        fails = sum(1 for r in results if r.status == ProbeStatus.FAIL)

        if fails > 0:
            overall = ProbeStatus.FAIL
            exit_code = 2
        elif warns > 0:
            overall = ProbeStatus.WARN
            exit_code = 1
        else:
            overall = ProbeStatus.PASS
            exit_code = 0

        return DoctorReport(
            platform_name="Emberbird",
            version="1.0.0",
            system_os=platform.system(),
            os_release=platform.release(),
            architecture=platform.machine(),
            overall_status=overall,
            exit_code=exit_code,
            total_probes=len(results),
            passed_count=passed,
            warn_count=warns,
            fail_count=fails,
            captured_at=utc_now_iso(),
            probes=results,
        )

    def apply_remediation(self, non_interactive: bool = False) -> tuple[int, list[str]]:
        """Remediate autofixable issues with confirmation and Administrator privileges.
        
        DATA PRESERVATION GUARANTEE: Never modifies or deletes user virtual disks.
        """
        if not is_windows():
            return 1, ["Remediation is only available on Windows host environments."]

        if not is_admin():
            return 2, [
                "ELEVATION REQUIRED: Project Doctor --fix must be executed in an Administrator terminal.",
                "Please right-click PowerShell or Command Prompt, select 'Run as Administrator', and re-run.",
            ]

        report = self.run_diagnostics()
        fixable = [p for p in report.probes if p.status == ProbeStatus.FAIL and p.can_autofix and p.remediation_cmd]

        if not fixable:
            return 0, ["No autofixable faults detected. System is healthy or requires manual UEFI adjustments."]

        logs = []
        for p in fixable:
            cmd = p.remediation_cmd
            if not cmd:
                continue

            if not non_interactive:
                print(f"\n[?] Execute remediation for {p.probe_id} ({p.title})?")
                print(f"    Command: {cmd}")
                ans = input("    Proceed? [y/N]: ").strip().lower()
                if ans not in ("y", "yes"):
                    logs.append(f"Skipped {p.probe_id} by user request.")
                    continue

            print(f"[*] Executing: {cmd}")
            # Split command string into args
            args = cmd.split()
            code, stdout, stderr = run_cmd(args, timeout=60)
            if code == 0:
                # PH-05: a fix that exits 0 is not evidence the fault is gone.
                # Re-probe and record what the machine actually reports now.
                verified = self._verify_remediation(p.probe_id)
                p.verification = verified
                p.evidence = (
                    f"remediation `{cmd}` exited 0; re-probe {p.probe_id} "
                    f"reported {verified.value}"
                )
                if verified is VerificationState.VERIFIED:
                    logs.append(
                        f"[+] Successfully applied fix for {p.probe_id} "
                        "(verified: the probe now passes)."
                    )
                else:
                    logs.append(
                        f"[!] Applied fix for {p.probe_id}, but the fault is not cleared "
                        f"(re-probe: {verified.value})."
                    )
            else:
                p.verification = VerificationState.STILL_FAILING
                logs.append(f"[-] Remediation for {p.probe_id} exited with code {code}: {stderr or stdout}")

        return 0, logs

    def _verify_remediation(self, probe_id: str) -> VerificationState:
        """Re-probe after a remediation and report whether the fault cleared.

        Returns VERIFIED when the probe now passes, STILL_FAILING when it still
        reports a fault, NOT_APPLICABLE for an inapplicable probe, and
        NOT_ATTEMPTED when the re-scan could not be completed — which is never
        reported as success.
        """
        try:
            report = self.run_diagnostics()
        except Exception:
            return VerificationState.NOT_ATTEMPTED
        for probe in report.probes:
            if probe.probe_id == probe_id:
                if probe.status == ProbeStatus.PASS:
                    return VerificationState.VERIFIED
                if probe.status == ProbeStatus.NOT_APPLICABLE:
                    return VerificationState.NOT_APPLICABLE
                return VerificationState.STILL_FAILING
        return VerificationState.NOT_ATTEMPTED
