use crate::state::{derive_subsystem_state, DetectionInputs, SubsystemState};
use serde::{Deserialize, Serialize};
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
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
    let (installed, ver, path, vhdx) = check_package_registration();

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
    if let Ok(key) = hklm.open_subkey("SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock") {
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
    // Hyper-V check stub for native compilation
    true
}

#[cfg(not(windows))]
fn check_virtualization() -> bool {
    true
}

#[cfg(windows)]
fn check_processes() -> bool {
    use windows::Win32::System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, Process32FirstW, Process32NextW, PROCESSENTRY32W, TH32CS_SNAPPROCESS,
    };

    unsafe {
        let snapshot = match CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0) {
            Ok(s) => s,
            Err(_) => return false,
        };

        let mut entry = PROCESSENTRY32W::default();
        entry.dwSize = std::mem::size_of::<PROCESSENTRY32W>() as u32;

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
    // In production, queries WinRT Windows.Management.Deployment.PackageManager
    // Fallback/standard path detection:
    let local_app_data = std::env::var("LOCALAPPDATA").unwrap_or_default();

    // Orphaned-data detection: the VHDX is only reported when the file
    // actually exists on disk, so an orphaned file can never read as an
    // installation signal.
    let vhdx_candidate = if !local_app_data.is_empty() {
        Some(format!(
            "{}\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache\\userdata.vhdx",
            local_app_data
        ))
    } else {
        None
    };
    let vhdx = vhdx_candidate.filter(|p| std::path::Path::new(p).exists());

    // Package data directory (LocalCache): exists only when the package has
    // created its data, i.e. WSA was actually set up at least once.
    let data_dir = if !local_app_data.is_empty() {
        let dir = format!(
            "{}\\Packages\\MicrosoftCorporationII.WindowsSubsystemForAndroid_8wekyb3d8bbwe\\LocalCache",
            local_app_data
        );
        if std::path::Path::new(&dir).exists() {
            Some(dir)
        } else {
            None
        }
    } else {
        None
    };

    (
        false,
        None,
        data_dir,
        vhdx,
    )
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
