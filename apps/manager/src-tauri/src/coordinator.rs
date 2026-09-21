use crate::backup::{create_vhdx_backup_impl, get_default_vhdx_path, BackupMetadata};
use crate::installer::{find_appx_manifest, register_wsa_package};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

pub const REQUIRED_DISK_SPACE_BYTES: u64 = 25 * 1024 * 1024 * 1024; // 25 GB

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct UpgradePreflight {
    /// `None` = the host build could not be read. Unverifiable is never a pass
    /// (Zero-Mock law): the UI renders UNVERIFIED, not a green check.
    pub windows_version_ok: Option<bool>,
    pub windows_build: Option<u32>,
    /// Minimum supported build (registry/preflight truth — FB-1). The UI must
    /// render this instead of a hardcoded requirement string.
    pub required_windows_build: u32,
    pub dev_mode_ok: bool,
    pub virtualization_ok: bool,
    /// `None` = free space could not be measured (UNVERIFIED, never a pass).
    pub disk_space_ok: Option<bool>,
    pub free_disk_bytes: Option<u64>,
    pub required_disk_bytes: u64,
    pub wsa_running: bool,
    pub has_existing_vhdx: bool,
    pub warnings: Vec<String>,
    pub errors: Vec<String>,
    pub can_upgrade: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, specta::Type)]
pub struct UpgradeOptions {
    pub package_path: String,
    pub create_backup: bool,
    pub backup_note: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, specta::Type)]
pub struct UpgradeResult {
    pub success: bool,
    pub backup_metadata: Option<BackupMetadata>,
    pub installed_manifest: Option<String>,
    pub message: String,
}

/// Tri-state requirement evaluation: `None` means the underlying probe could
/// not observe the host, so no verdict may be claimed; `Some(false)` fails,
/// `Some(true)` passes. Every preflight requirement routes through here so
/// "could not measure" can never be rendered as "met".
fn verify_requirement<T: PartialOrd>(value: Option<T>, required: T) -> Option<bool> {
    value.map(|v| v >= required)
}

/// Free bytes on the volume containing `path`. `None` = measurement failed.
#[cfg(windows)]
pub fn get_available_disk_space_bytes(path: &Path) -> Option<u64> {
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
            Some(free_bytes_available_to_caller)
        } else {
            None
        }
    }
}

#[cfg(not(windows))]
pub fn get_available_disk_space_bytes(_path: &Path) -> Option<u64> {
    None
}

/// Windows build read from the registry. `None` = unreadable, which stays
/// UNVERIFIED instead of falling back to an assumed build number.
#[cfg(windows)]
pub fn check_windows_build_number() -> Option<u32> {
    use winreg::enums::*;
    use winreg::RegKey;

    let hklm = RegKey::predef(HKEY_LOCAL_MACHINE);
    let key = hklm
        .open_subkey("SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion")
        .ok()?;
    let build_str = key.get_value::<String, _>("CurrentBuild").ok()?;
    build_str.parse::<u32>().ok()
}

#[cfg(not(windows))]
pub fn check_windows_build_number() -> Option<u32> {
    None
}

pub fn run_upgrade_preflight(package_path: Option<&str>) -> UpgradePreflight {
    let mut warnings = Vec::new();
    let mut errors = Vec::new();

    let required_windows_build = crate::state::min_windows_build();
    let windows_build = check_windows_build_number();
    let windows_version_ok = verify_requirement(windows_build, required_windows_build);
    match (windows_version_ok, windows_build) {
        (Some(false), Some(build)) => errors.push(format!(
            "Windows build {} is unsupported. Windows 10 Build {}+ or Windows 11 Build 22000+ is required.",
            build, required_windows_build
        )),
        (None, _) => warnings.push(
            "Windows build number could not be read from the registry; the build requirement is UNVERIFIED."
                .to_string(),
        ),
        _ => {}
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
    let disk_space_ok = verify_requirement(free_disk_bytes, REQUIRED_DISK_SPACE_BYTES);
    let required_disk_gb = REQUIRED_DISK_SPACE_BYTES / (1024 * 1024 * 1024);
    match (disk_space_ok, free_disk_bytes) {
        (Some(false), Some(free)) => warnings.push(format!(
            "Available disk space ({} GB) is below the recommended {} GB.",
            free / (1024 * 1024 * 1024),
            required_disk_gb
        )),
        (None, _) => warnings.push(format!(
            "Free disk space could not be measured; the {} GB requirement is UNVERIFIED.",
            required_disk_gb
        )),
        _ => {}
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
        required_windows_build,
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
        // The verdict exists only when the probe read the host.
        assert_eq!(
            preflight.windows_version_ok.is_some(),
            preflight.windows_build.is_some(),
            "an unreadable build probe must stay UNVERIFIED, never a pass"
        );
        assert_eq!(
            preflight.disk_space_ok.is_some(),
            preflight.free_disk_bytes.is_some(),
            "an unmeasurable disk probe must stay UNVERIFIED, never a pass"
        );
    }

    #[test]
    fn test_unverified_requirement_is_never_a_pass() {
        assert_eq!(verify_requirement(None::<u32>, 19045), None);
        assert_eq!(verify_requirement(Some(19044u32), 19045), Some(false));
        assert_eq!(verify_requirement(Some(19045u32), 19045), Some(true));
    }

    #[test]
    fn test_unverified_probes_warn_instead_of_passing_silently() {
        let preflight = run_upgrade_preflight(None);
        if preflight.windows_version_ok.is_none() {
            assert!(preflight.windows_build.is_none());
            assert!(
                preflight.warnings.iter().any(|w| w.contains("UNVERIFIED")),
                "an unreadable build probe must surface a warning"
            );
        }
        if preflight.disk_space_ok.is_none() {
            assert!(preflight.free_disk_bytes.is_none());
            assert!(
                preflight.warnings.iter().any(|w| w.contains("UNVERIFIED")),
                "an unmeasurable disk probe must surface a warning"
            );
        }
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
