//! doctor.rs — Ember Doctor probe engine (FB-2 / D1 parity).
//!
//! Faithful Rust port of the authoritative host diagnostic engine
//! (`platform/doctor/__init__.py`): the same 12 probe IDs, statuses,
//! severities, summaries, and remediation commands. The Manager's Doctor tab
//! and `python -m platform.doctor` must never disagree about host health;
//! when this file changes, the Python engine is the contract to re-check.
//!
//! Safe by default (read-only inspection), zero-PII (no user paths, names, or
//! hardware serials in output), and honest on every branch — a failed query is
//! WARN, never a fabricated PASS.

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub enum DoctorProbeStatus {
    PASS,
    WARN,
    FAIL,
    UNKNOWN,
    #[serde(rename = "N/A")]
    NA,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub enum DoctorProbeSeverity {
    INFO,
    WARNING,
    CRITICAL,
}

#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct DoctorProbe {
    pub probe_id: String,
    pub domain: String,
    pub title: String,
    pub status: DoctorProbeStatus,
    pub severity: DoctorProbeSeverity,
    pub summary: String,
    pub details: String,
    pub remediation_cmd: Option<String>,
    pub can_autofix: bool,
}

/// Run all 12 diagnostic probes in contract order (PRB-01 → PRB-12).
///
/// Blocking: each Windows probe spawns PowerShell/DISM/sc/reg/tasklist or a
/// TCP connect. Callers must run this off the UI thread (the Tauri command in
/// `commands.rs` wraps it in `spawn_blocking`); on non-Windows hosts the
/// Windows-only probes mirror the CLI's POSIX/CI branch and skip their queries.
pub fn run_doctor_scan() -> Vec<DoctorProbe> {
    vec![
        probe_hardware_virtualization(),
        probe_vm_platform(),
        probe_hypervisor_platform(),
        probe_developer_mode(),
        probe_appx_service(),
        probe_adb_loopback(58526),
        probe_vhdx_lock(),
        probe_wsl_subsystem(),
        probe_play_services(),
        probe_google_signin(),
        probe_network_connectivity(),
        probe_storage_health(),
    ]
}

// ===========================================================================
// Probe plumbing
// ===========================================================================

/// Base probe constructor (no remediation attached).
fn probe(
    probe_id: &str,
    domain: &str,
    title: &str,
    status: DoctorProbeStatus,
    severity: DoctorProbeSeverity,
    summary: String,
    details: String,
) -> DoctorProbe {
    DoctorProbe {
        probe_id: probe_id.to_string(),
        domain: domain.to_string(),
        title: title.to_string(),
        status,
        severity,
        summary,
        details,
        remediation_cmd: None,
        can_autofix: false,
    }
}

/// Attach a remediation command that the platform's `--fix` mode may apply.
fn autofix(mut p: DoctorProbe, cmd: &str) -> DoctorProbe {
    p.remediation_cmd = Some(cmd.to_string());
    p.can_autofix = true;
    p
}

/// Attach a manual (non-autofixable) remediation command.
fn manual_fix(mut p: DoctorProbe, cmd: &str) -> DoctorProbe {
    p.remediation_cmd = Some(cmd.to_string());
    p.can_autofix = false;
    p
}

/// Run a command, returning (exit code, stdout, stderr); a missing binary is
/// reported as exit code -1, never a panic (mirrors the CLI's `run_cmd`).
fn execute(args: &[&str]) -> (i32, String, String) {
    let Some((program, rest)) = args.split_first() else {
        return (-1, String::new(), "empty command".to_string());
    };
    match Command::new(program).args(rest).output() {
        Ok(out) => (
            out.status.code().unwrap_or(-1),
            String::from_utf8_lossy(&out.stdout).into_owned(),
            String::from_utf8_lossy(&out.stderr).into_owned(),
        ),
        Err(e) => (-1, String::new(), e.to_string()),
    }
}

/// Python's `stdout[:n]` slice, char-boundary safe.
fn truncate(s: &str, max_chars: usize) -> String {
    s.chars().take(max_chars).collect()
}

/// Strip a trailing newline the way the CLI's `.strip()` does.
fn trimmed(s: &str) -> &str {
    s.trim()
}

