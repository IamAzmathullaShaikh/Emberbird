use crate::state::{derive_subsystem_state, DetectionInputs, SubsystemState};
use serde::{Deserialize, Serialize};
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct WsaStatus {
    pub installed: bool,
    pub package_version: Option<String>,
    pub developer_mode_enabled: bool,
    pub virtualization_enabled: bool,
    pub is_running: bool,
    pub install_path: Option<String>,
    pub vhdx_path: Option<String>,
    /// Authoritative lifecycle state. This is the ONLY field the UI may use
    /// to decide install-state wording; `installed` and friends are raw
    /// detection signals retained for backward compatibility.
    pub state: SubsystemState,
    /// Evidence trail explaining how `state` was derived.
    pub state_evidence: Vec<String>,
}

pub fn detect_subsystem() -> WsaStatus {
    let dev_mode = check_developer_mode();
    let virt = check_virtualization();
    let running = check_processes();
    let (_, ver, path, vhdx) = check_package_registration();

    // Single authoritative derivation. `installed` is re-derived from the
    // state so the boolean can never contradict the state the UI renders.
    let inputs = DetectionInputs::from_signals(ver.clone(), path.clone(), vhdx.clone());
    let derived = derive_with_baseline(&inputs);

    WsaStatus {
        installed: derived.state.is_registered(),
        package_version: ver,
        developer_mode_enabled: dev_mode,
        virtualization_enabled: virt,
        is_running: running,
        install_path: path,
        vhdx_path: vhdx,
        state: derived.state,
        state_evidence: derived.evidence,
    }
}

/// Derivation with the subsystem baseline from release intelligence.
fn derive_with_baseline(inputs: &DetectionInputs) -> crate::state::DerivedSubsystemState {
    let baseline = crate::state::subsystem_baseline_version();
    let mut with_baseline = inputs.clone();
    with_baseline.baseline_version = baseline;
    derive_subsystem_state(&with_baseline)
}

#[cfg(windows)]
fn check_developer_mode() -> bool {
    use winreg::enums::*;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    if let Ok(key) =
        hklm.open_subkey("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock")
    {
        if let Ok(val) = key.get_value::<u32, _>("AllowDevelopmentWithoutDevLicense") {
            return val == 1;
        }
    }
    false
}

#[cfg(not(windows))]
fn check_developer_mode() -> bool {
    true
}

#[cfg(windows)]
fn check_virtualization() -> bool {
    // Real detection: Hyper-V present means virtualization is active. Fall back
    // to CPU virtualization-firmware support via wmic when Hyper-V is off —
    // that is what the VM needs to start. Never hardcode `true`.
    if let Ok(output) = std::process::Command::new("powershell.exe")
        .args([
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_ComputerSystem).HypervisorPresent",
        ])
        .output()
    {
        if output.status.success() && String::from_utf8_lossy(&output.stdout).contains("True") {
            return true;
        }
    }
    matches!(
        std::process::Command::new("wmic")
            .args(["cpu", "get", "VirtualizationFirmwareEnabled", "/value"])
            .output(),
        Ok(out)
            if out.status.success()
                && String::from_utf8_lossy(&out.stdout)
                    .to_lowercase()
                    .contains("virtualizationfirmwareenabled=true")
    )
}

#[cfg(not(windows))]
fn check_virtualization() -> bool {
    true
}

#[cfg(windows)]
fn check_processes() -> bool {
    use windows::Win32::System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, Process32FirstW, Process32NextW, PROCESSENTRY32W,
        TH32CS_SNAPPROCESS,
    };

    unsafe {
        let snapshot = match CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) {
            Ok(s) => s,
            Err(_) => return false,
        };

        let mut entry = PROCESSENTRY32W {
            dwSize: std::mem::size_of::<PROCESSENTRY32W>() as u32,
            ..Default::default()
        };

        if Process32FirstW(snapshot, &mut entry).is_ok() {
            loop {
                let name = String::from_utf16_lossy(&entry.szExeFile);
                let clean = name.trim_matches(char::from(0)).to_lowercase();
                if clean.contains("vmmemwsa") || clean.contains("wsaclient") {
                    return true;
                }
                if Process32NextW(snapshot, &mut entry).is_err() {
                    break;
                }
            }
        }
    }
    false
}

#[cfg(not(windows))]
fn check_processes() -> bool {
    false
}

fn check_package_registration() -> (bool, Option<String>, Option<String>, Option<String>) {
    let local_app_data = std::env::var("LOCALAPPDATA").unwrap_or_default();

    let (data_dir, vhdx) = if !local_app_data.is_empty() {
        let cache = std::path::PathBuf::from(&local_app_data)
            .join("Packages")
            .join("MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe")
            .join("LocalCache");
        if cache.exists() {
            let v2 = cache.join("userdata.2.vhdx");
            let v1 = cache.join("userdata.vhdx");
            let vhdx_path = if v2.exists() {
                Some(v2.to_string_lossy().to_string())
            } else if v1.exists() {
                Some(v1.to_string_lossy().to_string())
            } else {
                None
            };
            (Some(cache.to_string_lossy().to_string()), vhdx_path)
        } else {
            (None, None)
        }
    } else {
        (None, None)
    };

    #[cfg(windows)]
    {
        let mut is_registered = false;
        let mut version = None;
        let mut install_path = None;

        if let Ok(output) = std::process::Command::new("powershell.exe")
            .args([
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "(Get-AppxPackage MicrosoftCorporationII.WindowsSubsystemForAndroid) | ForEach-Object { \"$($_.Version)|$($_.InstallLocation)\" }",
            ])
            .output()
        {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !stdout.is_empty() {
                    if let Some((ver, path)) = stdout.split_once('|') {
                        let v = ver.trim();
                        let p = path.trim();
                        if !v.is_empty() {
                            version = Some(v.to_string());
                            is_registered = true;
                        }
                        if !p.is_empty() {
                            install_path = Some(p.to_string());
                        }
                    }
                }
            }
        }

        (is_registered, version, install_path.or(data_dir), vhdx)
    }

    #[cfg(not(windows))]
    {
        (false, None, data_dir, vhdx)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wsa_status_struct_serialization() {
        let status = WsaStatus {
            installed: true,
            package_version: Some("2311.40000.5.0".to_string()),
            developer_mode_enabled: true,
            virtualization_enabled: true,
            is_running: false,
            install_path: Some("C:\\WSA".to_string()),
            vhdx_path: Some("C:\\WSA\\userdata.vhdx".to_string()),
            state: SubsystemState::Installed,
            state_evidence: vec!["test evidence".to_string()],
        };

        let json = serde_json::to_string(&status).expect("Serialization failed");
        assert!(json.contains("2311.40000.5.0"));
        assert!(json.contains("developer_mode_enabled"));
        assert!(json.contains("INSTALLED"));
    }
}
