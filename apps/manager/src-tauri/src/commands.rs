use crate::detector::{detect_subsystem, WsaStatus};
use crate::env::{resolve_environment, ManagerEnvConfig};
use crate::releases::{is_update_available, ReleaseInfo, UpdateStatus};

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