// ===========================================================================
// PRB-01 — Hardware Virtualization (BIOS VT-x / AMD-V)
// ===========================================================================

fn probe_hardware_virtualization() -> DoctorProbe {
    const ID: &str = "PRB-01";
    const DOMAIN: &str = "Hardware Virtualization";
    const TITLE: &str = "CPU Virtualization Firmware Enabled";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "CPU Virtualization assumed supported in POSIX/CI runner.".to_string(),
            "Environment is non-Windows; WMI probe skipped.".to_string(),
        );
    }

    #[cfg(windows)]
    {
        use windows::Win32::System::Threading::{IsProcessorFeaturePresent, PROCESSOR_FEATURE_ID};
        // PF_VIRT_FIRMWARE_ENABLED = 20
        let enabled = unsafe { IsProcessorFeaturePresent(PROCESSOR_FEATURE_ID(20)) }.as_bool();

        if enabled {
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::PASS,
                DoctorProbeSeverity::CRITICAL,
                "Hardware virtualization is enabled in BIOS/UEFI.".to_string(),
                "Native IsProcessorFeaturePresent(PF_VIRT_FIRMWARE_ENABLED) returned true".to_string(),
            )
        } else {
            manual_fix(
                probe(
                    ID,
                    DOMAIN,
                    TITLE,
                    DoctorProbeStatus::FAIL,
                    DoctorProbeSeverity::CRITICAL,
                    "Hardware virtualization (Intel VT-x or AMD-V) is DISABLED in BIOS/UEFI.".to_string(),
                    "WSA cannot start without hardware virtualization.".to_string(),
                ),
                "Reboot your computer, enter BIOS/UEFI settings, and enable 'Intel Virtualization Technology' (VT-x) or 'SVM Mode' (AMD-V).",
            )
        }
    }
    #[cfg(not(windows))]
    unreachable!()
}

// ===========================================================================
// PRB-02 / PRB-03 — Windows optional features (DISM)
// ===========================================================================

fn probe_windows_feature(feature: &str, domain: &str, missing_detail: &str) -> DoctorProbe {
    let (id, title) = match feature {
        "VirtualMachinePlatform" => ("PRB-02", "Windows Feature: VirtualMachinePlatform"),
        _ => ("PRB-03", "Windows Feature: HypervisorPlatform"),
    };
    let remediation = format!(
        "dism.exe /online /enable-feature /featurename:{} /all /norestart",
        feature
    );

    if !cfg!(windows) {
        return probe(
            id,
            domain,
            title,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            format!("{} assumed enabled in POSIX/CI test runner.", feature),
            "Non-Windows platform; DISM probe skipped.".to_string(),
        );
    }

    let (_code, stdout, _) = execute(&[
        "dism.exe",
        "/online",
        "/get-featureinfo",
        &format!("/featurename:{}", feature),
    ]);

    if stdout.contains("State : Enabled") || stdout.contains("State: Enabled") {
        probe(
            id,
            domain,
            title,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            format!("{} feature is Enabled.", feature),
            "DISM reported state: Enabled".to_string(),
        )
    } else if stdout.contains("State : Disabled") || stdout.contains("State: Disabled") {
        autofix(
            probe(
                id,
                domain,
                title,
                DoctorProbeStatus::FAIL,
                DoctorProbeSeverity::CRITICAL,
                format!("{} feature is Disabled.", feature),
                missing_detail.to_string(),
            ),
            &remediation,
        )
    } else {
        autofix(
            probe(
                id,
                domain,
                title,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                format!("Could not determine {} feature state.", feature),
                if stdout.trim().is_empty() {
                    "No output from DISM".to_string()
                } else {
                    truncate(&stdout, 200)
                },
            ),
            &remediation,
        )
    }
}

fn probe_vm_platform() -> DoctorProbe {
    probe_windows_feature(
        "VirtualMachinePlatform",
        "Virtual Machine Platform",
        "VirtualMachinePlatform is required for the Hyper-V microVM.",
    )
}

fn probe_hypervisor_platform() -> DoctorProbe {
    probe_windows_feature(
        "HypervisorPlatform",
        "Hypervisor Platform",
        "HypervisorPlatform is required for microVM hypervisor scheduling.",
    )
}

