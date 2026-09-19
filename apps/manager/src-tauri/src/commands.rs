use crate::backup::{create_vhdx_backup_impl, BackupResult};
use crate::coordinator::{
    execute_upgrade_orchestration, run_upgrade_preflight, UpgradeOptions, UpgradePreflight,
    UpgradeResult,
};
use crate::detector::{detect_subsystem, WsaStatus};
use crate::env::{resolve_environment, ManagerEnvConfig};
use crate::registry::{list_backups, prune_backups as prune_backups_impl, RestoreCandidate};
use crate::registry_truth::latest_published_wsa_release;
use crate::releases::{clean_version, is_update_available, ReleaseInfo, UpdateStatus};
use crate::restore::{execute_restore_impl, RestoreResult};

#[tauri::command]
pub fn detect_wsa_status() -> Result<WsaStatus, String> {
    Ok(detect_subsystem())
}

#[tauri::command]
pub async fn check_for_updates() -> Result<UpdateStatus, String> {
    // Registry-Driven Truth: the latest version comes from the bundled release
    // registry, never from a hardcoded constant. The installed version comes
    // from real OS detection. If either side is unavailable we report a
    // detection failure instead of guessing.
    let current_ver = detect_subsystem()
        .package_version
        .filter(|v| !v.is_empty())
        .ok_or_else(|| {
            "Detection Failed: no installed subsystem package version could be read".to_string()
        })?;
    let latest = latest_published_wsa_release().ok_or_else(|| {
        "Registry unavailable: no published WSA release found in the release registry".to_string()
    })?;
    let latest_ver = clean_version(&latest.wsa_version);

    Ok(UpdateStatus {
        update_available: is_update_available(&current_ver, &latest_ver),
        current_version: current_ver.clone(),
        latest_version: latest_ver.clone(),
        latest_release: Some(ReleaseInfo {
            tag_name: latest.tag.clone(),
            name: latest.release_id.clone(),
            published_at: latest.published_at.clone(),
            body: String::new(),
            assets: latest
                .assets
                .iter()
                .map(|a| crate::releases::ReleaseAsset {
                    name: a.filename.clone(),
                    size: a.size_bytes,
                    browser_download_url: a.source_url.clone(),
                    architecture: a.arch.clone(),
                    root_flavor: String::new(),
                    gapps_flavor: String::new(),
                })
                .collect(),
        }),
    })
}

#[tauri::command]
pub async fn get_latest_releases() -> Result<Vec<ReleaseInfo>, String> {
    // Registry-Driven Truth: enumerate published WSA releases from the bundled
    // registry. An empty registry is an honest empty list — no fabrication.
    let doc = crate::registry_truth::load_registry()
        .ok_or_else(|| "Registry unavailable: releases.json not found or unreadable".to_string())?;
    Ok(doc
        .releases
        .iter()
        .filter(|r| r.status == "published" && r.tag.starts_with("wsa-v"))
        .map(|r| ReleaseInfo {
            tag_name: r.tag.clone(),
            name: r.release_id.clone(),
            published_at: r.published_at.clone(),
            body: String::new(),
            assets: r
                .assets
                .iter()
                .map(|a| crate::releases::ReleaseAsset {
                    name: a.filename.clone(),
                    size: a.size_bytes,
                    browser_download_url: a.source_url.clone(),
                    architecture: a.arch.clone(),
                    root_flavor: String::new(),
                    gapps_flavor: String::new(),
                })
                .collect(),
        })
        .collect())
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

#[tauri::command]
pub async fn launch_wsa(target: Option<String>) -> Result<(), String> {
    #[cfg(windows)]
    {
        let uri = target.unwrap_or_else(|| "wsa://settings".to_string());
        
        // 1. Direct invocation via shell to avoid powershell overhead where possible
        std::process::Command::new("cmd")
            .args(["/C", &format!("start \"\" \"{}\"", uri)])
            .spawn()
            .map_err(|e| format!("Failed to trigger WSA launch: {}", e))?;

        // 2. Synchronous Ready-State Loop
        // Poll every 500ms for up to 15 seconds to verify the VM actually booted
        for _ in 0..30 {
            if crate::detector::detect_subsystem().is_running {
                return Ok(());
            }
            tokio::time::sleep(std::time::Duration::from_millis(500)).await;
        }

        Err("Launch Timeout: The WSA subsystem failed to reach a 'Running' state within 15 seconds.".to_string())
    }
    #[cfg(not(windows))]
    {
        let _ = target;
        Ok(())
    }
}

#[tauri::command]
pub fn shutdown_wsa() -> Result<(), String> {
    crate::backup::request_wsa_shutdown()
}
