use crate::backup::{create_vhdx_backup_impl, BackupResult};
use crate::coordinator::{
    execute_upgrade_orchestration, run_upgrade_preflight, UpgradeOptions, UpgradePreflight,
    UpgradeResult,
};
use crate::detector::{detect_subsystem, WsaStatus};
use crate::doctor::DoctorProbe;
use crate::downloader::{stage_asset_from_candidates, StagedAsset, STAGE_PROGRESS_EVENT};
use crate::env::{resolve_environment, ManagerEnvConfig};
use crate::registry::{list_backups, prune_backups as prune_backups_impl, RestoreCandidate};
use crate::registry_truth::latest_published_wsa_release;
use crate::releases::{clean_version, is_update_available, ReleaseInfo, UpdateStatus};
use crate::restore::{execute_restore_impl, RestoreResult};
use crate::runtime_state::LifecycleReport;

#[tauri::command]
pub fn detect_wsa_status() -> Result<WsaStatus, String> {
    Ok(detect_subsystem())
}

/// The reconciled runtime lifecycle (PH-02 engine, PH-08 surface feed).
///
/// Detection runs on the blocking pool: it shells out to the Windows package
/// manager and can take hundreds of milliseconds, and the lifecycle command is
/// called on every dashboard refresh.
#[tauri::command]
pub async fn get_lifecycle_report() -> Result<LifecycleReport, String> {
    tauri::async_runtime::spawn_blocking(crate::runtime_state::lifecycle_report)
        .await
        .map_err(|e| format!("Lifecycle report task failed: {}", e))
}

#[tauri::command]
pub async fn run_doctor_scan() -> Result<Vec<DoctorProbe>, String> {
    // The probe engine spawns PowerShell/DISM/sc/tasklist and can take many
    // seconds; run it on the blocking pool so the UI thread never freezes.
    tauri::async_runtime::spawn_blocking(crate::doctor::run_doctor_scan)
        .await
        .map_err(|e| format!("Doctor scan task failed: {}", e))
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
pub fn validate_manager_env() -> Result<ManagerEnvConfig, String> {
    resolve_environment()
}

/// FB-3 — Close the install loop: resolve the published registry asset for
/// (release_tag, edition), stream it to the staging area with progress
/// events, SHA-256-verify against the registry hash, extract, and return the
/// staged manifest path ready for `install_wsa_package`. Registry-Driven
/// Truth: an unknown tag/edition is an error, never a guessed URL.
#[tauri::command]
pub async fn download_and_stage_release(
    release_tag: String,
    edition: String,
    app_handle: tauri::AppHandle,
) -> Result<StagedAsset, String> {
    let doc = crate::registry_truth::load_registry()
        .ok_or_else(|| "Registry unavailable: releases.json not found or unreadable".to_string())?;
    let release = doc
        .releases
        .iter()
        .find(|r| r.status == "published" && r.tag == release_tag && r.edition == edition)
        .ok_or_else(|| {
            format!(
                "No published registry asset for tag '{}' with edition '{}'",
                release_tag, edition
            )
        })?;
    let asset = release
        .assets
        .iter()
        .find(|a| a.role == "package")
        .ok_or_else(|| {
            format!(
                "Registry release '{}' carries no package asset to stage",
                release.release_id
            )
        })?;

    let window = app_handle.clone();
    // PH-40: try the registry's primary URL, then its mirrors. Verification
    // is against the registry digest for every candidate; a mirror that
    // serves different bytes is reported as a mismatch, never accepted
    // silently.
    let mirrors = asset.mirrors.clone();
    let report = stage_asset_from_candidates(
        &asset.source_url,
        &mirrors,
        &asset.sha256,
        move |progress| {
            use tauri::Emitter;
            let _ = window.emit(STAGE_PROGRESS_EVENT, progress);
        },
    )
    .await?;
    Ok(report.asset)
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
pub fn install_wsa_package(
    package_path: String,
) -> Result<crate::installer::InstallResult, String> {
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

/// Returns the host CPU architecture as reported by the Rust runtime.
/// Used by the frontend to display the correct architecture badge
/// without guessing from the User-Agent string (Rule 17 — no UA heuristics).
#[tauri::command]
pub fn get_host_arch() -> &'static str {
    std::env::consts::ARCH
}