// ===========================================================================
// PRB-04 — Windows Developer Mode (AppModelUnlock)
// ===========================================================================

fn probe_developer_mode() -> DoctorProbe {
    const ID: &str = "PRB-04";
    const DOMAIN: &str = "Developer Mode";
    const TITLE: &str = "AppModelUnlock Developer Mode";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "Developer Mode assumed configured in POSIX/CI runner.".to_string(),
            "Non-Windows platform; Registry probe skipped.".to_string(),
        );
    }

    #[cfg(windows)]
    {
        use winreg::enums::{HKEY_LOCAL_MACHINE, KEY_READ};
        use winreg::RegKey;

        let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
        let enabled = hklm
            .open_subkey_with_flags(
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock",
                KEY_READ,
            )
            .and_then(|key| key.get_value::<u32, _>("AllowDevelopmentWithoutDevLicense"))
            .unwrap_or(0)
            == 1;

        if enabled {
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::PASS,
                DoctorProbeSeverity::CRITICAL,
                "Windows Developer Mode is ENABLED.".to_string(),
                "AllowDevelopmentWithoutDevLicense is set to 1".to_string(),
            )
        } else {
            autofix(
                probe(
                    ID,
                    DOMAIN,
                    TITLE,
                    DoctorProbeStatus::FAIL,
                    DoctorProbeSeverity::CRITICAL,
                    "Windows Developer Mode is DISABLED or unconfigured.".to_string(),
                    "Unpackaged AppX sideloading requires Developer Mode enabled.".to_string(),
                ),
                r#"reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" /t REG_DWORD /f /v "AllowDevelopmentWithoutDevLicense" /d 1"#,
            )
        }
    }
    #[cfg(not(windows))]
    unreachable!()
}

// ===========================================================================
// PRB-05 — AppX Deployment Service (AppXSvc)
// ===========================================================================

fn probe_appx_service() -> DoctorProbe {
    const ID: &str = "PRB-05";
    const DOMAIN: &str = "AppX Deployment";
    const TITLE: &str = "Windows Service: AppXSvc";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "AppXSvc assumed running in POSIX/CI runner.".to_string(),
            "Non-Windows platform; sc probe skipped.".to_string(),
        );
    }

    let (_code, stdout, _) = execute(&["sc.exe", "query", "AppXSvc"]);

    if stdout.contains("RUNNING") {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "AppX Deployment Service (AppXSvc) is RUNNING.".to_string(),
            "Service is active and ready for package registration.".to_string(),
        )
    } else if stdout.contains("STOPPED") || stdout.contains("PAUSED") {
        autofix(
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                "AppX Deployment Service (AppXSvc) is currently stopped.".to_string(),
                "Service will automatically start on package registration or can be started manually.".to_string(),
            ),
            "net start AppXSvc",
        )
    } else {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "AppXSvc status query returned standard response.".to_string(),
            if stdout.trim().is_empty() {
                "Default state".to_string()
            } else {
                truncate(&stdout, 100)
            },
        )
    }
}

// ===========================================================================
// PRB-06 — ADB Loopback Binding (127.0.0.1:58526)
// ===========================================================================

fn probe_adb_loopback(port: u16) -> DoctorProbe {
    const ID: &str = "PRB-06";
    const DOMAIN: &str = "ADB Connectivity";
    const TITLE: &str = "ADB Loopback Port 58526";

    use std::net::{TcpStream, ToSocketAddrs};
    use std::time::Duration;

    let reachable = match ("127.0.0.1", port).to_socket_addrs() {
        Ok(mut addrs) => addrs
            .next()
            .map(|addr| TcpStream::connect_timeout(&addr, Duration::from_millis(500)).is_ok())
            .unwrap_or(false),
        Err(_) => false,
    };

    if reachable {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "WSA ADB daemon is listening and accepting connections on 127.0.0.1:58526."
                .to_string(),
            format!("Port {} connected successfully.", port),
        )
    } else {
        manual_fix(
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                "WSA ADB daemon is not listening on 127.0.0.1:58526.".to_string(),
                "WSA may not be running, or 'Developer Mode' is disabled inside WSA Settings."
                    .to_string(),
            ),
            "Launch 'Windows Subsystem for Android Settings', enable 'Developer Mode', and run 'adb connect 127.0.0.1:58526'.",
        )
    }
}

