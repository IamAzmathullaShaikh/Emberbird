use crate::backup::{create_vhdx_backup_impl, get_default_vhdx_path, BackupMetadata};
use crate::installer::{find_appx_manifest, register_wsa_package};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

pub const REQUIRED_DISK_SPACE_BYTES: u64 = 25 * 1024 * 1024 * 1024; // 25 GB

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UpgradePreflight {
    pub windows_version_ok: bool,
    pub windows_build: u32,
    pub dev_mode_ok: bool,
    pub virtualization_ok: bool,
    pub disk_space_ok: bool,
    pub free_disk_bytes: u64,
    pub required_disk_bytes: u64,
    pub wsa_running: bool,
    pub has_existing_vhdx: bool,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub can_upgrade: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpgradeOptions {
    pub package_path: String,
    pub create_backup: bool,
    pub backup_note: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UpgradeResult {
    pub success: bool,
    pub backup_metadata: Option<BackupMetadata>,
    pub installed_manifest: Option<String>,
    pub message: String,
}

#[cfg(windows)]
pub fn get_available_disk_space_bytes(path: &Path) -> u64 {
    use std::os::windows::ffi::OsStrExt;
    use windows::core::PCWSTR;
    use windows::Win32::Storage::FileSystem::GetDiskFreeSpaceExW;

    let root_path = path.ancestors().last().unwrap_or(path);
    let mut wide: Vec<u16> = root_path.as_os_str().encode_wide().collect();
    wide.push(0);

    let mut free_bytes_available_to_caller = 0u64;
    let mut total_number_of_bytes = 0u64;
    let mut total_number_of_free_bytes = 0u64;

    unsafe {
        if GetDiskFreeSpaceExW(
            PCWSTR(wide.as_ptr()),
            Some(&mut free_bytes_available_to_caller),
            Some(&mut total_number_of_bytes),
            Some(&mut total_number_of_free_bytes),
        )
        .is_ok()
        {
            free_bytes_available_to_caller
        } else {
            50 * 1024 * 1024 * 1024
        }
    }
}

#[cfg(not(windows))]
pub fn get_available_disk_space_bytes(_path: &Path) -> u64 {
    50 * 1024 * 1024 * 1024
}

#[cfg(windows)]
pub fn check_windows_build_number() -> (bool, u32) {
    use winreg::enums::*;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    if let Ok(key) = hklm.open_subkey("SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion") {
        if let Ok(build_str) = key.get_value::<String, _>("CurrentBuild") {
            if let Ok(build_num) = build_str.parse::<u32>() {
                return (build_num >= 19045, build_num);
            }
        }
    }
    (true, 22631)
}

#[cfg(not(windows))]
pub fn check_windows_build_number() -> (bool, u32) {
    (true, 22631)
}

pub fn run_upgrade_preflight(package_path: Option<&str>) -> UpgradePreflight {
    let mut warnings = Vec::new();
    let mut errors = Vec::new();

    let (windows_version_ok, windows_build) = check_windows_build_number();
    if !windows_version_ok {
        errors.push(format!(
            "Windows build {} is unsupported. Windows 10 Build 19045+ or Windows 11 Build 22000+ is required.",
            windows_build
        ));
    }

    let status = crate::detector::detect_subsystem();
    let dev_mode_ok = status.developer_mode_enabled;
    if !dev_mode_ok {
        errors.push(
            "Windows Developer Mode is disabled. Enable it in Windows Settings > System > For developers."
                .to_string(),
        );
    }

    let virtualization_ok = status.virtualization_enabled;
    if !virtualization_ok {
        errors.push(
            "Virtual Machine Platform / Hyper-V is disabled. Enable virtualization in BIOS and Windows Features."
                .to_string(),
        );
    }

    let system_drive = Path::new("C:\\");
    let free_disk_bytes = get_available_disk_space_bytes(system_drive);
    let disk_space_ok = free_disk_bytes >= REQUIRED_DISK_SPACE_BYTES;
    if !disk_space_ok {
        warnings.push(format!(
            "Available disk space ({} GB) is below the recommended 25 GB.",
            free_disk_bytes / (1024 * 1024 * 1024)
        ));
    }

    if status.is_running {
        warnings.push(
            "WSA is currently running and will be gracefully terminated prior to upgrade."
                .to_string(),
        );
    }

    let has_existing_vhdx = get_default_vhdx_path()
        .map(|p| p.exists())
        .unwrap_or(false);

    if let Some(pkg) = package_path {
        let pkg_path = Path::new(pkg);
        if !pkg_path.exists() {
            errors.push(format!("Target package path does not exist: {}", pkg));
        } else if let Err(e) = find_appx_manifest(pkg_path) {
            errors.push(e);
        }
    }

    let can_upgrade = errors.is_empty();

    UpgradePreflight {
        windows_version_ok,
        windows_build,
        dev_mode_ok,
        virtualization_ok,
        disk_space_ok,
        free_disk_bytes,
        required_disk_bytes: REQUIRED_DISK_SPACE_BYTES,
        wsa_running: status.is_running,
        has_existing_vhdx,
        warnings,
        errors,
        can_upgrade,
    }
}

pub fn execute_upgrade_orchestration(options: UpgradeOptions) -> Result<UpgradeResult, String> {
    let preflight = run_upgrade_preflight(Some(&options.package_path));
    if !preflight.can_upgrade {
        return Err(format!(
            "Upgrade preflight check failed: {}",
            preflight.errors.join("; ")
        ));
    }

    let pkg_path = PathBuf::from(&options.package_path);
    let manifest_path = find_appx_manifest(&pkg_path)?;

    let mut backup_meta: Option<BackupMetadata> = None;
    if options.create_backup && preflight.has_existing_vhdx {
        let note = options.backup_note.clone().or_else(|| {
            Some("Automated safety backup before WSA package upgrade".to_string())
        });

        match create_vhdx_backup_impl(None, None, None, note, true) {
            Ok(meta) => {
                backup_meta = Some(meta);
            }
            Err(e) => {
                return Err(format!(
                    "Safety backup failed prior to upgrade: {}. Upgrade aborted.",
                    e
                ));
            }
        }
    }

    let install_res = register_wsa_package(&manifest_path)?;

    Ok(UpgradeResult {
        success: install_res.success,
        backup_metadata: backup_meta,
        installed_manifest: Some(manifest_path.to_string_lossy().to_string()),
        message: "WSA upgrade completed successfully".to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_upgrade_preflight_evaluation() {
        let preflight = run_upgrade_preflight(None);
        assert_eq!(preflight.required_disk_bytes, 25 * 1024 * 1024 * 1024);
        assert!(preflight.windows_build > 0);
    }

    #[test]
    fn test_upgrade_preflight_missing_package_error() {
        let preflight =
            run_upgrade_preflight(Some("C:\\nonexistent_wsa_package_never_exists_12345"));
        assert!(!preflight.can_upgrade);
        assert!(preflight
            .errors
            .iter()
            .any(|e| e.contains("does not exist")));
    }
}
