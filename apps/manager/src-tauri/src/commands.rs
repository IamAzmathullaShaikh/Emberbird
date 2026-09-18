use crate::backup::{create_vhdx_backup_impl, BackupResult};
use crate::coordinator::{
    execute_upgrade_orchestration, run_upgrade_preflight, UpgradeOptions, UpgradePreflight,
    UpgradeResult,
};
use crate::detector::{detect_subsystem, WsaStatus};
use crate::env::{resolve_environment, ManagerEnvConfig};
use crate::registry::{list_backups, prune_backups as prune_backups_impl, RestoreCandidate};
use crate::releases::{is_update_available, ReleaseInfo, UpdateStatus};
use crate::restore::{execute_restore_impl, RestoreResult};

#[tauri::command]
pub fn detect_wsa_status() -> Result<WsaStatus, String> {
    Ok(detect_subsystem())
}

#[tauri::command]
pub async fn check_for_updates() -> Result<UpdateStatus, String> {
    let current_ver = "2311.40000.5.0";
    let latest_ver = "2311.40000.5.0";

    Ok(UpdateStatus {
        update_available: is_update_available(current_ver, latest_ver),
        current_version: current_ver.to_string(),
        latest_version: latest_ver.to_string(),
        latest_release: None,
    })
}

#[tauri::command]
pub async fn get_latest_releases() -> Result<Vec<ReleaseInfo>, String> {
    Ok(vec![])
}

#[tauri::command]
pub fn validate_manager_env() -> Result<ManagerEnvConfig, String> {
    resolve_environment()
}

#[tauri::command]
pub fn create_vhdx_backup(note: Option<String>) -> Result<BackupResult, String> {
    match create_vhdx_backup_impl(None, None, None, note, true) {
        Ok(metadata) => Ok(BackupResult {
            success: true,
            metadata: Some(metadata),
            error: None,
        }),
        Err(err) => Ok(BackupResult {
            success: false,
            metadata: None,
            error: Some(err),
        }),
    }
}

#[tauri::command]
pub fn list_backup_candidates() -> Result<Vec<RestoreCandidate>, String> {
    list_backups(None)
}

#[tauri::command]
pub fn restore_vhdx_backup(candidate_id: String) -> Result<RestoreResult, String> {
    execute_restore_impl(&candidate_id, None, None)
}

#[tauri::command]
pub fn prune_backups(retain_count: usize) -> Result<Vec<String>, String> {
    prune_backups_impl(None, retain_count)
}

#[tauri::command]
pub fn preflight_upgrade(package_path: Option<String>) -> Result<UpgradePreflight, String> {
    Ok(run_upgrade_preflight(package_path.as_deref()))
}

#[tauri::command]
pub fn execute_upgrade(options: UpgradeOptions) -> Result<UpgradeResult, String> {
    execute_upgrade_orchestration(options)
}

#[tauri::command]
pub fn install_wsa_package(package_path: String) -> Result<crate::installer::InstallResult, String> {
    let p = std::path::Path::new(&package_path);
    let manifest = if p.is_file() {
        p.to_path_buf()
    } else {
        crate::installer::find_appx_manifest(p)?
    };
    crate::installer::register_wsa_package(&manifest)
}