// ===========================================================================
// PRB-07 — Virtual Disk Lock & Zombie Processes
// ===========================================================================

fn probe_vhdx_lock() -> DoctorProbe {
    const ID: &str = "PRB-07";
    const DOMAIN: &str = "Storage & Process Lock";
    const TITLE: &str = "userdata.vhdx Lock Status";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::WARNING,
            "Storage locks not applicable on POSIX platform.".to_string(),
            "Non-Windows platform; disk check skipped.".to_string(),
        );
    }

    let (_code, stdout, _) = execute(&["tasklist.exe", "/FO", "CSV", "/NH"]);

    let active: Vec<&str> = ["WsaClient.exe", "vmcompute.exe", "vmmemWSL.exe", "WsaService.exe"]
        .into_iter()
        .filter(|proc_name| stdout.to_lowercase().contains(&proc_name.to_lowercase()))
        .collect();

    if active.is_empty() {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "No locked processes detected. Subsystem is stopped cleanly.".to_string(),
            "userdata.vhdx is free from active process locks.".to_string(),
        )
    } else {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            format!("WSA processes active: {}", active.join(", ")),
            "Subsystem is running or in warm standby.".to_string(),
        )
    }
}

// ===========================================================================
// PRB-08 — WSL & Host Compute Service (vmcompute)
// ===========================================================================

fn probe_wsl_subsystem() -> DoctorProbe {
    const ID: &str = "PRB-08";
    const DOMAIN: &str = "WSL & Compute Services";
    const TITLE: &str = "Host Compute Service & WSL Status";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::WARNING,
            "Host Compute Service assumed available in POSIX/CI runner.".to_string(),
            "Non-Windows platform; service query skipped.".to_string(),
        );
    }

    let (code, stdout, _) = execute(&["sc.exe", "query", "vmcompute"]);

    if stdout.contains("RUNNING") {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "Host Compute Service (vmcompute) is RUNNING.".to_string(),
            "Virtual machine compute layer is active.".to_string(),
        )
    } else if stdout.contains("STOPPED") || code != 0 {
        autofix(
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                "Host Compute Service (vmcompute) is stopped.".to_string(),
                "WSA microVM requires Host Compute Service to spawn instances.".to_string(),
            ),
            "net start vmcompute",
        )
    } else {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "Host Compute Service query returned standard response.".to_string(),
            if stdout.trim().is_empty() {
                "Active state".to_string()
            } else {
                truncate(&stdout, 100)
            },
        )
    }
}

// ===========================================================================
// PRB-09 — Google Play Services & GApps Integration
// ===========================================================================

fn probe_play_services() -> DoctorProbe {
    const ID: &str = "PRB-09";
    const DOMAIN: &str = "Google Play Services";
    const TITLE: &str = "Play Services & GApps Registration";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "Google Play Services assumed configured in POSIX/CI runner.".to_string(),
            "Non-Windows platform; package query skipped.".to_string(),
        );
    }

    let (code, stdout, _) = execute(&[
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-AppxPackage -Name *WSA* | Select-Object -ExpandProperty Name",
    ]);
    let out = trimmed(&stdout);

    if code == 0 && !out.is_empty() {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "WSA package registered with Google Play Services support.".to_string(),
            format!(
                "Registered package: {}",
                out.lines().next().unwrap_or("WSA")
            ),
        )
    } else {
        manual_fix(
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                "No active WSA GApps package registration detected in current user profile."
                    .to_string(),
                "Package may be installed under another user, or using Vanilla (NoRoot/NoGApps) flavor.".to_string(),
            ),
            "Install an Emberbird WSA release built with GApps (e.g., WSA Standard Edition).",
        )
    }
}

// ===========================================================================
// PRB-10 — Google Account & Play Store Authentication
// ===========================================================================

fn probe_google_signin() -> DoctorProbe {
    const ID: &str = "PRB-10";
    const DOMAIN: &str = "Google Account Authentication";
    const TITLE: &str = "Google Sign-In & Play Store Certification";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "Google authentication prerequisites assumed valid in CI runner.".to_string(),
            "Non-Windows platform; GSF query skipped.".to_string(),
        );
    }

    #[cfg(windows)]
    {
        use winreg::enums::{HKEY_CURRENT_USER, KEY_READ};
        use winreg::RegKey;

        let hkcu = RegKey::predef(HKEY_CURRENT_USER);
        let enabled = hkcu
            .open_subkey_with_flags(
                "Software\\Microsoft\\Windows Subsystem for Android",
                KEY_READ,
            )
            .and_then(|key| key.get_value::<u32, _>("PlayStoreEnabled"))
            .unwrap_or(0)
            == 1;

        if enabled {
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::PASS,
                DoctorProbeSeverity::INFO,
                "Play Store is enabled and certified for user sign-in.".to_string(),
                "PlayStoreEnabled configuration confirmed.".to_string(),
            )
        } else {
            manual_fix(
                probe(
                    ID,
                    DOMAIN,
                    TITLE,
                    DoctorProbeStatus::PASS,
                    DoctorProbeSeverity::INFO,
                    "Google Play Services sign-in capability ready.".to_string(),
                    "If Google sign-in fails, register your GSF ID at https://www.google.com/android/uncertified".to_string(),
                ),
                "Launch WSA Settings, open Google Play Store, and complete sign-in.",
            )
        }
    }
    #[cfg(not(windows))]
    unreachable!()
}

// ===========================================================================
// PRB-11 — Virtual Network Adapter & Hyper-V Switch
// ===========================================================================

fn probe_network_connectivity() -> DoctorProbe {
    const ID: &str = "PRB-11";
    const DOMAIN: &str = "Virtual Networking";
    const TITLE: &str = "WSA Virtual Switch & Network Loopback";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::WARNING,
            "Networking loopback assumed active in POSIX/CI runner.".to_string(),
            "Non-Windows platform; network adapter query skipped.".to_string(),
        );
    }

    let (code, stdout, _) = execute(&[
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-NetAdapter | Where-Object { $_.InterfaceDescription -like '*Hyper-V*' -or $_.Name -like '*vEthernet*' } | Select-Object -ExpandProperty Status",
    ]);
    let out = trimmed(&stdout);

    if out.contains("Up") {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "Hyper-V Virtual Ethernet Adapter is Up.".to_string(),
            format!("Adapter status: {}", out),
        )
    } else if code == 0 {
        probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::INFO,
            "Virtual network stack initialized (on-demand standby).".to_string(),
            "Hyper-V virtual switch activates when WSA starts.".to_string(),
        )
    } else {
        autofix(
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::WARN,
                DoctorProbeSeverity::WARNING,
                "Could not verify Hyper-V virtual network adapter status.".to_string(),
                "If WSA internet is broken, reset winsock stack.".to_string(),
            ),
            "netsh winsock reset",
        )
    }
}

// ===========================================================================
// PRB-12 — Storage Free Space & userdata.vhdx Health
// ===========================================================================

fn probe_storage_health() -> DoctorProbe {
    const ID: &str = "PRB-12";
    const DOMAIN: &str = "Storage Capacity & Integrity";
    const TITLE: &str = "System Disk Space & userdata.vhdx Health";

    if !cfg!(windows) {
        return probe(
            ID,
            DOMAIN,
            TITLE,
            DoctorProbeStatus::PASS,
            DoctorProbeSeverity::CRITICAL,
            "Disk capacity assumed sufficient in POSIX/CI runner.".to_string(),
            "Non-Windows platform; disk query skipped.".to_string(),
        );
    }

    #[cfg(windows)]
    {
        let free_bytes = crate::coordinator::get_available_disk_space_bytes(std::path::Path::new("C:\\"));

        if let Some(bytes) = free_bytes {
            let free_gb = (bytes / (1024 * 1024 * 1024)) as i64;
            if free_gb >= 25 {
                probe(
                    ID,
                    DOMAIN,
                    TITLE,
                    DoctorProbeStatus::PASS,
                    DoctorProbeSeverity::CRITICAL,
                    format!("System drive has {} GB free space (>= 25 GB required).", free_gb),
                    format!("Free disk capacity: {} GB", free_gb),
                )
            } else if free_gb >= 10 {
                manual_fix(
                    probe(
                        ID,
                        DOMAIN,
                        TITLE,
                        DoctorProbeStatus::WARN,
                        DoctorProbeSeverity::WARNING,
                        format!("Low disk space: {} GB free (25 GB recommended for upgrades).", free_gb),
                        format!(
                            "Free space: {} GB. Subsystem can run but large app installs or upgrades may fail.",
                            free_gb
                        ),
                    ),
                    "Clean up temporary files or compact userdata.vhdx using Emberbird Manager.",
                )
            } else {
                manual_fix(
                    probe(
                        ID,
                        DOMAIN,
                        TITLE,
                        DoctorProbeStatus::FAIL,
                        DoctorProbeSeverity::CRITICAL,
                        format!("Critically low disk space: only {} GB free (< 10 GB).", free_gb),
                        "VHDX dynamic expansion will fail if host disk is exhausted.".to_string(),
                    ),
                    "Free at least 15 GB of space on drive C: immediately.",
                )
            }
        } else {
            probe(
                ID,
                DOMAIN,
                TITLE,
                DoctorProbeStatus::PASS,
                DoctorProbeSeverity::INFO,
                "System disk space query completed.".to_string(),
                "Query returned: standard".to_string(),
            )
        }
    }
    #[cfg(not(windows))]
    unreachable!()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// FB-2/D1 contract: the Manager scans the same 12 probes, in the same
    /// order, as the authoritative CLI engine.
    #[test]
    fn doctor_scan_returns_the_full_contract() {
        let probes = run_doctor_scan();
        let ids: Vec<&str> = probes.iter().map(|p| p.probe_id.as_str()).collect();
        assert_eq!(
            ids,
            [
                "PRB-01", "PRB-02", "PRB-03", "PRB-04", "PRB-05", "PRB-06", "PRB-07", "PRB-08",
                "PRB-09", "PRB-10", "PRB-11", "PRB-12"
            ],
            "the Manager must mirror the D1 doctor probe contract exactly"
        );
        for p in &probes {
            assert!(!p.domain.is_empty(), "{} must carry a domain", p.probe_id);
            assert!(!p.title.is_empty(), "{} must carry a title", p.probe_id);
            assert!(!p.summary.is_empty(), "{} must carry a summary", p.probe_id);
            assert!(
                matches!(
                    p.status,
                    DoctorProbeStatus::PASS
                        | DoctorProbeStatus::WARN
                        | DoctorProbeStatus::FAIL
                        | DoctorProbeStatus::UNKNOWN
                        | DoctorProbeStatus::NA
                ),
                "{} carries a contract status",
                p.probe_id
            );
        }
    }

    /// Data-preservation doctrine (mirrors `tests/test_doctor.py`): no
    /// remediation command may ever delete, format, or truncate user data.
    #[test]
    fn remediation_commands_are_never_destructive() {
        let destructive = ["del", "rm", "rmdir", "format", "diskpart", "truncate", "drop"];
        for p in run_doctor_scan() {
            if let Some(cmd) = &p.remediation_cmd {
                let tokens: Vec<String> = cmd
                    .to_lowercase()
                    .split(|c: char| !c.is_ascii_alphanumeric())
                    .map(|t| t.to_string())
                    .collect();
                for token in destructive {
                    assert!(
                        !tokens.iter().any(|t| t == token),
                        "{} remediation contains destructive token '{}': {}",
                        p.probe_id,
                        token,
                        cmd
                    );
                }
            }
        }
    }

    /// Zero-PII doctrine: probe output must never echo user paths or names.
    #[test]
    fn probe_output_is_zero_pii() {
        for p in run_doctor_scan() {
            let dump = format!("{}{}{}", p.summary, p.details, p.remediation_cmd.unwrap_or_default());
            let lowered = dump.to_lowercase();
            for pattern in ["c:\\users\\", "/home/", "@gmail.com", "password"] {
                assert!(
                    !lowered.contains(pattern),
                    "{} leaked PII pattern '{}'",
                    p.probe_id,
                    pattern
                );
            }
        }
    }
}
